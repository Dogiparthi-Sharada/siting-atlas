"""L1 — highway access per ZCTA, from TIGER/Line roads and ramps.

    PYTHONPATH=src python -m siting_atlas.ingest.tiger_roads

Why this covariate exists
-------------------------
Every industry account of delivery-station siting puts freeway access at
or near the top of the list: the building takes line-haul semis
overnight and releases several hundred vans in a morning wave, and both
flows have to reach a freeway without being routed through residential
streets. Nothing in the panel measures that.

`traffic_proximity` is in the panel and looks like it should. It does
not: it is EJScreen's pollution-exposure measure, the traffic COUNT on
roads within 500 m of the block, and it is large wherever a lot of
vehicles pass nearby whether or not anything can get on or off. Tested
as a covariate it returned +0.07 lift, which is nothing. Exposure and
access are different concepts and this module measures the second.

What is measured, and the three kinds of column
-----------------------------------------------
DISTANCE   ``*_dist_km``. From the ZCTA POLYGON, not its centroid: the
           centroid of a large rural ZCTA can be miles from anywhere a
           developer would look. Polygon distance is the shortest
           distance from any point of the zone, so it is a lower bound
           on the trip and it is exactly ZERO whenever the feature
           crosses the zone at all — which for interstates is 21% of
           panel ZCTAs and 49% of the ZCTAs in metros with a facility.
           A measure that is zero for half its support carries little
           information in the half that matters, which is the reason the
           next two kinds exist.

MILEAGE    ``*_miles``. Centreline miles of road falling inside the
           ZCTA. This separates the zones that distance cannot: two
           ZCTAs both scoring zero distance, one clipped by a corner of
           an interstate and one with nine miles of it down the spine.

COUNT      ``interchanges``. Connected clusters of TIGER ramp linework —
           see `tiger_ramps.py` for why the raw ramp features are not
           the unit. This is the closest thing in the data to the
           constraint the industry accounts actually describe, and it is
           the reason the per-county download in `tiger_fetch.py` is
           worth its 2 GB.

Mileage and count are EXTENSIVE — merge two ZCTAs and the merged zone
has the sum of the mileage and the sum of the interchanges. `choice.py`
section 1 of its docstring explains why that matters: the ``ln(beta'a)``
form exists to make the model invariant to how the Census drew the zone
boundaries, and that invariance holds only for variables that add. A
distance does not add, so `access` below is a workaround and is labelled
one wherever it appears.

The sign problem, and the transform it forces
----------------------------------------------
`choice.py` enforces ``beta_k = exp(theta_k) > 0``: every column is
weakly ATTRACTIVE and a repellent one cannot be expressed. Distance to a
highway is repellent by construction — nearer is better — so entering
``interchange_dist_km`` raw guarantees the optimiser walks it to the
boundary and reports it as worthless whatever it is worth.

``highway_access = 1 / (1 + d_km)`` is entered instead. It is positive
everywhere, it is strictly decreasing in distance, and unlike ``1/d`` it
is defined at ``d = 0``, which is not an edge case here but the modal
observation. The units are readable: 1.0 for a ZCTA containing an
interchange, 0.5 at one kilometre, 0.09 at ten. `tiger_lift.py` also
fits ``exp(-d / 5 km)`` and reports both, because the choice of decay
shape is an assumption and reporting one of two fitted forms would be
choosing the answer.

Coverage
--------
The 14,767 ZCTAs of the 235 metros that contain a facility — every ZCTA
the choice model can ever put in a choice set, and no others. See
`facility_scope` for why the artefact stops there. `ramp_coverage` marks
rows the interchange layer reached, and where it did not the interchange
columns are NULL rather than zero: a zero would read as "no interchange
in this ZCTA", which is a measurement, when the truth is "not measured".
"""

from __future__ import annotations

import argparse

import geopandas as gpd
import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from . import tiger_fetch, tiger_ramps, tiger_scope
from .tiger_geom import (
    REGIONS,
    assign_region,
    count_inside,
    length_inside_mi,
    nearest_km,
    probe_geometry,
)

_log = get_logger("ingest.tiger_roads")

GEOM = paths.INTERIM / "zcta_geom.parquet"
OUT = paths.INTERIM / "highway_access.parquet"

#: TIGER's route-type code for an Interstate. The rest of ``S1100`` is US
#: routes, state highways and named expressways — still primary roads, and
#: still line-haul capable, which is why both are measured. Alaska is the
#: reason it has to be both: the Glenn and Seward highways are the
#: line-haul routes into Anchorage and TIGER codes neither as ``I``.
INTERSTATE = "I"

#: Kilometres. ``1 / (1 + d)``; see the module docstring for why not 1/d.
ACCESS_OFFSET_KM = 1.0

__all__ = ["ACCESS_OFFSET_KM", "OUT", "build", "main"]


def facility_scope() -> tuple[set[str], list[str]]:
    """The ZCTAs and counties of every CBSA that contains a facility.

    Why the artefact stops here rather than covering all 25,022 panel
    ZCTAs. The conditional choice model only ever compares ZCTAs INSIDE a
    metro that has a facility in it — `build_frame` groups alternatives
    by `cbsa_code` and looks up the chosen facility's own metro — so a
    ZCTA outside those 235 metros can never enter a choice set, and a
    measurement there would be read by nothing.

    It also makes the coverage of the artefact a single fact rather than
    two. The ramp layer already stops at these counties, because 900
    county downloads is what it costs and 3,234 is what the nation costs.
    Matching the road columns to the same boundary means every column in
    the file is present on exactly the same rows, and there is no
    half-covered ZCTA for a later join to trip over.
    """
    from ..warehouse.national import load_national
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", "county_geoid"])
    member = panel.dropna(subset=["cbsa_code"]).drop_duplicates("zcta")
    home = member.set_index("zcta")["cbsa_code"].to_dict()
    expanded = (paths.ROOT / "data" / "external" / "facility_panel"
                / "national_facilities_expanded.csv")
    fac = load_national(expanded if expanded.exists() else None)
    codes = {home.get(str(z).strip()) for z in fac["zcta"].astype(str)}
    codes.discard(None)
    keep = member[member["cbsa_code"].isin(codes)]
    return (set(keep["zcta"].astype(str)),
            sorted(keep["county_geoid"].dropna().astype(str).unique()))


def _zctas(scope: set[str]) -> gpd.GeoDataFrame:
    if not GEOM.exists():
        raise SystemExit(f"\n  {paths.rel(GEOM)} not found — it is written "
                         "by the ZCTA geometry step\n")
    z = gpd.read_parquet(GEOM).rename(columns={"ZCTA5CE20": "zcta"})
    z = z[z["zcta"].isin(scope)]
    missing = len(scope) - len(z)
    if missing:
        _log.warning("%d in-scope ZCTA(s) have no TIGER geometry and are "
                     "absent from the artefact", missing)
    return z[["zcta", "geometry"]].copy()


def _region_block(zblock: gpd.GeoDataFrame, roads: gpd.GeoDataFrame,
                  inter: gpd.GeoDataFrame, crs: str) -> pd.DataFrame:
    """Every measurement for one region, in that region's projection."""
    z = zblock.to_crs(crs)
    r = roads.to_crs(crs)
    freeway = r[r["RTTYP"] == INTERSTATE]
    probe = probe_geometry(z.geometry)
    out = pd.DataFrame({"zcta": z["zcta"].to_numpy()})
    out["primary_road_dist_km"] = nearest_km(z.geometry, r.geometry, probe)
    out["interstate_dist_km"] = nearest_km(z.geometry, freeway.geometry,
                                           probe)
    out["primary_road_miles"] = length_inside_mi(
        z, r.geometry, "zcta").to_numpy()
    out["interstate_miles"] = length_inside_mi(
        z, freeway.geometry, "zcta").to_numpy()
    if len(inter):
        p = inter.to_crs(crs)
        out["interchange_dist_km"] = nearest_km(z.geometry, p.geometry, probe)
        out["interchanges"] = count_inside(z, p.geometry, "zcta").to_numpy()
    else:
        out["interchange_dist_km"] = np.nan
        out["interchanges"] = np.nan
    return out


def build(workers: int = 8, cluster_m: float = tiger_ramps.CLUSTER_M,
          cache: bool = True) -> pd.DataFrame:
    """One row per ZCTA with geometry: distances, mileage, interchanges."""
    scope, counties = facility_scope()
    zctas = _zctas(scope)
    roads = gpd.read_file(tiger_fetch.primary_roads(), engine="pyogrio")
    _log.info("%d primary road features (%d interstate), %d ZCTAs in %d "
              "counties", len(roads),
              int((roads["RTTYP"] == INTERSTATE).sum()), len(zctas),
              len(counties))
    got = tiger_fetch.county_roads(counties)
    inter = tiger_ramps.build_interchanges(
        got["paths"], workers=workers, cluster_m=cluster_m,
        cache=tiger_ramps.CACHE if cache else None)
    covered = set(got["covered"])

    zctas["region"] = assign_region(zctas)
    roads["region"] = assign_region(roads)
    inter["region"] = assign_region(inter) if len(inter) else pd.Series(
        dtype=object)

    blocks = []
    for name, crs, *_ in REGIONS:
        zb = zctas[zctas["region"] == name]
        if not len(zb):
            continue
        blocks.append(_region_block(
            zb, roads[roads["region"] == name],
            inter[inter["region"] == name] if len(inter) else inter, crs))
        _log.info("region %-7s %5d ZCTAs measured in %s", name, len(zb), crs)

    frame = pd.concat(blocks, ignore_index=True)
    frame = tiger_scope.mark_coverage(frame, covered)
    frame["highway_access"] = ACCESS_OFFSET_KM / (
        ACCESS_OFFSET_KM + frame["interchange_dist_km"])
    frame["interstate_access"] = ACCESS_OFFSET_KM / (
        ACCESS_OFFSET_KM + frame["interstate_dist_km"])
    return frame.sort_values("zcta").reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cluster-m", type=float,
                    default=tiger_ramps.CLUSTER_M,
                    help="interchange clustering radius, metres")
    ap.add_argument("--no-cache", action="store_true",
                    help="rebuild the interchange layer from the ramps")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L1", "TIGER highway access"), step("tiger_roads"):
        frame = build(args.workers, args.cluster_m, not args.no_cache)
        summary = tiger_scope.summarise(frame)
        for k, v in summary.items():
            if isinstance(v, (int, float)):
                metric(f"highway_{k}", v)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT, index=False)
    artefact(OUT, rows=len(frame))

    print(f"\n  {summary['zctas']:,} ZCTAs -> {paths.rel(OUT)}")
    print(f"  ramp layer covers        : {summary['ramp_covered_zctas']:,} "
          f"ZCTAs")
    print(f"  median interstate dist   : "
          f"{summary['interstate_dist_km_median']:.1f} km "
          f"({100 * summary['interstate_dist_zero_share']:.0f}% are zero)")
    if summary["interchange_dist_km_median"] is not None:
        print(f"  median interchange dist  : "
              f"{summary['interchange_dist_km_median']:.2f} km, "
              f"{summary['interchanges_total']:,.0f} interchanges, "
              f"{100 * summary['interchanges_zero_share']:.0f}% of covered "
              "ZCTAs have none")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
