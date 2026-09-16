"""Industrially-zoned land per ZCTA, from OpenStreetMap.

Why this source
---------------
Warehousing establishment counts (see `cbp_detail.py`) took the choice model
from 30% to 50% at top-10, and they work because they PROXY the real binding
constraint: you cannot site a delivery station on land that is not zoned and
built for it. This measures that constraint directly rather than by proxy.

The two are not the same thing and the difference is the point. A ZIP can
hold a great deal of industrial land with few establishments on it — which is
exactly the profile of a ZIP with room for a new station. An establishment
count cannot express "empty but zoned"; an area can.

    python -m siting_atlas.ingest.osm_landuse

What is fetched
---------------
Two tags, both extensive and both meaningful on their own:

    landuse=industrial   the zoning-like polygon. The planning constraint.
    building=warehouse   the building stock. Amazon leases far more often
                         than it builds, so existing warehouses are supply.

Queried per CBSA bounding box, because Overpass will not serve a national
query and 25,022 per-ZCTA queries would be abusive. The bbox is the envelope
of the metro's ZCTA polygons, so it over-covers; the spatial join afterwards
puts every polygon in its true ZCTA regardless.

Caching is not an optimisation here, it is a requirement
--------------------------------------------------------
Overpass is a free shared service that returns a runtime error whenever it is
busy — the main instance failed once and succeeded on retry during
development. Every response is cached to `data/raw/osm_landuse/` by CBSA, so
a re-run costs nothing and a partial failure resumes instead of restarting.
Be polite: one request at a time, with a pause between them.

The area is computed in an equal-area projection
------------------------------------------------
TIGER ships in EPSG:4269 (degrees). Computing area in degrees gives a number
that shrinks as you move north and is not an area at all. Everything is
reprojected to EPSG:5070, the Albers equal-area conic used for the
continental US, before any area is taken.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

import geopandas as gpd
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("ingest.osm_landuse")

RAW = paths.RAW / "osm_landuse"
GEOM = paths.INTERIM / "zcta_geom.parquet"
OUT = paths.INTERIM / "osm_landuse.parquet"

ENDPOINT = "https://overpass-api.de/api/interpreter"

#: Overpass returns HTTP 406 Not Acceptable to a request with no
#: User-Agent, which is what urllib sends by default. The first version
#: of this module failed every query that way and reported "0 polygons"
#: for three metros -- indistinguishable, in the output, from three
#: metros with no industrial land. Identify yourself.
HEADERS = {"User-Agent": "siting-atlas/0.1 (MSBA capstone; academic research)"}

#: Albers equal-area conic, continental US. Areas in degrees are meaningless.
EQUAL_AREA = "EPSG:5070"
SQM_PER_SQMI = 2_589_988.11

#: OSM tag -> output column. Both are extensive, so both may enter the
#: choice model's ln(beta'a) term.
TAGS = {
    ("landuse", "industrial"): "industrial_sqmi",
    ("building", "warehouse"): "warehouse_sqmi",
}

#: Seconds between requests. `GET /api/status` on the main instance reports
#: "Rate limit: 2" -- two concurrent slots for the whole world, with a slot
#: freeing roughly every 48 seconds under load. A 4-second pause was inside
#: that limit on paper and still drew a wall of HTTP 504s, so this is set to
#: a value that finishes in under an hour rather than one that finishes fast
#: and gets us throttled into failing silently.
#: Seconds between tile requests, and how many times a tile is retried.
#:
#: Raised from 10.0/3 after a live run on 2026-09-14 measured 12 gateway
#: errors (503/504) in the first four metros and lost three of them. Overpass
#: is a free shared service with no published rate limit; the only control a
#: client has is to ask less often and to give up more slowly. Combined with
#: the per-tile cache in `fetch_cbsa`, a slower run is strictly better than a
#: faster one that discards its own work -- wall-clock time is free here
#: because nothing is waiting on the result.
PAUSE = 20.0
ATTEMPTS = 5

#: Maximum degrees per side of a single Overpass query. A metro bbox is
#: split into a grid no coarser than this before querying.
#:
#: Found the hard way: Atlanta (CBSA 12060) spans about 1.6 degrees and
#: returned HTTP 504 Gateway Timeout on all three attempts, which the
#: caller reported as '0 polygons' -- indistinguishable from a metro
#: with no industrial land. Overpass charges by the area swept and the
#: geometry returned, so the fix is smaller queries, not a longer
#: timeout.
TILE_DEGREES = 0.5

__all__ = ["TAGS", "fetch_cbsa", "build_areas", "main"]


def _query(bbox: tuple[float, float, float, float]) -> str:
    """Overpass QL for every wanted tag in one bounding box."""
    s, w, n, e = bbox
    clauses = "".join(
        f'way["{k}"="{v}"]({s},{w},{n},{e});'
        f'relation["{k}"="{v}"]({s},{w},{n},{e});'
        for k, v in TAGS)
    return f"[out:json][timeout:180];({clauses});out geom;"


def _tiles(bbox: tuple[float, float, float, float]) -> list[tuple]:
    """Split a bbox into cells no larger than TILE_DEGREES on a side."""
    s, w, n, e = bbox
    rows = max(1, math.ceil((n - s) / TILE_DEGREES))
    cols = max(1, math.ceil((e - w) / TILE_DEGREES))
    dy, dx = (n - s) / rows, (e - w) / cols
    return [(s + r * dy, w + c * dx, s + (r + 1) * dy, w + (c + 1) * dx)
            for r in range(rows) for c in range(cols)]


def fetch_cbsa(cbsa: str, bbox: tuple[float, float, float, float]) -> dict:
    """One CBSA's polygons, from cache if present, tiled if large.

    A tile that fails every attempt still aborts the WHOLE CBSA rather than
    returning a partial answer, because a partial answer is a quiet
    understatement of industrial land in one corner of one metro -- and a
    silent understatement is worse than a visible gap.

    EVERY SUCCESSFUL TILE IS CACHED SEPARATELY, THOUGH.
    --------------------------------------------------
    The first version cached only the finished metro, which interacted badly
    with the abort rule above: a metro that failed on tile 7 of 18 threw away
    the six tiles that had succeeded, and the next run fetched them again.
    Measured against a live Overpass on 2026-09-14 -- 4 metros attempted, 3
    discarded, 12 gateway errors -- that makes the job effectively
    uncompletable, because the chance of 18 consecutive tiles all succeeding
    falls off a cliff once the server starts returning 503s.

    With per-tile caching the run becomes monotone: every attempt strictly
    increases what is on disk, a re-run only asks for what is still missing,
    and a metro completes across as many sessions as it needs. The abort rule
    is unchanged -- the metro is still all-or-nothing in the OUTPUT -- but the
    work is no longer all-or-nothing.
    """
    cache = RAW / f"{cbsa}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    tiles = _tiles(bbox)
    tile_dir = RAW / "tiles" / str(cbsa)
    tile_dir.mkdir(parents=True, exist_ok=True)

    merged: list[dict] = []
    fetched = 0
    for i, tile in enumerate(tiles, 1):
        tile_cache = tile_dir / f"{i:03d}.json"
        if tile_cache.exists():
            merged.extend(json.loads(tile_cache.read_text()))
            continue
        payload = _fetch_one(f"cbsa {cbsa} tile {i}/{len(tiles)}", tile)
        if payload is None:
            _log.error("cbsa %s: tile %d of %d failed; discarding the metro "
                       "rather than reporting a partial area. %d tile(s) are "
                       "cached and will not be re-fetched.",
                       cbsa, i, len(tiles), len(list(tile_dir.glob("*.json"))))
            return {"elements": []}
        elements = payload.get("elements", [])
        tile_cache.write_text(json.dumps(elements))
        merged.extend(elements)
        fetched += 1
        if len(tiles) > 1:
            time.sleep(PAUSE)

    payload = {"elements": merged}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload))
    # The metro is complete, so its per-tile scratch is redundant.
    for stale in tile_dir.glob("*.json"):
        stale.unlink()
    tile_dir.rmdir()
    if fetched < len(tiles):
        _log.info("cbsa %s: completed using %d cached tile(s) from an "
                  "earlier run", cbsa, len(tiles) - fetched)
    return payload


def _fetch_one(label: str, bbox: tuple[float, float, float, float]):
    """One Overpass request with retries. None when every attempt fails."""
    body = urllib.parse.urlencode({"data": _query(bbox)}).encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers=HEADERS)
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=300) as fh:
                payload = json.loads(fh.read().decode("utf-8", "replace"))
        except (urllib.error.HTTPError, urllib.error.URLError,
                json.JSONDecodeError, TimeoutError) as e:
            _log.warning("%s attempt %d/%d failed: %s",
                         label, attempt, ATTEMPTS, e)
            time.sleep(PAUSE * attempt * attempt)
            continue
        if "elements" not in payload:
            _log.warning("%s attempt %d/%d: no elements key",
                         label, attempt, ATTEMPTS)
            time.sleep(PAUSE * attempt * attempt)
            continue
        return payload
    return None


def _polygons(payload: dict) -> gpd.GeoDataFrame:
    """Overpass `out geom` elements as polygons, tagged by wanted column."""
    from shapely.geometry import Polygon

    rows = []
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        column = next((c for (k, v), c in TAGS.items() if tags.get(k) == v),
                      None)
        if column is None:
            continue
        # Ways carry `geometry`; relations carry `members`, each with its own.
        rings = ([el["geometry"]] if "geometry" in el
                 else [m["geometry"] for m in el.get("members", [])
                       if m.get("type") == "way" and "geometry" in m])
        for ring in rings:
            if len(ring) < 4:
                continue
            try:
                poly = Polygon([(p["lon"], p["lat"]) for p in ring])
            except (ValueError, KeyError):
                continue
            if poly.is_valid and poly.area > 0:
                rows.append({"column": column, "geometry": poly})
    if not rows:
        return gpd.GeoDataFrame(
            {"column": [], "geometry": []}, geometry="geometry",
            crs="EPSG:4326")
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def facility_cbsas() -> set[str]:
    """The metros the choice model actually needs.

    All 935 CBSAs would be ~8 hours of polite Overpass queries for data
    no model reads. The choice model only builds choice sets for metros
    that contain a facility, so those are the only ones fetched.
    """
    from ..warehouse.national import load_national
    panel = pd.read_parquet(paths.PANEL, columns=["zcta", "cbsa_code"])
    home = (panel.dropna(subset=["cbsa_code"]).drop_duplicates("zcta")
            .set_index("zcta")["cbsa_code"].to_dict())
    codes = {home.get(str(z).strip())
             for z in load_national()["zcta"].astype(str)}
    return {c for c in codes if c is not None}


def build_areas(limit: int | None = None,
                only: set[str] | None = None) -> pd.DataFrame:
    """Industrial and warehouse square miles per ZCTA, for every CBSA."""
    zctas = gpd.read_parquet(GEOM)
    panel = pd.read_parquet(paths.PANEL, columns=["zcta", "cbsa_code"])
    membership = panel.dropna(subset=["cbsa_code"]).drop_duplicates("zcta")
    zctas = zctas.rename(columns={"ZCTA5CE20": "zcta"}).merge(
        membership, on="zcta", how="inner").to_crs("EPSG:4326")

    out: list[pd.DataFrame] = []
    codes = sorted(zctas["cbsa_code"].unique())
    if only is not None:
        codes = [c for c in codes if c in only]
    if limit:
        codes = codes[:limit]

    for i, cbsa in enumerate(codes, 1):
        block = zctas[zctas["cbsa_code"] == cbsa]
        w, s, e, n = block.total_bounds
        cached = (RAW / f"{cbsa}.json").exists()
        payload = fetch_cbsa(str(cbsa), (s, w, n, e))
        if not cached:
            time.sleep(PAUSE)

        polys = _polygons(payload)
        frame = block[["zcta"]].copy()
        for column in TAGS.values():
            frame[column] = 0.0
        if len(polys):
            joined = gpd.overlay(
                block[["zcta", "geometry"]].to_crs(EQUAL_AREA),
                polys.to_crs(EQUAL_AREA), how="intersection",
                keep_geom_type=True)
            if len(joined):
                joined["sqmi"] = joined.geometry.area / SQM_PER_SQMI
                wide = (joined.groupby(["zcta", "column"])["sqmi"].sum()
                        .unstack(fill_value=0.0))
                for column in TAGS.values():
                    if column in wide.columns:
                        frame[column] = frame["zcta"].map(
                            wide[column]).fillna(0.0)
        out.append(frame)
        _log.info("[%d/%d] cbsa %s: %d polygons, %d ZCTAs, %.1f industrial "
                  "sq mi%s", i, len(codes), cbsa, len(polys), len(frame),
                  frame["industrial_sqmi"].sum(),
                  " (cached)" if cached else "")

    return pd.concat(out, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None,
                    help="first N CBSAs only, for a smoke test")
    ap.add_argument("--all-cbsas", action="store_true",
                    help="every CBSA, not just those with a facility "
                         "(~8 hours of Overpass queries)")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with (traced_layer("L1", "OSM industrial landuse"),
          step("osm_landuse:build")):
        only = None if args.all_cbsas else facility_cbsas()
        if only is not None:
            _log.info("restricting to the %d CBSAs that contain a "
                      "facility", len(only))
        frame = build_areas(args.limit, only)
        metric("osm_landuse_zctas", len(frame))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT, index=False)
    artefact(OUT, rows=len(frame))

    nz = frame[frame["industrial_sqmi"] > 0]
    print(f"\n  {len(frame):,} ZCTAs -> {paths.rel(OUT)}")
    print(f"  with any industrial land : {len(nz):,} "
          f"({100 * len(nz) / max(len(frame), 1):.1f}%)")
    print(f"  median where present     : {nz['industrial_sqmi'].median():.3f} "
          f"sq mi")
    total = frame["industrial_sqmi"].sum()
    print(f"  total industrial land    : {total:,.0f} sq mi\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
