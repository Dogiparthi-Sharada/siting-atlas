# Regional fuel and industrial electricity prices

**Registry key:** `eia_prices`  ·  **Status:** NEEDS KEY

> Reachable, but the provider requires a free API key. The pipeline skips it with a remediation message until the key is present.

## At a glance

| | |
|---|---|
| Provider | US Energy Information Administration |
| Grain | `region` |
| Role in the model | Fuel and energy capital bucket |
| Update cadence | monthly |
| Reporting lag | 2 months |
| Licence | US Government Work (public domain) |
| Credential | `$EIA_API_KEY` |

Provider documentation:

```
https://www.eia.gov/opendata/
```

## Endpoint

```
https://api.eia.gov/v2/electricity/retail-sales/data/
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `blocked` |
| HTTP status | 403 |
| Content-Type | `application/json` |
| Round trip | 0.28s |
| Detail | HTTP 403 refused |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

Free key from https://www.eia.gov/opendata/register.php. An unauthenticated request returns HTTP 403, which reads like a network block but is the missing-key response - the probe records 'blocked' until a key is present. Pages are capped at 5,000 rows and the cap is silent, so the extractor follows offsets rather than trusting one response.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
