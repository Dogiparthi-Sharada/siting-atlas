# Week 4 of 12 — The panel every model reads

> **Week 4 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | What is the unit of analysis, and how much of the country does it actually cover? |
| **Run it** | `bash run_week.sh 04` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: rebuilding the panel needs the whole L0-to-L2 chain |
| **What runs** | reads the panel report and the study-scope artefact |
| **Artefact** | `outputs/metrics/panel_report_expanded.json` · run `20260915-195503-5761` · built 2026-09-15 |
| **Artefact** | `outputs/metrics/scope.json` · run `20260929-203415-1d43` · built 2026-09-29 |

## What this stage does
One row per ZIP-code area per quarter. This is the object all three L4
models consume, and it ships with the repository — the single decision that
makes an offline ten-minute reproduction possible instead of a day of
downloads.

`enabled_cells` is worth reading twice. The panel is large, but the subset
where a facility could plausibly open AND every covariate is present is far
smaller, and it is that number the models are actually fitted on. Quoting
the panel row count as the sample size would overstate the evidence by more
than an order of magnitude.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Panel rows | **1,081,312** | `panel_report_expanded.rows` |
| Columns | **50** | `panel_report_expanded.cols` |
| Enabled cells | **200,219** | `panel_report_expanded.enabled_cells` |
| ZCTAs nationally | **33,791** | `scope.national_zctas` |
| Pilot ZCTAs | **2,413** | `scope.pilot.zctas` |
| On disk | **15.3 MB** | `scope.panel.megabytes` |

## What this week does *not* establish

- A ZCTA is a postal-delivery construct, not a polygon. It is the finest grain most free US data publishes at, which is why it was chosen, and it is coarser than a parcel or a building.
- Fifty columns are carried. Week 8 shows how few survive.

## Read next

- [`docs/MODEL_SPEC.md`](../../../../siting-atlas/docs/MODEL_SPEC.md) — the panel's schema, column by column

---

[← Week 3](WEEK-03.md) · [Index](../README.md) · [Week 5 →](WEEK-05.md)
