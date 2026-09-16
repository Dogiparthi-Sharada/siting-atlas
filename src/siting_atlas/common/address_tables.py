"""The standardisation vocabulary: how a street address is spelled here.

Split out of `address.py` so that the tables can be read, reviewed and
extended on their own. Every entry is a claim about American addressing, not
about this dataset, and that is the test for whether a new one belongs: a
rule that only fires on one building is a lookup table pretending to be a
method, which is the thing this rewrite exists to remove.

The practice these tables implement is Winkler RR99-04 Sec. 2.3: during
standardisation "commonly occurring words such as Mister, Road, Post Office
Box, etc. are replaced by standardized spellings and the components of the
names and addresses are placed in fixed locations."
"""

from __future__ import annotations

import re

#: One suffix table for the whole project. There used to be two - a longer
#: one in `ingest/osha.py` and a shorter one inlined in a scratch script -
#: and they disagreed on CIRCLE, PLACE, TERRACE, TRAIL, the diagonal
#: directionals and the unit designators. Two tables that disagree are worse
#: than one table that is wrong, because the pipeline's answer then depends
#: on which entry point happened to run.
SUFFIX = {
    "AVENUE": "AVE", "AVENU": "AVE", "AV": "AVE",
    "STREET": "ST", "STR": "ST", "STREE": "ST",
    "ROAD": "RD", "DRIVE": "DR", "DRIV": "DR",
    "BOULEVARD": "BLVD", "BOUL": "BLVD", "BL": "BLVD", "BLV": "BLVD",
    "PARKWAY": "PKWY", "PARKWY": "PKWY", "PKY": "PKWY",
    "LANE": "LN", "COURT": "CT", "CIRCLE": "CIR", "PLACE": "PL",
    "HIGHWAY": "HWY", "HIWAY": "HWY", "EXPRESSWAY": "EXPY",
    "TERRACE": "TER", "TRAIL": "TRL", "TURNPIKE": "TPKE",
    "LOOP": "LOOP", "PIKE": "PIKE", "WAY": "WAY", "PLAZA": "PLZ",
    "SQUARE": "SQ", "CROSSING": "XING", "EXTENSION": "EXT",
}
# CENTER is deliberately absent. It looks like a street type and the Postal
# Service does abbreviate it to CTR, but in this dataset it is almost always
# part of the street NAME - "GATEWAY COMMERCE CENTER DR", "HAZELWOOD
# LOGISTICS CENTER DR", "1 CENTER POINT BLVD". Folding it split the New
# Castle DE pair, because "CENTER POINT" became "CTR POINT" and no longer
# matched "CENTERPOINT". A rule that fires on the wrong slot is worse than
# no rule.

#: The set of standardised suffix values, i.e. what a token looks like once
#: SUFFIX has been applied. Membership in this set is how the parser decides
#: a trailing token is a street type rather than part of the street name.
SUFFIX_VALUES = set(SUFFIX.values())

#: Directionals get their own table because they occupy their own SLOT. A
#: directional is never part of the street name for our purposes, and the
#: pre- and post- positions are compared separately - see the module
#: docstring for why conflating them loses real facilities.
DIRECTION = {
    "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W",
    "NORTHEAST": "NE", "NORTHWEST": "NW",
    "SOUTHEAST": "SE", "SOUTHWEST": "SW",
    "N": "N", "S": "S", "E": "E", "W": "W",
    "NE": "NE", "NW": "NW", "SE": "SE", "SW": "SW",
}

#: Secondary-unit designators. A suite number is evidence about a tenant, not
#: about a building, so these are parsed out and then given almost no weight
#: in the comparison. "3680 LANGLEY DRIVE SUITE 100" and "3680 LANGLEY DR"
#: are one warehouse.
UNIT_WORDS = {"STE", "SUITE", "APT", "UNIT", "RM", "ROOM", "FL", "FLOOR",
              "BLDG", "BUILDING", "DEPT", "SPC", "TRLR"}

#: Route designators that precede a numbered rural road. Dropping them makes
#: "4412 W CR 300 N" and "4412 W 300 N" the same street, which they are -
#: "CR" is a label for the road's authority, not part of its name.
ROUTE_WORDS = {"CR", "CO", "COUNTY", "SR", "RTE", "ROUTE", "FM", "HC"}

#: Words that mean the free-text field has stopped describing a street and
#: started describing the tenant. Truncating here is only safe AFTER a street
#: suffix has been seen - see `_cut_operator_noise` for the trap that guards.
OPERATOR_NOISE = {"AMAZON", "AMAZONCOM", "WHOLE", "FOODS", "FULFILLMENT",
                  "FULFILMENT", "SORTATION", "SORT", "DELIVERY", "STATION",
                  "WAREHOUSE", "DISTRIBUTION", "RECEIVE", "DOCK"}

#: An Amazon building code: two to four letters (usually the nearest airport)
#: and one or two digits, e.g. DWS4, BFI7, MGE8, ORD4, BF15. Inspectors type
#: these into the street-address box. The code is genuinely useful - it is
#: the only identifier shared with the OpenStreetMap export, which has no
#: street address at all - so it is extracted into its own field rather than
#: deleted. Directionals and route words are excluded by `_is_code` because
#: "SW1" and "CR5" are geography, not buildings.
FACILITY_CODE = re.compile(r"^([A-Z]{2,4})([0-9]{1,2})$")

#: A trailing ", CITY, ST 12345" that duplicates the record's own city/state/
#: ZIP columns. Left in place it makes two spellings of one address differ by
#: five tokens, which no string comparator recovers from.
TRAILING_CSZ = re.compile(
    r",\s*[A-Z][A-Z .'-]*,?\s*[A-Z]{2}\.?\s*,?\s*\d{5}(-\d{4})?\s*$")

#: Mail-routing instructions. Everything from ATTN / C/O onward is about a
#: person, not a place.
ATTN = re.compile(r"\b(ATTN|ATTENTION|C\s*/\s*O)\b.*$")


#: Wisconsin-style grid house numbers: a directional letter fused to the
#: number, with an optional second pair. "W6331", "N93W16890", "S74W16860".
#: These are house numbers, not directionals - the letters are part of the
#: coordinate - so they must be recognised before the parser concludes an
#: address has no number at all and gives up on it.
GRID_HOUSE = re.compile(r"^[NSEW]{1,2}\d+([NSEW]\d+)?$")
