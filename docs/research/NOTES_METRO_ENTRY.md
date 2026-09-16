# The metro-level entry model: H0 holds

*Executed 2026-09-15 against `docs/PREREG_METRO_MODEL.md`, md5
`946f7ef75db69e5278eea409a04c3823`, written earlier the same day and before
any model was fitted. Code `src/siting_atlas/models/metro_entry.py` and the
`metro_*` helpers; artefact `outputs/metrics/metro_entry.json`,
run `20260915-231322-7d21`.*

> *That md5 is the pre-registration **as fitted**, it is what
> `metro_entry.json:prereg_md5` records, and **re-hashing
> `docs/PREREG_METRO_MODEL.md` today still reproduces it.** Check it yourself:*
>
> ```
> md5sum docs/PREREG_METRO_MODEL.md
> ```
>
> *An earlier version of this caveat said the hash would no longer match. That
> was true for a few hours on 2026-09-15, when three wrong motivating figures
> were corrected inside the pre-registration itself. Those edits were reverted
> and the corrections moved to
> [`../PREREG_METRO_MODEL_ERRATA.md`](../PREREG_METRO_MODEL_ERRATA.md),
> precisely so this check keeps working — a pre-registration nobody can verify
> is worth very little. The seal is now guarded by a CI gate and a reference
> copy under `reproducibility/seals/`.*

The prereg fixed the question, the sample, the covariates, the model forms,
the baselines, the evaluation and the success criterion in advance, and it
wrote both outcomes' language in advance too. This note reports the outcome
whose language was already written. It is section 7's H0 paragraph, quoted
without softening:

> Free public data cannot predict siting at any grain tested. The ZIP-level
> failure is not a resolution problem but a general one: the variables that
> drive the decision are not public at any resolution.

---

## 1. The criterion, and how it was missed

Prereg section 9:

> H1 is supported if, out of time, the metro model beats the households
> baseline on AUC in a majority of held-out years AND its calibration is at
> least as good as the constant null in a majority of years.

```
                          clause 1            clause 2
                      AUC > households    ECE <= constant null
  prereg_strict           0 of 7                3 of 7        H0
  vintage_clean           0 of 7                3 of 7        H0
  vintage_relaxed         1 of 7                0 of 7        H0
```

Both clauses fail in every arm and under all three model forms — logistic,
Poisson and negative binomial. Neither clause is close: the first is lost
0 of 7, not 3 of 7.

## 2. Out of time, year by year — the verdict arm

Fit through t-1, predict t, rolled forward; 935 metros per year; 306 event
metro-years across the seven held-out years. AUC:

```
  year  events   model  b1 uniform  b2 households  b3 facilities
  2019     23   0.7487     0.5         0.9464         0.7198
  2020     49   0.6968     0.5         0.9682         0.7600
  2021     53   0.8119     0.5         0.9239         0.7811
  2022     36   0.7509     0.5         0.8780         0.7012
  2023     31   0.7713     0.5         0.9049         0.7934
  2024     50   0.6307     0.5         0.8363         0.6968
  2025     64   0.6098     0.5         0.8543         0.6902
```

The model beats baseline 1 in all seven years. Prereg section 8.4 says in
advance that this means nothing: *"Beating only the uniform baseline.
Trivial at 935 metros. Baseline 2 is the bar."* Against the bar the model
loses 7 of 7, by 0.112 of AUC in its best year (2021) and 0.271 in its worst
(2020).

Top-k, which is the metric the ZIP-grain work used, says the same thing:

```
  year   top25: model  b2  b3   |   top50: model  b2  b3   | uniform null(25)
  2019          6      8   7    |         11     11  11    |      0.62
  2020         16     19  16    |         22     32  22    |      1.31
  2021         17     20  16    |         24     31  25    |      1.42
  2022         10     11   9    |         16     15  15    |      0.96
  2023          8     10   7    |         13     11  12    |      0.83
  2024         12     15  12    |         19     22  19    |      1.34
  2025         15     13  15    |         24     23  23    |      1.71
  total        84     96  82    |        129    145  127   |
```

Raw counts against a uniform null, never a skill score — section 6, and
Gneiting & Raftery 2007 sec. 2.3 p.362.

**The fitted model is indistinguishable from baseline 3.** Pooled over the
seven held-out years the model scores AUC 0.7323 and the zero-parameter
count of facilities already present scores 0.7325, on 6,545 identical rows.
Top-50 totals are 129 against 127. A two-covariate logistic, fitted seven
times, reproduces a column of integers.

## 3. Calibration against the constant null — where the model dies

The second clause is reported here and not buried, because this is where the
hazard model died (AUC 0.689, 0 of 17 calibration comparisons,
`NOTES_HAZARD_REVIVAL.md`). ECE, quantile bins, 10 bins:

```
  year   model ECE   constant null ECE    model at least as good?
  2019    0.010972       0.002139                 no
  2020    0.026429       0.028877                 YES
  2021    0.011033       0.023529                 YES
  2022    0.033251       0.000535                 no
  2023    0.032841       0.005775                 no
  2024    0.030361       0.015508                 no
  2025    0.027335       0.028266                 YES
```

3 of 7 — a minority, so the clause fails. The pattern is legible and worth
stating because it is not the hazard model's pattern. The constant null is a
single number, last year's base rate, applied to all 935 metros; its ECE is
therefore almost exactly the year-on-year drift in the base rate. The model
wins in 2020, 2021 and 2025 — the three years the base rate jumped — and
loses in the four quiet years by an order of magnitude. So the model is not
*uniformly* worse calibrated than a constant; it is worse calibrated
whenever the world is steady, which is most of the time.

This is the prereg's own point, in its own words: *"Ranking without
calibration is not prediction — it tells a county it is more likely than its
neighbour and cannot tell it whether that means 5% or 40%."*

## 4. The 2020-21 sensitivity

Those two years hold 102 of the 306 held-out event metro-years — a third of
the evidence, and the pandemic build-out. Dropping them from the criterion:

```
                          clause 1      clause 2
  all seven years         0 of 7        3 of 7      H0
  excluding 2020-21       0 of 5        1 of 5      H0
```

The finding is not driven by 2020-21. It gets slightly worse without them,
because the two years the model wins on calibration are two of the three it
loses when they are removed.

## 5. The comparative half of H1

H1 asked for the metro margin to exceed the ZIP margin. The ZIP figure, from
`outputs/metrics/gbm_benchmark.json`, `across_repeats`, 50 paired re-splits:
the conditional logit came out **0.36 of 38 top-10 hits BELOW** its
zero-parameter raw-count baseline, winning 11 and losing 23.

The metro model comes out **2.29 of 50 top-50 hits per year below** its
households baseline, and 0.163 of AUC below it pooled. Scaled either way,
the metro model loses to its baseline by more than the ZIP model lost to
its own. The comparative clause fails in the same direction as the numeric
one.

## 6. Stratification — and the number that would have been misread

Prereg section 6 requires size strata with distinct-metro n, because this
project has fallen into Simpson's paradox twice. Terciles of households,
fixed across years, verdict arm, pooled over the seven held-out years:

```
  tier   distinct metros   metro-years   events   model AUC   b2 AUC
  tier1        312            2,184         6      0.4125     0.7668
  tier2        311            2,177        27      0.5666     0.6827
  tier3        312            2,184       273      0.6961     0.8023

  pooled       935            6,545       306      0.7323     0.8949
```

**The pooled AUC of 0.7323 is higher than the model's AUC in every single
tier.** That is the aggregation effect in its textbook form: size predicts
the outcome and size defines the strata, so pooling lets the model be
rewarded for a ranking it did not have to earn. Quoted alone, 0.73 would
have read as a working model. Within the only tier with enough events to
measure, it is 0.70 against a baseline's 0.80.

The direction of the verdict is unchanged in all three tiers — households
beats the model everywhere — so stratification strengthens the finding
rather than rescuing it. Tier 1 holds 6 events in 2,184 metro-years and
nothing there should be read as a measurement.

## 7. Uncertainty — the interval that may be quoted

Metro-clustered bootstrap, 2,000 draws, resampling whole CBSAs from the
pooled out-of-time predictions:

```
  model AUC                        0.7319  [0.6876, 0.7706]
  baseline2 households AUC         0.8946  [0.8743, 0.9139]
  model minus baseline2           -0.1628  [-0.2011, -0.1313]
```

The gap excludes zero by a wide margin on 935 clusters.

The secondary 50 paired re-splits (hold out 30% of metros, refit inside every
repeat) give a mean paired AUC difference of **-0.175, losing 50 of 50**.

One honest note against the prereg here. Section 6 states, from
`network_inference.json`, that a metro-clustered bootstrap came out 24-28%
WIDER than a re-split spread. On this problem it is the other way round: the
re-split spread is [-0.235, -0.133], width 0.102, and the bootstrap interval
is [-0.201, -0.131], width 0.070 — the bootstrap is 31% NARROWER. The two
objects are different, and that is the explanation rather than a
contradiction: the re-splits refit the model 50 times and so include
estimation variability, while the bootstrap conditions on the fitted models
and measures only the sampling variability of the metric. The prereg's rule —
do not quote a re-split spread as a standard error — still holds. The
direction of the difference is problem-specific and should not be carried
forward as a constant.

## 8. What the vintage gate did, which is the largest thing in this run

Prereg section 4 requires every covariate to be *"available strictly before
the year being predicted"*, and section 8.1 makes non-enforcement an
invalidating condition with a stated remedy: the column is dropped and the
drop is counted. Enforcing it removed **8 of the 12 prereg covariates**.

The reason is structural, not marginal. Most of the panel's columns are not
time series at all. Mean distinct values per unit across all 32 quarters of
`panel.parquet`:

```
  population, households, median_household_income      1.00
  traffic_proximity, diesel_pm                         1.00
  wage_all_occupations, wage_freight_handler           1.00
  metro_employment                                     1.00
  permit_units_total                                   4.97   (annual, real)
```

One value, repeated. The vintages behind them:

```
  column group                     source                   vintage   verdict
  households, population, income   ACS 5-year 2023           2023     usable 2024+
  traffic_proximity, diesel_pm     EJScreen 2024             2024     usable 2025
  wages, metro_employment          BLS OES oesm25ma.zip      2025     never usable
  permit_units_total, yoy          Census BPS, annual        per-year usable at lag 1
```

The ACS 5-year 2023 file is built from responses collected 2019-2023. Using
it to predict 2020 is not a borderline publication-lag call: three of its
five collection years are after the outcome. This is the same shape as
`NOTES_COVARIATE_LEAKAGE.md`, where a guard that looked real was defeated by
a median 34 months.

Two further columns then failed a coverage floor of 90% in every held-out
year. The Census permits ingest covers about 745 counties for 2017-2021 and
about 3,022 for 2022-2025, which at metro grain is 24% of metro-years in
2019-2022 and 97.8% in 2023-2025. A complete-case fit on a quarter of the
universe selects on data availability, and availability correlates with
metro size — the shape of error section 8.2 rules out.

What survived into the verdict arm: `facilities_open_prior` and
`dist_nearest_outside_prior`. Both are Tier 3, both computed from the
facility panel as of the end of year t-1.

**So the Tier 1 mechanism that generated H1 was never testable on this
panel.** Prereg section 2 predicted that the six county-grain covariates
would work at metro grain because *"their variation is between counties, and
therefore between metros"*. That prediction is still untested: the county
and metro columns that were supposed to carry it are single-vintage
broadcasts that cannot be used to predict any year in the window without
leakage. This is a finding about the data, not about the hypothesis, and it
is stated here rather than in a footnote because it is the single biggest
qualification on the H0 verdict.

## 9. The arms, declared before any fit

Three, named in the artefact at stage 1 with `verdict_arm` set before a
single model was estimated:

```
  prereg_strict     vintage gate + coverage floor          VERDICT COMES FROM HERE
                    -> facilities_open_prior, dist_nearest_outside_prior
  vintage_clean     vintage gate, coverage floor waived
                    -> + permit_units_total, permits_yoy_pct
  vintage_relaxed   the prereg list ignoring vintage       DIAGNOSTIC ONLY
                    -> + traffic_proximity, diesel_pm, households,
                         population, median_household_income
```

The relaxed arm exists to answer "how much of this is leakage" with a number
rather than a shrug, and it cannot change the verdict because the verdict arm
was fixed first. Its answer is the most interesting secondary result in the
run:

```
  vintage_relaxed, out of time, AUC

  year   model   baseline2 households   diff
  2019  0.9439        0.9464          -0.0025
  2020  0.9528        0.9682          -0.0154
  2021  0.9243        0.9239          +0.0004
  2022  0.8777        0.8780          -0.0003
  2023  0.8970        0.9049          -0.0079
  2024  0.8140        0.8363          -0.0223
  2025  0.8506        0.8543          -0.0037
```

A seven-covariate logistic that **contains households**, plus population,
income, traffic proximity, diesel particulates and the network terms, and
that is allowed to see data from after the year it predicts, still loses to
ranking on households alone in 6 of 7 years. Its single win is +0.0004 of
AUC. Its calibration loses 7 of 7. The extra six covariates are not adding
signal; log-households and log-population are near-collinear, and their
fitted coefficients oscillate accordingly (2020: +6.05 and -3.45).

Leakage is therefore not what is holding the model up, and removing it is not
what is holding the model down. **The ceiling is the baseline.**

One more detail from that arm, stated because it contradicts an earlier
project finding. Conditional on metro size, `facilities_open_prior` takes a
NEGATIVE coefficient in all seven years (-0.09 to -0.45). `white_space.json`
measured that 68.7-75.9% of 2024-25 openings landed inside existing coverage at
its headline 45-mile radius — the range being across the two coordinate sets at
that one radius (75.9% = 60 of 79 real-coordinate openings, 68.7% = 90 of 131
once ZCTA-centroid fallbacks are included), not across radii — and
the raw correlation here agrees — baseline 3 alone scores AUC 0.73. But once
size is controlled, having facilities already predicts *fewer* new ones.
Densification is a statement about where the big metros are, not an
independent mechanism, at least at this grain.

## 10. Deviations

Four, all recorded in the artefact's `deviations` block.

1. **20 dated facilities carry no `cbsa_code`.** They cannot be assigned to a
   metro so they contribute no event. The prereg's own rule for an undated
   facility — excluded from the event set, retained in the universe, counted
   — is applied unchanged. Events in window: 462, not the ~480 section 3
   anticipated, across the expected 195 metros. Per-year event metro counts
   run 21 to 64, matching section 3 exactly.

2. **8 of 12 covariates dropped on vintage, 2 more on coverage.** Section 8.
   Detailed in section 8 above.

3. **Baseline 2 is scored on the ACS 2023 households column that the gate
   rules inadmissible as a covariate for 2019-2023.** Section 5 fixes the
   baseline and section 4 fixes the vintage rule; with one ACS vintage on
   disk they cannot both be honoured. The prereg's baseline is run as
   written. The bar is therefore set using information the model is not
   allowed to see, which biases the comparison AGAINST H1 — conservative for
   the finding that was reached, and a reason a narrow H1 win under this
   arrangement would not have been safe to report.

4. **A held-out metro-year with a missing covariate is scored at the training
   base rate**, not dropped from the universe and not imputed. Nil effect on
   the verdict arm (0 of 6,545 held-out rows). Severe for `vintage_clean`,
   where 720 of 935 rows in 2019 fall back to the null and the arm has no
   complete training rows at all, so it does not fit for that year.

Nothing was corrected or imputed anywhere in the run.

## 11. What would make me distrust this

Stated because the prereg's value depends on the negative being as
scrutinised as a positive would have been.

- **The verdict arm has two covariates.** It is a weak model, and it is weak
  because the vintage rule made it weak. The honest reading is "the prereg's
  own leakage rule leaves almost nothing to fit", not "a well-specified metro
  model failed". The defence is arm 3: the fully-specified, leakage-permitted
  model also loses, 6 of 7 on AUC and 7 of 7 on calibration. If that arm had
  won, this note would read very differently and would be much less safe.
- **The households baseline is extraordinarily strong here** — AUC 0.84 to
  0.97. That is mostly a statement about the universe. Of 935 CBSAs, the 21
  to 64 that receive an opening in a year are nearly all large, so "rank by
  size" is close to the right answer by construction. A different universe —
  say, the 200 largest metros only — would compress the baseline and could
  change the verdict. The prereg fixed the universe at all 935 and section
  8.2 explains why; restricting it now would be exactly the move the prereg
  exists to prevent.
- **One model family, one transform map.** Log1p on count-like columns,
  standardisation inside the fold. Neither was searched over and neither is
  in the prereg. A different transform could move AUC by a point or two. It
  could not plausibly move it by the 0.16 the verdict turns on.
- **306 held-out event metro-years is not many**, and 2020-21 supply a third
  of them. The sensitivity in section 4 addresses the second worry, not the
  first.
- **ECE with 10 quantile bins on a 3-5% event rate is a noisy statistic.**
  The 3-of-7 count would be worth re-reading at a different bin count before
  anyone builds on the exact number. It would not survive being re-read into
  a 4-of-7, because the four losing years lose by 5x to 60x, not by a margin.

## 12. Where I think the prereg is wrong

Run as written, and recorded here rather than acted on.

- **Section 4 lists Tier 1 and Tier 2 covariates that the panel cannot supply
  in a time-respecting form.** The prereg's authors could have checked the
  distinct-value count per unit before fixing the list; the check is two
  lines. Had they done so, the covariate list would have been three or four
  columns long and the prereg would have said so. This is the one change I
  would make to it.
- **Section 5's baseline and section 4's vintage rule are in direct
  conflict** given a single ACS vintage, and the prereg does not say which
  wins. Deviation 3 resolves it in the direction that disfavours the
  hypothesis; a prereg should have resolved it itself.
- **Section 9 does not say which model form carries the verdict**, having
  required two in section 5. It made no difference — logistic, Poisson and
  negative binomial agree to within 0.0001 of AUC in every year — but it
  could have.

None of these change the outcome. All three are the kind of thing that is
only visible once the prereg meets the data, which is an argument for writing
one, not against it.

## 13. What this means for the project's claim

The prereg said both outcomes were complete findings and that this one is
*"harder and arguably more valuable, because it says the transparency gap is
structural rather than an artefact of one model's grain"*. The measurement
supports the stronger reading, with one qualification that belongs in the
same sentence as the claim.

At ZIP grain the fitted model lost to a warehouse count. At metro grain the
fitted model loses to a household count, in every year, under every form,
with and without the pandemic, in every size tier, and whether or not it is
allowed to cheat on vintage. In both cases a single free public column
already contains everything the model recovered, and in both cases the model
adds nothing to it.

The qualification: this run tested whether free public data adds anything to
*knowing how big a place is*. It did not test the Tier 1 construction and
freight covariates that motivated H1, because no time-respecting vintage of
them exists in this panel. That is a data-availability finding, and it points
at the same conclusion from a different direction — the covariates that might
have distinguished one metro from another are published once, late, and
without a usable history, which is itself a form of the transparency gap.
