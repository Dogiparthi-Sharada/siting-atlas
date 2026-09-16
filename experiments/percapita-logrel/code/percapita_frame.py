"""Per-household RATE columns, and the collinearity they are meant to cure.

`COVARIATES_TRIED.md` section 1.2 diagnoses five ACS columns as
unidentified: they correlate 0.84-1.00 with `households` WITHIN a metro,
and `households` is the numeraire whose coefficient is fixed at 1.0. The
model cannot tell "attractive because people live here" from "attractive
because people live here and therefore own cars".

This module builds the obvious fix — divide by the numeraire — and the
measurement that shows whether the fix worked ON ITS OWN TERMS, i.e. the
within-metro correlation with `households` before and after. Whether the
de-collinearised column then PREDICTS anything is a separate question and
is the job of `percapita_search`.

The price, stated here rather than in a footnote
------------------------------------------------
`MODEL_SPEC.md` section 1 derives `V = ln(beta'a)` from Train section 3.4
Example 2, and the derivation works ONLY because the attraction variables
are EXTENSIVE: merge two ZCTAs and `a_j + a_k = a_c`, so
`exp(V_j) + exp(V_k) = exp(V_c)` and the choice probabilities add. A RATE
is intensive. Merge two ZCTAs and employment-per-household AVERAGES; it
does not add. Every column this module creates therefore breaks the
zone-merger invariance that is the stated reason the log form was chosen.

The project has already paid this price twice — for `inv_median_home_value`
and `inv_diesel_pm` in `covariate_frame`, and for the network-proximity
covariates in `panel_network` — so it is a priced trade-off and not a
disqualification. It is still a real cost: with a rate in `a`, the
specification is a positive-weight ranking function that resembles a
conditional logit rather than a destination-choice model in Train's sense,
and the ZCTA boundaries stop being innocent.

There is a second, more concrete version of the same problem. `a` is a SUM
of columns, so mixing counts with rates mixes units. A large ZCTA's
utility is dominated by its counts and the rate term is a rounding error;
a small ZCTA's utility can be dominated by the rate. The column therefore
acts mostly on small alternatives whatever its coefficient, which is a
functional-form artefact rather than a finding about warehouses.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .choice import ChoiceData

#: Suffix marking a column as divided by the numeraire.
SUFFIX = "_per_hh"

#: The denominator. Must match `choice.NUMERAIRE`.
DENOMINATOR = "households"

#: Count columns that `COVARIATES_TRIED.md` records as failing ON
#: COLLINEARITY (section 1.2) rather than on geographic grain (1.1). The
#: grain failures are not fixable by a transform and are not here.
#: `establishments` and `warehousing_establishments` are in the published
#: baseline rather than among the failures, and are included because the
#: first sits at the boundary and the second is the whole model.
SOURCES = ("employment", "establishments", "annual_payroll",
           "in_labor_force", "owner_occupied", "renter_occupied",
           "vehicle_availability_total", "bachelors_degree",
           "warehousing_establishments")

#: Columns whose per-household ratio is DEGENERATE, with the measurement
#: that says so. `vehicle_availability_total` is not merely correlated
#: 1.000 with `households`, as `COVARIATES_TRIED.md` row 10 describes it —
#: it IS `households`, to floating-point equality, on all 21,768 ZCTAs of
#: the frame. It is the ACS table B25044 universe, "total households by
#: vehicles available", whose total is the household count. Its ratio is
#: therefore the constant 1.0 and cannot be entered: a constant column in
#: `beta'a` adds the same amount to every alternative's linear index,
#: which in THIS model is not a no-op (it flattens every probability
#: towards uniform) and carries no information either way. It stays in the
#: correlation table, because the fact that the project shipped a
#: duplicate of its own numeraire for fifteen covariate tests is the
#: finding, and it is dropped from the arms.
DEGENERATE = ("vehicle_availability_total",)

#: What actually gets a ratio column and an arm.
MODEL_SOURCES = tuple(c for c in SOURCES if c not in DEGENERATE)

__all__ = ["DEGENERATE", "DENOMINATOR", "MODEL_SOURCES", "SOURCES", "SUFFIX",
           "add_ratios", "correlation_table", "ratio_name"]


def ratio_name(col: str) -> str:
    return col + SUFFIX


def add_ratios(d: ChoiceData, sources: tuple[str, ...] = MODEL_SOURCES,
               ) -> ChoiceData:
    """The same decisions and alternatives, with `col / households` added.

    The incoming columns are already mean-scaled by `build_frame`, so the
    ratio computed here is the true ratio times a constant. It is
    re-scaled to mean one, exactly as `build_frame` scales everything
    else, which changes the units of beta and nothing else because the
    choice probability is a ratio of linear indices.
    """
    names = list(d.names)
    if DENOMINATOR not in names:
        raise ValueError(f"{DENOMINATOR} absent; it is the denominator")
    h = d.a[:, names.index(DENOMINATOR)]
    if not np.all(h > 0):
        raise ValueError(f"{DENOMINATOR} must be strictly positive")
    cols = [d.a]
    for src in sources:
        if src not in names:
            raise ValueError(f"{src} absent from the frame")
        r = d.a[:, names.index(src)] / h
        if r.std() == 0:
            raise ValueError(f"{src}/{DENOMINATOR} is constant; see "
                             "percapita_frame.DEGENERATE")
        mean = float(r.mean())
        cols.append((r / mean if mean > 0 else r)[:, None])
        names.append(ratio_name(src))
    return ChoiceData(np.hstack(cols), d.group, d.chosen, list(d.ids),
                      tuple(names))


def _corr(x: np.ndarray, y: np.ndarray) -> float | None:
    if x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def correlation_table(d: ChoiceData, sources: tuple[str, ...] = SOURCES,
                      min_alternatives: int = 100) -> dict:
    """Within-choice-set correlation with the numeraire, before and after.

    A choice set here IS a metro: `build_frame` offers every ZCTA of the
    facility's CBSA. Restricting to sets with more than `min_alternatives`
    alternatives reproduces the "metros with more than 100 ZCTAs" cut the
    hypothesis was measured on, and is the same `large_gt100` stratum the
    lift table reports.

    DISTINCT BLOCKS, NOT DECISIONS. Several facilities open in the same
    metro and see a near-identical choice set; averaging over decisions
    would weight big metros by how many warehouses they happen to have.
    Blocks are deduplicated on (n_alternatives, summed numeraire), which
    separates metros and separates CBP vintages within a metro.
    """
    names = list(d.names)
    sizes = np.bincount(d.group)
    seen: set[tuple] = set()
    per_block: dict[str, list[float]] = {}
    blocks = 0
    for g in range(d.n_decisions):
        if sizes[g] <= min_alternatives:
            continue
        rows = np.flatnonzero(d.group == g)
        block = d.a[rows]
        h = block[:, names.index(DENOMINATOR)]
        key = (len(rows), round(float(h.sum()), 6))
        if key in seen:
            continue
        seen.add(key)
        blocks += 1
        for src in sources:
            x = block[:, names.index(src)]
            for label, v in ((src, x), (ratio_name(src), x / h)):
                c = _corr(v, h)
                if c is not None:
                    per_block.setdefault(label, []).append(c)
    table = {"blocks": blocks, "min_alternatives": min_alternatives,
             "statistic": "mean over distinct metro blocks of the "
                          "within-block Pearson correlation with "
                          f"{DENOMINATOR}", "correlation": {}}
    for src in sources:
        table["correlation"][src] = {
            "level": float(np.mean(per_block[src])) if src in per_block
            else None,
            "per_household": float(np.mean(per_block[ratio_name(src)]))
            if ratio_name(src) in per_block else None}
    return table


def print_correlations(table: dict) -> None:
    print(f"\n  within-metro correlation with {DENOMINATOR}, "
          f"{table['blocks']} metro blocks of >{table['min_alternatives']} "
          "alternatives")
    print(f"  {'column':34}{'level':>10}{'per household':>16}{'change':>10}")
    for src, row in table["correlation"].items():
        lo, hi = row["level"], row["per_household"]
        left = f"{lo:+10.3f}" if lo is not None else f"{'--':>10}"
        if hi is None:
            print(f"  {src:34}{left}{'constant':>16}{'degenerate':>12}")
            continue
        print(f"  {src:34}{left}{hi:+16.3f}{abs(hi) - abs(lo):+10.3f}")
    print("  change is |after| - |before|; negative means less collinear")
    print("  'constant' = the ratio has zero variance, so the column IS the "
          "numeraire.\n  See percapita_frame.DEGENERATE.")


def frame_correlations(z: pd.DataFrame, sources: tuple[str, ...],
                       min_zctas: int = 100) -> dict:
    """The same statistic computed on the ZCTA frame, as a cross-check.

    `correlation_table` measures the matrix the model actually sees, which
    is the number that matters. This one measures the ZCTA table before
    any vintage join, so the two disagreeing would mean the join changed
    the collinearity rather than the transform.
    """
    sizes = z.groupby("cbsa_code").size()
    big = z[z["cbsa_code"].isin(sizes[sizes > min_zctas].index)]
    out: dict[str, dict] = {}
    for src in sources:
        if src not in big.columns:
            continue
        lv, rt = [], []
        for _, b in big.groupby("cbsa_code"):
            h = b[DENOMINATOR].to_numpy(float)
            x = b[src].to_numpy(float)
            for bucket, v in ((lv, x), (rt, x / h)):
                c = _corr(v, h)
                if c is not None:
                    bucket.append(c)
        out[src] = {"level": float(np.mean(lv)) if lv else None,
                    "per_household": float(np.mean(rt)) if rt else None}
    return {"metros": int((sizes > min_zctas).sum()), "correlation": out}
