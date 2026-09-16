# ADR 0004 — Replace the hazard model with a conditional ZIP-choice model

- **Status:** proposed
- **Date:** 2026-09-13
- **Updated:** 2026-09-14 — the successor has been fitted. See
  [the update at the end](#update-2026-09-14--the-successor-was-fitted-and-a-raw-covariate-matched-it).
  The status is unchanged and deliberately so. (That heading, and this link,
  said "a raw covariate beat it" until later the same day; the correction is
  inside the update.)
- **Deciders:** P1 / P2 / P3

This ADR exists because [`../STATUS.md`](../STATUS.md) §7 lists decision **D1 —
confirm the conditional-choice reframe in writing** as owed by
the owner and not yet given. It is written as the place that confirmation
belongs. It is **proposed**, not accepted, and it should stay proposed until
the owner signs it off; an assistant cannot take a decision the status page
records as the owner's. Everything in the Context and Options sections below is settled
and checkable today.

**The model being built is not the same event as the decision being ratified,
and the gap between them is the awkward part of this document.** On
2026-09-14 the successor was fitted and reported
(`outputs/metrics/choice_report.json`). The decision recorded here was not
taken first. So this ADR now documents a change that has already happened in
code while remaining, correctly, unratified in writing. Whoever signs it off
is ratifying something they can inspect rather than something they are
authorising, and the 2026-09-14 update below exists so that the signature is
given in full knowledge of how the fit turned out — which is badly.

Note that **two distinct decisions in this repository are labelled D1.**
[`0001-observable-estimand.md`](0001-observable-estimand.md) settled *what* is
observed — service enablement rather than constructed order volume — and was
accepted on 2026-09-08. This ADR is about *whose decision* the observation
records. The observable estimand survives unchanged; the unit it is measured
on does not.

## Context

### The specification that was built

`models/hazard.py` fits a **complementary log-log discrete-time hazard** on a
ZCTA-quarter risk set. The unit is the ZCTA-quarter, the outcome is "this ZIP
was first switched on in this quarter", and units leave the risk set at the
event (`models/risk_set.py`). Time enters through a spline basis
(`models/timebasis.py`) and splits are unit-wise (`models/splits.py`).

**Why it was chosen, honestly.** The estimand set by ADR-0001 is *whether and
when* a ZIP was first switched on. That is a time-to-event question with
right-censoring — most ZIPs have not been enabled **yet** — and a plain
classifier must either discard the timing or treat "not enabled by 2025" as
"never enabled", both of which throw away the quantity of interest. A
discrete-time hazard handles censoring natively, fits with standard software,
and the panel was already at quarterly grain. The reasoning is recorded at
[`../DECISION_LOG.md`](../DECISION_LOG.md) §3.1 and it was sound *given the
unit*. The unit was never examined.

One provenance note, recorded because it bears on who owes the correction:
the hazard specification **does not appear in the user's original v3
proposal**. It was introduced by the assistant in v4. That remains TESTIMONY
rather than something a reader can verify (`../DECISION_LOG.md` §2.1) — but
for a narrower reason than this paragraph used to give. It used to say "there
is no git history in this repository". **That is no longer true: the
repository is under version control.** The history begins on 2026-09-13,
after the v4 decision was taken, so it cannot corroborate a claim about who
wrote what in v4; from here on it can.

### The measured failure

Fitted on the real panel. All figures from `experiments/hazard-model/artefacts/hazard_report.json`
(`run_id 20260914-002509-2374`); regenerate with `make model`. The artefact was
regenerated on 2026-09-14 and no value below changed; an earlier version of
this ADR cited `run_id 20260913-133904-a60e`, which is superseded.

```
  held-out test, 8,044 rows / 161 events     model       null (a constant)
  --------------------------------------------------------------------------
  Brier score                               0.019522     0.019614
  calibration error (ECE)                    0.00863      0.00005
  AUC                                         0.6894       0.5000

  temporal hold-out, 11,871 rows / 245 events
  Brier score                               0.020635     0.020213
  calibration error (ECE)                    0.01196      0.00073
  AUC                                         0.5551       0.5000
```

Read the ECE row twice. A model that ignores every covariate and predicts the
same number for every ZIP in every quarter is **better calibrated than ours,
by a factor of 170**. Out of time the constant beats it outright on the proper
score as well. One of three covariates was distinguishable from zero —
`households`, hazard ratio 1.00005 — which is the model having learned
*"Amazon builds where the people are"*: true, and not worth a model.

**Two reporting rules apply to that table and are part of this decision.**

1. **Report the raw Brier pair, not the Brier skill.** A skill score is
   `1 - S_model/S_null`, and Gneiting & Raftery (2007) §2.3 p.362 states that
   skill scores "are generally improper, even if the underlying scoring rule S
   is proper". The Brier score itself is strictly proper (§3.1 p.363). The
   `brier_skill: 0.00471` still emitted by the artefact is a normalisation for
   readability, not the estimand. See
   [`../research/NOTES_gneiting_raftery_2007.md`](../research/NOTES_gneiting_raftery_2007.md).
2. **The geographic hold-out is not a transfer result.**
   `experiments/hazard-model/artefacts/hazard_report.json:819` records that Phoenix and Boise hold
   **two dated delivery stations between them**, "so this is a smoke test for
   gross failure and not a test of geographic transfer". Its `-0.06184` is
   therefore absent from the table above and must not be quoted as evidence
   about generalisation. Earlier versions of several documents quoted it bare,
   which overstated the evidence against our own model.

### The diagnosis: unit of analysis, not sample size

Amazon does not switch on ZIP codes. It signs a lease on **one building**, and
coverage follows mechanically from a fifteen-mile van catchment
(`warehouse/facilities.py`, `CATCHMENT_MILES`). Measured on the delivered
panel, one station covers a **median of 58 ZCTAs**, a mean of 88 and a maximum
of 307.

So the risk set's **812 ZCTA-quarter "events" are not 812 decisions.** The
artefact's own `power` block bounds the real count:

```
   events per parameter, NOMINAL (counts ZCTAs)               97.4
   events per parameter, effective (metro-quarter episodes)    5.6
   events per parameter, optimistic (usable facilities)        7.6
   floor                                                      10.0
```

A nominal 97.4 per parameter looks like a well-powered study. The report's own
`power.note` says: *"The nominal ratio counts ZCTAs and is not evidence of
power."*

**Train (2009) §3.7.1, printed p. 61, gives the test in one line**, where the
likelihood is built:

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> `L(beta) = prod_n prod_i (P_ni)^{y_ni}`."

*Independence across observations.* That is what a fifteen-mile disk destroys.
"ZIP A switched on" and "ZIP B switched on" are one outcome observed dozens of
times, not two outcomes. The model spent its capacity learning to draw circles.
The standard name for the failure is clustering, or pseudo-replication.

> **A citation corrected, because getting it wrong once is the reason this
> paragraph is long.** Earlier versions of this ADR, and of several other
> project documents, attributed the failure to **Train §2.2**'s requirement
> that a choice set be mutually exclusive. Having read §2.2 in full, that
> attribution is wrong. §2.2 governs a choice set facing a decision maker, and
> a hazard on ZCTA-quarters has no decision maker choosing among those rows, so
> exclusivity is not a property they can have or lack. Worse for the rhetoric,
> Train calls the criterion easy: "The first and second criteria are not
> restrictive. Appropriate definition of alternatives can nearly always assure
> that the alternatives are mutually exclusive" (p. 12), and he supplies a
> two-line repair recipe. Citing §2.2 therefore named a rule that is *not*
> binding, in support of a diagnosis that is correct. The diagnosis stands;
> only the citation and the word were wrong, and the correct citation makes the
> argument stronger. §2.2 remains the right authority for building the
> **successor's** choice set, and the Decision section uses it that way.

The analogy that makes it obvious: if you want to know which houses flood, you
model **where the river breaches** and then compute which houses sit below the
water line. You do not model five hundred houses as five hundred independent
events. That would mostly teach you that neighbouring houses flood together.

**This check costs nothing and requires no data.** It should have been applied
before a line of code was written. It was not, and
[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.2 calls it
the largest single error in the project. Nothing in the test suite could have
caught it: every ZCTA-quarter row is individually valid.

### What is *not* the diagnosis, and why this paragraph is here

Five documents — `../STATUS.md`, the separate backlog since merged into
`../STATUS.md` §5, `../ROADMAP.md`,
`../ARCHITECTURE.md` and `../REPRODUCE.md` — reported the negative result
correctly and then attributed it to **sample size**: some variant of "39
usable events across 43 buildings cannot identify a siting model". That is the
explanation [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.2 opens by
rejecting. It is recorded here rather
than quietly overwritten, because several independent documents agreeing on a
wrong cause reads as corroboration, which is worse than one document being
blank. All five now carry the correction and the sentence they used to carry.

A panel ten times larger at ZCTA-quarter grain would have failed in the same
way, because the alternatives still would not have been mutually exclusive.

**And sample size is not thereby irrelevant.** As written, this ADR expected
the successor to have roughly **43 decisions** on the pilot frame — 38 that
`diagnostics.usable_facilities()` counts as usable, 39 by the honest definition
(`../STATUS.md` defect D2) — against 5 parameters, i.e. **7.6 per parameter
against a conventional floor of 10**, with the reframe not moving it. **What
was actually fitted has 94 decisions against 3 parameters, on the national
frame, which clears the floor comfortably at 18.7 per parameter in estimation.**
The paragraph's arithmetic is therefore superseded, but its conclusion survives
intact and is now measured rather than predicted: the reframe made the
specification **valid**, not **powerful**, and clearing a power floor turned out
to buy nothing. See the 2026-09-14 update.

The date problem is a third, separate thing and it survives the reframe: most
of the 43 dates are "operating by" **upper bounds** from OSHA inspection
records, with externally verified lags of 4, 13, 57, 69 and 345 months. That
is a censoring problem, and it is why interval censoring stays on the backlog
rather than leaving it.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **A. Keep the cloglog hazard, add interval censoring** | Cheapest; `risk_set.py` already exists; interval censoring is the honest treatment of an upper-bound date | Does not touch the defect. Makes the *reported* result correct on a specification whose choice set is invalid. 3-5 days spent perfecting a model the successor replaces |
| **B. Keep the hazard, enlarge the panel** | No new method to learn | Wrong on its own terms. More ZCTA-quarters multiply the geometry, not the decisions. This is the sample-size diagnosis made operational, and it is the wrong diagnosis |
| **C. Holmes / Houde revealed-preference moment inequalities** | Set identification; no distributional assumption about what the firm knew; the estimator two *Econometrica* papers used on exactly this class of problem | Identified by **swapping facility opening dates**, which is the one quantity we measure worst. Contested — see below |
| **D. Molinari §2.3 interval-outcome partial identification** | The closest match to the data we actually have. Needs no model of Amazon's optimisation, no assumption about what Amazon knew, no swap construction. Turns the panel's worst defect into the estimator's input. Shipping software exists (Beresteanu–Molinari–Morris) | Offered, not costed. Nobody has checked the code runs on a panel this shape. Answers a narrower question and returns a set, not a forecast. Ponomareva–Tamer: misspecification makes such sets **spuriously tight**, so a narrow interval from 43 buildings is a reason for suspicion |
| **E. Conditional ZIP-choice model** (Train §2.2/§2.3, §7.7.3) | Fixes the defect directly: the choice set becomes mutually exclusive. Real decisions, standard software, interpretable, and the ZIP-level answer is recovered rather than abandoned | Still under-powered at 7.6 decisions per parameter. Requires `V = ln(beta'a)` with additive attraction variables or the result is an artefact of ZCTA boundaries. Assumes the firm's ex-ante unknowns are our unobservables, which Train himself calls doubtful |

### Option C is contested, and this ADR surfaces the disagreement

Two documents in this repository disagree about the Holmes/Houde route, and a
reader who consults them in the wrong order will get contradictory guidance.

```
  METHODS_RESEARCH.md §8   "Two routes are on the table. NO WINNER is
                           declared here. That decision is the user's and
                           has not been made."  Presents (A) moment
                           inequalities and (B) the closed-form dynamic logit
                           in a trade-off table, plus (C) Molinari as a third
                           route "offered, not chosen".

  DECISION_LOG.md §1.8     "UNRESOLVED — which estimator. OPEN. Two routes,
                           no winner, and the decision has not been made."
                           Agrees with METHODS_RESEARCH.

  ROADMAP.md               Lists moment inequalities under "Cut, with
  "Cut, with reasons"      reasons", with a reason: the identifying
                           variation is the quantity this project cannot
                           observe, and Holmes §8.3 says the estimator is
                           inconsistent under this kind of measurement
                           error.
```

The roadmap closes a question the other two leave open. **This ADR resolves it
in the roadmap's favour, and states the argument so the resolution can be
attacked on its merits.**

The argument: Holmes's §6.1 measurement-error result is what first attracted
us, and it assumes `x` and the instruments are *"directly observed"*, putting
the error on **profits**. §8.3 is explicit that the procedure "yields
inconsistent estimates of the identified set when there is measurement error
in the `x` variables", and §7 states that opening dates "are all assumed to be
measured without error". Under the swap design **our dates define the
deviations, the instrument groups and the discounting window all at once**.
Holmes protects the side we have clean and assumes clean the side we do not.
Our dates are OSHA inspection dates with verified lags of 4, 13, 57, 69 and
345 months; for many pairs we do not know the sign of `t_j - t_k`, so we
cannot say which roll-out was chosen and which is the counterfactual. The
identifying variation *is* the quantity we cannot observe.

Two things this resolution does **not** claim. It does not declare the
estimator bad — it is the estimator of two *Econometrica* papers and it is
respectable (Molinari §3.5). And it does not close **option D**: Molinari
§2.3 is a partial-identification route that does not use the swap design and
therefore does not inherit this objection. `METHODS_RESEARCH.md` §8's "no
winner" is, on this reading, answering a slightly different question — which
*estimator* to adopt in general — while the roadmap's cut list is answering
which route to spend the next fortnight on. Read that way they are compatible, but the
two documents do not say so, and until one of them is amended the
disagreement is real. Whoever accepts this ADR should also amend
`METHODS_RESEARCH.md` §8 and `DECISION_LOG.md` §1.8 to point here, or reject
this paragraph.

> **CHECKED AGAIN 2026-09-14: THE CONTRADICTION IS STILL LIVE, AND IT HAS NOT
> BEEN RESOLVED BY ANYBODY.** All three passages were re-read against the files
> on disk today and none has been amended:
>
> ```
>   METHODS_RESEARCH.md §8      heading "The open methodological question".
>                               "Two routes are on the table. **No winner is
>                               declared here.** That decision is the user's
>                               and has not been made."  Closes with "OPEN."
>
>   DECISION_LOG.md §1.8        heading "UNRESOLVED -- which estimator".
>                               "**OPEN.** Two routes, no winner, and the
>                               decision has not been made."
>
>   ROADMAP.md                  under "Cut, with reasons": "**Moment
>   "Cut, with reasons"         inequalities (Holmes 2011 / Houde, Newberry
>                               & Seim 2023)** -- the identifying variation is
>                               exactly the quantity this project cannot
>                               observe, and Holmes Sec. 8.3 states the
>                               estimator is inconsistent under this kind of
>                               measurement error"
> ```
>
> Two documents say the question is open and one says it is closed against
> moment inequalities. **This ADR proposes a resolution in the roadmap's favour
> and does not impose one**, which is the right posture for a document whose
> own status is `proposed`. The flag is raised here rather than fixed for three
> reasons. It is a research decision and the cut list records it as the owner's.
> An assistant amending two documents to agree with a third would manufacture
> consensus rather than establish it. And a reader who consults the three in
> the wrong order will still be misled until somebody with standing chooses,
> so leaving the contradiction visible is safer than leaving it half-mended.
>
> There is also a reading on which the three are compatible, stated above:
> §8 and §1.8 answer "which estimator in general", the roadmap's cut list
> answers "which
> route for the next fortnight". If that is the intended reading, **say so in
> all three files**, because none of them says it now.
>
> Note that the block quotations at lines above are accurate in substance but
> were paraphrased rather than transcribed; the cut-list quotation is
> verbatim, the other two are not. The verbatim text is in the box here.
>
> **Re-checked 2026-09-15 after the status merge.** The third position was
> carried by `PLAN.md` §6 until that file was retired. It now sits in
> [`../ROADMAP.md`](../ROADMAP.md) under "Cut, with reasons", quoted verbatim
> above, and the same argument is written out at
> [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §15.1. The contradiction
> did not move: it is now *inside* `METHODS_RESEARCH.md`, whose §8 still says
> OPEN while its own §15.1 says rejected. Still nobody with standing has
> chosen.

## Decision

**Retire the ZCTA-quarter discrete-time hazard as the primary specification.
Adopt a conditional ZIP-choice model** (option E): *which ZIP does the station
go in, conditional on a station opening in metro `m` in period `t`.*

```
                     was                    becomes        AS ACTUALLY FITTED
  unit          ZCTA-quarter         siting decision      same
  observations  812 ZCTA "events"    ~43 real choices     94 decisions,
                                     (pilot frame)        NATIONAL frame
  question      when does a ZIP      which ZIP, given     same
                switch on            one opens
  model         cloglog discrete     conditional choice,  same
                -time                V = ln(beta'a)
  time          32 quarters          2-3 structural       ONE period.  No
                                     periods              time parameter was
                                                          fitted at all
  headline      AUC                  raw Brier pair +     as promised, plus
                                     calibration          top-k
  the date      the event time       a conditioning       a conditioning
                                     variable             variable -- but see
                                                          the update: it is
                                                          also the OSHA bound
```

The right-hand column was added on 2026-09-14 and two of its rows differ from
what this ADR decided. The frame is national, not the pilot, which is what
made the fit possible at all. And the two-to-three structural periods were
dropped to one, so the specification's time dimension was not implemented.
Neither departure was recorded when it was made.

Binding specification constraints, each with the section that forces it:

- **`V = ln(beta'a)` with additive attraction variables** (Train §3.4 Ex. 2).
  Not a style choice: with zonal alternatives, any other functional form makes
  the result an artefact of how the Census drew ZCTA boundaries.
- **2-3 structural periods, not 32 quarters** (Train §7.7.3: define as few
  time periods as possible, structurally).
- **Bootstrapped standard errors** (Train §8.6), on the count of **buildings**
  — `METHODS_RESEARCH.md` §2.5 — not of ZCTA-quarters.
- **A gradient-boosted ranker beside it as a benchmark** — since built and
  fitted, [`../STATUS.md`](../STATUS.md) §2.
  Atheoretical, no causal claim. If it out-predicts the structural model that
  is a finding either way. A structural model with nothing to lose to has not
  been tested.
- **Report the raw Brier pair and the calibration error**, never a skill score
  as the headline, and never the geographic smoke test as a transfer result.

**The ZIP-level answer is derived, not abandoned:**

```
  P(your ZIP gets same-day service)
    =  P(a station opens in your metro)         from base rates
    x  P(the chosen site is within 15 miles)    from the choice model
```

**Option D is kept open** as the partial-identification complement, not as a
rival. It is the natural home for the upper-bound dates, and it is the honest
answer if the choice model turns out to be too imprecise to say anything. It
is unfunded and uncosted today.

**Option A is demoted, not deleted.** Interval censoring in `risk_set.py`
remains an open defect ([`../STATUS.md`](../STATUS.md) §6) and returns with the **timing** factor
of the product above, which is still a model of dates that are still upper
bounds. It moved off the critical path because correcting the censoring of a
retired specification does not make that specification right.

## Consequences

**What becomes easier.**

- The choice set satisfies Train §2.2, so a coefficient means something. Every
  observation is a decision somebody actually took.
- The upper-bound date stops being a defect and becomes a **conditioning
  variable**: the choice model asks "which ZIP, given a station opened in this
  window", which tolerates a loose window far better than an event-time model
  does.
- Far fewer nominal observations, all of them real. Nobody can mistake 97.4
  events per parameter for evidence of power again.
- Train §7.7.3's closed form — a forward-looking siting model resembling the
  upper level of a nested logit — is available, which is why option E is cheap
  in software terms.

**What becomes harder.**

- Every headline number in the model layer must be recomputed. `models/`
  currently serves the hazard specification.
- The defence pack still says "discrete-time hazard" as the method
  (`defense/VIVA_QA`), and `academic/defense/helper.txt` — the
  spoken-answer crib sheet — still tells the presenter to assert a target AUC
  of 0.84 (`DECISION_LOG.md` §4.1). That is the highest-value single fix left
  in the tree and it is outside this ADR's scope.
- Three cheap prerequisites become load-bearing: the 43 addresses are
  **ungeocoded** and fall back to ZCTA centroids
  ([`../STATUS.md`](../STATUS.md) §3 blocker 4), which
  a siting model cannot tolerate as gracefully as a coverage model did; the
  national panel's 104 rows describe 101 buildings with three **contradicting
  opening dates**
  ([`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md)
  §12.6); and complete-case deletion on `rent_index`
  drops exactly the sparse ZCTAs the siting question is about
  ([`../STATUS.md`](../STATUS.md) §6).

**What we are committed to.**

- Quoting the **decision** count, not the ZCTA count, beside every metric.
- Publishing the power figure with the result rather than beneath it. 7.6 per
  parameter against a floor of 10 goes in the abstract, not the appendix.
- Keeping the failed hazard fit and its artefacts on the record. It is the
  benchmark the successor must beat, and the negative result is itself a
  finding: *this panel, at this unit of analysis, cannot identify a siting
  policy, and here is exactly how it fails.*

**What is unchanged, and works today on real data:** the cost model (2,333
ZCTAs, median **$1.0830**/parcel, run `20260916-024154-0aa8`), the portfolio
optimiser (282 activations, $1.128bn, run `20260914-002431-7419`), the six agent
gates, the whole L0-L3 pipeline, and the project's central argument. Four of the
project's five components were never affected. Two figures were corrected here
on 2026-09-14: the median was quoted as $1.09 from a superseded run, and "334
solved depots" was quoted although no depot count appears in any artefact — it
survives only as a docstring in `cost/depots.py`, and it has been removed rather
than re-quoted.

## Residual risk

**The successor may also fail, and for a reason we would notice late.** 7.6
decisions per parameter is below the floor. The most likely outcome is wide
bootstrap intervals covering zero on every coefficient. That is a *valid*
answer to the question and an unsatisfying one. **How we would notice:** the
bootstrap intervals are the diagnostic, and they must be computed on buildings
rather than rows or they will lie in the flattering direction — the same
error, at a different level, as counting 812 events.

**The benchmark may win.** If the gradient-boosted ranker out-predicts the
structural model, the structure is not earning its assumptions. We have
committed in advance to reporting that. Predicting it here is what makes the
report credible rather than a rationalisation.

**`V = ln(beta'a)` may be applied carelessly.** The additivity requirement is
on the *attraction variables*, and a log or a ratio slipped into `a` silently
reintroduces the boundary artefact. **How we would notice:** re-estimate at a
different spatial grain — the MAUP check at H3 grain already on the roadmap —
and see whether the coefficients move. If they do, the functional form is
wrong.

**The reframe could be mistaken for a rescue.** It is not. It converts an
invalid specification into a valid, imprecise one. Any write-up that presents
the change as having fixed the result, rather than having fixed the question,
is misreporting it — and that is the specific failure this ADR was written to
prevent, having just watched the opposite error (a correct result with a wrong
cause) propagate through five documents.

**The Holmes/Houde resolution above could be wrong.** It rests on reading
§8.3's inconsistency result as applying to the swap design's use of dates. If
somebody shows the swap design tolerates date error of our magnitude — an
assumption ladder with a breakdown point, "robust to measurement error up to X
months", which is the assumption-ladder item in
[`../ROADMAP.md`](../ROADMAP.md) under "Identification" — option C reopens.
**How we would notice:** that is exactly what the ladder computes, so the
check is already
scheduled. As of 2026-09-15 that item is still unticked, so the
check is scheduled and not done.

## Update 2026-09-14 — the successor was fitted, and a raw covariate matched it

**The status line above still says `proposed`. That is correct and it is not an
oversight.** The decision this ADR records is the user's to ratify; what
follows is what happened when the code was written anyway, reported so that the
ratification is informed rather than nominal. All figures from
`outputs/metrics/choice_report.json`, seed 20260914.

### What was fitted

```
  frame                      national  (not the ten-metro pilot)
  decisions                  94 total, 56 train / 38 held out
  free parameters            3, converged
  log-likelihood             -203.4497   against a uniform -253.3351
  McFadden rho-squared       0.1969      (in sample, on the 56)
  structural periods         one.  The 2-3 periods this ADR specified were
                             not implemented and no time parameter was fitted

  beta, households fixed at 1 as the numeraire
    households                    1.0        numeraire, not estimated
    warehousing_establishments    1.4428
    land_area_sqmi                3.0e-16    AT THE BOUNDARY
    establishments                4.7e-16    AT THE BOUNDARY
```

`warehousing_establishments` — the count of NAICS 493 warehousing and storage
establishments in the ZCTA, from Census County Business Patterns — was added
after the first fit and is not in this ADR's original attraction vector. It is
the only covariate that does anything.

### The three residual risks this ADR pre-registered, scored

**"The benchmark may win." IT DREW.** This ADR committed in advance to
reporting that outcome, and the commitment is now due. (This line said "IT
WON" until the re-split evidence below arrived; a draw is still a failure for
the model, because a model that only draws with a free one-column sort has not
earned its parameters.)

```
  held out, 38 decisions      top-1    top-5    top-10    Brier
  ----------------------------------------------------------------
  the fitted model             7/38    16/38     19/38    0.008724
  warehousing count alone      8/38    16/38     20/38    0.008951
  households alone             1/38     5/38     10/38    0.009271
  uniform within the metro     1/38     3/38      7/38    0.009316
```

Ranking each metro's ZCTAs by their existing warehousing count — a published
Census number, nothing estimated from it, zero parameters — **matches** the
three-parameter fitted model on ranking: nominally one hit ahead at top-1 and
at top-10, level at top-5. The fitted model is marginally ahead on the raw
Brier score and that gap is far too small to survive 38 decisions. The word
for this is *matches*, and the one-hit gaps in the table above are not to be
quoted as a win for either side.

> **Corrected 2026-09-14, and the correction is against the earlier text of
> this very ADR.** This paragraph said **beats**, and went further — it said
> in so many words *"the word for this is beats, not matches: an earlier
> internal note used 'matches', which errs in the flattering direction and has
> been corrected."* That instruction was **wrong**, and it is withdrawn. The
> earlier note was right. "Beats" rested entirely on the single seeded 56/38
> split tabulated above: one hit at top-1, one hit at top-10. Repeat the split
> fifty times on the same 94 decisions and the raw count is ahead by **0.36
> hits of 38, paired sd 1.14**; it *wins* 23 of the 50, *loses* 11 and ties
> 16, with mean top-10 of 20.96 against the fitted model's 20.6
> (`../../outputs/metrics/gbm_benchmark.json`, `across_repeats`). A third of
> one decision, with a paired sd three times its size, is a coin toss.
>
> This is not the evidence moving on — the fit is the same fit and the table
> is still correct for its seed. It is a claim that was **wrong when written**,
> because a one-hit difference on 38 decisions was read as a result. The
> irony is on the record deliberately: this ADR overcorrected *against* its
> own model, and overstating evidence against yourself is still overstating
> evidence.
>
> **The pre-registered residual risk is still realised and the negative result
> is untouched.** Three estimated parameters buy no ranking improvement over
> counting warehouses. That was the finding under "beats" and it is the
> finding under "matches".

Two qualifications, neither of which rescues the result. The pre-registered
benchmark was an **atheoretical gradient-boosted ranker**, and that was never
built; single-covariate rankings are a weaker adversary, so a real benchmark
would if anything have made the model look worse, not better. And the model
does decisively
beat a population ranking, 19/38 against 10/38 at top-10 — which is a finding
about warehousing, not about the estimation, since the raw warehousing count
gets there without it.

The substantive reading is *"the operator builds where warehouses already
are"*. True, useful, exactly twice as good as a population map, and obtainable
without a model.

**"The successor may also fail, for a reason we would notice late." IT FAILED,
AND THE DIAGNOSTIC THIS ADR NAMED CONFIRMS IT.** The pre-registered prediction,
written before any of this was run, was "wide bootstrap intervals covering zero
on every coefficient", with the bootstrap named as *the* diagnostic. The
diagnostic has been run and the prediction holds — against the correct null,
which is 1.0 rather than 0, because households is the numeraire and only ratios
are identified.

```
  56 training decisions across 38 metros, alpha 0.05
  1,000 bootstrap replicates over decisions, 1,500 over metros, converged

  warehousing_establishments, beta = 1.4428  -- the only interior parameter
    sandwich, 95%                  [0.734,  2.835]
      z against the ratio 1                 1.064    p = 0.287
    bootstrap over decisions       [0.760,  4.762]   11.8% below 1
    bootstrap over metros          [0.702, 10.013]   13.4% below 1
    BCa                            [0.714,  3.522]
    ALL FOUR INTERVALS COVER 1.0.

  land_area_sqmi       beta = 3.0e-16   AT THE BOUNDARY
  establishments       beta = 4.7e-16   AT THE BOUNDARY
    sandwich REFUSED for both, correctly; one-sided bootstrap instead
    upper endpoints 0.165 / 0.228 and 0.765 / 1.238
    about 80% of replicates sit at the boundary in each case
```

So the single covariate that does any work is **not distinguishable from one
more household**. That is entirely consistent with only matching a raw count, and
it is the outcome this ADR said in advance was most likely. A prediction
published before the measurement and then confirmed by it is worth considerably
more than the measurement alone. It is also, in substance, a fourth negative
result rather than a rescue, and it should be reported in that order.

**Currency note.** The `inference` block landed on 2026-09-14 and was
uncommitted at the time this update was written. Re-read the artefact before
quoting these figures.

There is a second-order finding here that this ADR did not anticipate.
The two halves of the prescription are not equally available. `beta = exp(theta)`
keeps the attraction index positive, so `beta = 0` means `theta -> -inf`, and a
sandwich estimator assumes an interior maximum at which the gradient vanishes.
At a boundary it does not, so a standard error computed there is not a wide
number, it is a meaningless one. The implementation refuses to print one and
prints the reason, which is the right behaviour. But `MODEL_SPEC.md` §6.3 asks
for both side by side without noticing that one of them cannot exist for two of
the three parameters, and that section should be amended.

And the resampling unit needs one more level than this ADR specified — which
the measurement now demonstrates rather than merely suggesting. It says
resample buildings rather than rows, which is right as far as it goes. But the
100 loaded national facilities fall in only 62 metros and Los Angeles alone
contributes seven, all facing the same choice set with the same attraction
values. A bootstrap over decisions treats those seven as seven draws; a
bootstrap over metros treats them as one, and **the upper endpoint moves from
4.76 to 10.01**. A factor of two is not an academic distinction. The
metro-clustered figure is the conservative one and is the one to quote;
`MODEL_SPEC.md` §6.3 is silent on which, and should not be. This is the error
that killed the hazard model, appearing a third time in a third costume, and
this time it was caught before it reached a published number.

**"`V = ln(beta'a)` may be applied carelessly." Not carelessly, but the form
cost more than this ADR priced.** Because `beta = exp(theta)` forbids a
negative coefficient, a *repelling* variable cannot be represented at all; the
best it can do is go to the boundary. `land_area_sqmi` did exactly that. The
proposal's claim that a positive loading on households beside a negative
loading on land area would constitute a density preference was therefore never
available in this specification, and it has been withdrawn from
`../proposal/PROPOSAL_V5.md` §5.4. The MAUP check at H3 grain is still not run.

### A defect this ADR did not foresee, and it undercuts the one working covariate

An Amazon delivery station **is** a warehousing establishment. A contemporaneous
CBP count would therefore contain its own outcome, and `ingest/cbp_detail.py`
installs a vintage lag against exactly that: each facility is scored on the
latest CBP vintage *strictly earlier than its recorded `open_year`*.

The guard is correct in design and nominal in practice. **On all 100 loaded
national rows, `open_year` and `open_quarter` equal the quarter of the earliest
OSHA inspection.** `open_year` is not an opening date; it is the "operating by"
upper bound, restated. A building first inspected in 2022 may have opened in
2017, in which case the "strictly earlier" 2021 vintage already counts the
facility itself. The five pilot addresses with an independently known opening
month give lags to first inspection of 4, 13, 57, 69 and 345 months: **three of
the five exceed twelve months**, so on the only evidence available the guard is
defeated more often than it holds. Its margin is zero or negative, not a year.

This ADR's Consequences section says the upper-bound date "stops being a defect
and becomes a conditioning variable". **That is now the least defensible
sentence in the document.** The date did not stop being a defect; it moved into
the covariate. It is recorded as defect M in `../proposal/PROPOSAL_V5.md` §6 and
it is the highest-value remaining fix, because it is the only thing that could
make the headline covariate mean what the model says it means.

### What this update does not change

The decision itself. Retiring an invalid specification for a valid one was the
right move and remains so; validity is not contingent on the valid model
performing well. The warning in the Residual risk section — *"the reframe could
be mistaken for a rescue"* — has aged better than anything else here. It was
not a rescue. It fixed the question and left the answer where it was.

The status stays **proposed** until the user signs it off.
