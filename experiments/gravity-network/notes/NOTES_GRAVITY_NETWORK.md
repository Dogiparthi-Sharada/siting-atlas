# Notes — a gravity term over the Amazon network, and whether it beats the nearest facility

*Built and run 2026-09-15. Artefact: [`../artefacts/gravity_network.json`](../artefacts/gravity_network.json),
run_id `20260915-210603-b780`, seed 20260914, 50 paired re-splits, thirteen
specifications on the identical
483 decisions. Code: [`../code/gravity_network.py`](../code/gravity_network.py)
and its four helpers (`gravity_terms`, `gravity_arms`, `gravity_report`,
`gravity_print`), moved out of `src/siting_atlas/models/` with the experiment.
Every figure below is read out of that artefact; the
console table it prints is reproducible from the artefact alone without
refitting. Where a number is derived rather than stored, it says so.*

**The one-line result: the `gravity_count_a3` term has BOTH its columns
interior in ALL FIFTY re-splits under a strict boundary census — a bar
`sortation_proximity` (4 of 50 at the boundary) and `network_within_50mi`
(42 of 50) miss, though `fulfilment_proximity` clears it too — and when
gravity and nearest-distance are offered together the optimiser keeps
gravity and throws both proximities at the boundary. On prediction it
depends on k: `gravity_count_a3` LOSES on large-metro top-10 lift (6.219x
against `proximity_published`'s 6.290x, and below the `no_network` floor's
6.259x) and WINS on top-1, top-5 and Brier (+0.0116, +0.0126, −1.39e-05
paired over the same 50 re-splits).**

So the answer to "does gravity beat nearest-distance" is **yes on
inference, and on prediction it depends which k you ask about** — there is
no single scalar that settles it. The inference answer and the top-10
answer are not in tension: gravity is a better-identified column that
carries the same information.

---

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes one file per paper. This is not a
paper; it is an experiment, filed here because that is where
[`NOTES_PANEL_EXPERIMENTS.md`](../../../docs/research/NOTES_PANEL_EXPERIMENTS.md) put its own and
because it is an argument about what an estimate means. Part 7 of the
convention, "what I did NOT read", survives as §10, "what this does not
settle", and it is again the most important section.

---

## 1. Why this test, and why it is not a fishing trip

[`COVARIATES_TRIED.md`](../../../docs/research/COVARIATES_TRIED.md) §1.3 records fifteen failed
covariates and one class that worked, and inside that class one line is
easy to read past:

```
  sortation_proximity    0.118 [0.018, 0.235]   interior in all 50 re-splits
  fulfilment_proximity   0.178 [0.028, 0.334]   interior in all 50 re-splits
  network_within_50mi    AT THE BOUNDARY at 25, 50 AND 100 miles
```

(Those three lines are quoted as `COVARIATES_TRIED.md` §1.3 recorded them.
The current run moves the two proximity coefficients — see §3.1 for the
values and §3.2 for the boundary census, which also shows the "interior in
all 50" wording was too strong for `sortation_proximity`.)

A **continuous distance to the single nearest facility** works. A **count
of facilities inside a radius** fails at every radius tried. That is an
already-measured result, not a hypothesis, and it says the radius was never
the problem — the construct was.

Both constructs discard information, and they discard **different**
information. The nearest distance throws away every facility but one. The
radius count throws away every distance. A gravity term keeps both:

```
  G_i(alpha)  =  sum_j  mass_j / (1 + d_ij) ** alpha
```

summed over the facilities `j` of one type that were **already open** when
decision `i` was made.

### 1.1 The kernel is the SAME kernel, on purpose

`panel_network._proximity` is `1 / (1 + miles)` to the nearest facility of a
type. The `alpha = 1`, count-mass gravity term is `sum_j 1/(1 + miles_ij)`
over the whole network of that type. **The baseline takes the MAX of a set
of terms; this takes the SUM of the identical terms.** Nothing else differs,
so the comparison is a clean test of "max versus sum" rather than a test of
two unrelated kernels, and any difference cannot be attributed to the
functional form of the decay.

`1 + d` rather than `d` because a candidate ZCTA can *be* the facility's
ZCTA, where `1/d**alpha` diverges. The shift also makes the empty network
score 0, which is the kernel's limit and the value `panel_network` already
uses for "no such facility exists yet".

### 1.2 Time-respecting, by the existing mechanism and not a new one

`NOTES_COVARIATE_LEAKAGE.md` records what happens when a covariate is
measured after the decision it is meant to predict. Using the 2025 network
to score a 2019 siting would be that failure, larger and more obvious.

The vintage machinery here is **imported, not rewritten**: 14 annual
vintages 2017-2030 from `panel_network`, vintage `Y` holding only
`open_year <= Y`, and a decision scored on the latest vintage strictly
earlier than its own opening year — the identical rule `choice.build`
applies to CBP. A facility that cannot be dated is excluded by
`panel_network.load_network_facilities` *before* it reaches this module, so
it can never enter a sum. The distance matrix is
`panel_network._distance_matrix`, imported rather than re-derived, so the
two tables cannot drift apart on geometry.

```
  811   non-DS US facilities in data/interim/mwpvl_facilities.csv
 -243   no numeric open_year        -> cannot be placed in TIME, excluded
  -17   postcode is not a panel ZCTA -> cannot be placed in SPACE, excluded
        (5 of those are also undated, so 255 are excluded in all)
  ----
  556   usable: 259 fulfilment, 92 sortation, 73 heavy/bulky, 50 inbound
        cross-dock, 49 fresh hub, 18 fresh DC, 15 air gateway, 0 Whole Foods
```

Only the 259 fulfilment centres and 92 sortation centres enter a gravity
column; the other 205 are placed but unused, because the existing
covariates are split by type and the parcel flow makes them different legs.

### 1.3 The three mass definitions, and why the third one is not optional

```
  count               every placeable facility of the type, mass 1
  sqft                square feet where MWPVL states them; the rest get
                      mass 0, which removes them from the sum
  count_sqft_subset   mass 1 on EXACTLY the facilities `sqft` uses
```

The third is the **control**, and without it the count/sqft comparison is
uninterpretable. `sqft` differs from `count` in two ways at once: it weights
by size **and** it drops the facilities with no stated size. A difference
between them could be either. `count_sqft_subset` holds the network fixed
and varies only the weighting, so the two effects can be told apart. §6 is
where that pays off, and the answer turns out to be the opposite of the
obvious one.

Nothing is imputed. A facility with no stated square footage is carried as
a gap, the line `panel_arms` and `PANEL_EXPANSION.md` §6 already take.

```
  square footage stated for 435 of 556 placeable facilities   78.2%
    sortation     92 placeable,  80 with sq ft, median   314,350
    fulfilment   259 placeable, 233 with sq ft, median   700,000
```

### 1.4 The exponents, including the one deliberately not run

`alpha = 1` and `2` are the brief's. `alpha = 3` is added because the sum
converges on its largest term as alpha grows, so alpha = 3 is the end of the
family where gravity **degenerates towards the baseline** — nearest facility
and almost nothing else. Running 1, 2, 3 therefore reads as a path from "the
whole network counts" to "only the nearest one counts", and the shape of
that path is the answer (§5).

**`alpha = 0` is not run, and the reason is that it is degenerate.**
`(1+d)**0 == 1`, so `G_i` becomes the total number of open facilities —
identical for every ZCTA in the country at a given vintage, and therefore
carrying exactly zero within-choice-set variation. It is not a weaker
version of the test; it is not a test.

---

## 2. Thirteen specifications, one panel, one set of decisions

Every arm is fitted on `panel_arms`' **`combined`** frame — all 687
facilities, 483 fitted decisions, 86,682 alternatives — with the identical
CBP vintages carried forward to 2030. Arms differ in **one** thing: which
columns `choice.build` is handed.

```
  no_network             CBP only                              the floor
  proximity_published    + the 3 panel_network columns         THE BASELINE
  proximity_only         + the 2 proximities (drops the count)
  gravity_<mass>_a<n>    + 2 gravity columns                   9 arms
  gravity_best_plus_     + 2 gravity + 2 proximities           the head-to-head
    proximity
```

`NOTES_PANEL_EXPERIMENTS.md` §2 and §3.2 document what happens when arms
differ in their *decisions* as well as their columns: the market mix ranks
the arms and the model does not. That cannot arise here, and the artefact
asserts it rather than assuming it:

```
  decision_sets_identical          true      483 decisions in every arm
  warehousing_identical            true      the load-bearing column is the
                                             same numbers in every arm
  sliced_arm_equals_rebuilt_arm    true      see below
```

**The third check is about a shortcut and is worth one paragraph.** Building
thirteen arms means walking 14 CBP vintages and merging each against 25,022
ZCTAs thirteen times, about fifteen minutes. Instead one build is done with
every column and each arm is a **column slice** of it. That is exact rather
than approximate — `choice.build` divides each column by *its own* mean, so
a column's scaled values do not depend on which other columns were built
beside it, and the rows, groups, chosen index and ids do not depend on the
columns at all. The check proves it by building the baseline arm the slow
way and comparing every number.

### 2.1 The baseline reproduces the published arm

`proximity_published` is the published `combined_plus_network`
specification, so it is a reproduction test on the whole construction:

```
                              published (panel_experiments.json)   here
  land_area_sqmi              0.0000 [0.0000, 0.0000]              0.0000 [0.0000, 0.0000]
  establishments              0.3441 [0.0008, 0.9411]              0.3441 [0.0008, 0.9411]
  warehousing_establishments  1.4189 [1.1342, 2.0474]              1.4189 [1.1342, 2.0474]
  sortation_proximity         0.1039 [0.0000, 0.2102]              0.1039 [0.0000, 0.2102]
  fulfilment_proximity        0.1868 [0.0585, 0.3263]              0.1868 [0.0585, 0.3263]
  network_within_50mi         0.0041 [0.0000, 0.0401]              0.0041 [0.0000, 0.0401]

  top-10 lift, large stratum  6.2903                               6.2903
  decisions / alternatives    483 / 86,682                         483 / 86,682
```

**Every number agrees to every digit printed, and to full float precision.**
An earlier edition of this section reported a small residual — the published
run had placed **554** non-DS facilities against this file's **556**, worth
0.0002 on `sortation_proximity` — and located it in two postcodes that the
ZCTA panel had since learned to match. On the current pair of artefacts that
residual is gone: both sides place 556 and the two arms are bit-identical.

---

## 3. Result 1 — the boundary verdict, which is the outcome that matters

`choice.py` sets `beta_k = exp(theta_k)`, so a column the optimiser wants to
discard is driven towards `theta = -inf` and lands at ~1e-15. Such a value
formally "excludes 1.0" and means nothing. The question that matters for a
new covariate is therefore not the size of the coefficient but whether the
optimiser keeps it at all.

Two rules are reported, and they are not the same rule.

- **The percentile rule** — `p97.5 < 1e-6` is at the boundary; `p2.5 < 1e-6`
  means a boundary solution sits inside the interval. This is exactly
  `panel_print.verdict`, the rule that produced the published "interior"
  statements, so the comparison is like-for-like.
- **The boundary census** — refit the same 50 training halves and *count* how
  many put the coefficient on the boundary. A 2.5th percentile cannot say
  "interior in all 50"; a census can. The artefact carries a
  `reproduces_harness_percentiles` flag proving the census loop fits the
  same training sets as the harness, because otherwise its count would be
  about a different estimator.

### 3.1 Alpha decides everything

```
  arm                           column                        beta      [p2.5,  p97.5]  verdict
  gravity_count_a1              sortation_gravity_count_a1   0.0107  [0.0000, 0.0479]  boundary inside
                                fulfilment_gravity_count_a1  0.0003  [0.0000, 0.0005]  boundary inside
  gravity_sqft_a1               sortation ...                0.0000  [0.0000, 0.0000]  AT THE BOUNDARY
                                fulfilment ...               0.0017  [0.0000, 0.0146]  boundary inside
  gravity_count_sqft_subset_a1  sortation ...                0.0000  [0.0000, 0.0000]  AT THE BOUNDARY
                                fulfilment ...               0.0044  [0.0000, 0.0361]  boundary inside

  gravity_count_a2              sortation ...                0.0836  [0.0193, 0.1539]  INTERIOR
                                fulfilment ...               0.1819  [0.0802, 0.3261]  INTERIOR
  gravity_sqft_a2               sortation ...                0.0334  [0.0000, 0.0889]  boundary inside
                                fulfilment ...               0.1527  [0.0448, 0.2446]  INTERIOR
  gravity_count_sqft_subset_a2  sortation ...                0.0375  [0.0000, 0.1049]  boundary inside
                                fulfilment ...               0.1745  [0.0648, 0.2935]  INTERIOR

  gravity_count_a3              sortation ...                0.0468  [0.0111, 0.0894]  INTERIOR
                                fulfilment ...               0.1097  [0.0513, 0.1811]  INTERIOR
  gravity_sqft_a3               sortation ...                0.0194  [0.0000, 0.0524]  boundary inside
                                fulfilment ...               0.0928  [0.0319, 0.1531]  INTERIOR
  gravity_count_sqft_subset_a3  sortation ...                0.0191  [0.0000, 0.0500]  boundary inside
                                fulfilment ...               0.1030  [0.0403, 0.1632]  INTERIOR
```

**Not one of the six `alpha = 1` columns is interior** — four have the
boundary inside their interval and two sit flat on it. **Seven of the twelve
`alpha >= 2` columns are strictly interior, and the five that are not are
every sortation column except the two count-mass ones.** So alpha is still
the threshold that separates "never interior" from "sometimes interior", and
§5 measures why — but it is not a clean step, and the residual failures fall
on one side of the network rather than at random. On the current run this
section is weaker than it was: the earlier edition read "all but one of the
twelve `alpha >= 2` columns are strictly interior", and that is no longer
true.

### 3.2 The census, where the bar is actually set

```
  arm                          column                        at the boundary   verdict
  proximity_published          sortation_proximity            4 of 50
                               fulfilment_proximity           0 of 50          INTERIOR IN ALL
                               network_within_50mi           42 of 50
                               establishments                 2 of 50
                               warehousing_establishments     0 of 50          INTERIOR IN ALL
                               land_area_sqmi                50 of 50
  gravity_count_a3             sortation_gravity_count_a3     0 of 50          INTERIOR IN ALL
                               fulfilment_gravity_count_a3    0 of 50          INTERIOR IN ALL
                               establishments                 0 of 50          INTERIOR IN ALL
                               warehousing_establishments     0 of 50          INTERIOR IN ALL
```

Two things here, and the first is a **correction to a published claim**.

**1. One of the two published proximities is not interior in all 50
re-splits; the other is.** The statement in `NOTES_PANEL_EXPERIMENTS.md`
§5.2 and `COVARIATES_TRIED.md` §1.3 is derived from the percentile rule, and
by that rule it passes for both columns. Under the census `sortation_proximity`
is driven to the boundary in **4 of 50** re-splits, so "interior in all 50"
overstates it. `fulfilment_proximity` survives the strict test at **0 of
50** — its minimum over the fifty fits is 0.0397, nowhere near the
boundary — so for that column the published wording is exactly right. The
correction is therefore narrower than an earlier edition of this section
claimed (it said one re-split in fifty for *each* column), and it does not
change the published conclusion; it is recorded here because the same census
is what this file's own headline rests on, and it would be dishonest to
apply the strict rule only to the new covariate.

**2. `gravity_count_a3` clears the strict bar that `sortation_proximity`
misses.** Zero of fifty for both columns, and `fulfilment_proximity` is the
only published network column that matches it. `network_within_50mi` at 42
of 50 is the same radius count failing again, on the same panel, in the same
run.

### 3.3 The head-to-head: gravity displaces nearest-distance

`gravity_best_plus_proximity` hands the model the `alpha = 3` count-mass
gravity columns **and** the two published proximities at once, on the same
483 decisions. If gravity were a noisier restatement of nearest-distance the
optimiser would keep the proximities. It does the opposite.

```
  column                        beta      [p2.5,  p97.5]   at the boundary
  sortation_gravity_count_a3   0.0473  [0.0111, 0.0903]     0 of 50   INTERIOR IN ALL
  fulfilment_gravity_count_a3  0.1094  [0.0514, 0.1858]     0 of 50   INTERIOR IN ALL
  sortation_proximity          0.0171  [0.0000, 0.1106]    28 of 50
  fulfilment_proximity         0.0296  [0.0000, 0.1073]    22 of 50
```

`fulfilment_proximity` goes from **0 of 50** on the boundary alone to **22 of
50 beside the gravity term**, and its coefficient falls from 0.1868 to
0.0296. `sortation_proximity` goes from 4 of 50 to 28 of 50 and falls from
0.1039 to 0.0171. The gravity columns are unmoved (0.0468 -> 0.0473,
0.1097 -> 0.1094).

**Read plainly: offered both, the model keeps the sum and discards the
max.** That is the strongest single statement in this file, and it is the
one that answers the brief's question. It is also the one most worth
attacking, because the two families are strongly related by construction
(§1.1) and a near-collinear pair can be split arbitrarily by an optimiser.
What makes it more than a coin-flip is that the split is **not** arbitrary
in direction: it goes the same way for both facility types, the discarded
column is the one that is discarded, and the retained column's point
estimate barely moves.

---

## 4. Result 2 — prediction, stratified, where gravity does NOT win

Top-10 lift over the analytic chance rate `min(10, J)/J`, per stratum, with
**distinct-decision n**. All arms hold the same decisions and the same
splits, so the chance rate is identical across arms and a lift difference is
a model difference and nothing else.

```
  chance rate      0.6643 (J<=25)   0.2269 (26-100)    0.0485 (J>100)
  distinct n          65                160                258
                   (none THIN: the threshold is 20)

  arm                              J<=25         26-100          J>100
  no_network                    1.4566 (+0.00) 3.0547 (-0.06) 6.2585 (-0.03)
  proximity_published  BASELINE 1.4566         3.1154         6.2903
  proximity_only                1.4566 (+0.00) 3.1154 (+0.00) 6.2823 (-0.01)
  gravity_count_a1              1.4578 (+0.00) 3.0616 (-0.05) 6.2545 (-0.04)
  gravity_sqft_a1               1.4566 (+0.00) 3.0547 (-0.06) 6.2585 (-0.03)
  gravity_count_sqft_subset_a1  1.4566 (+0.00) 3.0547 (-0.06) 6.2505 (-0.04)
  gravity_count_a2              1.4601 (+0.00) 3.1416 (+0.03) 6.1829 (-0.11)
  gravity_sqft_a2               1.4578 (+0.00) 3.0520 (-0.06) 6.1590 (-0.13)
  gravity_count_sqft_subset_a2  1.4589 (+0.00) 3.0754 (-0.04) 6.0953 (-0.20)
  gravity_count_a3              1.4530 (-0.00) 3.1416 (+0.03) 6.2187 (-0.07)
  gravity_sqft_a3               1.4554 (-0.00) 3.0465 (-0.07) 6.1511 (-0.14)
  gravity_count_sqft_subset_a3  1.4542 (-0.00) 3.0713 (-0.04) 6.1033 (-0.19)
  gravity_best_plus_proximity   1.4518 (-0.00) 3.1457 (+0.03) 6.1988 (-0.09)
```

**No gravity arm beats the `proximity_published` baseline in the large
stratum, and none beats the `no_network` floor either.** The best of them on
the pre-stated selection rule, `gravity_count_a3`, is 6.2187 against
`proximity_published`'s 6.2903 and the `no_network` floor's 6.2585. The
three `alpha = 1` arms sit at the floor rather than at the baseline because
they *are* the no-network arm wearing extra zeros — their columns are at or
next to the boundary.

**The standardised column no longer disagrees.** Standardised to the
reference mix, `gravity_count_a3` reads 2.7671 against
`proximity_published`'s 2.7682 — a loss of 0.0011, in the same direction as
its large-stratum loss. An earlier edition of this section reported the
standardised column as a *win* for gravity and spent a paragraph explaining
why the stratum columns should govern anyway; on the current run there is no
disagreement left to adjudicate, and the conclusion the paragraph reached is
now reached by both columns at once. The rule itself is unchanged and still
right: report stratum lifts with n, and refuse to rank on the standardised
column, because direct standardisation equalises the *share* of decisions
per bucket and cannot equalise the distribution of `J` *inside* a bucket
(`NOTES_PANEL_EXPERIMENTS.md` §3.2). It rules against gravity on top-10
either way.

### 4.1 The paired differences, which say something more specific

Paired because the arms hold identical decisions and draw identical splits.
**Not a sign test** — the 50 re-splits resample the same 483 decisions and
are not independent, the identical caveat `NOTES_GBM_BENCHMARK.md` §8 item 4
attaches to its own W-L records. Every row is that arm against
`proximity_published`.

```
  arm                            d top1    d top5   d top10  sd(top10)  W-L   d Brier
  no_network                    +0.0006   -0.0107   -0.0054     0.0099   8-30  +6.0e-6
  gravity_count_a1              +0.0006   -0.0110   -0.0049     0.0096   9-30  +6.8e-6
  gravity_count_a2              +0.0115   +0.0142   -0.0005     0.0119  19-22  -1.8e-5
  gravity_count_a3              +0.0116   +0.0126   -0.0002     0.0123  18-22  -1.4e-5
  gravity_sqft_a3               +0.0002   -0.0051   -0.0089     0.0107   6-38  +1.2e-6
  gravity_best_plus_proximity   +0.0117   +0.0130   -0.0005     0.0125  18-22  -1.4e-5
```

**The effect is concentrated at the top of the list, not the bottom.**
`gravity_count_a3` improves top-1 by +0.0116 (42 re-splits improved, 4
worsened) and top-5 by +0.0126 (44 / 2), while top-10 is −0.0002 (18 / 22) —
a dead heat that leans very slightly the baseline's way. Converted to
decisions of the 193 held out (derived: the rate times 193, and 193 is
`0.40 * 483` rounded, not a stored field) that is **+2.2 top-1 and +2.4 top-5
decisions, and −0.04 at top-10** — which is to say no measurable decision at
top-10 in either direction.

**This is why there is no single scalar for "gravity versus proximity".**
The same arm, the same decisions, the same splits: gravity wins at k = 1 and
k = 5 and on Brier, and loses at k = 10 by an amount smaller than a single
decision. Any sentence in this project that settles the question with one
number has picked a k without saying so.

That is the opposite shape from the published proximities, which
`NOTES_PANEL_EXPERIMENTS.md` §5.2 measured as sharpening the shortlist more
than the pick. Gravity sharpens the **pick**. Both remain smaller than the
split-to-split spread of a single method: the paired sd of the top-10
difference is 0.0123 against a paired mean of −0.0002, so a reader handed one
split could not detect any of this.

### 4.2 Brier, as a raw pair and never a skill score

```
  no_network                   0.0050363
  proximity_published          0.0050303      <- the baseline
  gravity_count_a2             0.0050124      best in the file
  gravity_best_plus_proximity  0.0050163
  gravity_count_a3             0.0050165
  gravity_sqft_a3              0.0050315      worse than the baseline
```

Every arm holds the identical 86,682 alternative rows, so unlike
`NOTES_PANEL_EXPERIMENTS.md` §3.3 these Brier scores **are** comparable
across arms — the denominator problem that invalidated that comparison does
not arise when the rows are the same rows. Normalising by a null would still
be forbidden (Gneiting & Raftery 2007 §2.3 p.362, skill scores are generally
improper), so the raw values are what is reported.

On Brier the `alpha >= 2` count-mass arms beat the baseline and the sqft
arms do not. The margin for `gravity_count_a3` is 1.4e-5 on 5.0e-3, about
0.3%.

---

## 5. Why alpha decides it, measured rather than asserted

The alpha threshold in §3.1 is not a curiosity. It is a second, independent
confirmation of the diagnosis `COVARIATES_TRIED.md` §1.1 built out of the
county-grain failures — and it is the first time that diagnosis has been
tested on a covariate whose grain is a **tunable parameter** rather than an
accident of who published the data.

A conditional choice model compares alternatives *inside* a choice set, so
everything between metros is differenced away by construction. A column's
only currency is how much it varies among the candidate ZCTAs of one metro.
`gravity_terms.within_metro_dispersion` measures exactly that: mean
within-CBSA `sd/mean` at the last vintage, over the **41 metros with 101 or
more candidate ZCTAs** (8,271 ZCTAs), which is `panel_strata`'s large
stratum and the stratum the covariate has to work in.

```
  column                                  within-metro cv   outcome
  LOW BAND, cv < 0.6 -- 7 terms, 0 interior
  fulfilment_gravity_count_a1                      0.2975   boundary inside
  fulfilment_gravity_count_sqft_subset_a1          0.3070   boundary inside
  fulfilment_gravity_sqft_a1                       0.3328   boundary inside
  sortation_gravity_sqft_a1                        0.4267   AT THE BOUNDARY
  sortation_gravity_count_sqft_subset_a1           0.4329   AT THE BOUNDARY
  sortation_gravity_count_a1                       0.4427   boundary inside
  network_within_50mi                              0.5918   42 of 50 AT THE BOUNDARY

  0.6 <= cv <= 1.3 -- 0 terms. The band is EMPTY.

  HIGH BAND, cv > 1.3 -- 14 terms, 9 interior. The 5 that are not:
  sortation_proximity                              1.3993   boundary inside (4 of 50)
  sortation_gravity_count_sqft_subset_a2           5.2999   boundary inside
  sortation_gravity_sqft_a2                        5.3063   boundary inside
  sortation_gravity_count_sqft_subset_a3           8.2282   boundary inside
  sortation_gravity_sqft_a3                        8.2920   boundary inside
  ... and a sample of the 9 that are:
  fulfilment_proximity                             1.4418   INTERIOR (0 of 50)
  fulfilment_gravity_count_a2                      4.3630   INTERIOR
  sortation_gravity_count_a2                       5.4917   INTERIOR
  fulfilment_gravity_count_a3                      6.8194   INTERIOR
  fulfilment_gravity_sqft_a3                       7.7371   INTERIOR
  sortation_gravity_count_a3                       8.5046   INTERIOR
```

**The relationship is real but it is ASYMMETRIC, and the asymmetry is the
finding.** Of the 21 terms carrying a `mean_within_metro_cv`, **7 fall below
cv 0.6 and not one of them is interior in its own arm — 7 of 7 fail.** So
**low within-metro dispersion is SUFFICIENT FOR FAILURE.** Above cv 1.3
there are 14 terms and **9 are interior**; the other 5 are not. So **high
dispersion is NECESSARY BUT NOT SUFFICIENT for success** — it buys a chance,
not a result. An earlier edition of this section claimed the outcome tracks
the ordering "without an exception" and that everything above 1.3 is
interior. That is wrong in one direction: there are five counterexamples
inside this very run.

The five are `sortation_proximity`, `sortation_gravity_sqft_a2`,
`sortation_gravity_count_sqft_subset_a2`, `sortation_gravity_sqft_a3` and
`sortation_gravity_count_sqft_subset_a3` — **every one of them on the
sortation side, and four of the five carrying square footage.** Every
fulfilment-side high-cv term is interior, 7 of 7. Whatever is defeating
those five is a property of the sortation network and of the sqft subset
(§6), not of dispersion, which is precisely why dispersion alone cannot
carry a sufficiency claim.

**No term is observed with cv between 0.6 and 1.3** — that band is empty —
so the finding says nothing whatever about intermediate dispersion, and a
threshold "at 0.6" or "at 1.3" is an artefact of where this family of
columns happens to land rather than a measured cut point.

**What this is, stated exactly.** A **descriptive regularity within one
artefact**: n = 21 terms, and they are not independent — each is one of two
columns in one of 13 arms fitted over the same 483 decisions, from one run at
one vintage (2030, over 41 large metros and 8,271 candidate ZCTAs). It is not
an estimated relationship and carries no standard error. Nothing here should
be quoted as a two-sided rule, and nothing here should be quoted as "21 of
21".

**Two rules, and they must be named.** The outcomes above are the
**percentile** rule of §3 plus the boundary census of §3.2, both from this
artefact. `network_inference.json` applies a **point-estimate** rule under a
500-replicate cluster bootstrap and reaches a different verdict on
`sortation_proximity` — `at_boundary: false` there, against "boundary inside
the interval" here. Both are current and both are right under their own
rule. A statement about whether a term is "at the boundary" is meaningless
without the rule attached.

The mechanism is now legible. At `alpha = 1` the decay is so slow that the
sum is dominated by the hundreds of distant facilities, and the column
becomes a smooth continental gradient — large in level, nearly constant
across the ZCTAs of any one metro, and therefore unable to rank anything
inside a choice set. That is precisely the failure mode of a county figure
broadcast down to every ZCTA, arrived at from the opposite direction.
Raising alpha concentrates the sum on nearby facilities and the within-metro
variation returns.

**This reframes what a gravity term is for.** Alpha is not a nuisance
parameter to be tuned for fit; it is the knob that sets the geographic grain
of the covariate, and this model can only use covariates whose grain is
finer than a metropolitan area. The correlation is across 21 columns of one
family on one panel and is not a causal demonstration — a column can have
high within-metro dispersion and still fail, and in this run five of them
do. The mechanism above is therefore an account of why coarse grain
**fails**, which is the direction the evidence supports; it is not an
account of why fine grain succeeds, because five fine-grained columns did
not.

---

## 6. Result 3 — square footage buys nothing, and the control says why

The obvious expectation is that a million-square-foot fulfilment centre
should pull harder than a 200,000-square-foot one, so `sqft` mass should
beat `count` mass. It does not, and the three-way design says exactly where
the loss is.

```
  alpha = 3          sortation beta            fulfilment beta     large lift   d top1
  count            0.0468 [0.0111, 0.0894]   0.1097 [0.0513, 0.1811]  6.2187    +0.0116
  count_sqft_      0.0191 [0.0000, 0.0500]   0.1030 [0.0403, 0.1632]  6.1033    +0.0027
    subset
  sqft             0.0194 [0.0000, 0.0524]   0.0928 [0.0319, 0.1531]  6.1511    +0.0002
```

(All three are `alpha = 3` gravity arms; the lift column is large-stratum
top-10 and `d top1` is paired against `proximity_published`.)

**On the coefficients `sqft` and `count_sqft_subset` land on top of each
other and `count` sits apart from both** — 0.0194 and 0.0191 against 0.0468
on the sortation side. The difference between using the whole placeable
network and using only the 435 of 556 facilities whose square footage MWPVL
states is a **halving** of the sortation coefficient, 0.0468 to 0.0191, with
the boundary moving into the interval.

On large-stratum lift the picture is muddier than an earlier edition of this
section reported. The three do not collapse to two: `count` 6.2187,
`sqft` 6.1511, `count_sqft_subset` 6.1033. Restricting the network costs
0.115 of lift (count → subset) and size-weighting the restricted network
*recovers* 0.048 of it (subset → sqft) rather than the ~0.00 previously
quoted. Against a paired top-10 sd of about 0.012 on the rate, none of these
gaps is separable from noise, so the coefficient evidence is what carries
this section and the lift column is reported, not leaned on.

So the cost is the **subset**, not the weighting. Twelve of the 92 placeable
sortation centres carry no stated square footage, and dropping them from the
sum costs more than size-weighting the remaining eighty buys back — 0.115 of
lift out against 0.048 in, and nothing at all on the sortation coefficient.
The same pattern holds at `alpha = 2` (count 6.1829, sqft 6.1590,
count_sqft_subset 6.0953).

Two readings, and the honest one is the second.

1. *Size does not matter to a siting decision.* Possible, and it would be
   interesting.
2. *Size does not matter **here**, because within one facility type the
   square footages are not spread enough to matter once distance has been
   raised to the third power.* Fulfilment centres have a median of 700,000
   sq ft and sortation centres 314,350; the variation the model could use is
   the within-type spread, and a `(1+d)**3` denominator moves over orders of
   magnitude while the sq ft numerator moves over a factor of a few.

This file cannot separate those, and §10 item 3 says so. What it can say
is the practical conclusion: **use the count. The square footage column is
not worth the 121 facilities it costs.** Without `count_sqft_subset` that
conclusion would have been unreachable, and the natural (wrong) reading of
`count` beating `sqft` would have been "size does not matter".

---

## 7. The verdict

The selection rule was fixed before the numbers were seen and is stored in
the artefact: *among the gravity arms whose both columns are interior, the
highest top-10 lift in the large stratum.* It selects **`gravity_count_a3`**
— count mass, `alpha = 3`, the two facility types separate.

```
  DOES GRAVITY BEAT NEAREST-DISTANCE?
  (gravity_count_a3 against proximity_published, 483 decisions, 50 re-splits)

  on coefficient identification      YES against sortation_proximity, TIE
                                     against fulfilment_proximity. 0 of 50
                                     re-splits at the boundary for both
                                     gravity columns; sortation_proximity is
                                     4 of 50, fulfilment_proximity 0 of 50.

  offered BOTH at once               YES, and decisively. The optimiser
                                     keeps gravity (0 of 50 at the boundary)
                                     and drives sortation_proximity to the
                                     boundary in 28 of 50, fulfilment in 22.

  on the top of the shortlist        YES, marginally. +0.0116 top-1 (42
                                     re-splits improved / 4 worsened) and
                                     +0.0126 top-5 (44 / 2), about +2.2 and
                                     +2.4 decisions of 193.

  on top-10 lift in large metros     NO.  gravity_count_a3 6.219x against
                                     proximity_published 6.290x, and below
                                     the no_network floor's 6.259x.
                                     Paired, -0.0002 (18 / 22).

  on Brier                           marginally yes, 0.0050165 against
                                     0.0050303, a 0.3% margin.

  is any of it bigger than noise?    NO. The paired sd of the top-10
                                     difference is 0.0123 against a mean of
                                     -0.0002.
```

**There is no one-line answer, and a document that gives one has chosen a k
without saying so.** Gravity wins at k = 1 and k = 5 and on Brier; it loses
at k = 10. Those are the same fits on the same decisions.

**The defensible sentence.** *A gravity term over the already-open Amazon
network, with count mass and a cubed distance decay, is at least as
well-identified as the distance to the nearest facility and better
identified than `sortation_proximity` — it survives all fifty re-splits,
where `sortation_proximity` is driven to the boundary in four, and when both
families are in the model it is the nearest-distance columns that are
discarded. On prediction it sharpens the pick (top-1, top-5, Brier) and does
not move the shortlist (top-10), so "does it predict better" has no answer
that is not conditional on k. The project's ceiling of roughly 2.77x
standardised lift and 52% top-10 is exactly where it was: 2.7671 and 0.5248
for `gravity_count_a3` against 2.7682 and 0.5250 for the baseline.*

That closes the question the brief asked, and it closes it in the direction
that matters least for a forecast and most for an explanation.

---

## 8. The theoretical cost, stated and not buried

**A gravity term is not extensive.** Merging two ZCTAs does not add their
attractions: the gravity of a merged zone is some distance-weighted average
of its parts, not their sum. So the exact zone-merger invariance
`MODEL_SPEC.md` §1 buys from Train §3.4 Example 2 — *the entire
justification for the `ln(beta'a)` form* — does not hold for any arm in this
file except `no_network`. Every coefficient reported above is therefore
partly a statement about where the Census drew its ZCTA boundaries.

This is **the same cost the existing proximities already incur** and the one
`models/accessibility.py` declared and switched itself off over. It is paid
here deliberately, and it is the first thing to hold against anything in
this file.

Gravity adds one wrinkle the proximities do not have. Its **level grows with
the network**, and in a share model `P_j = beta'a_j / sum_k beta'a_k` a shift
common to a whole choice set does **not** cancel — it flattens the
distribution towards uniform. The proximities are bounded in `[0, 1]` and
have no such drift. The size of it is in the artefact:

```
  mean over candidate ZCTAs      2017      2020      2030     ratio
  fulfilment_gravity_count_a1   0.1204    0.2275    0.4269     3.5x
  fulfilment_gravity_count_a3   0.0028    0.0056    0.0108     3.9x
  sortation_gravity_count_a3    0.0012    0.0019    0.0038     3.1x
```

A 2030 decision sees a column **three to four times the level** a 2017
decision sees, and the ratio is about the same at every alpha because it
tracks the growth of the network rather than the decay. Whether that biases
the coefficient is not measured here; §10 item 2 names the test.

---

## 9. The machine, and a reduction that did not happen

The brief required single-threaded execution on a shared six-core box. The
entry point calls `os.nice(19)`, the run is single-threaded (`n_jobs=1`,
`OMP_NUM_THREADS=1`, no process pool), and it was told to cut the repeat
count rather than parallelise if 50 re-splits proved too slow.

They did, twice: under a load average near 35 from other work on the box a
full pass was accumulating about 2 CPU-seconds per wall-clock minute and
would have taken roughly ten hours. Two complete passes were therefore run
at **10** re-splits as the box permitted, and the final artefact was run at
the **full 50** during a window when the load dropped to 4. Nothing was
parallelised and the repeat count was not reduced in the shipped result.
`main` takes `--repeats N` so the count that was actually run is a
command-line argument written into the artefact's `repeats` field rather
than a default nobody checked.

Wall clock for the shipped run: about 40 minutes for 13 specifications
plus 4 boundary censuses, single-threaded.

---

## 10. What this does NOT settle

Ranked by how much each would change the reading.

**1. A percentile over re-splits is not a standard error, and the
head-to-head in §3.3 rests on a count of them.** The 50 re-splits resample
the same 483 decisions, so they are not independent and their spread
understates sampling variability by an amount nothing here measures; each
re-split fit also uses only 60% of the decisions, so the bracket is not an
interval on the same estimator as a full-sample point estimate. The boundary
census is a count of those same non-independent fits. The test that would
settle §3.3 is `choice_inference`'s metro-clustered bootstrap, run on
`gravity_best_plus_proximity`, which `network_inference.py` already has the
machinery for and which was not run here.

**2. The aggregation-invariance cost is declared but not measured.** §8.
`network_merge.additivity_error` measures it for the published network arm;
the equivalent number for a gravity arm is not in this artefact, and the
level drift makes it plausible that gravity is *worse* rather than equal.
One call to that module would settle it.

**3. Whether square footage genuinely does not matter, or merely does not
matter at `alpha = 3`.** §6. The within-type spread of square footage is
small against a cubed distance denominator, so the test as run is weak
against the hypothesis rather than decisive. A specification with square
footage entering separately from distance, rather than multiplying inside
the sum, would be the clean test and was not run.

**4. Only two facility types of eight are used.** 205 of the 556 placeable
facilities — heavy/bulky, inbound cross-dock, fresh hub, fresh DC, air
gateway — are placed in space and time and then never enter a column,
because the published covariates split sortation from fulfilment and this
file matched that choice for comparability. An inbound cross-dock feeds the
same network.

**5. 255 of 811 non-DS facilities are excluded and the exclusion is not
uniform across types.** Inherited wholesale from `panel_network`, and
`NOTES_PANEL_EXPERIMENTS.md` §9 item 3 has the by-table breakdown. A missing
facility makes every ZCTA look further from the network than it is, which
attenuates — but only if the missingness is unrelated to location, and
nothing tests that. The gravity term is *more* exposed to this than the
nearest distance, because every missing facility is a missing term in every
sum rather than a term that probably was not the minimum anyway.

**6. Alpha was chosen from three values on the same data the result is
read from.** The selection rule was fixed in advance and is stored, and
`alpha = 2` and `alpha = 3` agree on every qualitative conclusion, so the
choice between them is not load-bearing. But three exponents is a grid, a
grid searched on the evaluation data is a fitted parameter, and the honest
version would nest the alpha choice inside each training fold the way
`NOTES_COVARIATE_SEARCH.md` nests its column selection — where it cost 0.15
of lift.

**7. The splits are not clustered by metro.** Inherited deliberately from
`choice_runner` so this file is comparable with `panel_experiments`,
`gbm_benchmark` and `refit_expanded`. It inflates every arm's absolute
accuracy equally, so the *differences* reported here are less affected than
the levels — but "less affected" is not "unaffected" and nothing measures
which.

**8. The dispersion result of §5 is a descriptive regularity across 21
non-independent columns of one covariate family, in one run.** It is
asymmetric and must always be quoted that way: low dispersion is
**sufficient for failure** (7 of 7 terms below cv 0.6 are not interior),
high dispersion is **necessary but not sufficient for success** (9 of 14
terms above cv 1.3 are interior; 5 are not). The sufficiency claim is not
merely unproven, it is **falsified inside this artefact** by those five
sortation columns. The 0.6–1.3 band is empty, so nothing is known about
intermediate dispersion, and the two thresholds are where this column family
happens to land rather than measured cut points. The 21 terms are two columns
each from 13 arms over the same 483 decisions at one vintage, so n = 21 is
not 21 independent observations.

**9. The published "interior in all 50 re-splits" claim is corrected for one
of the two proximity columns.** §3.2. `sortation_proximity` is at the
boundary in 4 of 50; `fulfilment_proximity` is interior in all 50 and the
published wording holds for it. Recorded because the same census is what
this file's own headline rests on.

---

## 11. How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.gravity_network
```

About 40 minutes on one core on an unloaded box: 13 specifications x 50
re-splits at the conditional logit, plus 4 boundary censuses that refit the
same training halves. `--repeats N` runs a shorter pass; the count is
written into the artefact. Requires
`data/external/facility_panel/national_facilities_expanded.csv`,
`data/interim/mwpvl_facilities.csv` and `data/interim/cbp_detail.parquet`.
Wrote `../artefacts/gravity_network.json` and printed the tables in §1,
§3, §4 and §7.

*The command above no longer runs as written: the module moved to `../code/`
when the experiment was retired and is not importable as
`siting_atlas.models.*`. See `../../README.md`, "Running any of this again".*

The console report can be regenerated from the artefact alone, without
refitting anything:

```python
  import json
  from gravity_print import report_text          # ../code/gravity_print.py
  print(report_text(json.load(
      open("experiments/gravity-network/artefacts/gravity_network.json"))))
```

## 12. Related

- [`COVARIATES_TRIED.md`](../../../docs/research/COVARIATES_TRIED.md) §1.1 and §1.3 — the grain
  diagnosis §5 tests on a tunable covariate, and the three-line result that
  prompted this file.
- [`NOTES_PANEL_EXPERIMENTS.md`](../../../docs/research/NOTES_PANEL_EXPERIMENTS.md) §5 — where the
  proximity covariates come from, §3.2 for the standardised-versus-stratum
  disagreement §4 repeats, and §9 item 1 for the caveat §10 item 1 inherits.
- [`NOTES_COVARIATE_LEAKAGE.md`](../../../docs/research/NOTES_COVARIATE_LEAKAGE.md) — why the
  vintage machinery in §1.2 is structural rather than a filter.
- [`NOTES_GBM_BENCHMARK.md`](../../../docs/research/NOTES_GBM_BENCHMARK.md) §8 item 4 — why the
  win-loss records in §4.1 are not a sign test.
- [`NOTES_gneiting_raftery_2007.md`](../../../docs/research/NOTES_gneiting_raftery_2007.md) §6.3 —
  why §4.2 reports raw Brier values and not a skill score.
- [`NOTES_train_ch03_logit.md`](../../../docs/research/NOTES_train_ch03_logit.md) and
  [`../MODEL_SPEC.md`](../../../docs/MODEL_SPEC.md) §1 — the aggregation invariance §8
  knowingly breaks.
- [`../artefacts/network_inference.json`](../artefacts/network_inference.json) —
  the metro-clustered bootstrap §10 item 1 says should be run on the
  head-to-head arm.
