# Every Free Parameter, Its Source, and What It Is Worth

> ## STATUS — every cost-model figure below is from the RETIRED pilot
>
> **Updated 2026-09-16.** The parameter provenance in this document is
> unaffected and remains current. The *measured sensitivities and headline
> figures* are not: on 2026-09-16 the depot layer was rebuilt on the
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
> Two further consequences for this document specifically.
> `parcels_per_depot_per_day` (40,000) — the largest **rank** mover in the
> model, Spearman 0.90 — **no longer enters the cost path at all**, because
> there is no placement step left to feed. And every "moves the median by X%"
> figure below was measured on the 2,333-ZCTA pilot frame and has not been
> re-measured on the 8,037-ZCTA one; treat them as indicative of direction and
> rough magnitude, not as current measurements. **`docs/NUMBERS.md` §10 is the
> current figures**, §10.3 is the full before/after, and §10.4 records that the
> "zero of 43 facilities sit in their metro's cheapest decile" statistic is
> **withdrawn** as unidentified.


**The document to hand a reviewer who asks "where does 2.4 minutes per stop
come from?" It answers that question for every constant in the cost and
portfolio models, names the ones that have no published source, and measures
how far the headline moves when each is wrong.**

Code: `src/siting_atlas/cost/params.py`, `src/siting_atlas/optimize/params.py`,
`src/siting_atlas/warehouse/facilities.py`.
Bibliography: [`../REFERENCES.md`](../REFERENCES.md).
Model narrative: [`COST_MODEL.md`](COST_MODEL.md).
Joint uncertainty: [`UNCERTAINTY.md`](UNCERTAINTY.md).

Every sensitivity figure below was **measured on 2026-09-13**, not asserted.
The method is in §9.

**This document is one-at-a-time and that is a limitation, not a style.**
[`UNCERTAINTY.md`](UNCERTAINTY.md) moves all twenty-one sampled constants at
once across 500 draws and is the companion to this one. It confirms the §3
ordering (rank agreement Spearman 0.918) and it **overturns the top row of
§4's break-even column**. Where the two disagree, the disagreement is recorded
in both and neither is quietly deleted: §4 and §4.1 below carry the pointers.

---

## 1. The honest summary, before the detail

Twenty-six entries: the twenty-four fields of `CostParameters` (17) and
`PortfolioParameters` (7), plus the two `CATCHMENT_MILES` radii, which are not
dataclass fields but behave like parameters. Here is what happened when each
was chased to a source:

| Verdict | Count | Which |
|---|---|---|
| Published source found, our value agrees | 5 | `bhh_constant`, `parcels_per_household_per_week`, `parcels_per_depot_per_day`, `circuity`, `maintenance_usd_per_mile` |
| Published source found, **our value disagrees** | 4 | `shift_hours` and `delivery_days_per_week` (jointly the hours-per-year denominator), `wage_loading`, `discount_rate` |
| Published comparator exists but measures a different thing | 5 | `avg_speed_mph`, `van_mpg`, `capital_per_activation_usd`, `CATCHMENT_MILES["DS"]`, `cannibalisation_peak` |
| No published source found: engineering estimate | 9 | `stops_per_tour`, `service_minutes_per_stop`, `parcels_per_stop`, `van_lease_usd_per_day`, `income_elasticity`, `reference_income_usd`, `linehaul_sharing`, `cannibalisation_radius_km`, `delivery_days_per_year` |
| Convention or dead in practice | 3 | `horizon_years`, `default_linehaul_miles`, `CATCHMENT_MILES["SDC"]` |

**`CATCHMENT_MILES["DS"]`'s row is the one that has since moved, and it moved
the good way.** On 2026-09-14 MWPVL 2025 was found to state a radius for
exactly this facility class — *"designed to service a 45-mile radius"* — so
the comparator no longer measures a different thing, it measures this thing
and disagrees with us by 3x. The counts above are left as they were because
the value in the code has not changed; the disagreement and the sensitivity
band across it are in §5.1 and §6.21.

**`delivery_days_per_year` was added to this table on 2026-09-14 and it had
been missing since the document was written.** It has a row in the §4
sensitivity table and had no entry in the §6 register at all — the only
sampled constant in [`UNCERTAINTY.md`](UNCERTAINTY.md) whose range had to be
lifted from a table because there was no register entry to read it from. The
entry is now §6.22. Earlier drafts said "twenty-four constants" and the
arithmetic happened to come out right only because they also counted
`CATCHMENT_MILES` twice and merged `shift_hours` with
`delivery_days_per_week`.

**The disagreements are in §7 and they are not cosmetic.** Correcting the
two labour ones alone moves the headline from **$1.09 to $1.45 per parcel, a
+33.6% shift**, which is larger than the entire published sensitivity table in
`COST_MODEL.md` §5.6. They have NOT been changed in the code; they are flagged
for a decision.

**`cannibalisation_peak` was reclassified on 2026-09-13**, from "our value
disagrees with a published one" to "the published comparator measures a
different thing". Reading Holmes Table VIII and HNS Table VIII in full showed
that the earlier verdict compared a *ceiling* to an *average*, quoted 10% where
the table says 12.3%, and -- decisively -- that both papers measure diversion
of demand *between a firm's own outlets*, not loss of demand in an area, which
is what our term does. See §7.4. The two portfolio parameters with the largest
effect on the answer, `capital_per_activation_usd` and `cannibalisation_peak`,
turn out to be **one defect**, not two: see §7.5.

A second, structural caution before any of the numbers: this is a
**one-at-a-time** sensitivity analysis. Real parameter error is correlated —
if `service_minutes_per_stop` is wrong it is probably wrong because
`stops_per_tour` is also wrong, and the two move the answer the same way. The
ranges below are therefore a floor on the true uncertainty, not a confidence
interval.

That caution has since been measured rather than asserted.
[`UNCERTAINTY.md`](UNCERTAINTY.md) draws twenty-one of these constants jointly,
500 times, and finds that **a quarter of the variance in the activation count
is not attributable to any single parameter** — it is interaction and the
discrete behaviour of the greedy stopping rule, which is exactly the part a
one-at-a-time sweep cannot see. It also samples independently, which lets
errors cancel, so its bands are a floor as well.

---

## 2. How to read the sensitivity columns

Two different questions, and they have different answers:

- **Level sensitivity** — how much does the median `$/parcel` move? This is
  what matters if you are quoting the number, or comparing it to a contribution
  margin.
- **Rank sensitivity** — does the *ordering* of the 2,333 ZCTAs change?
  Reported as Spearman rho against the baseline ranking. This is what matters
  for siting, because the model's actual output is a ranking.

They dissociate sharply, and that dissociation is the single most useful
finding in this document. The parameters that move the level most
(`service_minutes_per_stop`, `parcels_per_stop`) barely move the ranking at
all (rho > 0.98) because they are close to uniform multipliers. The parameters
that move the ranking most (`parcels_per_depot_per_day`,
`parcels_per_household_per_week`, `income_elasticity`) barely move the level.

> **So: if you are defending the ranking, defend the demand and depot
> parameters. If you are defending the dollar figure, defend the labour
> parameters. They are different arguments and they need different evidence.**

---

## 3. Ranked sensitivity: the cost model

Baseline 2023Q4, from `outputs/metrics/cost_report.json`, run
**`20260916-024154-0aa8`**: median **$1.0830/parcel**, p10 $0.9778, p90
$1.4180, 2,333 ZCTAs, $14.00m/day, 78,292 vans. Quote the run_id, not the
number: the p-median rewrite of `cost/depots.py` (§9.1) moved all five of
these and the next change to the depot solver will move them again.

**The percentage columns below were measured against the superseded baseline**
(median $1.0875, p10 $0.9853, p90 $1.3637, $14.09m/day). They are ratios and
the median moved only 0.4%, so they remain usable; the p90 moved 4.0%, so the
dispersion figures in that older run should not be quoted. Sorted by the larger
of `|% lo|` and `|% hi|`.

`% lo` / `% hi` are at the plausible-range endpoints. `+/-50%` is the uniform
stress test, written `+50% / -50%`. `rho` is the worst Spearman rank
correlation against the baseline ordering across the range.

| Parameter (base -> range) | % lo | % hi | +/-50% | rho |
|---|---|---|---|---|
| `service_minutes_per_stop` 2.4 -> 1.5-4.0 | -25.01 | +44.29 | +33.3/-33.4 | 0.99 |
| `parcels_per_stop` 1.4 -> 1.0-2.0 | +39.26 | -29.47 | -32.8/+97.9 | 1.00 |
| `van_lease_usd_per_day` 41 -> 25-70 | -8.76 | +15.87 | +11.2/-11.2 | 1.00 |
| `delivery_days_per_week` 6 -> 5-7 | +13.53 | -9.63 | -22.9/+67.7 | 0.92 |
| `stops_per_tour` 120 -> 90-180 | +9.80 | -9.97 | -10.0/+29.6 | 1.00 |
| `shift_hours` 9 -> 8-10 | +9.26 | -7.43 | -24.8/+74.2 | 1.00 |
| `wage_loading` 1.32 -> 1.25-1.45 | -3.93 | +7.28 | +37.1/-37.1 | 1.00 |
| `avg_speed_mph` 22 -> 15-30 | +3.52 | -2.02 | -2.5/+7.5 | 1.00 |
| `parcels_per_depot_per_day` 40k -> 20k-60k | -2.54 | +1.70 | +1.7/-2.5 | **0.90** |
| `parcels_per_household_per_week` 3.2 -> 2.5-4.0 | +1.62 | -1.28 | -2.3/+4.5 | **0.91** |
| `circuity` 1.30 -> 1.15-1.45 | -1.22 | +1.23 | +5.5/-5.6 | 1.00 |
| `bhh_constant` 0.57 -> 0.45-0.71 | -0.72 | +0.90 | +1.9/-2.0 | 1.00 |
| `income_elasticity` 0.35 -> 0.0-0.7 | +0.43 | -0.84 | -0.3/+0.3 | **0.92** |
| `van_mpg` 14 -> 10-20 | +0.80 | -0.60 | -0.7/+2.1 | 1.00 |
| `maintenance_usd_per_mile` 0.19 -> 0.10-0.30 | -0.56 | +0.73 | +0.6/-0.6 | 1.00 |
| `reference_income_usd` 75k -> 60k-90k | -0.49 | +0.29 | +0.9/-1.4 | **0.92** |
| `default_linehaul_miles` 25 -> 15-40 | 0.00 | 0.00 | 0.0/0.0 | 1.00 |

### 3.1 What this table actually says

**Four parameters carry the headline.** Service time, parcels per stop, the
van lease and the labour-hours denominator (`shift_hours` x
`delivery_days_per_week`) between them account for essentially all the
level uncertainty. Three of those four have **no published source**.

**The routing mathematics is decoration.** `bhh_constant` is the parameter
this model is named after, it is the only one already carrying a citation, and
being wrong by 50% moves the answer **1.9%**. Same for `circuity` (5.5%) and
`van_mpg` (0.7%). The reason is in `COST_MODEL.md` §7.3: local travel is 3.3%
of the bill and fuel is another 3.3%. A reviewer who spends their question
budget attacking the Daganzo constant is attacking the strongest part of the
model, and they should be pointed at §7 instead.

**Joint sampling agrees with this ordering, which is the strongest thing that
can be said for it.** [`UNCERTAINTY.md`](UNCERTAINTY.md) §6.1 ranks the same
parameters by their effect on median `$/parcel` under 500 joint draws and gets
a rank agreement of **Spearman 0.918** against this table. The top two are the
same and in the same order; the largest movement anywhere is two places, and
none of the movements exceeds the noise floor. **§3 is durable and can be
quoted.** §4, below, is not.

**`default_linehaul_miles` is dead code on this pilot.** It moves the answer
by exactly 0.00% at any value, because every pilot ZCTA has a `cbsa_code` and
a placed depot, so the fallback never fires. It is not a parameter; it is a
guard. It matters the moment the model runs outside a CBSA.

**`parcels_per_stop` is the largest single lever and the most fragile.** At
1.0 the median rises 39%. It is a pure divisor on cost per parcel, so its
elasticity is exactly -1 and it never touches the ranking. It is also the one
with the least evidence behind it (§6.10).

---

## 4. Ranked sensitivity: the portfolio model

Baseline, $2bn budget, 2023Q4 baseline cost table. Take it from
`experiments/portfolio-optimiser/artefacts/portfolio_report.json`, run **`20260914-002431-7419`**:
**282 activations, $1.128bn committed, break-even margin $1.3431/parcel**,
optimality gap 10.7%, capacity 500.

The $2bn budget **never binds**. Capacity is 500 activations and the greedy
loop stops at 282 on negative marginal NPV, leaving $872m unspent. Any
sentence of the form "deploys $1.128bn of $2bn" is a statement that the budget
is slack, not that it was nearly exhausted.

> **THE TABLE BELOW IS MEASURED AGAINST A SUPERSEDED BASELINE — see §9.1.**
> It was swept on 2026-09-13 against **330 activations, $1.32bn,
> $1.3887/parcel, gap 13.4%**. The cause of the move is the concurrent rewrite
> of `cost/depots.py` from k-means to p-median, not anything in `optimize/`.
> The ratios, the orderings and the Jaccard patterns survive; **every absolute
> `n` in the table is on the old depot network** and should be read as a
> proportion of 330, not of 282. The one row that has been re-swept on the
> current network is `cannibalisation_peak`, in §7.4, and it lands close
> enough to confirm the pattern.

The break-even margin is a poor sensitivity target on its own, because a
parameter can leave it almost unchanged while completely rearranging *which*
ZCTAs get funded. So the selection overlap (Jaccard index against the baseline
selection) is reported alongside it, and it is the more alarming column.

`BE` is the break-even margin. `n` is the number of ZIPs funded. `Jaccard` is
the overlap of the selected set with the superseded baseline's 330, at the low
and high ends of the range.

| Parameter (base -> range) | BE % lo/hi | n lo/hi | Jaccard lo/hi |
|---|---|---|---|
| `capital_per_activation_usd` $4m -> $2-8m | -7.55 / +13.45 | 419 / 250 | 0.70 / 0.69 |
| `cannibalisation_peak` 0.18 -> 0.05-0.35 | -9.72 / +1.31 | 338 / 197 | 0.67 / **0.38** |
| `horizon_years` 7 -> 5-10 | +5.47 / -4.25 | 350 / 304 | 0.90 / 0.85 |
| `delivery_days_per_year` 312 -> 260-365 | +3.74 / -3.09 | 341 / 307 | 0.93 / 0.88 |
| `discount_rate` 0.10 -> 0.05-0.15 | -3.32 / +3.17 | 307 / 339 | 0.88 / 0.93 |
| `cannibalisation_radius_km` 20 -> 10-40 | -2.86 / +1.90 | 418 / 279 | **0.54** / 0.68 |
| `linehaul_sharing` 0.35 -> 0.0-0.7 | +0.12 / -0.65 | 308 / 337 | 0.89 / 0.93 |

#### 4.0.1 The `BE % lo/hi` column does not survive joint sampling. The `n` column does.

This table ranks `cannibalisation_peak` **first** on break-even margin, at
-9.72% / +1.31%. Under the 500 joint draws in
[`UNCERTAINTY.md`](UNCERTAINTY.md) §6.2 its Spearman rho against the break-even
margin is **+0.029 with p = 0.52** — not small, *absent*, and the sign is the
other way round. Recorded rather than resolved, because the two measurements
are both correct and they answer different questions:

```
  what sec.4 measures    the level shift at the ENDPOINTS of the range,
                         with everything else held at baseline. The -9.72%
                         is realised at peak = 0.05.
  what joint sampling    the density-weighted effect after the optimiser has
    measures             re-optimised, with the other twenty parameters
                         moving too. Triangular sampling with the mode at
                         0.18 visits peak = 0.05 rarely.
  why they differ        the two channels offset. Raising `peak` makes
                         marginal ZCTAs unprofitable, the selector funds
                         fewer of them, and the margin at the new stopping
                         point is roughly where it started. The deciles in
                         UNCERTAINTY.md sec.6.2 show `n` falling
                         monotonically from 293 to 177 while break-even
                         wanders inside a six-cent band and is not monotone.
```

The same non-monotonicity is already visible in §7.4's own re-sweep, where the
break-even margin peaks near 0.20 and *falls* again by 0.336. §4 did not draw
the conclusion from it.

**So: the right parameter is at the top of the wrong column.**
`cannibalisation_peak` controls the *size* of the portfolio, not its unit
economics, and on size it is decisively first — 44.3% of the variance in `n`
across the joint draws. The practical rule, from
[`UNCERTAINTY.md`](UNCERTAINTY.md) §6.3: **the `n lo/hi` column above is a
usable ranking of importance (rank agreement Spearman 0.714 with joint
sampling, top two unchanged); the `BE % lo/hi` column is not (Spearman
0.086 — no relationship).**

Two further things this table cannot show, both from the same source:

- **It never crosses.** §3 sweeps cost parameters against cost outcomes and §4
  sweeps portfolio parameters against portfolio outcomes. Neither asks what a
  cost parameter does to the activation count. Joint sampling does: cost
  parameters carry **18.8% of the variance in `n`**, and
  `delivery_days_per_week` — which does not appear in this table at all — is
  the second-strongest single driver of the activation count in the whole
  model (rho +0.280). It is also half of the denominator §7.1 says is wrong.
- **`delivery_days_per_year` is the weakest driver here and it is also the one
  constant in the table that had no register entry** until §6.22 was written.
  Its joint rho against `n` is -0.052 (p = 0.24) and against break-even
  -0.126, so nothing rests on it — but see §6.22 for why sampling it at all is
  questionable.

### 4.1 What this table actually says

**The portfolio is far less robust than the cost ranking.** No cost parameter
reordered the ZCTAs (worst rho 0.90). Two portfolio parameters change *the
majority of the answer*: at `cannibalisation_peak = 0.35` only **38%** of the
selected ZIPs are the same ones, and at `cannibalisation_radius_km = 10` only
**54%** are. A reader who treats the funded ZIP list — 330 then, 282 now — as
a recommendation is treating an unsourced parameter as a fact.

**And `cannibalisation_peak` is the worst-evidenced parameter in the whole
project** (§7.4). Its own docstring calls it a PLACEHOLDER.

**`linehaul_sharing` is decoration.** Zeroing it entirely moves the break-even
margin 0.12%. This is expected and it is a *good* sign: `objective.py`
deliberately restricts the shareable pool to the mileage-driven share of cost,
and mileage is ~11% of the bill. The parameter was worth building correctly;
it is not worth defending.

**The optimality gap is not fixed slack, and earlier drafts of this paragraph
said it was.** They read: "the optimality gap (13.4%) is larger than every
parameter effect in the table", and treated 13.4% as a property of the
heuristic that sat above the parameter uncertainty. It is not a constant. On
today's baseline it is 10.7%, and across the 500 joint draws in
[`UNCERTAINTY.md`](UNCERTAINTY.md) §4 it **ranges from 1.1% to 26.4%, with a
standard deviation of 3.9 percentage points, and is itself parameter-driven**
— Spearman +0.51 against `cannibalisation_peak`, and only 62.0% of its
variance is linear in the twenty-one sampled constants at all.

The restated version, which is weaker and correct:

> The gap is of the same order as the largest parameter effects and is
> partly caused by them. Improving the solver is still worth attention — a
> ten-point gap is a lot of unrealised NPV — but "the heuristic's slack
> dominates the parameters" is not a statement the evidence supports, because
> the slack is a function of the parameters. The two cannot be ranked against
> each other as though they were independent sources of error.

What does survive is the practical advice the old sentence was carrying:
nobody should commission a better estimate of `linehaul_sharing` (§6.20).
Joint sampling puts it, `bhh_constant`, `circuity`, `van_mpg` and
`maintenance_usd_per_mile` at or below the noise floor in every outcome.

---

## 5. The catchment radius: a parameter that sets the sample size

`CATCHMENT_MILES` does not touch the cost model at all. It sets the `enabled`
target, and therefore how many events the hazard model has to learn from. With
the delivered panel (43 facilities, all type `DS`):

| Radius (mi) | Enabled panel cells | Distinct ZCTAs ever enabled | % of panel |
|---|---|---|---|
| 5 | 7,060 | 383 | 0.65 |
| 10 | 17,903 | 882 | 1.66 |
| **15 (baseline)** | **27,914** | **1,257** | **2.58** |
| 20 | 36,853 | 1,593 | 3.41 |
| 25 | 43,942 | 1,819 | 4.06 |
| 30 | 50,084 | 2,006 | 4.63 |

Dropping to 10 miles removes **30%** of the treated ZCTAs; going to 20 miles
adds **27%**. Against a panel that `COST_MODEL.md` §6.2 says carries only 39
usable events, this is the parameter that most directly controls whether the
causal stage has any power at all. It deserves a sensitivity band in the
hazard results, not a fixed value.

`CATCHMENT_MILES["SDC"] = 10.0` is **currently unreachable**: the delivered
`facilities.csv` contains 43 rows and all 43 are `DS`. It is not wrong, it is
untested.

### 5.1 The band, run 2026-09-14

That sensitivity band now exists:
`src/siting_atlas/warehouse/catchment_band.py` ->
`outputs/metrics/catchment_band.json`, written up in
[`../research/NOTES_CATCHMENT_RADIUS.md`](../research/NOTES_CATCHMENT_RADIUS.md).
The six rows above were re-measured by it and **all six agree exactly**, which
is what licenses the rest of the sweep.

**Range: 8.3 to 45.0 miles.** Both endpoints are external, from MWPVL 2025.
The high end is the document's own prose (line 383, `MWPVL_2025.md` §3.2):
delivery stations are *"designed to service a 45-mile radius"*. The low end is
its most frequent same-day statement, *"Same Day Service Within 45 Minute
Drive Time"* (37 rows), converted at this project's own congested speed and
circuity — 16 mph, 1.45 (`cost/params.py:295`) — giving 8.28 straight-line
miles. Seven OCR'd rows state 50 to 90 miles, but six of the seven are rural
"Wagon Wheel" or small-metro buildings, so they are swept as a 60-mile
over-run probe OUTSIDE the band rather than setting it.

| quantity | 8.3 mi | **15 mi** | 45 mi | high/low |
|---|---|---|---|---|
| ZCTAs ever enabled | 721 | **1,257** | 2,572 | 3.57x |
| enabled panel cells | 14,121 | **27,914** | 67,216 | 4.76x |
| facilities attached | 43 | **43** | 43 | 1.00x |
| ZCTAs served by 2+ stations | 57.3% | **72.0%** | 80.2% | 1.40x |
| out-of-sample AUC | 0.6269 | **0.6894** | 0.7081 | 1.13x |
| Brier skill vs a constant | 0.0032 | **0.0047** | 0.0095 | 2.98x |

**This is a sensitivity range over an assumption, not a confidence interval** —
the same disclaimer `optimize/montecarlo` attaches to its own output.

**The conclusion is robust to it.** Across the whole band the AUC never
reaches the pre-registered 0.80; the model beats a constant on Brier by 0.3
to 0.9%; the constant stays better calibrated; and `households` stays the one
covariate distinguishable from zero at 8.3-19.6 miles. The only claim that
moves is the *count* of significant covariates (3 of 3 at 25 and 45 miles),
and §6.21 explains why that is sample inflation rather than signal.

Two things the band found that were not predicted: **facilities attached is
flat at 43 at every radius** (a facility attaches at least its own ZCTA, so
the radius buys ZCTAs per facility — 33 at 8.3 mi, 88 at 15, 293 at 45 — and
buys no buildings), and **the risk set shrinks** as the radius grows, from
1,977 units at 8.3 miles to 1,076 at 45, because a wider catchment
left-truncates more ZCTAs than it newly treats.

---

## 6. The parameter register

Each entry: what it is, where the number came from, what the plausible range
is and why, and which way an error biases the answer.

Citation confidence is marked throughout:
**[V]** verified against the source text or a source document read in full;
**[T]** title and venue verified via search, content not read;
**[K]** asserted from the author's own knowledge, page not opened from this
host (WebFetch is proxy-blocked here) - **treat as unverified**;
**[E]** engineering estimate, no source found.

### 6.1 `bhh_constant` = 0.57 -- **sourced, agrees**

Dimensionless constant `k` in tour length `~ k * sqrt(n*A)`.

**Source [V/T].** Daganzo (1984b), *Approximate Formulas for Average Distances
Associated with Zones*, Transportation Science 18(3), 231-253, and Daganzo
(1984a), *The Distance Traveled to Visit N Points with a Maximum of C Stops
per Vehicle*, Transportation Science 18(4), 331-350. Both titles and venues
confirmed against INFORMS DOIs (`10.1287/trsc.18.3.231`,
`10.1287/trsc.18.4.331`). The underlying theorem is Beardwood, Halton and
Hammersley (1959). Larson and Odoni, *Urban Operations Research* (1981) §6.4.8
gives the same approximation in textbook form and is freely readable at
`web.mit.edu/urban_or_book/www/book/chapter6/6.4.8.html`.

**Range 0.45 - 0.71.** The upper end is the asymptotic uniform-random-TSP
constant; the lower end is aggressive strip routing. **[K]** The commonly
quoted asymptotic value is approximately 0.7124, but I could not open a source
to confirm that digit string and it should not be quoted without checking.

**Sensitivity: +/-1% over the whole range. Decoration.**

**Bias.** 0.57 is the optimistic end, so it biases cost DOWN. Immaterially.

### 6.2 `circuity` = 1.30 -- **sourced, agrees on an analytical argument**

Street distance divided by straight-line distance.

**Source.** Two independent anchors, one analytical and one empirical.

*Analytical, and this is the strong one.* On a perfect rectangular grid the
travelled distance is the L1 (Manhattan) metric while the straight line is L2.
Averaging over a uniformly distributed direction gives a ratio of exactly
**4/pi = 1.2732**. That is a derivation, not a citation, and it is checkable in
one line. Our 1.30 is that value plus 2% for non-grid detours.

*Empirical [T].* Boeing, *The Relative Circuity of Walkable and Drivable Urban
Street Networks* (arXiv:1708.00836), and Liu, Xie, Lin and Jin, *Empirical
Estimation of Shortest Route Length along U.S. Interstate Highways Based on
Great Circle Distance* (OSTI 1813132). **[K] Caution: Boeing's measure is
edge-level network circuity, which is much closer to 1.0 than an
origin-destination ratio, and citing it as support for 1.30 would be citing a
different quantity.** It is listed so a reviewer can see it was considered and
rejected, not as evidence for our value.

*Contrast.* Neither Holmes (2011) nor Houde, Newberry and Seim (2023) applies
any circuity factor at all; both use raw great-circle distance. Holmes
addresses it in a footnote and dismisses it as small relative to his
magnitudes. **Our model is more conservative than both published papers here.**

**Range 1.15 - 1.45. Sensitivity: +/-1.2% over the range; +/-5.5% at +/-50%.**
Setting it to the exact 4/pi value moves the median -0.24%, so the 2%
engineering padding is immaterial.

**Bias.** Higher circuity raises cost. 1.30 above 4/pi biases cost slightly UP,
i.e. conservatively.

### 6.3 `stops_per_tour` = 120 -- **ENGINEERING ESTIMATE [E]**

Deliveries per van per shift.

**No published source found.** The docstring claims "industry last-mile figures
run 100-150". That claim could not be substantiated with a citable source in
this session. Searching returns Amazon DSP job advertisements and trade
commentary, which are advertisements, not measurements.

*What can honestly be said.* The value is internally consistent with the rest
of the model rather than independently sourced: at 9 hours and 2.4 minutes of
service time per stop, 120 stops consumes 4.8 hours of the shift at the door
and leaves 4.2 hours for driving and breaks. That is a plausible allocation,
but it is a consistency check between two unsourced numbers, not evidence.

**Range 90 - 180. Sensitivity: -10% to +10% over the range.**

**Bias.** More stops spreads the van lease and the line haul thinner, so a
higher true value means our cost is biased UP. 120 is therefore the
conservative direction.

### 6.4 `van_mpg` = 14.0 -- **comparator exists, measures something else**

**No directly applicable source found [E].** Manufacturer and EPA figures for
Class 2b vans are unloaded highway-cycle numbers and do not describe a loaded
stop-start delivery duty cycle. NREL, *Development of 80- and 100-Mile Work Day
Cycles Representative of Commercial Pickup and Delivery Operation*
(NREL/TP-5400-70943) **[T]** is the right *kind* of source -- a measured duty
cycle -- but its fuel-economy results were not read.

Neither Holmes nor Houde et al. uses fuel economy at all; both reduce transport
to a single dollars-per-distance parameter.

**Range 10 - 20. Sensitivity: +0.8% / -0.6%. Decoration.**

### 6.5 `maintenance_usd_per_mile` = 0.19 -- **sourced, agrees, wrong vehicle**

**Source [T/K].** ATRI, *An Analysis of the Operational Costs of Trucking*
(annual; 2023 update at `connect.ncdot.gov/.../ATRI-Operational-Cost-of-
Trucking-06-2023.pdf`, 2025 update at `truckingresearch.org/wp-content/
uploads/2025/07/ATRI-Operational-Costs-of-Trucking-07-2025.pdf`). ATRI reports
a repair-and-maintenance line in the high-teens cents per mile for recent data
years. **[K] I believe the 2023 update (2022 data year) reports approximately
$0.196/mile, but I could not open the PDF from this host and that figure must
be checked before it is quoted.**

**The real problem is not the number, it is the vehicle.** ATRI measures Class
8 combination tractor-trailers. A delivery van is a fraction of the mass with a
fraction of the tyre and brake bill, so borrowing a tractor-trailer maintenance
rate for a Sprinter is almost certainly **too high** -- but it is high in the
conservative direction and it moves the answer by 0.7%, so it is not worth
fixing.

**Range 0.10 - 0.30. Sensitivity: +/-0.7%. Decoration.**

### 6.6 `van_lease_usd_per_day` = 41.0 -- **ENGINEERING ESTIMATE [E]**

**No published source found.** Commercial fleet lease rates are negotiated and
not published; search returns consumer lease advertisements, which are the
wrong market.

*What can honestly be said.* $41/day over 312 delivery days is $12,792/year,
which is in the range a $50-60k van amortised over four to five years with
insurance and registration would imply. That is a reconstruction, not a source.

**This is the third-largest lever in the model (+15.9% at $70/day) and it has
no evidence behind it at all.** It is also the component that behaves most
unlike the others: because it is charged as `lease / stops_per_tour`, it is a
flat $0.34 per stop in every ZCTA in the country, which makes it 22.8% of the
pilot's bill and 24.5% of Greenpoint's.

**Range 25 - 70. Sensitivity: -8.8% to +15.9%.**

**Bias.** Unknown. This is the largest unhedged exposure in the cost model.

### 6.7 `avg_speed_mph` = 22.0 -- **comparator exists, measures something else**

Door-to-door average including time in traffic, not posted limits.

**No directly applicable source found [E].** The nearest published quantities
are ATRI's bottleneck monitoring (rush-hour truck speeds around 36 mph on
major corridors **[T]**) and NREL's commercial pickup-and-delivery duty cycles
**[T]**. Neither measures the door-to-door average of a residential parcel
round, which is the quantity in the model and is necessarily much lower.

**Range 15 - 30. Sensitivity: +3.5% / -2.0%.** Note this is far smaller than
the +14.5% the old single-centroid model showed, because realistic line hauls
left much less driving for a low speed to punish (`COST_MODEL.md` §5.6).

### 6.8 `service_minutes_per_stop` = 2.4 -- **ENGINEERING ESTIMATE [E], and it
is the number that matters most**

Park, walk, hand off, scan.

**No published source found, and this is the most serious gap in the
project.** It is the largest driver of the headline (-25% to +44% across a
plausible range; 66.5% of the pilot's cost per stop) and it rests on nothing.

*Leads that exist but were not read.* There is a real literature on delivery
dwell time and it should be mined before submission:
- **[T]** *Vehicle stop time estimation during last mile deliveries: a
  statistical analysis to increase the accuracy of ...*, TU Delft repository
  and CORE record 130234459. This is directly on the quantity.
- **[T]** Urban Freight Lab, University of Washington, *Do Parcel Lockers
  Reduce Delivery Times? Evidence from the Field* (also OSTI 2418036). Reports
  field-measured delivery times.
- **[T]** USPS Office of Inspector General, *City Delivery Efficiency Review --
  New York District* (DR-AR-11-002). Postal carrier time standards are the
  closest thing to an audited public figure for time at the door.
- **[T]** METRANS/Rodrigue, *Residential Parcel Deliveries: Evidence from a
  Large Apartment Complex* (MF 5.1d).

**Do not let anyone cite these as supporting 2.4 minutes.** They are places to
look, and until one of them is read, 2.4 is a guess with a large coefficient in
front of it.

**Range 1.5 - 4.0. Sensitivity: -25.0% / +44.3%. Rank effect: negligible
(rho 0.99), because it is near-uniform across ZCTAs.**

**Bias.** Unknown, and the asymmetry matters: the upside (4 minutes, +44%) is
larger than the downside (1.5 minutes, -25%). If the distribution of plausible
values is symmetric, the expected error in the headline is upward -- i.e.
**$1.09 is more likely too low than too high.**

### 6.9 `shift_hours` = 9.0 and `delivery_days_per_week` = 6.0 -- **SOURCED, AND
OUR COMBINATION IS WRONG. See §7.1.**

### 6.10 `parcels_per_stop` = 1.4 -- **ENGINEERING ESTIMATE [E]**

Parcels handed over in a single visit.

**No published source found.** The *concept* is right and important -- charging
service time per parcel rather than per door would systematically penalise
dense ZCTAs, which is a real error and not a rounding one -- but the magnitude
1.4 is unevidenced.

*Leads [T].* METRANS/Rodrigue MF 5.1d (above) counts actual parcel arrivals at
a single large residential building and is the closest public measurement.
Pitney Bowes' *Parcel Shipping Index* gives national parcel volume but not
consolidation.

**This is the single largest lever in the model**: at 1.0 the median rises
39.3%, at 2.0 it falls 29.5%. Its elasticity on cost per parcel is exactly -1
by construction, and it is invisible to the ranking (rho 1.00).

**Bias.** Consolidation has risen with e-commerce order batching, so if 1.4 is
stale it is stale LOW, which biases cost UP.

### 6.11 `parcels_per_household_per_week` = 3.2 -- **sourced, agrees**

**Source.** Derived from published national volume: roughly 22 billion US
parcels in 2023 over roughly 131 million households gives 3.23/household/week.
The volume side is Pitney Bowes' *Parcel Shipping Index* **[T]** and the
household count is the Census Bureau **[T]**. **[K] Neither the 22bn nor the
131m was re-verified from the source in this session; both are widely
reported and both should be pinned to a specific release before submission.**

*Independent cross-check from the literature [V].* Houde, Newberry and Seim
(2023) report scaled comScore average household spending on Amazon of about
$1,040 in 2016 across 32 orders, i.e. **0.62 Amazon orders per household per
week** at a time when Amazon held roughly 31% of US online retail. Grossing up
gives roughly 2 online orders per household per week in 2016, against our 3.2
for 2023 across *all* carriers including non-e-commerce parcels. **The two are
consistent in magnitude and in the right direction over time.** This is the
best external validation any demand parameter in the model has.

**Range 2.5 - 4.0. Sensitivity: +1.6% / -1.3% on the level -- but rho falls to
0.91, making it one of the three parameters that actually move the ranking.**
The level barely moves because volume enters cost only through
`1/sqrt(density)`, and local travel is 3.3% of the bill.

### 6.12 `income_elasticity` = 0.35 -- **ENGINEERING ESTIMATE [E], and the
literature does not support the functional form**

Parcel volume elasticity with respect to household income.

**No source found for 0.35, and the closest published evidence points the
other way.** Houde, Newberry and Seim (2023) Table III regress log relative
spending on log income and find a coefficient of **0.226 with a standard error
of 0.22 -- statistically indistinguishable from zero** -- and they state
plainly: "Log-income does not have any significant linear impacts on spending,
but high-income households have lower preferences for online shopping." Their
Figure 2 note gives 2016 Amazon spending of $1,219 for high-income households
against $989 for low-income, a ratio of 1.23 across a wide income gap. **[V]**

Note their coefficient is on a spending *ratio* relative to offline, not a
level elasticity, so it is not the same object as ours. But it is the nearest
published estimate and it is (a) smaller than 0.35 and (b) insignificant.

**Range 0.0 - 0.7. Sensitivity on the level: +0.4% / -0.8%. Negligible.
Rank effect: rho 0.92, one of the largest in the model.**

**Recommendation.** The value is defensible as a conservative choice *because*
it is nearly inert on the headline, and the docstring's reasoning (a higher
value would concentrate demand in wealthy ZCTAs and flatter the ranking's top
end) is sound. But the docstring should stop implying it is known, and should
cite HNS as the reason for keeping it low.

### 6.13 `reference_income_usd` = 75,000 -- **convention, not a parameter**

The income at which the per-household parcel rate applies unscaled. It is a
pivot: moving it rescales every ZCTA by a common factor.
**Sensitivity: +/-0.5%.** Rho 0.92, because it interacts with the elasticity.
Roughly the 2023 US median household income, which is the sensible pivot.

### 6.14 `default_linehaul_miles` = 25.0 -- **dead on this pilot**

**Sensitivity: exactly 0.00% at every value tested.** Never fires, because
every pilot ZCTA has a CBSA and a placed depot. Keep it; document it as a
guard rather than an assumption.

### 6.15 `parcels_per_depot_per_day` = 40,000 -- **sourced by network-size
validation, which is the right kind of evidence**

Throughput of one delivery station; sets `K = ceil(metro parcels / 40,000)`.

**This is the best-evidenced parameter in the model, and not because a paper
states it.** It is evidenced by the consequence test in `COST_MODEL.md` §6.1:
40,000 implies 334 depots across 11 CBSAs holding 17.6% of US population;
Amazon alone runs roughly 700-900 US delivery stations, so all operators
together should land near 250-320 in this footprint. The implied network is the
right size, which it had no way of being if the throughput were badly wrong.

**[K] The 700-900 delivery-station count is the widely quoted MWPVL
International figure and was not re-verified here.** MWPVL is a legitimate
source and is the facility-network source used by Houde, Newberry and Seim
(2023) for exactly this purpose, which is a point in its favour. **[T]**

**Range 20,000 - 60,000. Sensitivity on the level: -2.5% / +1.7%. But it is
the single largest RANK mover in the model (rho 0.90),** because it decides how
many depots a metro gets and therefore which ZCTAs are near one. Level-robust,
rank-fragile: exactly the dissociation in §2.

**Bias.** Raising it builds fewer, more distant depots and pushes cost UP.

### 6.16 `capital_per_activation_usd` = $4,000,000 -- **the unit is the problem,
not the number**

**No source found for $4m [E]**; the docstring says only "midpoint of the $3-5M
range used throughout the proposal", which is a cross-reference to another
unsourced claim in the same project.

**The more serious issue is what "an activation" is.** `select.py:46-47` sets
`capacity = floor(budget / capital_per_activation_usd)` and
`objective.py:164` computes `capital = float(sel.sum()) *
p.capital_per_activation_usd`. The unit charged is a **ZCTA**, not a facility,
and there is **no de-duplication of any kind** across ZCTAs that would share a
station. Confirmed by reading both files in full on 2026-09-13.

#### 6.16.1 How many stations would actually be needed — measured, not asserted

This was computed rather than guessed, because the obvious guess is wrong. The
tempting arithmetic is "median 58 ZIPs per station (§5), so 330 ZIPs is about
six stations, so the true capital is tens of millions". **That is wrong by
roughly a factor of twenty**, for two reasons.

First, 58 is the median count of ZCTAs within 15 miles of a facility counted
over *all* ZCTAs. The funded set is a scattered subset of the cheapest ZCTAs
across 11 metros, not a contiguous blob, so covering it takes far more disks
than 330/58 suggests. Second, and dominant: **a delivery station has a
throughput.** `parcels_per_depot_per_day = 40,000` (§6.15) is the project's own
constraint, `depots.py` already applies it, and the funded ZCTAs are the
*densest* ones, so they carry a disproportionate share of the volume. Geometry
does not bind; capacity does.

Both were computed per metro and the larger taken, which is the defensible
figure:

```
  stations needed to serve the funded ZCTAs         count   at $4m/station
  ------------------------------------------------  -----   --------------
  geometry only, greedy 15-mile disk cover             64        $  256 m
  throughput only, ceil(metro parcels / 40,000)        98        $  392 m
  per-metro max(geometry, throughput)                 103        $  412 m
  ------------------------------------------------  -----   --------------
  CHARGED BY THE MODEL (n x $4m)                      282        $1,128 m

  overcharge factor                                            2.74x
```

Per-metro detail, measured against the pre-p-median depot code (330 funded
ZCTAs at the time), showing that New York alone accounts for most of the
capacity requirement:

```
  cbsa     ZCTAs   parcels/day   geometry   throughput   max
  -----    -----   -----------   --------   ----------   ---
  35620      137     1,855,636        14         47       47
  33100       69       670,220         5         17       17
  16980       42       569,227         8         15       15
  38060       17       207,042         9          6        9
  12420       13       197,095         5          5        5
  34980       14       193,469         5          5        5
  41860       13       183,568         5          5        5
  42660       10       127,293         5          4        5
  19740        9       112,204         2          3        3
  41940        4        63,940         2          2        2
  14260        2        23,499         1          1        1
  -----    -----   -----------   --------   ----------   ---
  TOTAL      330     4,203,193        61        110      114
```

**So the correction is about 2.7x-2.9x, not 20x or 30x.** The capital line does
double-count buildings, but far less than the catchment geometry alone implies,
because throughput forces a dense network regardless.

#### 6.16.2 Does the finding invert? No — and it did not need to

The worry worth stating plainly is that "a $2bn budget deploys $1.32bn" might
become "the budget is nowhere near binding". **The budget already does not
bind, and the published sentence already says so.** Measured:

```
  capacity = floor($2bn / $4m)                              500
  activations actually selected                             282
  log line from select.py:90                "stopped at 282 of 500 fundable
                                             activations: the next one would
                                             reduce NPV by $19,537"
```

The greedy loop stops on **negative marginal NPV**, not on the budget cap —
exactly as `select.py`'s docstring says it is designed to. "Deploys $1.32bn of
$2bn" is a statement that $680m was left unspent because no further ZIP paid
for itself. Correcting the capital unit changes the *size* of the capital line;
it does not convert a binding constraint into a slack one, because the
constraint was never binding.

What it *would* change, if the unit were made per-station and the budget
constraint re-expressed in those terms, is that the constraint becomes
**vacuous rather than merely slack**: the entire 11-metro pilot of 2,333 ZCTAs
needs 334 depots, which at $4m each is **$1.336bn**, so a $2bn budget builds
the whole network with $664m spare. A budget constraint that cannot bind on any
feasible portfolio is not doing any work and should not be presented as though
it were.

#### 6.16.3 What the literature actually does — the previous wording was misleading

The claim in earlier versions of this document, that Holmes and HNS "refuse to
put a dollar figure on opening a facility... precisely because it does not vary
by location", is right on the mechanism and wrong on the implication. Both
papers were re-read for this specific question on 2026-09-13; see
[`../research/NOTES_holmes_2011_capital_and_cannibalisation.md`](../research/NOTES_holmes_2011_capital_and_cannibalisation.md)
§3 and
[`../research/NOTES_hns_2023_capital_and_cannibalisation.md`](../research/NOTES_hns_2023_capital_and_cannibalisation.md)
§3 for the full quotes. **[V]**

Holmes normalises `omega_0 = 0` (§2, p. 260) explicitly for "the analysis of
*where* Wal-Mart places a given number of stores" — he conditions on the
number. On sunk cost he says the opposite of "there is none" (§2, p. 262):
"Implicitly, sunk costs are large... Sunk costs can easily be worked into the
model... This leaves the objective in equation (2) unchanged."

HNS are even more explicit that this is a property of their estimator (§3.6,
p. 166): they disregard sunk costs "*rather than* the optimality of the number
of facilities, ... *provided these are the same across facilities*". And
(§4.3, p. 178) their estimator "is only able to capture costs that vary across
the locations in the network. We are therefore not able to, for example,
identify a constant base cost".

**Both papers are silent on the value of a capital term, not hostile to its
existence, and both are silent for a reason that does not apply to us.** Our
model chooses *how many* units to fund — the exact margin both papers say they
are not working on. So we should keep a capital term.

Holmes's $18m/year figure stands as described: a *distribution centre*
*operating* cost, footnote 20 on p. 287, from 1m sq ft at $6/sq ft plus a third
of a $36m payroll, with no source for any of the four inputs. **[V]**

A magnitude check from HNS Table VII (p. 178) **[V]**: Amazon's entire facility
fixed cost in 2018 was **$0.30 per order** (rent $0.08 + density $0.22) against
a total fulfilment cost of $1.11. Amortised over the 7-year horizon at 10%
(annuity factor 4.8684, 312 delivery days), our capital line is **$0.2005 per
parcel** as charged and **$0.0732 per parcel** at one station per 2.7 ZCTAs.
Different objects — theirs a recurring rent, ours an amortised stock — so this
is a sanity check, not a validation. But the per-ZCTA charge alone coming to
two thirds of Amazon's whole fixed operating cost per order, on a comparable
cost base, is not reassuring.

**Range $2m - $8m. Sensitivity: -7.6% / +13.5% on the break-even margin, and
it changes the number of funded ZIPs from 419 to 250.** Jaccard overlap with
the baseline selection is only ~0.70 at either end.

**Recommendation, unchanged in direction and now quantified.** Redefine the
unit: charge capital per *depot*, using the network `depots.py` already solves,
or relabel the output as a "capital envelope per activated ZIP" and stop
describing it as construction cost. On today's portfolio that moves the capital
line from **$1,128m to $412m**. This is a definitional fix, not a calibration
one, and the value $4m can stay exactly where it is once the unit is right.

A second-order consequence worth flagging before anyone implements it: charging
per depot rather than per ZCTA removes the per-ZCTA entry fee, so marginal
ZCTAs that currently fail the stopping rule would start passing it and **the
portfolio would grow**. A crude fixed-point approximation (charging the
amortised $4m x stations/n per ZCTA and iterating) pushed the selection from
330 to roughly 440-520 ZIPs and the break-even margin from $1.3887 to about
$1.24. Treat those as order-of-magnitude only; the proper fix is a
station-level decision variable, not a rescaled per-ZCTA charge.

### 6.17 `horizon_years` = 7 and `discount_rate` = 0.10 -- see §7.3

### 6.18 `cannibalisation_radius_km` = 20 -- **ENGINEERING ESTIMATE [E]**

**No source found.** The docstring's justification is internal consistency with
the donor-pool gate, which is a good reason for the two to *agree* and no
reason at all for the value to be 20.

*Published comparators, all different objects [V].* Holmes (2011) restricts a
consumer's Wal-Mart choice set to **25 miles** (40 km) and reports a distance
decay in his Table VI under which the shop probability at 10 miles is a small
fraction of the probability at 0. Houde, Newberry and Seim (2023) cluster
Amazon facilities within **20 miles** and use a **150-mile** sortation
catchment from MWPVL. **20 km = 12.4 miles sits below all of these**, but they
are retail choice sets and facility clusters, not parcel-demand cannibalisation
radii, so none of them settles our value.

**Range 10 - 40 km. Break-even effect small (-2.9% / +1.9%) but the
SELECTION effect is the largest in the project: at 10 km only 54% of the
funded ZIPs are the same ones, and n moves 418 to 279.**

### 6.19 `cannibalisation_peak` = 0.18 -- **THE COMPARATOR MEASURES A DIFFERENT
QUANTITY, AND THE ROW WE WERE QUOTING WAS THE WRONG ONE. See §7.4.**

Revised 2026-09-13 after reading both Econometrica papers for this specific
question. Short version: Holmes's figure is 12.3% not 10%; it is an average
over his whole diffusion history whereas ours is a *ceiling*, and his saturated
states show 33.6%; and both papers measure diversion *between a firm's own
outlets* rather than loss of demand in an area, which is what we apply it to.
HNS Table VIII measures our quantity directly and gets exactly zero. Our value
is not obviously too high; it may be measuring something the model does not
contain.

### 6.20 `linehaul_sharing` = 0.35 -- **ENGINEERING ESTIMATE [E]**

Maximum share of line-haul cost avoided by sharing trips with neighbours.

**No source found.** Zeroing it moves the break-even margin 0.12%, so it is
decoration and does not need one. Say so rather than dressing it up.

### 6.21 `CATCHMENT_MILES` = {DS: 15, SDC: 10} -- **now externally anchored,
and banded**

**Value.** `DS: 15.0`, `SDC: 10.0`, `warehouse/facilities.py`.

**Source [V], added 2026-09-14.** MWPVL 2025, line 383: delivery stations are
*"designed to service a **45-mile radius**"* ([`MWPVL_2025.md`](MWPVL_2025.md)
§3.2). Seven OCR'd table rows state building-level radii of 50, 50, 50, 60,
60, 90 and (at Tesseract confidence 5) 60-70; six of the seven are rural
"Wagon Wheel" or small-metro stations. 37 rows state *"Same Day Service
Within 45 Minute Drive Time"*, 36 of them on SubSameDay fulfillment centres.
So the source supports a FAMILY of radii, all of them larger than 15.

**Provenance of 15 and 10 themselves: still [E].** The docstring's "20-30
minutes' drive" is an unsourced trade claim, and it does not reproduce 15:
at this file's own `avg_speed_mph = 22.0` and `circuity = 1.30`, a 30-minute
drive is 8.46 straight-line miles, and 15 miles needs a 39 mph average. 15 is
a good match for the 45-minute claim (12.7 mi at baseline speed) and a poor
match for the sentence defending it.

**Range: 8.3 to 45.0 miles**, both endpoints external -- see §5.1 for the
derivation and the full sweep. A 60-mile over-run probe is reported outside
the band.

**Measured leverage across that range** (`outputs/metrics/catchment_band.json`):
treated ZCTAs 721 -> 2,572 (**3.57x**), enabled panel cells 14,121 -> 67,216
(**4.76x**), facilities attached 43 -> 43 (**flat**), out-of-sample AUC
0.6269 -> 0.7081 (**1.13x**, baseline 0.6894). The chain was followed:
`CATCHMENT_MILES` is read in one file, `enabled` reaches only `models/` and
`agent/`, and the cost, choice and portfolio stages never see it. **This
parameter cannot move the capital or activation headlines at all.**

*Comparators [V/T].* Houde, Newberry and Seim (2023) take Amazon facility
catchments from **MWPVL International** and report a **150-mile** sortation
catchment and a 25-mile FC-to-SC proximity rule. Those describe sortation,
not last-mile delivery. Holmes (2011) uses a 25-mile consumer choice radius
for retail. Both are swept as the 25-mile point.

**Bias, predicted and now measured.** A radius that is too large labels
untreated ZIPs as treated and attenuates every hazard coefficient toward
zero. Measured: the `households` coefficient falls from 6.0e-05 at 8.3 miles
to 4.5e-05 at 45 (**-25%**) and 3.2e-05 at the 60-mile probe (-47%), while
its p-value falls too because the row count rises and 80% of enabled ZCTAs at
45 miles sit in two or more catchments. More stars from more correlated
copies of the same 43 decisions is not more evidence.

### 6.22 `delivery_days_per_year` = 312 -- **NO SOURCE, AND IT IS NOT INDEPENDENT
OF §7.1**

Added 2026-09-14. This constant has had a row in §4 since that table was
written and had **no entry in this register at all**. It is the only sampled
constant in [`UNCERTAINTY.md`](UNCERTAINTY.md) whose range had to be lifted
from a sensitivity table because there was nothing here to read it from. The
omission is recorded rather than quietly repaired: a register that can lose a
parameter can lose another one.

Days a year the network delivers. Used in `optimize/objective.py` to annualise
`daily_parcels` and `daily_cost_usd`, both of which are per *delivery* day.

**No published source, and none is really possible [E]**, because the quantity
is not measured anywhere — it is a modelling convention about how many days a
year a parcel network runs. The value is not typed. `optimize/params.py:213`
sets it as

```python
    delivery_days_per_year: float = COST_BASELINE.delivery_days_per_week * 52.0
```

so it is `6 x 52 = 312` and it is **derived from `delivery_days_per_week`**,
which is half of the labour-hours denominator §7.1 says is wrong. It therefore
has no evidential standing of its own: whatever is decided about §7.1 decides
this too. Deriving rather than typing it is the right call and the docstring
explains why — the two must agree, and annualising at 365 would invent 53 days
of volume that never happen, shrinking capital's share and reporting a
break-even margin about 3.5% too low.

**Range 260 - 365, taken from §4.** 260 is five days a week, 365 is every day.
Neither endpoint is sourced; they are the arithmetic bounds of a weekly
schedule.

**Sensitivity.** One-at-a-time (§4): BE +3.74% / -3.09%, `n` 341 / 307,
Jaccard 0.93 / 0.88 — the weakest row in that table. Joint (500 draws): rho
against `n` **-0.052, p = 0.24**, indistinguishable from zero against a noise
floor of 0.115; rho against the break-even margin -0.126. It is the weakest
portfolio driver by either method, which is the one reassuring thing about it.

**A defect in the sampling, logged here because this is the entry that owns
the constant.** `optimize/montecarlo.py` draws `delivery_days_per_week`
(5-7, in `COST_RANGES`) and `delivery_days_per_year` (260-365, in
`PORTFOLIO_RANGES`) **independently**, which breaks the `x 52` identity the
baseline is built on. A draw can deliver six days a week in the cost model and
365 days a year in the portfolio model. The effect on the published bands is
small — the parameter is near the noise floor in every outcome — but the two
should be tied, and until they are, `delivery_days_per_year` is contributing
inconsistency rather than uncertainty.

**Bias.** A value that is too high annualises too much volume and too much
operating cost, shrinking the fixed capital line's share and biasing the
break-even margin DOWN. 312 is the conservative end of the plausible range.

---

## 7. Where our value disagrees with a published one

Four cases. None has been changed in the code. Each needs a decision.

### 7.1 The labour-hours denominator: **2,808 vs the BLS convention of 2,080**

`labour_usd_per_hour` divides a BLS annual mean wage by
`shift_hours * delivery_days_per_week * 52 = 9 * 6 * 52 = 2,808` hours.

**That conflates two different things: how many days a week the NETWORK
delivers, and how many hours a YEAR one driver works.** A network that delivers
six days a week does not employ drivers who work six days a week; it employs
more drivers.

**[K] The BLS Occupational Employment and Wage Statistics programme states
that annual wages are computed by multiplying the hourly mean wage by 2,080
hours** (Handbook of Methods, OEWS, "Calculation",
`bls.gov/opub/hom/oews/calculation.htm`; the page was not opened from this
host and this should be confirmed). If so, dividing the OEWS annual mean by
2,808 recovers an hourly rate **26% below** the rate BLS actually measured.

Amazon's own delivery-partner job advertisements overwhelmingly describe a
**four-day, ten-hour** week, i.e. 40 hours, i.e. ~2,080 a year **[T -- these
are advertisements, not data]**.

**Measured effect.** Setting the denominator to 2,080 with everything else
unchanged: **median $1.0875 -> $1.3704, +26.0%.**

**Recommendation: this looks like a defect rather than a judgement call, and
it biases the headline DOWN by about a quarter.** The fix is to stop deriving
driver-hours from `delivery_days_per_week` and introduce an explicit
`driver_hours_per_year` constant sourced to the OEWS convention. It was not
applied here because it changes the project's headline figure and that is the
user's call.

### 7.2 `wage_loading` = 1.32 vs BLS ECEC at roughly 1.42

**[K] The BLS Employer Costs for Employee Compensation series reports that for
private-industry workers, wages and salaries are approximately 70% of total
compensation and benefits approximately 30%,** which implies a loading of
about **1.42**, not 1.32. For transportation and material-moving occupations
the benefit share is typically a little higher still. The ECEC news releases
are at `bls.gov/news.release/archives/ecec_*.htm` **[T -- URLs confirmed, the
specific figures were not read from them]**.

Neither Holmes (2011) nor Houde, Newberry and Seim (2023) applies any benefits
loading; both use gross payroll or gross annual wage directly. Holmes flags his
own approach as "crude". **[V]** So the published practice is *no* loading at
all, and we are already more careful than both.

**Measured effect.** 1.42 gives **$1.1483, +5.6%**. 1.46 gives **+7.9%**.

**Recommendation: raise to the ECEC figure once it is verified.** Unlike §7.1
this is a modest correction, but it runs the same direction.

**Combined with §7.1: $1.0875 -> $1.4525, +33.6%.**

### 7.3 `discount_rate` = 0.10 vs 0.05 in both Econometrica papers

Both Holmes (2011) and Houde, Newberry and Seim (2023) set a discount factor
**beta = 0.95**, i.e. roughly a 5.3% annual rate. Neither cites a source; both
simply set it. **[V] -- independently re-verified 2026-09-13 by opening both
papers.** Holmes, §2 "Dynamics", printed p. 261: *"the discount factor each
period is beta. The period length is a year, and the discount factor is set to
beta = .95."* That is the entire treatment. HNS, §3.5, printed p. 165, in a
subordinate clause beneath equation (11): *"where beta = 0.95 is Amazon's
discount factor"*. Also the entire treatment. `1/0.95 - 1 = 5.263%`, so our
0.10 is 1.9x theirs, not exactly double.

Our 10% is **double** theirs. That is defensible -- theirs is closer to a
social or risk-free rate while ours is closer to a private hurdle rate for a
logistics investment, and industry cost-of-capital datasets (Damodaran, NYU
Stern, `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html`
**[T]**) put trucking and transportation WACCs in the high single digits to low
teens. But the disagreement should be *stated*, not hidden.

**Measured effect: 5% gives -3.3%, 15% gives +3.2% on the break-even margin.**
Small. `horizon_years = 7` is pure convention (5 years gives +5.5%, 10 gives
-4.3%); both Econometrica papers write an infinite horizon and then avoid
solving it.

**Recommendation: keep 10%, add the comparison to the docstring.** The
parameter is not doing much work and the choice is arguable either way.

### 7.4 `cannibalisation_peak` = 0.18 -- the comparison in earlier drafts was against the wrong row, and probably against the wrong quantity

Both papers were re-read for this question on 2026-09-13. Full quotes, page
numbers and the complete Table VIII are in
[`../research/NOTES_holmes_2011_capital_and_cannibalisation.md`](../research/NOTES_holmes_2011_capital_and_cannibalisation.md)
§3 and
[`../research/NOTES_hns_2023_capital_and_cannibalisation.md`](../research/NOTES_hns_2023_capital_and_cannibalisation.md)
§3. Three corrections follow, and the third is the one that matters.

**Correction 1: the number is 12.3%, not 10%. [V]** Holmes (2011) Table VIII,
printed p. 275, general merchandise, all 3,176 stores: stand-alone sales
$41.4m against incremental $36.3m. `(41.4 - 36.3) / 41.4 = 12.32%`. Holmes's
own prose calls this "approximately a 10 percent difference", which is a
rounding of his own table. The food row, $44.8m vs $40.2m, is 10.27% and is
where "approximately 10 percent" is accurate. So the comparator is 0.123 for
general merchandise and 0.103 for food. Table V's ~1% chain-wide figure is a
different denominator and Holmes says so explicitly on p. 275; it is not a
comparator for us.

**Correction 2: we were comparing a ceiling to an average.**
`cannibalisation_peak` is defined at `optimize/params.py:97` as the *maximum*
share of volume a ZCTA can lose, the asymptote of `peak * (1 - exp(-exposure))`
at `optimize/objective.py:157-158`. Holmes's "All" row is an average over
Wal-Mart's entire fifty-year diffusion, including greenfield entry where
cannibalisation is near zero by construction. His by-maturity rows, which
earlier drafts of this document did not report, show the rate climbing
monotonically with network density. Computed by us from his Table VIII (he does
not print this column):

```
  State's Wal-Mart age    N (GM)   General merch.   Food (supercenters)
  --------------------    ------   --------------   -------------------
  1-2   (greenfield)         288        1.8%               3.4%
  3-5                        614        4.8%               4.5%
  6-10                       939        8.1%               9.5%
  11-15                      642       14.5%              19.0%
  16-20                      383       20.1%              22.0%
  21 and above               310       33.6%                n/a
  --------------------    ------   --------------   -------------------
  All                      3,176       12.3%              10.3%
```

The right Holmes comparator for a *saturation ceiling* is the *saturated* row:
**33.6%**. Against that, 0.18 is not 1.8x too high -- it sits between his
average and his ceiling, which is a defensible and arguably conservative place
for a peak to be. **And the 0.35 endpoint that §4 presents as an implausible
stress test is almost exactly Holmes's 0.336.** The stress test is the
literature-supported value.

**Correction 3, and this supersedes the other two: the quantity almost
certainly does not transfer at all.**

The caveat already in the code (`optimize/params.py:120-124`) -- that Holmes
cannibalises *sales at a store*, which walk, whereas we cannibalise *volume in
a ZCTA*, which does not -- is **correct and understated**. It is not a reason
to prefer 0.10 over 0.18; it is a reason to doubt any non-zero value under the
current specification.

Holmes's mechanism is a consumer choosing one outlet from a 25-mile choice set
(§4.1, p. 265). Sales move *between stores*. `optimize/objective.py:158`
instead reduces `annual_parcels` for a selected ZCTA, and `annual_parcels` is
built in `cost/daganzo.py` from the *households resident in that ZCTA*. Those
households do not order fewer parcels because a neighbouring ZIP was also
activated. Parcel demand is anchored to the customer's home; there is no second
outlet to divert it to.

**HNS turn that argument into a measurement. [V]** Their Table VIII (§4.4,
pp. 180-181) moves three San Bernardino fulfilment-centre openings forward a
year and reports the effect on every other facility. The Arizona facility loses
**88%** of its orders; Nevada 17%; Washington 3%. But the system-wide total
change in orders under a tax-neutral counterfactual is **exactly 0.00** -- the
paper states "total demand remains unchanged (see last row)". All of the
facility-level cannibalisation is *reallocation between facilities*. Separately
(§3.6, p. 165) they tested whether household spending responds to facility
proximity, could not reject independence, and adopted it as a maintained
assumption.

So both papers measure diversion of a fixed quantity of demand between the
firm's own outlets, and neither measures destruction of demand in a geographic
area. Our term does the latter.

**Measured effect (2026-09-13, single process, `cost/depots.py` md5 `d93ae1ecaf`
-- see §9.1).**

```
  cannibalisation_peak                              n     BE $/parcel   Jaccard
  ----------------------------------------------  ----   -----------   -------
  0.000  HNS-implied net demand effect             313      1.1788      0.574
  0.050  low end of the published range            311      1.2289      0.647
  0.103  Holmes VIII food, ALL stores              302      1.2780      0.764
  0.123  Holmes VIII gen. merch, ALL stores        302      1.2974      0.808
  0.180  CURRENT VALUE                             282      1.3431      1.000
  0.201  Holmes VIII GM, state age 16-20           266      1.3559      0.864
  0.336  Holmes VIII GM, state age 21+             177      1.3369      0.457
  0.350  high end of the published range           177      1.3403      0.434
```

Note the break-even margin is **not** monotone -- it peaks near 0.20 and falls
again by 0.336, because heavy cannibalisation drives the optimiser into a
smaller, denser, individually cheaper portfolio. A reader who judges robustness
by the margin column alone will conclude the parameter barely matters. The
Jaccard column says 43% of the portfolio changes between 0.18 and 0.00, and 54%
between 0.18 and 0.336.

**Recommendation, revised.** The earlier recommendation -- report at 0.10 and
0.18 side by side -- rests on a comparator that is both the wrong row of
Holmes's table and, more importantly, the wrong quantity. Replace it with:

1. **Decide what an activation is.** This parameter and
   `capital_per_activation_usd` are the same defect (§7.5). If an activation is
   a ZCTA of resident demand, the peak should be near **zero** and the
   neighbour interaction should affect only cost, which `linehaul_sharing`
   already handles. If an activation is a *station* with a catchment, then
   Holmes transfers cleanly, **0.12-0.34** is the right band, and $4m per unit
   becomes correct -- but parcels and cost per unit are then wrong by the
   ZCTAs-per-station ratio.
2. **Until that is decided, report the portfolio at 0.00, 0.18 and 0.336**, not
   at 0.10 and 0.18. Those three are the HNS-implied value, the current value,
   and the strongest Holmes-supported value, and they bracket the honest
   uncertainty. The 330-ZIP list -- or the 282-ZIP list, see §9.1 -- should not
   be presented as a single answer.
3. The Pollmann distance-band estimate remains the right destination, but note
   it would estimate a *spatial spillover in observed volume*, which is the
   quantity we actually need and neither Econometrica paper supplies.

### 7.5 The two disagreements above are one defect

`capital_per_activation_usd` (§6.16) and `cannibalisation_peak` (§7.4) are not
independent problems. They are two symptoms of an unresolved ambiguity about
what an "activation" is:

```
  term                          file:line                    treats a unit as
  ---------------------------   --------------------------   ----------------
  annual_parcels, annual_cost   optimize/objective.py:81-83  a ZCTA of resident demand
  capital (n x $4m)             optimize/objective.py:164    a facility
  cannibalisation of volume     optimize/objective.py:158    a facility with a catchment
```

Rows two and three are consistent with each other and both are inconsistent
with row one. Tuning the two constants separately cannot fix that; deciding
what an activation is fixes both at once. **This is the single highest-value
decision outstanding in the portfolio model**, and it is the user's to make.

A third-order observation, logged and not acted on: `optimize/objective.py:126`
builds the interaction weight as `clip(1 - d/radius, 0, 1)`, strictly monotone
in distance. HNS Table VIII shows the effect of a new facility on existing ones
is **non-monotone** in distance -- Washington at 965 miles loses more shipping
cost than Nevada at 399 -- and they say the non-monotonicity is severe enough
to rule out Jia's (2008) solution methods (p. 181). If this interaction is ever
estimated rather than assumed, a monotone kernel is the wrong starting point.

---

## 8. What could not be verified

Listed so nobody mistakes silence for confirmation.

- **Every `[K]` item above.** WebFetch is proxy-blocked on this host and the
  search tool returns titles and URLs only, so no page was opened. Specifically
  unverified: the ATRI $0.196/mile figure; the BLS OEWS 2,080-hour convention;
  the BLS ECEC ~30% benefit share; the ~0.7124 asymptotic TSP constant; the
  22bn parcels / 131m households figures behind 3.2; the MWPVL 700-900
  delivery-station count.
- **`stops_per_tour`, `van_lease_usd_per_day`, `service_minutes_per_stop`,
  `parcels_per_stop`, `income_elasticity`, `linehaul_sharing`,
  `cannibalisation_radius_km`, `CATCHMENT_MILES`** -- no published source was
  found for any of these. They are engineering estimates and the documents now
  say so.
- **Author attribution for the dwell-time and cannibalisation leads in §6.8 and
  §6.18.** Titles and venues were confirmed; author lists were not.
- **Nishida (2012), Management Science 58(11) 2001-2018** -- the title is
  confirmed and a copy exists at
  `marketing.business.uconn.edu/.../empirical-investigation-of-retail-
  expansion.pdf`, but the author attribution is carried over from
  `REFERENCES_to_add_v4.md` where it is itself marked unconfirmed.

---

## 9. How the sensitivity was measured, so it can be re-run

Reproduce with `.venv/bin/python`:

```python
from dataclasses import replace
from siting_atlas.cost.daganzo import DaganzoCostModel
from siting_atlas.cost.params import BASELINE
from siting_atlas.cost.runner import pilot_slice

frame = pilot_slice(2023, 4)                      # 2,333 pilot ZCTAs
base = DaganzoCostModel(BASELINE).evaluate(frame)["cost_per_parcel"].median()
alt  = replace(BASELINE, service_minutes_per_stop=4.0)
new  = DaganzoCostModel(alt).evaluate(frame)["cost_per_parcel"].median()
print(new / base - 1)                             # +0.4429
```

One parameter is moved at a time from `BASELINE`; everything else, including
the solved depot network, is recomputed. The rank column is the Spearman
correlation between the perturbed ordering of `zcta` and the baseline
ordering. For the portfolio table the same is done with
`PortfolioParameters`, a $2bn budget and `BudgetedSelector.solve(None)`, and
the overlap column is the Jaccard index of the two selected ZCTA sets.

The catchment table in §5 re-runs `warehouse.facilities.enabled_flags` against
the delivered `data/external/facility_panel/facilities.csv` at each radius.

A full run of the cost model takes about 10 seconds and the portfolio about 8,
so re-measuring the whole of this document costs a few minutes. There is no
excuse for quoting a stale sensitivity figure.

### 9.1 Why §4's sweep is on a superseded baseline

§4's headline was updated on 2026-09-14 and now quotes
`experiments/portfolio-optimiser/artefacts/portfolio_report.json` run `20260914-002431-7419`. **Its
table was not re-swept** and is still on the older network; this section is
the record of what changed and by how much.

The table was swept against **330 activations, $1.32bn committed, break-even
$1.3887/parcel, optimality gap 13.4%**. `docs/DECISION_LOG.md` §4.2 reports
$1.27bn, a third value. Re-measured on 2026-09-13 the same call returns:

```
                          sec.4 sweep basis      run 20260914-002431-7419
  activations                     330                    282
  capital committed            $1.32bn                $1.128bn
  break-even margin            $1.3887                 $1.3431
  optimality gap                 13.4%                   10.7%
  median cost per parcel       $1.0875                 $1.0830
```

Nothing in `optimize/` changed. The cause is `src/siting_atlas/cost/depots.py`,
which was being rewritten during this session -- k-means placement replaced by
a p-median formulation, on the correct argument that line haul is billed
linearly in distance so the minimiser is the weighted median, not the weighted
mean. Different depots, different line haul, different cost ranking, different
portfolio. The cost model itself is deterministic (verified: identical md5 of
the `cost_per_parcel` vector across repeated processes, with and without
`OMP_NUM_THREADS=1`), so this is a real change in the model, not flakiness.

Two consequences. First, **every absolute count in §4 and §6.16 needs
re-running once `depots.py` settles**; the orderings, the Jaccard patterns and
the ratios are the durable content. Second, the portfolio baseline is more
sensitive to the *depot placement algorithm* than to any parameter in §4 --
`n` moved 15% and the break-even margin 3.3% from a change nobody classified as
a parameter at all. That belongs in the sensitivity story, because it is larger
than `discount_rate`, `linehaul_sharing` and `delivery_days_per_year` put
together.

**Joint sampling has since put a number on that second point, and it is the
sharper version of the argument.** [`UNCERTAINTY.md`](UNCERTAINTY.md) §3 solves
500 draws on the *current* p-median network and finds 282 at the 68th
percentile of the resulting distribution — comfortably inside — while 330 sits
at the **97th**. So under today's solver, no plausible combination of the
twenty-one sampled parameters makes 330 a typical answer; under yesterday's
solver it was the baseline. **The depot algorithm moved the headline further
than a two-sigma parameter excursion does.** The 48-activation drift was real,
and the parameters did not cause it.
