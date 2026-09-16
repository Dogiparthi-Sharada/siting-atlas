"""The sandwich `choice_sandwich` does not compute: clustered by METRO.

The gap this fills, and it is a real one
----------------------------------------
`choice_sandwich.sandwich` says, in its own docstring, "One score per
DECISION, which is what makes the clustering right by construction: each
decision contributes exactly one term to the log-likelihood, so there is
no within-cluster correlation left to correct for." The first clause is
true and the second does not follow. One term per decision makes the
SCORE well defined per decision; it does not make two decisions
independent. `choice_bootstrap.metro_clusters` exists precisely because
they are not: six of the published arm's 94 openings are Los Angeles and
share one choice set and one set of attraction values, and on the arm
this module is used for, 485 decisions sit in 194 metros.

So `choice_sandwich`'s ``H^-1 (sum_n s_n s_n') H^-1`` is the
independent-decisions sandwich. The metro-clustered one replaces the
per-decision outer products with per-metro ones,
``H^-1 (sum_g s_g s_g') H^-1`` with ``s_g = sum_{n in g} s_n``, which is
Liang-Zeger CR0. If decisions within a metro are positively correlated it
is LARGER, and the difference between the two is a measurement of how
much the independence assumption was worth.

What is NOT done here
---------------------
No small-cluster correction. The usual ``G/(G-1) * (N-1)/(N-K)`` factor
is 1.005 at G = 194 and would change nothing at the third decimal; it is
reported as a number so a reader can apply it rather than being applied
silently. And the boundary refusal is inherited unchanged: a parameter at
``beta = 0`` has no interior optimum, so no sandwich of any clustering is
defined for it. `choice_sandwich.REFUSAL` is the text that goes with it,
reused rather than reworded.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .choice import ChoiceData
from .choice_sandwich import BOUNDARY_TOL, REFUSAL, score_and_hessian

__all__ = ["clustered_sandwich"]


def clustered_sandwich(theta: np.ndarray, d: ChoiceData,
                       names: tuple[str, ...], clusters: np.ndarray,
                       alpha: float = 0.05) -> dict:
    """``H^-1 (sum_g s_g s_g') H^-1`` on the interior block; refusal else."""
    beta = np.exp(theta)
    interior = np.flatnonzero(beta > BOUNDARY_TOL)
    out: dict = {name: {"available": False, "beta": float(beta[k]),
                        "reason": REFUSAL}
                 for k, name in enumerate(names) if k not in interior}
    if not len(interior):
        return out

    scores, hess = score_and_hessian(theta, d)
    labels = np.unique(clusters)
    by_metro = np.stack([scores[clusters == g].sum(axis=0) for g in labels])
    s = by_metro[:, interior]
    per_decision = scores[:, interior]
    hinv = np.linalg.inv(hess[np.ix_(interior, interior)])
    se = np.sqrt(np.diag(hinv @ (s.T @ s) @ hinv))
    # The independent-decisions standard error, recomputed here purely so
    # the RATIO can be reported. Clustering is usually assumed to inflate
    # it; whether it does is an empirical question about the sign of the
    # within-metro dependence, and the design effect is the answer.
    se_ind = np.sqrt(np.diag(
        hinv @ (per_decision.T @ per_decision) @ hinv))
    deff = ((s ** 2).sum(axis=0)
            / np.maximum((per_decision ** 2).sum(axis=0), 1e-300))
    z = norm.ppf(1 - alpha / 2)
    n, k = int(d.n_decisions), len(interior)
    correction = (len(labels) / (len(labels) - 1)) * ((n - 1) / (n - k))
    for i, kk in enumerate(interior):
        out[names[kk]] = {
            "available": True, "beta": float(beta[kk]),
            "se_log_beta": float(se[i]),
            "lower": float(np.exp(theta[kk] - z * se[i])),
            "upper": float(np.exp(theta[kk] + z * se[i])),
            "z_against_ratio_one": float(theta[kk] / se[i]),
            "p_two_sided_against_ratio_one":
                float(2 * norm.sf(abs(theta[kk] / se[i]))),
            "excludes_ratio_one": bool(
                np.exp(theta[kk] - z * se[i]) > 1.0
                or np.exp(theta[kk] + z * se[i]) < 1.0),
            # > 1 means metro clustering WIDENS the interval, which is
            # what everybody assumes. < 1 means the scores of two
            # decisions in one metro partly cancel, and the assumption
            # was wrong in this model.
            "se_ratio_vs_independent_decisions": float(se[i] / se_ind[i]),
            "within_metro_design_effect": float(deff[i]),
            "conditional_on_boundary_selection": bool(len(interior)
                                                      < len(names)),
        }
    out["_meta"] = {
        "estimator": "Liang-Zeger CR0, clusters are metros",
        "n_clusters": int(len(labels)), "n_decisions": n,
        "small_cluster_correction_not_applied": float(correction),
    }
    return out
