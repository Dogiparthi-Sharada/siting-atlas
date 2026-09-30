# Week 1 of 12 — Where every number comes from

> **Week 1 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Can a stranger fetch every ingredient of this project themselves, and is each one licensed for that? |
| **Run it** | `bash run_week.sh 01` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: re-fetching needs three API keys and ~4 GB of downloads |
| **What runs** | reads the probe and acquisition reports |
| **Artefact** | `outputs/metrics/source_probe.json` · run `20260912-doc-verify` · built 2026-09-12 |
| **Artefact** | `outputs/metrics/acquire_report.json` · run `20260912-103506-b1e8` · built 2026-09-12 |

## What this stage does
Fourteen public sources, each fetched into a content-addressed cache with a
SHA-256 per file, so a later run can prove it read the same bytes.

`make probe` checks every endpoint is still alive BEFORE anything is
downloaded. That ordering is the cheap half of reproducibility: a project
that only discovers a dead URL after four gigabytes cannot tell a moved
source from a broken parser.

Six sources cannot be fetched automatically and must be placed by hand. Two
of those are licensed and are deliberately not redistributed.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Sources probed | **14** | `source_probe.results` |
| Probed on | **2026-09-12** | `source_probe.probed_on` |
| Sources acquired | **13** | `acquire_report.results` |

## What this week does *not* establish

- Two sources are licensed — a paid CSV and two industry PDFs — and are excluded from the public repository. The DERIVED tables built from them ship; the originals do not.
- Some sources are single-vintage snapshots that will never reproduce byte-for-byte if re-fetched later. `docs/DATA_SOURCES.md` names which ones.

## Read next

- [`docs/DATA_SOURCES.md`](../../../../siting-atlas/docs/DATA_SOURCES.md) — every source, its licence, and how to fetch it

---

[Index](../README.md) · [Week 2 →](WEEK-02.md)
