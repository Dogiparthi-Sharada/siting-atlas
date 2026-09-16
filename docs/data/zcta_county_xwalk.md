# ZCTA-to-county relationship file, 2020

**Registry key:** `zcta_county_xwalk`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `zcta` |
| Role in the model | Joins county-grain sources (building permits, wages) down to ZCTA |
| Update cadence | decennial |
| Reporting lag | not applicable |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.census.gov/geographies/reference-files.html
```

## Endpoint

```
https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `text/plain` |
| Round trip | 0.16s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

A ZCTA can span several counties; the file carries the land area of each intersection so the join can be area-weighted rather than assigned to one county arbitrarily.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
