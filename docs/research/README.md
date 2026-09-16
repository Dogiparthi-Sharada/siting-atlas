# Reading notes — index

*Started 2026-09-13. This index is APPENDED TO as papers are read. It is
not rewritten. If you have just read a paper, add your line to the table
below; do not reorganise or delete anyone else's.*

---

## Why this directory exists

The project kept answering "is the methodology sound?" from standard
knowledge rather than from sources, and got caught doing it. The fix was to
download the papers and read them. This directory is the durable product of
that reading: **one file per paper, written so that nobody ever has to
reopen the PDF.**

That is the test. If a future reader has to go back to the PDF to answer a
reasonable question about what the paper says, the notes file has failed.
Be generous rather than terse. A notes file that is longer than the section
of the paper it describes is fine; a notes file that summarises a
twenty-page paper in a page is not.

The notes are **not** the argument. They record what a paper says. The
argument about what to do lives in:

```
  docs/data/CLEANING_LITERATURE.md   the data-cleaning argument
  docs/data/DATA_QUALITY.md          the audit of this pipeline
  docs/METHODS_RESEARCH.md           the econometrics argument, and the
                                     implemented-vs-documented ledger (§15)
  docs/STATUS.md                     the measured state, and what each
                                     argument has actually changed
```

Those documents should **cite** the notes files rather than duplicate them.

---

## Naming convention

```
  NOTES_<first-author-surname>_<year>.md
```

lower case, underscores, no spaces, no punctuation in the surname. For two
authors where both names are how the work is known, join with an
underscore: `NOTES_rahm_do_2000.md`, `NOTES_fellegi_holt_1976.md`,
`NOTES_gneiting_raftery_2007.md`. For a numbered technical report where the
report number is how people find it, use the number:
`NOTES_winkler_rr99_01.md`. For an unattributed or heavily multi-authored
survey, a short title slug is acceptable: `NOTES_five_facets_2024.md`,
`NOTES_dq_tools_survey_2019.md`. For a partial read of a book, say which
part: `NOTES_little_rubin_ch1_3.md`.

If two papers collide, disambiguate with a slug, not a letter:
`NOTES_winkler_rr99_04_linkage.md`, not `NOTES_winkler_1999b.md`.

A `.txt` twin is generated from each `.md` by `tools/docs/md_to_txt.py`.
Do not hand-edit a `.txt`.

---

## Required structure — seven parts, in this order

Every notes file must contain all seven. Keep the headings numbered so a
reader can jump.

```
  1  Citation and local file
       Full citation, and the filename in ../Research/ it came from.
       Include the PDF-page to printed-page offset if they differ, so
       later readers can find a passage.  Flag any paper that is easily
       confused with another (same author, same year).

  2  What the paper is for
       One paragraph.  What problem it solves, what kind of paper it is
       (theory / survey / vision / procedure), and what we want from it.

  3  Section-by-section walkthrough of the WHOLE paper
       For each section: its number, its title, what it argues, and the
       specific results, definitions and theorems it states.  This is the
       part that means we never reread.  Reproduce the paper's own tables
       and figures as ASCII where they carry content.  Say which figures
       are images that do not appear in the PDF text layer.

  4  Verbatim quotes for anything load-bearing
       Marked as > blockquotes, each with its section (and page if the
       PDF shows one).  Never cite a section number you have not opened.
       If unsure of a page, write "section X" rather than inventing a page.

  5  Definitions the paper gives formally
       Stated exactly as the paper states them, not paraphrased.  An
       "edit", an "implied edit", the minimum-change criterion, an
       "outlier" -- whatever the paper defines, quote it.

  6  What this means for siting-atlas
       Concrete.  Point at file:line.  Say which of our findings the
       paper confirms, which it contradicts, and which it renames.  If
       the paper shows one of our claims is WRONG, say so loudly here --
       that is the most valuable thing a notes file can contain.

  7  What I did NOT read or did not understand
       Honest.  Which appendix, which proof, which table you skipped or
       could not reconstruct from a damaged text layer.  Which cited
       works you did not follow and whether they are in ../Research/.
       Never imply completeness you do not have.
```

Part 7 is not optional and is not a formality. Several of these PDFs have
damaged text layers — scrambled bit matrices, mangled equations, figures
that are raster images with no extractable text. A notes file that does not
say where it is uncertain is worse than no notes file, because the next
reader will trust it.

---

## The notes

Data cleaning and data quality — read 2026-09-13:

```
  NOTES_rahm_do_2000.md
      The canonical taxonomy.  2x2 (single/multi-source x schema/instance)
      x 4 scopes, NOT a plain 2x2.  Corrects our misfiling of the ACS
      top-code, which is their "missing values" class (dummy values), not
      "embedded values".  Also the five phases of a cleaning process,
      including backflow, which we had never named.

  NOTES_fellegi_holt_1976.md
      The founding paper of automatic edit and imputation.  The three
      criteria, the normal form, implied edits, the complete set, and the
      minimum-change criterion as a set-cover problem.  Section 7's a
      priori reliability weights are the principled answer to
      facilities.py:206's min().  Section 1 option 5 demolishes
      complete-case deletion in 1976, before MCAR had a name.

  NOTES_winkler_rr99_01.md
      How Fellegi-Holt is actually implemented in statistical agencies,
      with cost numbers.  Contradicts our "a week, wrong trade" estimate.
      Macro / selective editing (Hidiroglu-Berthelot) is the answer to
      our 28% outlier stand-off: rank by influence on the published
      total, not by distance from the median.  NOT the same paper as
      rr99-04, which is record linkage.

  NOTES_van_den_broeck_2005.md
      The procedure: a REPEATING cycle of screening, diagnosis and
      treatment.  Four screening oddities, four diagnoses (erroneous /
      true extreme / true normal / idiopathic), three treatments, hard
      and soft cutoffs.  "Erroneous inlier" is the name for the ACS
      top-code and for open_quarter.fillna(1).  States exactly when
      deletion is and is not acceptable.

  NOTES_five_facets_2024.md
      Vision paper.  Five facets (data, source, system, task, human) and
      a 29-dimension glossary.  Gives the modern name for our worst
      defect class -- "hidden missing values" / disguised missing values,
      with a detector (FAHES).  EU AI Act Article 10 names
      representativity, accuracy, completeness and relevancy, which gives
      our rent_index finding legal framing.

  NOTES_dq_tools_survey_2019.md
      667 tools found, 13 evaluated against 43 requirements.  Empirical
      evidence that the academic dimension-and-metric programme did not
      reach practice: zero of thirteen tools implement a consistency or
      timeliness metric.  The 43-item catalog is a scorecard we can be
      graded against.  Also: no tool does outlier detection well, so our
      gap is the market's gap.
```

### If you read three, read these three

```
  NOTES_daganzo_1984.md
      Read first, and read the first line first. It is the ONE file here
      written without the PDF open, because no Daganzo paper is on disk or
      obtainable from this host. It says so at the top and then does the
      honest thing instead: what cost/daganzo.py actually computes, what
      Larson & Odoni sec. 6.4.8 does say (K ~= 0.765, read in full), four
      numerical experiments, and a numbered checklist of what must be
      checked against the original. It is the model for how to write up a
      source you could not get, and the cost model rests on it.

  NOTES_LEAKAGE_DECISIVE.md
      The decisive test on the one covariate that carries the choice model.
      Forced onto a CBP vintage strictly earlier than MWPVL's stated
      opening rather than the OSHA upper bound, warehousing_establishments
      keeps 79% of its measured value on 29 of 94 decisions. Read
      NOTES_COVARIATE_LEAKAGE.md first if you want the accusation; this is
      the verdict.

  NOTES_METRO_ENTRY.md
      The pre-registered negative result, executed against
      PREREG_METRO_MODEL.md and its recorded md5 before anything was
      fitted. H0 on every arm and every model form. This is the shape the
      project's central claim takes.
```

### Papers read, with the PDF open

```
  NOTES_rahm_do_2000.md            (above)
  NOTES_fellegi_holt_1976.md       (above)
  NOTES_winkler_rr99_01.md         (above)
  NOTES_van_den_broeck_2005.md     (above)
  NOTES_five_facets_2024.md        (above)
  NOTES_dq_tools_survey_2019.md    (above)

  NOTES_little_rubin_ch1_3.md
      Chapters 1-3 only: patterns, mechanisms, and why complete-case
      analysis is the wrong default. Diagnosis for our rent_index hole;
      no treatment built.

  NOTES_gneiting_raftery_2007.md
      JASA 102(477). Propriety, the Brier score, and the finding that
      skill scores are generally IMPROPER even when the rule is proper.
      The defence of this project's headline-metric change.

  NOTES_hakimi_1964.md
      Optimum locations of switching centers. Read in full, and it does
      NOT license the node restriction we claimed from it.

  NOTES_klose_drexl_2005.md
      The facility-location survey behind cost/depots.py's p-median.

  NOTES_holmes_2011_capital_and_cannibalisation.md
      Read selectively for two questions: a dollar figure on opening a
      facility, and what the cannibalisation number measures. Sec. 8.3's
      inconsistency result is why the swap design is not open to us.

  NOTES_hns_2023_capital_and_cannibalisation.md
      Houde, Newberry & Seim on the same machine applied to Amazon. Same
      two questions, and the paid-data version of our own panel.

  NOTES_train_ch02_properties.md
      Choice-set properties. Carries sec. 6.1, THE CORRECTION: §2.2 is not
      what the hazard model broke.

  NOTES_train_ch03_logit.md
      The most load-bearing chapter in the list. §3.4 Ex.2 (V = ln(beta'a)),
      §3.7.1 p. 61 (the assumption that WAS broken), §3.8.1 (the metric).

  NOTES_train_ch04_gev.md
      GEV and nested logit. Why our two-factor decomposition IS a nested
      logit, and why we still do not fit one.

  NOTES_train_ch08_estimation.md
      Numerical maximisation. The bootstrap at §8.6, and the precondition
      — "if this sample is large enough" — that our sample fails.

  NOTES_train_ch13_endogeneity.md
      Control functions, and BLP verified verbatim as unavailable to us.
```

### Experiments and measurements run inside this project

These follow the same seven-part discipline where it applies, but the source
is an artefact under `outputs/metrics/` rather than a PDF.

```
  COVARIATES_TRIED.md          every covariate tried, and why each failed
  NOTES_COVARIATE_SEARCH.md    the panel's unused columns, and the two
                               reasons none of them can help
  NOTES_COVARIATE_LEAKAGE.md   the accusation: the warehousing covariate
                               probably contains its own outcome
  NOTES_LEAKAGE_DECISIVE.md    the verdict on that accusation (above)
  NOTES_METRO_ENTRY.md         the pre-registered H0 (above)
  NOTES_EXPANDED_REFIT.md      refitting the choice model on the 693-row
                               panel: 483 decisions, same conclusion
  NOTES_GBM_BENCHMARK.md       the atheoretical ranker the structural model
                               had to lose to, and the re-split intervals
                               that resized "beats" down to "matches"
  NOTES_PANEL_EXPERIMENTS.md   five panel compositions, two algorithms, and
                               one covariate that had never been tried
  NOTES_CATCHMENT_RADIUS.md    the radius moves the sample by 3.6x; the
                               band it has needed since day one
  NOTES_WHITE_SPACE.md         where is there unserved demand, and does
                               asking predict anything
  NOTES_daganzo_1984.md        the exception to this directory's rule
                               (above)
```

### Retired lines of work — notes moved out with their code

Four notes left this directory when the work they describe was retired. They
live beside the code and artefacts they belong to, under
[`../../experiments/`](../../experiments/README.md), which is the index for
all five retired lines:

```
  ../../experiments/hazard-model/notes/NOTES_HAZARD_REVIVAL.md
      The ZCTA-quarter hazard model, revived on 6.7x the events and
      retired a second time. A constant is still better calibrated in
      17 of 17 comparisons.
  ../../experiments/gravity-network/notes/NOTES_GRAVITY_NETWORK.md
      Whole-network pull against distance-to-nearest. A better
      measurement that does not predict better.
  ../../experiments/percapita-logrel/notes/NOTES_PERCAPITA.md
  ../../experiments/percapita-logrel/notes/NOTES_LOG_RELATIVE.md
      Per-household and log-relative transforms. Neither rescues the
      covariates, and one broke the estimator in a way worth reading.
```

Add your own line to the appropriate block as you read; do not fold someone
else's entry into yours.

---

## Papers we know we need and do not have

Recorded here so the gap is visible rather than rediscovered. None of these
is in `../Research/`.

```
  Winkler (1998), "Problems with inliers", Census Bureau RR98/05
      Cited by Van den Broeck as ref [23].  The obvious next paper if
      erroneous inliers become a workstream.  rr99-01 has NO inlier
      content -- do not substitute it.

  Qahtan et al. (2018), "FAHES: A robust disguised missing values
  detector", KDD
      The detector for the class our ACS top-codes belong to.

  Hernandez & Stolfo (1998), "Real-World Data is Dirty: Data Cleansing
  and the Merge/Purge Problem"
      Rahm & Do ref [15].  The primary source for multi-pass windowed
      matching, which linkage.py's blocking approximates.

  Little & Rubin, Statistical Analysis with Missing Data
      Partially covered by NOTES_little_rubin_ch1_3.md.

  Daganzo (1984), Transportation Science 18(3) 231-253 and 18(4) 331-350
  Beardwood, Halton & Hammersley (1959)
      The continuous approximation in cost/daganzo.py and the constant
      bhh_constant = 0.57.  NOT ON DISK, NOT READ, and both DOIs return a
      Cloudflare challenge from this host.  NOTES_daganzo_1984.md exists
      anyway (added 2026-09-14) and is the EXCEPTION to this directory's
      one-file-per-paper-read rule: it says so in its first line, quotes
      no page number from Daganzo, and instead records what the code
      does, what Larson & Odoni's Urban Operations Research sec. 6.4.8
      does say (K ~= 0.765, retrieved and read in full), four numerical
      experiments, and a numbered checklist of what must be checked
      against the original.  Read it before writing a replacement.
      Daganzo, Logistics Systems Analysis (Springer) is the most
      obtainable substitute and READING_LIST.md item 7 should be
      re-upgraded -- it was downgraded on the grounds that the VALUE is
      insensitive, which does not touch the DERIVATION or the CONDITIONS
      OF VALIDITY, and those are the actual gap.

  Daganzo (1984), "The length of tours in zones of different shapes",
  Transportation Research Part B 18(2) 135-145
      Confirmed to exist (274 citations) and almost certainly the real
      source of bhh_constant = 0.57.  REFERENCES.md does not cite it.
      READ THIS BEFORE THE OTHERS.  Note that REFERENCES.md's second
      "Daganzo 1984" entry, Transportation Science 18(3) 231-253, is
      NOT Daganzo -- it is Vaughan (1984), 231-244, on a different
      subject.  See NOTES_daganzo_1984.md sec. 1.1.1.

  Merchan & Winkenbach (2019), "An empirical validation and data-driven
  extension of continuum approximation vehicle routing models", MIT
      hdl.handle.net/1721.1/140763 -> dspace.mit.edu, blocked here.
      An EMPIRICAL VALIDATION of the approximation cost/daganzo.py uses,
      which is the thing ALTERNATIVES.md says we cannot do.  Highest-value
      single download available to this project; get it from a machine
      with normal network access.
```
