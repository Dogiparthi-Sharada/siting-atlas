# Week 1 of 12 — Scope and feasibility

> **Week 1 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Is this answerable at all from free public data — and at what geographic grain? |
| **Run it** | `bash run_week.sh 01` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: scoping is a decision, not a computation; its record is ROADMAP.md and ALTERNATIVES.md |
| **What runs** | reads the study-scope artefact and the options document |
| **Artefact** | `outputs/metrics/scope.json` · run `20260930-023242-2c53` · built 2026-09-30 |

> **Where we got to.** Question fixed, and feasibility proven before we wrote modelling code.

## What this stage does
Before anything is modelled, two questions have to be settled: what exactly
is being predicted, and is the evidence for it obtainable by someone with no
special access.

We fixed the unit as the ZIP-code area (ZCTA) because it is the finest grain
most free US data publishes at — not because it is the natural unit of a
siting decision, which is a parcel. That gap is a limitation we carried all
semester and stated every time it mattered.

The scope artefact is the honest size of the thing: how many metros, how
many counties, how many ZCTAs, and how big the decision space is if you
treat every ZCTA as a yes/no. That last number is why an exhaustive search
was never on the table.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Pilot metros | **10** | `scope.pilot.metros` |
| Pilot counties | **84** | `scope.pilot.counties` |
| Pilot ZCTAs | **2,413** | `scope.pilot.zctas` |
| ZCTAs nationally | **33,791** | `scope.national_zctas` |
| Decision space | **2^2,413** | `scope.compute.search_space_label` |
| Options written up before choosing | **5** | `docs/ALTERNATIVES.md '## Option'` |

## The risk we flagged

That the target variable — where a firm opens a building — simply does not exist in public form. We checked first rather than discovering it in week 8.

## What this week does *not* establish

- A ZCTA is a postal-delivery construct, not a polygon, and it is coarser than the parcel a siting decision is actually made over. Chosen for data availability, not for fit.
- The pilot scope is ten metros. The national panel came later, and several early results are pilot-only — week 11 says which.

## Read next

- [`docs/ROADMAP.md`](../../../../siting-atlas/docs/ROADMAP.md) — what we set out to do, written first
- [`docs/ALTERNATIVES.md`](../../../../siting-atlas/docs/ALTERNATIVES.md) — the five directions considered and why four were dropped

---

[Index](../README.md) · [Week 2 →](WEEK-02.md)
