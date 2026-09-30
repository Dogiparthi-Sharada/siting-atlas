# Week 10 of 12 — Diagnosis — why it failed, and what we retired

> **Week 10 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. This week has no metrics artefact: its table is the archive directory, read at build time, so adding or removing a programme changes the page with nobody editing it.

| | |
|---|---|
| **Question** | Was the failure about our model, or about what free public data can carry? And can you tell in advance? |
| **Run it** | `bash run_week.sh 10` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: a live covariate refit is about ninety minutes on two workers; the archive listing is read at build time |
| **What runs** | reads the covariate search, the gravity arms, and the experiments archive |
| **Artefact** | `outputs/metrics/covariate_search.json` · run `20260915-235210-ff92` · built 2026-09-15 |
| **Artefact** | `experiments/gravity-network/artefacts/gravity_network.json` · run `20260915-210603-b780` · built 2026-09-15 |
| **Directory** | `experiments/` |

> **Where we got to.** We can now say WHY, and turn it into a screening rule anyone can run before fitting. Five programmes were retired on the evidence and archived rather than deleted.

## What this stage does
A conditional choice model can only use a covariate that **varies inside a
metro**. Most free US public data is published at county grain, so across
two hundred candidate ZIP codes it arrives as a handful of distinct values.
A near-constant cannot rank anything, however large its real-world effect.

That gives a test you can run before fitting anything: measure each
covariate's within-metro coefficient of variation.

    cv below 0.6     it will fail          every one of them did
    cv 0.6 to 1.3    nothing lands here
    cv above 1.3     it may work           some did, some did not

The rule runs **one way**. Low dispersion is sufficient for failure; high
dispersion is necessary but nowhere near sufficient. Stating it as a
two-sided rule would be the overclaim, and the empty middle band is the
only reason the one-sided version is worth anything.

**What we retired.** A survival model, a gravity formulation of network
pull, two covariate transforms and a portfolio optimiser — each built, run,
and taken out on evidence. Their code and artefacts are archived, and
nothing in `src/` imports any of them. Retiring a programme is not the same
as it having been a mistake: the survival model was the right thing to try
given what was known in week 5, and knowing it does not work here is itself
a result.

The table below counts **directories, not programmes**. Five are the
retired programmes; `retired-tests` holds the tests that retired with them,
and `superseded-artefacts` holds outputs a later run replaced — kept so a
number quoted in an older document can still be traced to its source.

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

## The risk we flagged

Explaining a failure can slide into excusing it. The guard is that the rule is stated ONE-SIDED — it predicts failure, it does not promise success — and the band that would make it a two-sided rule is empty, which we show rather than assert.

## What this week does *not* establish

- Descriptive. Twenty-one non-independent terms from one run — a rule of thumb worth checking on your own data, not an estimated threshold with a confidence interval.
- The empty band is an observation about THESE covariates. It is not a claim that no covariate can sit at cv 1.0.
- Retired code is unmaintained and outside the test suite. It is evidence of a search, not a working component.

## Read next

- [`docs/EXPERIMENTS.md`](../../../../siting-atlas/docs/EXPERIMENTS.md) — all 21 experiments and what each does NOT support
- [`experiments/README.md`](../../../../siting-atlas/experiments/README.md) — what each retired programme asked, and what came back
- [`docs/DECISION_LOG.md`](../../../../siting-atlas/docs/DECISION_LOG.md) — when each was retired, and on what evidence

---

[← Week 9](WEEK-09.md) · [Index](../README.md) · [Week 11 →](WEEK-11.md)
