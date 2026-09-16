"""L3 — the warehouse becomes the one panel every model reads.

Grain: one row per ZCTA per quarter, PANEL_START_YEAR Q1 .. PANEL_END_YEAR Q4.
Dense by construction: every ZCTA gets every quarter whether or not any
source observed it. Filtering to observed rows here would quietly hand the
model a sample-selection bug, because the sources with the best coverage
(Zillow, BPS) are the urban ones.

Three kinds of column:

  levels          ACS 2023 and CBP 2022, repeated down the quarters. Pinned
                  vintages, not a time series — see common.config.
  rates of change rent index and permits, year-on-year percent. These are
                  what actually distinguish a growing ZCTA from a large one.
  availability    ``rent_observed``, explicitly. Read the comment on it.
  quality flags   ``*_topcoded`` / ``*_bottomcoded`` (an ACS censoring code
                  read as a measurement), ``wage_suppressed`` (BLS withheld
                  the cell) and ``open_quarter_imputed`` (the switch-on date
                  is a Q1 convention). None of these changes a value; each
                  says how a value came to be. ``warehouse/flag_gate.py``
                  fails the build if one is computed upstream and lost here,
                  which is what happened to all of them until 2026-09-13.

The target variable
-------------------
``enabled`` is TRUE for a (ZCTA, quarter) inside the catchment of an operating
last-mile facility. ``panel_sql`` declares it typed and NULL so the panel has
one shape whether or not a facility frame is present, and
``warehouse/facilities.attach`` overwrites it in the same build.

**Corrected 2026-09-14.** This docstring used to read *"No target variable.
The facility panel has not arrived, so ``enabled`` is present, all NULL, and
typed."* That stopped being true on 2026-09-13. In the shipped
``data/processed/panel.parquet``: 27,914 of 1,081,312 cells are enabled,
across 1,257 ZCTAs, 912 of which switch on inside the window.

Which facilities set it is a per-build choice, and the default is the
43-row hand-verified pilot — ``facility_load.DEFAULT_FRAME``. The 104-row
national and 700-row expanded frames are opt-in, and opting in writes a
*different file*, because ``panel.parquet`` is what the published figures,
``choice_report.json`` and the proposal were built against:

    python -m siting_atlas.warehouse.panel              # panel.parquet
    python -m siting_atlas.warehouse.panel --coverage
    python -m siting_atlas.warehouse.panel --facility-frame expanded
                                          # -> panel_expanded.parquet

Ever-enabled ZCTAs by frame, measured 2026-09-14: pilot 1,257, national
2,713, expanded 8,937 of 33,791. Those are three different target variables
and no result computed on one transfers to another.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..common import paths
from ..common.context import init_run
from ..common.db import connect
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from . import facilities
from .flag_gate import assert_flags_carried
from .optional import OPTIONAL_SOURCES, block
from .panel_sql import build_sql

_log = get_logger("panel")

__all__ = ["assert_grain", "build_sql", "coverage", "run"]

def assert_grain(db, rows: int, table: str = "panel") -> None:
    """Fail the build unless the panel is exactly one row per ZCTA-quarter.

    Every join in ``_BASE_CTES`` is a LEFT JOIN onto a dense grid, so each one
    is a chance to fan out instead of to enrich: a duplicate
    ``(county_geoid, year)`` in building permits, or a county listed twice in
    the delineation, turns one ZCTA-quarter into two. Both rows look
    perfectly plausible on inspection — only the count betrays it, and
    nothing was counting.

    It holds today because ``ingest.normalise`` de-duplicates both sources,
    which makes the panel correct by luck rather than by contract. This is the
    contract. Cheap: one COUNT DISTINCT against a table already in memory.
    """
    distinct = db.scalar(
        f"SELECT COUNT(*) FROM (SELECT DISTINCT zcta, date_id FROM {table})")
    if rows != distinct:
        worst = db.df(f"""
            SELECT zcta, date_id, COUNT(*) AS n FROM {table}
            GROUP BY 1, 2 HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 3
        """)
        raise ValueError(
            f"panel grain broken: {rows:,} rows for {distinct:,} distinct "
            f"(zcta, date_id) pairs — a source has fanned out. Worst "
            f"offenders:\n{worst.to_string(index=False)}\n"
            f"Check for duplicate keys in building_permits (county_geoid, "
            f"year), cbsa_county (county_geoid) or any optional source.")


def coverage(db, table: str) -> list[dict]:
    """Percent non-null per column — the first thing to look at in review."""
    cols = db.df(f"DESCRIBE {table}")["column_name"].tolist()
    total = db.scalar(f"SELECT COUNT(*) FROM {table}")
    parts = ", ".join(f'COUNT("{c}") AS "{c}"' for c in cols)
    row = db.df(f"SELECT {parts} FROM {table}").iloc[0]
    return [{"column": c, "non_null": int(row[c]),
             "pct": round(100.0 * int(row[c]) / total, 2)} for c in cols]


def panel_path(frame: str) -> Path:
    """Where a frame's panel is written.

    The default frame keeps ``paths.PANEL``; every other frame gets its own
    file. This is the guard, not a convention: there is no argument a caller
    can pass that makes an expanded build land on top of the reference
    artefact, so a published number cannot move by accident.
    """
    if frame == facilities.DEFAULT_FRAME:
        return paths.PANEL
    return paths.PANEL.with_name(f"{paths.PANEL.stem}_{frame}"
                                 f"{paths.PANEL.suffix}")


def run(frame: str | None = None) -> dict:
    """Build the panel from the warehouse and write it out.

    ``frame`` names a facility frame (``facility_load.FACILITY_FRAMES``) and
    decides both the target variable and the output path. ``None`` resolves
    through ``facilities.resolve_frame`` — argument, then
    ``$SITING_ATLAS_FACILITY_FRAME``, then ``DEFAULT_FRAME``.
    """
    frame = facilities.resolve_frame(frame)[0]
    out = panel_path(frame)
    paths.ensure_dirs()
    if not paths.WAREHOUSE.exists():
        raise FileNotFoundError(
            f"{paths.rel(paths.WAREHOUSE)} is missing; run "
            "siting_atlas.warehouse.schema first")

    with traced_layer("L3", f"panel[{frame}] -> {paths.rel(out)}"):
        with connect(paths.WAREHOUSE) as db:
            taken: set[str] = set()
            blocks = []
            with step("optional_sources"):
                for name in OPTIONAL_SOURCES:
                    attached = block(db, name, taken)
                    if attached:
                        taken.update(attached["names"])
                        blocks.append(attached)

            with step("build_panel"):
                db.execute(f"CREATE OR REPLACE TEMP TABLE panel AS "
                           f"{build_sql(blocks)}")
                rows = db.scalar("SELECT COUNT(*) FROM panel")
                assert_grain(db, rows)

            with step("target"):
                enabled = facilities.attach(db, frame=frame)
                cols = coverage(db, "panel")

            # After the target, because facilities.py computes a flag too.
            # A grain contract without a provenance contract lets the panel
            # be exactly the right shape and quietly missing the columns that
            # say how it got that way.
            with step("flag_gate"):
                flags = assert_flags_carried(
                    db, extra=facilities.warehouse_flags(frame))

            with step("write_panel"):
                db.execute("COPY panel TO ? (FORMAT PARQUET)", [str(out)])

        artefact(out, rows=rows, cols=len(cols))
        metric("panel_rows", rows)
        metric("panel_cols", len(cols))
        metric("optional_sources_joined", len(blocks))
        metric("quality_flags_carried", len(flags["carried"]))

    # `facility_frame` and `path` travel in the report because a panel that
    # does not say which frame built it is exactly the confusion the
    # 2026-09-14 audit sec. 2.1 found: three live targets, none labelled.
    return {"rows": rows, "cols": len(cols), "coverage": cols,
            "facility_frame": frame, "path": paths.rel(out),
            "enabled_cells": enabled,
            "optional": [b["names"] for b in blocks],
            "quality_flags": flags}


def main() -> int:
    """CLI entry point for L3. Builds the panel and prints its shape."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coverage", action="store_true",
                    help="print percent non-null for every column")
    ap.add_argument("--facility-frame", default=None,
                    choices=sorted(facilities.FACILITY_FRAMES),
                    help=f"which facility list sets `enabled` (default "
                         f"{facilities.DEFAULT_FRAME!r}; anything else "
                         f"writes its own parquet and leaves "
                         f"{paths.PANEL.name} alone)")
    args = ap.parse_args()

    init_run()
    configure()
    report = run(args.facility_frame)
    suffix = ("" if report["facility_frame"] == facilities.DEFAULT_FRAME
              else "_" + report["facility_frame"])
    write_json(paths.METRICS / f"panel_report{suffix}.json", report)

    print(f"\n  panel -> {report['path']}")
    print(f"    {report['rows']:,} rows x {report['cols']} columns")
    print(f"    facility frame {report['facility_frame']!r}: "
          f"{report['enabled_cells']:,} enabled cells")
    if args.coverage:
        print()
        for c in report["coverage"]:
            print(f"    {c['column']:32} {c['pct']:6.2f}%  "
                  f"{c['non_null']:>10,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
