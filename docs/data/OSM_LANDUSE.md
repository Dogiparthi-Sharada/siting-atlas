# OSM industrial land — built, verified on three metros, then blocked

*Written 2026-09-14. Code `src/siting_atlas/ingest/osm_landuse.py`. Artefact
`data/interim/osm_landuse.parquet` — **60 ZCTAs from a three-metro smoke test,
not a usable covariate**. Cache `data/raw/osm_landuse/`, one CBSA of 62. Run
logs under `logs/run-20260914-01*` and `logs/run-20260914-024151-e68b`.*

**Status: BUILT AND BLOCKED.** The code works, it was verified end to end on
three metros, and the national extraction cannot finish because the public
Overpass API will not serve it. No model reads the artefact. Nothing in this
document is a result; it is a record of what was built, what it cost, and the
three bugs that were found on the way, so the next attempt does not rediscover
them.

---

## 1. Why it was built

[`CBP_DETAIL.md`](CBP_DETAIL.md) records that warehousing establishment counts
took the choice model's held-out top-10 from 23.7% to 50.0%. They work because
they **proxy** the real binding constraint: you cannot site a delivery station
on land that is not zoned and built for it.

This measures the constraint directly instead of by proxy, and the difference
is the point. A ZIP can hold a great deal of industrial land with very few
establishments on it — which is exactly the profile of a ZIP with room for a
new station. An establishment count cannot express "empty but zoned"; an area
can. It also has no circularity problem: a warehouse polygon is a building,
not a business registration, and OSM is not a register of who operates there.

Two tags, both extensive, so both may sit inside the choice model's
`ln(beta'a)` term:

```
  landuse=industrial    the zoning-like polygon. The planning constraint.
  building=warehouse    the building stock. Amazon leases far more often
                        than it builds, so existing warehouses are supply.
```

## 2. The three bugs, all found by the output being wrong rather than by an error

Each of these produced a *plausible* wrong answer rather than a crash, which is
why they are worth recording.

### 2.1 HTTP 406 with no User-Agent — reported as "0 polygons"

`urllib` sends no `User-Agent` by default. Overpass answers such a request with
**HTTP 406 Not Acceptable**. The first version of the module caught the error,
logged a warning, and returned an empty payload, which the caller printed as
"0 polygons" — **indistinguishable, in the output, from a metro with no
industrial land at all.**

The evidence is two runs eight minutes apart on the same three metros:

```
  logs/run-20260914-013120-bae1   no User-Agent
    [1/3] cbsa 10100:  0 polygons, 17 ZCTAs, 0.0 industrial sq mi
    [2/3] cbsa 10140:  0 polygons, 20 ZCTAs, 0.0 industrial sq mi
    [3/3] cbsa 10180:  0 polygons, 23 ZCTAs, 0.0 industrial sq mi

  logs/run-20260914-013359-4665   HEADERS = {"User-Agent": "siting-atlas/..."}
    [1/3] cbsa 10100: 57 polygons, 17 ZCTAs, 1.3 industrial sq mi
    [2/3] cbsa 10140:  0 polygons, 20 ZCTAs, 0.0 industrial sq mi
    [3/3] cbsa 10180: 59 polygons, 23 ZCTAs, 2.7 industrial sq mi
```

Fix: `HEADERS` at `osm_landuse.py:77`. Identify yourself.

**Note that 10140 still returns zero after the fix**, and on the current
evidence we cannot say whether Aberdeen, Washington genuinely has no
`landuse=industrial` polygon or whether that one query also failed. A
zero-versus-failure distinction the caller cannot make is the general shape of
this whole exercise, and `fetch_cbsa` was later changed to abort a metro
outright rather than return a partial answer for exactly that reason.

### 2.2 HTTP 504 on large bounding boxes — also reported as "0 polygons"

Atlanta (CBSA 12060) spans about 1.6 degrees and returned **504 Gateway
Timeout** on all three attempts. Overpass charges by the area swept and the
geometry returned, so the fix is smaller queries, not a longer timeout:
`TILE_DEGREES = 0.5` splits a metro bbox into a grid before querying. Atlanta
becomes 20 tiles; Bridgeport-Stamford (11260) becomes 84.

### 2.3 Areas computed in degrees are not areas

TIGER ships in EPSG:4269, which is degrees. A polygon area in square degrees
shrinks as you move north and is not an area in any unit. Everything is
reprojected to **EPSG:5070**, the Albers equal-area conic for the continental
US, before `.area` is taken, and divided by 2,589,988.11 to get square miles.

This one never reached a run — it was caught in review — but it is the failure
that would have been hardest to notice downstream, because the resulting
numbers are positive, ordered roughly correctly within a metro, and wrong by a
latitude-dependent factor between metros.

## 3. Why it is blocked

Overpass is a free shared service. `GET /api/status` on the main instance
reports "Rate limit: 2" — two concurrent slots for the whole world. The module
is deliberately polite: one request at a time, `PAUSE = 10.0` seconds between
them, three attempts with quadratic backoff, every response cached to
`data/raw/osm_landuse/` by CBSA so a re-run costs nothing.

It is not enough. From `logs/run-20260914-024151-e68b`, the last and most
patient attempt:

```
  19:42:41  [1/62] cbsa 10420: 906 polygons, 49 ZCTAs, 22.4 industrial sq mi
  19:42:50  cbsa 11260 tile  1/84  attempt 1/3 failed: HTTP 429 Too Many Requests
  19:43:23  cbsa 11260 tile  2/84  attempt 1/3 failed: HTTP 504 Gateway Timeout
  19:44:17  cbsa 11260 tile  4/84  attempt 1/3 failed: HTTP 429 Too Many Requests
  19:45:01  cbsa 11260 tile  6/84  attempt 1/3 failed: HTTP 429 Too Many Requests
  19:45:22  cbsa 11260 tile  6/84  attempt 2/3 failed: HTTP 429 Too Many Requests
  19:46:03  cbsa 11260 tile  6/84  attempt 3/3 failed: HTTP 503 Bad Gateway
  19:47:33  cbsa 11260: tile 6 of 84 failed; discarding the metro rather
            than reporting a partial area
```

One metro of 62 completed in six minutes; the second failed after five. The
tiling that fixed the 504s multiplied the request count by up to 84, which
walked straight into the rate limit. **The two fixes are in tension and the
module currently has no setting that satisfies both.**

`fetch_cbsa` aborts a whole CBSA when any tile fails every attempt, rather than
returning the tiles it has. That is the right call — a partial answer is a
silent understatement of industrial land in one corner of one metro, and
silent understatement is worse than a visible gap — but it means a single
unlucky tile in 84 discards the metro.

## 4. What is actually on disk

```
  data/interim/osm_landuse.parquet    60 rows, 3 columns
                                      CBSAs 10100 / 10140 / 10180 (Aberdeen SD,
                                      Aberdeen WA, Abilene TX) — the --limit 3
                                      smoke test, alphabetically first, chosen
                                      because they are small, NOT because they
                                      matter
                                      18 of 60 ZCTAs have industrial_sqmi > 0
                                      max 0.997 sq mi, median 0.000

  data/raw/osm_landuse/10420.json     1.1 MB, Akron OH, 906 polygons.
                                      The only cached metro of the 62 the
                                      choice model needs.
```

**No model reads either.** `osm_landuse.parquet` is not joined into the panel,
is not in `ATTRACTIONS` or `CBP_ATTRACTIONS`, and appears in no report. The
three ZCTA-level numbers above should not be quoted for anything: they are a
functional test that the pipeline produces plausibly-shaped output, on three
metros nobody cares about.

## 5. What to do next

In order of cost.

```
  1  A LOCAL EXTRACT, not the API.  Geofabrik publishes per-state .osm.pbf
     files and data/raw/geofabrik/rhode-island.osm.pbf is already on disk
     from an earlier experiment, along with the osmium bindings in the
     venv.  A national extract is a few GB and a few hours of local CPU
     with no rate limit, no 429, no 504 and no politeness budget.  This is
     the obvious answer and the Overpass route should probably not be
     retried.
  2  IF OVERPASS IS RETRIED: raise PAUSE well above 10s, drop ATTEMPTS
     backoff in favour of honouring Retry-After, and make the tile grid
     adaptive -- split only on a 504, rather than pre-splitting every
     metro into 84 pieces and guaranteeing a 429.
  3  REGISTER THE SOURCE.  osm_landuse is not in ingest/sources.py, not in
     data/raw/manifest.jsonl and not in the agent pipeline.  Like
     cbp_detail it bypasses the project's own provenance rule; see
     CBP_DETAIL.md section 6.
  4  ONLY THEN evaluate it.  Whether industrial area beats or complements
     the warehousing establishment count is an open empirical question and
     nothing in this document bears on it.
```

## 6. How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.osm_landuse --limit 3
```

Three metros, about 100 seconds, and it will either reproduce §4 or show that
Overpass has changed its mind. Without `--limit` it restricts to the 62 CBSAs
that contain a facility and will not finish; `--all-cbsas` is roughly eight
hours of queries for data no model reads.

Cached responses are reused, so deleting `data/raw/osm_landuse/10420.json` is
the only way to re-test the Akron path.

## 7. Related

- [`CBP_DETAIL.md`](CBP_DETAIL.md) — the establishment-count proxy this was meant to replace.
- [`osm.md`](osm.md) — the registered OSM road-network source, a different extract.
