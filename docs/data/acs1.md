# American Community Survey, 1-year estimates

**Registry key:** `acs1`  ·  **Status:** NEEDS KEY

> Reachable, but the provider requires a free API key. The pipeline skips it with a remediation message until the key is present.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `metro` |
| Role in the model | Recent demographic movement at a shorter lag (metro context) |
| Update cadence | annual |
| Reporting lag | 9 months |
| Licence | US Government Work (public domain) |
| Credential | `$CENSUS_API_KEY` |

Provider documentation:

```
https://www.census.gov/data/developers/data-sets/acs-1year.html
```

## Endpoint

```
https://api.census.gov/data/{year}/acs/acs1
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `needs_key` |
| HTTP status | 206 |
| Content-Type | `text/html` |
| Round trip | 0.46s |
| Detail | HTML body on a 200 — credential likely required |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Fields used

- `B01003_001E`
- `B19013_001E`

## Notes

Published only for areas above 65,000 population.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
