# Siting Atlas — a twelve-week walkthrough

Twelve weeks, one question each, in four movements:

| Weeks | | |
|---|---|---|
| **1-3** | Setup | choose the question, choose the method, get the data |
| **4-6** | Build | recover the target variable, build the panel, **find the finding** |
| **7-9** | Commit and test | seal the criterion, fit, report what came back |
| **10-12** | Diagnose and deliver | explain the failure, build what does work, ship it |

The turn is **week 6**. Weeks 1-5 are setup; week 6 is the discovery that the public record cannot see three in four of these places, which made failure the likely outcome. Week 7 is the response: commit to a criterion in writing, before fitting, so that a failure would be a measurement rather than an excuse. Week 9 is that bill coming due.

Each page carries the same six things: the question, how to run it, **where we got to**, **the risk we flagged**, the numbers, and what the week does *not* establish.

The project is **complete**. These pages pace how it is presented — they are not a claim about when the work happened. Every page prints the real `run_id` and build date of the artefact behind it, so the true chronology is on the page and can be checked.

| Week | | Where we got to | Mode |
|---|---|---|---|
| **01** | [Scope and feasibility](weeks/WEEK-01.md) | Question fixed, and feasibility proven before we wrote modelling code. | `INSPECT` |
| **02** | [Literature and method selection](weeks/WEEK-02.md) | Conditional logit for the choice model, Daganzo continuous approximation for cost. Both chosen in writing, against alternatives we recorded rather than forgot. | `INSPECT` |
| **03** | [Data acquisition and provenance](weeks/WEEK-03.md) | Fourteen sources in a content-addressed cache, one SHA-256 per file. Licences audited; two paid sources will not be redistributed. | `INSPECT` |
| **04** | [The hard one — a network read out of an image-only PDF](weeks/WEEK-04.md) | 1,904 facilities recovered. 94.71% survive an external falsification bound — and the 11 that fail are excluded, not argued with. | `INSPECT` |
| **05** | [One table every model reads](weeks/WEEK-05.md) | One panel, 1,081,312 rows, 50 columns — and everything above it is ignorant of where the bytes came from. | `INSPECT` |
| **06** ◆ | [What the public record cannot see](weeks/WEEK-06.md) | 138 of 488 cities. This is the project's actual finding, and it arrived in the middle of the semester and changed what the rest of it was for. | `INSPECT` |
| **07** | [Pre-registration — writing down what would count](weeks/WEEK-07.md) | Specification hashed and sealed before a single model was fitted. CI re-checks the match on every push. | `RECOMPUTE` |
| **08** | [Model 1 — which ZIP, given that one opening happens](weeks/WEEK-08.md) | Fits and converges. McFadden rho-squared around 0.20 — but on 94 decisions, and we lead with that rather than with the rho-squared. | `RECOMPUTE` |
| **09** | [Model 2 — the pre-registered test, and its answer](weeks/WEEK-09.md) | It lost to a zero-parameter baseline in every held-out year. We are reporting that, in the wording week 7 committed us to. | `RECOMPUTE` |
| **10** | [Diagnosis — why it failed, and what we retired](weeks/WEEK-10.md) | We can now say WHY, and turn it into a screening rule anyone can run before fitting. Five programmes were retired on the evidence and archived rather than deleted. | `INSPECT` |
| **11** | [What does work — pricing the operation](weeks/WEEK-11.md) | $1.14 to put a parcel on a doorstep, across 8,037 ZIP-code areas and 57.8% of US households — priced against 501 real buildings, from road geometry and wages alone. | `RECOMPUTE` |
| **12** | [The artefact — and the defence](weeks/WEEK-12.md) | 694 tests, an offline reproduction from a clone with no API keys, a CI-verified pre-registration seal, and an IEEE-format write-up drafted. | `RECOMPUTE` |

`RECOMPUTE` weeks re-derive their result offline from a clone — five of the twelve do. `INSPECT` weeks read what already ships; each page states its own reason, which is never the same twice.

## Running a week

```bash
bash run_week.sh 07        # run week 7 and print its summary
bash build.sh              # regenerate all twelve pages
```

The repository is found by walking up to `MSBA_Project/` and looking for `siting-atlas/`. Set `SITING_ATLAS=/path/to/clone` if yours lives elsewhere.

Nothing here writes to the repository except the artefacts a `RECOMPUTE` week legitimately rebuilds, so revising this narrative never touches the code it describes.
