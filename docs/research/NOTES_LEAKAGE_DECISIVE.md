# The warehousing covariate is mostly agglomeration, on 29 of 94 decisions

*Measured 2026-09-14. `src/siting_atlas/models/leakage_decisive.py`,
`src/siting_atlas/models/leakage_dates.py`,
`outputs/metrics/leakage_decisive.json`. The test named in
[`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) §5, run.*

The covariate survives. It keeps **79%** of its measured value when the CBP
vintage is forced behind the building's stated opening date rather than its
OSHA bound, and it still beats the no-covariate floor on 50 of 50 paired
re-splits. It does not survive cleanly: the test cost two thirds of the
sample, it cannot separate the leak from the staleness that removing the leak
introduces, and a second, model-free measurement says the chosen ZCTA really
does gain about one establishment its neighbours do not.

---

## 1. What was run

Three arms, one codebase, one seed, 50 paired re-splits, refitting inside
every repeat.

```
  osha_bound     CBP vintage chosen off `open_year`  -- the status quo
  true_date      CBP vintage chosen off the MWPVL-stated opening year
  no_covariate   warehousing removed entirely        -- the floor
```

Only the DATE changes between the first two. `choice.build` picks the vintage
from `open_year`, so the `true_date` arm substitutes that column and nothing
else; the guard, the join, the optimiser and the evaluation are the same code
running over the same 29 decisions.

## 2. The sample, and what it cost

This is the first number to read, because it bounds everything after it.

```
  100  decisions with no industry covariate at all
   94  decisions with a CBP vintage before the OSHA bound   (the ablation's sample)
   29  decisions with a STATED opening date AND a vintage before it
  ---
   65  lost, 69% of the working sample
```

Two filters do the cutting. A facility must appear in MWPVL and be reached by
the address matcher — 58 of the 104 national rows match, 41 of those matches
carry a stated opening year, and 39 of those survive the panel's own
`E_operating_by` exclusion — and its stated opening must then be late enough
that a comparable CBP vintage exists before it. The series starts at 2017, so
a building that truly opened in 2017 or earlier has none, which removes the
last 10.

**All three arms are restricted to the same 29.** If `true_date` were fitted
on fewer decisions than `osha_bound` the comparison would confound leakage
with sample size, which is the one thing this test exists to avoid. The
no-covariate floor is therefore recomputed here and is **not** the 12.90 of
the ablation; that figure belongs to a different, larger sample.

With 40% held out the test set is **12 decisions** and the fit runs on 17
against 3 estimable parameters — 5.7 events per parameter, well under the
conventional floor of 10. This is a small test and is reported as one.

## 3. The result

29 decisions, 12 held out, 50 re-splits.

```
                     top-10 of 12     sd    lift      Brier    beta warehousing
  osha_bound             9.24        1.00   4.36    0.008771   4.24 [2.32, 16.97] *
  true_date              8.22        1.04   3.88    0.008889   3.68 [2.05, 14.06]
  no_covariate           4.48        1.25   2.11    0.009752   --
  uniform null           2.12

  * one split of 50 drove beta to the boundary (4.8e15): the covariate
    separated that split's choice sets outright and the likelihood is flat
    above it. Counted, not dropped, which is why the MEDIAN is quoted.
```

Paired over the same splits:

```
  osha_bound  -  true_date        +1.02 hits (sd 1.02)   34 W  13 T   3 L
  true_date   -  no_covariate     +3.74 hits (sd 1.40)   50 W   0 T   0 L
  osha_bound  -  no_covariate     +4.76 hits (sd 1.64)   50 W   0 T   0 L
```

`true_date` keeps **3.74 of the 4.76** hits the covariate is worth — 79% —
and clears the floor on every single split. Moving to the contaminated
vintage buys 1.02 hits of 12, and is not free of ties: 13 of 50 splits show
no difference at all.

**A percentile interval over re-splits is not a standard error.** It
describes how the estimator moves across partitions of one fixed sample of 29
buildings. It says nothing about drawing a different 29.

## 4. The coefficient does not move; the column does

The scaled betas above look 15% apart. They are not comparable as printed:
`choice.build` divides each column by its own mean, and the warehousing mean
over the alternatives is 1.410 at the OSHA-bound vintages against 1.238 at
the stated-date vintages — 14% higher. Dividing each beta by its own column
mean puts both on the raw column, and the households scale they are ratios to
is identical in the two arms:

```
  per-establishment weight, osha_bound / true_date   =  1.012
```

**The price of an establishment is the same to within 1.2%.** What changes
between the two vintages is the level of the column, not the model's use of
it. That is what agglomeration looks like and is not what a contaminated
regressor looks like.

## 5. The self-count check, which needs no model

A prediction test cannot separate self-counting from agglomeration. This can,
and it fits nothing. For each of the 29 facilities take the two vintages the
two arms use and ask how much warehousing rose in the ZCTA the building
actually went into, against how much it rose in the average alternative of
the same metro over the same two vintages.

```
  chosen ZCTA           +1.17 establishments
  average alternative   +0.13
  ------------------------------------------
  excess                +1.04   (sd 2.56, median 0.00)

  chosen ZCTA gains at least one    11 of 29
  vintage identical in both arms     3 of 29
```

**The excess is one establishment**, which is exactly the size of the object
being predicted, and the coincidence should not be waved away. But the median
excess is zero and the sd is 2.56: this is a mean carried by a minority
(+9, +7, +7, +5 in four ZCTAs) against several that move the other way (−4,
−2). The honest statement is that self-counting is **present and real in
about a third of the sample**, and that the prediction test above says it is
worth about a fifth of the covariate's value.

## 6. What this does not settle

**The leak and the staleness are the same intervention.** `true_date` reads a
vintage that is older as well as cleaner — a median two years older. Nothing
in this design separates "the facility left the count" from "the count is now
two years out of date", so the +1.02 hit gap is an **upper bound** on the
leak and not a measurement of it. §4 argues the gap is mostly level and not
price, which points the same way, but it is an argument and not a separate
experiment.

**The intersection is not a random subsample.** `osha_bound` scores 9.24 of
12 here (77%) against 20.60 of 38 (54%) on the full 94. These 29 buildings
are the ones MWPVL happens to list and the address matcher happens to reach,
and they are measurably easier. Nothing here transfers to the other 65
without that assumption being stated.

**14 of the 29 stated dates come from an MWPVL table for a different
facility class** — inbound cross dock (6), fulfilment centre (4), sortation
centre (2), fresh hub (1), heavy/bulky (1) — matched on the same street
address. That is either a co-located site, an MWPVL table assignment this
project cannot audit, or a match that is right about the building and wrong
about the business. Restricting to the two delivery-station tables halves
the sample and the difference disappears into noise:

```
  delivery-station tables only:  15 decisions, 6 held out
  osha_bound - true_date  =  +0.34 hits (sd 1.17)   24 W  15 T  11 L
```

Six held-out decisions settle nothing, in either direction. It is reported so
the headline set is not the only number on the page.

**Nothing was corrected.** Two of the 29 stated dates are LATER than the OSHA
bound for the same building, which the project's own `E_operating_by` edit
would call impossible. They are used as stated. Dropping the pairs that
disagree in the inconvenient direction is how a leakage test is rigged.

## 7. The verdict

**In between, and much closer to agglomeration than to leakage.**

- It is not the collapse that would have killed the headline. `true_date`
  beats the no-covariate floor 50 times out of 50 and keeps 79% of the
  covariate's value.
- It is not a clean bill of health either. About a fifth of the covariate's
  measured value rides on a vintage that post-dates the building, some
  fraction of that is real self-counting (§5 finds about one establishment,
  concentrated in a third of the sample), and the rest is vintage freshness
  that this design cannot split off.
- The per-establishment coefficient is unchanged to within 1.2%, which is the
  strongest single piece of evidence that the model was reading clustering
  rather than reading itself.

What the prediction results may now say: that the warehousing covariate
carries genuine agglomeration signal, **audited on 29 decisions whose CBP
vintage strictly precedes the building's stated opening**, with a ~20%
haircut of unknown split between self-counting and staleness.

What they still may not say: that this holds on the 65 decisions the audit
could not reach.

## 8. What would change this

1. **More matched dates.** The binding constraint is that only 39 of the 100
   loaded rows carry a stated date at all. A capture list dating the other 61
   would take the
   intersection from 29 toward 90 and make the test set worth reading on its
   own.
2. **A CBP vintage before 2017.** Ten facilities were lost because their true
   opening precedes the usable series. `ingest/cbp_detail` excludes 2016 for
   a measured reason (`USABLE_VINTAGES`); a reconciled 2016 would recover
   them.
3. **A staleness control.** Refitting `osha_bound` on a vintage aged by the
   same median two years, for facilities whose leak is known absent, would
   split the +1.02 into leak and staleness. No such facility exists in this
   panel — every one of them is a warehouse — so the control needs a
   different outcome, not a different sample.
4. **The delivery-station-only result at usable n.** If the 14 cross-class
   dates are wrong, the headline is wrong, and today the clean version of the
   test has six test decisions.

## 9. Related

- [`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) — the problem
  statement, the ablation (7.70 of 38, 50 of 50), and the 34-month median lag
  that defeats the guard.
- [`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) — **53.53%** of GBM split
  gain sits on this column, which is why the audit mattered.
  (`gbm_benchmark.json:gain_importance.warehousing_establishments` = 0.5353 on
  run `20260915-200312-1d51`. This line said 54.5%, which is the figure from
  the pre-expansion run and still appears in `models/leakage_test.py`'s
  docstring.)
- [`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md) §5 — the lag guard and the
  `open_year` provenance.
- [`../data/MWPVL_2025.md`](../data/MWPVL_2025.md) — where the stated dates
  came from, and the publisher's own caveats on them.
