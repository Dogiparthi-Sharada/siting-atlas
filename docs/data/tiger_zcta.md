# TIGER/Line ZCTA boundaries, 2020 vintage

**Registry key:** `tiger_zcta`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `zcta` |
| Role in the model | Geometry for spatial joins, centroids and distance bands |
| Update cadence | decennial, with annual reissues |
| Reporting lag | not applicable |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.census.gov/geographies/mapping-files.html
```

## Endpoint

```
https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/tl_2020_us_zcta520.zip
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `application/zip` |
| Round trip | 0.21s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

~520 MB. Vintage is pinned: mixing 2010 and 2020 ZCTA boundaries silently corrupts a time series.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
