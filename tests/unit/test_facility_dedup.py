"""Contradicting facility records: found, bounded, and never silently picked.

`docs/data/DATA_QUALITY.md` F4 names the missing test exactly: the matcher
finds three pairs in `national_facilities.csv` at score 1.000, the pairs
disagree about the OPENING DATE by 10, 6 and 3 quarters, and "the test that
would fail is not written". This is that test.

It fails on the pre-fix code because `adjudicate` did not exist: 104 rows went
into `enabled_flags` as 104 facilities and `min(open_q_index)` resolved each
conflict in the same direction without recording that there was one.

The resolution rule is Fellegi & Holt Sec. 7: an a priori reliability weight on
the PROVENANCE of each date, used only where the two provenances differ.
Where they tie — which is all three known pairs, all six rows being
`source_type=permit` — Sec. 1 option 2 applies ("avoid 'manufacturing' data
instead of collecting it") and nothing is picked.
"""

from __future__ import annotations

import csv

import numpy as np
import pandas as pd
import pytest

from siting_atlas.common.paths import EXTERNAL
from siting_atlas.warehouse.facility_dedup import (
    ADJUDICATED_COLUMNS,
    DATE_RELIABILITY,
    adjudicate,
)

#: The three pairs, with the gap in quarters the audit measured.
KNOWN_CONTRADICTIONS = {
    ("NAT-0011", "NAT-0012"): 10,
    ("NAT-0025", "NAT-0026"): 6,
    ("NAT-0078", "NAT-0079"): 3,
}


def rows(*specs, source_types=None) -> pd.DataFrame:
    """specs = (facility_id, street, city, state, zip, open_year, quarter)."""
    frame = pd.DataFrame(
        [{"facility_id": i, "site_address": s, "city": c, "state": st,
          "zcta": z, "facility_type": "DS", "open_year": float(y),
          "open_quarter": float(q)} for i, s, c, st, z, y, q in specs])
    frame["source_type"] = source_types or ["permit"] * len(frame)
    frame["open_quarter_imputed"] = False
    frame["open_q_index"] = frame["open_year"] * 4 + frame["open_quarter"] - 1
    frame["close_q_index"] = np.inf
    return frame


# ---------------------------------------------------------------------------
# the no-op case, which is what the delivered file actually is
# ---------------------------------------------------------------------------
def test_distinct_buildings_are_left_alone():
    frame, report = adjudicate(rows(
        ("A", "1555 N CHRISMAN RD", "TRACY", "CA", "95304", 2020, 1),
        ("B", "1555 S CHRISMAN RD", "TRACY", "CA", "95304", 2022, 3)))
    assert len(frame) == 2
    assert report == []
    assert not frame["open_date_contradicted"].any()
    # The bounds collapse onto the value, so no consumer needs a branch.
    assert frame["open_q_index_lower"].equals(frame["open_q_index"])
    assert frame["open_q_index_upper"].equals(frame["open_q_index"])


def test_every_adjudicated_column_exists_even_with_nothing_to_adjudicate():
    frame, _ = adjudicate(rows(
        ("A", "1 MAIN ST", "TRACY", "CA", "95304", 2020, 1)))
    for column in ADJUDICATED_COLUMNS:
        assert column in frame.columns


def test_a_file_with_no_site_address_matches_nothing():
    """Two rows in one ZIP are not one building. Degrading to 'no pairs' is
    the safe direction; degrading to 'all one building' would delete a real
    facility and its event with it."""
    frame = rows(("A", "", "TRACY", "CA", "95304", 2020, 1),
                 ("B", "", "TRACY", "CA", "95304", 2022, 3))
    out, report = adjudicate(frame.drop(columns=["site_address"]))
    assert len(out) == 2
    assert report == []


# ---------------------------------------------------------------------------
# the contradiction
# ---------------------------------------------------------------------------
def test_one_building_on_two_rows_is_collapsed_to_an_interval():
    """The Hawthorne pair. Both rows are permits, so nothing ranks them and
    no date is manufactured — the interval is recorded and the operative
    value is left NaN."""
    frame, report = adjudicate(rows(
        ("A", "2815 W EL SEGUNDO BL", "HAWTHORNE", "CA", "90250", 2020, 2),
        ("B", "2815 W. EL SEGUNDO BLVD.", "HOLLYGLEN", "CA", "90250",
         2017, 4)))

    assert len(frame) == 1, "the same building must not be two facilities"
    kept = frame.iloc[0]
    assert kept["open_date_contradicted"]
    assert kept["open_date_unresolved"]
    assert kept["open_date_resolved_by"] == ""
    assert kept["open_q_index_lower"] == 2017 * 4 + 3
    assert kept["open_q_index_upper"] == 2020 * 4 + 1
    assert pd.isna(kept["open_q_index"]), (
        "min() is biased early by construction; a tie must not be resolved "
        "by a rule at all")
    assert kept["duplicate_of"] == "B"
    assert report[0]["quarters_apart"] == 10
    assert report[0]["unresolved"]


def test_a_more_reliable_provenance_settles_the_date():
    """Fellegi & Holt Sec. 7: where the edits leave a choice, an a priori
    reliability weight selects. A press release dates the opening; a permit
    is filed before the building operates."""
    frame, report = adjudicate(rows(
        ("A", "2815 W EL SEGUNDO BL", "HAWTHORNE", "CA", "90250", 2020, 2),
        ("B", "2815 W. EL SEGUNDO BLVD.", "HOLLYGLEN", "CA", "90250",
         2017, 4),
        source_types=["press_release", "permit"]))

    kept = frame.iloc[0]
    assert kept["open_date_contradicted"]
    assert not kept["open_date_unresolved"]
    assert kept["open_date_resolved_by"] == "source_reliability"
    assert kept["open_q_index"] == 2020 * 4 + 1, (
        "the press release wins, and it happens to be the LATER date — a "
        "rule that took the earlier one would have gone the other way")
    assert report[0]["winner"] == "press_release"
    # The bounds survive the resolution, so it stays reversible.
    assert kept["open_q_index_lower"] == 2017 * 4 + 3
    assert kept["open_q_index_upper"] == 2020 * 4 + 1


def test_an_unknown_provenance_cannot_outrank_a_known_one():
    frame, _ = adjudicate(rows(
        ("A", "1 MAIN ST", "TRACY", "CA", "95304", 2020, 2),
        ("B", "1 MAIN STREET", "TRACY", "CA", "95304", 2017, 4),
        source_types=["", "permit"]))
    kept = frame.iloc[0]
    assert kept["open_q_index"] == 2017 * 4 + 3
    assert kept["open_date_resolved_by"] == "source_reliability"


def test_the_reliability_order_is_the_one_the_project_already_declared():
    """Not a new ranking invented here: `ingest/facility_check` already
    declares this order and calls it 'how much weight a row deserves'."""
    from siting_atlas.ingest.facility_check import VALID_SOURCE_TYPES

    assert set(DATE_RELIABILITY) == VALID_SOURCE_TYPES
    assert DATE_RELIABILITY[0] == "press_release"
    assert DATE_RELIABILITY[-1] == "other"


def test_two_rows_that_agree_are_a_duplicate_not_a_contradiction():
    """The distinction Rahm & Do draw, and it changes the treatment: a
    duplicate can be deleted, a contradiction has to be bounded."""
    frame, report = adjudicate(rows(
        ("A", "3610 NW SAINT HELENS RD", "PORTLAND", "OR", "97210", 2017, 4),
        ("B", "3610 NW ST HELENS RD", "PORTLAND", "OR", "97210", 2017, 4)))
    assert len(frame) == 1
    assert not frame.iloc[0]["open_date_contradicted"]
    assert report[0]["quarters_apart"] == 0


# ---------------------------------------------------------------------------
# the real file — the check the audit says nobody wrote
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not (EXTERNAL / "facility_panel" / "national_facilities.csv").exists(),
    reason="national_facilities.csv not placed")
def test_the_national_panel_holds_exactly_three_contradicting_pairs():
    path = EXTERNAL / "facility_panel" / "national_facilities.csv"
    with open(path, encoding="utf-8-sig", newline="") as fh:
        raw = list(csv.DictReader(fh))

    frame = rows(*[(r["facility_id"], r["site_address"], r["city"],
                    r["state"], r["zip"], int(r["open_year"]),
                    int(r["open_quarter"])) for r in raw],
                 source_types=[r["source_type"] for r in raw])
    out, report = adjudicate(frame)

    found = {tuple(e["facility_ids"]): e["quarters_apart"]
             for e in report if e["contradicted"]}
    assert found == KNOWN_CONTRADICTIONS
    assert len(out) == len(raw) - 3, "104 rows describe 101 buildings"
    # All six rows are source_type=permit, so no reliability weight separates
    # any pair and all three are human work, not rule work.
    assert all(e["unresolved"] for e in report if e["contradicted"])
    assert all(e["source_types"] == ["permit"]
               for e in report if e["contradicted"])


@pytest.mark.skipif(
    not (EXTERNAL / "facility_panel" / "facilities.csv").exists(),
    reason="facilities.csv not placed")
def test_the_delivered_pilot_panel_has_nothing_to_adjudicate():
    """The file the pipeline actually reads is clean, which is why none of
    this moves a published number today. Asserted rather than assumed, so
    that a future batch cannot quietly introduce one."""
    from siting_atlas.warehouse.facility_load import load_facilities

    frame = load_facilities()
    assert not frame["open_date_contradicted"].any()
    assert not frame["open_date_unresolved"].any()
    assert frame["duplicate_of"].isna().all()


def test_an_unresolved_contradiction_refuses_the_load(tmp_path):
    """The build must not ship a manufactured event date. Three permit
    lookups is the correct next action, and a fatal error is what causes
    them; a warning would be read once and forgotten."""
    from siting_atlas.warehouse.facility_load import load_facilities

    csv = tmp_path / "facilities.csv"
    csv.write_text(
        "facility_id,operator,facility_type,city,state,zip,site_address,"
        "open_year,open_quarter,source_url,source_type\n"
        "A,Amazon,DS,HAWTHORNE,CA,90250,2815 W EL SEGUNDO BL,2020,2,"
        "https://x.test,permit\n"
        "B,Amazon,DS,HOLLYGLEN,CA,90250,2815 W. EL SEGUNDO BLVD.,2017,4,"
        "https://x.test,permit\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contradicting facility record"):
        load_facilities(csv)


def test_a_resolvable_contradiction_loads(tmp_path):
    """The same file with one provenance that outranks the other must load,
    or the gate is just 'never have two rows'."""
    from siting_atlas.warehouse.facility_load import load_facilities

    csv = tmp_path / "facilities.csv"
    csv.write_text(
        "facility_id,operator,facility_type,city,state,zip,site_address,"
        "open_year,open_quarter,source_url,source_type\n"
        "A,Amazon,DS,HAWTHORNE,CA,90250,2815 W EL SEGUNDO BL,2020,2,"
        "https://x.test,press_release\n"
        "B,Amazon,DS,HOLLYGLEN,CA,90250,2815 W. EL SEGUNDO BLVD.,2017,4,"
        "https://x.test,permit\n", encoding="utf-8")

    frame = load_facilities(csv)
    assert len(frame) == 1
    assert frame.iloc[0]["open_q_index"] == 2020 * 4 + 1
