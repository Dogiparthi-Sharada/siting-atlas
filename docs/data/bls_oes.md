# Occupational Employment and Wage Statistics, metro

**Registry key:** `bls_oes`  ·  **Status:** BLOCKED

> The host refuses requests from this network. Download manually and place the file in `data/external/`.

## At a glance

| | |
|---|---|
| Provider | US Bureau of Labor Statistics |
| Grain | `metro` |
| Role in the model | Driver and warehouse wages (largest varying capital bucket) |
| Update cadence | annual |
| Reporting lag | 12 months |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.bls.gov/oes/tables.htm
```

## Endpoint

```
https://www.bls.gov/oes/special-requests/oesm{yy}ma.zip
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `blocked` |
| HTTP status | 403 |
| Content-Type | `text/html` |
| Round trip | 0.15s |
| Detail | HTTP 403 refused |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

bls.gov returns HTTP 403 to this environment even with a descriptive User-Agent. Download manually.

## Acquisition procedure

1. Open https://www.bls.gov/oes/tables.htm in a browser.
2. Download the file described above.
3. Place it in `data/external/bls_oes/` keeping the original filename.
4. Record the download date and the source URL in `data/raw/manifest.jsonl` so provenance stays complete.

The pipeline treats a missing manual source as a skipped stage with a stated reason, not as a failure — the rest of the run still executes.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
