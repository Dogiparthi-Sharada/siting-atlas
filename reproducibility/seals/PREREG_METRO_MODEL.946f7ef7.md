# Pre-registration — the metro-level entry model

**Written 2026-09-15, BEFORE the model was fitted.** Committed to disk with a
timestamp for exactly that reason. Everything below — sample, covariates,
metric, baselines, and what each outcome means — is fixed in advance.

This document exists because the project has already measured what happens
when you choose after seeing the answer: an honest nested forward selection,
choosing covariates inside each training fold, came out **0.72 points WORSE**
than adding nothing (`outputs/metrics/covariate_search.json`). Selection is
itself a parameter. Choosing a FRAMING after seeing a result is the same error
one level up, and it is the error this file is here to prevent.

---

## 1. The question

> At what geographic resolution can free public data reconstruct a private
> siting decision, and where does that resolution fail?

Two grains, one question:

```
  WITHIN a metro   which ZIP gets the station?      ALREADY MEASURED: it fails
  BETWEEN metros   which metro gets one next?       THIS TEST
```

## 2. The hypothesis, and the mechanism that generates it

**H1. The metro-level model will out-predict its baseline by more than the
ZIP-level model out-predicts its own.**

This is not a hope. It is what the project's own measured diagnosis predicts.

A conditional choice model uses only variation *within* a choice set. The
project measured a threshold on that variation — the within-metro coefficient
of variation — over 21 covariate terms
(`outputs/metrics/gravity_network.json`, `terms.dispersion`):

```
  cv below 0.6   ->  coefficient lands on the boundary   21 of 21
  cv above 1.3   ->  coefficient is interior             21 of 21
  nothing in between
```

Six of the fifteen tested covariates are county figures broadcast to every
ZCTA in the county — about **9 distinct values across 200 candidate ZIPs**.
They cannot rank ZIPs. **Their variation is between counties, and therefore
between metros, which is precisely the variation a metro-level model uses and
a ZIP-level model discards by construction.**

A second, independent line points the same way. The hazard model was revived
on 6.7x the events with real opening dates and did not move (AUC 0.6894 ->
0.6832, calibration beaten by a constant in 0 of 17 comparisons,
`outputs/metrics/hazard_revival.json`). Its structural defect is that **one
opening switches on a median 39 ZCTAs**, and no radius between 8.3 and 45
miles brings that below 14. At metro grain, one opening is one metro: the
violation does not exist.

**H0.** The metro model performs no better than its baseline, and free public
data cannot predict siting at any grain tested.

## 3. Sample — fixed now

```
  unit             CBSA x year
  window           2018-2025
  universe         all 935 CBSAs present in panel.parquet, NOT only the 195
                   with a known opening. The 740 that never received one are
                   the comparison group and excluding them would be selection
                   on the outcome.
  event            >= 1 delivery station opens in that CBSA in that year
  facility source  data/external/facility_panel/national_facilities_expanded.csv
                   551 dated facilities across 195 CBSAs
  observed         openings per year range 25 to 106, across 21 to 64 metros
```

Approximately **7,480 metro-years and ~480 events**.

A facility with no numeric opening year cannot contribute an event and is
excluded from the event set; it is NOT dropped from the universe, and the
count is reported.

## 4. Covariates — fixed now, and chosen by mechanism not by trial

Everything here must be available **strictly before** the year being
predicted. This is not optional: the project has already documented a
covariate that contained its own outcome, and the guard against it being
defeated by a median 34 months
(`docs/research/NOTES_COVARIATE_LEAKAGE.md`).

**Tier 1 — the columns that failed at ZIP grain because they are coarse.**
This is the test of H1. They should work here for the same reason they failed
there.

```
  permit_units_total, permits_yoy_pct     construction activity
  wage_freight_handler, wage_all_occupations
  metro_employment
  traffic_proximity, diesel_pm            freight-corridor proxies
```

**Tier 2 — scale and demand.** Expected to dominate; they are the thing the
baseline already captures.

```
  households, population, median_household_income
```

**Tier 3 — the existing network, time-respecting.**

```
  facilities already open in the metro
  distance to the nearest existing facility OUTSIDE the metro
```

Tier 3 is included because the project measured that **Amazon densifies** —
67-77% of 2024-25 openings landed inside coverage that already existed
(`outputs/metrics/white_space.json`). A model that ignores the existing
network would be ignoring the single strongest regularity found.

## 5. Model and baselines — fixed now

Two model forms, both reported:

- **Logistic**: P(at least one opening in metro m, year t)
- **Poisson / negative binomial** on the COUNT of openings, since 2020 and
  2021 saw 104 and 106 openings across 49 and 53 metros — several metros take
  more than one.

**Baselines, and the honest one is the second:**

```
  1  uniform across metros                 the no-information floor
  2  rank by households                    THE ONE THAT MATTERS
  3  rank by facilities already present    the densification null
```

Baseline 2 is the real test. At ZIP grain the equivalent — a raw warehouse
count with nothing fitted — matched the fitted model to within 0.36 hits of
38. **If the metro model cannot beat "rank by population", it has not
worked**, whatever its absolute accuracy.

## 6. Evaluation — fixed now

```
  primary     out-of-time: fit through year t-1, predict year t, rolled forward
  secondary   50 paired re-splits, model refitted inside every repeat
  metrics     AUC; calibration (ECE) against the constant null; Brier and
              Brier pair; top-k against each baseline
  reporting   raw Brier and top-k against a uniform null, never a skill score
              (Gneiting & Raftery 2007 sec. 2.3, p.362: skill scores are
              improper)
```

**Out-of-time is primary, not the re-splits.** The question is "which metro
next year", so the evaluation must be the same shape as the question. A random
re-split would let the model see 2025 while predicting 2021.

**Stratify by metro size tier** and report distinct-metro n per tier. Pooling
across heterogeneous strata is a Simpson's-paradox trap this project has
fallen into twice, the second time inside a standardisation.

**A percentile spread across re-splits is not a standard error.** Measured
here: a metro-clustered bootstrap came out 24-28% WIDER than the re-split
spread on more data (`outputs/metrics/network_inference.json`).

## 7. What each outcome means — both written before the result

**If H1 holds** — the metro model beats "rank by population" out of time, and
by a wider margin than the ZIP model beat its own baseline:

> Free public data predicts regional expansion but cannot discriminate within
> a metropolitan area. The boundary sits between the county and the ZIP code —
> exactly where most US public data stops being published. A community can
> learn that its region is on the list; it cannot learn that its neighbourhood
> has been chosen.

**If H0 holds** — the metro model does not beat the population baseline:

> Free public data cannot predict siting at any grain tested. The ZIP-level
> failure is not a resolution problem but a general one: the variables that
> drive the decision are not public at any resolution.

**Both are complete findings.** The second is harder and arguably more
valuable, because it says the transparency gap is structural rather than an
artefact of one model's grain.

## 8. What would invalidate this test

Stated in advance so it cannot be explained away afterwards:

1. **Leakage.** Any covariate observed at or after the predicted year. The
   guard is a strict vintage check; if it cannot be enforced for a column,
   that column is dropped and the drop is counted.
2. **Selection on the outcome.** Restricting the universe to the 195 metros
   that received a facility would guarantee a flattering result and measure
   nothing.
3. **An unpaired comparison read as a result.** The project already has one:
   `mwpvl_clean` scores 6.78 against `combined`'s 6.26, but on 194 versus 258
   different decisions, with no paired test available. That gap is not a
   finding and neither is anything shaped like it.
4. **Beating only the uniform baseline.** Trivial at 935 metros. Baseline 2 is
   the bar.
5. **A result driven by 2020-21.** Those two years hold 210 of ~480 openings —
   the pandemic build-out. Report with and without them.

## 9. Success criterion, stated numerically

**H1 is supported if**, out of time, the metro model beats the households
baseline on AUC in a majority of held-out years AND its calibration is at
least as good as the constant null in a majority of years.

That second clause is deliberate and it is where the hazard model died: it
lost 17 of 17 calibration comparisons while scoring AUC 0.689. **Ranking
without calibration is not prediction** — it tells a county it is more likely
than its neighbour and cannot tell it whether that means 5% or 40%.
