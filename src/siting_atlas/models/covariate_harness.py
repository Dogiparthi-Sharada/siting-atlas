"""Running an arm set over paired re-splits, and persisting it a stage
at a time.

An ARM SET is a dict of named column subsets plus named forward searches.
`run_experiment` takes one `ChoiceData`, re-splits it `REPEATS` times, and
re-fits every arm inside every split so the comparison between arms is
PAIRED: a fold that happens to contain easy decisions lifts every arm at
once and the difference removes it.

Why the repeats are farmed out to processes
-------------------------------------------
A single conditional-logit fit is one to ten seconds depending on how flat
the likelihood is, and the experiment runs thousands. The repeats are
independent by construction — each seeds its own `default_rng` — so
process parallelism changes the wall clock and nothing else. The data
object is passed once through the pool initialiser rather than once per
job, because it is tens of megabytes and there are fifty jobs.

Why the artefact is written after EVERY stage
---------------------------------------------
This is not defensive programming for its own sake; it is a fix for a
measured failure. On 2026-09-14 a monolithic version of this experiment
wrote its artefact once, at the very end, after four stages. The machine
it shares was at load average 44 on six cores, the run had to be stopped,
and forty-five minutes of completed, correct, finished work was discarded
because it existed only in memory. `save` and the stage ledger exist so
that cannot recur: a finished stage is on disk before the next one starts,
and the ledger records whether a stage in the artefact was computed by
this invocation or carried forward from an earlier one.

A carried-forward stage is legitimate ONLY while the scientific code is
unchanged. Recording it is what makes that checkable, which is the whole
reason it is recorded rather than silently reused.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..common import paths
from ..common.log_json import write_json
from .choice import ChoiceData
from .choice_runner import SEED, TEST_FRACTION
from .covariate_arms import fit_and_score, forward_select, split_decisions
from .covariate_report import print_report, summarise_arm
from .panel_strata import TOP_KS, bucket_of, chance_rates, hit_flags

#: 50, for the reason `NOTES_GBM_BENCHMARK.md` section 4 gives: one split
#: moves a top-10 count by three decisions, which is larger than any
#: effect this search is looking for.
REPEATS = 50

ARTEFACT = "covariate_search.json"

#: Stages, in dependency order. `permits` needs `naive`, which needs the
#: core frame; nothing else depends on anything.
STAGES = ("audit", "anchor", "core", "naive", "permits")

#: The artefact key each stage fills, so the ledger can tell "this stage
#: ran" from "this key happens to exist".
STAGE_KEY = {"audit": "column_audit", "anchor": "anchor", "core": "core",
             "naive": "naive_selection", "permits": "permits"}

LEDGER_NOTE = (
    "carried_forward = reused from an earlier invocation of this module at "
    "the same seed, same frame and same arm list, not recomputed. Re-run "
    "--stages <name> if the scientific code changes. See "
    "NOTES_COVARIATE_SEARCH.md section 11.")

__all__ = ["ARTEFACT", "LEDGER_NOTE", "REPEATS", "STAGES", "ledger", "load",
           "run_experiment", "save"]

_DATA: ChoiceData | None = None


def _init(data: ChoiceData) -> None:
    global _DATA
    _DATA = data


def _arm(train, test, cols, trace=None) -> dict:
    """One column subset, fitted on `train` and scored on `test`."""
    score, fitted = fit_and_score(train, test, cols)
    y = np.zeros(len(score))
    y[test.chosen] = 1.0
    uniform = 1.0 / np.bincount(test.group)[test.group]
    return {
        "cols": list(cols),
        "hits": {str(k): hit_flags(score, test, k).tolist() for k in TOP_KS},
        "brier": float(np.mean((score - y) ** 2)),
        "brier_null": float(np.mean((uniform - y) ** 2)),
        "mean_prob_of_chosen": float(score[test.chosen].mean()),
        # A searched arm has no fixed column list, so a beta interval over
        # re-splits would average coefficients from different models.
        "beta": fitted["beta"] if trace is None else None,
        "trace": trace,
    }


def _repeat(job: tuple[int, dict]) -> dict:
    """One 60/40 re-split with every arm re-fitted on it."""
    seed, spec = job
    data = _DATA
    tr_idx, te_idx = split_decisions(data.n_decisions, seed, TEST_FRACTION)
    train, test = data.subset(tr_idx), data.subset(te_idx)
    out = {
        "seed": seed,
        "bucket": bucket_of(np.bincount(test.group)).tolist(),
        "chance": {str(k): chance_rates(test, k).tolist() for k in TOP_KS},
        "n_test": test.n_decisions, "arms": {},
    }
    for name, cols in spec["fixed"].items():
        out["arms"][name] = _arm(train, test, tuple(cols))
    for name, search in spec.get("search", {}).items():
        cols, trace = forward_select(train, tuple(search["base"]),
                                     tuple(search["candidates"]), seed)
        out["arms"][name] = _arm(train, test, cols, trace=trace)
    return out


def run_experiment(title: str, data: ChoiceData, coverage: dict, spec: dict,
                   ref: str, workers: int) -> dict:
    """`REPEATS` paired re-splits of one frame, every arm on every split."""
    jobs = [(SEED + r, spec) for r in range(REPEATS)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                             initargs=(data,)) as pool:
        repeats = list(pool.map(_repeat, jobs))
    names = list(spec["fixed"]) + list(spec.get("search", {}))
    arms = {n: summarise_arm(repeats, n, ref) for n in names}
    print_report(title, arms, ref)
    return {"coverage": coverage, "reference_arm": ref,
            "n_test_decisions": repeats[0]["n_test"], "arms": arms,
            "example_selection_trace": {
                n: repeats[0]["arms"][n]["trace"]
                for n in spec.get("search", {})}}


def ledger(report: dict, ran: tuple[str, ...]) -> dict:
    """Which stages are in this artefact, and how they got there.

    `ran_this_invocation` is claimed only for the stages THIS call ran.
    An earlier ledger's claim is deliberately not carried over: a stage
    that ran an hour ago and was reused now is `carried_forward`, and
    saying otherwise would let an artefact assert it was regenerated when
    it was not — which is the exact thing the ledger exists to prevent.
    """
    return {s: ("ran_this_invocation" if s in ran
                else "carried_forward" if STAGE_KEY[s] in report
                else "absent")
            for s in STAGES}


def load() -> dict:
    dest = paths.METRICS / ARTEFACT
    return json.loads(dest.read_text()) if dest.exists() else {}


def save(report: dict) -> None:
    """Persist after every stage. See the module docstring for why."""
    dest = paths.METRICS / ARTEFACT
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_json(dest, report)
    print(f"\n  -> {paths.rel(dest)}\n")
