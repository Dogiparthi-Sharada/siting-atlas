# Week 6 of 12 — Which ZIP, given that one opening happens

> **Week 6 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Conditional on a facility opening somewhere in a metro, can public data say which ZIP code it lands in? |
| **Run it** | `bash run_week.sh 06` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make model — refits the conditional choice model |
| **Measured** | 151s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/choice_report.json` · run `20260929-203157-754d` · built 2026-09-29 |

## What this stage does
A conditional logit over the ZIP codes inside a metro. Utility is
`V = ln(beta' a)`, with `beta = exp(theta)` so every weight stays positive,
and households as the numeraire so the remaining coefficients read as
"worth this many households".

Note the sample size. Ninety-odd decisions is what a national panel of
openings actually yields once you condition on the metro — and the honest
consequence is that inference is by a metro-clustered bootstrap, not by the
textbook standard errors, because openings inside one metro are not
independent draws.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Frame | **national** | `choice_report.frame` |
| Decisions | **94** | `choice_report.n_decisions_total` |
| Train / test | **56 / 38** | `choice_report.n_train_decisions, n_test_decisions` |
| Parameters | **3** | `choice_report.fit.n_parameters` |
| McFadden rho-squared | **0.1969** | `choice_report.fit.mcfadden_rho_squared` |
| Converged | **True** | `choice_report.fit.converged` |

## What this week does *not* establish

- One operator. Nothing here transfers to another carrier without refitting, and the panel cannot test whether it would.
- The model answers WHICH ZIP GIVEN AN OPENING. It says nothing about whether an opening happens — that is week 7, and it is the harder question.

## Read next

- [`docs/MODEL_SPEC.md`](../../../../siting-atlas/docs/MODEL_SPEC.md) — the utility specification in full
- [`docs/ALGORITHMS.md`](../../../../siting-atlas/docs/ALGORITHMS.md) — conditional logit, in plain language then precisely

---

[← Week 5](WEEK-05.md) · [Index](../README.md) · [Week 7 →](WEEK-07.md)
