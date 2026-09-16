# Uncertainty — how far the answer moves when every parameter moves at once

*Measured 2026-09-13 from 500 joint draws, seed 20260914, 2023Q4, $2bn budget.
Artefacts: `experiments/portfolio-optimiser/artefacts/montecarlo_report.json`,
`outputs/tables/montecarlo_draws.parquet`. Code:
`src/siting_atlas/optimize/montecarlo.py`. Reproduce with*

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.optimize.montecarlo --draws 500
```

*500 draws took 4,564 seconds — 9.13 seconds each.*

---

## 1. What this is not

**This is not a confidence interval and it must never be quoted as one.**

Every range sampled below was chosen by this project, out of
[`PARAMETERS.md`](PARAMETERS.md) §3 and §4. Eight of the constants its §1
classifies have **no published source at all** — `stops_per_tour`,
`service_minutes_per_stop`, `parcels_per_stop`, `van_lease_usd_per_day`,
`income_elasticity`, `reference_income_usd`, `linehaul_sharing` and
`cannibalisation_radius_km` — and two of the three largest drivers found below
are among them.

So what follows measures **how far the answer moves across the range we
consider plausible**. It propagates our priors, not the world's. A reader who
reads "p10 152, p90 306 activations" as "there is an 80% chance the true
number lies between 152 and 306" has read it wrong, and the error is ours if
we let them. The right reading is: *if our judgement about these twenty-one
constants is correct, the answer is this unstable; if our judgement is wrong,
this understates it.*

Three further things it is not:

```
  NOT COMPLETE.  CostParameters and PortfolioParameters have twenty-four
    fields between them and twenty-one are sampled. The three held fixed are
    named in section 7, and one of them is the depot knob —
    the single thing DECISION_LOG.md sec.4.2 blames for the drift this study
    exists to explain. The spread below is therefore a FLOOR.
  NOT A MODEL-ERROR ESTIMATE.  It varies the numbers inside the model. It
    cannot see the model being wrong. The known defects in STATUS.md sec.6 —
    the infeasible depot network, the activation that is priced three
    different ways, the listwise deletion — are all untouched by it and all
    larger than anything here.
  NOT INDEPENDENT OF THE SOLVER.  Every draw was solved with today's
    p-median depots and today's greedy selector. Change either and the whole
    distribution moves, which is the finding of section 3.
```

---

## 2. What was sampled, and how

Twenty-one parameters, drawn jointly and independently, one full cost-model
solve and one full portfolio solve per draw.

Triangular on the documented range, with the mode at the current baseline.
Triangular rather than uniform because the baseline is not an arbitrary point
in the range — it is a value somebody argued for — and rather than a normal
because the ranges are hard bounds from physical or accounting limits, not
two-sigma guesses. Triangular respects the bounds and still puts mass where
the evidence is.

`discount_rate` is the exception and is uniform. `PARAMETERS.md` §7.3 records
that both Econometrica ancestors use beta = 0.95, about 5.3%, against our
10%, and that the choice between a private hurdle rate and a social one has
no defensible mode.

**One range had to be taken from a table rather than a register entry.**
`delivery_days_per_year` appears in `PARAMETERS.md` §4 with a sweep range of
260-365 and had **no entry in the §6 parameter register at all** — it was the
one sampled constant with no recorded source, classification or
justification. It turns out to be the weakest portfolio driver in §5 below,
so nothing here rests on it. The register was completed on 2026-09-14 and the
entry is now `PARAMETERS.md` §6.22.

**And writing that entry found a defect in this study.** In the baseline,
`delivery_days_per_year` is not a free constant: `optimize/params.py:213`
derives it as `delivery_days_per_week * 52`, so 6 x 52 = 312. `montecarlo.py`
draws the two **independently**, `delivery_days_per_week` from `COST_RANGES`
and `delivery_days_per_year` from `PORTFOLIO_RANGES`, which breaks that
identity — a draw can deliver six days a week in the cost model and 365 days
a year in the portfolio model. The effect on the bands below is small,
because both parameters sit near the noise floor for most outcomes, but the
two should be tied and until they are this study is propagating an
inconsistency rather than an uncertainty. It is the fourth item for the next
run, after the three in §7.

**Independent sampling is itself an assumption, and a generous one.**
`PARAMETERS.md` §1 already says the true errors are correlated: if
`service_minutes_per_stop` is wrong it is probably wrong because
`stops_per_tour` is also wrong, and the two move the answer the same way.
Drawing them independently lets errors cancel. Correlated draws would widen
the bands below, not narrow them.

---

## 3. The question this was built to answer

The portfolio headline has moved three times — 317, then 330, then 282
activations — and [`../DECISION_LOG.md`](../DECISION_LOG.md) §4.2 records that
**not one of those moves was
caused by a parameter change**. They came from the depot solver changing,
from a panel rebuild, from a column being repaired. The question is whether
282 and 330 are two different answers or one answer measured three times.

Here is the distribution of `n` across 500 draws, with the three headlines
marked:

```
  min      p10      p25      p50      p75      p90      max      sd
   82      152      214      264      289      306      385    58.9

   |------------------------------------------------------------|
  82                        264                                385
            [====== p10 to p90, width 154 ======]
                                    ^282        ^317  ^330
                                    p68          p95   p97
```

| Headline | Percentile of the draws | Draws at least this large | Verdict |
|---|---|---|---|
| 282 activations (current) | 67.8 | 163 of 500 (32.6%) | **inside p10-p90** |
| 317 activations | 94.8 | 27 of 500 (5.4%) | **outside, above p90** |
| 330 activations | 97.3 | 14 of 500 (2.8%) | **outside, above p90** |

**So the answer is split, and the split is the finding.**

The observed drift of 48 activations, 282 to 330, is **0.82 standard
deviations** and **31% of the p10-p90 width**. On that arithmetic alone it is
unremarkable: 30.0% of all draws land inside the interval [282, 330]. If you
are asked "is a 48-activation move large?", the honest answer is no — it is
smaller than an ordinary draw from our own parameter uncertainty.

But the three numbers are not symmetric about the distribution. Today's
answer, 282, sits comfortably inside at the 68th percentile. The two older
ones sit above the 94th and the 97th. **Parameter error alone, on today's
model, reproduces 330 in fourteen draws out of five hundred.** That is not
"could easily have happened"; it is a tail.

The resolution is that the distribution is conditional on the solver. These
500 draws were all solved with the **current** p-median depot placement.
`PARAMETERS.md` §9.1 records that swapping k-means for p-median moved `n`
from 330 to 282 with nothing in `optimize/` touched. So the correct statement
is:

> **Under today's depot solver, no plausible parameter combination makes 330
> a typical answer — it needs the 97th percentile. Under yesterday's solver,
> 330 was the baseline. The solver change therefore moved the answer by more
> than a two-sigma parameter excursion, and the project's refusal to quote a
> headline in prose is vindicated, not dissolved, by this study.**

That is the publishable finding and it is the less comfortable of the two
available. The drift was real. The parameters did not cause it.

Two smaller observations from the same table:

**The baseline is optimistic relative to its own uncertainty.** The point
estimate is 282; the median of the distribution built around it is 264.5. The
baseline sits 17.5 activations — 6.6% — above the median of the draws whose
mode it defines. That is a Jensen effect: the map from parameters to
activations is concave over most of the sampled region, so the answer at the
modal parameters is not the modal answer.

**The capital figure carries no information the activation count does not.**
`capital_usd` is exactly `$4,000,000 x n` in all 500 draws, because
`capital_per_activation_usd` is fixed and is not de-duplicated across ZCTAs
(the defect in [`../STATUS.md`](../STATUS.md) §6). The three headline pairs — $1.268bn, $1.320bn,
$1.128bn — are the three activation counts multiplied by $4m. They are one
piece of evidence written twice, and the capital band below should never be
quoted as a second, corroborating result.

---

## 4. The bands

`n` and `capital_usd` are a single quantity, as above.

| Outcome | min | p10 | p25 | p50 | p75 | p90 | max | sd |
|---|---|---|---|---|---|---|---|---|
| activations `n` | 82 | 152 | 214 | 264.5 | 289 | 306 | 385 | 58.9 |
| capital $bn | 0.328 | 0.608 | 0.857 | 1.058 | 1.156 | 1.224 | 1.540 | 0.236 |
| break-even margin $/parcel | 0.8604 | 1.0892 | 1.2102 | 1.3682 | 1.5610 | 1.7259 | 2.3288 | 0.2578 |
| median $/parcel | 0.6128 | 0.8368 | 0.9561 | 1.1224 | 1.3214 | 1.4836 | 2.0951 | 0.2603 |
| optimality gap | 0.0110 | 0.0555 | 0.0748 | 0.0968 | 0.1247 | 0.1532 | 0.2639 | 0.0386 |

**The tail, since the middle is the part that flatters us.** The full range of
`n` is 82 to 385 — the largest draw is **4.7 times** the smallest. The p10-p90
band spans 154 activations and a factor of 2.0; the min-max range spans 303
and a factor of 4.7. **Half the total spread lives outside the band we would
normally report.** The inter-quartile range is 75, under a quarter of the full
range.

The same asymmetry runs through `median $/parcel`: p10-p90 is $0.84 to $1.48,
but the draws run from $0.61 to $2.10. The upper tail is long, which is what
a cost model built on multiplicative labour terms should produce.

**The optimality gap is not a constant.** `PARAMETERS.md` §4.1 used to say
"the optimality gap (13.4%) is larger than every parameter effect in the
table", arguing that improving the solver buys more than tightening a
parameter. The gap is not a fixed 13.4% slack; it ranges from 1.1% to 26.4%
with a standard deviation of 3.9 points, and it is itself driven by the
parameters (Spearman +0.51 against `cannibalisation_peak`; only 62.0% of its
variance is linear in the twenty-one). The sentence is still directionally
right about the solver being worth attention, but the gap is a function of
the inputs, not a property of the heuristic alone, so the two cannot be
ranked against each other as independent sources of error. §4.1 was restated
on 2026-09-14 and now says so.

---

## 5. What drives the spread

Two rankings. Spearman rho between each sampled parameter and each outcome,
and the share of outcome variance attributable to each parameter in a
standardised linear regression on all twenty-one at once. Because the inputs
are sampled independently, the two largely agree, and the variance shares are
interpretable as a decomposition.

**A noise floor, so nothing small is over-read.** With 500 draws the standard
error of a Spearman rho is 0.045, so anything with |rho| below about **0.115**
is indistinguishable from zero at p < 0.01. The calibration check is
`default_linehaul_miles`, whose measured one-at-a-time effect is exactly 0.00%
because the fallback never fires on this pilot: its joint rho against median
$/parcel is -0.014. The floor is real, and the bottom third of every table
below is noise.

### 5.1 Activation count `n`

Top eight of twenty-one, sorted by variance share. The two columns do not
order identically, which is ordinary: rho measures monotone association and
the share measures linear contribution.

| Parameter | rho | variance share |
|---|---|---|
| `cannibalisation_peak` | -0.622 | 44.3% |
| `cannibalisation_radius_km` | -0.249 | 6.9% |
| `parcels_per_stop` | +0.238 | 5.0% |
| `delivery_days_per_week` | +0.280 | 4.9% |
| `parcels_per_household_per_week` | -0.136 | 2.8% |
| `service_minutes_per_stop` | -0.133 | 2.5% |
| `horizon_years` | -0.125 | 2.3% |
| `stops_per_tour` | +0.221 | 1.8% |

Cost parameters carry **18.8%** of the variance, portfolio parameters
**55.9%**, and **25.3% is not linear in the parameters at all** — it is
interaction and threshold behaviour in the greedy selector. That residual is
the largest single block after `cannibalisation_peak`, and it is exactly what
a one-at-a-time sweep cannot produce.

### 5.2 Break-even margin

Top eight of twenty-one, sorted by variance share.

| Parameter | rho | variance share |
|---|---|---|
| `service_minutes_per_stop` | +0.666 | 41.6% |
| `parcels_per_stop` | -0.636 | 36.6% |
| `van_lease_usd_per_day` | +0.179 | 3.9% |
| `stops_per_tour` | -0.140 | 2.1% |
| `delivery_days_per_week` | -0.145 | 2.0% |
| `parcels_per_household_per_week` | -0.154 | 1.8% |
| `cannibalisation_peak` | +0.029 | 1.6% |
| `shift_hours` | -0.159 | 1.6% |

Cost parameters carry **91.0%**, portfolio parameters **5.5%**, and only 3.4%
is nonlinear. The break-even margin is a cost quantity wearing a portfolio
label.

### 5.3 The three that matter

```
  cannibalisation_peak       44.3% of the variance in the ACTIVATION COUNT
  service_minutes_per_stop   41.6% of the variance in the BREAK-EVEN MARGIN
  parcels_per_stop           36.6% of the variance in the BREAK-EVEN MARGIN
```

**None of the three can be cited.** `service_minutes_per_stop` (§6.8) and
`parcels_per_stop` (§6.10) are both marked [E] — engineering estimate, no
source found. `cannibalisation_peak` is not on the [E] list, but only because
a comparator exists that §7.4 shows measures a different quantity: Holmes and
Houde et al. both measure diversion of demand *between a firm's own outlets*,
not loss of demand in an area, which is what our term does. `PARAMETERS.md`
§4.1 calls it the worst-evidenced parameter in the whole project, and its own
docstring says PLACEHOLDER.

Between them the three account for roughly four fifths of the movement in the
two headline outcomes. **Three unciteable constants carry most of the
answer**, and that is worse than the one-at-a-time tables imply, because §3
and §4 rank cost and portfolio parameters separately and never add them up.

---

## 6. Where joint sampling disagrees with the one-at-a-time ranking

`PARAMETERS.md` §3 and §4 sweep each parameter alone and report the endpoint
effects. That is a sensitivity analysis. This is an uncertainty analysis. They
answer different questions, and the places they disagree are the places
one-at-a-time cannot see.

### 6.1 Where they agree, which is most of the cost model

Ranked by effect on median $/parcel, the two orderings have a rank agreement
of **Spearman 0.918**. The top two are the same and in the same order, and the
bottom is noise in both. Movement in the middle is one or two places:
`stops_per_tour` 5 -> 7, `shift_hours` 6 -> 5, `wage_loading` 7 -> 6,
`parcels_per_household_per_week` 9 -> 12, `bhh_constant` 11 -> 15. None of
those differences exceeds the noise floor.

**So §3 is durable and can be quoted.** The cost model is close enough to
multiplicative that composing the parameters does not reorder them.

### 6.2 Where they disagree, and it is worth the whole exercise

**Disagreement 1: `cannibalisation_peak` is §4's top break-even lever and
joint sampling cannot distinguish it from zero.**

§4 gives it -9.72% / +1.31% on the break-even margin, first of seven. Under
joint sampling its rho against break-even is **+0.029, p = 0.52**. Not small
— absent.

The cause is visible in the deciles:

```
  decile   mean peak   mean break-even   mean n
     1       0.0875        1.3380         293
     3       0.1427        1.3848         279
     5       0.1852        1.3644         270
     7       0.2194        1.4174         232
    10       0.3087        1.3742         177
```

`n` falls monotonically and steeply; break-even wanders inside a six-cent
band and is not monotone. §4's -9.72% is an **endpoint** effect, realised at
peak = 0.05, and triangular sampling with the mode at 0.18 rarely goes there.
More importantly, the two channels offset: raising `peak` makes marginal ZCTAs
unprofitable, the selector funds fewer of them, and the margin at the new
stopping point is about where it was. One-at-a-time reports the level shift at
an endpoint; joint sampling reports the density-weighted effect after the
optimiser has re-optimised. **The second is the one a reader wants.**

What `cannibalisation_peak` actually controls is the *size* of the portfolio,
not its unit economics — and on that it is decisively first, at 44% of the
variance. §4 had the right parameter at the top of the wrong column.

**Disagreement 2: the two tables never cross, and the crossing terms are
large.**

§3 measures cost parameters against cost outcomes. §4 measures portfolio
parameters against portfolio outcomes, holding the cost table at baseline.
Neither asks what a cost parameter does to the activation count. Joint
sampling does, and the answer is that cost parameters supply **18.8% of the
variance in `n`**:

```
  delivery_days_per_week            rho +0.280
  parcels_per_stop                  rho +0.238
  stops_per_tour                    rho +0.221
  avg_speed_mph                     rho +0.137
  parcels_per_household_per_week    rho -0.136
  service_minutes_per_stop          rho -0.133
```

`delivery_days_per_week` is the **second-strongest single driver of the
activation count of any parameter in the model**, behind only
`cannibalisation_peak` and ahead of every other portfolio parameter including
`cannibalisation_radius_km`. It does not appear in §4 at all. It is also one
of the two terms in the quantity §7.1 flags as *disagreeing with a published
source*: the 2,808-hour labour denominator,
`shift_hours x delivery_days_per_week x 52`, against the BLS OEWS convention
of 2,080. A quantity we already believe is wrong is the second-largest lever
on the portfolio size, and the existing sensitivity tables are structurally
incapable of showing that.

One caveat on that finding, in our own disfavour. §7.1's actual charge is that
`delivery_days_per_week` should not be driving driver-hours at all: it
conflates how many days a week the *network* delivers with how many hours a
*year* one driver works. Sampling it therefore moves two things at once, and
part of its apparent power here is that conflation rather than genuine
economic leverage. Splitting the constant in two, as §7.1 recommends, would
change both this ranking and the headline. Until that is done, read this row
as "a defect is doing a lot of work", not as "network delivery frequency is
the second-biggest lever".

**Disagreement 3: on `n`, §4's own `n` column survives; it is the BE column
that does not.**

Ranked by §4's `n lo/hi` spread rather than its break-even column, the
agreement with joint sampling is **Spearman 0.714**, with the top two
unchanged:

```
  one-at-a-time (sec.4 n column)      joint sampling
   1  cannibalisation_peak             1  cannibalisation_peak      rho -0.622
   2  cannibalisation_radius_km        2  cannibalisation_radius_km rho -0.249
   3  horizon_years                    3  discount_rate             rho +0.219
   4  delivery_days_per_year           4  horizon_years             rho -0.125
   5  discount_rate                    5  linehaul_sharing          rho +0.101
   6  linehaul_sharing                 6  delivery_days_per_year    rho -0.052
```

Ranked by §4's break-even column instead, agreement collapses to **Spearman
0.086** — no relationship. The practical rule is: **§4's `n` column is a
usable ranking of importance; its BE % column is not.** (The Jaccard column
measures something this study does not record, since the selected ZCTA sets
are not written to the draw artefact, so nothing here bears on it either way.)

**Disagreement 4: a quarter of the variance in `n` is not attributable to any
parameter.**

The linear model on all twenty-one explains 74.7% of the variance in `n` and
62.0% in the optimality gap. The rest is interaction and the discrete
behaviour of a greedy stopping rule. One-at-a-time sweeps report only the
main effects, so they are describing three quarters of the story for `n` and
under two thirds for the gap, with no way to know it.

---

## 7. What was not sampled, and why it matters

Three of the twenty-four fields of `CostParameters` and `PortfolioParameters`
are held at baseline.

```
  capital_per_activation_usd  DELIBERATE AND CORRECT.  STATUS.md sec.6 records
    that its UNIT is wrong -- it charges $4m per ZCTA for a facility, with
    no de-duplication. Sampling a quantity whose definition is broken would
    dress a known defect as uncertainty. It is a defect, not a distribution.
    Consequence: capital_usd = $4m x n exactly, in all 500 draws.

  parcels_per_depot_per_day   AN OMISSION, AND THE WORST ONE.  Range
    20k-60k in PARAMETERS.md sec.3. It has the smallest LEVEL effect in the
    whole cost table (-2.54% / +1.70%) and the LARGEST RANK effect
    (rho 0.90, worst in sec.3). It sets the number of depots, and the depot
    network is precisely what DECISION_LOG.md sec.4.2 blames for the
    330 -> 282 drift
    this document exists to explain. Leaving it out means section 3's band
    is conditioned on a fixed depot count as well as a fixed depot
    algorithm. Sampling it is the obvious next run.

  reference_income_usd        AN OMISSION, MINOR.  Range 60k-90k, level
    effect under 0.5%, rank effect rho 0.92. It is a normalising convention
    (sec.6.13) rather than a physical quantity, but it does reorder ZCTAs
    and it is on the [E] list.
```

The first is a decision the module documents. The other two are not
documented anywhere and are recorded here as a gap. **Both omissions narrow
the reported band**, so every figure in §4 is a lower bound on the spread
this same method would produce if it were complete.

---

## 8. What to do with this

```
  1  Stop quoting a headline activation count without the band. The
     defensible sentence is "264 activations at the median of our parameter
     uncertainty, p10 152 to p90 306, on the 2026-09-13 depot solver".
     Never the point estimate alone, and never the capital figure as though
     it were separate evidence.

  2  Source cannibalisation_peak or replace it. It is 44% of the variance in
     the portfolio size and it is a placeholder. Nothing else on the
     parameter backlog buys as much.

  3  Resolve the labour-hours denominator (PARAMETERS.md sec.7.1). It is the
     second-largest driver of activation count, and we already believe our
     value is wrong.

  4  Re-run with parcels_per_depot_per_day sampled, and then again under a
     second depot algorithm. The solver, not the parameters, is the largest
     identified source of movement in the headline, and it is still
     unmeasured as a distribution.

  5  Do not commission a better estimate of linehaul_sharing, bhh_constant,
     circuity, van_mpg or maintenance_usd_per_mile. All five sit at or below
     the noise floor in every outcome. PARAMETERS.md sec.3.1 said the
     routing mathematics was decoration; joint sampling agrees.
```

---

## 9. How to reproduce and how to check it

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.optimize.montecarlo --draws 500
```

Deterministic given the seed. The draw-level artefact
`outputs/tables/montecarlo_draws.parquet` carries one row per draw with all
twenty-one sampled parameters beside all five outcomes, so every correlation
and variance share above can be recomputed without re-running the solve.

Failures are recorded, not dropped. `run()` catches a failing draw, logs it
and writes a row with `ok = False`, because parameter combinations that break
the solver are not a random sample of parameter combinations and dropping
them would bias the distribution toward the numerically comfortable. **In this
run all 500 draws succeeded**, so the point is currently moot and the
invariant is held by `tests/unit/test_montecarlo.py` rather than by evidence.

The tests also pin that every draw stays inside its documented range, that the
modal bin of a large sample contains the baseline, that `discount_rate` has
uniform rather than triangular variance, that a baseline outside its own range
is warned about rather than silently clipped, and that the
not-a-confidence-interval caveat reaches the artefact and not just this
document.
