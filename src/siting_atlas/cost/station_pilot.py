"""The pilot cost model, recomputed at runtime as the comparison arm.

The station model only means something beside the thing it replaces, and
the thing it replaces already shipped as five parquet tables. Those are
read here and re-reduced — median, decomposition, scenario span, the two
tour floors — rather than quoted from `docs/NUMBERS.md`. If a pilot table
is ever regenerated, this comparison moves with it instead of going stale
silently, and if the tables are absent the payload says so.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths

#: The pilot artefacts, one per scenario. Not regenerated here — read.
PILOT_BASE = "cost_to_serve_2023q4_{}.parquet"

#: The pilot ran under BASELINE, so its floors are the baseline ones.
PILOT_STOPS_PER_TOUR = 120
PILOT_MIN_POINTS = 15

COMPONENTS = (("service_time", "cost_service_time"),
              ("vehicle", "cost_vehicle"),
              ("drive_time", "cost_drive_time"),
              ("distance", "cost_distance"))


def _pilot_density(pilot: pd.DataFrame) -> float | None:
    """Median households per square mile over the pilot's ZCTAs.

    The pilot parquet carries land area but not households, so the count is
    fetched back from the panel. This is the figure the catchment's density
    claim is measured against, so it is recomputed rather than quoted.
    """
    if not paths.PANEL.exists():
        return None
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "year", "quarter", "households",
                                     "land_area_sqmi"])
    panel = panel[(panel["year"] == 2023) & (panel["quarter"] == 4)]
    j = pilot[["zcta"]].merge(panel, on="zcta", how="left")
    land = j["land_area_sqmi"].where(j["land_area_sqmi"] > 0)
    return float((j["households"] / land).median())


def pilot_comparison(base: dict) -> dict:
    """The same statistics recomputed from the pilot's own parquets.

    Read at runtime from `outputs/tables/cost_to_serve_2023q4_*.parquet` so
    the comparison cannot drift from what the pilot artefact actually says.
    Returns ``{"available": False}`` rather than a typed constant if the
    pilot tables are absent.
    """
    path = paths.TABLES / PILOT_BASE.format("baseline")
    if not path.exists():
        return {"available": False}
    pilot = pd.read_parquet(path)
    stops = pilot["daily_stops"]
    med = float(pilot["cost_per_parcel"].median())
    out = {
        "available": True,
        "source": paths.rel(path),
        "zctas": int(len(pilot)),
        "median_cost_per_parcel": med,
        "p10": float(pilot["cost_per_parcel"].quantile(0.10)),
        "p90": float(pilot["cost_per_parcel"].quantile(0.90)),
        "median_households_per_sqmi": _pilot_density(pilot),
        # The published "475" the catchment gets compared to. It is a STOPS
        # density, not a households density — see station_report.radius_sweep.
        "median_stops_per_sqmi":
            float(pilot["stop_density_per_sqmi"].median()),
        "median_linehaul_miles": float(pilot["linehaul_miles"].median()),
        "below_one_tour_pct":
            100.0 * float((stops < PILOT_STOPS_PER_TOUR).mean()),
        "below_bhh_floor_pct":
            100.0 * float((stops < PILOT_MIN_POINTS).mean()),
        "delta_median_pct":
            100.0 * (base["median_cost_per_parcel"] / med - 1.0),
    }
    cols = [c for _, c in COMPONENTS] + ["cost_per_stop"]
    good = pilot[pilot[cols].notna().all(axis=1)]
    w = good["daily_stops"]
    total = float((good["cost_per_stop"] * w).sum() / w.sum())
    for label, col in COMPONENTS:
        out[f"{label}_share_pct"] = 100.0 * float(
            (good[col] * w).sum() / w.sum()) / total
    spans = {}
    for name in ("baseline", "congested", "dense_routing", "high_fuel",
                 "pessimistic_tour"):
        p = paths.TABLES / PILOT_BASE.format(name)
        if p.exists():
            spans[name] = float(
                pd.read_parquet(p, columns=["cost_per_parcel"])
                  ["cost_per_parcel"].median())
    if spans:
        b = spans["baseline"]
        pcts = {k: 100.0 * (v / b - 1.0) for k, v in spans.items()}
        out["scenario_pct"] = pcts
        out["span_pct"] = [min(pcts.values()), max(pcts.values())]
    return out
