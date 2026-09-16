"""The robust covariance, and the two parameters it refuses to report on.

Train Sec. 8.6, p. 201 gives ``H^-1 W H^-1`` and calls it "valid whether or
not the model is correctly specified". That validity has a precondition the
printed table usually hides: it is derived from the asymptotic normality of
the score at an INTERIOR maximum, where the gradient vanishes in every
direction. `choice.py` parameterises ``beta_k = exp(theta_k)``, so a
coefficient of zero is ``theta_k -> -inf``, and two of the three attraction
variables are there. At such a point the gradient does not vanish, the
Hessian block is not the information matrix, and the number the formula
returns is not a wide standard error — it is an arbitrary one, whose size is
set by how far the optimiser happened to wander before it stopped.

So this module returns a REFUSAL for those parameters, with the reason
attached, and computes the sandwich on the interior block alone. That block
is itself conditional on the other two being exactly zero rather than
estimated at zero; inference after a boundary selection is a known open
problem, and the caveat is recorded rather than resolved.

That last sentence is standard knowledge and this project's rule is that a
named citation has a notes file in `docs/research/` behind it. Andrews (1999)
on estimation when a parameter is on a boundary is the reference usually
given, it is NOT in `../Research/`, and nobody here has opened it. So it is
named here as a lead to follow rather than as support, and it must not appear
in `REFERENCES.md` above a [K] mark until somebody reads it. The substance of
the caveat does not depend on the attribution: the interior block is
conditional on a selection, and that is visible from the algebra above.

The derivatives are analytic. Finite-differencing a log-likelihood that is
flat to machine precision in two of its three directions returns noise.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .choice import ChoiceData

#: A coefficient below this fraction of the numeraire is AT the boundary, not
#: merely small. The fitted values are ~3e-16 — machine zero against 1.0 — so
#: nothing depends on where between 1e-16 and 1e-4 the line is drawn.
BOUNDARY_TOL = 1e-6

REFUSAL = (
    "beta is at the boundary (beta = exp(theta) = 0 requires theta -> -inf), "
    "so the maximum is not interior, the gradient does not vanish and the "
    "Hessian block is not the information matrix the sandwich asymptotics "
    "assume. A standard error here would be a number with no interpretation, "
    "so none is printed. The bootstrap is the estimator to read instead.")

__all__ = ["BOUNDARY_TOL", "REFUSAL", "sandwich", "score_and_hessian"]


def score_and_hessian(theta: np.ndarray, d: ChoiceData):
    """Per-decision scores and the total Hessian in theta, analytically.

    With ``u_j = beta'a_j``, ``U_n = sum_j u_j``, ``S_nk = sum_j a_jk`` and c
    the chosen row, ``dlnP_n/dtheta_k = beta_k (a_ck/u_c - S_nk/U_n)``. The
    Hessian follows by differentiating once more; the ``beta_k`` factor from
    the exp reparameterisation leaves a diagonal term behind.
    """
    beta = np.concatenate([[1.0], np.exp(theta)])
    u = d.a @ beta
    totals = np.bincount(d.group, weights=u)
    sums = np.stack([np.bincount(d.group, weights=d.a[:, k])
                     for k in range(1, d.a.shape[1])], axis=1)
    ac = d.a[d.chosen, 1:]
    uc = u[d.chosen][:, None]
    scores = beta[1:] * (ac / uc - sums / totals[:, None])
    outer = (np.einsum("nk,nl->kl", sums, sums / totals[:, None] ** 2)
             - np.einsum("nk,nl->kl", ac, ac / uc ** 2))
    return scores, np.diag(scores.sum(axis=0)) + np.outer(
        beta[1:], beta[1:]) * outer


def sandwich(theta: np.ndarray, d: ChoiceData, names: tuple[str, ...],
             alpha: float = 0.05) -> dict:
    """``H^-1 W H^-1`` on the interior block; a refusal for the rest.

    One score per DECISION, which is what makes the clustering right by
    construction: each decision contributes exactly one term to the
    log-likelihood, so there is no within-cluster correlation left to correct
    for. Intervals are formed in theta and exponentiated, which is exact for
    a monotone transform and keeps beta positive.
    """
    beta = np.exp(theta)
    interior = np.flatnonzero(beta > BOUNDARY_TOL)
    out = {name: {"available": False, "beta": float(beta[k]),
                  "reason": REFUSAL}
           for k, name in enumerate(names) if k not in interior}
    if not len(interior):
        return out

    scores, hess = score_and_hessian(theta, d)
    s, hinv = scores[:, interior], np.linalg.inv(
        hess[np.ix_(interior, interior)])
    se = np.sqrt(np.diag(hinv @ (s.T @ s) @ hinv))
    z = norm.ppf(1 - alpha / 2)
    for i, k in enumerate(interior):
        out[names[k]] = {
            "available": True, "beta": float(beta[k]),
            "se_log_beta": float(se[i]),
            "se_beta_delta_method": float(beta[k] * se[i]),
            "lower": float(np.exp(theta[k] - z * se[i])),
            "upper": float(np.exp(theta[k] + z * se[i])),
            # Against 1.0, never against 0.0: households is the numeraire, so
            # theta = 0 IS the null "worth the same as one household".
            "z_against_ratio_one": float(theta[k] / se[i]),
            "p_two_sided_against_ratio_one":
                float(2 * norm.sf(abs(theta[k] / se[i]))),
            "conditional_on_boundary_selection": bool(len(interior)
                                                      < len(names)),
        }
    return out
