# Week 7 of 12 — A pre-registered test that was allowed to fail

> **Week 7 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Which metro gets the next delivery station? And — committed in writing beforehand — what would count as getting that right? |
| **Run it** | `bash run_week.sh 07` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make metro — reruns the pre-registered out-of-time test |
| **Measured** | 50s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/metro_entry.json` · run `20260929-195313-6682` · built 2026-09-29 |

## What this stage does
The question, sample, covariates, baselines, evaluation and a numeric
success criterion were fixed and hashed BEFORE a single model was fitted.
The pre-registration sits in the repository, its md5 is recorded inside the
result artefact, and CI re-checks the match on every push — so the
specification cannot be edited after seeing the answer without the check
going red.

    md5sum docs/PREREG_METRO_MODEL.md

The model lost to a zero-parameter rule that ranks metros by household
count, in every held-out year. That is the headline, and it is reported in
the wording the pre-registration committed to publishing if the model
failed.

**This is the most valuable week of the twelve to defend.** A negative
result from a sealed specification is evidence; the same result from an
unsealed one is indistinguishable from having tried until something worked.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Pre-registration md5 | **946f7ef75db69e5278eea409a04c3823** | `metro_entry.prereg_md5` |
| Held-out years | **7** | `metro_entry.held_out_years` |
| Years the model won | **0 of 7** | `metro_entry.verdict.clause1` |
| Pooled AUC, model | **0.7323** | `metro_entry.pooled_out_of_time.model.auc` |
| Pooled AUC, households baseline | **0.8949** | `...pooled_out_of_time.baseline2_households.auc` |
| Clustered bootstrap difference | **-0.1628 [-0.2011, -0.1313]** | `...clustered_bootstrap.auc_minus_baseline2_households.model` |
| Verdict | **H0** | `metro_entry.verdict.hypothesis` |

## What this week does *not* establish

- The verdict holds across all nine arm-by-form combinations tried, so it is not an artefact of one specification — but those nine are not independent tests.
- Losing to a households baseline is not the same as the model being uninformative. It means it adds nothing OVER a variable anyone can look up.
- Three corrections to the sealed text are in `docs/PREREG_METRO_MODEL_ERRATA.md`. The seal is never edited; corrections go in the errata.

## Read next

- [`docs/PREREG_METRO_MODEL.md`](../../../../siting-atlas/docs/PREREG_METRO_MODEL.md) — the sealed specification
- [`docs/PREREG_METRO_MODEL_ERRATA.md`](../../../../siting-atlas/docs/PREREG_METRO_MODEL_ERRATA.md) — what was corrected afterwards, and why the seal stands

---

[← Week 6](WEEK-06.md) · [Index](../README.md) · [Week 8 →](WEEK-08.md)
