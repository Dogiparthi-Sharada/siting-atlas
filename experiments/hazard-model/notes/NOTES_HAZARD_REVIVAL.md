# Reviving the retired hazard model on the expanded panel

**Run:** `PYTHONPATH=src .venv/bin/python -m siting_atlas.models.hazard_revival`
— ~37 s single-threaded. *(That command no longer runs: the module and its
five helpers moved to [`../code/`](../code/) when the experiment was retired
and are not importable as `siting_atlas.models.*`. See `../../README.md`,
"Running any of this again".)* It refuses to proceed if the re-derived target
disagrees with `panel_expanded.parquet` on a single cell
(`provenance.target_rebuild_check`: 200,219 enabled cells, 0 mismatches).
`ruff check src tests` clean; `pytest tests -q` 796 passed, 2 xfailed.
(Recorded 2026-09-15, before 11 test files retired to `experiments/`; the
live suite is now 660.)
**Artefact:** `../artefacts/hazard_revival.json`.
**Baseline, never overwritten:** `../artefacts/hazard_report.json`.
**Date:** 2026-09-15. Every figure below is read off the artefact.

## The one-line answer

**The retirement stands.** The negative finding survives on **6.7 times** the
events (812 → 5,441) and on real opening dates instead of OSHA upper bounds.
That is a
*stronger* result than retiring the model on 39 events, because the obvious
objection — "you never gave it enough data, or real dates" — has now been
answered with a measurement rather than an argument.

It would have been the same sentence had the AUC gone up. It did not.

## 1. What changed since the retirement, and what did not

| | retired run | this run |
|---|---|---|
| panel | `panel.parquet`, 43-facility pilot | `panel_expanded.parquet`, 687 loadable facilities |
| dates | OSHA "operating by" upper bounds | MWPVL stated openings on 545 of them |
| events (ZCTA-quarters) | 812 | 5,441 |
| independent episodes (train) | 28 | 436 |
| events per parameter, effective | 5.6 (floor 10, **failed**) | 87.2 (**cleared**) |
| **ZCTAs one opening switches on** | median 58 | **median 39** |
| **the likelihood's independence assumption** | **violated** | **still violated** |

Two handicaps removed, one untouched — and the untouched one is the reason
for the retirement.

---

## 2. The four-way comparison

Held-out-by-unit split, the same `split_by_unit` seed the retired run used.
`AUC_t` is the out-of-time hold-out at `t = 19` (2022Q4), refitted.

```
  arm                    events  episod     AUC     Brier      null      ECE  nullECE   AUC_t
  RETIRED (pilot)           812      28  0.6894  0.019522  0.019614  0.00863  0.00005  0.5551
  new_dates_3cov           5441     436  0.6832  0.021163  0.021291  0.00494  0.00057  0.6323
  new_dates_5cov           3516     866  0.6608  0.122635  0.129024  0.02144  0.01614  0.4619
  old_dates_3cov           3178     147  0.6431  0.014664  0.014679  0.00376  0.00046  0.5596
  old_dates_5cov           2038     370  0.6459  0.045154  0.045693  0.00820  0.00673  0.4527
  new_dates_4cov           5571     434  0.6461  0.030685  0.030819  0.00647  0.00112  0.5458
  matched_new_3cov         2666     140  0.6513  0.013360  0.013384  0.00308  0.00007  0.5924
  matched_old_3cov         3131     141  0.6556  0.014793  0.014813  0.00380  0.00050  0.5658
```

**Brier and ECE are not comparable across rows.** Each arm has a different
target, test set and base rate, so each carries its own constant-predicting
null scored on its own test rows; the model-against-its-own-null *pair* is
the comparison, the same rule `catchment_band` ([`../code/catchment_band.py`](../code/catchment_band.py),
formerly `warehouse/catchment_band`) applies to the radius sweep. AUC is comparable only in the weak sense that 0.5 means the
same thing everywhere.

### Did AUC move off 0.689?

No. The comparable arm — expanded panel, MWPVL dates, the same three
covariates — is **0.6832** against **0.6894**. Across all seven arms and all
three hold-outs the AUC range is **0.4527 to 0.7515**, median **0.6459**.
Both figures above 0.70 are out-of-area scores on 53 and 63 events; the
0.4527 is an out-of-time score, worse than a coin flip at the task the model
exists to do.

### Did calibration ever beat the constant null?

**No. Zero wins in seventeen comparisons** (`calibration_against_constant`
in the artefact). On the comparable arm the model's ECE is **8.7x** the
null's; on the matched-new arm, **47.3x**. Its best is 1.2x worse than a
constant, in the five-covariate arm — and that arm's event rate is 15%, so
the constant it loses to is a much less trivial one. A model whose
probabilities are worse than one number repeated is not a probability model.

---

## 3. The date control, and why it is weaker than it sounds

Is any change attributable to the *dates* rather than to the extra *events*?
Answering that needs the same facilities dated two ways, and the data only
half supports it.

An OSHA bound exists only where an inspection happened. Of 687 loadable
expanded facilities, **139** match an OSHA building at all — and **100 of
those are the national rows, whose dates were derived from the bound in the
first place.** So the set of facilities whose date actually *moves* between
the two datings is **30**.

```
  arm        facilities dated   facilities whose date differs
  new                     545   --
  old                     139   39 are MWPVL-linked, 100 are the bound already
  matched pair            130   30
```

Two contrasts, neither clean and strong at once:

**Full frame (545 against 139).** AUC +0.0401 for the new dates, ECE +0.00118
(worse), out-of-time AUC +0.0727. But the facility set changes as well as the
dates, so this measures "more stations *and* better dates" and cannot
attribute either.

**Matched 130 facilities.** AUC **-0.0043** — the *new* dates score
marginally *worse*. ECE -0.00072 (marginally better). Out-of-time AUC
+0.0266. Every one of these is inside noise on a 30-facility contrast.

**Verdict on the dates: no measurable effect, on a control too weak to
detect a small one.** Stating that is the whole reason the control was run:
without it the +0.04 AUC in the full-frame contrast would have been reported
as a dating effect, and it is not.

### The bound really is about three years late — re-measured here

On the 30 facilities carrying both a stated MWPVL opening and an OSHA bound:

```
  median gap    10.5 quarters  =  31.5 months
  mean gap      12.0 quarters  =  36.0 months
  over a year   80% (24 of 30)
```

Independently consistent with the 34-month / n=42 / 88% figure that
motivated the run. The 100 national rows show a gap of exactly zero, which
is an *identity* (the file was built by classifying the OSHA extract) and
not a measurement; the artefact separates the two blocks for that reason.

### The counter-intuitive consequence nobody should skip

Correcting a date **backwards** does not add events — it *removes* them. An
opening moved from 2021 to 2018 falls out of the front of the window, its
catchment is enabled at `t = 0`, and `risk_set._drop_left_truncated` removes
it. On the matched 130:

```
                  opened before 2018   inside window
  stated dates                    14             103
  OSHA bounds                      7             107
```

which is why `matched_new_3cov` has **2,666** events against
`matched_old_3cov`'s **3,131**, on identical facilities. Better dates, fewer
events. Anyone expecting the true-date arm to be the larger one has the sign
backwards.

---

## 4. The covariate decision: three, four or five

`panel_source.REAL_COVARIATES` was cut from five to three on two arguments.
One is dead and one got worse.

**Counting — DEAD.** The cut cited *"49 delivery stations, 44 opening inside
the window"*, a pre-expansion number. The expanded frame attaches **540**
facilities, 477 opening inside the window; effective events per parameter is
**87.2** at three covariates and **123.7** at five, against a floor of ten.
The power objection to five covariates no longer exists.

**Coverage — ALIVE, AND WORSE.** Measured on `panel_expanded.parquet`:

```
  households                99.9%
  establishments            91.5%
  median_household_income   90.6%
  permits_yoy_pct           55.4%
  rent_index_yoy_pct         9.5%     <-- was quoted at 30% on the pilot
```

`rent_index_yoy_pct` costs **82.8%** of the scoped rows, and the loss is not
random: Zillow publishes for dense urban ZIPs, so the rows it deletes are the
sparse ones — precisely the contrast the model is meant to measure. The
five-covariate arm's event rate is **15.2%** against the three-covariate
arm's **2.2%**: not a smaller sample of the same population but a different
population, and its out-of-time AUC of **0.4619** (worse than chance, Brier
skill **-0.96**) is what that looks like.

**Decision: all three specifications are reported, and the one this evidence
supports is four, not five.** `new_dates_3cov` is the only arm comparable to
the retired run; `new_dates_5cov` restores both, as asked, and pays the
coverage bill in full so the bill is visible; `new_dates_4cov` restores
`permits_yoy_pct` only — the covariate the power argument blocked and the
coverage argument does not — costs 32% of rows instead of 83%, and changes
nothing (AUC 0.6461, ECE 5.8x the null).

Restoring covariates did not rescue the model on any arm. Adding the two
back moved AUC **down**, from 0.6832 to 0.6608.

**One caveat on the reconstruction.** The original five-tuple predates
version control and is not recoverable as a literal.
`hazard_revival_frames.COVARIATES_ADDED` reconstructs it from `panel_source`'s
own docstring (which names `rent_index_yoy_pct` as a casualty) and from
`warehouse/panel.py` (which records exactly two "rates of change" columns,
these two). If the original fifth was something else, the coverage finding
stands and the label is wrong.

---

## 5. The thing that is not fixed, quantified

> "The likelihood assumes each decision maker's choice is independent of
> that of other decision makers." — Train (2009) §3.7.1, printed p. 61.

One leasing decision. Many rows.

```
  radius   ZCTAs      ZCTAs per opening        ZCTAs whose   ZCTAs inside
  (miles)  covered  median   mean     max     switch-on it   2+ catchments
                                                 sets (med)
   8.3       5,260      14    19.8     170            8         42.2%
  12.7       7,956      30    40.5     263           12         55.1%
  15.0       9,113      39    52.4     317           13         58.4%   <- in use
  19.6      11,110      59    77.6     419           16         61.4%
  25.0      13,328      79   108.4     514           20         62.8%
  45.0      20,741     173   231.1     811           29         67.1%
```

**One opening switches on a median of 39 ZCTAs** at the radius in use, mean
52.4, max 317, against the retired run's 58 on the pilot frame. The number
came *down* and the problem got *worse*, and the reason is the last column.
On the pilot frame catchments were mostly disjoint, so a ZCTA's switch-on
date belonged to one station. Here **58.4% of covered ZCTAs sit inside two
or more catchments**, so only the earliest arrival registers an event
(median 13 ZCTAs per station, not 39) and a ZIP's switch-on quarter is now a
joint function of several buildings' decisions — a *second* dependence
layered on the first. Clustering the covariance on the CBSA, which every arm
does, reduces the damage and does not remove it: the unit of decision is the
building, not the metro and certainly not the ZIP.

**Did the radius change the answer?** No, and the radius did not move: every
fit is at the 15 miles `facilities.CATCHMENT_MILES` sets.
`outputs/metrics/catchment_band.json` found a 4.76x lever on enabled cells
across 8.3-45 miles on the *pilot* frame with the conclusion unchanged at
every radius. Re-measured on the expanded frame the lever on covered ZCTAs
is **3.94x**, and the per-opening count never falls below 14 and never
approaches one. There is no radius at which one opening is one observation.

---

## 6. Out-of-area, and a hole worth naming

Phoenix and Boise are the metros `common.metros` withholds. The retired run
called its transfer check a smoke test because those two metros held two
dated stations between them. On the expanded frame with MWPVL dates they
hold **122 ZCTAs, 53 events and 6 independent episodes** — still thin, but
no longer two decisions. `new_dates_3cov` scores AUC **0.7104** there,
Brier 0.018971 against a null's 0.019033, ECE **0.0111 against 0.00179**:
the best AUC of the whole exercise, and still six times worse calibrated
than a constant.

**The OSHA-dated arms could not run this test at all.** Not one of the 139
facilities carrying an OSHA bound sits in Phoenix or Boise, so there is no
enabled cell to score; the artefact records `out_of_area.ran = false` with
the reason rather than omitting it. That sharpens §3: the OSHA-only panel is
not a smaller version of the expanded one but a differently shaped one,
covering **100 CBSAs** against **275**.

---

## 7. What was not done, deliberately

- **Nothing was corrected or imputed.** A facility with no OSHA bound is
  *dropped* from the OSHA arm — 548 of them — and never given a
  manufactured date. A facility with no date at all never reaches
  `catchments`. Both counts are in `provenance`.
- **`hazard_report.json` was not touched.** Neither were `hazard*.py` or
  `runner.py` (then in `src/siting_atlas/models/`, now in `../code/`),
  `outputs/figures/` or `docs/proposal/`.
- **The `choice.fit` guards added on 2026-09-14** (non-finite starts, the
  `beta'a > 0` positivity check) were never reached: the hazard path goes
  through `statsmodels.GLM`. Neither fired because neither was on the path.
- **The time baseline was held at `linear`.** `runner.resolve_baseline`
  chooses it on a Q1-by-convention argument the MWPVL dates largely repair,
  so a spline might now be affordable — but changing it here would confound
  the comparison with the retired run. Separate experiment, and a small one.
- **Interval censoring is still not implemented** (open defect A). It now
  applies to fewer rows, but the 139 OSHA-dated facilities are still entered
  as exact event times when they are upper bounds.

---

## 8. What this changes in the project's story

The old statement was *"the hazard model failed on 39 events and dates that
were upper bounds"*, and the obvious rejoinder was *"then get more events
and better dates"*. Both have now been got. The statement is now:

> The discrete-time hazard on a ZCTA-quarter panel fails on 5,441 events
> across 275 metros with stated opening dates, at AUC 0.68 and calibration
> worse than a constant in all seventeen measurements taken. It fails for a
> reason no quantity of data addresses: one siting decision enters the
> likelihood as a median of 39 independent observations.

That is the finding. It should be written up as the finding, and the AUC
should not be quoted without the calibration beside it.
