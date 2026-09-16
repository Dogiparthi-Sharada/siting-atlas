"""The merge entry point: two screens, one expanded panel, one artefact.

`FACILITY_PANEL_PROVENANCE` sec.19.2 records the failure this module exists
to avoid: 362 rows went out for hand-labelling and 289 of them were ALREADY
classified, because the worklist was screened on an exact address key. A
duplicate that slips through does not raise — it becomes a facility.

So the two screens, the table filter and the run stamp are asserted on a
fixture small enough to reason about by hand.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.common import log_json
from siting_atlas.warehouse import mwpvl_geo, mwpvl_merge

#: Column order of `data/interim/mwpvl_facilities.csv`.
_MWPVL_DEFAULTS = {
    "table": "08_us_delivery_station", "row": "0", "region": "California",
    "code": "DAX8", "street": "1910 E Vista Way", "city": "Vista",
    "addr_region": "California", "postcode": "92081", "sqft": "142800",
    "open_month": "10", "open_year": "2019", "open_quarter": "",
    "date_precision": "month", "description": "Delivery Station",
    "address_raw": "1910 E Vista Way, Vista, California, USA, 92081",
    "not_confirmed": "False", "delayed": "False", "cancelled": "False",
    "closed": "False", "sqft_estimated": "False", "colocated": "False",
    "rural_wagon_wheel": "False",
}

_NATIONAL_DEFAULTS = {
    "facility_id": "NAT-0001", "operator": "Amazon", "facility_type": "DS",
    "city": "VISTA", "state": "CA", "zip": "92081",
    "site_address": "1910 E VISTA WAY", "latitude": "", "longitude": "",
    "open_year": "2019", "open_quarter": "4", "close_year": "",
    "close_quarter": "", "square_feet": "", "status": "open",
    "source_url": "x", "source_type": "permit", "confidence": "high",
    "cbsa_title": "San Diego, CA",
}

#: Two MWPVL rows. The first is the same building as NAT-0001 and must be
#: screened OUT; the second is genuinely new.
_MWPVL_ROWS = (
    {"row": "0", "code": "DAX8"},
    {"row": "1", "code": "DSM5", "region": "Iowa",
     "street": "6910 SE Four Mile Drive", "city": "Ankeny",
     "addr_region": "Iowa", "postcode": "50021", "open_year": "2022",
     "open_month": "1",
     "address_raw": "6910 SE Four Mile Drive, Ankeny, Iowa, USA, 50021"},
)

#: A fulfilment centre. Not a delivery station, and merging it would put a
#: million-square-foot building into a last-mile panel without complaint.
_WRONG_CLASS = {"table": "01_us_fulfillment_center", "row": "0",
                "code": "PHX5", "street": "6835 W Buckeye Rd",
                "city": "Phoenix", "addr_region": "Arizona",
                "postcode": "85043",
                "address_raw": "6835 W Buckeye Rd, Phoenix, Arizona, "
                               "USA, 85043"}


@pytest.fixture
def merge_tree(data_root, tmp_path, monkeypatch):
    """Relocate every path the module resolved at import time.

    ``data_root`` comes first so that `edits.load_operating_bounds`, which
    reads `paths.INTERIM` at call time, looks in the empty tmp tree rather
    than at the repository's real OSHA extract.
    """
    def _build(mwpvl_rows=_MWPVL_ROWS, national_rows=({},)):
        mwpvl = tmp_path / "mwpvl_facilities.csv"
        national = tmp_path / "national_facilities.csv"
        pd.DataFrame([{**_MWPVL_DEFAULTS, **r}
                      for r in mwpvl_rows]).to_csv(mwpvl, index=False)
        pd.DataFrame([{**_NATIONAL_DEFAULTS, **r}
                      for r in national_rows]).to_csv(national, index=False)

        pd.DataFrame({
            "zcta": ["92081", "50021", "85043"],
            "county_geoid": ["06073", "19153", "04013"],
            "shared_land_area": [1.0, 1.0, 1.0],
        }).to_parquet(tmp_path / "zcta_county.parquet", index=False)
        pd.DataFrame({
            "county_geoid": ["06073", "19153", "04013"],
            "cbsa_code": ["41740", "19780", "38060"],
            "cbsa_title": ["San Diego", "Des Moines", "Phoenix"],
        }).to_parquet(tmp_path / "cbsa_county.parquet", index=False)

        monkeypatch.setattr(mwpvl_geo, "ZCTA_COUNTY",
                            tmp_path / "zcta_county.parquet")
        monkeypatch.setattr(mwpvl_geo, "CBSA_COUNTY",
                            tmp_path / "cbsa_county.parquet")
        monkeypatch.setattr(mwpvl_merge, "MWPVL", mwpvl)
        monkeypatch.setattr(mwpvl_merge, "NATIONAL", national)
        monkeypatch.setattr(mwpvl_merge, "EXPANDED",
                            tmp_path / "national_facilities_expanded.csv")
        monkeypatch.setattr(mwpvl_merge, "ARTEFACT",
                            tmp_path / "mwpvl_merge.json")
        return tmp_path
    return _build


def test_run_writes_both_artefacts_and_returns_what_it_measured(merge_tree):
    merge_tree()
    report = mwpvl_merge.run()

    assert mwpvl_merge.EXPANDED.exists()
    assert mwpvl_merge.ARTEFACT.exists()
    for key in ("mwpvl_rows_in_file", "mwpvl_rows", "new_rows_added",
                "panel_rows_before", "panel_rows_after", "cross_matches",
                "geography_mwpvl", "validation_E_operating_by",
                "facility_check", "caveats"):
        assert key in report, key


def test_the_row_arithmetic_closes(merge_tree):
    """Every MWPVL row is accounted for exactly once: wrong class, internal
    duplicate, already in the panel, held for review, or added. A count that
    does not close is a row that went somewhere nobody is looking."""
    merge_tree()
    r = mwpvl_merge.run()

    assert r["mwpvl_rows_in_file"] == r["mwpvl_rows"] \
        + r["mwpvl_rows_excluded_wrong_facility_class"]
    assert r["mwpvl_rows"] == r["internal_duplicates_dropped"] \
        + r["after_internal_dedup"]
    assert r["after_internal_dedup"] == r["already_in_panel"] \
        + r["held_for_clerical_review"] + r["new_rows_added"]
    assert r["panel_rows_after"] == r["panel_rows_before"] \
        + r["new_rows_added"]


def test_only_delivery_station_tables_are_read(merge_tree):
    """The filter is load-bearing and was added AFTER the fact. Without it a
    fulfilment centre enters a last-mile panel and nothing complains: the
    rows have the same columns and geocode perfectly well."""
    merge_tree(mwpvl_rows=(*_MWPVL_ROWS, _WRONG_CLASS))
    r = mwpvl_merge.run()

    assert r["mwpvl_rows_in_file"] == 3
    assert r["mwpvl_rows"] == 2
    assert r["mwpvl_rows_excluded_wrong_facility_class"] == 1
    expanded = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str)
    assert "85043" not in set(expanded["zip"])


def test_a_building_already_in_the_panel_is_not_added_again(merge_tree):
    """The 289-duplicate defect, in miniature. The MWPVL row spells the
    address differently from the curated one; an exact key would miss it."""
    merge_tree()
    r = mwpvl_merge.run()

    assert r["already_in_panel"] == 1
    assert "MWP-0001" in r["cross_matches"]
    assert r["cross_matches"]["MWP-0001"] == ["NAT-0001"]
    assert r["new_rows_added"] == 1

    expanded = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str)
    assert len(expanded) == 2
    assert sorted(expanded["zip"]) == ["50021", "92081"]


def test_the_two_provenances_stay_separable_in_the_output(merge_tree):
    merge_tree()
    mwpvl_merge.run()
    expanded = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str)

    assert set(expanded["source_dataset"]) == {"national_facilities",
                                               "mwpvl_2025q1"}
    # The existing schema is a PREFIX of the new one, so any reader that
    # selects the old columns by name still works.
    assert list(expanded.columns)[:19] == list(
        pd.read_csv(mwpvl_merge.NATIONAL, dtype=str).columns)


def test_the_artefact_carries_the_run_that_wrote_it(merge_tree):
    """Audit sec.6.5: `mwpvl_merge.json` was one of the 14 unstamped files."""
    merge_tree()
    mwpvl_merge.run()
    got = log_json.read_json(mwpvl_merge.ARTEFACT)
    assert got["run_id"] and got["written_at"]
    assert got["new_rows_added"] == 1


def test_two_runs_write_the_same_ids_so_a_reported_id_is_traceable(
        merge_tree):
    merge_tree()
    first = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str) \
        if mwpvl_merge.EXPANDED.exists() else None
    assert first is None
    mwpvl_merge.run()
    a = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str)["facility_id"].tolist()
    mwpvl_merge.run()
    b = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str)["facility_id"].tolist()
    assert a == b


def test_an_absent_extract_names_the_command_that_makes_it(merge_tree):
    merge_tree()
    mwpvl_merge.MWPVL.unlink()
    with pytest.raises(SystemExit, match="mwpvl_tables"):
        mwpvl_merge.run()


def test_an_absent_osha_extract_is_reported_as_unevaluated_not_as_a_pass(
        merge_tree):
    merge_tree()
    r = mwpvl_merge.run()
    validation = r["validation_E_operating_by"]
    assert validation["evaluated"] is False
    assert "CANNOT BE EVALUATED" in validation["reason"]
    assert validation["rows_it_would_have_checked"] >= 1


def test_the_edit_is_evaluated_and_reported_when_osha_is_present(merge_tree):
    """REPORT, not EXCLUDE: the pass rate is what the merge is graded on."""
    from siting_atlas.common import paths

    merge_tree()
    pd.DataFrame([{"activity_nr": "1",
                   "site_address": "6910 SE FOUR MILE DRIVE",
                   "site_city": "ANKENY", "site_state": "IA",
                   "site_zip": "50021", "operating_by": "2021-03-01"}]
                 ).to_csv(paths.INTERIM / "osha_amazon.csv", index=False)

    validation = mwpvl_merge.run()["validation_E_operating_by"]
    assert validation.get("evaluated") is not False
    # Claimed 2022Q1, proven operating by 2021-03: the date is impossible
    # against evidence from an unrelated source. It is counted, not dropped.
    expanded = pd.read_csv(mwpvl_merge.EXPANDED, dtype=str)
    assert "50021" in set(expanded["zip"])


def test_the_schema_check_is_reported_rather_than_enforced(merge_tree):
    """`facility_check` treats open_year as REQUIRED and MWPVL prints none
    on a quarter of its rows. The failure is reported so nobody discovers it
    by running --check."""
    merge_tree(mwpvl_rows=({"row": "1", "code": "DSM5", "region": "Iowa",
                            "street": "6910 SE Four Mile Drive",
                            "city": "Ankeny", "addr_region": "Iowa",
                            "postcode": "50021", "open_year": "",
                            "open_month": "", "date_precision": "none",
                            "address_raw": "6910 SE Four Mile Drive, "
                                           "Ankeny, Iowa, USA, 50021"},))
    r = mwpvl_merge.run()
    assert "passes" in r["facility_check"]
    assert "note" in r["facility_check"]
    # The undated row still entered: it supplies a location, which is what a
    # fourth capture list exists for.
    assert r["new_rows_added"] == 1


def test_main_prints_a_report_and_stamps_the_run(merge_tree, capsys):
    merge_tree()
    assert mwpvl_merge.main() == 0
    assert log_json.read_json(mwpvl_merge.ARTEFACT)["run_id"]
    assert str(mwpvl_merge.EXPANDED.name) in capsys.readouterr().out
