"""L4 — cost to serve, priced from the operator's REAL delivery stations.

    python -m siting_atlas.cost.station_runner
    python -m siting_atlas.cost.station_runner --year 2023 --quarter 4

The pilot runner (`cost.runner`) costs 2,333 ZCTAs in ten metros against 334
depots a p-median invented. This one costs every ZCTA within
`stations.CATCHMENT_MILES` of one of the 501 geocoded delivery stations that
actually exist, and reports a cost per STATION — a unit the invented network
could not produce, because you cannot quote an operating cost for a building
nobody built.

It writes NEW artefacts and touches none of the pilot's. The pilot is the
comparison and has to survive: every difference between the two is the depot
layer, since `StationCostModel` inherits the whole of `DaganzoCostModel`
except where the line-haul mile comes from.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from . import station_pilot, station_print
from . import station_report as rpt
from .params import SCENARIOS
from .stations import (
    CATCHMENT_MILES,
    MIN_TOUR_POINTS,
    StationCostModel,
    StationNetwork,
    catchment,
)

_log = get_logger("cost.station_runner")

REQUIRED = ("zcta", "households", "median_household_income", "land_area_sqmi",
            "latitude", "longitude", "wage_light_truck_driver",
            "diesel_usd_gal", "population", "cbsa_code", "cbsa_title")

NON_METRO = "(outside a CBSA)"


def national_slice(year: int, quarter: int) -> pd.DataFrame:
    """Every panel ZCTA for one period — no metro filter at all.

    The pilot's ten-metro restriction existed because the depot layer was
    solved per metro and a metro was the unit that had one. Real stations
    stand where they stand, so the geography is now decided by the catchment
    and by nothing else.
    """
    panel = pd.read_parquet(paths.PANEL)
    frame = panel[(panel["year"] == year)
                  & (panel["quarter"] == quarter)].copy()
    if frame.empty:
        raise ValueError(f"no panel rows for {year}Q{quarter}")

    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise KeyError(f"panel is missing {missing}; rebuild warehouse.panel")

    before = len(frame)
    frame = frame[frame["households"].fillna(0) > 0]
    if before != len(frame):
        _log.info("dropped %d ZCTA(s) with no households", before - len(frame))
    frame["metro_label"] = frame["cbsa_title"].fillna(NON_METRO)
    return frame.reset_index(drop=True)


def build_catchment(frame: pd.DataFrame, network: StationNetwork,
                    radius: float = CATCHMENT_MILES) -> tuple:
    """Frame restricted to the catchment, plus a coverage record.

    Two exclusions happen here and both are counted rather than hidden:
    outside the radius, and inside it with no driver wage. The wage is an
    OEWS metro-area figure and some ZCTAs in the catchment sit outside every
    metro area OEWS publishes. There is no imputation: inventing a wage would
    be inventing the 66% of the bill that labour carries, which is the exact
    mistake this module exists to stop making on the depot side.
    """
    assigned = network.assign(frame)
    inside = catchment(assigned, radius)
    near = frame[inside].join(assigned[["station_id", "station_miles"]])

    wage_ok = near["wage_light_truck_driver"].notna()
    costed = near[wage_ok].reset_index(drop=True)
    total_hh = float(frame["households"].sum())
    cover = {
        "panel_zctas": int(len(frame)),
        "panel_households": total_hh,
        "in_catchment_zctas": int(inside.sum()),
        "in_catchment_households": float(near["households"].sum()),
        "dropped_no_driver_wage_zctas": int((~wage_ok).sum()),
        "dropped_no_driver_wage_households":
            float(near.loc[~wage_ok, "households"].sum()),
        "costed_zctas": int(len(costed)),
        "costed_households": float(costed["households"].sum()),
        "costed_household_share":
            float(costed["households"].sum() / total_hh),
        "catchment_household_share":
            float(near["households"].sum() / total_hh),
        "median_households_per_sqmi": float(
            (costed["households"]
             / costed["land_area_sqmi"].where(
                 costed["land_area_sqmi"] > 0)).median()),
        "stations_with_at_least_one_zcta":
            int(costed["station_id"].nunique()),
        "stations_with_no_zcta":
            int(len(network.stations) - costed["station_id"].nunique()),
    }
    _log.info("catchment %.0f mi: %d of %d ZCTAs, %.1f%% of US households",
              radius, cover["costed_zctas"], cover["panel_zctas"],
              100 * cover["costed_household_share"])
    return costed, cover, assigned


def aggregate_stations(result: pd.DataFrame,
                       stations: pd.DataFrame) -> pd.DataFrame:
    """One row per station: the spread of cost across the ZCTAs it serves.

    Median and IQR, not a mean. The distribution of cost per parcel inside a
    catchment is right-skewed — a handful of sparse fringe ZCTAs sit far above
    the rest — and a mean would report those rather than the station's typical
    ZIP. The IQR is carried so a reader can see how wide the catchment's
    economics actually are instead of trusting one number.
    """
    g = result.groupby("station_id", dropna=True)
    out = pd.DataFrame({
        "zctas": g["cost_per_parcel"].size(),
        "cost_per_parcel_median": g["cost_per_parcel"].median(),
        "cost_per_parcel_q1": g["cost_per_parcel"].quantile(0.25),
        "cost_per_parcel_q3": g["cost_per_parcel"].quantile(0.75),
        "cost_per_parcel_min": g["cost_per_parcel"].min(),
        "cost_per_parcel_max": g["cost_per_parcel"].max(),
        "daily_parcels": g["daily_parcels"].sum(),
        "daily_stops": g["daily_stops"].sum(),
        "daily_cost_usd": g["daily_cost_usd"].sum(),
        "households": g["households"].sum(),
        "median_linehaul_miles": g["linehaul_miles"].median(),
        "median_stop_density": g["stop_density_per_sqmi"].median(),
    }).reset_index()
    out["cost_per_parcel_iqr"] = (out["cost_per_parcel_q3"]
                                  - out["cost_per_parcel_q1"])
    # Dollars over parcels, which is additive; the median above is not.
    out["cost_per_parcel_pooled"] = (out["daily_cost_usd"]
                                     / out["daily_parcels"])

    meta = stations.rename(columns={"cbsa_title": "station_cbsa_title"})
    out = out.merge(meta[["station_id", "station_lat", "station_lon", "city",
                          "state", "station_cbsa_title", "status",
                          "operator", "facility_type"]],
                    on="station_id", how="left")
    # A station whose own CBSA is unknown inherits the modal metro of the
    # ZCTAs it serves, so the by-metro table never silently loses one.
    modal = (result.groupby("station_id")["metro_label"]
                   .agg(lambda s: s.mode().iat[0] if len(s.mode()) else
                        NON_METRO))
    out["metro"] = (out["station_cbsa_title"]
                    .fillna(out["station_id"].map(modal))
                    .fillna(NON_METRO))
    return out.sort_values("cost_per_parcel_median").reset_index(drop=True)


def run(year: int, quarter: int, scenario: str, frame: pd.DataFrame) -> dict:
    """Cost the catchment for one scenario and write both parquets."""
    params = SCENARIOS[scenario]
    model = StationCostModel(params, frame["station_miles"])
    result = model.evaluate(frame)
    result = result.join(frame[["station_id", "station_miles", "metro_label",
                                "state", "cbsa_code", "population",
                                "households", "land_area_sqmi"]])
    result = result.sort_values("cost_per_parcel").reset_index(drop=True)
    result.insert(0, "rank", result.index + 1)

    tag = f"{year}q{quarter}_{scenario}"
    zpath = paths.TABLES / f"cost_to_serve_station_{tag}.parquet"
    result.to_parquet(zpath, index=False)
    artefact(zpath, rows=len(result), scenario=scenario)

    by_station = aggregate_stations(result, model_stations())
    spath = paths.TABLES / f"cost_by_station_{tag}.parquet"
    by_station.to_parquet(spath, index=False)
    artefact(spath, rows=len(by_station), scenario=scenario)

    cost = result["cost_per_parcel"]
    metric(f"station_cost_median_{scenario}", round(cost.median(), 4))
    summary = {
        "scenario": scenario, "year": year, "quarter": quarter,
        "zctas": int(len(result)), "stations": int(len(by_station)),
        "zcta_table": paths.rel(zpath), "station_table": paths.rel(spath),
        "parameters": params.summary(),
        "median_cost_per_parcel": float(cost.median()),
        "p10": float(cost.quantile(0.10)),
        "p25": float(cost.quantile(0.25)),
        "p75": float(cost.quantile(0.75)),
        "p90": float(cost.quantile(0.90)),
        "pooled_cost_per_parcel": float(result["daily_cost_usd"].sum()
                                        / result["daily_parcels"].sum()),
        "total_daily_cost_usd": float(result["daily_cost_usd"].sum()),
        "total_daily_parcels": float(result["daily_parcels"].sum()),
        "total_vans": int(np.ceil(result["van_days"].sum())),
        "median_linehaul_miles": float(result["linehaul_miles"].median()),
        "station_median_cost_median":
            float(by_station["cost_per_parcel_median"].median()),
        "station_median_cost_iqr":
            float(by_station["cost_per_parcel_iqr"].median()),
        "decomposition": rpt.decomposition(result),
        "tour_floors": rpt.tour_floors(result, params.stops_per_tour,
                                       MIN_TOUR_POINTS),
        "extremes": rpt.extremes(by_station),
    }
    return summary | {"result": result, "by_station": by_station}


def counterfactual_costs(frame: pd.DataFrame,
                         network: StationNetwork) -> pd.DataFrame:
    """Baseline costs with every ZCTA's own station masked out.

    NOT a scenario and never written to a parquet — it is the control for one
    test. `station_report.decile_test` explains why: with the real facilities
    as the depot layer, a facility's own ZCTA is cheap because the facility is
    in it, so the published frame cannot answer "do facilities sit in cheap
    ZCTAs". Here the line haul is measured to the nearest station OUTSIDE the
    ZCTA, which prices the place as it would be if nothing had been built
    there.
    """
    away = network.assign(frame, exclude_own_zcta=True)
    model = StationCostModel(SCENARIOS["baseline"], away["station_miles"])
    out = model.evaluate(frame)
    return out.join(frame[["metro_label", "households"]])


_STATIONS: pd.DataFrame | None = None


def model_stations() -> pd.DataFrame:
    """The station table, loaded once per process."""
    global _STATIONS
    if _STATIONS is None:
        _STATIONS = StationNetwork.load().stations
    return _STATIONS


def main() -> int:
    """CLI entry point for the station-based cost model."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--quarter", type=int, default=4)
    ap.add_argument("--radius", type=float, default=CATCHMENT_MILES)
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L4", f"cost by station {args.year}Q{args.quarter}"):
        with step("catchment"):
            frame = national_slice(args.year, args.quarter)
            network = StationNetwork(model_stations())
            costed, cover, assigned = build_catchment(
                frame, network, args.radius)
            sweep = rpt.radius_sweep(frame, assigned)
        results = {}
        for name in sorted(SCENARIOS):
            with step(f"cost:{name}"):
                results[name] = run(args.year, args.quarter, name, costed)
        with step("counterfactual"):
            loo = counterfactual_costs(costed, network)

    base = results["baseline"]
    payload = {
        "catchment_miles": args.radius,
        "stations": rpt.station_census(network.stations),
        "coverage": cover,
        "radius_sweep": sweep,
        "scenarios": {k: {kk: vv for kk, vv in v.items()
                          if kk not in ("result", "by_station")}
                      for k, v in results.items()},
        "sensitivity": rpt.sensitivity(results),
        "by_metro": rpt.by_metro(base["by_station"]),
        "decile_test": rpt.decile_test(base["result"], network.stations, loo),
        "pilot_comparison": station_pilot.pilot_comparison(base),
    }
    out = write_json(paths.METRICS / "cost_by_station.json", payload)
    artefact(out, scenarios=len(results))
    station_print.print_report(payload, base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
