# Week 11 of 12 — Five programmes that were retired

> **Week 11 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. This week has no metrics artefact: its table is the archive directory, read at build time, so adding or removing a programme changes the page with nobody editing it.

| | |
|---|---|
| **Question** | What was built, run, and then taken out — and why is it still in the repository? |
| **Run it** | `bash run_week.sh 11` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: there is nothing to recompute — the archive is a directory, and it is read at build time |
| **What runs** | lists experiments/ and its notes |
| **Directory** | `experiments/` |

## What this stage does
A survival model, a gravity formulation of network pull, two covariate
transforms and a portfolio optimiser. Each was built, run, and retired.
Their code, artefacts and notes are archived rather than deleted, and
nothing in `src/` imports any of them.

Keeping them is a deliberate choice about what a research artefact is for.
A repository that shows only what worked teaches the reader nothing about
the search, and invites them to repeat it. The archive records what each
programme asked and what came back.

Worth defending directly: retiring a programme is not the same as it having
been a mistake. The survival model was the right thing to try given what
was known at the time, and knowing it does not work here IS a result.

The table below counts **seven directories, not seven programmes**. Five
are the retired programmes above; `retired-tests` holds the tests that
retired with them, and `superseded-artefacts` holds outputs a later run
replaced — kept so a number quoted in an older document can still be
traced to the artefact it came from.

## What came back

| Measure | Value | Read from |
|---|---|---|
| agent-demo | **25 files** | `experiments/agent-demo/` |
| gravity-network | **19 files** | `experiments/gravity-network/` |
| hazard-model | **15 files** | `experiments/hazard-model/` |
| percapita-logrel | **14 files** | `experiments/percapita-logrel/` |
| portfolio-optimiser | **17 files** | `experiments/portfolio-optimiser/` |
| retired-tests | **12 files** | `experiments/retired-tests/` |
| superseded-artefacts | **5 files** | `experiments/superseded-artefacts/` |
| Directories in the archive | **7** | `experiments/` |

## What this week does *not* establish

- Retired code is not maintained and is not covered by the test suite. It is evidence of a search, not a working component.

## Read next

- [`experiments/README.md`](../../../../siting-atlas/experiments/README.md) — what each programme asked and what came back
- [`docs/DECISION_LOG.md`](../../../../siting-atlas/docs/DECISION_LOG.md) — when each was retired, and on what evidence

---

[← Week 10](WEEK-10.md) · [Index](../README.md) · [Week 12 →](WEEK-12.md)
