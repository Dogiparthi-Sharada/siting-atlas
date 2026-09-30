# Week 8 of 12 — Model 1 — which ZIP, given that one opening happens

> **Week 8 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Conditional on a facility opening somewhere in a metro, can public data say which ZIP code it lands in? |
| **Run it** | `bash run_week.sh 08` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make model — refits the conditional choice model offline |
| **Measured** | 165s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/choice_report.json` · run `20260930-023028-fc4f` · built 2026-09-30 |

> **Where we got to.** Fits and converges. McFadden rho-squared around 0.20 — but on 94 decisions, and we lead with that rather than with the rho-squared.

## What this stage does
A conditional logit over the ZIP codes inside a metro. Utility is
`V = ln(beta' a)`, with `beta = exp(theta)` so every weight stays positive,
and households as the numeraire so the remaining coefficients read as
"worth this many households".

The sample size is the thing to look at first, not the fit statistic.
Ninety-odd decisions is what a national panel of openings actually yields
once you condition on the metro. That is a real constraint, not a
presentational one, and it is why inference here is a clustered bootstrap.

Note what this model does and does not claim. It answers **which ZIP, given
an opening**. It says nothing at all about whether an opening happens. That
is the harder question, it is the pre-registered one, and it is week 9.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Frame | **national** | `choice_report.frame` |
| Decisions | **94** | `choice_report.n_decisions_total` |
| Train / test | **56 / 38** | `choice_report.n_train_decisions, n_test_decisions` |
| Parameters | **3** | `choice_report.fit.n_parameters` |
| McFadden rho-squared | **0.1969** | `choice_report.fit.mcfadden_rho_squared` |
| Converged | **True** | `choice_report.fit.converged` |
| Bootstrap unit | **decision (never an alternative)** | `choice_report.inference.resampling_unit` |

## The risk we flagged

n = 94. Small enough that textbook standard errors would be misleading, because openings inside one metro are not independent draws. Inference is a metro-clustered bootstrap instead, which is the honest cost of the sample we have.

## What this week does *not* establish

- One operator. Nothing here transfers to another carrier without refitting, and this panel cannot test whether it would.
- Conditional on an opening. The model is silent on whether one occurs, which is the question that actually matters commercially.

## Read next

- [`docs/MODEL_SPEC.md`](../../../../siting-atlas/docs/MODEL_SPEC.md) — the utility specification in full
- [`docs/ALGORITHMS.md`](../../../../siting-atlas/docs/ALGORITHMS.md) — conditional logit, in plain language then precisely

---

[← Week 7](WEEK-07.md) · [Index](../README.md) · [Week 9 →](WEEK-09.md)
