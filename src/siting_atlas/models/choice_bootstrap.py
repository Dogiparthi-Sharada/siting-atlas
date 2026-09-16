"""The resampling engine: what a bootstrap replicate of this model IS.

The unit is the DECISION
------------------------
One opening contributes exactly one term to the log-likelihood, and its
choice set — every ZCTA of its metro — is what that term conditions on.
Resample alternatives instead and a metro's ZCTAs end up spread across
replicates with the chosen one possibly absent, which is not a draw from
anything. `docs/adr/0004` records the same error at a different level in the
hazard model, where 58 ZCTAs switching on together were counted as 58 draws.

There is a second level to it. Decisions are not independent ACROSS METROS
either: six of the 94 openings are Los Angeles and share one choice set and
one set of attraction values. ``metro_clusters`` recovers that grouping from
the choice sets themselves, so a block bootstrap over metros can run beside
the per-decision one and the difference be reported.

How many replicates
-------------------
Not a round number. ``bootstrap`` runs in batches and stops when Monte Carlo
noise can no longer change what the interval is FOR: the verdict "does this
ratio exclude 1.0". Two conditions, both on the interval endpoint NEAREST
1.0, and both estimated by resampling the replicates already in hand rather
than by refitting anything. The FAR endpoint is deliberately excluded from
the rule — a ratio has a heavy right tail at this sample size, so the 97.5th
percentile would need of the order of 100,000 replicates to settle and would
still be the 97.5th percentile of 56 decisions. It is measured and reported,
not chased.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from ..common.logging_setup import get_logger
from .choice import ChoiceData, _neg_log_likelihood
from .choice_sandwich import BOUNDARY_TOL

_log = get_logger("models.choice_bootstrap")

#: Two-sided 95%. A boundary parameter is reported one-sided instead — see
#: `choice_inference.py`, which owns the interval definitions.
ALPHA = 0.05

#: Batches, floor and cost ceiling for the adaptive replicate count, then the
#: two stopping conditions on the endpoint nearest 1.0.
R_BATCH, R_MIN, R_MAX = 250, 500, 4000
MCSE_WIDTH_TARGET, VERDICT_MARGIN = 0.01, 10.0

__all__ = ["ALPHA", "R_BATCH", "R_MIN", "R_MAX", "MCSE_WIDTH_TARGET",
           "VERDICT_MARGIN", "rows_by_decision", "resample_decisions",
           "metro_clusters", "refit", "bootstrap", "jackknife_acceleration",
           "mcse"]


def rows_by_decision(d: ChoiceData) -> list[np.ndarray]:
    """Row indices of each decision's choice set, computed once."""
    order = np.argsort(d.group, kind="stable")
    edges = np.cumsum(np.bincount(d.group, minlength=d.n_decisions))
    return np.split(order, edges[:-1])


def resample_decisions(d: ChoiceData, draw: np.ndarray,
                       rows: list[np.ndarray] | None = None) -> ChoiceData:
    """Rebuild the data from decision indices, repeats allowed.

    ``ChoiceData.subset`` cannot be used: it maps indices through a dict, so
    a decision drawn twice would collapse to one and the replicate would
    quietly be a draw WITHOUT replacement — understating the spread, which is
    the flattering direction.
    """
    rows = rows if rows is not None else rows_by_decision(d)
    take = [rows[g] for g in draw]
    sizes = np.array([len(r) for r in take])
    offsets = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    chosen = np.array([o + int(np.flatnonzero(r == d.chosen[g])[0])
                       for o, r, g in zip(offsets, take, draw, strict=True)])
    return ChoiceData(
        d.a[np.concatenate(take)],
        np.repeat(np.arange(len(draw)), sizes),
        chosen, [d.ids[g] for g in draw], d.names)


def metro_clusters(d: ChoiceData) -> np.ndarray:
    """Label each decision by its metro, read off the choice sets themselves.

    Two decisions in the same metro face the SAME alternatives, so the pair
    (choice-set size, numeraire total) identifies the metro with no CBSA code
    carried through. Checked against the real codes in
    `tests/unit/test_choice_inference.py`: the partitions agree exactly.
    """
    keys = [(len(r), round(float(d.a[r, 0].sum()), 6))
            for r in rows_by_decision(d)]
    lookup: dict[tuple, int] = {}
    return np.array([lookup.setdefault(k, len(lookup)) for k in keys])


def refit(d: ChoiceData, theta0: np.ndarray) -> np.ndarray:
    """One replicate fit: BFGS then Nelder-Mead, from two starting values.

    `choice.fit` uses five starts, right for the headline and 3.4x the cost
    per replicate. Two — the estimate and the origin — reproduced all five to
    1e-6 in beta over 40 replicates when this was written.
    """
    best = None
    for start in (theta0, np.zeros_like(theta0)):
        r = minimize(_neg_log_likelihood, start, args=(d,), method="BFGS")
        r = minimize(_neg_log_likelihood, r.x, args=(d,), method="Nelder-Mead")
        # The same guard as choice.fit, and for the same reason. Without the
        # finiteness test a non-finite first start is never displaced: every
        # later `r.fun < nan` is False, so `best` keeps the NaN result and this
        # returns NaN parameters with no warning. That failure was found in
        # choice.py on 2026-09-14; this copy of the loop was missed and still
        # had it on 2026-09-16.
        if not np.isfinite(r.fun):
            continue
        if best is None or r.fun < best.fun:
            best = r

    if best is None:
        # Both starts failed. Raising beats returning NaN: a replicate that
        # silently yields NaN parameters poisons the percentile it feeds
        # without ever failing a test.
        raise ValueError(
            "bootstrap replicate: both starting values produced a non-finite "
            "objective, so no usable fit exists for this resample")
    return best.x


def mcse(values: np.ndarray, q: float, seed: int, b: int = 400) -> float:
    """Monte Carlo error of a percentile, by resampling the replicates.

    No refits: how much the endpoint moves because we drew R replicates
    rather than infinitely many is answered by the R numbers in hand.
    """
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(b, len(values)))
    return float(np.std(np.percentile(values[idx], q, axis=1)))


def endpoint_errors(beta_k: np.ndarray, seed: int) -> dict:
    """Both endpoints, their Monte Carlo errors, and the verdict margin."""
    lo, hi = np.percentile(beta_k, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])
    m_lo = mcse(beta_k, 100 * ALPHA / 2, seed)
    m_hi = mcse(beta_k, 100 * (1 - ALPHA / 2), seed + 1)
    near, m_near = ((lo, m_lo) if abs(lo - 1.0) <= abs(hi - 1.0)
                    else (hi, m_hi))
    return {"lower": float(lo), "upper": float(hi),
            "mcse_lower": m_lo, "mcse_upper": m_hi,
            "near_endpoint_mcse_share_of_width": m_near / max(hi - lo, 1e-12),
            "near_endpoint_distance_from_one_in_mcse":
                abs(near - 1.0) / m_near if m_near else float("inf")}


def bootstrap(d: ChoiceData, theta_hat: np.ndarray, seed: int,
              cluster: np.ndarray | None = None) -> dict:
    """Resample DECISIONS (or whole metros) with replacement and refit.

    Only the INTERIOR parameters gate the stopping rule: a boundary
    parameter's interval says "indistinguishable from zero" whatever its
    third decimal does, so spending replicates to settle it buys nothing.
    """
    rows = rows_by_decision(d)
    rng = np.random.default_rng(seed)
    interior = np.flatnonzero(np.exp(theta_hat) > BOUNDARY_TOL)
    units = (np.unique(cluster) if cluster is not None
             else np.arange(d.n_decisions))
    members = ([np.flatnonzero(cluster == u) for u in units]
               if cluster is not None else None)
    reps: list[np.ndarray] = []
    trace, errors, settled = [], {}, False
    while len(reps) < R_MAX:
        for _ in range(R_BATCH):
            pick = rng.integers(0, len(units), len(units))
            draw = (np.concatenate([members[p] for p in pick])
                    if members is not None else pick)
            reps.append(refit(resample_decisions(d, draw, rows), theta_hat))
        beta = np.exp(np.array(reps))
        errors = {int(k): endpoint_errors(beta[:, k], seed + 7)
                  for k in range(beta.shape[1])}
        settled = all(
            errors[k]["near_endpoint_mcse_share_of_width"] < MCSE_WIDTH_TARGET
            and errors[k]["near_endpoint_distance_from_one_in_mcse"]
            > VERDICT_MARGIN for k in interior)
        trace.append({"replicates": len(reps), "settled": bool(settled),
                      **{f"param_{k}": errors[k] for k in interior}})
        if len(reps) >= R_MIN and settled:
            break
    _log.info("bootstrap over %s: %d replicates, settled=%s",
              "metros" if cluster is not None else "decisions",
              len(reps), settled)
    return {"beta": np.exp(np.array(reps)), "replicates": len(reps),
            "n_units": int(len(units)), "trace": trace,
            "settled": bool(settled), "endpoint_errors": errors}


def jackknife_acceleration(d: ChoiceData, theta_hat: np.ndarray,
                           k: int) -> float:
    """BCa acceleration, from leave-one-DECISION-out refits."""
    rows = rows_by_decision(d)
    keep = np.arange(d.n_decisions)
    vals = np.array([
        np.exp(refit(resample_decisions(
            d, np.delete(keep, i), rows), theta_hat)[k])
        for i in range(d.n_decisions)])
    dev = vals.mean() - vals
    denom = 6.0 * (dev @ dev) ** 1.5
    return float((dev ** 3).sum() / denom) if denom else 0.0
