# Handbook Part 5 — Cost, NPV and the Portfolio Problem

**How much it costs to deliver a package, what a ZIP is worth over the horizon,
how uncertain that number is, and why ranking ZIPs is the wrong way to decide.**

---

## 5.0 Lead with this: the cost side is the part that works

```
  +--------------------------------------------------------------------+
  |  THIS CHAPTER DESCRIBES THE STRONGEST COMPONENT IN THE PROJECT.    |
  |                                                                    |
  |  The cost model runs on real data and produces real numbers.       |
  |  Run 20260914-002418-0623, cost_report.json:                       |
  |     2,333 priced ZCTAs                                             |
  |     median $1.0830 per parcel  (p10 $0.9778, p90 $1.4180)          |
  |     total daily cost $14,001,626, total vans 78,292                |
  |     5 scenario tables, spanning -16.7% to +4.8% on the median      |
  |  The portfolio optimiser runs, run 20260914-002431-7419, and its   |
  |  most interesting output is a refusal: at a $2bn budget it funds   |
  |  282 activations for $1.128bn -- 56.4% of the budget -- and        |
  |  DECLINES THE REMAINING 44%.                                       |
  |                                                                    |
  |  THREE caveats you must carry through the whole chapter:           |
  |    1. The demand term N_i(t) is an ASSUMPTION, not a model         |
  |       output. See Sec. 5.4.1. The hazard model that was supposed   |
  |       to supply it FAILED and has no usable posterior.             |
  |    2. The cannibalisation term theta_i is an ASSUMED CONSTANT,     |
  |       not an estimate. The causal study in Part 3 that was         |
  |       supposed to supply it was never built.                       |
  |    3. The optimiser prices an activation THREE INCONSISTENT WAYS   |
  |       in one file, and overcharges capital by a factor of about    |
  |       2.74. See Sec. 5.6.1. This is the same unit-of-analysis      |
  |       error that killed the hazard model, in a second component.   |
  +--------------------------------------------------------------------+
```

> **Corrections to this box, so nobody quotes the old version.** It used to
> say median **$1.0875** per parcel: stale, the current run gives $1.082994,
> quoted as **$1.0830**. It used to say **"334 solved depots across 11
> CBSAs"**: that figure **cannot be verified from any current artefact**.
> There is no depot count in `cost_report.json` and no depot column in
> `outputs/tables/cost_to_serve_2023q4_baseline.parquet`, whose 23 columns are
> all ZCTA-level. The depot solve happens in memory and is never written out.
> Do not requote 334; it has to be re-derived and re-published before anyone
> says it again. It used to say the scenarios span **-17.0% to +4.4%**: the
> five scenario tables measured today give **-16.65% (dense routing) to
> +4.84% (congested)** on the median cost per parcel, and `cost_report.json`
> records only the baseline, so that span has to be computed from the parquet
> files rather than read from the report. And it used to say the optimiser
> deploys "roughly two thirds" -- it deploys **56.4%**, so it declines about
> **44%**, not a third.

**Why the caveats do not sink the chapter.** A cost-to-serve number is a
statement about *technology and geography*: how far apart the houses are, how
fast a van moves, what a driver is paid. None of that depends on predicting
where Amazon will build next. That is why four of the project's five components
survived the hazard model's failure - **they never needed the facility panel**.

**Where to get the run-stamped figures.** Every number above is re-derived on
each run into `outputs/metrics/cost_report.json` and
`outputs/metrics/portfolio_report.json`, with a `run_id` and a timestamp.
`docs/STATUS.md` carries the one-page summary. Where this handbook and an
artefact disagree, **believe the artefact** - and if a figure in this chapter
carries no run stamp, treat it as illustrative.

---

## 5.1 The cost model in one equation

Cost per delivered package in ZIP *i* splits into two parts:

```
   c_i = c_fixed + b_stem * d_stem(i) + b_local * A_i / sqrt(d_i * N_i)
         ^^^^^^^   ^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         overhead  STEM: depot to zone  LOCAL: within-zone routing
```

- `d_stem(i)` — drive time from the nearest node to the zone
- `A_i` — the ZIP's area
- `δ_i` — delivery density (stops per unit area)
- `N_i` — expected daily volume

### The two halves, intuitively

> **Stem cost** is the van driving *out* to the neighbourhood before delivering
> anything. It is pure overhead — no packages are delivered during it. A
> ZIP 40 minutes from the nearest station pays that cost on every route, every
> day.
>
> **Local cost** is the driving *between* stops once you're there. This is where
> the density law from Part 1 bites: it scales as `1/sqrt(δ)`.

> **Worked example.** Two ZIPs, both with 200 daily packages.
> - **ZIP A:** 8 minutes from the station, 5 km² area. Short stem, high density.
> - **ZIP B:** 35 minutes from the station, 40 km² area. Long stem, low density.
>
> ZIP B pays roughly **4× the stem cost** and, at one-eighth the density,
> roughly **2.8× the local distance per stop** (`sqrt(8) ≈ 2.83`). Same package
> count, wildly different economics.

---

## 5.2 Where drive times come from — and the decision to throw the engine away

### The obvious approach, and why it fails

Run OSRM (Open Source Routing Machine) against OpenStreetMap data. Ask it for
drive times. Done.

Except OSRM does not just *read* a map — it **preprocesses** it, and
preprocessing is expensive:

```
   metro bbox PBF    200 MB   ->  osrm-extract  ->  2-5 GB of artifacts
   California PBF    1.2 GB   ->  osrm-extract  ->  15-25 GB, slow on 16 GB RAM
   full US PBF        12 GB   ->  osrm-extract  ->  NOT laptop territory
                                                    (needs 64-128 GB RAM)
```

A naive design serves all ten metros from a running container. Ten metros
retained simultaneously is **~30 GB of artifacts** plus the source files. On a student
laptop that is survivable but unpleasant; on 8 GB of RAM the extract step for a
large metro will fail.

### The insight that removes the problem

> **You do not need a routing server. You need a table of drive times.**

`d_stem(i)` is a finite, precomputable set of numbers: roughly 800,000
within-metro origin–destination pairs, which stores as a **10 MB parquet file**.

```
   FOR EACH METRO, ONE AT A TIME:
     1. download the metro bbox extract        (~200 MB)
     2. preprocess
     3. query the full OD table
     4. write od_<metro>.parquet               (~1 MB)
     5. DELETE the extract and every artifact  <-- the important step
     6. next metro

   PEAK DISK  = one metro (~5 GB), not ten (~30 GB)
   FINAL DISK = ten parquets = ~10 MB
   DEPLOYED APP DEPENDENCY = one 10 MB lookup, no routing engine at all
```

**Why this is worth saying out loud in an interview.** It is a real engineering
judgement: recognising that a heavyweight *service* was only ever needed to
produce a lightweight *artifact*. It removes a demo failure mode, a cold-start
latency, and a 30 GB dependency.

### The fallback that de-risks it entirely

Daganzo's law is *already* a continuous approximation. Adding exact road routing
to an approximate cost model is precision in the wrong place.

**Circuity factor:** road distance ≈ great-circle distance × *k*, with
*k* ≈ 1.3–1.4 for US metros.

```python
road_km = haversine_km(node, zcta_centroid) * CIRCUITY   # CIRCUITY = 1.35
```

Then OSRM becomes a **validation step, not a dependency**: calibrate *k* on one
metro against routed ground truth, report the residual error, apply to the rest.

> **If the residual error is large, you have a finding. If it is small, you have
> saved two weeks.** Either way you win — which is the same structure as the
> RQ2 bet in Part 3.

---

## 5.3 The eight capital buckets

Rather than treating capital as a single unexplained number, we decompose it
into eight auditable buckets, each with a documented public proxy — and add
the sensitivity analysis that makes the decomposition defensible.

| # | Bucket | Public proxy | Metro variation | Tier |
|---|---|---|---|---|
| 1 | Real-estate lease | Commercial rent index by ZIP | **Very high** (SF ≈ 3× Austin) | Primary |
| 2 | Building fitout | Industry benchmarks, $30–60/sq ft | Low–medium | Secondary |
| 3 | Delivery vehicles | $45–65k/van, 5-yr depreciation | Low | Primary |
| 4 | Hiring (one-time) | BLS recruitment cost estimates | Medium | Secondary |
| 5 | Wages (ongoing) | BLS OES median by metro | **High** (union NY ≫ TX) | Primary |
| 6 | Fuel and energy | EIA regional prices | Medium | Primary |
| 7 | Permitting | State cost-of-doing-business indices | **High** (CA/NY ≫ TX/FL) | Secondary |
| 8 | Marketing activation | $50–150 per new subscriber | Low | Secondary |

**The four primary buckets account for roughly 75% of the variation.**

### Why the tiering is a communication device, not a modelling choice

All eight enter the Monte Carlo at their true weight. The tiering exists so that
in a viva you lead with the four that matter and can still defend the other four
if pushed. **Say that explicitly** — a reviewer who suspects you are hiding
four weak buckets is much more hostile than one who is told which four dominate.

### The sensitivity plot is the actual defence

```
   Real-estate lease      |========================|  +/- $1.34M
   Wages (ongoing)          |====================|    +/- $0.99M
   Fuel and energy             |============|         +/- $0.61M
   Delivery vehicles           |===========|          +/- $0.55M
   Building fitout                |=====|             +/- $0.33M
   Hiring (one-time)               |==|               +/- $0.18M
   Permitting                      |==|               +/- $0.15M
   Marketing activation             |=|               +/- $0.11M
                                    0
```

> **The argument this enables:** *"You do not need all eight buckets to be
> accurate. You need the two that dominate the swing to be accurate — and
> this plot identifies which two, rather than my asserting it."*

That is a much stronger position than claiming all eight estimates are good.

### The external check

Aggregate ZIP-level capital to metro level; compare against the operator's
**publicly disclosed capital expenditure**. Target: within 25%.

**This would be the only externally falsifiable number in the whole system.**
Feature it. A check that cannot fail is not a check.

> **Status: not built.** There is an `outputs/metrics/external_check.json`, but
> it is a different thing - it verifies that each manually sourced file is
> present, parseable and the right shape. It does not compare modelled capital
> against disclosed capex. Do not let the filename fool you or an examiner.
>
> **And note the awkward interaction with §5.4.1.** Capital in the shipped code
> is a flat $4m per activation, not a sum of eight estimated buckets. Aggregate
> a constant to metro level and you have multiplied it by a count - so the check
> would currently be testing whether the activation *count* is right, not
> whether the capital *model* is. The eight-bucket decomposition has to be built
> before the external check means anything. Say that rather than letting someone
> discover it.

---

## 5.4 Net present value

### The structure

For each ZIP, over the horizon *H*:

```
              H     (1 - θ_i) · N_i(t) · m  -  c_i(t) · N_i(t)
   NPV_i  =   Σ    ------------------------------------------   -   K_i
             t=1                  (1 + r)^t
```

| Symbol | Meaning |
|---|---|
| `θ_i` | cannibalisation coefficient — the fraction that isn't incremental |
| `N_i(t)` | volume in year *t* |
| `m` | contribution margin per incremental order |
| `c_i(t)` | per-package delivery cost from §5.1 |
| `r` | discount rate (10%) |
| `H` | horizon — **7 years**, not 5; an earlier version of this chapter said 5 |
| `K_i` | total capital ($4m per activation in the shipped baseline) |

`H`, `r` and the $4m are frozen in
`src/siting_atlas/optimize/params.py::PortfolioParameters`, which is also what
`outputs/metrics/portfolio_report.json` echoes back. If you quote them, quote
them from there.

### 5.4.1 Where each term ACTUALLY comes from today

This is the table to memorise, because it is the one that separates what the
code computes from what the proposal promised.

| Term | What the proposal said it would be | What the code uses TODAY |
|---|---|---|
| `c_i(t)` | Daganzo continuous approximation over a solved depot network | **Exactly that.** Real, run, 2,333 priced ZCTAs, median $1.0830/parcel (run `20260914-002418-0623`). But see §5.6.2: 42% of depots exceed the 40,000 parcels/day cap, so line haul is a **lower bound** |
| `K_i` | eight decomposed capital buckets | A single **$4m per activation**, the midpoint of the $3-5M range. The eight-bucket decomposition in §5.3 is a design, not a fitted object |
| `N_i(t)` | **"draws from the hazard model's posterior"** | **An assumption.** Households x 3.2 parcels/household/week x an income scaling, from `cost/params.py`. Flat over time |
| `θ_i` | the Pollmann distance-band estimate from Part 3 | **An assumed constant**: 20 km radius, 0.18 peak, saturating on neighbour exposure |
| `m` | a number | **Deliberately not chosen.** It is unobservable, so the tool solves a frontier over it instead - see §5.7 |

**The `N_i(t)` line is the one that changed, and you must be able to say why.**
An earlier version of §5.5 sourced `N_i(t)` from "the hazard model's posterior".
That model was fitted on real data and it failed (AUC 0.6894 against a null of
0.5000, calibration 170 times worse than a constant-rate null, negative Brier
skill on both hold-outs). **A model whose probabilities are worse calibrated
than a constant has no posterior you would want to draw demand from.** Drawing
from it would not add information; it would add noise wearing a distribution's
clothing.

So the demand-arrival term is currently **an assumption, not a model output**,
and the honest reading of the NPV layer is:

> *"The cost side is measured. The demand side is assumed. The cannibalisation
> side is assumed. What the NPV layer therefore delivers is a rigorous,
> reproducible answer to a conditional question - given this much volume and
> this much cannibalisation, is the activation worth it - and not a forecast of
> volume."*

> **Worked example of why that distinction matters.** Two ZCTAs, both 12,000
> households. The cost model prices them at $1.02 and $1.41 per parcel, and
> those two numbers are *earned*: they come from measured density, measured
> distance to a solved depot, and measured local wages. The volume figure -
> 12,000 x 3.2 parcels/week x an income adjustment - is the **same formula
> applied to both**, so it can rank them but it cannot tell you whether either
> will actually see that volume in 2029. The ranking is defensible. The absolute
> NPV is only as good as an assumption somebody typed.

**Say this proactively.** A reviewer who finds an assumed demand curve behind a
dollar NPV, unannounced, will not believe the cost model either - and the cost
model deserves to be believed.

### The one term to explain carefully

`(1 - θ_i)` is where all of Part 3 *would* land. If θ = 0.4, then **40% of
observed orders were cannibalised** from the existing 2-day channel and only 60%
count as incremental revenue.

> **Why this term decides everything.** A ZIP with 1,000 new orders/month looks
> great. If θ = 0.7, only 300 are genuinely new — and you just spent $4M for
> 300 orders/month. **The entire causal apparatus in Part 3 exists to estimate
> this one number**, because getting it wrong flips the sign of the decision.

> **And it has not estimated it.** Part 3 is the project's second estimand and
> **not one line of it has been built** - no synthetic control, no placebo
> inference, no distance bands. What the optimiser uses instead is a constant:
> a 20 km radius, a 0.18 peak, applied through a saturating function of
> neighbour exposure, `peak * (1 - exp(-exposure))`. Its own docstring calls it
> a placeholder for the Pollmann estimate.
>
> **That is not a small caveat, given the paragraph above.** The chapter has
> just argued that θ decides the sign of the decision, and θ is assumed. The
> correct conclusion is not "therefore the NPV is worthless" - it is
> "therefore the deliverable is a frontier and a break-even, not a dollar
> figure", which is exactly what §5.7 ships. The tool declines to pretend it
> knows the two numbers it does not know.

---

## 5.5 Monte Carlo — it ran, and here is what it settled

> **A claim withdrawn, and it is the biggest correction in this chapter.**
> This section used to say the Monte Carlo was *"designed scope"*, *"blocked"*
> on the fact that three of its four inputs had no uncertainty model, and
> *"still on the backlog"*. **All of that is now false.** The Monte Carlo has
> been run. It is 500 draws over 21 sampled parameters, 500 of 500 succeeded,
> seed `20260914`, artefacts `outputs/metrics/montecarlo_report.json` and
> `outputs/tables/montecarlo_draws.parquet` (500 rows x 28 columns).
>
> The section also used to print an **illustrative** histogram with P10 -$0.4M,
> P50 +$1.2M, P90 +$2.9M as though those were results. They were invented to
> show a shape. They are replaced below by measured numbers.
>
> And it used to describe a **24-billion-evaluation** bootstrap
> (10,000 draws x 1,000 bootstraps x 2,413 ZIPs). **That was never run and
> there was never a 10,000-draw Monte Carlo either.** No bootstrap layer
> exists. See §5.8, where the same 24-billion figure needs the same treatment.

### Why not just compute NPV once?

Because every input is uncertain, and a single point estimate hides that
completely.

### What was actually sampled, and what was not

The sampler does not draw from `N_i(t)` posteriors or synthetic-control
weights, because those still do not exist. It draws from the **parameter
ranges in `docs/data/PARAMETERS.md`** -- 21 of them, all at once, six
portfolio parameters (`p_*`) and fifteen cost parameters (`c_*`) -- and
re-solves the whole cost model and the whole portfolio optimiser on each draw.
That is a weaker thing than the original design, and a real thing rather than
a planned one. Note what is **not** in the `p_*` list:
`capital_per_activation_usd` is held fixed, which is why the capital band
below carries no information of its own.

| Draw | Specified source | What the 500 draws actually do |
|---|---|---|
| `N_i(t)` | the hazard model's posterior | **Not sampled from a posterior.** Still a formula. Its *inputs* are sampled: `parcels_per_household_per_week`, `parcels_per_stop` |
| `θ_i` | synthetic-control weight uncertainty | **Not estimated.** But `cannibalisation_peak` and `cannibalisation_radius_km` are sampled across their assumed ranges, and they turn out to dominate |
| `c_i(t)` | routing and density variance | **Sampled**, through 15 cost parameters. The five named scenario tables remain as a separate, auditable sweep |
| the capital buckets | each proxy's uncertainty | **Not sampled.** Capital is still exactly $4m per activation in all 500 draws |

### The measured bands

```
   quantity                p10       p50       p90       min       max
   ---------------------------------------------------------------------
   activations n           152      264.5      306        82       385
   capital $bn           0.608     1.058     1.224     0.328     1.540
   break-even margin    1.0892    1.3682    1.7259    0.8604    2.3288
   median $/parcel      0.8368    1.1224    1.4836    0.6128    2.0951
   optimality gap       0.0555    0.0968    0.1532    0.0110    0.2639
   ---------------------------------------------------------------------
   n: mean 247.3, sd 58.9, over 500 draws, 0 failed
```

### What it settles, and this is the point of having run it

The published headline activation count has drifted across drafts of this
project: 330, then 317, then 282. The obvious suspicion is that someone
changed a parameter. **The Monte Carlo rules that out.**

```
   published figure   percentile of the 500 draws   verdict
   -----------------------------------------------------------------
   282                          67th                INSIDE the band
   317                          95th                outside
   330                          97th                outside
   -----------------------------------------------------------------
```

282 sits comfortably inside the plausible range. 330 does not, and 317 barely
does not. So the drift was **real**, it was not parameter churn, and the cause
is elsewhere: it is **depot placement**, which is re-solved upstream of the
optimiser and is not classified as a parameter, so the sampler never touches
it. That is a finding about the project's own definition of "parameter", and
it is worth volunteering.

**The second thing it settles is less flattering.** In all 500 draws,
`capital_usd` is exactly `$4,000,000 x n` -- the standard deviation of the
ratio is exactly zero. So the three published capital figures, **$1.128bn,
$1.268bn and $1.320bn, are not three financial results.** They are the three
activation counts 282, 317 and 330 restated in dollars, and nothing more. If
you quote a capital figure, say that.

### Where the variance comes from

From `docs/data/UNCERTAINTY.md` §5.1, a standardised linear regression of the
activation count on all twenty-one sampled inputs at once -- not a
one-at-a-time sweep, which cannot see interactions.

```
   parameter                          rho      share of variance in n
   ----------------------------------------------------------------------
   cannibalisation_peak             -0.622            44.3%
   cannibalisation_radius_km        -0.249             6.9%
   parcels_per_stop                 +0.238             5.0%
   delivery_days_per_week           +0.280             4.9%
   parcels_per_household_per_week   -0.136             2.8%
   service_minutes_per_stop         -0.133             2.5%
   ----------------------------------------------------------------------
   cost parameters       18.8%
   portfolio parameters  55.9%
   NOT LINEAR AT ALL     25.3%   <- interaction and threshold behaviour
                                    in the greedy selector
```

**One assumed constant with no external source carries 44% of the variance in
the headline number.** That is the sentence to lead with, not the band.

> **Do not confuse the two variance tables.** The drivers above are for the
> **activation count**. The **break-even margin** has different drivers:
> `service_minutes_per_stop` at 41.6% and `parcels_per_stop` at 36.6%
> (`UNCERTAINTY.md` §5.2). Quoting one table for the other question is an easy
> error and an examiner who has read `UNCERTAINTY.md` will catch it.

### Two caveats that must travel with every quote of these bands

```
  +--------------------------------------------------------------------+
  |  1. IT IS NOT A CONFIDENCE INTERVAL. Never call it one.            |
  |     The artefact says so itself: "Every range is from              |
  |     docs/data/PARAMETERS.md and was chosen by this project;        |
  |     eight of the constants have no external source. This           |
  |     measures how far the answer moves across the range we          |
  |     consider plausible, and it propagates our priors rather        |
  |     than the world's."                                             |
  |                                                                    |
  |  2. EVERY BAND IS A FLOOR, NOT A RANGE.                            |
  |     parcels_per_depot_per_day was NOT sampled, by oversight. It    |
  |     is absent from the 28 columns of montecarlo_draws.parquet.     |
  |     It is the parameter that sets how many depots get solved, so   |
  |     omitting it removes a source of variation that plausibly       |
  |     matters more than several that were included.                  |
  +--------------------------------------------------------------------+
```

### What is still not reported

| Statistic | Status |
|---|---|
| P50, P10 / P90 on n, capital, break-even, cost, gap | **Reported** above |
| Bootstrap CI on the P50 | **No.** No bootstrap layer exists |
| Does the band cross zero? | Not applicable as framed -- the sampler reports break-even margin and activation counts, not a per-ZCTA NPV distribution |
| **Top-K rank stability** | **No.** The draws table emits no per-ZCTA ranking. See Part 4 §4.7 -- this is the cheapest outstanding item in the project |

---

## 5.6 The portfolio problem — why ranking is wrong

This is the most intellectually interesting part of the cost side.

### The instinct, and the hidden assumption

Score every ZIP, sort, take the top 20. That silently assumes:

```
   NPV(A ∪ B)  =  NPV(A)  +  NPV(B)
```

**It doesn't hold.** Two forces, pulling opposite ways:

```
   NEGATIVE INTERACTION                POSITIVE INTERACTION
   cannibalisation:                     shared station, pooled density:
   A steals demand from B               1/sqrt(δ) -> cost falls for BOTH
             \                                    /
              \                                  /
               v                                v
             NPV(A ∪ B)  ≠  NPV(A) + NPV(B)
```

### The worked example — memorise this

```
   EVALUATED ALONE                    EVALUATED AS A BUNDLE

   ZIP A                              ZIP A + ZIP B
     density LOW                        share ONE delivery station
     needs its own station              pooled density crosses threshold
     NPV = -$200k        [reject]       cost per package  -30%

   ZIP B                                NPV = +$1.1M       [accept]
     density LOW
     needs its own station
     NPV = -$150k        [reject]

   A RANKING REJECTS BOTH. THE BUNDLE IS PROFITABLE.
   The ranking never even evaluates the pair.
```

### Why greedy selection carries no guarantee here

There is a beautiful result in optimisation: for **submodular** objectives
(diminishing returns), greedy selection is guaranteed within `1 − 1/e` ≈ 63% of
optimal.

Our objective is not submodular:

```
   cannibalisation    ->  diminishing returns  ->  SUBmodular
   density economics  ->  increasing returns   ->  SUPERmodular
                                |
                                v
                    the objective is NEITHER
                                |
                                v
        the (1 - 1/e) greedy guarantee DOES NOT APPLY
                                |
                                v
        so the size of the gap is an EMPIRICAL question
                                |
                                v
                      <<<  that is the result  >>>
```

### The search space

```
   as a RANKING    ->  2,413 independent decisions
   as a PORTFOLIO  ->  2^2,413 candidate bundles
   restricted to top 200  ->  2^200  ≈  1.6 x 10^60
```

Larger than the number of atoms in the observable universe. **This is the
sentence that ends the "is this a college project?" conversation.**

### How we actually solve it

Not exactly — we don't need to. Greedy construction plus **pairwise-swap
local search** over the top candidate set, scored against a computed upper
bound so the gap is reported rather than assumed.

**It has been run on real data.** Run `20260914-002431-7419`, the frozen
parameters and the solved result:

```
   PARAMETERS (portfolio_report.json -> parameters)
   budget                     $2,000,000,000
   activation capacity        500
   capital per activation     $4,000,000
   horizon                    7 years
   discount rate              10%
   cannibalisation radius     20 km
   cannibalisation peak       0.18
   linehaul sharing           0.35
   delivery days per year     312

   SOLVED (portfolio_report.json -> detail, and top level)
   activations n                      282
   capital deployed          $1,128,000,000   = 56.4% of the budget
   portfolio break-even margin    1.343067     $ per parcel
   greedy break-even              1.343321
   upper bound                    1.212938
   optimality gap                 0.107284
```

> **Three stale figures corrected.** This section used to quote the break-even
> as **"about $1.39 per parcel"**; the artefact says **1.343067**. Earlier
> drafts elsewhere quoted **$1.3842**; also stale. And it used to say the
> optimiser deploys **"roughly two thirds"** of the budget; 282 x $4m is
> $1.128bn against $2bn, which is **56.4%** -- it declines about **44%**, not
> a third. The direction of the finding is unchanged and the size of it is
> larger than we were claiming.

**Do not hardcode the selection count, the capital deployed, or the optimality
gap into your notes.** Those are re-derived on every run and the file is
re-stamped with a fresh `run_id`. Read them from
`outputs/metrics/portfolio_report.json`, or from `docs/STATUS.md`. The figures
printed above carry their `run_id` so that a reader can tell when they went
stale, which is the only reason it is defensible to print them at all.

The finding that is stable across runs, and the one to actually say out loud:

```
  +--------------------------------------------------------------------+
  |  AT A $2 BILLION BUDGET THE OPTIMISER FUNDS 282 ACTIVATIONS FOR    |
  |  $1.128 BILLION -- 56.4% OF THE BUDGET -- AND DECLINES THE         |
  |  REMAINING 44%.                                                    |
  +--------------------------------------------------------------------+
```

**Why the refusal is the result.** The unspent 44% is not a bug, a solver
timeout, or a capacity limit. The activation cap is 500 and the solution has
282, so **the capacity is not binding** and neither is the budget. The
optimiser has evaluated the remaining fundable activations and concluded they
**destroy value at the neutral margin**, so it leaves the money on the table.

> **And check the refusal against §5.5 before leaning on it.** 282 sits at the
> 67th percentile of 500 Monte Carlo draws whose p10-p90 range is 152 to 306.
> The refusal survives across that whole range -- even at the 90th percentile
> the optimiser funds 306 of 500 and spends $1.224bn of $2bn. So "it declines
> to spend" is robust to the parameters. What is *not* robust is the specific
> number 282, and §5.6.1 gives a reason to think even the $1.128bn is wrong.

> **Why a ranking could never have produced that sentence.** A ranking sorts and
> takes the top K. It has no vocabulary for "K should be smaller than your
> budget allows", because it does not evaluate the bundle - it evaluates items
> and stops when the money runs out. The refusal is only expressible by an
> objective that scores portfolios.

> **And an earlier version of ours could not express it either, which is the
> better story.** The first objective *minimised the portfolio's break-even
> margin*. That sounds reasonable until you notice it is minimised at a
> portfolio of **one** - the single cheapest ZCTA. The objective was optimising
> a ratio when the decision needed a total. Be ready to tell that story; a
> reviewer trusts "here is the objective I got wrong and how I noticed" far more
> than a clean result.

**On the optimality gap.** Greedy construction plus pairwise-swap local search
carries no guarantee here (see below), so the solver reports the gap against a
computed upper bound rather than asserting optimality. The current gap is
**0.107284**, between a greedy break-even of 1.343321 and an upper bound of
1.212938. Quote it as *"we report the gap rather than hide it"* - the habit is
the point, not the specific percentage, and the percentage is re-derived every
run.

### 5.6.1 An open defect: the optimiser prices an activation three ways

**This is the same unit-of-analysis error that killed the hazard model, in a
second component, and it was found after the headline was published.** Lead
with that. It is the strongest thing this chapter can say about its own
process and it is also a live, unfixed bug.

`src/siting_atlas/optimize/objective.py` does not have a single, consistent
idea of what "an activation" is:

```
   lines 81-83   an activation is a ZCTA OF RESIDENT DEMAND
                 annual parcels and annual cost are read off the ZCTA row

   line 158      an activation is a FACILITY WITH A CATCHMENT
                 line-haul cost is shared with neighbours, which only
                 makes sense if a station serves more than its own ZCTA

   line 164      an activation is a FACILITY
                 capital = (number of selected ZCTAs) x $4,000,000,
                 with NO de-duplication of ZCTAs that would share a station
```

Lines 158 and 164 agree with each other. Both contradict line 81.

**The measured consequence.** Covering the funded set needs about **103
stations** against **282 charged** at $4m each -- a factor of **2.74**. The
model is charging for 282 buildings to serve a footprint that 103 buildings
would cover. That is a **capital overcharge**, not an undercharge.

```
   WHAT THE OPTIMISER CHARGES        WHAT THE FOOTPRINT NEEDS
   282 x $4m = $1,128,000,000        about 103 stations
                                     factor of 2.74 too much capital
```

> **Does it invert the headline? No, and say why not.** The budget was already
> slack: the optimiser spent 56.4% of $2bn and declined the rest on *value*
> grounds, not on affordability. Charging less capital per activation makes
> more activations affordable, but affordability was never the binding
> constraint, so the refusal stands. What the defect does change is every
> dollar figure attached to the refusal, and it changes them in the direction
> that makes the project look *better*, which is precisely why it must be
> disclosed rather than quietly fixed.
>
> **And the deeper point is the one to lead with in a viva.** Part 4 §4.1
> diagnosed the hazard model as an error about what counts as one observation.
> The same error is here, in the optimiser, in a file nobody re-read after
> that diagnosis was written. Finding your own bug twice in the same shape is
> evidence the diagnosis was right and evidence the fix was not propagated.
> Both halves belong in the answer.

### 5.6.2 An open defect: line haul is a lower bound where it matters most

**42% of the solved depots exceed 40,000 parcels per day**, which is the
`parcels_per_depot_per_day` cap the depot solver is built around
(`cost/depots.py`). Over the cap, the model keeps serving the demand from the
depots it has instead of opening another one, so it does not charge the extra
line haul that the real network would pay.

The consequence is **directional, not symmetric**. A depot blows through the
cap exactly where demand is bunched, and demand is bunched exactly at the top
of the published ranking. So the model **understates cost precisely where the
recommendations are**, and every cost figure in this chapter for a high-demand
ZCTA is a **lower bound**.

> **What this does to §5.5.** It makes the caveat there sharper, not weaker.
> `parcels_per_depot_per_day` is the parameter that governs this behaviour and
> it is **the one parameter the Monte Carlo forgot to sample**. The band on
> the median cost per parcel, p10 $0.8368 to p90 $1.4836, therefore does not
> contain the variation that this defect generates. A floor, not a range.

### 5.6.3 An open defect: rent_index is 94.3% missing and still listwise-deleted

`rent_index` is missing in **at least one quarter for 94.3% of ZCTAs**. Two
stricter readings of the same gap, so that a reader who recomputes it does not
conclude the figure was invented: **88.8%** of ZCTA-quarter rows in
`data/processed/panel.parquet` are null, and **80.5%** of ZCTAs carry no value
in any quarter at all. The stratum where it *is*
observed is **63.6 times denser** than the stratum where it is missing --
1,556.8 against 24.5 households per square mile. So the missingness is not
remotely at random. It tracks urbanity, and urbanity is the single strongest
driver of every cost term in §5.1.

It is nonetheless still dropped listwise, at
`src/siting_atlas/cost/runner.py:166`, where rows with any missing cost
component are removed from the frame. The code comment there gives a correct
reason for dropping incomplete rows -- a NaN row would contribute doors to the
denominator and no dollars to the numerator -- but that reason does not
generalise to a variable that is missing for roughly seventeen ZCTAs in
eighteen, and missing *systematically*.

> **How to state it.** *"Real-estate cost enters the model through a variable
> that is present for about one ZCTA in eighteen, and the ones where it is
> present are 63.6 times denser than the ones where it is not. Listwise
> deletion there is not a data-cleaning step, it is a sample-selection
> decision, and it is biased against exactly the sparse ZCTAs the siting
> question is about."* Conceding it in that form is stronger than waiting to
> be asked which ZCTAs got dropped.

All three defects in §5.6.1 to §5.6.3 are recorded in `docs/PLAN.md` §7 with
their derivations, and none of the three is fixed at the time of writing.

### The honesty requirement

**Do not claim this as a novelty.** Multi-facility network optimisation has been
a mature commercial category for twenty years — Coupa Supply Chain Guru,
AIMMS, anyLogistix, Optilogic. Location-allocation and p-median problems are
textbook operations research.

> **How to state it:** *"This is a correctness fix, not a contribution. Ranking
> is simply the wrong model of the decision. What's less common is solving it
> with an empirically estimated cannibalisation coefficient rather than an
> assumed one — but the optimisation itself is standard, and I'd cite the
> p-median literature."*

**Volunteering that boundary is worth more than the claim would have been.**

---

## 5.7 Break-even inversion — making it prescriptive

> **THERE IS NO FRONTIER IN THE ARTEFACT. Read this before the rest of the
> section.** `outputs/metrics/portfolio_report.json` contains the key
> `"frontier": null`, and `"naive_breakeven": null` beside it. Run
> `20260914-002431-7419` solved **one** portfolio at the neutral margin, not a
> ladder. Any text in any document that describes reading a six-row margin
> ladder out of that file -- including the version of this section that stood
> here until today -- is describing something that is not there.
>
> **What withdrawn.** This section used to print a three-band ASCII ladder
> (low / mid / high), assert that the portfolio "saturates against the
> 500-activation capacity", and instruct the reader to "read the run-stamped
> ladder out of `portfolio_report.json`". The ladder does not exist in the
> artefact; the saturation claim is contradicted by the artefact, which solves
> to **282 activations against a capacity of 500** so that **neither** the
> capacity nor the budget binds; and the instruction sends a reader to a null
> field. The break-even was quoted as **$1.39** and is **1.343067**.

The *argument* for a frontier is unchanged and still correct: the operator's
contribution margin per parcel is unobservable, NPV is linear in that margin,
so picking a value for it would pick the answer. The right deliverable is
therefore a curve over the margin, not a portfolio at one point on it.

**What the tool ships today is one point on that curve, plus the point's
break-even.** At the neutral margin it funds 282 activations and reports the
margin at which that portfolio washes its face:

```
   portfolio break-even margin    1.343067   $ per parcel
   greedy break-even              1.343321
   upper bound                    1.212938
   optimality gap                 0.107284
   activations at that solution         282   (capacity 500, NOT binding)
```

Read that as: **below about $1.34 per parcel of contribution margin the funded
portfolio does not pay for itself; above it, it does.** That single threshold
is the honest deliverable, and it is falsifiable without ever guessing the
operator's P&L. The frontier over a ladder of margins is **specified and not
built**, and the `"frontier": null` in the artefact is the project saying so
in machine-readable form.

> **The shape claim, with the part that is supported separated from the part
> that is not.** *Supported:* the portfolio is empty below a threshold and
> grows through a middle band -- that follows from the objective and from the
> break-even being interior. *Not supported:* that it then "saturates against
> the 500-activation capacity". Nothing in any current artefact shows the
> capacity binding. The Monte Carlo's 500 draws reach a maximum of **385**
> activations across the whole plausible parameter range (§5.5), so the cap is
> not approached even at the extreme. Drop the saturation claim until a
> frontier run produces it.

Instead of *"what is the NPV?"* ask *"what would have to be true for this to
work?"* — invert the NPV function and solve for the threshold.

> **Example output.** *"Boise 83702 crosses NPV = 0 if any one of: drop density
> rises 22%, OR permitting cost falls $180k, OR cannibalisation drops below 9%."*
>
> **Illustrative.** The per-ZCTA inversion is a root-find on a function that
> already exists and is on the backlog; the specific 22% / $180k / 9% are made
> up to show the shape of the output. What *has* been solved is the
> portfolio-level break-even, **1.343067** per parcel, run
> `20260914-002431-7419`.

**Why it matters.** It converts the tool from descriptive to prescriptive, and it
gives a city council a **lever** — "here is what we would need to change" is
actionable in a way "your score is 0.34" is not.

It is a root-find on a function we already have: roughly half a day.

> **Honesty note:** what-if and sensitivity analysis ships in every commercial
> supply-chain package. This is a good UX feature, not a contribution.

---

## 5.8 The scale framing

File size is the only axis on which this project is small.

```
   DECISION VALUE
     2,413 pilot ZIPs  x  $3-5M per activation
     =  $7.2B - $12.1B of capital allocation in scope
     national, if scaled:  $101B - $169B

   COMPUTE
     500 Monte Carlo draws, 500 succeeded, 21 parameters sampled
     each draw re-solves the cost model AND the portfolio optimiser
     (montecarlo_report.json, seed 20260914)

   COMBINATORICS
     2^2,413 portfolio search space

   INTEGRATION
     14 registered sources (13 analytical), 8 grains, 8 years

   FOOTPRINT
     1,081,312 rows / 14 MB      <-- the only small number
```

Most figures above are read from `outputs/metrics/scope.json`, which
`report/scope.py` derives from the artefacts. That machinery exists precisely
because an earlier draft of this handbook asserted 5,200 ZCTAs and $15.6–26B
from an estimate rather than a count. **The compute line is the exception and
it is a live inconsistency:** `scope.json` still carries
`"draws_total": 24130000000` and `"label": "24 billion"`, from the
`report/scope.py` formula `10,000,000 draws per ZCTA x 2,413 ZCTAs`. **No such
run has ever happened**, and `scope.json` is stamped with the older run
`20260912-222301-dbde`. The number above comes from `montecarlo_report.json`
instead, which is the artefact that records an execution rather than an
arithmetic product.

> **A claim withdrawn.** This section used to say *"24,130,000,000 Monte Carlo
> evaluations (specified, not yet run)"* and the sentence below used to read
> *"I'd rather spend the compute on 24 billion uncertainty draws than on
> scanning rows I don't need."* There was never a 24-billion-draw run, there
> was never a 10,000-draw run, and there was never a bootstrap layer. Quoting
> a compute figure that was only ever a multiplication, in a section whose
> whole purpose is to establish that the project's numbers are counted rather
> than estimated, is exactly the failure mode that section was written to
> prevent.

> **The sentence, repaired:** *"I deliberately kept the analytical panel
> small. The hard problem is identification, not throughput. The 500 Monte
> Carlo draws I did run each re-solve the whole cost model and the whole
> portfolio optimiser over 21 sampled parameters, and they bought a finding --
> that the drift in the headline was not parameter churn (§5.5). A bigger
> number of cheaper draws would have bought nothing."*

A junior brags about volume. A senior explains a trade-off.

---

## 5.9 Part 5 self-check

1. What are the two components of delivery cost, and which one delivers no
   packages?
2. Why does OSRM preprocessing threaten the project, and what removes it from
   the critical path?
3. What is the circuity fallback, and why is losing exact routing acceptable
   here?
4. Which four capital buckets dominate, and what does the tornado plot let you
   argue?
5. In the NPV equation, what does `(1 − θ)` do, why does Part 3 exist, and what
   value does θ actually take in the shipped code?
6. The Monte Carlo **has** been run. How many draws, how many parameters, and
   what are the two caveats that must travel with every band you quote from
   it? (One is about what it is *not*; one is about a parameter that was
   omitted.)
6a. What does the Monte Carlo settle about the published activation counts
    282, 317 and 330? Give the three percentiles and name the cause of the
    drift.
6b. Why are $1.128bn, $1.268bn and $1.320bn *not* three financial results?
6c. Which single parameter carries 44.3% of the variance in the activation
    count, and why is that an uncomfortable fact rather than a neutral one?
7. Work through the A + B bundle example from memory.
8. Why does the `1 − 1/e` greedy guarantee not apply here?
9. Why must you *not* claim the portfolio optimiser as a novelty?
10. Give the three magnitude numbers that answer "isn't this a college
    project?" -- and say why "24 billion evaluations" is not one of them.
11. Where does `N_i(t)` come from today, and what was it *supposed* to come
    from? Why can it not come from there?
12. The optimiser leaves **44%** of a $2bn budget unspent -- not a third. Why
    is that a result rather than a bug, why could a ranking never say it, and
    what in the artefact shows that neither the budget nor the 500-activation
    capacity is binding?
13. Which figures in this chapter must be read from an artefact rather than
    quoted from the page, and why?
14. Name the three open defects in §5.6.1-§5.6.3. For the first, say how many
    ways `objective.py` prices an activation, what the overcharge factor is,
    and why it does **not** invert the headline.
15. Why is the cost figure for a high-demand ZCTA a lower bound rather than an
    estimate, and what does that do to the §5.5 band on median cost per
    parcel?
16. `rent_index` is missing for 94.3% of ZCTAs and dropped listwise. Why is
    that a sample-selection decision rather than a cleaning step?
17. What is in `portfolio_report.json` under the key `"frontier"`, and what
    does that mean for any sentence beginning "the margin frontier shows"?

---

**Next:** `HANDBOOK_06_AGENT.md` — LLMs, RAG, ReAct, MCP, and the six gates.
