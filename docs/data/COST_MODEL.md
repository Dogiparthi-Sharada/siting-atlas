# The Cost Model, Explained From Zero

> ## STATUS — this document describes the RETIRED pilot cost model
>
> **Updated 2026-09-16.** On 2026-09-16 the depot layer was rebuilt on the
> operator's **501 real address-geocoded delivery stations**
> (`src/siting_atlas/cost/stations.py`), replacing the solved 334-site
> p-median in `depots.py`. Every figure below belongs to the p-median run and
> is correct *for that run*; none of it describes the current model.
>
> | | pilot (this document) | current |
> |---|---|---|
> | depots | 334 solved | 501 real, 481 with a costed ZCTA |
> | ZCTAs costed | 2,333 (10 metros) | 8,037 (57.8% of US households) |
> | median $/parcel | $1.0830 | **$1.1389** |
> | median line haul | 4.02 mi | **9.09 mi** |
> | service/vehicle/drive/distance | 66.96/22.93/6.97/3.14 | **59.75/21.63/12.63/5.98** |
> | artefact | `cost_report.json` `20260916-064133-4d65` | `cost_by_station.json` `20260916-131845-34f1` |
>
> The `1/√δ` mechanism, the parameter provenance and the derivations below are
> all unchanged and still the best explanation of how the model works — only
> the depot layer and the costed universe moved. **`docs/NUMBERS.md` §10 is the
> current figures**, §10.3 is the full before/after, and §10.4 records that the
> "zero of 43 facilities sit in their metro's cheapest decile" statistic is
> **withdrawn** as unidentified.


**What it costs to deliver one parcel in one ZIP-code area, why the answer
turns on how tightly packed the deliveries are and how far the nearest depot
is — two things that are substantially the same thing — and how to read the
table it produces.**

Code: `src/siting_atlas/cost/params.py` (every assumption),
`daganzo.py` (the maths), `depots.py` (where the vans start from),
`runner.py` (the L4 stage).
Output: `outputs/tables/cost_to_serve_2023q4_baseline.parquet`.

This document assumes you know nothing about vehicle routing. Every idea
gets a concrete number attached to it. Every number was re-measured on
2026-09-12 after the depot network replaced the single-centroid proxy; see
§6.1 for what changed and why it mattered.

---

## 1. The question, and why it is hard

You want to know what it costs a delivery company to serve ZIP code 11222
(Greenpoint, Brooklyn) for one day.

The obvious approach is to solve the routing problem: take the actual
addresses, work out the shortest tour through them, add up the miles and the
hours. That is the Travelling Salesman Problem, and it is famously expensive
to solve. Now note that we need this answer for **2,333 ZIP-code areas**, and
that a Monte Carlo uncertainty pass would need it ten thousand times over.
Exact routing is not on the table; it is not close to being on the table.

**You do not need it.** You are not dispatching vans tomorrow. You want the
cost of a *good* route, to within a few percent, for a place you have never
seen. That is a completely different and much easier question.

---

## 2. The one insight: distance scales as 1 / sqrt(density)

Carl Daganzo's continuous approximation says: stop thinking about individual
addresses and start thinking about a *density of addresses smeared over an
area*. Then the length of a good tour follows a law.

The law comes from the Beardwood-Halton-Hammersley theorem, which is worth
one sentence in plain English:

> If you scatter `n` points at random in an area `A` and walk the shortest
> loop through all of them, that loop is about `k * sqrt(n * A)` long.

`k` is a constant — a property of the geometry, not of your particular
points.

### 2.1 Turning that into cost per stop

One van handles `C` stops per shift (here, 120). If stops are packed at
`delta` stops per square mile, the patch of ground that van works is
`C / delta` square miles. Put those into the theorem:

```
    tour length  =  k * sqrt( C * (C / delta) )  =  k * C / sqrt(delta)
    per stop     =  k / sqrt(delta)
```

Add the drive out from the depot and back, `2L`, shared across all `C`
stops on the tour, and you have the whole model:

```
                       2 * L                 k
     d_stop     =     ---------     +     ----------
                          C              sqrt(delta)

                   line haul, shared      local travel between
                   across the tour        doors, per stop
```

Three inputs: how far the depot is, how many stops per tour, how dense the
stops are. No addresses, no street network, no solver.

### 2.2 What "1 over square root" actually feels like

This is the part people get wrong, so here it is as a picture. Square root
is a *slow* function. Doubling density does not halve your local driving:

```
  local miles per stop  =  0.57 * 1.30 / sqrt(delta)

  delta (stops/sq mi)   local mi/stop     vs. delta = 1
  -------------------   -------------     -------------
          1               0.741                 1.0x
          4               0.371                 2.0x cheaper
         25               0.148                 5.0x
        100               0.074                10.0x
      1,000               0.023                31.6x
     10,000               0.0074              100.0x

  100x more density  ->  only 10x less local driving.
```

Two consequences, and the whole siting argument rests on them:

- **Density helps, but with diminishing returns.** Going from a rural ZCTA
  to a suburban one is transformative. Going from a dense suburb to
  Manhattan barely moves local travel at all — by then local travel has
  almost vanished and something else dominates the bill.
- **Line haul is the opposite.** It is divided by `C`, so in a dense zone
  where you fill a van in a few blocks it is nearly free per stop, and in a
  sparse zone where the van drives far to reach its first door it is brutal.

That crossover — local travel flattening out while line haul stays punishing
— is what separates a profitable ZIP from an unprofitable one.

### 2.3 Density does NOT simply dominate, and saying so would be wrong

It is tempting to write "cost is driven by density" and stop. The measured
rank correlations across the 2,333 pilot ZCTAs say otherwise:

```
   Spearman(cost per parcel, stop density)      =  -0.763
   Spearman(cost per parcel, depot distance)    =  +0.777
   Spearman(stop density,    depot distance)    =  -0.665
```

Two things to take from that. First, **depot distance is at least as strong a
predictor of cost as density is** — +0.777 against −0.763. Second, the two
are themselves strongly related (−0.665), and **that relationship is not a
coincidence, it is built in**: depots are placed where the parcels are (§6.1),
so a sparse ZCTA is by construction far from the nearest concentration of
demand. Density and remoteness are two views of the same underlying fact.

So the honest sentence is: *cost is driven by how tightly packed the
deliveries are and how far the nearest depot is, and those two are
substantially the same thing.* Not "density dominates".

---

## 3. From distance to dollars

Distance is not the bill. The chain from households to cost per parcel runs
like this, and every arrow is a line of code in `daganzo.py`:

```
  households                        [panel, ACS 2023]
      x 3.2 parcels/household/week
      x (income / 75,000) ^ 0.35    income scaling
      / 6 delivery days
      = daily parcels
      / 1.4 parcels per stop        <- a parcel is NOT a stop
      = daily STOPS
      / land area sq mi             <- LAND, not total
      = delta, stop density
            |
            |   in parallel: the depot network
            |   K = ceil(metro daily parcels / 40,000) depots per metro,
            |   placed by parcel-weighted k-means; L = miles to the
            |   NEAREST one, x 1.30 circuity        [depots.py]
            v
  d_stop = 0.57 * 1.30 / sqrt(delta)  +  2 * L / 120
            |
            +--> x ($/mile: diesel/14 mpg + $0.19 wear) = cost_distance
            +--> / 22 mph x hourly wage                 = cost_drive_time
  2.4 min at the door / 60 x hourly wage                = cost_service_time
  $41 van lease / 120 stops                             = cost_vehicle
            |
            v
      cost per STOP  = the four above, summed
      cost per PARCEL = cost per stop / 1.4
```

Two of those steps are where naive versions of this model go wrong:

**A parcel is not a stop.** The driver is paid once per door, not once per
box. If you charge 2.4 minutes of labour to every parcel, you overstate the
cost of exactly the dense, high-volume ZIPs the ranking is supposed to find
cheap. The model consolidates at 1.4 parcels per visit.

**Land area, not total area.** A coastal ZCTA that is two-thirds water has
its deliveries concentrated on the land. Dividing by total area would make it
look artificially cheap.

---

## 4. A worked example: two real ZCTAs, every number

These are the actual values in `panel.parquet` for 2023Q4 and the actual
values in the cost table. Reproduce them with §8.4 of
[`../REPRODUCE.md`](../REPRODUCE.md).

### 4.1 The inputs

| | 11222 Greenpoint, Brooklyn | 83650 Murphy, Idaho |
|---|---|---|
| metro | New York | Boise City |
| households | 20,277 | 202 |
| median household income | $123,963 | $44,375 |
| land area | 1.523 sq mi | 1,455.965 sq mi |
| driver wage (BLS, annual mean) | $52,480 | $54,700 |
| diesel | $4.2247 /gal | $4.3497 /gal |

Two places that could hardly be less alike: 13,300 households per square
mile against 0.14.

### 4.2 Step by step

```
                                     11222            83650
  ------------------------------------------------------------
  income scale
    (inc / 75,000) ^ 0.35            1.192287         0.832199
  weekly parcels
    hh x 3.2 x scale                77,363.21           537.93
  daily parcels  (/ 6)              12,893.87            89.66
  daily stops    (/ 1.4)             9,209.91            64.04
  stop density   (/ land)            6,047.21           0.0440
  ------------------------------------------------------------
  local mi/stop
    0.57 x 1.30 / sqrt(delta)          0.009529         3.533208
  miles to NEAREST depot (x 1.30)      1.9473          61.4046
  line-haul mi/stop  (2L / 120)        0.032455         1.023409
  TOTAL miles per stop                 0.041984         4.556617
  ------------------------------------------------------------
  fully loaded wage/hour
    wage x 1.32 / 2,808 h             $24.67           $25.71
  cost per mile
    diesel/14 + 0.19                   $0.4918          $0.5007
  ------------------------------------------------------------
  cost_distance     (mi x $/mi)        $0.0206          $2.2815
  cost_drive_time   (mi / 22 x $/h)    $0.0471          $5.3258
  cost_service_time (2.4/60 x $/h)     $0.9868          $1.0285
  cost_vehicle      ($41 / 120)        $0.3417          $0.3417
  ------------------------------------------------------------
  COST PER STOP                        $1.3962          $8.9775
  COST PER PARCEL   (/ 1.4)            $0.9973          $6.4125
  rank (of 2,333)                       306             2,333
```

**Notice what the depot network did to Greenpoint.** Under the old
one-depot-per-metro proxy, 11222 sat 0.37 miles from the assumed depot —
because the population-weighted centre of the New York metro happens to land
almost on top of it — and it ranked **6th cheapest of 2,333**. With a real
network of depots serving the whole metro, its nearest depot is 1.95 miles
away, and it ranks **306th**. Nothing about Greenpoint changed. What changed
is that the model stopped rewarding ZCTAs for being near an imaginary point.
That single fix is the difference between a ranking and an artefact.

### 4.3 Read the example, do not just look at it

**The square-root law, verified.** Density ratio is
`6047.21 / 0.0440 = 137,487` — Greenpoint is 137 *thousand* times denser.
The square root of that is **370.8**. And the local-travel ratio is
`3.533208 / 0.009529 = ` **370.8**. Exactly. That is not a coincidence; it is
the law, and you can check it on any two rows of the table.

**Where the money actually goes is different in the two places.** Split the
cost per stop into shares:

| Component | 11222 | 83650 |
|---|---|---|
| driver time at the door | 70.7% | 11.5% |
| driver time driving | 3.4% | 59.3% |
| fuel and wear | 1.5% | 25.4% |
| vehicle lease | 24.5% | 3.8% |

In Greenpoint the van barely moves; the bill is overwhelmingly the 2.4
minutes it takes to park, walk up and hand the parcel over, plus the lease on
a van that is paid for whether it is full or not. **In a dense city, cost is
a labour problem, not a transport problem.** In Murphy, Idaho, 84.7% of the
bill is moving the vehicle. Any intervention that helps one place is close to
useless in the other — which is precisely why a single national
cost-per-parcel number would be meaningless.

**The 6.4x spread is the whole business case.** $1.00 against $6.41 per
parcel. If the contribution margin on a parcel is, say, $2, Greenpoint is
comfortably profitable and Murphy loses four dollars a parcel, every parcel,
forever. No amount of operational cleverness closes that.

**Line haul is small per stop but not negligible overall.** In 11222 it is
0.032 miles per stop — because 2L is divided by 120 — from a depot 1.95 miles
away. In Murphy, 61 miles of line haul contributes 1.02 of the 4.56 miles per
stop, so the dominant term in the sparse case is still *local* travel: 3.53
miles between one farmhouse and the next. Across the whole pilot, line haul
is **63.4% of the median ZCTA's distance per stop** — but distance is only
about 11% of cost, so the depot assumption moves roughly **7% of the total
bill**. Small, and not nothing, which is exactly why it had to be solved
rather than guessed (§6.1).

---

## 5. Every parameter, its provenance, and which way it biases the answer

Each of these lives in `cost/params.py` as a frozen dataclass field with its
justification in the docstring. Nothing here is fitted — they are engineering
and operating assumptions. The *estimated* quantities (wages, fuel, density,
income) come from the panel.

The bias column is the point of the table: if a reviewer disagrees with a
number, they should be able to see immediately whether the current value
flatters the answer or penalises it.

### 5.1 Tour geometry

| Parameter | Value | Provenance | Bias if wrong |
|---|---|---|---|
| `bhh_constant` | 0.57 | Daganzo's value for strip / ring-radial routing in a served zone. The asymptotic random-TSP value is ~0.71; real drivers beat random because they sweep along streets | **Cost DOWN.** 0.57 is the optimistic end, so marginal ZCTAs look better than they are. The `pessimistic_tour` scenario sets 0.71 and moves the median only +1.0% |
| `stops_per_tour` | 120 | Industry last-mile figures run 100-150 per van per shift | Raising it divides line haul across more stops and spreads the lease thinner, so cost falls. `dense_routing` at 150 is the single largest lever in the sensitivity table, -17.6% |
| `circuity` | 1.30 | Street distance over straight-line distance; 1.2-1.4 for US urban grids | Applies to both local travel and line haul, so it scales distance cost roughly linearly. `congested` uses 1.45 |

### 5.2 Vehicle

| Parameter | Value | Provenance | Bias if wrong |
|---|---|---|---|
| `van_mpg` | 14.0 | Diesel sprinter-class van, loaded, stop-start duty | Only touches fuel, which is ~11% of the median bill. `high_fuel` at 11 mpg moves the median +1.8% |
| `maintenance_usd_per_mile` | 0.19 | Wear per mile, on top of fuel | Same channel as fuel; small |
| `van_lease_usd_per_day` | 41.0 | Daily cost of the vehicle whether or not it is full | Spread over `stops_per_tour`, so it is a flat $0.34 per stop everywhere. That makes it 25% of the bill in Greenpoint and 4% in Murphy |
| `avg_speed_mph` | 22.0 | Door-to-door average *including* stopping in traffic, not posted limits | Converts miles into paid driver hours. Dominant in sparse ZCTAs. `congested` at 16 mph is the second-largest lever, +4.4% |

### 5.3 Labour

| Parameter | Value | Provenance | Bias if wrong |
|---|---|---|---|
| `service_minutes_per_stop` | 2.4 | Park, walk, hand off, scan | **The dominant cost at high density.** In 11222 it is 73% of the bill. Get this wrong and every dense ZCTA is wrong |
| `shift_hours` | 9.0 | A delivery shift | Sets the denominator when a BLS annual wage becomes an hourly rate |
| `wage_loading` | 1.32 | Employer cost over base wage: payroll tax, benefits, workers' comp | Scales all labour cost linearly, and labour is ~72% of the median bill, so this is a big multiplier hiding in plain sight |
| implied hours/year | 2,808 | `9 h x 6 days x 52 weeks` | A BLS *annual mean* divided by a six-day schedule. If the real schedule is five days, the hourly rate is understated by 20% |

### 5.4 Demand

| Parameter | Value | Provenance | Bias if wrong |
|---|---|---|---|
| `parcels_per_household_per_week` | 3.2 | ~22 bn US parcels in 2023 over ~131 m households. Anchored to published national volume, not guessed | Scales volume, which changes density, which changes local travel by its square root. A 20% error moves cost per parcel by ~10% |
| `parcels_per_stop` | 1.4 | Parcels handed over in one visit | The one that is a real error and not a rounding one. Setting it to 1.0 would charge full service time to every parcel and penalise dense ZCTAs specifically |
| `income_elasticity` | 0.35 | Richer households order more, but far from proportionally | Set conservatively. **Higher would concentrate predicted demand in wealthy ZCTAs** and flatter the top of the ranking |
| `reference_income_usd` | 75,000 | The income at which 3.2/week applies unscaled | A pivot, not a level. Moving it rescales every ZCTA by the same factor and barely changes the *ranking* |
| `delivery_days_per_week` | 6.0 | Six-day operation | Appears twice — dividing weekly volume, and in the hours-per-year denominator |

### 5.5 Depot geometry

| Parameter | Value | Provenance | Bias if wrong |
|---|---|---|---|
| `parcels_per_depot_per_day` | 40,000 | Throughput of one delivery station. Published figures run 20,000–60,000, so this sits mid-range | **The one that replaced an assumption with a check.** It sets K, the number of depots a metro needs. Raising it builds fewer, more distant depots and pushes cost **UP**; lowering it does the reverse |
| `default_linehaul_miles` | 25.0 | Fallback when geography supplies nothing | Rarely used; only when `cbsa_code` is missing or no depot was placed |
| depot locations | **solved** | Parcel-weighted k-means, K per metro from the throughput above, seeded at 20260912 | See §6.1. Previously a single metro centroid, which was an artefact worth up to $2.62/parcel |

### 5.6 The five scenarios

`SCENARIOS` in `params.py`. Each moves one lever a *plausible* amount rather
than an extreme, so the spread is a credible range and not a worst case
nobody believes.

| Scenario | What moves | Median $/parcel | vs baseline |
|---|---|---|---|
| `dense_routing` | 150 stops/tour, 2.0 min/stop | 0.90 | -17.0% |
| `baseline` | — | 1.09 | +0.0% |
| `high_fuel` | 14 -> 11 mpg | 1.09 | +0.6% |
| `pessimistic_tour` | BHH 0.57 -> 0.71 | 1.10 | +1.0% |
| `congested` | 22 -> 16 mph, circuity 1.45 | 1.14 | +4.4% |

Read that table as a statement about **what this model is sensitive to**.
It is sensitive to labour productivity — how many doors per shift and how
long at each door. It is barely sensitive to fuel. Anyone whose intuition
says last-mile economics are about fuel price should update.

The spread also *narrowed* when the depot network replaced the single
centroid: `congested` used to sit at +14.5% and is now +4.4%, because with
realistic line hauls there is far less driving for a lower average speed to
punish. A sensitivity table computed on the old proxy was partly measuring
the proxy.

---

## 6. What is wrong with this model

Stated plainly, because a cost figure is only as defensible as its stated
weaknesses.

### 6.1 The depot proxy: an assumption we asserted, measured, and found 20x off

This one deserves its own section, because it is the failure mode the whole
project claims to be about.

The first version of the cost model placed **one depot per metro** at the
population-weighted centroid, and its own docstring asserted that the choice
"barely matters" — reasoning that line haul enters divided by `C`, so a
ten-mile error moves cost per parcel by well under a cent.

Then somebody measured it. The arithmetic:

```
   one extra line-haul mile  =  2/C          =  0.0167 mi per stop
   a van-mile costs          =  $0.49 cash + $1.12 driver time = $1.61
   so one mile               =  $0.027 per stop = $0.019 per parcel
   ten miles                 =  $0.19 per parcel
```

Roughly **twentyfold** the claimed effect, not "well under a cent". And under
a single centroid the implied line hauls ran from **0.4 to 145.7 miles**, so
the depot assumption alone was injecting up to **$2.62 per parcel** of spread
into a ranking whose median was $1.51. The model was, to a large degree,
ranking ZCTAs by distance from a metro's centre of mass — an artefact of the
assumption — rather than by cost.

A 145-mile line haul is not a modelling subtlety. It is a description of a
network nobody operates. Real carriers avoid exactly that by building many
delivery stations close to demand, which is *why* line haul is a small term
in practice.

**The fix.** `cost/depots.py` solves a depot network instead of assuming one
point: K depots per metro by parcel-weighted k-means, with

```
   K = ceil(metro daily parcels / 40,000 parcels per station)
```

The throughput number is what makes this an external check rather than a
second free parameter. Across the pilot it implies **334 depots over 11
CBSAs** for 13,152,992 daily parcels — 39,380 per depot. Amazon alone runs
roughly 700–900 US delivery stations, and the pilot holds about 17.6% of the
US population, so Amazon's share here would be ~125–160 and all operators
together ~250–320. **The implied network is the right size**, which it had no
way of being if the throughput figure were badly wrong.

Line-haul p90 fell from 60.2 to **10.05 miles** (median 3.96, max 86.03 in
rural Idaho, which is real remoteness rather than an artefact). Median cost
fell from $1.51 to $1.09 per parcel, and — more importantly — the *ordering*
changed: see what happened to Greenpoint in §4.2.

**What is still wrong with the depots.** They are modelled locations, not
observed ones. Real operators site on industrial land near motorway
junctions, not at the weighted mean of their customers, and they inherit
sites from history. The moment the facility panel lands, these become
observed coordinates and this section becomes a note about how it used to be
done.

### 6.2 Everything else that is still wrong

- **Distance is great-circle times 1.30, not routed.** The drive-time matrix
  (OSM, OSRM, ADR-0002) is designed and not built.
- **Demand is modelled, not observed.** Nobody publishes parcels per ZIP.
  3.2 per household per week scaled by income is an assumption with a
  national anchor, and it is uniform within a metro.
- **Median income is missing for 9.4% of panel rows** — 51 of the 2,333
  pilot ZCTAs, or 2.19% — and falls back to the reference income, which
  makes the scale factor exactly 1.0. That is a neutral assumption and it is
  flagged, not hidden: the output carries an `income_imputed` boolean column.
- **80 ZCTAs are dropped** from the 2,413 pilot areas because they report
  zero households. Keeping them would divide by zero and put an infinite cost
  at the top of the ranking. The drop is logged.
- **Everything is per day, in one quarter, at one wage vintage.** There is no
  seasonality and no capital amortisation in this table.

And the one that matters most:

> **A cheap ZCTA is not a prediction that anyone will build there.** This
> model answers "what would it cost to serve here", which is engineering
> economics. "Will the operator choose to" is the behavioural question, and
> it is answered by the hazard model on the facility panel, not by this
> table. That panel arrived on 2026-09-13 and carries **39 usable events**,
> so even the model that *does* answer it answers it weakly. Do not read
> this ranking as a forecast, and do not read the hazard coefficients as one
> either.

---

## 7. How to read the output table

```bash
.venv/bin/python -m siting_atlas.cost.runner
.venv/bin/python -m siting_atlas.cost.runner --all-scenarios
.venv/bin/python -m siting_atlas.cost.runner --year 2024 --scenario congested
```

Writes `outputs/tables/cost_to_serve_<year>q<q>_<scenario>.parquet`, one row
per pilot ZCTA, sorted cheapest first, plus
`outputs/metrics/cost_report.json`.

### 7.1 The columns

| Column | Meaning |
|---|---|
| `rank` | 1 is cheapest per parcel |
| `zcta` | five-digit code, zero-padded string |
| `daily_parcels` | modelled volume |
| `daily_stops` | doors visited = parcels / 1.4 |
| `stop_density_per_sqmi` | `delta`. The number the whole model turns on |
| `linehaul_miles` | depot to zone, circuity applied |
| `local_miles_per_stop` | the `k / sqrt(delta)` term |
| `linehaul_miles_per_stop` | the `2L / C` term |
| `miles_per_stop` | the two above, summed |
| `cost_distance` | fuel and wear, per stop |
| `cost_drive_time` | paid driving, per stop |
| `cost_service_time` | paid time at the door, per stop |
| `cost_vehicle` | lease share, per stop |
| `cost_per_stop` | the four cost components summed |
| `cost_per_parcel` | `cost_per_stop / 1.4`. **The headline** |
| `daily_cost_usd` | `cost_per_stop x daily_stops` |
| `vans_required` | `ceil(stops / 120)` |
| `income_imputed` | true where median income was missing |
| `metro_label`, `state`, `population`, `land_area_sqmi` | context |

### 7.2 Five rules for reading it

1. **The components are per STOP, not per parcel.** Dividing them by
   `cost_per_parcel` makes the shares sum to 140%. This is a real bug that
   was in the reporting code and was fixed; do not reintroduce it in your own
   analysis.
2. **Compare within a metro before comparing across.** Wages and diesel are
   metro- and state-level, so a cross-metro difference partly reflects the
   labour market rather than the geography.
3. **Look at `stop_density_per_sqmi` before you believe a rank.** If it looks
   wrong, the cost is wrong, because everything else is derived from it.
4. **`cost_per_parcel` is also a break-even margin.** A ZCTA at $0.99 pays
   for itself if the operator's contribution margin per parcel exceeds $0.99.
   That framing is deliberate: it lets the model make a falsifiable claim
   without ever guessing the operator's P&L. Note what it is *not* good for —
   `optimize/` tried minimising a portfolio's break-even margin and it turned
   out to be minimised at a portfolio of one. It is the right way to describe
   a single ZCTA and the wrong thing to optimise over a set.
5. **These are per-DELIVERY-day figures, not per calendar day.** The network
   delivers 6 days a week, 312 a year. Annualising `daily_parcels` or
   `daily_cost_usd` at 365 invents 53 days of volume that never happen —
   which is a bug that really was live in `optimize/` until 2026-09-12.

### 7.3 The baseline run, for orientation

2023Q4, baseline scenario. **Re-derived 2026-09-16** from
`outputs/tables/cost_to_serve_2023q4_baseline.parquet` and
`cost_report.json` (`20260916-024154-0aa8`):

| | |
|---|---|
| ZCTAs | 2,333 (of 2,413 pilot; 80 have no households) |
| depots placed | 334 across 11 CBSAs |
| median | $1.0830 / parcel |
| p10 / p90 | $0.9778 / $1.4180 |
| cheapest metro | Miami, median $0.9437 |
| dearest metro | Boise, median $1.4349 |
| second dearest | Nashville, median $1.3084 |
| most expensive ZCTA | 83650, Boise, $6.42 |
| fleet | 78,292 vans/day |
| total | $14.00 m/day |

> **Corrected 2026-09-16.** This table was stamped "verified 2026-09-12" and
> carried the **pre-p-median** run throughout: median $1.09, p10/p90
> $0.99/$1.36, Miami $0.95, Boise $1.31, 79,484 vans, $14.09 m/day. Three of
> those are worth naming. **$1.31 is Nashville, not Boise** — the second
> dearest metro had been written into the dearest metro's row, which hid
> $0.12 of the national range. **The p90 moved 4.0%**, from $1.36 to $1.4180,
> so the old pair understated the spread. And **79,484 is not the fleet**: it
> is the sum of a per-ZCTA `ceil`, taken 2,333 times, which invents 1,192
> vans; `cost_report.json` reports `ceil(sum(van_days))` = 78,292. See
> `../NUMBERS.md` §10 and its "easily confused" items 11 and 12.

Volume-weighted across the pilot, cost per stop is $1.49 — $1.06 per parcel —
split: driver time at the door **66.96%**, vehicle lease **22.93%**, driver
time driving **6.97%**, fuel and wear **3.14%**. **Nearly three dollars in
four is labour.**

Two notes on that split, because it is easy to quote wrongly:

- It is **weighted by stops**, not a median of per-ZCTA shares. Dense ZCTAs
  carry most of the volume, so an unweighted average over ZCTAs would
  describe a typical *place* rather than a typical *parcel*. The median of
  the per-ZCTA shares is 66.0 / 22.5 / 7.6 / 3.5 and the unweighted total is
  60.5 / 20.7 / 12.9 / 5.8 — both different and less useful statements.
  *(This line previously gave "61.0 / 20.9 / 12.5 / 5.6" as the unweighted
  median; that is close to the unweighted total, not the median, and it was
  measured on the pre-p-median run.)*
- The shares are of cost per **stop**. Dividing them by cost per *parcel*
  makes them sum to 140% — a real bug that was in the reporting code and was
  fixed.

---

## 8. If you want to challenge a number

That is the intended use. Every constant is in one file, frozen, with its
provenance. Change one and re-run:

```python
from dataclasses import replace
from siting_atlas.cost.params import BASELINE
from siting_atlas.cost.daganzo import DaganzoCostModel

mine = replace(BASELINE, service_minutes_per_stop=3.5, stops_per_tour=100)
model = DaganzoCostModel(mine)
```

Or add a named entry to `SCENARIOS` and it appears in `--all-scenarios`
automatically. The frozen dataclass means a scenario cannot be mutated
halfway through a run, so every result stays traceable to the exact
parameter set that produced it — and `cost_report.json` records that set
alongside the numbers.
