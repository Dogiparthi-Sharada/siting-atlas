"""One arm's fit, and the same evaluation battery the retired run reported.

Every number emitted here has a counterpart in
``outputs/metrics/hazard_report.json``, computed by the same functions, so
the revival and the retirement are comparable line for line. Nothing is
added to make the new run look better and nothing is dropped to make it look
worse; where a figure cannot be computed the reason is returned in its place.

Brier is NOT comparable across arms. Each arm has a different target, a
different test set and a different base rate, so each arm also carries the
constant-predicting null scored on its own test rows — that pairing is the
comparison, exactly as ``warehouse/catchment_band`` argues for the radius
sweep. ECE is reported the same way and for the same reason.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from . import diagnostics
from .base import BaselineOnly
from .hazard import DiscreteTimeHazard, HazardSpec
from .metrics import brier_skill_score
from .risk_set import (
    EVENT_COL,
    TargetUnpopulatedError,
    build_risk_set,
    summarise,
)
from .splits import split_by_time, split_by_unit

_log = get_logger("models.hazard_revival_fit")

#: ``models/runner.REAL_CLUSTER_COL``, copied by value on purpose so that a
#: change there shows up as a disagreement rather than travelling silently.
CLUSTER_COL = "cbsa_code"

#: ``models/runner.TEMPORAL_CUTOFF_T``: 2022Q4 on a panel opening at 2018Q1.
TEMPORAL_CUTOFF_T = 19

#: ``models/runner.resolve_baseline`` returns "linear" for a real panel. The
#: argument it gives is about Q1-by-convention dating, which the MWPVL arm
#: largely repairs — but changing the time basis between the retired run and
#: this one would confound the comparison, so it is held fixed and the
#: question is left for a separate experiment.
BASELINE = "linear"


def _scored(model, null, test: pd.DataFrame, label: str) -> dict:
    """Model and null on the same rows, with the pair kept together."""
    report = model.evaluate(test, label=label)
    null_report = null.evaluate(test, label=f"{label}-null")
    y = test[EVENT_COL].to_numpy()
    pred = model.predict(test).to_numpy()
    return {
        "n_rows": int(len(test)),
        "n_events": int(y.sum()),
        "auc": round(report.auc, 4),
        "brier": round(report.brier, 6),
        "brier_null": round(null_report.brier, 6),
        "beats_null_on_brier": bool(report.brier < null_report.brier),
        "brier_skill": round(brier_skill_score(y, pred), 5),
        "ece": round(report.ece, 5),
        "ece_null": round(null_report.ece, 5),
        "null_better_calibrated": bool(null_report.ece < report.ece),
        "ece_ratio_model_over_null": round(
            float(report.ece / null_report.ece), 1)
        if null_report.ece > 0 else None,
    }


def fit_arm(frame: pd.DataFrame, covariates: tuple[str, ...], *,
            heldout: pd.DataFrame | None = None) -> dict:
    """Risk set, split, fit, and the full battery for one arm.

    The split is ``split_by_unit`` on the same seed the retired run used, so
    the train/calibration/test partition is drawn the same way; the temporal
    hold-out refits at ``TEMPORAL_CUTOFF_T``; the out-of-area hold-out scores
    the metros ``common.metros`` withholds, refitting nothing.
    """
    risk = build_risk_set(frame)
    shape = summarise(risk)
    parts = split_by_unit(risk)
    spec = HazardSpec(covariates=covariates, baseline=BASELINE,
                      cluster_col=CLUSTER_COL)

    model = DiscreteTimeHazard(spec).fit(parts["train"])
    null = BaselineOnly().fit(parts["train"])
    summary = model.summary()
    out = {
        "covariates": list(covariates),
        "risk_set": {k: shape[k] for k in ("units", "rows", "events")},
        "split": {k: {"rows": len(v), "units": int(v["zcta"].nunique()),
                      "events": int(v[EVENT_COL].sum())}
                  for k, v in parts.items()},
        "converged": summary["converged"],
        "n_parameters": summary["n_parameters"],
        "n_clusters": summary["n_clusters"],
        "log_likelihood": summary["log_likelihood"],
        "coefficients": summary["coefficients"],
        "covariates_p_lt_0_05": sorted(
            c["term"] for c in summary["coefficients"]
            if c["term"] not in ("intercept", "t") and c["p_value"] < 0.05),
        "held_out_by_unit": _scored(model, null, parts["test"],
                                    "cloglog-hazard"),
        "power": _power(risk, parts["train"], summary["n_parameters"]),
        "out_of_time": _temporal(risk, spec),
        "out_of_area": _transfer(model, null, heldout),
    }
    _log.info("arm %s: AUC %s, ECE %s against null %s",
              list(covariates), out["held_out_by_unit"]["auc"],
              out["held_out_by_unit"]["ece"],
              out["held_out_by_unit"]["ece_null"])
    return out


def _power(risk: pd.DataFrame, train: pd.DataFrame, n_parameters: int
           ) -> dict:
    """Events per parameter, counted three ways, as the retired run did.

    ``n_usable_facilities`` is deliberately not passed: ``usable_facilities``
    reads the pilot target file off disk and would answer about the wrong
    frame. The optimistic bound is therefore absent here and the verdict
    falls on the episode count, which is the conservative end.
    """
    episodes = diagnostics.independent_episodes(train, CLUSTER_COL)
    out = diagnostics.events_per_parameter(
        int(train[EVENT_COL].sum()), n_parameters, episodes)
    out["episodes_whole_risk_set"] = diagnostics.independent_episodes(
        risk, CLUSTER_COL)
    return out


def _temporal(risk: pd.DataFrame, spec: HazardSpec) -> dict:
    """Refit on t <= cutoff, score t > cutoff. The honest backtest."""
    parts = split_by_time(risk, cutoff_t=TEMPORAL_CUTOFF_T)
    if not parts["train"][EVENT_COL].sum() or \
            not parts["test"][EVENT_COL].sum():
        return {"ran": False,
                "reason": "one side of the temporal split has no events"}
    model = DiscreteTimeHazard(spec).fit(parts["train"])
    null = BaselineOnly().fit(parts["train"])
    out = {"ran": True, "cutoff_t": TEMPORAL_CUTOFF_T,
           "train_events": int(parts["train"][EVENT_COL].sum())}
    out.update(_scored(model, null, parts["test"], "temporal-holdout"))
    return out


def _transfer(model, null, heldout: pd.DataFrame | None) -> dict:
    """Score the withheld metros. No refit — this is transfer, not tuning."""
    if heldout is None or heldout.empty:
        return {"ran": False, "reason": "no held-out frame supplied"}
    try:
        risk = build_risk_set(heldout)
    except TargetUnpopulatedError as exc:
        # Not a bug and not a guard misfiring: this arm's facility set simply
        # puts no station in Phoenix or Boise, so there is nothing to
        # transfer TO. Reported rather than swallowed.
        return {"ran": False, "reason": f"no enabled cell in the held-out "
                                        f"metros for this arm ({exc})"}
    if not risk[EVENT_COL].sum():
        return {"ran": False,
                "reason": "the held-out metros carry no observed event"}
    out = {"ran": True, "n_units": int(risk["zcta"].nunique()),
           "episodes": diagnostics.independent_episodes(risk, CLUSTER_COL)}
    out.update(_scored(model, null, risk, "heldout-metros"))
    return out


def compare(new: dict, old: dict) -> dict:
    """The date contrast, stated as differences rather than left to the eye.

    Signed so that a positive number means the NEW dates did better on a
    metric where more is better, and worse where less is better; the key
    names say which. ``None`` where an arm did not run.
    """
    def delta(path: str, key: str) -> float | None:
        a, b = new.get(path, {}), old.get(path, {})
        if not a.get("ran", True) or not b.get("ran", True):
            return None
        if key not in a or key not in b:
            return None
        return round(float(a[key]) - float(b[key]), 6)

    return {
        "auc_new_minus_old": delta("held_out_by_unit", "auc"),
        "ece_new_minus_old_lower_is_better": delta("held_out_by_unit", "ece"),
        "brier_new_minus_old_lower_is_better": delta("held_out_by_unit",
                                                     "brier"),
        "brier_skill_new_minus_old": delta("held_out_by_unit",
                                           "brier_skill"),
        "auc_out_of_time_new_minus_old": delta("out_of_time", "auc"),
        "events_new_minus_old": int(new["risk_set"]["events"]
                                    - old["risk_set"]["events"]),
    }


def constant_null_verdict(arms: dict) -> dict:
    """Did calibration EVER beat the constant, in any arm or hold-out?

    Asked once, over everything, because the retirement turned on exactly
    this and a reader should not have to scan eleven blocks to check.
    """
    wins, losses = [], []
    for name, arm in arms.items():
        for split in ("held_out_by_unit", "out_of_time", "out_of_area"):
            block = arm.get(split, {})
            if not block.get("ran", True) or "ece" not in block:
                continue
            tag = f"{name}/{split}"
            (wins if block["ece"] < block["ece_null"] else losses).append(tag)
    return {"model_better_calibrated_at": wins,
            "constant_better_calibrated_at": losses,
            "n_comparisons": len(wins) + len(losses),
            "verdict": "the constant null is better calibrated everywhere"
            if not wins else "the model is better calibrated somewhere"}


def worst_case_auc(arms: dict) -> dict:
    """AUC across every arm and hold-out, so no single figure is quoted."""
    rows = []
    for name, arm in arms.items():
        for split in ("held_out_by_unit", "out_of_time", "out_of_area"):
            block = arm.get(split, {})
            if block.get("ran", True) and "auc" in block:
                rows.append({"arm": name, "split": split,
                             "auc": block["auc"],
                             "n_events": block["n_events"]})
    values = [r["auc"] for r in rows]
    return {"all": rows, "min": min(values) if values else None,
            "max": max(values) if values else None,
            "median": round(float(np.median(values)), 4) if values else None}
