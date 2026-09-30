# Week 7 of 12 — Pre-registration — writing down what would count

> **Week 7 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Before fitting anything: what result would we accept as success, and how do we stop ourselves moving that line afterwards? |
| **Run it** | `bash run_week.sh 07` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | md5sum of the sealed pre-registration, compared against the hash recorded inside the result artefact |
| **Measured** | 1s on the author's machine, offline, no API keys — the seal check itself is instant |
| **Artefact** | `outputs/metrics/metro_entry.json` · run `20260930-022458-edbf` · built 2026-09-30 |

> **Where we got to.** Specification hashed and sealed before a single model was fitted. CI re-checks the match on every push.

## What this stage does
The question, the sample, the covariates, the baselines, the evaluation and
a numeric success criterion were all fixed and hashed **before** a single
model was fitted.

The mechanism is deliberately boring, which is why it works. The
pre-registration is a file in the repository. Its md5 is written inside the
result artefact. A CI job re-computes both on every push and fails if they
disagree. Editing the specification after seeing the answer is therefore not
something we promise not to do — it is something that turns the build red.

    md5sum docs/PREREG_METRO_MODEL.md

**This is the single most defensible week of the twelve.** A negative result
from a sealed specification is evidence. The identical result from an
unsealed one is indistinguishable from having tried things until something
looked good. Week 6 told us failure was likely; week 7 is what made that
failure worth reporting.

Corrections discovered later go in a separate errata file. The seal is never
edited — not even to fix a genuine mistake in it — because a seal that can
be improved is not a seal.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Pre-registration | **docs/PREREG_METRO_MODEL.md** | `metro_entry.prereg` |
| Sealed md5 | **946f7ef75db69e5278eea409a04c3823** | `metro_entry.prereg_md5` |
| Question committed to | **prereg section 1: BETWEEN metros -- which metro gets one next?** | `metro_entry.question` |
| Held-out years declared | **7** | `metro_entry.held_out_years` |
| Arm declared | **before any model was fitted, at stage 1** | `metro_entry.verdict_arm_declared` |
| Arm scored | **prereg_strict** | `metro_entry.verdict_arm` |
| Coverage floor | **0.9** | `metro_entry.coverage_floor` |

## The risk we flagged

Committing in advance means we might have to publish a failure. That is the cost, and we accepted it in writing. The alternative — deciding what counts as success after seeing the answer — is not a cheaper option, it is a different and worse study.

## What this week does *not* establish

- A pre-registration constrains the analysis, not the data. It cannot rescue a panel that lacks the variables that drive the decision — which is exactly what week 6 suggested.
- Three corrections to the sealed text exist and are recorded in the errata rather than patched into the file.

## Read next

- [`docs/PREREG_METRO_MODEL.md`](../../../../siting-atlas/docs/PREREG_METRO_MODEL.md) — the sealed specification
- [`docs/PREREG_METRO_MODEL_ERRATA.md`](../../../../siting-atlas/docs/PREREG_METRO_MODEL_ERRATA.md) — what was corrected afterwards, and why the seal stands

---

[← Week 6](WEEK-06.md) · [Index](../README.md) · [Week 8 →](WEEK-08.md)
