# Week 9 of 12 — What it costs to put a parcel on a doorstep

> **Week 9 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Forget prediction. Can free public data price the operation itself? |
| **Run it** | `bash run_week.sh 09` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make cost — recomputes all five scenarios offline |
| **Measured** | 52s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/cost_report.json` · run `20260929-203119-8afb` · built 2026-09-29 |

## What this stage does
A Daganzo continuous approximation. Distance per stop is

    d = (k / sqrt(density)) * rho  +  2L / C

— a local term that falls as one over the square root of stop density, plus
a line haul amortised over the tour. Road geometry, wages and population
density, with no operator disclosure of any kind.

This is the week where the answer is yes. It is also the week to be clear
about what "works" means: the method is published, every parameter is
sourced or explicitly flagged as unsourced, and the result survives five
stress scenarios. It has **not** been validated against the operator's
realised costs, because nobody publishes those.

This version still places depots by a p-median solve. Week 10 removes that
assumption.

## What came back

| Measure | Value | Read from |
|---|---|---|
| ZCTAs costed | **2,333** | `cost_report.baseline.zctas` |
| Median cost per parcel | **$1.0830** | `cost_report.baseline.median_cost_per_parcel` |
| p10 / p90 | **$0.98 / $1.42** | `cost_report.baseline.p10, p90` |
| Scenarios | **5** | `cost_report top-level scenario keys` |

## What this week does *not* establish

- SUPERSEDED by week 10. This run places 334 depots by a p-median solve — buildings the operator never chose. It is kept here because the before/after is itself the result.
- Not validated against realised costs. No operator publishes them, so the model is checkable but not verified.

## Read next

- [`docs/ALGORITHMS.md`](../../../../siting-atlas/docs/ALGORITHMS.md) — the Daganzo approximation and its regime of validity

---

[← Week 8](WEEK-08.md) · [Index](../README.md) · [Week 10 →](WEEK-10.md)
