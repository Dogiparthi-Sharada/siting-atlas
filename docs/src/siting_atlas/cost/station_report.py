"""Diagnostics for the station-based cost model.

Every figure the write-up needs is computed here, at runtime, from the frame
that was just produced — never read back from prose. The three that exist to
BOUND the claim rather than support it (`tour_floors`, `radius_sweep`,
`decile_test`) are computed on the same footing as the headline, so a run
cannot report the headline without also reporting what limits it.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from .daganzo import DaganzoCostModel
from .params import BASELINE
from .stations import STATION_FILE

_log = get_logger("cost.station_report")

COMPONENTS = (("service_time", "cost_service_time"),
              ("vehicle", "cost_vehicle"),
              ("drive_time", "cost_drive_time"),
              ("distance", "cost_distance"))

#: Radii the catchment choice is audited against. 15 is the one used; the
#: rest exist so the choice is visibly a choice.
SWEEP_MILES = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 45.0)

def station_census(stations: pd.DataFrame) -> dict:
    """What the depot layer is made of, and what was left out of it."""
    with open(STATION_FILE, encoding="utf-8") as fh:
        raw = sum(1 for _ in fh) - 1
    out = {
        "facility_rows": int(raw),
        "geocoded_used": int(len(stations)),
        "excluded_zcta_centroid_fallback": int(raw - len(stations)),
        "distinct_coordinates": int(
            stations[["station_lat", "station_lon"]]
            .drop_duplicates().shape[0]),
    }
    for col in ("operator", "facility_type", "status"):
        if col in stations.columns:
            out[f"by_{col}"] = {str(k): int(v) for k, v in
                                stations[col].value_counts(
                                    dropna=False).items()}
    return out


def decomposition(result: pd.DataFrame) -> dict:
    """Stop-weighted cost shares — dollars over doors, which is additive.

    The identity `runner.py:156` was rebuilt around after two bugs: never
    divide a per-stop component by a per-parcel total, and never average
    medians. Rows with any missing component are dropped so a NaN cannot
    contribute doors to the denominator without dollars to the numerator.
    """
    cols = [c for _, c in COMPONENTS] + ["cost_per_stop", "daily_stops",
                                         "daily_parcels", "daily_cost_usd"]
    costed = result[result[cols].notna().all(axis=1)]
    stops = costed["daily_stops"]
    total = float((costed["cost_per_stop"] * stops).sum() / stops.sum())
    out = {"excluded_incomplete_rows": int(len(result) - len(costed)),
           "cost_per_stop": total,
           "parcels_per_stop_realised":
               float(costed["daily_parcels"].sum() / stops.sum()),
           "pooled_cost_per_parcel":
               float(costed["daily_cost_usd"].sum()
                     / costed["daily_parcels"].sum())}
    for label, col in COMPONENTS:
        usd = float((costed[col] * stops).sum() / stops.sum())
        out[f"{label}_usd_per_stop"] = usd
        out[f"{label}_share_pct"] = 100.0 * usd / total
    return out


def tour_floors(result: pd.DataFrame, stops_per_tour: float,
                min_points: int) -> dict:
    """How much of the costed set is outside the approximation's regime.

    Two different objections, kept apart:

    * Below `stops_per_tour` a ZCTA cannot fill one van, so the line-haul
      term ``2L/C`` charges it a share of a tour it does not have. The model
      is still coherent — the van finishes its round in a neighbouring ZCTA —
      but the per-ZCTA reading is a marginal one, not a standalone route.
    * Below `min_points` the BHH asymptote `daganzo.py` rests on is simply
      outside its stated regime and the local term is not trustworthy at all.
    """
    stops = result["daily_stops"]
    n = len(result)
    below_tour = stops < stops_per_tour
    below_bhh = stops < min_points
    return {
        "stops_per_tour": float(stops_per_tour),
        "min_tour_points": int(min_points),
        "zctas": int(n),
        "below_one_tour": int(below_tour.sum()),
        "below_one_tour_pct": 100.0 * float(below_tour.mean()),
        "below_one_tour_household_pct": 100.0 * float(
            result.loc[below_tour, "households"].sum()
            / result["households"].sum()),
        "below_bhh_floor": int(below_bhh.sum()),
        "below_bhh_floor_pct": 100.0 * float(below_bhh.mean()),
        "below_bhh_floor_household_pct": 100.0 * float(
            result.loc[below_bhh, "households"].sum()
            / result["households"].sum()),
        "median_daily_stops": float(stops.median()),
    }


def radius_sweep(frame: pd.DataFrame, assigned: pd.DataFrame,
                 radii=SWEEP_MILES) -> list[dict]:
    """What the catchment radius buys and what it costs, per radius.

    The catchment choice is made on this table rather than in a footnote.
    Two densities are reported and they are NOT interchangeable: households
    per square mile is a property of the place, stops per square mile is the
    delta the 1/sqrt(delta) term actually consumes, and the two differ by the
    parcels-per-household and consolidation factors. The pilot's published
    density, 475, is a STOPS figure; comparing a households figure to it
    overstates the catchment by roughly 2.3x.

    Every wider radius adds ZCTAs that are sparser than the ones already in,
    monotonically, because the added ring is further from the volume the
    operator built for. The radius is therefore a straight trade of coverage
    against the regime the approximation is valid in.
    """
    work = frame.join(assigned[["station_miles"]])
    land = work["land_area_sqmi"].where(work["land_area_sqmi"] > 0)
    hh_dens = work["households"] / land
    stops = DaganzoCostModel(BASELINE).daily_stops(work)
    stop_dens = stops / land
    total = float(work["households"].sum())
    rows = []
    for r in radii:
        m = work["station_miles"].le(r).fillna(False)
        rows.append({
            "radius_miles": float(r),
            "zctas": int(m.sum()),
            "households": float(work.loc[m, "households"].sum()),
            "household_share_pct": 100.0 * float(
                work.loc[m, "households"].sum() / total),
            "median_households_per_sqmi": float(hh_dens[m].median()),
            "median_stops_per_sqmi": float(stop_dens[m].median()),
            "stations_used": int(
                assigned.loc[m[m].index, "station_id"].nunique()),
        })
    return rows


def extremes(by_station: pd.DataFrame, k: int = 10) -> dict:
    """Cheapest and dearest stations by the median cost inside a catchment."""
    cols = ["station_id", "city", "state", "metro", "zctas",
            "cost_per_parcel_median", "cost_per_parcel_iqr",
            "median_linehaul_miles", "median_stop_density", "daily_parcels"]
    s = by_station.sort_values("cost_per_parcel_median")

    def pack(df: pd.DataFrame) -> list[dict]:
        """Rows as plain dicts, JSON-safe."""
        return [{c: (v.item() if hasattr(v, "item") else v)
                 for c, v in row.items()}
                for _, row in df[cols].iterrows()]

    return {"cheapest": pack(s.head(k)), "dearest": pack(s.tail(k)[::-1]),
            "spread_usd": float(s["cost_per_parcel_median"].iat[-1]
                                - s["cost_per_parcel_median"].iat[0])}


def by_metro(by_station: pd.DataFrame) -> list[dict]:
    """Station economics rolled up to the metro the station sits in."""
    rows = []
    for name, g in by_station.groupby("metro"):
        g = g.sort_values("cost_per_parcel_median")
        rows.append({
            "metro": str(name),
            "stations": int(len(g)),
            "zctas": int(g["zctas"].sum()),
            "median_station_cost": float(g["cost_per_parcel_median"]
                                         .median()),
            "cheapest_station": str(g["station_id"].iat[0]),
            "cheapest_station_cost": float(g["cost_per_parcel_median"]
                                           .iat[0]),
            "dearest_station": str(g["station_id"].iat[-1]),
            "dearest_station_cost": float(g["cost_per_parcel_median"]
                                          .iat[-1]),
            "daily_parcels": float(g["daily_parcels"].sum()),
        })
    return sorted(rows, key=lambda r: r["median_station_cost"])


def _rank_in_metro(result: pd.DataFrame) -> pd.DataFrame:
    """Percentile rank of cost within the ZCTA's own metro."""
    out = result[["zcta", "metro_label", "cost_per_parcel",
                  "linehaul_miles"]].copy()
    out["pct_rank"] = (out.groupby("metro_label")["cost_per_parcel"]
                          .rank(pct=True))
    return out


def _decile_stats(rows: pd.DataFrame, n_total: int) -> dict:
    """The numbers the paper's claim is made of, plus what moved them.

    `median_linehaul_miles` is carried because it is how a reader checks
    whether the leave-one-out mask actually bit. Masking a facility's own
    station does nothing for a facility whose neighbour's station is two
    miles away, and in a dense metro that is the normal case.
    """
    pr = rows["pct_rank"]
    return {
        "facilities_matched": int(len(pr)),
        "facilities_considered": int(n_total),
        "in_cheapest_decile": int((pr <= 0.10).sum()),
        "in_cheapest_decile_pct": 100.0 * float((pr <= 0.10).mean()),
        "in_cheapest_quartile_pct": 100.0 * float((pr <= 0.25).mean()),
        "median_pct_rank": float(pr.median()),
        "median_linehaul_miles": float(rows["linehaul_miles"].median()),
    }


def _decile_arm(result: pd.DataFrame, stations: pd.DataFrame) -> dict:
    """The cheapest-decile statistics for one cost frame.

    Join each facility to the ZCTA it stands in, rank that ZCTA's cost per
    parcel against the other costed ZCTAs of the same metro, count how many
    land in the cheapest tenth. Two facility sets: all 501 real stations, and
    the original 43 pilot facilities re-ranked on THESE costs, which separates
    the change of depot layer from the change of universe.
    """
    ranked = _rank_in_metro(result)
    ranked = ranked[ranked["metro_label"].notna()]
    by_zcta = ranked.set_index(ranked["zcta"].astype(str))

    sid = stations.dropna(subset=["station_zcta"]).copy()
    sid["z"] = sid["station_zcta"].astype(str).str.zfill(5)
    hit = sid[sid["z"].isin(by_zcta.index)]
    out = {"stations": _decile_stats(by_zcta.loc[hit["z"]], len(stations))}

    fac = paths.EXTERNAL / "facility_panel" / "facilities.csv"
    if fac.exists():
        f = pd.read_csv(fac, dtype={"zip": str})
        z = f["zip"].astype(str).str.zfill(5)
        z = z[z.isin(by_zcta.index)]
        if len(z):
            out["pilot_facilities"] = _decile_stats(by_zcta.loc[z], len(f))
    return out


def decile_test(result: pd.DataFrame, stations: pd.DataFrame,
                counterfactual: pd.DataFrame | None = None) -> dict:
    """Recompute "zero facilities sit in their metro's cheapest decile".

    THE TEST IS NOT IDENTIFIED ON THE HEADLINE COST FRAME, and that is the
    finding. Once the depot layer IS the facility panel, a ZCTA that contains
    a station has a line haul of roughly zero because the station is inside
    it. Line haul is 2L/C per stop and drive plus distance is ~19% of the
    bill, so the model makes every facility's own ZCTA cheap by construction.
    Ranking facilities on that frame measures the circularity, not the siting.

    So two arms are returned and only the second answers the question:

    ``as_costed`` — ranks against the published frame. Reported so the
    circularity is visible and quantified rather than asserted.
    ``leave_one_out`` — ranks against a frame in which every ZCTA's line haul
    is measured to the nearest station OUTSIDE it (`StationNetwork.assign`
    with ``exclude_own_zcta=True``). This is the counterfactual the claim
    needs: how expensive would this place be if the operator had not built
    here?

    A second caveat the pilot did not have: the reference set is the metro's
    COSTED ZCTAs, i.e. those inside the catchment. The catchment trims a
    metro's sparse outer ring, which is its dear end, so every facility's
    percentile rank is pushed UP relative to a whole-metro ranking.
    """
    out = {"as_costed": _decile_arm(result, stations)}
    if counterfactual is not None:
        out["leave_one_out"] = _decile_arm(counterfactual, stations)
    return out


def sensitivity(results: dict) -> dict:
    """Each scenario's median against the baseline's."""
    base = results["baseline"]["median_cost_per_parcel"]
    out = {"baseline_median": base}
    pct = {}
    for name, r in results.items():
        m = r["median_cost_per_parcel"]
        pct[name] = 100.0 * (m / base - 1.0)
        out[name] = {"median": m, "pct_vs_baseline": pct[name]}
    out["span_pct"] = [min(pct.values()), max(pct.values())]
    return out
