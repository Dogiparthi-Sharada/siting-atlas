# Week 9 of 12 — Model 2 — the pre-registered test, and its answer

> **Week 9 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Which metro gets the next delivery station? Scored against the criterion we sealed in week 7. |
| **Run it** | `bash run_week.sh 09` |
| **Mode** | **RECOMPUTE** — the command below re-derives this result offline from the clone, so the number is demonstrated, not quoted |
| **What runs** | make metro — reruns the out-of-time test end to end |
| **Measured** | 56s on the author's machine, offline, no API keys |
| **Artefact** | `outputs/metrics/metro_entry.json` · run `20260930-022458-edbf` · built 2026-09-30 |

> **Where we got to.** It lost to a zero-parameter baseline in every held-out year. We are reporting that, in the wording week 7 committed us to.

## What this stage does
Trained on everything before the held-out year, scored on that year. The
comparison is against a baseline with **no parameters at all**: rank metros
by household count.

The model lost every year. Not narrowly — the clustered bootstrap difference
excludes zero comfortably.

The verdict holds across all nine arm-by-form combinations tried, so it is
not an artefact of one specification. Those nine are not independent tests
and we do not present them as if they were.

What makes this publishable rather than embarrassing is the ordering. The
criterion existed, hashed, before the fit. The paragraph reporting the
failure was written into the pre-registration in advance, and it is quoted
verbatim rather than softened:

> *Free public data cannot predict siting at any grain tested. The
> ZIP-level failure is not a resolution problem but a general one: the
> variables that drive the decision are not public at any resolution.*

Losing to a households baseline is not the same as being uninformative. It
means the model adds nothing **over a number anyone can look up** — which,
given week 6, is close to what we should have expected.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Years the model won | **0 of 7** | `metro_entry.verdict.clause1` |
| Pooled AUC, model | **0.7323** | `metro_entry.pooled_out_of_time.model.auc` |
| Pooled AUC, households baseline | **0.8949** | `...pooled_out_of_time.baseline2_households.auc` |
| Clustered bootstrap difference | **-0.1628 [-0.2011, -0.1313]** | `...clustered_bootstrap.auc_minus_baseline2_households` |
| Bootstrap clusters | **935** | `metro_entry.clustered_bootstrap.n_clusters` |
| Seal still intact | **946f7ef75db69e5278eea409a04c3823** | `metro_entry.prereg_md5` |
| Verdict | **H0** | `metro_entry.verdict.hypothesis` |

## The risk we flagged

The risk we took in week 7 came due. A model that loses is uncomfortable to present; a model that loses against a criterion you wrote down first is a result. The failure mode to avoid now is quietly adding a specification that wins — which the seal prevents.

## What this week does *not* establish

- Nine arm-by-form combinations all return the same verdict, which is reassuring but not nine independent tests.
- This is a statement about FREE PUBLIC DATA, not about predictability in principle. An operator with its own pipeline data is answering a different question.

## Read next

- [`docs/PREREG_METRO_MODEL.md`](../../../../siting-atlas/docs/PREREG_METRO_MODEL.md) — the criterion this was scored against
- [`docs/NUMBERS.md`](../../../../siting-atlas/docs/NUMBERS.md) — every figure above, re-derived

---

[← Week 8](WEEK-08.md) · [Index](../README.md) · [Week 10 →](WEEK-10.md)
