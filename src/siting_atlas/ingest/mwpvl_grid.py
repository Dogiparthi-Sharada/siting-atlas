"""Turn a bag of OCR'd words with boxes back into table cells.

The OCR emits words and pixel coordinates; this recovers the grid. Nothing
here knows what a facility is -- that is `mwpvl_tables.py`. The split is
deliberate, because the geometry is the part that must be right for all
thirteen tables and the interpretation differs between them.

THE PROBLEM, CONCRETELY
-----------------------
MWPVL's rows wrap over two to four printed lines, so reading order interleaves
neighbouring cells:

    7200 Chavenelle Road,          January
    Iowa  WWI2  Dubuque, Iowa, USA, 52002  120,000  9022

"January" and "2022" are one cell -- a date -- split across lines by the
address wrapping underneath it. In coordinates they are 46 px apart in x and
both inside the Year Opened column, so grouping by column and then by row band
reassembles them. That is the whole idea.

COLUMNS ARE MEASURED, NOT ASSUMED
---------------------------------
Boundaries come from vertical gutters in the data: project every word box onto
the x axis, find the runs of x that no word covers, and cut at their midpoints.
Self-calibrating matters here because the thirteen tables do not share a
layout -- the US tables start with State, the rest-of-world tables start with a
flag icon and a Country column, which shifts everything right. A hardcoded
boundary would silently mis-assign every rest-of-world row.

ROWS ARE ANCHORED ON ZIP CODES
------------------------------
Every facility row ends its address with a postal code, and nothing else in
the table looks like one in that column. Their y-centres are the row anchors;
boundaries are the midpoints between consecutive anchors. Anchoring on the
tallest column instead would fail, because the description cell often wraps to
more lines than the address and drifts out of alignment.

A row whose postal code did not OCR is LOST, and that is the dominant known
loss mode. It is counted and reported rather than estimated away.
"""

from __future__ import annotations

import re
from pathlib import Path

#: A word this faint is noise -- a rule mistaken for a hyphen, a speck. Kept
#: low because a wrong digit in a date is caught downstream by the OSHA bound,
#: while a dropped word is caught by nothing.
MIN_CONF = 25

#: Two readings of the same text within this many pixels, in both axes, are
#: the same word seen by two overlapping strips. Generous because the same
#: word OCR'd twice can differ by a pixel or two in either direction, and
#: small because the nearest genuine repeat -- a city name in the address and
#: again in the description -- is a different column and hundreds of px away.
DEDUPE_PX = 6

#: A gutter narrower than this is the space between words, not between
#: columns. The narrowest real gutter measured on the delivery station table
#: is the one before the address column, at 13 px.
MIN_GUTTER = 12

#: A column of x is a gutter if fewer than this FRACTION of the busiest
#: column's words cover it.
#:
#: The first version tested for ZERO coverage and found no columns at all --
#: bounds came back as [0, 819] on a table with six. Over 540 rows there is
#: always some row whose description overflows or whose address wraps into the
#: gutter, so no x is ever completely empty. The gutters are real but shallow:
#: measured coverage runs 1,385 words at the centre of the address column
#: against 3 at the gutter beside it, and 490 in the square-footage column
#: against 65 in the gap after it. 10% separates every one of the five gutters
#: from every one of the six columns with an order of magnitude to spare.
GUTTER_FRACTION = 0.10

#: A token ending in five digits, tolerating the two ways OCR mangles a US
#: postal code in this document. Both were found by measuring the rows that
#: failed to anchor, not anticipated:
#:
#:     92081-2607   clean ZIP+4
#:     85034-       ZIP+4 split across tokens; the "6852" arrives separately
#:                  and is only four digits, so a strict pattern matches
#:                  NEITHER half and the row silently merges into its neighbour
#:     USA36322     the comma and space between "USA," and the code dropped
#:
#: Anchored at the END of the token so that "143,200" and "2025" cannot match.
#: A five-digit STREET number matches too -- that is deliberate and is handled
#: by `_ends_its_line`, because position, not shape, is what separates them.
ZIP_RE = re.compile(r"(?:^|\D)\d{5}(?:-\d{0,4})?[.,]?$")

#: An Amazon facility code: two to four letters then one or two digits. DBM3,
#: YYC1, MMG1, HPX1, AVP8. Used as the fallback row anchor where postal codes
#: are not five digits.
CODE_RE = re.compile(r"[A-Z]{2,4}\d{1,2}")

#: Printed height of one table row, measured: 535 rows over 32,729 px on the
#: delivery station table is 61 px. Used only to judge whether an anchoring
#: strategy found the rows or found something else.
ROW_HEIGHT_PX = 61

#: Two words are on the SAME printed line if their y-centres are no further
#: apart than this. Measured on the delivery station table: consecutive lines
#: inside one row sit 17 px apart, while words sharing a line scatter by 0-5 px
#: (a trailing comma printed below the baseline is the widest case seen, at
#: 5 px). 8 px separates the two populations with room either side, and is the
#: same tolerance `_ends_its_line` and `build_rows` already use for "same
#: line".
LINE_GAP_PX = 8

#: How far a word's printed height may differ from the cell's typical height
#: before it is treated as a MARK rather than as text. Body text in this
#: document is 10-13 px tall. What falls outside is a ruled border read as `|`
#: (measured at 41 px, spanning the whole row), a speck read as `,` or `:`
#: (1-2 px), or a smear read as `ae`/`vee` (23-28 px). Those sit BETWEEN two
#: printed lines, so letting them define a line lets them bridge the two: with
#: them included, `2700 Regent Blvd, Irving, Texas, / USA. 75063` reassembled
#: as `2700 USA. Regent 75063 Blvd, Irving, Texas,` and the row lost its
#: street, its city and its state. Lines are therefore positioned from body
#: text and the marks are attached to whichever line is nearest.
MARK_HEIGHT_RATIO = 2

#: How far apart the top and bottom of ONE printed line's word centres may be.
#: Measured at 0-5 px on this document (a comma printed below the baseline is
#: the widest); the step to the next line is 14-17 px. A cluster taller than
#: this is two lines that a mark bridged, and only such a cluster is re-split.
MAX_LINE_SPAN_PX = 10

#: The words MWPVL prints in its column headings. Used only to locate the
#: heading band so it can be dropped -- see `_header_bottom`.
HEADER_WORDS = frozenset((
    "state", "country", "flag", "code", "location", "square", "feet",
    "year", "opened", "description", "operation"))

#: A heading has to be at the top of the image. Two row heights is generous --
#: the deepest heading measured ends at y=38 -- and the cap is what stops a
#: data row containing the word "Location" from being read as a heading.
HEADER_MAX_Y = 2 * ROW_HEIGHT_PX

#: How many DISTINCT heading words a band must contain before it is treated as
#: the heading. Three, because every table prints at least five and a data row
#: would have to coincide on three unrelated ones to be mistaken for it.
HEADER_MIN_WORDS = 3

#: A heading printed on two lines ("Square / Feet", "Year / Opened") has a
#: bigger gap between its lines than one line of body text does, but a much
#: smaller one than the gap down to the first data row: 10 px against 19-38 px
#: on the tables measured. The second heading line is absorbed at this radius.
HEADER_JOIN_PX = 15

#: A strategy must find at least this share of the rows the image height
#: implies. Set low because rows vary in height and the alternative to
#: accepting a thin result is returning nothing at all -- but high enough that
#: five-digit US ZIPs cannot "win" a Canadian table by matching a handful of
#: street numbers.
MIN_ANCHOR_DENSITY = 0.4


def load_words(directory: Path) -> list[dict]:
    """Every word from every strip TSV in one table's directory.

    Strips overlap by 400 px so that no row is cut in half by both of the
    strips containing it, which means the overlap region is OCR'd twice. The
    duplicates are removed by POSITION -- coordinates were rebased to the
    original image in `grid_ocr.py`, so the same word read twice lands at the
    same place. Removing them by string instead would delete genuine repeats:
    two facilities in one city share most of their address words.
    """
    raw: list[dict] = []
    for path in sorted(directory.glob("*.tsv")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[1:]:
            f = line.split("\t")
            if len(f) < 12:
                continue
            try:
                conf = float(f[10])
                x, y, w, h = (int(f[6]), int(f[7]), int(f[8]), int(f[9]))
            except ValueError:
                continue
            text = f[11].strip()
            if not text or conf < MIN_CONF:
                continue
            raw.append({"x": x, "y": y, "w": w, "h": h, "conf": conf,
                        "text": text, "cx": x + w // 2, "cy": y + h // 2})

    # Deduplicate by PROXIMITY, not by a grid cell.
    #
    # The first version keyed on (x//8, y//8, text), and it leaked: two strips
    # reading the same word can disagree by a pixel, and if that pixel crosses
    # a lattice boundary the two copies get different keys and both survive.
    # The damage is silent and reads as a stutter -- "Riverside, Riverside,
    # California, California" -- which then breaks the address parse rather
    # than announcing itself. Comparing distances has no boundaries to fall
    # across.
    #
    # Same text within DEDUPE_PX in both axes is the same word. The nearest
    # genuine repeat in this table is a city name appearing in the address and
    # again in the description, which are different columns and hundreds of
    # pixels apart.
    kept: list[dict] = []
    by_text: dict[str, list[dict]] = {}
    for word in sorted(raw, key=lambda d: -d["conf"]):
        near = by_text.setdefault(word["text"], [])
        if any(abs(o["cx"] - word["cx"]) <= DEDUPE_PX
               and abs(o["cy"] - word["cy"]) <= DEDUPE_PX for o in near):
            continue
        near.append(word)
        kept.append(word)
    return sorted(kept, key=lambda d: (d["cy"], d["cx"]))


def column_bounds(words: list[dict], min_gutter: int = MIN_GUTTER,
                  fraction: float = GUTTER_FRACTION) -> list[int]:
    """Cut points between columns, found from thin vertical bands.

    Projects every word box onto the x axis, counts how many words cover each
    pixel column, and cuts at the middle of each sustained low-density run.
    Returns boundaries including 0 and the right edge, so consecutive pairs
    are column spans.

    Density, not emptiness -- see `GUTTER_FRACTION`. Over hundreds of rows
    some description always overflows into the gap, so testing for zero
    coverage finds nothing and reports the whole table as one column.
    """
    if not words:
        return [0, 1]
    right = max(w["x"] + w["w"] for w in words) + 1
    cover = [0] * right
    for w in words:
        for x in range(max(0, w["x"]), min(right, w["x"] + w["w"])):
            cover[x] += 1

    cutoff = max(cover) * fraction
    bounds, run_start = [0], None
    for x in range(right):
        if cover[x] <= cutoff:
            if run_start is None:
                run_start = x
        else:
            if run_start is not None and x - run_start >= min_gutter:
                bounds.append((run_start + x) // 2)
            run_start = None
    # A trailing low-density run is the right margin, not a gutter: cutting
    # there would append a final empty column that every consumer then has to
    # know to ignore.
    bounds.append(right)
    return bounds


def _column_of(word: dict, bounds: list[int]) -> int:
    """Index of the column a word's CENTRE falls in.

    Centre, not left edge: a long description that overhangs its gutter by a
    few pixels still belongs to the column holding most of it.
    """
    for i in range(len(bounds) - 1):
        if bounds[i] <= word["cx"] < bounds[i + 1]:
            return i
    return len(bounds) - 2


def _ends_its_line(word: dict, words: list[dict]) -> bool:
    """True if nothing in the address column sits to this word's right.

    THE DISTINCTION THIS DRAWS, AND WHY IT IS NOT OPTIONAL
    -----------------------------------------------------
    A US street address contains TWO five-digit numbers and only one of them
    is a postal code:

        20920 Krameria Ave, March Air Reserve Base, California, USA, 92518
        ^^^^^ house number                                          ^^^^^ ZIP

    Both match `\\d{5}`. Treating the house number as a row anchor invents a
    facility -- measured here as a row containing the fragment "20920 Krameria
    Ave, March Air" and nothing else, while the real facility lost its first
    address line. Two damaged rows, no error, and the row count looks right.

    Position separates them cleanly: a house number is followed by the street
    name on the same printed line, a postal code ends the address. Testing for
    "leftmost" instead would fail, because a postal code that wraps onto a line
    of its own is both leftmost AND rightmost.

    PUNCTUATION DOES NOT COUNT AS SOMETHING TO THE RIGHT. The table is drawn
    with ruled borders, and a vertical rule OCRs as `|` sitting just right of
    the last real word -- so "94561 |" would be read as a postal code with
    something after it, the anchor would be rejected, and that facility would
    merge into its neighbour. Observed on exactly that ZIP before this filter
    existed.
    """
    return not any(o["cx"] > word["cx"] + 4
                   and abs(o["cy"] - word["cy"]) <= 8
                   and any(ch.isalnum() for ch in o["text"])
                   for o in words)


def _lines(ws: list[dict], gap: int = LINE_GAP_PX) -> list[list[dict]]:
    """Group words into the printed lines they were printed on.

    THE LATTICE BUG THIS REPLACES
    -----------------------------
    Reading order inside a cell used to be `sort(key=(cy // 12, cx))`, which
    puts every word into a fixed 12-pixel band. A fixed lattice has EDGES, and
    words sharing a printed line straddle them. Measured, from the delivery
    station table:

        cy=1186 'Road,'   -> band 98
        cy=1188 'Higley'  -> band 99      same printed line, two bands apart

    "Higley" then sorts AFTER everything else on its own line and lands beside
    the first word of the line below, and the cell reads

        3115 N. Road, Mesa, Higley Phoenix, Arizona, USA, 85215

    instead of "3115 N. Higley Road, Mesa, Arizona, USA, 85215". The street
    loses its name and the city gains a word. It is silent -- the row still has
    a ZIP, a state and a plausible-looking street -- and it is exactly the
    damage `docs/data/GEOCODING.md` sec.5 measured as a 22-point geocoding loss
    on the OCR'd rows. `9807 E. Road, Prescott Valley Valley` and `1900 Pine
    Street North Little, Rock` are the same fault, one band boundary each.

    Clustering on the GAP between neighbours has no edges to fall across, so
    the grouping depends on the text's own spacing rather than on where the
    origin happens to be. The one thing a gap can still get wrong is a MARK
    parked between two lines, which `_unbridge` repairs.
    """
    out: list[list[dict]] = []
    for group in _cluster(ws, gap):
        span = group[-1]["cy"] - group[0]["cy"]
        out.extend([group] if span <= MAX_LINE_SPAN_PX
                   else _unbridge(group, gap))
    return out


def _cluster(ws: list[dict], gap: int) -> list[list[dict]]:
    """Words in y order, cut wherever the step to the next exceeds `gap`."""
    out: list[list[dict]] = []
    previous: int | None = None
    for w in sorted(ws, key=lambda d: d["cy"]):
        if previous is None or w["cy"] - previous > gap:
            out.append([])
        out[-1].append(w)
        previous = w["cy"]
    return out


def _unbridge(group: list[dict], gap: int) -> list[list[dict]]:
    """Re-split one cluster that spans more than a printed line can.

    Reached only when a cluster is too tall to be one line, which happens when
    a MARK sat between two lines and joined them -- see `MARK_HEIGHT_RATIO`.
    The lines are then re-found from body text alone and the marks attached to
    whichever is nearest.

    Splitting on height UNCONDITIONALLY does not work, and the rows that prove
    it are the ones whose postal code wraps onto a line of its own: OCR boxes
    `92240` at 24 px because it takes in the ruled border under it, so the ZIP
    is "a mark" by height, its line has no body text, and the ZIP gets pulled
    up into the city line. Splitting only a cluster that is ALREADY impossible
    leaves those rows alone -- their lines are 14 px apart and were never
    bridged.
    """
    heights = sorted(w["h"] for w in group)
    typical = heights[len(heights) // 2] or 1
    body = [w for w in group
            if typical / MARK_HEIGHT_RATIO <= w["h"]
            <= typical * MARK_HEIGHT_RATIO]
    lines = _cluster(body, gap)
    if len(lines) < 2:
        return [group]

    body_ids = {id(w) for w in body}
    # Distance to the NEAREST WORD of a line, not to the line's midpoint: a
    # line of one word and a line of five are equally close to a mark sitting
    # one step below either. Ties go to the line ABOVE, because a mark between
    # two lines is usually punctuation trailing the line it was printed on
    # rather than leading the next one.
    def nearest(w: dict) -> int:
        return min(range(len(lines)),
                   key=lambda k: min(abs(o["cy"] - w["cy"]) for o in lines[k]))

    for w in group:
        if id(w) not in body_ids:
            lines[nearest(w)].append(w)
    return lines


def _header_bottom(words: list[dict]) -> int:
    """y below which the table's column HEADING has ended, or -1 if none.

    The heading is a printed row like any other and the OCR reads it like any
    other, so its words fall above the first ZIP anchor and join row 0. The
    observed damage is the first facility of a table reading

        ; Location 6735 Trippel Road, Theodore, Alabama, USA, 36582

    -- the `Location` column heading and the `|` rule beside it, prepended to a
    real address, which then fails to geocode. Every table in the document is
    affected and two of the thirteen (the `_part2` continuations) have no
    heading at all, so the band is DETECTED rather than assumed.

    Detection is by heading vocabulary inside the top `HEADER_MAX_Y` pixels,
    not by "the first band is the heading": the continuation tables open on a
    data row, and cutting it would lose a facility.
    """
    top = [w for w in words if w["cy"] < HEADER_MAX_Y]
    if not top:
        return -1
    hits = [w for w in top
            if re.sub(r"[^a-z]", "", w["text"].lower()) in HEADER_WORDS]
    if len({re.sub(r"[^a-z]", "", w["text"].lower()) for w in hits}) \
            < HEADER_MIN_WORDS:
        return -1
    bottom = max(w["cy"] for w in hits)
    # A heading set in two lines -- "Square / Feet", "Year / Opened" -- may
    # have its second line missed by the vocabulary test when OCR mangles it
    # ("(Gpened"). Absorb any band that follows within one heading line gap.
    for line in _lines(top):
        low, high = min(w["cy"] for w in line), max(w["cy"] for w in line)
        if bottom < low <= bottom + HEADER_JOIN_PX:
            bottom = high
    return bottom


#: A postal code whose ZIP+4 tail did not fit on the line: "85034-".
TRUNCATED_ZIP_RE = re.compile(r"\d{5}-$")

#: What such a tail looks like on the line below: "6852", and nothing else.
ZIP_TAIL_RE = re.compile(r"\d{1,4}[.,]?$")


def _reunite_postcode_tails(rows: list[dict[int, list[dict]]]) -> None:
    """Give a wrapped ZIP+4 tail back to the row it came off.

    A row is a band ABOVE its anchor, and the anchor is the postal code on the
    row's last printed line. When the +4 does not fit, MWPVL wraps it onto a
    line of its own BELOW the anchor -- which is below the row -- so it is
    assigned to the row underneath and lands at the front of that row's
    address:

        row 7  2050 East Riverview Drive, Phoenix, Arizona, USA, 85034-
        row 8  6852                                    <- the tail of 85034
               7300 N Silverbell Rd, Tucson, Arizona, USA, 85743

        parsed street of row 8: "6852 7300 N Silverbell Rd"

    The house number is then wrong and the row cannot geocode. 26 rows in the
    delivery station tables are damaged this way.

    The evidence that a leading number is a tail rather than a house number is
    NOT the number itself. Three things have to hold together:

    * the row above ends in a cut-off postal code, "30122-";
    * the number is ALONE on its printed line -- a real street's first line
      carries the street name beside the number;
    * the row still has a house number once it is taken away.

    The third is what the first version got wrong. "3120 / Lakepoint Parkway,
    Cartersville, Georgia, USA, 30121" satisfies the first two and 3120 is the
    house number of ATL6, which wrapped for the same reason a +4 does. With
    the remainder starting "Lakepoint", there is no house number left and the
    number stays where it is; with the remainder starting "7300 N Silverbell
    Rd" or "845 Paragon Way", there already is one and the leading number is
    not a second.

    Nothing is deleted or rewritten; the word moves between two cells.
    """
    for i in range(1, len(rows)):
        for col, ws in rows[i].items():
            above = rows[i - 1].get(col)
            if not above or not ws:
                continue
            if not any(TRUNCATED_ZIP_RE.search(w["text"])
                       for w in _lines(above)[-1]):
                continue
            lines = _lines(ws)
            if len(lines) < 2 or len(lines[0]) != 1:
                continue
            leftmost = min(lines[1], key=lambda w: w["cx"])
            if (ZIP_TAIL_RE.fullmatch(lines[0][0]["text"])
                    and leftmost["text"][:1].isdigit()):
                above.append(lines[0][0])
                ws[:] = [w for w in ws if w is not lines[0][0]]


def _collapse(ys: list[int], gap: int = 20) -> list[int]:
    """Merge anchors closer together than one printed line."""
    out: list[int] = []
    for y in sorted(ys):
        if not out or y - out[-1] > gap:
            out.append(y)
    return out


def _zip_anchors(by_col: dict[int, list[dict]]) -> dict[int, list[int]]:
    """Candidate anchors from US postal codes, per column."""
    per_col: dict[int, list[int]] = {}
    for col_i, col_words in by_col.items():
        for w in col_words:
            if ZIP_RE.match(w["text"]) and _ends_its_line(w, col_words):
                per_col.setdefault(col_i, []).append(w["cy"])
    return per_col


def _code_anchors(by_col: dict[int, list[dict]]) -> dict[int, list[int]]:
    """Candidate anchors from Amazon facility codes, per column.

    The fallback for tables with no US postal code. A code -- DBM3, YYC1,
    MMG1 -- is short, always on one printed line, and sits vertically centred
    in its row rather than on the last line, which makes it a CLEANER anchor
    than a ZIP where it is available. It is the fallback rather than the
    default only because the code cell is sometimes blank in the US tables,
    and a missing anchor loses a whole facility.
    """
    per_col: dict[int, list[int]] = {}
    for col_i, col_words in by_col.items():
        for w in col_words:
            if CODE_RE.fullmatch(w["text"].strip().upper()):
                per_col.setdefault(col_i, []).append(w["cy"])
    return per_col


def row_anchors(words: list[dict], bounds: list[int]) -> tuple[list[int], int]:
    """y-centres of the rows, and the index of the column that anchored them.

    Tries US postal codes first and Amazon facility codes second.

    WHY A FALLBACK IS NEEDED AT ALL
    -------------------------------
    Three of the thirteen tables are rest-of-world -- 61,428 of the document's
    152,915 pixel-rows, 40% of it -- and their addresses end in Canadian,
    Japanese and British postal codes, none of which are five digits. Anchoring
    only on `\\d{5}` finds almost nothing there, and the failure is quiet: the
    table parses to a handful of enormous merged rows and reports a row count,
    not an error.

    The anchor COLUMN is found by counting in both strategies rather than
    assumed, because the rest-of-world tables carry a flag glyph and a Country
    column ahead of the address, shifting every field one to the right.

    A strategy is accepted only if it finds at least `MIN_ANCHOR_DENSITY` of
    the rows the image's height implies. A printed row is about 61 px here --
    measured, 535 rows over 32,729 px on the delivery station table -- so a
    strategy returning far fewer has not found the rows; it has found
    something else that happens to match its pattern.
    """
    by_col: dict[int, list[dict]] = {}
    for w in words:
        by_col.setdefault(_column_of(w, bounds), []).append(w)

    height = max((w["cy"] for w in words), default=0)
    expected = height / ROW_HEIGHT_PX if height else 0

    best: tuple[list[int], int] = ([], -1)
    for finder in (_zip_anchors, _code_anchors):
        per_col = finder(by_col)
        if not per_col:
            continue
        col = max(per_col, key=lambda c: len(per_col[c]))
        anchors = _collapse(per_col[col])
        if not expected or len(anchors) >= expected * MIN_ANCHOR_DENSITY:
            return anchors, col
        if len(anchors) > len(best[0]):
            best = (anchors, col)
    # Nothing cleared the density bar. Return the better attempt rather than
    # nothing, so the caller sees a thin result it can judge instead of an
    # empty one it cannot tell apart from an absent file.
    return best


def build_rows(words: list[dict], bounds: list[int],
               anchors: list[int]) -> list[dict[int, str]]:
    """Assign every word to a row and a column; join each cell's text.

    A word belongs to the FIRST anchor at or below it. This looks arbitrary
    until the printed layout is measured, and then it is forced:

        y=2617   275 Valencia Avenue, Brea,          address, line 1
        y=2625   DJT4 | 181,500 | 2025 | Delivery... everything else
        y=2634   California USA. 92823               address, line 3 <- ANCHOR

    The postal code sits on the LAST line of its row, not the middle, so a
    row occupies the space ABOVE its anchor. Splitting at the midpoint between
    consecutive anchors -- the obvious choice, and the first thing tried
    here --
    fails because row heights vary with how far the address wraps: measured
    gaps of 48 and 64 px in the same table put the midpoint above the next
    row's first line, which then joins the previous facility's address. The
    result is two corrupted rows and no error.

    TOLERANCE is half a printed line, because the anchor is the postal code's
    own centre and other words on that line scatter a few pixels around it.

    Words below the last anchor join the final row rather than being dropped.
    """
    if not anchors:
        return []
    tolerance = 8

    # The column HEADING is not a facility. Dropped here rather than in
    # `load_words` so that `column_bounds` and `row_anchors` still see exactly
    # the words they saw before: the heading sits in the same columns as the
    # data and helps rather than hinders the gutter measurement, and removing
    # it upstream would move boundaries for no gain.
    cut = _header_bottom(words)
    if cut >= 0:
        words = [w for w in words if w["cy"] > cut + 4]

    rows: list[dict[int, list[dict]]] = [{} for _ in anchors]
    for w in words:
        target = w["cy"] - tolerance
        lo, hi = 0, len(anchors) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if anchors[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        rows[lo].setdefault(_column_of(w, bounds), []).append(w)

    _reunite_postcode_tails(rows)

    out: list[dict[int, str]] = []
    for cells in rows:
        row: dict[int, str] = {}
        for col, ws in cells.items():
            # Reading order WITHIN a cell: top to bottom, then left to right.
            # A wrapped address must rejoin as "6910 S.E. Four Mile Drive,
            # Ankeny, Iowa, USA, 50021" and not in x order, which would
            # interleave the two printed lines. Lines are found by gap, not by
            # a fixed band -- see `_lines` for what the fixed band did.
            ordered = [w for line in _lines(ws)
                       for w in sorted(line, key=lambda d: d["cx"])]
            row[col] = " ".join(w["text"] for w in ordered)
        out.append(row)
    return out
