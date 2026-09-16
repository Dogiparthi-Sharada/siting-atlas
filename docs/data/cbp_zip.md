# County Business Patterns, ZIP-code totals

**Registry key:** `cbp_zip`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `zip` |
| Role in the model | Retail density / competitive pull (administrative universe) |
| Update cadence | annual |
| Reporting lag | 18 months |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.census.gov/programs-surveys/cbp.html
```

## Endpoint

```
https://www2.census.gov/programs-surveys/cbp/datasets/{year}/zbp{yy}totals.zip
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `application/zip` |
| Round trip | 0.2s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

Replaces a commercial business directory: bulk download, no key, no rate limit, and an administrative universe rather than a self-selected one.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
