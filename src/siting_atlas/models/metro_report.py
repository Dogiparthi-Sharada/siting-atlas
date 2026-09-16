"""Prereg section 9, applied mechanically, and section 7 quoted verbatim.

The criterion has two clauses and the second is where models die:

> H1 is supported if, out of time, the metro model beats the households
> baseline on AUC in a majority of held-out years AND its calibration is at
> least as good as the constant null in a majority of years.

Both are counted here from the per-year table, with no discretion left. The
outcome language in `VERDICT_TEXT` is copied from prereg section 7 and is
not rewritten to fit the number that came out: the prereg says both outcomes
are complete findings and that the negative is "harder and arguably more
valuable", which is only true if it is reported in the words that were
written before the result.
"""

from __future__ import annotations

__all__ = ["VERDICT_TEXT", "criterion", "ZIP_BENCHMARK"]

VERDICT_TEXT = {
    "H1": (
        "Free public data predicts regional expansion but cannot "
        "discriminate within a metropolitan area. The boundary sits between "
        "the county and the ZIP code - exactly where most US public data "
        "stops being published. A community can learn that its region is on "
        "the list; it cannot learn that its neighbourhood has been chosen."
    ),
    "H0": (
        "Free public data cannot predict siting at any grain tested. The "
        "ZIP-level failure is not a resolution problem but a general one: "
        "the variables that drive the decision are not public at any "
        "resolution."
    ),
}

#: The ZIP-grain margin H1's first paragraph asks the metro margin to beat,
#: read from outputs/metrics/gbm_benchmark.json across_repeats, 50 paired
#: re-splits of 38 held-out decisions. The fitted conditional logit came out
#: BELOW its zero-parameter raw-count baseline.
ZIP_BENCHMARK = {
    "artefact": "outputs/metrics/gbm_benchmark.json",
    "block": "across_repeats.conditional_logit.vs_raw_count_mean",
    "model_minus_baseline_top10_of_38": -0.36,
    "as_share_of_decisions": -0.0095,
    "wins": 11, "losses": 23, "n_repeats": 50,
    "reading": ("at ZIP grain the fitted model did not beat its own "
                "zero-parameter baseline, so any positive metro margin "
                "clears the comparative half of H1; the numeric criterion "
                "in prereg section 9 is the binding one"),
}


def criterion(per_year: dict, *, exclude_years=()) -> dict:
    """Count the two clauses over the held-out years.

    `per_year` maps year -> {"model": {...}, "baseline2_households": {...},
    "constant_null": {...}}, each with "auc" and "ece".
    """
    excl = {int(y) for y in exclude_years}
    years = sorted(int(y) for y in per_year if int(y) not in excl)
    auc_rows, ece_rows = [], []
    for y in years:
        blk = per_year[y] if y in per_year else per_year[str(y)]
        m, b, n = (blk["model"], blk["baseline2_households"],
                   blk["constant_null"])
        auc_ok = (m["auc"] is not None and b["auc"] is not None
                  and m["auc"] > b["auc"])
        ece_ok = (m["ece"] is not None and n["ece"] is not None
                  and m["ece"] <= n["ece"])
        auc_rows.append({"year": y, "model_auc": m["auc"],
                         "baseline2_auc": b["auc"],
                         "diff": (None if m["auc"] is None or b["auc"] is None
                                  else round(m["auc"] - b["auc"], 4)),
                         "model_wins": bool(auc_ok)})
        ece_rows.append({"year": y, "model_ece": m["ece"],
                         "constant_null_ece": n["ece"],
                         "diff": (None if m["ece"] is None or n["ece"] is None
                                  else round(m["ece"] - n["ece"], 6)),
                         "model_at_least_as_good": bool(ece_ok)})

    n_years = len(years)
    auc_wins = sum(r["model_wins"] for r in auc_rows)
    ece_wins = sum(r["model_at_least_as_good"] for r in ece_rows)
    clause1 = auc_wins * 2 > n_years
    clause2 = ece_wins * 2 > n_years
    holds = bool(clause1 and clause2)
    return {
        "years": years,
        "n_years": n_years,
        "excluded_years": sorted(excl),
        "auc_vs_baseline2": auc_rows,
        "ece_vs_constant_null": ece_rows,
        "clause1_auc_majority": {"wins": auc_wins, "of": n_years,
                                 "passes": bool(clause1)},
        "clause2_calibration_majority": {"wins": ece_wins, "of": n_years,
                                         "passes": bool(clause2)},
        "hypothesis": "H1" if holds else "H0",
        "verdict_text": VERDICT_TEXT["H1" if holds else "H0"],
    }
