"""The atheoretical benchmark MODEL_SPEC.md section 9.4 specified.

Specified 2026-09-13, never built until now.

    python -m siting_atlas.models.gbm_benchmark

What section 9.4 asks for, verbatim: "A gradient-boosted ranker is fitted on
the same splits, scored on the same rows, and reported in the same table. No
causal claim attaches to it. ... The GBM is scored on Brier and calibration
exactly like the structural model, not on AUC."

The question it settles
-----------------------
The conditional logit takes 19 of 38 held-out decisions into its top ten.
Ranking ZIPs by the raw warehousing-establishment count, with nothing fitted
at all, takes 20 of 38. The model loses to counting. Two explanations:

    DATA CEILING    the four free covariates do not carry the signal, and
                    no learner can do better
    MODEL CEILING   V = ln(beta'a) is too rigid and a flexible learner
                    finds structure it cannot express

A tree ensemble can express interactions, thresholds and non-monotonicity
the logit's single linear index cannot. If it also loses, the ceiling is
the data.

Four choices section 9.4 leaves open, and what was chosen
---------------------------------------------------------
1. LIBRARY AND OBJECTIVE. LightGBM's ``LGBMRanker`` with ``lambdarank``,
   groups = decisions, relevance 1 for the chosen ZCTA and 0 otherwise. It
   is the only gradient-boosted *ranker* in the venv and lambdarank
   optimises within-group order, which is the estimand.

2. FEATURES. The same four attraction columns the logit gets and nothing
   else, so the comparison isolates functional form rather than data. Two
   feature sets are run because the choice is not innocent: a tree scores
   each alternative from its own raw levels, whereas the logit's
   probability is a SHARE of the metro total. Withholding the shares would
   handicap the GBM and manufacture a data-ceiling verdict. The shares are
   a deterministic transform of the same columns plus the group structure
   the logit already uses, so supplying them is not extra information.

3. HYPERPARAMETERS. Not tuned, and not pre-registered either, because the
   grid had been run once by the time a primary would have been declared.
   Instead the whole grid is reported with its intervals and the verdict is
   taken on the RANGE. A conclusion that survives the worst and the best
   configuration does not depend on a choice made after looking.

4. PROBABILITIES FOR THE BRIER SCORE. A ranker emits scores on an arbitrary
   scale, so a Brier score computed from them means nothing. The scores are
   mapped to within-metro probabilities by a one-parameter softmax whose
   temperature is fitted ON THE TRAINING DECISIONS ONLY, by maximising the
   same conditional-logit likelihood the structural model maximises. The
   map is strictly increasing, so every top-k count is unchanged by it.

Why no single accuracy number is reported
-----------------------------------------
38 test decisions. One split's top-10 count carries a binomial standard
error near 3 decisions before any variation from WHICH decisions landed in
the fold. Everything is therefore measured over ``N_REPEATS`` 60/40
re-splits of the same 94 decisions, with every method re-fitted inside
every repeat so the comparison is PAIRED. Repeat 0 is bit-identical to
``choice_runner``'s split, so the published headline reproduces. The
interval is a spread over re-splits of ONE sample of 94 decisions, not a
confidence interval for the population of Amazon siting decisions - the
precondition Train states on p.202 and ``choice_inference.py`` quotes.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure
from ..common.trace import artefact, metric, step, traced_layer
from ..warehouse.national import load_national
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, ChoiceData, build, fit
from .choice_runner import SEED, TEST_FRACTION
from .gbm_report import HEADLINE_SPLIT_WARNING, caveats, summarise, table

#: Re-splits. 50 keeps the whole run under two minutes and gives the mean
#: a Monte Carlo error well under one decision.
N_REPEATS = 50

#: The covariate the raw-count benchmark ranks by. This is the column that
#: beat the fitted model in `choice_runner._benchmark`.
COUNT_COLUMN = "warehousing_establishments"

#: Reported in full, never collapsed to a winner. See choice 3 above.
#: Sized for 56 training decisions: deep trees have nothing to split on.
_STUMP = {"num_leaves": 2, "max_depth": 1,
          "n_estimators": 200, "learning_rate": 0.10}
_SMALL = {"num_leaves": 4, "max_depth": 2,
          "n_estimators": 100, "learning_rate": 0.05}
_DEEP = {"num_leaves": 8, "max_depth": 3,
         "n_estimators": 300, "learning_rate": 0.05}
GRID: tuple[tuple[str, bool, dict], ...] = (
    ("stump/200  shares", True, _STUMP),
    ("small/100  shares", True, _SMALL),
    ("deep/300   shares", True, _DEEP),
    ("stump/200  levels", False, _STUMP),
    ("small/100  levels", False, _SMALL),
    ("deep/300   levels", False, _DEEP),
)


def _features(d: ChoiceData, shares: bool) -> np.ndarray:
    """Raw levels, optionally with each column's share of its metro."""
    if not shares:
        return d.a
    totals = np.stack([np.bincount(d.group, weights=d.a[:, k])[d.group]
                       for k in range(d.a.shape[1])], axis=1)
    safe = np.where(totals > 0, totals, 1.0)
    return np.hstack([d.a, np.where(totals > 0, d.a / safe, 0.0)])


def _top_k_hits(score: np.ndarray, d: ChoiceData, k: int) -> int:
    """Copied from `choice.evaluate` so tie-breaking matches exactly."""
    n = 0
    for g in range(d.n_decisions):
        rows = np.flatnonzero(d.group == g)
        order = rows[np.argsort(-score[rows])]
        n += int(d.chosen[g] in order[:k])
    return n


def _softmax(score: np.ndarray, d: ChoiceData, t: float) -> np.ndarray:
    """Within-metro probabilities at temperature t >= 0.

    Strictly increasing in score, so it cannot change any top-k count.
    """
    gmax = np.full(d.n_decisions, -np.inf)
    np.maximum.at(gmax, d.group, score)
    e = np.exp(t * (score - gmax[d.group]))
    return e / np.bincount(d.group, weights=e)[d.group]


def _temperature(score: np.ndarray, d: ChoiceData) -> float:
    """Fit t on TRAINING decisions by the conditional-logit likelihood."""
    def nll(t: float) -> float:
        p = _softmax(score, d, max(t, 0.0))
        return -float(np.log(np.maximum(p[d.chosen], 1e-300)).sum())
    r = minimize_scalar(nll, bounds=(0.0, 200.0), method="bounded")
    return float(max(r.x, 0.0))


def _metrics(p: np.ndarray, d: ChoiceData) -> dict:
    """The fields `choice.evaluate` reports, computed the same way."""
    y = np.zeros(len(p))
    y[d.chosen] = 1.0
    uniform = 1.0 / np.bincount(d.group)[d.group]
    return {
        "top1": _top_k_hits(p, d, 1),
        "top5": _top_k_hits(p, d, 5),
        "top10": _top_k_hits(p, d, 10),
        "brier": float(np.mean((p - y) ** 2)),
        "brier_uniform_null": float(np.mean((uniform - y) ** 2)),
        "mean_prob_of_chosen": float(p[d.chosen].mean()),
    }


def _fit_gbm(train: ChoiceData, test: ChoiceData, shares: bool,
             params: dict, seed: int) -> tuple[dict, object]:
    import lightgbm as lgb
    x_tr, x_te = _features(train, shares), _features(test, shares)
    y_tr = np.zeros(len(x_tr), dtype=int)
    y_tr[train.chosen] = 1
    # deterministic=True / force_row_wise=True are NOT set, deliberately.
    # Both were tried on 2026-09-15 against the single-split instability
    # described in gbm_report.HEADLINE_SPLIT_WARNING and returned
    # bit-identical counts to this call in all eight comparisons. At
    # n_jobs=1 the fit is already reproducible on identical input; what
    # moves is the histogram binning under a 1e-12 change in the DATA, and
    # a determinism flag cannot touch that. Setting them would cost a
    # re-emit of published numbers and buy a false sense of a fix.
    model = lgb.LGBMRanker(objective="lambdarank", label_gain=[0, 1],
                           random_state=seed, n_jobs=1, verbose=-1, **params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(x_tr, y_tr, group=np.bincount(train.group))
        t = _temperature(model.predict(x_tr), train)
        metrics = _metrics(_softmax(model.predict(x_te), test, t), test)
    return metrics, model


def _gain_share(model, names: tuple[str, ...], shares: bool) -> dict:
    """Where the ensemble's total split gain went. Answers 'what did the
    flexible learner find that the linear index could not express?'"""
    labels = list(names) + ([f"{c} (share of metro)" for c in names]
                            if shares else [])
    gain = np.asarray(model.booster_.feature_importance("gain"), float)
    total = gain.sum()
    return {n: float(g / total) for n, g in zip(labels, gain, strict=True)
            } if total > 0 else {}


def _count_only(test: ChoiceData) -> dict:
    """Rank by one raw column, share-normalised.

    Identical to `choice_runner._benchmark`, reimplemented rather than
    imported because that helper is private and takes the full data object.
    """
    v = test.a[:, test.names.index(COUNT_COLUMN)]
    totals = np.bincount(test.group, weights=v)[test.group]
    return _metrics(np.where(totals > 0, v / np.where(totals > 0, totals, 1.0),
                             0.0), test)


def _logit(train: ChoiceData, test: ChoiceData) -> dict:
    from .choice import predict
    fitted = fit(train)
    return _metrics(predict(np.asarray(fitted["theta"], float), test), test)


def _repeat(data: ChoiceData, seed: int) -> dict:
    """One 60/40 re-split, all methods re-fitted on it. Seed SEED reproduces
    choice_runner exactly: same rng, same permutation, same cut."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(data.n_decisions)
    cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
    train = data.subset(np.sort(order[:cut]))
    test = data.subset(np.sort(order[cut:]))
    out = {"n_test": test.n_decisions,
           "conditional_logit": _logit(train, test),
           "raw_count": _count_only(test)}
    for label, shares, params in GRID:
        out[f"gbm {label}"], _ = _fit_gbm(train, test, shares, params, seed)
    return out


def run() -> dict:
    with traced_layer("L5", "GBM benchmark"):
        with step("gbm:load"):
            facilities = load_national()
            cols = ["zcta", "cbsa_code", *ATTRACTIONS]
            panel = pd.read_parquet(paths.PANEL, columns=cols)
            cbp_path = paths.INTERIM / "cbp_detail.parquet"
            if not cbp_path.exists():
                raise FileNotFoundError(
                    f"{paths.rel(cbp_path)} is missing. Without it the choice "
                    "model is fitted on three covariates and this benchmark "
                    "would not be comparable. Run "
                    "python -m siting_atlas.ingest.cbp_detail")
            data = build(facilities, panel, pd.read_parquet(cbp_path),
                         CBP_ATTRACTIONS)

        with step("gbm:repeats"):
            repeats = [_repeat(data, SEED + r) for r in range(N_REPEATS)]

    methods = ["conditional_logit", "raw_count"] + [
        f"gbm {lab}" for lab, _, _ in GRID]
    gbm = [m for m in methods if m.startswith("gbm")]
    def mean10(m):
        return float(np.mean([r[m]["top10"] for r in repeats]))
    best = max(gbm, key=mean10)
    metric("gbm_top10_mean", mean10(best))

    # Refit the best configuration on repeat 0 purely to read its split
    # gains. Costs one fit and answers the question the top-k table cannot.
    label, shares, params = next(g for g in GRID if f"gbm {g[0]}" == best)
    rng = np.random.default_rng(SEED)
    order = rng.permutation(data.n_decisions)
    cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
    _, model = _fit_gbm(data.subset(np.sort(order[:cut])),
                        data.subset(np.sort(order[cut:])),
                        shares, params, SEED)

    report = {
        "frame": "national",
        "n_decisions_total": data.n_decisions,
        "n_test_decisions": repeats[0]["n_test"],
        "n_repeats": N_REPEATS,
        "seed": SEED,
        "attractions": list(data.names),
        "spec": "docs/MODEL_SPEC.md section 9.4",
        "headline_split": {m: repeats[0][m] for m in methods},
        "headline_split_warning": HEADLINE_SPLIT_WARNING,
        "across_repeats": {m: summarise(repeats, m) for m in methods},
        "best_gbm_by_cv_top10": best,
        "gain_importance": _gain_share(model, data.names, shares),
        "caveats": caveats(data.n_decisions,
                           int(np.bincount(data.group).min())),
    }
    out = paths.METRICS / "gbm_benchmark.json"
    # `main` already starts a run; this is what puts the id INSIDE the file.
    write_json(out, report)
    artefact(out, repeats=N_REPEATS)
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    table(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
