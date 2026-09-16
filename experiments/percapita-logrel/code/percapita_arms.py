"""Serial, resumable re-splits for the per-capita experiment.

This is `covariate_harness.run_experiment` with two deliberate changes and
no scientific ones. The arms, the split, the fit, the scoring and the
summary all come from the covariate-search modules unchanged, so a
baseline arm run through here must reproduce the baseline arm in
`covariate_search.json` to the last digit. That equality is checked by
`percapita_search` before anything else is believed.

Change 1: ONE PROCESS, NO POOL. The workstation this runs on is shared and
was at load average 25 when the experiment was written. A pool of five
would finish in forty minutes and make the machine unusable for everyone
else; one niced process takes about three and a half hours and is
invisible. Parallelism here buys wall clock and nothing else, because the
repeats are independent by construction.

Change 2: ARM-MAJOR ORDER, AND A CHECKPOINT AFTER EVERY FIT. The pool
version runs repeat-major — every arm on repeat 1, then every arm on
repeat 2 — which is the right order when the run is certain to finish and
the worst possible order when it is not, because an interruption leaves
every arm equally unfinished and none of them readable. This one runs the
arms in a declared PRIORITY ORDER, each across all fifty re-splits, and
writes after every single fit. An interruption then leaves a prefix of
arms COMPLETE at the full repeat count and the rest absent, which is a
publishable result rather than a ruined one.

Nothing about the estimates changes. A re-split is a deterministic
function of its seed (`covariate_arms.split_decisions`), so arm A on seed
s and arm B on seed s see the same partition whichever order they were
computed in, and the pairing survives.

This was not caution. On the day it was written the workstation was at
load average 26 with another agent holding five cores, and this process,
at `nice 19` in its own session, measured 1.1% of one core against 96.5%
for a sibling at identical nice. `run_serial` therefore has to assume it
will be stopped before it finishes.

Distinct decisions, not decision-evaluations
--------------------------------------------
`covariate_report.aggregate` marks a stratum informative on its
decision-evaluation count, which counts the same decision once per
re-split. `panel_strata.MIN_INFORMATIVE` says in its own comment that the
count that should be tested is DISTINCT DECISIONS: fifty re-splits of
seven decisions produce 136 evaluations and no more information than seven
decisions hold. `attach_distinct` recomputes the flag on the distinct
count, which is a property of the frame and identical for every arm.
"""

from __future__ import annotations

import json

import numpy as np

from .choice_runner import SEED, TEST_FRACTION
from .covariate_arms import fit_and_score, split_decisions
from .covariate_report import summarise_arm
from .panel_strata import (
    BUCKETS,
    MIN_INFORMATIVE,
    TOP_KS,
    bucket_of,
    chance_rates,
    counts_from_sizes,
    hit_flags,
)

__all__ = ["attach_distinct", "distinct_counts", "run_serial",
           "split_meta", "summarise"]


def distinct_counts(data) -> dict:
    """Distinct decisions per choice-set-size stratum, over the frame."""
    return counts_from_sizes(np.bincount(data.group))


def _arm(train, test, cols: tuple[str, ...]) -> dict:
    """One column subset, fitted on `train` and scored on `test`.

    Byte-identical in behaviour to `covariate_harness._arm`; it is
    reproduced rather than imported because that one is private to a file
    this experiment does not own.
    """
    score, fitted = fit_and_score(train, test, cols)
    y = np.zeros(len(score))
    y[test.chosen] = 1.0
    uniform = 1.0 / np.bincount(test.group)[test.group]
    return {"cols": list(cols),
            "hits": {str(k): hit_flags(score, test, k).tolist()
                     for k in TOP_KS},
            "brier": float(np.mean((score - y) ** 2)),
            "brier_null": float(np.mean((uniform - y) ** 2)),
            "mean_prob_of_chosen": float(score[test.chosen].mean()),
            "beta": fitted["beta"], "trace": None}


def split_meta(data, repeats: int) -> list[dict]:
    """Per-re-split bucket labels and chance rates. Cheap, arm-independent."""
    out = []
    for r in range(repeats):
        _, te = split_decisions(data.n_decisions, SEED + r, TEST_FRACTION)
        test = data.subset(te)
        out.append({"seed": SEED + r,
                    "bucket": bucket_of(np.bincount(test.group)).tolist(),
                    "chance": {str(k): chance_rates(test, k).tolist()
                               for k in TOP_KS},
                    "n_test": test.n_decisions, "arms": {}})
    return out


def _read(path) -> dict:
    """``{arm: {seed: result}}`` from the checkpoint, or empty."""
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("cells", {})


def run_serial(data, arms: dict, repeats: int, checkpoint, log=print,
               fit: bool = True) -> tuple[list[dict], list[str]]:
    """Every arm across every re-split, arm-major, saved after each fit.

    With ``fit=False`` nothing is estimated and the checkpoint is only
    read, which is how a long run can be summarised from another process
    while it is still going.

    Returns the repeat records and the list of arms that are COMPLETE at
    `repeats` re-splits. An arm that is missing or part-finished is left
    out of both, because a summary over thirty of fifty re-splits is not
    comparable with one over fifty and silently mixing them would be the
    kind of error this project keeps finding in its own past work.
    """
    meta = split_meta(data, repeats)
    cells = {k: v for k, v in _read(checkpoint).items() if k in arms}
    total = len(arms) * repeats
    fits = sum(len(v) for v in cells.values())
    for name, cols in arms.items():
        slot = cells.setdefault(name, {})
        for r in range(repeats if fit else 0):
            if str(SEED + r) in slot:
                continue
            tr, te = split_decisions(data.n_decisions, SEED + r,
                                     TEST_FRACTION)
            slot[str(SEED + r)] = _arm(data.subset(tr), data.subset(te),
                                       tuple(cols))
            fits += 1
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_text(json.dumps({"cells": cells}),
                                  encoding="utf-8")
            log(f"  fit {fits}/{total}  {name}  repeat {r + 1}/{repeats}")
    complete = [n for n in arms
                if len(cells.get(n, {})) >= repeats]
    for rec in meta:
        for name in complete:
            rec["arms"][name] = cells[name][str(rec["seed"])]
    return meta, complete


def attach_distinct(summary: dict, distinct: dict) -> dict:
    """Rewrite the thinness flag on DISTINCT decisions, and record them."""
    for k in TOP_KS:
        block = summary.get(f"top{k}")
        if block is None:
            continue
        for name, _, _ in BUCKETS:
            cell = block.get(name)
            if cell is None:
                continue
            cell["decisions"] = distinct.get(name, 0)
            cell["informative"] = bool(cell["decisions"] >= MIN_INFORMATIVE)
        if "pooled" in block:
            block["pooled"]["decisions"] = int(sum(distinct.values()))
            block["pooled"]["informative"] = True
            block["pooled"]["note"] = (
                "pooled across heterogeneous choice sets; a Simpson's-paradox "
                "trap. Read the strata.")
    return summary


def summarise(repeats: list[dict], arms: dict, ref: str,
              distinct: dict) -> dict:
    """Per-arm stratified summary, paired against `ref`, thinness fixed."""
    return {name: attach_distinct(summarise_arm(repeats, name, ref), distinct)
            for name in arms}
