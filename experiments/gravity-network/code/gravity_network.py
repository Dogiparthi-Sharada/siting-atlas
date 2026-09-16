"""Does a gravity term beat the distance to the nearest facility?

    python -m siting_atlas.models.gravity_network [--repeats N]

The question, and why it is worth one run
-----------------------------------------
Fifteen covariates have failed. The one class that has ever produced an
interior coefficient is proximity to Amazon's own non-delivery-station
network, and inside that class one line of `COVARIATES_TRIED.md` is the
whole prompt for this module:

    sortation_proximity    0.118 [0.018, 0.235]   interior
    fulfilment_proximity   0.178 [0.028, 0.334]   interior
    network_within_50mi    AT THE BOUNDARY at 25, 50 AND 100 miles

A continuous distance to the nearest facility works; a count inside a
radius fails at every radius. The radius was never the problem, the
construct was. A gravity term ``sum_j mass_j / (1 + d_ij)**alpha`` is the
next point on the same axis: it keeps the distances the count discards
and the far facilities the nearest-distance discards. `gravity_terms`
holds the construction and the reason the kernel is the SAME kernel the
baseline maxes over.

What is measured, and against what
----------------------------------
The baseline is the CURRENT specification -- `combined_plus_network`,
three columns -- not nothing. Every arm sits on the identical 485
decisions and takes the identical splits from the identical seeds, so the
differences are paired and the market-mix confound that
`NOTES_PANEL_EXPERIMENTS.md` §2 documents cannot arise. The baseline is
RE-RUN here at whatever repeat count this run uses rather than read from
`panel_experiments.json`, so a lower count than the published 50 makes
every comparison in the artefact coarser but none of them unfair.

Three things are read, in this order:

1. **Is each coefficient INTERIOR or at the positivity boundary?** This
   is the outcome that matters. `choice.py` sets ``beta = exp(theta)``, so
   a column the optimiser wants to discard lands at ~1e-15 and formally
   "excludes 1.0" while meaning nothing. The bar is the one the current
   proximities cleared.
2. **Top-10 lift, STRATIFIED by choice-set size with distinct-decision n.**
   Pooled lift across heterogeneous choice sets has produced two wrong
   conclusions in this project. A stratum under 20 distinct decisions is
   labelled THIN and is not compared.
3. Brier, as a raw pair, never a skill score.

A 2.5-97.5 percentile over re-splits is NOT a standard error and nothing
here pretends otherwise; the caveat is printed beside every interval.

The theoretical cost, stated and not buried
-------------------------------------------
A gravity term is not an extensive quantity: merging two zones does not
add their attractions. That breaks the Train §3.4 Example 2 invariance
`MODEL_SPEC.md` §1 is built on. It is the same cost the existing
proximities already incur and `models/accessibility.py` switched itself
off over, plus one extra wrinkle -- gravity's LEVEL grows with the
network, and in a share model an additive shift does not cancel. The
per-vintage means are in the artefact so the drift can be seen.
"""

from __future__ import annotations

import argparse
import os
import sys

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .choice import CBP_ATTRACTIONS
from .choice_runner import SEED
from .gravity_arms import (
    BASELINE,
    FACILITY_ARM,
    FLOOR,
    PROXIMITIES,
    build_arms,
    build_panel,
    slice_arm,
    spec_columns,
)
from .gravity_print import report_text
from .gravity_report import (
    boundary_census,
    census_matches,
    paired,
    pick_best,
    strata_vs,
    verdicts,
)
from .gravity_terms import ALPHAS, MASS_MODES, TYPES, column_name
from .panel_harness import LOGIT, REPEATS, measure
from .panel_strata import standardise

_log = get_logger("models.gravity_network")

OUT_PATH = paths.METRICS / "gravity_network.json"

COMBINED_ARM = "gravity_best_plus_proximity"

SPREAD_IS_NOT_A_STANDARD_ERROR = (
    "Every [2.5, 97.5] bracket in this file is a PERCENTILE OVER THE "
    "RE-SPLITS recorded in the `repeats` field, all of them drawn from "
    "the same fixed set of decisions. It is NOT a standard error and not "
    "an estimate of one: the re-splits are not independent draws, so the "
    "spread understates sampling variability by an amount nothing here "
    "measures, and each re-split fit uses 60% of the decisions, so it is "
    "not an interval on the same estimator as a full-sample point "
    "estimate would be. It is reported because it is the quantity the "
    "published proximity claim was made on, so the comparison against "
    "that claim is like-for-like. At a repeat count below about 40 the "
    "2.5th percentile is effectively the minimum of the draws and the "
    "bracket should be read as a range, not as a quantile.")

INVARIANCE_COST = (
    "A gravity term is NOT EXTENSIVE: merging two ZCTAs does not add "
    "their attractions, so the zone-merger invariance MODEL_SPEC.md §1 "
    "buys from Train §3.4 Example 2 -- the entire justification for the "
    "ln(beta'a) form -- does not hold for any arm in this file except "
    "no_network. This is the same cost the existing proximities already "
    "incur and accessibility.py switched itself off over. Gravity adds "
    "one wrinkle: its level grows as the network grows, and in a share "
    "model P_j = beta'a_j / sum_k beta'a_k an additive shift common to a "
    "choice set does not cancel, it flattens the distribution towards "
    "uniform. See terms.mean_by_vintage for the size of that drift.")


def _measure_arm(data, repeats: int, mix: dict | None) -> tuple[dict, dict]:
    arm = measure(data, repeats, with_gbm=False)
    block = arm["methods"][LOGIT]
    reference = mix if mix is not None else arm["size_mix"]
    out = {
        "covariates": list(data.names),
        "n_decisions": arm["n_decisions"], "n_test": arm["n_test"],
        "n_alternatives": arm["n_alternatives"],
        "beta_mean": arm["beta_mean"], "beta_p025": arm["beta_p025"],
        "beta_p975": arm["beta_p975"],
        "strata": block["strata"], "raw_pooled": block["raw_pooled"],
        "raw_pooled_sd": block["raw_pooled_sd"],
        "standardised_top10": standardise(block["strata"], reference)["top10"],
        "per_repeat": block["per_repeat"],
    }
    out["verdicts"] = verdicts(out)
    return out, arm["size_mix"]


def run(repeats: int = REPEATS, alphas: tuple[float, ...] = ALPHAS) -> dict:
    with traced_layer("L5", "gravity network covariates"):
        with step("gravity:build"):
            panel = build_panel(alphas)
            specs = spec_columns(alphas)
            built, full, checks = build_arms(panel, specs)

        arms, mix = {}, None
        for name, data in built.items():
            with step(f"gravity:{name}"):
                arms[name], mix = _measure_arm(data, repeats, mix)

        best = pick_best(arms)
        with step(f"gravity:{COMBINED_ARM}"):
            mass, alpha = _decompose(best["arm"])
            extra = (CBP_ATTRACTIONS
                     + tuple(column_name(k, mass, alpha) for k in TYPES)
                     + PROXIMITIES)
            combined = slice_arm(full, extra)
            arms[COMBINED_ARM], _ = _measure_arm(combined, repeats, mix)
            built[COMBINED_ARM] = combined

        with step("gravity:census"):
            census_arms = [BASELINE, "proximity_only", best["arm"],
                           COMBINED_ARM]
            census = {n: boundary_census(built[n], repeats)
                      for n in dict.fromkeys(census_arms)}

    base = arms[BASELINE]
    # Every difference is taken BEFORE anything is dropped: the baseline
    # is itself one of the arms in this loop, and popping its per-repeat
    # series first would leave every later arm differencing against a
    # missing key.
    differences = {name: (None if name == BASELINE else paired(arm, base))
                   for name, arm in arms.items()}
    for name, arm in arms.items():
        arm["paired_vs_baseline"] = differences[name]
        arm["top10_lift_vs_baseline"] = strata_vs(arm, base)
        arm.pop("per_repeat")
    census = {name: {"columns": block,
                     "reproduces_harness_percentiles": census_matches(
                         block, arms[name])}
              for name, block in census.items()}

    report = {
        "seed": SEED, "repeats": repeats, "facility_arm": FACILITY_ARM,
        "alphas": list(alphas), "mass_modes": list(MASS_MODES),
        "baseline_arm": BASELINE, "floor_arm": FLOOR,
        "checks": checks, "reference_mix": mix, "terms": panel.terms,
        "spread_is_not_a_standard_error": SPREAD_IS_NOT_A_STANDARD_ERROR,
        "aggregation_invariance_cost": INVARIANCE_COST,
        "best_gravity": best, "boundary_census": census, "arms": arms,
        "reporting_rule": (
            "Lift is stratified by choice-set size with DISTINCT-decision n "
            "and a stratum under 20 distinct decisions is marked THIN and "
            "not compared. Brier is a raw pair, never a skill score "
            "(Gneiting & Raftery 2007 §2.3 p.362). All arms hold the same "
            "decisions and the same splits, so chance rates are identical "
            "across arms and a lift difference is a model difference."),
    }
    metric("gravity_best_fully_interior",
           float(best["both_columns_interior"]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUT_PATH, report)
    artefact(OUT_PATH, arms=len(arms))
    return report


def _decompose(arm_name: str) -> tuple[str, float]:
    """``gravity_sqft_a2`` -> ``("sqft", 2.0)``."""
    body = arm_name[len("gravity_"):]
    mass, _, alpha = body.rpartition("_a")
    return mass, float(alpha.replace("p", "."))


def main(argv: list[str] | None = None) -> int:
    """``--repeats N`` because the count actually run has to be stated.

    `panel_harness.REPEATS` is 50 and that is the published protocol. This
    module was run at a lower count on a machine carrying a load average
    near 30 from other work, so the count is a command-line argument and
    the value used is written into the artefact's `repeats` field rather
    than being implied by a default nobody checked.
    """
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=REPEATS,
                        help=f"re-splits per arm (published protocol: "
                             f"{REPEATS})")
    args = parser.parse_args(argv)
    # Single-threaded and lowest priority: this box is shared and the
    # brief's machine discipline is a requirement, not a preference.
    os.nice(19)
    paths.ensure_dirs()
    init_run()
    configure()
    print(report_text(run(args.repeats)))
    print(f"  -> {paths.rel(OUT_PATH)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
