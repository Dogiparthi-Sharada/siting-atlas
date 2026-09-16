"""L4 — fit the discrete-time hazard and report what it can and cannot do.

    python -m siting_atlas.models.runner
    python -m siting_atlas.models.runner --baseline dummies --alpha 0.05
    python -m siting_atlas.models.runner --synthetic      # force the fixture

One code path, two possible inputs. If the real panel has a populated
outcome it is used; if it does not, the labelled synthetic fixture is used,
a warning banner goes to the console and the log, and every artefact is
written under a ``SYNTHETIC_`` name with ``"synthetic": true`` inside it.
There is no separate "demo mode" to fall out of date, and on the day
``facilities.csv`` lands the only thing that changes is which branch of
:func:`panel_source.load_panel` returns.

That day has come. The real branch brings three things the fixture never
needed and that a reader must not be able to skip: the panel is cut to the
pilot metros with Phoenix and Boise withheld (``panel_source``), the robust
covariance is clustered on the metro rather than the ZCTA because one
station flips a whole catchment at once, and every performance figure is
accompanied by ``diagnostics`` — the effective events-per-parameter ratio,
the Q1 dating artefact, and the OSHA inspection-recency contamination.
"""

from __future__ import annotations

import argparse
from dataclasses import replace

import numpy as np

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from . import console, diagnostics, sensitivities
from .base import BaselineOnly
from .conformal import SplitConformalBinary
from .fixtures import SyntheticSpec, true_coefficients
from .hazard import DiscreteTimeHazard, HazardSpec
from .metrics import brier_skill_score
from .panel_source import load_panel
from .risk_set import build_risk_set, summarise
from .splits import split_by_unit

_log = get_logger("models.runner")

#: Cluster the robust covariance on the metro when the panel is real. The
#: ZCTA default assumes a unit's quarters are the only dependence, and a
#: delivery station flipping eighty ZCTAs in one quarter violates that far
#: more severely than serial correlation does. See hazard.HazardSpec.
REAL_CLUSTER_COL = "cbsa_code"

#: Last quarter index of 2022, for the secondary temporal split. The panel
#: opens at 2018Q1 = 0, so 2022Q4 is (2022 - 2018) * 4 + 3.
TEMPORAL_CUTOFF_T = 19


def resolve_baseline(requested: str, synthetic: bool) -> str:
    """Pick the time baseline the sample can actually support.

    The default is ``auto`` and it resolves differently for the two panels,
    which is the point. The fixture has 1,200 units and events spread over
    every quarter, so a restricted cubic spline is affordable and correct.

    CORRECTED 2026-09-13. This paragraph used to say the real panel had SIX
    distinct event times, ALL of them Q1, because ``open_quarter`` was never
    collected. Every one of those claims is now false, and the comment was
    load-bearing — it is the whole justification for the value returned
    below. ``outputs/metrics/hazard_report.json`` records **17** distinct
    event times spread across all four quarters (Q1 288, Q2 155, Q3 176,
    Q4 193), so Q1 is 35.5% of events rather than 100%.

    The conclusion survives the correction, for a different reason. 19 of 43
    facilities still have no reported ``open_quarter`` and are dated to Q1 by
    convention, so 44.2% of the quarter axis is our own default rather than a
    measurement. Among the rows that DO carry a reported quarter the openings
    run 5/6/7/6 across the year — essentially uniform — which means the entire
    Q1 excess is the convention and none of it is seasonality. A spline would
    spend 3 parameters fitting a curve through 17 points whose horizontal
    position is 44% invented, and ``dummies`` would spend 30 and separate on
    the convention. A single linear trend remains the only shape this target
    pays for, and it will stay that way until the 19 quarters are collected.

    Resolved here and not in ``main`` so that the bare command and the
    library call cannot drift apart: whatever the report says, the flagless
    ``python -m siting_atlas.models.runner`` reproduces it.
    """
    if requested != "auto":
        return requested
    return "spline" if synthetic else "linear"


def run(*, baseline: str = "auto", n_knots: int = 4, alpha: float = 0.10,
        force_synthetic: bool = False, n_units: int | None = None) -> dict:
    """Fit, evaluate, conformalise, and hand back everything measured."""
    spec_kwargs = {"n_units": n_units} if n_units else {}
    source = load_panel(force_synthetic=force_synthetic,
                        spec=SyntheticSpec(**spec_kwargs))
    baseline = resolve_baseline(baseline, source.synthetic)

    with step("risk_set"):
        risk = build_risk_set(source.frame)
        shape = summarise(risk)
        for key in ("units", "rows", "events"):
            metric(f"hazard_riskset_{key}", shape[key])

    with step("split"):
        parts = split_by_unit(risk)

    with step("fit"):
        spec = HazardSpec(
            covariates=source.covariates, baseline=baseline,
            n_knots=n_knots,
            cluster_col=REAL_CLUSTER_COL if not source.synthetic
            else HazardSpec.cluster_col)
        model = DiscreteTimeHazard(spec)
        model.fit(parts["train"])
        null = BaselineOnly().fit(parts["train"])

    with step("evaluate"):
        report = model.evaluate(parts["test"], label="cloglog-hazard")
        null_report = null.evaluate(parts["test"], label="baseline-only")
        skill = brier_skill_score(parts["test"]["event"].to_numpy(),
                                  model.predict(parts["test"]).to_numpy())
        metric("hazard_auc", round(report.auc, 4))
        metric("hazard_brier", round(report.brier, 6))
        metric("hazard_brier_skill", round(skill, 5))
        metric("hazard_ece", round(report.ece, 5))
        metric("hazard_auc_null", round(null_report.auc, 4))

    with step("conformal"):
        # Calibrated on the split the model never saw, then measured on a
        # third split. Calibrating on training rows would tighten q_hat and
        # break the very guarantee being reported.
        conformal = SplitConformalBinary(alpha=alpha).calibrate(
            model.predict(parts["calibration"]).to_numpy(),
            parts["calibration"]["event"].to_numpy())
        coverage = conformal.evaluate(
            model.predict(parts["test"]).to_numpy(),
            parts["test"]["event"].to_numpy(),
            groups=parts["test"]["zcta"].to_numpy())
        metric("conformal_coverage", round(coverage.empirical_coverage, 4))
        metric("conformal_nominal", coverage.nominal_coverage)

    recovery = _recovery_table(model, source.synthetic)
    extra = {} if source.synthetic else _real_panel_checks(
        risk, spec, parts, model, source.frame)

    with step("write"):
        predictions = parts["test"][["zcta", "t", "event"]].copy()
        predictions["hazard"] = model.predict(parts["test"]).to_numpy()
        sets = conformal.predict_set(predictions["hazard"].to_numpy())
        predictions["set_includes_0"] = sets[:, 0]
        predictions["set_includes_1"] = sets[:, 1]
        predictions["synthetic"] = source.synthetic

        out = paths.TABLES / source.filename("hazard_predictions",
                                             ".parquet")
        predictions.to_parquet(out, index=False)
        artefact(out, rows=len(predictions), synthetic=source.synthetic)

    return {
        "synthetic": source.synthetic,
        "panel_origin": source.origin,
        "panel_detail": source.detail,
        "risk_set": shape,
        "split": {k: {"rows": len(v), "units": int(v["zcta"].nunique()),
                      "events": int(v["event"].sum())}
                  for k, v in parts.items()},
        "fit": model.summary(),
        "evaluation": report.to_dict(),
        "brier_skill": round(skill, 5),
        "null_model": null_report.to_dict(),
        "conformal": coverage.to_dict(),
        "recovery": recovery,
        "predictions_path": paths.rel(out),
        "baseline_hazard": model.baseline_hazard(
            np.arange(shape["t_min"], shape["t_max"] + 1)
        ).to_dict(orient="records"),
        **extra,
    }


def _real_panel_checks(risk, spec: HazardSpec, parts: dict,
                       model: DiscreteTimeHazard,
                       scoped_panel) -> dict:
    """Everything that only makes sense once the target is the real one.

    Kept out of :func:`run` because each of these is a caveat rather than a
    result, and because a caveat computed in the same breath as the number
    it qualifies is a caveat that cannot be dropped from the report by
    someone assembling a slide in a hurry.
    """
    with step("diagnostics"):
        # Counted on the TRAINING split, not the whole risk set: these are
        # the observations the coefficients were actually estimated from,
        # and pairing train-side events with whole-sample episodes would
        # flatter the ratio by exactly the size of the held-out splits.
        train = parts["train"]
        episodes = diagnostics.independent_episodes(train, REAL_CLUSTER_COL)
        naive = DiscreteTimeHazard(
            replace(spec, cluster_col="zcta")).fit(train)
        out = {
            "contamination": diagnostics.CONTAMINATION,
            # Facilities counted over the whole SCOPED PANEL while events
            # and episodes come from training. Deliberately mismatched: the
            # building count is the generous end of the bracket and the
            # verdict is taken on it, so it is counted in the way least
            # likely to manufacture a failure. See usable_facilities.
            "power": diagnostics.events_per_parameter(
                int(train["event"].sum()),
                model.summary()["n_parameters"], episodes,
                diagnostics.usable_facilities(scoped_panel)),
            "event_timing": diagnostics.event_timing(risk),
            "events_by_metro": diagnostics.events_by_metro(
                risk, REAL_CLUSTER_COL),
            # The same fit under the clustering the code used to assume, so
            # the report can show how much of the apparent precision was an
            # artefact of clustering on the wrong thing.
            "coefficients_clustered_by_zcta":
                naive.summary()["coefficients"],
            "temporal_secondary": sensitivities.temporal_check(
                risk, spec, cutoff_t=TEMPORAL_CUTOFF_T),
            "annual_sensitivity": sensitivities.annual_sensitivity(
                risk, spec, parts),
            "transfer_smoke_test": _transfer(model),
        }
    metric("hazard_events_per_parameter_effective",
           out["power"]["events_per_parameter_effective"])
    return out


def _transfer(model: DiscreteTimeHazard) -> dict:
    """Score Phoenix and Boise, which no fit was allowed to see."""
    held = load_panel(heldout=True)
    if held.synthetic:
        return {"ran": False,
                "reason": "no real panel for the held-out metros"}
    return sensitivities.transfer_check(model, build_risk_set(held.frame))


def _recovery_table(model: DiscreteTimeHazard, synthetic: bool) -> list[dict]:
    """On synthetic data the truth is known, so report the error directly.

    This is the only table in the project where a "true" column can exist,
    and it exists precisely because the data is not real. It is what turns
    "the model ran" into "the model is right", and it disappears the moment
    the run is against the real panel — where, correctly, there is nothing
    to compare a coefficient to.
    """
    if not synthetic:
        return []
    truth = true_coefficients()
    coef = model.coefficients().set_index("term")
    rows = []
    for name, true_value in truth.items():
        if name not in coef.index:
            continue
        est = float(coef.loc[name, "coefficient"])
        se = float(coef.loc[name, "std_error"])
        rows.append({"term": name, "true": true_value,
                     "estimate": round(est, 4), "std_error": round(se, 4),
                     "error": round(est - true_value, 4),
                     "z_from_truth": round((est - true_value) / se, 2)
                     if se > 0 else None})
    return rows



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", default="auto",
                    choices=("auto", "spline", "dummies", "linear"),
                    help="shape of the time baseline; 'auto' is a spline "
                         "on the fixture and linear on the real panel, "
                         "which has 6 distinct event times")
    ap.add_argument("--n-knots", type=int, default=4)
    ap.add_argument("--alpha", type=float, default=0.10,
                    help="conformal miscoverage level; 0.10 gives 90%% sets")
    ap.add_argument("--synthetic", action="store_true",
                    help="use the fixture even if a real panel is present")
    ap.add_argument("--n-units", type=int, default=None,
                    help="synthetic panel size (ignored for a real panel)")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L4", "discrete-time hazard"):
        result = run(baseline=args.baseline, n_knots=args.n_knots,
                     alpha=args.alpha, force_synthetic=args.synthetic,
                     n_units=args.n_units)

    console.print_report(result)

    prefix = "SYNTHETIC_" if result["synthetic"] else ""
    out = write_json(paths.METRICS / f"{prefix}hazard_report.json", result)
    artefact(out, synthetic=result["synthetic"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
