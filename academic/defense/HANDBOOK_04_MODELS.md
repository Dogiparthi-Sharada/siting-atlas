# Handbook Part 4 — The Models and What "Accuracy" Means

**A fitted choice model, a retired hazard model, and the four different things
people mean when they say a model is accurate.**

> **READ THIS BEFORE ANYTHING ELSE IN PART 4.**
>
> This project has had two siting models and **neither one succeeded**. Say
> that first, in that order, before any mitigation.
>
> **The current one** is the conditional ZCTA choice model in Sec. 4.0. It is
> fitted, it converged, and on held-out data it is **matched by a single raw
> Census count with nothing estimated from it**: warehousing establishments
> per ZCTA takes 8 of 38 first places against the fitted model's 7, a gap that
> washes out entirely once you re-split (Sec. 4.0). Two of its
> three free parameters sit on the boundary at `exp(-35)`. It carries **no
> standard errors and no intervals at all**. Its conformal prediction sets
> reach their nominal coverage by naming 71% of the metro.
>
> **The retired one** is the discrete-time hazard model in Sec. 4.1. It was
> built, it was fitted on the real delivered panel, and **it failed**. It
> scored AUC 0.6894 against a coin-flip null of 0.5000, it beat that null on
> Brier score by 0.00471, and it is roughly **170 times worse calibrated**
> than a model that says the same number every time. On a held-out future and
> on held-out metros it scored **worse than doing nothing**. It is kept in
> full here because its diagnosis is the most valuable thing the project
> produced, and because the same unit-of-analysis error turns up a second time
> in the portfolio optimiser (Part 5).
>
> The rest of this part still teaches you what a hazard is, what AUC, Brier,
> ECE, calibration and conformal prediction mean, because you need that
> vocabulary to understand both failures. But every target in this document
> that is phrased as an aspiration ("target 0.84", "target precision@100
> >= 0.60") is a *pre-registration*, not a result.
>
> **On the numbering.** Sec. 4.1 onwards keeps the numbers it has always had,
> because `HANDBOOK_02_DATA.md` and `HANDBOOK_06_AGENT.md` cite Sec. 4.1, 4.5,
> 4.9 and 4.10 by number and this file cannot renumber them. The current model
> therefore leads as **Sec. 4.0**: first in reading order, and no cross-
> reference broken.
>
> ---
>
> ## UPDATED 2026-09-15 — THERE ARE NOW THREE, AND TWO STATEMENTS ABOVE ARE WRONG
>
> **Correction 1. "It carries no standard errors and no intervals at all" is
> false.** Both landed on 2026-09-14, and what they say is not good news: the
> 95% sandwich interval on the only interior parameter is **[0.734, 2.835]
> against a null of 1.0** (households is the numeraire, so the null is one and
> not zero), at p = 0.287, with both bootstraps and the BCa agreeing. On the
> 483-decision expanded panel the interval narrows 64% to **[0.956, 1.490]**
> and still covers 1.0, with the point estimate moved *towards* the numeraire.
> Say "the intervals exist and they cover the null", not "there are no
> intervals".
>
> **Correction 2. "Two siting models" is now three, and the third is the most
> defensible negative result in the project because it was pre-registered.**
>
> ```
>   A METRO-LEVEL ENTRY MODEL.  Registered in docs/PREREG_METRO_MODEL.md
>   before any fit -- sample, covariates, three baselines, metric, success
>   criterion and BOTH outcomes' language written in advance.  The artefact
>   outputs/metrics/metro_entry.json records the prereg's path and its md5
>   (946f7ef75db69e5278eea409a04c3823) so the registered document can be
>   checked against the one on disk.
>
>     clause 1  AUC > "rank metros by households"       0 of 7 years
>     clause 2  ECE <= a constant null                  3 of 7 years
>     pooled    model 0.7323 | households 0.8949 | facilities-open 0.7325
>     bootstrap model minus households  -0.1628 [-0.2011, -0.1313]
>               2,000 draws over 935 CBSA clusters
>     re-splits mean -0.175, losing 50 of 50
>     VERDICT   H0, under logistic, Poisson AND negative binomial
> ```
>
> Two details that make it worth more than "a third failure". A
> *zero-parameter column of integers* — the count of facilities already open
> in the metro — scores 0.7325 against the fitted model's 0.7323 on the same
> 6,545 rows. And the pooled 0.7323 is **higher than the model's AUC in every
> individual size tier** (0.4125 / 0.5666 / 0.6961), which is Simpson's
> paradox in textbook form and is reported by the run rather than found by a
> reader.
>
> **Correction 3. The hazard model in Sec. 4.1 was revived and failed
> again.** 5,441 events instead of 812, stated opening dates instead of
> inspection bounds, effective events per parameter 5.6 → 87.2. AUC 0.6894 →
> **0.6832**, and calibration beaten by a constant in **0 of 17** comparisons
> (`hazard_revival.json`). The independence violation is untouched: one
> opening still switches on a median 39 ZCTAs, and no radius between 8.3 and
> 45 miles brings that below 14.
>
> **What this does to the framing of Part 4.** The old framing was "two models
> failed, probably because the sample is small". That explanation is now
> measured and dead — the sample was quintupled, the events went up 6.7x, a
> flexible learner was tried, and the grain was changed. Read every
> "under-powered" in this document as **"tested, and power was not the
> problem"**.

---

## 4.0 The fitted choice model — the model this project ships now

> **The result first.** The model is fitted and it does not earn its keep. On
> 38 held-out decisions a single raw Census County Business Patterns count --
> warehousing establishments per ZCTA, with **nothing fitted from it at all**
> -- **matches** the three-parameter fitted model: one hit ahead at top-1, one
> ahead at top-10, level at top-5 on this seed, and level over fifty
> re-splits. The estimation buys nothing measurable.

> **Corrected 2026-09-14, and it does not let the model off.** This section,
> the Part 4 banner above it and the self-check in Sec. 4.11 all used to say
> the raw count **beats** the fitted model, and Sec. 4.11 went so far as to
> mark an answer wrong if it omitted the word "beaten". That instruction is
> now reversed, because the word was an error and not merely out of date. It
> rested on one seeded 56/38 split — the table in "Held out" below. Across
> fifty paired re-splits of the same 94 decisions the raw count's margin is
> **+0.36 hits out of 38, paired sd 1.14**, and the raw count *loses* 11 of
> the 50 (`outputs/metrics/gbm_benchmark.json`, key
> `across_repeats.conditional_logit`: `top10_mean` 20.96 for the raw count
> against 20.6 for the logit). A third of a decision is a tie, and calling it
> a defeat read sampling noise as a result — the same sin as calling it a
> victory, only self-directed. Every single-split figure quoted in Sec. 4.0 is
> still correct for its seed, and the finding is untouched: estimating three
> parameters buys **no** ranking improvement over counting warehouses.

### What it asks

Given that one delivery station opens in metro `m`, **which ZCTA of `m` is it
sited in?** One opening, one decision maker, one term in the likelihood. That
is the reframe the hazard model's failure pointed to (Sec. 4.1), and building
it is how the project acted on its own diagnosis.

### The functional form is forced, not chosen

Zone boundaries are the Census Bureau's arbitrary choice, not Amazon's. A
model that changes its answer when two adjacent ZCTAs are merged is measuring
the Census. Invariance to a merger requires `exp(V_j)` to add across the
merged zones, which holds when `V_j = ln(beta' a_j)`:

```
                       beta' a_j
   P(j | m)  =  ----------------------
                 sum_k  beta' a_k
```

So the probability a ZCTA is chosen is just **its share of the metro's total
attraction**, and the exponentials cancel out of the logit entirely. The
attraction variables must be *extensive* -- counts that genuinely add.
Households, land area, establishments and warehousing establishments qualify.
Medians, rates and densities do not, because the median income of two merged
ZIPs is not the sum of the two medians.

Two consequences follow that the specification did not anticipate.

1. **Only ratios are identified.** Multiplying every coefficient by `c` leaves
   every probability unchanged, so one coefficient has to be normalised.
   Households is fixed at 1, and the others read as "worth this many
   households".
2. **`beta' a` must be positive** for every alternative, or the probability is
   undefined. The implementation sets `beta = exp(theta)`, which enforces it
   and restricts every variable to be weakly *attractive*. A variable that
   genuinely repels cannot be expressed in this specification. That is a real
   restriction, and it is why the coefficient table below reads the way it
   does.

### The fit

Every number here is from `outputs/metrics/choice_report.json`, frame
`national`, seed `20260914`.

```
   decisions total                  94
   train / held out             56 / 38
   free parameters                   3   (households fixed as numeraire)
   converged                       yes
   log-likelihood             -203.4497
   log-likelihood, uniform    -253.3351
   McFadden rho-squared         0.19691   in sample, on the 56
```

**The coefficients, and why two of them are not really there:**

```
   attraction                    beta       theta    reading
   -----------------------------------------------------------------
   households                  1.0          --       numeraire, fixed
   warehousing_establishments  1.4428      +0.367    the only live term
   land_area_sqmi              3.04e-16   -35.73     AT THE BOUNDARY
   establishments              4.72e-16   -35.29     AT THE BOUNDARY
   -----------------------------------------------------------------
```

`exp(-35.73)` is not a small effect. It is the optimiser walking a parameter
down to the floor that `beta = exp(theta)` gives it, because the only way this
specification can say "this variable does not help" is to say "this variable
weighs nothing". **One of three free parameters is doing any work.**

### Held out: the benchmark draws level

38 decisions, 3,998 alternatives. Every row below is scored on the same
held-out decisions.

```
   predictor                       top-1   top-5   top-10     Brier
   --------------------------------------------------------------------
   the fitted model                 7/38   16/38    19/38   0.008724
   warehousing count ALONE          8/38   16/38    20/38   0.008951
   households alone                 1/38    5/38    10/38   0.009271
   establishments alone             0/38    8/38     9/38   0.009307
   land area alone                  0/38    3/38     6/38   0.009816
   uniform within metro             1/38    3/38     7/38   0.009316
   --------------------------------------------------------------------
```

Read row two against row one and say the true thing: **the raw count draws
level.** On this seed it is one ahead at top-1, 8 against 7, one ahead at
top-10, 20 against 19, and level at top-5; over fifty re-splits the average
gap is a third of a decision, which is no gap. It has no fitted parameter in
it at all; it is a column you can download from County Business Patterns, and
it does everything three estimated parameters do.

The fitted model is ahead on raw Brier, 0.008724 against 0.008951. **Do not
lean on that.** It is a gap of 0.00023 on 38 decisions, nothing that thin
survives a sample that small, and the project ships no interval that could
say otherwise (see below).

> **The one-line version for a viva.** *"We fitted three parameters and did no
> better than the one variable we did not fit."*

> **What the exercise is still evidence of.** It says something, just not what
> was hoped. Warehousing establishments carrying the entire model on their
> own is a finding about **agglomeration**: Amazon sites where logistics real
> estate already is. And both rows beat uniform-within-metro by a wide margin,
> 7 or 8 first places against 1, so the internal geography of a metro is not
> random. What is *not* supported is any claim that this estimation procedure
> extracted something a download could not.

### The standard errors landed late, and they cover the null

`docs/MODEL_SPEC.md` §6.3 prescribes two uncertainty calculations, side by
side: a robust sandwich covariance, and a nonparametric bootstrap over
*decisions*, reported as percentile intervals.

> **A statement withdrawn, 2026-09-14.** This section used to open "There are
> no standard errors, and that is the largest hole", and it listed the keys of
> `choice_report.json` to prove the artefact carried no uncertainty block. That
> was true for most of the day and is no longer. An `inference` key now sits
> beside the others and `models/choice_runner.py` calls
> `choice_inference.summarise` to build it. The correction is recorded rather
> than swallowed, because the shape of the finding changed with it: the gap was
> a missing calculation, and what the calculation says is a fourth negative
> result.

**The null here is `beta = 1`, not `beta = 0`.** Households is fixed at 1 as
the numeraire because the model is scale-invariant and only *ratios* of
coefficients are identified, so every interval below is an interval on "how
many households one unit of this covariate is worth". A reader who imports the
usual "does it cover zero" habit reads the table backwards.

```
  56 training decisions across 38 metros, alpha 0.05
  1,000 bootstrap replicates over decisions, 1,500 over metros, converged

  warehousing_establishments, beta = 1.4428  -- the only interior parameter
    sandwich, 95%                  [0.734,  2.835]
      se on log beta                       0.345
      z against the ratio 1                1.064     p = 0.287
    bootstrap over decisions       [0.760,  4.762]   11.8% below 1
    bootstrap over metros          [0.702, 10.013]   13.4% below 1
    BCa                            [0.714,  3.522]
    ALL FOUR INTERVALS COVER 1.0.

  land_area_sqmi       beta = 3.0e-16   AT THE BOUNDARY
  establishments       beta = 4.7e-16   AT THE BOUNDARY
    sandwich REFUSED for both, and the refusal is correct behaviour
    one-sided bootstrap instead; upper endpoints
      land_area       0.165 (decisions)  /  0.228 (metros)
      establishments  0.765 (decisions)  /  1.238 (metros)
    about 80% of replicates sit at the boundary in each case
```

**Read it three ways.**

*It confirms a pre-registration.* ADR-0004's residual-risk section, written
before any of this ran, predicted "wide bootstrap intervals covering zero on
every coefficient" and named the bootstrap as the diagnostic that would show
it. The diagnostic ran and the prediction held against the correct null. A
project that predicts its own null result and then measures it is in a better
position than one that merely fails.

*It agrees with the ranking null result rather than adding a separate one.* A
coefficient you cannot distinguish from the numeraire is exactly the
coefficient you would expect to add nothing over a raw count.

*The resampling unit matters more than the specification allowed for.* The
decision-level and metro-level bootstraps differ by a factor of two on the
upper endpoint, 4.76 against 10.01, because seven of the 100 loaded facilities
share the Los Angeles choice set. The metro-clustered figure is the
conservative one and is the one to quote. §6.3 is silent on which, and should
not be.

**A currency note.** The `inference` block landed on 2026-09-14 and was
uncommitted at the time of writing, as were `choice_inference.py`,
`choice_sandwich.py`, `choice_bootstrap.py` and
`tests/unit/test_choice_inference.py`. Re-read the artefact before quoting any
figure above; an examiner running `git status` will see them in the untracked
or modified list.

A coefficient without an interval, at 56 training decisions, is not a result --
and Train's own precondition for the bootstrap fails here in any case (§8.6,
p. 202: "if this sample is large enough"). At 56 decisions these intervals
measure how far the estimate moves with *which of our 56* are included. That is
a real quantity. It is not sampling variability over the population of siting
decisions, and the artefact carries that quotation.
There is a second-order point that has to travel with that concession, because
a reader who knows the theory will make it for you if you do not:

> **A standard error on the two boundary parameters would not be wide -- it
> would be meaningless.** The sandwich estimator's asymptotics assume an
> *interior* maximum, at which the gradient vanishes. `theta = -35.73` is not
> an interior maximum; it is a corner. The usual formula does not merely
> widen there, it does not apply at all. So the correct statement is not "we
> should have reported wide intervals on all three". It is "we should have
> reported an interval on the one live parameter, and said out loud that the
> other two are at a bound where the standard machinery has nothing to say."

### The conformal sets cover by being nearly vacuous

Split conformal was run on the choice model as well; Sec. 4.6 explains the
method. It is calibrated on 23 decisions and tested on 24, in metros where the
median choice set holds 59.5 alternatives.

```
   alpha   nominal   empirical    median     median share of
                      coverage   set size    the choice set
   --------------------------------------------------------------
   0.10      90%       100.0%       38.5          71.4%
   0.20      80%        95.8%       34.0          61.7%
   0.30      70%        83.3%       18.5          34.0%
   --------------------------------------------------------------
```

**Over-coverage is not a pass.** At the 90% level the procedure attains 100%
coverage by naming 38.5 of 59.5 ZCTAs -- **71% of the metro**. A prediction
set holding seven ZIPs in every ten is not telling a planner anything a map
could not. Compare it honestly with the retired hazard model's 88.19% against
a 90% nominal target (Sec. 4.6.3): that one *undershot*, and it is the
better-behaved of the two, because it was at least sharp enough to be capable
of missing.

Only the `alpha = 0.30` row is doing recognisable work, and it over-covers
too: a set of 18.5 out of 59.5, a third of the metro, covering 83.3% of the
time against a 70% target.

> **A claim withdrawn.** Earlier drafts of this handbook presented conformal
> coverage as the project's single strongest result, without qualification.
> That remains defensible for the hazard model *with its tolerance attached*
> (Sec. 4.6.3). It is **not** defensible for the choice model. Coverage
> without sharpness is arithmetic, not evidence, and 24 test decisions cannot
> distinguish 100% coverage from 90% in any case.

### What Sec. 4.0 obliges you to say out loud

```
   IF ASKED                         SAY THIS FIRST
   ----------------------------     -----------------------------------------
   "Is the choice model better      No. It is matched on held-out top-1 by
    than the hazard model?"         a raw Census count. It is better POSED
                                    than the hazard model -- one decision,
                                    one likelihood term -- which is a
                                    different claim, and it is the one I
                                    defend.

   "What is your rho-squared?"      0.19691, in sample, on 56 decisions, with
                                    no interval attached to it.

   "Are the coefficients            No. Two of the three are at exp(-35), on
    significant?"                   a bound, where a sandwich SE is undefined
                                    and is correctly refused. The third has a
                                    95% interval of [0.734, 2.835] against a
                                    null of 1.0 -- households is the numeraire,
                                    so the null is 1, not 0 -- at p = 0.287.
                                    It covers the null.
```

---

## 4.1 The retired hazard model, and what it taught us

> **RETIRED / SUPERSEDED.** This model is no longer the project's siting
> model; Sec. 4.0 is. The section is kept in full, at its original number, for
> three reasons: the numbers in it are real and must stay on the record, the
> diagnosis in it is the most transferable thing the project produced, and
> `HANDBOOK_02_DATA.md` cites "Sec. 4.1" for exactly this content.
>
> Every metric below is from `outputs/metrics/hazard_report.json`, current run
> id `20260914-002509-2374`.

We predict two things at once: **whether** a ZIP gets same-day service, and
**when**. A plain classifier answers only the first.

### The idea

A **discrete-time hazard model** asks, for each ZIP in each quarter:

> *Given that this ZIP has not been enabled yet, what is the probability it gets
> enabled this quarter?*

That conditional probability is the **hazard**. Chain the quarterly hazards
together and you get a survival curve — the probability of still being
un-enabled by any future date.

> **Example.** ZIP 85008 in Phoenix. The model outputs quarterly hazards of
> 0.04, 0.06, 0.09, 0.11 over four quarters. The cumulative probability of
> enablement within a year is
> `1 − (0.96 × 0.94 × 0.91 × 0.89) ≈ 27%`.
>
> That is a genuinely different statement from "27% likely" with no time
> attached — and it is what a planner needs.

### Why not just a logistic regression on "ever enabled"?

Three reasons:

1. **Censoring.** A ZIP not yet enabled might be enabled next month. A plain
   classifier labels it "0" — a negative example — which is wrong. Hazard
   models handle this correctly: it contributed un-enabled quarters, and then we
   stopped observing.
2. **Time-varying covariates.** Income, rents and competitor facilities change
   over the panel. A hazard model uses the values *as at that quarter*.
3. **Timing is the deliverable.** "Top decile" is less useful to a planner than
   "60% probability within 18 months."

### The specification

A complementary log-log link (natural for grouped survival data), with metro
random effects and a flexible baseline in time since the nearest node opened.
Fitted by penalised maximum likelihood, seed recorded in the reproducibility
manifest.

As delivered, the fitted model is a cloglog hazard with a linear baseline in
`t` and three covariates -- households, median household income and
establishments -- five parameters in total, standard errors clustered by
CBSA. The risk set holds 1,756 units, 40,358 unit-quarter rows and 812
ZCTA-quarter events.

### What happened when we fitted it: it failed

Everything above is the *argument* for the specification. The specification
was then written, fitted on the real panel, and it did not work. That sentence
belongs here, next to the argument, and not in a later section where a tired
reader might miss it.

Every number in this subsection comes from
`outputs/metrics/hazard_report.json` (current run `20260914-002509-2374`).
Nothing here is simulated; the artefact records `"synthetic": false`.

> **A stale run id corrected.** This paragraph used to cite run
> `20260913-133904-a60e`. That run has been superseded. The **values did not
> change** on the re-run -- only the stamp did -- but a document that quotes a
> run id no longer present in the artefact is a document an examiner can no
> longer check, which is the whole point of stamping them.

```
   PRIMARY RESULT -- unit-clustered hold-out
   test split: 8,044 rows | 161 events | event rate 0.020015 (2.0%)

   metric        our model      null model      what it means
   ---------------------------------------------------------------------
   AUC             0.6894          0.5000       weak but real ranking
   Brier         0.019522        0.019614       skill +0.00471, near nil
   ECE            0.00863         0.00005       the NULL is ~170x better
   ---------------------------------------------------------------------
```

The "null model" here is not a straw man that we designed to lose. It is a
**constant predictor**: it hands every single ZCTA-quarter the same number,
0.02006, which is just the base rate, and it never says anything else. Our
model, with three covariates and a time baseline, buys 0.19 of AUC over that
constant and 0.5% of Brier score, and pays for it with calibration that is two
orders of magnitude worse.

That is the primary split. Here is every other split we ran:

```
   split                        AUC     Brier skill    verdict
   --------------------------------------------------------------------
   unit-clustered (primary)   0.6894      +0.00471     barely beats null
   annual-grain sensitivity   0.6918      +0.01823     barely beats null
   temporal hold-out          0.5551      -0.02091     WORSE than null
   geographic hold-out        0.6168      -0.06184     WORSE than null
   --------------------------------------------------------------------

   negative Brier skill = you would have been better off
                          predicting the base rate for every ZIP
```

Two readings of that table are honest and one is not.

- **Honest.** On the split the model was tuned for, it has a little ranking
  signal and no calibration. On a held-out *future* -- the split that matches
  how the thing would actually be used -- it is worse than nothing.
- **Honest.** The geographic hold-out is Phoenix and Boise, which hold **two
  dated delivery stations between them**. That is a smoke test for gross
  failure, not a test of geographic transfer. Do not quote -0.06184 as
  evidence about transfer; quote it as evidence that we looked.
- **Not honest.** "The primary split beats the null, so the model works."
  A +0.00471 Brier skill with a 170x calibration penalty is not a working
  model. It is a rounding error with a p-value attached.

**The coefficients.** Three covariates, one of them distinguishable from
zero:

```
   term                       hazard ratio    p-value
   ----------------------------------------------------
   households                    1.00005      0.00007
   median_household_income       1.0          0.780
   establishments                1.00015      0.298
   ----------------------------------------------------
```

The one surviving finding is that Amazon builds where the people are. That is
true, it is not in dispute, and nobody needed a survival model to learn it.
Income and business establishments cannot be distinguished from no effect at
all.

**The conformal intervals worked, and that is a separate question.** Empirical
coverage came out at **88.19%** against a 90% nominal target, inside a
two-sigma tolerance of 0.032 computed on 351 effective units. So the
uncertainty machinery is sound. It is honestly quantifying the uncertainty of
a model with nothing to say. A correct error bar around a useless prediction
is still a useless prediction.

**And there was never enough data.** The model has 5 parameters. How many
independent decisions do we have to fit them on?

```
   counting rule                                events   per parameter
   --------------------------------------------------------------------
   nominal   -- ZCTA-quarter events in train      487        97.4
   optimistic -- usable facilities                 38         7.6   <-- verdict
   conservative -- metro-quarter episodes          28         5.6
   --------------------------------------------------------------------
   conventional floor for a survival model                   10.0
                                                    NOT MET even on the
                                                    most generous count
```

The 97.4 figure is the one a careless write-up would report, and it is
meaningless -- for the reason set out in the diagnosis below. The verdict is
taken at 7.6, the most generous *defensible* count, and it still fails.

### Why the ECE number is the single most quotable fact here

Expected Calibration Error measures whether the probabilities are honest. Ours
is 0.00863. The constant predictor's is 0.00005. We are about **170 times
worse calibrated than a model that has no inputs at all.**

That sounds like a paradox until you see why:

> **A constant predictor is almost perfectly calibrated because it never
> sticks its neck out.** Picture a weather forecaster in a town where it rains
> on 2% of days. Every morning she says "2% chance of rain". Over a year she
> is almost exactly right: on the days she said 2%, it rained about 2% of the
> time. Her calibration is flawless. Her usefulness is zero -- she has never
> once told you to take an umbrella today rather than tomorrow.
>
> Our model does stick its neck out. It says 1.1% for some ZCTAs and 4.4% for
> others. Sticking your neck out is the whole point; it is how a model earns
> its keep. But you only get credit for it if the neck-sticking is *right*,
> and ours is not.

The calibration table in the artefact shows exactly where it goes wrong, and
the worst place is the worst possible place:

```
   decile of predicted hazard    predicted    observed    gap
   ------------------------------------------------------------------
   2nd lowest                      1.18%       0.25%     over by 4.7x
   ...
   9th (second highest)            2.96%       4.48%     under
   10th (HIGHEST -- the shortlist) 4.40%       2.86%     over, and it
                                                          REVERSES
   ------------------------------------------------------------------
```

Read the last two rows again. The decile the model is **most confident
about** -- the one a planner would actually build from -- has a *lower*
observed enablement rate than the decile below it. The ranking is not merely
weak at the top; it inverts. Every practical use of this model reads off the
top decile, and the top decile is where it is wrong.

### The diagnosis: a ZCTA-quarter is not an independent observation

The failure is not a tuning problem. You cannot fix it with more covariates, a
spline baseline, or a gradient-boosted benchmark. **The unit of analysis is
wrong**, and the diagnosis is in `docs/METHODS_RESEARCH.md` Sec. 5.1.

Here is the mechanism, in code. In
`src/siting_atlas/warehouse/facilities.py`:

```
   CATCHMENT_MILES = {"DS": 15.0, "SDC": 10.0}
```

When a delivery station opens, **every ZCTA whose centroid falls within 15
straight-line miles of it is marked enabled in that same quarter.** Not
gradually. All at once, by construction.

```
   ONE decision by Amazon             WHAT THE PANEL RECORDS
   ---------------------------        ----------------------------

        +-------------+                 60608   enabled  2021Q2
        |  Amazon     |                 60609   enabled  2021Q2
        |  opens ONE  |  --15 mi-->     60612   enabled  2021Q2
        |  station    |    radius       60616   enabled  2021Q2
        +-------------+                 60623   enabled  2021Q2
                                          ...   (about 53 more)
                                        60644   enabled  2021Q2

          1 real choice        becomes      58 "events"
```

Measured on the delivered panel, the median station covers **58** ZCTAs, the
mean **88**, and the largest **307**. The build log for the delivered panel
records **3,767 facility-ZCTA catchment pairs from 43 last-mile facilities**.

So the sentence "Amazon chose ZIP 60608 in 2021Q2" is not describing a choice.
It is describing one of about 88 simultaneous *consequences* of one choice
that was made about a building somewhere in the middle.

**Why that is fatal rather than merely untidy.** The assumption the panel
breaks is **independence across observations**. Train (2009) Sec. 3.7.1,
printed page 61, states it in the act of building the likelihood:

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> `L(beta) = prod_n prod_i (P_ni)^{y_ni}`."

That product over `n` is only a likelihood if its terms are independent draws.
Ours are not. On the median, 58 of them are the same building seen 58 times
through a 15-mile buffer. The standard name for the failure is **clustering**,
or **pseudo-replication**. It inflates the apparent sample, shrinks every
standard error, and it is exactly why 812 events behave like 38.

> **A citation corrected, and the argument got stronger for it.** Earlier
> drafts of this handbook said the violated requirement was Train Sec. 2.2,
> which asks that alternatives be **mutually exclusive from the decision
> maker's perspective**. That was the wrong section, for two reasons, and an
> examiner holding a copy of Train would have found both.
>
> First, Sec. 2.2 governs **a choice set facing a decision maker**. A hazard
> on area-quarters has no decision maker choosing among those rows, so
> exclusivity is not a property they can have or lack. The criterion does not
> bite, because it was never pointed at this kind of object.
>
> Second, and worse for the rhetoric, Train calls that criterion **"not
> restrictive"**: "Appropriate definition of alternatives can nearly always
> assure that the alternatives are mutually exclusive" (p. 12), and he then
> gives a two-line repair. Citing it meant citing the one requirement the
> textbook says is easy to satisfy, as though it were the fatal one.
>
> The replacement is a **harder** charge, not a softer one, and that is the
> part to say out loud. Exclusivity is a definitional tidiness problem with a
> known fix. Independence across observations is an **information** problem:
> no redefinition of the alternatives can create decisions that were never
> made. Getting the citation wrong had been making our own diagnosis sound
> more fixable than it is.

That is also why the 97.4 events-per-parameter figure above is meaningless.
812 ZCTA-quarter events sound like plenty. They are 38-or-fewer real buildings
wearing 812 costumes. The likelihood counts costumes; the information content
is in the buildings.

> **The one-line version for a viva.** *"We had 812 events and 38 decisions.
> The model was fitted on the 812."*

**The reframe, and it was built.** The question whose observations *are*
independent is: *which ZIP does the station go in, conditional on a station
opening in metro `m` in period `t`?* Each opening then contributes exactly one
term to the log-likelihood, so the count of terms is the count of decisions.
That model now exists: it is **Sec. 4.0**, on a national frame of **94
decisions**, 56 fitted and 38 held out. Read Sec. 4.0 before concluding the
reframe rescued anything. It fixed the unit of analysis and still did no
better than a raw Census count.

**And the obvious escape hatch does not work.** Sampling of alternatives --
Train Sec. 3.7.1 again, this time the unnumbered sub-heading "Estimation on a
Subset of Alternatives", pp. 64-66 -- lets you estimate on a subset of the
choice set without inconsistency. Two reasons it does not rescue us: it is a
**logit-only** result, so it does not survive to a probit or mixed logit; and
the machinery is built on `q(K|i)`, the probability the researcher's own
sampling scheme drew subset `K`, which presupposes you can enumerate the full
set. It solves "there are too many alternatives". Our problem is "we do not
know what the alternatives were". Different problem.

> **Why Sec. 3.7.1 appears twice on this page.** It is a long section. The
> independence statement quoted above is on p. 61, where Train assembles the
> exogenous-sample likelihood; the sampling-of-alternatives material sits
> under an unnumbered sub-heading later in the same section, pp. 64-66. Two
> different results, one section number. Be ready to say which p. you mean.

**When this went wrong.** The ZCTA-quarter unit was introduced in proposal v4
and was never tested against Train's rule. It was adopted because the panel
was already built at that grain, which is a data-availability argument
masquerading as a modelling decision. Train warns about exactly this in the
same section: specification "is governed largely by the goals of the research
and the data that are available", which is a description, not a permission.

### What replaced it: route (A) was chosen and built

> **A claim withdrawn.** This section used to open with the sentence **"No
> successor specification has been chosen."** That is now false. Route (A)
> below -- the conditional logit on the metro choice -- was chosen, written,
> fitted and published as `outputs/metrics/choice_report.json`. It is Sec. 4.0
> of this handbook. The sentence was true when it was written and stopped
> being true when the model was built; it is corrected here rather than
> deleted, because "we said it was open and then we closed it" is the fact an
> examiner should be able to follow.

Three routes were on the table. One has been taken.

```
   (A)  Conditional logit on the metro choice                  <-- BUILT
        Identifies a POINT. Cheap. Requires assuming the firm's
        ex-ante unknowns are our unobservables, iid extreme value --
        an assumption Train himself calls doubtful. Delivered as the
        static conditional logit of Sec. 4.0; the DYNAMIC version
        (Train Sec. 7.7.3) was NOT built.

   (B)  Moment inequalities, Holmes-style                      still open
        Identifies a SET, not a point. No distributional assumption on
        the firm's information. Expensive, unfamiliar, and Holmes needs
        the dates measured without error -- which ours are not.

   (C)  Interval-outcome partial identification                still open
        Molinari Sec. 2.3. The closest fit to data whose dates are
        upper bounds rather than event times, and the route neither
        author named at the outset.
```

The full comparison, including the failure mode of each that you would not
notice, is in `docs/METHODS_RESEARCH.md` Sec. 8. Read it there rather than
here.

**And do not let "we built the successor" be heard as "we fixed it".** Route
(A) repaired the *unit of analysis*, which was the diagnosed defect, and
that repair is real: 94 independent decisions in place of 812 correlated
echoes. It did not produce a model that improves on a raw Census count
(Sec. 4.0).
Those are two separate results and both of them belong in the answer.

One further gap belongs in the same list. The delivered dates are "operating
by" upper bounds, so the specification the data actually calls for is
**interval censoring**, and `docs/STATUS.md` marks it **NOT STARTED**. The
current risk-set builder treats an upper bound as though it were an event
time. Fixing it will not rescue the AUC -- it will make the reported number
correct, which is a different and more important thing. Note that the
successor in Sec. 4.0 **side-steps** this rather than solving it: a choice
model conditions on an opening having happened and never asks *when*, so it
needs the location to be right but not the date. That is a narrowing of the
question, not an answer to it.

---

## 4.2 The secondary models, and why each exists

> **Status note before you read this section. CORRECTED 2026-09-15 — the
> LightGBM half of it is no longer true.**
>
> **ZINB and SHAP are still *specified* here and not delivered**, and 4.2.1
> and 4.2.3 should be read as design rationale that a future author could
> execute. Do not cite any target in them as a result.
>
> **LightGBM IS delivered.** `src/siting_atlas/models/gbm_benchmark.py` and
> `gbm_report.py` exist, LightGBM is a dependency, and the artefact is
> `outputs/metrics/gbm_benchmark.json` (built 2026-09-13). It was built to
> answer one question — *is the choice model held back by the data or by its
> own simple functional form?* — and the answer is the data:
>
> ```
>   over 50 re-splits, 94 decisions, 38 held out
>     conditional choice model    20.60 of 38     best Brier of the three
>     warehouse count, unfitted   20.96 of 38
>     shallow gradient boosting   ~22.2 of 38     worst Brier
>
>   then the sample was quintupled to 483-485 decisions
>     the GBM's edge disappeared entirely:  0.5198 against 0.5196
> ```
>
> **Two warnings that must travel with any GBM number from this project.**
> Quote `across_repeats`, never `headline_split` — the artefact's own
> `headline_split_warning` field explains that the single-split GBM rows move
> by up to 2 of 38 decisions under a 1e-12 perturbation of the attraction
> matrix, about what a parquet float round-trip costs, while the conditional
> logit and the raw count do not move at all in any draw. And that
> instability is **not** fixable with a determinism flag:
> `deterministic=True, force_row_wise=True` was tested against every arm and
> returned bit-identical counts in all eight comparisons, because the call
> was already reproducible on identical input. The sensitivity is to the
> data.
>
> Section 4.2.2 below was written as a design and is now partly a record.
> Where it states an intention, read it as executed; where it states a
> target, it is still a target.

### 4.2.1 ZINB — zero-inflated negative binomial

**The problem it solves.** Count data with far more zeros than a standard model
expects, from **two different mechanisms**:

- **Structural zeros** — units that will *never* produce a positive count
- **Sampling zeros** — units that could, but happened not to this period

> **Example.** Counting fish caught by park visitors. Some visitors *didn't
> fish at all* (structural zero — will always be 0). Others fished and
> caught nothing (sampling zero — could have been 3). One model cannot
> describe both.

ZINB is a mixture: a logistic model for "is this a structural zero?" and a
negative binomial for the count if it isn't. **Negative binomial** rather than
Poisson because Poisson assumes variance equals mean, and real count data is
almost always over-dispersed.

**Its role in this design:** demoted to a secondary, honestly-labelled
specification-recovery exercise (see Part 2 §2.4.5).

> **An assumption that does not survive.** Zero-inflation is often justified
> with "rural areas generate zero same-day demand regardless of income." The June 2025
> announcement of $4bn+ to reach 4,000+ rural communities contradicts that. Zero
> inflation is now framed as a statement about *service availability*, not
> latent demand.

### 4.2.2 LightGBM — the convergent-validity benchmark

**Why have a second model at all?** To answer a specific reviewer question:

> *"Is your result real, or an artefact of your parametric assumptions?"*

A hazard model imposes functional form. A gradient-boosted tree ensemble imposes
almost none. If both rank the same ZIPs highly, the ranking is unlikely to be an
artefact.

> **The test.** Rank ZIPs by each model on held-out metros, take the top decile,
> compute Spearman rank correlation. Target ≥ 0.80, reported with a bootstrap
> confidence interval on the correlation itself.
>
> If it comes out at 0.45, that is not a failure to hide — it is a finding
> that demands a drill-down into which ZIPs disagree and why.

**Why LightGBM over XGBoost:** histogram-based splits handle high-cardinality
categoricals (state FIPS, metro ID) natively, without one-hot expansion.

> **Citation warning.** A common citation error: some sources cite *Chen & Guestrin (2016)* as
> LightGBM. That paper is **XGBoost**. LightGBM is *Ke et al. (2017)*. The error
> appeared twice, in a section arguing LightGBM beats XGBoost. Fixed in this design.

### 4.2.3 SHAP — explaining individual predictions

**SHapley Additive exPlanations** decomposes a single prediction into per-feature
contributions, borrowing the Shapley value from cooperative game theory: *how
much did each feature contribute, averaged over all orders in which features
could be added?*

> **Example output for one ZIP.** "Predicted enablement probability is 0.72.
> Baseline is 0.31. Median income contributes **+0.14**, distance to nearest
> facility **+0.19**, population density **+0.11**, competitor proximity
> **−0.03**."
>
> That is the drilldown card in the application — and the difference
> between a dashboard and a decision tool.

### 4.2.4 The Huff gravity factor

Retail gravity, from Reilly (1931) and Huff (1964): attraction rises with
facility size and falls with distance.

```
                       attractiveness_A / distance_A^β
   pull_A(i)  =  ------------------------------------------
                  Σ_j  attractiveness_j / distance_j^β
```

**Why include it.** Distance to the nearest facility captures first-order
gravity. But demand also depends on how attractive that facility is *relative to
competitors'*. The Huff factor captures relative pull.

**Why β is fixed at 2.0 and not fitted.** Because fitting it invites the
criticism "you tuned your parameter to your data." Fixing it at the canonical
value from the retail-geography literature costs a little fit and buys a lot of
credibility. **This is a good trade and worth stating explicitly.**

---

## 4.3 What "accuracy" actually means — four different questions

The single biggest source of confusion in model evaluation is treating "accuracy"
as one thing. It is at least four.

| Question | Metric family | What it does *not* tell you |
|---|---|---|
| Does it **rank** well? | AUC, PR-AUC | Whether the probabilities are meaningful |
| Are the **probabilities honest**? | Calibration, ECE, Brier | Whether ranking is good |
| How **wrong could I be**? | Conformal intervals | Anything about the point estimate |
| Would the **decision change**? | Rank stability | Anything about statistical fit |

**A model can be excellent at one and terrible at another.** You need all four.

---

## 4.4 Ranking metrics

### 4.4.1 AUC-ROC

**Plain definition:** pick one ZIP that was enabled and one that wasn't, at
random. AUC is the probability the model scored the enabled one higher.

```
   0.50  =  coin flip, no information
   0.6894 = WHAT WE MEASURED  <-- the retired hazard model (Sec. 4.1)
   0.70  =  weak but real
   0.84  =  what we pre-registered, and did not get
   0.95  =  suspicious; check for leakage
```

We pre-registered 0.84 as "strong for a public-data-only model". We measured
**0.6894**. That is not a near miss; it is on the wrong side of "weak but
real". Quote the measurement, never the target.

> **Why we did not target 0.95 in the first place.** With public covariates and
> no internal data, an AUC of 0.95 would suggest something has leaked -- most
> likely a variable that encodes the outcome. Setting an honest target is a
> credibility signal. Missing your own honest target, and saying so, is a
> bigger one.

> **And the deeper point about AUC.** 0.6894 is not zero. There *is* ranking
> signal in the panel. But AUC is a purely ordinal statistic -- it asks only
> whether the enabled ZIP scored higher than the un-enabled one, never by how
> much, and never whether the number attached to it means anything. Section 4.5
> shows the same model's probabilities are worse than a constant's. **A
> respectable-looking AUC next to a catastrophic ECE is the signature of a
> model that has learned a weak correlate and dressed it up as a
> probability.**

### 4.4.2 PR-AUC, and why it would matter here

> **Not computed. Do not cite a PR-AUC for this project.**
> `outputs/metrics/hazard_report.json` reports AUC, Brier, ECE, a ten-bin
> calibration table and conformal coverage. It does not report PR-AUC or
> precision@k. What follows explains the concept, so you can answer a question
> about it, and so a future author knows what to add.

**The problem with AUC when positives are rare.** Only **2.0%** of the
ZCTA-quarters in the test split are enablements (161 events in 8,044 rows);
across the whole panel the `enabled` share is 2.58%. AUC can look flattering
when positives are that rare, because the denominator is stuffed with easy
true negatives that any model gets right.

**Precision-recall AUC** ignores true negatives and focuses on the question a
planner actually has: of the ZIPs you flagged, how many were right?

> **Worked example at our real base rate.** Base rate 2.0%. A model that picks
> at random has an expected PR-AUC of about 0.02 -- the base rate itself.
> So a PR-AUC of 0.10 would be **five times better than random** at
> concentrating true positives near the top, and a PR-AUC of 0.31 would be
> roughly fifteen times better. The multiple is the meaningful statement,
> which is why the base rate must be printed next to the PR-AUC every time.
> An earlier draft of this handbook did the arithmetic at a 6% base rate,
> which was never the rate in this panel.

### 4.4.3 precision@100

> **Also not computed.** A target of >= 0.60 was pre-registered. No value was
> ever produced, so the pre-registered threshold was neither met nor missed;
> it was left unanswered, and that is what should be said out loud.

**Why it is the metric that matches the decision.** Nobody acts on 2,413
ranked ZIPs. They act on a shortlist. So: of our top 100, how many were
actually enabled? It is the most *decision-relevant* ranking metric and the
easiest to explain to a non-technical audience.

**And the reason it would not have flattered us.** Section 4.1 showed that the
highest-decile predictions have a *lower* observed enablement rate (2.86%)
than the decile below them (4.48%). Precision@100 reads straight off the top
of that ranking. A metric computed on the part of the ranking that inverts is
not going to save a model.

---

## 4.5 Calibration — are the probabilities honest?

A model can rank perfectly and still lie about probabilities.

> **Example.** A weather model that always says "70% chance of rain" on days it
> rains and "20%" on days it doesn't has **perfect AUC** — flawless
> ranking. But if it actually rains on 95% of the "70%" days, the probabilities
> are wrong, and anyone budgeting against them is misled.

### How to check it

Bucket predictions (0–10%, 10–20%, …). In each bucket, compare *mean predicted*
against *actual frequency*. Plot. A perfectly calibrated model sits on the
diagonal.

```
   observed
   frequency
      1.0 |                                    /
          |                                 /*
          |                              /*
      0.5 |                          /*
          |                      /*
          |                  /*
      0.0 |______________/*____________________
          0.0          0.5                  1.0
                predicted probability

          diagonal = perfect calibration
```

**Expected Calibration Error (ECE)** is the average absolute gap, weighted by
bucket size. We pre-registered a target of < 0.05.

**Brier score** combines calibration and sharpness into one number: the mean
squared error of the probability forecast. Lower is better; we pre-registered
<= 0.06.

### What we measured, and why "passing" both targets is the trap

```
   metric   target      measured     null model    pass?
   ------------------------------------------------------------------
   ECE     < 0.05        0.00863       0.00005      "PASS"
   Brier   <= 0.06      0.019522      0.019614      "PASS"
   ------------------------------------------------------------------
```

Both thresholds were cleared. The model is still useless, and this is the most
instructive result in the whole project.

**Why the thresholds are cleared by a failure.** Both ECE and Brier are on the
scale of the probabilities themselves. When events happen 2% of the time, every
sensible prediction lives between 0 and roughly 0.09. A squared error on that
scale is tiny no matter what you do. A model that always guesses 0.02 scores
Brier 0.019614 and ECE 0.00005 -- it clears both thresholds comfortably
while containing exactly zero information.

> **The lesson, stated so an examiner cannot state it for you.** A fixed
> threshold is only meaningful relative to what a no-information model scores
> on the same data. We set < 0.05 and <= 0.06 without checking what the null
> would score. Had we checked, we would have seen the targets were
> unfalsifiable before the first line of model code was written. **Always
> pre-register against the null, not against a round number.**

The honest statistic is the comparison, and it is brutal: our ECE of 0.00863
is about **170 times** the null's 0.00005, and our Brier skill over the null is
+0.00471 -- half of one percent of the available improvement.

> **Why calibration matters here specifically.** A city council acting on "60%
> probability of a facility within 18 months" is making a financial decision on
> that number. If our 60% actually means 85%, we have mispriced their
> negotiating position. Our model never says 60% -- its whole range is
> roughly 1% to 9% -- but within that range it over-predicts by as much as a
> factor of four, under-predicts by about a factor of two, and at the top of
> the range it points the wrong way.

---

## 4.6 Conformal prediction — the strongest thing we can say

### 4.6.1 The problem with normal prediction intervals

Most models produce intervals from their own internal assumptions — Gaussian
errors, correct specification, asymptotic normality. If any assumption is wrong,
the interval is wrong, and **you have no way to know.**

### 4.6.2 What conformal prediction does differently

Split conformal (Angelopoulos & Bates, 2021) is nearly assumption-free:

1. Split data into a training set and a **calibration** set.
2. Fit on training.
3. Predict on calibration, and record the **errors**.
4. For 90% coverage, take the 90th percentile of those absolute errors — call
   it `q`.
5. For a new prediction, the interval is `prediction ± q`.

**The guarantee:** under exchangeability, this covers the truth at least 90% of
the time. No distributional assumption. Finite-sample. Valid for *any* underlying
model.

> **Example.** Fit the model. On the calibration set, 90% of absolute errors are
> below 0.11. So every prediction gets ±0.11. On held-out data, count how often
> the truth fell inside. **It should be ~90%, and we report the measured
> number.**

### 4.6.3 Why this is the highest-value thing in the accuracy section

Because it converts an *assumed* guarantee into a *measured* one. Here is the
measurement, from `outputs/metrics/hazard_report.json`:

```
   nominal coverage                    90.00%
   empirical coverage                  88.19%   <-- measured
   gap                                  1.81pp
   2-sigma tolerance                    3.2pp
   effective units behind the number      351
   verdict                             INSIDE TOLERANCE
```

So the claim we are entitled to make is:

> *"Our 90% prediction sets empirically covered 88.19% of held-out
> ZCTA-quarters, against a 90% nominal target, which is inside a two-sigma
> tolerance of 0.032 computed on 351 effective units."*

Note what changed from earlier drafts. That sentence used to read "covered
90.2%", a number that was never measured. The real figure is **88.19%**, it
undershoots nominal, and it is still a pass -- because the honest version of
this claim carries its tolerance and its sample size, and 351 effective units
cannot resolve a 1.8-point gap. **Cite 88.19%, always with the tolerance.**

That sentence is verifiable, falsifiable, and costs about 30 lines of code. It
is the single best credibility-per-hour item in the project.

> **But do not oversell what it rescues.** Conformal prediction guarantees the
> *interval*, not the *model*. Section 4.1 showed the point predictions are
> barely better than a constant and mis-ordered at the top. Conformal coverage
> being sound means we are honestly reporting how uncertain a weak model is.
> It does not make the model strong. This is exactly the distinction in the
> 4.3 table: "how wrong could I be" is a different question from "does it rank
> well", and you can pass one while failing the other.

> **And the second conformal result is worse than this one.** The same
> machinery was run on the current choice model and it **over**-covers: 100%
> empirical against a 90% nominal target, achieved by naming 71% of the metro
> (Sec. 4.0). Under-coverage at 88.19% with a stated tolerance is the
> better-behaved outcome of the two, because a set that names seven ZIPs in
> ten cannot fail. If you are asked "is your conformal layer a success", the
> honest answer names both numbers and concedes that the newer one is the
> weaker.

---

## 4.7 Rank stability — the metric an executive actually needs

Everything above is statistical. This one is about the decision.

**The question:** if the inputs move within their uncertainty bands, does the
recommendation change?

> **Status: NOT COMPUTED, and the simulation it needs already exists.** The
> Monte Carlo did run -- **500 draws, 500 succeeded, seed 20260914**,
> `outputs/metrics/montecarlo_report.json` and
> `outputs/tables/montecarlo_draws.parquet`. But the draws table has 28
> columns and **none of them is a per-ZCTA ranking**: it records `n`,
> `capital_usd`, `breakeven_margin`, `optimality_gap`,
> `median_cost_per_parcel` and the 23 sampled parameters, one row per draw.
> Per-ZIP top-K stability was never written out. This is the cheapest
> outstanding item in the project and it is still outstanding.

**The method it would use:** in each of the 500 draws, record the ranking.
Then report, per ZIP, the share of draws in which it holds a top-K position.

```
   ILLUSTRATIVE ONLY -- these four ZCTAs and four percentages are made up
   to show the SHAPE of the output. No such table has been produced.

   ZCTA      share of draws in top-10
   ---------------------------------------------------------
   94608     ############################################  87%   STABLE
   94501     ##################################            68%   stable
   94612     #################                             34%   UNSTABLE
   30318     ########                                      16%   UNSTABLE
```

> **What this would let you say.** *"ZIP 94608 appears in the top ten in 87% of
> draws — act on it. ZIP 94612 appears in 34% — that is close to a coin
> flip, so do not commit $4M to it."* Do not say it yet. Nothing has been
> measured that entitles anyone to a sentence of that shape.

**Almost no student project reports this**, it falls straight out of a
simulation that has already been run, and it would reframe uncertainty from an
apology into a product feature. That it was not done, when the draws were
sitting there, is a straightforward miss and should be conceded as one.

> **A claim withdrawn.** This section used to say *"we already run 10,000
> Monte Carlo draws for NPV"* and printed the table above with no caveat. Both
> were false. The Monte Carlo is **500** draws, not 10,000, and it does not
> emit rankings. See Part 5 §5.5 for what it does emit.

---

## 4.8 Why MAPE was removed — the full argument

A natural instinct is to set "MAPE below 25%" as the headline accuracy target. Two independent reasons
this had to go.

### Reason 1 — it is undefined on the data

```
                      1        |actual - predicted|
   MAPE  =  100 x  -------  Σ  --------------------
                      n              actual
                                     ^^^^^^
                                   division by zero
```

The entire premise of the demand model is that many ZIPs are structural zeros.
Where `actual = 0`, MAPE is undefined. Options: drop the zeros — destroying
the reason ZINB was chosen — or report infinity.

Hyndman & Koehler (2006), *Another look at measures of forecast accuracy*, is the
standard citation. **Cite it yourself before a reviewer cites it at you.**

### Reason 2 — it was measured against a fabricated target

Even where computable, it scored predictions against a variable built from the
predictors (Part 2 §2.4). A low MAPE would have been evidence of circularity.

### What replaces it

| Outcome type | Metrics | Actually computed? |
|---|---|---|
| Binary / timing (primary) | AUC, Brier, ECE, calibration table | **Yes** -- in `hazard_report.json` |
| Binary / timing (primary) | PR-AUC, precision@k | **No** -- specified, never produced |
| Count (secondary) | Poisson/NB deviance, RMSLE, MASE | **No** -- the ZINB model was never built |
| Any | Conformal interval coverage | **Yes** -- hazard 88.19% vs 90% nominal; choice model 100% vs 90% at 71% of the metro (Sec. 4.0) |
| Choice (current) | top-1 / top-5 / top-10, raw Brier vs a uniform null | **Yes** -- in `choice_report.json`, and only matched by a raw count |
| Decisions | Top-K rank stability | **No** -- the 500 Monte Carlo draws exist but emit no rankings (Sec. 4.7) |

The third column exists because a metrics table with no delivery status is an
invitation to assume everything in it was run. Three of the six rows were not.

---

## 4.9 Validation design — out-of-time, not just out-of-sample

**Out-of-sample** means held-out rows. **Out-of-time** means held-out *future*.
They are not the same, and the second is much harder.

```
   TIME ------------------------------------------------------>

   |<------- TRAIN: facilities open through 2023 -------->|
                                                           |
                                    |<-- PREDICT 2024-25 -->|
                                                           |
                              score against what actually happened
```

Plus two metros (Phoenix, Boise) withheld from training entirely, so we test
**geographic** transfer as well as temporal.

> **Why out-of-time is the honest test.** Random row splits leak information:
> the model sees 2025 patterns while predicting 2024. Real forecasting never has
> that luxury. An out-of-time backtest is the only design that mimics the actual
> use.

**And the pre-commitment:** if the criteria are not met, we report the failure.
The validation set is never used for retraining. Stating this in advance is what
makes the eventual number believable.

### The pre-commitment was tested, and here is the bill

This is the section where the promise above gets paid. Both harder splits were
run and both went against us:

```
   split                what it withholds        AUC     Brier skill
   ---------------------------------------------------------------------
   temporal hold-out    everything after t=19   0.5551     -0.02091
   geographic hold-out  Phoenix + Boise         0.6168     -0.06184
   ---------------------------------------------------------------------
   a NEGATIVE Brier skill means: predicting the base rate for
   every ZIP would have scored better than our model did
```

Three things a reader must take from that block.

1. **The out-of-time result is the one that counts, and it is a failure.**
   0.5551 is a coin flip with a decimal point. Random row splits leak
   information -- the model sees 2025 patterns while predicting 2024 -- and
   the primary split's 0.6894 is partly that leak. When the leak is closed, the
   signal mostly goes with it.
2. **The geographic number is not a transfer result.** Phoenix and Boise hold
   two dated delivery stations between them. It is a smoke test for gross
   failure, and it is reported because we said we would report it, not because
   two facilities can test transfer.
3. **The dates make the temporal split doubly weak.** Most opening dates are
   OSHA "operating by" upper bounds with a measured median lag of 57 months
   (see Part 2 Sec. 2.2.7.1). An out-of-time split slices on a date that can be
   years wrong, so some of the 0.5551 is the model failing and some of it is
   the split being drawn in the wrong place. We cannot currently separate the
   two, and the fix -- interval censoring -- is marked NOT STARTED in
   `docs/STATUS.md`.

> **Why report this at all.** Because the pre-commitment was public and the
> alternative is to quietly drop the split that lost. A project that reports
> only its unit-clustered number, and does so after running three others, is
> not reporting a result; it is reporting the maximum of four draws.

---

## 4.10 Evaluating the agent — a different problem entirely

### 4.10.1 Calibrate the target against the field first

On the BIRD benchmark (Li et al., NeurIPS 2023):

```
   best public systems ............ ~80% execution accuracy
   human baseline ................. ~93%
   a naive target .................. 85% on 40 self-authored questions
```

**That would claim above-state-of-the-art performance on a self-authored test
set.** A reviewer who knows the field reads that as either naive or
unfalsifiable.

### 4.10.2 The n=40 problem

At n = 40, an observed 85% has a 95% Wilson confidence interval of roughly
**[71%, 93%]**.

```
   |------------------|====================|-------------|
   71%               85%                  93%

   a "pass" at 85% and a "fail" at 72% are
   STATISTICALLY INDISTINGUISHABLE at this sample size
```

**Fixes:** n ≥ 100, report the interval, target 75% overall.

### 4.10.3 Execution accuracy, not human judgement

**Execution accuracy:** does the generated SQL return the *same result set* as a
gold query? Objective, reproducible, field-standard. Human judgement is reserved
for narrative-quality questions only.

### 4.10.4 Stratify by difficulty

```
   tier 1  lookup            "How many facilities in Texas?"
   tier 2  aggregation       "Average NPV by metro, ranked"
   tier 3  spatial join      "ZIPs within 10 km of a competitor facility"
   tier 4  multi-hop         "Top-decile ZIPs whose ranking is unstable,
                              excluding those adjacent to a 2024 opening"
```

Aggregate numbers hide that **spatial joins are where these systems break**
— and our warehouse is spatial. Per-tier reporting is both more informative
and more honest.

### 4.10.5 If you use an LLM as judge, know its failure modes

- **Position bias** — judges favour whichever answer appears first
  (arXiv:2406.07791)
- **Reliability without validity** — consistent but consistently wrong
  (arXiv:2606.19544)
- **Coin-flip behaviour** on genuinely hard items (arXiv:2606.13685)

**Mitigations:** randomise option order, use two judges plus a human tiebreak,
and report Cohen's κ (inter-rater agreement).

### 4.10.6 Pre-register the minimum detectable effect

If you compare models on n = 200 items with a hit rate near 0.8, the standard
error is about 2.8 percentage points. Differences below roughly **8pp are not
distinguishable**.

```
   Model A  |==================================| 82%  +/- 5.5pp
   Model B  |===================================| 84% +/- 5.1pp
   Model C  |===================================| 85% +/- 5.0pp
                                                 ^
                              intervals OVERLAP -> there is no result
```

**Saying this in advance turns a weakness into evidence of rigour.** Saying it
afterwards looks like an excuse.

---

## 4.11 Part 4 self-check

**On the current model -- answer these before anything else.**

0a. Which model does this project ship as its siting model today, and what did
    it score against the best single-covariate benchmark on held-out top-1?
    (If your answer does not contain the word "matched", it is wrong — and
    if it contains "beaten", see the correction block in Sec. 4.0.)

0b. Two of the three free parameters are at `exp(-35)`. What does that mean
    mechanically, given `beta = exp(theta)`, and why can a sandwich standard
    error not be reported for them?

0c. Does `choice_report.json` contain a standard error, a confidence interval
    or a bootstrap? What did `MODEL_SPEC.md` §6.3 prescribe, and what is
    `choice_inference.py`?

0d. The choice model's conformal sets cover 100% at a nominal 90%. Explain in
    one sentence why that is a worse outcome than the hazard model's 88.19%.

**On the retired hazard model.**

1. State the primary hazard result in one sentence, with the AUC, the Brier
   skill, the ECE and the null's ECE.
2. A constant predictor has an ECE of 0.00005 and ours has 0.00863. Explain to
   a non-technical listener why being 170 times worse calibrated than a model
   with no inputs is possible, and why it is damning rather than a paradox.
3. Both pre-registered calibration thresholds (ECE < 0.05, Brier <= 0.06) were
   cleared. Why is that not good news, and what should the thresholds have
   been set against instead?
4. What did the temporal hold-out score, and why is it a more honest number
   than the primary split?
5. Why is the geographic hold-out result *not* evidence about geographic
   transfer?
6. A delivery station opens in Chicago. How many ZCTAs flip to `enabled` that
   quarter, and what does `CATCHMENT_MILES` have to do with it?
7. Quote the assumption in Train Sec. 3.7.1, p. 61 that the hazard panel
   violates, name the standard term for the violation, and explain in two
   sentences how a 15-mile catchment causes it. Then say why Sec. 2.2 --
   mutual exclusivity -- was the *wrong* citation, and why the corrected one
   makes the charge harder rather than softer. (Train calls the Sec. 2.2
   criterion "not restrictive", p. 12.)
8. We had 812 events and roughly 38 decisions. Which number did the likelihood
   count, and why does that make "97.4 events per parameter" a fiction?
9. Why does sampling of alternatives (Train Sec. 3.7.1, the unnumbered
   sub-heading at pp. 64-66) not rescue the specification? Give both reasons,
   and say why Sec. 3.7.1 gets cited twice in this chapter for two different
   things.
10. Name the three successor routes and state which one has been chosen.
    (Check your answer against Sec. 4.1 -- route (A) was built, and it is
    Sec. 4.0. Then say why building it did not fix the result.)

**On the concepts.**

11. Why a hazard model rather than a classifier? Give the censoring argument.
12. Explain structural vs sampling zeros with the fishing example.
13. Why is the Huff β fixed rather than fitted?
14. Give a model with perfect AUC and terrible calibration, and then say which
    of those two our model actually resembles.
15. Why would PR-AUC matter more than AUC at our real base rate of 2.0%, and
    is a PR-AUC reported anywhere in this project?
16. Explain split conformal prediction in four steps, then state our measured
    coverage and its tolerance.
17. State the two independent reasons MAPE was removed.
18. What is the difference between out-of-sample and out-of-time?
19. Why is 85% on 40 self-authored questions a weak claim, in two ways?
20. How many Monte Carlo draws does this project actually have, and is top-K
    rank stability reported anywhere? If not, what would it take?

---

**Next:** `HANDBOOK_05_COST_NPV.md` — Daganzo, capital buckets, Monte Carlo, and
why expansion is a portfolio problem.
