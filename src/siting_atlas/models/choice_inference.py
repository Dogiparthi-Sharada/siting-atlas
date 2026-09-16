"""Uncertainty for the conditional ZCTA-choice model: intervals, not points.

What an interval here is an interval ON
---------------------------------------
`choice.py` fixes households at 1 because the model is scale-invariant: only
RATIOS are identified. Every interval below is therefore on a RATIO — "how
many households one unit of this covariate is worth" — never on an absolute
effect. The null that matters is ``beta = 1``, not ``beta = 0``, and a reader
who brings the covers-zero habit will read the table backwards. No zero test
is printed, at any point, in the artefact or on the console.

Three reasons this is harder than a coefficient table
-----------------------------------------------------
1. **Two coefficients sit ON the boundary.** ``beta_k = exp(theta_k)``, so
   ``beta_k = 0`` is ``theta_k -> -inf``, and `land_area_sqmi` and
   `establishments` are both there. The sandwich assumes an interior optimum
   and is invalid at such a point — hence `choice_sandwich.py` and its
   explicit refusal. The bootstrap copes, needing no interior optimum, but
   its interval is ONE-SIDED and is labelled so.
2. **The unit of resampling is the DECISION**, never an alternative. The
   argument, and the metro-level clustering beyond it, are in
   `choice_bootstrap.py`.
3. **Train's own precondition fails.** Sec. 8.6, p. 202 justifies the
   bootstrap only *"if this sample is large enough"*. At 56 decisions that is
   exactly the clause in doubt, so the quote travels with the intervals in
   the artefact rather than sitting in a footnote nobody reads.

Which of the three estimators to believe
----------------------------------------
`MODEL_SPEC.md` Sec. 6.3 asks for the sandwich and the bootstrap side by
side, on the grounds that a disagreement is itself a finding about how
little the sample constrains the model. It is reported that way. Where they
differ, the bootstrap over METROS is the conservative one and the one to
quote.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .choice import ChoiceData
from .choice_bootstrap import (
    ALPHA,
    MCSE_WIDTH_TARGET,
    R_BATCH,
    R_MAX,
    R_MIN,
    VERDICT_MARGIN,
    bootstrap,
    jackknife_acceleration,
    mcse,
    metro_clusters,
)
from .choice_sandwich import BOUNDARY_TOL, sandwich

__all__ = ["summarise", "TRAIN_PRECONDITION"]

TRAIN_PRECONDITION = (
    "Train (2009) Sec. 8.6, p. 202, on the bootstrap: 'The sampling "
    "covariance of an estimator is, by definition, a measure of the amount "
    "by which the estimates change when different samples are taken from "
    "the population. Our original sample is one sample from the population. "
    "However, if this sample is large enough, then it is probably similar "
    "to the population, such that drawing from it is similar to drawing "
    "from the population itself.' At 56 decisions that italicised "
    "precondition is exactly what is in doubt. These intervals measure how "
    "much the estimate moves with WHICH OF OUR 56 decisions are included. "
    "That is a real and useful quantity. It is not a licence to read them "
    "as sampling variability over the population of siting decisions.")

BCA_REFUSAL = (
    "BCa needs a smooth statistic and a well-defined bias correction. With "
    "the replicates pinned at zero the jackknife acceleration estimates "
    "nothing and z0 is degenerate, so the percentile interval stands alone.")


def _interval(beta_k: np.ndarray, point: float, boundary: bool,
              seed: int) -> dict:
    """Percentile interval; one-sided when the parameter is at the boundary."""
    if boundary:
        upper = float(np.percentile(beta_k, 100 * (1 - ALPHA)))
        return {"kind": "one-sided percentile", "lower": 0.0, "upper": upper,
                # Of the endpoint actually published, which is the 95th
                # percentile here and not the 97.5th the stopping rule
                # monitors.
                "mcse_upper": mcse(beta_k, 100 * (1 - ALPHA), seed),
                # An upper bound under 1.0 is still a finding: worth strictly
                # LESS than one household. Against the numeraire, not zero.
                "excludes_ratio_one": bool(upper < 1.0),
                "share_of_replicates_at_boundary":
                    float((beta_k < BOUNDARY_TOL).mean()),
                "note": ("at the boundary the sampling distribution has an "
                         "atom at zero, so a two-sided interval would be a "
                         "fiction; all of alpha goes to the upper tail")}
    lo, hi = np.percentile(beta_k, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])
    return {"kind": "percentile", "lower": float(lo), "upper": float(hi),
            "excludes_ratio_one": bool(lo > 1.0 or hi < 1.0),
            "share_of_replicates_below_one": float((beta_k < 1.0).mean()),
            "bootstrap_median": float(np.median(beta_k)),
            "bias_point_minus_median": float(point - np.median(beta_k))}


def _bca(beta_k: np.ndarray, point: float, accel: float) -> dict:
    """Bias-corrected and accelerated endpoints, for a smooth interior ratio.

    Justified only because the statistic is smooth away from the boundary and
    the acceleration comes from 56 cheap leave-one-decision-out refits. Both
    z0 and the acceleration are themselves estimated from 56 units, so BCa is
    reported beside the percentile interval rather than instead of it.
    """
    share = (beta_k < point).mean() + 0.5 * (beta_k == point).mean()
    z0 = float(norm.ppf(min(max(share, 1e-6), 1 - 1e-6)))
    z = norm.ppf([ALPHA / 2, 1 - ALPHA / 2])
    lo, hi = np.percentile(
        beta_k, 100 * norm.cdf(z0 + (z0 + z) / (1 - accel * (z0 + z))))
    return {"kind": "BCa", "lower": float(lo), "upper": float(hi),
            "z0": z0, "acceleration": float(accel),
            "excludes_ratio_one": bool(lo > 1.0 or hi < 1.0)}


def summarise(d: ChoiceData, fitted: dict, seed: int) -> dict:
    """Everything the report needs: bootstrap, sandwich, and the caveats."""
    theta = np.asarray(fitted["theta"], float)
    names = tuple(n for n in d.names if n != fitted["numeraire"])
    beta = np.exp(theta)
    at_boundary = beta <= BOUNDARY_TOL
    clusters = metro_clusters(d)

    boot = bootstrap(d, theta, seed)
    clustered = bootstrap(d, theta, seed + 101, cluster=clusters)

    params: dict[str, dict] = {}
    for k, name in enumerate(names):
        params[name] = {
            "beta_point": float(beta[k]),
            "at_boundary": bool(at_boundary[k]),
            "interpretation": (
                f"households per unit of {name}: the ratio beta_{name} / "
                f"beta_{fitted['numeraire']}, which is what scale invariance "
                f"identifies. NOT an absolute effect."),
            "bootstrap_over_decisions":
                _interval(boot["beta"][:, k], beta[k], at_boundary[k], seed),
            "bootstrap_over_metros": _interval(
                clustered["beta"][:, k], beta[k], at_boundary[k], seed),
            # The stopping rule's own diagnostic, at the two-sided quantiles
            # it monitors. For a boundary parameter the PUBLISHED endpoint is
            # the one-sided one above, which carries its own error.
            "stopping_rule_diagnostic": boot["endpoint_errors"][k],
            "bca": {"available": False, "reason": BCA_REFUSAL}
            if at_boundary[k] else _bca(
                boot["beta"][:, k], beta[k],
                jackknife_acceleration(d, theta, k)),
        }

    return {
        "n_decisions": int(d.n_decisions),
        "n_metros": int(len(np.unique(clusters))),
        "seed": seed, "alpha": ALPHA,
        "resampling_unit": "decision (never an alternative)",
        "replicates": boot["replicates"],
        "replicates_clustered": clustered["replicates"],
        "convergence_settled": boot["settled"],
        "convergence_trace": boot["trace"],
        "convergence_rule": (
            f"batches of {R_BATCH}, minimum {R_MIN}, ceiling {R_MAX}. Stop "
            f"when every interior parameter's endpoint nearest 1.0 has a "
            f"Monte Carlo standard error under {MCSE_WIDTH_TARGET:.0%} of the "
            f"interval width AND under 1/{VERDICT_MARGIN:.0f} of its distance "
            f"from 1.0, so Monte Carlo noise cannot flip the verdict. That "
            f"error comes from resampling the replicates, needing no refits. "
            f"The far endpoint is measured and NOT chased: at n = 56 the "
            f"right tail does not settle."),
        "parameters": params,
        "sandwich": sandwich(theta, d, names, ALPHA),
        "null_that_matters": (
            "beta = 1, not beta = 0. households is the numeraire, so beta = 1 "
            "means the covariate is worth exactly one household and the model "
            "cannot tell them apart."),
        "train_precondition": TRAIN_PRECONDITION,
    }
