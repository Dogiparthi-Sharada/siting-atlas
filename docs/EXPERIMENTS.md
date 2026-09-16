# Experiments — everything this project ran, and what came back

*Written 2026-09-15. A research programme, not a list of failures: several of the
negative results below were expensive to establish and are the contribution.*

[`NUMBERS.md`](NUMBERS.md) is the tie-breaker on every figure; where it and this page
disagree, it wins. **Cite the artefact, not the figure.** Nine artefacts carry **no
`run_id` and no `written_at`**, only a file mtime — `panel_experiments`, `white_space`,
`mwpvl_coverage`, `national_panel_expanded`, `subsidies`, `logrel_search`,
`percapita_search`, and (not yet in `NUMBERS.md`'s list) `leakage_decisive` and
`catchment_band`. **Every `[2.5, 97.5]` bracket below is a percentile over re-splits of
one fixed decision set — not a confidence interval and not a standard error**
([`ALGORITHMS.md` §5](ALGORITHMS.md)). Companion: [`ALGORITHMS.md`](ALGORITHMS.md) —
how each estimator works and why it was chosen.

## The programme at a glance

| § | Experiment | The question | What came back | Artefact |
|---|---|---|---|---|
| [1](#e1) | Five panel compositions × three algorithms | Does a 5× bigger panel buy ranking accuracy? | No, and it costs none. 15 cells span 2.49–3.08 standardised lift | `panel_experiments.json` |
| [2](#e2) | The expanded refit | Was the binding constraint sample size? | No. 5× the sample; the coefficient walked *towards* the numeraire | `refit_expanded.json` |
| [3](#e3) | Fifteen covariates, plus permits | Do any unused columns help? | Ten exact no-ops; the table spans 0.94 pp. Permits 0.0000, 0-50-0 | `covariate_search.json` |
| [4](#e4) | Nested forward selection | Does honest in-fold selection beat adding nothing? | **−0.62 pp on the large-metro top-10 stratum, +0.36 pp pooled** | `covariate_search.json` |
| [5](#e5) | Per-capita and log-relative transforms | Do covariates fail on scale rather than content? | No — **and log-relative exposed an estimator bug that now ships as a guard** | `percapita_search.json`, `logrel_search.json` |
| [6](#e6) | Highway access | Is buildability the missing covariate? | Best of six declared specs: +0.33 pp, better on 19 of 50 splits | `highway_access.json` |
| [7](#e7) | Gravity vs proximity | Whole-network pull, or nearest-facility distance? | **Depends on k.** Loses top-10, wins top-1, top-5 and Brier | `gravity_network.json` |
| [8](#e8) | The dispersion regularity | Can you tell in advance whether a covariate will work? | Asymmetrically. Low cv ⇒ failure (7/7); high cv ⇒ not sufficient (9/14) | `gravity_network.json` |
| [9](#e9) | The leakage audit and the decisive test | Does the one working covariate contain its own outcome? | **79% retention, 50 of 50 splits, on 29 decisions** | `leakage_test.json`, `leakage_decisive.json` |
| [10](#e10) | The GBM benchmark | Is the ceiling the data, or the model's form? | Data, with a small model term. **`headline_split` is not quotable** | `gbm_benchmark.json` |
| [11](#e11) | White space / unserved demand | Predict openings by ranking the unserved? | 14 of 108 cells, 0 significant wins against 32. Amazon densifies | `white_space.json` |
| [12](#e12) | Catchment radius sensitivity | Does 15 miles carry the hazard result? | No. The sample moves 3.6×, the conclusion not at all | `catchment_band.json` |
| [13](#e13) | The hazard model and its revival | Will a station open in this ZIP this quarter? | Retired on the unit of analysis; **6.7× the events does not touch it** | `hazard_revival.json` |
| [14](#e14) | The pre-registered metro-entry test | Which *metro* gets the next station? | **H0** on every arm × form. 0 of 7 years beaten a households baseline | `metro_entry.json` |
| [15](#e15) | Subsidies, line-haul saving, data coverage | Three smaller questions | All negative, each for a different reportable reason | see §15 |
| [16](#e16) | Data acquisition — six ways to build the target variable | Where does a panel of dated delivery stations come from? | Five failed. The survivors are LLM-assisted labelling and an OCR pass graded at **94.71%** | `mwpvl_extraction.json`, `mwpvl_validation.json`, `satellite_dates.csv` |

---

<a id="e1"></a>
## 1. Five panel compositions × three algorithms

**Asks.** The panel went 104 → 693 rows by OCR of an industry census. Did that buy
ranking accuracy, and does the answer depend on the learner?

**Tested.** Five compositions through one `E_operating_by` edit, three algorithms each,
50 paired re-splits, seed 20260914, 60/40 over decisions, every method refitted inside
every repeat. `original_only` (100 facilities → 94 decisions), `mwpvl_only` (587 → 389),
`mwpvl_clean` (dated **and** `mwpvl_vouched`, 415 → 360), `combined` (687 → 483),
`combined_plus_network` (+3 network columns, 483).

**Result.** `panel_experiments.json` — **no `run_id`**, mtime 2026-09-15 13:37:43.
Large-metro (J > 100) top-10 lift against the analytic `min(k,J)/J` null:

| arm | cond. logit | gbm stump/200 | gbm deep/300 |
|---|---|---|---|
| `original_only` | **6.1804** | 7.0414 | 4.9940 |
| `mwpvl_only` | **6.5257** | 6.2322 | 5.1280 |
| `mwpvl_clean` | **6.7791** | 6.2275 | 5.3780 |
| `combined` | **6.2585** | 6.4097 | 5.5224 |
| `combined_plus_network` | **6.2903** | 6.4574 | 5.8248 |

All fifteen cells span **2.4862 to 3.0830** standardised to `combined`'s size mix. Three
measures disagree and that is the finding: `combined` wins coefficient precision (the
`warehousing_establishments` spread narrows monotonically in n — 1.565 → 0.789 → 0.745 →
0.534, no inversion); `mwpvl_clean` wins prediction; **Brier cannot rank the arms at
all**, since it averages over alternative rows and the denominators run 11 715 to 86 682.
The repair — a skill score — is forbidden by `MODEL_SPEC.md` §9.1 on Gneiting & Raftery
(2007) §2.3 p. 362.

**Does not support.** Not "no learner can predict Amazon siting" — the ceiling is on
*seven columns for these panels*. Not "cleaning MWPVL rows buys precision": the spread
**widens** 0.745 → 0.789 and the earlier claimed narrowing is withdrawn. Not that
`mwpvl_clean`'s edge is cleanliness rather than age. And never a pooled lift across arms
— they hold different size mixes, a Simpson trap this project has hit twice.

Notes: [`research/NOTES_PANEL_EXPERIMENTS.md`](research/NOTES_PANEL_EXPERIMENTS.md).
Code: `src/siting_atlas/models/panel_experiments.py`.

---

<a id="e2"></a>
## 2. The expanded refit — was it sample size?

**Asks.** Declared in the module docstring *before* the run: "the thing to read is not
which top-10 is higher. It is whether the coefficient intervals finally exclude the
numeraire."

**Result.** `refit_expanded.json`, `run_id 20260915-195645-1f05`, 50 repeats.

| | `original_104` (100 fac / 94 dec) | `expanded_658` (687 / 483) |
|---|---|---|
| top-10 rate / Brier | 0.5421 (sd 0.0715) / 0.0075504 | 0.5196 (sd 0.0273) / 0.0050363 |
| `warehousing_establishments` | **1.5282 [0.9850, 2.5497]** | **1.1912 [0.9558, 1.4901]** |
| `establishments` | 0.0021 — boundary | 0.2991 [0.0223, 0.7117] |
| `land_area_sqmi` | 0.0380 [2.2e-20, 0.2611] | 4.0e-16 — boundary **50 of 50** |

Bought: a 66% narrower spread, and `establishments` off the boundary. Did not buy: any
coefficient crossing 1.0. **Five times the sample and the point estimate walked towards
the numeraire, 1.53 → 1.19.** Cost: 204 of 687 facilities never reach the fit (21 no
panel ZCTA, 136 no numeric `open_year`, 47 no strictly-earlier CBP vintage).

**Does not support.** The arm key `expanded_658` is stale; the data is not — quote
`facilities`. And this is **not** a clean leakage test: 389 of 483 decisions are MWPVL
rows dated off a stated opening and 94 sit on the OSHA bound, so the arm is a mixture
and the 1.53 → 1.19 fall is only *consistent with* contamination.

Notes: [`research/NOTES_EXPANDED_REFIT.md`](research/NOTES_EXPANDED_REFIT.md).

---

<a id="e3"></a>
## 3. Fifteen covariates, and the permits stage

**Asks.** The data ceiling was measured on four columns; `panel.parquet` has fifty. Does
a buildability covariate beat another agglomeration covariate?

**Result.** `covariate_search.json`, `run_id 20260915-235210-ff92`, `facilities: 687`,
seed 20260914, 50 paired re-splits. **The `run_id` is not a version marker** — the
emitter reads its own artefact back in and the previous stamp shadows the fresh one;
check `facilities: 687` and `stage_ledger`. `core` frame: 477 decisions, 191 held out,
21 768 frame ZCTAs, chance rate 4.903%. Baseline **30.473% / 6.2157×**; floor
`no_warehousing` **13.132% / 2.6785×**, so the one live covariate is worth **17.372 pp**
and loses 0 of 50.

| Δ large top-10 rate (W-T-L) | covariate, and why it fails |
|---|---|
| **+0.038 pp** (3-45-2) | `traffic_proximity` — best of fifteen; county grain, 9.2 distinct values per metro |
| −0.014 (7-36-7) | `annual_payroll` — r = 0.654 with `establishments` |
| −0.219 (2-36-12) | `in_labor_force` — not identified, 82% of splits at the *upper* boundary |
| −0.580 (6-20-24) | `employment` — actively harmful; r = 0.834 with `establishments` |
| **−0.903** (1-15-34) | `owner_occupied` — worst at top-10; r = 0.880 with households |
| **0.000, 0-50-0** | `diesel_pm`, `low_income_pct`, `people_of_colour_pct`, `median_home_value`, `inv_median_home_value`, `inv_diesel_pm`, `vehicle_availability_total`, `bachelors_degree`, `median_age`, `renter_occupied` |

**Ten of fifteen are exact no-ops**, identical to 15 decimals; the table spans 0.94 pp
end to end and Brier moves at most 7e-6 against a null-to-model gap of 3.3e-4. Three are
not independent tests and the column audit says so: `vehicle_availability_total` **is**
`households` (within-metro r = 1.000, ACS B25044), and
`owner_occupied + renter_occupied = households` exactly — so **thirteen independent
candidates**. Six failures are county values broadcast to every ZCTA
(`county_grain_share = 1.00`). `median_home_value` is the one clean ZCTA-grain
independent candidate (r = 0.019 with households) and is a no-op in both directions.

**Permits**, run as its own stage: 376 decisions, baseline 29.458% / 6.3185×. All four
permit arms and `forward (nested) over permits` are **0.0000, 0-50-0**; `naive best +
permits` is −0.358 pp. The strong form: `permit_units_total` is *off* the boundary on
**96%** of splits (median β 0.178 [0.007, 0.397]) and still moves nothing.

**Does not support.** It does not condemn EJScreen — the verdict is on the panel's
county-broadcast copy, not the tract-grain original. The 50 re-splits are **not
independent**, W-T-L is **not a sign test**, no p-value is computed anywhere, and splits
are not clustered by metro, so every level is optimistic. Every time-invariant column
shares one post-decision vintage (ACS 2019–2023, EJScreen 2024): the *between-arm*
comparison is clean, every arm's *level* — including the published baseline — is not.
And the permit frame is **not a random subsample**: it costs 101 of 477 decisions and
the dropped ZCTAs are systematically smaller on every baseline column (households 3 554
vs 7 908), which makes ranking *easier*, so none of its levels may sit beside `core`.

Notes: [`research/COVARIATES_TRIED.md`](research/COVARIATES_TRIED.md),
[`research/NOTES_COVARIATE_SEARCH.md`](research/NOTES_COVARIATE_SEARCH.md).

---

<a id="e4"></a>
## 4. Nested forward selection — the honest one

**Asks.** Does choosing covariates *inside each training fold* beat adding nothing? The
dishonest version (select on the whole frame) was also run and is labelled optimistic in
the artefact.

**Tested.** The training fold is re-split 75/25; columns are selected on the inner
validation **mean log-likelihood per decision** (not top-k — `MODEL_SPEC.md` §9.3, Train
§3.8.1 p. 69); the winner is refitted on the full training fold and scored once on the
untouched test fold. 36 subsets examined, not 2¹³ = 8 192.

**Result.** `covariate_search.json` `core.arms["forward (nested, honest)"]`:

```
  large-metro top-10 rate   30.473%  ->  29.852%   = -0.6201 pp
                            50 re-splits, 5 wins / 19 ties / 26 losses
  pooled top-10 rate        52.419%  ->  52.775%   = +0.3560 pp  BETTER
```

Selection frequency: the four baseline columns 50/50 each, then `employment` 43,
`owner_occupied` 34, `in_labor_force` 24, nothing else above 6. **The three columns the
fold picks most are the three most collinear with the baseline.**

**The stratum must always be named.** The sealed pre-registration quotes this as
"**0.72 points WORSE**" with no stratum;
[`PREREG_METRO_MODEL_ERRATA.md`](PREREG_METRO_MODEL_ERRATA.md) Correction 1 fixes it.
The magnitude has settled at −0.62 pp and the pooled contrast has *grown* from +0.08 to
+0.36 pp; the sign and the stratum-specificity both survived the re-run.

**The substitution test, which closes the circularity escape route.** Best searched set
*without* `warehousing_establishments`: 19.527% / 3.9830× — it recovers **6.408 of the
17.372 pp = 36.9%**, loses 50 of 50, and at top-1 is 3.80× against 10.31×. **There is no
free replacement for the audited covariate.**

---

<a id="e5"></a>
## 5. Two transforms: per-capita, and log-relative

**Asks.** Do the covariates fail because of *scale* — everything is a headcount in
disguise — rather than content? Divide by households; or express each ZCTA in logs
relative to its metro's median.

**Per-capita.** `percapita_search.json` — **no `run_id`**, mtime 2026-09-14 20:13, run
on the superseded 694-facility / 479-decision frame (baseline 6.3889), so **its levels
may not sit beside the current `core` baseline of 6.2157**. The transform does exactly
what it was meant to: within-metro correlation with households falls from
0.9815 → 0.1122 (`in_labor_force`), 0.8803 → 0.1582 (`bachelors_degree`),
0.9091 → −0.3683 (`owner_occupied`). And it buys nothing — **six of the eight added
columns are exact no-ops** (0.000, 50/50 ties, β at the boundary on 68–100% of splits)
and the other two, `employment_per_hh` and `annual_payroll_per_hh`, manage −0.019 pp
each. *(This read "seven … and the eighth" until 2026-09-16; the artefact's
`vs_baseline_large_top10` gives two arms at −0.00019 and six at exactly 0.)* The
*level* versions were harmful (−0.12, −0.18, −0.05
lift); the *rate* versions are inert. **The collinearity was real and it was not hiding
anything — the failure was over-determined.** A separate swap arm
(`warehousing_establishments_per_hh` **instead of** the count) retains **81.6%** of the
covariate's value but loses 41 of 50 and is worse than dropping the covariate entirely
on the declared headline metric (Brier 0.005407 vs 0.005371 vs baseline 0.005227).

**Log-relative, and the estimator bug.** `logrel_search.json` — **no `run_id`**, mtime
2026-09-14 20:42, 41 re-splits (not 50 — see below). On prediction: nothing. On the
estimator: `choice.py` enforces `β′a > 0` by writing `β = exp(θ)`, which holds only while
every attraction column is non-negative — and a log-relative column is negative on ~half
its rows, so a *positive* coefficient on a *negative* column **subtracts** attraction.
`logrel_frame.bound` computes the exact feasibility ceiling; five of ten arms fitted
**19.55× to 77.19× past it**, pushing 765 to 4 816 non-chosen alternatives below zero for
log-likelihood gains up to **+1.20**. Because the chosen alternative is never one of them
(`negative_and_chosen` = 0 in all ten arms), the negative rows simply shrink their metro's
denominator and inflate `P(chosen)` from 0.078685 to 0.079346. **The optimiser bought
likelihood with arithmetic, and nothing complained.** The tell is five for five: for each
column one direction went to machine zero and the other produced a coefficient, and **the
direction that "worked" was always the one with the lower ceiling.** The 50-split run also
crashed at repeat 42, when enough alternatives went negative that a metro total reached
zero. **The experiment is retired; the guard it produced is live** —
`choice.py:299-334` now raises if the optimum puts `β′a ≤ 0` anywhere.

**Does not support.** Every `_per_hh` and log-relative column is **intensive**, and
`V = ln(β′a)` is justified by Train §3.4 Example 2 only because attractions *add* across
a zone merger; a rate averages. These arms are a positive-weight ranking function
resembling a conditional logit, not a destination-choice model in `MODEL_SPEC.md` §1's
sense. The positivity constraint is also *not* the explanation for these columns: seven
of ten log-relative arms were boxed in below 0.65% of the numeraire, but **three had room
comparable to `establishments` and went to machine zero with ΔLL of exactly +0.000000**.
And `logrel_search.json` is **no longer reproducible against current `choice.py`**, which
would raise on five of ten arms.

Notes: `experiments/percapita-logrel/notes/`. Both were corrected on 2026-09-16 —
`NOTES_PERCAPITA.md` §8 recorded four arms as unfinished and now records the finished
run (`arms_unfinished: []`, all eleven arms at 50 re-splits), and
`NOTES_LOG_RELATIVE.md` §6 said the positivity guard was "recorded here, not
implemented" and now records that it shipped at `choice.py:299-334`, together with the
consequence that its own artefact no longer reproduces against current code.

**Neither artefact will be re-run.** Both sit on the superseded 694-facility /
479-decision frame with a 6.3889 baseline, against `covariate_search`'s current `core`
baseline of **6.2157** on 477 decisions / 687 facilities. They are retired evidence: a
delta against each file's own baseline carries across, a level does not. Any document
printing a number from either one beside a `covariate_search` number must say so.

---

<a id="e6"></a>
## 6. Highway access

**Asks.** Six specifications of freeway access, all declared before the result, on the
stated prior that nine covariates had already failed.

**Tested.** Extensive (what `ln(β′a)` wants): `interchanges`, `interstate_miles`,
`primary_road_miles`. Intensive, and labelled so: `highway_access` = 1/(1 + km to the
nearest interchange), `interstate_access`, `interchange_decay` = exp(−km/5). **Two decay
shapes rather than one, "because the shape is an assumption and reporting whichever of
the two did better would be choosing the answer."** Plus a seventh combining arm.

**Result.** `highway_access.json` — **no `run_id`**, mtime 2026-09-15 13:11. Own frame:
479 decisions, 13 779 frame ZCTAs (40.8% retention), baseline 6.4477 / 31.406%.
`+ interchanges` **6.5148, +0.329 pp, better on 19 of 50** (the combining arm is identical
to it); `+ highway_access` −0.001; `+ interchange_decay` exactly 0.000;
`+ interstate_access` −0.053; `+ interstate_miles` −0.037; `+ primary_road_miles` −0.226.
Same shape as `traffic_proximity`, only larger.

**Does not support.** Its frame retains only 40.8% of panel ZCTAs, so the levels are not
comparable to `core`. The module also works around a real `choice.fit` defect — a NaN
from the first optimiser start could never be displaced — by dropping non-finite splits
from that arm only; `non_finite_fits` is empty on this run.

---

<a id="e7"></a>
## 7. Gravity versus proximity

**Asks.** Nearest-facility distance throws away every facility but one; a radius count
throws away every distance. `G_i(α) = Σ_j mass_j / (1 + d_ij)^α` over facilities already
open at decision time keeps both.

**Tested.** 13 arms on one build — `decision_sets_identical: true`,
`sliced_arm_equals_rebuilt_arm: true` — 483 decisions, 86 682 alternatives, 50 re-splits.
Decay α ∈ {1,2,3}; masses `count`, `sqft`, and `count_sqft_subset` (**the control**:
mass 1 on exactly the facilities `sqft` uses, so weighting and subsetting can be told
apart). Sortation and fulfilment are separate columns. α = 0 was deliberately not run:
`(1+d)^0 = 1` is constant within a choice set — not a weaker test but not a test.

**Result.** `experiments/gravity-network/artefacts/gravity_network.json`,
`run_id 20260915-210603-b780`. Large-metro top-10 lift: `no_network` (floor) **6.2585**,
`proximity_published` (baseline) **6.2903**, `proximity_only` 6.2823, `gravity_count_a3`
(best fully-interior gravity arm) **6.2187**. Paired over the same 50 re-splits,
`gravity_count_a3` vs `proximity_published`: top-1 **+0.011606** (42 improved / 4
worsened), top-5 **+0.012642** (44 / 2), top-10 **−0.000207** (18 / 22), Brier −1.386e-05
(40 / 10). **Do not quote a single scalar** — it loses at k = 10 and wins at k = 1, k = 5
and Brier, and the paired sd at top-10 is 0.0123, sixty times the paired mean.

**It won on measurement.** `gravity_count_a3` is the only specification with both columns
interior in all 50 re-splits; offered both families at once the model **keeps gravity and
discards nearest-distance** (`sortation_proximity` 0.1039 → 0.0171, 4/50 → 28/50 at the
boundary; `fulfilment_proximity` 0.1868 → 0.0296, 0/50 → 22/50). On square footage, **the
cost is the subset, not the weighting**: at α = 3, count 6.2187 → `count_sqft_subset`
6.1033 → `sqft` 6.1511, so restricting to the 435 facilities with a stated area costs
0.115 of lift and size-weighting the restricted network recovers 0.048. Without the
control the natural — and wrong — reading would be "size does not matter".

**Does not support, and what it costs.** `aggregation_invariance_cost`, verbatim: *"A
gravity term is NOT EXTENSIVE: merging two ZCTAs does not add their attractions, so the
zone-merger invariance MODEL_SPEC.md §1 buys from Train §3.4 Example 2 — the entire
justification for the `ln(β'a)` form — does not hold for any arm in this file except
`no_network`."* Gravity adds a wrinkle bounded proximities do not have: its **level**
grows with the network (fulfilment α=1 mean 0.1204 in 2017 → 0.4269 in 2030), and in a
share model a shift common to a choice set flattens the distribution rather than
cancelling. That cost is **declared but not measured for gravity**; it *is* measured for
the published proximity arm (`network_inference.json`, `20260915-210640-dbcd`): 43 224
merged pairs, median absolute relative probability error **0.04356**, max 0.45493, against
an extensive-only control of exactly **0.0**. Nor are the proximity columns safe: under a
500-replicate metro-clustered bootstrap `sortation_proximity` is β 0.097 [3.0e-14, 0.247],
3.8% of replicates at zero. And only 351 of the 556 placeable non-DS facilities ever enter
a column.

Notes: `experiments/gravity-network/notes/NOTES_GRAVITY_NETWORK.md`.

---

<a id="e8"></a>
## 8. The dispersion regularity

**Asks.** Can you tell, before fitting, whether a covariate will work?

**Result.** `gravity_network.json` `terms.dispersion`, at vintage **2030**, over the
**41 metros with ≥101 candidate ZCTAs (8 271 ZCTAs)**. Statistic: mean within-CBSA
`sd/mean`. Twenty-one terms carry one; boundary state read from
`arms.<arm>.verdicts.<col>.state` in the arm where each is fitted:

```
  cv < 0.6       7 terms (0.2975 - 0.5918)    0 interior    7 not interior
  0.6 - 1.3      0 terms                      THE BAND IS EMPTY
  cv > 1.3      14 terms (1.3993 - 8.5046)    9 interior    5 not interior
```

> Low within-metro dispersion is **sufficient for failure** — every term with cv < 0.6
> (7 of 7) lands at the coefficient boundary. High dispersion is **necessary but not
> sufficient for success** — 9 of the 14 above 1.3 are interior; the 5 that are not are
> all sortation-side, four of them square-footage masses.

Mechanism: at α = 1 the sum is dominated by hundreds of distant facilities, giving a
smooth continental gradient nearly constant inside a metro. This is §3's county-broadcast
failure reached from the other direction, on a covariate family whose grain is a
**tunable parameter**.

**Does not support.** Nothing about intermediate dispersion — nothing was observed between
0.6 and 1.3. No two-way rule: a low reading rules a variable out, a high reading does not
rule it in. And it is **descriptive, not estimated**: n = 21 non-independent terms (each
is one of two columns in one of 13 arms over the same 483 decisions) from **one run at one
vintage**. A cv without its vintage is not a quantity, and anything resting on
`boundary_census` alone covers 5 of the 21 terms. The sealed pre-registration states the
rule symmetrically as "21 of 21" both ways;
[`PREREG_METRO_MODEL_ERRATA.md`](PREREG_METRO_MODEL_ERRATA.md) Correction 2 fixes it.

---

<a id="e9"></a>
## 9. The leakage audit, and the decisive test

**Asks.** The one working covariate counts warehouses in a ZCTA. **An Amazon delivery
station is itself a warehousing establishment.** Does the covariate contain its own
outcome?

**The audit.** `cbp_detail.py` already refuses any CBP vintage not strictly earlier than
`open_year` — but for 104 of 104 national rows `open_year` is the quarter of the
**earliest OSHA inspection**, an upper bound, measured at a **median 34 months late**
(mean 38, p75 54, max 89; 88% over a year) across 42 linked buildings. **⚠ Those lag
figures have no artefact**: `models/leakage_dates.py:9` cites the notes file as their
source, which is circular. Prose-only, hand-measured.

**The ablation.** `leakage_test.json`, `run_id 20260915-195832-4275`, 50 repeats:
`with_warehousing` **20.60** of 38 (n = 94) against `without_warehousing` **12.90**
(n = 100), difference **+7.70 hits**, 50 W / 0 L. **It cannot answer the question, and
the artefact says so** in `what_this_cannot_show`: *"An ablation cannot distinguish
contamination from genuine agglomeration. Both imply the covariate predicts. Only a CBP
vintage measured before every opening separates them."* The two arms also hold different
decision counts and different nulls, so the "+7.70 paired" spans two samples.

**The decisive test.** Three arms, one seed, 50 paired re-splits, **all restricted to the
same 29 decisions**: `osha_bound`, `true_date` (vintage off the stated opening year,
nothing else changes), `no_covariate`. Reaching the 29: 100 decisions with no industry
covariate → 94 with a vintage before the OSHA bound → **29 with a stated opening date and
a vintage before it**. **65 of 94 working decisions lost — 69%**, leaving 12 test
decisions and 5.7 events per parameter against a floor of 10. `leakage_decisive.json` —
**no `run_id`, no `written_at`**, only `seed: 20260914`; mtime 2026-09-14 13:54.

```
  arm            top-10 hits of 12   sd      vs no_covariate
  osha_bound              9.24      1.001    +4.76,  50 W / 0 L
  true_date               8.22      1.036    +3.74,  50 W / 0 L
  no_covariate            4.48      1.249    --      (uniform null 2.12)
```

**Retention = 3.74 / 4.76 = 78.6%, reported as 79%.** Moving to the contaminated vintage
buys 1.02 hits of 12, with 13 of 50 splits showing no difference. Two supporting
measurements: the **price of an establishment barely moves** — each β divided by its own
column mean (1.40983 vs 1.23849) gives a ratio of **1.01197**, so the column changed and
the coefficient did not; and a **model-free self-count check** finds the chosen ZCTA
gaining +1.1724 establishments between vintages against +0.1275 for the average
alternative, an excess of +1.0449 with a **median of 0.00**, carried by a minority.

**Does not support — six stated limitations.** (1) **The leak and the staleness are one
intervention**: `true_date` reads a vintage older *as well as* cleaner (median 2.0 years),
so +1.02 is an **upper bound** on the leak, not a measurement of it. (2) The 29 are **not
a random subsample** — `osha_bound` scores 77% here against 54% on the full 94, so nothing
transfers to the other 65. (3) **14 of 29 stated dates come from an MWPVL table for a
different facility class**; the DS-only sensitivity is 15 decisions and settles nothing.
(4) **Nothing was corrected** — two stated dates are *later* than the OSHA bound, which
`E_operating_by` calls impossible, and they are used as stated, because dropping the
inconvenient pairs is how a leakage test is rigged. (5) A percentile interval over
re-splits is not a standard error. (6) 5.7 events per parameter.

**Verdict as written:** in between, and much closer to agglomeration than to leakage —
genuine agglomeration *audited on 29 decisions*, with a ~20% haircut of unknown split
between self-counting and staleness.

Notes: [`research/NOTES_COVARIATE_LEAKAGE.md`](research/NOTES_COVARIATE_LEAKAGE.md),
[`research/NOTES_LEAKAGE_DECISIVE.md`](research/NOTES_LEAKAGE_DECISIVE.md).

---

<a id="e10"></a>
## 10. The GBM benchmark

**Asks.** Is the conditional logit held back by **the data** or by **its own simple
form**? `MODEL_SPEC.md` §9.4: *"A structural model with nothing to lose to has never been
tested."*

**Tested.** LightGBM `LGBMRanker`, `objective="lambdarank"`, groups = decisions. Six
configurations reported in full and never collapsed to a winner — stump (2 leaves / depth
1 / 200 trees / lr 0.10), small (4/2/100/0.05), deep (8/3/300/0.05) — each on raw `levels`
and on `shares`. National frame, 94 decisions, 38 test, 50 repeats, seed 20260914; repeat
0 is bit-identical to `choice_runner`'s split.

**Result.** `gbm_benchmark.json`, `run_id 20260915-200312-1d51`. Quote `across_repeats`:

| method | top-10 of 38 | sd | mean Brier | vs raw_count |
|---|---|---|---|---|
| `gbm stump/200 levels` | **22.26** | 2.75 | 0.007681 | +1.30, 30/11 |
| `gbm small/100 levels` | 22.18 | 2.64 | 0.007782 | +1.22, 34/10 |
| `raw_count` | 20.96 | 2.50 | 0.007793 | — |
| `conditional_logit` | 20.60 | 2.72 | **0.007550** | −0.36, 11/23/16t |
| `gbm deep/300 levels` | 18.76 | 2.48 | 0.010392 | −2.20, 10/36 |

Gain importance: `warehousing_establishments` 0.535, `land_area_sqmi` 0.185, `households`
0.143, `establishments` 0.137 — **the tree takes 32.2% of its split gain from exactly the
two columns the logit drove to the boundary**, which is the model-ceiling term. Answer: **a
data ceiling with a measured, small model-ceiling term.** The learner wins **one of four**
reported quantities, losing 1.2–1.6 hits at top-1 and losing the Brier, the declared
headline. Quintupled to the 483-decision `combined` arm the edge **disappears**: GBM
top-10 rate 0.51979 against the logit's 0.51959.

**Does not support — the headline split is not a quantity.** The artefact carries its own
`headline_split_warning`: multiplying the attraction matrix by
`(1 + 1e-12 × standard normal)` — about what a parquet float round-trip costs — moves the
single-split GBM top-10 by **up to 2 of 38**, while the conditional logit (19) and raw
count (20) **do not move in any draw**. `deterministic=True, force_row_wise=True` were
tested against every arm and returned **bit-identical counts in all eight comparisons**:
the call was already reproducible on identical input; the sensitivity is to the *data*.
**Any document quoting single-split GBM counts (24, 23, 20, 18 of 38) is quoting noise.**
This is also where "a raw count **beats** the fitted model" was corrected to **"matches"**
— −0.36 top-10, paired sd 1.1386, 11 W / 23 L / 16 ties.

Notes: [`research/NOTES_GBM_BENCHMARK.md`](research/NOTES_GBM_BENCHMARK.md).

---

<a id="e11"></a>
## 11. White space — unserved demand

**Asks.** Rank the places Amazon does *not* serve by household demand. Does that predict
where it builds next?

**Tested.** A ZCTA is covered when its centroid is within the radius in straight-line
great-circle miles of at least one facility — the same geometry `warehouse/facilities.py`
uses for the `enabled` target. Two coordinate sets, never averaged, because the 72.3%
geocode match rate is **not missing at random** (hand rows 83.7%, OCR'd rows 70.3%):
`real` (501 geocoded DS + 785 centroid-only support sites) and `real_plus_fallback`
(690 + 785). Radii 8.3 / 12.7 / 15.0 / 19.6 / 25.0 / **45.0**, plus a 60.0 over-run probe.
**45.0 is the headline because it is the only radius with an external source** — MWPVL
states delivery stations are "designed to service a 45-mile radius".

**Result.** `white_space.json` — **no `run_id`**, mtime 2026-09-15 13:24:50. A *cell* is
one (coordinate arm × radius × level × top-N cut-off) comparison against a households-only
baseline on the same held-out openings, tested with a two-sided exact **McNemar** on the
discordant pairs.

```
  cells scored 108   white space wins 14 (13%)   baseline wins or ties 94
  p < 0.05 for white space 0        p < 0.05 for the baseline 32
```

Twelve of the fourteen wins are ZCTA-level, thirteen are in the fallback arm, none is
significant; at metro level white space loses by 20 to 48 points.

**The densification backtest — the finding worth keeping.** Coverage from facilities
opened 2023 or earlier (undated rows excluded, since an undated row could be a 2025
building), scored on 2024–25 openings. At the headline 45 miles, **68.7%–75.9% of openings
land inside coverage the pre-2024 network already had**: 75.9% = 60 of 79 on real
coordinates, 68.7% = 90 of 131 with ZCTA-centroid fallbacks; median distance to the nearest
pre-cut facility 7.5 mi / 10.1 mi. **That range is across coordinate sets at one radius,
not across radii** — 67.1% is `real` at **15** miles, and the full grid runs 45.0%
(fallback, 8.3 mi) to 75.9%. See
[`PREREG_METRO_MODEL_ERRATA.md`](PREREG_METRO_MODEL_ERRATA.md) Correction 3.

**Why it failed, diagnosed rather than asserted.** Five rules raced on the same hold-out;
`demand_in_radius` is `coverage_gain` with the coverage mask removed and nothing else
changed. At metro level, N = 25: the **mask** costs 13.9 to 24.0 points; the **spatial
smoothing** the rule shares with its own control costs −6.3 to +0.8, i.e. it is free or
helpful. Remove the mask alone and the whole gap returns (6.3% → 46.8% at real / 45 mi /
N = 100). **Excluding served places is the defect — not the idea, not the smoothing.**

**Does not support.** Two rules do out-score the baseline at 15 miles —
`load_per_facility` (which *weights* by service intensity instead of *excluding* served
places) and `demand_in_radius`. But `rules_that_beat_households_everywhere` is an **empty
list**, and the artefact's multiplicity guard reports 128 post-hoc paired tests on one
hold-out, 6.4 significances expected by chance, 9 observed in favour of an alternative rule
against 62 in favour of the baseline. **Those cells are a hypothesis for a fresh hold-out,
not a finding.** One un-geocodable row also moved a metro: the Census geocoder returned
`No_Match` for Amazon's Dorado PR station, which is why San Juan is the `real` arm's top
unserved metro at 797 364 households.

Notes: [`research/NOTES_WHITE_SPACE.md`](research/NOTES_WHITE_SPACE.md).

---

<a id="e12"></a>
## 12. Catchment radius sensitivity

**Asks.** `CATCHMENT_MILES['DS'] = 15.0` is an engineering estimate with no published
source, and the stated justification does not reproduce it (at the project's own 22 mph
and 1.30 circuity, 30 minutes is 8.46 miles; getting 15 needs 39 mph). Does the hazard
conclusion depend on it?

**Tested.** Seven radii, six inside a band anchored on external evidence: **8.3** (45-min
congested drive), **12.7** (cost baseline), **15.0** (the code), **19.6** (fast end of the
Monte Carlo ranges), **25.0** (Holmes 2011 / HNS 2023), **45.0** (MWPVL prose), plus
**60.0** as an out-of-band probe. Before any point was trusted: 27 914 enabled cells
recomputed against the panel over all 1 081 312 cells with **0 mismatches**, six recorded
radii re-measured exactly, and the 15-mile fit reproducing `hazard_report.json` to the
digit.

**Result.** `catchment_band.json` — **no `run_id`**, mtime 2026-09-14 15:40. AUC runs
0.7081 (8.3 mi) / 0.6689 / 0.6894 / 0.6829 / 0.6406 / **0.6269** (45 mi), on risk sets of
559 to 921 events over 14 121 to 67 216 enabled cells. **The radius moves the sample by
3.6× and the conclusion by nothing.** AUC never reaches the pre-registered 0.80 at any
radius (`auc_at_or_above_0_80_at: []`); the model beats a constant on Brier at every radius
by 0.32%–0.95%; **the constant is better calibrated at every radius**; `households` is
distinguishable from zero at every radius. Two unpredicted findings: `facilities_attached`
is **43 at every radius** (a wider catchment buys replication, never buildings), and the
risk set **shrinks** monotonically, 1 977 → 1 076 units, because a wider catchment
left-truncates faster than it treats.

**Does not support.** The one non-robust claim — "exactly one of three covariates
significant", true at 8.3–19.6 and false at 25/45 — is a **sample-inflation artefact**:
coefficients attenuate 25% across the band while p-values fall, because rows rise, the
robust covariance is clustered on only nine CBSAs, and at 45 mi 80.2% of enabled ZCTAs sit
in two or more catchments so the added rows are near-duplicates. Correct headline phrasing:
*AUC 0.63 to 0.71 across every catchment radius the source supports, against a target of
0.80.*

Notes: [`research/NOTES_CATCHMENT_RADIUS.md`](research/NOTES_CATCHMENT_RADIUS.md) — **its
§5 summary table swaps the `low`/`high` radius labels on the AUC and Brier-skill rows**;
the artefact stores those as min/max over the sweep, not endpoint values.

---

<a id="e13"></a>
## 13. The hazard model, and its revival on 6.7× the events

**Asks, v1.** For every ZIP, every quarter: will a station open here now?

**Why it was retired.** Not because it scored badly, but because it broke an assumption no
tuning repairs. **One opening switches on a median of 39 ZCTAs at the 15-mile catchment**,
and the likelihood counts each as independent — Train (2009) §3.7.1, printed p. 61. (Not
§2.2; that citation error is logged as the largest in the project,
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §10.) The retired run's 812 ZCTA-level events
came from between 28 and 38 real decisions plus a circle.

**Asks, v2 — the obvious objection.** The first retirement had 812 events. Was it a
sample-size problem? Seven arms on the expanded panel: MWPVL dates vs OSHA bounds, three /
four / five covariates, and a **matched** pair on the same 130 facilities so the date effect
separates from the facility set. Three hold-outs: by unit, out of time, out of area. An
integrity gate refuses to run if the re-derived target disagrees with the panel on one cell
— 200 219 cells, 0 mismatches.

**Result.** `experiments/hazard-model/artefacts/hazard_revival.json`,
`run_id 20260915-224104-21a7`; the retired baseline in `hazard_report.json`
(`20260914-002509-2374`) was **never overwritten**.

| | retired run | best revival arm |
|---|---|---|
| events | **812** | **5 441** (6.70×) |
| risk-set units / rows | 1 756 / 40 358 | 11 230 / 256 081 |
| events per parameter | 5.6 (floor 10, failed) | 87.2 (cleared) |
| AUC by unit / out of time / out of area | 0.6894 / 0.5551 / 0.6168 | **0.6832** / 0.6323 / 0.7104 |

AUC across all 7 arms × 3 hold-outs: **0.4527 – 0.7515, median 0.6459, 17 comparisons**.
(Four out-of-area runs could not execute and the reason is recorded rather than the row
omitted: **not one of the 139 OSHA-bounded facilities sits in Phoenix or Boise.**)
**The calibration record is the verdict:** the constant null is better calibrated in **17 of
17 comparisons** and `model_better_calibrated_at` is an **empty list**. The date control
finds nothing — only **30 facilities' dates actually move** (100 of the 139 OSHA-bounded
rows had their dates *derived* from the bound), and on the matched 130 the new dates score
AUC −0.0043, marginally *worse*. Better dates also **remove** events, 2 666 against 3 131
on identical facilities, because correcting a date backwards pushes openings before the
panel window.

**Verdict: retirement stands.** `independence_violation`: *"Every standard error in this
file is wrong in that known direction. Clustering the covariance on the CBSA reduces the
damage and does not remove it, because the unit of decision is the building, not the metro
and certainly not the ZIP."*

**Does not support.** The median-39 came *down* from 58 on the pilot frame and the problem
got *worse*: at 58.4% double coverage only the earliest arrival registers an event (median
newly-switched-on is **13**, not 39), so a ZIP's switch-on quarter is a joint function of
several buildings — a second dependence on top of the first. **Only the 39 supports the
independence argument; the 13 is a different quantity.** There is no radius at which one
opening is one observation: the per-opening count never falls below 14 across 8.3–45 mi.

Notes: `experiments/hazard-model/notes/NOTES_HAZARD_REVIVAL.md` (its one-line answer said
"thirteen times the events"; corrected 2026-09-16 to the actual multiplier, **6.7×**).

---

<a id="e14"></a>
## 14. The pre-registered metro-level entry test

**Asks.** The ZIP question failed on the unit of analysis. Move up a level: which *metro*
gets a delivery station next year?

**How the pre-registration worked.** [`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md) was
written 2026-09-15 at 15:49, **before any model was fitted**, and sealed by hash.
`metro_entry.json` records `prereg_md5: 946f7ef75db69e5278eea409a04c3823`; a sealed copy
and hash live in `reproducibility/seals/` and **CI checks the seal on every push**
(re-verified while writing this page — the file still hashes to that value). It fixed the
question, hypothesis, sample, covariates, model forms, the three baselines, the evaluation,
**both outcome paragraphs verbatim**, five invalidating conditions and a numeric success
criterion. **Do not edit it**; corrections live in
[`PREREG_METRO_MODEL_ERRATA.md`](PREREG_METRO_MODEL_ERRATA.md), which records that no
pre-registered clause changed — all three errata are in motivating figures.

**Tested.** CBSA × year, 2018–2025, **all 935 CBSAs** — excluding the 740 with no known
opening would be selection on the outcome. Three baselines: uniform (declared trivial in
advance), **rank by households (the bar)**, rank by facilities already present. Three arms
(`prereg_strict` — the verdict arm, declared at stage 1 — `vintage_clean`,
`vintage_relaxed`) × three forms (logit / poisson / negbin). Primary evaluation is out of
time: fit through t−1, predict t, rolled forward. **Success criterion (§9):** beat the
households baseline on AUC in a majority of held-out years **AND** be at least as well
calibrated as the constant null in a majority.

**Result.** `metro_entry.json`, `run_id 20260915-231322-7d21`, arm `prereg_strict`, form
`logit`:

```
  years won on AUC vs the households baseline    0 of 7     clause 1 FAILS
  years at least as calibrated as the null       3 of 7     clause 2 FAILS

  pooled out-of-time AUC   model 0.7323   households 0.8949   facilities 0.7325
                           year-base-rate null 0.5367    6,545 rows, 306 events
  metro-clustered bootstrap, 2,000 draws, 935 clusters, seed 20260913
                           model - households  -0.1628 [-0.2011, -0.1313]
```

Per-year AUC differences run −0.112 (2021) to −0.271 (2020). **H0 on every arm × form —
nine cells — and H0 also with 2020–21 excluded**, where it gets slightly worse. Two things
the run added that the prereg did not ask for: stratifying by household tercile, **the
pooled AUC exceeds the model's AUC in every tier** (0.4125 / 0.5666 / 0.6961 against
0.7323) — Simpson's paradox in textbook form, with the direction unchanged in all three
tiers, so stratification *strengthens* the finding; and the leakage diagnostic
`vintage_relaxed` — a seven-covariate logistic *containing households*, allowed to see
post-outcome data — still loses to households alone in 6 of 7 years and loses calibration
7 of 7. **Leakage is not holding the model up; the ceiling is the baseline.**

**Does not support — the biggest qualification on H0.** The vintage gate dropped 8 of 12
pre-registered covariates and the coverage floor dropped 2 more, leaving two. Most panel
columns are not time series (mean distinct values per unit across 32 quarters: population,
households, income, traffic, diesel, wages all 1.00), and Census permits cover 24% of
metro-years in 2019–2022 against 97.8% in 2023–25, below the 90% floor. **The Tier 1
mechanism that generated H1 was never testable on this panel.** Four deviations are
recorded in the artefact, including 20 dated facilities with no `cbsa_code`, so the run
found 462 events where the prereg anticipated ~480. One finding cuts *against*
densification: conditional on metro size, `facilities_open_prior` takes a **negative**
coefficient in all seven years. Baseline 3 alone scores 0.73, so the raw correlation agrees
with §11 — but once size is controlled, having facilities predicts *fewer* new ones.

Notes: [`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md), including its own
§12, "Where I think the prereg is wrong", written after the result.

---

<a id="e15"></a>
## 15. Three smaller experiments

**Subsidies — the disclosure is too coarse, and that is the finding.** `subsidies.json`
(**no `run_id`**). Good Jobs First Subsidy Tracker, Amazon parent, downloaded 2026-09-14
for USD 25: 576 records, $16.06bn, 2000–2026. **30 records carry a postcode** and 86 a
street address; 414 name only a county, and only 16 of the project's 538 facility cities
overlap the 80 subsidy cities (**3.0%**). `what_this_cannot_support`: *"Facility-level
attribution… Any statement of the form 'facilities like yours received X' is unsupported by
this file."* This is the best case for public transparency — a nonprofit consolidating
legally mandated disclosure — and it still cannot price a building. Set beside MWPVL that
is a pair: **commercial network data is withheld because it is worth money; mandated
subsidy data is published and still too coarse to act on.** Megadeals are split by class
rather than winsorised, because a data-centre award is not an outlier in a delivery-station
distribution, it is a different population.

**Line-haul saving — the experiment that could not be run.** `models/accessibility.py`
computes `saving(c) = Σ_j parcels_j × max(0, min(d_j_now, 25) − d(j,c))`, where `d_j_now`
is the distance to the nearest depot that **already existed when the decision was made** —
the greedy step of the p-median heuristic evaluated one candidate at a time, on a real
prior network rather than a solved optimum, so it cannot be accused of being the project's
own cost model predicting itself. The coefficient comes back at 0.0000 with held-out top
1/5/10 identical at 7/16/19 — **but 65 of the 100 national facilities are the first Amazon
facility in their metro**, and for those the prior network is empty and the formula
degenerates to demand-weighted centrality, the population measure it exists to escape. Its
distinctive content was available for 35 decisions, and after a 60/40 split for ~14. **The
defensible statement is "we could not test this properly with this panel", not "position
relative to the existing network does not matter."** The code is kept, tested, switched off.

**How much of the network public data can see.** `mwpvl_coverage.json` (**no `run_id`**):
488 cities where MWPVL lists an Amazon **delivery station**, 340 where OSHA ever inspected
**any** Amazon facility class, 138 in both — so OSHA has a record in **28.3%** of the 488
and 350 are invisible to it. Two qualifications travel with it: the comparison is
**conservative** (OSHA's side is unrestricted by class, so narrowing it would widen the
gap) and it is a **floor, not an estimate** — a two-list intersection, not
capture-recapture. The modelled version is `nlrb_coverage.json`: two-list Chapman 630
cities / **54.0%** coverage (an upper bound), Chao lower bound 899 / 37.8%, and a
three-list log-linear model over ten states using OpenStreetMap as a third list whose
capture mechanism is unrelated to worker grievance. **Dependence is measured, not
assumed** — conditional odds ratios 1.72 to 3.82, all positive, which is why every
population figure is a lower bound and every coverage figure an upper bound.

*The data-acquisition attempts that used to sit here — satellite dating, the labelling
programme and the abandoned SEC route — have moved to §16, where they are written up
alongside the four methods that preceded them and the OCR pass that ended the problem.*

---

<a id="e16"></a>
## 16. Data acquisition — six ways to build the target variable

**Why this is on the page at all.** Every experiment above is fitted on a panel of dated
delivery stations, and no public source publishes one. Building it was the longest and
most expensive strand of work in the project, it was run the same way — a declared
question, a method, a measured answer and a rule for stopping — and five of its six
methods returned a negative. Provenance:
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md); artefacts in
`data/collection/`, 47 files that ship; the source entry is
[`DATA_SOURCES.md` §17](DATA_SOURCES.md). Also
[`DECISION_LOG.md`](DECISION_LOG.md) §2.13–2.14.

> **A count to fix while quoting it.** The provenance document heads its list *"The five
> failures"* and then enumerates four (§3.1–3.4); its own summary §18 says *"Four
> attempts … failed. The fifth attempt works."* Four is right for that list. The fifth
> failure is the satellite programme in §16.2, which was run later and is written up
> separately — **six methods attempted, five negative**.

### 16.1 The four routes tried before labelling worked

**Asks.** Is there a public route from "an Amazon building is at this address" to "it is a
delivery station, and it opened in year Y"? Each route is recorded because it rules out a
question a reader would otherwise ask as *"why didn't you just…?"*

**Tested, and what came back.**

| Route | Result |
|---|---|
| Scrape `hiring.amazon.com`, where the job title names the building type | Delivery stations are staffed by **Delivery Service Partner contractors, not Amazon employees**, so they barely appear. A 50-mile Chicago search returned 7 jobs, all fulfilment or sortation, **none at a delivery station**. Structural, and it will not change |
| Take the oldest Google Maps review as a lower bound on the opening | Does not scale (500+ reviews, no paginated sort-by-oldest), and fatally, **Google merges listings for successive tenants at one address** — the oldest review can be evidence about the previous occupant and nothing on the page says so |
| Ask a language model to web-search an opening date, given a city | ~60 queries produced 4 dates, **one a genuine opening**; the rest were announcements and lease signings. An earlier pass **fabricated 33 of 35 dates**, every row citing the same URL, which supported none of them |
| MWPVL's public network table as the frame | It is an **April 2012 snapshot**. Of 202 OSM-harvested candidates, exactly **4** appear in it — PHX3, PHX6, PHX7, BFI1 — and **all four are fulfilment centres**. Zero delivery stations |

**The transferable result is the third row, and it is about shape, not accuracy.** The
fabricated output was *uniformly plausible*: 35 rows, every one carrying a year, a quarter
and a URL, no hedging and no gaps. **A dataset with no missing values, produced by a
process that should have produced many, is evidence of fabrication rather than of
diligence.** Two checks caught it — a known answer planted in the list (Chicago 60628
opened Oct 2020 per a chicago.gov release; the model returned 2024 Q3) and a second source
on the same facility. The honest redo, `data/collection/results/DATES_FOUND.csv`, returned
**15 of its 35 rows with no date at all**.

**Does not support.** Three of the four rows above have **no artefact**: the provenance
document's §17 files the 7 jobs, the "500+ reviews", the 60-queries-4-dates tally and the
33-of-35 fabrication under *"figures we could not verify at all — reported on the
collector's testimony only"*, and the fabricated output itself was not retained. They are
the reasons a route was abandoned, not measurements of that route's accuracy, and nothing
here bounds how well any of them would work if pushed. Only the MWPVL row is verified
(4 of 202, April 2012, both re-derived), and 15-of-35 is on disk. **Do not read the table
as "these sources are useless"** — MWPVL failed as a *frame* and then supplied both the
only independent check on the OSHA bound (§6.2 of the provenance document) and, once
OCR'd, 1,904 facilities (§16.3).

### 16.2 The satellite dating programme — the best negative result in the set

**Asks.** Every date in the panel is an OSHA "operating by" **upper** bound with no lower
bound: for 104 of 104 national rows `open_year` *is* the quarter of the earliest
inspection. That single gap makes the CBP lag guard nominal (§9), blocks any use of time
in the choice model and killed the hazard model's event timing. A delivery station is a
large bright roof appearing where bare ground was, and Sentinel-2 photographs every point
on Earth every five days, free, back to 2015. **Can imagery supply the missing lower bound
and turn a bound into an interval?**

**Tested.** `data/collection/satellite/colab_date_from_satellite.py`, a standalone Colab
notebook needing no key, no Earth Engine account and no payment. 133 sites in; 107
geocoded by the free Census geocoder; Microsoft Planetary Computer STAC `sentinel-2-l2a`,
2016-01-01 to 2026-09-01, cloud < 20%, least-cloudy scene per month; a 240 m patch around
the point; signal `z(red) − z(ndvi)`; detector = the largest mean shift over all splits in
`[6, n−6]`; confidence = shift ÷ sd(first differences), declared a signal-to-noise ratio
and never a probability. **The stopping rule was written into `RUN_THIS.txt` before the
run**: *"If it cannot recover the dates we already know, the method is wrong and we throw
it away, having lost only machine time."*

**Result.** `data/external/satellite/satellite_dates.csv`, 107 rows — committed with a
`.gitignore` exception because the imagery host is blocked from this network and the file
cannot be regenerated here. Every figure below re-derived from it:

```
  coverage                   107 of 107 geocoded sites returned an estimate,
                             median 106 cloud-free scenes each
  within 1 year of the
  known year (n = 83)        41%
  LOGICALLY IMPOSSIBLE       39 of 107 = 36%, dating construction AFTER the
                             day OSHA found the building operating,
                             median 33 months after
  impossible, conf > 2       35%          impossible, conf 1-2      30%
```

**Why a method that answers every question is not thereby a good method.** The 107 of 107
is the symptom, not the achievement. `detect_construction()` returns the argmax of a
mean shift over interior splits: **there is no null outcome** — no threshold the shift
must clear, no test against the hypothesis that nothing happened. Handed a site already
built before Sentinel-2 began, it returns the argmax of a decade of noise and seasonal
drift, which is roughly uniform over the window; 36% landing after the inspection is
precisely what that produces. The confidence score then fails to catch it **because it
rewards the failure mode**: its denominator is the sd of *first differences*, so a smooth
drifting series scores high while a genuine step inflates its own denominator. It measures
smoothness, not stepness — which is why the two bands are indistinguishable and filtering
changes nothing. And `z(red) − z(ndvi)` looks like two channels; red and NDVI are
dominated by the same vegetation signal with opposite sign, so subtracting z-scores
doubles one measurement rather than corroborating two. **The 41% is the finding the 36%
keeps stealing attention from**: two in five inside a year is about what a uniform guess
over the plausible build-out window scores.

**Does not support — and one thing it positively forbids.** **The 68 estimates that
survive the logical test must not be presented as dates.** Keeping them is selecting on
the outcome: the test that keeps them is "earlier than the OSHA inspection", so by
construction the survivors agree with the bound we already had and carry no independent
information about the opening. A reader shown "68 facilities dated by satellite, all
consistent with OSHA" would reasonably conclude the method works; it is the same
36%-broken estimator with the visibly broken third deleted. Both softenings are ruled out
by measurement rather than by taste — "report only the high-confidence ones" by the
35%/30% bands, "report them as a wide lower bound" by a bound that is wrong in the
forbidden direction 36% of the time. One hypothesis was **not** tested and is not the
leading one: `PATCH_M = 120` samples 240 m around a street-centreline interpolation, so
some patches may not contain the roof; that would produce noise rather than this specific
after-the-inspection bias. **Cost: four hours of Colab and an afternoon of code**, no
money and no credentials — an experiment that worked as an experiment and failed as a
measurement, and those are different things.
[`data/SATELLITE.md`](data/SATELLITE.md), including the five conditions §7 sets for a
second attempt being worth running.

### 16.3 The OCR extraction — the one that worked, and how it was graded

**Asks.** MWPVL states an opening month and year for each facility and publishes its
tables as **images**. Can they be recovered well enough to trust — given that a silent
extraction error is indistinguishable downstream from a fact?

**Tested.** `tools/ocr/{grid_ocr,mwpvl_layout,mwpvl_strip}.py`, with the geometry in the
package proper at `src/siting_atlas/ingest/mwpvl_grid.py` because that part is tested.
Thirteen table images, up to 828 × 26,480 px, 152,915 pixel-rows, **no text layer**.
Columns are recovered from vertical valleys in word density (a fixed grid was tried first
and leaked words between columns); rows are anchored on the postal code, which every
record carries and which sits on the *last* line of its row. The defects were found by
measurement, not review — the reading-order bug that cost **22 points of geocoding match
rate** (OCR'd rows 61.7% against hand-collected rows 83.7%) surfaced only because
[`data/GEOCODING.md`](data/GEOCODING.md) §5 compared the two populations.

**Result.** `mwpvl_extraction.json`, `run_id 20260915-195231-c54f`:

```
  facilities extracted                1,904   13 tables, 58,088 words
  with a postal code                  1,767   92.8%
  with an opening YEAR                1,420   74.6%
  with an opening MONTH                 873   45.9%
  flagged "not confirmed" by MWPVL       44
  US small-package delivery stations    635   <- the target class
```

These are the project's only opening dates that are *lower* bounds; every other date on
record is an OSHA-derived upper bound, and the merge took the panel from **104 rows to
693** (`mwpvl_merge.json`). **Three independent checks grade it**, and none of them is
inspection:

| Check | Result | Artefact |
|---|---|---|
| OSHA falsification (`E_operating_by`) over all 1,420 dated rows | **208 linked, 11 falsified, 94.71%** — by precision, month 160 / 9, year 25 / 2, quarter 23 / 0 | `mwpvl_validation.json`, `20260915-195247-dbb5` |
| OCR'd state against an independently geocoded state | **604 of 606 comparable agree = 99.67%** (613 parsed, 22 unparsed of 635) | `mwpvl_merge.json:ocr_state_grade`, `20260915-195256-1c53` |
| Date plausibility | **99.5%** = (1 420 − 7) / 1 420: 2 before the network start, 5 beyond plausible | `mwpvl_validation.json:date_plausibility` |

**The 94.71% is only meaningful because §16.2 exists.** Same edit, same bound, two methods:
the satellite estimator fails it on 36% of its output, the OCR pass on **5.3%** (11 of
208). A pass rate quoted with no failing comparator is a number without a scale.

**Does not support.** Five limits, and the first is the one to carry. **(1) The OSHA check
covers 208 of 1,420 dated rows; 1,212 were never checked, and an unchecked row is not a
passing row** — 94.71% is the pass rate *on the checkable seventh*, not on the extraction.
(2) The three checks measure three different things and **none of them is the accuracy of
a year**: falsification runs one way only, the state check grades geography, and
plausibility is a range test a column systematically wrong by two years would pass.
(3) The dominant loss mode survives — a row whose postal code did not OCR merges into its
neighbour, **18 of 535 = 3%** on the delivery-station table (down from 41 of 510) — and
**that count is emitted into no artefact**, so it is a working measurement rather than a
reproducible one. (4) `facility_check` on the expanded file **fails**: 142 rows carry a
non-numeric `open_year`. (5) It is not re-runnable by anyone without a copy of a PDF the
publisher states is being withdrawn, which is recorded as a threat to validity rather than
as a formality.

Notes: [`data/MWPVL_OCR_PIPELINE.md`](data/MWPVL_OCR_PIPELINE.md),
[`tools/ocr/README.md`](../tools/ocr/README.md).

### 16.4 The labelling programme, and a route abandoned

**Asks.** OSHA's establishment name is silent on the facility class for 362 of its 474
national buildings. Does sending those addresses out for labelling buy facilities **per
metro**, which is what the line-haul covariate of §15 needed?

**Tested.** Six batches, 362 addresses, each answered with a class, a quotable sentence
and a URL, `UNKNOWN` permitted; then matched against both existing facility frames with
`common/linkage.py`'s Fellegi-Sunter comparator over parsed addresses rather than on a
city string.

**Result.** 135 delivery stations and **8 `UNKNOWN`** — recorded as `UNKNOWN`, not as a
failed join. Of the 135, 98 were already in `national_facilities.csv` and 24 in the pilot
file, leaving **13 new to both** across 8 CBSAs. The binding defect is upstream of the
labelling: the batch generator selected rows the OSHA name regex could not classify and
never checked them against `NATIONAL_CLASSIFIED.csv`, so **289 of 362 (79.8%) had already
been classified before a prompt was sent**. The salvage is the duplication itself — 122
already-known delivery stations relabelled blind, which is a labelled validation set for a
classifier whose agreement rate has never been measured. A fourth route, *SEC filings*,
was abandoned with no artefact.

**Does not support.** **The number 13 is not emitted by any code into any artefact** — it
is hand-counted, it has moved once, and rebuilding it by address match gives 27 or 37.
`warehouse/batch_candidates.py:54` hardcodes `BATCHES = ("1", "2", "3")`, so the module as
shipped reads 210 of the 362 rows and writes **nine**. The thirteen also **must not** enter
a `with_saving` fit: they carry no opening date, so `choice.build` counts every one of them
first-in-metro by construction, which would dilute 35 informative decisions with thirteen
degenerate ones and make an underpowered test look better resolved than it is.

---

## What the programme establishes, taken together

Five panel compositions, three algorithms, fifteen covariates, two transforms, thirteen
network specifications, seven survival arms, nine metro arm-form cells, 108 white-space
cells. They land in the same narrow band, and the band has three names.

**1. A data ceiling, measured from both sides.** The GBM benchmark bounds the *model*-side
gap: a flexible learner with no theory in it is worth **1.3 decisions of 38** over ranking
by a single raw count — and that edge vanishes entirely at 483 decisions. The covariate
search bounds the *column*-side gap: fifteen unused variables move the large-metro top-10
rate by at most **0.94 percentage points end to end**, and ten move it by exactly zero. The
per-capita and log-relative arms then rule out the most attractive alternative explanation
— that the columns fail on scale rather than content. They do not: the transform removes
the collinearity cleanly and the columns stay inert.

**2. A grain diagnosis, and it is a finding about public data infrastructure rather than
about this project.** Six of the fifteen failures are county-level values broadcast onto
every ZCTA in the county — about nine distinct numbers across a 200-ZCTA choice set. **You
cannot rank 200 things with 9 numbers, however important the thing being measured.** The
dispersion regularity reaches the same wall from the other direction, on a covariate family
whose grain is a tunable parameter: every term with within-metro cv < 0.6 lands at the
coefficient boundary, 7 of 7. That is a test you can run *before* fitting anything, and it
runs one way only. The metro-level test then shows the problem is not fixed by moving up a
level — the same free data loses to "rank by households" in 0 of 7 held-out years, and the
one covariate tier that motivated the hypothesis was never testable on the panel.

**3. Densification, the mechanism that unifies the rest.** At the headline 45-mile radius,
**68.7%–75.9% of 2024–25 delivery-station openings landed inside territory the pre-2024
network already served**, a median 7.5 miles from an existing building. That single fact
explains why a warehouse count is the only covariate that works — it is a proxy for
"already here"; why network proximity and gravity both carry weight; why the hazard model's
catchments overlap 58.4% of the time and destroy the independence its likelihood assumes;
and why ranking *unserved* places wins 0 of 108 cells against ranking populated ones. The
white-space diagnosis isolates it to one operation: the **coverage mask** costs 13.9 to
24.0 points, while the spatial smoothing it shares with its own control costs nothing.

**The honest boundary on all three.** Densification is measured at metro grain and above
and **does not survive as an independent mechanism once metro size is controlled** —
`facilities_open_prior` takes a negative coefficient in all seven metro-model years. The
data ceiling is a ceiling on *seven columns for these panels*, not on the question. And the
covariate that carries the whole choice model was audited to the point of doubt and retains
79% of its value on pre-opening vintages — on **29 decisions**, with the leak and the
staleness confounded in one intervention, and with nothing that transfers to the other 65.

What is left standing is a cost model that works on real data, a pre-registered negative
result whose H0 paragraph was written before the fit, a measured ceiling on the project's
own data coverage, and four models specified, fitted, scored and beaten — by a constant, by
a households baseline, by a single raw covariate. **Every one of those defeats is a
measurement, and the artefact that would contradict it ships in this repository.**
