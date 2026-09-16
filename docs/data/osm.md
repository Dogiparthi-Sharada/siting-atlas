# OpenStreetMap road network extracts

**Registry key:** `osm`  ·  **Status:** OPEN

> Downloads with no credential. `make acquire` fetches it.

## At a glance

| | |
|---|---|
| Provider | Geofabrik / BBBike |
| Grain | `network` |
| Role in the model | Drive times — used once, offline, then deleted |
| Update cadence | daily |
| Reporting lag | 0 months |
| Licence | Open Database License (ODbL) — attribution required |
| Credential | none |

Provider documentation:

```
https://download.geofabrik.de/
```

## Endpoint

```
https://download.geofabrik.de/north-america/us/{state}-latest.osm.pbf
```

Placeholders such as `{year}` are substituted from the pinned vintage map in `ingest/acquire.py`. Vintages are pinned deliberately: a silent vintage change is the failure mode that corrupts a panel without raising.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `open` |
| HTTP status | 206 |
| Content-Type | `application/octet-stream` |
| Round trip | 0.82s |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

Infrastructure rather than an analytical source: consumed once to produce the origin-destination matrix, after which every artefact is deleted (ADR-0002).

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
