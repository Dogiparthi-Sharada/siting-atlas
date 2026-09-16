"""Human-readable report for the station-based cost model.

Printing only. Every number here was computed in `station_report` and written
to `outputs/metrics/cost_by_station.json` before this module saw it, so the
console and the artefact cannot disagree.
"""

from __future__ import annotations

W = 78


def _rule(title: str = "") -> None:
    """A section rule, optionally titled."""
    print("=" * W if not title else f"\n{'=' * W}\n  {title}\n{'=' * W}")


def _coverage(p: dict) -> None:
    """Who is in the costed set and who was dropped on the way in."""
    c, s = p["coverage"], p["stations"]
    print(f"  depot layer   {s['geocoded_used']} real delivery stations "
          f"({s['excluded_zcta_centroid_fallback']} of "
          f"{s['facility_rows']} panel rows excluded: ZCTA-centroid "
          f"fallback, not a building)")
    print(f"  catchment     {p['catchment_miles']:.0f} great-circle miles")
    print(f"  costed        {c['costed_zctas']:,} ZCTAs of "
          f"{c['panel_zctas']:,} in the panel   "
          f"{c['costed_household_share'] * 100:.1f}% of US households")
    print(f"  dropped       {c['dropped_no_driver_wage_zctas']:,} in "
          f"catchment with no OEWS driver wage "
          f"({c['dropped_no_driver_wage_households'] / 1e3:,.0f}k "
          f"households)")
    print(f"  density       median "
          f"{c['median_households_per_sqmi']:,.0f} households/sq mi")
    print(f"  stations used {c['stations_with_at_least_one_zcta']} of "
          f"{s['geocoded_used']} have at least one ZCTA")


def _headline(p: dict) -> None:
    """Median cost and how it moved against the pilot."""
    b = p["scenarios"]["baseline"]
    pc = p["pilot_comparison"]
    print(f"\n  median ${b['median_cost_per_parcel']:.4f}/parcel   "
          f"p10 ${b['p10']:.4f}  p90 ${b['p90']:.4f}")
    print(f"  pooled ${b['pooled_cost_per_parcel']:.4f}/parcel   "
          f"{b['total_daily_parcels'] / 1e6:.2f}M parcels/day   "
          f"${b['total_daily_cost_usd'] / 1e6:.1f}M/day   "
          f"{b['total_vans']:,} vans")
    if pc.get("available"):
        print(f"  pilot  ${pc['median_cost_per_parcel']:.4f} over "
              f"{pc['zctas']:,} ZCTAs  ->  "
              f"{pc['delta_median_pct']:+.1f}%")


def _decomposition(p: dict) -> None:
    """Where the money goes, beside the pilot's shares."""
    d = p["scenarios"]["baseline"]["decomposition"]
    pc = p["pilot_comparison"]
    print(f"\n  WHERE THE MONEY GOES (per stop; a stop carries "
          f"{d['parcels_per_stop_realised']:.1f} parcels)")
    print(f"  {'component':18} {'$/stop':>8} {'share':>8} {'pilot':>8}")
    for label in ("service_time", "vehicle", "drive_time", "distance"):
        ref = pc.get(f"{label}_share_pct")
        print(f"  {label:18} {d[f'{label}_usd_per_stop']:>8.4f} "
              f"{d[f'{label}_share_pct']:>7.2f}% "
              f"{(f'{ref:.2f}%' if ref is not None else '-'):>8}")
    print(f"  {'= cost per stop':18} {d['cost_per_stop']:>8.4f}")


def _sensitivity(p: dict) -> None:
    """The five-scenario span, beside the pilot's."""
    s = p["sensitivity"]
    pc = p["pilot_comparison"]
    print("\n  SENSITIVITY  (median $/parcel)")
    names = [k for k in s if isinstance(s[k], dict)]
    for name in sorted(names, key=lambda n: s[n]["median"]):
        ref = (pc.get("scenario_pct") or {}).get(name)
        print(f"  {name:20} ${s[name]['median']:>7.4f}  "
              f"{s[name]['pct_vs_baseline']:>+6.1f}%   pilot "
              f"{(f'{ref:+.1f}%' if ref is not None else '   -'):>7}")
    lo, hi = s["span_pct"]
    print(f"  span {lo:+.1f}% to {hi:+.1f}%", end="")
    if pc.get("span_pct"):
        print(f"   (pilot {pc['span_pct'][0]:+.1f}% to "
              f"{pc['span_pct'][1]:+.1f}%)")
    else:
        print()


def _floors(p: dict) -> None:
    """What share of the costed set is outside the model's regime."""
    t = p["scenarios"]["baseline"]["tour_floors"]
    pc = p["pilot_comparison"]
    print("\n  WHAT THE MODEL CANNOT CLAIM")
    print(f"  below {t['stops_per_tour']:.0f} stops (one van-tour)   "
          f"{t['below_one_tour']:,} ZCTAs  "
          f"{t['below_one_tour_pct']:.2f}%  "
          f"{t['below_one_tour_household_pct']:.2f}% of catchment households"
          f"   pilot {pc.get('below_one_tour_pct', float('nan')):.2f}%")
    print(f"  below n={t['min_tour_points']} (Larson & Odoni BHH floor) "
          f"{t['below_bhh_floor']:,} ZCTAs  "
          f"{t['below_bhh_floor_pct']:.2f}%  "
          f"{t['below_bhh_floor_household_pct']:.2f}% of households"
          f"   pilot {pc.get('below_bhh_floor_pct', float('nan')):.2f}%")


def _radius(p: dict) -> None:
    """The catchment choice, audited against its alternatives."""
    pc = p["pilot_comparison"]
    print("\n  CATCHMENT RADIUS SWEEP")
    if pc.get("available"):
        print(f"  pilot reference: {pc['median_households_per_sqmi']:,.0f} "
              f"households/sq mi, {pc['median_stops_per_sqmi']:,.0f} "
              f"stops/sq mi over {pc['zctas']:,} ZCTAs")
    print(f"  {'miles':>6} {'zctas':>8} {'hh share':>9} "
          f"{'med hh/sqmi':>12} {'med stop/sqmi':>14} {'stations':>9}")
    for r in p["radius_sweep"]:
        mark = " <-" if abs(r["radius_miles"]
                            - p["catchment_miles"]) < 1e-9 else ""
        print(f"  {r['radius_miles']:>6.0f} {r['zctas']:>8,} "
              f"{r['household_share_pct']:>8.1f}% "
              f"{r['median_households_per_sqmi']:>12,.0f} "
              f"{r['median_stops_per_sqmi']:>14,.0f} "
              f"{r['stations_used']:>9,}{mark}")


def _stations(p: dict, k: int = 10) -> None:
    """Cheapest and dearest stations."""
    e = p["scenarios"]["baseline"]["extremes"]
    for title, rows in (("CHEAPEST STATIONS", e["cheapest"]),
                        ("DEAREST STATIONS", e["dearest"])):
        print(f"\n  {title}")
        print(f"  {'id':9} {'city':18} {'st':3} {'zctas':>6} "
              f"{'$/parcel':>9} {'IQR':>7} {'haul mi':>8}")
        for r in rows[:k]:
            print(f"  {str(r['station_id']):9} "
                  f"{str(r['city'])[:18]:18} {str(r['state'])[:3]:3} "
                  f"{r['zctas']:>6,} {r['cost_per_parcel_median']:>9.4f} "
                  f"{r['cost_per_parcel_iqr']:>7.4f} "
                  f"{r['median_linehaul_miles']:>8.1f}")
    print(f"\n  cheapest-to-dearest spread ${e['spread_usd']:.4f}/parcel")


def _metros(p: dict, k: int = 10) -> None:
    """Metro-level roll-up, cheapest and dearest ends."""
    rows = p["by_metro"]
    print(f"\n  BY METRO ({len(rows)} with at least one station) — "
          f"cheapest {k} and dearest {k}")
    print(f"  {'metro':30} {'stn':>4} {'zctas':>6} {'median $':>9} "
          f"{'min $':>8} {'max $':>8}")
    for r in rows[:k] + ([{"metro": "..."}] if len(rows) > 2 * k else []) \
            + rows[-k:]:
        if r["metro"] == "...":
            print("  ...")
            continue
        print(f"  {str(r['metro'])[:30]:30} {r['stations']:>4} "
              f"{r['zctas']:>6,} {r['median_station_cost']:>9.4f} "
              f"{r['cheapest_station_cost']:>8.4f} "
              f"{r['dearest_station_cost']:>8.4f}")


def _decile(p: dict) -> None:
    """The cheapest-decile claim, recomputed — both arms."""
    d = p["decile_test"]
    print("\n  DO FACILITIES SIT IN THEIR METRO'S CHEAPEST DECILE?")
    for arm, note in (("as_costed", "CIRCULAR — the facility's own ZCTA is "
                                    "cheap because the facility is in it"),
                      ("leave_one_out", "own station masked: the identified "
                                        "test")):
        if arm not in d:
            continue
        print(f"  [{arm}] {note}")
        for key, label in (("stations", "real stations"),
                           ("pilot_facilities", "43 pilot facilities")):
            if key not in d[arm]:
                continue
            s = d[arm][key]
            print(f"    {label:20} {s['facilities_matched']:>4}/"
                  f"{s['facilities_considered']:<4} cheapest decile "
                  f"{s['in_cheapest_decile']:>3} "
                  f"({s['in_cheapest_decile_pct']:>5.1f}%)  quartile "
                  f"{s['in_cheapest_quartile_pct']:>5.1f}%  median rank "
                  f"{s['median_pct_rank']:.3f}  median haul "
                  f"{s['median_linehaul_miles']:.1f} mi")


def print_report(payload: dict, base: dict) -> None:
    """The whole report, in the order a reader needs it."""
    b = payload["scenarios"]["baseline"]
    _rule(f"COST TO SERVE BY REAL DELIVERY STATION  -  "
          f"{b['year']}Q{b['quarter']}")
    _coverage(payload)
    _headline(payload)
    _decomposition(payload)
    _sensitivity(payload)
    _floors(payload)
    _radius(payload)
    _stations(payload)
    _metros(payload)
    _decile(payload)
    _rule()
