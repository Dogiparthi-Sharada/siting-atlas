# Notes — log-relative covariates, and the arithmetic that stops them working

*Built and run 2026-09-14. Artefact: [`../artefacts/logrel_search.json`](../artefacts/logrel_search.json),
seed 20260914, on the **479-decision** frame — which was
`covariate_search.json`'s core frame when this ran. That artefact was re-run
on 2026-09-15 and its core frame is now **477 decisions**, so the 6.3889
baseline reproduced below is the superseded one; the current
`covariate_search` core baseline is **6.2157**. **The two frames are not
comparable and this module will not be re-run onto the current one — it is
retired.** A lift from this file set beside a `covariate_search` lift compares
frames, not arms; deltas against each artefact's own baseline carry across,
levels do not.
Code: [`../code/logrel_search.py`](../code/logrel_search.py) and its
`logrel_frame` and `logrel_runner` helpers (moved out of
`src/siting_atlas/models/` with the experiment; they no longer import). Every
figure below is printed by that runner or read out of that artefact. None is
recalled.*

**The one-line result: centring a covariate inside its own metro does NOT let
`choice.py` express a repellent attribute. It cannot, because
`logrel = ln(x / metro_median(x))` is still monotone INCREASING in `x` and
`beta = exp(theta)` is still positive. What the transform does instead is
introduce a SECOND boundary that the old specification did not have — half a
log-relative column is negative, `ln(beta'a)` requires `beta'a > 0`, and the
largest admissible coefficient turns out to be 0.0003 to 0.084 against a
numeraire of 1.0, with seven of the ten arms under 0.007. Every arm that
appeared to find something had walked 20x to 77x past that ceiling and was
assigning NEGATIVE choice probabilities to between 765 and 4,816
alternatives.**

```
  THE RESULT IN THREE NUMBERS

  1  CEILING.  ln(beta'a) needs beta'a > 0 for every alternative. A
     log-relative column is below zero on 49.4-49.9% of its rows BY
     CONSTRUCTION, so a positive coefficient SUBTRACTS attraction there.
     For seven of the ten arms the largest feasible coefficient is
     0.000290 to 0.006538 of the households numeraire -- boxed into an
     interval two to three orders of magnitude narrower than the
     numeraire, unable to move a ranking whatever its true effect. For
     the other three it is 0.055 to 0.084, which is not obviously
     crippling, AND THOSE THREE WENT TO MACHINE ZERO ANYWAY. So the
     ceiling is not the whole story; see item 2.

  2  FIVE OF TEN ARMS WENT TO MACHINE ZERO.  beta between 6.7e-19 and
     1.4e-14, delta-log-likelihood +0.000000 exactly. The same exact-no-op
     signature the levels produced in COVARIATES_TRIED.md section 2.

  3  THE OTHER FIVE BROKE THE MODEL.  beta 20x to 77x the ceiling,
     2,187-4,816 alternatives with negative attraction, and a
     log-likelihood "gain" of up to +1.20 bought entirely by pushing
     NON-CHOSEN alternatives below zero, which shrinks the denominator and
     inflates P(chosen) from 0.078685 to 0.079346. Nothing was learned.
     choice.py does not crash on this: it floors the chosen probability at
     1e-300 and keeps going. It DOES crash when the cliff is steep enough
     that no start stays finite at all, which is how the 50-re-split run
     ended on its 42nd split.
```

---

## 0. The prior, stated before the run and not after it

This test was worth running and was not expected to work. The brief that
commissioned it said so, and the record supports it:

- The plain reciprocal was already tried on the same column as an explicit
  sign fix and did nothing. `inv_median_home_value` moved large-metro top-10
  lift by **+0.0041**; `inv_diesel_pm` was an exact **0.0000**
  (`COVARIATES_TRIED.md` section 2, rows 8 and 9). So the sign constraint was
  not the binding problem for those columns.
- `median_home_value` is not collinear with the numeraire either. Neither of
  the project's two documented failure mechanisms (county grain, collinearity
  with the numeraire) explains its no-op result.

  The brief that commissioned this work quoted that correlation as +0.061.
  It does not reconcile with the artefact and the artefact is what is used
  here: `covariate_search.json`'s `column_audit` records the within-metro
  correlation of `median_home_value` with `households` as **+0.0187**, over
  181.8 distinct values per large metro. The conclusion is the same either
  way — both numbers are far from the 0.84-1.00 band that defines the
  collinearity mechanism — but the figure is corrected rather than repeated.

### Which of the five columns are actually clean cases

| column | distinct values per large metro | within-metro corr with `households` | clean? |
|---|---|---|---|
| `median_home_value` | 181.8 | +0.0187 | yes — ZIP grain, not collinear |
| `median_age` | 121.7 | -0.2489 | yes |
| `bachelors_degree` | 186.5 | +0.8808 | no — collinear with the numeraire |
| `owner_occupied` | 189.7 | +0.8800 | no |
| `renter_occupied` | 181.4 | +0.8395 | no |

Only two of the five are cases the sign constraint could plausibly explain.
The other three are already accounted for by collinearity
(`COVARIATES_TRIED.md` section 1.2), and centring does not obviously cure
that either — although it is worth noting that `logrel_bachelors_degree` is
*not* linearly collinear with `households` the way `bachelors_degree` is,
because a log ratio of a near-proportional column is not itself
near-proportional. That potential benefit is moot: section 3 shows none of
these arms was ever allowed a coefficient large enough to test it.

A log relative IS a different object from a reciprocal: it removes the metro
LEVEL rather than inverting the value. That is why it was worth an
experiment. It was not expected to rescue the column, and it did not.

What it did do was expose something more useful than another null covariate.

---

## 1. The reproduction gate, passed exactly

Nothing below means anything unless the frame is the frame the published
numbers were measured on. `logrel_search` therefore refits the two published
arms on the augmented frame, over the same 50 re-splits at the same seeds,
and compares to fifteen decimal places before reporting anything else.

```
  arm               expected             observed             exact
  baseline          6.388945150223279    6.388945150223279    True
  no_warehousing    2.735190253657848    2.735190253657848    True
```

Recorded in the artefact under `gate_check`. The log-relative columns are
appended to the same `ChoiceData`, so every arm sees identical choice sets
and the paired comparison is about the column alone.

### Stratum sizes, in DISTINCT decisions

| stratum | distinct decisions | thin? |
|---|---|---|
| small, <=25 alternatives | 71 | no |
| mid, 26-100 | 162 | no |
| large, >100 | 246 | no |

`panel_strata.MIN_INFORMATIVE` is 20 distinct decisions. No stratum here is
thin, so all three are comparable. The tables print
*decision-evaluations* — distinct decisions times the ~40% test share times
the repeat count — which is a much larger number and is not an independent
sample size.

---

## 2. What the transform is, and why it is free to compute

`logrel_x = ln(x_j / median_m(x))` over the alternatives of metro `m`.

The choice set IS the metro's ZCTA list, so the within-group median and the
metro median are the same number and the transform can be computed from the
built `ChoiceData` without going back to the panel.
`covariate_frame.build_frame` divides every column by its own mean, and that
constant cancels in `x / median(x)`, so the column built from the scaled
frame is identical to the one built from the raw values. That is what makes
the reproduction gate above possible: same frame object, same decisions, new
columns appended.

The log-relative columns are NOT mean-scaled. Their mean is approximately
zero and dividing by it would be arbitrary. Rescaling a column changes the
units of its coefficient and nothing else — the probability is a ratio — so
leaving them alone costs no comparability.

### The shape of what was built

| column | zeros winsorised | min | 1st pct | 99th pct | max | share < 0 |
|---|---|---|---|---|---|---|
| `logrel_median_home_value` | 0 | -3.308 | -1.069 | 1.103 | 1.873 | 0.498 |
| `neglogrel_median_home_value` | 0 | -1.873 | -1.103 | 1.069 | 3.308 | 0.498 |
| `logrel_median_age` | 0 | -0.956 | -0.416 | 0.452 | 0.735 | 0.494 |
| `neglogrel_median_age` | 0 | -0.735 | -0.452 | 0.416 | 0.956 | 0.494 |
| `logrel_bachelors_degree` | 311 | -7.920 | -4.852 | 2.212 | 4.290 | 0.498 |
| `neglogrel_bachelors_degree` | 311 | -4.290 | -2.212 | 4.852 | 7.920 | 0.498 |
| `logrel_owner_occupied` | 0 | -6.360 | -3.981 | 1.810 | 3.784 | 0.499 |
| `neglogrel_owner_occupied` | 0 | -3.784 | -1.810 | 3.981 | 6.360 | 0.499 |
| `logrel_renter_occupied` | 1,009 | -6.815 | -5.276 | 2.933 | 5.916 | 0.498 |
| `neglogrel_renter_occupied` | 1,009 | -5.916 | -2.933 | 5.276 | 6.815 | 0.499 |

Two honest deviations, both recorded in the artefact:

1. **Zeros.** `ln(0)` is undefined and `covariate_frame.static_frame` keeps
   `x >= 0`, so `bachelors_degree` carries 311 exact zeros (0.38% of 82,926
   alternatives) and `renter_occupied` carries 1,009 (1.22%). Those are
   winsorised up to the smallest strictly positive value in the same metro.
   That is an imputation and this project's rule is not to impute; it is
   confined to alternatives that were never chosen (`negative_and_chosen` is
   0 in every arm, and no chosen alternative carried a zero), and it is
   labelled rather than buried.
2. **`neglogrel_x` is exactly `-logrel_x`**, i.e. `ln(median / x)`. It exists
   because it is the only way this specification can look at the other sign.
   See section 4.

---

## 3. The ceiling, which is the actual finding

`choice.py`'s module docstring states the constraint plainly: *"beta'a must be
positive for every alternative or the probability is undefined."* It then
enforces it the only way it can, by writing `beta = exp(theta)` — which works
when every column is a non-negative count, and stops working the moment a
column can be negative.

A log-relative column is negative on half its rows. So for a given fit of the
other coefficients there is a largest admissible value

```
  beta_max  =  min over alternatives with logrel < 0  of
                   (baseline attraction) / (-logrel)
```

`logrel_frame.bound` computes it exactly, at the baseline fit
(`households` 1.0 by normalisation, `land_area_sqmi` 8.45e-16,
`establishments` 0.2403, `warehousing_establishments` 1.0937). One fit, no
re-splitting, because the ceiling is a property of the frame and the
transform rather than of any train/test partition. The binding alternative is
a single ZCTA whose baseline attraction is 0.0018 of the frame mean.

| column | beta_max (share of numeraire) | fitted beta | beta / beta_max | dLL | alts with beta'a <= 0 |
|---|---|---|---|---|---|
| `logrel_median_home_value` | 0.003154 | 1.412e-14 | 0.00 | +0.0000 | 0 (0.00%) |
| `logrel_median_age` | 0.006538 | 2.647e-15 | 0.00 | +0.0000 | 0 (0.00%) |
| `logrel_bachelors_degree` | 0.000302 | 0.01661 | 55.05 | +0.8449 | 4,221 (5.09%) |
| `logrel_owner_occupied` | 0.000290 | 0.02235 | 77.19 | +1.2043 | 4,816 (5.81%) |
| `logrel_renter_occupied` | 0.000403 | 0.007881 | 19.55 | +0.4177 | 2,453 (2.96%) |
| `neglogrel_median_home_value` | 0.002805 | 0.05887 | 20.99 | +0.2827 | 765 (0.92%) |
| `neglogrel_median_age` | 0.004463 | 0.1707 | 38.24 | +1.1728 | 2,187 (2.64%) |
| `neglogrel_bachelors_degree` | 0.054922 | 8.921e-16 | 0.00 | +0.0000 | 0 (0.00%) |
| `neglogrel_owner_occupied` | 0.083911 | 6.695e-19 | 0.00 | +0.0000 | 0 (0.00%) |
| `neglogrel_renter_occupied` | 0.064061 | 7.508e-16 | 0.00 | +0.0000 | 0 (0.00%) |

Read the first column first, and read it in two groups.

**Seven of the ten arms are confined to at most 0.65% of the numeraire**, and
the tightest to 0.029%. A model in which `warehousing_establishments` is worth
1.09 households cannot be moved by a term that is not allowed past 0.003
households. For those arms the re-split lift in section 5 is not measuring
whether the column has signal; it is measuring a coefficient that was never
permitted to be large enough to matter.

**Three arms had room** — `neglogrel_bachelors_degree`,
`neglogrel_owner_occupied` and `neglogrel_renter_occupied`, with ceilings of
0.055 to 0.084, comparable to the fitted `establishments` coefficient of
0.24 and an order of magnitude above the others. Those three went to machine
zero (6.7e-19 to 8.9e-16) and returned a log-likelihood gain of exactly
+0.000000. That matters for the interpretation: where the feasibility ceiling
was NOT the binding thing, the optimiser still found nothing. The ceiling
explains why the other seven arms are uninformative; it does not have to
carry the whole result.

### 3.1 The five "interior" arms are not interior, they are infeasible

The arms with a non-zero coefficient are 19.55x to 77.19x past the ceiling.
At those points the model gives 765 to 4,816 alternatives — 0.92% to 5.81% —
a NEGATIVE attraction, and therefore a negative choice probability.
`choice._neg_log_likelihood` does not notice: it floors the CHOSEN
probability at 1e-300 and the chosen alternative is never one of the negative
ones (`negative_and_chosen` is 0 in all ten arms). The optimiser has found a
free lunch and taken it:

> A non-chosen alternative pushed below zero SUBTRACTS from its metro's
> denominator. The chosen alternative's share therefore rises. Mean
> probability of the chosen ZCTA goes from **0.078685** at the baseline to
> **0.079346** under `logrel_owner_occupied` — a "gain" of +1.20 in total
> log-likelihood across 479 decisions, produced by arithmetic rather than by
> information.

This is not a numerical wrinkle to be tightened away with a better optimiser.
It is the likelihood being maximised outside the region where it is a
likelihood. Any coefficient, standard error or lift computed there is a
number about the optimiser, in exactly the sense `choice_sandwich.REFUSAL`
uses for a boundary coefficient.

### 3.2 The tell: which direction "wins" is predicted by the ceiling, not by the data

For each of the five columns, one of the two directions went to machine zero
and the other produced a non-zero coefficient. Line up which:

| column | `logrel` beta_max | `neglogrel` beta_max | lower ceiling | which got a non-zero beta |
|---|---|---|---|---|
| `median_home_value` | 0.003154 | 0.002805 | `neglogrel` | `neglogrel` |
| `median_age` | 0.006538 | 0.004463 | `neglogrel` | `neglogrel` |
| `bachelors_degree` | 0.000302 | 0.054922 | `logrel` | `logrel` |
| `owner_occupied` | 0.000290 | 0.083911 | `logrel` | `logrel` |
| `renter_occupied` | 0.000403 | 0.064061 | `logrel` | `logrel` |

**Five for five.** The direction that appears to work is always the direction
in which the infeasible region is CLOSEST — the one where it is cheapest for
the optimiser to buy likelihood by driving junk alternatives negative. That
correlation is with a property of the transform's left tail, not with
anything about warehouses. It is the cleanest available evidence that the
non-zero coefficients in this experiment carry no information about siting.

---

## 4. Does the transform let a negative effect be expressed? No.

This was the diagnostic the experiment was commissioned to settle, and the
answer is arithmetic rather than empirical.

`logrel_x = ln(x / median)` is a **monotone increasing** function of `x`.
`beta = exp(theta)` is positive. The composition is increasing in `x`. So the
fitted effect of "more `x`" on attraction is still forced to be weakly
positive. Centring changes where the column sits on the number line; it does
not change the direction the model is allowed to read it in.

What centring changes is something else, and it is worth being precise about
because it is easy to mistake for a sign fix: a centred column can SUBTRACT
attraction from a below-median alternative, which a strictly positive column
cannot. That looks like repellence and is not. It is a single monotone
ordering with its origin moved, and moving the origin is exactly what creates
the feasibility ceiling in section 3.

The only way to get the other sign out of this specification is to enter a
DECREASING transform — `1/x`, or `neglogrel_x = ln(median / x)` — and pick
which one to believe. That is what the reciprocal arms in
`COVARIATES_TRIED.md` already did. It is a sign chosen a priori by the
analyst and then confirmed by model comparison, not a sign estimated from the
data, and it carries no standard error: `choice_sandwich` refuses an interval
on a boundary coefficient for a reason, and a direction picked by comparing
two separate fits has no interval either.

So the honest statement is:

> **This model form cannot represent a repellent attribute.** The
> `exp(theta)` parameterisation is a real limitation of the specification, not
> a reporting artefact. But it is a limitation about *what can be estimated*,
> not the explanation for these five columns' no-op results. Both directions
> were run for all five columns, and the pattern is the same in every one of
> them: **the direction that fits FEASIBLY goes to machine zero, and the
> direction that produces a coefficient is the one that is infeasible.**
>
> | column | goes to machine zero | goes infeasible |
> |---|---|---|
> | `median_home_value` | `logrel` (1.4e-14) | `neglogrel` |
> | `median_age` | `logrel` (2.6e-15) | `neglogrel` |
> | `bachelors_degree` | `neglogrel` (8.9e-16) | `logrel` |
> | `owner_occupied` | `neglogrel` (6.7e-19) | `logrel` |
> | `renter_occupied` | `neglogrel` (7.5e-16) | `logrel` |
>
> Five for five. There is no column here for which a legitimately fitted
> coefficient of either sign is non-zero.

---

## 5. The re-splits

**41** paired re-splits at seeds 20260914..20260954, the same seeds and the
same frame as the gate, every arm refitted inside every split, 192 held-out
decisions per split.

Forty-one and not fifty, and the reason is worth recording rather than
hiding. The run was launched at fifty. It reached repeat 42 and stopped,
because `choice.fit` raised: *"all 5 starts returned a non-finite
log-likelihood on 287 decisions, 5 attractions."* The failing arm is
`+ logrel_renter_occupied` at seed 20260955, reproduced deliberately
afterwards; the other eleven arms fit on that same split without complaint.

That is the positivity cliff of section 3 taken to its conclusion. On that
partition the optimiser could not find ANY start from which the objective
stayed finite: `beta'a` goes negative for enough alternatives that a metro
total reaches zero, `util / totals` divides by zero, and every restart lands
in the same place. It is a failure of the experiment and it is also a
result — **a five-column model whose fifth column is a log relative is not
guaranteed to fit at all**, and which splits it fails on is not knowable in
advance.

(The guard that raised is new. `choice.py` gained it at 18:25 on the same
day, from separate work; before that the same condition returned a silent
NaN. The stages of this experiment that ran before and after that change
return bit-identical coefficients, so nothing here depends on which version
was loaded — but a run of this module against the pre-guard `choice.py`
would have recorded a NaN arm instead of stopping.)

Because the gate arms in section 1 ran to the full fifty, the then-published
6.3889 is reproduced exactly there (that is the superseded
`covariate_search` core baseline; the re-run of 2026-09-15 moved it to
6.2157 on a 477-decision frame, and this module has not been re-run against
it). The baseline in the table below is
refitted on these 41 splits and so reads 6.3449 — a different number for a
different set of splits, not a discrepancy. All comparisons here are paired
WITHIN these 41 splits.

| arm | small <=25 | mid 26-100 | large >100 | delta on large | pooled lift identical to baseline |
|---|---|---|---|---|---|
| `baseline` | 1.426x | 3.104x | 6.3449x | +0.0000 | (reference) |
| `no_warehousing` | 1.330x | 2.436x | 2.7550x | -3.5900 | no |
| `+ logrel_median_home_value` | 1.412x | 3.092x | 6.3449x | +0.0000 | yes |
| `+ logrel_median_age` | 1.421x | 3.102x | 6.3449x | +0.0000 | yes |
| `+ logrel_bachelors_degree` | 1.406x | 3.075x | 6.3549x | +0.0100 | no |
| `+ logrel_owner_occupied` | 1.419x | 3.119x | 6.3499x | +0.0050 | no |
| `+ logrel_renter_occupied` | 1.408x | 3.085x | 6.3599x | +0.0150 | no |
| `+ neglogrel_median_home_value` | 1.396x | 3.136x | 6.3449x | +0.0000 | yes |
| `+ neglogrel_median_age` | 1.396x | 3.071x | 6.3699x | +0.0250 | no |
| `+ neglogrel_bachelors_degree` | 1.426x | 3.104x | 6.3449x | +0.0000 | yes |
| `+ neglogrel_owner_occupied` | 1.426x | 3.104x | 6.3449x | +0.0000 | yes |
| `+ neglogrel_renter_occupied` | 1.426x | 3.104x | 6.3449x | +0.0000 | yes |

All three strata are above `MIN_INFORMATIVE`; none is thin. The best arm in
the table moves large-metro top-10 lift by **+0.025**, against a baseline of
6.34 and a warehousing contribution of 3.59. It is also one of the infeasible
fits.

### 5.1 "Identical pooled lift" and "no-op" are not the same claim

Six arms print a large-metro lift equal to the baseline's. Only four of them
are true no-ops. The paired table separates them:

| arm | mean rate diff (pp) | sd over re-splits | W | T | L | median beta | share of splits at the lower boundary |
|---|---|---|---|---|---|---|---|
| `no_warehousing` | -17.539 | 4.51 | 0 | 0 | 41 | | |
| `+ logrel_median_home_value` | -0.001 | 0.23 | 1 | 39 | 1 | 6.33e-15 | 0.73 |
| `+ logrel_median_age` | +0.000 | 0.00 | 0 | 41 | 0 | 3.76e-15 | 0.93 |
| `+ logrel_bachelors_degree` | +0.048 | 0.31 | 3 | 37 | 1 | 0.01762 | 0.00 |
| `+ logrel_owner_occupied` | +0.025 | 0.34 | 3 | 36 | 2 | 0.02074 | 0.00 |
| `+ logrel_renter_occupied` | +0.072 | 0.26 | 3 | 38 | 0 | 0.00613 | 0.02 |
| `+ neglogrel_median_home_value` | +0.000 | 0.39 | 3 | 35 | 3 | 0.06930 | 0.27 |
| `+ neglogrel_median_age` | +0.122 | 0.33 | 5 | 36 | 0 | 0.20030 | 0.07 |
| `+ neglogrel_bachelors_degree` | +0.000 | 0.00 | 0 | 41 | 0 | 4.80e-16 | 1.00 |
| `+ neglogrel_owner_occupied` | +0.000 | 0.00 | 0 | 41 | 0 | 1.62e-16 | 1.00 |
| `+ neglogrel_renter_occupied` | +0.000 | 0.00 | 0 | 41 | 0 | 3.66e-16 | 0.98 |

- **True exact no-ops** — 41 ties out of 41, standard deviation exactly zero,
  coefficient at machine zero on every split: `logrel_median_age`,
  `neglogrel_bachelors_degree`, `neglogrel_owner_occupied`,
  `neglogrel_renter_occupied`. The model is bit-identical with and without
  them, which is the same signature the raw levels produced in
  `COVARIATES_TRIED.md` section 2.
- **`logrel_median_home_value`** is nearly one: at the boundary on 73% of
  splits, differing on 2 of 41, and netting to -0.001pp. Its pooled lift is
  equal to the baseline's; its per-split behaviour is not identical. The
  distinction matters and the artefact records both.
- **`neglogrel_median_home_value`** prints the same pooled lift by
  CANCELLATION, not by inaction — 3 wins and 3 losses. Reading its 6.3449 as
  "no effect" would be wrong; it has an effect on six splits and they cancel.

A percentile spread or a standard deviation over re-splits is **NOT a
standard error**. It describes how the estimator moves across partitions of
one fixed set of 479 decisions and says nothing about drawing a different set
of decisions. It is printed because the win/tie/loss count is informative
about consistency, not because it supports an interval. For the four arms
with a non-zero median coefficient it would be doubly meaningless: section
3.1 shows those fits are outside the feasible region, so there is no
likelihood there to take a curvature from.

---

## 6. Verdict, and the minimal specification change that would fix it

### Is the positive-coefficient constraint a real limitation, or a red herring?

**Both, and the distinction matters.**

- **As a property of the specification it is real and it is now measured.**
  `V_j = ln(beta'a_j)` with `beta > 0` cannot represent an attribute that
  makes a location less attractive. Worse, any attempt to smuggle one in via
  a signed column does not merely fail — it hands the optimiser an infeasible
  region in which it can manufacture log-likelihood, and `choice.py` will not
  tell you it has gone there.
- **As an explanation for the seven exact no-ops in `COVARIATES_TRIED.md` it
  is a red herring.** `median_home_value` has now had three separate attempts
  at the other sign — the reciprocal `inv_median_home_value` (+0.0041), and
  both directions of a log relative — and it goes to machine zero every time
  the attempt is a feasible one. The other four columns have had two
  directions each, with the same result. The leading explanation for
  `median_home_value` is now the dull one: within a metro, it does not
  predict where Amazon puts a delivery station.

That closes the sign-constraint question for these columns. It does not close
it for the model: a genuinely repellent covariate — a wetland overlay, a
residential-zoning share, a flood zone — still cannot be entered.

### The minimal change, described and NOT implemented

This is the inspirator's decision, so it is written down and left alone.

**Move the signed covariate OUTSIDE the log:**

```
  now:       V_j = ln(beta' a_j)                      beta = exp(theta) > 0
  proposed:  V_j = ln(beta' a_j) + gamma' z_j         gamma unconstrained
```

where `a` stays the extensive count block and `z` is the within-metro-centred
covariate. This is the standard destination-choice form with a size variable
(`ln(size)` plus a linear index) rather than an invention.

What it buys:

- `gamma` is unconstrained, so a negative effect is **estimated** rather than
  chosen. The maximum is interior by construction, so the
  `choice_sandwich` refusal no longer applies and there is a real standard
  error on the sign.
- `beta'a > 0` is restored unconditionally, because `z` is no longer inside
  the log. The infeasible region of section 3 disappears.
- Scale invariance in `beta` survives: multiplying every `beta` by `c` adds a
  constant to every `V_j` in a metro and cancels in the logit, so the
  households normalisation is still needed and still does the same job.

What it costs, stated honestly:

- **Train's aggregation-invariance argument no longer covers the whole model.**
  `choice.py` exists in its present form because `exp(V) = beta'a` is additive
  across a merger of zones, so the fit does not depend on the Census's
  arbitrary ZCTA boundaries (Train section 3.4, Example 2). Under the proposal
  `exp(V_j) = (beta'a_j) * exp(gamma'z_j)`, and merging two zones preserves
  the sum only if they share the same `z`. Invariance holds exactly for the
  extensive block and only approximately for the new term.
  The mitigating fact: the reciprocal arms already in
  `covariate_search.json` put an intensive variable INSIDE the log, which
  breaks the same invariance AND keeps the sign constraint. The proposal
  breaks it no worse and buys a free sign.
- **Two scales in one table.** `beta` reads as "worth this many households";
  `gamma` reads as a log-odds shift per unit of `z`. They cannot be compared
  to each other, and the coefficient table has to say so.
- The model stops collapsing to the exponential-free share form that
  `choice.py`'s docstring advertises as its simplification. That is a
  presentational loss, not a statistical one.

**A smaller change that should happen regardless of the above**, and is not
a modelling decision: `choice.py` should ASSERT `beta'a > 0` at the returned
optimum, rather than only flooring the chosen probability at 1e-300.

`choice.py` gained a related guard at 18:25 on 2026-09-14, from separate
work: `fit` now discards a start whose objective is non-finite and raises if
every start fails. That is a real improvement — it is what stopped the
re-split run in section 5 rather than letting it record nonsense — but it
does not cover this case. An infeasible optimum here has a perfectly FINITE
log-likelihood; the negative probabilities are all on non-chosen
alternatives, which never enter the objective. So `fit` returned
`+1.20` of apparent log-likelihood from a point where 5.8% of alternatives
had negative probability, and said nothing. Two lines at the end of `fit` —
recompute `beta'a`, raise or flag if any element is non-positive — would have
turned this whole experiment into an error message.

> **It shipped.** This paragraph ended *"That is a suggestion about a file this
> work does not own. It is recorded here, not implemented."* It is now
> implemented, in `src/siting_atlas/models/choice.py:299-334`: after the
> optimiser returns, `fit` recomputes `utility = d.a @ beta`, counts
> `(utility <= 0)`, and raises `ValueError` naming the count, the total and
> the minimum if any element is non-positive. The error text points the reader
> at a separate unconstrained linear index and at this note.
>
> **The consequence for this note is that its artefact no longer reproduces
> against current code.** Five of the ten arms in `../artefacts/logrel_search.json`
> are exactly the arms that fitted past the feasibility ceiling, so re-running
> `logrel_search` today raises on all five instead of recording them. Every
> figure below is therefore a record of what the estimator did *before* the
> guard, kept because the guard is the finding. It cannot be regenerated, and
> it should not be: the run it describes is one the code now refuses.

---

## 7. What this does not settle

- It does not test the log-relative transform on a covariate that WORKS. The
  five columns here were selected precisely because they were no-ops, so a
  reader cannot tell from this alone whether the ceiling would also bind on,
  say, `sortation_proximity`. The arithmetic says it would — the ceiling is
  set by the transform's left tail and the frame's smallest baseline
  attraction, neither of which depends on the column being informative.
- It does not test centring by a statistic other than the median. A metro
  MEAN, a trimmed mean or a rank would all have the same sign problem, and a
  rank-based version (`percentile within metro`, in [0,1]) would not — that
  is strictly positive, bounded, and would face the boundary problem of
  `COVARIATES_TRIED.md` rather than the feasibility problem of this file.
  Untested.
- The zero-winsorisation in section 2 affects `bachelors_degree` and
  `renter_occupied`. Both of those columns went to machine zero in the
  direction where the transform is feasible, so the imputation cannot be
  what produced their null; but it has not been varied.
- It does not revisit whether `median_home_value` is measured at the right
  vintage. The ACS 2023 five-year estimates cover 2019-2023, so for an early
  decision the value is measured over a window that includes and follows the
  opening. Every arm inherits that equally (`covariate_frame`'s docstring
  says so), so the comparison survives, but the level does not.

---

## 8. Reproducing this

```
  OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python \
      -m siting_atlas.models.logrel_search --stages diagnose gate resplits
```

*That command no longer runs, twice over. The module moved to `../code/` when
the experiment was retired and is not importable as `siting_atlas.models.*`
(`../../README.md`, "Running any of this again"); and §6 records that
`choice.py` now raises on exactly the five arms this file is about. **This
artefact is not reproducible against current code and is not meant to be.***

`diagnose` is the cheap stage and carries the finding: eleven full-frame
fits, no re-splitting, about seven to fifty minutes depending on what else is
on the box. It was run twice, before and after `choice.py` acquired its
non-finite-start guard, and returned all ten coefficients bit-identically
both times. `gate` and `resplits` are the fifty-re-split stages; `resplits`
stops at 41 for the reason section 5 gives. Both write a per-repeat
checkpoint (`outputs/metrics/logrel_gate.json`,
`outputs/metrics/logrel_repeats.json` — working files, not retained; only the
finished `../artefacts/logrel_search.json` is) and resume from it, because a
log-relative fit takes minutes rather than seconds when the optimiser is
falling off the positivity cliff and the run is measured in hours when the
machine is busy.

The run is deliberately SINGLE-THREADED — `os.nice(19)`, one process, no
pool — because this workstation is in interactive use by other people.
`covariate_harness.run_experiment` uses a five-process pool; `logrel_runner`
calls the identical per-repeat function serially instead, so the numbers are
comparable to the digit and the machine is not.

## 9. Related

- [`COVARIATES_TRIED.md`](../../../docs/research/COVARIATES_TRIED.md) — the fifteen covariates, the
  two failure mechanisms, and the baselines this file reproduces
- [`NOTES_COVARIATE_SEARCH.md`](../../../docs/research/NOTES_COVARIATE_SEARCH.md) — the search this
  reuses the harness from
- [`NOTES_train_ch03_logit.md`](../../../docs/research/NOTES_train_ch03_logit.md) — section 3.4
  Example 2, the aggregation-invariance argument section 6 would weaken
