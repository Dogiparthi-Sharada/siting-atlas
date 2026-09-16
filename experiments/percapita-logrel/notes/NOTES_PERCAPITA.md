# Per-household normalisation: the collinearity was real, the signal was not

*Run 2026-09-15. Artefact: [`../artefacts/percapita_search.json`](../artefacts/percapita_search.json),
seed 20260914, 50 paired re-splits, on the **479-decision / 694-facility**
frame. That was `covariate_search`'s core frame when this ran;
`covariate_search` was re-run later the same day and its core frame is now
**477 decisions / 687 facilities**. **The two frames are not comparable and
this module will not be re-run onto the current one — it is retired.** Any
lift from this file placed beside a `covariate_search` lift is a
frame-to-frame comparison, not an arm-to-arm one: the baseline here is 6.3889
and there it is 6.2157, so directions and deltas carry across and levels do
not. Code: [`../code/percapita_search.py`](../code/percapita_search.py) and
its `percapita_frame`, `percapita_arms` and `percapita_report` helpers (moved
out of `src/siting_atlas/models/` with the experiment; they no longer import).
Every figure below is read out of the artefact. §8 records which arms finished
and when.*

**The one-line result: dividing the collinear count columns by `households`
DOES remove the collinearity — within-metro correlations fall from 0.41-0.98
to 0.00-0.37 — and it recovers NO predictive signal. The de-collinearised
columns are not small effects; they go to the coefficient boundary and the
model is bit-identical with and without them. Removing the confound removed
the HARM the level versions were doing and revealed nothing underneath, which
means those columns were EMPTY rather than MASKED. The question is closed.**

One thing did move, and it is not the thing the hypothesis was about.
`warehousing_establishments` entered as a RATE instead of a count keeps 82% of
the count's value and is the only per-household column ever to sit in the
interior. §6 says what that is worth to the circularity question, and what it
costs.

---

## 0. The baseline was reproduced first, exactly

Nothing below is worth reading if the harness is not the published one. It is
a different runner — serial instead of pooled, arm-major instead of
repeat-major (§9) — so the check is not a formality.

```
  arm                published   reproduced     difference
  baseline            6.388945     6.388945     +0.00e+00    OK
  no_warehousing      2.735190     2.735190     +0.00e+00    OK
```

Not "within tolerance". **Identical to every printed digit**, because the
frame, the seeds, the split, the optimiser and the scorer are the same code
and the eight ratio columns are appended AFTER the mean-scaling that
`build_frame` applies, so they cannot perturb the columns the baseline
selects.

---

## 1. What was tested

Eight count columns, each divided by `households`, each added to the
published four one at a time. Plus `warehousing_establishments` as a rate
*instead of* the count, which is a different question and is §6.

The choice of eight is not free. `COVARIATES_TRIED.md` separates two failure
mechanisms: §1.1 WRONG GRAIN (county values broadcast to every ZCTA — nine
distinct values across two hundred candidates) and §1.2 COLLINEAR WITH THE
NUMERAIRE. **Only the second is fixable by a transform.** Dividing
`traffic_proximity` by households would not give it more than 9.2 distinct
values per metro, so the grain failures are not here and no amount of
normalising will rescue them.

---

## 2. What this costs: the specification stops being a choice model

*This is its own section and not a footnote, because it is the reason the
result below is a relief rather than a disappointment.*

`MODEL_SPEC.md` §1 derives `V = ln(beta'a)` from Train §3.4 Example 2, and it
records the derivation verbatim. The property being bought is invariance to
how the Census drew the zone boundaries: merge zones `j` and `k` into `c` and
the model should say `P_nj + P_nk = P_nc`. For logit that needs

```
  exp(V_nj) + exp(V_nk) = exp(V_nc)
```

and `ln(beta'a)` delivers it for exactly one reason, which Train states
outright: *"The population and employment in the combined zone are
necessarily the sums of those in the two original zones: a_j + a_k = a_c."*
The attractions must be **extensive**.

**A rate is not extensive.** Merge two ZCTAs and employment-per-household
averages; it does not add. So `exp(V_c) != exp(V_j) + exp(V_k)`, the merger
invariance fails, and every arm in this note is a positive-weight ranking
function that resembles a conditional logit rather than a destination-choice
model in the sense §1 claims. If the Census redrew ZCTA boundaries tomorrow,
these arms would give different answers and the baseline would not.

Three things should be said about that honestly.

**It is a price the project has already paid.** `inv_median_home_value` and
`inv_diesel_pm` in `covariate_frame` are intensive, and `covariate_frame`'s
own docstring says so. The network-proximity covariates in `panel_network` —
the only new class ever to work — are distances, which are intensive too. So
this is a known and priced trade-off, not a new disqualification.

**It has a concrete form, not only a theoretical one.** `beta'a` is a SUM.
Mixing a rate into a sum of counts mixes units: a large ZCTA's linear index
is dominated by its counts and the rate term is a rounding error, while a
small ZCTA's index can be dominated by the rate. A rate column therefore acts
mostly on small alternatives whatever its coefficient, which is an artefact
of the functional form and not a fact about warehouses. Anyone reading a
positive rate coefficient as "Amazon likes high employment density" would be
reading the units.

**It is visible in the measurements.** §6's swap arm ranks far better than
dropping the covariate (5.72x against 2.74x) and is WORSE than dropping it on
the Brier score, which `MODEL_SPEC.md` §9 names as the headline. Good ranking
with degraded probabilities is what a units mismatch inside `beta'a` looks
like.

---

## 3. The transform works. Measured, before and after.

Within-metro Pearson correlation with `households`, averaged over the 36
distinct metro blocks with more than 100 alternatives — the same
`large_gt100` stratum the lift table reports, measured on the matrix the
model actually sees.

```
  column                        level   per household    |after|-|before|
  in_labor_force               +0.982          +0.112         -0.869
  bachelors_degree             +0.880          +0.158         -0.722
  establishments               +0.752          -0.053         -0.698
  employment                   +0.546          +0.008         -0.538
  owner_occupied               +0.909          -0.368         -0.541
  renter_occupied              +0.849          +0.368         -0.480
  annual_payroll               +0.410          -0.005         -0.406
  warehousing_establishments   +0.215          +0.036         -0.179
  vehicle_availability_total   +1.000        CONSTANT         degenerate
```

The same statistic on the ZCTA table before the CBP vintage join agrees to
within 0.01 on every row it holds — the eight ACS and CBP-free columns;
`warehousing_establishments` is vintaged and exists only after the join
(`collinearity_zcta_frame` in the artefact). So the join is not creating or
destroying the collinearity.

**The mechanism is confirmed and is reported independently of whether the
prediction improved.** Three of the eight go essentially to zero
(`employment` +0.008, `annual_payroll` -0.005, `establishments` -0.053). The
worst offender, `in_labor_force` at +0.982, falls to +0.112. Whatever else
follows, the transform did the job it was proposed to do.

### 3.1 Two structural facts the table exposed, which were not the question

**`vehicle_availability_total` IS `households`.** Not correlated 1.00 with it
— equal to it, to floating-point equality, on all 21,768 ZCTAs of the frame.
It is the ACS B25044 universe ("total households by vehicles available"),
whose total is by construction the household count. Its per-household ratio
is the constant 1.0, which cannot be entered: a constant column added to
`beta'a` shifts every alternative's linear index by the same amount, which in
THIS model is not a no-op — it flattens every probability towards uniform —
and carries no information either way. It is dropped from the arms and kept
in the correlation table.

`COVARIATES_TRIED.md` row 10 describes it as "correlates ~1.00 with
households" and records it as an exact no-op. Both are true and the second is
now explained: the optimiser was being offered a duplicate of the numeraire.
The row should say so.

**`owner_occupied + renter_occupied = households`, exactly.** The two
per-household correlations in the table above are `-0.36830991164973936` and
`+0.36830991164973925` — the same number to fifteen digits with the sign
flipped, which is what `corr(1 - x, h) = -corr(x, h)` produces and nothing
else does. So `owner_occupied_per_hh = 1 - renter_occupied_per_hh`. The two
arms are not independent tests; they are one column and its complement, and
the model can only distinguish them because `beta = exp(theta) > 0` forbids
the negative weight that would turn one into the other.

Neither fact was what this experiment was looking for. Both are properties of
the panel that fifteen covariate tests ran past.

---

## 4. It recovers no signal

Top-10 hit rate and lift over an analytic `min(k,J)/J` chance rate, 50 paired
re-splits, stratified by choice-set size. **Distinct decisions per stratum:
small 71, mid 162, large 246** — every stratum is above the
`MIN_INFORMATIVE` floor of 20 distinct decisions, so none is thin and all
three are comparable. (The decision-EVALUATION counts are 1391 / 3211 / 4998;
they are 50 re-splits of the distinct decisions and must not be used to
judge thinness.)

```
  arm                                     small    mid     LARGE   delta    W/T/L    Brier
  baseline                                1.42x   3.09x   6.3889      --       --   0.005227
  no_warehousing                          1.33x   2.42x   2.7352  -3.6538   0/0/50  0.005371
  ----------------------------------------------------------------------------------------
  + employment_per_hh                     1.41x   3.09x   6.3848  -0.0041  0/49/ 1  0.005231
  + annual_payroll_per_hh                 1.42x   3.09x   6.3848  -0.0041  0/49/ 1  0.005228
  + owner_occupied_per_hh                 1.42x   3.10x   6.3889  +0.0000  0/50/ 0  0.005227
  + in_labor_force_per_hh                 1.42x   3.09x   6.3889  +0.0000  0/50/ 0  0.005227
  + warehousing_establishments_per_hh     1.42x   3.09x   6.3889  +0.0000  0/50/ 0  0.005227
  + establishments_per_hh                 1.42x   3.09x   6.3889  +0.0000  0/50/ 0  0.005227
  + bachelors_degree_per_hh               1.42x   3.09x   6.3889  +0.0000  0/50/ 0  0.005227
  + renter_occupied_per_hh                1.42x   3.09x   6.3889  +0.0000  0/50/ 0  0.005227
  ----------------------------------------------------------------------------------------
  warehousing..._per_hh INSTEAD of count  1.41x   3.05x   5.7164  -0.6725  4/5/41   0.005407
```

`W/T/L` counts re-splits on which the arm's large-metro top-10 rate beat,
tied or lost to the baseline's. It is a paired count over partitions of one
fixed set of decisions, not a test.

**Six of the eight "+ rate" arms are EXACT no-ops.** Not small: the lift
agrees with the baseline to four decimals, the Brier to six, and the arm ties
the baseline on 50 of 50 re-splits. The optimiser drove the coefficient to
zero and the model was bit-identical with and without the column. The other
two, `employment_per_hh` and `annual_payroll_per_hh`, each manage -0.0041 and
lose exactly one re-split of fifty.

*Table completed 2026-09-16. It previously listed four arms and said "three of
the four", because four arms had not finished when it was written. The run
finished: `percapita_search.json` reads `arms_unfinished: []` and carries all
eleven declared arms at the full 50 re-splits. See §8.*

### 4.1 The comparison that makes this a finding rather than a null

Put the rate beside the level version of the same column, from
`COVARIATES_TRIED.md` §2:

```
  column          as a LEVEL (covariate_search)  as a RATE (this artefact)
  employment        6.0971   -0.1186             6.3848   -0.0041
  owner_occupied    6.0317   -0.1840             6.3889   +0.0000  no-op
  in_labor_force    6.1707   -0.0450             6.3889   +0.0000  no-op
```

*The level column is re-read from `covariate_search.json`'s completed
2026-09-15 re-run (477 decisions, baseline 6.2157); the rate column is from
this artefact's own 479-decision frame (baseline 6.3889). Each delta is
against its own baseline, so the directions compare and the levels do not.*

The two columns that did the MOST DAMAGE to the baseline are among those
tested here, and normalising fixed the damage completely. That is the
collinearity diagnosis being CONFIRMED: a column correlated 0.55-0.91 with
the numeraire,
forced to carry a positive weight, was pulling weight off `households` and
costing about 0.18 of lift. Divide it by `households` and the optimiser can
simply switch it off, which it does.

**So the collinearity was real and it was harmful. It was not, however,
hiding anything.** The harm disappeared and no lift appeared in its place.
The correct reading is:

> The failure of these columns was over-determined. They were collinear AND
> they were empty. Removing the collinearity removes the cost of including
> them and leaves a column with nothing in it.

On all eight columns, that closes the question: there is no version of
"employment, but measured properly" that rescues them, because the problem was
never the measurement. *This paragraph used to end "Four of the eight were not
reached"; all eight were, and the four that arrived late — `annual_payroll`,
`establishments`, `bachelors_degree`, `renter_occupied` — landed on the same
side. See §8.*

---

## 5. Which coefficients are interior

`choice.py` writes `beta_k = exp(theta_k)`, so a column the model has no
positive use for is walked towards `theta = -inf` down a flat likelihood.
`lo` is the share of the 50 re-splits on which that happened. **The bracketed
figures are 2.5-97.5 PERCENTILES OVER RE-SPLITS of one fixed set of
decisions. They are not standard errors and say nothing about drawing a
different sample of facilities.**

```
  arm / column                                     median        percentile spread    lo
  BOUNDARY
  + employment_per_hh / employment_per_hh        1.2e-14   [3.7e-20,     0.106]     0.68
  + owner_occupied_per_hh / owner_occupied..     3.0e-15   [9.9e-22,   0.00863]     0.72
  + annual_payroll_per_hh / annual_payroll..     8.2e-15   [1.2e-26,    0.0434]     0.74
  + in_labor_force_per_hh / in_labor_force..     2.3e-15   [4.3e-29,   0.01055]     0.82
  + renter_occupied_per_hh / renter_occupied..   4.6e-15   [2.1e-43,   7.8e-14]     0.98
  + warehousing..._per_hh / warehousing..._per_hh 5.8e-17   [0,         1.2e-14]     1.00
  + establishments_per_hh / establishments..     5.3e-16   [1.5e-35,   1.0e-14]     1.00
  + bachelors_degree_per_hh / bachelors..        2.4e-15   [8.3e-23,   2.9e-14]     1.00
  INTERIOR
  swap arm / warehousing_establishments_per_hh     0.8997   [0.6356,     1.367]     0.00
```

Every ADDED per-household column is at the boundary: on 68% to 100% of
re-splits, and at a median of `1e-14` to `1e-17` in the rest, which is the
boundary in all but name. None of the eight is interior on a single re-split
in any meaningful sense. *Four rows were added on 2026-09-16 from the finished
run; the 68-100% range is unchanged by them.*

The one interior per-household coefficient in the whole experiment is
`warehousing_establishments_per_hh` in the SWAP arm, where it is the only
industry column available and is interior on **50 of 50** re-splits. That is
not a de-collinearised column coming to life; it is the count's information
arriving in a different container, and §6 measures what the container costs.

For context, the baseline's own coefficients on the same run:
`warehousing_establishments` 1.093 [0.845, 1.443], interior on 50 of 50;
`establishments` 0.261, at the boundary on 6%; `land_area_sqmi` at the
boundary on **100%** of re-splits, which is the published specification
carrying a column that contributes nothing.

---

## 6. Warehousing as a rate, and what it says about circularity

This arm is not a test of the collinearity hypothesis. It is a test of
`NOTES_LEAKAGE_DECISIVE.md`: a RATE is harder to contaminate by one building
than a COUNT is, because one new warehouse moves a count from six to seven
and moves a per-household rate by the same absolute amount divided by ten
thousand households.

```
  no_warehousing (the floor)                         2.7352
  warehousing as a RATE, instead of the count        5.7164
  warehousing as a COUNT (the published baseline)    6.3889
```

The rate keeps **(5.7164 - 2.7352) / (6.3889 - 2.7352) = 81.6%** of the
count's value over the floor. Its coefficient is interior on 50 of 50
re-splits. It loses to the baseline on 41 of 50 re-splits, ties on 5 and wins
on 4, for a mean of -3.28 percentage points of top-10 hit rate.

**What this does and does not license.** It shows the covariate's value does
not depend on the count's arithmetic, which is a genuine, if partial,
robustness result for the load-bearing column: an 82% retention under a
transform that blunts single-building contamination sits beside the 79%
retention under honest pre-opening vintages that `leakage_decisive.json`
measured on n=29. Two different attacks, two similar answers.

It does not license swapping the specification. Three reasons:

1. **It is worse, and on the declared headline metric it is worse than
   nothing.** Brier 0.005407 for the rate against 0.005371 for dropping the
   covariate entirely and 0.005227 for the count. `MODEL_SPEC.md` §9 says the
   raw Brier pair is the headline and top-k is not. On the headline, the rate
   arm is the worst of the three.
2. **It breaks the merger invariance** the published specification is built
   on. §2.
3. **It does not remove the leak, it dilutes it.** A per-household rate
   computed from a contaminated count is still computed from a contaminated
   count. The right test remains the vintage test.

The ranking-versus-Brier split is itself the §2 cost showing up in the
numbers: a rate mixed into a sum of counts can preserve the ORDER of
alternatives while distorting the probability MASS assigned to them.

---

## 7. Verdict

**Was the collinearity masking real signal, or was there never any signal
there?** On all eight columns: **there was never any signal there.**

The evidence is not a null result. It is three findings that only fit
together one way:

1. The transform removes the collinearity — measured, 0.41-0.98 down to
   0.00-0.37, independently of any model.
2. The de-collinearised columns then go to the coefficient boundary on
   68-100% of re-splits and leave the model bit-identical. Six of eight are
   no-ops to the last printed digit.
3. The harm the level versions did (-0.17, -0.19) disappears exactly.

If the columns had held masked signal, (1) and (3) would have been
accompanied by lift. They were not. Collinearity was a real and costly
problem, and fixing it revealed an empty column.

**This closes the ACS-count line of enquiry permanently.** Not "these eight
did not work" but "the mechanism that was supposed to rescue them works, and
there is nothing behind it". `COVARIATES_TRIED.md` §6 already rules out "any
remaining ACS column" on the grounds of collinearity; this note replaces that
reasoning with a stronger one, because collinearity is fixable and emptiness
is not.

It also strengthens the rule that note ends on. The covariates that work are
computed as a DISTANCE FROM each candidate (`sortation_proximity`,
`fulfilment_proximity`) rather than looked up against it. Normalising a
looked-up count does not convert it into a computed one. `industrial_sqmi`
and highway distance remain the tests worth running; another ACS ratio does
not.

---

## 8. What did not finish at first, and why it was absent rather than partial

> **Resolved.** This section recorded four arms as unfinished. The run was
> resumed from its checkpoint and **all eleven declared arms completed at the
> full 50 re-splits**: `percapita_search.json` reads `arms_complete` = all
> eleven and `arms_unfinished: []`. The four that were missing —
> `+ annual_payroll_per_hh`, `+ establishments_per_hh`,
> `+ bachelors_degree_per_hh`, `+ renter_occupied_per_hh` — are in the §4 and
> §5 tables above. Three are exact no-ops; `annual_payroll_per_hh` costs
> -0.0041 and loses one re-split of fifty. **Nothing in the verdict moved**,
> which is the least interesting way for a gap to close and the one this
> section was written hoping for.
>
> The account below is kept because the *design* decision it records — report
> an arm only at the full repeat count, or not at all — is the reason the
> partial run was safe to read.

At the time of writing, seven of the eleven declared arms had completed at the
full 50 re-splits. Four had not:

```
  + annual_payroll_per_hh      + establishments_per_hh
  + bachelors_degree_per_hh    + renter_occupied_per_hh
```

They were **absent from the artefact and from every table above**, not
summarised over fewer re-splits. An arm scored on thirty partitions is not
comparable with a baseline scored on fifty, and quietly mixing the two is the
class of error this project keeps finding in its own past work.

The cause is the machine, not the method, and it is recorded because it
shaped the design. The workstation is six cores shared with other agents. The
run is deliberately single-process at `nice 19` (§9). For the first hour a
sibling job held five cores; measured directly, this process received **1.1%
of one core against 96.5% for a sibling at identical nice**, and later the
sibling relaunched at `nice 0`, where the 68x scheduler weight difference
made progress effectively nil. Seven arms landed in the windows between.

**Resuming cost one command and no re-computation.** The checkpoint at
`outputs/metrics/percapita_repeats.json` held every completed fit keyed by arm
and seed (it was a working file and is not retained; only the finished
`../artefacts/percapita_search.json` is):

```
  OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python \
      -m siting_atlas.models.percapita_search
```

*That command no longer runs. The module moved to `../code/` when the
experiment was retired and is not importable as `siting_atlas.models.*`; see
`../../README.md`, "Running any of this again".*

`--report-only` re-reads the checkpoint and rewrites the artefact without
fitting anything, which is how §0 and §4 were read while the run was still
going.

**Did the gap change the verdict?** It did not, and the argument written while
it was open said why it probably would not. Both halves are kept: the
reasoning, and the measurement that has since settled it. At the time it
weakened the verdict by exactly the width of four untested columns and no
more, and the arms that had finished were the strongest available subset, for
two independent reasons.

*They are the columns the collinearity diagnosis had the most to explain.*
`in_labor_force` is the most collinear column in the panel at **+0.982** with
the numeraire — if the diagnosis were right anywhere, it is there. Its rate
correlates +0.112 and is an exact no-op on 50 of 50 re-splits.

*They are the columns that did the most damage.* `owner_occupied` (-0.1927)
and `employment` (-0.1722) are the two worst of the fifteen in
`COVARIATES_TRIED.md`. Both are repaired, and neither produces lift.

The missing four included `establishments`, whose level version already sits
at or near the boundary in the published specification, and
`renter_occupied`, which §3.1 shows is `1 - owner_occupied_per_hh` and
therefore not an independent test of anything. That left `annual_payroll`
(+0.410, the second-least collinear) and `bachelors_degree` (+0.880) as the
only genuinely untested cases.

**Both have since been tested.** `bachelors_degree_per_hh` is an exact no-op
(0.0000, at the boundary on 100% of re-splits) and `annual_payroll_per_hh`
costs -0.0041 with one loss in fifty — the same two outcomes the other six
produced. The verdict in §7 is therefore **closed on all eight**, not
strongly indicated, and this section is no longer the reason to hedge it.

---

## 9. Method, and two departures from the covariate-search harness

Everything scientific is inherited unchanged — the frame, the 60/40 split
over decisions, `choice.fit`, the stratification, the scoring, the summary.
That is what makes §0 possible. Two things differ, both operational:

**Serial, one process, `nice 19`.** `covariate_harness` farms its repeats to
a five-process pool. On a shared six-core box at load average 25-34 that is
antisocial, and parallelism buys wall clock and nothing else because the
repeats are independent by construction.

**Arm-major, with a checkpoint after every fit.** The pool version runs
repeat-major — every arm on repeat 1, then every arm on repeat 2 — which is
the right order when a run is certain to finish and the worst possible order
when it is not, because an interruption leaves every arm equally unfinished
and none of them readable. This one runs the arms in a priority order
declared in `percapita_search.PRIORITY` BEFORE the run, each across all fifty
re-splits. An interruption then leaves a prefix of arms complete and the rest
absent, which is §8.

Declaring the order in advance is what stops it becoming a result. An order
chosen after seeing the lifts would be a selection rule, and
`COVARIATES_TRIED.md` §3 already records what selection does to this sample.

A re-split is a deterministic function of its seed
(`covariate_arms.split_decisions`), so arm A on seed `s` and arm B on seed
`s` see the same partition whichever order they were computed in. The pairing
survives the reordering; §0 is the proof that it did.

**No search.** Every arm is a fixed, pre-declared column list. The honest
nested forward selection in `covariate_search` came out **0.1268 of a lift
point WORSE on the large-metro top-10 stratum** — 6.0889x against the
baseline's 6.2157x, which is the same comparison as its −0.6201 percentage
points
on the large-metro top-10 *rate*, expressed as a lift rather than a rate. (The
two are one result, not two; and pooled across all choice-set sizes the same
comparison is marginally better, so the stratum has to be named — see
[`NOTES_COVARIATE_SEARCH.md`](../../../docs/research/NOTES_COVARIATE_SEARCH.md) §5.) It is a measured
result about overfitting the selection at this sample size, and offering it
eight more candidates would measure that again and nothing else.

---

## 10. Related

- [`COVARIATES_TRIED.md`](../../../docs/research/COVARIATES_TRIED.md) — the fifteen, the two failure
  mechanisms, and the baseline this note reproduces
- [`NOTES_COVARIATE_SEARCH.md`](../../../docs/research/NOTES_COVARIATE_SEARCH.md) — the search
  harness this one borrows
- [`NOTES_LEAKAGE_DECISIVE.md`](../../../docs/research/NOTES_LEAKAGE_DECISIVE.md) — the circularity
  question §6 speaks to
- [`NOTES_train_ch03_logit.md`](../../../docs/research/NOTES_train_ch03_logit.md) and
  `docs/MODEL_SPEC.md` §1 — the merger invariance §2 gives up
