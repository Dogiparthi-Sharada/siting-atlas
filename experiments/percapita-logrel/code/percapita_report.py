"""The reproduction check: does this harness rebuild the published run?

Nothing measured by `percapita_search` is interpretable until its baseline
arm reproduces the baseline arm of `covariate_search.json`'s core stage.
The frame, the seeds, the split, the optimiser and the scoring are all the
same code; the only difference is eight appended ratio columns that the
baseline arm does not select. If the number moves at all, the two
harnesses have diverged and the per-capita arms are being compared
against something other than the published baseline.

The targets are READ FROM THE ARTEFACT, not retyped, so they cannot drift
out of agreement with the run they claim to reproduce. The literals below
are a fallback for a checkout without the artefact, and they are the
figures published in `COVARIATES_TRIED.md` section 0.
"""

from __future__ import annotations

import json

from ..common import paths

#: Large-metro (>100 alternatives) top-10 lift, `covariate_search.json`
#: core stage, 50 re-splits.
PUBLISHED = {"baseline": 6.388945150223279,
             "no_warehousing": 2.735190253657848}

#: Tolerance on the check. Same frame, same seeds, same optimiser, so the
#: only admissible difference is floating-point summation order; anything
#: larger means the harnesses have diverged and must be reconciled before
#: the per-capita arms mean anything.
TOLERANCE = 1e-9

__all__ = ["PUBLISHED", "TOLERANCE", "check", "published"]


def published() -> dict:
    """The core-stage large-metro top-10 lifts this run must reproduce."""
    src = paths.METRICS / "covariate_search.json"
    if not src.exists():
        return dict(PUBLISHED)
    core = json.loads(src.read_text()).get("core", {}).get("arms", {})
    out = {}
    for name, fallback in PUBLISHED.items():
        cell = core.get(name, {}).get("top10", {}).get("large_gt100", {})
        out[name] = cell.get("lift", fallback)
    return out


def check(summary: dict) -> dict:
    """Compare the reproduced baseline arms with the published ones."""
    want, rows = published(), {}
    for name, target in want.items():
        if name not in summary:
            rows[name] = {"published": target, "reproduced": None,
                          "difference": None, "matches": None,
                          "note": "arm unfinished at this repeat count"}
            continue
        got = summary[name]["top10"]["large_gt100"]["lift"]
        rows[name] = {"published": target, "reproduced": got,
                      "difference": got - target,
                      "matches": bool(abs(got - target) <= TOLERANCE)}
    print("\n  reproduction check: large-metro top-10 lift vs "
          "covariate_search.json core stage")
    for name, r in rows.items():
        if r["reproduced"] is None:
            print(f"  {name:34}{r['published']:12.6f}{'unfinished':>12}")
            continue
        flag = "OK" if r["matches"] else "DIVERGED"
        print(f"  {name:34}{r['published']:12.6f}{r['reproduced']:12.6f}"
              f"{r['difference']:+14.2e}  {flag}")
    return rows
