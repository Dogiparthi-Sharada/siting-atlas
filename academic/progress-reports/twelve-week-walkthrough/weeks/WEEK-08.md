# Week 8 of 12 — Why it failed — a screening rule you can run first

> **Week 8 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Was the failure about this model, or about what free public data can carry? And can you tell in advance? |
| **Run it** | `bash run_week.sh 08` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: a live covariate refit is about ninety minutes on two workers |
| **What runs** | reads the covariate search and the gravity-network arms (a live refit is ~90 minutes) |
| **Artefact** | `outputs/metrics/covariate_search.json` · run `20260915-235210-ff92` · built 2026-09-15 |
| **Artefact** | `experiments/gravity-network/artefacts/gravity_network.json` · run `20260915-210603-b780` · built 2026-09-15 |

## What this stage does
A conditional choice model can only use a covariate that varies INSIDE a
metro. Most free US public data is published at county grain, so across two
hundred candidate ZIP codes it arrives as a handful of distinct values. A
near-constant cannot rank anything, however large its real-world effect.

That gives a test you can run BEFORE fitting: measure each covariate's
within-metro coefficient of variation.

The rule runs **one way**. Low dispersion is sufficient for failure; high
dispersion is necessary but not sufficient. Stating it as a two-sided rule
would be the overclaim, and the empty middle band is what makes the
one-sided version worth anything.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Facilities in the search | **687** | `covariate_search.facilities` |
| Repeats | **50** | `covariate_search.repeats` |
| Terms screened | **21** | `gravity_network.terms.dispersion.mean_within_metro_cv` |
| Below cv 0.6 — all fail | **7** | `derived from the same field` |
| In the band cv 0.6 to 1.3 | **0** | `derived from the same field` |

## What this week does *not* establish

- Descriptive. 21 non-independent terms from one run — this is a rule of thumb worth checking on your own data, not an estimated threshold with a confidence interval.
- The empty band is an observation about THESE covariates. It is not a claim that no covariate can sit at cv 1.0.

## Read next

- [`docs/EXPERIMENTS.md`](../../../../siting-atlas/docs/EXPERIMENTS.md) — all 21 experiments and what each does NOT support
- [`experiments/gravity-network/`](../../../../siting-atlas/experiments/gravity-network/) — the arms behind the rule

---

[← Week 7](WEEK-07.md) · [Index](../README.md) · [Week 9 →](WEEK-09.md)
