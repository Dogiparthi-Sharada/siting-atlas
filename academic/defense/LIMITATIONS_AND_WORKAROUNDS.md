# Limitations and Workarounds

**Every limitation, what it actually costs you, how to work around it, and what
you honestly cannot claim. Ends with: which of this survives on a résumé.**

> **The framing that makes this document worth reading.** A limitations section
> that lists problems is an apology. A limitations section that lists problems
> *with the workaround, the residual risk, and the cost of the workaround* is an
> engineering document. Reviewers and hiring managers respond very differently
> to the two.
>
> Two of these have genuinely good workarounds that most people miss. Two have
> partial ones. One has none, and saying so is the correct move.

---

# Part A — The two that sound fatal

These are the two you raised, and they are the two a reviewer will raise. Both
have better answers than they first appear to.

---

## A1. "The ACS data is two years old. How can this be useful?"

### The concern, stated fairly

American Community Survey 5-year estimates carry an 18–24 month reporting lag.
The "2023" release describes 2019–2023. A neighbourhood that gentrified in 2024
looks like its 2021 self. On the face of it, you are predicting today's decisions
with yesterday's world.

### Workaround 1 — the reframe that dissolves most of it

**The operator faced the same lag.**

When the operator decided in 2023 where to build, they were also looking at
ACS data from 2021–2022. They do not have a secret real-time census. Their
internal order data is current, yes — but their *demographic and economic
covariates are the same public releases we use, with the same lag.*

```
   OPERATOR'S DECISION IN 2023
     internal order history ......... current   (we don't have this)
     ACS demographics ............... 2021-22   (same as ours)
     property / rent indices ........ current   (we have this - monthly)
     wage data ...................... 2022      (same as ours)
     land and zoning ................ current   (we have this)
```

So on the covariate axis we are **not behind the decision-maker.** We are
missing their order history, which is a real gap and which is exactly why the
estimand is service enablement rather than volume.

> **How to say it in a viva:** *"The lag is real, but it's the same lag the
> operator's own planners faced. Nobody has a real-time census. The gap between
> us and them is order history, not demographics — which is precisely why we
> model the decision rather than the demand."*

### Workaround 2 — the decision is slower than the data

Siting decisions have **18–36 month lead times**: site search, lease
negotiation, permitting, fitout, hiring. A facility opening in 2025 was decided
in 2023 on 2021–22 data.

**So a two-year-lagged covariate is roughly contemporaneous with the decision it
explains.** Using this year's data to explain this year's opening would actually
be the *error* — it would use information the decision-maker did not have.

This is not a rationalisation; it is standard practice in any forecasting
problem with a decision lag. Aligning covariate vintage to decision vintage is
correct specification.

### Workaround 3 — for what genuinely changes fast, use a fast source

Not all covariates are slow. Blend by update frequency:

| Signal | Source | Frequency | Lag |
|---|---|---|---|
| Rent, home values | Zillow ZORI / ZHVI | **Monthly** | ~1 month |
| Construction activity | Census Building Permits Survey | **Monthly** | ~2 months |
| Business establishment counts | Census CBP | Annual | ~18 months |
| Wages | BLS OES | Annual | ~12 months |
| Energy prices | EIA | **Monthly** | ~2 months |
| Demographics | ACS 5-year | Annual release | 18–24 months |
| Demographics, large areas | **ACS 1-year** | Annual | **~9 months** |

**Two concrete additions worth making:**

1. **ACS 1-year estimates for large geographies.** Published for areas above
   65,000 population, with roughly a 9-month lag instead of 18–24. Not available
   at ZCTA grain, but available at metro and county level — so you can use
   it to *update the metro-level context* even when the ZCTA-level detail is
   older. A ZCTA in a metro whose 1-year estimates show sharp income growth can
   be adjusted accordingly.
2. **Building permits as a leading indicator.** The Census Building Permits
   Survey is monthly and is a genuine *forward* signal — construction
   precedes population. A ZCTA with a permit surge is changing now, regardless
   of what the 5-year ACS says.

> **Worked example.** ZCTA 78702 in Austin. ACS 5-year says median income
> $58,000 (reflecting 2019–2023). But Zillow shows rents up 31% since 2022 and
> the permits series shows 900 new units approved. The slow covariate says
> "moderate income area"; the fast covariates say "rapidly changing." Including
> both lets the model see the trajectory, not just the level.

### Workaround 4 — model the lag explicitly rather than ignoring it

Include **rate-of-change features** from the fast sources alongside the level
features from the slow ones. A model that sees `income_level` (lagged) plus
`rent_growth_12m` (current) can infer where the lagged level is heading.

### Workaround 5 — for the backtest, the lag is irrelevant

The out-of-time backtest trains on data available through 2023 and predicts
2024–25. **We are deliberately restricting ourselves to information available
before the prediction window.** That is what makes it a forecast rather than a
fit. Data recency is not a limitation of the backtest; it is a *requirement* of
it.

### Residual risk, stated honestly

A neighbourhood that changed sharply in the last 18 months and has *no* permit
or rent signal will be misclassified. We cannot fix that with public data. We
report it as a known failure mode and, where the fast and slow signals disagree
sharply, flag the ZCTA as low-confidence in the application.

### Cost of the workaround

Roughly **two days** to add ACS 1-year metro context, building permits, and
rate-of-change features.

---

## A2. "You can't measure revenue. What is the model even worth?"

This is the sharper of the two, and it deserves a longer answer.

### The concern, stated fairly

We cannot observe order volume, revenue, or margin per ZCTA. Those are the
operator's private numbers. So how can a net-present-value model mean anything?

### Workaround 1 — separate what needs revenue from what doesn't

This is the key move, and it is under-appreciated. **Most of the decision does
not require absolute revenue.**

| Output | Needs absolute revenue? | Why |
|---|---|---|
| **Which ZCTAs rank highest** | **No** | Ranking is invariant to a common scale factor |
| **Which bundles beat which** | **No** | Same — relative comparison |
| **Rank stability under uncertainty** | **No** | Ordering, not magnitude |
| **Break-even thresholds** | **No** | Expressed as ratios |
| **"Would they have built here anyway?"** | **No** | Pure propensity |
| **Timing window** | **No** | Hazard model output |
| Absolute dollar NPV | **Yes** | Needs margin per order |
| "This ZIP is worth $1.2M" | **Yes** | Needs margin per order |

**Six of eight outputs are unaffected.** The two that are affected are the two we
therefore do not claim.

> **Why ranking is scale-invariant.** If every ZCTA's revenue is multiplied by
> the same unknown constant *m*, the ordering does not change. `NPV_A > NPV_B`
> holds regardless of *m* as long as *m* is common. We do not know *m*. We do
> not need it to say A beats B.

### Workaround 2 — report NPV in units of margin

Instead of pretending to know *m*, **factor it out and let the reader supply
it.**

```
   Instead of:   "ZCTA 94608 has a five-year NPV of $1.2M"
                 (requires us to invent a margin)

   Report:       "ZCTA 94608 has a five-year NPV of 41,000 x m  -  $3.8M
                  where m is contribution margin per incremental order.
                  At m = $1.20 this is +$1.4M; at m = $0.80 it is -$0.6M;
                  break-even is m = $0.93."
```

**This is strictly more informative than a point estimate**, and it is honest.
Any reader with a view on margin — an operator, a consultant, an analyst
— can plug in their own number. A reader without one still gets the
break-even.

> **Precedent:** this is exactly how real-options and valuation work is
> presented when a key input is unobservable. You do not invent the input; you
> parameterise it and report the sensitivity.

### Workaround 3 — bound *m* from public disclosures

We are not entirely in the dark. Operators disclose, at company or segment level:
net sales, cost of sales, fulfilment expense, and shipping costs. Those bound
plausible per-order economics.

**The method:** derive a defensible range for *m* from disclosed aggregates, run
the NPV across that range, and report results as a band rather than a point. The
range comes from published filings, so it can be checked.

### Workaround 4 — validate the half you *can* observe

NPV has two sides. Revenue is hidden. **Capital is not.**

```
   NPV  =  [ revenue side ]  -  [ capital side ]
              hidden               PARTIALLY OBSERVABLE

   Operators disclose capital expenditure at company and often segment level.
   We aggregate our ZCTA-level capital estimates to metro level and compare.
   Target: within 25%.
```

**This is the only externally falsifiable number in the system, and it can
fail.** That is what makes it a real check. If our capital model is within 25%
of disclosed capex, the cost side of the NPV is credible even though the revenue
side is parameterised.

### Workaround 5 — change what you claim to predict

Already done, and it is the deepest fix. The **primary** output is not dollars.
It is:

- **Will the operator enable service here?** (observable, scoreable)
- **When?** (observable, scoreable)
- **Would they have built here anyway?** (the abatement counterfactual)

Those are the outputs a planner, an air district or a community group actually
needs, and **none of them requires revenue at all.** The NPV layer is a
secondary, clearly-labelled analysis for the operator-facing view.

### Workaround 6 — remember the operator doesn't know either

Their *forecast* of a ZIP's five-year NPV is also an estimate, built on assumed
margins, assumed adoption and assumed cost trajectories. They have better inputs.
They do not have certainty. The difference between us and them on the revenue
side is one of precision, not of kind.

This is not an excuse — it is a calibration of how much precision the
decision actually supports. A decision between "activate" and "don't" does not
need three significant figures.

### Residual risk, stated honestly

**If margin varies systematically across ZCTAs** — for example if affluent
areas have higher basket values *and* higher margins — then factoring out a
single *m* biases the ranking, not just the level. We cannot rule this out from
public data.

**Mitigation:** run the ranking under a margin that varies with median income
(a plausible worst case) and report how much the top-100 list changes. If it
barely moves, the constant-*m* assumption is safe for the decision. If it moves
a lot, we say so.

That sensitivity check is about half a day and it converts an unquantified
worry into a measured one.

### The sentence for the viva

> *"We make no accuracy claim on dollar NPV, because no public ground truth
> exists. We report NPV in units of contribution margin with break-even
> thresholds, we validate the capital side against disclosed capital
> expenditure to within 25%, and our primary outputs — will they build
> here, when, and would they have anyway — need no revenue estimate at
> all."*

---

# Part B — The rest, each with its workaround

---

## B1. Facility open dates are not opening dates

**Why it matters more than it used to.** This is the *target variable*, and
the delivered panel is worse than "may be wrong" — it is **knowingly
censored**. Most of the 43 rows are dated by the date the US Department of
Labor opened an OSHA inspection case at the address. That proves the
building was operating by then. It says nothing about when it opened.

**What changed in the workarounds, and why.** The original plan was to
hand-verify a random sample of 100 facilities and publish the error rate.
The delivered panel is **43 rows**, so a 100-row sample is not a sample —
there are not 100 facilities to draw from. That workaround was replaced.

**Workarounds as actually applied:**

1. **Census, not sample.** All 43 rows carry their source; the
   hand-researched subset carries a URL and a quotable sentence in
   `data/collection/results/DATES_FOUND.csv`. On a table this small a census
   costs less than a sampling design and has no sampling error.
2. **Measure the bound instead of assuming an error rate.** Five addresses
   appear both in MWPVL's 2012 census, which states real opening months, and
   in the OSHA extract. The bound **held 5 of 5** — no inspection predates an
   opening — and the lag was **4, 13, 57, 69 and 345 months**. One site
   opened in 1997 and was first inspected in 2026. That is a measured
   statement about how loose the bound is, which is what "publish the error
   rate" was trying to buy.
3. **Consume the date as an interval, not a point.** The hazard model takes
   `(panel start, X]`, so a loose bound widens an interval rather than
   fabricating an event at the wrong time.
4. **Use quarter, not month.** Coarser grain is more robust to date noise,
   and quarterly resolution is sufficient for a decision with an 18-month
   horizon.
5. **Triangulate where a second source exists.** Two independent sources
   make a date high-confidence; a single-source date is flagged. In practice
   this was possible for only a handful of rows.
6. **A noise simulation is still worth running** — corrupt *x%* of dates by
   ±1 quarter, re-run the backtest, report the degradation — but note that
   with at most 38 usable buildings the simulation's own variance is large,
   so report a range rather than a single point. And note the scale
   mismatch: a ±1 quarter perturbation is three months, while the *measured*
   lags run to 345. A one-quarter noise study is not a test of this problem.
   It is a test of a much smaller problem that we do not have.
7. **Present the conclusion as an assumption ladder**, not as a single
   result. This is the workaround that actually fits the size of the error,
   and it is set out below.

### B1.1 The assumption ladder — the honest way to report a bounded date

**The problem with every workaround above.** Each of them treats date error
as noise to be absorbed. It is not noise. It is a **one-sided bound with an
unknown width**, and the five cases where we can measure the width show it
ranging over two orders of magnitude. Averaging over that is not a summary;
it is a guess wearing a summary's clothes.

**The alternative.** Do not report one number. Report *how far the
conclusion survives as you weaken the assumption*, and name the point beyond
which the data stop speaking. Formally: let **L** be the maximum lag you are
willing to assume between the true opening and the OSHA inspection date. L
is a dial. Turn it and report what happens.

The panel runs 2018Q1 to 2025Q4 — **32 quarters, 96 months**. That length is
what makes the ladder finite, and it is what sets the breakdown point.

```
   L = maximum assumed lag (opening -> first OSHA inspection)

   L        covers    what it means for the analysis
   -------  --------  ----------------------------------------------
     0 mo    0 of 5   The naive specification: treat the inspection
                      date AS the opening date. This is what was
                      actually fitted. It failed on its own terms
                      before the date problem is even reached.

    13 mo    2 of 5   Dates are right to within about a year. The
                      quarterly grain absorbs most of this. Any
                      timing conclusion that survives here is
                      reasonably safe.

    57 mo    3 of 5   The MEDIAN measured lag. Nearly five years, or
                      59% of the entire panel window. A station
                      "opening" in 2023 may have opened in 2018.
                      Cohort-level statements start to dissolve.

    69 mo    4 of 5   Over seven years. The 2023 cohort -- the
                      largest in the panel -- becomes
                      indistinguishable from the 2018 cohort.

    96 mo    4 of 5   *** BREAKDOWN POINT ***
                      Exactly the panel length. At L = 96 every
                      dated facility could have opened before the
                      panel starts. Every unit is left-censored,
                      no unit contributes an event, and the data
                      are SILENT about timing. Not "imprecise" --
                      silent. There is nothing left to estimate.

   345 mo    5 of 5   Observed once (PHL1, opened Nov 1997, first
                      inspected Aug 2026). 3.6x the panel length.
                      Outside any analysis this panel can support.
```

**How to report a result on this ladder.** For any timing claim, state the
largest L at which it still holds, and state the breakdown point. For
example: *"the claim that openings accelerated after 2021 holds for L up to
13 months and does not survive L = 57; the data are silent beyond L = 96."*
That sentence is falsifiable, it is honest about what is assumed, and a
reader who thinks our lags are shorter than ours can read their own answer
off the ladder.

**Why this is the right presentation and not a dodge.** Three reasons worth
saying out loud.

1. **It matches the shape of what we know.** We know a *bound*, not a point.
   Reporting a point estimate from bounded data is the actual dodge.
2. **It puts the burden in the right place.** A reader who wants a tighter
   conclusion must argue for a smaller L, and the five measured cases are
   there to argue against. Nobody has to take our word for the width.
3. **It makes the breakdown point a finding.** "96 months of panel cannot
   survive a 57-month median labelling lag" is a concrete statement about
   what federal inspection records can and cannot support, and it is the kind
   of thing a city or a regulator can act on: an opening-date registry would
   be a small administrative object, and it would move L to zero.

**What the ladder does NOT rescue.** It is a presentation for *timing*
claims. It does nothing for the deeper problem, which is that the
ZCTA-quarter was never a valid alternative in the first place (see
`VIVA_QA.md` Part 0 and `HANDBOOK_04_MODELS.md`). Fixing the unit of
analysis and honestly bounding the dates are two separate repairs, and the
model needs both. Do not let the ladder's tidiness suggest that the date
problem was the only problem — it was not even the first one.

> **The sentence for the viva.** *"My dates are upper bounds, and I measured
> how loose: lags of 4, 13, 57, 69 and 345 months on the five cases where I
> can check. So I don't report a timing result, I report how far a timing
> result survives as you weaken the assumption, and I name the point — 96
> months, the panel length — beyond which the data are silent. The median
> measured lag is already 59% of the way there."*

**Residual risk, and it is larger than the date noise.** The sample is
selected on workplace injury, so it under-reports small delivery stations
relative to large fulfilment centres, and it over-reports metros with active
state-plan OSHA programmes. Seattle contributes 11 of 43; Nashville, a
*fitting* metro, contributes **zero**, because all five of its OSHA
addresses are fulfilment centres. A coefficient that looks like a Seattle
effect may be an inspection effect.

**Cost:** already paid. See
[`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md).

---

## B2. Modifiable areal unit problem (MAUP)

**The problem.** Results can change if you redraw the boundaries. ZCTAs are
postal constructs, not statistical ones, and they change between vintages.

**Workarounds:**

1. **Pin one vintage** (2020) and document the crosswalk. Never mix.
2. **Contract-test the ZCTA count.** If the count changes between runs, fail the
   build. Vintage mixing is a *silent* failure otherwise — it produces a
   plausible-looking series with fabricated discontinuities.
3. **Re-run at H3 hexagonal grain.** Hexagons are a completely different
   partition with no postal logic. If the conclusion survives, MAUP is not
   driving it. **This is the actual defence**, and it is the one spatial
   reviewers want to see.
4. **Report both** in an appendix.

**Residual risk:** if H3 and ZCTA disagree, you have a finding you must report
rather than a result you can present. That is the right outcome.

**Cost:** ~1 day.

---

## B3. Donor-pool scarcity

**The problem.** Synthetic control needs untreated comparison units. As a
network saturates nationally, that pool shrinks — and units adjacent to
treated ones are contaminated by spillover.

**Workarounds:**

1. **Use the decay radius (Part 3 of the handbook) to define contamination
   precisely.** Rather than excluding all neighbours, exclude only units within
   the *measured* spillover radius. This is a direct payoff from estimating the
   decay curve: it recovers donors that a conservative contiguity rule would
   have thrown away.
2. **Exploit staggered adoption.** Units treated *later* serve as controls for
   units treated *earlier*, before their own treatment. This is standard in
   modern DiD and substantially expands the effective donor pool.
3. **Widen geographically.** Donors need not be in the same metro — they
   need to match on pre-treatment trajectory. A Nashville ZCTA can be a donor
   for an Austin one.
4. **Report donor-pool size and weight concentration** as a diagnostic. If one
   donor carries 80% of the weight, the estimate is fragile and readers deserve
   to know.

**Residual risk:** in the most saturated metros there may be too few clean
donors for a credible estimate. Where that happens, we report "not estimable"
rather than producing a number.

**Cost:** ~2 days.

---

## B4. Generated regressors

**The problem.** Facility attributes extracted from text by a language model
enter the estimators as if measured without error. This **understates standard
errors** — you look more confident than you are.

**Workarounds:**

1. **Design-based supervised learning** (Egami et al., NeurIPS 2023) or
   prediction-powered inference (Angelopoulos et al., *Science* 2023). Both
   correct downstream inference using a hand-labelled subsample.
2. **A hand-labelled validation set now exists, and it arrived by accident.**
   This item used to read "the hand-labelled sample from B1 does double duty —
   it is exactly the validation set these methods require." **That was false
   when written: no such sample existed.** B1's own body says the plan to
   hand-verify a hundred facilities was abandoned because the panel had only
   43 rows. One does exist now: 122 of the 362 hand-labelled sites are
   independent confirmations of classifications the pipeline had already made,
   each from a different public source with a quote and a URL. They are a
   validation set for the name-based classifier in `ingest/osha.py`. They were
   produced by a bug rather than by design — see B10 — and the correction
   methods above have still not been applied to anything.

**Residual risk:** the correction is not applied. This is a solved problem in
the literature that this project, like most, simply has not applied. Saying
"none material once corrected" invites the reader to assume it was corrected.
It was not.

**Cost:** ~1 day, and it is one of the strongest rigour signals in the project.

---

## B5. Proxy validity generally

**The problem.** Zillow residential indices proxy commercial land cost. CBP
establishment counts proxy retail attractiveness. Neither is the thing itself.

**Workarounds:**

1. **The external check** (metro capital vs disclosed capex) validates the
   *composite*, which is what matters. Individual proxies can each be imperfect
   while the aggregate is calibrated.
2. **Sensitivity analysis per proxy** — the tornado plot shows which proxies
   the conclusion depends on. If the ranking is insensitive to the retail-density
   proxy, its imperfection is irrelevant to the decision.
3. **Report the correlation** between each proxy and any partially-observable
   ground truth available.

**Residual risk:** a proxy that is biased in a way correlated with the outcome
would bias results systematically. The equity audit is partly designed to detect
this.

**Cost:** included in the sensitivity work already planned.

---

## B6. ACS margins of error

**The problem.** At ZCTA grain, ACS estimates carry substantial margins of
error. Two ZCTAs reported at $71,000 and $68,000 median income may be
statistically indistinguishable.

**Workarounds:**

1. **Carry the MOE through as an uncertainty input** to the Monte Carlo, rather
   than treating point estimates as exact. ACS publishes the MOE for every
   estimate; most analyses discard it.
2. **Flag ZCTAs where the MOE exceeds a threshold** as low-confidence in the
   application.
3. **Prefer ratios and ranks over levels** where possible, since they are less
   sensitive to estimate noise.

**Residual risk:** small-population ZCTAs will remain noisy. Reported.

**Cost:** ~0.5 days.

---

## B7. Selection and the exclusion restriction

Covered fully in Handbook Part 3. Short version: the instrument is contestable,
so we report the first-stage F-statistic, run a sensitivity analysis under
assumed small direct effects, and state the residual risk rather than claiming
the restriction holds.

**The meta-point:** naming your own weakness before the reviewer does converts an
attack into evidence of rigour. This is the single most useful defensive move in
the project.

---

## B8. The headline covariate may contain its own outcome

**This is the top open defect in the project and it has no workaround yet, so
it is listed in Part B only because a route to one exists.**

**The problem.** An Amazon delivery station *is* a warehousing establishment —
NAICS 493 is warehousing and storage, and a delivery station falls inside it.
The model's only working covariate is the count of NAICS 493 establishments in
a ZCTA. A contemporaneous count therefore contains the outcome, and the model
would look excellent for the worst available reason.

**The guard that exists.** `ingest/cbp_detail.py` scores every facility on the
latest County Business Patterns vintage *strictly earlier* than its recorded
`open_year`. Six facilities that opened in 2017 or earlier have no clean
vintage and are dropped rather than scored, which is what takes the sample from
100 decisions to 94. The design is right.

**Why the guard is nominal.** `open_year` is not an opening date. On **all 100
loaded national rows** it equals the quarter of the earliest OSHA inspection —
the "operating by" upper bound of B1, restated in a column with a misleading
name. A building first inspected in 2022 may have opened in 2017, in which case
the "strictly earlier" 2021 vintage already counts the facility itself. The
five addresses with an independently known opening month give lags to first
inspection of 4, 13, 57, 69 and 345 months.

```
  lag from opening to first OSHA inspection, the 5 measured cases
    4 months     guard holds
   13 months     guard FAILS
   57 months     guard FAILS
   69 months     guard FAILS
  345 months     guard FAILS

  the guard clears 12 months.  4 of the 5 exceed it.
```

**Workarounds, in order of how much they would buy:**

1. **A genuine lower bound on opening dates**, from county building permits or
   industrial REIT property schedules. Both are public and neither has been
   worked through. This is the only route that fixes the defect rather than
   bounding it. The satellite attempt was the cheap version of it and it failed
   (B9).
2. **Widen the lag to the measured median.** Scoring on a vintage five years
   earlier than the bound would clear four of the five measured lags, at the
   cost of dropping every facility whose bound falls before 2021 and of
   measuring a ZCTA's industrial character half a decade stale. Not obviously
   worth it, and not done.
3. **Report the defect and decline to interpret the coefficient.** This is what
   is currently done, and it is a disclosure rather than a workaround.

**Residual risk: HIGH and unmitigated.** It does not explain the headline away
— the fitted model does no better than the raw covariate either way, so the
defect cannot be what makes the model look bad. But it means the one thing that *does* rank
well may rank well partly because it contains the answer, and nothing
currently distinguishes "Amazon builds where warehouses are" from "Amazon's
warehouse is in the warehouse count".

> ## Downgraded 2026-09-15 — MEDIUM, and partly mitigated. The workaround listed above as "the only route that fixes the defect" was executed.
>
> **Everything above this block is still an accurate description of the
> problem and of the guard. What has changed is that the guard has now been
> tested rather than merely disclosed.** Artefact
> `outputs/metrics/leakage_decisive.json`, write-up
> `../research/NOTES_LEAKAGE_DECISIVE.md`.
>
> **What was run.** Three arms, one codebase, one seed, 50 paired re-splits
> refitting inside every repeat, all three restricted to the **same 29
> decisions** so that the comparison cannot confound leakage with sample
> size:
>
> ```
>   osha_bound     CBP vintage chosen off `open_year`     -- the status quo
>   true_date      CBP vintage chosen off the MWPVL
>                  STATED opening year
>   no_covariate   warehousing removed entirely           -- the floor
> ```
>
> **The result.**
>
> ```
>                        top-10 of 12    lift     Brier    beta warehousing
>   osha_bound                9.24       4.36   0.008771   4.24 [2.32, 16.97]
>   true_date                 8.22       3.88   0.008889   3.68 [2.05, 14.06]
>   no_covariate              4.48       2.11   0.009752   --
>   uniform null              2.12
>
>   paired over the same splits
>     osha_bound - true_date       +1.02 hits (sd 1.02)   34 W  13 T   3 L
>     true_date  - no_covariate    +3.74 hits (sd 1.40)   50 W   0 T   0 L
>     osha_bound - no_covariate    +4.76 hits (sd 1.64)   50 W   0 T   0 L
> ```
>
> **The covariate survives. It keeps 3.74 of the 4.76 hits it is worth —
> 79% — on vintages that strictly precede the building's stated opening, and
> it clears the no-covariate floor on 50 of 50 splits.**
>
> **And a second, model-free measurement points the same way.** Divide each
> beta by its own column mean, which puts both on the raw column: the
> per-establishment weight ratio between the two arms is **1.012**. *The
> price of an establishment is the same to within 1.2%.* What changes between
> the vintages is the **level** of the column, not the model's use of it.
> That is what agglomeration looks like and it is not what a contaminated
> regressor looks like — a self-counting covariate would show a changed
> price, not a changed level.
>
> **Why the risk is MEDIUM rather than LOW. Four reasons, and give all
> four.**
>
> 1. **The test cost two thirds of the sample.** 100 decisions with no
>    industry covariate, 94 with a clean-enough vintage, **29** with both a
>    stated opening date and a vintage before it. 65 lost. With 40% held out
>    the test set is **12 decisions** and the fit runs on 17 against 3
>    parameters — 5.7 events per parameter, well under the floor of 10.
> 2. **The intersection is not a random subsample and it is measurably
>    easier.** `osha_bound` scores 9.24 of 12 here, 77%, against 20.60 of 38
>    on the full 94, which is 54%. These 29 are the buildings MWPVL happens to
>    list and the address matcher happens to reach. Nothing here transfers to
>    the other 65 without that assumption being stated out loud.
> 3. **The leak and the staleness are the same intervention.** `true_date`
>    reads a vintage that is older *as well as* cleaner — a median two years
>    older. Nothing in this design separates "the facility left the count"
>    from "the count is now two years out of date", so **the +1.02 hit gap is
>    an upper bound on the leak, not a measurement of it**.
> 4. **A self-count check that needs no model finds real self-counting.** For
>    each of the 29, how much did warehousing rise in the ZCTA the building
>    went into, against the average alternative in the same metro over the
>    same two vintages?
>
>    ```
>      chosen ZCTA           +1.17 establishments
>      average alternative   +0.13
>      excess                +1.04   (sd 2.56, MEDIAN 0.00)
>      chosen ZCTA gains at least one     11 of 29
>    ```
>
>    **The excess is one establishment, which is exactly the size of the
>    object being predicted**, and that coincidence should not be waved away.
>    But the median is zero and the sd is 2.56: it is a mean carried by a
>    minority. The honest statement is that self-counting is present and real
>    in about a third of the sample, and the prediction test says it is worth
>    about a fifth of the covariate's value.
>
> **One further caveat that cuts at the headline set itself.** 14 of the 29
> stated dates come from an MWPVL table for a *different facility class* —
> cross dock, fulfilment centre, sortation centre, fresh hub, heavy/bulky —
> matched on the same street address. Restricting to the two delivery-station
> tables halves the sample and the difference disappears into noise: 15
> decisions, 6 held out, +0.34 hits with 24 wins, 15 ties and 11 losses. Six
> held-out decisions settle nothing in either direction, and it is reported
> so the headline set is not the only number on the page.
>
> **Nothing was corrected.** Two of the 29 stated dates are *later* than the
> OSHA bound for the same building, which the project's own `E_operating_by`
> edit calls impossible. They are used as stated, because dropping the pairs
> that disagree in the inconvenient direction is how a leakage test is
> rigged.
>
> **The claim you may now make:** *"The warehousing covariate carries genuine
> agglomeration signal, audited on 29 decisions whose Census vintage strictly
> precedes the building's stated opening, with a roughly 20% haircut of
> unknown split between self-counting and staleness."*
>
> **The claim you may NOT make:** that this holds on the 65 decisions the
> audit could not reach.

**The uncomfortable framing, which should be volunteered:** this is the third
place in the project where a variable turned out not to be the thing its column
name said, and the second instance of circularity specifically. The first was
caught in design (a constructed order-volume target predicted from its own
inputs). This one got as far as the published result.

**Cost:** unknown, and dominated by the date-collection problem. Days if
permits are scriptable for a few counties; weeks nationally.

---

## B9. Satellite dating was attempted and it failed

**The problem it was meant to solve.** B1 leaves every date as an upper bound.
A *lower* bound would turn each into an interval, which is the input interval
censoring needs, the timing factor the decomposition needs, and the clean lag
B8 needs. One attempt could have closed three defects.

**What was tried.** Sentinel-2 photographs every point on Earth every five
days, free, back to 2015. When a delivery station is built, bare ground becomes
a large bright roof and a car park. A changepoint detector on the reflectance
series should find the month the ground changed.
`data/collection/satellite/colab_date_from_satellite.py`, run in Google Colab
on 2026-09-14.

```
  sites attempted                     107
  sites that returned an estimate     107     (100%)
  median cloud-free scenes            106

  validation on the 83 with a known opening year
    within 1 year                      41%
    error standard deviation          3.42 years

  the logical test, on all 107
    dated AFTER the day an inspector
      found the building operating     39 of 107   (36%)
    median lateness of those 39         33 months

  does the confidence score separate them?   NO
    impossible at confidence > 2        35%
    impossible at confidence 1-2        30%
```

**Why the logical test is the one that matters.** A 41% hit rate within a year
could be argued into usefulness for coarse work. An estimate that dates
construction *after* the building was observed operating is not imprecise, it
is impossible, and more than a third of them are. And because the confidence
score does not discriminate, there is no filter that rescues the good ones: the
68 estimates that pass are not a trustworthy subset, they are the ones that
happened to land on the right side of a test a third of their siblings fail.
**They are not presented as dates anywhere and must not be.**

**Workarounds:**

1. **Fix the detector, not the data source.** A median of 106 cloud-free scenes
   per site is ample. The failure is in changepoint selection — most likely a
   seasonal or resurfacing transition being taken for construction. Constraining
   the search to end before the OSHA bound would make the impossible estimates
   arithmetically unreachable, which is a crude fix that at least stops the
   worst output.
2. **Change the target.** A binary "was this site built out between year A and
   year B" is a much easier question than a date, and it is enough to bound the
   CBP vintage in B8.
3. **Abandon and use permits.** See B8 workaround 1.

**Residual risk:** the route is unsuccessful rather than closed, and nothing
downstream depends on it having worked.

**Cost of the attempt, already spent:** one Colab run and the scripting around
it. **Cost of a retry:** a day on the detector, and it is worth it, because
three separate defects are waiting on it.

**The artefact lives outside the repository**, at `../satellite_dates.csv`
relative to the repo root. Getting it under version control with everything
else is an outstanding item.

---

## B10. The labelling programme was generated against the wrong reference

**The problem.** Six batches, 362 OSHA sites hand-classified against public
sources over four evenings. 135 of them are delivery stations. **Thirteen are
genuinely new** to the delivered facility frames, and **289 of the 362 worklist
rows — 80% — were already classified** in
`data/collection/results/NATIONAL_CLASSIFIED.csv`.

The cause is ours. `scripts/make_unlabelled_batches.py` selected the rows the
OSHA name regex could not classify and never checked them against
`NATIONAL_CLASSIFIED.csv`, which is the file the national frame was built from.
The worklist was called unlabelled and was mostly labelled. The same error —
comparing against the wrong reference — then recurred inside the same
programme, when batch 6 was predicted to yield zero new sites and yielded three.

**The recoverable half, and it is real.** The 122 rows that were neither new
nor unclassifiable are **independent confirmations of classifications the
pipeline had already made**, each from a different public source, each with a
quote and a URL. That is a validation set for the name-based classifier in
`ingest/osha.py`, and it is the artefact B4 wrongly claimed to have. It was
produced by accident.

**Workarounds:**

1. **Use the 122 as the validation set B4 needs.** Not yet done. The
   classifier's measured accuracy against them has not been computed, and it is
   an afternoon's work.
2. **Fix the generator before any seventh batch.** Three lines. Not done, so a
   batch generated today would repeat the error.

**Residual risk:** low going forward, once the generator is fixed. The cost is
sunk.

**The honest yield figure, which should be stated before the recovery:**
13 new facilities from 362 labels is under 4%. A correctly generated worklist
would have been most of the way to 100%. The programme delivered two things at
roughly seven times the necessary cost.

---

## B11. Two of three fitted coefficients sit on a boundary

**The problem.** The choice model parameterises `beta = exp(theta)` so the
attraction index stays positive and its logarithm exists. A consequence nobody
wrote down in advance: **no coefficient can be negative.** A repelling variable
cannot be represented at all. The best it can do is run to the boundary at
zero, which is what `land_area_sqmi` and `establishments` both did —
`theta` of -35.7 and -35.3, i.e. `beta` of about 3e-16 and 5e-16.

Two consequences follow.

1. **The "density preference" reading was never available.** The proposal
   argued that a positive loading on households beside a negative loading on
   land area would express a density preference without any intensive variable
   entering the model. It cannot: the negative loading is forbidden by the
   functional form. That claim has been withdrawn from the proposal.
2. **A sandwich standard error is undefined there.** It is derived from the
   asymptotic normality of the score at an interior maximum where the gradient
   vanishes (Train §8.6 p. 201). At a boundary it does not vanish, so a number
   computed there would be meaningless rather than merely wide.

**Workarounds:**

1. **Refuse the sandwich at the boundary and print the reason.** Done — the
   inference code declines rather than emitting a number.
2. **One-sided bootstrap intervals instead**, since the sampling distribution
   has an atom at zero and a two-sided interval would be a fiction. Done: about
   80% of replicates sit at the boundary for each of the two.
3. **Report a parameter count of one, not three.** Not done in the artefact,
   and worth doing in the write-up.

**Residual risk:** interpretive rather than statistical. The danger is a reader
seeing "three parameters" and inferring three estimated quantities.

---

## B12. The bootstrap's resampling unit changes the answer by a factor of two

**The problem.** The specification says resample *decisions*, never rows, which
is the lesson the hazard model taught expensively. There is a level above that
it does not mention. The 100 loaded national facilities fall in only 62 metros,
and Los Angeles alone contributes seven — all facing the same choice set with
the same attraction values. Resampling decisions treats those seven as seven
independent draws. Resampling metros treats them as one.

```
  95% interval on the warehousing ratio, null is 1.0
    bootstrap over decisions     [0.760,  4.762]
    bootstrap over metros        [0.702, 10.013]
```

Both cover the null, so the conclusion does not turn on the choice — this time.
The upper endpoint moves by a factor of two, so on some other question it would.

**Workarounds:**

1. **Report both and quote the metro-clustered one**, which is the
   conservative figure. Both are computed; the convention is not yet written
   into `MODEL_SPEC.md` §6.3, which is silent on the question.

**Residual risk:** low, and the fix is a sentence in the specification.

**The pattern worth naming:** this is the clustering error that killed the
hazard model, appearing for the third time, one level further up each time.
ZCTA-quarters within a catchment; decisions within a metro; and it will appear
again wherever the project counts something that is not what it looks like.

> **Updated 2026-09-15 — and the direction of the effect does NOT
> generalise, which is a limitation of this entry.** Two more measurements
> now exist and they disagree with each other about which interval is wider.
> On the ZIP-grain network arm the metro-clustered *sandwich* is roughly
> 24-32% wider than a re-split spread, while the metro-clustered *bootstrap*
> on the one column that matters is somewhere between 5% and 13% wider
> depending on which run of `network_inference.json` you read. On the
> metro-entry problem it **reverses**: the re-split spread is width 0.102 and
> the 2,000-draw metro-clustered bootstrap is width 0.070, i.e. the bootstrap
> is **31% narrower** (`NOTES_METRO_ENTRY.md` §7).
>
> That is not a contradiction, and the explanation matters more than the
> numbers: **re-splits refit the model inside every repeat and so include
> estimation variability; a bootstrap over fitted predictions conditions on
> the model and measures only the sampling variability of the metric.** They
> are different objects. `PREREG_METRO_MODEL.md` §6 states the 24-28% figure
> as though it were a constant; it is not, and `NOTES_METRO_ENTRY.md` §7
> flags that explicitly.
>
> **The rule that survives all versions is the negative one: never quote a
> percentile spread across re-splits as a standard error.** Do not carry a
> direction or a percentage forward without re-reading the artefact.

---

## B13. Eight of twelve pre-registered covariates could not be used at all, because the panel's economic columns are single-vintage broadcasts

*Added 2026-09-15. `NOTES_METRO_ENTRY.md` §8; artefact
`outputs/metrics/metro_entry.json`, `vintage_gate` and `deviations`.*

**The problem.** A covariate can only predict year *t* if a vintage of it
exists that was published before *t*. Most of this panel's columns fail that
test not marginally but completely: they are **one value repeated across
every quarter**.

```
  mean distinct values per unit, all 32 quarters of panel.parquet
  ---------------------------------------------------------------
  population, households, median_household_income      1.00
  traffic_proximity, diesel_pm                         1.00
  wage_all_occupations, wage_freight_handler           1.00
  metro_employment                                     1.00
  permit_units_total                                   4.97   (annual, real)
```

The vintages behind them:

```
  households, population, income   ACS 5-year 2023        usable 2024+
  traffic_proximity, diesel_pm     EJScreen 2024          usable 2025
  wages, metro_employment          BLS OES oesm25ma.zip   NEVER usable
  permit_units_total, yoy          Census BPS, annual     usable at lag 1
```

The ACS 5-year 2023 file is built from responses collected 2019-2023. Using
it to predict 2020 is not a borderline publication-lag call: **three of its
five collection years are after the outcome**.

**What it cost.** Enforcing the pre-registration's own vintage rule removed
**8 of 12** registered covariates. Two more — the permit columns — then
failed a 90% coverage floor, because the Census permits ingest covers about
745 counties for 2017-2021 and about 3,022 for 2022-2025, which at metro
grain is 24% of metro-years in 2019-2022 against 97.8% in 2023-2025. A
complete-case fit on a quarter of the universe selects on data availability,
and availability correlates with metro size. **The verdict arm therefore has
two covariates.**

**Why this is a limitation and not an excuse.** It means the hypothesis that
motivated the metro test — that county-grain covariates would work at metro
grain because their variation is between counties — **was never actually
tested**. That has to be said in the same sentence as the H0 verdict, not in
a footnote.

**Workarounds, in order of how much they would buy:**

1. **Fetch the historical vintages.** ACS 5-year releases back to 2013, BLS
   OES back further, and EJScreen annually are all free and all downloadable.
   Nothing about this is hard; it was not done. This is the only route that
   makes the Tier 1 hypothesis testable, and it is the highest-value open
   item in the project.
2. **Use the one column that is a real time series.** `permit_units_total`
   has 4.97 distinct values per unit and is genuinely annual. It survives the
   vintage gate and dies on coverage — a county-level backfill would recover
   it.
3. **Report the drop and count it**, which is what was done, and which is a
   disclosure rather than a workaround.

**Residual risk: HIGH for the *comparative* claim, LOW for the verdict.** The
verdict survives because the leakage-permitted arm — seven covariates
including households, allowed to see the future — *also* loses, 6 of 7 on AUC
and 7 of 7 on calibration. If that arm had won, this entry would be the whole
story instead of a qualification.

**Cost of the workaround:** a day or two of ingest work per source, and no
methodological difficulty at all. That is the uncomfortable part.

---

## B14. Two figures asserted results the project does not have

*Added 2026-09-15. Found in `docs/data/FIGURES.md`; remediated in
`tools/figures/fig_methods.py`.*

**The problem, stated without softening.** `fig05_decay` plotted a
cannibalisation decay curve from nine hand-typed effect values, wrapped in a
shaded band **labelled "95% CI"**, with one point annotated **"n.s."** — and
on a y-axis of **2-day order volume, a variable that does not exist in this
project's data**, whose absence is the documented reason the cannibalisation
estimand was abandoned. Its caption said "values are illustrative pending
estimation". `fig07_tornado` typed in eight bucket swings, printed per-bar
dollar labels, carried **no disclosure at all**, and its caption asserted the
three-quarters split as measured fact.

**Workaround applied, 2026-09-15:**

1. **The interval, the significance annotation and the per-bar labels are
   gone.** Both figures now carry no numbers on the affected axis at all
   (`set_yticklabels([])`, `set_xticklabels([])`), with an inline comment
   saying why: *"no numbers: none of them are measured"*.
2. **An `ILLUSTRATIVE ONLY` banner sits inside the axes**, not in the
   caption, because figures get cropped into slides and captions do not
   travel with them.
3. **The claim was reduced to what is defensible.** Figure 5 now only makes
   the pedagogical point that a decay curve is what should define a spatial
   weights matrix rather than an arbitrary contiguity rule. Figure 7 now
   claims only the *ordering*, which follows from the cost model's own
   structure — driver time at the door is 66.5% of the per-stop bill.

**Residual risk: MEDIUM, and it is a process risk rather than a numerical
one.**

- **The invented magnitudes are still drawn**, just unlabelled. Figure 7's
  eight swings are typed constants. Making it real means decomposing the 500
  Monte Carlo draws by bucket — about a day's work, listed as open.
- **This was the second occurrence, not the first.** The same defect class
  had already been purged from two other figures, one of which had printed a
  target AUC of 0.84 under an ROC curve synthesised to have that area. A
  project that catches this twice has a habit, not an accident.
- **The document that records the finding is untracked.**
  `docs/data/FIGURES.md` and `docs/AUDIT_2026_09_14.md` are on disk and not
  under version control. The code fixes are in tracked files. So a clean
  clone contains some of the retracted material and not all of the
  retractions.

**Cost of the workaround:** about two hours for the restyle. The remaining
day of work is the honest fix.

**The framing to use if this comes up.** Do not argue that two figures out of
fourteen is a small proportion. Say what was wrong, say that the project's
own audit found it and wrote it down, say that the audit is readable, and
then say what is still open. An examiner weighing integrity is watching
whether the concession has to be dragged out.

---

## B15. Two bugs in the estimator, one of which flattered the fit

*Added 2026-09-15. `src/siting_atlas/models/choice.py` lines 271-334.*

**Bug 1 — a NaN that could never be displaced.** `choice.fit` runs five
starts and keeps the best by `r.fun < best.fun`. Every comparison against NaN
is False, so a NaN from the *first* start was never displaced by any later
start however good, and the function returned an all-NaN `beta` with no error
and no warning. **Guard:** skip non-finite starts, and raise if all five
fail, because a caller that gets an exception stops and a caller that gets
NaN carries it into a published number.

**Bug 2 — an infeasible optimum, and this is the dangerous one.** The choice
probability is only a probability while `beta'a > 0` for every alternative.
The `beta = exp(theta)` parameterisation guarantees that **only while every
attraction column is non-negative**, which stops being true the moment a
centred or log-relative column is added. Measured on the log-relative arms:

```
  coefficients driven past the feasibility ceiling      20x to 77x
  non-chosen alternatives pushed below zero          765 to 4,816
  P(chosen) inflated                          0.078685 -> 0.079346
  log-likelihood raised by                             up to 1.20
  terms in the objective that became undefined                  0
```

**Nothing complained, because nothing was undefined.** The tell was that in
all five columns, *the direction with the lower feasibility ceiling was the
one that "found" a coefficient* — success was predicted by how cheap it was
to violate positivity. **Guard:** check `beta'a > 0` at the optimum and raise
with the fix in the message. Note the first guard does not catch the second:
an infeasible optimum has a perfectly finite log-likelihood.

**Residual risk: MEDIUM, and the honest reason is coverage rather than
these two bugs.** The project's own audit reports **39 of 133 source modules
never imported by any test, 20 of them the two-day sprint**, and
`models/choice_runner.py` — the module that writes the headline artefact — is
among the untested. Both bugs were found by a result that looked slightly too
good and had no explanation, which is a habit rather than a test suite.

**Workaround:** the two guards are in place and both raise rather than warn.
The real fix is test coverage on the sprint modules, and it is open.

**A related instability that was deliberately NOT patched.** The GBM
benchmark's single-split figures move by up to 2 of 38 decisions under a
perturbation of 1e-12 — about what a parquet float round-trip costs — while
the conditional logit and the raw count do not move at all. Setting
LightGBM's determinism flags was tested and returned bit-identical counts in
all eight comparisons, because the call was already reproducible on identical
input; the sensitivity is to the **data**, and no flag removes it. The
remediation is a `headline_split_warning` field in the artefact instructing
readers to quote `across_repeats` instead. **Patching it would have bought a
false sense of a fix and cost a re-emit of published numbers.**

---

# Part C — What has no workaround

Being straight about this is what makes Parts A and B believable.

### C1. We cannot observe order volume, revenue or margin

No public source provides it. No clever transformation recovers it. We
parameterise it (A2), we validate the capital side (A2 workaround 4), and we
make **no accuracy claim** on dollar figures.

### C2. We cannot validate the cannibalization coefficient directly

We estimate it from observable proxies with a credible design, but there is no
public number to check it against. We report the placebo distribution, the
confidence bands and the decay curve. We do not claim it is *right* — we
claim it is *identified under stated assumptions*, and we show what happens if
those assumptions are relaxed.

### C3. We cannot see internal constraints

Corporate real-estate portfolios, existing lease obligations, internal capital
rationing, executive preference, and decisions we would consider mistakes. These
are unobservable and they are part of why the model is framed as
**operator-consistent desirability** rather than viability.

### C4. Public data has an accuracy ceiling below what the decision needs —
and on this frame we have now measured it

**This entry used to be written in the conditional. It is not conditional
any more.** It said: *"it is possible that the ceiling is too low for the
tool to be decision-grade, and we will report that if it happens."* It
happened. Here is the report.

The siting model was fitted on the real 43-building panel and it lost to a
model that predicts the same constant everywhere:

```
                                   model      null      verdict
  ------------------------------------------------------------------
  AUC (ranking)                    0.6894    0.5000     model better
  Brier (accuracy)                 0.01952   0.01961    +0.5% skill
  ECE  (calibration)               0.00863   0.00005    NULL ~170x better
  ------------------------------------------------------------------
  Brier skill, temporal hold-out            -0.02091    NULL better
  Brier skill, geographic hold-out          -0.06184    NULL better
  ------------------------------------------------------------------
  covariates distinguishable from zero       1 of 3     households only
  events per parameter                       7.6        floor is 10
```

Source: `outputs/metrics/hazard_report.json`; regenerate with `make model`.

**Two caveats in both directions, so the finding is not oversold.**

*Against reading this as a clean measurement of the ceiling:* the
specification itself was wrong. The ZCTA-quarter is not an independent
observation, because a station switches on a whole 15-mile catchment at once
(median 58 ZIPs, mean 88, largest 307), and the likelihood assumes
independence across observations — Train §3.7.1, p. 61. (Earlier versions of
this entry cited Train §2.2 on mutual exclusivity. That was the wrong section:
§2.2 governs a choice set facing a decision maker, and Train calls the
criterion "not restrictive". The failure is clustering.) So this result
confounds "public data cannot do it" with "we asked the wrong question of it".

**That was the caveat as written, and it contained a labelled prediction. The
prediction has now been scored, and this is the most important paragraph in
this file.** It said: *"A correctly specified conditional-choice model on the
same 43 buildings might do better. It would still face 43 decisions and 7.6
events per parameter, so it will not do much better — but that is a prediction,
not a measurement, and it should be labelled as one."*

The correctly specified conditional-choice model was built and fitted, on the
national frame rather than the 43-building pilot. The prediction was
directionally right and wrong about the mechanism.

```
  what was predicted            what happened
  ------------------------------------------------------------------
  43 decisions                  94 decisions, national frame
  7.6 per parameter, below      18.7 per parameter in estimation,
    the floor of 10               ABOVE the floor
  "will not do much better"     it does not do better at all.  Held out,
                                  38 decisions:

     the fitted model         top-1  7/38   top-5 16/38   top-10 19/38
     warehousing count alone  top-1  8/38   top-5 16/38   top-10 20/38
     uniform within metro     top-1  1/38   top-5  3/38   top-10  7/38

  the reason predicted         small sample, power below the floor
  the reason measured          NOT power.  The floor was cleared and the
                                 estimation still bought nothing: a single
                                 raw Census covariate with zero parameters
                                 MATCHES the fitted three-parameter model
```

Source: `outputs/metrics/choice_report.json`. **Say "matches", not "beats".**

> **Corrected 2026-09-14, and read what it does and does not undo.** The line
> above used to read **"Say 'beats', not 'matches'"**, and the box above it
> said the raw covariate **BEATS** the fitted model; an earlier internal note
> that said "matches" was overruled here as erring in the flattering
> direction. That overruling was itself the error. "Beats" was read off the
> single seeded 56/38 split whose counts are printed in the box. Over fifty
> paired re-splits of the same 94 decisions the raw count is ahead by **0.36
> hits out of 38, paired sd 1.14**, and it loses 11 of the 50
> (`outputs/metrics/gbm_benchmark.json`, key
> `across_repeats.conditional_logit`). A third of a decision is a tie. So the
> instruction is reversed — not because the work moved on, but because the
> word was wrong: leaning away from the flattering direction is still a bias,
> and one third of a hit was never a defeat to report. **What does not change
> is the finding this whole section rests on:** the power floor was cleared
> and three estimated parameters still bought **no** ranking improvement over
> a raw count of warehouses. The counts in the box are correct for their seed.

This makes the ceiling finding *stronger* rather than weaker, and it changes
what the ceiling is made of. The original story was "the sample is too small".
The measured story is that the sample was made large enough and the covariates
still carry nothing the raw warehousing count does not already carry. The
public record supports a ranking and does not support parameters.

> **CORRECTED 2026-09-15 — the sentence below says the gradient-boosted
> ranker "was never built". That is now false.** It was built on 2026-09-13
> and its artefact is `outputs/metrics/gbm_benchmark.json`. The correction
> makes the ceiling finding *stronger*, not weaker, so it should be
> volunteered: the stronger adversary was run and it did not escape the
> ceiling either. Over 50 re-splits on the same 94 decisions the shallow GBM
> arms score about 22.2 of 38 against the conditional logit's 20.60 and the
> raw count's 20.96 — about one decision in 38 — **and the GBM loses on
> Brier**. Then the sample was quintupled to 485 decisions and the GBM's edge
> **vanished entirely**, 0.5198 against 0.5196. Its one-decision advantage had
> been the small-sample model being slightly underfitted, not a gain from
> flexibility. *The ceiling is the data, not the functional form* — and that
> is now a measurement rather than an inference.
>
> One caveat that must travel with it: quote `across_repeats`, never
> `headline_split`. The artefact's own `headline_split_warning` field
> explains why — the single-split GBM rows move by up to 2 of 38 under a
> 1e-12 perturbation of the input, while the logit and the raw count do not
> move at all.

Two things must be said alongside it. The pre-registered benchmark was an
atheoretical gradient-boosted ranker and **it was never built**, so the
adversary that actually drew level with the model is a weaker one than the one
promised, and a stronger one would probably have been harder to hold off. And
the intervals — absent for most of
2026-09-14 and computed the same day — agree with the ranking result. **The
null here is `beta = 1`, not `beta = 0`**, because households is the numeraire
and only ratios are identified; a reader applying the usual habit reads the
table backwards.

```
  warehousing_establishments, beta 1.4428, the only interior parameter
    sandwich, 95%               [0.734,  2.835]   z 1.064, p = 0.287
    bootstrap over decisions    [0.760,  4.762]
    bootstrap over metros       [0.702, 10.013]   the conservative one
    BCa                         [0.714,  3.522]
    ALL FOUR COVER 1.0
```

So the one covariate that works is not distinguishable from one more
household. That is a fourth negative result rather than a rescue, and it is
what ADR-0004 predicted in advance. See B11 and B12 for the two things the
specification got wrong about how to compute it.

*For reading it as informative anyway:* the failure is not subtle and it is
not a near miss. Negative skill on two hold-outs, and one covariate of three
separating from zero, is not the signature of a good model held back by a
small sample. And the specific mechanism of the ceiling is identifiable and
fixable by somebody other than us: the federal inspection trail tells you
**where** buildings are and will not reliably tell you **when** they opened.
The where is fine. The when is the ceiling.

> **This is worth saying out loud in a viva.** *"I said before running it that
> there was a version of this project where the answer is 'public data isn't
> good enough'. That is the version I got. The useful form of the finding is
> narrower than the slogan: OSHA records give you location reliably and
> opening dates only as upper bounds with a 57-month median lag, and it is the
> dates that break it. An opening-date registry is a small administrative
> object and it would close most of the gap. That is something a regulator can
> actually do."*

### The ceiling, re-measured three more times on 2026-09-15. It held.

**This is the most important addition to this entry, because it removes the
last escape route from the finding — including the one the viva sentence
above leans on.** The paragraph above says *"it is the dates that break it"*.
That is now partly falsified by the project's own measurement, and the
replacement is a harder claim rather than a softer one.

```
  the escape route                  the test that closed it
  --------------------------------------------------------------------
  "not enough events"               hazard revived on 5,441 events
                                      instead of 812.  AUC 0.6894 ->
                                      0.6832.  Events per parameter
                                      5.6 -> 87.2.  hazard_revival.json

  "the dates are upper bounds"      the same revival used MWPVL STATED
                                      opening dates on 545 facilities.
                                      On the 130 matched facilities the
                                      true-date arm scores AUC -0.0043,
                                      i.e. marginally WORSE.  No
                                      measurable dating effect, on a
                                      control (30 facilities whose date
                                      actually moves) too weak to
                                      detect a small one

  "not enough decisions"            choice model refitted on 483
                                      decisions instead of 94.  Interval
                                      64% narrower, still covers the
                                      numeraire, point estimate moved
                                      TOWARDS it.  refit_expanded.json

  "the wrong functional form"       gradient-boosted ranker built.  Edge
                                      of about one decision in 38 on the
                                      pilot frame, GONE at 485
                                      (0.5198 vs 0.5196).  gbm_benchmark.json

  "the wrong geographic grain"      metro-level entry model, PRE-
                                      REGISTERED before the fit.  Lost to
                                      "rank by households" in 7 of 7
                                      held-out years, pooled AUC 0.7323
                                      vs 0.8949, 50 of 50 paired
                                      re-splits.  metro_entry.json
  --------------------------------------------------------------------
```

**So the ceiling statement is now stronger and its mechanism has changed.**
The old version was *"the dates break it"*. The measured version is:

> *At ZIP grain the fitted model is matched by a raw warehouse count. At
> metro grain the fitted model loses to a household count — in every year,
> under every model form, with and without the pandemic years, in every size
> tier, and whether or not it is allowed to cheat on vintage. In both cases a
> single free public column already contains everything the model recovered.*

**And the mechanism is now nameable rather than gestured at.** A conditional
choice model can only use covariates that vary *within* a metropolitan area
and are *not* proxies for population. Six of eighteen audited columns are
county figures broadcast to every ZCTA — about nine distinct values across
two hundred candidates. Five more correlate 0.84 to 1.000 with the numeraire
within metro. At metro grain the equivalent obstruction is temporal rather
than spatial: the economic columns are single-vintage broadcasts with 1.00
distinct values across all 32 quarters, so eight of twelve pre-registered
covariates could not be used at all (B13).

**The regulator ask is therefore bigger than it was, and more specific.** Not
only an opening-date registry. Also: **publish the economic series that
already exist with a usable vintage history, at a grain below the county.** A
covariate you cannot lag is a covariate nobody outside the firm can predict
with.

**One qualification that must travel with all of this.** The metro run did
*not* test the construction and freight covariates that motivated it, because
no time-respecting vintage of them exists in this panel. That is a
data-availability finding rather than a test of the hypothesis, and it is the
largest hole in the H0 claim. See B13.

---

# Part D — Does any of this survive on a résumé?

You asked directly. Here is the direct answer.

## D1. The short version

**Yes — and the limitations barely touch the résumé story, because none of
the résumé-worthy claims depend on the things we can't measure.**

Look at what actually goes on a CV:

| Résumé claim | Depends on revenue data? | Depends on fresh data? | Survives? |
|---|---|---|---|
| "Priced last-mile cost to serve for 2,333 ZIP codes at a median $1.0830/parcel across five sensitivity scenarios" | No | No | ✅ — but the "334-depot network" this line used to carry is CUT: no depot count appears in any current artefact |
| "Built a capital-allocation optimiser with an efficient frontier over an unobservable margin; it declines to spend a $2bn budget in full" | No | No | ✅ |
| "Conformal intervals with verified coverage — 88.19% against 90% nominal, tolerance computed on effective rather than nominal units" | No | No | ✅ for the RETIRED hazard model, and quote the 10.09% empty-set rate with it. Do NOT extend the claim to the choice model: there, 90% nominal coverage is bought by naming 71% of the metro |
| "Built a national DuckDB star schema over 33,791 ZCTAs; 1,081,312-row quarterly panel across 14 sources" | No | No | ✅ |
| "Six validation gates on an LLM agent's writes to a causal model, with a per-invocation audit record" | No | No | ✅ |
| "Cut peak disk 60 GB → 8 GB by precomputing an OD matrix" | No | No | ✅ |
| "Cold clone to green build in one command, offline; 648 tests" | No | No | ✅ — green at commit `b29071e`, 648 passed and 2 xfailed. Quote the commit with the count. It moved five times in two hours on 2026-09-14 (638 → 648 → 645p/3f → 646p/2f → 648), and a bare number in prose rots faster than anything else in this pack |
| "Built a free delivery-station opening panel from 5.2m federal OSHA records after six other sourcing methods failed" | No | No | ✅ — "first" was CUT; it breaks this pack's own rule against the word, and the sourcing count was five, now six with satellite dating |
| "Diagnosed why a fitted siting model failed — pseudo-replication, i.e. a likelihood that assumes independence across observations fed 88 echoes of one decision — and measured the failure against a null" | No | No | ✅ — the old wording said "mutual-exclusivity violation", which is the WRONG diagnosis and was on a résumé line |
| ~~"Out-of-time backtest, AUC 0.84"~~ | No | No | ❌ **never achieved.** Measured 0.6894 |
| ~~"Estimated cannibalization decay radius"~~ | No | No | ❌ **never estimated.** The 20 km / 0.18 penalty is assumed |
| ~~"Forecast $X revenue"~~ | **Yes** | — | ❌ never claim |

**Nine of twelve survive, four of them only after rewording.** Note which three do not, and why: two of them were
things the project *planned* and did not do, and the third was never
observable. None of them was lost to a limitation in this document — they
were lost to the difference between a proposal and a result.

> **The rule.** A résumé line is a claim you can be asked to reproduce on the
> spot. "AUC 0.84" fails that test in this project, because the artefact says
> 0.6894 and the artefact is public. Do not write a line you would have to
> walk back in an interview.

## D2. Why the limitations actively *help* you

This is counterintuitive but true in interviews, and in this project it is
the whole story rather than a consolation.

> **A candidate who says "my model got AUC 0.84" gets a nod.**
> **A candidate who says "my model got 0.69 against a null of 0.50, its
> calibration was 170x worse than a constant, and here is the textbook
> section that tells me why" gets a conversation — and, in a research
> setting, more trust than the first candidate.**

The reason is simple: the first claim cannot be distinguished from someone
who overfitted and did not check. The second one can only be made by someone
who built the null, built the hold-outs, and went to the literature when the
answer came back bad. That sequence is the skill being hired for.

Knowing the boundaries of your own result is the thing that separates people who
ran a model from people who understand one. Every workaround in this document is
an interview answer:

- **A1** → "tell me about working with imperfect data"
- **A2** → "how do you handle an unobservable key input?"
- **B1** → "how do you know your labels are right?"
- **B2** → "how do you know the result isn't an artefact?"
- **B4** → "what's a subtle bug most people miss?"
- **C4** → "tell me about a time you'd have to report a negative result"

You cannot answer any of those from a project with no stated limitations.

## D3. What you must NOT put on a résumé

Be strict about this. Each of these is checkable and each collapses under thirty
seconds of probing:

- ❌ "Forecast $X in revenue" — you cannot observe revenue
- ❌ "Predicted Amazon's expansion with 95% accuracy" — wrong metric, wrong
  number, and 95% would itself be a red flag
- ❌ "Big data pipeline" — the analytical panel is 14 MB, and claiming
  otherwise is the one unrecoverable error
- ❌ "Real-time" — the data has an 18-month lag on one axis
- ❌ "First/novel" anything — see the prior-art check
- ❌ "AI-powered platform" — says nothing and reads as filler
- ❌ **"Built a conditional choice model of Amazon's siting decisions"** on its
  own. True and useless. The model does no better on held-out ranking than a
  single raw Census count with nothing fitted from it, and the interval on its
  only working coefficient covers the null. If the model goes on the CV, the
  null result goes on the CV with it, in the same sentence. See B4 and Part
  C4.
- ❌ **Any standard error, confidence interval or p-value quoted without its
  null.** The intervals exist now, but the null in this model is `beta = 1`,
  not `beta = 0`, because households is the numeraire. Quoting "the interval
  excludes zero" would be technically true of the warehousing coefficient and
  completely misleading — it does not exclude *one*, which is the only
  comparison that means anything.
- ❌ **"Dated facilities from satellite imagery"** — 36% of the estimates were
  logically impossible. The failure is reportable; the capability is not.
- ❌ **Anything citing a drive-time matrix, an OSRM pipeline or a disk-usage
  reduction** — none of it was built.
- ❌ **A published open dataset or a deployed application** — neither exists.

## D4. What to say when a limitation comes up in an interview

Use this structure. It works every time:

```
   1. NAME IT PLAINLY        "The ACS covariates lag 18-24 months."
   2. SIZE IT                "That affects level features, not the
                              rate-of-change features."
   3. GIVE THE WORKAROUND    "We blend monthly rent and permit series,
                              and align covariate vintage to decision
                              vintage - the operator faced the same lag."
   4. STATE THE RESIDUAL     "A neighbourhood that changed in the last
                              18 months with no permit signal will be
                              misclassified. We flag those as
                              low-confidence."
```

**Name, size, work around, state the residual.** Never stop at step 1, and never
skip step 4.

## D5. The line that reframes the whole conversation

If someone dismisses the project because of the data constraints:

> *"The constraint is the research question. Nobody has published how much of a
> trillion-dollar company's siting behaviour is visible from public data alone.
> If it's 70%, that's a finding about transparency. If it's 40%, that's a
> finding about opacity and tells regulators exactly how much disclosure would
> close the gap. Either way it's a number that doesn't exist yet."*

---

# Part E — Summary table

| # | Limitation | Workaround | Residual | Cost |
|---|---|---|---|---|
| A1 | ACS 18–24 month lag | Operator faced same lag; decision lead time matches; blend monthly rent/permits; ACS 1-year metro context; rate-of-change features | Sharp recent change with no permit signal | 2 d |
| A2 | Cannot observe revenue | 6 of 8 outputs are scale-invariant; report NPV in units of margin with break-even; bound margin from filings; validate capital side vs disclosed capex | Margin varying systematically by ZCTA | 1.5 d |
| B1 | Facility date errors | Verify 100; triangulate; noise simulation to bound the damage; quarterly grain; prefer availability checks | Small stations under-reported | 1.5 d |
| B2 | MAUP | Pin vintage; contract-test count; **H3 robustness check** | H3 and ZCTA may disagree | 1 d |
| B3 | Donor-pool scarcity | Decay radius defines contamination precisely; staggered adoption; cross-metro donors; report weight concentration | Saturated metros may be non-estimable | 2 d |
| B4 | Generated regressors | DSL / prediction-powered inference using the B1 sample | None material | 1 d |
| B5 | Proxy validity | External capex check; per-proxy sensitivity | Correlated bias | included |
| B6 | ACS margins of error | Carry MOE into Monte Carlo; flag high-MOE areas | Small ZCTAs stay noisy | 0.5 d |
| B7 | Exclusion restriction | First-stage F; sensitivity under assumed direct effect; state residual | Cannot be tested | 0.5 d |
| C1 | No revenue ground truth | **None.** Parameterise and don't claim | Stated | — |
| C2 | Cannot validate θ directly | **None.** Report placebo distribution and bands | Stated | — |
| C3 | Internal constraints invisible | **None.** Hence "operator-consistent" framing | Stated | — |
| C4 | Public-data ceiling **is** too low — **measured five times as of 2026-09-15** | **None.** It is RQ4 and it has been answered. Report it | Measured: hazard lost to a constant and lost again on 6.7x the events with real dates; the choice model only matched one raw covariate and did not improve on 5x the sample; a GBM's edge vanished at the larger sample; a **pre-registered** metro model lost to a household count 7 of 7 | — |
| B8 | Warehousing covariate may contain its own outcome | **Executed 2026-09-15:** refit on vintages strictly preceding the stated opening date, n = 29 | **MEDIUM, partly mitigated** (was HIGH/unmitigated). Retains **79%** of its value, beats the floor 50 of 50, per-establishment price unchanged to 1.2%. But: 65 of 94 decisions lost, the 29 are measurably easier, leak and staleness are not separable, and a model-free check finds ~1 excess establishment in the chosen ZCTA | done, n = 29 |
| B13 | 8 of 12 pre-registered covariates unusable — the panel's economic columns are single-vintage broadcasts (1.00 distinct values across 32 quarters) | Fetch the historical ACS / OES / EJScreen vintages. All free, none fetched | **HIGH for the comparative claim, LOW for the verdict** — the leakage-permitted arm also loses, 6 of 7 and 7 of 7 | 1-2 d per source |
| B14 | Two figures asserted a 95% CI, a significance test and per-bar dollar labels on typed-in numbers | Restyled as schematics, in-axes `ILLUSTRATIVE ONLY` banner, all affected axis numbers removed | **MEDIUM, and it is a process risk.** Magnitudes still drawn though unlabelled; second occurrence of the class; the audit that found it is untracked | 2 h done, 1 d open |
| B15 | Two bugs in `choice.fit` — a NaN first start that could never be displaced, and an infeasible optimum that raised the log-likelihood by up to 1.20 while pushing 765-4,816 alternatives below zero probability | Both guarded; the second raises with the fix in the message | **MEDIUM**, and the reason is coverage: 39 of 133 modules have no test, including the one that writes the headline artefact | guards done |
| B9 | Satellite dating failed | Fix the changepoint detector, or switch to a binary built/not-built target | 36% of estimates logically impossible; route unsuccessful, not closed | 1 d retry |
| B10 | Labelling worklist generated against the wrong reference | Fix the generator (3 lines); use the 122 confirmations as a validation set | Cost is sunk; 13 new sites from 362 labels | 0.5 d |
| B11 | Two of three coefficients on a boundary | Refuse the sandwich there and print the reason; one-sided bootstrap | Interpretive: "three parameters" means one estimated quantity | done |
| B12 | Bootstrap resampling unit moves the upper endpoint 2x | Report both; quote the metro-clustered figure | Low; MODEL_SPEC 6.3 is silent and should not be | 1 h |

**Total workaround cost: roughly 10 person-days** — well inside the ~11 days
freed by the scope cuts recorded in the roadmap.

---

## The closing argument

Every serious empirical project has limitations. What distinguishes a good one
is not having fewer, but knowing them precisely, working around what can be
worked around, and refusing to claim what cannot be supported.

The four things in Part C have no workaround. Saying so is not a weakness in the
project — **it is the reason to believe everything in Parts A and B.**
