"""The repeated-split harness `panel_experiments` runs on every arm.

Copied from `refit_expanded._measure` and extended in three ways, each
of which is a requirement rather than a preference:

1. It records per-decision hits, not just a rate, because the lift has
   to be stratified by choice-set size (`panel_strata` says why a pooled
   lift would rank the arms on their market mix instead of on the model).
2. It runs a second algorithm on the same splits, so a difference
   between two arms can be attributed to the data or to the functional
   form rather than to whichever of the two is being read.
3. It carries the coefficient draws out, because interval width is the
   first of the three measures of confidence and the only one the GBM
   cannot produce.

The split protocol -- ``SEED``, ``TEST_FRACTION``, 60/40 over DECISIONS,
refit inside every repeat -- is IMPORTED from `choice_runner` rather
than re-declared, so `original_only` reproduces `refit_expanded`'s
original arm rather than merely resembling it.
"""

from __future__ import annotations

import numpy as np

from .choice import ChoiceData, evaluate, fit, predict
from .choice_runner import SEED, TEST_FRACTION
from .gbm_benchmark import _DEEP, _STUMP, _features, _softmax, _temperature
from .panel_strata import (
    TOP_KS,
    accumulate_strata,
    bucket_of,
    counts_from_sizes,
    finalise,
    hit_flags,
    mix_from_sizes,
)

REPEATS = 50

#: Two of `gbm_benchmark.GRID`'s six. The `shares` feature sets are
#: dropped because that benchmark measured them worth 0.04 top-10 hits
#: against `levels`; `stump` and `deep` are both kept because its
#: "capacity hurts" finding was measured at 56 training groups and is
#: exactly the kind of result that should not be assumed to survive a
#: five-fold larger sample. Labels keep the benchmark's spelling so the
#: two artefacts line up row for row.
GBM_GRID = (("gbm stump/200  levels", False, _STUMP),
            ("gbm deep/300   levels", False, _DEEP))

LOGIT = "conditional_logit"

__all__ = ["GBM_GRID", "LOGIT", "REPEATS", "measure"]


def _gbm_score(train: ChoiceData, test: ChoiceData, shares: bool,
               params: dict, seed: int) -> np.ndarray:
    """Within-metro probabilities from a lambdarank ensemble.

    The temperature is fitted on TRAINING decisions only and the map is
    strictly increasing, so no top-k count changes under it -- the same
    construction and the same reason as `gbm_benchmark`.
    """
    import warnings

    import lightgbm as lgb
    x_tr, x_te = _features(train, shares), _features(test, shares)
    y_tr = np.zeros(len(x_tr), dtype=int)
    y_tr[train.chosen] = 1
    model = lgb.LGBMRanker(objective="lambdarank", label_gain=[0, 1],
                           random_state=seed, n_jobs=1, verbose=-1, **params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(x_tr, y_tr, group=np.bincount(train.group))
        t = _temperature(model.predict(x_tr), train)
        return _softmax(model.predict(x_te), test, t)


def _brier(p: np.ndarray, d: ChoiceData) -> float:
    y = np.zeros(len(p))
    y[d.chosen] = 1.0
    return float(np.mean((p - y) ** 2))


def _coefficients(thetas: list, names: tuple) -> dict:
    """Mean beta and the 2.5-97.5 spread over re-splits, as RATIOS.

    Not a standard error, and `NOTES_EXPANDED_REFIT.md` §8 item 1 is the
    standing caveat: the re-splits resample the same decisions, so the
    spread understates true sampling variability.
    """
    arr = np.exp(np.vstack(thetas))
    return {
        "beta_mean": {n: float(arr[:, i].mean())
                      for i, n in enumerate(names[1:])},
        "beta_p025": {n: float(np.percentile(arr[:, i], 2.5))
                      for i, n in enumerate(names[1:])},
        "beta_p975": {n: float(np.percentile(arr[:, i], 97.5))
                      for i, n in enumerate(names[1:])},
    }


def measure(data: ChoiceData, repeats: int = REPEATS,
            with_gbm: bool = True) -> dict:
    """Paired re-splits. Every method is refitted inside every repeat."""
    sizes = np.bincount(data.group)
    buckets = bucket_of(sizes)
    methods = [LOGIT] + ([lab for lab, _, _ in GBM_GRID] if with_gbm else [])
    strata: dict = {m: {} for m in methods}
    pooled: dict = {m: {f"top{k}": [] for k in TOP_KS} | {"brier": []}
                    for m in methods}
    empirical_null, thetas = [], []

    for r in range(repeats):
        rng = np.random.default_rng(SEED + r)
        order = rng.permutation(data.n_decisions)
        cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
        keep_train, keep_test = np.sort(order[:cut]), np.sort(order[cut:])
        train, test = data.subset(keep_train), data.subset(keep_test)
        test_buckets = buckets[keep_test]

        theta = np.asarray(fit(train)["theta"], float)
        thetas.append(theta)
        out = evaluate(theta, test)
        empirical_null.append(
            [out["top1_uniform"], out["top5_uniform"], out["top10_uniform"],
             out["brier_uniform_null"]])

        scores = {LOGIT: predict(theta, test)}
        if with_gbm:
            for label, shares, params in GBM_GRID:
                scores[label] = _gbm_score(train, test, shares, params,
                                           SEED + r)
        for name, score in scores.items():
            accumulate_strata(strata[name], score, test, test_buckets)
            for k in TOP_KS:
                pooled[name][f"top{k}"].append(
                    float(np.mean(hit_flags(score, test, k))))
            pooled[name]["brier"].append(_brier(score, test))

    null = np.mean(empirical_null, axis=0)
    return {
        "n_decisions": int(data.n_decisions),
        "n_test": int(round(data.n_decisions * TEST_FRACTION)),
        "n_alternatives": int(len(data.a)),
        "covariates": list(data.names),
        "choice_set": {"median": float(np.median(sizes)),
                       "mean": float(sizes.mean()),
                       "max": int(sizes.max()), "min": int(sizes.min())},
        "size_mix": mix_from_sizes(sizes),
        "methods": {
            m: {"raw_pooled": {k: float(np.mean(v))
                               for k, v in pooled[m].items()},
                "raw_pooled_sd": {k: float(np.std(v, ddof=1))
                                  for k, v in pooled[m].items()},
                # Kept per repeat so two arms fitted on the SAME decisions
                # and the SAME seeds can be differenced pairwise. Across
                # arms with different decisions they must not be.
                "per_repeat": {k: [float(x) for x in v]
                               for k, v in pooled[m].items()},
                "strata": finalise(strata[m], counts_from_sizes(sizes))}
            for m in methods},
        "empirical_uniform_null": {
            "top1": float(null[0]), "top5": float(null[1]),
            "top10": float(null[2]), "brier": float(null[3]),
            "note": "from choice.evaluate, where argsort breaks the "
                    "constant-score ties by row order, so it is a property "
                    "of the row order as much as of chance. Lift is taken "
                    "against the analytic min(k,J)/J held in `strata`."},
        **_coefficients(thetas, data.names),
    }
