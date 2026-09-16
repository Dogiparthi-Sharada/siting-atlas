"""The declared edit set, and the cross-source edit that reads OSHA.

Fellegi & Holt's whole apparatus starts from a set of EDITS — logical
constraints a record must satisfy — declared in one place and checked
mechanically. Until now this project had exactly one, and it was implicit in
`facility_dedup`: two rows the matcher calls one building must agree about the
opening date. This file tests the second one, which is the first that reaches
outside the record being judged:

    E_operating_by :  quarter_start(open_q_index) <= osha_operating_by

An OSHA inspection proves the establishment existed and was operating on the
inspection date, so that date is an UPPER bound on the opening. A claimed
opening strictly after it is not less reliable — it is impossible.

The distinction from Sec. 7 matters and is the point of the module. A
reliability weight expresses a PREFERENCE between two admissible values, and
ties when the provenances match. An edit expresses a CONTRADICTION, and a
contradiction does not tie.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.common.paths import EXTERNAL, INTERIM
from siting_atlas.warehouse.edits import (
    EDIT_COLUMNS,
    EDITS,
    EXCLUDE,
    REPORT,
    check_operating_by,
    edit_by_name,
    load_operating_bounds,
)

NATIONAL = EXTERNAL / "facility_panel" / "national_facilities.csv"
PILOT = EXTERNAL / "facility_panel" / "facilities.csv"
OSHA = INTERIM / "osha_amazon.csv"

needs_osha = pytest.mark.skipif(not OSHA.exists(),
                                reason="osha_amazon.csv not built")


def facilities(*specs) -> pd.DataFrame:
    """specs = (facility_id, street, city, state, zip, open_year, quarter)."""
    frame = pd.DataFrame(
        [{"facility_id": i, "site_address": s, "city": c, "state": st,
          "zcta": z, "facility_type": "DS",
          "open_year": float(y) if y is not None else np.nan,
          "open_quarter": float(q) if q is not None else np.nan}
         for i, s, c, st, z, y, q in specs])
    frame["open_q_index"] = (frame["open_year"] * 4
                             + frame["open_quarter"].fillna(1) - 1)
    return frame


def bounds(*specs) -> pd.DataFrame:
    """specs = (activity_nr, street, city, state, zip, operating_by)."""
    return pd.DataFrame(
        [{"activity_nr": a, "site_address": s, "site_city": c,
          "site_state": st, "site_zip": z, "operating_by": d}
         for a, s, c, st, z, d in specs])


# ---------------------------------------------------------------------------
# the edit is declared, not buried
# ---------------------------------------------------------------------------
def test_the_edit_set_is_declared_in_one_place():
    names = [e.name for e in EDITS]
    assert names == sorted(set(names)), "edit names must be unique"
    assert "E_date_contradiction" in names
    assert "E_operating_by" in names


def test_every_edit_states_its_constraint_and_its_source():
    for edit in EDITS:
        assert edit.statement, f"{edit.name} has no statement"
        assert edit.fields, f"{edit.name} localises no field"
        assert edit.rationale, f"{edit.name} has no rationale"


def test_the_cross_source_edit_names_the_artefact_it_needs():
    edit = edit_by_name("E_operating_by")
    assert edit.source == "data/interim/osha_amazon.csv"
    assert edit.fields == ("open_q_index",)


# ---------------------------------------------------------------------------
# the constraint itself
# ---------------------------------------------------------------------------
def test_a_claim_after_the_proven_operating_date_fails_the_edit():
    frame, failures = check_operating_by(
        facilities(("A", "1500 E GRANTLINE RD", "TRACY", "CA", "95304",
                    2026, 3)),
        bounds(("1", "1500 EAST GRANT LINE ROAD", "TRACY", "CA", "95304",
                "2025-03-17")))
    assert frame.loc[0, "open_date_falsified"]
    assert len(failures) == 1
    assert failures[0]["facility_id"] == "A"
    assert failures[0]["osha_operating_by"] == "2025-03-17"
    # The uncorrected value is preserved, not overwritten.
    assert frame.loc[0, "open_q_index"] == 2026 * 4 + 2


def test_a_claim_inside_the_proven_operating_quarter_passes():
    """The boundary case, and the reason the edit compares QUARTER STARTS.

    Portland's surviving record claims 2017Q4 and OSHA proves the building was
    operating on 2017-12-21 — inside that same quarter. An opening on
    2017-10-01 is consistent with both, so nothing is falsified. Comparing
    quarter ENDS would have thrown the true record away.
    """
    frame, failures = check_operating_by(
        facilities(("A", "3610 NW SAINT HELENS RD", "PORTLAND", "OR", "97210",
                    2017, 4)),
        bounds(("1", "3610 NW ST HELENS RD", "PORTLAND", "OR", "97210",
                "2017-12-21")))
    assert not frame.loc[0, "open_date_falsified"]
    assert failures == []


def test_the_address_matcher_bridges_the_two_spellings():
    """City strings differ — HOLLYGLEN against HAWTHORNE, one neighbourhood
    inside the other — so a city join finds nothing. The Fellegi-Sunter
    matcher works on the parsed address and finds it."""
    frame, failures = check_operating_by(
        facilities(("A", "2815 W EL SEGUNDO BL", "HAWTHORNE", "CA", "90250",
                    2020, 2)),
        bounds(("1", "2815 W. EL SEGUNDO BLVD.", "HOLLYGLEN", "CA", "90250",
                "2017-12-29")))
    assert frame.loc[0, "open_date_falsified"]
    assert failures[0]["osha_operating_by"] == "2017-12-29"


def test_a_building_osha_never_inspected_is_not_judged():
    frame, failures = check_operating_by(
        facilities(("A", "1 MAIN ST", "TRACY", "CA", "95304", 2026, 3)),
        bounds(("1", "999 ELSEWHERE AVE", "TRACY", "CA", "95304",
                "2015-01-01")))
    assert not frame.loc[0, "open_date_falsified"]
    assert pd.isna(frame.loc[0, "osha_operating_by"])
    assert failures == []


def test_an_undated_row_cannot_fail_a_date_edit():
    frame, failures = check_operating_by(
        facilities(("A", "1 MAIN ST", "TRACY", "CA", "95304", None, None)),
        bounds(("1", "1 MAIN STREET", "TRACY", "CA", "95304", "2015-01-01")))
    assert not frame.loc[0, "open_date_falsified"]
    assert failures == []


def test_the_tightest_bound_wins_when_a_site_was_inspected_twice():
    frame, _ = check_operating_by(
        facilities(("A", "1 MAIN ST", "TRACY", "CA", "95304", 2021, 1)),
        bounds(("1", "1 MAIN ST", "TRACY", "CA", "95304", "2022-06-01"),
               ("2", "1 MAIN STREET", "TRACY", "CA", "95304", "2019-02-02")))
    assert frame.loc[0, "osha_operating_by"] == "2019-02-02"
    assert frame.loc[0, "open_date_falsified"]


def test_the_edit_adds_only_annotations_and_never_a_value():
    """Both added columns describe the record; neither replaces anything in
    it. That is what makes the result reversible by dropping two columns."""
    before = facilities(("A", "1 MAIN ST", "TRACY", "CA", "95304", 2026, 3))
    after, _ = check_operating_by(
        before, bounds(("1", "1 MAIN ST", "TRACY", "CA", "95304",
                        "2015-01-01")))
    assert set(after.columns) - set(before.columns) == set(EDIT_COLUMNS)
    assert after[list(before.columns)].equals(before)


def test_no_bounds_at_all_leaves_the_edit_unevaluated():
    frame, failures = check_operating_by(
        facilities(("A", "1 MAIN ST", "TRACY", "CA", "95304", 2026, 3)), None)
    assert "open_date_falsified" in frame.columns
    assert not frame["open_date_falsified"].any()
    assert failures == []


# ---------------------------------------------------------------------------
# disposition: flagged and excluded, never overwritten
# ---------------------------------------------------------------------------
def test_the_dispositions_are_the_two_van_den_broeck_allows():
    assert {EXCLUDE, REPORT} == {"exclude", "report"}


@needs_osha
def test_the_real_bounds_file_loads():
    frame = load_operating_bounds()
    assert frame is not None and len(frame) > 400
    assert {"site_address", "operating_by"} <= set(frame.columns)


# ---------------------------------------------------------------------------
# the real files
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not NATIONAL.exists(), reason="national panel not placed")
@needs_osha
def test_the_edit_falsifies_exactly_four_national_records():
    """Three are one half of a contradicting pair; the fourth is a lone row.

    All four claim an opening LATER than the date OSHA proves the building was
    already operating. That every deviation from the OSHA quarter runs in the
    impossible direction, four times out of four, is the evidence that these
    are derivation errors rather than independently researched dates.
    """
    raw = pd.read_csv(NATIONAL, dtype=str)
    frame = raw.assign(
        open_year=pd.to_numeric(raw["open_year"]),
        open_quarter=pd.to_numeric(raw["open_quarter"]))
    frame["open_q_index"] = (frame["open_year"] * 4
                             + frame["open_quarter"].fillna(1) - 1)
    out, failures = check_operating_by(frame, load_operating_bounds())

    assert {f["facility_id"] for f in failures} == {
        "NAT-0011", "NAT-0026", "NAT-0036", "NAT-0079"}
    # Every one of the 104 is matched to an OSHA building, which is itself the
    # finding: the national panel was BUILT from this extract, so the edit is
    # an internal consistency check and not independent corroboration.
    assert out["osha_operating_by"].notna().all()


@pytest.mark.skipif(not PILOT.exists(), reason="pilot panel not placed")
@needs_osha
def test_the_pilot_panel_has_one_violation_and_it_is_reported_not_enforced():
    """DS-032, Austin. Found by this edit, NOT acted on.

    Excluding it would take Austin's only building out of the fitted frame and
    move published numbers (1,257 ever-enabled ZCTAs, 39 usable events). That
    is a decision for the inspirator, so the pilot load runs the edit in
    REPORT disposition and this test pins the finding rather than the fix.
    """
    from siting_atlas.warehouse.facility_load import load_facilities

    frame = load_facilities()
    assert len(frame) == 43, "the pilot load must not shrink"
    violations = frame.loc[frame["open_date_falsified"], "facility_id"]
    assert list(violations) == ["DS-032"]
