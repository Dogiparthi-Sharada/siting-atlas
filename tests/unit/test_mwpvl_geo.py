"""Placing an OCR'd postal code, and counting what could not be placed.

Everything here fails QUIETLY if it fails at all: a postcode absent from the
crosswalk produces an empty ZCTA, a county in no CBSA produces an empty CBSA
code, and both look identical to a successful placement in a CSV. The module
answers that by giving every row exactly one `geo_status`, so the failures add
up to the total. These tests hold that invariant.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.warehouse import mwpvl_geo as geo


@pytest.fixture
def crosswalks(tmp_path, monkeypatch):
    """A four-ZCTA crosswalk: one metro county, one non-metro, one in CT."""
    zcta_county = tmp_path / "zcta_county.parquet"
    cbsa_county = tmp_path / "cbsa_county.parquet"
    pd.DataFrame({
        "zcta": ["92081", "50021", "59001", "06001"],
        "county_geoid": ["06073", "19153", "30009", "09001"],
        "shared_land_area": [1.0, 1.0, 1.0, 1.0],
    }).to_parquet(zcta_county, index=False)
    pd.DataFrame({
        "county_geoid": ["06073", "19153"],
        "cbsa_code": ["41740", "19780"],
        "cbsa_title": ["San Diego", "Des Moines"],
    }).to_parquet(cbsa_county, index=False)
    monkeypatch.setattr(geo, "ZCTA_COUNTY", zcta_county)
    monkeypatch.setattr(geo, "CBSA_COUNTY", cbsa_county)
    return tmp_path


def test_a_known_postcode_resolves_all_the_way_to_a_metro(crosswalks):
    frame, report = geo.resolve(pd.Series(["92081"]))
    row = frame.iloc[0]
    assert (row["zcta"], row["county_geoid"]) == ("92081", "06073")
    assert (row["state"], row["cbsa_code"]) == ("CA", "41740")
    assert row["geo_status"] == geo.OK
    assert report["with_zcta"] == report["with_cbsa"] == 1


def test_every_row_carries_exactly_one_status_and_they_add_up(crosswalks):
    """The invariant. Without it a failure can be lost between subtotals."""
    codes = pd.Series(["92081", "50021", "59001", "06001", "99999", None])
    frame, report = geo.resolve(codes)
    assert len(frame) == len(codes)
    assert frame["geo_status"].notna().all()
    assert sum(report["by_status"].values()) == report["rows"] == len(codes)
    assert set(report["by_status"]) <= {geo.OK, geo.NO_ZCTA, geo.NO_CBSA,
                                        geo.CT_VINTAGE, geo.NO_XWALK}


def test_a_postcode_that_is_not_a_zcta_is_counted_not_geocoded(crosswalks):
    frame, report = geo.resolve(pd.Series(["99999"]))
    assert frame["zcta"].iloc[0] == ""
    assert frame["geo_status"].iloc[0] == geo.NO_ZCTA
    assert report["by_status"][geo.NO_ZCTA] == 1


def test_a_county_in_no_cbsa_is_a_status_of_its_own(crosswalks):
    frame, _ = geo.resolve(pd.Series(["59001"]))
    assert frame["geo_status"].iloc[0] == geo.NO_CBSA
    assert frame["state"].iloc[0] == "MT"     # placed, just not in a metro


def test_the_connecticut_vintage_gap_is_named_rather_than_left_blank(
        crosswalks):
    """OMB 2023 uses nine planning regions; the 2020 ZCTA file uses eight
    legacy counties. They do not join, and the row is not a failure of this
    row."""
    frame, _ = geo.resolve(pd.Series(["06001"]))
    assert frame["geo_status"].iloc[0] == geo.CT_VINTAGE


def test_a_zip_plus_four_is_truncated_to_five(crosswalks):
    frame, _ = geo.resolve(pd.Series(["92081-2607"]))
    assert frame["zcta"].iloc[0] == "92081"


def test_an_absent_crosswalk_places_nothing_and_says_how_many(tmp_path,
                                                              monkeypatch):
    """"We could not do it" and "there was nothing to do" are different."""
    monkeypatch.setattr(geo, "ZCTA_COUNTY", tmp_path / "missing.parquet")
    monkeypatch.setattr(geo, "CBSA_COUNTY", tmp_path / "gone.parquet")
    frame, report = geo.resolve(pd.Series(["92081", "50021"]))
    assert (frame["geo_status"] == geo.NO_XWALK).all()
    assert report["crosswalks_present"] is False
    assert report["rows_uncovered_by_the_missing_file"] == 2
    assert len(report["crosswalks_missing"]) == 2


def test_the_index_is_preserved_so_the_result_joins_back_on_its_rows(
        crosswalks):
    codes = pd.Series(["92081", "50021"], index=[7, 11])
    frame, _ = geo.resolve(codes)
    assert frame.index.tolist() == [7, 11]
    assert list(frame.columns) == list(geo.COLUMNS)


def test_a_split_zcta_resolves_to_the_county_holding_most_of_its_land(
        tmp_path, monkeypatch):
    """A no-op on today's file, which is one row per ZCTA. It is written as
    a reduction so a future re-ingest that keeps the splits cannot silently
    pick whichever row pandas saw first."""
    zcta_county = tmp_path / "zcta_county.parquet"
    pd.DataFrame({
        "zcta": ["92081", "92081"],
        "county_geoid": ["06073", "06059"],
        "shared_land_area": [3.0, 9.0],
    }).to_parquet(zcta_county, index=False)
    cbsa_county = tmp_path / "cbsa_county.parquet"
    pd.DataFrame({"county_geoid": ["06059"], "cbsa_code": ["31080"],
                  "cbsa_title": ["Los Angeles"]}).to_parquet(cbsa_county,
                                                             index=False)
    monkeypatch.setattr(geo, "ZCTA_COUNTY", zcta_county)
    monkeypatch.setattr(geo, "CBSA_COUNTY", cbsa_county)

    frame, _ = geo.resolve(pd.Series(["92081"]))
    assert frame["county_geoid"].iloc[0] == "06059"


# ---------------------------------------------------------------------------
# grade_ocr_state
# ---------------------------------------------------------------------------
_NAME_TO_CODE = {"california": "CA", "iowa": "IA", "montana": "MT"}


def test_the_ocr_state_is_graded_against_the_crosswalk_for_free(crosswalks):
    resolved, _ = geo.resolve(pd.Series(["92081", "50021", "59001"]))
    grade = geo.grade_ocr_state(pd.Series(["California", "Iowa", "Taxas"]),
                                resolved, _NAME_TO_CODE)
    assert grade["comparable"] == 2
    assert grade["agree"] == 2 and grade["disagree"] == 0
    assert grade["ocr_state_unparsed"] == 1
    assert grade["agreement_rate"] == 1.0


def test_a_disagreement_is_counted_rather_than_corrected(crosswalks):
    resolved, _ = geo.resolve(pd.Series(["92081"]))
    grade = geo.grade_ocr_state(pd.Series(["Iowa"]), resolved, _NAME_TO_CODE)
    assert grade["disagree"] == 1
    assert grade["agreement_rate"] == 0.0
    # The crosswalk's answer stands; the OCR's is reported, not written back.
    assert resolved["state"].iloc[0] == "CA"


def test_the_denominator_is_stated_when_nothing_is_comparable(crosswalks):
    resolved, _ = geo.resolve(pd.Series(["99999"]))
    grade = geo.grade_ocr_state(pd.Series(["Nowhere"]), resolved,
                                _NAME_TO_CODE)
    assert grade["comparable"] == 0
    assert grade["agreement_rate"] is None
