"""Shared fixtures: a throwaway data root, so no test touches the real tree.

``siting_atlas.common.paths`` resolves its constants at import time, and every
module reads them as attributes at call time. Patching the attributes is
therefore enough to relocate an entire layer onto tmp_path, with no network,
no warehouse and no 1M-row panel.
"""

from __future__ import annotations

import zipfile

import pytest

from siting_atlas.common import paths as _paths


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """Redirect every data directory at a fresh tmp_path."""
    layout = {"ROOT": tmp_path, "DATA": tmp_path / "data",
              "RAW": tmp_path / "data" / "raw",
              "INTERIM": tmp_path / "data" / "interim",
              "PROCESSED": tmp_path / "data" / "processed",
              "EXTERNAL": tmp_path / "data" / "external",
              "OUTPUTS": tmp_path / "outputs",
              "MODELS": tmp_path / "outputs" / "models",
              "METRICS": tmp_path / "outputs" / "metrics",
              "TABLES": tmp_path / "outputs" / "tables",
              "RUN_FIGURES": tmp_path / "outputs" / "figures"}
    for name, value in layout.items():
        monkeypatch.setattr(_paths, name, value)
    monkeypatch.setattr(_paths, "PANEL", layout["PROCESSED"] / "panel.parquet")
    monkeypatch.setattr(_paths, "WAREHOUSE",
                        layout["PROCESSED"] / "siting_atlas.duckdb")
    monkeypatch.setattr(_paths, "_WRITABLE",
                        tuple(layout[k] for k in
                              ("RAW", "INTERIM", "PROCESSED", "EXTERNAL",
                               "OUTPUTS", "MODELS", "METRICS", "TABLES",
                               "RUN_FIGURES")))
    for value in layout.values():
        value.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def write_zip(data_root):
    """Write ``text`` as the single member of a zip under data/raw/<folder>."""
    def _write(folder: str, member: str, text: str, name: str = "src.zip"):
        target = _paths.RAW / folder
        target.mkdir(parents=True, exist_ok=True)
        archive = target / name
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr(member, text)
        return archive
    return _write


# ---------------------------------------------------------------------------
# MWPVL: a synthetic OCR'd table, laid out the way the real one is
# ---------------------------------------------------------------------------
#: (region, code, address, sqft, date, description). Six facilities, because
#: `mwpvl_grid.row_anchors` judges an anchoring strategy against the row count
#: the image height implies and a two-row table clears no such bar.
MWPVL_CELLS = (
    ("California", "DAX8", "1910 E Vista Way, Vista, California, USA, 92081",
     "142,800", "October 2019", "Delivery Station"),
    ("Iowa", "DSM5",
     "6910 S.E. Four Mile Drive, Ankeny, Iowa, USA, 50021",
     "120,000", "January 2022", "Delivery Station"),
    ("Texas", "DFW9", "2601 W Pioneer Pkwy, Arlington, Texas, USA, 76013",
     "88,500", "2025", "Delivery Station not yet confirmed"),
    ("Ohio", "DCM2", "6210 Pontiac Drive, Columbus, Ohio, USA, 43228",
     "95,000", "March 2021", "Delivery Station"),
    ("Utah", "DUT1", "777 N 5600 W, Salt Lake City, Utah, USA, 84116",
     "110,000", "June 2020", "Delivery Station"),
    ("Nevada", "DLV3",
     "4550 Mitchell St, North Las Vegas, Nevada, USA, 89081",
     "101,000", "2024", "Delivery Station"),
)

#: Left edge of each column. The gaps are the gutters `column_bounds` has to
#: find; the address column is wide because its text wraps into it.
_MWPVL_X = (0, 120, 240, 700, 800, 920)

_TSV_HEADER = ("level\tpage\tblock\tpar\tline\tword\t"
               "left\ttop\twidth\theight\tconf\ttext")


def _address_lines(text: str) -> list[str]:
    """Break an address the way the printed table does: three lines."""
    first = text.index(",") + 1
    second = text.rindex(",", 0, text.rindex(",")) + 1
    return [text[:first].strip(), text[first:second].strip(),
            text[second:].strip()]


@pytest.fixture
def mwpvl_tsv_dir(tmp_path):
    """Write one table directory of tesseract TSV, and return its path.

    Real OCR output, in miniature: one word per line with a pixel box, the
    address wrapped over three printed lines so that reading order interleaves
    it with its neighbours, and one strip file rather than thirty.
    """
    def _write(name: str = "08_us_delivery_station",
               cells=MWPVL_CELLS, root=None):
        directory = (root or tmp_path) / name
        directory.mkdir(parents=True, exist_ok=True)
        lines = [_TSV_HEADER]
        for i, row in enumerate(cells):
            top = 100 + i * 61
            for column, (x, text) in enumerate(zip(_MWPVL_X, row,
                                                   strict=True)):
                parts = _address_lines(text) if column == 2 else [text]
                for line_i, part in enumerate(parts):
                    cursor = x
                    for token in part.split():
                        width = 8 * len(token)
                        lines.append(
                            f"5\t1\t1\t1\t1\t1\t{cursor}\t{top + line_i * 18}"
                            f"\t{width}\t12\t90\t{token}")
                        cursor += width + 6
        (directory / "strip_000.tsv").write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")
        return directory
    return _write
