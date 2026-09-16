"""Two decisions the NLRB export forces before anything can be counted.

Is this case about Amazon, and is this city the same city as that one? Both
are keyed off free text typed by regional staff, both change the answer to
"how much of the network do we see", and neither belongs buried in a parser.

Split out of `ingest.nlrb` so `ingest.nlrb_capture` can apply the same city
key to the OSHA and OpenStreetMap lists. A capture-recapture estimate in
which the two lists are normalised differently is not measuring coverage, it
is measuring the difference between two normalisers.
"""

from __future__ import annotations

import re

# Imported, not copied. `ingest.osha` carries a comment about what happened
# last time this project kept two copies of one matching table: the count of
# distinct Amazon sites depended on which entry point you ran.
from .osha import IS_THE_RETAILER, NOT_THE_RETAILER

__all__ = ["is_amazon_employer", "normalise_city"]

#: Place-name noise that is not part of the place. Applied only at the ends
#: of the string: "Brownstown Township" and "Brownstown" are one city, but
#: "Kansas City" and "Kansas" are two, so no interior token is touched.
_LEAD = re.compile(r"^(CITY|TOWN|TOWNSHIP|VILLAGE|BOROUGH) OF ")
_TRAIL = re.compile(r"\s+(TOWNSHIP|TWP|TOWN|VILLAGE|BORO|BOROUGH)$")
_ABBREV = (("ST ", "SAINT "), ("MT ", "MOUNT "), ("FT ", "FORT "))

#: "Amazon" as a whole word anywhere in the case name, not only at the front.
#: Anchoring this to the start cost nine cases on the first run, and they
#: were the nine that matter most: "MOLOCK Logistics and Amazon, as joint
#: employers", "Silverstar Delivery LTD ... and Amazon, Logistics, Inc.,
#: Joint Employers", "Elite Line Services at Amazon CLT2". Those are the DSP
#: filings - limitation 1 in HOWTO.md section 4 - and dropping them would
#: have removed the only direct evidence in the source that a
#: delivery-station charge can name somebody other than Amazon.
_AMAZON_WORD = re.compile(r"\bamazon\b", re.I)


def normalise_city(name: str | None) -> str:
    """A city key that survives the spellings these exports contain.

    Deliberately conservative. Every rule below collapses a pair OBSERVED as
    two spellings of one place across `nlrb_cases_amazon.csv` and
    `data/interim/osha_amazon.csv`; nothing here is speculative tidying.

    The direction of the risk is asymmetric and decides the design. A false
    NON-match invents a city that one list has and the other does not, which
    inflates the estimated population and makes our coverage look worse. A
    false MATCH deletes a city from the frame and makes coverage look
    better. Only the second is self-serving, so the rules are end-anchored
    and none of them merges on similarity.
    """
    if not isinstance(name, str):
        return ""
    text = re.sub(r"[.,'`()]", " ", name.upper()).replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = _TRAIL.sub("", _LEAD.sub("", text))
    for short, long in _ABBREV:
        if text.startswith(short):
            text = long + text[len(short):]
            break
    return re.sub(r"\s+", " ", text).strip()


def is_amazon_employer(name: str) -> bool:
    """Whether this case concerns Amazon the retailer, not a namesake.

    Weaker than `osha.is_amazon_retailer` on purpose, and the reason is the
    field. OSHA's establishment name comes with a NAICS code, so a bare
    "AMAZON" can be adjudicated on whether it files under warehousing. An
    NLRB case name has no such companion field, and 105 of 970 cases in this
    export are exactly "Amazon" or "AMAZON". Rejecting them would throw away
    11% of the source to guard against a namesake the export's own employer
    filter has already excluded.

    "CONCERNS" rather than "names", because the joint-employer and DSP
    filings put a third party first and Amazon second, and those are rows we
    want. The cost of the looser rule is one case, "Amazon Construction",
    which the shared exclusion list catches anyway.
    """
    if IS_THE_RETAILER.search(name):
        return True
    if NOT_THE_RETAILER.search(name):
        return False
    return bool(_AMAZON_WORD.search(name))
