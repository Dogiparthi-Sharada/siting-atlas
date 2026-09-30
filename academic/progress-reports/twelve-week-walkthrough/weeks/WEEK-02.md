# Week 2 of 12 — A facility network read out of an image-only PDF

> **Week 2 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | The best public census of this operator's buildings is a PDF whose tables are pictures. Can it be recovered, and can the result be trusted? |
| **Run it** | `bash run_week.sh 02` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: the OCR needs tesseract, poppler and the licensed source PDFs, which are not redistributed |
| **What runs** | reads the extraction and validation reports |
| **Artefact** | `outputs/metrics/mwpvl_extraction.json` · run `20260915-195231-c54f` · built 2026-09-15 |
| **Artefact** | `outputs/metrics/mwpvl_validation.json` · run `20260915-195247-dbb5` · built 2026-09-15 |

## What this stage does
Thirteen tables, no text layer — so `tesseract` plus `poppler`, and then a
validation problem rather than an OCR problem. The question is not "did the
characters come out" but "is a row claiming a 2019 opening actually true".

Three independent checks: internal consistency, date plausibility against
the operator's known network start, and an EXTERNAL falsification bound.
That third one is the load-bearing check — a row linkable to an OSHA
inspection record that predates its claimed opening is impossible, and is
counted as a failure rather than explained away.

Four earlier collection methods failed before this one worked. They are
written down rather than quietly dropped.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Facilities recovered | **1,904** | `mwpvl_extraction.facilities` |
| With an opening year | **1,420** | `mwpvl_extraction.with_year` |
| Linked to an OSHA record | **208** | `mwpvl_validation.linked_to_osha` |
| Falsified by that link | **11** | `mwpvl_validation.falsified` |
| Pass rate | **94.71%** | `mwpvl_validation.pass_rate` |

## What this week does *not* establish

- The pass rate is computed on the rows that could be linked to OSHA at all, not on all dated rows. It bounds ONE failure mode; it is not an overall accuracy figure.
- The facts are MWPVL International's and are credited as theirs. The source PDFs are not redistributed.

## Read next

- [`docs/DATA_SOURCES.md`](../../../../siting-atlas/docs/DATA_SOURCES.md) — the four collection methods that failed first

---

[← Week 1](WEEK-01.md) · [Index](../README.md) · [Week 3 →](WEEK-03.md)
