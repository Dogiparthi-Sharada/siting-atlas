"""Aggregation and printing for `covariate_search`.

Every number is reported STRATIFIED by choice-set size. Pooled top-k lift
across heterogeneous choice sets already produced one wrong conclusion in
this project — pooled lift FELL while lift rose in the mid and large
strata — so pooled figures appear here only beside the strata that
generate them, never instead of them. The artefact for that finding is
`outputs/metrics/panel_experiments.json`: standardised top-10 lift
2.858 -> 2.706, `arms.*.methods.conditional_logit.standardised.top10`.
It is NOT `lift_by_market_size.json`, which measured the same thing on
one split with a tie-broken null and was superseded on 2026-09-14.

The strata, the chance rate and the `MIN_INFORMATIVE` cut are imported
from `panel_strata` rather than re-declared, so this artefact and
`panel_experiments.json` cut the data the same way and can be read
together. The chance rate is the analytic ``min(k, J)/J``, not the
tie-broken empirical null `choice.evaluate` emits.
"""

from __future__ import annotations

import numpy as np

from .panel_strata import BUCKETS, MIN_INFORMATIVE, TOP_KS

__all__ = ["aggregate", "paired", "print_report"]


def _blank() -> dict:
    return {name: {"n": 0, "hits": 0.0, "chance": 0.0}
            for name, _, _ in BUCKETS}


def aggregate(repeats: list[dict], arm: str) -> dict:
    """Stratum rates and lift for one arm, pooled over every repeat."""
    out = {}
    for k in TOP_KS:
        cells = _blank()
        for rep in repeats:
            bucket = np.asarray(rep["bucket"])
            hits = np.asarray(rep["arms"][arm]["hits"][str(k)], float)
            chance = np.asarray(rep["chance"][str(k)], float)
            for i, (name, _, _) in enumerate(BUCKETS):
                m = bucket == i
                cells[name]["n"] += int(m.sum())
                cells[name]["hits"] += float(hits[m].sum())
                cells[name]["chance"] += float(chance[m].sum())
        total = {"n": 0, "hits": 0.0, "chance": 0.0}
        for cell in cells.values():
            for key in total:
                total[key] += cell[key]
        out[f"top{k}"] = {
            name: _rates(cell) for name, cell in cells.items()} | {
            "pooled": _rates(total)}
    briers = [rep["arms"][arm]["brier"] for rep in repeats]
    out["brier"] = float(np.mean(briers))
    out["brier_uniform_null"] = float(np.mean(
        [rep["arms"][arm]["brier_null"] for rep in repeats]))
    out["columns"] = repeats[0]["arms"][arm]["cols"]
    return out


def _rates(cell: dict) -> dict:
    n = cell["n"]
    if not n:
        return {"decision_evaluations": 0, "model_rate": None,
                "chance_rate": None, "lift": None, "informative": False}
    model, chance = cell["hits"] / n, cell["chance"] / n
    return {"decision_evaluations": n, "model_rate": model,
            "chance_rate": chance,
            "lift": (model / chance) if chance else None,
            "informative": bool(n >= MIN_INFORMATIVE)}


def _large_rate(rep: dict, arm: str, k: int) -> float:
    """One repeat's top-k hit RATE inside the >100-alternative stratum."""
    bucket = np.asarray(rep["bucket"])
    m = bucket == (len(BUCKETS) - 1)
    hits = np.asarray(rep["arms"][arm]["hits"][str(k)], float)
    return float(hits[m].mean()) if m.any() else float("nan")


def paired(repeats: list[dict], arm: str, ref: str, k: int = 10) -> dict:
    """Paired difference against a reference arm, large metros only.

    A percentile spread over re-splits is NOT a standard error: it
    describes how the estimator moves across partitions of one fixed set
    of decisions and says nothing about drawing a different set.
    """
    diff = np.array([_large_rate(r, arm, k) - _large_rate(r, ref, k)
                     for r in repeats])
    diff = diff[~np.isnan(diff)]
    return {"mean_rate_difference": float(diff.mean()),
            "sd_over_resplits": float(diff.std(ddof=1)),
            "wins": int((diff > 0).sum()), "ties": int((diff == 0).sum()),
            "losses": int((diff < 0).sum())}


#: Below this a coefficient is at the lower boundary: `choice.py` writes
#: beta = exp(theta) and the optimiser walks theta to minus infinity down
#: a flat likelihood when a column is worthless TO A POSITIVE WEIGHT.
BOUNDARY_LO = 1e-8

#: Above this it has run to the other boundary. `NOTES_LEAKAGE_DECISIVE.md`
#: section 3 hit the same thing once in 50 splits and quoted the median.
BOUNDARY_HI = 1e8


def _beta_interval(repeats: list[dict], arm: str) -> dict:
    """Median, mean and 2.5-97.5 percentile of each beta over re-splits.

    The MEDIAN is the summary to read. A conditional logit on a flat
    likelihood direction produces betas of 1e-30 and 1e+300 in the same
    experiment, and a mean of those is a number about the optimiser
    rather than about the covariate. Both boundary shares are reported so
    a reader can see how often it happened instead of inferring it.
    """
    names = list(repeats[0]["arms"][arm]["cols"][1:])
    draws = {n: np.array([r["arms"][arm]["beta"][n] for r in repeats
                          if r["arms"][arm]["beta"] is not None], float)
             for n in names}
    return {n: {"median": float(np.median(v)),
                "mean": float(np.mean(v[np.isfinite(v)]))
                if np.isfinite(v).any() else None,
                "p025": float(np.percentile(v, 2.5)),
                "p975": float(np.percentile(v, 97.5)),
                "at_lower_boundary_share": float((v < BOUNDARY_LO).mean()),
                "at_upper_boundary_share": float((v > BOUNDARY_HI).mean())}
            for n, v in draws.items() if len(v)}


def summarise_arm(repeats: list[dict], arm: str, ref: str | None) -> dict:
    out = aggregate(repeats, arm)
    if repeats[0]["arms"][arm]["beta"] is not None:
        out["beta"] = _beta_interval(repeats, arm)
    if ref is not None and arm != ref:
        out["vs_baseline_large_top10"] = paired(repeats, arm, ref, 10)
        out["vs_baseline_large_top1"] = paired(repeats, arm, ref, 1)
    picks: dict[str, int] = {}
    for rep in repeats:
        for col in rep["arms"][arm]["cols"]:
            picks[col] = picks.get(col, 0) + 1
    if len({tuple(r["arms"][arm]["cols"]) for r in repeats}) > 1:
        out["selection_frequency"] = dict(
            sorted(picks.items(), key=lambda kv: -kv[1]))
        out["columns"] = "varies by repeat"
    return out


def _cell(arm: dict, k: int, stratum: str) -> str:
    c = arm[f"top{k}"][stratum]
    if c["lift"] is None:
        return f"{'--':>14}"
    mark = " " if c["informative"] else "?"
    return f" {100 * c['model_rate']:5.1f}% {c['lift']:5.2f}x{mark}"


def print_report(title: str, arms: dict, ref: str) -> None:
    """Stratified table. Large metros last because they are the point."""
    print(f"\n  === {title} ===\n")
    head = f"  {'arm':34}" + "".join(
        f"{name:>14}" for name, _, _ in BUCKETS) + f"{'pooled':>14}"
    for k in (10, 1):
        print(f"\n  top-{k}: hit rate and lift over an analytic "
              "min(k,J)/J chance rate")
        print(head)
        for arm, res in arms.items():
            row = "".join(_cell(res, k, name) for name, _, _ in BUCKETS)
            print(f"  {arm:34}{row}{_cell(res, k, 'pooled')}")
    print("\n  ? = stratum thinner than "
          f"{MIN_INFORMATIVE} decision-evaluations; reported, not compared")
    print("\n  paired vs baseline, LARGE metros (>100 alternatives), top-10")
    print(f"  {'arm':34}{'mean diff':>12}{'sd':>8}{'W':>5}{'T':>5}{'L':>5}"
          f"{'Brier':>11}")
    for arm, res in arms.items():
        p = res.get("vs_baseline_large_top10")
        if p is None:
            print(f"  {arm:34}{'(reference)':>12}{'':>23}"
                  f"{res['brier']:11.6f}")
            continue
        print(f"  {arm:34}{100 * p['mean_rate_difference']:+11.2f}pp"
              f"{100 * p['sd_over_resplits']:8.2f}{p['wins']:5d}"
              f"{p['ties']:5d}{p['losses']:5d}{res['brier']:11.6f}")
    print(f"\n  reference arm: {ref}. A percentile spread over re-splits is"
          "\n  NOT a standard error.")
    print_betas(arms)


def print_betas(arms: dict) -> None:
    """Coefficients, as ratios to the households numeraire.

    `lo` is the share of re-splits on which the optimiser drove the
    coefficient to zero. A column with lo near 1.0 was judged worthless
    BY A MODEL THAT CAN ONLY GIVE IT A POSITIVE WEIGHT, which is not the
    same finding as a column with no information in it.
    """
    print("\n  coefficients: median over re-splits, ratio to households")
    print(f"  {'arm / column':52}{'median':>11}{'2.5%':>11}{'97.5%':>11}"
          f"{'lo':>6}{'hi':>6}")
    for arm, res in arms.items():
        for name, b in res.get("beta", {}).items():
            print(f"  {arm + ' / ' + name:52}{b['median']:11.4g}"
                  f"{b['p025']:11.4g}{b['p975']:11.4g}"
                  f"{b['at_lower_boundary_share']:6.2f}"
                  f"{b['at_upper_boundary_share']:6.2f}")
