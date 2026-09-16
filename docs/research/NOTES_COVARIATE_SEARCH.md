# Notes — the panel's unused columns, and the two reasons none of them can help

> **SETTLED — the re-run landed.** The
> `python -m siting_atlas.models.covariate_search` run that was in flight on
> 2026-09-15 completed at exit 0 with all five stages present, and every
> figure in this file has been re-derived from the finished artefact. The
> frame is **477 decisions, 191 held out**; the baseline is **6.216x, 30.47%**;
> the nested forward-selection penalty is **−0.6201 pp**, not −0.72. The
> facility count now reads **687 at every stage** (§11). **One caution still
> stands and is not about this run:** the emitter reuses one `run_id` across
> successive writes and stamps `written_at` at the *first* write, so the stamp
> below cannot by itself distinguish two versions of this file. Check
> `facilities: 687` and `stage_ledger` before trusting a quotation from it.

*Built and run 2026-09-14; **artefact re-read from the completed run
2026-09-15**, `run_id 20260915-235210-ff92`, `written_at
2026-09-15T23:52:16Z`. Artefact:
`outputs/metrics/covariate_search.json`, seed 20260914, 50 paired re-splits.
**The search runs on its own frame, not on `panel_experiments.json`'s:** the
`core` stage holds **477 decisions, 191 held out, 21,768 frame ZCTAs and
82,912 alternatives**, against the `anchor` stage's full frame of 483
decisions, 193 held out, 22,882 ZCTAs and 86,682 alternatives. Do not quote a
figure from this file as though it were on the 483-decision panel. Code:
`src/siting_atlas/models/covariate_search.py` and its `covariate_frame`,
`covariate_arms`, `covariate_audit`, `covariate_permits`, `covariate_report`
and `covariate_gbm` helpers. Every figure below is read out of an artefact or
printed by the runner. None is recalled. §11 records which stages of the run
are in the artefact and which are not, and why.*

**The one-line result: fifteen unused panel columns — entered as eighteen
terms, because three are also entered as a positive transform of the opposite
sign — were added to the four the model reads, one at a time and in searched
combinations. The best of them moved large-metro top-10 accuracy by
+0.038 percentage points, and an honest
forward selection made the model 0.62 points WORSE **on that same large-metro
top-10 rate** — though marginally better, +0.36 points, pooled across all
choice-set sizes (§5). But the null is not the finding. The
finding is that the reason is now MEASURED, it is structural, and it predicts
what would work.**

```
  WHY NOTHING IN THE PANEL CAN HELP, IN TWO NUMBERS

  1  GRAIN.  traffic_proximity, diesel_pm and both permit columns are
     COUNTY values broadcast to every ZCTA of the county. A large metro
     presents ~200 candidate ZIPs and these columns present
     9.2 DISTINCT VALUES across all of them. A conditional choice model
     uses only WITHIN-choice-set variation, so a covariate that is
     near-constant inside a metro cannot answer the question however
     strong its true effect. This is not "the column is weak". It is
     "the column is at the wrong geographic grain."

  2  IDENTIFICATION.  Five ACS candidates correlate 0.84 to 1.000 with
     `households` WITHIN METRO. households is the numeraire, fixed at 1.
     A column proportional to the numeraire leaves the likelihood flat
     along a whole ray: the model is NOT IDENTIFIED in it. Their fitted
     coefficients do not go to zero like an uninformative column; their
     intervals span fourteen to nineteen orders of magnitude and one of
     them has a MEDIAN of 5e12.
```

Together those close the question `NOTES_GBM_BENCHMARK.md` §8 left open, and
they turn "we tested fifteen columns and none helped" into "we established why
this panel cannot help, and what shape of covariate could."

---

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes seven parts and says the directory holds
one file per paper. This is not a paper; it is an experiment. The seven-part
structure is adapted — no citation, no page offsets, no author to quote. Part
7, "what I did NOT read", survives as §10, "what this does not settle".

---

## 1. The question, and where it came from

[`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) §8 item 2, verbatim:

> "**The data ceiling is a ceiling on FOUR COLUMNS, not on the question.**
> Households, land area, establishments, warehousing establishments. ... 'No
> learner can do better with these four columns' is what was measured; 'no
> learner can predict Amazon siting' is not, and the two must not be
> conflated."

`data/processed/panel.parquet` has fifty columns. This file tests the ones
that were not conflated.

**The theory being tested, stated before the run.** A large metro offers 300+
candidate ZIPs and most are *physically impossible* — residential, no
industrial land, no parcel large enough. If the four columns cannot separate
those from the real candidates, the model spends its ranking on ZIPs that were
never in contention, and a **buildability** covariate would be worth more than
another agglomeration covariate. `traffic_proximity` (highway access),
`diesel_pm` (truck corridors), `median_home_value` (expensive implies
residential implies unbuildable) and the building-permit columns (where
construction actually happens) are the panel's candidates for that role.

**A second question rides along.** If `warehousing_establishments` works as a
buildability proxy rather than as an agglomeration measure, a clean land or
traffic covariate might **substitute** for it — which would both improve the
model and retire the circularity risk
[`NOTES_LEAKAGE_DECISIVE.md`](NOTES_LEAKAGE_DECISIVE.md) priced at a ~20%
haircut. §6 tests that directly and closes it.

## 2. What each column IS, before a single fit. This section explains the whole result.

Three properties decide whether a column can help a conditional choice model,
and two of them are fatal. Measured on the 42 metros with more than 100
candidate ZIPs — the stratum the experiment is about.

```
  column                        popul  county   values   r|estab  r|hhold
  ---------------------------------------------------------------------
  households        (in model)  0.999    0.02    193.3     0.710     --
  land_area_sqmi    (in model)  1.000    0.02    199.6    -0.097   -0.055
  establishments    (in model)  0.915    0.02    164.1      --      0.710
  ---------------------------------------------------------------------
  traffic_proximity             0.999    1.00      9.2     0.242    0.283
  diesel_pm                     0.992    1.00      9.2     0.294    0.340
  low_income_pct                0.999    1.00      9.2     0.043    0.134
  people_of_colour_pct          0.999    1.00      9.2     0.226    0.318
  permit_units_total            0.654    1.00      8.0     0.190    0.220
  permits_yoy_pct               0.554    1.00      7.9    -0.064   -0.060
  ---------------------------------------------------------------------
  employment                    0.915    0.02    191.9     0.834    0.474
  annual_payroll                0.915    0.02    197.0     0.654    0.265
  vehicle_availability_total    0.999    0.02    193.3     0.710    1.000
  in_labor_force                0.999    0.02    194.7     0.684    0.979
  bachelors_degree              0.999    0.02    186.5     0.750    0.881
  owner_occupied                0.999    0.02    189.7     0.610    0.880
  renter_occupied               0.999    0.02    181.4     0.610    0.840
  median_age                    0.971    0.02    121.7    -0.181   -0.249
  median_home_value             0.897    0.02    181.8     0.227    0.019
  ---------------------------------------------------------------------
  popul    share of panel rows non-null
  county   share of counties with a single value = the column is at
           COUNTY grain, broadcast to every ZCTA of the county
  values   mean number of DISTINCT values a large-metro choice set sees
  r|x      within-metro correlation with a column already in the model,
           demeaned by metro because a raw national correlation mostly
           measures metro size
```

### 2.1 The grain diagnosis. Read the `values` column first.

A large metro presents about **200 alternatives**. `traffic_proximity`
presents **9.2 distinct values** across all of them. `permits_yoy_pct`
presents **7.9**.

These are not ZCTA measurements. EJScreen is a census-tract file, there is no
tract-to-ZCTA crosswalk in L1, and `warehouse/optional.py` aggregates it to
**county** (population-weighted tract means) before the panel ever sees it.
The Building Permits Survey is a county series joined on `county_geoid` in
`warehouse/panel_sql.py`. Both are then broadcast unchanged to every ZCTA in
the county — `county_grain_share = 1.00` says that literally: for 100% of
counties, every ZCTA in that county carries an identical value.

**A conditional choice model uses only within-choice-set variation.** Its
probability is `P_j = beta'a_j / sum_k beta'a_k`, a share of the metro total.
A column that takes 9 values across 200 alternatives can rank the *counties*
of a metro and can say nothing whatever about which of the fifty ZIPs inside a
county was chosen. The hypothesis in §1 — that highway access and truck
corridors discriminate *among ZIPs* — is not a hypothesis this panel can
express. It holds the county average.

That single fact explains the whole run of failures at a stroke, and it is a
much stronger statement than "these columns are weak". A weak column might be
rescued by more data. A county-grain column cannot be rescued by anything
except a finer-grained source.

**It also predicts what would work, and the prediction checks out.** The one
covariate family in this project that is genuinely constructed at ZIP level is
the network-proximity pair — `sortation_proximity` and `fulfilment_proximity`,
`1/(1 + road miles)` computed per ZCTA from coordinates in
`models/panel_network.py`. That is a separately owned, concurrently running
experiment and the figures below are read from **its** artefact
(`outputs/metrics/panel_experiments.json`, `network_gain`), not produced here:

```
  adding the ZIP-level proximity covariates, conditional logit, 50 re-splits

    top-5   +1.23pp   improved 42 re-splits, worsened  1
    top-10  +0.32pp   improved 28,             worsened 12
    Brier   improved on 49 of 50
```

Those are small gains. They are also **consistent in sign in a way nothing in
this file is**: the best column tested here wins 3 re-splits of 50, ties 45
and loses 2. The contrast between a 42-1 record and a 3-45-2 record, on the same panel
and the same protocol, is the grain diagnosis being confirmed by an
independent measurement.

### 2.2 The identification diagnosis. Then read `r|hhold`.

```
  vehicle_availability_total   r = 1.000  with households, within metro
  in_labor_force               r = 0.979
  bachelors_degree             r = 0.881
  owner_occupied               r = 0.880
  renter_occupied              r = 0.840
  ---
  employment                   r = 0.834  with establishments
  annual_payroll               r = 0.654  with establishments
```

These are ACS household-side counts, and `households` is the **numeraire**,
fixed at 1.000 because the model is scale-invariant in beta and one
coefficient must be pinned (`choice.py` module docstring, consequence 1). A
column proportional to the numeraire leaves the likelihood flat along an
entire ray — only the *ratio* of the two coefficients is identified, not
either one.

**The optimiser says so out loud, and §4 shows it.** These columns do not go
to zero like an uninformative column. `in_labor_force` takes a median beta of
**5.1e12**, hits the upper boundary on 82% of re-splits, and drags
`warehousing_establishments` to **5.0e12** alongside it, because only their
ratio is pinned down. A reader handed the point estimate alone would report a
coefficient of seven trillion. `employment` and `annual_payroll` are the same
CBP establishment file measured three ways.

**This must be reported as non-identification, not as "the column was
uninformative."** They are different findings with different remedies. An
uninformative column is a fact about warehouses; a column collinear with the
numeraire is a fact about the model's parameterisation, and it would behave
identically if the column were the single best predictor in the world.

**Exactly one candidate is ZCTA-grain AND independent of what is already in
the model: `median_home_value`**, r = 0.227 with establishments and **0.019**
with households. It is precisely the buildability proxy the theory asked for.
§4 reports what happened to it.

### 2.3 Two columns screened out before the search, and why

`wage_freight_handler` (55.3% populated — it was on the brief's list) and
`metro_employment` are **BLS OES metro-grain series, constant inside every
choice set** (`constant_within_large_metro = 1.00`). A constant does not
cancel out of `beta'a_j / sum_k beta'a_k`; it flattens every probability
toward uniform, so the only sensible weight for it is zero. It cannot help,
and no fit is needed to know that — which is the grain diagnosis in its
limiting case. `rent_index` is 11.2% populated and was not pursued.

### 2.4 Time-invariance is NOT a screen, and is not the leakage trap

Thirteen of the fifteen candidates take one value per ZCTA across all eight
panel years. That is fatal for a before/after design and **irrelevant here**:
a conditional choice model compares alternatives inside one choice set at one
date and never differences a ZCTA against its own past, so cross-sectional
variation is the only variation it uses. It also rules **out** the
self-counting mechanism
[`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) documents: a value
that does not move cannot move because of the facility.

What it does not rule out is a measurement **window** that post-dates the
decision. The ACS columns are the 2023 five-year estimates
(`data/interim/acs5_zcta_2023.parquet`, window 2019-2023) and EJScreen is the
2024 release, so for a 2019 opening the value is measured partly after the
building existed. That is a weaker and different exposure from self-counting,
and the three **baseline** columns already carry it — `households` and
`establishments` are the same single vintage — so every arm inherits it
equally and the comparison between arms survives. The *level* of every arm,
including the published one, does not.

## 3. How it was measured, and the four rules that were not negotiable

**1. Every arm is a COLUMN SUBSET of one frame.** Adding a column with gaps
drops alternatives, and an arm built on its own frame would be scored on
easier choice sets. `covariate_frame.build_frame` assembles one object
carrying every column and each arm is a `columns_only` view of it, so choice
sets are identical across arms and a paired difference is about the column
alone.

The cost is reported rather than absorbed. The frame carrying all thirteen
time-invariant candidates keeps **21,768 of 22,882 ZCTAs (95.1%)** and **477
of 483 decisions**; the candidates that can cost anything are the least
populated ones, and `column_audit` names them — `median_home_value` at
**89.7%** of panel rows, `employment` and `annual_payroll` at **91.5%** each
(the CBP share the baseline already carries through `establishments`),
`median_age` at **97.1%** and `diesel_pm` at **99.2%**; the remaining eight are
at 99.9% or better. *The artefact records the populated share per column but
not which column dropped which ZCTA, so this is an attribution from the audit,
not a measurement.*

Because the dropped alternatives are the thin ones, the restricted frame is
slightly **easier in hit rate** — baseline large-metro top-10 is **30.473%**
on the `core` (restricted, 477-decision) frame against **30.326%** on the
`anchor` (full, 483-decision) frame — but **not in lift**, because the chance
rate rises with it, from **4.846%** to **4.903%**. In lift the `core` frame
reads **6.2157x** against `anchor`'s **6.2585x**. *This reverses what this
paragraph said before the 2026-09-15 re-run, which had the restricted frame
ahead on lift as well (6.389x against 6.259x); on the settled artefact the two
measures point opposite ways and the paragraph has to name which one it
means.* Either way the point stands: the two frames are not interchangeable,
which is why the baseline is refitted inside the same frame as every arm it is
compared to.

**2. Stratified by choice-set size, always.** Pooled top-k lift across
heterogeneous choice sets is a Simpson's-paradox trap that already produced
one wrong conclusion here — `outputs/metrics/lift_by_market_size.json` records
pooled lift FALLING 3.68x to 2.61x while lift ROSE in the mid and large
strata. The cuts (<=25, 26-100, >100) and the analytic `min(k,J)/J` chance
rate are imported from `models/panel_strata`, not re-declared, so this
artefact and `panel_experiments.json` can be read together. Small markets are
capped near 1.5x because a random guess already scores 96% there; **the >100
stratum is the only one carrying information.**

**3. Selection happens inside the training fold.** A subset chosen by looking
at the test fold is a subset chosen by the answer.
`covariate_arms.forward_select` splits the TRAINING decisions again, 75/25,
selects on the inner-validation part, and never touches the test fold until
the selected subset is refitted on the whole training fold and scored once.
The naive full-data selection is run too and labelled optimistic, because the
gap between the two IS the selection bias.

The criterion is the inner-validation **mean log-likelihood per decision**,
not top-k. `MODEL_SPEC.md` §9.3 says top-k is not the headline and Train
§3.8.1 p.69 says "percent correctly predicted" "should actually be avoided";
selecting on it would make it the estimand. Selecting on a different quantity
from the one reported also weakens — it does not remove — the selection bias
in the reported top-k.

Forward and greedy rather than exhaustive, for honesty rather than compute. At
477 decisions an exhaustive search over 2^13 subsets is affordable to run and
not affordable to believe: the best of 8,192 subsets on a finite validation
fold is the maximum of 8,192 noisy numbers, and its selected gain is biased
upward by roughly the spread of that noise. Forward selection with a stopping
rule looks at 36 and stops when the criterion stops improving.

**4. The vintage rule applies to anything time-varying, and only to that.**
`permit_units_total` and `permits_yoy_pct` move year to year, so each is read
at the panel year **strictly earlier** than `open_year`, and a decision with
no earlier panel year is dropped — the discipline `ingest/cbp_detail` applies
to warehousing. §7. The other thirteen cannot carry that failure; see §2.4.

Everything is 50 paired re-splits, 60/40 over decisions, seeds `SEED + r`
imported from `choice_runner`, every arm refitted inside every repeat, on the
`core` restricted frame (**477 decisions, 191 held out**) — not on the
483-decision MWPVL-expanded panel that `refit_expanded.json` and
`panel_experiments.json` use.

**Anchor check.** The published four columns on the **full** frame (`anchor`
stage, 483 decisions, 193 held out) reproduce `panel_experiments.json`'s
`combined` arm to four decimal places: large-metro top-10 lift **6.2585x**
against `combined`'s **6.2585x**, top-1 **10.7425x** against **10.7425x**, and
pooled Brier 0.0050363 against 0.0050363. The coefficient block reproduces
`refit_expanded.json` exactly: `establishments` mean 0.2991, median 0.2824;
`warehousing_establishments` mean **1.1912 [0.9558, 1.4901]**, median 1.1692.

> **Corrected 2026-09-15.** This paragraph used to anchor against
> `lift_by_market_size.json` — "large-metro top-10 lift 6.330x against the
> 6.31x recorded", and "top-1 11.78x against a recorded 12.20x, the 3.5% gap
> being the chance-rate definition". **6.33x and 6.31x match no current
> artefact at all**, and `lift_by_market_size.json` is formally retired: it
> carries a `superseded_by: panel_experiments.json` stamp, has no emitter in
> the tree, no `run_id`, one split, and the tie-broken empirical null that the
> chance-rate excuse was invoking. The anchor is now taken against
> `panel_experiments.json`, where it is exact rather than approximate, so the
> chance-rate caveat is no longer needed — this file and that one both use the
> analytic `min(k,J)/J` from `panel_strata`.

### The specification limit this search runs into, stated in advance

`choice.py` enforces `beta_k = exp(theta_k) > 0`. **A column that repels
cannot be expressed.** The optimiser walks it to the boundary and it reads as
worthless when it may be strongly informative with the other sign. Not
hypothetical: `median_home_value` and `diesel_pm` both have a plausible
negative story, and a percentage change in permits is signed outright, which
makes `beta'a` potentially negative and the probability undefined.

Three columns are therefore entered twice, as the level and as a positive
transform increasing in the other direction:

```
  median_home_value     also as  1 / median_home_value
  diesel_pm             also as  1 / diesel_pm
  permits_yoy_pct       as       1 + pct/100 = permits_t / permits_{t-1}
                        and as   its reciprocal
```

The permits transform is a re-expression, not a re-definition: `1 + pct/100`
is the gross growth ratio the percentage was computed from, strictly
increasing in it, and positive wherever defined. The two reciprocals are
**not** sign flips — `1/x` is a different functional form — and like the
levels they are intensive, which breaks the aggregation invariance
`MODEL_SPEC.md` §1 says the `ln(beta'a)` form exists to preserve. Both facts
are why they are reported as a workaround and not as a specification.

## 4. The result: every column, one at a time

477 decisions, 191 held out, 50 paired re-splits, **large metros (>100
alternatives) only**. `diff` is the paired difference in top-10 hit RATE
against the baseline fitted on the same split; W-T-L counts re-splits won,
tied and lost. `lo` is the share of re-splits on which the optimiser drove the
added column's coefficient to zero.

```
                                top-10    lift     diff    sd   W  T  L     lo
  baseline (4 columns)          30.47%   6.216x       --   --   --------   --
  ---------------------------------------------------------------------------
  + traffic_proximity           30.51%   6.224x   +0.038 0.41   3 45  2   0.26
  + diesel_pm                   30.47%   6.216x   +0.000 0.00   0 50  0   0.72
  + median_home_value           30.47%   6.216x   +0.000 0.00   0 50  0   0.90
  + vehicle_availability_total  30.47%   6.216x   +0.000 0.00   0 50  0   0.04*
  + bachelors_degree            30.47%   6.216x   +0.000 0.00   0 50  0   0.98
  + median_age                  30.47%   6.216x   +0.000 0.00   0 50  0   1.00
  + renter_occupied             30.47%   6.216x   +0.000 0.00   0 50  0   1.00
  + low_income_pct              30.47%   6.216x   +0.000 0.00   0 50  0   1.00
  + people_of_colour_pct        30.47%   6.216x   +0.000 0.00   0 50  0   0.88
  + inv_median_home_value       30.47%   6.216x   +0.000 0.00   0 50  0   1.00
  + inv_diesel_pm               30.47%   6.216x   +0.000 0.00   0 50  0   1.00
  + annual_payroll              30.45%   6.212x   -0.014 0.74   7 36  7   0.18
  + in_labor_force              30.25%   6.171x   -0.219 0.67   2 36 12   0.00*
  + employment                  29.89%   6.097x   -0.580 1.13   6 20 24   0.00
  + owner_occupied              29.57%   6.032x   -0.903 0.81   1 15 34   0.00*
  ---------------------------------------------------------------------------
  forward selection (nested)    29.85%   6.089x   -0.620 1.04   5 19 26
  forward + demographics        29.85%   6.089x   -0.620 1.04   5 19 26
  ---------------------------------------------------------------------------
  no warehousing (3 columns)    13.13%   2.678x  -17.372 4.26   0  0 50

  * NOT identified rather than estimated -- see section 2.2 and below.
```

**The whole table spans 0.94 of a percentage point**, from +0.038 to -0.903,
against a baseline of 30.47% and a no-covariate floor 17.4 points below.
**Ten of the fifteen arms score identically to the baseline on the large-metro
top-10 rate on every one of the 50 splits** — 0 wins, 50 ties, 0 losses, and a
lift equal to the baseline's to fifteen decimal places. On five of the ten the
optimiser set the new coefficient to zero on every split; on four more
(`diesel_pm` 0.72, `people_of_colour_pct` 0.88, `median_home_value` 0.90,
`bachelors_degree` 0.98) it did so on most of them and the surviving weight
was too small to move a ranking. The tenth,
`vehicle_availability_total`, is the numeraire entered twice and is not
identified at all — see §2.2 and point 3 below.

### Five things this table says

**1. The best column in the panel is worth +0.038 percentage points.**
`traffic_proximity` wins 3 re-splits, ties 45, loses 2. On top-1 it is
marginally better too — 5.13% against 5.05%, lift 10.47x against 10.30x — one
of only two candidates that improves both, the other being
`owner_occupied`, which buys its top-1 gain by losing 0.90pp of top-10 (point
4). It is also the column §2.1 showed has 9.2
distinct values per 200 alternatives, so a negligible effect is the *most* it
could have had.

**2. The positivity constraint is real, it bites, and it does not explain the
result.** Five candidates sit at the lower boundary on 100% of splits and four
more on 72% to 98% of them. `median_home_value` — the one ZCTA-grain, genuinely
independent candidate, the buildability proxy the theory asked for — has a
coefficient median of **3.5e-15** and is at the boundary on **90%** of splits,
and its held-out numbers are identical to the baseline's on all 50. The model
cannot say "expensive ZIPs are unbuildable"; it can only say "expensive ZIPs
are more attractive" or "expensive ZIPs are irrelevant", and it picks the
second.

That is exactly why the reciprocals exist, and **they change nothing.**
`inv_median_home_value` — which CAN say "cheap is attractive" — is at the
boundary on **100%** of splits and buys **+0.000 percentage points**, winning
none. `inv_diesel_pm` is at the boundary on 100% too. The
constraint costs this project something on paper and nothing measurable here,
and that is a stronger conclusion than leaving it untested: the specification
limit is genuine but it is not what is holding the model down.

**3. Three columns are not identified, and the artefact shows it.**
`vehicle_availability_total`, `in_labor_force` and `owner_occupied` correlate
1.000, 0.979 and 0.880 with the numeraire within metro. Their coefficients do
not go to zero like an uninformative column; they run away.

```
  arm / column                    median beta   2.5% - 97.5%      at upper
                                                                  boundary
  + in_labor_force                   5.09e12    3.5  - 9.6e19       82%
    ...its warehousing beta          5.02e12    4.7  - 1.0e20       82%
  + owner_occupied                      4.11    0.61 - 6.3e13       26%
  + vehicle_availability_total         12.86    5.2e-08- 3.8e08      4%
```

Read the **intervals**, not the medians: they span fourteen to nineteen orders
of magnitude. `in_labor_force` hits the upper boundary on 82% of re-splits and
drags `warehousing_establishments` up with it, to the same 5.0e12, because
only the RATIO of the two is pinned down. `owner_occupied`'s median looks
respectable at 4.11 and its 97.5th percentile is 6.3e13. A reader handed a
point estimate from any of these would report a number with no content.

This is `choice.py`'s documented property — only ratios are identified —
meeting a column that is very nearly a linear multiple of the numeraire. It is
reported, not fixed, because it is the correct answer: those columns carry no
information the numeraire does not already carry.

**4. The Brier pair, which `MODEL_SPEC.md` §9.1 makes the headline and top-k
is not.** Raw pair, never a skill score (Gneiting & Raftery 2007 §2.3). Over
the same 50 re-splits, all 191 held-out decisions, all strata:

```
  uniform-within-choice-set null          0.005549
  ---------------------------------------------------
  best three arms (+employment, both
    forward searches)                     0.005211
  baseline (4 columns)                    0.005218
  worst added column (+owner_occupied)    0.005219
  ---------------------------------------------------
  no warehousing, searched substitute     0.005330
  no warehousing, 3 columns               0.005372
```

**Fifteen added columns move the Brier score by at most 7e-6 in either
direction, on a null-to-model gap of 3.3e-4.** That is 2% of the distance the
four existing columns cover. The three arms that edge the baseline on Brier —
`+employment` and the two forward searches — are the same arms that LOSE on
large-metro top-10, which is the trade `NOTES_GBM_BENCHMARK.md` §5 found
between shortlist accuracy and per-case probability, reappearing at a
hundredth of the size.
`+owner_occupied` is the mirror image: worst on top-10 at -0.90pp and the
**best** arm on large-metro top-1 (5.31% against 5.05%, lift 10.84x against
10.30x). Both halves are reported because reporting one would be a choice of
metric made after seeing the answer.

**5. The two demographic columns do not predict siting in this panel, and
that is not the same as siting being demographically neutral.**
`low_income_pct` and `people_of_colour_pct` are each worth +0.000pp, tying the
baseline on all 50 splits. They
were held out of the headline search on purpose — a model that predicts where
a warehouse goes from who lives there is a different object from one that
predicts it from land and industry, and this project exists to help
communities evaluate siting decisions, so that inclusion is a choice to argue
in the open rather than one for a greedy search to make by itself. A third
search run WITH them in the pool lands on identical held-out numbers
(-0.620pp on the large-metro top-10 rate, 5-19-26). **But both columns are
county-grain with 9.2 distinct
values per metro** (§2.1). This is not evidence about environmental justice in
siting; it is evidence that this panel cannot see the question.

## 5. Honest forward selection makes the model WORSE on the large-metro top-10 rate, and that is a result about method

```
  forward selection, chosen inside the training fold
    LARGE-METRO (>100) top-10 hit rate   30.473% -> 29.852%
                                         -0.620pp   5 W 19 T 26 L
    POOLED        top-10 hit rate        52.419% -> 52.775%
                                         +0.356pp -- slightly BETTER
```

**The search loses 26 of 50 re-splits and wins 5 — on the large-metro stratum.**
That is the stratum this experiment is about (§3 rule 2: it is the only one
carrying information), and it is where the headline belongs. But the stratum
must be named every time, because **pooled across all choice-set sizes the same
comparison goes the other way**, by +0.36 points. Quoting "0.62 points worse"
unqualified is contradicted by a number in the same block of the same artefact.
*(The pooled contradiction is not an artefact of the old run: on the settled
run it is four times larger than the +0.08pp the superseded copy reported.)*

This is the cleanest statement of a data ceiling in the project, and it is a
measured result about **method** rather than about Amazon.

The search is not misbehaving. The inner-validation log-likelihood it
maximises genuinely does improve when a column is added — on the inner fold.
It just does not transfer. Adding a parameter costs more in estimation
variance than the column returns in signal, and at 286 training decisions with
a 72-decision inner-validation fold the criterion cannot see that. **A
selection procedure applied at this sample size overfits its own selection
step**, which is precisely why §3 rule 3 insists the search be nested and why
the naive variant is reported beside it.

**What the search keeps picking is the diagnosis restated.** Selection
frequency over the 50 re-splits:

```
  employment          43 of 50      r = 0.834 with establishments
  owner_occupied      34 of 50      r = 0.880 with households (numeraire)
  in_labor_force      24 of 50      r = 0.979 with households
  median_home_value    6 of 50
  diesel_pm            6 of 50
  ... every other candidate 5 or fewer
```

The three columns the greedy search reaches for most are the three most
collinear with columns already in the model. It is not finding new
information; it is finding **a second copy of the information it already has**,
which raises the inner-fold likelihood by re-weighting the numeraire and costs
held-out accuracy by spending a parameter on it. *(The settled run swaps the
order of the second and third — `owner_occupied` 34 and `in_labor_force` 24,
where the superseded copy had 35 and 24 the other way round. The three names
are the same three, and they are the same three that head the `r|hhold`
column of §2.)*

The **naive** selection — the same search allowed to see the whole frame, test
decisions included — picks
`households, land_area_sqmi, establishments, warehousing_establishments,
employment, in_labor_force, median_age`: the same two collinear columns plus
one that was an exact no-op on its own (§4). It is recorded in the artefact
under `naive_selection` with a warning attached. A reader shown only that set
would conclude the search had found something.

## 6. The substitution test: nothing replaces the warehousing count

This is the circularity escape route
[`NOTES_LEAKAGE_DECISIVE.md`](NOTES_LEAKAGE_DECISIVE.md) §8 wanted. It is
closed.

```
                                       top-10   lift     vs baseline    W  T  L
  baseline, with warehousing           30.47%  6.216x           --      -------
  3 columns, no warehousing            13.13%  2.678x      -17.372pp    0  0 50
  best searched set, no warehousing    19.53%  3.983x      -10.964pp    0  0 50
```

A forward search over all thirteen time-invariant candidates with
`warehousing_establishments` **forbidden** recovers **6.41 of the 17.37
points** the covariate is worth — 37% — and still loses every one of the
50 re-splits. On top-1 it is worse: 1.86% against the baseline's 5.05%, lift
3.80x against 10.30x, so the substitute set is markedly worse at picking the
ZIP than at drawing a shortlist.

**The reading.** Just over a third of what `warehousing_establishments`
contributes can be reconstructed from land, ACS and EJScreen columns; nearly
two thirds cannot. That
is consistent with the covariate being what
[`NOTES_LEAKAGE_DECISIVE.md`](NOTES_LEAKAGE_DECISIVE.md) concluded it is —
genuine agglomeration, audited at 79% of its value on strictly pre-opening
vintages — and it is **not** consistent with it being a buildability proxy in
disguise, which is the hypothesis §1 set out to test. If it were mainly a
proxy for "this ZIP is industrial land", a traffic or land-value covariate
would have picked up most of it. None picks up half.

So the circularity risk cannot be engineered away by substitution. It has to
be lived with at the size `NOTES_LEAKAGE_DECISIVE.md` measured, or removed
with a column this project does not yet have — §10 item 1.

## 7. Permits: the only time-varying candidates, and what asking for them costs

Building permits are the only panel columns that are both **time-varying** and
**forward-looking**, and nothing in the project used them. Two are tested and
they measure different things: `permit_units_total` is a level (how many
housing units the county permitted last year) and `permits_yoy_pct` is a flow
and the panel's only leading indicator (whether permitting is accelerating).
The flow is the more interesting for a siting question — every other candidate
says how much of something is already in a place; this one says which way the
place is moving.

376 decisions, 150 held out, 50 paired re-splits, **large metros only**, all
arms refitted inside the permit frame:

```
                                top-10    lift     diff    sd   W  T  L     lo
  baseline (4 columns)          29.46%   6.319x       --   --   --------   --
  + permit_units_total          29.46%   6.319x   +0.000 0.00   0 50  0   0.04
  + all three permit columns    29.46%   6.319x   +0.000 0.00   0 50  0
  forward (nested) over permits 29.46%   6.319x   +0.000 0.00   0 50  0
  + permits_yoy_ratio           29.46%   6.319x   +0.000 0.00   0 50  0   1.00
  + inv_permits_yoy_ratio       29.46%   6.319x   +0.000 0.00   0 50  0   1.00
  naive best + permits          29.10%   6.242x   -0.358 0.64   0 37 13
```

**`permit_units_total` is one of the very few candidates the model actually
uses, and it still buys nothing.** Its coefficient is non-zero on 96% of
re-splits — median 0.178, [0.007, 0.397] — against `median_home_value`'s 90%
at the boundary. That is a *stronger* null than the rest of §4: this is not
"the optimiser discarded the column", it is "the optimiser weighted the column
and the held-out large-metro top-10 rate did not move at all" — 0 wins, 50
ties, 0 losses, a lift identical to the baseline's to fifteen decimals. (It
does move large-metro top-1 from 5.24% to 5.27% and pooled top-10 from 51.11%
to 51.17%, which is the same size of nothing.) The
nested search over the three permit transforms picks exactly this column and
lands in the same place.

**Both directions of the acceleration signal are empty.** `permits_yoy_ratio`
sits at the boundary on 100% of re-splits and its reciprocal likewise, so
"permits are booming here" and "permits are collapsing here" are equally
uninformative once the level is available. Both are county-grain with 7.9
distinct values per metro (§2.1), so this was the predicted outcome.

**`naive best + permits` is the §5 overfit showing up again**, at -0.36pp
losing 13 of 50 and tying 37. Its `warehousing_establishments` coefficient
runs to 1.6e13 and sits at the UPPER boundary
on 100% of re-splits, because the naive set contains `in_labor_force` and the
pair is not identified (§2.2). It is reported because dropping an arm that
misbehaves is how a search is rigged. *On the superseded copy of this artefact
this arm cost -1.10pp and lost 32 of 50; the settled run has it a third that
size. The direction and the mechanism are unchanged.*

### 7.1 The attrition, which is the point

Requiring a **pre-opening** permit vintage is expensive, and the cost is not
random. Measured by `covariate_permits.attrition`:

```
  decisions   477 -> 376   (101 lost)
  ZCTAs     21,768 -> 9,730  (44.7% of the frame has a permit value at all)

  market-size mix          kept     lost
    small  <=25           0.138    0.198
    mid    26-100         0.340    0.515
    large    >100         0.521    0.287

  median choice set        106       47

  ZCTA mean            has permits   no permits
    households              7,908.6      3,554.2
    establishments            531.2        212.2
    land_area_sqmi             44.3         78.0
```

**The permit frame is not a random subsample.** ZCTAs with a permit value have
2.2x the households and 2.5x the establishments of those without, and half the
land area — the join keeps the dense urban end of each metro and drops the
thin rural end. Dropping thin alternatives makes the ranking problem
structurally **easier**, so a permit arm that scored better than a baseline
fitted on the full frame would be measuring the attrition and not the column.
That is why every arm in this stage is refitted inside the permit frame and
compared only to a baseline in the same frame.

101 of 477 decisions are lost, disproportionately from mid-size markets (51.5%
of the losses against 34.0% of the survivors). 24 are lost to the vintage rule
alone — they opened in 2018, and the panel starts in 2018, so no strictly
earlier year exists — and a further 24 because the chosen ZCTA itself has no
permit value and is filtered out of the frame.

## 8. The GBM: NOT COMPLETED, and what that does and does not leave open

**This measurement was built, launched, and did not finish. It is reported as
unfinished rather than dropped, because a missing section with no explanation
is how a null result gets quietly improved.**

`src/siting_atlas/models/covariate_gbm.py` runs the identical LightGBM
`lambdarank` learner as `gbm_benchmark` — `_fit_gbm`, `GRID` and the
temperature-calibrated softmax are IMPORTED from it rather than copied, so
only the columns differ — over the same 50 paired re-splits, on three column
sets: the baseline four, the searched `best` seven, and all nineteen. It
reached **45 of 50 re-splits** and was then starved to under 2% of a core by
concurrent jobs on the shared machine. It writes its artefact only at the end,
so there is no partial result to report — the same design flaw §11 records
fixing in `covariate_search`, which was not fixed here before the run started.
`outputs/metrics/covariate_gbm.json` does not exist.

**What the question was.** If the extra columns carry signal that
`ln(beta'a)` cannot express — a threshold, a non-monotonicity, or the negative
sign `beta = exp(theta) > 0` forbids — a tree would find it and the logit
would not. A tree is indifferent to both the positivity constraint and the
collinearity of §2.2, so it is the right instrument for exactly the two
failure modes this file diagnoses.

**One design decision inside it is worth keeping even though the run did not
finish.** The all-columns arm is run for the GBM and **not** for the logit.
That is a judgement, not a saving: the 19-column logit contains three columns
the model is not identified in (§2.2), so its coefficients are arbitrary along
a ray and its fit is the optimiser wandering a flat likelihood — measured at
**213 seconds per fit against 2.8 for the baseline**. Reporting it would be
reporting an optimisation artefact.

**What is already known without it, and what is not.**
[`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) §5 ran this learner on the
baseline four columns and measured the flexible-learner premium at +0.98 to
+1.34 top-10 hits of 38, bought at 1.2 hits of top-1 and a worse Brier. That
result stands and is not disturbed here. What is **not** known is whether that
premium grows when the learner is given the other fifteen columns. §2.1
predicts it should not — a tree cannot manufacture within-metro variation that
a county-grain column does not contain — and §4 shows the GBM's two advantages
over the logit, non-monotonicity and freedom from the positive-weight
constraint, aimed at columns that are mostly either county averages or
numeraire copies. **That is a prediction this file makes and does not test.**
Re-running the command in §12 on a quiet machine settles it in about 40
minutes.

## 9. Verdict: the ceiling is real, and it is a ceiling on GRAIN

**The data ceiling is real, it was not an artefact of only ever testing four
columns, and the reason is now structural rather than statistical.**

```
  WAS THE CEILING AN ARTEFACT OF TESTING ONLY FOUR COLUMNS?   No.
      Fifteen more were tested on the same frame, the same seeds and the
      same 50 paired re-splits. The best is worth +0.038pp of large-metro
      top-10; the whole table spans 0.94pp; ten of fifteen arms tie the
      baseline on all 50 splits.

  IS THE REASON "AMAZON SITING IS UNPREDICTABLE"?             No, and this
      is the upgrade over the GBM benchmark's verdict. Six of the fifteen
      candidates are COUNTY values with 9.2 distinct values across a
      200-ZIP choice set and mathematically cannot answer a ZIP-level
      question. Five more are 0.84-1.000 collinear with the numeraire and
      the model is not identified in them. Two more are the same CBP file
      the model already reads. That leaves ONE genuinely new ZCTA-grain
      column, median_home_value, and the positivity constraint pins it at
      zero in the level and the search rejects its reciprocal.

  SO WHAT WOULD WORK?                                          A covariate
      that is (a) measured AT ZCTA GRAIN, (b) not a linear multiple of
      households, and (c) expressible with a positive weight. The
      network-proximity pair satisfies all three and is the only covariate
      family in this project that moves a metric with a consistent sign
      (top-5 +1.23pp, improved on 42 of 43 re-splits, per
      panel_experiments.json). Industrial land area per ZCTA would satisfy
      all three; data/interim/osm_landuse.parquet holds exactly that
      (industrial_sqmi, warehouse_sqmi) for 293 ZCTAs, which is the pilot
      and not the nation.

  AND THE SELECTION PROCEDURE ITSELF OVERFITS.                 Honest
      nested forward selection scores -0.620pp ON THE LARGE-METRO TOP-10
      RATE (+0.356pp pooled), losing 26 of 50 re-splits.
      It reaches for employment (43/50) and owner_occupied (34/50), two of
      the three most collinear candidates. At 286 training decisions,
      choosing covariates costs more than the covariates return.
```

**The sentence for the write-up:** *the four columns the model reads, fifteen
more from the panel, a nested covariate search and a gradient-boosted ranker
all place the true ZIP in the top ten of its large metro about 30% of the time
against a 4.9% chance rate. The reason the fifteen added columns cannot move
it is not that warehouse siting is unpredictable; it is that six of them are
county averages with nine distinct values per metro, five are near-copies of
the numeraire, two are the CBP file the model already reads, and the panel
contains exactly ONE independent ZIP-level covariate — which the positivity
constraint then pins at zero.*

## 10. What this does NOT settle

Ranked by how much each would move the answer.

**1. Industrial land at ZCTA grain is the missing column and it has not been
tested.** The theory in §1 was about *buildability*, and nothing in the panel
measures it: `data/interim/osm_landuse.parquet` carries `industrial_sqmi` and
`warehouse_sqmi` per ZCTA, which is precisely the right variable at precisely
the right grain, for **293 ZCTAs** — the pilot frame, against 22,882 in the
national one. Extending that ingest nationally is the single highest-value
follow-up this file identifies, and it would also give §6's substitution test
a candidate that could actually win.

**2. EJScreen at tract grain is recoverable and was not recovered.**
`warehouse/optional.py` aggregates EJScreen to county only because "no
tract-to-ZCTA crosswalk exists in L1". `traffic_proximity` and `diesel_pm` are
published per tract; a tract-to-ZCTA crosswalk would raise them from 9.2
distinct values per metro to something ZIP-level, and this file's verdict on
those two columns would have to be re-taken. **The verdict here is on the
panel's version of the column, not on the underlying EJScreen measurement.**

**3. The positivity constraint was worked around, not removed.** Reciprocals
are a different functional form, not a sign flip. A specification allowing
signed coefficients — which would cost the `ln(beta'a)` aggregation invariance
`MODEL_SPEC.md` §1 defends — would test `median_home_value` properly. The
evidence here is that it would not change much (`inv_median_home_value` buys
+0.000pp and never leaves the boundary) but that is an argument from one
transform, not a proof.

**4. The 50 re-splits are not independent and the W-T-L records are not a sign
test.** They resample the same 477 decisions, so the reported sd understates
true sampling variability. There is no p-value in this file and there should
not be one. A percentile interval over re-splits is **not** a standard error.

**5. The splits are not clustered by metro.** Decisions in the same metro
share a choice set and random splitting puts them on both sides, which
inflates every arm's absolute level equally. The comparison survives; the
levels are optimistic. Matched deliberately to `choice_runner`.

**6. Selecting on log-likelihood and reporting top-k weakens the selection
bias without removing it.** The nested search never sees the test fold, but
the *decision to report the large-metro stratum* was made before the run and
the stratum cuts were inherited from an existing artefact, which is the
defence offered; it is not the same as pre-registration.

**7. Every time-invariant column shares one post-decision vintage.** §2.4. The
comparison between arms is clean; the absolute level of all of them,
*including the published baseline*, rests on ACS 2019-2023 and EJScreen 2024
values used to score openings from 2018 onward.

## 11. Artefact state: which stages ran, and which did not

Stated explicitly because an unexplained empty field is not an honest
artefact. `outputs/metrics/covariate_search.json` carries a `stage_ledger`
recording the same thing machine-readably.

```
  column_audit      PRESENT   section 2
  anchor            PRESENT   section 3, the reproduction check
  core              PRESENT   sections 4-6, all 20 arms, 50 re-splits
  naive_selection   PRESENT   section 5
  permits           PRESENT   section 7, 7 arms, 50 re-splits, plus
                              permit_attrition
  ------------------------------------------------------------------
  covariate_gbm     ABSENT    outputs/metrics/covariate_gbm.json was not
                              written. The run reached 45 of 50 re-splits
                              and was starved out. Section 8 says so and
                              gives the command that finishes it.
```

The machine-readable `stage_ledger` in the artefact marks every stage
`ran_this_invocation`, `carried_forward` or `absent`. A stage is only ever
`ran_this_invocation` for the call that ran it; a later call that reuses it
downgrades it to `carried_forward`, so the artefact can never claim to have
been regenerated when it was not.

On the 2026-09-15 re-run **all five stages carry `ran_this_invocation`** —
nothing in the current artefact is carried forward. An earlier copy of the
file had `anchor` and `core` reused from a previous invocation at the same
seed, which was defensible but is no longer the state of the file. **If any of
this module's scientific code changes, the affected stages must be re-run; the
`stage_ledger` records which is which so that is checkable.**

> **Resolved, 2026-09-15.** This section previously recorded an internal
> disagreement: `anchor` and the top-level `facilities` field said **687**
> while `core` and `permits` said **694** in `coverage.facilities_offered`,
> with no way to tell from the file which loader each stage had used. **The
> completed re-run resolves it in favour of 687**, which is the correct count
> (693 CSV rows minus the six `E_operating_by` exclusions). The string `694`
> does not occur anywhere in the artefact, and every stage's drop ledger now
> balances against the same 687:
>
> ```
>   anchor    687 − 13 − 142 − 49                = 483 decisions
>   core      687 − 19 − 142 − 49                = 477 decisions
>   permits   687 − 72 − 142 − 49 − 24 − 24      = 376 decisions
> ```
>
> Everything in §§4-7 was a paired within-stage comparison and was unaffected
> by the disagreement either way. What the re-run changed is the *levels*: the
> headline forward-selection penalty moved a tenth of a point (−0.72 → −0.62),
> and the two largest movers were `no warehousing` (−17.89 → −17.37) and
> `naive best + permits` (−1.10 → −0.36). No sign flipped in §§4-7; §3's
> core-vs-anchor **lift** comparison did, and says so.
>
> **What is NOT resolved is how the two versions came to share a stamp.** The
> emitter takes `run_id` and `written_at` from `common/log_json.write_json`,
> which spreads the payload *after* the two stamp keys — and because
> `covariate_harness.load()` reads the previous artefact back in whole, the
> previous run's `run_id` and `written_at` are in the payload and shadow the
> fresh ones. So a resumed run inherits the old id and the first write's
> timestamp for the life of the file. Until that is fixed, `run_id` cannot be
> used to tell two versions of this artefact apart; check
> `facilities: 687` and the `stage_ledger` instead.

The staged design exists because of that episode: `run()` persists the
artefact after **every** stage rather than once at the end, and `--stages`
lets a stage be run alone against an existing artefact. An earlier monolithic
version discarded forty-five minutes of completed, correct work when it was
interrupted.

## 12. How to reproduce

```
  # everything, ~50 min on a quiet six-core box, hours on a busy one
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.covariate_search

  # one stage at a time, against the existing artefact
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.covariate_search \
      --stages permits --workers 5

  # the flexible-learner comparison on the searched column sets
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.covariate_gbm
```

Requires `data/interim/cbp_detail.parquet` and
`data/external/facility_panel/national_facilities_expanded.csv`; the runner
raises naming the ingest command rather than quietly fitting a
non-comparable model.

## 13. Related

- [`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) — the data-ceiling
  finding this extends, and the §8 item 2 caveat that commissioned it.
- [`NOTES_LEAKAGE_DECISIVE.md`](NOTES_LEAKAGE_DECISIVE.md) — the circularity
  audit whose escape route §6 tests and closes.
- [`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) — the vintage
  trap §3 rule 4 obeys and §2.4 distinguishes from time-invariance.
- [`NOTES_EXPANDED_REFIT.md`](NOTES_EXPANDED_REFIT.md) — the 483-decision
  panel every arm here is fitted on.
- [`NOTES_gneiting_raftery_2007.md`](NOTES_gneiting_raftery_2007.md) — why the
  Brier pair is reported raw and never as a skill score.
- `outputs/metrics/panel_experiments.json` — the concurrent, separately owned
  network-proximity experiment whose ZIP-level covariates §2.1 cites as the
  confirming case.
