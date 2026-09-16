# Career materials — index

*Index last updated 2026-09-16, after a FOURTH pass. The first two passes
(2026-09-13, 2026-09-14) corrected numbers. The third (2026-09-15) changed the
position: the material is now organised around the engineering and the research
conduct, because the prediction model largely did not work and a pitch
organised around it is a pitch organised around an absence. The fourth
re-derived every figure in these five files from the artefact itself and found
that three of the third pass's own corrections were wrong — see "What was
walked back on 2026-09-16".*

Four documents about how to talk about this project to a recruiter or a hiring
manager. Nothing in here feeds the model, the pipeline or the viva. It is the
only folder in `docs/` that is not about the research.

**Read "What was fixed" and "What was walked back" before you copy a single
line of this into a CV.** These files have quoted results the project does not
have, twice, and the third pass found four more overstatements — in work
written that same week. The corrections are listed below so that anyone who
copied the old bullets into a CV, a LinkedIn post or a covering letter can find
and unpick them.

---

## The one-paragraph version of the position

The model did not work. Four specifications, eighteen arms, one hashed
pre-registration failed 0 of 7 years. What the project has instead is an OCR
pipeline that recovered 1,904 facility records from a PDF with no table layer
and hardened it for a locked-down grid; a research-conduct record that includes
a pre-registration failed and reported, a circularity audit of the project's
own key variable, a significance claim withdrawn on the author's initiative,
and fabricated values found in the author's own figures; one transferable
finding (the dispersion rule); and one working product (a parcel-level cost
model). Lead with the engineering, follow with the conduct, and give the model
results third, as measurement rather than as apology.

---

## What is in this folder

There are no `.txt` twins any more; they were deleted on 2026-09-16 and the
reason is at the end of this file.

```
  LINKEDIN.md             NEW 2026-09-15. Four complete, postable drafts -
                          the OCR/extraction work, the pre-registration that
                          failed, the dispersion rule as a tip other analysts
                          can use, and a short "what I'd do differently" -
                          plus a headline and an About paragraph. Every post
                          carries a checking note naming the artefact behind
                          each figure; STRIP THOSE BEFORE POSTING. Three posts
                          from the old eight-post series are marked dead in
                          PORTFOLIO_PLAYBOOK.md section 4, including the week-1
                          hook "can you predict where Amazon builds next",
                          which promised a scoreable outcome that came back no.

  INTERVIEW_STORIES.md    NEW 2026-09-15. Six STAR stories, each with the file
                          that proves it. Three are about mistakes and that is
                          deliberate: the fabricated 95% confidence interval
                          found in an audit of the author's own figures; the
                          estimator bug that returned a wrong answer with a
                          finite, BETTER objective value; and overloading a
                          shared six-core machine to load average 44 after
                          being told in writing not to. Do not soften these
                          into near-misses in the room.

  PORTFOLIO_PLAYBOOK.md   How the project becomes interviews: which assets a
                          hiring manager actually values, how three people
                          share one project without reading as one person's
                          work divided by three, ready-made CV bullets per
                          person, LinkedIn strategy (copy now in LINKEDIN.md),
                          and an interview talk track.
                          CORRECTED TWICE (2026-09-13, 2026-09-14) and
                          REPOSITIONED once (2026-09-15). §1 now leads with
                          the extraction pipeline rather than the failed
                          backtest; §2b is new and maps the work to four role
                          families with the evidence for each; §3 gains six
                          data-engineering bullets and three research-conduct
                          bullets that are stronger than anything that was
                          there before; §5 opens the 90-second answer on the
                          data recovery instead of on the model. §3 still ends
                          with an explicit list of claims that may NOT go on a
                          CV until the work behind them exists. That list grew
                          again on 2026-09-15, this time with NEW work being
                          overstated rather than old work going stale.

  SCALE_AND_IMPACT.md     The answer to "a fourteen-megabyte panel? that's a
                          college project." Reframes the work from row count
                          to decision value ($7.2bn-$12.1bn of capital
                          allocation across 2,413 ZCTAs), lists the axes on
                          which the project genuinely is industry-grade
                          (integration across 14 sources at 8 grains, the
                          2^2413 portfolio search space, two measured negative
                          results), and scripts the "our data is 100x bigger"
                          question.
                          CORRECTED 2026-09-14, and it needed it. The previous
                          version of this index called it "LARGELY CURRENT"
                          with "one stale row". That was wrong: it carried at
                          least seven false or stale items, including an
                          unbuilt OSRM redesign billed in bold as "the
                          strongest engineering signal in the whole project".
                          See below.
                          EXTENDED 2026-09-15 with a new axis — data recovery —
                          which is now the strongest magnitude claim in the
                          file and the only one about something BUILT rather
                          than something measured. The facility-panel block
                          moved from 104 rows to 693; §9 went from two
                          memorised sentences to three, with the extraction
                          first; and §7 gained the shared-machine incident as
                          a counter-example to its own thesis about compute
                          restraint.
```

> **Corrected 2026-09-14 — and it changes what you may say out loud.** The
> `PORTFOLIO_PLAYBOOK.md` entry above said the successor was one "that a single
> raw covariate **beats**". It now says **matches**, and both files below have
> been changed to match. This is a retraction, not an update: "beats" was read
> off one seeded 56/38 split where the raw warehousing count led 8-7 at top-1
> and 20-19 at top-10. Fifty paired re-splits of the same 94 decisions put that
> lead at **0.36 hits of 38, paired sd 1.14**, with the raw count losing 11 of
> the 50 (`../../outputs/metrics/gbm_benchmark.json`, `across_repeats`). One
> third of a decision is not a result.
>
> **The second negative result is intact and still goes in the talk track.**
> A three-parameter model that a free Census column matches is a model whose
> estimation bought nothing — which is the thing worth saying in an interview.
> Say "a raw covariate matched it"; do not say "beat it", because that is a
> number you cannot defend if anybody asks for the spread.

---

## Start here

`PORTFOLIO_PLAYBOOK.md` §1 and §2b, for the position and the roles it maps to.
Then `LINKEDIN.md` and `INTERVIEW_STORIES.md`, which are where the copy lives —
those two are the ones you will actually use. `SCALE_AND_IMPACT.md` is the
answer to one specific objection ("that's a college project") and can wait
until you hear it.

Read all four with a pen. None is a model for the others: the two older files
have been through two correction passes and a repositioning, and the second
pass found more in `SCALE_AND_IMPACT.md` than in the playbook.

What `SCALE_AND_IMPACT.md` does do well is keep its corrections visible in the
text — it names the figures that were wrong (5,200 ZCTAs, $15.6-26bn, "~4,000
facilities, 3 operators", "800,000 OD pairs", and now the OSRM disk savings)
and replaces them with what is on disk. Copy that habit, not its accuracy
record. Its own line is the rule for this whole folder:

> *Do not put an unbuilt number on a resume, and do not round 43 up to
> "thousands of facilities"; both are the kind of claim an interviewer can
> check in a minute.*

Then read `PORTFOLIO_PLAYBOOK.md` with the same pen. Both files have broken
that rule; both have been corrected twice.

---

## What is stale — read this before using anything here

### PORTFOLIO_PLAYBOOK.md quoted results that do not exist — corrected

The playbook was written before the model was fitted and read as though the
backtest had already succeeded. The model was subsequently built and **failed**
— AUC 0.6894 against 0.5000 for a constant, calibration error worse than a
constant, both hold-outs negative (`../PLAN.md` §2). Each of the following was
in the file as something to say out loud, and each has been removed or
replaced:

```
  was                                        now
  -----------------------------------------  ---------------------------------
  headline asset: "Trained on <=2023,        the headline asset is the
  predicted 2024-25 openings, AUC 0.84"      measured loss to a null, quoted
                                             as the Brier pair
  CV bullet: "out-of-time backtest ...       the P1 bullets quote 0.6894,
  achieved AUC 0.84 and precision@100        0.019522 vs 0.019614, 0.00863 vs
  of 0.61"                                   0.00005, all from hazard_report
                                             .json. precision@100 was never
                                             computed and is now listed as a
                                             claim that may not be made
  "walk me through the project": "...        the answer opens with the failure
  backtested it ... AUC 0.84"                and spends its 90 seconds on the
                                             diagnosis
  "Corrected firm self-selection with a      removed. No such model exists in
  Heckman two-step model"                    src/
  "conformal prediction intervals with       the measurement is 88.19% against
  empirically verified 90% coverage"         a nominal 90%, inside the
                                             two-sigma band 351 independent
                                             units allow — and a tenth of the
                                             prediction sets are empty. The
                                             bullet now says both halves.
                                             (This entry previously said
                                             conformal was NOT BUILT. That was
                                             wrong: src/siting_atlas/models/
                                             conformal.py exists and ran. The
                                             defect was the number, not the
                                             existence of the work)
  "distance decay of cannibalisation         removed. Never estimated; the
  (-12% within 8 km ...)", and the same      LinkedIn post that carried it is
  numbers as LinkedIn post 4                 replaced by one about the failure
  "Top-K rank stability (share of 10,000     removed. The Monte Carlo pass is
  Monte Carlo draws ...)"                    a backlog item
  LinkedIn post 6, "Does the Amazon model    replaced by the unit-of-analysis
  predict Walmart?"                          story, which did happen
  "Shipped a public decision-support         removed. The Streamlit dashboard
  application ...; sub-5-second load"        runs locally; it is not deployed
                                             and load was never timed
  "Cut peak disk from ~60 GB to ~8 GB by     removed. No OD parquet, no OSRM
  precomputing an 800,000-pair drive-time    artefact; the cost model uses
  matrix"                                    great-circle distance x 1.30
```

**Second pass, 2026-09-14.** The list above was not the end of it. These were
still in the playbook after the first correction:

```
  was                                        now
  -----------------------------------------  ---------------------------------
  "A published open dataset" offered as a    caveated in place and added to the
  rare signal, with no caveat, while the     "not yet true" list. No dataset,
  line above it correctly caveated the       no data card, no release exists
  dashboard
  "surfacing the selection propensity as     removed from the P3 bullet and
  a tax-abatement counterfactual", and       from the spoken answer. It is the
  the same idea closing the 90-second        Heckman claim this folder deleted
  answer                                     once, re-entering in other words.
                                             grep -ri heckman src/ is empty
  "commits $1.32bn across 330 activations,   282 activations, $1.128bn,
  break-even 1.389, optimality gap 13.4%"    break-even 1.343067, gap 10.73%,
                                             from run 20260914-002431-7419
  "median $1.09 per parcel"                  $1.0830, run 20260914-002418-0623
  "about 104 real decisions"                 94. 104 is the raw row count of
                                             national_facilities.csv, not the
                                             fitted decision count
  "2,413 ZIP-code areas" as the FITTED       the hazard risk set was 1,756
  sample                                     units; 2,413 is the pilot SCOPE
  "Train's text gives the test in one        WRONG SECTION, and it was inside
  line: the alternatives have to be          the answer said OUT LOUD. Train
  mutually exclusive"                        2.2 is about a choice set facing a
                                             decision maker and he calls the
                                             criterion "not restrictive"
                                             (p.12). A hazard on area-quarters
                                             has no decision maker. The
                                             assumption actually violated is
                                             INDEPENDENCE ACROSS OBSERVATIONS,
                                             Train 3.7.1, p.61 - i.e.
                                             clustering / pseudo-replication
  "my first model hit 4% error"              no 4% figure in any artefact.
                                             Marked unverified; the LinkedIn
                                             post now tells the circularity
                                             story without a number
  "a median of 58 ZIP codes" per station     resolved on 2026-09-16, and the
                                             number is 39. hazard_revival.json
                                             gives a median of 39 ZCTAs
                                             switched on per opening at the
                                             15-mile catchment. 58 belongs to
                                             the retired pilot specification -
                                             correct only in a sentence that
                                             says "the pilot", 39 otherwise
  "every headline figure reads from the      restated. The generated FIGURES
  pipeline's JSON rather than being typed"   do; the PROSE does not, which is
                                             how every item in this table
                                             survived beside a correct chart
  the Monte Carlo as a backlog item          it RAN on 2026-09-14: 500 draws,
                                             seed 20260914. Not 10,000, not
                                             24 billion, and NOT a confidence
                                             interval
```

The irony was that the playbook's own §8 stated the rule it broke: *"A
polished LinkedIn series about a project that doesn't run is worse than
silence — it's checkable, and someone will check."* §8 now records the breach
rather than just the rule.

The file's *structure* was sound and is unchanged — the three-person split by
job family, the eight-post cadence, the "did you use AI" answer, the
pre-application checklist. It was the numbers that had to be replaced, and the
replacement is a better pitch: a candidate who built a model, tested it
properly, found it failed, diagnosed why across two literatures and changed
the specification is more employable than one with an unverified 0.84.

**If you have already used the old bullets**, the table above is the list to
grep your CV and LinkedIn against.

### SCALE_AND_IMPACT.md — seven items, all corrected 2026-09-14

This section previously said "one stale row" and that "everything else in that
file reconciles". Both statements were wrong. What was actually in the file:

```
  was                                        now
  -----------------------------------------  ---------------------------------
  "peak disk, after the OSRM redesign        REMOVED. No OSRM was ever run, no
  ....~8 GB", billed in bold as "the         OD parquet exists, and no disk
  strongest engineering signal in the        figure was ever measured. The ~60
  whole project"                             GB and ~8 GB are design estimates
                                             from ADR-0002, an ACCEPTED ADR
                                             that was never implemented. The
                                             same file already said the OD
                                             matrix was unbuilt sixteen lines
                                             later. This was the single
                                             highest-risk sentence in the
                                             folder
  "24 billion simulated NPV realisations     both deleted. There is no standard
  with bootstrap CIs"; "I'd rather spend     error of any kind in this project.
  the compute budget on 24 billion           24 billion is a specification in
  uncertainty draws"                         scope.json that was never
                                             executed. What ran is 500 draws,
                                             and its artefact says in terms
                                             that it is not a confidence
                                             interval
  "shipped a decision tool"                  "built". No Dockerfile, Procfile
                                             or fly.toml exists. The playbook
                                             already forbade the word
  "317 of 500 activations, 13.03% gap,       282, 10.73%, $1.128bn, about 44%
  deploys $1.27bn, leaves a third            declined. And "10.79% better NPV
  unspent, 10.79% better NPV than the K      than naive" is NOT COMPUTED in the
  cheapest ZCTAs"                            current run - naive_breakeven is
                                             null - so it was removed as
                                             unverifiable
  "1,081,312 rows x 44 columns" (twice)      50 columns
  "334 depots across 11 CBSAs"               "11 CBSAs" removed; 334 stands.
                                             The priced table covers 10 metros,
                                             and 334 is the sum over those ten
                                             of ceil(daily parcels / 40,000),
                                             recomputed from the baseline
                                             parquet. 329 is the same quantity
                                             taken as one national division.
                                             Always say which
  "four collection methods failed, the       FIVE failed, one worked. Satellite
  fifth worked"                              dating was attempted 2026-09-14
                                             and failed
  "which took a solve from 653 seconds to    marked unverified and cut from the
  30"                                        spoken answer. In no artefact
  "every word of it is defensible"           now true, but only because the
                                             OSRM claim above was removed
  "What broke?" -> "OSRM redesign";          replaced with true answers that
  "How did you know it worked?" ->           are also better: the 2.74x
  "out-of-time backtest, conformal           activation-capital overcharge in
  coverage"                                  objective.py, 42% of depots over
                                             40,000 parcels/day, rent_index
                                             missing for 94.3% of ZCTAs and
                                             still listwise-deleted, 0 of 104
                                             facilities geocoded - and, for the
                                             second question, that it did NOT
                                             work and the evaluation is the
                                             accomplishment
```

Added to that file rather than removed: the two negative results from this
week — satellite dating (36% of 107 estimates logically impossible) and the
labelling programme (80% of 362 rows already classified, 13 genuinely new) —
both written failure-first.

---

## What was walked back on 2026-09-15 — third pass

The first two passes caught old claims going stale. **This pass mostly caught
new work being described more strongly than the artefact supports**, which is
the harder one, because there is no superseded document to blame.

```
  was                                        now
  -----------------------------------------  ---------------------------------
  the dispersion rule as "21 of 21 each      21 TERMS IN TOTAL; written as "21
  way" - the phrasing in                     of 21 each way" it reads as 42
  ../PREREG_METRO_MODEL.md lines 40-44       observations and doubles the
  and MODELS_EXPLAINED.md section 7          apparent evidence. But the
                                             replacement this pass wrote,
                                             "7 of 7 and 14 of 14", was ALSO
                                             WRONG - see the fourth pass below.
                                             The gap itself is real: nothing
                                             falls between cv 0.5918 and cv
                                             1.3993
  the dispersion rule "shown causal          the knob experiment is real and is
  with a knob"                               the best part of the claim. But
                                             NOTES_GRAVITY_NETWORK.md section 5,
                                             the source, says in terms that it
                                             "is not a causal demonstration".
                                             MODELS_EXPLAINED.md section 7
                                             upgrades it past what its own
                                             source allows. The career files
                                             use the source's framing
  geocoding "65% -> 72%" as something an     72.3% (501 of 693) is real. The
  interviewer can open in the repo           rest of what this row said was
                                             WRONG - see the fourth pass below.
                                             Neither geocoded file is
                                             committed, and both read 72.3%
  "334 depots across 11 CBSAs" (again -      only the "11 CBSAs" was ever
  it re-entered via the cost-model story)    wrong. 334 = per-metro ceil summed
                                             over the TEN priced metros, which
                                             is what the solver opens;
                                             cost/params.py:220's "~329" is the
                                             national division of 13,152,992 by
                                             40,000. Both docstrings are right
                                             about different things and both
                                             should say which
  the OCR merge quality as a percentage      MWPVL_OCR_PIPELINE.md section 13.1
  ("97% clean, up from 92%")                 says the 517-of-535 figure is a
                                             working measurement from the fix
                                             session and is NOT reproducible
                                             from an artefact. Quote the counts
                                             - 41 merged rows falling to 18
  the cost sensitivity table's percentages   this entry is WITHDRAWN - see the
  (-17.0%, +0.6%, +1.0%, +4.4%)              fourth pass below. The published
                                             table was very nearly right and
                                             the "correction" was not
  the validation figures 157 linked / 10     the current artefacts say 208 /
  falsified / 93.6%, and 556 of 557 /        11 / 94.71% and 604 of 606 /
  99.8%, quoted in five documents            99.67%. These moved UP, which is
                                             why nobody noticed; a figure that
                                             goes stale in your favour is still
                                             stale
  the week-1 LinkedIn hook, "can you         DEAD. It promised a scoreable
  predict where Amazon builds next using     outcome and the outcome was no.
  only public data? I'm going to find out    The pre-registration post in
  in public"                                 LINKEDIN.md is the honest version
                                             of the same idea, told after the
                                             fact instead of before it
```

**One thing was walked back in the other direction, and it belongs on the
list.** The facility-panel block in `SCALE_AND_IMPACT.md` said "0 of 104 rows
are geocoded", which was true when written and is now two results out of date
in the project's favour. Understating is not safer than overstating; it is the
same defect, and it cost a real asset a year of visibility in these files.

---

## What was walked back on 2026-09-16 — fourth pass, on the corrections themselves

**This pass re-derived every figure in these five files from the artefact
rather than from another document, and found that three of the third pass's
corrections were wrong.** Not the original claims — the *fixes*. That is a
worse failure than the one it was fixing, because a correction reads as
already-checked and nobody re-checks it.

```
  the third pass said                        the artefact says
  -----------------------------------------  ---------------------------------
  the dispersion rule is "7 of 7 and 14      7 of 7 and 9 OF 14. Re-derived
  of 14"                                     from arms.*.verdicts.*.state in
                                             gravity_network.json, which
                                             covers all 21 terms. The rule is
                                             ASYMMETRIC: cv below 0.6 is
                                             SUFFICIENT FOR FAILURE (7 of 7 at
                                             the boundary); cv above 1.3 is
                                             NECESSARY BUT NOT SUFFICIENT (9 of
                                             14 interior). The five high-cv
                                             failures are all sortation-side,
                                             four of them carrying square
                                             footage. Counting strictly -
                                             interior in EVERY arm - gives 8,
                                             because fulfilment_proximity is
                                             interior in two arms and
                                             boundary-straddling in a third.
                                             Descriptive, 21 non-independent
                                             terms, one run, one vintage
  the committed geocoding artefact "is       there is NO committed geocoding
  still 455 of 700 = 65.0%"                  artefact. git ls-files lists
                                             neither geocoded_expanded.csv nor
                                             the data/interim/ rebuild, and the
                                             two files are BYTE-IDENTICAL and
                                             both read 501 of 693 = 72.3%.
                                             65.0% = 455 of 700 was measured on
                                             the superseded 700-row panel and
                                             nothing on disk reproduces it.
                                             Quote the level, not the lift; the
                                             denominators differ
  the cost scenarios are "-16.65%,           -17.1% (dense routing), +0.5%
  +0.97%, +1.38%, +4.84%" and the            (high fuel), +0.9% (pessimistic
  parquets are a day older than the          tour), +4.4% (congested).
  baseline                                   cost_report.json was regenerated
                                             (20260916-024154-0aa8) and holds
                                             all five scenarios; all five
                                             parquets share one mtime, so
                                             nothing is a day apart; and the
                                             report and the parquets agree to
                                             the fourth decimal. The published
                                             table this entry "corrected" was
                                             right to within a rounding step
  "a median of 58 ZIP codes per station"     39, not unverified. hazard_revival
  is UNVERIFIED                              .json: median 39 ZCTAs per opening
                                             at the 15-mile catchment. 58 is
                                             the retired pilot spec
  "334 depots across 11 CBSAs" is not in     334 is derivable and correct: the
  any artefact                               sum over the TEN priced metros of
                                             ceil(daily parcels / 40,000).
                                             Only "11 CBSAs" was ever wrong
  787 tests passing                          660 collected across 49 files,
                                             658 passed, 2 xfail. The suite
                                             SHRANK because 11 test files
                                             retired to experiments/retired-
                                             tests/ with the code they covered,
                                             taking 138 tests - not because
                                             tests were deleted. Say it that
                                             way if anyone has seen 798
  39 of 133 modules unreachable from any     75 of 138, re-measured. The gap
  test                                       widened; it did not close
```

**The lesson is one line and it is the most important line in this folder.**
Three of these came from reading a *document* that had already been corrected
once. A correction is a claim; source it from the artefact, exactly as you
would source the claim it replaces.

---

## The .txt twins — deleted on 2026-09-16

There used to be a `.txt` next to every `.md` here. **All five have been
deleted, and they should not come back.**

They were generated by `tools/docs/md_to_txt.py` via `scripts/build_docs.sh`,
which walks the `siting-atlas/` tree only. These files do not live in that
tree, so the twins could never be regenerated in place — every one of them was
*newer than its `.md`* by the time they were removed, which means anyone who
opened the `.txt` was reading a different document from anyone who opened the
`.md`, with no way to tell which was current. A stale copy of a
recruiter-facing file is the same defect as a stale number in one, and it is
harder to notice.

If a plain-text rendering is ever wanted again, generate it at the moment of
use and do not commit it beside the source.
