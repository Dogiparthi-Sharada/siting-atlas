# Week 10 of 12 — Replacing the model's depots with real buildings

> **Week 10 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | What changes when the depot layer stops being a solve and becomes the buildings the operator actually runs? |
| **Run it** | `bash run_week.sh 10` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | python -m siting_atlas.cost.station_runner — every scenario, offline |
| **Measured** | 17s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/cost_by_station.json` · run `20260929-195014-5235` · built 2026-09-29 |

## What this stage does
Week 9's p-median is a good solve of the wrong problem. Once the facility
panel carries geocoded delivery stations, the assumption can be DELETED
rather than improved: depots are those buildings, there is no placement
step, and no capacity story to apologise for.

The headline moves the "wrong" way, and that is the finding. A p-median
minimises demand-weighted distance by construction; real siting is
constrained by land, labour, zoning and lease terms. The gap between the
two is what the increase measures.

Only address-geocoded stations are used. The rest carry a ZCTA-centroid
fallback, and a centroid is not a building — using one would put a depot in
the middle of its own catchment and drive that line haul to roughly zero,
which is the single most cost-reducing error available in this model.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Stations used | **501** | `cost_by_station.stations.geocoded_used` |
| Excluded as centroid fallbacks | **192** | `...stations.excluded_zcta_centroid_fallback` |
| ZCTAs costed | **8,037** | `cost_by_station.coverage.costed_zctas` |
| US households covered | **57.81%** | `cost_by_station.coverage.costed_household_share` |
| Median cost per parcel | **$1.1389** | `cost_by_station.scenarios.baseline.median_cost_per_parcel` |
| Median line haul | **9.09 mi** | `...scenarios.baseline.median_linehaul_miles` |
| Change against week 9 | **+5.16%** | `the two artefacts, divided` |

## What this week does *not* establish

- Coverage is now decided by where the operator built, not by a chosen study area. A ZCTA more than 15 miles from any station is left uncosted rather than costed badly.
- Twenty stations have no ZCTA inside the catchment and contribute to no cost, so the map draws more stations than the cost tables price.

## Read next

- [`docs/NUMBERS.md`](../../../../siting-atlas/docs/NUMBERS.md) — the full before/after, section 10.3

---

[← Week 9](WEEK-09.md) · [Index](../README.md) · [Week 11 →](WEEK-11.md)
