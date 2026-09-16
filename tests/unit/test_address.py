"""Standardisation must put components in fixed locations, per Winkler 2.3.

The cases here are all real values from the 516-address OSHA extract. They
are grouped by the defect each one used to cause, so a failure names the
thing that broke rather than just an address.
"""

import pytest

from siting_atlas.common.address import (
    normalise_address,
    parse_address,
)


@pytest.mark.parametrize(("text", "field", "want"), [
    # The facility code an inspector typed into the street box. It must come
    # out of `street` or the address never matches its own twin - and it
    # must land in `code`, not the bin, because it is the only identifier
    # shared with the OpenStreetMap export.
    ("315 SHUKSAN WAY DWS4", "code", "DWS4"),
    ("315 SHUKSAN WAY DWS4", "street", "SHUKSAN"),
    ("1901 140TH AVE E BFI7", "code", "BFI7"),
    ("20526 59TH PLACE SOUTH BF15", "code", "BF15"),
    # Typed with a space, after the suffix, so it is past the address proper.
    ("3050 GATEWAY COMMERCE CENTER DR S STL 4", "code", "STL4"),
    # Directionals occupy their own slots, never the street name.
    ("4616-6 WEST HOWARD LANE", "predir", "W"),
    ("4616-6 HOWARD LANE", "predir", ""),
    ("5509 MILITARY RD E,", "postdir", "E"),
    ("4905 DERRICK ROAD SOUTHWEST", "postdir", "SW"),
    # Suffix folded to one spelling.
    ("2801 S. WESTERN AVENUE", "suffix", "AVE"),
    ("2801 S. WESTERN AVE.", "suffix", "AVE"),
    # Tenant-level detail parsed out of the street.
    ("3680 LANGLEY DRIVE SUITE 100", "unit", "100"),
    ("7555 AIRPORT WAY SW #6162", "unit", "6162"),
    ("100 W THOMAS P ECHOLS LN 3", "unit", "3"),
    # The whole address re-typed into a field that already has city/ST/ZIP.
    ("2600 N NORMANDY BLVD, DELTONA, FL 32725", "street", "NORMANDY"),
    # Mail routing is about a person, not a place.
    ("21005 64TH AVENUE S ATTN JESSICA ANG", "street", "64TH"),
    # Business name before the house number.
    ("AMAZON.COM BUILDING, 1901 MEADOWVILLE TECH", "house", "1901"),
    # Hyphenated house number survives whole, and blocks on its digits.
    ("4616-6 HOWARD LANE", "house", "4616-6"),
])
def test_component_lands_in_its_own_slot(text, field, want):
    assert getattr(parse_address(text), field) == want


def test_house_number_blocks_on_leading_digits():
    """"4616-6" and "4616" must reach the same block or never be compared."""
    assert parse_address("4616-6 HOWARD LN").number == "4616"
    assert parse_address("4616 HOWARD LN").number == "4616"


@pytest.mark.parametrize(("a", "b"), [
    # Tokenised two ways. Only the de-spaced core makes these comparable.
    ("1500 EAST GRANT LINE ROAD", "1500 E GRANTLINE RD"),
    ("4900 WEST ELK HORN BLVD.", "4900 W. ELKHORN BLVD"),
    ("1 CENTER POINT BOULEVARD", "1 CENTERPOINT BLVD."),
    ("550 OAKRIDGE ROAD", "550 OAK RIDGE ROAD"),
])
def test_despaced_street_core_agrees(a, b):
    assert parse_address(a).core == parse_address(b).core


def test_saint_is_not_street():
    """SAINT folds to ST, but only where ST cannot mean STREET.

    "3610 NW SAINT HELENS RD" and "3610 NW ST HELENS RD" are one road in
    Portland. Folding blindly would let the parser read SAINT as a street
    type and throw away the street name.
    """
    a, b = (parse_address("3610 NW SAINT HELENS RD"),
            parse_address("3610 NW ST HELENS RD"))
    assert a.street == b.street == "ST HELENS"
    assert a.suffix == b.suffix == "RD"


def test_operator_name_is_not_stripped_when_it_is_the_street():
    """ZAPPOS.COM BLVD is a real street in Shepherdsville KY.

    The rule that deletes "AMAZON ... SORTATION CENTER" trailing noise must
    not fire before a street suffix has been seen, or it eats the street.
    """
    kept = parse_address("376 ZAPPOS.COM BOULEVARD")
    assert kept.street == "ZAPPOS COM"
    assert kept.suffix == "BLVD"
    cut = parse_address("4905 DERRICK ROAD SW AMAZON MGE8 SORTATION CENTER")
    assert cut.street == "DERRICK"


def test_center_is_part_of_street_names_here():
    """CENTER must not be folded to CTR - see the table's own comment."""
    assert parse_address("1 CENTER POINT BLVD").core == "CENTERPOINT"
    assert "CENTER" in parse_address("3050 GATEWAY COMMERCE CENTER DR").street


def test_route_designator_dropped():
    """"CR" labels the road's authority; it is not part of its name."""
    assert (parse_address("4412 W CR 300 N").street
            == parse_address("4412 W 300 N").street)


@pytest.mark.parametrize(("text", "house", "street"), [
    ("W6331 WALLY WAY", "W6331", "WALLY"),
    ("N93W16890 CLEVELAND AVE", "N93W16890", "CLEVELAND"),
])
def test_wisconsin_grid_house_numbers_survive(text, house, street):
    """A house number may start with a letter, and one really does here.

    "W6331 WALLY WAY" in Greenville WI is a real Amazon facility. An earlier
    cut of this parser required the house number to start with a digit, found
    none, returned an empty street, and the ingest dropped the row - the
    facility vanished from the extract with nothing to show it had. That is
    the one failure mode worth a dedicated test, because a deletion leaves
    no trace to notice downstream.
    """
    got = parse_address(text)
    assert got.house == house
    assert got.street == street


def test_unparseable_address_returns_empty_street_not_a_guess():
    """Winkler 2.3: a record that fails to standardise cannot be matched.

    Saying so is the honest outcome. Emitting a component that is really a
    guess would let the matcher act on it.
    """
    for junk in ("", "   ", "NO ADDRESS GIVEN", "PO BOX"):
        assert parse_address(junk).street == ""


def test_normalise_address_is_a_view_on_the_parse():
    """There is one implementation, not two agreeing by coincidence."""
    assert normalise_address("2801 S. WESTERN AVENUE") == "2801 S WESTERN AVE"
    assert (normalise_address("315 SHUKSAN WAY DWS4")
            == normalise_address("315 SHUKSAN WAY"))
