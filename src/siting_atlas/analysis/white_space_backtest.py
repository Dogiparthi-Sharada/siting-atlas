"""Hold out 2024-25 and ask whether the white space predicted it.

A coverage map is unfalsifiable on its own: it describes the present, and any
description of the present is true. This is the test that makes it a claim.

The test
--------
Build the service network from facilities that opened **2023 or earlier**,
rank the places it leaves uncovered by households, and take the top N. Then
look at where Amazon actually opened a delivery station in 2024 and 2025. If
white space means anything, the openings land in the flagged set more often
than in a list that never looked at coverage at all.

The baseline is the whole point
-------------------------------
The fair comparison is **the same N places, ranked by raw household count,
with no coverage logic**. That baseline is not a straw man: Amazon builds
where people are, so a household ranking will hit. If white space cannot beat
it, then the coverage layer adds nothing and the honest conclusion is that
"where is there unserved demand" resolves back to "where are there people".
Chance — N places drawn uniformly — is reported beside both, as a floor, not
as the comparison.

The pairing matters. Both rules score the SAME openings, so the difference is
tested on the discordant pairs only (McNemar's exact test, which here is a
two-sided binomial on the openings one rule caught and the other missed).
An unpaired chi-square would treat 129 openings as 258 independent draws.

Leakage
-------
``opened_by=2023`` is enforced in :func:`~.white_space_network.network`, and
it drops every UNDATED facility as well as every late-dated one. That is
strict on purpose. ``docs/research/NOTES_COVARIATE_LEAKAGE.md`` documents
what happens when a date that is really an upper bound is used as though it
were the opening: the guard passes and the number is worthless. An undated
MWPVL row could be a 2025 building, so it cannot be in a 2023 network.

The dates are MWPVL's stated opening months, 1,420 of them, validated at
93.6% against the OSHA first-inspection upper bound. 6.4% of them are
therefore wrong in an unknown direction, and nothing below corrects for that.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..common.logging_setup import get_logger
from . import white_space_cover as cover
from . import white_space_network as net

__all__ = ["CUT_YEAR", "HELD_OUT_YEARS", "N_CBSA", "N_ZCTA", "backtest",
           "mcnemar", "prepare", "score"]

_log = get_logger("analysis.white_space")

#: Facilities opening after this year are invisible to the network.
CUT_YEAR = 2023

#: The openings being predicted.
HELD_OUT_YEARS = (2024, 2025)

#: Cut-offs for the ZCTA-level list. 33,791 ZCTAs, so N=1000 is the top 3%.
N_ZCTA = (100, 250, 500, 1000, 2000)

#: Cut-offs for the CBSA-level list. 935 CBSAs in the panel.
N_CBSA = (10, 25, 50, 100)


def mcnemar(flagged: np.ndarray, baseline: np.ndarray) -> dict:
    """Two-sided exact McNemar on two rules scored over the same openings."""
    only_flagged = int((flagged & ~baseline).sum())
    only_baseline = int((baseline & ~flagged).sum())
    n = only_flagged + only_baseline
    p = (float(stats.binomtest(only_flagged, n, 0.5).pvalue) if n
         else float("nan"))
    return {"caught_only_by_white_space": only_flagged,
            "caught_only_by_households": only_baseline,
            "discordant_pairs": n,
            "p_value": None if n == 0 else round(p, 4)}


def _score(keys: pd.Series, flagged: set, baseline: set,
           universe: int, n: int) -> dict:
    """One cut-off: how often each rule contained the realised openings."""
    hit_ws = keys.isin(flagged).to_numpy()
    hit_bl = keys.isin(baseline).to_numpy()
    total = len(keys)
    return {
        "n_flagged": n,
        "openings_scored": total,
        "white_space_hits": int(hit_ws.sum()),
        "white_space_hit_rate": round(100.0 * hit_ws.mean(), 1),
        "household_baseline_hits": int(hit_bl.sum()),
        "household_baseline_hit_rate": round(100.0 * hit_bl.mean(), 1),
        "chance_hit_rate": round(100.0 * n / universe, 1),
        "white_space_beats_baseline": bool(hit_ws.sum() > hit_bl.sum()),
        "mcnemar": mcnemar(hit_ws, hit_bl),
    }


def _zcta_level(zctas: pd.DataFrame, nearest: np.ndarray, miles: float,
                openings: pd.DataFrame) -> list[dict]:
    uncovered = nearest > miles
    hh = zctas["households"].to_numpy(float)
    order_ws = zctas["zcta"].to_numpy()[np.argsort(
        -np.where(uncovered, hh, -np.inf), kind="stable")]
    order_bl = zctas["zcta"].to_numpy()[np.argsort(-hh, kind="stable")]
    n_unc = int(uncovered.sum())
    rows = []
    for n in N_ZCTA:
        # Never flag more places than are actually uncovered: padding the
        # list with covered ZCTAs to hit a round N would be scoring the
        # baseline under the white-space name.
        k = min(n, n_unc)
        row = _score(openings["zcta"], set(order_ws[:k]),
                     set(order_bl[:n]), len(zctas), n)
        row["n_flagged_available"] = k
        rows.append(row)
    return rows


def _cbsa_level(zctas: pd.DataFrame, nearest: np.ndarray, miles: float,
                openings: pd.DataFrame) -> list[dict]:
    ranked = cover.by_cbsa(zctas, nearest, miles)
    total = (zctas.dropna(subset=["cbsa_code"])
             .groupby("cbsa_code")["households"].sum()
             .sort_values(ascending=False))
    zc_to_cbsa = zctas.set_index("zcta")["cbsa_code"]
    titles = (zctas.dropna(subset=["cbsa_code"]).drop_duplicates("cbsa_code")
              .set_index("cbsa_code")["cbsa_title"])
    keys = openings["zcta"].map(zc_to_cbsa).dropna()
    rows = []
    for n in N_CBSA:
        flagged = set(ranked["cbsa_code"].head(n))
        row = _score(keys, flagged, set(total.index[:n]), len(total), n)
        row["openings_without_a_cbsa"] = int(len(openings) - len(keys))
        # Named, because "4 hits" is not checkable and "Amazon opened in
        # San Juan, which this flagged first" is.
        row["white_space_hit_metros"] = sorted(
            {titles.get(c) for c in keys if c in flagged})
        rows.append(row)
    return rows


def prepare(zctas: pd.DataFrame, coords: str) -> dict:
    """The pre-cut network, its nearest-facility array and the held-out set.

    Separated from :func:`score` because none of it depends on the radius:
    a seven-point sweep reads the facility frames once, not seven times.
    """
    pre, prov = net.network(coords, support=True, opened_by=CUT_YEAR,
                            zctas=zctas)
    nearest = cover.nearest_miles(zctas, pre)
    ds = net.delivery_stations(coords)
    openings = ds[ds["open_year"].isin(HELD_OUT_YEARS)].copy()
    openings = openings[openings["zcta"].isin(set(zctas["zcta"]))]
    zc_near = dict(zip(zctas["zcta"], nearest, strict=True))
    return {"provenance": prov, "nearest": nearest, "openings": openings,
            "network_frame": pre,
            "opening_distance": openings["zcta"].map(zc_near).to_numpy(float)}


def score(zctas: pd.DataFrame, ctx: dict, coords: str,
          miles: float) -> dict:
    """Score one (coordinate arm, radius) pair against the held-out years."""
    nearest, openings = ctx["nearest"], ctx["openings"]
    # The mechanism behind whatever the hit rates say. If Amazon densified,
    # these distances are short and no coverage-gap rule can be right.
    dist = ctx["opening_distance"]
    inside = dist <= miles
    _log.info("backtest %s @ %.1f mi: %d openings, %d inside pre-%d coverage",
              coords, miles, len(openings), int(inside.sum()), CUT_YEAR)
    return {
        "coord_set": coords,
        "radius_miles": miles,
        "network": ctx["provenance"],
        "openings_scored": int(len(openings)),
        "opening_zctas_distinct": int(openings["zcta"].nunique()),
        "openings_inside_existing_coverage": int(inside.sum()),
        "openings_inside_existing_coverage_pct": round(
            100.0 * float(inside.mean()), 1) if len(openings) else None,
        "median_miles_opening_to_nearest_pre_cut_facility": round(
            float(np.median(dist)), 1) if len(openings) else None,
        "zcta_level": _zcta_level(zctas, nearest, miles, openings),
        "cbsa_level": _cbsa_level(zctas, nearest, miles, openings),
    }


def backtest(zctas: pd.DataFrame, coords: str, miles: float) -> dict:
    """:func:`prepare` then :func:`score`, for a single point."""
    return score(zctas, prepare(zctas, coords), coords, miles)
