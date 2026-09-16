# Proposal artefacts — index

*Index last updated 2026-09-14.*

The submitted capstone proposal and the two presentation decks, plus the
internal record of what changed between drafts.

**Read this first, because the folder now contains two different kinds of
document and confusing them is easy.**

```
  v4 and the two decks       HISTORICAL.  Written in the future tense before
                             any model was fitted.  They specify a
                             discrete-time hazard model, which was built and
                             failed.  Read them as the record of a commitment,
                             not as a description of the project.

  PROPOSAL_V5.md / .txt      CURRENT, and it reports measured results rather
  PROPOSAL_V5.docx           than intentions.  Both models it describes have
                             been fitted and both returned negative results.
                             Sec. 5.3 is the retired hazard model; Sec. 5.4 is
                             the conditional choice model, which is only
                             MATCHED on held-out ranking by a single raw
                             covariate -- it buys nothing over it -- and
                             whose coefficient interval covers the null.
                             ("Beaten" here was corrected to "matched" on
                             2026-09-14; see "What is stale" below.)
                             It also carries the Monte Carlo, the failed
                             satellite dating attempt, and the labelling
                             programme.
```

`../PLAN.md` remains the shortest current description of the project as a
whole. v5 is the longest, and where the two disagree, check the artefact in
`../../outputs/metrics/` and its run identifier.

---

`PROPOSAL_GAP_2026_09_14.md` is new and should be read before editing
`PROPOSAL_V5.md`. It lists every claim in v5 that the artefacts no longer
support, classified WRONG / MISSING / PENDING, with the artefact that settles
each. The WRONG class was fixed in the Markdown on 2026-09-14 and the MISSING
class became §4.8 and §5.10; the PENDING class is waiting on the expanded panel
being wired into the warehouse and on the 700 addresses being geocoded.

**The `.docx` has not been rebuilt.** `PROPOSAL_V5.docx` is the 2026-09-14 01:27
build and is now behind the Markdown by two new sections and nine corrections.
Rebuilding it overwrites the submitted document and has not been approved;
`PROPOSAL_GAP_2026_09_14.md` §5 states exactly what it would take.

---

## What is in this folder

`PROPOSAL_V5.md` is the source of the v5 document and follows the repository's
`.md` plus `.txt` twin convention; so does this index. Everything else here is
a **generated binary or a hand-written log**. An earlier version of this
section said there was no `.md` in the folder at all, which stopped being true
when v5 was written in Markdown.

`PROPOSAL_V5.docx` is rendered from `PROPOSAL_V5.md` by
`tools/proposal/build_v5.py`, so the Markdown, the text twin and the Word file
cannot drift apart. **Rebuild it after any edit to the Markdown:**

```
  <docx python> tools/proposal/build_v5.py
  <repo python> tools/docs/md_to_txt.py docs/proposal/PROPOSAL_V5.md \
                docs/proposal/PROPOSAL_V5.txt --width 0
```

Note the widths differ by file. `PROPOSAL_V5.txt` is rendered unwrapped
(`--width 0`) so paragraphs reflow in Word; this index and everything under
`../defense/`, `../adr/` and `../career/` use `--width 80`. Rendering either
at the other's width produces a large spurious diff.

```
  Siting_Atlas_Proposal_v4.docx        The submitted proposal. ~3.0 MB, ten
                                       top-level sections: Executive Summary,
                                       1 Introduction, 2 Related Work,
                                       3 Research Objectives, 4 Data,
                                       5 Proposed Methods, 6 References,
                                       7 Roles and Contributions, 8 Timeline,
                                       9 Budget. All 14 figures embedded.
                                       GENERATED — see below.

  Siting_Atlas_Deck_v1_overview.pptx   26 slides, 16:9, with presenter notes.
                                       The narrative deck: problem, why the
                                       target variable had to change, the
                                       decay curve, the agent gates, the
                                       backtest. Uses 9 of the 14 figures.
                                       GENERATED.

  Siting_Atlas_Deck_v2_technical.pptx  30 slides, 16:9, with presenter notes.
                                       The method-and-results deck: success
                                       criteria table, identification, the
                                       evidence pack, the agent evaluation
                                       and its Wilson intervals. Also carries
                                       the defence slides.
                                       GENERATED.

  CHANGELOG.txt                        HAND-WRITTEN, and the only thing in
                                       this folder worth reading as prose.
                                       The internal diff between drafts v1 to
                                       v4 and the reasoning for each change:
                                       why the target variable moved off
                                       constructed order volume, which three
                                       novelty claims were withdrawn after
                                       the prior-art check and what falsified
                                       them, the LightGBM/XGBoost citation
                                       error, and fifteen structural defects
                                       found in the earlier draft. 188 lines.
                                       NOT part of the submission.
                                       Explicitly not generated by
                                       build_docs.sh despite the .txt suffix.
```

---

## Start here

`CHANGELOG.txt`. It is short, it is the only text file here, and it is the
best short account anywhere in the repo of *how the project's thinking moved*
— particularly the section headed "TARGET VARIABLE (the change everything
else depends on)", which is the decision later formalised as ADR-0001.

Read the `.docx` only when you need to know what was actually promised to the
examiner. Read the decks only when you are about to present.

---

## These are build outputs — do not edit them

Editing the `.docx` or a `.pptx` in Word or PowerPoint works exactly once.
The next build overwrites it. The content lives in Python:

```
  tools/proposal/build_v5.py       renders PROPOSAL_V5.md -> the v5 .docx.
                                   THIS IS THE CURRENT DELIVERABLE'S BUILDER
                                   and is what scripts/build_all.sh runs.

  tools/proposal/build_v4.py       assembles the HISTORICAL v4 Word document
                                   from Python section modules.  No longer in
                                   build_all.sh -- run it by hand if you need
                                   to reproduce v4.
    tools/proposal/docx_kit.py       styles, page numbers
    tools/proposal/sections_front.py    title, exec summary, introduction
    tools/proposal/sections_related.py  related work
    tools/proposal/sections_core.py     objectives, data
    tools/proposal/sections_methods.py  proposed methods
    tools/proposal/sections_back.py     references, roles, timeline, budget

  tools/deck/build_deck.py         assembles both decks
    tools/deck/slides_story.py          v1 narrative
    tools/deck/slides_v2_method.py      v2 method
    tools/deck/slides_v2_results.py     v2 results
    tools/deck/slides_defence.py        defence slides
    tools/deck/notes_v1.py / notes_v2.py   presenter notes
    tools/deck/pptx_kit.py, textfit.py     layout primitives
    tools/deck/check_layout.py          fails the build on overflow
```

Rebuild everything, in the order that matters (figures first, because both
documents embed them):

```
  bash scripts/build_all.sh
```

or individually:

```
  python tools/figures/build_all.py            # the 14 PNGs
  python tools/proposal/build_v5.py            # the v5 .docx (8 figures)
  python tools/deck/build_deck.py              # both .pptx
  python tools/deck/check_layout.py \
      docs/proposal/Siting_Atlas_Deck_v1_overview.pptx
```

Both builders hard-fail if a referenced figure is missing, on the grounds that
a missing PNG otherwise produces a document with a silent hole in it. v4
references all 14; v5 references 8, because §8's figure rule removed the rest.

**Until 2026-09-14, `scripts/build_all.sh` ran `build_v4.py`**, so `make docs`
regenerated the superseded document and never touched the current one
(`../AUDIT_2026_09_14.md` §2.7). It now runs `build_v5.py`.

---

## What is stale

### The method is superseded

**This section applies to v4 and the two decks. v5 is current and is not
covered by it.**

The v4 proposal specifies a discrete-time hazard model over ZCTA-quarters. That
model was built, fitted and failed, and the diagnosis is that the unit of
analysis was wrong: the 812 ZCTA-quarter "events" were echoes of a much smaller
number of real siting decisions plus a fifteen-mile circle, so the likelihood's
assumption of independence across observations (Train §3.7.1, p. 61) was
violated. **The replacement, a conditional ZIP-choice model, HAS now been
built and fitted** — 94 decisions, 3 parameters, and on held-out ranking it is
only *matched* by a single raw warehousing count, which is to say the
estimation buys nothing. This paragraph used to say the replacement was "not
yet built"; that stopped being true on 2026-09-14. Full account:
`PROPOSAL_V5.md` §5.4, `../adr/0004-model-change-conditional-choice.md`,
`../PLAN.md` §2 and §3.

> **Corrected 2026-09-14, twice over.** The sentence above first said the
> replacement was "not yet built" (fixed when it was fitted), and then said it
> was **beaten** on held-out ranking by the raw warehousing count. It now says
> **matched**. This second change is not the work moving on — it is a claim
> that was **wrong**. "Beaten" came from one seeded 56/38 split, where the raw
> count led 8-7 at top-1 and 20-19 at top-10. Across fifty paired re-splits of
> the same 94 decisions the raw count's lead is **0.36 hits of 38, paired sd
> 1.14**, and it loses 11 of the 50 outright
> (`../../outputs/metrics/gbm_benchmark.json`, `across_repeats`). One third of
> a decision is noise. **The negative result stands unchanged**: fitting three
> parameters buys no ranking improvement over counting warehouses, and v5 is
> still a document about two models that did not work. The correction removes
> a defeat the data cannot support, not the finding.

Two smaller corrections to what this section used to say. It gave the decision
count as "about 104"; the fitted model has **94**, and 104 is the raw row count
of the national facility file. And it attributed the failure to Train §2.2 in
earlier drafts elsewhere in the tree; §2.2 is the wrong section and Train calls
its criterion "not restrictive".

The word "hazard" appears in the proposal source in `sections_front.py`,
`sections_core.py`, `sections_methods.py` and `sections_back.py`, and in the
deck source in `slides_v2_method.py`, `slides_v2_results.py` and `notes_v2.py`.
Rebuilding the documents will not fix this; the text has to change.

### Some numbers in the documents are targets, not results

Stating a target in a proposal is legitimate. Drawing one as though it were a
measurement is not, and the documents did both. What remains, and what was
fixed on 2026-09-13:

```
  STILL A TARGET, and correctly labelled as one
    sections_front.py    "at an out-of-time AUC of 0.80 or better"
    sections_core.py     success criterion "AUC-ROC, out-of-time >= 0.80"
    slides_v2_method.py  "out-of-time AUC >= 0.80 on metros withheld"

  WAS A FABRICATION, now corrected
    fig08_backtest       printed AUC 0.84 / ECE 0.03 / precision@100 0.61
                         over an ROC curve synthesised as
                         tpr = fpr**(1/0.84 - 1) so its area would match.
                         Now reads every value from hazard_report.json.
    fig09_rank_stability invented eight ZIP codes and their Monte Carlo
                         shares. Deleted; replaced by
                         fig09_conformal_coverage.
    sections_core.py     the label-noise example quoted "measured AUC
                         degrades from 0.84 to 0.81" for a simulation that
                         has not been run
    slides_story.py      s12 "we target 0.84"; s13 note "numbers shown are
                         the targets we commit to in advance"; the banner
                         quoting ZIP 94608 at 87% and 94612 at 34%
    slides_story.py      s08, titled "Idea 1, measured", with a presenter
                         note instructing the speaker to read out a
                         cannibalisation decay nobody has estimated
    slides_v2_results.py s18, which presented the design and never the result

  MEASURED (outputs/metrics/hazard_report.json)
    AUC            0.6894 on the primary hold-out, which holds out whole
                   ZCTAs, not rows; 0.5551 on the secondary split by time.
                   The null is 0.5000 in both cases. An earlier version of
                   this file called 0.6894 "in sample" and said 0.5551 was
                   "below the base rate": the first is wrong, and the second
                   compares AUC to an event rate, which are not on the same
                   scale.
    Brier          0.019522 against 0.019614 for a constant, same 8,044 rows;
                   0.020635 against 0.020213 on the temporal split, where the
                   model is WORSE than the constant
    ECE            0.00863 against 0.00005
    conformal      88.19% against a nominal 90%, inside the two-sigma band
                   351 independent units allow; 10.09% of sets are empty
```

Both figures now carry their source file and run id on the image, and the
proposal and deck builders read the same JSON at build time, so a re-fit
cannot leave a stale number behind. `fig08_backtest` is still Word Figure 4
and is still in both decks; it now shows the failure, which is the project's
central finding. See `../figures/README.md`.

### Two things the proposal promises that the data could not deliver

```
  "hand-verification of a 100-facility sample"   The pilot panel is 43
                                                 buildings, the national one
                                                 104. Replaced by a census
                                                 plus a measured date-lag
                                                 bound. Recorded in ADR-0001
                                                 as a dated update.
  "measured date-error rate"                     Wrong frame. The dates are
                                                 OSHA "operating by" upper
                                                 bounds, i.e. censoring, not
                                                 noise -- and on all 100
                                                 loaded national rows the
                                                 open_year field IS that
                                                 bound rather than an
                                                 opening. See PROPOSAL_V5
                                                 Sec. 6 defect M.
```

### What the CHANGELOG does not yet record

There is no v5 section. The target-variable change of v4 is documented; the
unit-of-analysis change that followed the model failure is not. If the
proposal is ever revised, that is the entry to write.
