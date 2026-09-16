"""Read facility fields out of reconstructed table cells.

`mwpvl_grid` recovers the grid; this decides what each column means and pulls
structure out of the text. Kept apart because the geometry must hold for all
thirteen tables while the interpretation differs between them.

COLUMNS ARE IDENTIFIED BY CONTENT, NOT BY POSITION
--------------------------------------------------
The US tables begin with a State column; the rest-of-world tables begin with a
flag icon and a Country column, which shifts every subsequent field one to the
right. Indexing by position would therefore read square footage out of the
date column for five of the thirteen tables and report nothing wrong. So each
column is scored for how much it looks like each field and assigned to its
best match.

WHAT IS DELIBERATELY NOT DONE HERE
----------------------------------
No value is repaired, dropped or inferred. A date that reads "9022" is carried
through as 9022. Cleaning belongs downstream in `warehouse/edits.py`, where
the OSHA "operating by" bound is available to test a date against evidence
rather than against plausibility -- and where a rejection is recorded instead
of happening silently inside a parser.
"""

from __future__ import annotations

import re

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{1,2})\b")
SQFT_RE = re.compile(r"\b(\d{1,3}(?:[,.]\d{3})+)\b")
MONTH_RE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
                      r"[a-z]*\.?", re.I)
YEAR_RE = re.compile(r"\b(19\d\d|20\d\d)\b")
QUARTER_RE = re.compile(r"\bQ([1-4])[ :./-]*(20\d\d)\b", re.I)
ADDR_RE = re.compile(r"^(?P<street>.+?),\s*(?P<rest>[^,]+(?:,[^,]+)*?),?\s*"
                     r"(?:USA|U\.S\.A\.?)[,. ]*(?P<zip>\d{5})", re.I)

#: Phrases MWPVL uses to mark its own uncertainty. These are the most valuable
#: thing in the description column: the publisher is telling us which rows it
#: does not stand behind, which is a per-record reliability weight of the kind
#: Fellegi & Holt sec.7 asks for and almost no source ever supplies.
FLAGS = (
    ("not_confirmed", re.compile(r"not\s+(?:yet\s+)?confirmed|could\s+be\s+a|"
                                 r"role\s+of\s+facility|not\s+much\s+is\s+known",
                                 re.I)),
    ("delayed", re.compile(r"delay(?:ed|s)?|postponed", re.I)),
    ("cancelled", re.compile(r"cancel+ed|shelved|abandoned", re.I)),
    ("closed", re.compile(r"\bclosed\b|decommissioned|"
                          r"consolidated\s+into", re.I)),
    ("sqft_estimated", re.compile(r"sq\.?\s*ft\.?\s+is\s+an\s+estimate|"
                                  r"estimated\s+sq", re.I)),
    ("colocated", re.compile(r"included\s+in\b|co-?located", re.I)),
    ("rural_wagon_wheel", re.compile(r"rural\s+wagon\s+wheel", re.I)),
)

FIELDS = ("code", "address", "sqft", "date", "region", "description")


def _score(cells: list[str]) -> dict[str, int]:
    """How strongly a column's contents resemble each field."""
    joined = " ".join(cells)
    return {
        "code": sum(1 for c in cells if CODE_RE.fullmatch(c.strip())),
        "address": len(re.findall(r"USA", joined, re.I)),
        "sqft": len(SQFT_RE.findall(joined)),
        "date": len(YEAR_RE.findall(joined)) + len(MONTH_RE.findall(joined)),
        "description": len(re.findall(r"\b(?:station|center|centre|facility|"
                                      r"delivery|sortation|fulfillment)\b",
                                      joined, re.I)),
    }


def identify_columns(rows: list[dict[int, str]]) -> dict[str, int]:
    """Map field name -> column index, by content.

    Assigned greedily from the strongest evidence down, so that a column
    already claimed by a better-fitting field cannot be taken twice. Address
    wins on "USA" counts and description on facility vocabulary; both are
    strong signals, and resolving them first keeps them from stealing the
    numeric columns.
    """
    cols = sorted({c for r in rows for c in r})
    scores = {c: _score([r.get(c, "") for r in rows]) for c in cols}

    out: dict[str, int] = {}
    taken: set[int] = set()
    for field in ("address", "description", "date", "sqft", "code"):
        best, best_n = None, 0
        for c in cols:
            if c in taken:
                continue
            if scores[c][field] > best_n:
                best, best_n = c, scores[c][field]
        if best is not None:
            out[field] = best
            taken.add(best)

    # Whatever is left of the address is the state or country. Rest-of-world
    # tables carry both a flag glyph and a country name; the flag lands in its
    # own narrow column and is discarded by taking the RIGHTMOST leftover.
    left = [c for c in cols if c not in taken
            and c < out.get("address", max(cols) + 1)]
    if left:
        out["region"] = left[-1]
    return out


def parse_sqft(text: str):
    """Square footage as an int, or None.

    OCR reads the thousands separator as either a comma or a full stop --
    "142,800" and "142.800" both occur in this document for the same kind of
    value -- so both are stripped. That is safe here because no square-footage
    figure in the table is fractional.

    Returns None for a missing value AND for a stated zero, which are
    different things: MWPVL states that a zero means the facility shares a
    building and its floor area is counted under another record. Telling them
    apart is the caller's job via the `colocated` flag; conflating them here
    would let a real zero be averaged in as a real area.
    """
    m = SQFT_RE.search(text or "")
    if not m:
        return None
    value = int(re.sub(r"[,.]", "", m.group(1)))
    return value or None


def parse_date(text: str) -> dict:
    """Month, year and quarter from a date cell.

    The cell holds "October 2019", or a bare "2025", or "Q3:2024". All three
    appear. A bare year is not a missing month -- it is MWPVL recording a year
    it is confident about and a month it is not -- so `month` stays None and
    `precision` says which was found.
    """
    text = text or ""
    out: dict = {"month": None, "year": None, "quarter": None,
                 "precision": "none"}

    q = QUARTER_RE.search(text)
    if q:
        out.update(quarter=int(q.group(1)), year=int(q.group(2)),
                   precision="quarter")
        return out

    years = [int(y) for y in YEAR_RE.findall(text)]
    if years:
        # The largest plausible year: a description fragment bleeding into the
        # column contributes older years ("replaced AVP6 in 2016"), while the
        # opening date is the value the column is for.
        out["year"] = max(years)
        out["precision"] = "year"
    m = MONTH_RE.search(text)
    if m and out["year"]:
        out["month"] = MONTHS[m.group(1)[:3].lower()]
        out["precision"] = "month"
    return out


#: Tokens whose trailing full stop is an abbreviation, not a field separator.
#: Without this list, normalising "." to "," would cut "6250 Sycamore Canyon
#: Blvd., Riverside" into two fields at the Blvd.
ABBREV = {"st", "ave", "av", "rd", "dr", "blvd", "ln", "ct", "cir", "pkwy",
          "hwy", "expy", "fwy", "pl", "ste", "apt", "bldg", "mt", "ft", "jr",
          "sr", "no", "us", "n", "s", "e", "w", "ne", "nw", "se", "sw"}

#: OCR reads a capital I as a lowercase l in this font, so state names arrive
#: as "lowa", "llinois", "ndiana". Rebuilt from the canonical list rather than
#: enumerated, so it cannot fall out of step with STATES.
#: Single-word names are written as one space-separated string and split,
#: because forty quoted strings with commas is a wall nobody proof-reads.
#: Two-word names cannot go in it and are listed separately.
_ONE_WORD = (
    "alabama alaska arizona arkansas california colorado connecticut delaware "
    "florida georgia hawaii idaho illinois indiana iowa kansas kentucky "
    "louisiana maine maryland massachusetts michigan minnesota mississippi "
    "missouri montana nebraska nevada ohio oklahoma oregon pennsylvania "
    "tennessee texas utah vermont virginia washington wisconsin wyoming"
)
_TWO_WORD = ["new hampshire", "new jersey", "new mexico", "new york",
             "north carolina", "north dakota", "rhode island",
             "south carolina", "south dakota", "west virginia",
             "district of columbia"]
STATES = _ONE_WORD.split() + _TWO_WORD


def _split_fields(text: str) -> list[str]:
    """Split an address tail on commas AND on full stops used as commas.

    MWPVL's table is printed small and OCR reads a comma as a full stop often
    enough to matter: "W. Tucson. Arizona. USA. 85713" is one address whose
    separators are all periods. Splitting on commas alone leaves city and
    state fused, which was measured at 63 of 591 rows -- 11% -- every one of
    which then failed to map to a state and dropped out of the coverage count.

    A full stop is a separator unless the word before it is a street-type
    abbreviation or a single letter, which is what keeps "Blvd." and "W."
    intact.
    """
    text = re.sub(r"\s+", " ", text or "")
    text = re.sub(
        r"(?<=[A-Za-z])\.(?=\s|$)",
        lambda m: ".",  # placeholder; the real decision happens below
        text)
    out, buf = [], []
    for token in text.split(" "):
        buf.append(token)
        if token.endswith(",") or (
                token.endswith(".")
                and token.rstrip(".").lower() not in ABBREV
                and len(token.rstrip(".")) > 1):
            out.append(" ".join(buf).strip(" ,."))
            buf = []
    if buf:
        out.append(" ".join(buf).strip(" ,."))
    return [p for p in out if p]


def canonical_state(text: str):
    """A US state name from a possibly OCR-mangled string, or None.

    Tries the literal name, then the same name with lowercase l read back as
    the capital I it almost certainly was. "lowa" -> "iowa" is the common case
    and appears throughout this document.
    """
    s = re.sub(r"[^a-z ]", "", (text or "").lower()).strip()
    if not s:
        return None
    for candidate in (s, s.replace("l", "i", 1), "i" + s,
                      s.replace("rn", "m"), s.replace("m", "rn")):
        if candidate in STATES:
            return candidate.title()
    return None


def _street_at(parts: list[str]) -> int:
    """Index of the field holding the street, among everything before the
    state.

    ONE CELL, TWO FACILITIES
    ------------------------
    A row whose postal code failed to OCR has no anchor, so its words join the
    row below it (`mwpvl_grid`, and sec.13.1 of MWPVL_OCR_PIPELINE.md, which
    measures the defect at 3%). The cell then holds two addresses:

        2050 E Riverview Dr, Phoenix, 14000 W Grant St, Goodyear, Arizona,
        USA, 85338

    Taking the street as "everything before the first comma" pairs the LOST
    facility's street with the ANCHORED facility's city and postal code. 85338
    is Goodyear; 2050 E Riverview Dr is in Phoenix. The row that comes out
    describes a building that does not exist, and it geocodes accordingly --
    42 of the 50 rows shaped like this failed to match.

    The postal code that anchored the row is the LAST one printed in the cell,
    so the address it belongs to is the last one too: take the LAST field that
    opens with a house number.

    WHY A HOUSE NUMBER AND NOT A STREET-TYPE WORD. The first version of this
    scored a field as a street if it ended in Road/Way/Terrace/Park and so on,
    and it was wrong in both directions. Federal Way, Temple Terrace, Overland
    Park and Buena Park are US cities, all four are in this document, and the
    list read the city as the street on every one of them -- "33855
    Weyerhaeuser Way S., Building B, Federal Way, Washington" came out with a
    street of "Federal Way" and no city at all. A leading house number cannot
    be a city and needs no list to recognise. It also costs nothing where it
    finds none: a street with no number ("Goodman Way", "Isle of Capri")
    cannot be geocoded whichever field it is read from, so there is no gain to
    trade against the risk.
    """
    numbered = [i for i, p in enumerate(parts) if p[:1].isdigit()]
    return numbered[-1] if numbered else 0


def parse_address(text: str) -> dict:
    """Street, city, region and postal code from the address cell."""
    text = re.sub(r"\s+", " ", (text or "").replace("|", " ")).strip()
    out = {"street": None, "city": None, "addr_region": None,
           "postcode": None, "address_raw": text}
    m = ADDR_RE.search(text)
    if not m:
        z = re.search(r"\b(\d{5})\b", text)
        if z:
            out["postcode"] = z.group(1)
        return out
    out["postcode"] = m.group("zip")
    # The leading field is taken WHOLE and is never re-split. `_split_fields`
    # treats a full stop after an unrecognised token as a separator, which is
    # right for the tail of an address and wrong inside a street: it cut
    # "6910 S.E. Four Mile Drive" at the "S.E." and "3333S. 7th St" at the
    # house number, and each row then lost the number it needs to geocode.
    parts = [m.group("street").strip(" ,.")] + _split_fields(m.group("rest"))
    if not parts:
        return out

    # The state is the last part that RESOLVES to one, not simply the last
    # part -- merged rows and stray description text put junk at the end, and
    # taking it positionally is how "Lathrop Connecticut" became a state.
    region_at = next((i for i in range(len(parts) - 1, -1, -1)
                      if canonical_state(parts[i])), None)
    # The street is looked for BEFORE the region field and never in it.
    street_at = _street_at(parts[:max(region_at if region_at is not None
                                      else len(parts) - 1, 1)])
    out["street"] = parts[street_at]
    if region_at is not None:
        out["addr_region"] = canonical_state(parts[region_at])
        # The city is what sits BETWEEN the street and the state. Nothing sits
        # there on a cell that names a street and a state and no place.
        if region_at - 1 > street_at:
            out["city"] = parts[region_at - 1]
        return out

    # No part resolves to a state. The trailing part is reported as the region
    # anyway -- unchanged behaviour, and the OCR grade in `mwpvl_merge` is what
    # reads it -- and the city keeps its positional reading, because on
    # "2865 Duke Parkway, Aurora, USA. 60563" the one place name present is the
    # city and dropping it would cost a geocode to gain nothing.
    out["addr_region"] = parts[-1]
    out["city"] = parts[-2] if len(parts) > 2 else (
        parts[1] if len(parts) > 1 else None)
    return out


def parse_flags(text: str) -> dict:
    """MWPVL's own caveats, as booleans. See FLAGS for why these matter."""
    text = text or ""
    return {name: bool(rx.search(text)) for name, rx in FLAGS}


def parse_code(text: str):
    """The Amazon facility code, e.g. DBM3. None if the cell holds no code.

    Takes the FIRST match: a merged row carries two codes and the first
    belongs to the facility this row is anchored on.
    """
    m = CODE_RE.search((text or "").upper())
    return m.group(1) if m else None
