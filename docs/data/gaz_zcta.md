# Census Gazetteer, ZCTA national file

**Registry key:** `gaz_zcta`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `zcta` |
| Role in the model | Centroid and land area for every ZCTA - the geometry the cost model actually needs |
| Update cadence | annual |
| Reporting lag | not applicable |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.census.gov/geographies/reference-files.html
```

## Endpoint

```
https://www2.census.gov/geo/docs/maps-data/data/gazetteer/{year}_Gazetteer/{year}_Gaz_zcta_national.zip
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `application/zip` |
| Round trip | 0.18s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Fields used

- `GEOID`
- `ALAND_SQMI`
- `INTPTLAT`
- `INTPTLONG`

## Notes

1 MB, versus 520 MB for the full TIGER shapefile. Daganzo needs area and a centroid, not polygon detail, so the shapefile is only pulled when a choropleth is rendered.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
