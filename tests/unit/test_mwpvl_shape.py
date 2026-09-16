"""Shaping OCR'd rows into the national facility-panel schema.

Schema drift is the silent failure here. If the expanded frame and the
104-row frame do not carry identical columns, `pd.concat` fills the
difference with NaN and the stacked panel ships with half its rows missing a
column nobody checked. So the column sets are asserted against each other,
not against a written list.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.warehouse import mwpvl_shape as shape


def _raw(rows: list[dict]) -> pd.DataFrame:
    defaults = {"code": "DAX8", "street": "1910 E Vista Way", "city": "Vista",
                "addr_region": "California", "postcode": "92081",
                "sqft": "142800", "open_year": "2019", "open_month": "10",
                "open_quarter": "", "date_precision": "month",
                "description": "Delivery Station",
                "table": "08_us_delivery_station", "row": "0"}
    defaults.update(dict.fromkeys(shape.FLAGS, "False"))
    return pd.DataFrame([{**defaults, **r} for r in rows], dtype=str)


def _geo(n: int, **over) -> pd.DataFrame:
    base = {"zcta": "92081", "county_geoid": "06073", "state": "CA",
            "cbsa_code": "41740", "cbsa_title": "San Diego",
            "geo_status": "ok"}
    base.update(over)
    return pd.DataFrame([base] * n)


# ---------------------------------------------------------------------------
# to_panel_rows
# ---------------------------------------------------------------------------
#: Declared in `ADDED_COLUMNS` but NOT written by `to_panel_rows`. They come
#: from `facility_dedup.adjudicate`, which `mwpvl_merge` runs in between.
#:
#: This asymmetry is a trap rather than a live defect. `mwpvl_merge` reaches
#: the concat through `adjudicate`, so the three arrive and the panel stacks.
#: Any other caller that shapes rows and stacks them directly gets three
#: silently-NaN columns and no error. Pinned here so the gap is visible.
_FILLED_BY_ADJUDICATE = {"duplicate_of", "open_date_contradicted",
                         "open_date_unresolved"}


def test_the_output_carries_the_national_schema_plus_the_added_columns():
    out = shape.to_panel_rows(_raw([{}]), _geo(1))
    assert list(out.columns)[:len(shape.NATIONAL_COLUMNS)] \
        == list(shape.NATIONAL_COLUMNS)
    assert set(shape.ADDED_COLUMNS) - _FILLED_BY_ADJUDICATE <= set(out.columns)


def test_three_declared_columns_are_not_written_here_but_downstream():
    """See `_FILLED_BY_ADJUDICATE`. If this ever fails because the set
    shrank, `mwpvl_shape` grew the columns and the note above is stale."""
    out = shape.to_panel_rows(_raw([{}]), _geo(1))
    assert set(shape.ADDED_COLUMNS) - set(out.columns) \
        == _FILLED_BY_ADJUDICATE


def test_a_row_keeps_its_place_so_an_id_traces_back_to_a_line_of_ocr():
    out = shape.to_panel_rows(_raw([{}, {"code": "DSM5"}, {"code": "DFW9"}]),
                              _geo(3))
    assert out["facility_id"].tolist() == ["MWP-0001", "MWP-0002", "MWP-0003"]
    assert out["mwpvl_code"].tolist() == ["DAX8", "DSM5", "DFW9"]


def test_geography_comes_from_the_crosswalk_and_not_from_the_ocr():
    """MWPVL's state column arrives as "Taxas", "Texas Texas". The county
    GEOID's first two digits are a fact about the crosswalk."""
    out = shape.to_panel_rows(_raw([{"addr_region": "Taxas"}]), _geo(1))
    assert out["state"].iloc[0] == "CA"
    assert out["mwpvl_region_ocr"].iloc[0] == "Taxas"   # kept, not discarded


@pytest.mark.parametrize("month,quarter,expected", [
    ("10", "", "4"),
    ("1", "", "1"),
    ("", "3", "3"),
    ("", "", ""),          # never invented
])
def test_a_quarter_is_converted_or_left_empty_but_never_defaulted(
        month, quarter, expected):
    """`warehouse/facility_load` applies the Q1 convention at load and
    records it in `open_quarter_imputed`. Writing Q1 here would destroy the
    distinction that module exists to preserve."""
    out = shape.to_panel_rows(_raw([{"open_month": month,
                                     "open_quarter": quarter}]), _geo(1))
    assert out["open_quarter"].iloc[0] == expected


def test_an_impossible_year_is_flagged_and_still_carried():
    out = shape.to_panel_rows(_raw([{"open_year": "2094"},
                                    {"open_year": "2009"},
                                    {"open_year": "2019"}]), _geo(3))
    assert out["open_year"].tolist() == ["2094", "2009", "2019"]
    assert out["date_flag"].tolist() == [shape.DATE_IMPLAUSIBLE,
                                         shape.DATE_BEFORE_NETWORK,
                                         shape.DATE_OK]


def test_vouching_is_the_publishers_statement_and_drives_confidence():
    out = shape.to_panel_rows(_raw([{}, {"not_confirmed": "True"},
                                    {"delayed": "True"},
                                    {"cancelled": "True"}]), _geo(4))
    assert out["mwpvl_vouched"].tolist() == [True, False, False, False]
    assert out["confidence"].tolist() == ["medium", "low", "low", "low"]


def test_closed_does_not_become_a_status_because_both_hits_are_false():
    """A `closed` status with no `close_year` reaches `warehouse/facilities`
    as a close index of +inf, which loses the closure entirely. Both rows
    that set this flag are descriptions of something else closing."""
    out = shape.to_panel_rows(_raw([{"closed": "True"}]), _geo(1))
    assert out["status"].iloc[0] == "open"
    assert out["closed"].iloc[0] is True or bool(out["closed"].iloc[0])


def test_not_confirmed_and_cancelled_become_announced():
    out = shape.to_panel_rows(_raw([{"not_confirmed": "True"},
                                    {"cancelled": "True"},
                                    {"delayed": "True"}]), _geo(3))
    # delayed says nothing about WHICH state the building is in, so it stays
    # a flag rather than moving the status.
    assert out["status"].tolist() == ["announced", "announced", "open"]


def test_the_source_type_stays_inside_the_closed_vocabulary():
    from siting_atlas.ingest.facility_check import VALID_SOURCE_TYPES
    out = shape.to_panel_rows(_raw([{}]), _geo(1))
    assert out["source_type"].iloc[0] in VALID_SOURCE_TYPES
    # The precise provenance travels in a column where it cannot be mistaken
    # for one of the seven.
    assert out["source_dataset"].iloc[0] == shape.SOURCE_DATASET


def test_no_coordinate_is_invented():
    out = shape.to_panel_rows(_raw([{}]), _geo(1))
    assert out["latitude"].iloc[0] == "" and out["longitude"].iloc[0] == ""


# ---------------------------------------------------------------------------
# align_national
# ---------------------------------------------------------------------------
def _national(n: int = 2) -> pd.DataFrame:
    return pd.DataFrame([dict.fromkeys(shape.NATIONAL_COLUMNS, "x")] * n)


def test_the_two_frames_stack_with_nothing_lost_to_a_missing_column():
    """The path `mwpvl_merge` actually takes: shape, adjudicate, then stack.

    A column present on one side and absent on the other is filled with NaN
    by `pd.concat` and the panel ships with half its rows missing it.
    """
    from siting_atlas.warehouse.facility_dedup import adjudicate

    right = shape.to_panel_rows(_raw([{}, {"code": "DSM5",
                                           "street": "9 Elm St"}]), _geo(2))
    right["open_q_index"] = [2019 * 4 + 3, 2022 * 4]
    right, _ = adjudicate(right)

    left = shape.align_national(_national(2), _geo(2))
    assert set(left.columns) <= set(right.columns)

    # `adjudicate` leaves `duplicate_of` as an object column of None on rows
    # it did not fold, and `align_national` fills the same column with "".
    # Stacking the two without this line gives a column that is empty-string
    # on the 104 curated rows and NaN on the MWPVL ones — one column, two
    # spellings of "no duplicate". `mwpvl_merge.run` does exactly this.
    assert right["duplicate_of"].isna().all()
    right["duplicate_of"] = right["duplicate_of"].fillna("")

    stacked = pd.concat([left, right[list(left.columns)]], ignore_index=True)
    assert len(stacked) == 4
    assert not stacked.isna().any().any()


def test_an_added_column_is_never_filled_with_something_measurable():
    out = shape.align_national(_national(1), _geo(1))
    for column in shape.ADDED_COLUMNS:
        if column in ("zcta", "cbsa_code", "geo_status", "source_dataset"):
            continue
        expected = False if column in shape.BOOLEAN_COLUMNS else ""
        assert out[column].iloc[0] == expected, column


def test_the_existing_rows_are_labelled_so_the_two_sources_are_separable():
    out = shape.align_national(_national(1), _geo(1))
    assert out["source_dataset"].iloc[0] == "national_facilities"


def test_the_curated_cbsa_title_is_not_overwritten_by_the_crosswalk():
    national = _national(1)
    national["cbsa_title"] = "Curated Metro"
    out = shape.align_national(national, _geo(1, cbsa_title="San Diego"))
    assert out["cbsa_title"].iloc[0] == "Curated Metro"
    # ...but the three geography columns ARE filled, so a join cannot drop
    # the older half of the panel.
    assert out["cbsa_code"].iloc[0] == "41740"
