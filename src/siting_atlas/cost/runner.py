"""L4 — run the cost model over the pilot and write the ranked output.

    python -m siting_atlas.cost.runner
    python -m siting_atlas.cost.runner --year 2024 --scenario congested

This stage needs no target variable, which is why it runs today while the
hazard model waits on the facility panel. It answers "what would it cost to
serve this ZIP code?" — an engineering-economics question — and not "will the
operator choose to", which is the causal question the panel is blocking.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.metros import REGISTRY
from ..common.trace import artefact, metric, step, traced_layer
from .daganzo import DaganzoCostModel
from .params import SCENARIOS

_log = get_logger("cost.runner")

REQUIRED = ("zcta", "households", "median_household_income", "land_area_sqmi",
            "latitude", "longitude", "wage_light_truck_driver",
            "diesel_usd_gal", "population", "cbsa_code")


def pilot_slice(year: int, quarter: int) -> pd.DataFrame:
    """One row per pilot ZCTA for the requested period."""
    delineation = pd.read_parquet(paths.INTERIM / "cbsa_county.parquet")
    xwalk = pd.read_parquet(paths.INTERIM / "zcta_county.parquet")
    counties = set(REGISTRY.counties(delineation)["county_geoid"])
    pilot = set(xwalk[xwalk["county_geoid"].isin(counties)]["zcta"])

    panel = pd.read_parquet(paths.PANEL)
    frame = panel[(panel["zcta"].isin(pilot)) & (panel["year"] == year)
                  & (panel["quarter"] == quarter)].copy()
    if frame.empty:
        raise ValueError(f"no pilot rows for {year}Q{quarter}")

    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise KeyError(f"panel is missing {missing}; rebuild warehouse.panel")

    # A ZCTA with no households has nothing to deliver to. Keeping it would
    # divide by zero and give it an infinite cost per parcel, which an
    # ascending sort parks at the BOTTOM of the ranking, dressed as the most
    # expensive place in the pilot rather than as a place with no demand.
    before = len(frame)
    frame = frame[frame["households"].fillna(0) > 0]
    if before != len(frame):
        _log.info("dropped %d ZCTA(s) with no households", before - len(frame))

    frame = frame.merge(
        REGISTRY.counties(delineation)[["county_geoid", "metro_label"]]
                .drop_duplicates("county_geoid"),
        on="county_geoid", how="left")
    return frame.reset_index(drop=True)


def run(year: int, quarter: int, scenario: str) -> dict:
    """Cost every pilot ZCTA for one period under one scenario.

    Writes the ranked parquet to outputs/tables/ and returns a summary dict
    that also carries the frame itself under "result", so the caller can
    print a report without re-reading what was just written.
    """
    frame = pilot_slice(year, quarter)
    model = DaganzoCostModel(SCENARIOS[scenario])

    result = model.evaluate(frame)
    result = result.join(frame[["metro_label", "state", "population",
                                "land_area_sqmi"]])
    result = result.sort_values("cost_per_parcel").reset_index(drop=True)
    result.insert(0, "rank", result.index + 1)

    out = paths.TABLES / f"cost_to_serve_{year}q{quarter}_{scenario}.parquet"
    result.to_parquet(out, index=False)
    artefact(out, rows=len(result), scenario=scenario)

    metric("cost_median_usd", round(result["cost_per_parcel"].median(), 4))
    metric("cost_p10_usd", round(result["cost_per_parcel"].quantile(.10), 4))
    metric("cost_p90_usd", round(result["cost_per_parcel"].quantile(.90), 4))
    metric("cost_zctas", len(result))

    return {"scenario": scenario, "year": year, "quarter": quarter,
            "zctas": len(result), "path": paths.rel(out),
            "parameters": SCENARIOS[scenario].summary(),
            "median_cost_per_parcel":
                float(result["cost_per_parcel"].median()),
            "p10": float(result["cost_per_parcel"].quantile(.10)),
            "p90": float(result["cost_per_parcel"].quantile(.90)),
            "total_daily_cost_usd": float(result["daily_cost_usd"].sum()),
            # Ceil at the NETWORK level, which is where whole vans are bought.
            "total_vans": int(np.ceil(result["van_days"].sum())),
            "result": result}


def _print_report(r: dict) -> None:
    """Print the human-readable cost report for one scenario result."""
    res = r["result"]
    w = 78
    print("\n" + "=" * w)
    print(f"  COST TO SERVE  -  {r['year']}Q{r['quarter']}  -  "
          f"scenario: {r['scenario']}")
    print("=" * w)
    print(f"  {r['zctas']:,} pilot ZCTAs   "
          f"median ${r['median_cost_per_parcel']:.2f}/parcel   "
          f"p10 ${r['p10']:.2f}  p90 ${r['p90']:.2f}")
    print(f"  {r['total_vans']:,} vans/day   "
          f"${r['total_daily_cost_usd']:,.0f}/day total")

    print("\n  CHEAPEST 10 (dense, close to the depot)")
    print(f"  {'#':>4} {'zcta':6} {'metro':24} {'$/parcel':>9} "
          f"{'stops/sqmi':>11} {'mi/stop':>8}")
    for _, x in res.head(10).iterrows():
        print(f"  {x['rank']:>4} {x['zcta']:6} "
              f"{str(x['metro_label'])[:24]:24} "
              f"{x['cost_per_parcel']:>9.2f} "
              f"{x['stop_density_per_sqmi']:>11,.0f} "
              f"{x['miles_per_stop']:>8.3f}")

    print("\n  MOST EXPENSIVE 10 (sparse, or far out)")
    for _, x in res.tail(10).iterrows():
        print(f"  {x['rank']:>4} {x['zcta']:6} "
              f"{str(x['metro_label'])[:24]:24} "
              f"{x['cost_per_parcel']:>9.2f} "
              f"{x['stop_density_per_sqmi']:>11,.1f} "
              f"{x['miles_per_stop']:>8.3f}")

    print("\n  BY METRO")
    print(f"  {'metro':26} {'zctas':>6} {'median $':>9} {'min':>7} {'max':>8}")
    by = (res.groupby("metro_label")["cost_per_parcel"]
             .agg(["count", "median", "min", "max"])
             .sort_values("median"))
    for name, x in by.iterrows():
        print(f"  {str(name)[:26]:26} {int(x['count']):>6,} "
              f"{x['median']:>9.2f} {x['min']:>7.2f} {x['max']:>8.2f}")

    print("\n  WHERE THE MONEY GOES (per stop, whole pilot)")
    comp = [("driver time at the door", "cost_service_time"),
            ("driver time driving", "cost_drive_time"),
            ("fuel and wear", "cost_distance"),
            ("vehicle lease", "cost_vehicle")]
    # Two traps have been sprung in this block, so it is now built the one way
    # that is arithmetically closed: every figure is total dollars divided by
    # total doors, which IS additive.
    #   1. Components are per STOP and were divided by cost per PARCEL, so the
    #      shares summed to 140%.
    #   2. Medians are not additive. Four component medians against a median
    #      cost per stop summed to 99.0% pooled across metros - and to exactly
    #      100% within any single metro, which is why it stayed hidden.
    # Rows with any missing component are dropped up front rather than left in.
    # Series.sum() skips NaN, so an un-costed ZCTA left in the frame would
    # contribute its doors to the denominator and no dollars to the numerator,
    # shrinking that one segment by a plausible-looking amount.
    cols = [c for _, c in comp] + ["cost_per_stop", "daily_cost_usd",
                                   "daily_parcels", "daily_stops"]
    costed = res[res[cols].notna().all(axis=1)]
    if len(costed) < len(res):
        print(f"  ({len(res) - len(costed)} ZCTA(s) with an incomplete cost "
              f"breakdown excluded from this table)")
    stops = costed["daily_stops"]

    def per_stop(col: str) -> float:
        """Stops-weighted mean of a per-stop column: dollars over doors."""
        return float((costed[col] * stops).sum() / stops.sum())

    total = per_stop("cost_per_stop")
    print(f"  {'(a stop carries':26}  "
          f"{costed['daily_parcels'].sum() / stops.sum():.1f} "
          f"parcels)")
    for label, col in comp:
        v = per_stop(col)
        bar = "#" * int(round(v / total * 40))
        print(f"  {label:26} ${v:>5.2f}  {v/total*100:>4.1f}%  {bar}")
    print(f"  {'= cost per stop':26} ${total:>5.2f}")
    # Same identity one level down: total dollars over total parcels. Not the
    # median cost per parcel, which belongs to no particular ZCTA here.
    per_parcel = (costed["daily_cost_usd"].sum()
                  / costed["daily_parcels"].sum())
    print(f"  {'-> cost per parcel':26} ${per_parcel:>5.2f}")
    print("=" * w)


def main() -> int:
    """CLI entry point for L4 cost-to-serve."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--quarter", type=int, default=4)
    ap.add_argument("--scenario", default="baseline",
                    choices=sorted(SCENARIOS))
    ap.add_argument("--all-scenarios", action="store_true",
                    help="run every scenario and print the sensitivity table")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L4", f"cost to serve {args.year}Q{args.quarter}"):
        names = sorted(SCENARIOS) if args.all_scenarios else [args.scenario]
        results = {}
        for name in names:
            with step(f"cost:{name}"):
                results[name] = run(args.year, args.quarter, name)

    _print_report(results[args.scenario if not args.all_scenarios
                          else "baseline"])

    if args.all_scenarios:
        print("\n  SENSITIVITY  (median $/parcel)")
        base = results["baseline"]["median_cost_per_parcel"]
        for name in sorted(results, key=lambda n:
                           results[n]["median_cost_per_parcel"]):
            m = results[name]["median_cost_per_parcel"]
            print(f"  {name:20} ${m:>5.2f}   {(m/base - 1)*100:>+6.1f}% "
                  f"vs baseline")

    write_json(paths.METRICS / "cost_report.json",
               {k: {kk: vv for kk, vv in v.items() if kk != "result"}
                for k, v in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
