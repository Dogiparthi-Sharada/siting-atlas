"""Grid recovery from OCR word boxes: the three defects that were silent.

Every failure this file guards against produced PLAUSIBLE OUTPUT and no
error. A table that reports six columns as one, a house number promoted to a
row anchor, a word that survives deduplication twice — none of them raise,
none of them change a row count enough to notice, and all three were found by
measuring rather than by the pipeline complaining.

Each of the first three tests is written so that the fixture PROVES it
discriminates: it also exercises the superseded rule and asserts that the
superseded rule gets the wrong answer on the same input. A regression test
whose fixture passes under the old code is not a regression test.
"""

from __future__ import annotations

import pytest

from siting_atlas.ingest import mwpvl_grid as grid

TSV_HEADER = ("level\tpage\tblock\tpar\tline\tword\t"
              "left\ttop\twidth\theight\tconf\ttext")


def _tsv_row(x: int, y: int, w: int, h: int, conf: float, text: str) -> str:
    """One tesseract `--psm 6 tsv` line."""
    return f"5\t1\t1\t1\t1\t1\t{x}\t{y}\t{w}\t{h}\t{conf}\t{text}"


def _word(x: int, y: int, w: int, text: str, h: int = 12) -> dict:
    """A word box shaped the way `load_words` emits them."""
    return {"x": x, "y": y, "w": w, "h": h, "conf": 90.0, "text": text,
            "cx": x + w // 2, "cy": y + h // 2}


# ---------------------------------------------------------------------------
# column_bounds — the zero-coverage rule that found NO columns
# ---------------------------------------------------------------------------
#: Six columns and five gutters, in the proportions of the delivery station
#: table. Gutter widths are 20px, comfortably over MIN_GUTTER.
_SPANS = ((0, 80), (100, 260), (280, 360), (380, 460), (480, 600), (620, 800))


@pytest.fixture
def six_column_table() -> list[dict]:
    """Forty rows of six columns, with a few cells that OVERFLOW a gutter.

    The overflow is the whole point. Over hundreds of printed rows some
    description always spills into the gap beside it, so no x column is ever
    completely empty — which is precisely why testing for zero coverage
    reported a six-column table as one column spanning [0, 819].
    """
    words = []
    for r in range(40):
        y = 100 + r * 61
        for i, (lo, hi) in enumerate(_SPANS):
            words.append(_word(lo, y, hi - lo, f"c{i}r{r}"))
    for r in (3, 17):
        y = 100 + r * 61 + 20
        for lo, hi in ((0, 110), (100, 285), (280, 385), (380, 485),
                       (480, 625)):
            words.append(_word(lo, y, hi - lo, "overflow"))
    return words


def test_column_bounds_finds_every_gutter_a_shallow_one_included(
        six_column_table):
    bounds = grid.column_bounds(six_column_table)
    # Six columns is six spans, which is seven boundaries including 0 and the
    # right edge. Anything less and some pair of fields has been fused.
    assert len(bounds) == 7, bounds
    assert bounds[0] == 0
    # Each cut lands inside its gutter, not inside a column.
    for cut, (left, right) in zip(bounds[1:-1],
                                  zip([s[1] for s in _SPANS[:-1]],
                                      [s[0] for s in _SPANS[1:]],
                                      strict=True), strict=True):
        assert left <= cut <= right, (cut, left, right)


def test_the_zero_coverage_rule_reports_the_whole_table_as_one_column(
        six_column_table):
    """The defect, reproduced on the same fixture.

    `fraction=0.0` is the superseded rule: cut only where NOTHING covers x.
    If this ever starts returning seven bounds the fixture has lost its
    overflow words and the test above has stopped proving anything.
    """
    assert grid.column_bounds(six_column_table, fraction=0.0) == [0, 801]


def test_column_bounds_on_an_empty_table_does_not_divide_by_a_missing_max():
    assert grid.column_bounds([]) == [0, 1]


# ---------------------------------------------------------------------------
# row_anchors / _ends_its_line — the five-digit STREET number
# ---------------------------------------------------------------------------
#: Six facilities. The second is the measured failure: `20920 Krameria Ave`
#: opens with a five-digit house number that matches ZIP_RE exactly as well
#: as the real postal code at the end of the address does. The third ends in
#: a ruled border that OCRs as `|`, which must NOT disqualify its anchor.
_FACILITIES = (
    ("Ohio", ("6210 Pontiac Drive,", "Columbus, Ohio,", "USA, 43228")),
    ("California", ("20920 Krameria Ave,", "March Air Reserve Base,",
                    "California, USA, 92518")),
    ("Texas", ("2601 W Pioneer Pkwy,", "Arlington, Texas,", "USA, 76013 |")),
    ("Iowa", ("6910 S.E. Four Mile Drive,", "Ankeny, Iowa,", "USA, 50021")),
    ("Utah", ("777 N 5600 W,", "Salt Lake City, Utah,", "USA, 84116")),
    ("Nevada", ("4550 Mitchell St,", "North Las Vegas, Nevada,",
                "USA, 89081")),
)


@pytest.fixture
def wrapped_addresses() -> list[dict]:
    """A region column and an address column that wraps over three lines."""
    words = []
    for i, (region, lines) in enumerate(_FACILITIES):
        top = 100 + i * grid.ROW_HEIGHT_PX
        words.append(_word(0, top, 70, region))
        for line_i, line in enumerate(lines):
            y, x = top + line_i * 20, 120
            for token in line.split(" "):
                width = 8 * len(token)
                words.append(_word(x, y, width, token))
                x += width + 6
    return words


def test_a_five_digit_house_number_does_not_invent_a_row(wrapped_addresses):
    bounds = grid.column_bounds(wrapped_addresses)
    anchors, _ = grid.row_anchors(wrapped_addresses, bounds)
    assert len(anchors) == len(_FACILITIES)


def test_matching_on_shape_alone_would_have_invented_that_row(
        wrapped_addresses):
    """The defect, reproduced on the same fixture.

    ZIP_RE alone — no `_ends_its_line` — accepts `20920` as readily as it
    accepts `92518`, and the two are 40px apart so `_collapse` keeps both.
    One extra anchor, one facility split in half, no error.
    """
    shape_only = [w["cy"] for w in wrapped_addresses
                  if grid.ZIP_RE.match(w["text"])]
    assert len(grid._collapse(shape_only)) == len(_FACILITIES) + 1


def test_a_ruled_border_to_the_right_of_a_postcode_still_anchors(
        wrapped_addresses):
    """`76013 |` is a postal code. The `|` is the table's own border."""
    address = [w for w in wrapped_addresses if w["cx"] > 100]
    zip_word = next(w for w in address if w["text"] == "76013")
    assert grid._ends_its_line(zip_word, address)


def test_a_house_number_is_rejected_because_something_follows_it(
        wrapped_addresses):
    address = [w for w in wrapped_addresses if w["cx"] > 100]
    house = next(w for w in address if w["text"] == "20920")
    assert not grid._ends_its_line(house, address)


def test_build_rows_keeps_each_wrapped_address_whole(wrapped_addresses):
    bounds = grid.column_bounds(wrapped_addresses)
    anchors, _ = grid.row_anchors(wrapped_addresses, bounds)
    rows = grid.build_rows(wrapped_addresses, bounds, anchors)

    assert len(rows) == len(_FACILITIES)
    joined = [" ".join(r[c] for c in sorted(r)) for r in rows]
    # The house number and the postal code belong to ONE row. Before
    # `_ends_its_line` this address arrived as a fragment ending "March Air"
    # and a second row that had lost its first line.
    krameria = next(t for t in joined if "Krameria" in t)
    assert "20920" in krameria and "92518" in krameria
    for region, _ in _FACILITIES:
        assert any(t.startswith(region) for t in joined), region


def test_row_anchors_falls_back_to_facility_codes_outside_the_us():
    """Rest-of-world tables have no five-digit postal code at all.

    40% of the document. Without the fallback the table parses to a handful
    of enormous merged rows and reports a row count rather than an error.
    """
    words = []
    for i, (code, line) in enumerate((("YYC1", "261185 Wagon Wheel Way,"),
                                      ("YYZ4", "8050 Heritage Road,"),
                                      ("YVR3", "18988 96 Ave, Surrey BC"),
                                      ("YEG1", "18291 118 Ave NW"),
                                      ("YOW3", "222 Citigate Drive"),
                                      ("YHM1", "2750 Peddie Road"))):
        top = 100 + i * grid.ROW_HEIGHT_PX
        words.append(_word(0, top, 40, code))
        x = 120
        for token in line.split(" "):
            width = 8 * len(token)
            words.append(_word(x, top, width, token))
            x += width + 6
    bounds = grid.column_bounds(words)
    anchors, col = grid.row_anchors(words, bounds)
    assert len(anchors) == 6
    # The anchor column is the code column, found by counting rather than
    # assumed — rest-of-world tables shift every field one to the right.
    assert col == 0


def test_build_rows_with_no_anchors_returns_nothing_rather_than_one_big_row():
    assert grid.build_rows([_word(0, 0, 10, "x")], [0, 20], []) == []


# ---------------------------------------------------------------------------
# load_words — the 8px dedup lattice that let a duplicate through
# ---------------------------------------------------------------------------
@pytest.fixture
def overlapping_strips(tmp_path):
    """Two strips whose overlap region OCR'd the same word twice.

    The two readings differ by ONE pixel in y, and they straddle an 8px
    lattice boundary. That is the whole defect: the superseded key
    `(x // 8, y // 8, text)` puts them in different cells, both survive, and
    the row reads "Riverside, Riverside".
    """
    assert 95 // 8 != 96 // 8, "the fixture must straddle a lattice boundary"
    directory = tmp_path / "08_us_delivery_station"
    directory.mkdir()
    (directory / "strip_000.tsv").write_text("\n".join([
        TSV_HEADER,
        _tsv_row(100, 95, 72, 12, 91, "Riverside"),
        # A GENUINE repeat: the city name again, hundreds of px away in the
        # description column. Deduplicating by string would delete it.
        _tsv_row(600, 95, 72, 12, 88, "Riverside"),
        _tsv_row(100, 140, 60, 12, 12, "speck"),
        "5\t1\t1\t1\t1\t1\t100\t160\t60\t12",
    ]) + "\n", encoding="utf-8")
    (directory / "strip_001.tsv").write_text("\n".join([
        TSV_HEADER,
        _tsv_row(100, 96, 72, 12, 89, "Riverside"),
    ]) + "\n", encoding="utf-8")
    return directory


def test_the_same_word_read_by_two_strips_survives_once(overlapping_strips):
    words = grid.load_words(overlapping_strips)
    texts = [w["text"] for w in words]
    assert texts.count("Riverside") == 2, (
        "two GENUINE occurrences — the address and the description — and no "
        "third from the strip overlap")
    assert sorted(w["x"] for w in words if w["text"] == "Riverside") \
        == [100, 600]


def test_an_8px_lattice_key_would_have_kept_both_copies(overlapping_strips):
    """The defect, reproduced on the same fixture."""
    raw = []
    for path in sorted(overlapping_strips.glob("*.tsv")):
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            f = line.split("\t")
            if len(f) >= 12 and float(f[10]) >= grid.MIN_CONF:
                raw.append((int(f[6]) // 8, int(f[7]) // 8, f[11]))
    assert sum(1 for k in set(raw) if k[2] == "Riverside") == 3


def test_a_faint_word_and_a_truncated_line_are_dropped(overlapping_strips):
    words = grid.load_words(overlapping_strips)
    assert "speck" not in [w["text"] for w in words]
    assert "short" not in [w["text"] for w in words]


def test_load_words_returns_reading_order(overlapping_strips):
    words = grid.load_words(overlapping_strips)
    assert [(w["cy"], w["cx"]) for w in words] \
        == sorted((w["cy"], w["cx"]) for w in words)


def test_load_words_on_a_directory_with_no_tsvs_is_empty(tmp_path):
    assert grid.load_words(tmp_path) == []
