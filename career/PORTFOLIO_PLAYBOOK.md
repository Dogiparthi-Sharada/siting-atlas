# Portfolio Playbook

**How this project turns into interviews and a full-time offer — and which parts
of it are actively working against you.**

> Written for three people sharing one project. That is the central problem this
> document solves: **if all three of you tell the same story, a recruiter reads it
> as one person's work divided by three.**

---

## 1. Blunt assessment: what is and isn't hireable here

> **Repositioned 2026-09-15, and this is the largest change this file has had.**
> Every earlier version of this document was organised around the model. The
> model largely did not work — not in the interesting-failure sense only, but
> across four specifications and eighteen arms — and organising a pitch around
> it means organising it around an absence.
>
> **The strongest career story in this project is the engineering.** An OCR
> pipeline that recovered 1,904 facility records from a PDF with no table
> layer, hardened for a locked-down grid, and validated three independent ways
> is an unambiguous achievement that anyone can check in ten minutes. The
> second-strongest is the research conduct: a pre-registration with a hash that
> was then failed and reported, a circularity audit of the project's own key
> variable, and a significance claim withdrawn on the author's own initiative.
> The model results are the third thing you say, not the first.
>
> This is not a retreat from honesty into engineering. It is the recognition
> that "I scored my model against a null and lost" is one good sentence, and
> after it you need something to show.

### What makes hiring managers lean in

| Asset | Why it's rare in 2026 |
|---|---|
| **A data-recovery pipeline that produced the project's target variable** | 1,904 facility records out of a 117-page PDF whose tables are images — columns recovered from pixel-density valleys, rows anchored on postal codes, and a relocatable tesseract bundle carrying its own dynamic loader because the grid's glibc is older than the build host's. This is the asset most candidates do not have and cannot fake |
| **A pre-registration that was written, hashed, and then failed** | `metro_entry.json` carries the md5 of the prereg file and a `written_at` 24 minutes after it. The criterion was missed 0 of 7 years, and the failure is reported in the artefact along with four self-logged deviations — one of which says the design is biased *against* the hypothesis being tested |
| **Three bugs found in the candidate's own estimator** | Including one where the optimiser gained likelihood by pushing non-chosen alternatives below zero probability. Finding a defect that produces a *finite, better* objective value is a different skill from finding a crash |
| **A model that was scored against a null, and lost** | Almost every student project reports in-sample fit. "Brier 0.019522 against 0.019614 for a constant, on the same 8,044 rows" is a *forecast that was scored*, and the fact that it lost is what proves the test was real |
| **A screening rule other analysts can use** | Within-group coefficient of variation below ~0.6 predicts a boundary coefficient — 7 of 7 on one panel. Above ~1.3 it is *necessary but not sufficient*: 9 of 14 came back interior. So the rule screens out, it does not screen in. There is a knob that moves the cv 28x on the same underlying facilities and moves the coefficient with it. See §3 for the exact phrasing, which matters |
| **A diagnosis, not just a number** | Anyone can report a bad metric. Naming *why* — the unit of analysis was wrong — and changing the specification for a stated reason is the part that reads as senior |
| **A successor that also failed its own test** | Rarer still. The conditional-choice model was fitted on 2026-09-14 and a single unfitted covariate — warehousing establishment count — matches it out of sample, so three estimated parameters bought no ranking. Two negative results, both volunteered |
| **A live URL that loads** | A link beats a repo; a repo that runs beats a repo that doesn't. *Not true yet: the dashboard runs locally and is not deployed* |
| **A published open dataset** | Very rare. It says "I produced something others use," not "I consumed a tutorial." *Not true yet: no dataset, no data card and no release exist. This row is an argument for doing it, not a claim that it was done* |
| **Honest negative results** | See rows 1 and 3. Nobody expects it from a student, and this project has several |
| **Reproducibility that actually works** | Clone → `make all` → green. Interviewers *do* try this |

> **Corrected 2026-09-14 — and this one is an interview liability, so read it.**
> Row 3 said the raw warehousing count **beats** the conditional-choice model
> out of sample. It says **matches**, and the same fix has been made to the
> ninety-second answer in §3. The reason is not that new work superseded the
> claim; the claim was simply **wrong**. It came from a single seeded 56/38
> split — the count led 8-7 at top-1 and 20-19 at top-10, gaps of one hit.
> Refit across fifty paired re-splits of the same 94 decisions and the count's
> lead is **0.36 hits of 38 against a paired sd of 1.14**, and it loses 11 of
> those 50 splits outright (`../../outputs/metrics/gbm_benchmark.json`,
> `across_repeats`). An interviewer who asks "how big was that margin?" would
> have ended the story there.
>
> **Row 3 still belongs on the list and the negative result is untouched.**
> Fitting three parameters bought no ranking improvement over counting
> warehouses — that is the volunteered failure, and it survives the word
> change intact. What does not survive is the stronger, more quotable version.
> Use the true one.

**Read row 1 twice, because the instinct is to hide it.** An unverified 0.84 is
worth nothing to a hiring manager, because they have no way to check it and
they know the typical student number is in-sample. A measured 0.6894 that you
volunteered, next to the 0.5000 a constant gets, is checkable, and it tells
them you built the benchmark you then lost to. That is a rarer signal than a
good number.

### What is working against you — say it out loud

**An LLM chatbot over a database is no longer a differentiator. In 2026 it is
close to a negative signal** if it is the centrepiece, because it reads as
"followed a tutorial." Every applicant has a RAG project.

So do not lead with the agent. Lead with the causal work and the artefact that
runs, and let the agent be the *delivery mechanism* — because the genuinely
interesting thing about your agent is not that it answers questions, it's that
**it writes to a causal model and you built gates to stop it corrupting the
inference.** That framing is rare. "I built a text-to-SQL chatbot" is not.

Same logic kills the fine-tuned narrator as a résumé item: "fine-tuned a 3.8B
model to write dashboard captions" invites *"why not just call an API?"* and you
have no good answer. Cut it (see `ROADMAP.md`, Cut list).

### The assets ranked by career value per day spent

```
  1.  the OCR / extraction pipeline     (done)  -> lead with this; it is the
                                                   only thing here that is
                                                   unambiguously an achievement
  2.  the pre-registered failure        (done)  -> the story senior people
                                                   respond to
  3.  the self-audit record             (done)  -> three estimator bugs, the
                                                   circularity test, the
                                                   withdrawn claim, the
                                                   fabricated figures found
  4.  public facility-opening dataset   2 days  -> rarest signal you can send,
                                                   and the OCR work is 90% of
                                                   the cost already paid
  5.  the app, DEPLOYED                 2 days  -> the click-through; it runs
                                                   locally today, which is
                                                   not the same thing
  ---------------------------------------------------------------------
  ... the LLM agent                    ~2 weeks -> commodity unless framed
      as the gates story
```

Assets 1 to 3 are already paid for. The work that remains on them is not more
modelling — it is being able to tell each story from memory with its numbers,
which is what `INTERVIEW_STORIES.md` is for.

Asset 4 is now the highest-return two days in the project rather than the
second. The 1,904-record extraction, the three validations and the merge
diagnostics are done; what is missing is a data card, a licence check and a
release. Note the blocker first: the source PDF is **outside the repository and
untracked** (`../AUDIT_2026_09_14.md` §1.1) and the publisher has announced
withdrawal from free circulation. Resolve provenance and licensing before
publishing anything, or the dataset becomes a liability rather than an asset.

---

## 2. Three people, three stories

If all three of you write "built an AI-powered delivery expansion platform," a
recruiter cannot tell you apart and assumes inflation. Split the narrative by
**job family**, not by ego.

| | Target roles | Owns the story of | Leads with |
|---|---|---|---|
| **P1** | Data Scientist · Causal Inference · Marketplace/Ops Analytics | *Identification* | "How do you know it's causal, not selection?" |
| **P2** | Analytics Engineer · Data Engineer · Platform | *Reproducibility* | "It builds from cold in one command, offline" |
| **P3** | Product Analyst · BI/Viz · AI Product · Growth | *Decision delivery* | "Here's the number a city council acts on" |

Each person's résumé mentions the project once, with **different bullets**, and
each links to a **different entry point** — P1 to the methods paper, P2 to the
repo, P3 to the app. Same project, three legitimate specialists. That reads
as a real team, which is what it is. P3's link is a repo link until the app is
actually deployed; do not write "live" before it is.

---

## 2b. Which roles this actually maps to

*Added 2026-09-15. Four families, with the specific evidence for each. If a
posting does not match one of these four, the project is not your strongest
argument for it and you should lead with something else.*

**Data engineering / analytics engineering — the strongest fit.**
The evidence is the OCR pipeline end to end: table detection corrected from a
height filter that silently dropped five of thirteen tables to a width filter
with `EXPECTED_TABLES = 13` pinned; a single entry point with six distinct exit
codes; a preflight that fails in 30 seconds rather than after six minutes of
image extraction; a settings stamp that refuses to resume under different
parameters; atomic staging via `rename(2)` after an in-place `rm -rf` took down
62 running workers; and a success banner that counts only files the current run
produced, added after a run reported success on 36 leftover files while writing
none. Supporting: a 14-source ELT into a DuckDB star schema, 660 tests passing,
a six-file-per-run logging contract with five redaction mechanisms and a
credential sweep over 592 run directories that found zero hits outside `.env`.
*The weakness to name before they find it:* **75 of 138 source modules are not
reachable from any test**, and every module that writes a headline artefact is
among them. (The audit's "39 of 133" is stale; re-measured 2026-09-16, the gap
has widened rather than closed — `../AUDIT_2026_09_14.md` §2.2 predates the
retirement described in §3.)

**Applied research / data science with an evaluation focus.**
The evidence is the conduct rather than the results: a pre-registration with a
verified md5 and a 24-minute lead on the fit; a declared verdict arm chosen
before any model existed; an H0 finding that holds in all 18 arm × form × scope
combinations; an ablation followed by a decisive vintage test that separates
circularity from agglomeration, reported with its own upper-bound caveat; four
proper interval estimators run against one improper one, and the claim
withdrawn when three of three contained the null. Plus the dispersion rule,
which is a genuine methodological contribution at the scale a capstone can
support. *The weakness:* nothing in this project produced a positive result,
so the interview has to be about method. Some teams want that; some do not.

**Policy and public-interest analytics.**
The evidence is that the whole thing is built from public sources only
(ADR-0003), that it ranks a decision with public money on the other side of it,
and that it declines to overstate: the portfolio optimiser commits $1.128bn of
a $2bn budget and leaves about 44% unspent because the remaining activations
lose money, and it reports its own optimality gap (10.73%) against a computed
bound rather than claiming a guarantee that does not apply to a non-submodular
objective. The coverage artefact reports a *floor* on invisibility — of the 488
cities where the extract puts a delivery station, OSHA has ever inspected an
Amazon facility of any class in 138, or 28.3%, leaving 350 with no OSHA record
at all — rather than an estimate it cannot defend. Two qualifications travel
with it: OSHA's side is unrestricted by facility class, so the comparison is
conservative, and a two-list intersection is a floor, not a capture-recapture
estimate. *The weakness:* no stakeholder has used any
of it, and "planners, air districts, EJ orgs" is an audience you named, not one
that asked.

**Public-interest tech / research engineering.**
This is the intersection role and the one this project fits best of all: the
code *is* the deliverable, the failures are documented in the code rather than
in a retrospective, and the modules carry their own indictments — `params.py`
saying its own unit is wrong, `montecarlo.py` listing the parameter it forgot
to sample and calling every band a floor, `objective.py` saying the greedy
bound does not apply here and anyone claiming it is wrong. That habit is rare
and it is visible from a `git clone`. *The weakness:* several of those
documented defects are documented-and-unfixed, and an interviewer who reads the
code finds the admission before the repair. Have an answer for which ones you
would fix first and why (the capital unit, at 2.7x, is the right answer).

---

## 3. Résumé bullets that survive a six-second scan

**The formula:** `action + method + measurable outcome`. A number in every bullet.
No adjectives.

**The rule that overrides the formula: every number below is on disk in
`outputs/metrics/` today.** If you cannot open the artefact and point at it
while the interviewer watches, it does not go on the CV. Bullets for work that
is planned but not built are listed separately at the end of this section, and
they stay there until the work lands.

### P1 — identification and research conduct

*The first three are new on 2026-09-15 and they are better bullets than the
hazard ones below, because they are about conduct rather than about a number
that lost.*
```
· Pre-registered the success criterion for a metro-entry model - two clauses,
  a declared verdict arm, and a hash of the file - 24 minutes before fitting
  it, then reported that it failed: 0 of 7 held-out years on discrimination
  against a rank-by-households baseline, 3 of 7 on calibration, and the same
  verdict across all 18 arm / functional-form / window combinations tried.
  The prereg's own vintage-admissibility rule dropped 10 of its 12 covariates,
  and the deviation is logged in the artefact rather than in a footnote.
· Found and fixed three defects in my own conditional-logit estimator,
  including one where the optimiser gained up to 1.204 of log-likelihood by
  driving coefficients 20x-77x past the positivity ceiling and pushing 765 to
  4,816 non-chosen alternatives below zero probability - a defect that returns
  a finite, better objective and therefore triggers nothing. Diagnosed from a
  pattern rather than an error: in all five affected columns, the direction
  that "found" an effect was the direction with the cheaper feasibility
  ceiling.
· Audited the model's single load-bearing covariate for circularity by
  re-reading it from a data vintage predating each opening: 78.6% of its
  out-of-sample value survives, on 29 decisions, reported with the caveat that
  removing the leak and adding staleness are the same intervention so the gap
  is an upper bound. Separately withdrew a published coefficient interval after
  three proper estimators - a metro-clustered bootstrap and two sandwich
  variants - all contained the null that the improper one excluded.
```

The model bullets, which are still correct and still worth carrying, but below
the three above rather than in front of them:

```
· Built and scored a discrete-time hazard model of same-day-delivery
  expansion, fitted on a risk set of 1,756 ZIP-code areas inside a 2,413-ZCTA
  pilot scope, from public data only; benchmarked it against a constant-rate
  null on the same 8,044 held-out rows and reported that it lost - Brier
  0.019522 vs 0.019614, calibration error 0.00863 vs 0.00005. The
  specification has since been retired.
· Diagnosed the failure as a unit-of-analysis error rather than a sample-size
  one: one delivery station enables many ZIP codes at once, so 812 apparent
  events were 94 decisions plus a catchment radius. Named the violated
  assumption - independence across observations, Train (2009) section 3.7.1,
  p.61; the failure mode is clustering, not a non-exclusive choice set.
  Respecified as a conditional choice over ZIP codes given a station opens.
· Designed the hold-out to defeat the leak that makes most such results
  meaningless: whole ZIP codes are held out rather than rows, so the model
  cannot see a ZIP's later quarters while scoring its earlier ones. Measured
  AUC 0.6894 on that split and 0.5551 on a further split by time, against
  0.5000 for the null.
· Fitted the successor - a conditional ZCTA-choice model, 94 decisions, 56
  train and 38 held out, three free parameters - and benchmarked it against
  three single-covariate rules. It draws: raw warehousing establishment count
  alone gets 8 of 38 at top-1 against the fitted model's 7, and 20 of 38 at
  top-10 against 19. Reported that the estimation buys nothing measurable
  rather than reporting the rho-squared of 0.197 on its own.
· Replaced a reported skill score with the raw score pair after Gneiting and
  Raftery (2007, section 2.3): skill scores are generally improper even when
  the underlying rule is proper. Reported split conformal coverage of 88.19%
  against a nominal 90% on the retired hazard model, and the 10.09% of
  prediction sets that came back empty.
```

*On uncertainty: for most of this project's life no standard error of any kind
existed, and "bootstrap CIs" was a fabricated claim that had to be deleted from
this folder twice. An inference layer appeared in `choice_report.json` on
2026-09-14 and was still being edited while this file was being corrected. Do
not put it on a CV until it is committed, tested and stable — and when you do,
note that it is a fourth negative result, not a rescue: the bootstrap interval
on the one parameter that does any work runs from about 0.76 to 4.76 and
therefore includes 1.0, so that parameter is not distinguishable from the
numeraire either. Read the artefact on the day you write the bullet.*

### P2 — reproducibility and data engineering

*These five are the strongest bullets in the file and they were not here before
2026-09-15. Lead with them.*
```
· Recovered 1,904 facility records from a 117-page industry PDF with no
  extractable table layer, by rebuilding table structure from OCR word boxes:
  columns cut at pixel-density valleys in the x-projection, rows anchored on
  the postal code. Three row-anchoring fixes took the largest table from 510
  rows with 41 merged to 535 with 18.
· Caught a silent 8% data loss in my own extraction: the first table filter
  kept images taller than 5,000 px and dropped five of thirteen tables with no
  error. Refiltered on width and pinned an expected-table count so the same
  failure cannot recur quietly.
· Shipped a relocatable tesseract bundle for a compute grid with no tesseract,
  no root and Python 3.6.8, after the first build failed with GLIBC_2.34 not
  found - the node's glibc is older than the build host's, and LD_LIBRARY_PATH
  cannot fix it because the dynamic loader is selected before any environment
  variable is read. The bundle carries ld-linux-x86-64.so.2 and the wrapper
  invokes it with --library-path.
· Production-hardened the pipeline to one entry point with six distinct exit
  codes, a 30-second preflight ahead of a 6-minute extraction, a settings
  stamp that refuses to resume a run under different OCR parameters, strict
  image reuse, and atomic staging via rename(2) - added after an in-place
  rm -rf aborted 62 running workers. Replaced a success banner that had
  reported "SUCCESS - 36 TSV files" on a run that attempted 120 strips and
  wrote none.
· Validated the extraction three independent ways: against OSHA inspection
  records that prove a building was already operating (197 of 208 checkable
  dates pass, 94.7%), against the source's own prose on when the network
  launched (1,413 of 1,420 dated rows plausible, 99.5%), and against a
  ZIP-county-state FIPS crosswalk the OCR knows nothing about (604 of 606
  agree, 99.7%).
· Geocoded the extracted panel to a 72.3% Census batch match rate - 501 of
  693 rows - after four address-parsing fixes traced to specific defects in
  the OCR reading order, heading handling, wrapped ZIP+4 tails and
  multi-facility cells: 402 cells reordered, 73 streets repaired, 91 streets
  re-parsed. Verified zero of the matched rows landed in the wrong state,
  against a deliberately corrupted negative control.
```

The pipeline bullets, which were the whole of P2 before 2026-09-15:

```
· Built a source-agnostic ELT pipeline over 13 analytical public datasets
  (Census, TIGER, Zillow, BLS, EIA, EPA) into a DuckDB star schema; cold build
  in one command, fully offline on a warm cache.
· Enforced data contracts (row counts, null rates, referential integrity) in CI;
  a contract breach fails the build.
· Replaced a rate-limited API dependency (3 days to acquire) with a bulk public
  source (10 minutes), removing a documented coverage bias in the process.
· Made every generated FIGURE read its numbers from the pipeline's own JSON
  artefacts rather than being typed, after an audit found a proposal figure
  printing a target as though it were a measurement. The prose in the written
  deliverables is still hand-typed and still goes stale - which is how three
  superseded portfolio figures survived in this very file until 2026-09-14.
  Quote the bullet at that scope; the stronger version is not true.
· Built the analytical panel: 14 registered public sources, 13 of them
  analytical, reconciled across 8 grains into 1,081,312 rows x 50 columns,
  about 14 MB, with 660 tests passing and 6 agent gates - 4 on data integrity
  and 2 on inferential integrity - guarding writes.
```

*Three caveats to carry with the P2 set.* **First, the geocoding bullet no
longer claims an improvement, and it should not.** 72.3% = 501 of 693 is real
and current, and the canonical `geocoded_expanded.csv` and the rebuilt copy in
`data/interim/` are byte-identical and both read it. But the "before" figure,
65.0%, is 455 of **700** — a different, superseded panel — so 65.0% → 72.3% is
not a like-for-like delta and no file on disk reproduces the 65.0% any more.
Quote the level, not the lift. **Second, neither geocoded file is committed**
(`git ls-files` does not list them), so an interviewer who clones the repo
cannot open either one; that is the thing to fix, not the number.

**Third, 660 tests passing is true and 75 of 138 source modules are unreachable
from any of them** — including every module that writes a headline artefact.
Quote the test count only if you are ready to volunteer the coverage gap in the
same breath. Note also that the count *fell* from 798: on 2026-09-15, 11 test
files retired to `experiments/retired-tests/` alongside the code they covered,
taking 138 tests with them. The suite shrank because code was archived, not
because tests were deleted, and that is the honest way to say it if anyone has
seen the older figure.

### P3 — decision delivery
```
· Built a decision-support dashboard over the cost model: 2,333 ZIP codes,
  median $1.08 per parcel (p10 $0.98, p90 $1.42), five scenarios, every chart
  generated by the same code that produces the printed figures so the two
  cannot disagree.
· Ran a portfolio optimiser over a $2bn budget: it commits $1.128bn across 282
  activations and declines about 44% of the budget because the remaining
  activations lose money; reports the break-even contribution margin (1.343)
  rather than inventing an unobservable one, and reports its own optimality
  gap (10.73%) against a computed upper bound instead of claiming optimality.
· Ran a 500-draw parameter sweep over the optimiser to settle whether a
  headline that had drifted from 330 activations to 282 was a parameter
  effect. It was not: 282 sits at the 67th percentile of the band and 330 at
  the 97th, so the mover was depot placement, which the sweep does not treat
  as a parameter. Reported the sweep as a sensitivity range and not as a
  confidence interval, and flagged that one input was left unsampled so every
  band is a floor.
· Presented a negative result as the headline finding of a capstone rather
  than burying it, with the figure drawn from the metrics file and stamped
  with its run id.
```

**Note what is absent from all three: the words "leveraged," "cutting-edge,"
"state-of-the-art," and "AI-powered."** Numbers do that work.

### Not yet true — do not put these on a CV until they are

These were in an earlier draft of this file as finished bullets. Each is a
real plan; none of them is built, and an interviewer can check every one in a
minute.

```
  Heckman two-step selection correction      no such model exists in src/
  the tax-abatement / selection-propensity   the same claim as the Heckman row
    counterfactual, "would it have been      above in different words. No such
    built here anyway?"                      model. It re-entered this file
                                             after being deleted once and was
                                             deleted again on 2026-09-14
  cannibalisation decay, "-12% within 8 km"  never estimated; the figure that
                                             showed it is four literal arrays
  Top-K rank stability over 10,000 draws     the sweep RAN on 2026-09-14, but
                                             at 500 draws, not 10,000, and it
                                             reports bands on n / capital /
                                             margin / gap, not rank stability.
                                             Quote 500 draws or nothing
  "bootstrap CIs", "confidence interval",    NOT a CV bullet yet. This claim
    or any +/- on any estimate               was pure fabrication when it was
                                             last written here: nothing
                                             computed a standard error, and
                                             MODEL_SPEC.md 6.3 had prescribed a
                                             sandwich covariance and a
                                             bootstrap that were never run. An
                                             inference block DID land in
                                             choice_report.json on 2026-09-14,
                                             mid-correction, and it is not yet
                                             committed to git. Wait until it
                                             settles, then quote it as a
                                             NEGATIVE: the interval on the one
                                             working parameter includes 1.0.
                                             Separately, the 500-draw sweep is
                                             a parameter sensitivity range and
                                             its artefact says in terms that it
                                             is NOT a confidence interval -
                                             never conflate the two
  cross-operator test ("does it predict      never run
    Walmart?")
  precision@100 and PR-AUC                   never computed. Both are listed in
                                             ADR-0001 as the evaluation plan
  a label-noise simulation bounding the      never built. Also ADR-0001
    effect of date error on AUC
  a gradient-boosted ranker benchmark        never built. The only benchmarks
                                             that exist are the three
                                             single-covariate rules and the
                                             uniform null
  an 800,000-pair precomputed drive-time     no OD parquet, no OSRM artefact,
    matrix, "peak disk 60 GB -> 8 GB"        no OSRM run of any kind; the cost
                                             model uses great-circle distance
                                             x 1.30. ADR-0002 is an ACCEPTED
                                             ADR for this decision and it was
                                             never implemented
  "shipped a public application", "live      the dashboard runs locally; there
    URL", "sub-5-second load"                is no Dockerfile, Procfile or
                                             fly.toml in the repository, and
                                             load was never timed
  "published an open dataset", "here is      no dataset, no data card, no
    the dataset, take it"                    release. It is a good plan and it
                                             is two days of work; it is not an
                                             accomplishment until it exists
  conformal coverage "verified 90%"          the hazard model measured 88.19%
                                             and a tenth of its prediction sets
                                             are empty. The choice model's
                                             conformal is worse, not better:
                                             alpha 0.10 reaches coverage 1.000
                                             by naming 71% of the metro, which
                                             is close to vacuous. Quote both
                                             halves or neither
  "a median of 58 ZIP codes per station"     RESOLVED, and the number is 39,
                                             not 58. hazard_revival.json
                                             (provenance.catchment_load) gives
                                             a MEDIAN OF 39 ZCTAs switched on
                                             per opening at the 15-mile
                                             catchment - mean 52.4, p90 105,
                                             max 317. 58 belongs to the retired
                                             pilot specification; say 58 only
                                             in a sentence that names the pilot,
                                             otherwise say 39. Do not confuse
                                             39 with the 13 in the same block,
                                             which is the median NEWLY switched
                                             on. The claim it supports - that
                                             one station enables many ZCTAs at
                                             once - now has its number back
  "my first model hit 4% error"              UNVERIFIED. No 4% figure appears
                                             in any artefact. The circularity
                                             story is real; the number is not
  "653 seconds to 30" as an optimisation     UNVERIFIED. Not in any artefact.
    result                                   See SCALE_AND_IMPACT.md 4
  "334 depots across 11 CBSAs"               334 IS RIGHT; "11 CBSAs" is not.
                                             334 = the sum over the TEN priced
                                             metros of ceil(metro daily
                                             parcels / 40,000), recomputed from
                                             cost_to_serve_2023q4_baseline
                                             .parquet, and it is what the
                                             solver opens. 329 is a different
                                             correct number - one national
                                             division, 13,152,992 / 40,000 =
                                             328.8 - and it is what
                                             cost/params.py:220 means. Say
                                             "334 depots across the ten priced
                                             metros, or 329 on a single
                                             national division"; never quote
                                             either without saying which
```

**Added 2026-09-15.** Six more, found while writing `LINKEDIN.md` and
`INTERVIEW_STORIES.md`. These are not old claims going stale; four of them are
*new* work being described more strongly than the work supports, which is the
same failure mode arriving from the other direction.

```
  the dispersion rule as "21 of 21          there are 21 TERMS IN TOTAL, so
    each way" - the phrasing in             "21 of 21 each way" reads as 42
    PREREG_METRO_MODEL.md lines 40-44       observations and doubles the
    and MODELS_EXPLAINED.md section 7       apparent evidence. CORRECTED AGAIN
                                            2026-09-16: the replacement this
                                            folder shipped, "7 of 7 and 14 of
                                            14", was ALSO WRONG. Re-derived
                                            from gravity_network.json
                                            (arms.*.verdicts.*.state, all 21
                                            terms), the counts are 7 of 7
                                            below cv 0.6 at the boundary and
                                            9 OF 14 above cv 1.3 interior.
                                            The rule is asymmetric: low
                                            dispersion is SUFFICIENT FOR
                                            FAILURE, high dispersion is
                                            NECESSARY BUT NOT SUFFICIENT. The
                                            5 high-cv failures are all
                                            sortation-side, 4 of them carrying
                                            square footage as the mass.
                                            Counting strictly - interior in
                                            every arm it appears in - gives 8
                                            rather than 9, because
                                            fulfilment_proximity straddles.
                                            Descriptive, n = 21 non-
                                            independent terms, one run, one
                                            vintage
  the dispersion rule as CAUSAL, "shown     the knob experiment is real and is
    causal with a knob"                     the strongest part of the claim -
                                            alpha 1/2/3 moves the cv 28x on
                                            the same facilities and the
                                            coefficient walks with it. But
                                            NOTES_GRAVITY_NETWORK.md section 5,
                                            the source, says in terms it "is
                                            not a causal demonstration". Say
                                            "a correlation with a mechanism
                                            and a manipulation", not "causal"
  geocoding "65% -> 72%" as a repo fact     CORRECTED AGAIN 2026-09-16. The
                                            after run is 501 of 693 = 72.3%.
                                            The claim on this line - that the
                                            committed geocoded_expanded.csv
                                            still shows 455 of 700 = 65.0% -
                                            is WRONG in both halves: the
                                            canonical file and the rebuilt
                                            copy in data/interim/ are byte-
                                            identical and both read 72.3%, and
                                            NEITHER IS COMMITTED, so there is
                                            no committed version at all. 65.0%
                                            = 455 of 700 was measured on the
                                            superseded 700-row panel and no
                                            file on disk reproduces it. Quote
                                            "72.3%, 501 of 693"; do not quote
                                            the lift, because the two figures
                                            have different denominators
  the OCR merge quality as a percentage     GEOCODING.md and
    ("97% clean, up from 92%")               MWPVL_OCR_PIPELINE.md section 13.1
                                            state that 517/535 is a working
                                            figure from the fix session and is
                                            NOT reproducible from an artefact.
                                            Quote the 41 merged -> 18 merged
                                            counts, which are
  the cost sensitivity table                WITHDRAWN 2026-09-16. This entry
    ("-17.0%, +0.6%, +1.0%, +4.4%")         was the error, not the table.
                                            cost_report.json was regenerated
                                            (run 20260916-024154-0aa8) and
                                            carries all five scenarios again;
                                            all five parquets share one mtime,
                                            so they are not a day apart.
                                            Recomputed from the report AND
                                            independently from the parquets,
                                            which agree, the figures are
                                            -17.1% (dense routing), +0.5%
                                            (high fuel), +0.9% (pessimistic
                                            tour), +4.4% (congested) against a
                                            $1.0830 baseline median. The
                                            "-16.65% / +0.97% / +1.38% /
                                            +4.84%" this line asserted matches
                                            nothing on disk
  "predicted where Amazon builds next"      the model does not do this in any
    in any form, including the week-1        specification. It was tested and
    LinkedIn hook in the old section 4       it failed. The repo shows this in
                                            one grep and the gap between the
                                            claim and the artefact is the
                                            single worst thing to be carrying
```

---

## 4. LinkedIn: build in public, don't announce at the end

**The drafts now live in [`LINKEDIN.md`](LINKEDIN.md).** Four complete,
postable posts — the extraction, the pre-registration that failed, the
dispersion rule, and a short "what I'd do differently" — plus a headline and an
About paragraph. Each carries a checking note naming the artefact behind every
figure, to be stripped before posting. This section keeps the strategy; the
copy is over there.

**The mistake:** one post in November saying "excited to share my capstone!"
That gets 40 likes from classmates and zero recruiters.

**What works:** a **series**, posted *during* the build, each post carrying one
finding. Consistency compounds — recruiters see someone who ships weekly.

### The series — revised 2026-09-15

The eight-post table that used to sit here was written when the plan was a
model that worked. Three of its eight posts cannot be written:

```
  week 1  "Can you predict where Amazon builds next        DEAD. It promised a
          using only public data? I'm going to find        scoreable outcome
          out in public."                                  and the outcome was
                                                           no. Posting the
                                                           promise now is
                                                           advertising a
                                                           result you do not
                                                           have. The
                                                           pre-registration
                                                           post in LINKEDIN.md
                                                           is the honest
                                                           version of the same
                                                           idea, told after
                                                           rather than before
  week 4  "My model lost to a constant. Here is the        MERGED into the
          chart, and here is why." Post fig08              pre-registration
                                                           post. fig08 is
                                                           genuine - it is one
                                                           of only two figures
                                                           reading a measured
                                                           artefact - but one
                                                           failure post is
                                                           enough; two reads
                                                           as a theme
  week 5  "I gave an LLM write access to a causal          HOLD. The gates are
          model. Here's what broke."                       real but the agent
                                                           is the weakest asset
                                                           in the project and
                                                           this post makes it
                                                           the headline
```

What replaces them: **post the extraction first.** It is the only asset here
that is unambiguously an achievement, it is the most broadly interesting to
people outside the domain, and it carries no risk of being read as a
humblebrag. Then the pre-registration, then the dispersion rule, then the
short retrospective. Keep the surviving originals — the circularity story, the
unit-of-analysis count, the satellite-dating failure, the power argument — as
posts five through eight if you want eight weeks of cadence.

### Rules for each post

- **One chart, always.** Use the figure toolkit — consistent visuals across eight
  posts build recognition.
- **Lead with the finding, not the process.** "My model lost to a constant"
  beats "This week I worked on survival analysis."
- **Never post a number you have not read off an artefact that morning.** Every
  figure in the series should come from `outputs/metrics/`; if a post needs a
  number that is not there, the post is early.
- **150–250 words.** Longer gets skimmed.
- **Link in the first comment, not the body** (LinkedIn suppresses outbound links
  in-post).
- **Name the limitation in the post.** "This is Amazon-consistent desirability,
  not objective demand" — the caveat *is* the credibility.
- **Tag nobody in the first hour.** Let it breathe.
- **All three of you post from your own angle**, and comment on each other's.
  Three perspectives on one project looks like a team; three identical posts look
  like a group chat.

### Medium / long-form
One piece, at the end, ~1,500 words: **the reproducibility write-up.** Title it
for search — *"Predicting warehouse siting from public data: what worked, what
didn't, and the dataset"* — and include the failures. This is what people find in
six months when they search the topic, and it's what a hiring manager reads
before an onsite.

---

## 5. The interview talk track

Interviewers probe for depth. Have these four ready. **Six STAR-format stories
with their evidence are in [`INTERVIEW_STORIES.md`](INTERVIEW_STORIES.md)** —
this section is the four set-piece answers; that file is what you reach for
when they ask for a second example, or for a time something went wrong.

**"Walk me through the project."** *(90 seconds, no jargon)*

*Revised 2026-09-15 to open on the data recovery.* The previous version opened
on the model, which meant the first forty seconds were spent building up a
result that then had to be taken away. Opening on something that worked buys
the credibility to spend the second half on something that did not.

> "The dataset this needed does not exist in machine-readable form. The best
> public inventory of parcel-delivery facilities is a 117-page PDF whose tables
> are pictures — you run a text extractor over it and get about 120 lines of
> prose. So the first thing I built was an extraction: OCR the table images,
> then rebuild the table structure from the word boxes, because OCR gives you
> words and coordinates, not rows and columns. Columns come from the gaps in
> the horizontal density of the words; rows come from anchoring on the postal
> code, which is the only thing in an address column shaped like one. That
> produced 1,904 facility records, and I checked them three independent ways —
> the sharpest one is against OSHA inspection records, because a building
> cannot have opened after an inspector was standing inside it. 197 of the 208
> records I could check pass that.
>
> Then the modelling, which is the part that did not work, and I think the way
> it did not work is the more interesting half."

Then continue with the original answer, which is unchanged and still correct:

> "Private companies decide where to build delivery infrastructure, and those
> decisions move property values, air quality and municipal budgets — but the
> models behind them are proprietary. We built an open one from public data
> and then did the thing most student projects skip: we scored it against a
> null model, on data it had never seen, with whole ZIP codes held out rather
> than rows.
>
> It lost. Brier score 0.019522 against 0.019614 for a model that ignores
> every covariate and just predicts the base rate, over the same 8,044 rows.
> Calibration was worse than the constant's outright. So I went and found out
> why, and the answer was not sample size — it was the unit of analysis. One
> delivery station switches on a whole catchment of ZIP codes at once, so what
> the panel recorded as 812 independent events was 94 real decisions plus a
> catchment circle. The model spent its capacity learning to draw circles. The
> assumption that breaks is independence across observations — Train's
> discrete-choice text, section 3.7.1 — and the standard name for it is
> clustering, or pseudo-replication. So we respecified it as a conditional
> choice: which ZIP code, given a station opens in this metro this period.
>
> Then we fitted that, and it did not rescue the result either. On 38 held-out
> decisions the fitted model gets 7 top-1; the raw count of warehousing
> establishments, with nothing estimated at all, gets 8. So the honest summary
> is that the covariates carry the signal and the estimation adds nothing I can
> measure — and I would rather tell you that than show you a rho-squared."

That is the whole interview, and it is deliberately not a success story.
Rehearse it until the three numbers come out without hesitation, because the
hesitation is what reads as embarrassment and the content does not warrant
any. If the interviewer's follow-up is *"so it didn't work?"*, the answer is:
*"neither specification did, and I can tell you exactly why each one failed,
which is more than I could have told you if either had worked."*

Do **not** end this answer on the city-council abatement question. An earlier
version did — *"would this have been built here anyway, without our tax
abatement?"* — and it implies a selection-propensity counterfactual that does
not exist in `src/`. It is the Heckman claim this file already deleted once,
wearing different clothes.

**"What was the hardest problem?"** → *the circularity bug.*
> "Our first target variable was constructed from the same covariates we used as
> predictors. The model scored beautifully and meant nothing. We caught it,
> changed the estimand to something observable — did the operator enable service
> here, and when — and that turned a meaningless fit metric into a real
> forecast we could score."

It demonstrates you can find a subtle validity error in your own work, which is
exactly what senior people do and juniors don't.

*Added 2026-09-15: there is now a better one, and it has numbers.* The
infeasible-optimum bug in the conditional-logit estimator is the stronger
answer to "hardest problem", because it is a defect that makes the objective
*better* and therefore trips nothing, and because it was found from a pattern
rather than from an error message — in all five affected columns, the direction
that "found" an effect was the direction with the cheaper feasibility ceiling.
Story 3 in `INTERVIEW_STORIES.md` has the full version with its measurements
and with the part that is still unfixed.

**"Tell me about a time you made a mistake."** *(they will ask; do not give
them a disguised success)*

Three are written up in `INTERVIEW_STORIES.md`, and the right one depends on
who is asking. For an engineering interviewer: the shared six-core machine,
load average 44, forty-five minutes of finished work discarded because the
experiment persisted only at the end — after the brief had explicitly told you
to cut repeats rather than parallelise. For a research or analytics
interviewer: the figures that carried a typed 95% confidence interval and a
significance annotation for a regression that had never been run, found in an
audit of your own charts. Both end in a mechanical fix rather than a
resolution to be more careful, and that is the part that does the work.

**"What would you do differently?"** *(never say "nothing")*
> "Check the unit of analysis before writing a line of code. That check is one
> line of a textbook, it costs nothing, and it would have saved the entire
> hazard specification. I found it after the model failed instead of before it
> was written, which is the largest single error in the project."

**"Did you use AI to build this?"** *(increasingly asked; answer confidently)*
> "Yes, for code and for literature triage — and it's also a component: an agent
> writes to the analytical model behind validation gates. The interesting part
> was discovering that standard gates protect data integrity but not
> *inferential* integrity, so we added two gates that check whether a write
> invalidates a causal assumption."

Never be defensive here. Using AI well is a skill; the differentiator is that
you know where it breaks.

---

## 6. Timing — start now, not in November

```
  WEEK 1-8   post the series while building        <- recruiters see momentum
  WEEK 6     repo public, README polished          <- before you apply anywhere
  WEEK 7     app live, dataset published
  WEEK 8     Medium piece + résumé updated
  WEEK 9+    apply, with a link that already has traction
```

Applying with a link that already has engagement is materially different from
applying with a link posted yesterday. **Recruiting cycles do not wait for your
defence date.**

---

## 7. What to have ready before any application

- [ ] Repo public, README with a screenshot and a 60-second quickstart
- [ ] App deployed, and the URL in the README above the fold. Until then
      the README says "runs locally with one command", which is also true
- [ ] Dataset published with a data card
- [ ] `make all` verified by someone outside the team on a clean machine
- [ ] Model card: what it does, what it doesn't, known biases
- [ ] Three distinct résumé variants (§3), every number in them checked
      against `outputs/metrics/` on the day you send them
- [ ] LinkedIn featured section linking to app / repo / write-up
- [ ] Non-affiliation disclaimer visible in the app footer
- [ ] The source PDF behind 589 of the 693 facility rows copied into
      `data/raw/mwpvl/` with its sha256 in the manifest. Today it lives
      outside the repository and the extraction is unreproducible without it
      (`../AUDIT_2026_09_14.md` §1.1). Do not link the repo to a recruiter as
      a reproducibility claim until this is fixed
- [ ] `geocoded_expanded.csv` actually committed. It already reads 72.3% (501
      of 693) and so does the `data/interim/` copy — they are byte-identical —
      but `git ls-files` lists neither, so the 72.3% cannot be opened by anyone
      who clones the repo. This is a `git add`, not a re-run
- [ ] Every checking note stripped out of the posts copied from `LINKEDIN.md`

---

## 8. The honest caveat

None of this substitutes for the work being real. **A polished LinkedIn series
about a project that doesn't run is worse than silence** — it's checkable, and
someone will check.

This file broke its own rule, twice, and the full itemisation now lives in
[`README.md`](README.md) rather than being repeated here — it is the same list
in both places and one of them was going to go stale. The short version: the
first pass (2026-09-13) removed an unverified "AUC 0.84 and precision@100 of
0.61" from both a CV bullet and the opening line of the spoken answer, along
with a Heckman correction, conformal coverage "verified" at 90%, a 10,000-draw
stability pass and a cannibalisation decay, none of which existed. The second
pass (2026-09-14) found the first one incomplete and removed eleven more,
including a wrong Train citation that was *inside* the ninety-second answer —
the one thing in this folder that gets said out loud to somebody who may have
read Train. The third (2026-09-15) is in §3's table and in the fourth point
below. The fourth (2026-09-16) re-checked the third against the artefacts and
found three of its corrections wrong; it is the fifth point.

Five things follow, and they are the only five worth taking from this
section.

**First, the failure mode is not lying, it is lag.** Nobody typed 0.84 in bad
faith; it was a pre-registered target, written before the model existed, that
sat in a document while the world moved. The defence against it is mechanical,
not moral: derive the number rather than type it. The generated **figures**
read `outputs/metrics/*.json` at build time, so a re-fit that moves a number
moves it in every chart. **The prose does not, and that is the hole.** Every
stale figure the second pass found was hand-typed sentence text sitting beside
a chart that was already correct. Until the prose is derived too, the only
control is the one in §7: re-check every number against `outputs/metrics/` on
the day you send the CV.

**Second, the honest version is the better pitch anyway.** You do not have to
choose between integrity and a story here. "I built the dataset out of a PDF
nobody could parse, validated it three ways, scored the model against a null,
lost, diagnosed why, respecified it twice, pre-registered the third attempt and
lost that too" is a stronger ninety seconds than any unverified 0.84, because
the 0.84 is exactly the kind of claim a hiring manager has learned to discount.

**Third, a second correction of the same file is itself the warning.** One
stale number is lag. Two rounds of it in one document means the document is
structurally unable to keep itself true, and the only safe posture is to treat
every sentence here as stale until checked against an artefact. That is not a
figure of speech — it is the operating instruction for this file.

**Fourth, 2026-09-15: the third pass found the same failure in new work.** The
first two passes were about old claims going stale. This one found four
overstatements in work written that same week — "21 of 21 each way" for the
dispersion rule; the same rule described as "shown causal" when its own source
note says in terms that it is not a causal demonstration; a geocoding
improvement quoted as a repo fact; and a cost sensitivity table said to be
computed against a superseded baseline. None of these is lag. They are a result
being described slightly more strongly than the artefact supports, at the
moment of writing, which is the harder failure to defend against because there
is no stale document to blame. The control is the same one: read the JSON, then
write the sentence.

**Fifth, 2026-09-16: three of those four corrections were themselves wrong, and
this is the worst finding in the file.** The dispersion fix said "7 of 7 and 14
of 14"; the artefact says 7 of 7 and **9 of 14**, and the rule is asymmetric
rather than symmetric. The geocoding fix said the committed file still shows
65.0%; there is no committed file, and the one on disk reads 72.3%. The cost
fix replaced a table that was very nearly right with percentages that match
nothing (`-16.65%` etc. against a true `-17.1%`). All three were produced by
reading another *document* rather than the artefact — which is the exact
failure mode the previous four points describe, arriving one level up. **A
correction is a claim. Source it the same way you would source the claim it
replaces, and never from prose.**

The order matters: make the number real, make the repo run, publish the
dataset. *Then* tell the story. Everything in this document assumes the thing
underneath it is true.

That, ultimately, is the same argument as the rest of the review: the
credibility comes from what survives checking.
