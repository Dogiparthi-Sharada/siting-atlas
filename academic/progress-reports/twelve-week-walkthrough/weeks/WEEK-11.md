# Week 11 of 12 — What does work — pricing the operation

> **Week 11 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Forget prediction. Can free public data price the operation itself — and what happens when we stop inventing where the depots are? |
| **Run it** | `bash run_week.sh 11` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make cost, then python -m siting_atlas.cost.station_runner |
| **Measured** | 49s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/cost_report.json` · run `20260930-022952-b4c0` · built 2026-09-30 |
| **Artefact** | `outputs/metrics/cost_by_station.json` · run `20260930-022558-76ae` · built 2026-09-30 |

> **Where we got to.** $1.14 to put a parcel on a doorstep, across 8,037 ZIP-code areas and 57.8% of US households — priced against 501 real buildings, from road geometry and wages alone.

## What this stage does
A Daganzo continuous approximation. Distance per stop is

    d = (k / sqrt(density)) * rho  +  2L / C

— a local term falling as one over the square root of stop density, plus a
line haul amortised over the tour. Road geometry, wages and population
density. No operator disclosure of any kind.

**The correction, which is the actual result of this week.** Version one
placed 334 depots by a p-median solve — buildings the operator never chose.
A p-median minimises demand-weighted distance *by construction*, so it was
quietly answering "what would this cost if sited optimally". Once the
facility panel carried geocoded stations, the assumption could be deleted
rather than improved: depots are those buildings, and there is no placement
step left to defend.

The headline moved the "wrong" way, and that is the point. The gap between
an optimal siting and a real one is what the increase measures.

Only address-geocoded stations are used. The rest carry a ZCTA-centroid
fallback, and a centroid is not a building — using one puts a depot in the
middle of its own catchment and drives that line haul to roughly zero,
which is the single most cost-reducing error available here.

**What "works" means.** The method is published, every parameter is sourced
or explicitly flagged as unsourced, and the result survives five stress
scenarios. It has **not** been validated against realised costs, because
nobody publishes those. Checkable, not verified.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Pilot ZCTAs (p-median depots) | **2,333** | `cost_report.baseline.zctas` |
| Pilot median | **$1.0830** | `cost_report.baseline.median_cost_per_parcel` |
| Real stations used | **501** | `cost_by_station.stations.geocoded_used` |
| ZCTAs costed against them | **8,037** | `cost_by_station.coverage.costed_zctas` |
| US households covered | **57.81%** | `cost_by_station.coverage.costed_household_share` |
| Median cost per parcel | **$1.1389** | `cost_by_station.scenarios.baseline.median_cost_per_parcel` |
| Median line haul | **9.09 mi** | `...scenarios.baseline.median_linehaul_miles` |
| Effect of using real buildings | **+5.16%** | `the two artefacts, divided` |

## The risk we flagged

We shipped a first version that placed depots by a p-median solve, then realised the depot layer was an ASSUMPTION we had been treating as a parameter. Finding your own unclassified assumption late is the risk; the response was to delete it rather than tune it.

## What this week does *not* establish

- Not validated against realised costs. No operator publishes them, so this is checkable but not verified.
- Coverage is decided by where the operator built, not by a chosen study area. A ZCTA more than 15 miles from any station is left uncosted rather than costed badly.
- Twenty stations have no ZCTA inside the catchment and contribute to no cost, so the map draws more stations than the cost tables price.

## Read next

- [`docs/ALGORITHMS.md`](../../../../siting-atlas/docs/ALGORITHMS.md) — the Daganzo approximation and its regime of validity
- [`docs/NUMBERS.md`](../../../../siting-atlas/docs/NUMBERS.md) — the full before and after, section 10.3

---

[← Week 10](WEEK-10.md) · [Index](../README.md) · [Week 12 →](WEEK-12.md)
