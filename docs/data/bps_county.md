# Building Permits Survey, county annual

**Registry key:** `bps_county`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau |
| Grain | `county` |
| Role in the model | Leading indicator — construction precedes population |
| Update cadence | monthly, with annual summaries |
| Reporting lag | 2 months |
| Licence | US Government Work (public domain) |
| Credential | none |
| Vintages fetched | 9 (2017–2025) |

Provider documentation:

```
https://www.census.gov/construction/bps/
```

## Endpoint

```
https://www2.census.gov/econ/bps/County/co{yy}12y.txt
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `text/plain` |
| Round trip | 0.18s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

The forward signal that offsets the ACS reporting lag.

One file per year, and every vintage is fetched: a year-over-year feature is impossible from a single year. Pulling only the latest file produced a silently all-null `permits_yoy_pct` - no error, no warning, just a dead column.

Two coverage breaks are real and are handled rather than smoothed over:

1. **County universe widens in 2022.** Vintages 2017-2021 report ~745 counties; 2022 onward report ~3,021. The earlier subset is the large counties - about 68% of national permit volume - so the series is not wrong, just narrower. Year-over-year is computed by a LEFT JOIN on year-1, so a county with no prior-year row yields NULL rather than a fabricated spike. Coverage of `permits_yoy_pct` is therefore ~33% for 2018-2022 and ~93% from 2023.

2. **Connecticut changes geography in 2023.** The eight counties (09001-09015) are replaced by nine planning regions (09110-09190), with no CT rows at all in the 2022 file. The ZCTA-to-county crosswalk still uses the old codes, so Connecticut ZCTAs carry permits for 2017-2021 and NULL from 2023. No pilot or hold-out metro is in Connecticut, so this is recorded as a known gap rather than repaired.

The file layout itself is stable across all nine vintages - 30 fields, the same two merged header rows. Only the county-name padding width changed, which is why one parser reads them all.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
