"""The matcher must collapse the same building and split different ones.

Every UNDER-COLLAPSE case here is a pair that the old string-equality
matcher left as two facilities. Every OVER-COLLAPSE case is a pair that a
naive fix - "just ignore directionals" - would wrongly merge, which is the
worse error: a spurious row is visible in a count, a wrong merge deletes a
real facility and nothing ever notices.
"""

import pytest

from siting_atlas.common.linkage import (
    MATCH,
    NONMATCH,
    REVIEW,
    LinkRecord,
    compare,
    jaro,
    jaro_winkler,
)
from siting_atlas.common.linkage_group import link


def rec(rid, street, city="X", state="ZZ", zipcode="00000", code=""):
    return LinkRecord.build(rid, street, city, state, zipcode, code)


# --- the string comparator, Winkler RR99-04 section 2.1 -----------------

def test_jaro_endpoints():
    assert jaro("ABC", "ABC") == 1.0
    assert jaro("ABC", "XYZ") == 0.0
    assert jaro("", "ABC") == 0.0


def test_jaro_winkler_rewards_an_agreeing_prefix():
    """Pollock and Zamora, cited in 2.1: keypunch errors skew rightward.

    So a pair that agrees at the front is likelier to be one string than a
    pair that agrees at the back, and Winkler's bonus has to reflect that.
    """
    front = jaro_winkler("BABBITT", "BABBIT")     # typo at the end
    back = jaro_winkler("ROSWELL", "POSWELL")     # typo at the start
    assert front > back
    assert jaro_winkler("ROSWELL", "POSWELL") == pytest.approx(jaro(
        "ROSWELL", "POSWELL"))


def test_transpositions_lower_the_score():
    """RR99-04's printed formula adds the transposition term, which would
    make a more-transposed pair score HIGHER. That is a transcription slip
    in the paper; the term is subtractive and this pins it down."""
    assert jaro("MARTHA", "MARHTA") < 1.0
    assert jaro("MARTHA", "MARHTA") > 0.9


# --- UNDER-COLLAPSE: the failures reported against the old matcher -------

@pytest.mark.parametrize(("a", "b", "note"), [
    ("315 SHUKSAN WAY DWS4", "315 SHUKSAN WAY",
     "facility code typed into the street field"),
    ("4616-6 HOWARD LANE", "4616-6 WEST HOWARD LANE",
     "leading directional present on one side only"),
    ("2801 S. WESTERN AVENUE", "2801 S WESTERN AVE.",
     "the same suffix spelled two ways"),
    ("5509 MILITARY RD.", "5509 MILITARY RD E,",
     "trailing directional on one side only"),
    ("1901 140TH AVE E BFI7", "1901 140TH AVENUE E", "code plus suffix"),
    ("1155 BABBITT ROAD", "1155 BABBIT ROAD", "a one-character typo"),
    ("1500 EAST GRANT LINE ROAD", "1500 E GRANTLINE RD", "token split"),
    ("3680 LANGLEY DR", "3680 LANGLEY DRIVE SUITE 100", "a suite number"),
    ("21005 64TH AVENUE S", "21005 64TH AVENUE S ATTN JESSICA ANG",
     "a mail-routing instruction"),
    ("2600 N NORMANDY BLVD.", "2600 N NORMANDY BLVD, DELTONA, FL 32725",
     "city, state and ZIP re-typed into the street field"),
])
def test_same_building_matches(a, b, note):
    assert compare(rec("a", a), rec("b", b)).call == MATCH, note


def test_chicago_pair_matches_across_a_zip_disagreement():
    """OSHA ZIPs are unreliable, so a ZIP disagreement is not a veto.

    City still corroborates here. When NEITHER corroborates the pair goes to
    review instead - see `test_no_corroboration_goes_to_review`.
    """
    got = compare(rec("a", "2801 S. WESTERN AVENUE", "CHICAGO", "IL",
                      "60608"),
                  rec("b", "2801 S WESTERN AVE.", "CHICAGO", "IL", "60609"))
    assert got.call == MATCH


def test_city_disagreement_alone_does_not_block_a_match():
    """One building, two city names: 8727 Harney Rd is Tampa AND Temple
    Terrace depending on who typed it. The shared ZIP carries it."""
    got = compare(rec("a", "8727 HARNEY ROAD", "TAMPA", "FL", "33637"),
                  rec("b", "8727 HARNEY ROAD", "TEMPLE TERRACE", "FL",
                      "33637"))
    assert got.call == MATCH


# --- OVER-COLLAPSE: merges that would delete a real facility -------------

def test_conflicting_directionals_are_different_streets():
    """1555 N and 1555 S Chrisman Rd are two real Tracy CA facilities."""
    got = compare(rec("a", "1555 N CHRISMAN ROAD", "TRACY", "CA", "95304"),
                  rec("b", "1555 S CHRISMAN RD", "TRACY", "CA", "95304"))
    assert got.call == NONMATCH


def test_bare_record_does_not_bridge_two_conflicting_ones():
    """The transitive-closure trap, and the reason grouping is checked.

    A agrees with B and A agrees with C, but B contradicts C. Connected
    components would return one building. The truth is at least two, so the
    closure must be dissolved rather than trusted.
    """
    recs = [rec("0", "1555 CHRISMAN RD", "TRACY", "CA", "95376"),
            rec("1", "1555 N CHRISMAN ROAD", "TRACY", "CA", "95304"),
            rec("2", "1555 S CHRISMAN RD", "TRACY", "CA", "95304")]
    grouping = link(recs)
    assert grouping.n_groups == 3, "N and S Chrisman must not be merged"
    assert len(grouping.ambiguous) == 3


def test_different_house_number_never_matches():
    assert compare(rec("a", "1800 140TH AVE E"),
                   rec("b", "1901 140TH AVE E")).call == NONMATCH


def test_different_street_on_the_same_house_number_never_matches():
    """50 New Canton Way and 50 Central Avenue are both real New Jersey
    addresses that share a house number. At Winkler's Table 1 threshold of
    0.6 - which is for person names - these would merge."""
    assert compare(rec("a", "50 CENTRAL AVENUE", "KEARNY", "NJ", "07032"),
                   rec("b", "50 NEW CANTON WAY", "ROBBINSVILLE", "NJ",
                       "08691")).call == NONMATCH


def test_different_building_code_is_decisive():
    """The code is Amazon's own identifier, so it settles it both ways."""
    assert compare(rec("a", "1 X RD", code="BFI7"),
                   rec("b", "1 X RD", code="DWS4")).call == NONMATCH
    assert compare(rec("a", "", "SEATTLE", "WA", "98101", code="BFI7"),
                   rec("b", "", "SEATTLE", "WA", "98101",
                       code="BFI7")).call == MATCH


def test_a_state_disagreement_is_always_a_nonmatch():
    assert compare(rec("a", "1 MAIN ST", state="WA"),
                   rec("b", "1 MAIN ST", state="OR")).call == NONMATCH


# --- the review band: Fellegi-Sunter eq. (4)'s middle region -------------

def test_no_corroboration_goes_to_review():
    """Identical street, but neither ZIP nor city agrees. Not decidable."""
    got = compare(rec("a", "2400 MCCLELLAN PARK DRIVE", "MCCLELLAN", "CA",
                      "95652"),
                  rec("b", "2400 MCCLELLAN PARK DRIVE", "SACRAMENTO", "CA",
                      "95838"))
    assert got.call == REVIEW


def test_suffix_conflict_goes_to_review():
    """Same number and name, different street TYPE. Usually a typo,
    occasionally two streets. We cannot tell, so we do not pick."""
    got = compare(rec("a", "7001 ZEUBER DR", "LITTLE ROCK", "AR", "72206"),
                  rec("b", "7001 ZEUBER ROAD", "LITTLE ROCK", "AR", "72206"))
    assert got.call == REVIEW


def test_osm_row_with_no_street_is_never_auto_merged():
    """The OpenStreetMap export has coordinates and a code but no street.

    32 of its 148 (state, ZIP) cells hold more than one station, so city and
    ZIP alone cannot identify a building. Without a code this is review.
    """
    got = compare(rec("a", "", "CHICAGO", "IL", "60609"),
                  rec("b", "1234 S SOMETHING AVE", "CHICAGO", "IL", "60609"))
    assert got.call == REVIEW


def test_review_pairs_do_not_silently_become_groups():
    """A review verdict must leave the two records separate."""
    recs = [rec("0", "7001 ZEUBER DR", "LITTLE ROCK", "AR", "72206"),
            rec("1", "7001 ZEUBER ROAD", "LITTLE ROCK", "AR", "72206")]
    grouping = link(recs)
    assert grouping.n_groups == 2
    assert len(grouping.review) == 1


def test_delivered_panel_holds_one_row_per_building():
    """The facility panel must not describe one building twice.

    A duplicate row is not cosmetic here: `enabled_flags` turns each row into
    a served-ZCTA interval, so the same building counted twice can switch a
    ZIP on earlier than any real facility did, and the hazard model then fits
    to an event that never happened.

    This file was deduplicated by hand in September 2026, before there was a
    matcher able to check the work. Now there is one, so the check is a
    contract rather than a memory. Running the same check over
    `national_facilities.csv` finds three surviving duplicate pairs - see
    docs/data/FACILITY_PANEL_PROVENANCE.md Sec. 12.5 - which is exactly why
    this belongs in the suite and not in a one-off script.
    """
    import csv as _csv

    from siting_atlas.common.paths import EXTERNAL

    path = EXTERNAL / "facility_panel" / "facilities.csv"
    if not path.exists():          # the panel is an optional hand-placed file
        pytest.skip(f"{path} not present")
    with open(path, encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    recs = [LinkRecord.build(r["facility_id"], r["site_address"], r["city"],
                             r["state"], r["zip"]) for r in rows]
    grouping = link(recs)
    dupes = [[rows[i]["facility_id"] for i in g]
             for g in grouping.groups if len(g) > 1]
    assert not dupes, f"same building on more than one row: {dupes}"
