"""Top-k lift, stratified by choice-set size, and standardised across arms.

Why pooled lift is the wrong headline
-------------------------------------
A Simpson's paradox sits in the very comparison this experiment extends:
pooled top-10 lift FELL when the panel grew, while lift ROSE inside the
mid and large market strata. Measured by this module, in
`outputs/metrics/panel_experiments.json`
(`arms.*.methods.conditional_logit.strata.top10`), over 50 re-splits and
against the analytic null below:

    market size     original_only (n, lift)   combined (n, lift)
    small   <=25       7    1.72x              66    1.43x
    mid   26-100      41    2.75x             162    3.03x
    large    >100     46    6.18x             257    6.33x

    standardised to the combined mix:  2.858x -> 2.706x

The fall is composition. A choice set of 25 alternatives gives a random
guess a top-10 hit 40% of the time and a set of 11 gives it 91%, so lift
in the small stratum is capped near 1.5x whatever the model does. MWPVL
weights the panel towards small markets -- 7.4% of decisions to 13.6% --
and the pooled average moved with the mix, not with the model.

The superseded `outputs/metrics/lift_by_market_size.json` reported the
same paradox from one split against a tie-broken empirical null, and its
`finding` string quoted "3.68x -> 2.61x" against its own fields, which
read 2.948 -> 2.757. Neither pair is the like-for-like number; 2.858 ->
2.706 above is, because it asks both panels the same question mix. Cite
`panel_experiments.json`.

The five arms in this experiment have different market mixes BY
CONSTRUCTION, so ranking them on pooled lift would rank them on
composition. Everything here is therefore reported per stratum, with
``n``, and pooled only after direct standardisation to a common mix.

Two measurement choices, both declared
--------------------------------------
1. **The null is analytic, not empirical.** `choice.evaluate` computes
   its uniform null by ranking a constant score, so `np.argsort` breaks
   every tie by row order and the "uniform" top-10 becomes "is the chosen
   ZCTA among the first ten rows of the frame". That is an artefact of
   row order. The chance rate of a genuinely uniform guess is
   ``min(k, J) / J``, it has no tie-break, and it is what lift is taken
   against here. The empirical figure is still emitted beside it for
   continuity with `refit_expanded.json`.

2. **The reference mix is the `combined` arm's.** It is the largest arm
   and a superset of three of the other four, so standardising to it asks
   every arm the same question mix and asks it about the panel the
   project actually holds. Direct standardisation, in the demographic
   sense: weights come from the reference population, rates from the arm.
"""

from __future__ import annotations

import numpy as np

from .choice import ChoiceData

#: The same three cuts the superseded `lift_by_market_size.json` used, kept
#: so the retired artefact stays readable against this one. The cuts are the
#: only thing the two share: this module's null is analytic and its rates are
#: over 50 re-splits, so the LIFTS differ by construction and neither figure
#: corrects the other. `panel_experiments.json` is the one to cite.
BUCKETS: tuple[tuple[str, int, float], ...] = (
    ("small_le25", 1, 25),
    ("mid_26_100", 26, 100),
    ("large_gt100", 101, np.inf),
)

#: A stratum thinner than this is reported and NOT compared, and the
#: count that is tested is DISTINCT DECISIONS in the arm, not
#: decision-evaluations across re-splits. 50 re-splits of 7 decisions
#: produce 136 evaluations and no more information than 7 decisions
#: hold. 20 decisions puts a binomial standard error near 11 points on a
#: rate of 0.5, wider than any difference this experiment looks for.
MIN_INFORMATIVE = 20

TOP_KS = (1, 5, 10)

__all__ = ["BUCKETS", "MIN_INFORMATIVE", "TOP_KS", "bucket_of",
           "chance_rates", "counts_from_sizes", "hit_flags", "standardise"]


def bucket_of(sizes: np.ndarray) -> np.ndarray:
    """Bucket label index for each decision, from its choice-set size."""
    out = np.zeros(len(sizes), dtype=int)
    for i, (_, lo, hi) in enumerate(BUCKETS):
        out[(sizes >= lo) & (sizes <= hi)] = i
    return out


def hit_flags(score: np.ndarray, d: ChoiceData, k: int) -> np.ndarray:
    """Per-decision top-k hit. Tie-breaking copied from `choice.evaluate`."""
    flags = np.zeros(d.n_decisions, dtype=bool)
    for g in range(d.n_decisions):
        rows = np.flatnonzero(d.group == g)
        order = rows[np.argsort(-score[rows])]
        flags[g] = d.chosen[g] in order[:k]
    return flags


def chance_rates(d: ChoiceData, k: int) -> np.ndarray:
    """``min(k, J)/J`` per decision: a uniform guess's EXPECTED hit rate."""
    sizes = np.bincount(d.group).astype(float)
    return np.minimum(k, sizes) / sizes


def _accumulate(store: dict, key: str, hits, chance, buckets) -> None:
    """Add one repeat's per-decision results into the running totals."""
    slot = store.setdefault(key, {name: {"n": 0, "hits": 0.0, "chance": 0.0}
                                  for name, _, _ in BUCKETS})
    for i, (name, _, _) in enumerate(BUCKETS):
        m = buckets == i
        slot[name]["n"] += int(m.sum())
        slot[name]["hits"] += float(hits[m].sum())
        slot[name]["chance"] += float(chance[m].sum())


def accumulate_strata(store: dict, score: np.ndarray, d: ChoiceData,
                      buckets: np.ndarray) -> None:
    """Record one repeat for every reported k."""
    for k in TOP_KS:
        _accumulate(store, f"top{k}", hit_flags(score, d, k),
                    chance_rates(d, k), buckets)


def finalise(store: dict, distinct: dict) -> dict:
    """Rates and lift per stratum, with the thin strata marked.

    ``distinct`` is the number of DISTINCT decisions the arm holds in
    each bucket. It, not the evaluation count, decides thinness.
    """
    out = {}
    for key, strata in store.items():
        out[key] = {}
        for name, tot in strata.items():
            n = tot["n"]
            model = tot["hits"] / n if n else None
            chance = tot["chance"] / n if n else None
            out[key][name] = {
                "decisions": distinct.get(name, 0),
                "decision_evaluations": n,
                "model_rate": model,
                "chance_rate": chance,
                "lift": (model / chance) if (model and chance) else None,
                "informative": bool(distinct.get(name, 0) >= MIN_INFORMATIVE),
            }
    return out


def counts_from_sizes(sizes: np.ndarray) -> dict:
    """Distinct decisions per bucket."""
    b = bucket_of(sizes)
    return {name: int((b == i).sum()) for i, (name, _, _) in
            enumerate(BUCKETS)}


def mix_from_sizes(sizes: np.ndarray) -> dict:
    """Share of decisions in each bucket, for use as a reference mix."""
    b = bucket_of(sizes)
    return {name: float((b == i).mean()) for i, (name, _, _) in
            enumerate(BUCKETS)}


def standardise(strata: dict, mix: dict) -> dict:
    """Direct standardisation of an arm's stratum rates to a common mix.

    Returns the standardised model rate, the standardised chance rate and
    their ratio. ``None`` if the arm has no decisions in a weighted
    stratum, because extrapolating a rate into an empty cell would invent
    the number this whole file exists to avoid inventing.
    """
    out = {}
    for key, cells in strata.items():
        num = den = 0.0
        usable = True
        for name, weight in mix.items():
            cell = cells.get(name)
            if weight == 0:
                continue
            if cell is None or cell["model_rate"] is None:
                usable = False
                break
            num += weight * cell["model_rate"]
            den += weight * cell["chance_rate"]
        out[key] = ({"model_rate": num, "chance_rate": den,
                     "lift": num / den if den else None}
                    if usable else None)
    return out
