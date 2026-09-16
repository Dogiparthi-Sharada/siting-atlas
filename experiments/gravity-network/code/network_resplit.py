"""The re-split quantities, kept apart from the inference on purpose.

This module holds everything `network_inference` reports that is a
PERCENTILE OVER RE-SPLITS rather than an interval: the published spread
the claim was made on, the three measures on the new arm, and the paired
difference against the arm's no-network sibling. They are separated from
the bootstrap and the sandwich so that nothing in the reading of the
artefact can confuse the two, and so that the warning below travels with
every one of them rather than being stated once in a docstring.

`NOTES_EXPANDED_REFIT.md` §8 item 1, `NOTES_GBM_BENCHMARK.md` §8 item 4
and `NOTES_PANEL_EXPERIMENTS.md` §9 item 1 all say the same thing about
these quantities. This is the fourth place it is said, and the first
place it is said beside the bootstrap that replaces them.
"""

from __future__ import annotations

import json

import numpy as np

from ..common import paths
from .panel_strata import counts_from_sizes, standardise

PANEL_ARTEFACT = paths.METRICS / "panel_experiments.json"

SPREAD_IS_NOT_A_STANDARD_ERROR = (
    "A 2.5-97.5 percentile over 50 re-splits is NOT a standard error and "
    "is not an estimate of one. The re-splits draw from the same fixed "
    "set of decisions, so their spread understates sampling variability "
    "by an amount nothing here measures; and each re-split fit uses 60% "
    "of the decisions, so it is not even an interval on the same "
    "estimator as the full-sample point estimate beside it. It is "
    "reported only as the quantity the published claim was made on.")

__all__ = ["PANEL_ARTEFACT", "SPREAD_IS_NOT_A_STANDARD_ERROR",
           "panel_blob", "paired_against", "published_spread", "strata"]


def panel_blob() -> dict:
    """`panel_experiments.json`, or an empty dict if it has not been run."""
    if not PANEL_ARTEFACT.exists():
        return {}
    return json.loads(PANEL_ARTEFACT.read_text(encoding="utf-8"))


def published_spread(arm: str, blob: dict | None = None) -> dict:
    """The re-split percentiles the published claim was made on."""
    blob = panel_blob() if blob is None else blob
    if not blob:
        return {"available": False,
                "reason": f"{paths.rel(PANEL_ARTEFACT)} not found; run "
                          "panel_experiments first"}
    a = blob.get("arms", {}).get(arm)
    if a is None:
        return {"available": False,
                "reason": f"no arm {arm!r} in the artefact (expected for an "
                          "arm this module adds)"}
    return {"available": True, "repeats": blob["repeats"],
            "n_fitted_decisions_per_repeat": int(a["n_decisions"]
                                                 - a["n_test"]),
            "beta_mean": a["beta_mean"], "beta_p025": a["beta_p025"],
            "beta_p975": a["beta_p975"],
            "warning": SPREAD_IS_NOT_A_STANDARD_ERROR}


def strata(d, arm: dict, mix: dict) -> dict:
    """The three measures, per stratum, with DISTINCT-decision n.

    The standardised figure is emitted because `panel_experiments` emits
    it, and it must not be ranked on: `NOTES_PANEL_EXPERIMENTS.md` §3.2
    shows direct standardisation equalising the SHARE of decisions in a
    bucket without equalising the distribution of choice-set size inside
    it, which is Simpson's paradox one level down. `distinct_decisions`
    is the count that decides whether a stratum may be compared at all.
    """
    sizes = np.bincount(d.group)
    out = {"distinct_decisions": counts_from_sizes(sizes),
           "size_mix": arm["size_mix"], "methods": {}}
    for name, block in arm["methods"].items():
        out["methods"][name] = {
            "strata": block["strata"]["top10"],
            "standardised_top10": standardise(block["strata"], mix)["top10"],
            "raw_pooled": block["raw_pooled"],
        }
    return out


def paired_against(arm: dict, baseline: dict) -> dict:
    """Paired difference against the same arm without the network columns.

    Valid only because the two hold the identical decisions and take the
    identical splits from the identical seeds. NOT a sign test: the 50
    re-splits resample the same decisions and are not independent.
    """
    out: dict = {}
    for method, block in arm["methods"].items():
        base = baseline["methods"].get(method)
        if base is None:
            continue
        rows = {}
        for key, values in block["per_repeat"].items():
            other = base["per_repeat"][key]
            if len(other) != len(values):
                # A short smoke run against a 50-repeat artefact.
                return {"comparable": False,
                        "reason": f"{len(values)} repeats here against "
                                  f"{len(other)} published; not paired"}
            diff = np.asarray(values) - np.asarray(other)
            better = diff < 0 if key == "brier" else diff > 0
            rows[key] = {"paired_mean_difference": float(diff.mean()),
                         "paired_sd": float(diff.std(ddof=1)),
                         "repeats_improved": int(better.sum()),
                         "repeats_worsened": int((diff != 0).sum()
                                                 - better.sum())}
        out[method] = rows
    return out
