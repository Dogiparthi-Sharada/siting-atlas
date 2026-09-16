# Siting Atlas — Plain-English Explainer

**Read this before the defense. It explains the whole project from zero, in the
order a sceptical listener will want it, with an example for every idea.**

If you can explain each of the nine ideas below in your own words without
reading, you can defend this proposal.

**One thing outranks all nine of them: Sec. 0.1, the negative results.** There
are now **three**, and all three have to be delivered without flinching. The
discrete-time hazard model was built, fitted on real data, and it failed; it
is now retired — and when it was revived on 6.7 times the events with real
opening dates instead of inspection upper bounds, it failed again. Its
successor, a conditional ZCTA choice model, *is* fitted — and on held-out data
it is only matched by a single raw Census warehousing count with nothing
fitted from it, so the estimation buys nothing. And a third model, a
metro-level entry model, was **pre-registered before it was fitted** and lost
to "rank metros by household count" in 0 of 7 held-out years. Anyone who
finishes this document believing otherwise has been misled, so that section
comes before everything else and you should be able to deliver it cold.

> **Updated 2026-09-15.** Sections 0.1c to 0.1f are new. They cover the
> hazard model's revival and second failure, the pre-registered metro model,
> the panel expansion from 104 facilities to 693, and the two figures the
> project found fabricated in its own audit. Everything in 0.1a and 0.1b is
> still correct **for the pilot frame it was measured on**, but the pilot
> frame is no longer the only frame — see 0.1e for the two-frame problem,
> which is the single easiest way to misquote this project.

---

## 0. The whole thing in one paragraph

Big retailers decide which ZIP codes get same-day delivery. Each ZIP costs them
$3–5 million to enable. Those decisions are made inside private models nobody
outside the company can see — but the consequences are public: property
values, truck traffic, air quality, and tax breaks that cities hand over to
attract the facilities. **We build an open version of that decision model using
only free public data, and we check whether it actually predicts what the
company did.**

We did check. It does not. Read the next section before anything else.

---

## 0.1 STOP. Three siting models were built, fitted, and none earns its keep.

```
  +--------------------------------------------------------------------+
  |  THE HEADLINE, SO THAT NOBODY CAN READ PAST IT                     |
  |                                                                    |
  |  ONE. The discrete-time hazard model was specified, coded, fitted  |
  |  on REAL data, and it does not work. It is not "promising". It is  |
  |  not "directionally right". On the held-out data it is WORSE       |
  |  CALIBRATED than a model that predicts the same constant number    |
  |  for every ZIP in every quarter. It is now RETIRED -- and it was   |
  |  REVIVED on 5,441 events instead of 812, with real opening dates   |
  |  instead of inspection bounds, and it FAILED AGAIN.  Sec. 0.1c     |
  |                                                                    |
  |  TWO. Its successor, a conditional ZCTA choice model, IS fitted    |
  |  and IS the project's siting model. On 38 held-out decisions it    |
  |  is MATCHED by a single raw Census count of warehousing            |
  |  establishments with NOTHING fitted from it: 8 top-1 hits to its   |
  |  7, and 20 top-10 hits to its 19, a gap that vanishes over fifty   |
  |  re-splits. The estimation buys nothing measurable. The word is    |
  |  "matched", never "beaten".                                        |
  |                                                                    |
  |  THREE. A metro-level entry model was PRE-REGISTERED -- sample,    |
  |  covariates, baselines, metric and success criterion written to    |
  |  disk BEFORE any fit, md5 recorded -- and it LOST. Ranking metros  |
  |  by household count beats it in 7 of 7 held-out years. Pooled AUC  |
  |  0.7323 against the baseline's 0.8949. It loses 50 of 50 paired    |
  |  re-splits. The registered verdict is H0.  Sec. 0.1d               |
  +--------------------------------------------------------------------+
```

> **Corrected 2026-09-14, and the correction is not a rescue.** Box TWO used to
> read **BEATEN**, and the line under it used to insist *"the word is 'beaten',
> never 'matched'"*. Both are now inverted, because the word was wrong, not
> merely dated. "Beaten" was read off one seeded 56/38 split. Re-split the same
> 94 decisions fifty times and the raw count's margin is **+0.36 hits out of 38,
> paired sd 1.14**, and the raw count itself *loses* 11 of the 50
> (`outputs/metrics/gbm_benchmark.json`, `across_repeats.conditional_logit`).
> A third of one decision is not a win for anybody; the old wording read noise
> as a result. Nothing about the verdict changes: fitting three parameters buys
> **no** ranking improvement over counting warehouses, and the single-split
> numbers quoted in this box are still correct for their seed.

### 0.1a The retired hazard model

Here is the whole scoreboard, read straight out of
`outputs/metrics/hazard_report.json` (current run id `20260914-002509-2374`).
The "null" column is a model with no inputs at all: it predicts the base rate
everywhere, forever.

```
                                    model      null      verdict
   -----------------------------------------------------------------
   AUC (ranking ability)            0.6894    0.5000    model better
   Brier (squared error)            0.01952   0.01961   +0.5% skill
   ECE (calibration error)          0.00863   0.00005   NULL 170x better
   -----------------------------------------------------------------
   Brier skill, temporal hold-out            -0.02091   NULL better
   Brier skill, geographic hold-out          -0.06184   NULL better
   -----------------------------------------------------------------
   covariates distinguishable from 0          1 of 3    households only
   events per parameter                       7.6       the floor is 10
```

**What each line means in plain words.**

- **AUC 0.6894.** Pick one ZIP that got a station and one that did not. The
  model scores the right one higher about 69% of the time. A coin flip is 50%.
  So there is *some* signal. There is not much.
- **ECE 170x worse than the null.** Expected Calibration Error asks: when the
  model says "3% chance", does it happen 3% of the time? The null says "2.0%
  everywhere" and the truth is 2.0%, so the null is almost perfectly calibrated
  by refusing to stick its neck out. Our model spreads its guesses from 0.9% to
  8.5% and those spread-out guesses are wrong by enough that its average
  calibration error is 170 times the null's. **You must not quote a probability
  out of this model.**
- **Negative skill on both hold-outs.** Train on early quarters, predict later
  ones: worse than the constant. Train on eight metros, predict Phoenix and
  Boise: worse than the constant. (Phoenix and Boise hold two dated stations
  between them, so that second test is a smoke alarm for gross failure, not a
  real test of transfer.)
- **One of three covariates survives.** Households, hazard ratio 1.00005,
  p = 0.00007. Translated: *Amazon builds where the people are.* True, and not
  worth a capstone.
- **7.6 events per parameter.** 38 usable facilities divided by 5 parameters,
  on the most generous counting. The conventional floor for a model like this
  is 10. On the conservative count (28 independent metro-quarter episodes) it
  is 5.6. The study is under-powered and no amount of tuning fixes that.

### Why it failed, and why the diagnosis is the interesting part

**The unit of analysis was wrong.** A delivery station has a catchment of about
15 miles, and when it switches on, it switches on *every ZCTA inside that
circle at the same instant*. On the delivered panel the median station covers
**58** ZCTAs, the mean **88**, and the largest **307**.

> **Worked example.** The model's row is "ZIP 60608, 2021Q2, event = 1". It
> reads that as a decision. It is not a decision. It is one of 88 simultaneous
> consequences of a single decision: "open a building in Chicago". The model is
> being handed 88 copies of one fact and told they are 88 independent
> observations. Of course the standard errors are a fiction.

The assumption this breaks is **independence across observations**, Train
(2009) Sec. 3.7.1, printed page 61:

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> `L(beta) = prod_n prod_i (P_ni)^{y_ni}`."

That product *is* the likelihood the model maximises. If the rows are not
independent, the product is not a likelihood and the standard errors it implies
are fiction. The standard name for the failure is **clustering**, or
**pseudo-replication**.

> **A citation withdrawn, and the argument gets stronger for it.** Earlier
> drafts of this file, and of several siblings, attributed the failure to Train
> Sec. 2.2 and to **mutual exclusivity**. That was the wrong section. Sec. 2.2
> governs a choice set facing a *decision maker*; a hazard on area-quarters has
> no decision maker choosing among those rows, so exclusivity is not a property
> those rows can have or lack. Worse for the old rhetoric, Train calls that
> criterion "not restrictive" and says "Appropriate definition of alternatives
> can nearly always assure that the alternatives are mutually exclusive"
> (p. 12), and gives a two-line repair. An examiner who has read the book would
> have taken the point off us. Independence across observations has no two-line
> repair — the only fix is to change the unit of analysis — which is exactly
> why the corrected diagnosis is the stronger one. The repo's own correction is
> at `../research/NOTES_train_ch03_logit.md` Sec. 6.2.

Train Sec. 2.2 stays in the document, pointed at the **successor** rather than
at the failure: it is the right authority for *constructing* a choice set. The
reframe is **"which ZIP does the station go in, given that a station is opening
in metro m in period t"**. That successor specification has now been **built and
fitted**. See Sec. 0.1b.

### The second reason: the dates are upper bounds, not dates

The opening dates come from federal OSHA inspection records. An inspection
happens at a site that is *already operating*, so the date tells you "open by
then", not "opened then". On the five addresses that also appear in MWPVL's
2012 table with real opening months, the bound held 5 times out of 5 - but the
lag between opening and first inspection was **4, 13, 57, 69 and 345 months**.
One site opened in 1997 and was first inspected in 2026.

A date that can be 29 years late is a censoring interval, not an event time.
Anything that depends on *when* something happened inherits that problem.

---

## 0.1b The successor IS built, IS fitted, and a raw count matches it

This is the project's siting model now. Everything below is read straight out
of `outputs/metrics/choice_report.json`.

It is a **conditional ZCTA choice model** on the **national** frame — the
artefact's own first key is `"frame": "national"` — with **94** decisions,
**56** used for training and **38** held out, seed `20260914`. Three free
parameters. It converged. In-sample log-likelihood **-203.4497** against a
uniform model's **-253.3351**, giving a McFadden rho-squared of **0.19691**
*in sample, on the 56 training decisions*. Quote it as in-sample or not at all.

The coefficients, with `households` **fixed at 1 as the numeraire** (the model
is scale-invariant, so only ratios are identified and one coefficient has to be
pinned; the implementation sets `beta = exp(theta)` to keep the attraction index
positive):

```
   covariate                       beta        note
   ------------------------------------------------------------------
   households                      1.0         numeraire, not estimated
   warehousing_establishments      1.4428      the only one doing work
   land_area_sqmi                  3.04e-16    AT THE BOUNDARY
   establishments                  4.72e-16    AT THE BOUNDARY
```

**One parameter of three is doing any work.** Now the held-out scoreboard, 38
decisions over 3,998 alternatives, with every single-covariate benchmark the
artefact records. Learn both of the first two rows; giving only the first is
overselling.

```
                            top-1    top-5    top-10    Brier
   -------------------------------------------------------------
   fitted model              7/38    16/38     19/38    0.008724
   warehousing count alone   8/38    16/38     20/38    0.008951
   households alone          1/38     5/38     10/38    0.009271
   establishments alone      0/38     8/38      9/38    0.009307
   land area alone           0/38     3/38      6/38    0.009816
   uniform within metro      1/38     3/38      7/38    0.009316
```

**The headline finding, stated the bad way round first.** A single raw Census
County Business Patterns count — NAICS 493, warehousing and storage, with
*nothing fitted from it* — **matches** the three-parameter fitted model. On
this seed it is one hit ahead at top-1 and one ahead at top-10 and level at
top-5; over fifty re-splits that lead shrinks to +0.36 hits of 38, so read the
table as a tie, not a defeat (see the correction block in Sec. 0.1). The fitted
model is marginally ahead on raw Brier, and that gap is far too small to
survive 38 decisions either. **The estimation buys nothing measurable.**

The substantive reading is the useful half, and it is genuinely useful: *the
operator builds where warehouses already are.* That is true, it is exactly twice
as good as a population map at top-10 (20 against 10), and it is obtainable
without a model. Reporting that a raw count matched our estimator **is** the
finding. It is not an admission we were talked into.

### The intervals landed late, and they cover the null

`docs/MODEL_SPEC.md` Sec. 6.3 prescribes a robust sandwich covariance **and** a
bootstrap over decisions.

> **A claim withdrawn, 2026-09-14.** This section used to be headed "No
> standard errors. No intervals", and it listed the keys of
> `choice_report.json` to show the artefact carried no uncertainty block. That
> was true for most of the day and stopped being true the same day: an
> `inference` key now sits beside the others, `models/choice_runner.py` builds
> it, and `tests/unit/test_choice_inference.py` exists. The withdrawal is
> recorded rather than swallowed, because the finding changed shape with it.

**The null here is `beta = 1`, not `beta = 0`.** Households is fixed at 1 as
the numeraire because the model is scale-invariant and only ratios are
identified, so each interval is an interval on "how many households one unit of
this covariate is worth". A reader applying the usual "does it cover zero"
habit reads this backwards.

```
  56 training decisions across 38 metros, alpha 0.05
  1,000 bootstrap replicates over decisions, 1,500 over metros, converged

  warehousing_establishments, beta = 1.4428 -- the only interior parameter
    sandwich, 95%                  [0.734,  2.835]
      z against the ratio 1                1.064    p = 0.287
    bootstrap over decisions       [0.760,  4.762]  11.8% below 1
    bootstrap over metros          [0.702, 10.013]  13.4% below 1
    BCa                            [0.714,  3.522]
    ALL FOUR INTERVALS COVER 1.0.

  land_area_sqmi      beta = 3.0e-16   AT THE BOUNDARY
  establishments      beta = 4.7e-16   AT THE BOUNDARY
    sandwich REFUSED for both, correctly; one-sided bootstrap instead,
    with about 80% of replicates sitting at the boundary
```

So the single covariate that does any work is **not distinguishable from one
more household**, at p = 0.287. That is a fourth negative result rather than a
rescue, and it is exactly what ADR-0004 pre-registered before the procedure was
written. It also agrees with the ranking null result above rather than adding a
separate one.

The sandwich is refused at the two boundary parameters and that refusal is
correct rather than a shortfall: a sandwich estimator's asymptotics assume an
**interior** maximum with a vanishing gradient, and `beta = exp(theta)` puts
those two at `theta` around minus thirty-six. A standard error computed there
would be meaningless rather than merely wide. The bootstrap survives, with a
one-sided interval because the sampling distribution has an atom at zero.

Two caveats that must travel with the numbers. Train's precondition for the
bootstrap fails at 56 decisions (Sec. 8.6, p. 202), so these intervals measure
how far the estimate moves with *which of our 56* are included, not sampling
variability over the population. And the decision-level and metro-level
bootstraps differ by a factor of two on the upper endpoint, because seven of
the 100 loaded facilities share the Los Angeles choice set; quote the
metro-clustered one.

> **A currency note.** The `inference` block and the modules behind it --
> `choice_inference.py`, `choice_sandwich.py`, `choice_bootstrap.py` -- were
> uncommitted at the time of writing. Re-read the artefact before quoting, and
> expect an examiner running `git status` to see them in the untracked or
> modified list.

### Conformal on the choice model, which is a worse look than the hazard model's

```
   alpha   nominal   empirical   median set   share of choice set
   ----------------------------------------------------------------
   0.10     0.90       1.000        38.5             0.714
   0.20     0.80       0.958        34.0              --
   0.30     0.70       0.833        18.5              --
```

24-decision test split; median choice set 59.5 alternatives. Read honestly: at
the 90% level the procedure names **71% of the metro**. It is covering by being
very nearly vacuous. That is a *worse* result than the retired hazard model's
88.19% against 90% nominal, and it must not be presented as a success.

---

## 0.1c The hazard model was revived on better data, and it failed again

*Added 2026-09-15. Artefact `outputs/metrics/hazard_revival.json`; the
retired run's `hazard_report.json` was not touched.*

The obvious objection to retiring a model on 39 events was: **"then get more
events and better dates."** Both have now been got, and it made no
difference. That is a *stronger* negative result than the retirement was,
because the objection has been answered with a measurement rather than an
argument.

```
                                  retired run         this run
  -------------------------------------------------------------------
  panel                      43-facility pilot   687 loadable facilities
  dates                      OSHA "operating     MWPVL STATED openings
                             by" upper bounds      on 545 of them
  events (ZCTA-quarters)                 812              5,441
  independent episodes                    28                436
  events per parameter           5.6  FAILED         87.2  CLEARED
  AUC                                 0.6894             0.6832
  calibration vs a constant     lost, 170x       LOST, 0 OF 17 TIMES
  ZCTAs one opening switches on    median 58          median 39
  the independence violation        VIOLATED     STILL VIOLATED
  -------------------------------------------------------------------
```

**Two handicaps removed, one untouched — and the untouched one is the reason
for the retirement.** One leasing decision still enters the likelihood as a
median of 39 rows. There is no radius that fixes it: swept from 8.3 to 45
miles, the per-opening ZCTA count runs 14, 30, 39, 59, 79, 173 and never
approaches one.

**The problem actually got worse in a way the headline number hides.** The
median came *down* from 58 to 39, which sounds like progress. It is not. On
the pilot frame the catchments were mostly disjoint, so a ZCTA's switch-on
date belonged to one station. On the expanded frame **58.4% of covered ZCTAs
sit inside two or more catchments**, so only the earliest arrival registers
an event and a ZIP's switch-on quarter is now a joint function of several
buildings' decisions. That is a *second* dependence layered on the first.

**And one counter-intuitive consequence nobody should skip**, because it
inverts what everyone expects. Correcting a date *backwards* does not add
events — it removes them. An opening moved from 2021 to 2018 falls out of the
front of the window and is dropped as left-truncated. On the 130 matched
facilities the true-date arm has **2,666** events against the
inspection-bound arm's **3,131**, on identical buildings. Better dates, fewer
events.

**What the date control does and does not show.** Only **30** facilities
actually change date between the two datings — an OSHA bound exists only
where an inspection happened, 139 of 687 facilities match one at all, and 100
of those are rows whose dates were *derived* from the bound in the first
place. On the matched contrast the new dates score AUC **-0.0043**, i.e.
marginally *worse*. The honest verdict is **"no measurable effect from the
dates, on a control too weak to detect a small one"**, and stating that is
the whole reason the control was run: without it the +0.04 AUC in the
unmatched contrast would have been reported as a dating effect, and it is
not.

> **The sentence to be able to say cold.** *"The discrete-time hazard on a
> ZCTA-quarter panel fails on 5,441 events across 275 metros with stated
> opening dates, at AUC 0.68 and calibration worse than a constant in all
> seventeen measurements taken. It fails for a reason no quantity of data
> addresses: one siting decision enters the likelihood as a median of 39
> independent observations."*

---

## 0.1d The third model was pre-registered, and it lost

*Added 2026-09-15. Pre-registration `docs/PREREG_METRO_MODEL.md`, written
before the fit; artefact `outputs/metrics/metro_entry.json`, which records
the prereg's path and its md5 `946f7ef75db69e5278eea409a04c3823` so the
registered document can be checked against the one on disk. Full write-up
`../research/NOTES_METRO_ENTRY.md`.*

**The question.** The ZIP-level model failed. Does the failure disappear at a
coarser grain — can free public data say *which metro* gets a station next,
even if it cannot say which ZIP?

**Why that was a real hypothesis and not a hope.** Six of the covariates that
failed at ZIP grain are county figures broadcast to every ZCTA in the county
— about nine distinct values across two hundred candidate ZIPs. Their
variation is *between* counties, therefore between metros, which is exactly
the variation a metro-level model uses and a ZIP-level model throws away by
construction. So they should work at metro grain for the same reason they
failed at ZIP grain.

**The answer is no, and it is not close.**

```
  the registered criterion             clause 1        clause 2
                                   AUC > households   ECE <= constant
  ---------------------------------------------------------------
  prereg_strict  (the verdict arm)     0 of 7            3 of 7
  vintage_clean                        0 of 7            3 of 7
  vintage_relaxed (allowed to cheat)   1 of 7            0 of 7
  ---------------------------------------------------------------
  all three fail both clauses, under logistic, Poisson AND negative
  binomial, which agree to within 0.0001 of AUC in every year
```

```
  pooled over 7 held-out years, 6,545 metro-years, 306 events
    the fitted model                              AUC 0.7323
    rank by households, zero parameters           AUC 0.8949
    count of facilities already there, zero par.  AUC 0.7325   <-- !

  metro-clustered bootstrap, 2,000 draws, 935 CBSAs
    model minus households        -0.1628  [-0.2011, -0.1313]
  50 paired re-splits, refitted inside every repeat
    mean paired difference        -0.175,  losing 50 of 50
```

**The line to notice is the third one.** A two-covariate logistic, fitted
seven times, scores 0.7323 while a zero-parameter column of integers scores
0.7325 on the identical 6,545 rows. Top-50 totals are 129 against 127. The
model reproduced a count.

**Three things the run did that a defensive run would not have.**

1. **It reported a Simpson's paradox in its own headline.** Terciles of
   household count: the model's AUC is 0.4125, 0.5666 and 0.6961 — *the
   pooled 0.7323 is higher than the model's AUC in every single tier*. Size
   predicts the outcome and size defines the strata, so pooling rewards a
   ranking the model did not have to earn. Quoted alone, 0.73 would read as a
   working model.
2. **It ran the sensitivity the prereg demanded and it came out worse.** The
   pandemic years 2020-21 hold 102 of the 306 held-out events. Dropping them
   gives 0 of 5 and 1 of 5, so the finding is not driven by them.
3. **It ran a "let the model cheat" arm.** `vintage_relaxed` is a
   seven-covariate logistic that *contains households*, plus population,
   income, traffic proximity and diesel particulates, and is allowed to see
   data from after the year it predicts. It still loses to ranking on
   households alone in 6 of 7 years, by margins of -0.0003 to -0.0223, and
   its single win is +0.0004. Its calibration loses 7 of 7. **Leakage is not
   what is holding the model up, and removing it is not what is holding the
   model down. The ceiling is the baseline.**

### The largest qualification, which belongs in the same breath as the claim

**The vintage gate removed 8 of the 12 registered covariates, and 2 more
failed a coverage floor. The verdict arm has two.** That is a weak model and
it is weak because the project's own leakage rule made it weak.

The reason is structural rather than marginal. Most of the panel's columns
are **not time series at all** — mean distinct values per unit across all 32
quarters of `panel.parquet`:

```
  population, households, median_household_income      1.00
  traffic_proximity, diesel_pm                         1.00
  wage_all_occupations, wage_freight_handler           1.00
  metro_employment                                     1.00
  permit_units_total                                   4.97  (annual, real)
```

One value, repeated 32 times. ACS 5-year 2023 is built from responses
collected 2019-2023, so using it to predict 2020 is not a borderline
publication-lag call — three of its five collection years are *after* the
outcome. BLS OES `oesm25ma.zip` is a single May 2025 vintage and is never
usable. EJScreen 2024 is usable for 2025 only.

**So the Tier 1 mechanism that generated the hypothesis was never testable on
this panel.** That is a finding about the data rather than about the
hypothesis — and it points at the same conclusion from a different direction.
The covariates that might have distinguished one metro from another are
published once, late, and without a usable history, which is itself a form of
the transparency gap.

> **What to say if an examiner offers "so the prereg was badly designed".**
> Agree, in part, and say which part. `NOTES_METRO_ENTRY.md` §12 lists three
> places the prereg is wrong: it registered covariates the panel cannot
> supply in time-respecting form when a two-line check would have caught it;
> its baseline and its vintage rule are in direct conflict and it does not
> say which wins; and it does not say which model form carries the verdict.
> The run was executed as written anyway, and the conflict was resolved in
> the direction that disfavours the hypothesis. All three are the kind of
> thing only visible once a prereg meets the data, which is an argument for
> writing one rather than against it.

---

## 0.1e The panel went from 104 facilities to 693 — and the two-frame trap

*Added 2026-09-15. Artefacts `outputs/metrics/mwpvl_extraction.json`,
`mwpvl_merge.json`, `mwpvl_validation.json`, `national_panel_expanded.json`.*

**What happened.** Thirteen table images from an industry consultancy's
2025 network PDF were OCR'd into **1,904 facilities**, of which **1,420**
carry an opening date. Filtered to the US small-package delivery-station
class — 1,269 rows of other classes dropped on purpose, because this panel's
unit is a delivery station — that leaves **635** rows. Screened against the
hand-verified 104-row panel with the project's existing Fellegi-Sunter
linkage: 1 internal duplicate, 40 already present, 5 held for clerical
review, **589 added**.

```
  panel rows before        104
  panel rows after         693       687 buildings, 230 CBSAs, 50 states
  carrying a coordinate      0       every distance is ZCTA-centroid precision
```

**Three independent validations were run, and none of them is a clean bill.**

```
  1  OSHA CROSS-CHECK.  Of the 1,420 dated rows, 208 link to an OSHA
     building.  11 claim an opening AFTER the date an inspection proves
     the site was already operating, so the declared edit E_operating_by
     passes on 94.7%.  BLIND SPOT: 1,212 of the dated rows cannot be
     checked this way at all.

  2  PLAUSIBILITY.  Of the 1,420, two delivery-station rows predate the
     network and FIVE are beyond plausible -- the worst claims 2090Q2
     against an OSHA record proving operation by 2020-09-22, which is
     279 quarters after the bound.  Those rows are excluded, not
     corrected, and the CSV preserves the rejected value so the
     exclusion is reversible from the artefact alone.

  3  OCR STATE CROSS-CHECK.  The state name the OCR read, against the
     state implied by the postcode -> county -> state FIPS crosswalk.
     604 of 606 comparable rows agree -- 99.67%.  This one is free and
     it is the strongest of the three.  BLIND SPOT: 22 state strings
     did not parse at all.
```

**And the blind spots that are not validations.** 54 rows have no street
address to screen on, so they enter the panel as new *by default rather than
by evidence*. One known duplicate slipped through on a damaged street string.
And the source PDF supplying 589 of the 693 rows **is not in the repository**
and cannot be reproduced from what is — that is the top CRITICAL finding of
the project's own audit and it is a reproducibility hole, not a data-quality
one.

### What the extra data bought, and what it did not

**It did not buy accuracy.** Pooled top-10 lift fell 2.95x to 2.76x — and
that fall is a **Simpson's paradox**, not a model result. Lift is capped by
choice-set size: in a metro with 25 candidates a uniform guess is already in
the top ten two thirds of the time. The MWPVL rows are weighted to small
markets, so the *mix of questions* moved: decisions with 25 or fewer
alternatives went from 7 of 94 to 66 of 485. Read held out, over 50
re-splits, against an analytic chance rate, **large-metro top-10 lift goes
6.18x to 6.33x — flat.**

**It bought precision, which is what the code said to look for before the run
rather than after it.**

```
  warehousing_establishments     n     interval
  -----------------------------------------------------------
  pilot panel                    94    1.528  [0.985, 2.550]
  expanded panel                483    1.191  [0.956, 1.490]
```

64% narrower, still containing 1.0, and the point estimate has moved
*towards* the numeraire it was supposed to escape. **So sample size was never
the binding constraint.** That is the finding, and it is a negative one.

### The two-frame trap — the easiest way to misquote this project

> **Two facility frames are live at once and different artefacts read
> different ones. Always say which.**
>
> ```
>   PILOT frame    national_facilities.csv, 104 rows / 100 loaded
>                  94 decisions, 38 held out
>                  read by: choice_report.json, gbm_benchmark.json,
>                           leakage_test.json, the published figures
>
>   EXPANDED frame national_facilities_expanded.csv, 693 rows / 687 buildings
>                  483 decisions
>                  read by: refit_expanded.json, panel_experiments.json,
>                           hazard_revival.json, metro_entry.json
> ```
>
> Sections 0.1a and 0.1b above are the **pilot** frame and their numbers are
> correct for it. The audit's own headline is that the production model, the
> panel, the warehouse, the figures and the proposal are **all still on the
> pilot frame**, and the expanded frame exists only in experiment artefacts.
> Quoting a 94-decision number beside a 483-decision one without saying so is
> the mistake to avoid.

---

## 0.1f Two figures were fabricated. The project found them, and fixed them.

*Added 2026-09-15. Found in `docs/data/FIGURES.md`; remediation in the
docstrings of `tools/figures/fig_methods.py`.*

**This section is here because it is an integrity matter and integrity
matters are not survivable if you are seen to have hidden them.** Read it
before you present any figure from this project.

**Figure 5, the cannibalisation decay curve.** Nine effect values typed by
hand into the plotting code. A shaded band labelled **"95% CI"**. One point
annotated **"n.s."** — a significance test. And a y-axis of **2-day order
volume**, a quantity this project does not observe and whose absence is the
documented reason the cannibalisation analysis was abandoned in the first
place. The figure therefore asserted a causal effect, a confidence interval
and a significance test, on a variable that is not in the data. Its caption
read "values are illustrative pending estimation" — six words under a chart
carrying error bars, and figures get lifted into slides without captions.

**Figure 7, the tornado chart.** Eight bucket swings typed in, per-bar dollar
labels printed to the cent, and **no disclosure anywhere** — not in the
figure, not in the caption. Its caption asserted "four primary buckets
account for roughly three-quarters of the swing in net present value" as
measured fact. Nothing supports it: `montecarlo_report.json` carries
aggregate bands over 500 draws and no per-bucket decomposition.

**What was done, 2026-09-15.** Both were restyled as obvious schematics:

- the interval and the significance annotation are gone
- the decay curve is dashed, and its y-axis carries no numbers at all
- the tornado's per-bar dollar labels are gone, because they were false
  precision on invented numbers, and its x-axis carries no numbers either
- an **ILLUSTRATIVE ONLY** banner sits *inside the axes* on both, so it
  travels with the image when the chart is cropped into a slide

**Three things to say about this rather than two.**

1. **The fix removed the false precision, not the invented magnitudes.**
   Figure 7 still draws eight typed-in swings; what changed is that they are
   unlabelled and the claim has been reduced to the *ordering*, which is
   defensible from the cost model's own structure — driver time at the door
   is 66.5% of the per-stop bill. Making it real means decomposing the 500
   Monte Carlo draws by bucket. That is about a day's work and it is listed
   as open.
2. **It was the second time, not the first.** The same defect class had
   already been purged from two other figures: one had printed a target AUC
   of 0.84 under an ROC curve synthesised to have that area, and another had
   invented eight ZIP codes and their rank-stability shares. The honest
   reading is that this project has a habit of drawing the result it expects
   and a review process that keeps catching it late.
3. **The same audit cleared an adjacent suspicion rather than taking the
   chance to look worse-and-therefore-more-honest.** There was a worry that a
   re-split spread had been drawn somewhere as a confidence interval. It had
   not: the one figure carrying a band has a footer reading "the band in
   panel A is that two-sigma spread, not a confidence interval."

**And the exposure that remains.** The audit that found all this — and
`docs/data/FIGURES.md`, and `docs/data/ARTEFACTS.md`, and several research
notes — are **on disk but not under version control**. The two code fixes
are in tracked files. So a clean clone today contains some of the retracted
material and not all of the retractions. That is a five-minute job that has
not been done, and "it is on my disk" is not an acceptable answer for a
document whose entire purpose is to be checkable.

---

### What this means for how you read the rest of this document

```
  WORKS ON REAL DATA                    DOES NOT EXIST / FAILED
  -----------------------------------   -----------------------------------
  cost model     2,333 priced ZCTAs     hazard siting model   FAILED TWICE
                 median $1.0830                                (39 events,
  portfolio      282 activations,                               then 5,441)
                 $1.128bn of $2bn,      choice siting model   FITTED, but
                 so it DECLINES ~44%                            matched by a
  warehouse      33,791-ZCTA star                               raw count
                 schema, DuckDB         metro entry model     PRE-REGISTERED
  panel          1,081,312 rows                                 AND LOST, H0
  agent gates    6 gates, real data     cannibalisation study NEVER BUILT
  Monte Carlo    500 of 500 draws        (synthetic control, placebo
  tests          796 pass, 2 xfail       inference, Pollmann bands,
  version ctrl   git, in place           Heckman, mutable W - all
  facility panel 693 rows, 687          satellite dating      FAILED, 36%
                 buildings, 3 indep.                          impossible
                 validations           standard errors        PRODUCED, and
  the dispersion a PRIOR rejection      on the choice model     they cover
   rule          rule for covariates                            the null
```

> **Corrected 2026-09-15.** This table previously said "638 pass, 2 xfail"
> and listed "standard errors on the choice model — NOT PRODUCED". Both are
> now wrong: the last reported run is 796 passing with 2 xfailed, and the
> intervals exist. The intervals belong on the *right* of this table anyway,
> because what they say is that the only working coefficient is not
> distinguishable from the numeraire. And the table now has a third failure
> in it.

**The components that never needed the facility panel all work.** The one
component that needed a large sample of real decisions is the one that did
not get one — and it has now failed three times, at two geographic grains,
under a pre-registration, on a panel that grew by a factor of seven. The
sample-size explanation is dead; what replaced it is a diagnosis, and the
diagnosis is the contribution.

Sections 2 and 3 below describe the cannibalisation study and the spatial
weight matrix. **Read them as a design, not as a result.** They are the
project's *second* estimand and not one line of them has been run: there is no
weights matrix `W` anywhere in `src/`, and no decay curve was ever estimated.
Every time this document slips into "we measure", read "we would measure".

---

## 1. What are we actually predicting?

**The observable question:** *For each ZIP code, will the operator turn on
same-day delivery there — and when?*

That is a yes/no plus a date, and both are **visible from outside**. You can
type a ZIP into the operator's own delivery checker. You can read facility
opening announcements. So we can be *scored* — we make a prediction, and
reality tells us if we were right.

> **Example.** In 2023 the model looks at ZIP 85008 in Phoenix — its
> income, population density, distance to the nearest facility, land costs
> — and says *"72% chance this gets same-day service within 18 months."*
> Then we wait, look at what actually happened in 2024–25, and score it.

> **And that is exactly what we did, which is why we know the model is not
> usable.** The scoring is in Sec. 0.1. The design of the target is sound - it
> really is observable and really is scorable. The *specification* built on top
> of it is not. Keep those two judgements apart: "we picked a checkable target"
> survives, "our model hit it" does not.

### Why the target must be observable — the most important thing to understand

The tempting alternative is to predict **order volume per ZIP**, which nobody outside the company
can observe. That number must then be *invented*: take total company orders and split
them across ZIPs in proportion to income and retail density.

Then a model using income and retail density predicts that invented number.

**Do you see the problem?** The answer was made out of the same ingredients as
the question.

> **Example.** Suppose I define a student's "talent score" as
> `0.6 × height + 0.4 × shoe size`. Then I build a model that predicts talent
> score from height and shoe size. My model will be almost perfect — 3%
> error! — and it has learned **nothing about talent.** It reverse-engineered
> my own formula.
>
> That is exactly what a constructed target does. And the scary part: **the better the
> score looked, the more it proved the bug.**

Switching to "did they enable service here" fixes it, because that number comes
from the world, not from us.

---

## 2. What is "cannibalization" and why does it complicate everything?

```
  +--------------------------------------------------------------------+
  |  STATUS: NOT BUILT. Everything in this section and the next is the |
  |  project's SECOND estimand. It has never been touched. Read it as  |
  |  a design. The only cannibalisation that exists in the codebase is |
  |  an ASSUMED penalty in the portfolio optimiser - 20 km radius,     |
  |  0.18 peak, saturating with neighbour exposure. It is a parameter  |
  |  somebody typed, not a number anybody estimated. It has no         |
  |  standard error. See src/siting_atlas/optimize/params.py.          |
  +--------------------------------------------------------------------+
```

When same-day launches in ZIP A, some orders there are genuinely new. But some
are just customers who *would have ordered anyway* on 2-day shipping and simply
switched. Those are not new revenue — the company cannibalized itself.

Worse, it leaks into neighbours.

> **Example.** Same-day launches in Berkeley. A customer in neighbouring
> Oakland — where it did *not* launch — drives to a pickup point, or
> changes their ordering pattern because their household now has one
> same-day-eligible address. Oakland's numbers move even though Oakland was
> never "treated."

Statisticians call the assumption that this doesn't happen **SUTVA** (Stable Unit
Treatment Value Assumption). In delivery networks it is plainly false, and most
standard methods assume it.

**What the design calls for:** measure how far the leak reaches. Draw rings
around each launched ZIP — 0–8 km, 8–20 km, 20+ km — and estimate the effect
separately in each ring. That would give a **decay curve** (Figure 7 in the
proposal).

> **The result would read like this:** *"Cannibalisation is -12% within 8 km,
> -4% at 8-20 km, and statistically indistinguishable from zero past 20 km."*
> One sentence, and it is a number nobody has published.
>
> **Those three numbers are ILLUSTRATIVE. They have not been measured.** They
> are there to show you the *shape* of the answer the design would produce. If
> you quote them in a viva as findings you will be caught, and rightly.

**And there is a reason to doubt the design would survive contact with this
data.** A ring regression needs to know *when* each station opened, to split
"before" from "after". Our dates are OSHA upper bounds with measured lags of 4,
13, 57, 69 and 345 months (Sec. 0.1). The second estimand therefore inherits
the exact problem that sank the first one. Say that before an examiner does.

---

## 3. What is the "spatial weight matrix W", in normal words?

`W` is just **a table saying which ZIPs count as neighbours of which other ZIPs.**
Every spatial model needs one.

Almost everyone builds `W` by touching: if two ZIPs share a border, they're
neighbours — a 1 in the table. Otherwise 0.

**That's an assumption, not a measurement.** And a reviewer will ask "why
touching? why not 5 km? why not drive time?" — and an earlier draft had no answer.

**The proposed fix is neat:** the decay curve in §2 would tell us how far the
effect actually reaches, so we would define neighbours by measured reach rather
than by shared borders. `W` would stop being an assumption and become an
estimate with error bars.

> **Status: not built, and it cannot be built before §2 is.** This move is
> downstream of the decay curve, and the decay curve does not exist. Today the
> codebase has no `W` at all - the optimiser uses a fixed 20 km radius with a
> 0.18 peak, which is the very kind of hand-picked assumption this section
> complains about. Being able to say that out loud is worth more in a viva than
> the fix would have been.

---

## 4. What does the AI agent do, and why is it not just a chatbot?

The agent has three tools. Two are boring and read-only: write SQL, draw a map.

The third one **writes to the database** — and that's where it gets
interesting. It reads competitor news ("Walmart opens a sortation centre in
Plano") and adds that facility to our data, which changes `W`, which changes the
cannibalization estimate, which changes the recommendation.

Letting an AI write into your data is dangerous, so there are gates.

### The four obvious gates (everyone has these)

1. Is the data shaped right? (schema)
2. Do the coordinates exist on Earth? (geocoding)
3. Is the AI confident enough? (threshold)
4. Is it logged so we can undo it? (audit)

### The two gates that are our actual contribution

Here is the insight. **A write can pass all four gates and still destroy the
analysis.**

> **Example — memorise this one, it's the best thing in the project.**
> The agent reads "Walmart opens sortation centre in Plano, TX." It writes
> `(33.0198, −96.6989, SORTATION)`.
>
> - Schema? ✅ valid
> - Geocoding? ✅ Plano is real
> - Confidence? ✅ 0.94
> - Logged? ✅ yes
>
> **All four gates pass. The data is perfect.**
>
> But now Plano's neighbours changed → so the "control group" for our
> Dallas experiment changed → so the cannibalization estimate changed →
> so the NPV moved by millions.
>
> **The data is fine. The inference is broken. And nothing checked that.**

So we add:

- **Gate 5 — donor-pool integrity.** Did this write accidentally move a
  *control* ZIP into the *treated* group? (In an experiment, you cannot let your
  control group get treated. That ruins the comparison.)
- **Gate 6 — estimate stability.** Re-run the estimate with and without the
  write. If the answer moves more than a pre-agreed amount, **stop and ask a
  human** — no matter what the settings say.

**Why this is publishable:** all existing work protects *data integrity* (don't
corrupt rows). Nobody protects *inferential integrity* (don't break the
experiment). That distinction is the contribution.

> **Status: this one is real.** All six gates are implemented and all six run
> against the actual 33,791-ZCTA DuckDB warehouse, writing an audit record on
> every invocation. Gate 5 escalates often, because the donor pool genuinely is
> thin. Note the honest wrinkle: Gate 5 and Gate 6 protect a synthetic-control
> study that has not been built yet (§2), so what they currently guard is the
> *machinery* of the donor pool and the stability check rather than a published
> estimate. The gates work; the thing downstream of them does not exist yet.

---

## 5. Why is expansion a "portfolio" and not a "ranking"?

The natural instinct: score every ZIP, sort the list, take the top 20.

**That's wrong, because ZIPs affect each other.**

> **Example.** ZIP A alone: loses $200k — too few deliveries to justify its
> own station. ZIP B alone: loses $150k — same problem.
>
> But A and B are adjacent. Together they **share one station**, their combined
> delivery density crosses the efficiency threshold, cost per package drops 30%,
> and the pair makes **+$1.1 million**.
>
> A ranking rejects both. It never even evaluates the pair.

Two forces pull in opposite directions: cannibalization makes neighbours worth
*less* together; shared density makes them worth *more*. So you have to choose
**bundles**, not items.

**Honest note for the viva:** this is not our invention. Supply-chain network
design software has done multi-site optimisation for twenty years. We include it
because ranking is simply the *wrong model of the decision* — it's a
correctness fix, not a novelty claim. Say that plainly if asked.

---

## 6. How do we say how confident we are?

Three different tools, because "accuracy" means three different things.

| Question | Tool | Plain meaning | What we measured |
|---|---|---|---|
| Does it rank well? | **AUC** | Pick one ZIP that got service and one that didn't: how often does the model score the right one higher? 0.5 = coin flip, 1.0 = perfect | **0.6894** against a null of 0.5000 |
| Are the probabilities honest? | **Calibration / ECE** | When the model says "3% chance," does it happen ~3% of the time? | **0.00863 against the null's 0.00005 - the null wins by 170x** |
| How wrong could we be? | **Conformal prediction** | Gives a range, and we *verify* the range works | **88.19% empirical against 90% nominal, inside tolerance** |
| Did the estimation help? | **Top-k against a single raw covariate** | Of 38 held-out decisions, how often is the true ZIP in your top 1, 5 or 10? | **The fitted choice model 7 / 16 / 19. A raw warehousing count 8 / 16 / 20. They tie — see Sec. 0.1.** |

The first three rows are the **retired hazard model**. The fourth is the
**fitted choice model**, and it is the one that matters now.

An earlier draft of this file printed "we target 0.84" in this table. That was
a pre-registered target, not a result, and presenting it as one was wrong. The
measured figure is 0.6894. Quote the measured figure.

**Conformal prediction is worth understanding** because it's the strongest thing
you can say:

> Most models say "here's my 90% interval" and you have to trust the model's
> internal assumptions. Conformal prediction lets us check: *we said 90%, and
> when we tested on held-out ZIPs, our intervals actually contained the truth
> **88.19%** of the time - inside the tolerance band computed on the 351
> effective units.*
>
> That's a **measured** guarantee, not an assumed one. And it's about 30 lines of
> code.

> **Three warnings.** First, an earlier draft of this file said 90.2%. That
> figure is wrong and is withdrawn; the artefact says 88.19%. Second, conformal
> coverage holding does **not** rescue the model. Conformal wraps whatever you
> give it: if the underlying scores are near-useless, you get honest intervals
> around a useless prediction. Wide-but-honest is better than narrow-and-wrong,
> and it is still not a forecast you would spend $4m on.
>
> Third, and this is the one to volunteer: **on the fitted choice model the
> conformal result is worse, not better.** At alpha 0.10 the empirical coverage
> is 1.000 against a nominal 0.90, and it achieves that by naming a median of
> 38.5 alternatives out of a median choice set of 59.5 — **71% of the metro**.
> Perfect coverage obtained by nearly refusing to exclude anything is not a
> success, and the 88.19% figure above, which is the *retired* model's, is
> actually the better-looking of the two. Sec. 0.1b has the full table.

### And the one an executive actually wants: rank stability

The real question is not "what's your error rate" but **"if you're a bit wrong,
does your recommendation change?"**

> **Example — ILLUSTRATIVE, NOT MEASURED.** We run the whole simulation many
> times with slightly different assumptions. ZIP 94608 lands in the top ten in
> **87%** of runs — that's a solid recommendation. ZIP 94612 lands in the top
> ten in **34%** of runs — that's a coin flip, don't commit $4M to it.
>
> The 87% and 34% are **made up** to show you the shape of the output. There is
> no per-ZIP rank-stability artefact in this project. Do not quote them.

> **A claim withdrawn — and the correction runs the other way.** This passage
> used to say "the Monte Carlo layer is specified and on the backlog". **That
> is false. The Monte Carlo ran.** 500 of 500 draws, seed `20260914`, in
> `outputs/metrics/montecarlo_report.json` and
> `outputs/tables/montecarlo_draws.parquet`. The earlier text also said
> "10,000 times"; there was never a 10,000-draw run, and Sec. 9 below used to
> claim 24 billion draws, which is also withdrawn.

### What the Monte Carlo actually says

```
                       p10       p50       p90      min     max
   ---------------------------------------------------------------
   activations n       152       264.5     306       82      385
   capital, $bn        0.608     1.058     1.224     0.328   1.540
   breakeven margin    1.0892    1.3682    1.7259
   median $ / parcel   0.8368    1.1224    1.4836
```

Four things to say about it before anyone asks.

- **It is not a confidence interval, and the artefact says so itself.** Every
  range comes from this project's own `PARAMETERS.md`, and **eight** of the
  constants have no external source. It measures how far the answer moves
  across the range *we* consider plausible. It propagates our priors, not the
  world's.
- **`parcels_per_depot_per_day` was not sampled, by oversight.** So every band
  above is a **floor**, not a full accounting of the uncertainty.
- **It vindicates the headline and indicts an older one.** The delivered
  portfolio's 282 activations sit at the **67th percentile** — comfortably
  inside the band. The previously published 330 sits at the **97th** and 317 at
  the **95th**, i.e. outside or at the edge. So the drift in the headline was
  **real**, and the parameters did not cause it. Depot placement did, and depot
  placement is not classified as a parameter.
- **The three "capital" figures were never three financial results.**
  `capital_usd` is exactly $4m x n in all 500 draws, so $1.128bn, $1.268bn and
  $1.320bn are the three activation counts (282, 317, 330) restated in dollars.
  Presenting them as three findings would be presenting one number three times.

The top variance driver in `n` is `cannibalisation_peak` — rank correlation
-0.622, **44.3%** of the variance — followed by `cannibalisation_radius_km` at
6.9% and `parcels_per_stop` at 5.0%. That is uncomfortable, because
`cannibalisation_peak` is the assumed 0.18 from Sec. 2 that nobody estimated.
**The single largest source of uncertainty in the portfolio is a number
somebody typed.**

---

## 7. Who is this actually for?

The weakest possible answer is "Amazon's competitors." Here are the real ones.

**Cities deciding on tax breaks.** A council is asked for a $2M abatement to
attract a facility. The question they cannot currently answer: *would the company
have built here anyway?* If yes, the abatement is a gift. **A selection model's
propensity score IS that answer** — same output, read backwards.

> **But not ours, not yet.** That argument only works if the propensity score is
> trustworthy, and ours is not (§0.1): worse calibrated than a constant, and a
> probability is exactly what an abatement argument needs. Nor does the fitted
> choice model rescue it — its conformal sets name 71% of the metro at the 90%
> level (§0.1b), which answers "would they have built here anyway" with "very
> possibly, along with two thirds of the county". The *use case* survives - it
> is the reason to keep going - the *instrument* does not. Say "this is what a
> working model would be for", never "this is what our model does for you".

**Air-quality districts.** South Coast AQMD's Rule 2305 (EPA-approved) requires
large warehouses to offset emissions or pay. Districts need to forecast where
warehouses will appear to plan capacity.

**Community and environmental-justice groups.** They need to know where the
burden lands **before** the permit is filed, not after. We overlay predicted
expansion on EPA EJScreen by demographic group — a map that does not
currently exist publicly.

**Researchers.** The open panel + harness lets others test better methods
against our baseline.

> **The line to remember:** *"Proprietary data produces conclusions nobody can
> check. Public data produces conclusions anyone can check. For a decision
> communities have legal standing to contest, checkability is the product."*

---

## 8. Isn't public data too weak?

Turn it into the research question:

> **How much of a trillion-dollar company's siting behaviour is visible from
> public data alone?**

- If the answer is **70%** → that's a finding about transparency.
- If the answer is **40%** → that's a finding about opacity, and it tells
  regulators exactly how much disclosure would close the gap.

**You cannot lose.** Nobody has published this number.

### And we now have a partial answer, which is the uncomfortable kind

The honest version of the finding is not a percentage. It is this:

> *"Public data got us 43 dated delivery stations in ten metros, out of
> 5,200,011 federal OSHA inspection records, after five other sourcing methods
> failed outright. Those 43 dates are upper bounds, not opening dates. That is
> enough to price a network and to optimise a portfolio. It is not enough to
> identify a siting policy - 7.6 events per parameter against a floor of 10."*

That is still a finding about opacity, and it is a sharper one than "40%",
because it names the precise thing that is missing: **not covariates, but
dated decisions.** Every demographic input we could want is free and public.
The one variable that is not public is the one the model needed.

Do not dress this up. "You cannot lose" was written before the model was
fitted; the bet paid out on the side nobody hopes for.

### 8.1 Two more attempts to fix the dates. One failed outright; one was wasted.

Neither of these appeared in any defence document before now, which is itself a
problem worth owning. Both are disclosed here.

**Satellite dating — attempted 2026-09-14, and it failed.** The idea was a good
one: OSHA gives an *upper* bound on an opening date, and Sentinel-2 imagery
should give a *lower* bound, so upper plus lower is an interval the statistics
could actually use. The script is
`data/collection/satellite/colab_date_from_satellite.py` and it ran in Google
Colab. The source artefact is `satellite_dates.csv`, which sits **outside this
repository** — say so when you cite it.

```
   107 of 107   sites got an estimate; median 106 cloud-free scenes
   41%          of the 83 sites with a known year came within 1 year
   3.42 years   standard deviation of the error
   36%          THE TEST THAT KILLS IT: 39 of the 107 estimates are
                LOGICALLY IMPOSSIBLE - they date construction AFTER
                the day an OSHA inspector physically found the
                building operating. Median 33 months after.
```

You cannot filter your way out of it: 35% are impossible at a confidence score
above 2, against 30% at confidence 1-2, so the confidence score does not
discriminate at all. The cause is the changepoint detector, not the imagery.
**Report this as a negative result and stop there.** Do not offer the 68
surviving estimates as dates — they are the residue of a procedure that is
demonstrably wrong a third of the time, and nothing distinguishes them.

**The labelling programme — finished, and mostly wasted.** 362 sites were
hand-labelled across six batches, yielding 135 delivery stations, of which
**thirteen** were genuinely new to the delivered facility frames.

The reason is a bug and it should be stated as one. **289 of the 362 worklist
rows — 80% — were already classified** in
`data/collection/results/NATIONAL_CLASSIFIED.csv`.
`scripts/make_unlabelled_batches.py` selected rows the OSHA name regex could not
classify, and never checked them against `NATIONAL_CLASSIFIED.csv`. It compared
against the wrong reference. That cost four evenings of manual labelling.

**And there is a real recoverable half, which has to be said second, not
first.** The non-new remainder — 122 rows — are *independent confirmations* of
classifications the pipeline had already made, each from a different source,
each with a quote and a URL. That is an **accidental validation set** for the
name-based classifier in `ingest/osha.py`: exactly the kind of evidence
reviewers ask for and student projects almost never hold. It was produced by
accident rather than by design, and both halves of that sentence belong in the
answer.

### 8.2 Four more open defects, named before anyone finds them

- **The CBP lag guard is nominal.** An Amazon delivery station *is* a
  warehousing establishment, so a contemporaneous CBP count would contain its
  own outcome. `ingest/cbp_detail.py` guards against this by scoring each
  facility on the latest CBP vintage **strictly earlier** than its recorded
  `open_year`. But `open_year` is not an opening date: on all 100 loaded
  national rows, `open_year` and `open_quarter` equal the quarter of the
  **earliest OSHA inspection** — the "operating by" upper bound, restated. A
  building first inspected in 2022 may have opened in 2017, in which case the
  "strictly earlier" 2021 vintage already counts the facility itself. Of the
  five pilot addresses with an independently known opening month, the lags to
  first inspection are 4, 13, 57, 69 and 345 months — **three of five exceed
  twelve months**. The guard's margin is zero or negative. This undercuts the
  warehousing covariate, which is precisely the headline predictor in Sec. 0.1b.
- **`optimize/objective.py` prices an activation three inconsistent ways** — at
  `:81-83` a ZCTA, at `:164` a facility, at `:158` a facility with a catchment —
  amounting to roughly a **2.74x capital overcharge**. It is the *same
  unit-of-analysis error that killed the hazard model*, in a second component.
  Concede the pattern, not just the bug.
- **Two cost-model holes.** 42% of depots exceed 40,000 parcels/day, so line
  haul is a **lower** bound. And `rent_index` is missing in at least one quarter
for **94.3%** of ZCTAs — 88.8% of ZCTA-quarter rows are null and 80.5% of ZCTAs
have no value in any quarter, so always name the denominator —
  with the observed stratum **63.6x denser** than the missing one, and it is
  still listwise-deleted at `src/siting_atlas/cost/runner.py:166`.
- **Nothing is geocoded.** 0 of 104 national and 0 of 43 pilot facilities have
  latitude and longitude; both are null on every row. Coordinates are filled
  from ZCTA centroids, and **every distance quantity in the project inherits
  that**, including the 15-mile catchment that drives the whole clustering
  diagnosis.

### 8.3 How much of the network can OSHA see? We measured it.

`outputs/metrics/nlrb_coverage.json` answers the "isn't public data too weak"
question with a number rather than a shrug. Treating OSHA and NLRB as two
independent attempts to observe the same population of US cities containing an
Amazon facility — a capture-recapture design — OSHA sees **at most 54%** of
them under the Chapman estimator, and **37.8%** under the Chao lower-bound
estimator. A three-list log-linear model over ten states puts the population at
**314 to 417** cities, the range depending on which pairwise dependence terms
the specification allows.

The important methodological point, and the one to volunteer: the **dependence
between the lists is measured, not assumed**. Both OSHA and NLRB records are
generated by worker grievance, so presence on one raises the chance of presence
on the other. That positive dependence inflates the overlap, which deflates the
population estimate — which is why every population figure here is a lower
bound and every coverage figure an upper bound. The artefact states this in its
own `direction_of_bias` field.

For completeness on the other public source people always suggest: **SEC filings
disclose no facility locations and no dates.** "Delivery station" appears four
times in all of Amazon's filings, and Item 2 gives aggregate square footage
only. That is a measured negative and worth thirty seconds in the room.

---

## 9. Isn't a fourteen-megabyte panel too small to be impressive?

File size is the only axis where this is small. Don't lead with it.

```
   2,413 pilot ZIP codes  x  $3-5M per activation
   =  $7.2 BILLION - $12.1 BILLION of capital allocation in scope
```

Plus: a portfolio search space of 2^2,413; fourteen registered data sources,
thirteen analytical, at eight different geographic grains; and a panel that
already covers all 33,791 US ZCTAs — 1,081,312 rows, which is a million rows in
fourteen megabytes because quarterly demographics compress extremely well.

> **A claim withdrawn.** This paragraph used to open with "**24 billion** Monte
> Carlo simulation draws". That is false and there is no artefact behind it. The
> Monte Carlo that exists ran **500** draws (`montecarlo_report.json`, seed
> `20260914`). There was never a 24-billion-draw run and never a 10,000-draw NPV
> run. A fabricated compute figure is the easiest thing in this pack for an
> examiner to disprove, so the number is gone rather than adjusted.

If a reader has seen an older draft quoting $15.6–26B over 5,200 ZCTAs, say
where the change came from: the ZCTA count was estimated, the OMB 2023
delineation gives 2,413, and `report/scope.py` now derives the figure so it
cannot drift again. The smaller number is the defensible one.

> **The senior-sounding sentence:** *"I deliberately kept the panel small. The
> hard problem is identification, not throughput — I'd rather spend the compute
> propagating uncertainty through the portfolio than on scanning rows I don't
> need."* Do not attach a draw count to that sentence unless it is 500, which is
> what the artefact records.

Never claim it's big data. If someone probes for thirty seconds it collapses, and
you go from "honest engineer" to "inflates claims."

---

## 10. The three sentences that carry the whole defense

1. **On novelty:** *"Houde, Newberry and Seim did this in Econometrica for the
   fulfilment-and-sortation network on data purchased from MWPVL - demand at
   county grain, supply at a 20-mile cluster. We do delivery stations, which
   their paper never mentions, at ZCTA grain, on free federal OSHA records
   anyone can re-download."*

   **The correction to memorise.** An earlier draft of this sentence said Houde
   et al. worked "at state grain". That is wrong. **State is the unit of the
   *tax* variation they exploit, not the unit of their analysis.** Their demand
   side is county and their supply side is a 20-mile cluster. If you say "state
   grain" in a viva to someone who has read the paper, you lose the room. The
   evidence for every clause above is in `../METHODS_RESEARCH.md` Sec. 4 -
   including the grep showing "delivery station" returns **zero** hits in their
   published text.

   Three axes, and only three: **facility type** (delivery stations, unstudied
   in either paper), **data provenance** (free and reproducible versus
   purchased), and **question** (who gets served and can a city verify it,
   versus nexus tax policy and economies of density). **We do not claim a new
   estimator.** Say that unprompted.

2. **On accuracy:** *"We trained on the real panel, scored on held-out data, and
   the hazard model failed: AUC 0.6894, calibration 170 times worse than a
   constant, negative skill on both hold-outs, 7.6 events per parameter against
   a floor of 10. The diagnosis is that the unit of analysis was wrong - one
   station switches on a median of 58 ZCTAs at once, so the observations are not
   independent, which is the assumption Train's likelihood rests on at Sec.
   3.7.1. We then built the successor choice model and fitted it, and on 38
   held-out decisions a single raw Census warehousing count matches it - 8
   top-1 against 7, 20 top-10 against 19 on that split, and dead level over
   fifty re-splits. The estimation buys nothing measurable.
   Those are results with measurements behind them, and I would rather report
   them than a number I cannot defend."*

   **Why this is the right sentence to give.** "43 buildings, dated as OSHA
   upper bounds, cannot identify a siting policy" is a finding, and "a raw
   warehousing count matches my estimator" is a sharper one. "Our model achieves
   AUC 0.69" is a press release. Examiners can tell the difference, and the
   first two are much harder to attack.

   **Do not say "mutually exclusive" here.** An earlier draft of this sentence
   attributed the failure to Train Sec. 2.2 and mutual exclusivity. Wrong
   section, and a reader of Train will know that Train calls that criterion
   "not restrictive" and supplies a two-line repair. See Sec. 0.1.

   > **Updated 2026-09-15 — sentence 2 now has a stronger ending and you
   > should use it.** The version above stops at the choice model, and its
   > implicit concession is "on a small sample". That concession is no longer
   > available, because the sample grew and nothing changed. Add:
   >
   > *"Since then I have done three more things to that finding. I revived
   > the hazard model on 5,441 events instead of 812, with stated opening
   > dates instead of inspection bounds, and it scored 0.6832 and lost
   > calibration to a constant 17 times out of 17. I expanded the facility
   > panel from 104 rows to 693 and refitted; the coefficient interval got
   > 64% narrower, still covers the numeraire, and the point estimate moved
   > towards it. And I pre-registered a metro-level model — sample,
   > baselines, metric and criterion written to disk before the fit, md5
   > recorded — and it lost to ranking metros by household count in 7 of 7
   > held-out years. So the sample-size explanation is measured and dead. The
   > ceiling is the data, and I can now name the mechanism: a conditional
   > choice model can only use covariates that vary within a metro and are
   > not proxies for population, and most free public data is one or the
   > other."*
   >
   > Also update the arithmetic inside the old sentence: the median
   > catchment is **58 ZCTAs on the pilot frame and 39 on the expanded
   > one**, and the reason the smaller number is *worse* news is in Sec.
   > 0.1c. Say which frame you mean.

3. **On public data:** *"Air districts under Rule 2305, city councils facing
   abatement requests, and communities filing comments all need this forecast
   and none of them can buy it. Checkability is the product."*

---

## Where to go next

- **`../STATUS.md`** - one page, five minutes, every headline figure
  re-derived from an artefact. **Read it first if you only read one file.**

> **The tie-break rule, corrected.** This section used to say: where this
> explainer and `STATUS.md` disagree, believe `STATUS.md`. That was wrong,
> because a prose summary can go stale just as easily as this file can, and at
> the time of writing `STATUS.md` had. **Where any two documents in this pack
> disagree, believe the artefact in `outputs/metrics/`, and quote its `run_id`.**
> The ones that carry the headline figures are `choice_report.json`,
> `hazard_report.json` (run `20260914-002509-2374`), `cost_report.json` (run
> `20260914-002418-0623`), `portfolio_report.json` (run `20260914-002431-7419`)
> and `montecarlo_report.json`. A run id is the only thing in this pack that
> cannot quietly go out of date.
- **`../METHODS_RESEARCH.md`** — Sec. 4 is the provenance and novelty evidence;
  Sec. 5.1 is the diagnosis of why the siting model failed
- **`../data/FACILITY_PANEL_PROVENANCE.md`** — the five sourcing methods that
  failed, the sixth that worked, and every way the target is weak
- **`VIVA_QA.md`** — the anticipated questions with answers, including the
  hostile ones. It is still being added to, so no count is given here; open the
  file if you want one.
- **`GLOSSARY.md`** — every technical term, defined with an example
- **`../ROADMAP.md`** — what gets built when
- **`../engineering/DATA_ENGINEERING.md`** — why this runs on a laptop
