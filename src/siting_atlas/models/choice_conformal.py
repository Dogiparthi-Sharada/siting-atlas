"""Conformal prediction sets for the choice model: "which ZIPs, and how sure".

Why this exists
---------------
The choice model gets the right ZCTA into its top ten half the time. As a
point prediction that is useless — nobody can act on a 18% top-1 hit rate.
As a SET it is a different object entirely:

    "These N ZIP codes contain the site, with 90% coverage."

A city can act on that. It can review zoning in N places, consult N
neighbourhoods, plan road capacity for N candidates. The model's weakness at
top-1 stops mattering once the deliverable is a calibrated set, and the
guarantee does not depend on the model being right — see `conformal.py` for
the argument in full.

Adaptive sets, not a fixed threshold
------------------------------------
`conformal.py` scores a binary outcome by ``1 - p_hat(true)``. That does not
transfer here, because our choice sets run from 4 ZCTAs to 848 and their
difficulty varies with them. A single probability threshold would return two
ZIPs in a small metro and several hundred in New York.

So this uses **adaptive prediction sets** (APS). Sort the alternatives by
descending probability and accumulate; the score of a calibration decision is
the cumulative mass up to AND INCLUDING the true choice. A decision the model
nailed scores near its own top probability; one it got badly wrong scores
near 1. The test set then takes alternatives in descending order until the
cumulative mass reaches ``q_hat``.

The effect is that an easy metro gets a small set and a hard one gets a large
set, from the same guarantee. That is the property worth having: the set size
IS the honest statement of how much the model knows about that metro.

What is guaranteed, and what is not
-----------------------------------
Marginal coverage at least ``1 - alpha``, over decisions, given only that
calibration and test decisions are exchangeable. NOT per-metro coverage:
conditional coverage is not attainable distribution-free, so a promise of
"90% in Chicago specifically" is not on offer and is not made.

Exchangeability is a real assumption here. Decisions are split at random
rather than by date, so a structural change in how Amazon sites would break
it. With 94 decisions spanning 2018-2026 that is a live risk and it is
reported rather than assumed away.
"""

from __future__ import annotations

import numpy as np

from ..common.logging_setup import get_logger
from .choice import ChoiceData, predict
from .conformal import conformal_quantile

_log = get_logger("models.choice_conformal")

__all__ = ["aps_scores", "calibrate", "prediction_sets", "summarise"]


def _per_decision(d: ChoiceData, p: np.ndarray):
    """Yield (decision index, row indices sorted by descending probability)."""
    for g in range(d.n_decisions):
        rows = np.flatnonzero(d.group == g)
        yield g, rows[np.argsort(-p[rows], kind="stable")]


def aps_scores(theta: np.ndarray, d: ChoiceData) -> np.ndarray:
    """Cumulative probability up to and including the true choice.

    One score per decision, in [0, 1]. Low means the model ranked the truth
    highly; near 1 means it buried it.
    """
    p = predict(theta, d)
    out = np.empty(d.n_decisions)
    for g, order in _per_decision(d, p):
        cumulative = np.cumsum(p[order])
        hit = np.flatnonzero(order == d.chosen[g])
        # The chosen row is always present: `build` drops any decision whose
        # choice set lacks its own observed choice.
        out[g] = cumulative[hit[0]]
    return out


def calibrate(theta: np.ndarray, calibration: ChoiceData,
              alpha: float = 0.10) -> float:
    """q_hat from the calibration decisions, with the finite-sample bump."""
    scores = aps_scores(theta, calibration)
    q_hat = conformal_quantile(scores, alpha)
    _log.info("calibrated on %d decisions: q_hat=%.4f at alpha=%.2f",
              calibration.n_decisions, q_hat, alpha)
    return q_hat


def prediction_sets(theta: np.ndarray, d: ChoiceData,
                    q_hat: float) -> list[np.ndarray]:
    """Row indices in each decision's prediction set, best first."""
    p = predict(theta, d)
    sets = []
    for _, order in _per_decision(d, p):
        cumulative = np.cumsum(p[order])
        # Include everything up to the first alternative that takes the
        # cumulative mass to q_hat. `searchsorted` gives that position; +1
        # because the crossing alternative is itself included.
        take = int(np.searchsorted(cumulative, q_hat, side="left")) + 1
        sets.append(order[:min(take, len(order))])
    return sets


def summarise(theta: np.ndarray, d: ChoiceData, q_hat: float,
              alpha: float = 0.10) -> dict:
    """Coverage and set size on held-out decisions.

    Set size is the number a city would actually have to look at, so it is
    reported as a distribution and not only as a mean: a median of 12 with a
    maximum of 300 is a different proposition from a flat 15.
    """
    sets = prediction_sets(theta, d, q_hat)
    sizes = np.array([len(s) for s in sets], dtype=float)
    covered = np.array([d.chosen[g] in s for g, s in enumerate(sets)])
    choice_set_sizes = np.bincount(d.group).astype(float)

    return {
        "alpha": alpha,
        "nominal_coverage": 1.0 - alpha,
        "q_hat": float(q_hat),
        "n_decisions": int(d.n_decisions),
        "empirical_coverage": float(covered.mean()),
        "set_size_median": float(np.median(sizes)),
        "set_size_mean": float(sizes.mean()),
        "set_size_min": int(sizes.min()),
        "set_size_max": int(sizes.max()),
        # The number that decides whether this is useful. A set of 12 out of
        # 848 is a real narrowing; 400 out of 848 is a shrug with a
        # confidence level attached.
        "median_share_of_choice_set": float(
            np.median(sizes / choice_set_sizes)),
        "choice_set_size_median": float(np.median(choice_set_sizes)),
    }
