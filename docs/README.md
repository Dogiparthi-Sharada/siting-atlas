# docs/ — the index

*One line per document, grouped by who needs it. Updated 2026-09-16.*

> **Cost model rebuilt 2026-09-16.** The depot layer is no longer a solved
> 334-site p-median; it is the operator's 501 real geocoded delivery stations.
> Median cost per parcel $1.0830 → **$1.1389** over 2,333 → **8,037** ZCTAs,
> and the "zero of 43 facilities sit in their metro's cheapest decile"
> statistic is **withdrawn** — the test is unidentified once depots are the
> facilities. [`NUMBERS.md`](NUMBERS.md) §10 is the record;
> [`EXPERIMENTS.md`](EXPERIMENTS.md) E17 is the run;
> [`LESSONS.md`](LESSONS.md) §6.5 is why the withdrawal is itself a lesson.
> Documents dated before 2026-09-16 describe the retired pilot.

**Two rules before you read anything else.**
[`STATUS.md`](STATUS.md) is the current state of the project.
[`NUMBERS.md`](NUMBERS.md) is the tie-breaker on any figure — it re-derives
every headline number from the artefact that emitted it, and names the stale
variants still in circulation. Where a document and `NUMBERS.md` disagree,
`NUMBERS.md` wins and the document is the bug.

---

## Start here

| Document | Who it is for |
|---|---|
| [`STATUS.md`](STATUS.md) | Anyone. What works, what is fitted, what is blocked, what failed, what is pending — with a `run_id` behind every number |
| [`NUMBERS.md`](NUMBERS.md) | Anyone about to quote a figure. Every headline re-derived from its artefact, plus a list of quantities that are easily confused |
| [`EXPLAINER.md`](EXPLAINER.md) | A reader who has not followed the engineering. The four models in plain English, and how each performs |
| [`ROADMAP.md`](ROADMAP.md) | Anyone asking "what next". The only forward-looking document: decisions owed, Phases 3/5/6, the cut list, Volume II |

## Reproducing a result

| Document | Who it is for |
|---|---|
| [`DATA_SOURCES.md`](DATA_SOURCES.md) | Someone fetching the ingredients. Every source, how to get it, what ships already derived, and §18 for the offline path |
| [`REPRODUCE.md`](REPRODUCE.md) | Someone going cold clone to cost table: credentials, manual files, the ordered commands, expected counts and runtimes |
| [`../Makefile`](../Makefile) | `make help` lists every pipeline stage |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Someone reading the code. The L0–L5 layer model, the data flow, the star schema. **Dated 2026-09-12 and stale** on the module inventory |
| [`engineering/`](engineering/) | Three documents: the pipeline as built, what a run logs, and pre-build sizing |

## Method — why the models are what they are

| Document | Who it is for |
|---|---|
| [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) | Anyone challenging a method choice. Every claim tagged SAYS / WE / OPEN with a section number; §10 is a corrections log of the claims that did not survive the source; §14 is the unit-of-analysis diagnosis; §15 is the ledger of which paper changed which line of code |
| [`MODEL_SPEC.md`](MODEL_SPEC.md) | Anyone reading the choice model. The specification, written before any model code and checked clause by clause against Train. **Read §0.3 first** — the three places the fit departs from the spec |
| [`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md) | Anyone who suspects the negative result was chosen after the fact. The pre-registration, md5 `946f7ef75db69e5278eea409a04c3823`, with both outcomes' language written in advance |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | Anyone asking "what did you actually try?". Every experiment the project ran — the question, what was tested against what, the result with its artefact and `run_id`, and what the result does **not** support |
| [`ALGORITHMS.md`](ALGORITHMS.md) | Anyone asking "what methods, and why those?". Every algorithm and estimator, in plain language then precisely, each naming the `src/` file that implements it |
| [`research/`](research/) | One notes file per paper read in full, so no paper is opened twice, plus the per-experiment notes. See [`research/README.md`](research/README.md) |
| [`REFERENCES.md`](REFERENCES.md) | The bibliography, every entry marked [V] read in full / [T] title and venue checked / [K] from memory, verify before use |
| [`READING_LIST.md`](READING_LIST.md) | Papers not yet acquired, each annotated with the decision it gates |

## Decisions, errors and history

| Document | Who it is for |
|---|---|
| [`DECISION_LOG.md`](DECISION_LOG.md) | **Check §3 before asking a question — it may already be answered.** §1 what was decided and why, §2 every error made and what caught it, §3 questions already answered, §4 found during verification and not yet fixed |
| [`adr/`](adr/) | The four decisions formal enough to have their own record. ADR-0004 (the model change) is *proposed*, not accepted |
| [`ALTERNATIVES.md`](ALTERNATIVES.md) | The owner, deciding where the project goes. Five options, what each costs, the evidence in hand, and what would make each fail |
| [`AUDIT_2026_09_14.md`](AUDIT_2026_09_14.md) | A full audit of what the project had lost track of across data, code, parameters, features and literature. Historical — its test-coverage figures are superseded by `NUMBERS.md` §12 |
| [`LESSONS.md`](LESSONS.md) | Anyone building something else. 54 things this project learned the hard way, grouped by the kind of mistake — statistics, estimators, parameters, artefacts, checks that do not check, data, near-misses, conduct — each with the code or artefact that establishes it, what it cost, and why it was easy to get wrong. Ends with the five that generalise beyond this problem |

## Data

| Document | Who it is for |
|---|---|
| [`data/README.md`](data/README.md) | The index of all 30-odd data documents: the registry, the quality audit, the cleaning literature, every parameter with its provenance |
| [`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) | **Read before using the target variable.** How the panel was collected, the methods that failed first, and every known defect |
| [`data/PARAMETERS.md`](data/PARAMETERS.md) | Every constant, its source, and its measured sensitivity |
| [`data/DATA_QUALITY.md`](data/DATA_QUALITY.md) | The audit against Rahm & Do, with numbers |
| [`data/COST_MODEL.md`](data/COST_MODEL.md) | The Daganzo cost model from zero, with a worked two-ZCTA example |
| [`figures/`](figures/) | 9 generated illustration PNGs. **Read `figures/README.md` before showing any of them** — most contain no real results |

---

## I want to...

```
  ...know the measured state of everything, today
        STATUS.md

  ...check a number before I quote it
        NUMBERS.md                       then outputs/metrics/*.json

  ...understand the project without the engineering
        EXPLAINER.md

  ...know what failed and why
        STATUS.md  §4         what failed
        METHODS_RESEARCH.md  §14   the diagnosis, as method

  ...know what we got WRONG and how we caught it
        DECISION_LOG.md  §2

  ...check whether I already asked this
        DECISION_LOG.md  §3

  ...know why we chose this method over another
        METHODS_RESEARCH.md        then adr/

  ...know whether the DATA is any good
        data/DATA_QUALITY.md       the audit, with numbers
        data/CLEANING_LITERATURE.md  why the approach changed

  ...know what was cleaned, and how to undo it
        data/CLEANING_CHANGELOG.md

  ...know where a number came from
        NUMBERS.md                 headline figures
        data/PARAMETERS.md         every constant
        REFERENCES.md              the bibliography

  ...know what a paper actually said, without reading it again
        research/README.md         the index, then the notes file

  ...know where the DATA came from
        DATA_SOURCES.md                    every source, how to fetch it
        data/FACILITY_PANEL_PROVENANCE.md  the target variable

  ...reproduce a result
        DATA_SOURCES.md §18        the offline path, no keys
        REPRODUCE.md               the long form

  ...find out what is still broken
        STATUS.md  §6              known open defects

  ...find out what to do next, in order
        STATUS.md  §5              pending, ranked by what it buys
        ROADMAP.md                 everything further out

  ...decide where the project GOES, not just what to do next
        ALTERNATIVES.md

  ...understand the code
        ../src/README.md           then the README in each sub-package
```

---

## What not to trust, specifically

This project reports its defects rather than hiding them. These will cost you
time if you do not know them.

0. **Anything describing a "solved 334-depot network" as the current cost
   model is stale**, including `REPRODUCE.md` §5, `DECISION_LOG.md` §4.2,
   `ARCHITECTURE.md`, `docs/data/COST_MODEL.md` and the two cost figures under
   `docs/figures/`. Those are dated records of the retired pilot and their
   numbers are correct *for what they describe*. The current model is
   `NUMBERS.md` §10.1. Related: `cost/stations.py`'s `CATCHMENT_MILES`
   docstring still claims the 15-mile catchment is denser than the pilot — it
   is sparser, 350 against 475 stops/sq mi, and the docstring is wrong.
1. **`ARCHITECTURE.md` and `REPRODUCE.md` are stale.** Both predate the panel
   expansion. `REPRODUCE.md:502` claims the `enabled` column is `0.00%`
   non-null; it is 100% non-null (2.58% TRUE), and §4.4 of the same document
   says so 200 lines earlier. `REPRODUCE.md:513` gives 79,484 vans and
   $14,089,759/day against the artefact's 78,292 and $14,001,626.
2. **`lift_by_market_size.json` is retired and unregenerable** — no emitter,
   no `run_id`, an internally contradictory `finding` field. Five sites still
   cite it. Its 6.14 / 6.42 pair must not be quoted; use
   `panel_experiments.json`.
3. **Any GBM figure from `gbm_benchmark.json:headline_split`** is
   non-reproducible by the artefact's own measurement. Quote `across_repeats`.
4. **`covariate_search.json`'s 694-vs-687 disagreement is resolved.** The
   2026-09-15 re-run completed and the artefact reads **687 at every stage**,
   with no occurrence of 694; the figures quoted from it across `docs/` have
   been re-derived. **What is not fixed is the stamp:** the emitter reuses one
   `run_id` across successive writes and stamps `written_at` at the first
   write, so two materially different versions of the file carried an
   identical stamp and `run_id` cannot tell them apart. Check
   `facilities: 687` and the `stage_ledger`. `NUMBERS.md` carries the fix.
5. **Seven artefacts carry no `run_id` and no `written_at`** —
   `panel_experiments`, `white_space`, `mwpvl_coverage`,
   `national_panel_expanded`, `subsidies`, `logrel_*` and `percapita_*`. Only
   a file mtime backs them. Any document citing "a run" for those numbers is
   citing something the artefact does not record.
6. **The 693-row facility panel is not committed.**
   `national_facilities_expanded.csv` and `geocoded_expanded.csv` are
   untracked, so the panel behind most of §2 of `STATUS.md` exists on one
   disk. [`STATUS.md`](STATUS.md) §3 blocker 5.

---

## Generated files

```
  docs/figures/*.png        python tools/figures/build_all.py
  docs/data/README.md       python tools/docs/gen_data_docs.py (from the
  docs/data/<source>.md       source registry)
  everything under
    outputs/                the pipeline. `make help` lists the stages.

  Edit the generator, not the output.
```

`scripts/build_docs.sh` renders every Markdown file in the repository to a
plain-ASCII `.txt` twin at 80 columns. **The twins were removed from this
repository and are not being restored** — they doubled the file count and
every correction sweep had to touch two copies of the same document. Running
the script still regenerates them in the working tree; the CI `documents` job
diffs tracked files only, so untracked twins do not fail the build. If you run
it, do not commit the output.
