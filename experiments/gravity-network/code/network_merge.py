"""What the network covariates cost: Train's zone merger, measured.

The claim being tested
----------------------
`MODEL_SPEC.md` §1 buys the ``V = ln(beta'a)`` form from Train §3.4
Example 2 by one argument and one only: merge two zones and the
attraction ADDS, ``a_j + a_k = a_c``, so ``exp(V_j) + exp(V_k) =
exp(V_c)`` and ``P_j + P_k = P_c``. The model then does not depend on
where the Census drew the ZCTA lines. Every attraction in the published
specification is a count and the identity is exact.

A proximity is not a count. Merge two ZCTAs and the merged zone's
distance to the nearest sortation centre is the SMALLER of the two
distances, so its proximity is ``max(p_j, p_k)`` and not ``p_j + p_k``.
The merged zone is therefore worth ``beta_p * min(p_j, p_k)`` LESS than
the two zones were worth apart. Attraction leaks out of the metro at
every merger, the denominator moves with it, and every other zone's
probability changes too.

That is an argument. This module turns it into two numbers.

1. **The additivity error at the fitted beta.** Merge one pair at a time
   and compare ``P_c`` with ``P_j + P_k``. On the published
   extensive-only specification this is exactly zero and that is the
   control: if the code reports anything but zero there, the measurement
   is wrong and not the model. On the network specification it is the
   size of the violation.

2. **The drift in the estimate under a redrawn map.** Pair the ZCTAs of
   each metro at random, merge them, refit, and read
   ``warehousing_establishments`` again. Train's invariance is a
   statement about probabilities at a fixed beta, not about the
   estimator, so even the extensive-only specification moves a little
   when the map is coarsened -- it is being asked a coarser question.
   Running both specifications under the same redrawn maps is what
   separates "coarsening moves any estimate" from "this estimate is
   partly a statement about ZCTA boundaries".

The merge rule, declared
------------------------
Counts add. Proximities take the maximum, which is exact: the nearest
facility to the union of two zones is the nearer of the two nearest.
``network_within_50mi`` also takes the maximum, which is NOT exact -- the
true count for a merged zone is a union over two discs and needs geometry
this module does not have -- and it is a lower bound. Its coefficient is
at the positivity boundary on every fit in this project, so nothing below
turns on the approximation, and it is declared rather than hidden.
"""

from __future__ import annotations

import numpy as np

from .choice import ChoiceData
from .choice_bootstrap import refit, rows_by_decision
from .panel_network import NETWORK_COLUMNS

#: How many redrawn maps. Each costs one refit per specification.
MERGE_DRAWS = 20

__all__ = ["MERGE_DRAWS", "additivity_error", "merge_drift"]


def _max_columns(names: tuple[str, ...]) -> np.ndarray:
    """Which columns merge by max rather than by sum."""
    return np.array([n in NETWORK_COLUMNS for n in names])


def _merge_rows(a: np.ndarray, left: np.ndarray, right: np.ndarray,
                by_max: np.ndarray) -> np.ndarray:
    merged = a[left] + a[right]
    if by_max.any():
        merged[:, by_max] = np.maximum(a[left][:, by_max],
                                       a[right][:, by_max])
    return merged


def _pairings(d: ChoiceData, clusters: np.ndarray, rng) -> dict:
    """One random pairing of alternative POSITIONS per metro.

    Per metro, not per decision: a redrawn ZCTA map is one map, and every
    decision in a metro faces the same zones. Positions line up across a
    metro's decisions because `choice.build` takes every alternative
    block from the same frame in the same order.
    """
    rows = rows_by_decision(d)
    out = {}
    for g in np.unique(clusters):
        first = next(i for i in range(d.n_decisions) if clusters[i] == g)
        order = rng.permutation(len(rows[first]))
        cut = len(order) - (len(order) % 2)
        out[int(g)] = (order[:cut].reshape(-1, 2), order[cut:])
    return out


def additivity_error(d: ChoiceData, theta: np.ndarray,
                     clusters: np.ndarray, seed: int) -> dict:
    """``P_c`` against ``P_j + P_k``, one merged pair at a time.

    Exactly zero for an extensive-only specification. Anything else is
    the invariance being broken, and the quantiles say by how much.
    """
    rng = np.random.default_rng(seed)
    pairs = _pairings(d, clusters, rng)
    rows = rows_by_decision(d)
    by_max = _max_columns(d.names)
    beta = np.concatenate([[1.0], np.exp(np.asarray(theta, float))])

    rel_p, leak = [], []
    for g in range(d.n_decisions):
        idx, u = rows[g], d.a[rows[g]] @ beta
        total = u.sum()
        left, right = pairs[int(clusters[g])][0].T
        merged = _merge_rows(d.a[idx], left, right, by_max) @ beta
        pair_sum = u[left] + u[right]
        new_total = total - pair_sum + merged
        rel_p.append(merged / new_total / (pair_sum / total) - 1.0)
        leak.append((pair_sum - merged) / pair_sum)
    rel_p, leak = np.abs(np.concatenate(rel_p)), np.concatenate(leak)
    return {
        "pairs_merged": int(len(rel_p)),
        "abs_relative_probability_error": {
            "median": float(np.median(rel_p)),
            "p90": float(np.percentile(rel_p, 90)),
            "max": float(rel_p.max()),
        },
        "attraction_lost_share": {
            "median": float(np.median(leak)),
            "p90": float(np.percentile(leak, 90)),
            "max": float(leak.max()),
        },
        "note": ("P_c vs P_j+P_k for one merged pair at a time, at the "
                 "fitted beta. Zero for an extensive-only specification "
                 "by Train §3.4 Example 2; nonzero is the invariance "
                 "being broken."),
    }


def _merged_data(d: ChoiceData, clusters: np.ndarray, pairs: dict,
                 by_max: np.ndarray) -> ChoiceData:
    rows = rows_by_decision(d)
    blocks, groups, chosen, offset = [], [], [], 0
    for g in range(d.n_decisions):
        idx = rows[g]
        pair, single = pairs[int(clusters[g])]
        left, right = pair.T
        block = np.vstack([_merge_rows(d.a[idx], left, right, by_max),
                           d.a[idx][single]])
        where = int(np.flatnonzero(idx == d.chosen[g])[0])
        if where in single:
            new = len(pair) + int(np.flatnonzero(single == where)[0])
        else:
            new = int(np.flatnonzero((left == where) | (right == where))[0])
        blocks.append(block)
        groups.append(np.full(len(block), g))
        chosen.append(offset + new)
        offset += len(block)
    return ChoiceData(np.vstack(blocks), np.concatenate(groups),
                      np.array(chosen), list(d.ids), d.names)


def merge_drift(specs: dict, clusters: np.ndarray, column: str, seed: int,
                draws: int = MERGE_DRAWS) -> dict:
    """Refit every specification under the SAME redrawn maps.

    ``specs`` maps a label to ``(ChoiceData, theta_hat)``. The same seed
    drives the pairing for all of them, so a difference between two
    labels is the specification and not the map.
    """
    out: dict = {}
    for label, (d, theta) in specs.items():
        by_max = _max_columns(d.names)
        k = d.names.index(column) - 1
        point = float(np.exp(theta[k]))
        values = []
        for r in range(draws):
            pairs = _pairings(d, clusters, np.random.default_rng(seed + r))
            merged = _merged_data(d, clusters, pairs, by_max)
            values.append(float(np.exp(refit(merged, theta)[k])))
        v = np.array(values)
        out[label] = {
            "column": column, "draws": int(draws),
            "beta_unmerged": point,
            "beta_merged_mean": float(v.mean()),
            "beta_merged_min": float(v.min()),
            "beta_merged_max": float(v.max()),
            "mean_absolute_shift": float(np.abs(v - point).mean()),
            "mean_absolute_shift_pct_of_point": float(
                np.abs(v - point).mean() / point * 100),
            "draws_crossing_one": int(((v > 1.0) != (point > 1.0)).sum()),
        }
    return out
