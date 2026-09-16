"""L5 — render every result figure for one scenario.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.viz.build
    PYTHONPATH=src .venv/bin/python -m siting_atlas.viz.build --all-scenarios

This is the batch twin of the dashboard: the same chart functions, written to
outputs/figures/ so the proposal and the deck can embed them. It exits
non-zero if any label had to be shrunk past its floor, because a figure with
overflowing text is a defect that nobody notices in a PDF at 60% zoom — the
point of the audit is that it fails the build instead of the reader.
"""

from __future__ import annotations

import argparse
import sys

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import metric, step, traced_layer
from . import charts_density as cd
from . import charts_economics as ce
from . import data as cost_data
from .style import save_figure

_log = get_logger("viz.build")


def _figures(frame, threshold: float | None):
    """(name, Figure) for every chart, in the order a reader meets them."""
    return [
        ("cost_vs_density", cd.cost_vs_density(frame)),
        ("cost_by_metro", cd.cost_by_metro(frame)),
        ("cost_decomposition", ce.cost_decomposition(frame)),
        ("cumulative_coverage",
         ce.cumulative_coverage(frame, threshold=threshold)),
    ]


def build(year: int, quarter: int, scenario: str,
          threshold: float | None) -> dict:
    """Render one scenario's figures and return what was written."""
    frame = cost_data.load(year, quarter, scenario)
    metric("viz_rows", len(frame))

    written, defects = [], {}
    for name, fig in _figures(frame, threshold):
        stem = f"{name}_{year}q{quarter}_{scenario}"
        saved = save_figure(fig, stem)
        if saved.overflow:
            defects[stem] = saved.overflow
        written.append(paths.rel(saved.path))

    return {"scenario": scenario, "year": year, "quarter": quarter,
            "zctas": len(frame), "figures": written, "overflow": defects}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--quarter", type=int, default=4)
    ap.add_argument("--scenario", default="baseline")
    ap.add_argument("--all-scenarios", action="store_true",
                    help="render every scenario found in outputs/tables/")
    ap.add_argument("--threshold", type=float, default=None,
                    help="mark this $/parcel ceiling on the coverage curve")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    on_disk = cost_data.available()
    if not on_disk:
        _log.error(
            "no cost tables in %s — run the cost model first:\n    "
            "PYTHONPATH=src .venv/bin/python -m siting_atlas.cost.runner "
            "--all-scenarios", paths.rel(paths.TABLES))
        return 2

    wanted = ([(y, q, s) for y, q, s in on_disk
               if (y, q) == (args.year, args.quarter)] if args.all_scenarios
              else [(args.year, args.quarter, args.scenario)])

    reports = {}
    with traced_layer("L5", f"figures {args.year}Q{args.quarter}"):
        for year, quarter, scenario in wanted:
            with step(f"figures:{scenario}"):
                reports[scenario] = build(year, quarter, scenario,
                                          args.threshold)

    write_json(paths.METRICS / "viz_report.json", reports)
    bad = sum(len(r["overflow"]) for r in reports.values())
    total = sum(len(r["figures"]) for r in reports.values())
    print(f"\n  {total} figure(s) -> {paths.rel(paths.RUN_FIGURES)}")
    for report in reports.values():
        for name in report["figures"]:
            print(f"    {name}")
    if bad:
        print(f"\n  {bad} figure(s) have text that will not fit. "
              "Shorten the label or widen the box.", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
