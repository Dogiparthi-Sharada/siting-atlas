"""One re-split of the covariate search: fit every arm, score every arm.

Everything here is PAIRED. A repeat draws one train/test partition of the
decisions and every arm is re-fitted on that partition, so a fold that
happens to contain easy decisions lifts all arms at once and the
difference between two arms removes it. `NOTES_GBM_BENCHMARK.md` section 4
measured why that matters: a single split moves a top-10 count by three
decisions, which is larger than any effect this search is looking for.

Forward selection, and where it is allowed to look
--------------------------------------------------
A subset chosen by looking at the test fold is a subset chosen by the
answer, and the gain it reports is selection bias. So `forward_select`
runs entirely INSIDE the training decisions: it splits them again,
75/25, fits on the inner-training part and scores on the inner-validation
part. The test fold is untouched until the selected subset is refitted on
the whole training fold and scored once.

The selection criterion is the inner-validation MEAN LOG-LIKELIHOOD PER
DECISION, not top-k. Three reasons, all of them declared rather than
discovered afterwards:

  1  `MODEL_SPEC.md` section 9.3 says top-k is not the headline, and
     Train section 3.8.1 p.69 says "percent correctly predicted" "should
     actually be avoided". Selecting on it would make it the estimand.
  2  A hit count over ~70 inner-validation decisions is a very coarse
     criterion; the log-likelihood uses every decision's full probability.
  3  Selecting on a different quantity from the one reported weakens, but
     does not remove, the selection bias in the reported top-k.

It is still greedy and still forward. At 479 decisions and eight
candidate columns an exhaustive search over 2^8 subsets is affordable in
compute and is NOT affordable in honesty: the best of 256 subsets on a
finite validation fold is a maximum of 256 noisy numbers, and its
selected gain is biased upward by roughly the spread of that noise.
Forward selection with a stopping rule looks at far fewer and stops when
the criterion stops improving.
"""

from __future__ import annotations

import numpy as np

from .choice import ChoiceData, fit, predict
from .covariate_frame import columns_only

#: Greedy additions allowed. Three is the point past which the events per
#: parameter of the smallest arm falls under the conventional floor of 10:
#: 287 training decisions, 7 estimable parameters, 41 per parameter at the
#: pooled level but under 10 inside the large-metro stratum on some folds.
MAX_STEPS = 3

#: Share of the TRAINING decisions held back for the inner selection
#: score. Not the test fold, which no selection step may see.
INNER_FRACTION = 0.25

__all__ = ["INNER_FRACTION", "MAX_STEPS", "fit_and_score", "forward_select",
           "split_decisions"]


def split_decisions(n: int, seed: int,
                    test_fraction: float) -> tuple[np.ndarray, np.ndarray]:
    """The `choice_runner` partition: permute decisions, cut, sort."""
    order = np.random.default_rng(seed).permutation(n)
    cut = int(round(n * (1 - test_fraction)))
    return np.sort(order[:cut]), np.sort(order[cut:])


def fit_and_score(train: ChoiceData, test: ChoiceData,
                  cols: tuple[str, ...]) -> tuple[np.ndarray, dict]:
    """Fit one column subset on `train`, return its scores on `test`."""
    tr, te = columns_only(train, cols), columns_only(test, cols)
    fitted = fit(tr)
    theta = np.asarray(fitted["theta"], float)
    return predict(theta, te), fitted


def _mean_log_likelihood(score: np.ndarray, d: ChoiceData) -> float:
    """Out-of-sample log-likelihood per decision. Higher is better."""
    return float(np.log(np.maximum(score[d.chosen], 1e-300)).mean())


def forward_select(train: ChoiceData, base: tuple[str, ...],
                   candidates: tuple[str, ...], seed: int,
                   max_steps: int = MAX_STEPS) -> tuple[tuple[str, ...],
                                                        list[dict]]:
    """Greedy forward selection inside the training decisions only.

    Returns the selected column tuple and the trace of every step, so the
    artefact records what was considered and not only what won.
    """
    inner_tr, inner_va = split_decisions(train.n_decisions, seed,
                                         INNER_FRACTION)
    a, b = train.subset(inner_tr), train.subset(inner_va)
    chosen = tuple(base)
    remaining = [c for c in candidates if c not in chosen]
    score, _ = fit_and_score(a, b, chosen)
    best = _mean_log_likelihood(score, b)
    trace = [{"step": 0, "columns": list(chosen), "inner_ll": best}]
    for step in range(1, max_steps + 1):
        offers = {}
        for col in remaining:
            s, _ = fit_and_score(a, b, (*chosen, col))
            offers[col] = _mean_log_likelihood(s, b)
        if not offers:
            break
        winner = max(offers, key=offers.get)
        trace.append({"step": step, "offers": offers, "winner": winner,
                      "accepted": bool(offers[winner] > best)})
        if offers[winner] <= best:
            break
        best = offers[winner]
        chosen = (*chosen, winner)
        remaining.remove(winner)
    return chosen, trace
