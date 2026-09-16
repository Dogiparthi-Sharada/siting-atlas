# Zillow Observed Rent Index, ZIP level

**Registry key:** `zillow_zori`  ·  **Status:** BLOCKED

> The host refuses requests from this network. Download manually and place the file in `data/external/`.

## At a glance

| | |
|---|---|
| Provider | Zillow Research |
| Grain | `zip` |
| Role in the model | Disposable income proxy and commercial land-cost proxy |
| Update cadence | monthly |
| Reporting lag | 1 months |
| Licence | Zillow Research terms — free for non-commercial research |
| Credential | none |

Provider documentation:

```
https://www.zillow.com/research/data/
```

## Endpoint

```
https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `unreachable` |
| HTTP status | n/a |
| Content-Type | `n/a` |
| Round trip | 0.04s |
| Detail | ProxyError: HTTPSConnectionPool(host='files.zillowstatic.com', port=443): Max retries exceeded with url: /research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_m |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

Egress proxy returns HTTP 503 for files.zillowstatic.com. Download manually and place in data/external/.

## Acquisition procedure

1. Open https://www.zillow.com/research/data/ in a browser.
2. Download the file described above.
3. Place it in `data/external/zillow_zori/` keeping the original filename.
4. Record the download date and the source URL in `data/raw/manifest.jsonl` so provenance stays complete.

The pipeline treats a missing manual source as a skipped stage with a stated reason, not as a failure — the rest of the run still executes.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
