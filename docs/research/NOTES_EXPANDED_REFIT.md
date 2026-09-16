# Notes — refitting the choice model on the 693-row panel

*Built and run 2026-09-14; **every figure re-read from the current artefacts on
2026-09-15**. Artefact: `outputs/metrics/refit_expanded.json`, `run_id
20260915-195645-1f05`, seed 20260914, 50 re-splits. Code:
`src/siting_atlas/models/refit_expanded.py`. Every figure below is read out of
that artefact, or measured by re-running `models/choice.build` on the two files
and printed in §4 and §7. None is recalled, and the ones that are not in an
artefact are labelled as such.*

**The one-line result: five times the sample, and the headline coefficient got
LESS impressive, not more.** `warehousing_establishments` moved from
1.528 [0.985, 2.550] to **1.191 [0.956, 1.490]** — a 66% narrower interval
that still contains 1.0, with the point estimate moved *towards* the numeraire
it was supposed to escape.

---

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes seven parts and says the directory holds
**one file per paper**. This is not a paper; it is a refit. The seven-part
structure is adapted rather than followed — there is no citation, no page
offsets and no author to quote. Part 7, "what I did NOT read", survives as §8,
"what this does not settle", and it is again the most important section.

It is filed here rather than in `docs/data/` because it is an argument about
what an estimate means, not a description of a dataset. The dataset it runs on
is described in [`../data/PANEL_EXPANSION.md`](../data/PANEL_EXPANSION.md).

---

## 1. The question, and the prediction made before the run

The choice model's binding constraint was always claimed to be sample size.
`models/choice_sandwich` could not distinguish the one working covariate from
its own numeraire — 0.73 to 2.83 against a null of 1, p = 0.287 — and a
38-decision held-out set cannot separate a two-decision difference from noise
(`NOTES_GBM_BENCHMARK.md` §4).

`warehouse/mwpvl_merge` raises the facility frame from 104 rows to **693**. So
the question is whether the constraint was really sample size.

The module docstring states three reasons the new number could be worse
**before** the run, so they cannot be rediscovered afterwards as excuses
(`refit_expanded.py` lines 27-39): the added rows are OCR'd; a quarter of them
carry no numeric year; and a bigger, noisier sample can lower accuracy while
improving inference. It also states the reading rule:

> *"the thing to read is not which top-10 is higher. It is whether the
> coefficient intervals finally exclude the numeraire — that is what the extra
> sample was for."*

They do not.

## 2. What was run

Both panels are fitted by the same function, with the same seed, the same
`TEST_FRACTION` imported from `choice_runner`, and the same evaluation, so the
only difference between the arms is the facility file.

```
  arm "original_104"   data/external/facility_panel/national_facilities.csv
  arm "expanded_658"   data/external/facility_panel/
                       national_facilities_expanded.csv
  repeats              50, seeds SEED + r, 60/40 split over DECISIONS
  refit                inside every repeat, both arms
  covariates           households (numeraire), land_area_sqmi,
                       establishments, warehousing_establishments
```

**The arm label `expanded_658` is stale and the data under it is not.** The
merge it names produced 658 rows from two OCR'd tables; the file on disk today
has **693**, from the full thirteen-table extraction. The 687 facilities the
arm reports are 693 minus the six `E_operating_by` failures `load_national`
excludes, so the run is current and only the key is behind. This is the same
defect class as `power.n_events_zcta` in `hazard_report.json` — a name that
outlived the number it described. Quote the `facilities` field, not the key.


> ## Corrected 2026-09-14, evening — the pooled lift is a Simpson's-paradox trap
>
> **This document's headline cost figure, "lift over its own null fell 3.68x to
> 2.61x", is arithmetically right and substantively misleading, and it was
> misleading the moment it was written.** It is not stale; it is a comparison
> that cannot be made pooled.
>
> A top-10 lift depends on how many alternatives the choice set holds. In a set
> of 25, a uniform guess already lands in the top ten about two thirds of the
> time, so lift is structurally capped near 1.5x however good the model is. The
> MWPVL rows are weighted towards small markets — decisions with **<=25
> alternatives went from 7 of 94 to 65 of 483**, 7.4% to 13.5% of the question
> mix. Pooling across strata of different size therefore measures the *mix*,
> not the model.
>
> Stratified, from `outputs/metrics/lift_by_market_size.json` — **a formally
> retired artefact. Do not quote the figures in this table forward.** That file
> carries a `superseded_by: panel_experiments.json` stamp, has no emitter
> anywhere in the tree, no `run_id`, one split and a tie-broken empirical null,
> and its own `finding` field contradicts the fields beside it. It is
> reproduced here only because it is what this section's Simpson's-paradox
> argument was originally built on; the argument survives, the numbers are
> superseded by `panel_experiments.json` below:
>
> ```
>   RETIRED ARTEFACT -- lift_by_market_size.json, not regenerable
>   choice-set size    original (n, top-10 lift)   expanded (n, lift)
>   -----------------------------------------------------------------
>   small  <= 25            7      1.66x              66     1.44x
>   mid    26-100          41      2.67x             162     3.09x
>   large   > 100          46      6.14x             257     6.42x
>   -----------------------------------------------------------------
>   POOLED                 94      2.95x             485     2.76x
> ```
>
> **The 6.14x and 6.42x in that table are retired figures on a retired frame,
> and the 485 is a superseded decision count.** The current stratified
> replacement, held out over 50 re-splits, is in `panel_experiments.json` and
> is quoted in warning 1 below.
>
> The pooled figure falls while **no stratum falls except the one where lift is
> capped by construction**. That is Simpson's paradox, and it is the whole
> content of the "DOWN" arrow this document draws three times.
>
> **Two warnings about the table above, because it is easy to over-read in the
> other direction.**
>
> 1. **Those stratum figures are IN-SAMPLE.** They are computed over all 94 and
>    all 485 decisions, not a hold-out. Read held out, over 50 re-splits and
>    against an analytic `min(k, J) / J` null,
>    `outputs/metrics/panel_experiments.json` (re-read 2026-09-15) puts
>    large-metro top-10 lift, conditional logit, at **6.180x on the
>    `original_only` arm (94 decisions, 46 of them large-stratum) against
>    6.258x on the `combined` arm (483 decisions, 258 large-stratum) — flat.**
>    The expanded panel is **not better** in large metros. The retired
>    in-sample 6.14 -> 6.42 reading suggests a gain that the hold-out does not
>    support, and it must not be quoted as one.
> 2. **The small stratum on the original panel is 7 decisions.** Nothing can be
>    concluded from 1.66x. `models/panel_strata.py` sets `MIN_INFORMATIVE = 20`
>    distinct decisions for exactly this reason.
>
> **The defensible pooled statement** is a size-standardised one — every arm
> asked the same question mix, weights taken from the larger panel. On that
> basis (`panel_experiments.json`, 50 re-splits, held out) top-10 lift goes
> **2.868x on `original_only` (94 decisions) -> 2.740x on `combined` (483
> decisions)**: still slightly down, and a fifth of the fall this document
> reports.
>
> **What does NOT change.** The expanded panel did not buy accuracy. No
> coefficient interval crossed 1.0, `land_area_sqmi` went the wrong way, and
> §5's central verdict — that sample size was not the binding constraint — is
> untouched and is the finding. What changes is that "the lift fell 29%" was
> never evidence for it.
>
> *Every appearance of 3.68x -> 2.61x below is left in place and marked. It is
> the correct value of a statistic that should not have been the headline.*


## 3. The result

From `refit_expanded.json`. Rates rather than counts, because the two arms hold
out different numbers of decisions (38 against 193):

```
                             original 104     expanded 693
  facilities loaded                 100              687
  decisions fitted                   94              483
  held out per repeat                38              193

  top-10 rate                     54.2%            52.0%    <- DOWN
    sd over 50 re-splits           7.15%            2.73%
  uniform-null top-10 rate        14.7%            19.4%    <- also up
  lift over its own null           3.68x            2.68x    <- DOWN,
                                                            but POOLED --
                                                            see the block
                                                            above
  Brier                        0.007550         0.005036
```

**Coefficients, as ratios to households, the numeraire.** The null that matters
is beta = 1, "worth exactly one household", not beta = 0. The bracket is the
2.5th-97.5th percentile of the 50 re-split fits:

```
  parameter                     original 104              expanded 693
  land_area_sqmi        0.0380 [0.000,   0.261]   4.0e-16 [0.000, 9.6e-16]
  establishments        0.0021 [0.000, 1.7e-13]    0.2991 [0.022,   0.712]
  warehousing_estabs    1.5282 [0.985,   2.550]    1.1912 [0.956,   1.490]

  nothing in either arm excludes 1.0
```

Three readings, and two of them are against us.

**1. `warehousing_establishments` got less impressive.** The interval narrowed
from 1.565 wide to 0.534 wide — **66% narrower** — which is the only thing on
this page that behaved as the extra sample was supposed to make it behave. But
it still spans 1.0, and the point estimate walked from 1.53 down to **1.19**,
towards the numeraire rather than away from it. The honest sentence is: with
five times the decisions, the best estimate of what a warehouse is worth
relative to a household moved from "about one and a half households" to "about
one and a fifth", and we still cannot say it is not exactly one.

**2. `establishments` left the exact boundary — and on the current run it has
now cleared it.** 0.002 to 0.299 is a real move: on the 104-row panel the
optimiser drove this parameter to `theta` around -35 and `beta` to 4.7e-16 in
essentially every split; on the expanded panel it finds a finite value.

> **Conclusion changed, 2026-09-15.** This reading used to end *"But the 2.5th
> percentile is 1.2e-14, which is the boundary, so a boundary solution is still
> inside the interval in at least 2.5% of re-splits. 'Escaped' would be an
> overclaim."* On the current `refit_expanded.json` the 2.5th percentile is
> **0.022**, not the boundary, so no re-split in the lower 2.5% tail is a
> boundary solution and the caution no longer applies to this arm. The
> interval is interior. Two things still hold it back from being a finding: it
> is a percentile spread over re-splits and not a standard error (§8 item 1),
> and `panel_experiments.json`'s `combined` arm — the same frame, a different
> emitter — puts the same parameter at 0.299 [0.022, 0.712] while its
> `combined_plus_network` arm puts it at 0.344 with a 2.5th percentile of
> 0.0008, which is close enough to the boundary to reopen the question as soon
> as the network covariates are added.

**3. `land_area_sqmi` went the other way, and that is a finding.** On the
104-row panel it had a non-zero mean (0.038) and an upper end of 0.261, so some
re-splits gave it a real weight. On the expanded panel the *entire* interval
sits below 1e-15: every one of the 50 re-splits drove it to the boundary.
More data did not rescue this covariate; it made the model more certain the
covariate is worth nothing. The GBM gives that same column **18.5%** of its
split gain (`gbm_benchmark.json:gain_importance.land_area_sqmi` = 0.1854, run
`20260915-200312-1d51`; this said 17.9%, the pre-expansion figure), so the
structure is there and `beta_k = exp(theta_k) > 0` inside a log still cannot
express it. *Do not confuse this 17.9% with the other one in §4: that is the
weighted `min(10, J) / J` chance rate on the original panel, a different
quantity that happens to share the digits.*

## 4. Why the top-10 went DOWN, and why it must not be subtracted

54.2% to 52.0% is a 2.2-point fall and **it is not a comparable pair.** Top-k
is a property of the choice sets, and the choice sets changed. Measured by
re-running `choice.build` on both files on 2026-09-15; the first five rows are
now also emitted, for the same two frames, as `arms.*.choice_set` and
`arms.*.ledger` in `panel_experiments.json` (see §8):

```
                              original 104     expanded 693
  decisions                            94              483
  alternative rows                 11,715           86,682
  median choice set                  92.5             112
  mean choice set                   124.6            179.5
  largest choice set                  369              848
  decisions with <= 10 alts             1               13
```

Two mechanisms, pulling in opposite directions, and neither is about the model.

- A top-10 count is a **certain hit** whenever the choice set has ten or fewer
  members. That is 13 of 483 decisions against 1 of 94.
- The distribution of set sizes is skewed, and `min(10, J) / J` — what a
  genuinely uniform guess scores — is dominated by the small sets. Computed
  over all decisions it is **17.9% on the original panel and 19.0% on the
  expanded one** (derived by weighting `panel_experiments.json`'s per-stratum
  `chance_rate` by each arm's `size_mix`; not stored as a single field), which
  is why the measured uniform null rose from 14.7% to 19.4% even though the
  mean choice set grew by 44%.

So the baseline moved by 4.6 points in the same direction the model's score
was being read. Against its own null, the model's pooled lift fell from
**3.68x to 2.68x** (additively, +39.5 points to +32.6 points).

> **Corrected 2026-09-14, evening.** This paragraph used to end *"That is the
> least flattering reading available and it is also the most nearly comparable
> one."* The first half is true. **The second half is wrong**, and the
> paragraph's own last sentence says why without following it through: lift
> over a uniform null is a function of choice-set size, so pooling it across
> panels with different size mixes compares the mixes. Stratified, lift falls
> in no stratum except the capped one; held out, large-metro top-10 lift is
> flat at 6.180x (`original_only`, 94 decisions) -> 6.258x (`combined`, 483
> decisions). See the block at the head of §3. The least flattering
> reading is not the most comparable one — it is the one this document
> happened to compute.

**The Brier improvement is worth even less.** `choice.evaluate` computes Brier
as a mean over *every alternative row*, so a panel with 86,682 rows dilutes the
same per-decision error across seven times as many near-zero terms as one with
11,715. 0.007550 to 0.005036 is a 33% fall that is substantially arithmetic.
`NOTES_GBM_BENCHMARK.md` §2 already warns that Brier here is not invariant to
the score-to-probability map; this is the companion warning that it is not
invariant to the choice-set size either.

**The one accuracy number that did improve honestly is the spread.** The sd of
the top-10 rate over re-splits fell from 7.15 points to 2.73 points. Most of
that is simply 193 held-out decisions instead of 38, which is what a bigger
test set buys and is not a modelling result.

## 5. What the extra sample actually bought

Stated as a ledger, because "more data helped" and "more data did not help"
are both wrong.

```
  BOUGHT   a 66% narrower interval on the one covariate that carries
           the model, and a 2.62x tighter split-to-split spread
  BOUGHT   establishments off the exact boundary -- and, on the current
           run, clear of it: [0.022, 0.712] (see sec.3 reading 2)
  DID NOT  move any coefficient across 1.0
  DID NOT  rescue land_area_sqmi -- it went the other way
  COST     NOTHING measurable on ranking. This line used to read "the
           top-10 lift over the model's own null, 3.68x -> 2.61x". That
           fall is composition, not skill -- see the block at the head
           of sec.3. Held out and size-standardised the figure is
           2.868x (original_only, 94 dec) -> 2.740x (combined, 483 dec),
           and in large metros it is flat, 6.180x -> 6.258x on the same
           two arms. The expanded panel bought no accuracy; it did not
           cost any either.
  COST     204 of 687 facilities, which never reach the fit at all (sec.7)
```

The specification's own test was "does an interval finally exclude the
numeraire". After five times the sample, **no**. That is evidence that the
binding constraint was not only sample size, which is the opposite of what
this project has been telling itself since the hazard model's power
calculation.

## 6. The refit is accidentally 80% of the leakage test, and that matters

This was not designed and it is the most interesting thing in the run.

[`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) §5 names the
decisive test: lag the CBP vintage off each facility's **true** opening date
rather than off its OSHA upper bound. On the expanded file, `open_year` for an
MWPVL row **is** MWPVL's stated opening year, and `choice.build` lags off
`open_year`. So for most of the expanded arm, the decisive test has already
been run without anybody deciding to run it.

Measured by inspecting the fitted decision ids (not in any artefact):

```
  483 fitted decisions
    389  (80.5%)  MWPVL rows, lagged off a STATED opening year
                    262 month-precision, 104 year, 23 quarter
     94  (19.5%)  the original national rows, still lagged off the
                  OSHA inspection quarter, which is a ~34-month-late
                  upper bound
```

And on that mostly-decontaminated panel, `warehousing_establishments` fell from
1.528 to 1.191. **That is the direction the contamination hypothesis
predicts.** It is not proof of anything, for three reasons, and they should be
read before the sentence above is quoted:

1. The two arms differ in every other respect as well — different metros,
   different choice sets, different years, different sources. The fall is
   confounded with all of it.
2. The clean version of the test refits **the same panel twice**, once lagged
   off the MWPVL date and once off the OSHA bound, on the same decisions. That
   run does not exist and is cheap.
3. 94 of the 483 decisions are still lagged off the OSHA bound, so the arm is
   a mixture, and the covariate is measured at systematically different lags
   for the two halves.

## 7. 204 of 687 facilities never reach the fit, and the reason is documented

`refit_expanded.json` reports 687 facilities and 483 decisions and does not say
where the other 204 went. `panel_experiments.json` now does, as
`arms.combined.ledger`, and instrumenting `choice.build` reproduces it exactly:

```
  687  facilities loaded from the expanded file
                                                  original file, for scale
   -21  ZCTA absent from the covariate panel           0 of 100
  -136  NO numeric open_year, so no CBP vintage        0 of 100
        can be chosen
   -47  dated 2017 or earlier; CBP vintages run       6 of 100
        2017-2022 and the guard demands one
        STRICTLY earlier
  ----
   483  decisions fitted                             94 of 100
```

Two things follow.

**The `facility_check` failure has a measured price.** `PANEL_EXPANSION.md`
§7.1 records that the expanded file fails `ingest/facility_check` because 142
rows have a non-numeric `open_year`, and argues correctly that dropping them or
inventing a year are both worse than carrying the error. This is what carrying
it costs downstream: **136 of 687 facilities, 19.8%, contribute a location and
never enter a fit.** That is the number the next person deciding what to do
about missing years should be given.

**The leakage note's predicted sample loss has arrived.**
`NOTES_COVARIATE_LEAKAGE.md` §5 says the decisive test "costs the facilities
whose true opening precedes the earliest usable CBP vintage ... and must be
reported, not absorbed". It is 47 of 687 here, against 6 of 100 on the OSHA-
bound file — because MWPVL's dates are a median 34 months earlier, more
facilities fall off the front of the CBP window. It is being absorbed silently
today; this paragraph is the report.

One smaller defect in the same place. Three fitted decisions carry opening
years of 2075, 2094 and 2028. The first two are OCR damage that `date_flag`
already marks as `year_outside_2013_2030` (`PANEL_EXPANSION.md` §6), and
`choice.build` does not consult `date_flag`, so they are fitted on the 2022 CBP
vintage like any other late opening. Two of 483 is 0.4% and will not move a
coefficient, but a flag that nothing downstream reads is a flag that is not
doing its job.

## 8. What this does NOT settle

Ranked by how much each would change the reading.

**1. A percentile interval over re-splits is NOT a standard error.** The
artefact's own caveat says so. The 50 re-splits resample the same decisions, so
they are not independent, and the spread understates true sampling variability
— the identical caveat `NOTES_GBM_BENCHMARK.md` §8 item 4 makes. Nothing here
is a confidence interval for the population of siting decisions, and the
narrowing from 1.565 to 0.534 is a narrowing of *this* quantity, not of a
standard error.

**2. It does not account for OCR measurement error in the added rows.** 389 of
the 483 fitted decisions come from OCR'd tables. `PANEL_EXPANSION.md` §9 lists
what is known to be wrong with them: at least one duplicate survived the
screen, 54 rows are unscreenable because the OCR left them with no street name
at all, and about 3% of OCR'd rows merge with a neighbour and are invisible as
two buildings. The dates themselves pass `E_operating_by` on **94.71%** of the
**208** rows that could be linked to an OSHA building — 197 survive the bound
and 11 are falsified, out of all 1,420 dated extraction rows
(`outputs/metrics/mwpvl_validation.json`) — good, and not perfect, and the
refit treats every one of them as exact.

**3. Some of the numbers in this file are still not in `refit_expanded.json`,
but they are no longer unemitted.** The choice-set table in §4, the 389/94
composition in §6 and the 21/136/47 ledger in §7 were measured by re-running
`choice.build` and reading its counters — and the first and third are now
emitted for the same two frames as `arms.*.choice_set` and `arms.*.ledger` in
`panel_experiments.json`, which is what this item asked for. The composition in
§6 remains a hand measurement, reproducible only by re-running a script by
hand. The fix is the one the project keeps relearning — have the emitter emit
it. `refit_expanded.py` should write `n_facilities_loaded`,
`dropped_no_zcta`, `dropped_no_year`, `dropped_no_vintage` and the choice-set
size summary into its own artefact rather than leaving them to a sibling's.

**4. The clean leakage test is still not run.** §6 explains why the refit is
80% of it by accident. Being 80% of a test by accident is not the same as
having run it, and a mixture arm cannot be reported as the answer.

**5. The splits are not clustered by metro.** Inherited from `choice_runner`
and from the GBM benchmark, deliberately, so the three are comparable. It
inflates the absolute accuracy of both arms and it inflates the expanded arm
more, because 230 CBSAs with 483 decisions has more within-metro repetition
than 62 CBSAs with 94.

**6. Nothing here tests whether the expanded panel is a fair sample.** MWPVL
declares its own incompleteness five times, and the added rows are the
facilities a consultancy chose to track. Adding 589 rows makes the sample
bigger; it does not make it representative, and no test in this file could
tell the difference.

## 9. How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.refit_expanded
```

Requires `data/external/facility_panel/national_facilities_expanded.csv` — the
runner raises with the `mwpvl_merge` command rather than falling back — and
`data/interim/cbp_detail.parquet`. Writes
`outputs/metrics/refit_expanded.json` and prints the table in §3, with the
standing instruction beneath it: *"Read the intervals, not the top-10."*

The measurements that are not in `refit_expanded.json` are reproduced by
building both arms directly:

```python
  from siting_atlas.warehouse.national import load_national
  from siting_atlas.models.choice import ATTRACTIONS, CBP_ATTRACTIONS, build
  from siting_atlas.models.refit_expanded import EXPANDED
  d = build(load_national(EXPANDED), panel, cbp, CBP_ATTRACTIONS)
```

`build` writes two drop counters to **stderr** — 21 for "no panel ZCTA" and
**183** for "no CBP vintage strictly earlier than the opening year". It does
not split that 183, so the 136-undated / 47-too-early breakdown in §7 was
measured separately by counting `open_year` against the CBP vintage list
(2017-2022); it now also appears, already split, as `arms.combined.ledger` in
`panel_experiments.json`. `d.ids` and `np.bincount(d.group)` give §6 and §4.

## 10. Related

- [`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) — the contamination
  this refit is accidentally 80% of a test for, and the 34-month lag that
  defeats the guard.
- [`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) — the 50-re-split protocol
  this run copies, and the data-ceiling verdict this run does not overturn.
- [`../data/PANEL_EXPANSION.md`](../data/PANEL_EXPANSION.md) — the merge that
  built the file, its duplicate screen and its nine reasons to distrust the
  result. Written against the earlier two-table run; the artefact
  `outputs/metrics/mwpvl_merge.json` carries the current figures.
- [`../MODEL_SPEC.md`](../MODEL_SPEC.md) §0.3 — the three deviations from the
  specification, all of which survive this refit unchanged.
- [`../STATUS.md`](../STATUS.md) §2 — where this result is filed as
  a status.
