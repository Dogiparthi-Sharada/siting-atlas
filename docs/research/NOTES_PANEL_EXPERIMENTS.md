# Notes — five panel compositions, two algorithms, and one covariate that had never been tried

*Built and run 2026-09-14. Artefact: `outputs/metrics/panel_experiments.json`,
seed 20260914, 50 paired re-splits, every method refitted inside every repeat.
Code: `src/siting_atlas/models/panel_experiments.py` and its five helpers
(`panel_arms`, `panel_harness`, `panel_network`, `panel_strata`,
`panel_print`). Every figure below is read out of that artefact. None is
recalled, and the two that are derived from it rather than stored in it —
the boundary verdicts in §3.1 and the hits-of-193 conversions in §5.2 — say
so where they appear.*

**The one-line result: the arm that wins depends on which of the three
measures you read, the three disagree, and no specification in this file puts
`warehousing_establishments` away from the numeraire under anything that is
inference.** Adding the network covariates moves the point estimate — about
1.19 households per warehouse on `combined`, about 1.42 on
`combined_plus_network` — and widens the re-split spread rather than
tightening it. The one bracket that looked like an exclusion was a percentile
spread, not an interval, and it is **withdrawn**: see §12, and §3.1 reading 2
for what it was and why it fell.

> **The claim this file was originally written around is WITHDRAWN.**
> §12 tested it properly. The metro-clustered bootstrap on the same arm gives
> **1.3481 [0.9970, 1.9582]**, which CONTAINS 1.0, and both sandwiches agree
> (p = 0.065 clustered, p = 0.170 not). §3.1, §5.2, §7 and
> §8 are left standing as descriptions of the quantity they were computed
> from; §12.7 lists exactly which of their sentences are no longer claims
> about the world. Nothing in this file establishes that a
> `warehousing_establishments` interval excludes 1.0.
>
> *(This block quoted 1.312 [0.977, 1.919] and p = 0.088 / 0.203 until
> 2026-09-16. Those are the 2026-09-14 figures on the superseded 700-row
> panel; `network_inference.json` was re-run as `20260915-210640-dbcd` on the
> 483-decision panel and §12 has carried the new pair since. The verdict is
> identical either way — every interval that is inference contains 1.0.)*

---

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes seven parts and says the directory holds
**one file per paper**. This is not a paper; it is an experiment, filed here
because that is where the brief put it and because it is an argument about
what an estimate means rather than a description of a dataset. Part 7, "what
I did NOT read", survives as §9, "what this does not settle", and it is again
the most important section.

It extends [`NOTES_EXPANDED_REFIT.md`](NOTES_EXPANDED_REFIT.md), which
compared two panels. This compares five, adds a second algorithm to all of
them, and adds covariates the model has never had.

---

## 1. The five arms, and what each is

```
  arm                     facilities   fitted decisions   filter
  original_only                  100                 94   none (the reference)
  mwpvl_only                     587                389   source_dataset == mwpvl_2025q1
  mwpvl_clean                    415                360   MWPVL rows with a numeric
                                                          open_year AND mwpvl_vouched
  combined                       687                483   none
  combined_plus_network          687                483   none; adds 3 covariates
```

Every arm is loaded through `warehouse.national.load_national`, so the
declared edit `E_operating_by` is enforced identically on all of them and
excludes the same 6 rows of 693 (and 4 of 104). The arms then differ only in
which surviving rows they keep.

### 1.1 The protocol is imported, not re-declared, and it reproduces

`SEED` and `TEST_FRACTION` come from `choice_runner`; the split is 60/40 over
DECISIONS; every method is refitted inside every one of the 50 repeats. The
check that this worked is that `original_only` reproduces the two published
artefacts **exactly**, to every digit either one prints:

```
                                    this run     published
  logit top-10 rate                   0.542        0.542   refit_expanded.json
  logit Brier                      0.007550     0.007550   refit_expanded.json
  logit warehousing beta       1.528 [0.985,   1.528 [0.985,
                                      2.550]       2.550]  refit_expanded.json
  gbm stump/200 levels Brier       0.007681     0.007681   gbm_benchmark.json
  gbm deep/300  levels Brier       0.010392     0.010392   gbm_benchmark.json
  combined  logit top-10              0.520        0.520   refit_expanded.json
  combined  logit Brier            0.005036     0.005036   refit_expanded.json
  combined  warehousing beta   1.191 [0.956,   1.191 [0.956,
                                      1.490]       1.490]  refit_expanded.json
```

Nothing below is being compared across different rows or different splits.

*Two figures in that block were corrected on 2026-09-16. The GBM Brier rows
read 0.007685 and 0.010365 in **both** columns; `gbm_benchmark.json`
(`20260915-200312-1d51`) and `panel_experiments.json` both give 0.0076814 and
0.0103919, agreeing to thirteen digits, and §6 of this file already quoted the
correct pair. The reproduction still reproduces — the typo was in the
transcription, not in the run.*

### 1.2 The ledger `NOTES_EXPANDED_REFIT.md` §8 asked for is now emitted

That file's §8 item 3 recorded that the 22/138/49 drop breakdown had been
measured by hand and existed in no artefact. On the current panel the same
breakdown is **21/136/47** — the hand measurement was taken on the superseded
700-row file. It is now in
`panel_experiments.json` under `arms.<arm>.ledger`, for all five arms, and it
reconciles to the decision count exactly:

```
  arm                     loaded   no ZCTA   no year   no vintage   fitted
  original_only              100         0         0            6       94
  mwpvl_only                 587        21       136           41      389
  mwpvl_clean                415        15         0           40      360
  combined                   687        21       136           47      483
  combined_plus_network      687        21       136           47      483
```

The `combined` row is 21 / 136 / 47, which is the same quantity §7 of that
file measured by instrumenting `choice.build`. That hand measurement came out
22 / 138 / 49 on the 700-row panel; on the 693-row panel the artefact gives
21 / 136 / 47. The hand measurement was right about the shape of the loss and
it is no longer a hand measurement.

## 2. The correction that reorganised this whole experiment

Mid-run, `outputs/metrics/lift_by_market_size.json` established that the
headline this experiment was built on top of — *"lift over the uniform null
fell 3.68x to 2.61x when the panel grew"* — is a **Simpson's paradox**. Lift
rose in the mid and large strata and fell only in the pooled figure, because
MWPVL rows are weighted towards small markets where a random guess already
scores 67% at top-10 and lift is structurally capped near 1.5x.

That is not a footnote here; it is the main methodological risk, because
**the five arms have different market mixes by construction**:

```
  share of decisions by choice-set size J
  arm                      J<=25    26-100    J>100    median J
  original_only             7.4%     43.6%    48.9%          92
  mwpvl_only               14.9%     30.6%    54.5%         112
  mwpvl_clean              15.3%     30.8%    53.9%         112
  combined                 13.5%     33.1%    53.4%         112
  combined_plus_network    13.5%     33.1%    53.4%         112
```

`original_only` is twice as large-metro-weighted in the small stratum as the
MWPVL arms. Ranking the arms on a pooled lift would rank them on that table
and nothing else. So every lift below is reported **per stratum, with n**,
and pooled only after direct standardisation to a common mix.

**Two measurement choices, both declared.**

1. *The null is analytic.* `choice.evaluate` computes its uniform null by
   ranking a constant score, so `np.argsort` breaks every tie by row order and
   "uniform top-10" degenerates into "is the chosen ZCTA among the first ten
   rows of the frame". Lift is taken against `min(k, J) / J` instead, which is
   the expected hit rate of a genuinely uniform guess and has no tie-break.
   The empirical figure is still emitted beside it for continuity.
2. *The reference mix is `combined`'s.* It is the largest arm and a superset
   of three of the other four, so standardising to it asks every arm the same
   question mix and asks it about the panel the project actually holds.
   Weights 13.5% / 33.1% / 53.4%.

**A stratum is marked THIN and not compared when the arm holds fewer than 20
DISTINCT decisions in it.** 50 re-splits of 7 decisions produce 136
decision-evaluations and exactly 7 decisions' worth of information; counting
the evaluations would have made every cell look informative.

## 3. The result, on all three measures

### 3.1 Measure 1 — coefficient precision

**Nothing in this section is inference, and the one claim that was read as
inference has been withdrawn.** Every bracket below is a 2.5th-97.5th
percentile spread over 50 re-splits of one fixed decision set. It is not a
confidence interval, not a standard error, and a bracket that happens to sit
clear of 1.0 is not a finding about the world — §9 item 1 said so before §12
proved it, and §12.7 item 1 records what fell. Read this section as a
description of how the fits move when the split moves, and nothing else.

Ratios to households, the numeraire; 2.5th-97.5th percentile over the 50
re-split fits. The verdict column is derived from the two percentiles by the
rule in `panel_print.verdict` and is not itself stored: **anything whose
upper end is below 1e-6 is the positivity boundary, not a finding.**
`choice.py` sets `beta_k = exp(theta_k)`, so a covariate the optimiser wants
to discard is driven towards `theta = -inf` and lands at 1e-15, which
formally "excludes 1.0" and means nothing. `choice_inference` already refuses
to put a sandwich interval on such a parameter.

```
  arm                     covariate            beta    [2.5,   97.5]   width  verdict
  original_only           land_area          0.0380  [0.0000, 0.2611]  0.2611  boundary inside
                          establishments     0.0021  [0.0000, 0.0000]  0.0000  BOUNDARY
                          warehousing        1.5282  [0.9850, 2.5497]  1.5648  spans 1.0
  mwpvl_only              land_area          0.0000  [0.0000, 0.0000]  0.0000  BOUNDARY
                          establishments     0.4964  [0.0936, 0.9374]  0.8438  clear of 1.0
                          warehousing        1.1949  [0.8856, 1.6310]  0.7453  spans 1.0
  mwpvl_clean             land_area          0.0000  [0.0000, 0.0000]  0.0000  BOUNDARY
                          establishments     0.3979  [0.0780, 1.1549]  1.0768  spans 1.0
                          warehousing        1.1918  [0.8821, 1.6714]  0.7892  spans 1.0
  combined                land_area          0.0000  [0.0000, 0.0000]  0.0000  BOUNDARY
                          establishments     0.2991  [0.0223, 0.7117]  0.6894  clear of 1.0
                          warehousing        1.1912  [0.9558, 1.4901]  0.5343  spans 1.0
  combined_plus_network   land_area          0.0000  [0.0000, 0.0000]  0.0000  BOUNDARY
                          establishments     0.3441  [0.0008, 0.9411]  0.9403  clear of 1.0
                          warehousing        1.4189  [1.1342, 2.0474]  0.9132  clear of 1.0
                          sortation_prox     0.1039  [0.0000, 0.2102]  0.2102  boundary inside
                          fulfilment_prox    0.1868  [0.0585, 0.3263]  0.2677  clear of 1.0
                          network_50mi       0.0041  [0.0000, 0.0401]  0.0401  boundary inside
```

The verdict column used to read `EXCLUDES 1.0`. It now reads **`clear of
1.0`**, because "excludes" is the language of inference and this column is a
percentile spread. The change of wording is the whole point of §12.

Four readings.

**1. On WIDTH, `combined` wins and the ordering is monotone in sample size.**
Ordered by fitted decisions rather than by arm: 1.5648 at 94 -> 0.7892 at 360
-> 0.7453 at 389 -> 0.5343 at 483. More decisions buy a tighter spread, which
is what they are supposed to buy, and this is the cleanest single result in
the file. (On the previous run this ordering had one inversion; on the current
artefact it has none.)

**2. `combined_plus_network` is the only arm whose `warehousing_establishments`
spread sits clear of the numeraire, and that is a fact about the spread, not
about warehouses.** 1.4189 [1.1342, 2.0474] does not contain 1.0. Its width is
**0.9132 against `combined`'s 0.5343 — 71% WIDER**, so whatever moved is the
point estimate (1.19 to 1.42), not the precision. Asked properly, the same
quantity on the same arm contains 1.0: the metro-clustered bootstrap gives
**1.3481 [0.9970, 1.9582]** and both sandwiches agree (§12). The defensible
sentence is: *adding the network covariates raises the estimated worth of a
warehouse from about 1.2 households to about 1.4, and no estimator that is
inference separates either figure from 1.0.*

> **WITHDRAWN — this is what reading 2 used to say, kept here and in §12.7 so
> the retraction is legible:** *"On EXCLUDING 1.0, only `combined_plus_network`
> does it, and it does it the wrong way round. 1.4009 [1.0368, 1.8683] is the
> first `warehousing_establishments` interval in this project that does not
> contain the numeraire... and the lower end clears 1.0 by 3.7% ... which is
> weaker than 'significant' and is the strongest thing this project has ever
> been able to say here."* Two things are wrong with it. The figures were
> superseded by a re-run (the spread is now 1.4189 [1.1342, 2.0474] on 483
> decisions, not 1.4009 [1.0368, 1.8683] on 485), and — the part that matters
> — calling a re-split percentile an "interval" that "does not contain the
> numeraire" reads a spread as inference. §12 ran the inference. It contains
> 1.0.

**3. Which arm puts `establishments` in the interior and away from 1.0 has
CHANGED, and the old answer is now the wrong one.** On the current artefact
`mwpvl_only` (0.4964 [0.0936, 0.9374]) and `combined` (0.2991 [0.0223,
0.7117]) both sit clear of 1.0 with a lower end off the boundary, and
`mwpvl_clean` — which used to be the only arm that did — no longer does: its
upper end is 1.1549 and its spread now straddles the numeraire. So the
previous conclusion, *"cleaning the MWPVL rows bought one clean interior
parameter that no other arm has"*, does not survive the re-run. What survives
is weaker and less interesting: on this panel `establishments` sits below the
numeraire in most arms, and which arms it sits clear of 1.0 in is not stable
across runs — which is itself a reason not to build on the verdict column.

**4. `land_area_sqmi` is at the boundary in four arms of five** and has the
boundary inside its interval in the fifth. `NOTES_GBM_BENCHMARK.md` measured
that the GBM gives this column 18.5% of its split gain. More data does not
rescue it, cleaner data does not rescue it, and network covariates do not
rescue it. The restriction `beta > 0` inside a log is what kills it, and that
diagnosis is now tested on five panels instead of one.

### 3.2 Measure 2 — lift, stratified, then standardised

Top-10 lift over `min(10, J)/J`, conditional logit, 50 re-splits. `n` is
distinct decisions in the arm **in that stratum**; the arm's own fitted
decision count is in the first column, because a lift quoted without its arm
and its n is the error this project spent a day undoing.

```
  arm (fitted decisions)   J<=25          26-100         J>100      std. to combined
  original_only    (94)  1.72x  n=7 THIN   2.75x n=41   6.18x n=46        2.87x
  mwpvl_only      (389)  1.44x  n=58       3.19x n=119  6.53x n=212       2.81x
  mwpvl_clean     (360)  1.44x  n=55       3.21x n=111  6.78x n=194       2.83x
  combined        (483)  1.46x  n=65       3.05x n=160  6.26x n=258       2.74x
  combined_plus_network
                  (483)  1.46x  n=65       3.12x n=160  6.29x n=258       2.77x
```

**The standardised column and the stratum columns disagree, and the stratum
columns are right.**

Standardised, `original_only` leads at 2.87x. In **both** strata where it
holds enough decisions to be compared, it comes **last**: 2.75x against
3.05-3.21x in the mid stratum, 6.18x against 6.26-6.78x in the large one. Its
standardised total is carried entirely by the small stratum, where it holds
**7 decisions**, hits all 7 on every re-split, and — this is the part that
matters — draws a chance rate of **0.583** against the other arms' 0.664.
Direct standardisation equalises the share of decisions in the `J<=25`
bucket; it cannot equalise the distribution of `J` *inside* the bucket, and
`original_only`'s seven small markets are systematically larger within it. So
three buckets are not enough to remove the confounding, and the residue runs
in `original_only`'s favour. **This is the same Simpson's paradox as §2, one
level down, and it is the reason the brief's instruction to report n per
stratum was the right instruction.**

On the informative strata under the conditional logit, the ranking is:

```
  mid 26-100    mwpvl_clean 3.21 (n=111)  >  mwpvl_only 3.19 (n=119)
                >  +network 3.12 (n=160)  >  combined 3.05 (n=160)
                >  original_only 2.75 (n=41)
  large >100    mwpvl_clean 6.78 (n=194)  >  mwpvl_only 6.53 (n=212)
                >  +network 6.29 (n=258)  >  combined 6.26 (n=258)
                >  original_only 6.18 (n=46)
```

**`mwpvl_clean` wins both.** Under the GBM the picture is less tidy —
`mwpvl_only` leads the mid stratum at 3.21x and `original_only` leads the
large one at 7.04x on 46 decisions — which is itself a finding and is taken
up in §6.

A caution against reading the spread as large: from best to worst arm the mid
stratum spans 2.75x to 3.21x and the large stratum 6.18x to 6.78x, while a
single method's top-10 rate moves by an sd of 0.026-0.072 across re-splits.
Everything is in the same place. That is the data-ceiling signature
`NOTES_GBM_BENCHMARK.md` §6 named, and five panel compositions do not break
it.

### 3.3 Measure 3 — Brier, and why it cannot rank the arms

The raw pair, model and the arm's own uniform null, over the same rows.

```
  arm                     model Brier   uniform-null Brier   alternative rows
  original_only              0.007550             0.007986             11,715
  mwpvl_only                 0.004687             0.004994             74,967
  mwpvl_clean                0.004714             0.005048             69,388
  combined                   0.005036             0.005368             86,682
  combined_plus_network      0.005030             0.005368             86,682
```

Every arm beats its own null. **That is the only thing this table says.**
`choice.evaluate` averages the squared error over every alternative ROW, so
an arm with 86,682 rows divides the same per-decision error across seven
times as many near-zero terms as one with 11,715. `original_only`'s 0.007550
is not worse than `mwpvl_only`'s 0.004687; it is measured on a seventh of the
denominator.

**And the obvious repair is forbidden.** Dividing the model Brier by the null
Brier would make the arms comparable and it would be a skill score, which
`MODEL_SPEC.md` §9.1 rules out as a headline on Gneiting & Raftery (2007)
§2.3 p.362 — skill scores "are generally improper, even if the underlying
scoring rule S is proper". So the Brier column is reported as a pair, per
arm, and it **does not rank the arms**. Any ranking on it in this file would
be either wrong or improper.

The one Brier comparison in the file that IS valid is `combined` against
`combined_plus_network`, because those two hold the identical rows. It is in
§5.

## 4. What the dropped rows look like

`mwpvl_clean` is the only arm that drops, and the drop is not random. From
`panel_experiments.json.drop_profile`:

```
                              kept    dropped      undated     unvouched
                                       (both)       (n=142)       (n=47)
  rows                         415        172          142            47
  has a numeric open_year      415         30            0            30
  median open_year            2021       2024           --          2024
  has square_feet              365        103           79            26
  median square_feet       137,500    150,000      156,500       142,200
  MWPVL vouches for it         100%      72.7%        88.0%            0%
  region  South               34.5%      31.4%        31.0%         31.9%
          West                24.1%      25.6%        24.7%         29.8%
          Northeast           20.7%      22.7%        21.1%         29.8%
          Midwest             19.3%      19.2%        21.8%          8.5%
  overlap undated AND unvouched: 17
```

Three things, in order of how much they should worry a reader.

**1. The drop selects on TIME, not on geography or size.** The dropped rows
MWPVL does date have a median opening of **2024 against the kept rows' 2021**
— they are the front of the pipeline, announcements and recent builds. The
region shares agree to within **3.1 points on all four** regions (the 47
unvouched rows on their own are Midwest-light, 8.5% against 19.3%, which is
4 rows) and the median square footage differs by 9.1%. So the filter removes
*late and uncertain*, not *southern* or *small*.

**2. The undated filter looks enormous and costs the fit NOTHING.** It
removes 142 rows, 24.2% of the arm's input, and **0 fitted decisions** — the
ledger in §1.2 shows `mwpvl_clean` dropping 0 rows for "no year" because
`choice.build` had already dropped every one of them for having no CBP
vintage. The entire difference between `mwpvl_only` (389 decisions) and
`mwpvl_clean` (360) is the **29 decisions** contributed by dated unvouched
rows.

**And on the current artefact this reverses the claim that used to sit here.**
The previous run read the `warehousing_establishments` spread narrowing
0.8830 -> 0.6182 between those two arms and concluded that removing 29
announcement-stage rows bought a 30% tighter interval on a *smaller* sample.
It does not. On the current run the spread goes **0.7453 -> 0.7892** — it gets
**5.9% WIDER**, which is the ordinary direction for losing 29 decisions. So
cleaning the MWPVL rows does not buy precision; the only thing it still buys
is the stratum lift in §3.2, and one of the two legs that argument stood on is
gone.

**3. `mwpvl_clean`'s decisions are a strict subset of `mwpvl_only`'s.**
Verified in the artefact (`mwpvl_clean_subset_of_mwpvl_only: true`), so the
comparison between those two arms is a nested one and the 29 dropped
decisions are the whole of the difference.

**The honest worry this does not dispose of.** Dropping on *availability of a
date* is dropping on data quality, and data quality correlates with how long
a facility has existed. `mwpvl_clean` is therefore a slightly older, slightly
more settled panel, and older facilities are the ones whose warehousing
neighbourhoods have had longer to develop. Nothing here measures how much of
`mwpvl_clean`'s advantage in §3.2 is that rather than cleanliness.

## 5. The network covariates: what was built, and what it bought

### 5.1 What was built, and the time constraint

The OCR recovered 1,904 facilities; 811 of them are **US non-delivery-station**
buildings (tables 01-07 and 09; tables 10-11 are rest-of-world and cannot
feed a US station). Parcels flow FC -> sortation centre -> delivery station,
so where the feeding network already sits is a theoretically motivated
predictor, and it is one no specification in this project has ever had.

```
  811   non-DS US facilities in data/interim/mwpvl_facilities.csv
 -243   no numeric open_year        -> CANNOT be placed in time, excluded
  -17   postcode is not a panel ZCTA -> cannot be placed in space, excluded
        (5 of those 17 are also undated, so 255 are excluded in all)
  ----
  556   usable:  259 fulfilment, 92 sortation, 73 heavy/bulky, 50 inbound
        cross-dock, 49 fresh hub, 18 fresh DC, 15 air gateway, 0 Whole Foods DC
        (the Whole Foods table carries 0 dates of 11 rows)
```

**The time constraint is enforced structurally, not by a filter.** The
network is materialised as 14 annual vintages, 2017-2030; vintage `Y` holds
only facilities with `open_year <= Y`; and a decision is scored on the latest
vintage strictly earlier than its own opening year — the identical rule
`choice.build` already applies to CBP. A facility that cannot be dated cannot
be placed in a vintage and is one of the 243. Two facilities carry OCR-damaged
years beyond 2030 (the 2045 and 2090); they are not corrected and they are
inert, because no vintage ever contains them.

Three covariates, and the form is forced by the model:

```
  sortation_proximity    1 / (1 + road miles to the nearest ALREADY-OPEN
                         sortation centre);  0 if none exists yet
  fulfilment_proximity   same, nearest fulfilment centre
  network_within_50mi    count of already-open non-DS US facilities within
                         50 road miles
```

`choice.py` enforces `beta_k = exp(theta_k) > 0`, so every column must be one
where more is more attractive. A distance is the wrong sign, so distances
enter through a kernel that is strictly decreasing in distance and strictly
positive. It is a strictly monotone transform of the mileage, so the GBM
loses nothing by being handed it. Distances are ZCTA-centroid to
ZCTA-centroid (0 of 104 national rows carry a coordinate —
`warehouse/national` §caveat 2) times the project's own 1.30 circuity factor.

**The honest cost, paid deliberately.** Neither a proximity nor a radius
count is EXTENSIVE, so adding them breaks the exact zone-merger invariance
that `MODEL_SPEC.md` §1 buys from Train §3.4 Example 2. This is the same cost
`models/accessibility.py` declared and switched itself off over. It is the
first thing to hold against anything in this section.

**The 50-mile radius is a choice and it is reported as one.** The cost
model's `default_linehaul_miles` is 25 and describes the last-mile leg;
sortation-to-station is a middle-mile leg and is longer. The arm was
therefore re-run at 25, 50 and 100 miles. It makes no difference at all:

```
  count radius     standardised top-10 lift     beta(network_within_Rmi)
      25 mi                 2.7677               0.00316 [0.0, 0.0432]
      50 mi                 2.7682               0.00409 [0.0, 0.0401]
     100 mi                 2.7671               1.7e-14 [0.0, 5.3e-14]
```

and the reason it makes no difference is that the count covariate is **at or
next to the positivity boundary at every radius**. The radius does not matter
because the covariate does not work. The two proximity kernels are unaffected
to four decimal places by the radius.

### 5.2 What it bought — the only valid paired comparison in this file

`combined` and `combined_plus_network` hold the **identical 483 decisions**
and take the **identical 50 splits from the identical seeds**. The artefact
asserts both (`decision_sets_identical_combined_vs_network: true`) and also
asserts that extending the CBP vintages to 2030 left every warehousing value
a decision sees unchanged (`warehousing_identical_combined_vs_network:
true`). So the market-mix problem that invalidates every other cross-arm
comparison does not arise here, and the difference is attributable to the
three added columns and to nothing else.

Paired mean difference over the 50 re-splits, `combined_plus_network` minus
`combined`, as rates over 193 held-out decisions:

```
  method                  d top-1   d top-5   d top-10   sd(top10)  better-worse   d Brier
  conditional_logit       -0.0006   +0.0107    +0.0054      0.0099        30-8    -0.0000060
  gbm stump/200 levels    +0.0171   +0.0097    +0.0101      0.0171        34-13   -0.0000140
  gbm deep/300  levels    +0.0111   +0.0161    +0.0169      0.0245        36-12   +0.0000590

  the better-worse record is on top-10 and does not sum to 50: the balance
  is re-splits where the two arms hit exactly the same decisions (12, 3 and
  2 respectively)
```

In decisions of the 193 held out (derived: the rate above times 193, which
is `0.40 * 483` rounded, and is not itself a stored field):

```
  conditional logit     -0.12 top-1   +2.06 top-5   +1.04 top-10
  gbm stump/200         +3.30 top-1   +1.88 top-5   +1.94 top-10
```

**So: yes, they helped, and by about one to two decisions in 193.** Three
things about that number.

**1. The sign is consistent and the most consistent effect is not top-1.**
The logit's top-5 improves in **39 of 50 re-splits and worsens in 3**; its
Brier improves in **43 of 50**. Top-10 improves in 30 of 50 against 8, and
top-1 is a dead heat at 15 improved and 15 worsened, with a paired mean that
is very slightly negative. The covariates sharpen the shortlist and the long
list rather than the pick, which is what a covariate measuring *regional
position* should be expected to do and was not predicted in advance.

**2. It is smaller than the split-to-split spread of any single method**, as
everything in this project's prediction results has been. The paired sd of
the logit's top-10 difference is 0.0099 against a paired mean of 0.0054, so a
reader handed one split could not detect it. The W-L records are **not a sign
test**: the 50 re-splits resample the same 483 decisions and are not
independent, the identical caveat `NOTES_GBM_BENCHMARK.md` §8 item 4 attaches
to its own records.

**3. The coefficient result is larger than the prediction result**, and that
inversion is the interesting part. Three added columns move top-10 by 0.5
percentage points and move the `warehousing_establishments` re-split spread
from 1.191 [0.956, 1.490] to 1.419 [1.134, 2.047]. Prediction barely notices;
the spread moves a lot — and §12 shows that under actual inference the move
does not separate either figure from 1.0.
`fulfilment_proximity` at 0.187 [0.059, 0.326] is **strictly interior** in
every one of the 50 re-splits. **`sortation_proximity` is not, and this
sentence used to claim it was**: at 0.104 [0.000, 0.210] its 2.5th percentile
is 2.6e-15, so a boundary solution is inside its interval in at least 2.5% of
re-splits. One of the two proximities survives the "interior in every
re-split" description; the other does not. On this panel, a ZCTA at the mean
fulfilment proximity carries about 19% of the attraction that a ZCTA at the
mean household count does.

**Why the warehousing coefficient rose is not established.** The plausible
story is that proximity to the FC and sortation network absorbs an
urban-core component that `households` was carrying as the numeraire,
raising everything measured relative to it. That is a story, it is not
measured here, and it is listed in §9.

## 6. The GBM, and whether the data ceiling survives five-fold more data

`NOTES_GBM_BENCHMARK.md` concluded a **data ceiling with a ~1-decision
model-ceiling term**, measured at 56 training decisions. Two of its six
configurations were re-run here on all five arms: `stump/200 levels` (its
best) and `deep/300 levels` (its worst). The `shares` variants were dropped
because it measured them worth 0.04 top-10 hits against `levels`; `deep` was
kept precisely because "capacity hurts" was a 56-decision finding that should
not be assumed to survive 291.

```
  standardised top-10 lift          logit    gbm stump   gbm deep
  original_only                      2.87       3.08       2.61
  mwpvl_only                         2.81       2.76       2.52
  mwpvl_clean                        2.83       2.72       2.49
  combined                           2.74       2.74       2.57
  combined_plus_network              2.77       2.79       2.65
```

**1. "Capacity hurts" survives, and it survives everywhere.** `deep/300` is
worse than `stump/200` on all five arms, by 0.15 to 0.48 of lift, and worse
than the conditional logit on all five as well. Five times the training data
did not buy the capacity. That is a stronger version of the benchmark's
finding than the benchmark could make on 56 training decisions.

**2. The structural model wins the Brier on every arm, all five, both
rivals.** Logit 0.005036 against stump 0.005056 and deep 0.005330 on
`combined`; 0.007550 against 0.007681 and 0.010392 on `original_only`. The
narrowest margin is on `mwpvl_only`, 0.004687 against 0.004706, which is
1.9e-5 and should be read as a tie rather than a win. `MODEL_SPEC.md` §9.1
makes the Brier pair the headline, and on the headline the conditional logit
is never beaten.

**3. The GBM's advantage at top-10 has evaporated.** On the 94-decision
panel `stump/200 levels` took 0.586 top-10 against the logit's 0.542 — the
benchmark's headline gap. On `combined` it takes 0.520 against 0.520, and on
`mwpvl_only` 0.515 against 0.524, which is a **loss**. The model-ceiling term
that was worth about one decision in 38 is worth nothing measurable at 483
decisions. The most likely reading is that the 56-training-decision logit was
underfitting relative to a stump ensemble, and 290 training decisions closed
that gap — which is a statement about sample size, not about functional form,
and it is consistent with a data ceiling rather than against it.

**4. The GBM likes the network covariates more than the logit does.** Paired
top-1 +0.0171 against -0.0006, top-10 +0.0101 against +0.0054. A tree can use
a proximity non-monotonically — "close to a sortation centre but not on top of
one" — and `ln(beta'a)` with `beta > 0` cannot say that. It is worth about
three top-1 decisions in 193 and it is the clearest model-ceiling term in the
file.

## 7. So which arm wins? The three measures disagree, and here is the ranking

```
                          1. coefficient           2. lift, informative     3. Brier
                             precision                strata (logit)
  original_only           WORST  width 1.565      last in both              n/a
                          spans 1.0                (2.75 mid, 6.18 large)
  mwpvl_only              width 0.745             2nd mid (3.19)            n/a
                          spans 1.0; clean         2nd large (6.53)
                          interior `establishments`
  mwpvl_clean             width 0.789             BEST mid (3.21)           n/a
                          spans 1.0                BEST large (6.78)
  combined                BEST width 0.534        4th mid (3.05)            n/a
                          spans 1.0; clean         4th large (6.26)
                          interior `establishments`
  combined_plus_network   width 0.913             3rd mid (3.12)            n/a
                          only arm whose spread    3rd large (6.29)
                          sits clear of 1.0 --
                          NOT a finding, see 12
```

**They do not agree, and the disagreement is informative rather than
embarrassing.**

- If the question is *"which panel gives the sharpest estimate"*, the answer
  is **`combined`**: 483 decisions, the narrowest spread, and the ordering
  of widths is monotone in decisions across all four data arms.
- If the question is *"which panel predicts best"*, the answer is
  **`mwpvl_clean`** under the conditional logit, which wins both strata where
  it holds enough decisions to be compared — while costing 123 decisions
  against `combined` and a 48% wider spread.
- If the question is *"which specification finally says something about a
  warehouse that is not also true of a household"*, **the answer is none of
  them.** `combined_plus_network` is the only arm whose re-split spread sits
  clear of 1.0, but a re-split spread is not inference and §12's bootstrap and
  both sandwiches put the same coefficient across 1.0. This bullet previously
  named `combined_plus_network` and it was wrong to.
- Brier **cannot** rank them, for the reason in §3.3, and pretending
  otherwise would require an improper score.

**The single recommendation, if one is wanted.** `combined_plus_network` on
the `mwpvl_clean` filter has not been run and is the obvious next arm: it
would combine the only filter that improved prediction with the only
covariates that moved a coefficient. It is one line of `panel_arms.py`.

## 8. Can prediction be improved with the data we hold? An honest no, with the ceiling located

```
  best standardised top-10 lift, any arm, any algorithm    3.08x
  worst                                                    2.49x
  total spread across 5 panels x 3 algorithms              0.59x

  paired gain from three theoretically motivated,
  time-respecting covariates the model had never had      +0.0054 to +0.0169
                                                          top-10, i.e. +1.0 to
                                                          +3.3 decisions of 193
```

Five panel compositions ranging from 94 to 483 decisions, a curated panel and
an OCR'd one, a filtered panel and an unfiltered one, a linear-index
structural model and two tree ensembles, and a covariate class nobody had
tried, all land between 2.49x and 3.08x lift and between 0.469 and 0.586 raw
top-10. **Nothing available to this project moves that number by more than it
moves from one re-split to the next.**

What that does and does not license:

```
  ESTABLISHED   more decisions buy a narrower spread, monotonically:
                1.565 -> 0.789 -> 0.745 -> 0.534 as n goes 94 -> 360 -> 389
                -> 483. The spread tightens with sample size. It did not stop.
  WITHDRAWN     that cleaning on the source's own vouching narrows the
                spread while REMOVING 29 decisions. On the current artefact
                it WIDENS it, 0.745 -> 0.789, which is the ordinary
                sample-size direction. See sec. 4 item 2.
  QUALIFIED     position relative to the pre-existing non-DS network carries
                real, strictly positive weight. `fulfilment_proximity` is
                interior in every re-split; `sortation_proximity` is not
                (2.5th percentile 2.6e-15). Under the clustered bootstrap in
                sec. 12 both hold, weakly, and neither survives the
                `mwpvl_clean` filter.
  NOT SHOWN     that any of it improves prediction by more than about one to
                three held-out decisions in 193.
  NOT SHOWN     that "no learner can predict Amazon siting". What was
                measured is a ceiling on SEVEN columns for THESE panels.
```

The blunt version, for the write-up: *the data has a ceiling, it sits at
about 2.7x lift over chance and about 52% top-10, and five compositions, two
algorithms and a new covariate class all arrive within a re-split's noise of
it. What the extra data and the new covariates bought was not accuracy, and
— once §12 asked the question properly — it was not a coefficient result
either. Every estimator in this project that is inference still puts
`warehousing_establishments` across 1.0.*

## 9. What this does NOT settle

Ranked by how much each would change the reading.

**1. A percentile over re-splits is still not a standard error.** The 50
re-splits resample the same decisions, so they are not independent and the
spread understates true sampling variability —
`NOTES_EXPANDED_REFIT.md` §8 item 1 and `NOTES_GBM_BENCHMARK.md` §8 item 4
say the same thing. **The whole of the "excludes 1.0" claim in §3.1 rested on
this quantity**, and it was the claim most likely to dissolve under
`choice_inference`'s metro-clustered bootstrap. That bootstrap has since been
run on this arm, in §12, and the claim dissolved. This item is discharged and
kept only so the prediction and its outcome sit in the same file.

**2. The network covariates break aggregation invariance.** §5.1. The
`ln(beta'a)` form is the whole of `MODEL_SPEC.md` §1's argument, and it is
bought by every attraction being extensive. A proximity is not. So the arm
that produced the headline coefficient is the one arm that is not
zone-merger invariant, and the coefficient is therefore partly a statement
about the Census's ZCTA boundaries. `models/accessibility.py` refused to
ship for exactly this reason; this file ships and declares.

**3. 257 of 811 non-DS facilities are excluded, and the exclusion is not
uniform across facility types.** By table, the share excluded runs:

```
  whole foods DC     100.0%  (11 rows, 0 dates)      air gateway     37.5%
  heavy/bulky DS      39.7%                          fulfilment      33.0%
  inbound cross-dock  27.5%                          fresh hub       24.6%
  sortation           20.2%                          fresh DC        18.2%
```

The two covariates that carry weight sit on the two best-covered tables
(sortation 20.2% missing, fulfilment 33.0%), which is lucky rather than
designed. An undated facility is one MWPVL printed less about, and the
network is therefore measured with a systematic hole. The direction of the
resulting bias in `sortation_proximity` is not known: a missing facility
makes every ZCTA look further from the network than it is, which attenuates
— but only if the missingness is unrelated to location, and nothing tests
that.

**4. The standardisation does not fully remove the market-mix confound.**
§3.2 demonstrates the residue: `original_only`'s `J<=25` stratum has a chance
rate of 0.583 against the other arms' 0.677, so the arms differ in `J` WITHIN
a bucket. Finer buckets would reduce it and would make every cell thinner.
The honest fix is to report stratum lifts with n, which is what is done, and
to refuse to rank on the standardised column, which is also what is done.

**5. The splits are not clustered by metro.** Inherited deliberately from
`choice_runner`, `gbm_benchmark` and `refit_expanded` so all four are
comparable. It inflates every arm's absolute accuracy and inflates the big
arms more, because 230 CBSAs with 483 decisions repeat within metro more than
62 with 94. Every lift in §3.2 is optimistic and they are optimistic by
different amounts.

**6. The leakage question is untouched here.**
`NOTES_COVARIATE_LEAKAGE.md` establishes that `warehousing_establishments`
may contain its own outcome, and every arm in this file is built on it. If
that column is contaminated, then `combined_plus_network`'s 1.401 is a
contaminated 1.401. The clean test is
`models/leakage_decisive.py`, which is being built in parallel and is not
read here.

**7. `mwpvl_clean`'s advantage may be an age effect, not a cleanliness
effect.** §4. Dropping undated and unvouched rows leaves an older panel, and
older facilities sit in neighbourhoods whose warehousing counts have had
longer to settle. Nothing here separates the two.

**8. Why `warehousing_establishments` rose to 1.40 is a story, not a
measurement.** §5.2. The obvious test is to add the two proximity covariates
one at a time and read the path; it costs two more arms and was not run.

**9. The boundary verdict in §3.1 is derived in the printer, not stored.**
`panel_print.verdict` computes it from `beta_p025` and `beta_p975`, which
ARE in the artefact, by the rule stated in §3.1. That is one step better than
the working figures this project keeps re-measuring by hand and one step
worse than an emitted field.

## 10. How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.panel_experiments
```

About 27 minutes on one core: five arms x 50 re-splits x three methods, plus
three radius variants of the network arm at the logit only. Requires
`data/external/facility_panel/national_facilities_expanded.csv`,
`data/interim/mwpvl_facilities.csv` and `data/interim/cbp_detail.parquet`;
the runner raises with the ingest command rather than quietly fitting
something else. Writes `outputs/metrics/panel_experiments.json` and prints
the tables in §1.2, §2, §3 and §5.2.

The console table can be regenerated from the artefact alone, without
refitting:

```python
  import json
  from siting_atlas.models.panel_print import report_text
  print(report_text(json.load(open("outputs/metrics/panel_experiments.json"))))
```

## 11. Related

- [`NOTES_EXPANDED_REFIT.md`](NOTES_EXPANDED_REFIT.md) — the two-arm refit
  this extends, whose original and expanded arms this reproduces exactly, and
  whose §8 item 3 asked for the drop ledger now in §1.2.
- [`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) — the 50-re-split
  protocol, the grid two of whose six configurations are re-run here, and the
  data-ceiling verdict §8 does not overturn.
- [`NOTES_COVARIATE_LEAKAGE.md`](NOTES_COVARIATE_LEAKAGE.md) — why the time
  constraint in §5.1 is not optional, and the contamination §9 item 6 leaves
  open.
- [`NOTES_gneiting_raftery_2007.md`](NOTES_gneiting_raftery_2007.md) §6.3 —
  why §3.3 refuses to normalise the Brier scores into something comparable.
- [`../data/PANEL_EXPANSION.md`](../data/PANEL_EXPANSION.md) — the merge that
  built the 693-row file, its `mwpvl_vouched` column, and its nine reasons to
  distrust the result.
- [`../MODEL_SPEC.md`](../MODEL_SPEC.md) §9 — the reporting rule this file
  follows and §1's invariance argument that §5.1 knowingly breaks.
- `outputs/metrics/lift_by_market_size.json` — the Simpson's paradox that
  reorganised this experiment, §2.
- `experiments/gravity-network/artefacts/network_inference.json` — the metro-clustered
  bootstrap, the two sandwiches, the measured cost of the invariance
  break and the sixth arm. Written by
  `src/siting_atlas/models/network_inference.py` and reported in §12.

## 12. The headline, tested properly. It does not survive.

> **Provenance note, 2026-09-15.** This section was written against the
> 2026-09-14 run of `network_inference.json` on the then-current 700-row
> panel. The artefact has since been **re-run** —
> `run_id 20260915-210640-dbcd`, `written_at 2026-09-15T21:21:38Z` — on the
> **693-row / 687-facility / 483-decision** panel. The headline figures below
> have been requoted from that re-run and the decision counts corrected
> (483, not 485; `mwpvl_clean_plus_network` 360, not 362). **The verdict is
> unchanged in every respect**: the point estimate moved 1.312 → 1.348, the
> clustered bootstrap moved [0.977, 1.919] → [0.997, 1.958], the
> metro-clustered sandwich [0.961, 1.792] → [0.981, 1.852] and the
> independent-decision sandwich [0.864, 1.993] → [0.880, 2.066], and all
> three still contain 1.0. §§12.1-12.6 have been requoted from the re-run as
> well; where a figure moved far enough to change a sentence, the sentence
> says so rather than just carrying the new digits. Three such reversals are
> flagged in place: `establishments` now *contains* 1.0 under the clustered
> bootstrap (§12.2), `sortation_proximity` no longer clears zero (§12.4), and
> §12.8 item 7 is discharged.

*Re-run 2026-09-15; first run 2026-09-14, after everything above. Artefact:
`experiments/gravity-network/artefacts/network_inference.json`; seed 20260914; 500
metro-clustered bootstrap replicates per arm. Every figure below is read
out of that artefact or out of `panel_experiments.json`, except two that
are neither and say so where they appear: the binomial error in §12.2 is
derived from a stored share, and the reproduction check in §12.1 is a
standalone re-run. Code:
`src/siting_atlas/models/network_inference.py` and its six helpers
(`network_data`, `network_bootstrap`, `network_sandwich`, `network_merge`,
`network_resplit`, `network_print`). §9 item 1 of this file said the
"excludes 1.0" claim "is the claim most likely to dissolve under
`choice_inference`'s metro-clustered bootstrap, which has not been run on
this arm and should be". It has now been run.*

**The one-line result: it dissolved. The metro-clustered bootstrap puts
`warehousing_establishments` at 1.348 [0.997, 1.958]; both sandwiches
agree; §3.1's "first interval in this project's history that does not
contain the numeraire" is withdrawn.** The two proximity coefficients
survive, weakly, and one of the two claims made about them in §5.2 does
not.

```
  warehousing_establishments on combined_plus_network, asked five ways
  (all five from the 2026-09-15 re-run, 483 decisions)

                                          beta    interval        width  verdict
  re-split percentiles (see 3.1)        1.4189  [1.1342, 2.0474]  0.913  clear of 1.0
    -- NOT a standard error, see 9 item 1
  MLE on all 483 decisions              1.3481   --                  --  --
  bootstrap over 194 METROS, R=500      1.3481  [0.9970, 1.9582]  0.961  contains 1.0
  sandwich clustered by metro           1.3481  [0.9812, 1.8523]  0.871  contains 1.0
                                                                          p = 0.065
  sandwich, independent decisions       1.3481  [0.8797, 2.0658]  1.186  contains 1.0
                                                                          p = 0.170
```

Three of the three estimators that are inference contain 1.0. The one
that excludes it is the one that is not inference.

### 12.1 The point estimate was never 1.40 on all the data

`panel_harness._coefficients` reports `beta_mean` as
`np.exp(np.vstack(thetas)).mean(axis=0)` — the mean of 50 BETAS, each
fitted on the 290 training decisions of one re-split. The maximum
likelihood estimate on all **483** decisions is **1.3481**
(`converged=True`, McFadden rho-squared 0.1806).

So the bracket in §3.1 is not centred on the estimate the full panel
gives: it clears 1.0 at the bottom by 13.4% while sitting around a point
5.3% above the full-sample MLE. Two explanations are available and
neither is separable from the artefacts this project holds. Averaging
`exp(theta)` over noisy fits is biased upward by convexity, and 290
decisions are noisier than 483; and the estimator itself may move with n.
`panel_experiments.json` stores the percentiles and the mean of beta but
not the 50 thetas, so the two cannot be told apart without a re-run. What
can be said without one is that the number quoted and the number the data
gives are not the same number.

**A third explanation was available and has been ruled out — and the
mismatch it was about has since closed.** `data/processed/panel.parquet` was
rebuilt at 15:02 on 2026-09-14, 21 minutes after that day's
`panel_experiments.json` was written, by other work in this tree. The rebuild
gave coordinates to two more ZCTAs, so 556 non-delivery-station facilities
could be placed in space and time against the published run's 554 — one extra
fulfilment centre, one extra sortation centre. **Both artefacts have since
been re-run and both now report `kept: 556`** under `network_facilities` and
`network_covariates`, so the residual this paragraph was written to bound no
longer exists. The bound is kept because it is what licensed §12 to be read
beside §§1-11 in the first place.

```
  candidate ZCTAs                     25,022 published   25,022 now
  combined_plus_network decisions        483                483
  mwpvl_clean_plus_network decisions     360                360
  mwpvl_clean choice-set size mix   15.3 / 30.8 / 53.9  identical
```

The choice sets did not move. Neither did the extensive covariates: a
standalone re-run of `panel_harness.measure` on `mwpvl_clean` today
reproduces its published top-1, top-5 and top-10 to every digit
(0.15517, 0.38621, 0.53545) and its Brier to 1.6e-13 — that check is not
a stored field, and it is the only figure in this section that is
neither. And the two proximity columns are barely moved either. The
artefact's `facility_set_sensitivity` refits the arm five times, each
time dropping one random sortation centre and one random fulfilment
centre from the 556:

```
  covariate            all 556     mean       min       max     range
  warehousing          1.34810   1.34473   1.34152   1.34870   0.00718
  sortation_prox       0.09701   0.09387   0.07970   0.09789   0.01819
  fulfilment_prox      0.17049   0.16818   0.16084   0.17180   0.01095
```

Two facilities in or out of the two tables that carry the weight move
`warehousing_establishments` over a range of **0.0072**, which is 0.5% of
the point estimate and ten times too small to account for the 0.071
between 1.4189 and 1.3481. The gap is the estimator, not the input.

### 12.2 The clustered bootstrap

500 replicates, resampling whole METROS with replacement — 194 of them,
holding 483 decisions — and refitting each. The driver is
`choice_bootstrap.refit` on `choice_bootstrap.resample_decisions` with
draws from the same seeded generator in the same order as
`choice_bootstrap.bootstrap`'s own loop; it is spread over five cores
because a replicate costs a measured 4.5 wall-seconds on this arm. The
artefact records the check rather than the assertion: the parallel and
the sequential drivers agree to **0.0e+00** in beta over four replicates
(`parallel_matches_sequential`).

```
  covariate            beta     over 194 metros      verdict      replicates
                                                                 at the boundary
  land_area          0.0000   one-sided, < 0.0000    BOUNDARY           99.6%
  establishments     0.3146   [0.0000, 1.0115]       CONTAINS 1.0        3.0%
  warehousing        1.3481   [0.9970, 1.9582]       CONTAINS 1.0        0.0%
  sortation_prox     0.0970   [0.0000, 0.2472]       below 1.0           3.8%
  fulfilment_prox    0.1705   [0.0246, 0.3998]       below 1.0           1.6%
  network_50mi       0.0000   one-sided, < 0.0672    BOUNDARY           80.8%
```

`establishments` has moved since the first run: its clustered upper end is
now 1.0115 rather than 0.9204, so it **contains** 1.0 rather than sitting
below it. 97.4% of replicates are still below 1.0, but that is not the
verdict the interval gives.

`choice_inference._interval` sets one `excludes_ratio_one` flag for both
sides of the numeraire, so an untouched printer would have called a
proximity whose upper end is 0.26 and a warehouse coefficient whose lower
end is 1.04 by the same two words. `network_print.verdict` now prints the
SIDE, because the side is the entire claim. For the three covariates that
are worth LESS than one household the interesting null is not 1.0 at all;
it is zero, and the last column is the only thing in this project that
can speak to it.

**How close is close.** 15 of the 500 clustered replicates — **3.0%** —
put `warehousing_establishments` below 1.0, against the 2.5% an exclusion
would need. The Monte Carlo error on that share at R = 500 is 0.8
points (derived: the binomial standard error of a 3.0% share at R = 500,
not a stored field), so the verdict is "contains" by a margin well inside
one Monte Carlo standard error of itself. Said on the endpoint instead:
the 2.5th percentile is 0.9970 with a Monte Carlo error of **0.0140**, and it
sits 0.0030 from 1.0 — **0.22 of its own Monte Carlo error away**.
`choice_bootstrap`'s stopping rule asks for ten. It was not met and the
run is marked `capped: true, settled: false` in the artefact.

The right reading of that is not "run more replicates". It is that **the
lower endpoint of the clustered interval is indistinguishable from
exactly 1.0** — on the current run it is closer to 1.0 than on the first
one, 0.22 Monte Carlo errors rather than 0.94. That is a different sentence
from "the interval excludes 1.0" and a much weaker one, and at 0.22 MCSE it
is also a different sentence from "the interval comfortably contains 1.0".
The honest word is **does not exclude**.

**And the clustered interval is still WIDER than the spread it replaces, on
MORE data — but only just.** 0.961 against 0.913, **5% wider**, while being
fitted on 483 decisions against the re-splits' 290. Sample size should have
pushed the other way, so the direction of the demonstration survives: a
percentile over re-splits understates. On the first run the gap was 13% and
this paragraph could lean on it. At 5% it cannot, and the argument is left
standing at its real size.

### 12.3 The sandwich, its two refusals, and a direction nobody expected

`choice_sandwich.sandwich` **REFUSED** two parameters and no number was
forced out of it for either: `land_area_sqmi` at beta = 5.3e-19 and
`network_within_50mi` at beta = 1.6e-14. Both are `exp(theta)` running to
zero, both are outside the interior optimum the sandwich asymptotics
assume, and the refusal is the correct output.

On the four interior parameters, with the null that matters — `beta = 1`,
the numeraire, never `beta = 0`:

```
  covariate          independent decisions        clustered by metro     se ratio
  establishments   [0.0615, 1.6089] p = 0.165  [0.0794, 1.2471] p=0.100    0.844
  warehousing      [0.8797, 2.0658] p = 0.170  [0.9812, 1.8523] p=0.065    0.744
  sortation_prox   [0.0284, 0.3312] p < 0.001  [0.0291, 0.3232] p<0.001    0.980
  fulfilment_prox  [0.0551, 0.5276] p = 0.002  [0.0633, 0.4592] p<0.001    0.877

  Liang-Zeger CR0, 194 clusters, 483 decisions. The small-cluster factor
  G/(G-1) * (N-1)/(N-K) = 1.0115 is reported and NOT applied, so a reader
  can apply it rather than have it applied silently. It changes nothing
  at the third decimal.
```

`warehousing_establishments` contains 1.0 both ways, at p = 0.170
assuming independent decisions and p = 0.065 clustering by metro.

**Clustering by metro TIGHTENED the interval, and that is the opposite of
what everyone including this project assumed.** The metro-clustered
standard error on `warehousing_establishments` is **0.744 times** the
independent-decisions one, and the within-metro design effect on its
score — `sum_g (sum_n s_n)^2 / sum_n s_n^2` — is **0.858**. A design
effect below one means the scores of two decisions in one metro partly
CANCEL. There is a mechanism available: the score of a decision is
positive when its chosen ZCTA is warehousing-rich relative to its metro's
average and negative when it is not, Amazon does not open twice in the
same ZCTA, so a metro contributing several openings tends to contribute
some of each and the metro sum is smaller than the sum of magnitudes.
That is a story consistent with the number; it is not tested here and it
should not be repeated as though it were.

What it does NOT do is rescue the claim. The clustered sandwich is the
narrower of the two and it still contains 1.0.

**One thing no sandwich in this project can ever test.** `choice.py` sets
`beta_k = exp(theta_k)`, so `beta = 0` is `theta = -inf`: an infinitely
distant point in the parameter the standard error is computed in. A Wald
test against zero therefore does not exist in this parameterisation, for
any covariate, at any sample size. For an extensive covariate that costs
nothing, because `beta = 1` is the interesting null. For a proximity it
costs the interesting null outright, and only the bootstrap — which can
put an atom of its replicates exactly at zero and count them — can say
anything about it. That is what the "at boundary" column above is for.

### 12.4 The two proximities under proper inference

```
                       point   bootstrap over metros   share of replicates
                                                             AT zero
  sortation_prox      0.0970   [0.0000, 0.2472]              3.8%
  fulfilment_prox     0.1705   [0.0246, 0.3998]              1.6%
    for comparison, the re-split spread of 3.1 / 5.2, not a s.e.:
  sortation_prox      0.1039   [0.0000, 0.2102]      boundary inside
  fulfilment_prox     0.1868   [0.0585, 0.3263]      interior
```

**One survives and one does not, and on the first run both did.**
`fulfilment_proximity`'s 95% clustered interval still lies strictly above
zero, [0.025, 0.400], with 1.6% of replicates at the boundary.
`sortation_proximity`'s does not: its lower endpoint is now exactly zero and
3.8% of clustered replicates — more than the 2.5% the interval allows — send
it to the boundary. Both sandwiches still reject `beta = 1` for both columns
(p < 0.001 clustered), but that null means "worth much less than one
household", not "distinguishable from nothing", and for
`sortation_proximity` the interesting null is zero and it is no longer
cleared.

And **§5.2's stronger claim does not survive for either column, and §8's
"ESTABLISHED" line that repeats it must be softened.** That claim was that
the proximities are "strictly interior in every one of the 50 re-splits".
On the current run `sortation_proximity` is not even that: its own re-split
2.5th percentile is 2.6e-15. Resample METROS instead of re-splitting
decisions and 3.8% and 1.6% of replicates send the two columns to exactly
zero. Being interior in 50 of 50 re-splits of a fixed sample is a weaker
fact than it reads as, for the same reason the percentile spread is a weaker
fact than it reads as: the re-splits all contain most of the same decisions.

### 12.5 The theoretical cost, measured rather than conceded

§5.1 and §9 item 2 both say the network covariates break the zone-merger
invariance `MODEL_SPEC.md` §1 rests on. Neither says by how much. Here is
how much.

**The test is Train's own condition.** §3.4 Example 2, printed p. 54:
merging zones `j` and `k` into `c` must give `P_j + P_k = P_c`, which for
this functional form holds exactly when `a_j + a_k = a_c`. Every
alternative pair inside each metro is merged, one pair at a time, at the
fitted beta, with counts adding and proximities taking the maximum — the
maximum is EXACT for a proximity, because the nearest sortation centre to
the union of two ZCTAs is the nearer of the two nearest.
`network_within_50mi` also takes the maximum and there it is a lower
bound rather than exact, which is declared in `network_merge.py` and
matters to nothing because its coefficient is at the boundary on every
fit in this project.

```
  |P_c - (P_j + P_k)| / (P_j + P_k), over 43,224 merged pairs

  specification                    median        p90        max
  combined (extensive only)      0.00e+00   2.22e-16   5.55e-16   <- the control
  combined_plus_network          4.36e-02   1.35e-01   4.55e-01
```

The control is zero to machine precision, which is what validates the
measurement rather than the model. On the network arm the median merged
pair loses **4.38%** of its attraction and the worst loses **45.5%**.

**And the estimate moves when the map is redrawn.** Pair the ZCTAs of
every metro at random, merge them, refit, 20 times, same 20 maps for both
specifications:

```
  specification                beta    merged mean      min      max   mean |shift|
  combined_plus_network      1.3481         1.2969   1.0050   1.6836         11.0%
  combined extensive only    1.1589         1.0742   0.8881   1.2611          8.8%
```

Two honest readings of that pair. The network arm is more sensitive to
the map, but only by 1.2x — coarsening a choice set moves any estimate,
and most of this movement is not the invariance break. **The invariance
break is the table above it, where the control is exactly zero and this
arm is not.** And the random pairing UNDERSTATES the break: a real zone
merger joins ADJACENT ZCTAs, adjacent ZCTAs have similar proximities, so
`min(p_j, p_k)` is close to `max(p_j, p_k)` and the leak is at its
largest. Random pairs usually put one zone much nearer the network than
the other.

**So what is this model now?** Three statements, in decreasing comfort.

1. *It is still a conditional logit.* The likelihood is well defined, the
   probabilities sum to one over each metro's ZCTAs, estimation is
   ordinary maximum likelihood and nothing in McFadden's framework
   objects to a covariate being a proximity. As a model of choice among
   the ZCTAs AS THE CENSUS DREW THEM it is exactly as legitimate as the
   published arm.
2. *Its functional form is no longer derived.* `MODEL_SPEC.md` §1 is the
   only justification this project offers for `V = ln(beta'a)` in place
   of the ordinary linear-in-parameters `V = beta'x`, and that
   justification is the merger argument above. With a proximity inside
   the log the argument does not run, so the log survives only on the two
   conveniences that are left: it keeps `beta'a > 0`, and it makes
   `beta_k` readable as "worth this many households". Those are reasons
   to like a form. They are not a derivation, and `MODEL_SPEC.md` §1's
   "what this means for the specification" item 2 contemplated intensive
   variables entering ELSEWHERE in `V` and losing exact invariance. These
   enter inside the log, which is the case it did not contemplate.
3. *The coefficient is now partly a statement about ZCTA boundaries*, to
   the tune of the two tables above.

The operational consequence, and it is the one that matters for the
write-up: **a capstone cannot print "our specification is invariant to
how the Census drew ZCTA boundaries, per Train §3.4 Example 2" and print
this arm's coefficients on the same page.** One of those two has to go.
`models/accessibility.py` resolved the same conflict by switching itself
off.

### 12.6 `mwpvl_clean_plus_network`: the arm §7 named and nobody ran

One line of `panel_arms.py`, as §7 said. The frame is added to
`arm_frames` and deliberately NOT to `ARM_NAMES`, so
`panel_experiments.py` still runs exactly the five arms this file
describes and nothing above moves. 360 decisions in 169 metros, 69,388
alternatives, and the artefact asserts what makes it a paired arm:
`decision_sets_identical: true` and `warehousing_identical: true` against
`mwpvl_clean`.

**Measure 1, coefficients.**

```
  covariate          point   bootstrap over 169 metros  at bd   sandwich (metro)
  land_area         0.0000   one-sided, < 0.0000        100%    REFUSED
  establishments    0.3733   [0.0000, 1.4077]           5.6%    [0.098, 1.422] p=.149
  warehousing       1.2114   [0.8446, 1.9850]           0.0%    [0.840, 1.746] p=.304
  sortation_prox    0.0319   [0.0000, 0.1987]          30.4%    [0.001, 0.802] p=.036
  fulfilment_prox   0.0817   [0.0000, 0.2584]          19.8%    [0.015, 0.445] p=.004
  network_50mi      0.0000   one-sided, < 0.1415       67.4%    REFUSED

  its own re-split spread (NOT a standard error, and reported only
  because it is the quantity 3.1 used):
  establishments    0.4103   [0.0708, 1.2510]
  warehousing       1.2918   [0.8900, 1.8455]      <- contains 1.0 even here
  sortation_prox    0.0467   [0.0000, 0.1380]      <- boundary inside, even here
  fulfilment_prox   0.0784   [0.0000, 0.1978]      <- boundary inside, even here
```

**The exclusion does not reappear, and it does not even reappear on the
weak measure.** Crossing the only filter that improved prediction with the
only covariates that moved a coefficient gives
`warehousing_establishments` 1.211 [0.845, 1.985] clustered — further from
1.0 at the bottom than `combined_plus_network` was, not closer — and the
re-split spread itself now starts at 0.890.

**And the proximities collapse.** 30.4% and 19.8% of clustered replicates
put them at exactly zero, against 3.8% and 1.6% on `combined_plus_network`.
The point estimates fall by 67% and 52%, 0.097 to 0.032 and 0.170 to
0.082. The 29 dated-but-unvouched decisions that separate `mwpvl_clean`
from `mwpvl_only` are not the whole story: `mwpvl_clean_plus_network`
holds **123** fewer decisions than `combined_plus_network`, which is
`original_only`'s 94 plus those 29. Whatever the network
covariates were carrying on the full panel, this filter removes most of it.

**Measure 2, lift, per stratum, with distinct-decision n.** All three
strata clear the 20-decision floor, so nothing here is THIN and nothing
has to be refused. Against `mwpvl_clean`, its own paired baseline, on
identical decisions:

```
  conditional logit, top-10 lift over min(10, J)/J

  stratum        n    mwpvl_clean   +network    chance rate
  small <=25    55       1.436        1.433         0.667
  mid 26-100   111       3.206        3.228         0.222
  large >100   194       6.779        6.652         0.046
  standardised to combined's mix       2.832       2.823
```

The standardised column moves by 0.009x and the stratum columns disagree
about the sign: the network covariates help in the mid stratum by 0.022x
and hurt in the large one by 0.127x. **The standardised total is printed
and is not ranked on**, for the reason §3.2 gives and demonstrates. Note
also that the Simpson residue §9 item 4 identified is small for THIS
comparison and large for others: the two arms here share identical
decisions, so their chance rates are identical by construction, which is
exactly why a paired arm is the only honest cross-arm comparison in this
family.

**Measure 3, Brier**, model and the arm's own uniform null over the same
69,388 rows. The rows are identical to `mwpvl_clean`'s, so the null is
identical too, and this is the second valid paired Brier comparison in
the file after §5.2's:

```
                             model      uniform null
  mwpvl_clean              0.004714       0.005048
  mwpvl_clean_plus_network 0.004715       0.005048
```

The paired mean difference is **+1.1e-07**, and positive is WORSE. On
`combined` the three network columns improved the logit's Brier in 43
re-splits of 50; here they improve it in 28 of 50, which is a coin, and
the mean still comes out on the wrong side.

**The paired prediction difference, +network minus baseline, over 50
identical re-splits of the identical 360 decisions** (not a sign test —
the re-splits are not independent):

```
  method              d top-1    d top-5   d top-10    d Brier    W-L top10
  conditional logit   +0.0032    +0.0040   -0.0019   +1.1e-07       12-20
  gbm stump/200       +0.0061    +0.0086   +0.0081   -5.4e-06       29-13
  gbm deep/300        +0.0039    +0.0096   +0.0033   +1.1e-04       28-18

  a positive d Brier is WORSE. Only the stump ensemble's Brier improves.
  The logit's worsens by 1e-07, fifty times smaller than the stump's
  5.4e-06 gain, and the deep GBM's worsens in 44 of 50.
```

Of the 145 held-out decisions that is **+0.26 top-1, +0.22 top-5 and
-0.16 top-10** for the conditional logit: nothing, and slightly negative
on the long list. The GBM still likes them — +1.54 top-1 decisions — which
is the same asymmetry §6 item 4 found and the same explanation: a tree can
use a proximity non-monotonically and `ln(beta'a)` with `beta > 0` cannot.

**So the arm §7 recommended is a negative result, and a useful one.** It
combines the best filter with the best covariates and gets neither
benefit: no coefficient exclusion, no prediction gain under the structural
model, and proximities that go to the boundary in a fifth to a quarter of
clustered resamples.

### 12.7 What this forces to be corrected above

1. **§3.1 reading 2, §7's third bullet, and the blunt version at the end
   of §8** all say `combined_plus_network` is the only arm whose
   `warehousing_establishments` interval excludes 1.0. Under the
   metro-clustered bootstrap and under both sandwiches it does not.
   Those sentences describe the re-split spread and only the re-split
   spread, and the spread is not inference. They stand as descriptions of
   that quantity and fall as claims about the world.

   The withdrawn text is reproduced here verbatim so the retraction can be
   checked against what was actually said. §3.1 reading 2 read:

   > *"**2. On EXCLUDING 1.0, only `combined_plus_network` does it, and it
   > does it the wrong way round.** 1.4009 [1.0368, 1.8683] is the first
   > `warehousing_establishments` interval in this project that does not
   > contain the numeraire. But its width is **0.8314 against `combined`'s
   > 0.5602 — 48% WIDER.** The exclusion is bought by the point estimate
   > moving from 1.17 to 1.40, not by the interval tightening. And the lower
   > end clears 1.0 by 3.7%, on a quantity that is explicitly not a standard
   > error (§9 item 1). The defensible sentence is: adding the network
   > covariates raises the estimated worth of a warehouse from about 1.2
   > households to about 1.4, and on this spread the 2.5th percentile is just
   > above one — which is weaker than 'significant' and is the strongest
   > thing this project has ever been able to say here."*

   and the file's opening paragraph read:

   > *"`combined_plus_network` is the first specification in this project's
   > history whose `warehousing_establishments` interval excludes 1.0 —
   > **1.401 [1.037, 1.868]** — and it manages that by moving the point
   > estimate, not by tightening the interval, which got 48% wider."*

   Both are withdrawn on two counts. The inference count is the one above.
   The arithmetic count is separate and was found later: the figures were
   read from a superseded run of `panel_experiments.json`. On the current
   artefact the same spread is **1.4189 [1.1342, 2.0474]**, width 0.9132
   against `combined`'s 0.5343 — **71% wider, not 48%** — on **483**
   decisions, not 485. Neither number is inference and neither should be
   quoted as one.
2. **§5.2 and §8's third ESTABLISHED line** say the proximities carry
   "real, interior, strictly positive weight in every re-split". On the
   full panel only `fulfilment_proximity` survives that, as a 95% clustered
   interval above zero with 1.6% of replicates at zero;
   `sortation_proximity` has 3.8% at zero and a clustered lower endpoint of
   exactly zero. On the `mwpvl_clean` filter neither survives: 30.4% and
   19.8%.
3. **§9 item 1 was right**, and is now discharged.
4. **§9 item 5** says the splits are not clustered by metro and every
   lift is therefore optimistic. That remains true of every lift in this
   file, including §12.6's. The clustering has now been respected in the
   INFERENCE and still not in the SPLITS.

### 12.8 What §12 does not settle

1. **The per-decision bootstrap was not run**, and the artefact says so
   in `per_decision_bootstrap` rather than leaving a gap. It costs about
   8 wall-seconds a replicate against the clustered bootstrap's 4.5, one
   attempt had a pool worker killed by the host part way through, and the
   comparison it provides — what respecting the metro clustering costs —
   is available analytically and exactly from the two sandwiches, which
   differ in nothing but whether the meat is summed over decisions or
   over metros.
2. **500 replicates is a cost ceiling, not a convergence claim.**
   `choice_bootstrap.R_MAX` is 4,000 and its stopping rule can never fire
   on an endpoint that is genuinely near 1.0, because the rule asks the
   endpoint to be ten Monte Carlo errors away from 1.0. Every endpoint in
   this section carries its own Monte Carlo error so the reader can see
   what R is buying. For the verdict that matters it buys nothing: the
   endpoint is **0.22** MC errors from 1.0 — it was 0.94 on the first run —
   and more replicates would sharpen that number, not move it.
3. **Why the warehousing coefficient rose from 1.17 to 1.31 is still a
   story**, exactly as §9 item 8 said. Adding the proximities one at a
   time was not run here either.
4. **The leakage question is still untouched.** §9 item 6. Every number
   in this section sits on `warehousing_establishments`, and if that
   column contains its own outcome then a contaminated 1.3481 is what has
   been shown not to exclude 1.0.
5. **The metro-clustered sandwich being NARROWER than the independent one
   is measured and not explained.** The design effect is 0.905 and the
   mechanism offered in §12.3 is a conjecture. If it is wrong, the
   direction is still measured and the conclusion is unaffected, because
   the wider of the two also contains 1.0.
6. **The merge experiment pairs ZCTAs at random, not by adjacency.** §12.5
   argues the direction of that approximation is conservative. It does not
   measure it, and it would need ZCTA geometry the `ChoiceData` object
   does not carry.
7. **~~`panel_experiments.json` no longer reproduces exactly~~ — DISCHARGED
   2026-09-15.** The complaint was that the artefact this file is about was
   written 21 minutes before one of its inputs was rebuilt, that §12.1 could
   only bound the effect on two coefficients, and that the honest fix was to
   re-run `panel_experiments`. It has since been re-run on the 693-row panel,
   and so has `network_inference`; §§1-11 above are requoted from that
   re-run. The bound in §12.1 is no longer load-bearing. What replaces this
   item is smaller and still open: `panel_experiments.json` **still carries
   no `run_id` and no `written_at`**, so only its file mtime dates it.
8. **The `facility_set_sensitivity` drops two facilities at random.** It
   does not identify the two the rebuild added, which would need the
   pre-rebuild panel, so it bounds the effect of a perturbation of that
   size and kind rather than measuring the actual one.

### 12.9 How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.network_inference
```

About 70 minutes on five cores of a loaded six-core host: two
500-replicate metro-clustered bootstraps (35 and 28 minutes), two fits,
four sandwiches, five facility-set refits, the 43,224-pair merger test,
40 merged refits and 50 re-splits of the new arm. The per-decision
bootstraps are opt-in and off by default; §12.8 item 1 says why.
Writes `experiments/gravity-network/artefacts/network_inference.json` after every stage, so a
run that is interrupted leaves a file that says how far it got in
`stages_completed`. The console table regenerates from the artefact alone:

```python
  import json
  from siting_atlas.models.network_print import report_text
  print(report_text(json.load(open("experiments/gravity-network/artefacts/network_inference.json"))))
```
