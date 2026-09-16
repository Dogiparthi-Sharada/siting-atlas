"""Coverage as a union of discs, and the ranked list of what falls outside.

The geometry is deliberately the simplest thing that can be checked by hand:
a ZCTA is covered when its centroid is within ``miles`` **straight-line
great-circle distance** of at least one facility. Not a drive-time isochrone,
not a road-network buffer, not a polygon intersection. Straight-line is what
``warehouse/facilities.py`` already uses to build the target, so the coverage
here and the ``enabled`` column mean the same thing at the same radius, and a
reader comparing the two is not comparing two different geometries.

Three consequences, each of which makes the white space reported here an
OVER-estimate or an UNDER-estimate in a direction worth naming:

* A straight line ignores rivers, mountains and the absence of a road. Real
  service areas are smaller than the disc, so this **under**-states white
  space.
* A ZCTA is reduced to its centroid. A 900-square-mile rural ZCTA is covered
  or not covered as a single unit even when half of it is 40 miles from the
  other half. At 45 miles this is small; at 8.3 miles it is not.
* Every facility class gets the SAME radius. A fulfilment centre serves
  hundreds of miles — Houde, Newberry and Seim (2023) use 150 miles for
  sortation — so giving one the same 45-mile disc as a delivery station
  **over**-states white space around the big nodes.

None of the three is corrected. Correcting any of them means choosing a
second unmeasured parameter, and the radius sweep already moves the answer
more than any of these would.

Everything is computed from one array
-------------------------------------
:func:`nearest_miles` collapses a network of N facilities into one distance
per ZCTA. Every radius after that is a comparison against that array, so a
seven-point radius sweep costs one pass over the facilities, not seven — and,
more usefully, the nearest-facility distance is itself a reportable number
that the covered/uncovered boolean throws away.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..cost.daganzo import haversine_miles

__all__ = ["by_cbsa", "nearest_miles", "summarise", "top_uncovered"]

#: Columns of the named list. A ZCTA code alone is not a place a planner can
#: act on; the county and CBSA names are what make a row inspectable.
NAMED_COLUMNS = ("zcta", "state", "county_name", "cbsa_title", "households",
                 "population", "miles_to_nearest_facility")

#: Not reachable by road from a mainland facility at any radius in this
#: sweep. They are genuinely uncovered and they are counted — but a
#: great-circle distance of 1,000 miles to San Juan is not a siting
#: opportunity a road network can close, so the total is reported with this
#: subtotal beside it rather than folded in silently.
OFFSHORE_STATES = ("PR", "VI", "GU", "AS", "MP", "HI", "AK")


def nearest_miles(zctas: pd.DataFrame, net: pd.DataFrame) -> np.ndarray:
    """Great-circle miles from each ZCTA centroid to its nearest facility.

    ``inf`` for every ZCTA when the network is empty, which is the honest
    answer and keeps the caller's ``<= radius`` comparison total.
    """
    zlat = zctas["latitude"].to_numpy(float)
    zlon = zctas["longitude"].to_numpy(float)
    best = np.full(len(zctas), np.inf)
    for lat, lon in zip(net["latitude"].to_numpy(float),
                        net["longitude"].to_numpy(float), strict=True):
        np.minimum(best, haversine_miles(zlat, zlon, lat, lon), out=best)
    return best


def summarise(zctas: pd.DataFrame, nearest: np.ndarray,
              miles: float) -> dict:
    """Covered and uncovered ZCTAs, households and population at one radius.

    ``households_covered_pct`` is the share of the panel's 128.7M households,
    which includes Puerto Rico. Excluding PR would raise every coverage
    figure and would be a choice about who counts as a household, so it is
    not made silently here; ``states_fully_uncovered`` names the places that
    choice would move.
    """
    covered = nearest <= miles
    hh = zctas["households"].to_numpy(float)
    pop = zctas["population"].to_numpy(float)
    total_hh = float(hh.sum())
    by_state = (zctas.assign(covered=covered)
                .groupby("state")["covered"].mean())
    offshore = zctas["state"].isin(OFFSHORE_STATES).to_numpy()
    return {
        "radius_miles": miles,
        "zctas_total": int(len(zctas)),
        "zctas_covered": int(covered.sum()),
        "zctas_uncovered": int((~covered).sum()),
        "zctas_uncovered_with_households": int(
            ((~covered) & (hh > 0)).sum()),
        "households_covered": float(hh[covered].sum()),
        "households_uncovered": float(hh[~covered].sum()),
        "households_covered_pct": round(
            100.0 * hh[covered].sum() / total_hh, 2) if total_hh else 0.0,
        "households_uncovered_offshore": float(hh[(~covered) & offshore]
                                               .sum()),
        "households_uncovered_mainland": float(hh[(~covered) & ~offshore]
                                               .sum()),
        "population_uncovered": float(pop[~covered].sum()),
        "median_miles_to_nearest_uncovered": round(
            float(np.median(nearest[~covered])), 1) if (~covered).any()
        else None,
        "states_fully_uncovered": sorted(by_state[by_state == 0].index),
        "states_fully_covered": sorted(by_state[by_state == 1].index),
    }


def top_uncovered(zctas: pd.DataFrame, nearest: np.ndarray, miles: float,
                  n: int = 30) -> list[dict]:
    """The uncovered ZCTAs with the most households, named and inspectable.

    Ranked by households, not by population or by distance: households is
    the unit a delivery network serves (one drop per address, not one per
    person) and it is the covariate the hazard stage already found
    significant at every radius in ``catchment_band.json``.
    """
    out = zctas.loc[nearest > miles].assign(
        miles_to_nearest_facility=np.round(nearest[nearest > miles], 1))
    out = out.sort_values(["households", "zcta"], ascending=[False, True])
    rows = out.head(n)[list(NAMED_COLUMNS)].to_dict("records")
    for r in rows:
        r["households"] = int(r["households"])
        r["population"] = int(r["population"])
        for key in ("county_name", "cbsa_title"):
            if pd.isna(r[key]):
                r[key] = None
    return rows


def by_cbsa(zctas: pd.DataFrame, nearest: np.ndarray,
            miles: float) -> pd.DataFrame:
    """Uncovered households per CBSA, descending.

    The ZCTA is the unit the analysis computes on; the CBSA is the unit a
    facility decision is actually taken in, and a list of 30 adjacent ZIP
    codes in one metro reads as 30 opportunities when it is one. ZCTAs in no
    CBSA (8,769 of them, rural) are dropped here and ONLY here — they are
    still in every ZCTA-level count above.
    """
    frame = zctas.assign(uncovered_households=np.where(
        nearest > miles, zctas["households"], 0.0))
    frame = frame.dropna(subset=["cbsa_code"])
    agg = (frame.groupby(["cbsa_code", "cbsa_title"], as_index=False)
           .agg(uncovered_households=("uncovered_households", "sum"),
                total_households=("households", "sum")))
    agg["uncovered_share"] = np.where(
        agg["total_households"] > 0,
        agg["uncovered_households"] / agg["total_households"], 0.0)
    return agg.sort_values(["uncovered_households", "cbsa_code"],
                           ascending=[False, True]).reset_index(drop=True)
