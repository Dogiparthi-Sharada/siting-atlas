# Week 2 of 12 — Literature and method selection

> **Week 2 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Which methods, chosen against what alternatives — and how much of the literature did we actually read? |
| **Run it** | `bash run_week.sh 02` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: a literature review produces documents, not artefacts; the counts below are read out of those documents |
| **What runs** | counts options, references and logged decisions in the docs |

> **Where we got to.** Conditional logit for the choice model, Daganzo continuous approximation for cost. Both chosen in writing, against alternatives we recorded rather than forgot.

## What this stage does
Two methods carry the project.

**Conditional logit** for "which ZIP, given an opening" — because the
decision is a choice among alternatives in a set, which is exactly what the
model is for. Utility is `V = ln(beta' a)` with `beta = exp(theta)`, so
weights stay positive, and households act as numeraire so every other
coefficient reads as "worth this many households".

**Daganzo's continuous approximation** for cost — because it prices a
delivery tour from density and geometry rather than from a route solver,
which means it needs no proprietary routing data. Its regime of validity is
stated and tested rather than assumed.

The reference table is marked by how far each citation was verified, and
that marking is the number worth showing: **[V]** read in full, **[T]**
title and venue confirmed against a publisher page, **[K]** cited from
knowledge and explicitly flagged to check before submission. Most
bibliographies do not tell you which is which.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Options considered | **5** | `docs/ALTERNATIVES.md '## Option'` |
| References, read in full [V] | **11** | `docs/REFERENCES.md '[V]' markers` |
| References, title-verified [T] | **19** | `docs/REFERENCES.md '[T]' markers` |
| References, cited from knowledge [K] | **6** | `docs/REFERENCES.md '[K]' markers` |
| Method notes written | **1,654 lines** | `docs/METHODS_RESEARCH.md` |
| Decisions logged with evidence | **32** | `docs/DECISION_LOG.md numbered` |

## The risk we flagged

Picking a method because it is familiar rather than because it fits the data. The defence is that the rejected options are written down and can be argued with.

## What this week does *not* establish

- The [K] references are cited from knowledge, not checked against a page. They are real and standard works, but the details printed here are unconfirmed and marked as such.
- Choosing a method in advance is not the same as validating it. Whether Daganzo's approximation holds in this regime is tested in week 11, not here.

## Read next

- [`docs/METHODS_RESEARCH.md`](../../../../siting-atlas/docs/METHODS_RESEARCH.md) — the methods survey in full
- [`docs/REFERENCES.md`](../../../../siting-atlas/docs/REFERENCES.md) — every citation, with how far it was verified
- [`docs/ALGORITHMS.md`](../../../../siting-atlas/docs/ALGORITHMS.md) — each method in plain language, then precisely

---

[← Week 1](WEEK-01.md) · [Index](../README.md) · [Week 3 →](WEEK-03.md)
