"""What the three hand-labelled batches actually add, and on what terms.

Two claims are under test here and they pull in opposite directions.

The first is arithmetic: the batches were commissioned as 210 UNCLASSIFIED
OSHA buildings and they are not. Most of the delivery stations in them were
classified months ago and are sitting in the two facility frames already, so
a merge that trusts the brief would double-count a building in the very
statistic the merge exists to improve. The count is asserted exactly, against
the real files, because an approximate duplicate count is the same as none.

The second is a refusal: the survivors carry an OSHA upper bound and no
opening date, `E_operating_by` cannot falsify a record that claims nothing,
and so passing that edit is not evidence of anything. The tests below pin the
vacuity down rather than letting a green edit report stand in for a date.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.common.paths import EXTERNAL, INTERIM
from siting_atlas.warehouse import batch_candidates as bc
from siting_atlas.warehouse.edits import apply_operating_by

needs_files = pytest.mark.skipif(
    not (EXTERNAL / "facility_panel" / "national_facilities.csv").exists()
    or not (EXTERNAL / "facility_panel" / "facilities.csv").exists()
    or not (INTERIM / "osha_amazon.csv").exists(),
    reason="facility frames or the OSHA extract are not placed")


@needs_files
def test_the_three_batches_hold_one_three_five_delivery_stations():
    batches = bc.load_batches()
    # 362 rows across SIX batches. Was 210 when the module hardcoded
    # BATCHES = ('1','2','3') and silently ignored the rest.
    assert len(batches) == 362
    counts = batches["facility_type"].value_counts()
    assert counts.get(bc.DELIVERY_STATION) == 135


@needs_files
def test_the_four_unknown_answers_stay_blank_and_never_become_candidates():
    """UNKNOWN is an answer. It is not a failed join and not a facility."""
    batches = bc.load_batches()
    unknown = batches[batches["label"] == "UNKNOWN"]
    # Eight UNKNOWN across six batches (four in 1-3, four more in 4-6).
    assert len(unknown) == 8
    assert (unknown["facility_type"] == "").all()
    # UNKNOWN now appears in batches 3, 5 and 6, not only 3. The
    # point of the test is that an UNKNOWN never becomes a
    # candidate, not which batch it came from.
    assert set(unknown["batch"]) <= {"3", "5", "6"}


@needs_files
def test_most_of_the_one_three_five_are_already_in_a_facility_frame():
    """The premise the batches were commissioned under does not hold.

    Matching is on the parsed ADDRESS via the project's Fellegi-Sunter
    comparator, never on a city string.
    """
    frame, report = bc.select()
    assert report["delivery_stations"] == 135
    assert report["already_in_a_frame"] == 122
    assert report["in_national"] == 98
    assert report["in_pilot"] == 24
    assert len(frame) == 13


@needs_files
def test_every_candidate_is_delivered_without_an_opening_date():
    """The decision, asserted rather than described.

    An OSHA `operating_by` is an UPPER bound. Writing it into `open_year`
    would let `models/choice.build` pick a CBP vintage that is earlier than
    the bound and later than the opening, which is the circularity the lag
    exists to prevent. The column is therefore left empty and the bound is
    carried under its own name.
    """
    frame, _ = bc.select()
    assert frame["open_year"].isna().all()
    assert frame["open_quarter"].isna().all()
    assert frame["osha_operating_by"].notna().all()


@needs_files
def test_the_candidates_add_metros_rather_than_density():
    """What the merge buys, measured before anyone spends it.

    The stated purpose was more facilities PER METRO. Every candidate lands
    in a CBSA the national frame does not already hold, so the share of
    decisions with an empty prior network goes UP.
    """
    _, report = bc.select()
    assert report["cbsas_new_to_national"] == report["cbsas"]
    assert report["first_in_metro_share_before"] == pytest.approx(0.65)
    assert report["first_in_metro_share_after"] > 0.65


def test_an_undated_candidate_cannot_fail_the_operating_by_edit():
    """A green edit report on these rows carries no information.

    `E_operating_by` compares a CLAIMED opening against the bound. A row that
    claims nothing has nothing to contradict, so it passes by construction --
    which is the reason a passing edit must not be quoted as corroboration.
    """
    frame = pd.DataFrame([{
        "facility_id": "CAND-B1-002", "site_address": "1 EXAMPLE RD",
        "city": "GOODYEAR", "state": "AZ", "zip": "85395",
        "open_q_index": float("nan")}])
    osha = pd.DataFrame([{"activity_nr": "1", "site_address": "1 EXAMPLE RD",
                          "site_city": "GOODYEAR", "site_state": "AZ",
                          "site_zip": "85395",
                          "operating_by": "1999-01-01"}])
    checked, failures = apply_operating_by(frame, osha)
    assert failures == []
    # The bound was still FOUND -- the edit matched the building and simply
    # had no claim to test it against.
    assert checked.loc[0, "osha_operating_by"] == "1999-01-01"


def test_a_review_band_link_refuses_instead_of_choosing():
    """Neither admitting nor dropping an unsure pair is defensible.

    Admit it and one building is counted twice, in the within-metro density
    this exercise exists to raise. Drop it and a real facility is deleted.
    `facility_load._refuse_unresolved` sets the precedent: stop and say so.
    """
    left = pd.DataFrame([{"site_address": "100 CANTON ST",
                          "site_city": "SALEM", "site_state": "MA",
                          "site_zip": "01970", "facility_type": "DS",
                          "batch": "9", "item": "1", "label": "DS",
                          "operating_by": "2024-01-01", "evidence": "",
                          "source_url": "", "n_inspections": "1",
                          "estab_name": ""}])
    right = pd.DataFrame([{"facility_id": "NAT-9999", "frame": "national",
                           "site_address": "100 CANTON AVE",
                           "city": "SALEM", "state": "MA", "zip": "01970"}])
    with pytest.raises(ValueError, match="clerical review"):
        bc.split_on_links(left, right)
