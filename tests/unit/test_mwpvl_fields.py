"""Reading facility fields out of reconstructed cells.

The failure mode here is the same one the grid has: a mis-identified column
does not raise, it reads square footage out of the date column and reports a
row count that looks right. Five of the thirteen tables shift every field one
to the right, so column identity is measured from content — and that
measurement is what these tests pin.
"""

from __future__ import annotations

import pytest

from siting_atlas.ingest import mwpvl_fields as fields

#: A US table: region, code, address, sqft, date, description.
_US_ROWS = [
    {0: "California", 1: "DAX8", 2: "1910 E Vista Way, Vista, California, "
                                   "USA, 92081", 3: "142,800",
     4: "October 2019", 5: "Delivery Station"},
    {0: "Iowa", 1: "DSM5", 2: "6910 S.E. Four Mile Drive, Ankeny, Iowa, "
                              "USA, 50021", 3: "120,000",
     4: "January 2022", 5: "Delivery Station"},
    {0: "Texas", 1: "DFW9", 2: "2601 W Pioneer Pkwy, Arlington, Texas, "
                               "USA, 76013", 3: "88,500",
     4: "2025", 5: "Sortation Centre"},
]


# ---------------------------------------------------------------------------
# identify_columns
# ---------------------------------------------------------------------------
def test_columns_are_identified_by_content_not_by_position():
    cols = fields.identify_columns(_US_ROWS)
    assert cols["address"] == 2
    assert cols["sqft"] == 3
    assert cols["date"] == 4
    assert cols["description"] == 5
    assert cols["code"] == 1
    assert cols["region"] == 0


def test_a_rest_of_world_layout_shifts_every_field_and_is_still_read():
    """A flag glyph and a Country column push everything one to the right.

    Indexing by position would read square footage out of the date column for
    five of the thirteen tables and report nothing wrong.
    """
    shifted = [{k + 1: v for k, v in row.items()} for row in _US_ROWS]
    for row in shifted:
        row[0] = "|"        # the flag icon, in its own narrow column
    cols = fields.identify_columns(shifted)
    assert cols["address"] == 3
    assert cols["sqft"] == 4
    assert cols["date"] == 5
    # RIGHTMOST leftover before the address, so the flag column is discarded.
    assert cols["region"] == 1


def test_no_field_is_assigned_to_two_columns():
    cols = fields.identify_columns(_US_ROWS)
    assert len(set(cols.values())) == len(cols)


# ---------------------------------------------------------------------------
# parse_address
# ---------------------------------------------------------------------------
def test_a_clean_address_splits_into_four_fields():
    got = fields.parse_address("1910 E Vista Way, Vista, California, "
                               "USA, 92081")
    assert got["street"] == "1910 E Vista Way"
    assert got["city"] == "Vista"
    assert got["addr_region"] == "California"
    assert got["postcode"] == "92081"


def test_full_stops_read_as_commas_still_split():
    """63 of 591 rows had the separators after the street OCR'd as stops.

    Measured on the real extract: 232 rows reach `USA` through a full stop
    and 231 of them resolve a state. Splitting on commas alone left city and
    state fused, and every one of those rows then dropped out of the coverage
    count without complaint.
    """
    got = fields.parse_address("2417 E. Carson St., Long Beach. "
                               "California. USA. 90810")
    assert got["addr_region"] == "California"
    assert got["city"] == "Long Beach"
    assert got["street"] == "2417 E. Carson St"


def test_a_street_type_abbreviation_is_not_a_field_separator():
    got = fields.parse_address("6250 Sycamore Canyon Blvd., Riverside, "
                               "California, USA, 92507")
    assert got["city"] == "Riverside"
    assert got["addr_region"] == "California"


def test_a_capital_i_read_as_a_lowercase_l_still_resolves():
    assert fields.canonical_state("lowa") == "Iowa"
    assert fields.canonical_state("llinois") == "Illinois"
    assert fields.canonical_state("Zembla") is None


def test_the_state_is_the_last_part_that_resolves_not_the_last_part():
    """Merged rows put junk at the end; taking it positionally invents one."""
    got = fields.parse_address("500 Bayside Pkwy, Lathrop, California, "
                               "USA, 95330 replaced AVP6")
    assert got["addr_region"] == "California"
    assert got["city"] == "Lathrop"


def test_an_unparseable_address_still_yields_a_postcode_and_says_nothing_else(
):
    got = fields.parse_address("somewhere near 43228 perhaps")
    assert got["postcode"] == "43228"
    assert got["street"] is None and got["city"] is None


# ---------------------------------------------------------------------------
# parse_date / parse_sqft / parse_code / parse_flags
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("October 2019", {"month": 10, "year": 2019, "quarter": None,
                      "precision": "month"}),
    ("2025", {"month": None, "year": 2025, "quarter": None,
              "precision": "year"}),
    ("Q3:2024", {"month": None, "year": 2024, "quarter": 3,
                 "precision": "quarter"}),
    ("", {"month": None, "year": None, "quarter": None, "precision": "none"}),
])
def test_parse_date_says_which_precision_it_found(text, expected):
    """A bare year is not a missing month. Defaulting one would manufacture
    a date the publisher never printed."""
    assert fields.parse_date(text) == expected


def test_an_implausible_year_passes_through_unrepaired():
    """Cleaning belongs downstream, where the OSHA bound can test it.

    2094 is the worst year in the real extract and it survives the parser
    intact, which is the property the module claims.

    A DISCREPANCY worth knowing: both this module's docstring and
    `mwpvl_tables`' say "a date that reads 9022 is carried through as 9022".
    It is not. `YEAR_RE` matches only 19xx and 20xx, so a 9022 yields no year
    at all and the row arrives UNDATED rather than implausibly dated. No such
    value exists in the current extract, so nothing downstream is wrong — but
    the two docstrings describe behaviour the code does not have.
    """
    assert fields.parse_date("October 2094")["year"] == 2094
    assert fields.parse_date("9022")["year"] is None


def test_a_description_year_does_not_beat_the_opening_year():
    assert fields.parse_date("October 2019 replaced AVP6 in 2016")["year"] \
        == 2019


@pytest.mark.parametrize("text,expected", [
    ("142,800", 142800),
    ("142.800", 142800),      # OCR reads the separator either way
    ("0", None),              # a stated zero is co-location, not an area
    ("", None),
])
def test_parse_sqft(text, expected):
    assert fields.parse_sqft(text) == expected


def test_parse_code_takes_the_first_of_a_merged_rows_two_codes():
    assert fields.parse_code("DAX8 DAX9") == "DAX8"
    assert fields.parse_code("no code here") is None


def test_the_publishers_own_caveats_survive_as_booleans():
    flags = fields.parse_flags("Role of facility is not yet confirmed; "
                               "delayed to 2026")
    assert flags["not_confirmed"] and flags["delayed"]
    assert not flags["cancelled"]
    # Every declared flag is present whether or not it fired, so a consumer
    # cannot tell "absent" apart from "False" by accident.
    assert set(flags) == {name for name, _ in fields.FLAGS}
