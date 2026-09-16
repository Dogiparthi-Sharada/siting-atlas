"""Promoting the national frame: what the edit unblocks, measured.

`facility_load.load_facilities` refuses a file carrying an unresolved
contradiction, and that refusal is correct — it is what stops a manufactured
event date reaching the target. The three contradictions in
`national_facilities.csv` are what kept a 100-building, 62-CBSA frame out of
the warehouse while the model was fitted on 43 buildings in 10 metros.

The cross-source edit removes the contradictions by falsifying one side of
each, so the refusal never fires and nothing about it is weakened. These tests
assert both halves: the file loads, and the gate is still armed.
"""

from __future__ import annotations

import json

import pytest

from siting_atlas.common.paths import EXTERNAL, INTERIM
from siting_atlas.warehouse.national import (
    NATIONAL_PATH,
    load_national,
    summarise,
)

needs_files = pytest.mark.skipif(
    not NATIONAL_PATH.exists()
    or not (INTERIM / "osha_amazon.csv").exists(),
    reason="national panel or OSHA extract not placed")


@needs_files
def test_the_national_panel_loads_once_the_edit_has_run():
    frame = load_national()
    assert len(frame) == 100, (
        "104 rows describe 101 buildings; the edit falsifies one lone record "
        "as well as one half of each contradicting pair")
    assert not frame["open_date_unresolved"].any()
    assert frame["open_q_index"].notna().all()


@needs_files
def test_the_surviving_record_of_each_pair_is_the_one_osha_permits():
    frame = load_national().set_index("facility_id")
    for kept, dropped, quarter in (("NAT-0012", "NAT-0011", 2017 * 4 + 3),
                                   ("NAT-0025", "NAT-0026", 2025 * 4 + 0),
                                   ("NAT-0078", "NAT-0079", 2017 * 4 + 3)):
        assert kept in frame.index
        assert dropped not in frame.index
        assert frame.loc[kept, "open_q_index"] == quarter
        # Resolved by the edit, so no reliability weight was consulted and
        # none was needed. The tie that blocked the load is gone, not broken.
        assert not frame.loc[kept, "open_date_contradicted"]


@needs_files
def test_the_refusal_still_fires_on_a_contradiction_the_edit_cannot_reach():
    """The gate must not have been traded for one file's convenience."""
    from siting_atlas.warehouse.facility_load import load_facilities

    csv = EXTERNAL / "facility_panel" / "_test_unresolved.csv"
    csv.write_text(
        "facility_id,operator,facility_type,city,state,zip,site_address,"
        "open_year,open_quarter,source_url,source_type\n"
        "A,Amazon,DS,NOWHERE,ND,58001,1 NOWHERE ST,2020,2,"
        "https://x.test,permit\n"
        "B,Amazon,DS,NOWHERE,ND,58001,1 NOWHERE STREET,2017,4,"
        "https://x.test,permit\n", encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="contradicting facility record"):
            load_facilities(csv)
    finally:
        csv.unlink()


@needs_files
def test_a_falsified_lone_record_costs_a_building_but_no_metro():
    """NAT-0036, Temple Terrace FL. It has no twin, so excluding it deletes a
    real building rather than resolving a disagreement. Tampa keeps four other
    stations, so no CBSA is lost — which is the measurement that makes the
    exclusion arguable rather than assumed."""
    frame = load_national()
    assert "NAT-0036" not in set(frame["facility_id"])
    tampa = frame["cbsa_title"].str.startswith("Tampa")
    assert int(tampa.sum()) == 4


@needs_files
def test_the_exclusions_are_written_to_an_artefact_not_just_logged(tmp_path):
    out = tmp_path / "national_panel.json"
    report = summarise(out)
    assert out.exists()
    written = json.loads(out.read_text())
    assert written == report

    excluded = {e["facility_id"]: e for e in report["excluded"]}
    assert set(excluded) == {"NAT-0011", "NAT-0026", "NAT-0036", "NAT-0079"}
    for entry in excluded.values():
        # Van den Broeck's reversibility: the uncorrected value is kept.
        assert entry["claimed_open"]
        assert entry["osha_operating_by"]
        assert entry["edit"] == "E_operating_by"


@needs_files
def test_the_summary_measures_the_frame_rather_than_asserting_it(tmp_path):
    report = summarise(tmp_path / "n.json")
    assert report["rows_in_file"] == 104
    assert report["buildings"] == 100
    assert report["cbsas"] == 62
    # The pilot feature panel runs 2018Q1-2025Q4; a building outside it cannot
    # contribute an event to anything fitted on that panel.
    window = report["in_panel_window"]
    assert window["first_year"] == 2018 and window["last_year"] == 2025
    assert window["buildings"] == 81
    assert window["cbsas"] == 52
    assert window["events"] == 80
    assert window["independent_episodes"] == 79


@needs_files
def test_the_power_verdict_flips_on_the_larger_frame(tmp_path):
    """The reason any of this is worth doing. Reported, never refitted."""
    power = summarise(tmp_path / "n.json")["power"]
    assert power["n_parameters"] == 5
    assert power["events_per_parameter_effective"] == 15.8
    assert power["events_per_parameter_optimistic"] == 16.0
    assert power["floor"] == 10.0
    assert power["meets_floor"]


@needs_files
def test_no_coordinate_survives_and_the_report_says_so(tmp_path):
    """Both facility files are 0% populated on latitude/longitude. Distance
    covariates fall back to ZCTA centroids; this is reported, not geocoded."""
    report = summarise(tmp_path / "n.json")
    assert report["coordinates_present"] == 0
