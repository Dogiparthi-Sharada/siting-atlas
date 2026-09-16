"""L4 — pick a portfolio under a budget and report it.

    python -m siting_atlas.optimize.runner --budget 2e9
    python -m siting_atlas.optimize.runner --budget 2e9 --compare-naive

Like the cost model, this needs no target variable: it answers "given what it
costs to serve each ZIP, which set should be funded", which is an operations
question. Whether the operator WOULD choose them is the causal question that
waits on the facility panel.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .objective import PortfolioObjective, PortfolioParameters
from .select import BudgetedSelector

_log = get_logger("optimize.runner")


def load(scenario: str, year: int, quarter: int):
    """Read the cost table for a scenario, plus ZCTA coordinates.

    The panel is de-duplicated on zcta because it is a ZCTA-QUARTER panel
    and the objective indexes coordinates by ZCTA alone; reindexing against
    a duplicated index raises rather than silently picking a row.
    """
    table = (paths.TABLES
             / f"cost_to_serve_{year}q{quarter}_{scenario}.parquet")
    if not table.exists():
        raise FileNotFoundError(
            f"{paths.rel(table)} is missing. Build it first:\n"
            f"    python -m siting_atlas.cost.runner "
            f"--year {year} --quarter {quarter} --scenario {scenario}")
    frame = pd.read_parquet(table)
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "latitude", "longitude"])
    return frame, panel.drop_duplicates("zcta")


def naive_topk(frame: pd.DataFrame, obj: PortfolioObjective,
               k: int) -> np.ndarray:
    """The obvious alternative: take the K cheapest by standalone cost.

    Worth computing precisely because it is what anyone would do without this
    model. If the optimiser cannot beat it, the optimiser is not earning its
    place in the proposal.
    """
    sel = np.zeros(obj.n, dtype=bool)
    sel[np.argsort(obj.standalone_breakeven())[:k]] = True
    return sel


def _report(res: dict, obj: PortfolioObjective, frame: pd.DataFrame,
            naive: dict | None) -> None:
    """Print the portfolio, the gap, and the per-metro breakdown."""
    d = res["detail"]
    w = 78
    print("\n" + "=" * w)
    print("  PORTFOLIO SELECTION")
    print("=" * w)
    print(f"  budget funds {res['capacity']:,} activations; "
          f"{d['n']:,} selected")
    print(f"  capital committed      ${d['capital']:,.0f}")
    print(f"  annual parcels served  {d['parcels']:,.0f}")
    print(f"  annual cost to serve   ${d['cost']:,.0f}")
    print()
    print(f"  BREAK-EVEN MARGIN      "
          f"${res['breakeven_margin']:.3f} per parcel")
    print("    the contribution margin at which this portfolio returns its")
    print("    capital over the horizon. Below it the portfolio loses money.")
    print()
    print(f"  greedy alone           ${res['greedy_breakeven']:.4f}")
    print(f"  after local search     ${res['breakeven_margin']:.4f}")
    print(f"  upper bound            ${res['upper_bound']:.4f}  "
          f"(no cannibalisation)")
    print(f"  optimality gap         {res['optimality_gap'] * 100:.2f}%  "
          f"— instance-specific, NOT a worst-case guarantee")

    if naive is not None:
        delta = naive["breakeven_margin"] - res["breakeven_margin"]
        print()
        print(f"  vs naive top-K         ${naive['breakeven_margin']:.4f}  "
              f"({delta / naive['breakeven_margin'] * 100:+.2f}% better)")
        print("    naive picks the K cheapest ignoring cannibalisation; the")
        print("    difference is what accounting for interaction buys.")

    sel = res["selected"]
    chosen = frame.loc[sel].copy()
    print("\n  SELECTED BY METRO")
    print(f"  {'metro':26} {'picked':>7} {'of':>6} {'median $/parcel':>16}")
    tot = frame.groupby("metro_label").size()
    got = chosen.groupby("metro_label")
    for name in tot.index:
        n = len(got.get_group(name)) if name in got.groups else 0
        med = (got.get_group(name)["cost_per_parcel"].median()
               if n else float("nan"))
        print(f"  {str(name)[:26]:26} {n:>7,} {tot[name]:>6,} "
              f"{med:>16.3f}")
    print("=" * w)


def main() -> int:
    """CLI entry point for L4 portfolio selection."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget", type=float, default=2e9,
                    help="capital budget in USD (default 2e9)")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--quarter", type=int, default=4)
    ap.add_argument("--scenario", default="baseline")
    ap.add_argument("--compare-naive", action="store_true")
    ap.add_argument("--margin", type=float, default=None,
                    help="assumed contribution margin $/parcel; default is "
                         "the margin at which a full-budget portfolio breaks "
                         "even")
    ap.add_argument("--frontier", action="store_true",
                    help="solve across a range of margins instead of one")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L4", f"portfolio under ${args.budget:,.0f}"):
        with step("optimize:load"):
            frame, panel = load(args.scenario, args.year, args.quarter)
            obj = PortfolioObjective(frame, panel, PortfolioParameters())

        with step("optimize:solve"):
            selector = BudgetedSelector(obj, args.budget)
            res = selector.solve(args.margin)
            metric("portfolio_n", res["detail"]["n"])
            metric("breakeven_margin",
                   round(res["breakeven_margin"], 4))
            metric("optimality_gap_pct",
                   round(res["optimality_gap"] * 100, 3))
            metric("margin_assumed", round(res["margin"], 4))
            metric("npv_usd", round(res["npv"], 0))

        frontier = None
        if args.frontier:
            with step("optimize:frontier"):
                base = res["margin"]
                frontier = selector.frontier(
                    [base * f for f in (0.6, 0.8, 1.0, 1.2, 1.5, 2.0)])

        naive = None
        if args.compare_naive:
            with step("optimize:naive"):
                mask = naive_topk(frame, obj, res["capacity"])
                naive = obj.evaluate(mask)
                metric("naive_breakeven",
                       round(naive["breakeven_margin"], 4))

    out = paths.TABLES / f"portfolio_{args.year}q{args.quarter}.parquet"
    picked = frame.loc[res["selected"]].copy()
    picked["selected"] = True
    picked.to_parquet(out, index=False)
    artefact(out, rows=len(picked))

    _report(res, obj, frame, naive)

    if frontier is not None:
        print("\n  FRONTIER  (margin is unobservable, so solve across it)")
        print(f"  {'margin $/parcel':>16} {'activations':>12} "
              f"{'capital $':>16} {'NPV $':>18}")
        for r in frontier:
            print(f"  {r['margin']:>16.3f} {r['n']:>12,} "
                  f"{r['capital']:>16,.0f} {r['npv']:>18,.0f}")

    write_json(paths.METRICS / "portfolio_report.json", {
        "frontier": frontier,
        "budget_usd": args.budget,
        "capacity": res["capacity"],
        "breakeven_margin": res["breakeven_margin"],
        "greedy_breakeven": res["greedy_breakeven"],
        "upper_bound": res["upper_bound"],
        "optimality_gap": res["optimality_gap"],
        "naive_breakeven": naive["breakeven_margin"] if naive else None,
        "detail": res["detail"],
        "parameters": vars(PortfolioParameters()),
        "path": paths.rel(out)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
