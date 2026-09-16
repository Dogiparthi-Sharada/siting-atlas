"""Summary statistics and the console table for `gbm_benchmark`.

Split out only because the benchmark module was 333 lines and the house
limit is 300. Nothing here fits, predicts or splits; it reads a list of
per-re-split metric dicts and prints. If a number appears here that does
not appear in `outputs/metrics/gbm_benchmark.json`, that is a bug.
"""

from __future__ import annotations

import numpy as np

from ..common import paths

__all__ = ["HEADLINE_SPLIT_WARNING", "caveats", "summarise", "table"]

#: Carried into the artefact beside `headline_split` so the block cannot be
#: read without it. See `caveats` for the measurement behind it.
HEADLINE_SPLIT_WARNING = (
    "DO NOT QUOTE THE GBM ROWS OF headline_split. Measured 2026-09-15: "
    "multiplying the attraction matrix by (1 + 1e-12 * standard normal) -- a "
    "perturbation far below the precision of any input and about what a "
    "parquet float round-trip costs -- moves the GBM top-10 on this single "
    "split by up to 2 of 38 decisions (deep/300 shares 20 -> 19, 22, 18; "
    "deep/300 levels 18 -> 17, 20, 19; the four shallow arms by 1), over "
    "three perturbation draws. conditional_logit (19) and raw_count (20) do "
    "not move at all in any draw. The GBM figures here are therefore a draw "
    "from LightGBM's histogram bin boundaries, not a measurement. "
    "across_repeats is the block to quote: over the same three draws its "
    "top10_mean moves by at most 0.48 of a decision on a mean near 22, and "
    "the ordering that carries the verdict -- shallow GBM ~22.1-22.7 > "
    "raw_count ~20.5-21.0 ~ conditional_logit 20.6 > deep GBM ~18.5-18.9 -- "
    "is unchanged in every draw. NOTE that raw_count's own top10_mean moved "
    "0.5 in one draw, so across_repeats is stable to about half a decision "
    "rather than exactly. "
    "NOT FIXED BY A FLAG: lgb.LGBMRanker(deterministic=True, "
    "force_row_wise=True) was tested against every arm and returned "
    "bit-identical counts to the plain call in all eight comparisons (base, "
    "a repeat of base, and three perturbations). The call was already "
    "reproducible on identical input at n_jobs=1; the instability is "
    "sensitivity to the DATA, which no determinism flag removes."
)

#: The comparator every difference is taken against. Not the fitted model:
#: the raw count is the thing that beat the fitted model, so it is the bar.
BASELINE = "raw_count"


def caveats(n_decisions: int, smallest_set: int) -> list[str]:
    """Written here, not in the caller, so the artefact and the console
    table can never carry different caveats."""
    return [
        f"The interval is the spread over 60/40 RE-SPLITS of one sample of "
        f"{n_decisions} decisions. It is not a confidence interval for the "
        f"population of siting decisions.",
        "Re-splits share decisions, so the repeats are not independent and "
        "the sd understates true sampling variability.",
        "Splits are random over decisions and NOT clustered by metro, to "
        "match choice_runner. Decisions in one metro share a choice set.",
        "Brier depends on the fitted softmax temperature and so is not "
        "invariant to the score-to-probability map. Only top-k is. Read "
        "top-k as the comparison and Brier as a secondary.",
        f"The smallest choice set has {smallest_set} alternatives, so top-10 "
        f"is a certain hit there for every method including the null.",
        "GBM hyperparameters were not tuned and not pre-registered. The "
        "verdict is taken on the RANGE across the grid, not on a winner.",
        HEADLINE_SPLIT_WARNING,
    ]


def summarise(repeats: list[dict], method: str) -> dict:
    """Spread over re-splits, plus the PAIRED difference against the raw count.

    Paired because the same re-split is used for both: a fold that happens
    to contain easy decisions inflates every method at once, and the
    difference removes that. The unpaired sd is reported too so a reader can
    see how much of the spread is fold difficulty rather than method.
    """
    v = np.array([r[method]["top10"] for r in repeats], float)
    paired = v - np.array([r[BASELINE]["top10"] for r in repeats], float)
    return {
        "top10_mean": float(v.mean()), "top10_sd": float(v.std(ddof=1)),
        "top10_min": float(v.min()), "top10_max": float(v.max()),
        "top10_p2.5": float(np.percentile(v, 2.5)),
        "top10_p97.5": float(np.percentile(v, 97.5)),
        "top1_mean": float(np.mean([r[method]["top1"] for r in repeats])),
        "top5_mean": float(np.mean([r[method]["top5"] for r in repeats])),
        "brier_mean": float(np.mean([r[method]["brier"] for r in repeats])),
        "vs_raw_count_mean": float(paired.mean()),
        "vs_raw_count_sd": float(paired.std(ddof=1)),
        "vs_raw_count_wins": int((paired > 0).sum()),
        "vs_raw_count_losses": int((paired < 0).sum()),
    }


def table(r: dict) -> None:
    """The comparison section 9.4 asked to be reported in one table."""
    n = r["n_test_decisions"]
    print(f"\n  GBM BENCHMARK - MODEL_SPEC.md section 9.4, {r['frame']} frame")
    print(f"  {r['n_decisions_total']} decisions, {n} held out per split, "
          f"{r['n_repeats']} re-splits, seed {r['seed']}")
    print(f"  Covariates: {', '.join(r['attractions'])}\n")

    print(f"  HEADLINE SPLIT - repeat 0, bit-identical to choice_runner's "
          f"(hits of {n})")
    print("  *** the GBM rows below are NOT quotable: a 1e-12 perturbation "
          "moves them by up to 2 ***")
    print(f"    {'':22}{'top-1':>8}{'top-5':>8}{'top-10':>8}{'Brier':>12}")
    for m, v in r["headline_split"].items():
        print(f"    {m:22}{v['top1']:>8}{v['top5']:>8}{v['top10']:>8}"
              f"{v['brier']:>12.6f}")

    print(f"\n  ACROSS {r['n_repeats']} RE-SPLITS. One split is not evidence; "
          f"read this block, not the one above.")
    print(f"    {'':22}{'top-1':>7}{'top-5':>7}{'top-10':>8}{'sd':>6}"
          f"{'2.5-97.5':>12}{'vs count':>10}{'+/-':>7}{'W-L':>8}")
    for m, s in r["across_repeats"].items():
        span = f"{s['top10_p2.5']:.0f}-{s['top10_p97.5']:.0f}"
        wl = f"{s['vs_raw_count_wins']}-{s['vs_raw_count_losses']}"
        print(f"    {m:22}{s['top1_mean']:>7.2f}{s['top5_mean']:>7.2f}"
              f"{s['top10_mean']:>8.2f}{s['top10_sd']:>6.2f}{span:>12}"
              f"{s['vs_raw_count_mean']:>+10.2f}{s['vs_raw_count_sd']:>7.2f}"
              f"{wl:>8}")
    print(f"  All counts are of {n} held-out decisions. 'vs count' is the "
          f"PAIRED mean difference\n  against the raw count on the same "
          f"re-split; '+/-' is its sd over re-splits.\n  W-L counts "
          f"re-splits won and lost against the raw count; ties are neither.")

    imp = r.get("gain_importance", {})
    if imp:
        print(f"\n  WHAT THE GBM SPLITS ON - total gain share, "
              f"{r['best_gbm_by_cv_top10']}, fitted on repeat 0")
        for k, v in sorted(imp.items(), key=lambda kv: -kv[1]):
            print(f"    {k:34}{v:8.1%}")

    print("\n  CAVEATS - none of these is optional reading.")
    for c in r["caveats"]:
        print(f"    - {c}")
    print(f"\n  -> {paths.rel(paths.METRICS / 'gbm_benchmark.json')}\n")
