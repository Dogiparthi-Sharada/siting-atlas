"""The GBM benchmark, re-run on the columns `covariate_search` selected.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.models.covariate_gbm

Why this exists
---------------
`NOTES_GBM_BENCHMARK.md` ran a gradient-boosted ranker on FOUR columns and
concluded a data ceiling: a linear index, a zero-parameter count and a
200-tree ensemble all landed within 1.7 top-10 hits of each other, which
is less than any one of them moves between splits. Its own section 8.2
then warned that "the data ceiling is a ceiling on FOUR COLUMNS, not on
the question."

`covariate_search` answers the logit half of that. This module answers the
other half. If the extra columns carry signal that ``ln(beta'a)`` cannot
express — a threshold, a non-monotonicity, a sign the positivity
constraint forbids — the tree will find it and the logit will not, and the
gap between the two on the SAME columns measures it. If the tree does not
find it either, the column is empty rather than mis-specified, and that is
the stronger reading of a null result.

Two things this borrows rather than rebuilds
--------------------------------------------
`_fit_gbm` and `GRID` are imported from `gbm_benchmark` even though they
are private. That file reimplemented a private helper rather than import
it and said so; here the trade goes the other way, because the point of
this module is that the LEARNER is identical and only the columns change.
A copy would drift the moment either file was touched, and a drifted copy
would be a comparison of two learners wearing one name.

The evaluation is `covariate_report`'s, stratified by choice-set size, so
the logit rows here are directly comparable to `covariate_search.json`.
"""

from __future__ import annotations

import json

import numpy as np

from ..common import paths
from ..common.logging_setup import configure, get_logger
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, ChoiceData
from .choice_runner import SEED, TEST_FRACTION
from .covariate_arms import fit_and_score, split_decisions
from .covariate_frame import (
    RECIPROCALS,
    STATIC_CANDIDATES,
    build_frame,
    columns_only,
)
from .covariate_report import print_report, summarise_arm
from .covariate_search import BASE, REPEATS, _load
from .gbm_benchmark import GRID, _features, _fit_gbm, _softmax, _temperature
from .panel_strata import TOP_KS, bucket_of, chance_rates, hit_flags

_log = get_logger("models.covariate_gbm")

ARTEFACT = "covariate_gbm.json"

#: Only the shallow configurations. `NOTES_GBM_BENCHMARK.md` section 5
#: measured the two deep ones LOSING 2.2 decisions of 38 to a
#: zero-parameter count at 56 training groups; at 287 groups they are
#: still the wrong end of the grid and running them would spend most of
#: the compute on a configuration already known to be beaten.
CONFIGS = tuple(g for g in GRID if not g[0].startswith("deep"))


def _record(score: np.ndarray, test: ChoiceData, cols: tuple[str, ...],
            beta: dict | None = None) -> dict:
    y = np.zeros(len(score))
    y[test.chosen] = 1.0
    uniform = 1.0 / np.bincount(test.group)[test.group]
    return {"cols": list(cols),
            "hits": {str(k): hit_flags(score, test, k).tolist()
                     for k in TOP_KS},
            "brier": float(np.mean((score - y) ** 2)),
            "brier_null": float(np.mean((uniform - y) ** 2)),
            "beta": beta}


def _repeat(data: ChoiceData, seed: int, sets: dict) -> dict:
    tr_idx, te_idx = split_decisions(data.n_decisions, seed, TEST_FRACTION)
    train, test = data.subset(tr_idx), data.subset(te_idx)
    out = {"bucket": bucket_of(np.bincount(test.group)).tolist(),
           "chance": {str(k): chance_rates(test, k).tolist()
                      for k in TOP_KS},
           "n_test": test.n_decisions, "arms": {}}
    for label, (cols, with_logit) in sets.items():
        if with_logit:
            score, fitted = fit_and_score(train, test, tuple(cols))
            out["arms"][f"logit {label}"] = _record(
                score, test, tuple(cols), fitted["beta"])
        tr_c, te_c = (columns_only(train, tuple(cols)),
                      columns_only(test, tuple(cols)))
        for name, shares, params in CONFIGS:
            _, model = _fit_gbm(tr_c, te_c, shares, params, seed)
            # `_fit_gbm` fits the softmax temperature internally and keeps
            # only the metrics, so it is refitted here to recover the
            # PROBABILITIES the Brier score needs. Same code, same
            # training decisions, and strictly increasing, so no top-k
            # count can change under it.
            temp = _temperature(model.predict(_features(tr_c, shares)), tr_c)
            score = _softmax(model.predict(_features(te_c, shares)),
                             te_c, temp)
            out["arms"][f"gbm {name.strip()} {label}"] = _record(
                score, test, tuple(cols))
    return out


def run(best: tuple[str, ...] | None = None) -> dict:
    facilities, panel, cbp = _load()
    data, coverage = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS,
                                 static=STATIC_CANDIDATES,
                                 reciprocals=RECIPROCALS)
    if best is None:
        best = _best_from_artefact(data.names)
    # (columns, fit the conditional logit too?). The all-columns LOGIT is
    # not run and the omission is a judgement, not a saving. That arm
    # contains three columns the model is not identified in -- they
    # correlate 0.88 to 1.000 with the numeraire within metro, see
    # NOTES_COVARIATE_SEARCH.md section 2.2 -- so its coefficients are
    # arbitrary along a ray and its fit is the optimiser wandering a flat
    # likelihood in eighteen dimensions. Measured: 213 seconds per fit
    # against 2.8 for the baseline. Reporting it would be reporting an
    # optimisation artefact. The GBM on all columns IS run, because a
    # tree is indifferent to collinearity and to the positivity
    # constraint, which is exactly the comparison this module is for.
    sets = {"baseline": (list(BASE), True), "best": (list(best), True),
            "all columns": (list(data.names), False)}
    repeats = []
    for r in range(REPEATS):
        repeats.append(_repeat(data, SEED + r, sets))
        if (r + 1) % 5 == 0:
            _log.info("gbm benchmark: %d/%d re-splits", r + 1, REPEATS)
    names = list(repeats[0]["arms"])
    arms = {n: summarise_arm(repeats, n, "logit baseline") for n in names}
    print_report("GBM on the searched column sets", arms, "logit baseline")
    report = {"seed": SEED, "repeats": REPEATS, "coverage": coverage,
              "column_sets": {k: list(v[0]) for k, v in sets.items()},
              "logit_omitted_for": [k for k, v in sets.items()
                                    if not v[1]],
              "logit_omission_reason":
                  "not identified: three of these columns "
                  "correlate 0.88-1.000 with the numeraire "
                  "within metro, so the fit is the optimiser "
                  "wandering a flat likelihood (213s/fit). "
                  "See NOTES_COVARIATE_SEARCH.md section 2.2.",
              "configurations": [c[0].strip() for c in CONFIGS],
              "arms": arms}
    dest = paths.METRICS / ARTEFACT
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n  -> {paths.rel(dest)}\n")
    return report


def _best_from_artefact(available: tuple[str, ...]) -> tuple[str, ...]:
    """The column set `covariate_search` selected, or the baseline.

    Read from the artefact rather than re-derived so the two files cannot
    disagree about what "best" meant.
    """
    src = paths.METRICS / "covariate_search.json"
    if not src.exists():
        raise SystemExit(
            f"\n  {paths.rel(src)} not found\n  run: PYTHONPATH=src "
            ".venv/bin/python -m siting_atlas.models.covariate_search\n")
    picked = json.loads(src.read_text())["naive_selection"]["columns"]
    keep = tuple(c for c in picked if c in available)
    return keep if keep else (*ATTRACTIONS, *CBP_ATTRACTIONS)


def main() -> int:
    paths.ensure_dirs()
    configure()
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
