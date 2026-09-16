"""Reading one gravity arm: boundary verdicts, paired lift, selection.

Split out of `gravity_network` so the runner is a runner. Everything here
is a pure function of a measured arm, which means every number in the
artefact can be recomputed from the artefact.
"""

from __future__ import annotations

import numpy as np

from .choice import fit
from .choice_runner import SEED, TEST_FRACTION
from .choice_sandwich import BOUNDARY_TOL
from .panel_strata import BUCKETS

#: Every gravity column carries this in its name; nothing else does.
GRAVITY_MARKER = "_gravity_"

#: Fixed before the numbers were seen, and stored in the artefact so a
#: reader can see it was not chosen to suit the winner.
SELECTION_RULE = (
    "Among the gravity arms whose BOTH columns are INTERIOR by the "
    "percentile rule, the highest top-10 lift in the LARGE stratum "
    "(>100 candidate ZCTAs) -- the stratum with the most decisions, the "
    "least structural cap on lift, and the only one where a siting "
    "decision is genuinely contested. If no gravity arm has both columns "
    "interior, that is itself the finding and the highest large-stratum "
    "lift is reported with the boundary flag attached.")

__all__ = ["GRAVITY_MARKER", "SELECTION_RULE", "boundary_census",
           "census_matches", "paired", "pick_best", "strata_vs", "verdicts"]


def verdicts(arm: dict) -> dict:
    """Interior or boundary, by the rule that produced the published claim.

    `panel_print.verdict` derives the published "interior" statements from
    the two percentiles: anything whose upper end is below `BOUNDARY_TOL`
    is at the boundary, and a lower end below it means a boundary solution
    sits inside the interval. Reproduced here so this file's verdicts and
    `NOTES_PANEL_EXPERIMENTS.md` §3.1's are the same rule on the same
    quantity. `boundary_census` is the stricter version.
    """
    out = {}
    for name, mean in arm["beta_mean"].items():
        lo, hi = arm["beta_p025"][name], arm["beta_p975"][name]
        if hi < BOUNDARY_TOL:
            state = "AT THE BOUNDARY"
        elif lo < BOUNDARY_TOL:
            state = "boundary inside the interval"
        else:
            state = "INTERIOR"
        out[name] = {"beta_mean": mean, "p025": lo, "p975": hi,
                     "state": state,
                     "excludes_one": bool(lo > 1.0 or hi < 1.0)}
    return out


def boundary_census(data, repeats: int) -> dict:
    """How many of the re-split fits land ON the boundary, per column.

    The published claim is "interior in all 50 re-splits"; a 2.5th
    percentile cannot say that, so this refits the same training halves
    the harness used and counts them. It reproduces
    `panel_harness.measure`'s split exactly -- same `SEED`, same
    `TEST_FRACTION`, same permutation, same cut -- and
    `census_matches` is the proof: if the percentiles disagree then this
    loop is fitting different training sets and its census means nothing.
    """
    draws = []
    for r in range(repeats):
        rng = np.random.default_rng(SEED + r)
        order = rng.permutation(data.n_decisions)
        cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
        train = data.subset(np.sort(order[:cut]))
        draws.append(np.exp(np.asarray(fit(train)["theta"], float)))
    arr = np.vstack(draws)
    return {name: {
        "resplits": int(repeats),
        "resplits_at_boundary": int((arr[:, i] <= BOUNDARY_TOL).sum()),
        "interior_in_all_resplits": bool((arr[:, i] > BOUNDARY_TOL).all()),
        "min_beta": float(arr[:, i].min()),
        "max_beta": float(arr[:, i].max()),
        "p025": float(np.percentile(arr[:, i], 2.5)),
        "p975": float(np.percentile(arr[:, i], 97.5)),
    } for i, name in enumerate(data.names[1:])}


def census_matches(block: dict, arm: dict, tol: float = 1e-9) -> bool:
    """Does the census loop fit the same training sets as the harness?

    If it does, its percentiles are the harness's percentiles to machine
    precision. If it does not, the census describes different fits and its
    "interior in all N" claim is about a different estimator.
    """
    return all(
        abs(block[name]["p025"] - arm["beta_p025"][name]) <= tol
        and abs(block[name]["p975"] - arm["beta_p975"][name]) <= tol
        for name in arm["beta_mean"] if name in block)


def paired(block: dict, base: dict) -> dict:
    """Paired difference against the baseline arm, over the re-splits.

    Paired because the two arms hold the identical decisions and draw the
    identical splits. NOT a sign test: the re-splits resample the same
    485 decisions and are not independent, the caveat
    `NOTES_GBM_BENCHMARK.md` §8 item 4 attaches to its own W-L records.
    """
    out = {}
    for key, values in block["per_repeat"].items():
        diff = np.asarray(values) - np.asarray(base["per_repeat"][key])
        better = diff < 0 if key == "brier" else diff > 0
        out[key] = {"higher_is_better": key != "brier",
                    "paired_mean_difference": float(diff.mean()),
                    "paired_sd": float(diff.std(ddof=1)),
                    "repeats_improved": int(better.sum()),
                    "repeats_worsened": int((diff != 0).sum() - better.sum())}
    return out


def strata_vs(block: dict, base: dict) -> dict:
    """Top-10 lift per stratum, this arm beside the baseline, with n."""
    out = {}
    for name, _, _ in BUCKETS:
        cell = block["strata"]["top10"][name]
        ref = base["strata"]["top10"][name]
        out[name] = {
            "decisions": cell["decisions"],
            "informative": cell["informative"],
            "chance_rate": cell["chance_rate"],
            "baseline_lift": ref["lift"], "lift": cell["lift"],
            "lift_delta": (None if cell["lift"] is None or ref["lift"] is None
                           else cell["lift"] - ref["lift"]),
        }
    return out


def pick_best(arms: dict) -> dict:
    """The best gravity arm, by `SELECTION_RULE`.

    The interior test looks at the GRAVITY columns and nothing else.
    `land_area_sqmi` is at the boundary in four of five arms of
    `NOTES_PANEL_EXPERIMENTS.md` §3.1 and in every arm here, so including
    it would disqualify every candidate and reduce the rule to "highest
    lift" without saying so.
    """
    large = BUCKETS[2][0]
    rows = []
    for name, arm in arms.items():
        if not name.startswith("gravity_"):
            continue
        interior = all(v["state"] == "INTERIOR"
                       for k, v in arm["verdicts"].items()
                       if GRAVITY_MARKER in k)
        rows.append((name, interior, arm["strata"]["top10"][large]["lift"]))
    qualified = [r for r in rows if r[1]] or rows
    best = max(qualified, key=lambda r: (r[2] or 0.0))
    return {"rule": SELECTION_RULE,
            "any_gravity_arm_fully_interior": any(r[1] for r in rows),
            "arm": best[0], "both_columns_interior": best[1],
            "large_stratum_top10_lift": best[2],
            "ranking": [{"arm": n, "fully_interior": i, "large_lift": lift}
                        for n, i, lift in sorted(
                            rows, key=lambda r: -(r[2] or 0.0))]}
