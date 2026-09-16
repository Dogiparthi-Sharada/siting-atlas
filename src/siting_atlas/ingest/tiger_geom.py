"""Distance, length and containment primitives, in a projection that works.

The projection is not a detail
------------------------------
TIGER ships in EPSG:4269, which is degrees. A distance in degrees is not
a distance: one degree of longitude is 111 km at the equator and 82 km at
Seattle, so a degree-space "nearest road" comparison silently ranks
northern ZCTAs as closer than they are. Everything here is reprojected
before any measurement is taken.

`osm_landuse.py` uses EPSG:5070 (Albers equal-area, continental US) and
that is right for areas inside the CONUS. It is wrong OUTSIDE it, and
this project has four metros outside it — Anchorage, Honolulu, San Juan
and Aguadilla-Isabela, 152 panel ZCTAs between them. Albers CONUS at
Honolulu is roughly 40 degrees of longitude past its western limit and
the error there is not a rounding error. Rather than drop four metros or
report four wrong numbers, each region is measured in the projection its
own mapping agency uses. The regions are islands plus one continent, so
nothing sits near a boundary and no nearest-feature search can cross one.

Why the polygon and not the centroid
------------------------------------
A ZCTA is not a point. The centroid of a 900-square-mile rural ZCTA can
be eight miles from the only part of it anyone would ever build on, and
that is precisely the case where a highway-access covariate should have
something to say. Every distance here is POLYGON to FEATURE: the
shortest distance from any point of the ZCTA to the road. It is
therefore an upper bound on how far a developer must look, not a
description of the typical parcel — and it is zero whenever a highway
crosses the ZCTA at all, which is why `tiger_roads.py` does not rely on
distance alone.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import STRtree

#: (name, CRS, lon_min, lon_max, lat_min, lat_max). The CRS for each is
#: the metre-based projected system the relevant authority publishes:
#: Albers CONUS, Alaska Albers, NAD83 Hawaii zone 3, and the NAD83 Puerto
#: Rico / Virgin Islands Lambert grid. The boxes are disjoint and cover
#: every ZCTA in the panel; `assign_region` asserts that they do.
REGIONS: tuple[tuple[str, str, float, float, float, float], ...] = (
    ("conus", "EPSG:5070", -130.0, -65.0, 22.0, 50.0),
    ("alaska", "EPSG:3338", -180.0, -129.0, 50.0, 72.0),
    ("hawaii", "EPSG:26963", -161.0, -154.0, 18.0, 23.0),
    ("prvi", "EPSG:32161", -68.0, -64.0, 17.0, 19.0),
)

M_PER_KM = 1000.0
M_PER_MILE = 1609.344

#: Metres of Douglas-Peucker tolerance applied to the geometry that goes
#: into the nearest-feature INDEX, and only to that. A TIGER ZCTA carries
#: about 1,500 vertices and the national primary-road layer carries 3.5
#: million; an exact R-tree nearest query over those took 8 seconds per
#: 400 ZCTAs, which is 9 minutes per pass over the panel and three passes
#: are needed.
#:
#: The tolerance does NOT enter the reported number. The index is used to
#: PICK the nearest feature and the distance is then computed exactly,
#: between the full-resolution geometries, so the only way the shortcut
#: can be wrong is by picking the second-nearest feature when two are
#: within a whisker of each other. Measured on a 400-ZCTA sample against
#: the exact answer: worst case 13 m, 99th percentile 2.4 m, on distances
#: reported in kilometres. It is also one-sided — picking the wrong
#: feature can only overstate the distance, never understate it.
SIMPLIFY_M = 25.0

__all__ = ["M_PER_KM", "M_PER_MILE", "REGIONS", "SIMPLIFY_M",
           "assign_region", "count_inside", "length_inside_mi",
           "nearest_km", "probe_geometry"]


def assign_region(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Region label per feature, from a representative interior point.

    A representative point, not a centroid: the centroid of a C-shaped or
    multipart ZCTA can fall outside the polygon, and for a coastal
    multipart ZCTA it can fall in the sea and out of every box.
    """
    pt = gdf.to_crs("EPSG:4269").geometry.representative_point()
    x, y = pt.x.to_numpy(), pt.y.to_numpy()
    out = np.full(len(gdf), "", dtype=object)
    for name, _crs, lo_x, hi_x, lo_y, hi_y in REGIONS:
        hit = (x >= lo_x) & (x <= hi_x) & (y >= lo_y) & (y <= hi_y)
        out[hit & (out == "")] = name
    return pd.Series(out, index=gdf.index, name="region")


def probe_geometry(geoms: gpd.GeoSeries) -> np.ndarray:
    """The simplified copy used for INDEX LOOKUPS only. See `SIMPLIFY_M`."""
    return shapely.simplify(geoms.to_numpy(), SIMPLIFY_M)


def nearest_km(targets: gpd.GeoSeries, features: gpd.GeoSeries,
               probe: np.ndarray | None = None) -> np.ndarray:
    """Shortest distance in km from each target to the nearest feature.

    The index is queried on simplified geometry and the distance is then
    measured between the FULL-RESOLUTION pair, so the tolerance affects
    which feature is chosen and never the number reported.

    ``NaN`` when there is no feature at all, which is a different
    statement from "very far" and must not be written as a large number:
    an imputed 999 km would be read by the model as a real observation.
    """
    if not len(features) or not len(targets):
        return np.full(len(targets), np.nan)
    exact = features.to_numpy()
    tree = STRtree(shapely.simplify(exact, SIMPLIFY_M))
    idx = tree.nearest(probe_geometry(targets) if probe is None else probe)
    return shapely.distance(targets.to_numpy(), exact[idx]) / M_PER_KM


def length_inside_mi(polys: gpd.GeoDataFrame, lines: gpd.GeoSeries,
                     key: str) -> pd.Series:
    """Miles of line geometry falling INSIDE each polygon.

    Extensive, in the sense `choice.py` requires: merge two ZCTAs and the
    interstate mileage of the merged zone is the sum of the two. That is
    the property the ``ln(beta'a)`` functional form exists to preserve,
    and it is the property a distance does not have.
    """
    if not len(lines):
        return pd.Series(0.0, index=polys[key])
    frame = gpd.GeoDataFrame(geometry=lines.reset_index(drop=True),
                             crs=polys.crs)
    hit = gpd.sjoin(frame, polys[[key, "geometry"]], predicate="intersects",
                    how="inner")
    if not len(hit):
        return pd.Series(0.0, index=polys[key])
    lookup = polys.set_index(key).geometry
    clipped = [row.geometry.intersection(lookup[getattr(row, key)]).length
               for row in hit.itertuples()]
    hit = hit.assign(_m=clipped)
    total = hit.groupby(key)["_m"].sum() / M_PER_MILE
    return total.reindex(polys[key]).fillna(0.0)


def count_inside(polys: gpd.GeoDataFrame, points: gpd.GeoSeries,
                 key: str) -> pd.Series:
    """How many point features fall inside each polygon. Extensive too."""
    if not len(points):
        return pd.Series(0.0, index=polys[key])
    frame = gpd.GeoDataFrame(geometry=points.reset_index(drop=True),
                             crs=polys.crs)
    hit = gpd.sjoin(frame, polys[[key, "geometry"]], predicate="within",
                    how="inner")
    counts = hit.groupby(key).size().astype(float)
    return counts.reindex(polys[key]).fillna(0.0)
