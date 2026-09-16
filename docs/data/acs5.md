# American Community Survey, 5-year estimates

**Registry key:** `acs5`  ·  **Status:** NEEDS KEY

> Reachable, but the provider requires a free API key. The pipeline skips it with a remediation message until the key is present.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `zcta` |
| Role in the model | Demographics, income, age, household size (level features) |
| Update cadence | annual |
| Reporting lag | 21 months |
| Licence | US Government Work (public domain) |
| Credential | `$CENSUS_API_KEY` |

Provider documentation:

```
https://www.census.gov/data/developers/data-sets/acs-5year.html
```

## Endpoint

```
https://api.census.gov/data/{year}/acs/acs5
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `unreachable` |
| HTTP status | n/a |
| Content-Type | `n/a` |
| Round trip | 25.38s |
| Detail | ReadTimeout: HTTPSConnectionPool(host='api.census.gov', port=443): Read timed out. (read timeout=25) |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Fields used

- `B01003_001E`
- `B19013_001E`
- `B25077_001E`
- `B08201_001E`
- `B01002_001E`
- `B15003_022E`

## Notes

The query endpoint returns an HTML 'Missing Key' page with HTTP 200 when no key is supplied, which is why fetch() validates Content-Type. Keys are free and instant from https://api.census.gov/data/key_signup.html

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
