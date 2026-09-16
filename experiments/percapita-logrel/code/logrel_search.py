"""Does centring a covariate within its metro let the model use it?

    OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python \
        -m siting_atlas.models.logrel_search --stages diagnose

The question
------------
`choice.py` writes ``beta_k = exp(theta_k)``, so every coefficient is forced
positive and a covariate that REPELS cannot be expressed: the optimiser
walks it to the boundary and it reads as worthless. Seven of the fifteen
columns in `COVARIATES_TRIED.md` came back as exact no-ops, identical to the
baseline to fifteen decimal places, and `median_home_value` is the cleanest
case — ZIP grain (182 distinct values per large metro), correlation with the
households numeraire of only +0.061, and still an exact no-op.

The proposed fix is ``ln(x / metro_median(x))``: centre each covariate
inside its own metro so only within-metro variation survives.

The prior is modest and is stated before the run rather than after it. The
plain reciprocal was already tried as a sign fix on this very column and did
essentially nothing (`inv_median_home_value` +0.0041, `inv_diesel_pm` an
exact 0.0000), and neither known failure mechanism — county grain,
collinearity with the numeraire — applies to `median_home_value`. A log
relative IS a different object from a reciprocal, because it removes the
metro level rather than inverting the value, so the test is worth running.
It is not expected to rescue the column.

What the diagnose stage is for, and why it is the headline
----------------------------------------------------------
`ln(beta'a)` needs ``beta'a > 0`` for every alternative. A log-relative
column is negative on half its rows by construction, so a positive
coefficient on it SUBTRACTS attraction, and the largest coefficient that
keeps every metro's probabilities defined is a hard ceiling set by the
single worst alternative in the frame. `logrel_frame.bound` computes that
ceiling exactly and it costs one fit, no re-splits. If the ceiling is small
against the numeraire, the re-split stage cannot show anything and the
finding is about the SPECIFICATION rather than about the column.

Arms
----
``+ logrel_x`` is monotone INCREASING in x, so with ``beta > 0`` it still
says "more x is more attractive". ``+ neglogrel_x`` is its exact negative
and therefore says "less x is more attractive". Running both is the only
way this specification can look at both signs, and it does so as a choice
between two models rather than as one estimated sign — see
`choice_sandwich.REFUSAL` for why a boundary coefficient has no standard
error, and note that a sign picked by comparing two fits has none either.
"""

from __future__ import annotations

import argparse
import json
import os

from ..common import paths
from ..common.logging_setup import configure
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, fit
from .choice_runner import SEED, TEST_FRACTION
from .covariate_frame import (
    RECIPROCALS,
    STATIC_CANDIDATES,
    build_frame,
    columns_only,
)
from .covariate_harness import REPEATS
from .covariate_search import _load
from .logrel_frame import CANDIDATES, LOGREL, NEG, augment, bound
from .logrel_frame import negative_utilities as neg_util
from .logrel_runner import ARTEFACT, distinct_decisions, load, run_serial, save

BASE = (*ATTRACTIONS, *CBP_ATTRACTIONS)
NO_WAREHOUSING = ATTRACTIONS

STAGES = ("diagnose", "gate", "resplits")

#: Reproduction gate. `covariate_search.json`, core stage, large-metro
#: top-10 lift over 50 re-splits. If these two do not come back exactly,
#: the frame is not the frame the published numbers were measured on and
#: nothing else in this artefact means anything.
GATE = {"baseline": 6.388945150223279, "no_warehousing": 2.735190253657848}

#: Re-splits for the log-relative arms. Held at `REPEATS` so every figure
#: in this artefact is comparable with `covariate_search.json` without a
#: footnote. It is a separate constant because it nearly was not: a
#: log-relative fit is slower than a plain one — the optimiser has a
#: positivity cliff to fall off, see `logrel_frame` — and while the
#: workstation was at load average ~25 a single fit took four minutes,
#: which would have put the full run past a day. The load fell, the full
#: count became affordable, and the reduced-count path is kept behind
#: `--repeats` rather than baked in.
RESPLITS = REPEATS


def _frame():
    facilities, panel, cbp = _load()
    core, cov = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS,
                            static=STATIC_CANDIDATES,
                            reciprocals=RECIPROCALS)
    return core, cov


def _spec(cols: tuple[str, ...], mirror: tuple[str, ...]) -> dict:
    fixed = {"baseline": list(BASE), "no_warehousing": list(NO_WAREHOUSING)}
    for col in cols:
        fixed[f"+ {LOGREL}{col}"] = [*BASE, LOGREL + col]
    for col in mirror:
        fixed[f"+ {NEG}{col}"] = [*BASE, NEG + col]
    return {"fixed": fixed}


def diagnose(data, cols: tuple[str, ...], mirror: tuple[str, ...]) -> dict:
    """One fit per arm on the FULL frame: ceiling, coefficient, feasibility.

    No re-splits here. The feasibility ceiling is a property of the frame
    and the transform, not of a train/test partition, so it is measured
    once and exactly.
    """
    base_fit = fit(columns_only(data, BASE))
    out = {"baseline_beta": base_fit["beta"],
           "baseline_log_likelihood": base_fit["log_likelihood"],
           "note": "full-frame fits, no re-splitting. beta_max is the "
                   "largest coefficient on the transformed column that "
                   "keeps beta'a > 0 for every alternative; above it the "
                   "probability model is undefined and choice.py's 1e-300 "
                   "floor silently optimises something that is not a "
                   "likelihood.",
           "columns": {}}
    for name in [LOGREL + c for c in cols] + [NEG + c for c in mirror]:
        ceiling = bound(data, BASE, base_fit["beta"], name)
        fitted = fit(columns_only(data, (*BASE, name)))
        beta = fitted["beta"][name]
        out["columns"][name] = {
            "feasibility": ceiling,
            "beta": beta,
            "fitted_beta": fitted["beta"],
            "beta_over_beta_max": float(beta / ceiling["beta_max"]),
            "at_lower_boundary": bool(beta < 1e-8),
            "log_likelihood": fitted["log_likelihood"],
            "log_likelihood_gain": fitted["log_likelihood"]
            - base_fit["log_likelihood"],
            "fitted_model_feasible":
                neg_util(data, (*BASE, name), fitted["beta"]),
        }
        c = out["columns"][name]
        print(f"  {name:34} beta={beta:12.6g}  beta_max="
              f"{ceiling['beta_max']:10.6g}  "
              f"ratio={c['beta_over_beta_max']:8.4f}  "
              f"dLL={c['log_likelihood_gain']:+.6f}", flush=True)
    return out


def run(stages: tuple[str, ...] = STAGES, cols: tuple[str, ...] = CANDIDATES,
        mirror: tuple[str, ...] = CANDIDATES,
        repeats: int = RESPLITS) -> dict:
    report = load()
    core, cov = _frame()
    # Every candidate is BUILT in both directions so the diagnostics
    # block always covers all of them; `cols` and `mirror` select only
    # which of them get their own re-split arm.
    data, diag = augment(core, CANDIDATES, CANDIDATES)
    report |= {"seed": SEED, "test_fraction": TEST_FRACTION,
               "repeats": repeats, "coverage": cov,
               "transform": "ln(x / metro_median(x)); the choice set is the "
                            "metro, so the group median IS the metro median",
               "transform_diagnostics": diag,
               "distinct_decisions": distinct_decisions(data),
               "reproduction_gate": GATE,
               "interval_note": "percentile spreads over re-splits describe "
                                "how the estimator moves across partitions "
                                "of one fixed set of decisions. They are NOT "
                                "standard errors."}
    save(report)

    if "diagnose" in stages:
        report["diagnose"] = diagnose(data, cols, mirror)
        save(report)

    if "gate" in stages:
        report["gate"] = run_serial(
            "GATE: the published baseline, reproduced on this frame",
            data, {"fixed": {"baseline": list(BASE),
                             "no_warehousing": list(NO_WAREHOUSING)}},
            "baseline", REPEATS, "logrel_gate.json")
        report["gate_check"] = _gate_check(report["gate"])
        print("\n  reproduction gate:", json.dumps(report["gate_check"]))
        save(report)

    if "resplits" in stages:
        report["resplits"] = run_serial(
            "LOG-RELATIVE: within-metro centring of the ZIP-grain no-ops "
            f"({repeats} re-splits, NOT {REPEATS} - see RESPLITS)",
            data, _spec(cols, mirror), "baseline", repeats)
        report["resplits"]["repeat_count_note"] = (
            f"{repeats} re-splits at seeds {SEED}..{SEED + repeats - 1}, the "
            f"same seeds and the same frame as the 'gate' block and as "
            f"covariate_search.json. Every arm here is paired against the "
            f"baseline refitted on the identical splits."
            + ("" if repeats == REPEATS else
               f" NOTE: {repeats} is fewer than the {REPEATS} the published "
               "baseline uses, so this block is not directly comparable "
               "with covariate_search.json."))
        save(report)
    return report


def _gate_check(block: dict) -> dict:
    return {arm: {"expected": want,
                  "observed": block["arms"][arm]["top10"]["large_gt100"][
                      "lift"],
                  "exact": block["arms"][arm]["top10"]["large_gt100"][
                      "lift"] == want}
            for arm, want in GATE.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stages", nargs="*", choices=STAGES,
                        default=list(STAGES))
    parser.add_argument("--columns", nargs="*", default=list(CANDIDATES))
    parser.add_argument("--mirror", nargs="*", default=list(CANDIDATES))
    parser.add_argument("--repeats", type=int, default=RESPLITS)
    args = parser.parse_args(argv)
    os.nice(19)
    paths.ensure_dirs()
    configure()
    run(tuple(args.stages), tuple(args.columns), tuple(args.mirror),
        args.repeats)
    print(f"\n  -> {paths.rel(paths.METRICS / ARTEFACT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
