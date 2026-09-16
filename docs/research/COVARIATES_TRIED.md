# Every covariate tried, and why each one failed

> **SETTLED on the covariate-search figures, 2026-09-15.** The live re-run of
> `covariate_search.json` has completed and every figure below has been
> re-derived from it. The frame is **477 decisions, 191 held out**, the
> baseline is **6.2157x**, and the 694-vs-687 facility disagreement is gone —
> the artefact reads **687 at every stage**. **One caution survives and is not
> about this run:** the emitter reuses one `run_id` across writes and stamps
> `written_at` at the first write, so the stamp cannot distinguish two
> versions of the file. Check `facilities: 687` before quoting it. See
> [`NOTES_COVARIATE_SEARCH.md`](NOTES_COVARIATE_SEARCH.md) §11.

*Compiled 2026-09-14, **re-read from the completed re-run 2026-09-15**, from
`outputs/metrics/covariate_search.json` (`core` stage: 50 re-splits, **477
decisions**, 191 held out), `panel_experiments.json`, `network_inference.json`,
`leakage_test.json` and `gbm_benchmark.json`. Every figure here is read from an
artefact; none is retyped from prose. `covariate_search.json` now reports
**687 facilities offered** consistently at the top level and in all three
staged frames (see [`NOTES_COVARIATE_SEARCH.md`](NOTES_COVARIATE_SEARCH.md)
§11).*

This is the inventory the inspirator asked for: what has been tested, what it
did, and — the useful part — **why**. Two mechanisms account for almost every
failure, and neither is "the variable does not matter in the real world".

---

## 0. How to read the numbers

All lift figures are **top-10 lift over chance in LARGE METROS** (choice sets
with more than 100 candidate ZCTAs), measured on held-out decisions over 50
re-splits with the model refitted inside each one, on
**`covariate_search.json`'s `core` frame: 477 decisions, 191 held out**. That
frame is not the 483-decision frame `panel_experiments.json` and
`refit_expanded.json` use, and its lifts are not interchangeable with theirs —
the same four columns score 6.2157x here and 6.2585x there. Every lift quoted
below names its arm; if you carry one out of this file, carry the frame with
it.

Large metros only, because pooling across market sizes is a Simpson's-paradox
trap this project fell into twice. In a choice set of 25 or fewer, random
guessing already lands in the top ten about 67% of the time, so lift there is
structurally capped near 1.5x however good the model is. Large metros are also
where a siting decision is actually contested.

```
  covariate_search `core` baseline, four columns   6.2157   477 decisions
  the same model with warehousing removed          2.6785   <- the floor
```

**The whole model is one column.** Removing `warehousing_establishments` costs
3.54 of 6.22. Everything below is measured against that baseline.

---

## 1. The two mechanisms

### 1.1 Wrong geographic grain

A conditional choice model compares alternatives **inside** a choice set. It
never uses variation between metros — that is differenced away by construction.
So a covariate's only currency is how much it varies among the ~200 candidate
ZCTAs of one metro.

`mean_distinct_values_per_large_metro`, from the column audit:

```
  ZIP-GRAIN, usable                    COUNTY-GRAIN, dead on arrival
    land_area_sqmi          200          traffic_proximity      9.2
    annual_payroll          197          diesel_pm              9.2
    in_labor_force          195          low_income_pct         9.2
    households              193          people_of_colour_pct   9.2
    vehicle_availability    193          permit_units_total     8.0
    employment              192          permits_yoy_pct        7.9
    owner_occupied          190
    bachelors_degree        187
    median_home_value       182
    renter_occupied         181
    establishments          164
    median_age              122
```

Six of eighteen columns offer the model **nine distinct values to choose among
two hundred ZCTAs**. They are county figures broadcast down to every ZCTA in
the county. Their true effect could be enormous and they would still be unable
to answer the question, because within a metro they are nearly a constant, and
a constant cannot rank anything.

This is not a data-quality problem. `traffic_proximity` is populated on 99.9%
of rows. It is a **grain** problem, and no amount of collecting more county
data fixes it.

### 1.2 Collinear with the numeraire

`households` is the numeraire — the model fixes its coefficient at 1.0 and
measures everything else against it. Five ACS candidates correlate **0.84 to
1.000 with households within metro**. A ZCTA with twice the households has
twice the cars, twice the labour force, twice the graduates.

The model is not identified in those columns. It cannot tell "this place is
attractive because people live here" from "this place is attractive because
people live here and therefore own cars".

### 1.2b A number that predicts failure BEFORE fitting

The grain argument above is qualitative — "county columns are nearly constant
inside a metro". It can be made into a **screening rule**, and that is the
most transferable result the project has produced.

Measure the **within-metro coefficient of variation** of a candidate column,
averaged over the 41 large metros (8,271 candidate ZCTAs). Measured
2026-09-14 on twenty-one network terms, including six whose grain is a tunable
parameter rather than an accident of publication
(`experiments/gravity-network/artefacts/gravity_network.json`, `terms.dispersion`):

```
  within-metro cv        column                                  outcome
  ------------------     ------------------------------------    --------
  0.30                   fulfilment gravity, alpha = 1           BOUNDARY
  0.31 - 0.44            the other five alpha = 1 terms          BOUNDARY
  0.59                   network_within_50mi                     BOUNDARY
  ....................................................................
  1.40                   sortation_proximity                     BOUNDARY
  1.44                   fulfilment_proximity                    interior
  4.36 - 5.49            the six alpha = 2 terms                 4 interior,
                                                                 2 boundary
  6.82 - 8.50            the six alpha = 3 terms                 4 interior,
                                                                 2 boundary
```

**The rule runs ONE WAY ONLY.** Everything below cv 0.6 lands on the
boundary — **7 of 7**. Above cv 1.3, **9 of 14** are interior and **5 are
not**. Nothing at all falls in between: the 0.6–1.3 band is empty in
twenty-one terms, so this says nothing about intermediate dispersion.

So a low cv **rules a column out** and a high cv does **not** rule it in.
An earlier version of this section read "everything above cv 1.3 is interior",
which made the reading two-way and turned a screen into a predictor. The five
high-cv failures are `sortation_proximity`, `sortation_gravity_sqft_a2`,
`sortation_gravity_count_sqft_subset_a2`, `sortation_gravity_sqft_a3` and
`sortation_gravity_count_sqft_subset_a3` — every one on the **sortation**
side, four of the five carrying square footage. Every fulfilment-side high-cv
term is interior, 7 of 7.

**Read this as description, not as an estimated relationship.** n = 21 terms
from one run at one vintage, and they are not independent: each is one of two
columns in one of 13 arms fitted over the same 483 decisions. Verdicts are
`arms.<arm>.verdicts.<col>.state` in
`experiments/gravity-network/artefacts/gravity_network.json`
(`20260915-210603-b780`); see `docs/NUMBERS.md` §5.

Two things make this more than a correlation. The `alpha` exponent is a
*knob*: turning it from 1 to 3 changes nothing about what the covariate
measures — still proximity to the same facilities — and changes only how
sharply the measure discriminates within a metro. The cv rises from 0.30 to
8.50 and the coefficient moves from the boundary to the interior. That is the
grain mechanism isolated from every other property a column might have —
though the knob does not carry every term: the sortation square-footage
masses stay on the boundary at every alpha, which is the same five failures
listed above.

And it explains, retrospectively, the one failure that had no explanation:
`network_within_50mi` sits at cv 0.59, on the boundary side of the line,
which is why a *count* inside a radius failed at 25, 50 and 100 miles while a
*distance* to the same facilities worked. The radius was never the issue.

**Use it as a pre-filter.** Any candidate covariate can be scored for
within-metro cv in seconds, before any model is fitted. Below about 0.6, do
not bother. That would have saved most of the work in section 2.

### 1.3 The exception that proves both

The only covariate class ever found in the **interior** — a coefficient
neither at zero nor indistinguishable from the numeraire — is proximity to
Amazon's own non-delivery-station network. It is genuinely ZCTA-level
(a distance from each candidate), and it is not a population measure.

```
  sortation_proximity    0.097  [3.0e-14, 0.247]   4 of 50 re-splits at boundary
  fulfilment_proximity   0.170  [0.025,   0.400]   0 of 50 at boundary
  network_within_50mi    at the boundary at 25, 50 AND 100 miles
```

*Intervals are the metro-clustered bootstrap from
`experiments/gravity-network/artefacts/network_inference.json`
(`20260915-210640-dbcd`), not the re-split spread; the census counts are
`boundary_census.proximity_published` in `gravity_network.json`. **Corrected
2026-09-16.** This block read 0.110 [0.007, 0.255] and 0.164 [0.007, 0.419]
with "1 of 50 for each", which were the 2026-09-14 figures on the superseded
panel. The two columns are no longer symmetric: `fulfilment_proximity` really
is interior on all 50 re-splits in this arm, and `sortation_proximity` is at
the boundary on 4 — and its bootstrap lower endpoint IS the boundary. §5.1
withdraws the pair as a claim; this block is what the census says, not what
survives inference.*

A later specification does clear the strict test. `gravity_count_a3` — the
same facilities entered as `sum_j mass_j / d_ij^3` — is **0 of 50** at the
boundary in both columns, and in a head-to-head where gravity and
nearest-distance are offered together the optimiser keeps gravity and discards
distance: `fulfilment_proximity` moves from 0 of 50 to **22 of 50** on the
boundary, its coefficient collapsing 0.187 to 0.030, and `sortation_proximity`
from 4 of 50 to **28 of 50**, 0.104 to 0.017. See
[`NOTES_GRAVITY_NETWORK.md`](../../experiments/gravity-network/notes/NOTES_GRAVITY_NETWORK.md).

The third line of the block above is the one to keep: **proximity works,
counting does not**, at any radius — and §1.2b says why. The count sits at
cv 0.59, below the threshold; the radius was never the issue.

---

## 2. The fifteen, one at a time

Delta is against the 6.2157 baseline. "No-op" means the arm returned a number
**identical to the baseline to fifteen decimal places** — the added column's
weight was driven to the boundary, or left too small to reorder anything, and
the column contributed literally nothing.

| # | Covariate | Lift | Delta | Verdict | Why |
|---|---|---|---|---|---|
| 1 | `traffic_proximity` | 6.2239 | **+0.0082** | best of the fifteen, and still nothing | County grain: 9.2 distinct values per metro. Measures pollution exposure, not highway access |
| 2 | `diesel_pm` | 6.2157 | 0.0000 | **no-op** | County grain, 9.2 values |
| 3 | `low_income_pct` | 6.2157 | 0.0000 | **no-op** | County grain, 9.2 values |
| 4 | `people_of_colour_pct` | 6.2157 | 0.0000 | **no-op** | County grain, 9.2 values |
| 5 | `employment` | 6.0971 | **−0.1186** | actively harmful | ZIP grain, but collinear with households |
| 6 | `annual_payroll` | 6.2116 | −0.0041 | no effect | ZIP grain, collinear |
| 7 | `median_home_value` | 6.2157 | 0.0000 | **no-op** | Should enter negatively; `beta = exp(theta)` forbids it, so it goes to the boundary |
| 8 | `inv_median_home_value` | 6.2157 | 0.0000 | **no-op** | The reciprocal, added precisely to let #7 express a negative sign. It still did nothing |
| 9 | `inv_diesel_pm` | 6.2157 | 0.0000 | **no-op** | Same test for #2. Same answer |
| 10 | `vehicle_availability_total` | 6.2157 | 0.0000 | **no-op** | **It IS `households`** — see §2.2 |
| 11 | `in_labor_force` | 6.1707 | −0.0450 | no effect | Collinear |
| 12 | `bachelors_degree` | 6.2157 | 0.0000 | **no-op** | Collinear |
| 13 | `median_age` | 6.2157 | 0.0000 | **no-op** | Collinear |
| 14 | `owner_occupied` | 6.0317 | **−0.1840** | worst of the fifteen | Collinear |
| 15 | `renter_occupied` | 6.2157 | 0.0000 | **no-op** | Collinear |

**Ten of fifteen were exact no-ops** — up from seven on the superseded copy of
the artefact, because `diesel_pm`, `people_of_colour_pct` and
`inv_median_home_value` all moved from a hair's-breadth effect to none at all.
Not "small effects that might emerge with more data": the model was
bit-identical with and without them on every one of the 50 re-splits. The
ordering of the five that are not no-ops is unchanged — `traffic_proximity`
best, `owner_occupied` worst.

### 2.1 The building-permit columns, tested separately

`permit_units_total` and `permits_yoy_pct` got their own stage because they are
the only **forward-looking** columns in the panel — nine BPS vintages were
fetched specifically to build them, and nothing had ever used them.

```
  baseline (on the permit subsample)     6.3185
  + permit_units_total                   6.3185     0.0000   no-op
  + permits_yoy_ratio                    6.3185     0.0000   no-op
  + inv_permits_yoy_ratio                6.3185     0.0000   no-op
  + all three permit columns             6.3185     0.0000   no-op
```

**All four permit arms are now exact no-ops.** On the superseded copy
`permit_units_total` bought +0.0050 of lift, winning 1 re-split of 50; on the
settled run it wins none and ties 50. The optimiser still *uses* the column —
it is off the boundary on 96% of splits, median coefficient 0.178 — so this is
a stronger null than a discarded column, not a weaker one.

Also county grain — 8.0 and 7.9 distinct values per metro — and they cost
sample: **101 of 477 decisions drop** for want of permit coverage, and the
lost decisions are not a random slice (51.5% mid-size markets among the lost
against 34.0% among the kept).

### 2.2 Two of the fifteen were never independent tests

Found 2026-09-14 while testing per-capita normalisation, and both change how the
table above should be read.

**`vehicle_availability_total` is `households`.** Not correlated with it —
**equal to it**, to floating-point precision, on all 21,768 ZCTAs. It is ACS
table B25044, whose universe is occupied housing units, which is the same
quantity the panel calls `households`. Its per-household ratio is the constant
1.0 and cannot be entered at all.

So row 10 was never a test. It added the numeraire to the model a second time,
and the exact no-op is the only possible outcome. This is also a small warning
about the panel: two columns with different names hold one variable, and
nothing in the schema says so.

**`owner_occupied + renter_occupied = households`, exactly.** Their
per-household correlations with `households` are +0.36830991164973 and
−0.36830991164973 — identical to fifteen digits, opposite in sign — because
`owner_per_hh = 1 − renter_per_hh`. Rows 14 and 15 are therefore one test
reported twice, not two.

**Corrected count: thirteen independent candidates, not fifteen.** The verdict
does not change, but the arithmetic in §7 should be read with that in mind.

### 2.3 Normalising per household repairs the damage and finds nothing

The collinear columns were re-entered as rates, to test whether collinearity
was *masking* signal. The transform works — measured within-metro correlation
with `households`, before and after:

```
  in_labor_force     +0.982  ->  +0.112
  owner_occupied     +0.909  ->  -0.368
  bachelors_degree   +0.880  ->  +0.158
  establishments     +0.752  ->  -0.053
  employment         +0.546  ->  +0.008
```

And the prediction result, beside the level versions from the table above:

```
  column            LEVEL (covariate_search)   RATE (percapita_search)
  employment        6.0971  (-0.1186)          6.3848  (-0.0041)
  owner_occupied    6.0317  (-0.1840)          6.3889  ( 0.0000)  no-op
  in_labor_force    6.1707  (-0.0450)          6.3889  ( 0.0000)  no-op
```

*The two columns are no longer on the same frame.* `covariate_search.json` was
regenerated on 2026-09-15 onto a 477-decision / 687-facility frame;
`percapita_search.json` has not been re-run and is still on the superseded
479-decision / 694-facility frame, where the baseline reads 6.3889 and the
floor 2.7352. Each delta is against its own artefact's own baseline, so the
*directions* compare and the *levels* do not. Re-running
`percapita_search` would put them back on one frame.

**Normalising repaired the damage completely and produced no lift.** The
failures were over-determined: the columns were collinear *and* empty. That
closes the question — collinearity was not hiding anything.

One arm is worth recording separately. `warehousing_establishments` entered as
a RATE instead of a count keeps **81.6%** of the count's value over the floor
and is interior on 50 of 50 splits — but it loses 41 of 50 re-splits and its
Brier (0.005407) is **worse than dropping the covariate entirely** (0.005371).
Good ranking with degraded probabilities is what mixing a rate into a sum of
counts predicts. It does not license a swap.

Full detail:
[`NOTES_PERCAPITA.md`](../../experiments/percapita-logrel/notes/NOTES_PERCAPITA.md).
**All eleven declared arms completed** at the full 50 re-splits
(`percapita_search.json`, `arms_unfinished: []`), so the verdict is closed on
all eight per-household columns and not merely indicated: six of the eight are
exact no-ops (0.0000, tied on 50 of 50 re-splits) and the other two,
`employment_per_hh` and `annual_payroll_per_hh`, each cost −0.0041 of lift and
lose exactly one re-split of fifty. *(This paragraph said "four of eleven arms
completed under machine contention" until 2026-09-16; the contention was real
but the run was finished afterwards.)*

### 2.4 The collinear coefficients do not vanish — they explode

Worth stating separately because it is the opposite of what "no-op" suggests.
A column at the boundary contributes nothing and is harmless. A column
collinear with the numeraire is not harmless:

> `in_labor_force` takes a median coefficient of **5.1e12**, with an interval
> spanning nineteen orders of magnitude, and it drags
> `warehousing_establishments` with it — to 5.0e12, on the upper boundary in
> 82% of re-splits.

So the two failure mechanisms have different consequences. Wrong grain is
inert. Collinearity is destabilising, and it damages the one covariate that
works.

---

## 3. The searches, which failed in a more interesting way

| Search | Lift | Delta | What it says |
|---|---|---|---|
| **forward selection, nested and honest** | 6.0889 | **−0.1268** | Selecting columns inside each training fold produced a model **worse than adding nothing** on this stratum. Pooled across all choice-set sizes the same arm is slightly better, so the stratum has to be named |
| forward + demographics | 6.0889 | −0.1268 | Identical. The demographics add nothing even to a search |
| forward, no warehousing | 3.9830 | −2.2327 | With the load-bearing column removed, search recovers part of the gap and lands far short |
| naive selection (whole frame) | — | — | Selected on all the data, so its gain is optimistic by an unmeasured amount. Reported only as the contrast |

**The honest search losing to the baseline is a result about method, not about
Amazon.** At this sample size, choosing which columns to include is itself a
parameter, and fitting it overfits. The naive version is kept in the artefact
purely so a reader can see the size of the gap between "selected on everything"
and "selected honestly".

---

## 4. What has worked, for contrast

| Covariate | Effect | Status |
|---|---|---|
| `warehousing_establishments` | +3.54 lift over the no-covariate floor | The model. Audited for circularity: retains **79%** of its value on honest pre-opening vintages (`leakage_decisive.json`, n=29) |
| `sortation_proximity` | at the boundary in 4 of 50 re-splits; under the metro-clustered bootstrap it **no longer clears zero** | **Withdrawn as a working covariate** — see §5.1 |
| `fulfilment_proximity` | interior in 50 of 50 re-splits in the proximity arms, but at the boundary in 22 of 50 once gravity competes | Survives, weakly: 0.170 [0.025, 0.400] clustered, 1.6% of replicates at the boundary |
| `households` | numeraire, fixed at 1.0 | Not tested; it is the yardstick |
| `land_area_sqmi` | at the boundary | In the published specification and contributing nothing |
| `establishments` | at or near the boundary | Same |

Combined gain from the two network proximities: top-5 **+1.23 points**,
improving in 42 of 50 re-splits, Brier improving in 49 of 50 — about **two
decisions in 194**. Small, consistent, and the only positive result here.

*The two proximity rows were corrected on 2026-09-16. They both read "interior
in all 50 re-splits", which §5.1 of this same file had already withdrawn and
which the boundary census in `gravity_network.json` does not support for
`sortation_proximity` (4 of 50, and 28 of 50 once gravity competes). The
combined-gain sentence above is unaffected — it is a prediction gain, not a
claim about either coefficient's interval — but "the only new class ever to
work" is now one column, not two.*

---

## 5. Pending

| Feature | Grain | Status |
|---|---|---|
| **`industrial_sqmi`** (OpenStreetMap) | polygon → ZCTA | **Running.** 9 of 62 metros. The direct buildability measure, and the one most likely to work: genuinely ZIP-grain and not a population proxy |
| **Highway / interchange distance** (Census TIGER) | geometry → ZCTA | **Running.** Distinct from `traffic_proximity`, which failed on grain |
| ~~Network proximity under clustered inference~~ | — | **DONE, and the claim was WITHDRAWN.** See below |

### 5.1 The one claim that was withdrawn

An earlier run had the network arm producing the first coefficient interval in
the project's history to exclude the numeraire. Under proper inference it does
not (`experiments/gravity-network/artefacts/network_inference.json`, `run_id 20260915-210640-dbcd`,
`combined_plus_network` arm, 483 decisions, bootstrap over 194 metros,
R = 500):

```
  re-split percentiles        1.419  [1.134, 2.047]   clear of 1.0 -- NOT inference
  MLE on all 483 decisions    1.348       --
  bootstrap over 194 metros   1.348  [0.997, 1.958]   contains 1.0
  sandwich, metro-clustered   1.348  [0.981, 1.852]   contains, p = 0.065
  sandwich, independent       1.348  [0.880, 2.066]   contains, p = 0.170
```

**All three estimators that are inference contain 1.0; the one that excluded
it is the one that is not inference.** 15 of 500 clustered replicates fall
below 1.0 (3.0%) against the 2.5% an exclusion needs, and the 2.5th percentile
sits 0.22 of its own Monte Carlo error from 1.0 — it is close enough to 1.0
that more replicates could move it either way, so the honest reading is "does
not exclude", not "comfortably contains".

Two details worth carrying:

- The published point estimate was never 1.40 on all the data. It is the mean
  of `exp(theta)` over 50 fits on 290 decisions each; the MLE on all 483 is
  **1.348**.
- The clustered interval is **5% wider** than the re-split spread despite
  being fitted on 483 decisions rather than 290. That is the cleanest
  available demonstration that a percentile spread across re-splits
  understates uncertainty, and it should end the practice of quoting one.

The proximities are weaker than this section used to report. `fulfilment_proximity`
survives: 0.170 [0.025, 0.400], strictly above zero, with 1.6% of clustered
replicates at the boundary. **`sortation_proximity` no longer does**: 0.097
[3.0e-14, 0.247] — the lower endpoint is the boundary, not a positive number,
and 3.8% of clustered replicates land exactly at zero. "Interior in every one
of 50 re-splits" does not survive for either.

And the theoretical cost is now measured rather than conceded. Over 43,224
merged ZCTA pairs, the relative error in the merger identity is **0.00** for
the extensive-only control and **0.044 median, 0.455 maximum** for this arm.
A write-up cannot print "invariant to ZCTA boundaries, per Train sec. 3.4
Example 2" and this arm's coefficients on the same page.

---

## 6. Not built, ranked by what the evidence says

| Feature | Grain | Verdict |
|---|---|---|
| **Parcel acreage / van-staging land** | parcel | Passes **both** filters — finer than ZIP, uncorrelated with population. The best untested idea. Blocked on ~3,000 county portals; `services.arcgis.com` is reachable from this host but the browse portals are not |
| **ZCTA shape compactness** | polygon | **Free, and never measured.** Daganzo's own abstract says zone shape is his contribution — *"ignoring shape during the clustering step can increase significantly travel distances"* — and the TIGER shapefiles are already on disk |
| Rail intermodal distance | point | Cheap once the TIGER machinery exists |
| Airport proximity | point | Cheap, plausible for air-hub-fed stations |

### Ruled out, with the reason

- **Subsidies** — county grain, and endogenous besides: a county offers a
  subsidy *because* a firm is already interested. Measured separately in
  `outputs/metrics/subsidies.json`.
- **Any remaining ACS column** — collinear with households by construction.
- **Building attributes** (power supply, ceiling height, dock doors) — the
  right variables, and not public at national scale.

---

## 7. What this adds up to

Fifteen covariates, five panel compositions, three algorithms, and a reframing
have now been tested. The ceiling has held at roughly **2.5x to 3.1x**
standardised lift throughout, a spread narrower than a single method's
variation across re-samples.

The contribution is not that the covariates are weak. It is that **the failure
has a diagnosis**, and the diagnosis generalises:

> A conditional choice model over ZIP codes can only use covariates that vary
> **within** a metropolitan area and are **not proxies for population**. Most
> free public data is published at county grain, or is a population count
> wearing a different name. That is a statement about the public data
> infrastructure, not about this model.

It also generates a testable prediction, and `fulfilment_proximity` is its
first confirmation — one column, not the two this paragraph used to claim,
since §5.1 withdraws `sortation_proximity`: **the covariates that work are
the ones computed as a distance from each candidate rather than looked up
against it.** `industrial_sqmi` and highway distance are the next two tests of
that rule.

## 8. Related

- [`NOTES_COVARIATE_SEARCH.md`](NOTES_COVARIATE_SEARCH.md) — the search itself
- [`NOTES_PANEL_EXPERIMENTS.md`](NOTES_PANEL_EXPERIMENTS.md) — the five panel compositions and the network covariates
- [`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) — whether the ceiling is the data or the functional form
- [`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) and [`NOTES_LEAKAGE_DECISIVE.md`](NOTES_LEAKAGE_DECISIVE.md) — whether the one working covariate contains its own outcome
- [`NOTES_WHITE_SPACE.md`](NOTES_WHITE_SPACE.md) — the reframing, and why it failed
