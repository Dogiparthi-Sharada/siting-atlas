"""Turn the OCR'd MWPVL tables into one CSV of facilities.

    python -m siting_atlas.ingest.mwpvl_tables

Reads every `data/raw/mwpvl/tsv/<NN>_<table>/` directory written by
`tools/ocr/grid_ocr.py`, reconstructs each table's grid, reads the fields,
and writes `data/interim/mwpvl_facilities.csv` plus a quality report.

WHAT THIS IS FOR
----------------
Every facility in the project's panel has an UPPER bound on its opening date
-- an OSHA inspection proves the building was operating by then -- and no
lower bound, so the panel can say "open by 2019" and never "opened in 2019".
That single gap blocks the lag guard on the warehousing covariate, blocks any
use of time in the choice model, and is what killed the hazard model. Satellite
imagery was tried and failed (`docs/data/SATELLITE.md`). MWPVL's tables state
the opening month and year outright, which is why this pipeline exists.

WHAT THIS IS NOT
----------------
Not a census and not ground truth. MWPVL says so about this very table:
"The data concerning this network is challenging to track so we provide the
best information available." Nothing here is cleaned against plausibility --
values pass through as read, including a year of 9022 -- because the project
holds something better than plausibility: 409 cities where OSHA proves a
building was already operating. Contradictions are found there, against
evidence, and recorded. See `docs/data/MWPVL_2025.md`.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure
from . import mwpvl_fields as fields
from . import mwpvl_grid as grid

REPO = Path(__file__).resolve().parents[3]
TSV = REPO / "data" / "raw" / "mwpvl" / "tsv"
OUT = REPO / "data" / "interim" / "mwpvl_facilities.csv"
REPORT = REPO / "outputs" / "metrics" / "mwpvl_extraction.json"

COLUMNS = ("table", "row", "region", "code", "street", "city", "addr_region",
           "postcode", "sqft", "open_month", "open_year", "open_quarter",
           "date_precision", "description", "address_raw") + \
    tuple(name for name, _ in fields.FLAGS)


def parse_table(directory: Path) -> tuple[list[dict], dict]:
    """Facilities from one table directory, plus what went wrong."""
    words = grid.load_words(directory)
    stats = {"table": directory.name, "words": len(words), "rows": 0,
             "with_postcode": 0, "with_year": 0, "with_month": 0,
             "with_sqft": 0, "with_code": 0}
    if not words:
        return [], stats

    bounds = grid.column_bounds(words)
    anchors, _ = grid.row_anchors(words, bounds)
    rows = grid.build_rows(words, bounds, anchors)
    cols = fields.identify_columns(rows)
    stats["rows"] = len(rows)
    stats["columns"] = {k: int(v) for k, v in cols.items()}

    def cell(row, field):
        """One cell's text, or "" when this table has no such column."""
        idx = cols.get(field)
        return row.get(idx, "") if idx is not None else ""

    out = []
    for i, row in enumerate(rows):
        address = fields.parse_address(cell(row, "address"))
        date = fields.parse_date(cell(row, "date"))
        desc = cell(row, "description")
        rec = {
            "table": directory.name, "row": i,
            "region": cell(row, "region").strip(" |"),
            "code": fields.parse_code(cell(row, "code")),
            "sqft": fields.parse_sqft(cell(row, "sqft")),
            "open_month": date["month"], "open_year": date["year"],
            "open_quarter": date["quarter"],
            "date_precision": date["precision"],
            "description": " ".join(desc.split()),
        }
        rec.update(address)
        rec.update(fields.parse_flags(desc))
        out.append(rec)

        stats["with_postcode"] += bool(rec["postcode"])
        stats["with_year"] += bool(rec["open_year"])
        stats["with_month"] += bool(rec["open_month"])
        stats["with_sqft"] += bool(rec["sqft"])
        stats["with_code"] += bool(rec["code"])
    return out, stats


def main() -> int:
    # Stamped so the extraction artefact can be told apart from the next
    # one. `docs/AUDIT_2026_09_14.md` sec.6.5: the project's tie-break rule is
    # "where a run_id exists, the artefact wins", and it cannot be applied to
    # an artefact that carries none.
    init_run()
    configure()

    directories = sorted(d for d in TSV.glob("*") if d.is_dir())
    if not directories:
        raise SystemExit(
            f"  no OCR output in {TSV}\n"
            "  run: bash tools/ocr/grid_ocr.py\n")

    records: list[dict] = []
    report: list[dict] = []
    print(f"\n  {'table':38} {'rows':>7} {'zip':>6} {'year':>6} "
          f"{'month':>6} {'sqft':>6}")
    print("  " + "-" * 74)
    for directory in directories:
        rows, stats = parse_table(directory)
        records += rows
        report.append(stats)
        print(f"  {directory.name:38} {stats['rows']:7d} "
              f"{stats['with_postcode']:6d} {stats['with_year']:6d} "
              f"{stats['with_month']:6d} {stats['with_sqft']:6d}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    dated = sum(1 for r in records if r["open_year"])
    monthly = sum(1 for r in records if r["open_month"])
    flagged = sum(1 for r in records if r["not_confirmed"])
    print("  " + "-" * 74)
    zipped = sum(1 for r in records if r["postcode"])
    n = max(1, len(records))
    print(f"  {'TOTAL':38} {len(records):7d} {zipped:6d} "
          f"{dated:6d} {monthly:6d}")
    print(f"\n  {len(records)} facilities, {dated} with a year "
          f"({100 * dated / n:.0f}%), {monthly} with a month "
          f"({100 * monthly / n:.0f}%)")
    print(f"  {flagged} flagged 'not confirmed' by MWPVL itself")
    print(f"  -> {OUT}")

    write_json(REPORT,
               {"tables": report, "facilities": len(records),
                "with_year": dated, "with_month": monthly,
                "not_confirmed": flagged})
    print(f"  -> {REPORT}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
