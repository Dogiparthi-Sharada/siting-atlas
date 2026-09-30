# Week 12 of 12 — The artefact itself

> **Week 12 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Can a stranger clone this, run it, and get the same numbers — and can they tell when they have not? |
| **Run it** | `bash run_week.sh 12` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make test && make reproduce |
| **Measured** | 463s on the author's machine, offline, no API keys — 694 tests passed, 2 xfailed, then the full offline reproduction |
| **Artefact** | `outputs/metrics/scope.json` · run `20260929-203415-1d43` · built 2026-09-29 |
| **Artefact** | `outputs/metrics/viz_report.json` · run `20260929-203421-5a9e` · built 2026-09-29 |

## What this stage does
The deliverable is not the finding, it is the thing that lets someone check
the finding. Offline reproduction from a clone, no API keys; a test suite;
a pre-registration seal verified in CI; figures that read their numbers
from artefacts rather than carrying typed-in values; and an IEEE-format
write-up.

That last rule has a history. This project shipped a figure with nine
hand-entered values and a fabricated confidence band. It found it in its
own audit, fixed it, and the remedy was not "be more careful" but "make it
impossible" — a figure now either reads from an artefact or carries no
numbers at all. The same rule generates the twelve pages you are reading.

**The honest close.** Three of the project's four original claims are still
ambitions; only the artefact claim and the explainability-ceiling claim are
evidenced. Saying so is the point.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Panel shipped | **1,081,312 rows, 15.3 MB** | `scope.panel` |
| Reproduction | **offline, no API keys** | `Makefile: reproduce` |

## What this week does *not* establish

- Matplotlib PNGs are not byte-reproducible — embedded timestamps and freetype version. Figure checks verify existence and provenance, not bytes. The .docx build IS byte-reproducible.
- Reproduction starts at L3. Re-deriving the panel itself is week 1-4 territory and needs ~4 GB plus three API keys.

## Read next

- [`docs/REPRODUCE.md`](../../../../siting-atlas/docs/REPRODUCE.md) — the reproduction contract
- [`docs/STATUS.md`](../../../../siting-atlas/docs/STATUS.md) — the measured state of everything, with a run_id behind every number
- [`paper/`](../../../../siting-atlas/paper/) — the IEEE write-up

---

[← Week 11](WEEK-11.md) · [Index](../README.md)
