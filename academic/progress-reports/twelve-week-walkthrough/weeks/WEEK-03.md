# Week 3 of 12 — Typed layers and a star schema

> **Week 3 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | How do fourteen differently-shaped public files become one thing a model can query? |
| **Run it** | `bash run_week.sh 03` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: rebuilding the star schema needs the L0 source cache |
| **What runs** | reads the normalise and warehouse reports |
| **Artefact** | `outputs/metrics/normalise_report.json` · run `20260912-111233-13a9` · built 2026-09-12 |
| **Artefact** | `outputs/metrics/warehouse_report.json` · run `20260913-163016-3b33` · built 2026-09-13 |

## What this stage does
Two layers, and the split is the point.

**L1** turns each source into one typed parquet and does nothing else — no
joins, no derived columns — so a parsing bug is always attributable to
exactly one file. **L2** is a DuckDB star schema: conformed dimensions for
ZCTA, county and date, with facts hanging off them.

Everything above L2 is ignorant of where the bytes came from. That is why a
second operator, or a second country, would be a data swap rather than a
rewrite.

## What came back

| Measure | Value | Read from |
|---|---|---|
| dim_zcta | **33,791** | `warehouse_report.tables.dim_zcta` |
| dim_county | **3,211** | `warehouse_report.tables.dim_county` |
| dim_date | **32** | `warehouse_report.tables.dim_date` |
| dim_scenario | **1** | `warehouse_report.tables.dim_scenario` |
| fact_zcta_year | **270,328** | `warehouse_report.tables.fact_zcta_year` |

## What this week does *not* establish

- ZCTA geography is the 2020 TIGER vintage only. ZCTAs are redrawn each decade, so a cross-decade panel would need a crosswalk this schema does not carry.
- Rebuilding L2 needs the L0 cache, so this week inspects the shipped report rather than re-running the build.

## Read next

- [`docs/ARCHITECTURE.md`](../../../../siting-atlas/docs/ARCHITECTURE.md) — the six layers and what each owns

---

[← Week 2](WEEK-02.md) · [Index](../README.md) · [Week 4 →](WEEK-04.md)
