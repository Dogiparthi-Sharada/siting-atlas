"""Standardise and parse a US street address into comparable components.

Why this is its own module, and its own STEP
--------------------------------------------
Winkler (RR99-04) §2.3 lists four reasons record linkage fails, and the first
two are "records that do not address standardize" and "records that do not
name standardize". His description of what standardisation *is* is the design
brief for this file: "commonly occurring words such as Mister, Road, Post
Office Box, etc. are replaced by standardized spellings and the components of
the names and addresses are placed in fixed locations. If standardization
fails for a record, then automatic matching in software may be impossible."

Two things follow, and the old code got both wrong.

First, standardisation is a *separate step that runs before comparison*, not
a string-cleaning helper called from inside a matcher. The thing a matcher
should receive is a record with fields in fixed locations, not a flattened
string it has to guess at.

Second, "fixed locations" is the whole point. The old `normalise_address()`
returned one squashed string, so it could not tell the difference between
the two situations that dominate this dataset:

    "1555 N CHRISMAN RD"  vs  "1555 S CHRISMAN RD"   <- CONFLICT, 2 buildings
    "4616-6 W HOWARD LN"  vs  "4616-6 HOWARD LN"     <- MISSING, 1 building

Both differ by one directional token. Collapsing on "ignore directionals"
merges two real Tracy CA facilities into one; refusing to collapse splits one
Austin TX facility into two. Only a parse that puts the directional in a
named slot can treat absence and contradiction differently, which is exactly
Winkler's §2.3 case 3, "records that have more information or missing
matching variables".

What the OSHA free-text field actually contains
-----------------------------------------------
Real values from the national extract, each of which broke the previous
single-string normaliser:

    "315 SHUKSAN WAY DWS4"                  facility code in the street box
    "2600 N NORMANDY BLVD, DELTONA, FL 32725"   whole address re-typed
    "21005 64TH AVENUE S ATTN JESSICA ANG"  mail-routing instruction
    "AMAZON.COM BUILDING, 1901 MEADOWVILLE" operator name before the number
    "4905 DERRICK RD SW AMAZON MGE8 SORTATION CENTER"  all of it at once
    "376 ZAPPOS.COM BLVD - 100 W THOMAS PECHOL"  two addresses in one cell
    "W6331 WALLY WAY"                       a house number starting with W

Every rule below is driven by a *class* of these, never by one building. The
test for whether a rule belongs here is whether it would still fire on a
state we have not looked at yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .address_tables import (
    ATTN,
    DIRECTION,
    FACILITY_CODE,
    GRID_HOUSE,
    OPERATOR_NOISE,
    ROUTE_WORDS,
    SUFFIX,
    SUFFIX_VALUES,
    TRAILING_CSZ,
    UNIT_WORDS,
)


@dataclass(frozen=True)
class Address:
    """One street address with its components in fixed locations.

    Frozen because a parsed address is a value: two records that parse to
    equal components are interchangeable for matching, and nothing downstream
    has any business editing one in place.
    """

    house: str = ""          # "4616-6" -> the full token, hyphen kept
    predir: str = ""         # standardised directional before the name
    street: str = ""         # the name itself, suffix and directionals gone
    suffix: str = ""         # standardised street type: RD, AVE, BLVD
    postdir: str = ""        # standardised directional after the suffix
    unit: str = ""           # suite / building number, tenant-level
    code: str = ""           # Amazon facility code found in the street box
    raw: str = ""            # what we were handed, for clerical review

    @property
    def number(self) -> str:
        """Leading digits of the house number, for blocking.

        "4616-6" and "4616" have to land in the same block or the Austin
        pair can never be compared at all. Blocking errors are unrecoverable
        - a pair never generated is a false non-match no threshold can undo.
        """
        m = re.match(r"\d+", self.house)
        return m.group() if m else self.house

    @property
    def core(self) -> str:
        """Street name with spaces removed, for comparison only.

        OSHA contains "GRANT LINE" / "GRANTLINE", "ELK HORN" / "ELKHORN" and
        "CENTER POINT" / "CENTERPOINT" - the same street, tokenised two ways.
        Word-by-word comparison scores those as total disagreement; removing
        the spaces makes them identical. This is lossy and is never displayed.
        """
        return self.street.replace(" ", "")

    def key(self) -> str:
        """A single canonical string, for humans and for coarse grouping.

        This is what `normalise_address()` used to return, rebuilt from the
        parse so there is exactly one implementation. It is deliberately NOT
        the matching rule: equality of this string is sufficient for a match
        but nothing like necessary, which is the mistake the old code made.
        """
        parts = [self.house, self.predir, self.street, self.suffix,
                 self.postdir]
        return " ".join(p for p in parts if p)


def _cut_operator_noise(tokens: list[str]) -> list[str]:
    """Drop the tenant description that follows the street.

    The trap: "376 ZAPPOS.COM BLVD" is a real street in Shepherdsville KY,
    and ZAPPOS is an Amazon brand. A naive "delete operator words" rule
    deletes the street name. So the cut only fires once a street suffix has
    already been seen, which is the point at which the address proper has
    finished. "4905 DERRICK RD SOUTHWEST AMAZON MGE8 SORTATION CENTER" cuts
    at AMAZON because RD came first; "376 ZAPPOS.COM BLVD" does not cut at
    all because ZAPPOS comes before BLVD.
    """
    seen_suffix = False
    for i, tok in enumerate(tokens):
        if seen_suffix and tok in OPERATOR_NOISE:
            return tokens[:i]
        if tok in SUFFIX_VALUES:
            seen_suffix = True
    return tokens


def _is_house(tok: str) -> bool:
    """Whether a token can be a house number.

    Usually "starts with a digit". The exception is the grid addressing used
    across Wisconsin and parts of Illinois and Indiana, where the number
    leads with a directional letter and no space: "W6331 WALLY WAY" in
    Greenville WI, or the fuller "N93W16890". A digits-only test silently
    DROPPED that facility - no house number found, empty street returned,
    row filtered out by the ingest. A building that disappears is the
    expensive kind of bug: nothing downstream can notice an absence.
    """
    return bool(tok) and (tok[0].isdigit() or bool(GRID_HOUSE.match(tok)))


def _is_code(tok: str) -> bool:
    """Whether a token is an Amazon building code rather than geography.

    The letter part must not be a directional or a route designator, or
    "SW1" and "CR5" would be swallowed as building codes and the street
    would lose the only thing distinguishing it from its neighbour.
    """
    m = FACILITY_CODE.match(tok)
    if not m:
        return False
    head = m.group(1)
    return head not in DIRECTION and head not in ROUTE_WORDS


def _glue_split_code(tokens: list[str]) -> list[str]:
    """Rejoin a building code that was typed with a space: "STL 4".

    Only applied once a street suffix has been seen, for the same reason as
    `_cut_operator_noise`: before the suffix we are still inside the street
    name and "300 N" style tokens must survive. The letter half is also
    barred from being a suffix or unit word, which is what stops
    "... ECHOLS LN 3" from collapsing into a fictitious code "LN3".
    """
    if len(tokens) < 2:
        return tokens
    head, tail = tokens[-2], tokens[-1]
    seen_suffix = any(t in SUFFIX_VALUES for t in tokens[:-2])
    if (seen_suffix and tail.isdigit() and len(tail) <= 2
            and head.isalpha() and 2 <= len(head) <= 4
            and head not in SUFFIX_VALUES and head not in UNIT_WORDS
            and head not in DIRECTION and _is_code(head + tail)):
        return tokens[:-2] + [head + tail]
    return tokens


def _pop_unit(tokens: list[str]) -> tuple[list[str], str]:
    """Split off a secondary-unit number, returning (rest, unit)."""
    for i, tok in enumerate(tokens):
        if tok in UNIT_WORDS and i + 1 < len(tokens):
            return tokens[:i] + tokens[i + 2:], tokens[i + 1]
    # "#6162" - the hash is tokenised separately so that it can mark the
    # number that follows it as a unit wherever it appears in the string.
    if "#" in tokens:
        i = tokens.index("#")
        if i + 1 < len(tokens):
            return tokens[:i] + tokens[i + 2:], tokens[i + 1]
        return tokens[:i], ""
    # A bare trailing number after a suffix is a unit too: OSHA writes
    # "100 W THOMAS P ECHOLS LN 3". Guarded on len > 2 so that a numbered
    # street such as "4412 W 300 N" keeps its number.
    if (len(tokens) > 2 and tokens[-1].isdigit()
            and tokens[-2] in SUFFIX_VALUES):
        return tokens[:-1], tokens[-1]
    return tokens, ""


def _standardise_token(tok: str, is_last: bool) -> str:
    """One token, spelled the one agreed way.

    SAINT -> ST only when the token is not final. "ST" at the end of an
    address means STREET; "ST" in the middle means SAINT, as in the Portland
    pair "3610 NW SAINT HELENS RD" / "3610 NW ST HELENS RD". Folding them
    blind would turn "SAINT" into a street type and lose the street name.
    """
    if tok == "SAINT" and not is_last:
        return "ST"
    return SUFFIX.get(tok, tok)


def parse_address(text: str) -> Address:
    """Free text in, components in fixed locations out.

    Never raises and never returns None. An address it cannot parse comes
    back with `street` empty, which the matcher treats as "compare nothing",
    because Winkler's §2.3 warning is that a record which fails to
    standardise cannot be matched automatically - and saying so is better
    than emitting a component that is really a guess.
    """
    raw = text or ""
    up = raw.upper().strip()
    up = TRAILING_CSZ.sub("", up)
    up = ATTN.sub("", up)
    # Two addresses in one cell: OSHA's " - " separator. Keep the first,
    # which is the one the other columns' city and ZIP describe.
    up = re.split(r"\s+-\s+", up)[0]
    up = re.sub(r"[^A-Z0-9#/ -]", " ", up)
    # "#6162" is a unit marker, not a word boundary.
    up = up.replace("#", " # ")
    tokens = up.split()
    if not tokens:
        return Address(raw=raw)

    # Everything before the house number is a business name:
    # "AMAZON.COM BUILDING, 1901 MEADOWVILLE TECHNOLOGY". Only trimmed when
    # a house number exists at all, so a genuinely unnumbered address is
    # left intact rather than emptied.
    start = next((i for i, t in enumerate(tokens) if _is_house(t)), None)
    if start is None:
        return Address(raw=raw)
    tokens = tokens[start:]

    house, tokens = tokens[0], tokens[1:]
    tokens = [_standardise_token(t, i == len(tokens) - 1)
              for i, t in enumerate(tokens)]
    tokens = _cut_operator_noise(tokens)

    # The facility code is pulled before the unit split so that a trailing
    # "DWS4" is not mistaken for anything else, and before directional and
    # suffix detection so that it cannot occupy their slots.
    tokens = _glue_split_code(tokens)
    code = next((t for t in tokens if _is_code(t)), "")
    if code:
        tokens = [t for t in tokens if t != code]

    tokens, unit = _pop_unit(tokens)
    tokens = [t for t in tokens if t != "#"]
    tokens = [t for t in tokens
              if not (t in ROUTE_WORDS and len(tokens) > 1)]

    predir = ""
    if len(tokens) > 1 and tokens[0] in DIRECTION:
        predir, tokens = DIRECTION[tokens[0]], tokens[1:]
    postdir = ""
    if len(tokens) > 1 and tokens[-1] in DIRECTION:
        postdir, tokens = DIRECTION[tokens[-1]], tokens[:-1]
    suffix = ""
    if len(tokens) > 1 and tokens[-1] in SUFFIX_VALUES:
        suffix, tokens = tokens[-1], tokens[:-1]

    return Address(house=house, predir=predir, street=" ".join(tokens),
                   suffix=suffix, postdir=postdir, unit=unit, code=code,
                   raw=raw)


def normalise_address(text: str) -> str:
    """Canonical single-string form, for display and coarse grouping.

    Kept because callers and documentation refer to it, but it is now a thin
    wrapper over the parse rather than a second, competing implementation.
    Do not use it to decide whether two addresses match: use
    `linkage.compare_addresses`, which can see the components.
    """
    return parse_address(text).key()
