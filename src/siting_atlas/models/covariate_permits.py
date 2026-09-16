"""The time-varying arm of the covariate search, and what it costs.

Building permits are the only columns in the panel that are BOTH
time-varying and forward-looking, and nothing in the project uses them
(`docs/AUDIT_2026_09_14.md` section 4.2, item 9). Two of them are tested
here and they measure different things:

    permit_units_total    a STOCK-like level: how many housing units were
                          permitted in this county last year
    permits_yoy_pct       a FLOW, and the panel's only leading indicator:
                          whether permitting is accelerating

The flow is the more interesting of the two for a siting question. Every
other candidate in this search says how much of something is already in a
place; this one says which way the place is moving.

Two disciplines that are not optional here
------------------------------------------
THE VINTAGE RULE BINDS. Unlike the thirteen time-invariant candidates,
these move year to year, so a value read after the opening is the exact
failure `NOTES_COVARIATE_LEAKAGE.md` documents. `covariate_frame` reads
the latest panel year STRICTLY earlier than `open_year` and drops the
decision when none exists — which costs every 2018 opening, because the
panel starts in 2018.

THE SIGN PROBLEM IS REAL AND IS HANDLED BY TRANSFORM, NOT BY HOPE. A
year-on-year percentage is signed, and `beta'a` must be positive for every
alternative or the probability is undefined, so the raw column cannot be
entered at all. It is entered as the gross growth ratio
``1 + pct/100 = permits_t / permits_{t-1}`` and, separately, as that
ratio's reciprocal, so both signs get a turn. See `covariate_frame`.

The attrition question, which is the point of `attrition()`
------------------------------------------------------------
`permit_units_total` is the sparsest candidate in the search — 65.4% of
panel rows, and worse once the choice frame's other filters are applied.
Missing alternatives leave the choice set and missing CHOSEN alternatives
take the whole decision with them, so a covariate that improves the score
on what survives may only have made the question easier. `attrition()`
measures what left and whether it left at random: the decisions lost and
their market-size mix, and the ZCTAs lost against the ones that stayed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .choice import ChoiceData
from .covariate_frame import VARYING_CANDIDATES
from .panel_strata import BUCKETS, bucket_of

__all__ = ["attrition", "permit_spec"]


def permit_spec(base: tuple[str, ...], naive: tuple[str, ...]) -> dict:
    """Arms for the permit frame: each permit column alone, then a search.

    The search pool here is the three permit transforms ONLY, and the
    reason is cost rather than principle. A fit on this frame costs about
    nine seconds against two on the core frame, because the permit
    columns are county figures that are nearly constant inside a choice
    set and the optimiser crawls down the flat direction they create. A
    sixteen-candidate search would have cost eighty minutes to answer a
    question the core experiment has already answered for thirteen of
    those sixteen columns. `naive best + permits` covers the combination.
    """
    fixed = {"baseline": list(base)}
    for col in VARYING_CANDIDATES:
        fixed[f"+ {col}"] = [*base, col]
    fixed["+ all three permit columns"] = [*base, *VARYING_CANDIDATES]
    fixed["naive best + permits"] = [*naive, *VARYING_CANDIDATES]
    return {"fixed": fixed, "search": {
        "forward (nested) over permits": {
            "base": list(base),
            "candidates": list(VARYING_CANDIDATES)}}}


def _mix(sizes: np.ndarray) -> dict:
    """Share of decisions in each market-size stratum."""
    b = bucket_of(sizes)
    return {name: float((b == i).mean()) if len(b) else None
            for i, (name, _, _) in enumerate(BUCKETS)}


def attrition(core: ChoiceData, permit: ChoiceData,
              panel: pd.DataFrame, frame_zctas: set[str]) -> dict:
    """What requiring a permit vintage removed, and whether it was random.

    ``core`` and ``permit`` are the two frames; ``frame_zctas`` is the set
    of ZCTAs that survived the time-invariant filters, so the comparison
    isolates the permit join rather than re-reporting the earlier losses.
    """
    core_sizes = np.bincount(core.group)
    keep_sizes = np.bincount(permit.group)
    kept_ids = set(permit.ids)
    lost = np.array([i for i, d in enumerate(core.ids)
                     if d not in kept_ids], dtype=int)
    year = int(panel["year"].min())
    one = panel[(panel["year"] == year)].drop_duplicates("zcta")
    one = one[one["zcta"].isin(frame_zctas)]
    has = one["permit_units_total"].notna()
    cols = ["households", "establishments", "land_area_sqmi"]
    return {
        "decisions_core": int(core.n_decisions),
        "decisions_with_permits": int(permit.n_decisions),
        "decisions_lost": int(len(lost)),
        "market_mix_kept": _mix(keep_sizes),
        "market_mix_lost": _mix(core_sizes[lost]) if len(lost) else None,
        "median_choice_set_kept": float(np.median(keep_sizes)),
        "median_choice_set_lost": (float(np.median(core_sizes[lost]))
                                   if len(lost) else None),
        "zcta_coverage_measured_at_panel_year": year,
        "frame_zctas": int(len(one)),
        "frame_zctas_with_permits": int(has.sum()),
        "zcta_permit_coverage": float(has.mean()),
        "zcta_means_with_permits": {
            c: float(one.loc[has, c].mean()) for c in cols},
        "zcta_means_without_permits": {
            c: float(one.loc[~has, c].mean()) for c in cols},
        "note": "The ZCTAs without a permit value are systematically "
                "smaller on every baseline column, so the permit frame is "
                "not a random subsample: it drops the thin rural end of "
                "each metro's choice set and therefore makes the ranking "
                "problem easier. Arms are compared only WITHIN this frame.",
    }


def print_attrition(a: dict) -> None:
    print("\n  === what requiring a pre-opening permit vintage cost ===\n")
    print(f"  decisions   {a['decisions_core']} -> "
          f"{a['decisions_with_permits']}  ({a['decisions_lost']} lost)")
    print(f"  ZCTAs       {a['frame_zctas']} -> "
          f"{a['frame_zctas_with_permits']}  "
          f"({100 * a['zcta_permit_coverage']:.1f}% have a permit value)")
    print(f"\n  {'market-size mix':22}{'kept':>10}{'lost':>10}")
    for name, _, _ in BUCKETS:
        lost = a["market_mix_lost"]
        print(f"  {name:22}{a['market_mix_kept'][name]:10.3f}"
              f"{(lost[name] if lost else float('nan')):10.3f}")
    print(f"\n  {'ZCTA mean':22}{'has permits':>14}{'no permits':>14}")
    for col in a["zcta_means_with_permits"]:
        print(f"  {col:22}{a['zcta_means_with_permits'][col]:14.1f}"
              f"{a['zcta_means_without_permits'][col]:14.1f}")
