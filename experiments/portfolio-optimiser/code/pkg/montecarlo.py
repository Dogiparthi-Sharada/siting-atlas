"""Joint uncertainty over the cost and portfolio parameters.

The question this exists to answer
----------------------------------
The portfolio headline has moved three times — 317, then 330, then 282
activations; $1.268bn, then $1.320bn, then $1.128bn — and
`docs/DECISION_LOG.md` §4.2
records that **not one of those moves was caused by a parameter change**.
They were caused by the depot solver changing, by a panel rebuild, by a
column being repaired.

The project's defence so far has been to refuse to quote the number in prose
and point at the run-stamped artefact instead. That is honest and it is a
workaround. It does not answer the question a reader actually has, which is
whether 282 and 330 are two different answers or the same answer twice.

Only a distribution answers that. The backlog (`docs/STATUS.md` §5) has
carried the right
diagnosis for weeks — *"needs a distribution over the parameters, not point
values"* — and `docs/review/ORIGINAL_PROPOSAL_REVIEW.md` §5.1 ranks building
it first of everything available.

    python -m siting_atlas.optimize.montecarlo --draws 500

Why joint sampling and not the one-at-a-time sweep we already have
------------------------------------------------------------------
`docs/data/PARAMETERS.md` §3 sweeps each parameter alone and reports the
endpoints. That finds the influential levers, and it cannot compose them: it
never asks what happens when service time is high AND parcels per stop is
low, which is a perfectly ordinary state of the world. One-at-a-time is a
sensitivity analysis; this is an uncertainty analysis, and they answer
different questions.

WHAT THIS IS NOT
----------------
**Not a confidence interval.** Every range below was chosen by us, from
`docs/data/PARAMETERS.md`, and most of those ranges are engineering judgement
rather than a sampling distribution — eight of the constants have no source
at all. So the output answers "how much does the answer move across the range
we consider plausible", and propagates OUR priors, not the world's.

That is a real and useful question. It is not the same question as "what is
the 90% interval for the true value", and reporting it as though it were
would be exactly the kind of overclaim this project keeps catching in itself.
Every artefact and printout below says so.

Distributions, and why these
----------------------------
Triangular on the documented range with the mode at the current baseline.
Chosen over uniform because the baseline is not an arbitrary point in the
range — it is the value somebody argued for — and over a normal because the
ranges are hard bounds derived from physical or accounting limits, not
two-sigma guesses. Triangular respects the bounds and still concentrates mass
where the evidence is.

The one exception is `discount_rate`, which is uniform: `PARAMETERS.md` §6.16
records that both Econometrica ancestors use beta = 0.95 (about 5.3%) against
our 10%, and that the choice between a private hurdle rate and a social one
is a judgement with no defensible mode.
"""

from __future__ import annotations

import argparse
import dataclasses

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from ..cost.daganzo import DaganzoCostModel
from ..cost.params import BASELINE, CostParameters
from ..cost.runner import pilot_slice
from .objective import PortfolioObjective, PortfolioParameters
from .select import BudgetedSelector

_log = get_logger("optimize.montecarlo")

#: (low, high) for each cost parameter, from docs/data/PARAMETERS.md section 3.
#: The mode is the current baseline, read from BASELINE rather than repeated
#: here, so a parameter change cannot leave this table quietly disagreeing
#: with the model it is meant to describe.
COST_RANGES = {
    "service_minutes_per_stop": (1.5, 4.0),
    "parcels_per_stop": (1.0, 2.0),
    "van_lease_usd_per_day": (25.0, 70.0),
    "delivery_days_per_week": (5.0, 7.0),
    "stops_per_tour": (90.0, 180.0),
    "shift_hours": (8.0, 10.0),
    "wage_loading": (1.25, 1.45),
    "avg_speed_mph": (15.0, 30.0),
    "parcels_per_household_per_week": (2.5, 4.0),
    "circuity": (1.15, 1.45),
    "bhh_constant": (0.45, 0.71),
    "income_elasticity": (0.0, 0.7),
    "van_mpg": (10.0, 20.0),
    "maintenance_usd_per_mile": (0.10, 0.30),
    "default_linehaul_miles": (15.0, 40.0),
}

#: From PARAMETERS.md section 4. `capital_per_activation_usd` is deliberately
#: NOT sampled: STATUS.md sec.6 records that its UNIT is wrong (it charges
#: per ZCTA for a facility), and sampling a quantity whose definition is
#: broken would dress a known defect as uncertainty.
PORTFOLIO_RANGES = {
    "cannibalisation_peak": (0.05, 0.35),
    "cannibalisation_radius_km": (10.0, 40.0),
    "horizon_years": (5.0, 10.0),
    "delivery_days_per_year": (260.0, 365.0),
    "linehaul_sharing": (0.0, 0.7),
}

#: Uniform rather than triangular. See the module docstring.
UNIFORM = {"discount_rate": (0.05, 0.15)}

#: NOT SAMPLED, AND ONE OF THESE IS A REAL HOLE IN THIS STUDY.
#:
#:   capital_per_activation_usd   excluded on purpose. Its UNIT is wrong --
#:       it charges per ZCTA for a facility -- and sampling a quantity whose
#:       definition is broken would dress a known defect as uncertainty.
#:       Consequence, measured across all 500 draws: `capital_usd` is exactly
#:       4e6 * n every time, so the three published capital headlines
#:       ($1.268bn, $1.320bn, $1.128bn) are the three ACTIVATION COUNTS
#:       restated. They are not three pieces of evidence.
#:
#:   parcels_per_depot_per_day    excluded by oversight, found 2026-09-14.
#:       This is the worst rank-mover in PARAMETERS.md section 3 (rho 0.90)
#:       and it is the knob on the depot network -- which is precisely what
#:       DECISION_LOG.md sec.4.2 blames for the drift this study exists to
#:       explain. Leaving it out means every band below is a FLOOR.
#:
#:   reference_income_usd         excluded by oversight. Low stakes.
#:
#: Adding the latter two is the first thing to do if this is ever re-run.
NOT_SAMPLED = ("capital_per_activation_usd", "parcels_per_depot_per_day",
               "reference_income_usd")

__all__ = ["COST_RANGES", "PORTFOLIO_RANGES", "draw", "run", "main"]


def _triangular(rng, lo: float, hi: float, mode: float) -> float:
    """Triangular, with the mode clamped into the range.

    A baseline outside its own documented range is a real inconsistency and
    it is logged rather than silently clipped, because it means either the
    range or the baseline is wrong and somebody should find out which.
    """
    if not lo <= mode <= hi:
        _log.warning("baseline %.4f lies outside its documented range "
                     "[%.4f, %.4f]; clamping for the draw", mode, lo, hi)
        mode = min(max(mode, lo), hi)
    return float(rng.triangular(lo, mode, hi))


def draw(rng) -> tuple[CostParameters, PortfolioParameters]:
    """One joint draw across every sampled parameter."""
    base_cost = dataclasses.asdict(BASELINE)
    cost = {k: _triangular(rng, lo, hi, float(base_cost[k]))
            for k, (lo, hi) in COST_RANGES.items() if k in base_cost}

    base_port = dataclasses.asdict(PortfolioParameters())
    port = {k: _triangular(rng, lo, hi, float(base_port[k]))
            for k, (lo, hi) in PORTFOLIO_RANGES.items() if k in base_port}
    for k, (lo, hi) in UNIFORM.items():
        if k in base_port:
            port[k] = float(rng.uniform(lo, hi))

    return (dataclasses.replace(BASELINE, **cost),
            dataclasses.replace(PortfolioParameters(), **port))


def run(draws: int = 500, budget: float = 2_000_000_000.0,
        year: int = 2023, quarter: int = 4, seed: int = 20260914) -> dict:
    """Solve the whole chain `draws` times and summarise the spread.

    The panel and the pilot slice are loaded ONCE and reused: they are the
    same under every draw, and re-reading a 1.1m-row parquet per draw would
    be most of the runtime for none of the information.
    """
    rng = np.random.default_rng(seed)
    frame = pilot_slice(year, quarter)
    panel = pd.read_parquet(paths.PANEL).drop_duplicates("zcta")

    rows, selected = [], []
    for i in range(draws):
        cost_p, port_p = draw(rng)
        try:
            costed = DaganzoCostModel(cost_p).evaluate(frame)
            obj = PortfolioObjective(costed, panel, port_p)
            out = BudgetedSelector(obj, budget).solve()
        except Exception as exc:                              # noqa: BLE001
            # A draw that fails is recorded, not skipped. Silently dropping
            # failures would bias the distribution toward the parameter
            # combinations that happen to be numerically comfortable.
            _log.warning("draw %d failed: %s", i, exc)
            rows.append({"draw": i, "ok": False})
            continue
        d = out["detail"]
        rows.append({
            "draw": i, "ok": True,
            "n": int(d["n"]),
            "capital_usd": float(d["capital"]),
            "breakeven_margin": float(out["breakeven_margin"]),
            "optimality_gap": float(out["optimality_gap"]),
            "median_cost_per_parcel":
                float(costed["cost_per_parcel"].median()),
            **{f"p_{k}": v for k, v in dataclasses.asdict(port_p).items()
               if k in PORTFOLIO_RANGES or k in UNIFORM},
            **{f"c_{k}": dataclasses.asdict(cost_p)[k] for k in COST_RANGES},
        })
        if "selected" in out:
            selected.append(set(out["selected"]))
        if (i + 1) % 25 == 0:
            _log.info("draw %d/%d", i + 1, draws)

    res = pd.DataFrame(rows)
    ok = res[res["ok"]]
    if ok.empty:
        raise RuntimeError("every draw failed")

    def band(col: str) -> dict:
        v = ok[col].to_numpy(float)
        return {"p10": float(np.percentile(v, 10)),
                "p50": float(np.percentile(v, 50)),
                "p90": float(np.percentile(v, 90)),
                "min": float(v.min()), "max": float(v.max())}

    report = {
        "draws": draws, "ok": int(len(ok)), "failed": int(len(res) - len(ok)),
        "seed": seed, "budget_usd": budget, "period": f"{year}Q{quarter}",
        "bands": {c: band(c) for c in
                  ("n", "capital_usd", "breakeven_margin",
                   "median_cost_per_parcel", "optimality_gap")},
        "interpretation": (
            "NOT a confidence interval. Every range is from "
            "docs/data/PARAMETERS.md and was chosen by this project; eight of "
            "the constants have no external source. This measures how far the "
            "answer moves across the range we consider plausible, and it "
            "propagates our priors rather than the world's."),
    }
    out_path = paths.METRICS / "montecarlo_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, report)
    res.to_parquet(paths.TABLES / "montecarlo_draws.parquet", index=False)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=500)
    ap.add_argument("--budget", type=float, default=2_000_000_000.0)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--quarter", type=int, default=4)
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with (traced_layer("L4", f"Monte Carlo, {args.draws} draws"),
          step("montecarlo:run")):
        r = run(args.draws, args.budget, args.year, args.quarter)
        metric("montecarlo_draws_ok", r["ok"])

    print(f"\n  {r['ok']} of {r['draws']} draws succeeded "
          f"({r['failed']} failed)\n")
    print(f"  {'':26}{'p10':>14}{'p50':>14}{'p90':>14}")
    for label, key, fmt in (
            ("activations", "n", "{:.0f}"),
            ("capital $bn", "capital_usd", "{:.3f}"),
            ("break-even margin", "breakeven_margin", "{:.4f}"),
            ("median $/parcel", "median_cost_per_parcel", "{:.4f}"),
            ("optimality gap", "optimality_gap", "{:.4f}")):
        b = r["bands"][key]
        s = 1e9 if key == "capital_usd" else 1.0
        print(f"  {label:26}" + "".join(
            f"{fmt.format(b[q] / s):>14}" for q in ("p10", "p50", "p90")))
    print(f"\n  {r['interpretation']}\n")
    artefact(paths.METRICS / "montecarlo_report.json", draws=r["ok"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
