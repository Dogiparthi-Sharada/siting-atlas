# Week 5 of 12 — One table every model reads

> **Week 5 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | How do fourteen differently-shaped files become something three different models can all query? |
| **Run it** | `bash run_week.sh 05` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: rebuilding needs the whole L0 source cache, so this reads the shipped reports |
| **What runs** | reads the warehouse and panel reports |
| **Artefact** | `outputs/metrics/warehouse_report.json` · run `20260913-163016-3b33` · built 2026-09-13 |
| **Artefact** | `outputs/metrics/panel_report_expanded.json` · run `20260915-195503-5761` · built 2026-09-15 |

> **Where we got to.** One panel, 1,081,312 rows, 50 columns — and everything above it is ignorant of where the bytes came from.

## What this stage does
Two layers, and the split is the point.

**L1** turns each source into one typed parquet and does nothing else — no
joins, no derived columns. **L2** is a DuckDB star schema: conformed
dimensions for ZCTA, county and date, with facts hanging off them. **L3** is
the panel, one row per ZIP-code area per quarter.

The panel ships with the repository. That single decision is what makes an
offline ten-minute reproduction possible instead of a day of downloads, and
it is why a reader can check our numbers rather than deciding not to bother.

Read `enabled_cells` twice. The panel is large, but the subset where a
facility could plausibly open AND every covariate is present is far smaller
— and that is the number the models are fitted on. Quoting the panel row
count as a sample size would overstate the evidence by more than an order
of magnitude, and we say so wherever the figure appears.

## What came back

| Measure | Value | Read from |
|---|---|---|
| dim_zcta | **33,791** | `warehouse_report.tables.dim_zcta` |
| dim_county | **3,211** | `warehouse_report.tables.dim_county` |
| dim_date | **32** | `warehouse_report.tables.dim_date` |
| dim_scenario | **1** | `warehouse_report.tables.dim_scenario` |
| fact_zcta_year | **270,328** | `warehouse_report.tables.fact_zcta_year` |
| Panel rows | **1,081,312** | `panel_report_expanded.rows` |
| Columns | **50** | `panel_report_expanded.cols` |
| Enabled cells | **200,219** | `panel_report_expanded.enabled_cells` |

## The risk we flagged

A silent join error here corrupts every downstream model at once, and would be invisible in the results. The defence is the layer split: L1 does no joins, so a parsing bug is always attributable to exactly one source file.

## What this week does *not* establish

- ZCTA geography is the 2020 TIGER vintage only. ZCTAs are redrawn each decade, so a cross-decade panel would need a crosswalk this schema does not carry.
- Fifty columns are carried. Week 10 shows how few survive contact with a model.

## Read next

- [`docs/ARCHITECTURE.md`](../../../../siting-atlas/docs/ARCHITECTURE.md) — the six layers and what each owns
- [`docs/MODEL_SPEC.md`](../../../../siting-atlas/docs/MODEL_SPEC.md) — the panel schema, column by column

---

[← Week 4](WEEK-04.md) · [Index](../README.md) · [Week 6 →](WEEK-06.md)
