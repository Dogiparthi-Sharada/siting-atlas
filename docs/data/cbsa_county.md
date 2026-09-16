# OMB metropolitan area delineation, 2023

**Registry key:** `cbsa_county`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | US Census Bureau / OMB |
| Grain | `county` |
| Role in the model | Defines which counties constitute each metro area |
| Update cadence | revised every few years |
| Reporting lag | not applicable |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html
```

## Endpoint

```
https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Round trip | 0.13s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

Metro membership must come from the official delineation, not from whichever ZCTAs happen to appear in a commercial rent index.

Using Zillow's `Metro` column as the pilot filter was measured against this file and drops 35% of pilot-metro ZCTAs - and the dropped ones have a median population of 4,731 against 30,589 for those kept. Zillow publishes a rent index only where there are enough listings, so the filter silently selects for density. Those low-density fringe ZCTAs are precisely where a same-day expansion decision is contested; the dense ones are foregone conclusions. Filtering on them would be selecting the sample on something correlated with the outcome.

So membership comes from here, and rent stays a feature with honest missingness rather than becoming a filter.

The 2023 vintage uses Connecticut's nine planning regions. The ZCTA-to-county file is still 2020 and uses the eight old counties, so Connecticut will not join - the same known gap recorded under `bps_county`, and no pilot metro is affected.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
