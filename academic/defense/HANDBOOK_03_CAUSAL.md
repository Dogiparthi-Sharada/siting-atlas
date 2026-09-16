# Handbook Part 3 — Causal Inference

**The hardest part of the project and the part most likely to be attacked.
Selection bias, counterfactuals, synthetic control, interference, and how to
tell whether an effect is real or noise.**

Read this one twice.

---

## 3.0 STATUS BANNER - READ BEFORE ANY OTHER LINE IN THIS CHAPTER

```
  +====================================================================+
  |                                                                    |
  |   NOTHING IN THIS CHAPTER HAS BEEN IMPLEMENTED.                    |
  |                                                                    |
  |   Not the Heckman correction. Not the difference-in-differences.   |
  |   Not synthetic control. Not placebo inference. Not the Pollmann   |
  |   distance bands. Not the mutable spatial weight matrix W. Not     |
  |   one line of any of it exists in src/.                            |
  |                                                                    |
  |   This is the project's SECOND ESTIMAND, and it has never been     |
  |   touched. Work stopped before it started.                         |
  |                                                                    |
  |   WHERE THE FIRST ESTIMAND STANDS, since this chapter's argument   |
  |   in Sec. 3.11 depends on it:                                      |
  |                                                                    |
  |     CURRENT   a conditional ZCTA choice model. FITTED, converged,  |
  |               national frame, 3 free parameters, 94 decisions,     |
  |               56 train / 38 held out, seed 20260914. McFadden      |
  |               rho-squared 0.19691 in sample.                       |
  |               outputs/metrics/choice_report.json                   |
  |               HEADLINE: on the 38 held-out decisions a single raw  |
  |               Census count of warehousing establishments (NAICS    |
  |               493, nothing fitted from it) MATCHES it: 8/38 vs     |
  |               7/38 at top-1, 20/38 vs 19/38 at top-10, and         |
  |               level at top-5 (16/38), level over 50 re-splits.     |
  |               The estimation buys nothing measurable. Inference    |
  |               landed 2026-09-14 and agrees: the one working        |
  |               parameter is not distinguishable from the null of    |
  |               beta = 1 (households is the numeraire, so 1 means    |
  |               "worth one household"). Sandwich [0.734, 2.835],     |
  |               p = 0.287; bootstrap over decisions [0.760, 4.762];  |
  |               over metros [0.702, 10.013]; BCa [0.714, 3.522].     |
  |               All four cover 1.0.                                  |
  |                                                                    |
  |     RETIRED   the discrete-time hazard model on ZCTA-quarters.     |
  |               Built, fitted, FAILED (HANDBOOK_04_MODELS.md).       |
  |               Superseded, kept as teaching.                        |
  |                                                                    |
  |   THE ONLY CANNIBALISATION IN THE CODEBASE IS AN ASSUMPTION:       |
  |     a 20 km radius, a 0.18 peak, saturating with neighbour         |
  |     exposure as peak * (1 - exp(-exposure)).                       |
  |     See src/siting_atlas/optimize/params.py.                       |
  |     It is a parameter somebody typed. It has NO standard error,    |
  |     NO donor pool, NO placebo distribution, and NO confidence      |
  |     interval, because it was never estimated from anything.        |
  |                                                                    |
  +====================================================================+
```

> **Corrected 2026-09-14.** The CURRENT row used to say the raw CBP count
> **BEATS** the fitted model, and Sec. 3.10 repeated it as "beaten". Both now
> say *matches*, because the claim was wrong rather than overtaken. It came
> from a single seeded 56/38 split. Re-split the same 94 decisions fifty times
> and the raw count is ahead by **0.36 hits out of 38 (paired sd 1.14)** while
> losing 11 of the 50 outright (`outputs/metrics/gbm_benchmark.json`, key
> `across_repeats.conditional_logit`). A third of a decision is not a defeat,
> and asserting one was reading noise as signal. The per-split figures in the
> box are correct for their seed, and the conclusion this chapter leans on in
> Sec. 3.10 and Sec. 3.11 does not move: three estimated parameters buy **no**
> ranking improvement over a raw count of warehouses, so the first estimand is
> still not a usable instrument.

### So why is this chapter still here, and still long?

Because a viva examiner may still ask **"what is synthetic control?"** or
**"what does the exclusion restriction buy you?"**, and you must be able to
answer fluently. The teaching is real teaching and it stays. What changes is the
**tense**. Wherever this chapter used to say *"we do X"*, it now says *"we would
do X"* or *"the design calls for X"*, because the old tense was lying.

### How to read the numbers in this chapter

Three places quote a figure that looks like a result. None of them is.

| Where | The figure | Status |
|---|---|---|
| Sec. 3.3.3 | first-stage F-statistic, conventional bar F > 10 | **Never computed.** The selection equation was not fitted |
| Sec. 3.6.2 | "highest of 40 units, so p is about 1/40 = 0.025" | **Illustrative arithmetic.** No placebo study was run |
| Sec. 3.7.3 | "-12% within 8 km, -4% at 8-20 km, zero beyond 20" | **Illustrative.** A PLAN describing the shape of an answer, not a measurement |

Each of those is flagged again in place. If you quote any of them as a finding
you will be caught, and the examiner will be right.

### The one-sentence version to say out loud

> *"The cannibalisation estimand is fully specified and completely unbuilt. I
> can tell you exactly how I would identify it and exactly why I think the data
> would defeat it, and that second half is Sec. 3.11."*

---

## 3.1 The question causal inference exists to answer

Every claim in this project reduces to a comparison against something that never
happened.

> *"Launching same-day in this ZIP cannibalised 12% of its 2-day orders."*

Cannibalised **relative to what?** Relative to a world where the launch did not
happen — a world we cannot observe. That unobserved world is the
**counterfactual**, and estimating it is the entire discipline.

**The fundamental problem of causal inference:** for any unit, you observe either
the treated outcome or the untreated outcome. Never both. Every method below is a
strategy for manufacturing the missing half credibly.

---

## 3.2 Why naive comparison fails, three ways

Suppose we compare ZIPs with same-day service to ZIPs without, and find the
same-day ZIPs have 30% higher order volume.

### Failure 1 — Selection

The operator did not choose ZIPs at random. They chose dense, affluent,
logistics-accessible ones.

> **Example.** Compare hospitals: patients who receive intensive care die more
> often than patients who don't. Conclusion: intensive care kills?
>
> Obviously not. **Sicker patients get sent to the ICU.** The treatment is
> assigned based on the outcome's own predictors.

Same structure here: **high-demand ZIPs get same-day service.** Comparing them to
low-demand ZIPs measures the selection, not the treatment.

### Failure 2 — Time confounding

Same-day ZIPs launched during a period when e-commerce was growing everywhere.
Some of the "lift" is a trend the untreated ZIPs also experienced.

### Failure 3 — Interference

The untreated ZIPs are not clean controls, because they are *adjacent to treated
ones* and absorb spillovers. Your control group is contaminated.

**Each of the next three sections describes the method that would fix one of
these.** Would, not does: see the banner in Sec. 3.0.

---

## 3.3 Fixing selection — the Heckman correction

### 3.3.1 The intuition

Two things are happening: a *selection* process (does this ZIP get treated?) and
an *outcome* process (what happens if it does?). If unobserved factors drive
both, the outcome model is biased.

> **The classic example.** You want to estimate the effect of education on
> wages, using only employed people. But employment is itself selected —
> people with high unobserved ability are both more likely to work *and* to earn
> more. Your wage equation confuses ability with education.

Heckman (1979) said: **model the selection explicitly, then include a correction
term in the outcome equation.**

### 3.3.2 The two steps

**Step 1 — selection equation.** A probit over *all* ZCTAs in the pilot metro:

```
   P(facility opened touching ZCTA i)  =  Φ( α·X_i  +  γ·Z_i )
```

where `X` are demand covariates and `Z` is an **instrument** (below).

From this, compute the **inverse Mills ratio** for each ZIP — a number
capturing "how surprising is it that this ZIP was/wasn't selected, given its
characteristics."

**Step 2 — outcome equation.** Fit the outcome model with the inverse Mills ratio
included as an extra regressor. Its coefficient absorbs the selection effect,
leaving the other coefficients interpretable.

### 3.3.3 The instrument, and why ours is contestable

An instrument must satisfy two conditions:

1. **Relevance** — it affects selection. (Testable: first-stage F-statistic;
   the convention is F > 10.)
2. **Exclusion restriction** — it affects the outcome *only through*
   selection, never directly. (**Not testable.** It is an argument.)

**The proposed instrument:** distance to the nearest commercially zoned ZIP
centroid. Proposed, not used: no selection equation has been fitted, so **the
first-stage F-statistic has never been computed.** When this chapter says "we
report the first-stage F", read "we would report it".

**The argument for it:** operators prefer commercially zoned land — cheaper,
fewer objections, better truck access. So it drives siting.

**The argument against it, which a good reviewer will make:** commercial-zoning
proximity correlates with retail agglomeration, employment density and traffic
— each of which could plausibly drive residential ordering behaviour
*directly*. The exclusion restriction is not obviously satisfied.

> **How to handle this in the viva — do not defend it as airtight.**
>
> *"The exclusion restriction is an argument, not a test, and ours is
> contestable — commercial zoning correlates with employment density, which
> could affect demand directly. The design reports the first-stage F-statistic,
> and reports a sensitivity analysis showing how far the corrected coefficients
> would move if the instrument had a small direct effect. If a conclusion
> survives a plausible violation, that is worth more than claiming there isn't
> one. I should add that none of this has been run - the selection equation is
> specified and unbuilt."*

**Naming your own weakness before the reviewer does converts an attack into
evidence of rigour.** This is the single most useful defensive move in the
project.

### 3.3.4 Scope honesty

Full Heckman correction on all ten metros was always out of scope for eight
weeks. The plan was: do **one** metro properly, report corrected *and* naive
coefficients side by side so the magnitude of the correction is visible, and
footnote the other nine as embedding selection. Extending it via causal forests
or double machine learning was named as future work.

**Why that would have been acceptable:** demonstrating that the correction is
available and *materially changes estimates* is the scientific point. Doing it
ten times adds labour, not insight.

> **The update, and it is blunter than the paragraph above.** Zero metros were
> done, not one. The Heckman correction is specified and unbuilt. The scope
> honesty that actually matters now is not "we did one of ten" but "we did none
> of ten, because the first estimand consumed the time and then failed".

---

## 3.4 Fixing time confounding — difference-in-differences

### 3.4.1 The idea

Don't compare treated to untreated. Compare **the change in treated** to **the
change in untreated**.

```
                    BEFORE      AFTER      CHANGE
   treated ZIP        100        130         +30
   control ZIP         80         95         +15
                                            ------
   difference-in-differences effect          +15
```

The +15 the control gained is the trend both would have experienced anyway.
Subtract it, and +15 remains as the treatment effect.

### 3.4.2 The assumption that can fail

**Parallel trends:** absent treatment, both groups would have moved together.

**This is untestable for the post-period** (that's the counterfactual again). What
you *can* do is check whether they moved together *before* treatment, and show
the plot. If pre-trends diverge, the assumption is already in trouble.

> **Example of a parallel-trends failure.** Suppose the operator launches
> same-day in fast-growing suburbs. Those suburbs were already on a steeper
> growth path. DiD attributes the steeper trend to the launch. The estimate is
> biased upward, and no amount of post-period data reveals it.

---

## 3.5 Synthetic control — building a better comparison

### 3.5.1 Why DiD is not enough here

DiD needs a control group that resembles the treated group. But no single
untreated ZIP resembles Berkeley. Picking one by hand is arbitrary; averaging all
of them is worse.

### 3.5.2 The synthetic control idea

Abadie, Diamond and Hainmueller (2010): **build** the comparison unit as a
weighted blend of untreated units, choosing weights so the blend tracks the
treated unit closely *before* treatment.

> **Example.** No single US city is a good comparison for San Francisco. But
> perhaps `0.4 × Seattle + 0.3 × Boston + 0.2 × Austin + 0.1 × Denver`
> reproduces San Francisco's pre-launch trajectory almost exactly.
>
> That blend is **Synthetic San Francisco**. After the launch, we let the blend
> keep running. The gap between real San Francisco and Synthetic San Francisco
> is the estimated effect.

```
   volume
     |                                      ,-- real (treated)
     |                                 ,---'
     |                            ,---'        }  <- estimated effect
     |         both track    ,---'     ,-------'
     |         closely  ,---'    ,----'   synthetic (counterfactual)
     |           ,-----'   ,----'
     |     ,----'    ,----'
     +----------------------|--------------------------> time
                       treatment
        <-- pre-period -->  <----- post-period ----->
        (fit is checked)    (gap is the estimate)
```

### 3.5.3 The donor pool

The untreated units eligible to enter the blend. Two rules:

1. **Never include a treated unit.** Obvious, and it is exactly what Gate 5
   protects (Part 6).
2. **Exclude contaminated units.** A ZIP adjacent to a treated ZIP absorbs
   spillover and is not clean.

> **The donor-pool scarcity problem.** As a network saturates nationally, the
> supply of genuinely untreated, uncontaminated comparison units shrinks. This is
> a real limitation and the design states it in §4.4 rather than waiting to be
> asked.

> **And it is not hypothetical here.** Gate 5 (donor-pool integrity, Part 6) is
> implemented and does run against the real 33,791-ZCTA warehouse, and **it
> escalates often, because the donor pool genuinely is thin.** That is the one
> piece of hard evidence this chapter can point to: a working gate telling us,
> repeatedly, that the study this chapter describes would struggle for clean
> controls. Take it seriously rather than treating it as a nuisance alert.

### 3.5.4 Pre-treatment fit is necessary, not sufficient

Reporting only pre-treatment fit RMSE is not enough, and here is why:

> **You can fit the pre-period beautifully and still measure nothing.** With
> enough donors and enough flexibility, some blend will track almost any
> pre-period. The question is whether the post-period gap is *larger than the
> gaps you'd get by chance*.

That requires placebo inference.

---

## 3.6 Placebo inference — is the effect real?

This is the Abadie standard, and its absence in an earlier draft was a genuine red flag.

### 3.6.1 In-space placebos

**The procedure the design calls for** (specified; not run):
1. Take an untreated ZIP.
2. **Pretend** it was treated on the same date.
3. Run the whole synthetic control machinery on it.
4. Measure the "effect" you get — which should be near zero, because
   nothing happened.
5. Repeat for every untreated ZIP.

You now have a **distribution of effects under no treatment** — a null
distribution built from your own data, with no distributional assumptions.

**Then ask:** is the real treated unit's effect unusually large compared to that
distribution?

```
   placebo effects (untreated ZIPs, nothing happened)
        |
   -----|--|--|-|--||-|-|--|---|------------------|-------->
                                                  ^
                                            real treated unit

   if the real effect sits in the far tail -> plausibly real
   if it sits in the middle of the pack    -> indistinguishable from noise
```

### 3.6.2 The RMSPE ratio

Some units simply fit badly in the pre-period, so they show big post-period gaps
for uninteresting reasons. The fix is a **ratio**:

```
                    post-treatment RMSPE
   RMSPE ratio  =  ----------------------
                    pre-treatment RMSPE
```

A unit that fit well before and diverged after has a high ratio. A unit that
never fit has a high numerator *and* denominator, so it does not spuriously rank
high.

**The p-value:** rank the treated unit's ratio among all placebo ratios.
If it were the highest of 40 units, that would be a rank-based p-value of about
1/40 = 0.025.

> **That 0.025 is arithmetic, not a finding.** It is what 1/40 equals. **No
> placebo study has been run in this project**, so there is no rank, no
> distribution and no p-value. The number is in the text to show you how the
> inference *works*, and for no other reason.
>
> Note also what the arithmetic implies about feasibility: a rank-based p-value
> can never be smaller than 1/(number of placebo units + 1). With a thin donor
> pool you cannot reach conventional significance even in principle. If you only
> had 19 clean donors, your smallest achievable p-value is 0.05 - and you would
> have to rank first out of 20 to get it.

> **Why this is elegant.** No distributional assumption, no standard-error
> formula, no asymptotics. You built the null out of your own data. It is
> honest in a way parametric inference often isn't with n = 1 treated unit.

### 3.6.3 In-time placebos

Same logic, different axis: pretend treatment happened two years *earlier* than
it did. You should find no effect. If you find one, something other than the
treatment is driving your result.

---

## 3.7 Interference — the assumption everyone violates

### 3.7.1 SUTVA, stated properly

> **Do not confuse this section number with Train's.** *This handbook's* Sec.
> 3.7.1 is about SUTVA. *Train (2009)* Sec. 3.7.1 is about independence across
> observations, and it is the assumption the retired hazard model violated
> (Sec. 3.11). The matching number is a coincidence. Say "Train
> three-seven-one" when you mean his.

**Stable Unit Treatment Value Assumption** has two parts:

1. **No interference** — treating unit A does not affect unit B's outcome.
2. **No hidden variations** — "treatment" means the same thing everywhere.

Part 1 is the one we violate, flagrantly.

> **Example.** Same-day launches in Berkeley. An Emeryville resident works in
> Berkeley, now has a same-day-eligible address, and shifts their household
> ordering. Emeryville's outcome moved. Emeryville is in our donor pool.
>
> **Our "untreated" control was partially treated.** Every estimate using it is
> biased toward zero — we understate the effect, because the comparison
> moved with the treatment.

### 3.7.2 The standard non-solution

Most applied work handles this with a **spatial weight matrix W**: a table
declaring which units are neighbours, letting the model account for cross-unit
dependence.

Almost everyone builds W by **contiguity** — 1 if the polygons touch, 0
otherwise.

**And that is an assumption nobody defends.** Why touching? Why not 5 km? Why not
30 minutes' drive? an earlier draft used contiguity with no justification, and the question
"why contiguity?" had no answer.

### 3.7.3 What the design does instead — measure the reach

Rather than assuming the spillover structure, **estimate it**.

Following Pollmann (*Causal Inference for Spatial Treatments*), the design would
estimate the treatment effect separately within concentric **distance bands**
around each activated ZIP. The picture below is what such an estimate would look
like. **It is a sketch of a shape, not a plot of data.**

```
   effect (%)
     0% -+--------------------------------*----*----*----
         |                          *
    -4%  |                    *                          <- fading
         |            *
    -8%  |      *
         |   *
   -12%  *                                               <- material
         +----+----+----+----+----+----+----+----+---->
         0    5   10   15   20   25   30   35   40  km

         |<-- material -->|<- fading ->|<-- ~zero -->|
              0 - 8 km       8 - 20 km    beyond 20
```

**The result would be a sentence:** *"Cannibalisation is -12% within 8 km, -4%
at 8-20 km, and statistically indistinguishable from zero beyond 20 km."*

```
  +--------------------------------------------------------------------+
  |  ILLUSTRATIVE, NOT MEASURED.                                       |
  |  The -12% / -4% / zero figures and the 8 km and 20 km breakpoints  |
  |  are a PLAN. No ring regression has been run. No distance bands    |
  |  have been estimated. These numbers show the SHAPE of the answer   |
  |  the design would produce, so you can recognise it when you see    |
  |  it. Quote them as findings and you are fabricating a result.      |
  +--------------------------------------------------------------------+
```

Nobody has published that number for same-day delivery. The **estimator would be
Pollmann's** - the claim would be the parameter, not the method, and saying so
explicitly is what would keep the claim safe.

> **Where the 20 km in the codebase came from, since someone will ask.** The
> portfolio optimiser uses a 20 km cannibalisation radius with a 0.18 peak. That
> is *not* this estimate arriving early. It is a placeholder chosen so the
> optimiser had something defensible to run on, and its docstring says so:
> *"PLACEHOLDER: in the finished project this is the Pollmann distance-band
> estimate rather than a constant."* The number and the estimate are unrelated
> except that one is standing in for the other.

### 3.7.4 Then build W from it — the elegant part

*Having* measured how far the effect reaches, you would define neighbours by
**measured reach** rather than by shared borders.

```
   BEFORE                          AFTER
   W = binary contiguity     ->    W = f(estimated decay)

   "because that's what           derived from the ring
    people do"                    regression above

   -> "why contiguity?"           -> W is an ESTIMATED OBJECT
      has no answer                  with a standard error
```

Two problems solved with one estimate. **This is the most satisfying move in the
methodology** and worth being able to explain fluently.

> **And it is entirely on paper.** There is no `W` anywhere in `src/`, estimated
> or contiguity-based. The chain is strictly ordered - decay curve, then W, then
> the spatial estimator - and the first link does not exist, so neither do the
> other two. What the codebase has instead is the flat 20 km radius, which is
> precisely the hand-picked assumption this section was written to replace.
>
> **This is still the right thing to say in a viva**, provided you say it in the
> conditional. "Here is how I would stop W from being an arbitrary choice" is a
> good answer to "why contiguity?". "Here is how I did" is a false one.

---

## 3.8 The W claim an earlier draft got wrong

It is sometimes asserted: *"Spatial econometrics has treated W as fixed ex ante for four
decades."*

**That is false**, and one search falsifies it:

- Souza (2019) — estimation and selection of W in a spatial lag model
- Krisztin & Piribauer — Bayesian estimation of weight matrices
- *Political Analysis* (2024) — parameterising spatial weight matrices
- Ahrens & Bhattacharjee — two-step Lasso estimation of W
- **LeSage & Pace (2014), "The Biggest Myth in Spatial Econometrics"** —
  argues prominently that results are *less* sensitive to W than people assume

### What survives, stated narrowly

Every estimator above recovers W **from the same outcome panel used for
inference** — an in-sample statistical problem, solved once.

The design treats W as **event-driven state**: revised *between* estimation
cycles from an exogenous text stream. Different object, different update
channel. (**Designed, not implemented** - see the banner in Sec. 3.0. No W is
revised because no W exists.)

```
   PRIOR ART: W as an estimated parameter
        outcome panel ---> estimate W ---> infer effect
        (same data used for both; in-sample; once)

   OURS: W as event-driven state
        outcome panel -------------------\
                                          >--> re-infer effect
        external text --> extract --> revise W
        (exogenous; between cycles; repeatedly)
```

### And turn the myth paper into your experiment

LeSage & Pace say results are robust to W. Our project is a natural test. So
**pre-register the question**:

> **RQ2: Does event-driven revision of W materially change the estimated
> cannibalisation coefficient, or are spatial causal estimates robust to such
> revision?**

| If the coefficient moves | If it doesn't |
|---|---|
| You push back on a well-known robustness claim, using a novel perturbation | You confirm it under a novel perturbation |
| Workshop-paper material | A clean negative result, **plus** an honest engineering finding: the mutable-W machinery is elegant but not decision-relevant |

**Both are publishable. You cannot lose this bet** — and pre-registering the
prediction *before* running it is what makes the negative result credible rather
than a rationalisation.

> **The third outcome, which the table above did not contemplate: you never run
> it.** That is where RQ2 sits today. A pre-registered bet that is never settled
> pays out nothing. If asked "what happened with RQ2?", the answer is *"it is
> still pre-registered and still unrun, because the first estimand failed and
> RQ2 is downstream of a cannibalisation estimate that does not exist."*
>
> Do not let "you cannot lose" do work it has not earned. The phrase was written
> about the two outcomes of an experiment that was going to happen.

---

## 3.9 Generated regressors — the quiet bug

Facility attributes extracted from text by a language model would enter these
estimators **as if measured without error**. They are not: the extraction has an
error rate. (No estimator consumes them yet, so this is a bug waiting rather
than a bug shipped - but it is waiting, and it should be fixed before the first
estimate, not after.)

Treating an estimated quantity as if it were observed **understates standard
errors** — you look more certain than you are. This is a classic problem
(Pagan, 1984) and modern work addresses it directly:

- Egami, Hinck, Stewart & Wei (NeurIPS 2023) — design-based supervised
  learning for imperfect surrogates
- Angelopoulos et al. (*Science*, 2023) — prediction-powered inference

> **Why this matters for credibility.** Almost nobody in the LLM-agent space
> corrects for this. Doing it is not novel — it is *correct*, and it is
> roughly a day of work. It is also a strong answer to "how confident are you?"

---

## 3.10 The framing that keeps every causal claim honest

We never claim to estimate objective viability. The claim, when there is one, is
**operator-consistent expansion desirability** — what the operator's revealed
preference implies. (And note what "when there is one" is doing: neither siting
model is a usable instrument — the retired hazard model failed outright, and
the current choice model is only matched on held-out data by a raw Census count
that costs nothing to compute, and has intervals that all cover the null — and the causal estimand in this chapter
was never built. So **there is currently no causal claim of any kind to keep
honest.** The framing device stays because whatever comes next will need it on
day one.)

> **Why the distinction is load-bearing, not pedantic.** Suppose the operator has
> historically skipped a certain kind of neighbourhood for reasons unrelated to
> profit. The model learns that pattern and reproduces it. Calling the output
> "viability" would launder a historical pattern into an objective-sounding
> recommendation.
>
> Calling it "operator-consistent" keeps it visible — and is exactly why
> §4.5.5 stratifies results by demographic group and flags strata where the
> model is unreliable.

---

## 3.11 Does the first estimand's failure condemn the second?

This is the question an examiner will reach for the moment you admit the hazard
model failed, and it deserves a careful answer rather than a hopeful one. The
honest answer has three parts, and the third is the important one. **The short
version is "yes, partly, in two separate ways"** — which is a worse answer for
the project than the one this section used to give, and a more defensible one.

### Part 1 — The two estimands differ, but less than an earlier draft claimed

The two estimands ask different questions and would use different machinery.

```
   ESTIMAND 1                           ESTIMAND 2  (never built)
   ---------------------------------    ---------------------------------
   Question:  WHERE will a station      Question:  WHAT does an opening DO
              open next?                           to its neighbours?
   Method:    v1 discrete-time hazard   Method:    spatial DiD + synthetic
              on ZCTA-quarters (FAILED)            control, distance bands
              v2 conditional ZCTA
              choice, 94 decisions
              (FITTED; matched by a
              raw CBP count)
   Needs:     many independent          Needs:     a clean pre-period, clean
              siting DECISIONS                     donors, and a treatment DATE
   v1 failed  7.6 events per parameter;
   on:        OBSERVATIONS NOT
              INDEPENDENT (clustering)
```

> **The Train citation, and a warning about section numbers.** The assumption
> the hazard model violated is **independence across observations**, Train
> (2009) **Sec. 3.7.1**, printed page 61: *"Assuming that each decision maker's
> choice is independent of that of other decision makers, the probability of
> each person in the sample choosing the alternative that he was observed
> actually to choose is L(beta) = prod_n prod_i (P_ni)^{y_ni}."*
>
> **Disambiguation, because this will trip somebody up:** *Train's* Sec. 3.7.1
> is about independence across observations and has nothing to do with *this
> handbook's* Sec. 3.7.1, which is about SUTVA. The matching number is a pure
> coincidence. When you cite it out loud, say "Train section three-seven-one",
> not "section 3.7.1".

> **A citation corrected.** This passage used to say estimand 1 was killed
> because "ZCTA-quarters are not mutually exclusive alternatives", citing Train
> Sec. 2.2. That is the wrong section and the wrong failure. Sec. 2.2 governs a
> choice set facing a decision maker; a hazard on area-quarters has no decision
> maker choosing among those rows, so exclusivity is not a property they can
> have or lack. Train calls that criterion "not restrictive" (p. 12) and offers
> a two-line repair for it. Corrected 2026-09-14.

**And the correction costs this section its comfortable conclusion, so say so.**
The old argument ran: the defect was a *choice-model* defect, difference-in
-differences does not need mutually exclusive alternatives, therefore the
diagnosis does not transfer. With the right diagnosis that argument does not
hold. **Pseudo-replication is not choice-model-specific.** It is a general
clustering failure, and a DiD can commit exactly the same one: if 88 ZCTAs are
switched on by a single building and each is entered as an independent treated
unit, the effective sample is 1 and the standard errors are wrong, in a DiD
just as surely as in a hazard model. Estimand 2 inherits this.

> **A claim withdrawn.** This section used to conclude "the diagnosis in
> `../METHODS_RESEARCH.md` Sec. 5.1 does not transfer", and further that the
> catchment structure *helps* estimand 2 because "58 ZCTAs treated
> simultaneously by one event is a disaster for a choice model and a perfectly
> ordinary treated cluster for a DiD". Both were written on the wrong
> diagnosis. The first is false: clustering transfers. The second is
> half-right and was stated too strongly — a correlated treated cluster is
> indeed a routine object in a DiD, but only if you *treat* it as one cluster.
> Nothing in this project's design does. Corrected 2026-09-14.

**What survives, stated narrowly.** The clustering failure is *manageable* in a
DiD in a way it is not in the hazard specification, because there is a standard
and unglamorous fix: cluster the standard errors at the level of the thing that
was actually randomised — the building, or the metro-period — rather than at
the ZCTA. That fix is well understood, it is cheap, and it is not implemented
anywhere in this project. So the honest position is **"transferable but
treatable, and untreated"**, not "does not transfer".

The difference between the two estimands that genuinely does survive is about
*what the date is for*, and that is Part 3 below.

### Part 2 — No, and it does not validate it either

Resist the obvious rebound argument, which goes: *"estimand 1 failed for reasons
specific to estimand 1, therefore estimand 2 is fine."* That is not an argument,
it is a change of subject. **An unbuilt estimand has no evidence either way.**
Nothing about estimand 2 has been tested, so nothing about it has passed.

The correct framing is that the two failures would be *independent*, not that
the second is *unlikely*.

### Part 3 — But there is a shared dependency, and it is fatal-looking

Here is the strongest and most honest thing in this chapter.

**Both estimands need the same facility dates. Those dates are upper bounds.**

The opening dates come from federal OSHA inspection records. An inspection
happens at a site that is already operating, so the record tells you *"open by
then"*, not *"opened then"*. On the five addresses that also appear in MWPVL's
2012 table with real opening months, the bound held 5 times out of 5 - but the
lag between opening and first inspection was:

```
   measured lag, opening -> first inspection, n = 5
   ------------------------------------------------
     4 months
    13 months
    57 months
    69 months
   345 months     <- opened 1997, first inspected 2026
```

**Why that is worse for a DiD than for a hazard model.** A hazard model uses the
date to decide which quarter a row's event flag goes in; get it wrong and you
mis-time events. An event study uses the date to decide **which observations are
"before" and which are "after"**. Get it wrong by 57 months and you have put
nearly five years of post-treatment quarters into the pre-period.

> **Worked example.** A station truly opens in 2018Q1 and is first inspected in
> 2022Q4 - a 57-month lag, which is inside our measured range. We date it
> 2022Q4. The event study then treats 2018Q1 through 2022Q3 as *pre-treatment*.
>
> Two things break at once. First, the pre-period now contains the treatment, so
> the "parallel trends" check is being run on contaminated data and will look
> reassuringly flat for the wrong reason. Second, the synthetic control's
> weights are fitted to match the treated unit over a window in which the treated
> unit is *already treated* - so the synthetic counterfactual is fitted to
> reproduce the treatment effect, and the post-period gap collapses toward zero.
>
> **The estimate is biased toward "no cannibalisation", and the diagnostic that
> is supposed to catch that failure is the one the error disables.** That is the
> worst possible combination: a wrong answer with a clean-looking check.

**So the honest verdict:** the second estimand inherits **both**. It inherits
the first's *data defect* — the dates are upper bounds — and it is arguably
more sensitive to that than the hazard model was, for the reason just worked
through. And, contrary to what this chapter used to claim, it also inherits the
first's *diagnosis*: pseudo-replication is a general clustering failure, not a
choice-model quirk, and a DiD that enters 88 catchment ZCTAs as 88 independent
treated units commits exactly the same error. The difference is that the
clustering half has a cheap standard fix and the dating half does not.

> **A claim withdrawn.** This paragraph used to read "the second estimand does
> not inherit the first's *diagnosis*, but it does inherit the first's *data
> defect*". The first clause was false, and it was false because the diagnosis
> it referred to was itself wrong (Part 1 above). Corrected 2026-09-14.

### What would have to change first

Not "run the synthetic control". The prerequisite is upstream of it:

| Prerequisite | Why | Status |
|---|---|---|
| Real opening dates, or a credible left bound per site | An event study cannot run on a right-censored bound | **PARTLY AVAILABLE as of 2026-09-15, and it did not help.** An OCR of an industry network PDF supplied **stated opening dates on 545 loadable facilities** — not bounds, actual claimed openings, validated against OSHA at 94.7% (`mwpvl_validation.json`). The hazard model was refitted on them with 5,441 events instead of 812 and the AUC moved 0.6894 → 0.6832. On the **130 facilities datable both ways**, the true-date arm scores AUC **-0.0043**, i.e. marginally *worse*; only **30** of those actually change date, so the control is too weak to detect a small effect. Verdict: *no measurable dating effect, on a control too weak to rule one out* (`hazard_revival.json`). Note also the counter-intuitive consequence: correcting a date **backwards** removes events by left-truncation, so the true-date arm has 2,666 events against the bound arm's 3,131 on identical buildings |
| Interval censoring in the risk-set builder | The specification the data actually calls for | **NOT STARTED** (`docs/STATUS.md`), and now blocked: interval censoring needs a lower bound, and the attempt to manufacture one failed |
| Clustered standard errors at the level of the building or metro-period | The catchment structure makes ZCTA-level observations pseudo-replicates, in a DiD as much as in a hazard model (Part 1 above) | **Not implemented anywhere in the project** |
| A donor pool that survives Gate 5 | Synthetic control needs clean, uncontaminated controls | **Gate 5 escalates often; the pool is thin** |
| More than 43 dated buildings | 43 treated clusters on the pilot frame, heavily overlapping catchments | **SOLVED, and it changed nothing. Updated 2026-09-15.** The pilot frame has 43; the 104-row national frame yields 94 usable decisions; the **693-row expanded frame yields 483 decisions and 687 loadable buildings across 230 CBSAs**. The count is no longer the constraint and this row should no longer be quoted as a blocker. What the extra sample bought was *precision*, not accuracy: the headline coefficient's interval narrowed 64% and **still covers the numeraire** |
| Geocoded facilities | Distance bands need distances from buildings, not from polygon centroids | **Not available, and now larger in absolute terms.** 0 of 693 expanded, 0 of 104 national and 0 of 43 pilot rows carry a latitude or longitude; everything falls back to ZCTA centroids |
| **Non-overlapping treated units** | A DiD inherits the same pseudo-replication the hazard model died of | **NOT SOLVED, and measured to be worse on the expanded frame. Added 2026-09-15.** One opening still switches on a **median 39 ZCTAs** (mean 52.4, max 317), and the radius sweep from 8.3 to 45 miles never brings it below 14. Worse, **58.4% of covered ZCTAs now sit inside two or more catchments** against mostly-disjoint catchments on the pilot frame, so a ZCTA's switch-on quarter is a joint function of several buildings' decisions — a *second* dependence layered on the first (`hazard_revival.json`, `independence_violation`) |

> **The satellite attempt, because it is the obvious next question.** The
> natural way to get the missing lower bound is imagery: OSHA says "operating
> by X", Sentinel-2 should say "not built before Y", and `[Y, X]` is the
> interval. It was run on 2026-09-14 over 107 sites and it **failed**. Only 41%
> of estimates landed within a year of a known opening, the error standard
> deviation was 3.42 years, and — the test that settles it — **39 of the 107,
> 36%, date construction to AFTER the day an OSHA inspector physically found
> the building operating**, by a median of 33 months. A lower bound that sits
> above a known upper bound is not a bound. Filtering on the script's own
> confidence score does not help: 35% impossible above confidence 2 versus 30%
> at 1–2. Full write-up in `HANDBOOK_02_DATA.md` Sec. 2.2.11. Do not treat the
> 68 survivors as usable dates; selecting them is selecting on the outcome.

> **The sentence to give an examiner.** *"The second estimand is unbuilt, and I
> would not build it on this target. It needs a treatment date and what I have
> is a censoring interval that ran to 345 months in one measured case. An event
> study on that would produce a confidently null result with a clean-looking
> pre-trend, which is the most dangerous kind of wrong. The prerequisite is
> better dates, not more estimation."*

That answer is worth more than a synthetic-control plot would have been,
because it demonstrates you understand what your own data can and cannot
support.

---

## 3.12 Part 3 self-check

1. State the fundamental problem of causal inference in one sentence.
2. Give the ICU example and explain what it illustrates.
3. What are the two conditions an instrument must satisfy, and which one cannot
   be tested?
4. Why is our instrument contestable, and what is the right way to handle that
   in a viva?
5. Explain synthetic control using the "Synthetic San Francisco" example.
6. Why is pre-treatment fit insufficient evidence?
7. Describe an in-space placebo test and explain what the RMSPE ratio fixes.
8. Give a concrete SUTVA violation in delivery terms, and say which direction it
   biases the estimate.
9. Why did an earlier draft's W claim fail, and what narrower claim survives?
10. What are the two outcomes of the pre-registered RQ2 test, why is each
    publishable, and what is the third outcome that actually occurred?
11. **Which of the methods in this chapter have been implemented?** (Correct
    answer: none of them. Say it without hedging.)
12. What is the only cannibalisation figure that exists in the codebase, where
    does it live, and why is it not an estimate?
13. Does the hazard model's failure condemn the cannibalisation estimand?
    Give all three parts of the answer, ending on the shared date defect —
    and say why "the diagnosis does not transfer" is the wrong answer.
14. Why is a 57-month dating error worse for an event study than for a hazard
    model? Work the example through.
15. Name the Train (2009) section the hazard model actually violated, quote
    the assumption in your own words, and give the two standard names for the
    failure. Then say why Train Sec. 2.2 is the *wrong* citation for it and
    the *right* citation for the successor's choice set.
16. Warning: this handbook has its own Sec. 3.7.1 and Train has his own Sec.
    3.7.1. What is each one about, and why does it matter that you keep them
    apart out loud?
17. What is the cheap standard fix for pseudo-replication in a DiD, and has
    this project implemented it?

---

**Next:** `HANDBOOK_04_MODELS.md` — hazard models, calibration, conformal
prediction, and what "accuracy" actually means.
