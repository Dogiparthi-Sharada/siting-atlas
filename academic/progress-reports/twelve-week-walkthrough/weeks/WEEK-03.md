# Week 3 of 12 — Data acquisition and provenance

> **Week 3 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Can a stranger fetch every ingredient themselves, and is each one licensed for that? |
| **Run it** | `bash run_week.sh 03` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: re-fetching needs three free API keys and about 4 GB of downloads |
| **What runs** | reads the reachability probe and the acquisition manifest |
| **Artefact** | `outputs/metrics/source_probe.json` · run `20260912-doc-verify` · built 2026-09-12 |
| **Artefact** | `outputs/metrics/acquire_report.json` · run `20260912-103506-b1e8` · built 2026-09-12 |

> **Where we got to.** Fourteen sources in a content-addressed cache, one SHA-256 per file. Licences audited; two paid sources will not be redistributed.

## What this stage does
Fourteen public sources, each hashed on the way in, so a later run can prove
it read the same bytes rather than hoping so.

The ordering matters more than it sounds. `make probe` tests every endpoint
before `make acquire` fetches anything. A project that discovers a dead URL
only after four gigabytes cannot tell a moved source from a parser bug, and
will spend a day on the wrong one.

Six sources cannot be fetched automatically and must be placed by hand. Two
of those are licensed — a paid CSV and two industry PDFs — and are
deliberately excluded from the public repository. The tables derived from
them ship; the originals do not. That is the licence being respected, not a
gap in the method.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Sources probed | **14** | `source_probe.results` |
| Probed on | **2026-09-12** | `source_probe.probed_on` |
| Sources acquired | **13** | `acquire_report.results` |

## The risk we flagged

A source moves, changes vintage, or turns out to forbid redistribution after we have built on it. `make probe` checks reachability BEFORE any download, so a dead URL is never confused with a broken parser.

## What this week does *not* establish

- Some sources are single-vintage snapshots that will not reproduce byte-for-byte if re-fetched later. `docs/DATA_SOURCES.md` names which ones.
- Hashing proves we read the same bytes. It does not prove the publisher was right.

## Read next

- [`docs/DATA_SOURCES.md`](../../../../siting-atlas/docs/DATA_SOURCES.md) — every source, its licence, and how to fetch it

---

[← Week 2](WEEK-02.md) · [Index](../README.md) · [Week 4 →](WEEK-04.md)
