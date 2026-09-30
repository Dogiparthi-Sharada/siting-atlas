# Week 4 of 12 — The hard one — a network read out of an image-only PDF

> **Week 4 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | The best public census of this operator's buildings is a PDF whose tables are pictures. Can it be recovered, and can the result be trusted? |
| **Run it** | `bash run_week.sh 04` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: the OCR needs tesseract, poppler and the licensed source PDFs, which are not redistributed |
| **What runs** | reads the extraction and validation reports |
| **Artefact** | `outputs/metrics/mwpvl_extraction.json` · run `20260915-195231-c54f` · built 2026-09-15 |
| **Artefact** | `outputs/metrics/mwpvl_validation.json` · run `20260915-195247-dbb5` · built 2026-09-15 |

> **Where we got to.** 1,904 facilities recovered. 94.71% survive an external falsification bound — and the 11 that fail are excluded, not argued with.

## What this stage does
Thirteen tables, no text layer. So `tesseract` and `poppler` — and then the
real problem, which is not OCR at all. Getting the characters out is easy to
check. Knowing whether a row claiming a 2019 opening is *true* is not.

Three independent checks: internal consistency, date plausibility against
the operator's known network start, and an **external falsification bound**.
That third is the load-bearing one. A row linkable to an OSHA inspection
record that predates its claimed opening is not merely doubtful — it is
impossible, because the building was demonstrably operating earlier. Those
rows are counted as failures and dropped.

Four earlier collection methods failed before this one worked. They are
written down rather than quietly omitted, because a reader deciding whether
to repeat this needs to know what does not work.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Facilities recovered | **1,904** | `mwpvl_extraction.facilities` |
| With an opening year | **1,420** | `mwpvl_extraction.with_year` |
| Linkable to an OSHA record | **208** | `mwpvl_validation.linked_to_osha` |
| Falsified by that link | **11** | `mwpvl_validation.falsified` |
| Pass rate | **94.71%** | `mwpvl_validation.pass_rate` |

## The risk we flagged

If the OCR is unreliable the target variable is unusable and the project has no dependent variable. Four earlier collection methods had already failed; this was the week that decided whether there was a project.

## What this week does *not* establish

- The pass rate is computed on the rows that could be linked to OSHA at all, not on every dated row. It bounds one failure mode; it is not an overall accuracy figure.
- The facts are MWPVL International's and are credited as theirs. The source PDFs are not redistributed.

## Read next

- [`docs/DATA_SOURCES.md`](../../../../siting-atlas/docs/DATA_SOURCES.md) — the four collection methods that failed first

---

[← Week 3](WEEK-03.md) · [Index](../README.md) · [Week 5 →](WEEK-05.md)
