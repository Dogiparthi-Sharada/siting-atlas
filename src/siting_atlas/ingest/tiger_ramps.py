"""Freeway INTERCHANGES, clustered out of TIGER's ramp linework.

Why interchanges and not ramps
------------------------------
The siting constraint the industry accounts describe is an off-ramp, not
a freeway. A ZCTA can be crossed by eight lanes of interstate for four
miles with no way on or off it; a centreline-distance measure scores that
ZCTA as perfectly served, and it is not served at all.

TIGER codes ramps ``MTFCC=S1630`` and ships them only in the per-county
``ROADS`` files. But an S1630 FEATURE is not an interchange. Los Angeles
County has 4,177 of them, and it does not have 4,177 interchanges: one
four-level stack is dozens of features, and how many depends on where
TIGER happened to split the linework, which is a cartographic accident
and not a fact about the road. Counting features would measure TIGER's
digitising conventions.

So the features are CLUSTERED. Every ramp in a county is buffered by
`CLUSTER_M` metres and the buffers are dissolved; each connected
component of the result is one interchange, and its representative point
is where it is. LA County collapses from 4,177 features to 320
components, which is the right order for a county with roughly 330
freeway junctions.

The clustering radius, and what it is trading off
--------------------------------------------------
150 m. The two sides of a diamond interchange are separated by the
freeway carriageways, on the order of 50-100 m, so the radius has to
exceed that or every diamond counts twice. It must stay well under the
spacing of genuinely distinct exits, which in a dense urban corridor is
around 800 m-1 km. 150 m sits inside both bounds with room either side.

It is a parameter and it is reported as one. Re-run with
``tiger_roads.py --no-cache --cluster-m N`` to move it; over the 900
counties, the same 143,226 ramp features give:

    100 m   26,398 interchanges   (+10.9% against the default)
    150 m   23,812               (the default)
    250 m   19,869               (-16.6%)

A 67% change in the radius moves the count by about a sixth, in the
direction it should, with no cliff in between. The measure is not
balanced on the parameter.

Counties are clustered independently
-------------------------------------
An interchange sitting exactly on a county line is counted once in each
county it touches. That is a real error and it is small — a county line
follows a river or a survey grid and only rarely a freeway junction —
and fixing it would mean dissolving the national ramp layer in one
operation, which is a union over roughly three-quarters of a million
features to correct a handful of double counts.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from ..common import paths
from ..common.logging_setup import get_logger
from .tiger_geom import REGIONS

_log = get_logger("ingest.tiger_ramps")

RAMP_MTFCC = "S1630"
CLUSTER_M = 150.0
CACHE = paths.INTERIM / "tiger_interchanges.parquet"

__all__ = ["CACHE", "CLUSTER_M", "RAMP_MTFCC", "build_interchanges",
           "county_interchanges"]


def _region_of(gdf: gpd.GeoDataFrame) -> str:
    """Which projection this county's geometry should be measured in."""
    pt = gdf.to_crs("EPSG:4269").geometry.iloc[0].representative_point()
    for name, _crs, lo_x, hi_x, lo_y, hi_y in REGIONS:
        if lo_x <= pt.x <= hi_x and lo_y <= pt.y <= hi_y:
            return name
    return "conus"


def county_interchanges(path: Path,
                        cluster_m: float = CLUSTER_M) -> pd.DataFrame:
    """Interchange points for one county ROADS zip, as lon/lat.

    Read with an OGR ``where`` clause rather than read-then-filter: a
    county file is up to 135,000 features and we want the 3% that are
    ramps, so the filter belongs in the driver.
    """
    ramps = gpd.read_file(path, engine="pyogrio",
                          where=f"MTFCC='{RAMP_MTFCC}'")
    if not len(ramps):
        return pd.DataFrame({"lon": [], "lat": [], "ramps": []})
    region = _region_of(ramps)
    crs = next(c for n, c, *_ in REGIONS if n == region)
    dissolved = ramps.to_crs(crs).buffer(cluster_m).union_all()
    parts = shapely.get_parts(dissolved)
    pts = gpd.GeoSeries([p.representative_point() for p in parts],
                        crs=crs).to_crs("EPSG:4269")
    return pd.DataFrame({"lon": pts.x.to_numpy(), "lat": pts.y.to_numpy(),
                         "ramps": len(ramps)})


def _one(job: tuple[str, str, float]) -> tuple[str, pd.DataFrame]:
    geoid, path, cluster_m = job
    try:
        return geoid, county_interchanges(Path(path), cluster_m)
    except Exception as exc:                              # noqa: BLE001
        _log.error("county %s failed: %s", geoid, exc)
        return geoid, pd.DataFrame({"lon": [], "lat": [], "ramps": []})


def build_interchanges(county_paths: dict[str, Path], workers: int = 8,
                       cluster_m: float = CLUSTER_M,
                       cache: Path | None = CACHE) -> gpd.GeoDataFrame:
    """Every interchange in every supplied county, in EPSG:4269.

    Cached, because the dissolve is the expensive step of the whole
    pipeline and the covariate is refitted far more often than the roads
    change. Pass ``cache=None`` to force a rebuild.
    """
    if cache is not None and cache.exists() and cluster_m == CLUSTER_M:
        frame = gpd.read_parquet(cache)
        _log.info("interchanges: %d from cache %s", len(frame),
                  paths.rel(cache))
        return frame

    jobs = [(g, str(p), cluster_m) for g, p in sorted(county_paths.items())]
    rows, ramps_seen = [], 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for done, (geoid, frame) in enumerate(pool.map(_one, jobs), 1):
            if len(frame):
                ramps_seen += int(frame["ramps"].iloc[0])
                rows.append(frame.assign(county_geoid=geoid))
            if done % 100 == 0:
                _log.info("interchanges: %d/%d counties", done, len(jobs))

    flat = (pd.concat(rows, ignore_index=True) if rows
            else pd.DataFrame({"lon": [], "lat": [], "county_geoid": []}))
    out = gpd.GeoDataFrame(
        flat[["county_geoid"]],
        geometry=gpd.points_from_xy(flat["lon"], flat["lat"]),
        crs="EPSG:4269")
    _log.info("interchanges: %d clusters from %d ramp features across "
              "%d counties (radius %.0f m)", len(out), ramps_seen,
              len(jobs), cluster_m)
    if cache is not None and cluster_m == CLUSTER_M:
        cache.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(cache)
    return out
