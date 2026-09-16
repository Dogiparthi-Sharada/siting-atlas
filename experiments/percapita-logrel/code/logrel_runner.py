"""Serial, resumable re-split loop for the log-relative arms.

`covariate_harness.run_experiment` farms its fifty repeats out to a process
pool. This module runs the SAME per-repeat function, `covariate_harness`'s
`_repeat`, one repeat at a time and writes the raw result to disk after each
one. Two reasons, both operational rather than scientific:

  * the workstation this runs on is a six-core box in interactive use and was
    at load average ~24 when this experiment started, so a pool of five would
    be taking cores from the people using them;
  * a log-relative arm makes the likelihood much harder to optimise (see
    `logrel_frame`: the positivity constraint turns a flat direction into a
    cliff), and a fit that took one second in the original search takes tens.
    A run measured in hours that keeps its results only in memory is the
    failure `covariate_harness`'s own docstring documents.

Reusing `_repeat` rather than reimplementing it is deliberate. The fitted
numbers have to be comparable with `covariate_search.json` down to the
baseline arm's fifteenth decimal place, and the only way to guarantee that
is to run the identical code on the identical frame with the identical
seeds.
"""

from __future__ import annotations

import json
import time

import numpy as np

from ..common import paths
from .choice import ChoiceData
from .choice_runner import SEED
from .covariate_harness import REPEATS, _init, _repeat
from .covariate_report import print_report, summarise_arm
from .panel_strata import BUCKETS, MIN_INFORMATIVE, bucket_of

ARTEFACT = "logrel_search.json"

#: Raw per-repeat output, kept beside the artefact so a killed run resumes
#: instead of restarting. Not the deliverable; the deliverable is ARTEFACT.
CHECKPOINT = "logrel_repeats.json"

__all__ = ["ARTEFACT", "CHECKPOINT", "distinct_decisions", "load",
           "run_serial", "save"]


def _dest(name: str):
    """Results go to outputs/metrics; resume state goes to outputs/scratch.

    Only CHECKPOINT is resume state. Routing on the name rather than on a
    flag keeps every caller unchanged and makes it impossible to write the
    deliverable into scratch by passing the wrong argument.
    """
    if name == CHECKPOINT:
        return paths.checkpoint(name)
    return paths.METRICS / name


def load(name: str = ARTEFACT) -> dict:
    dest = _dest(name)
    return json.loads(dest.read_text()) if dest.exists() else {}


def save(report: dict, name: str = ARTEFACT) -> None:
    dest = _dest(name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2), encoding="utf-8")


def distinct_decisions(data: ChoiceData) -> dict:
    """DISTINCT decisions per stratum, not decision-evaluations.

    `covariate_report` counts evaluations — fifty re-splits of one decision
    read as fifty. `panel_strata.MIN_INFORMATIVE` is a threshold on distinct
    decisions, so the honest denominator is counted here and printed beside
    every table.
    """
    bucket = bucket_of(np.bincount(data.group))
    out = {name: int((bucket == i).sum())
           for i, (name, _, _) in enumerate(BUCKETS)}
    return out | {"total": int(len(bucket)),
                  "thin_below": MIN_INFORMATIVE,
                  "note": "distinct decisions in the FULL frame. The tables "
                          "report decision-evaluations, which are these "
                          "times the ~40% test share times the repeat count."}


def run_serial(title: str, data: ChoiceData, spec: dict, ref: str,
               repeats: int = REPEATS, checkpoint: str = CHECKPOINT,
               resume: bool = True) -> dict:
    """`repeats` paired re-splits, one process, checkpointed after each."""
    done = load(checkpoint) if resume else {}
    if done.get("arms_signature") != sorted(spec["fixed"]):
        done = {"arms_signature": sorted(spec["fixed"]), "repeats": []}
    out: list[dict] = done["repeats"]
    _init(data)
    start, first = time.time(), len(out)
    for r in range(first, repeats):
        out.append(_repeat((SEED + r, spec)))
        done["repeats"] = out
        save(done, checkpoint)
        elapsed = time.time() - start
        print(f"  repeat {r + 1}/{repeats} done  "
              f"({elapsed / 60 / (r + 1 - first):.1f} min/repeat, "
              f"{elapsed / 60:.0f} min elapsed)", flush=True)
    names = list(spec["fixed"])
    arms = {n: summarise_arm(out[:repeats], n, ref) for n in names}
    print_report(title, arms, ref)
    return {"reference_arm": ref, "repeats": repeats,
            "n_test_decisions": out[0]["n_test"],
            "distinct_decisions": distinct_decisions(data), "arms": arms}
