# Status — the measured state of the project

*State as of 2026-09-15. Every number below is re-derived in
[`NUMBERS.md`](NUMBERS.md), which names the artefact and the `run_id` behind
each one and is the tie-breaker when this page and anything else disagree.
[`ROADMAP.md`](ROADMAP.md) is the only forward-looking document; this one is
the ledger.*

**Standing rule: cite the artefact, not the figure.** Several headline
numbers in this project have been invalidated by re-running the code that
produced them, and not one of those moves was caused by a parameter. Where a
`run_id` is given, quote the `run_id`; the number beside it is a convenience.

---

## Orientation — the project in five lines

Siting Atlas asks two questions about last-mile delivery, using public data
only: **how does Amazon pick its next sites, and what does it cost to deliver
a parcel?**

```
  1  The cost question is answered. 8,037 ZIP-code areas -- 57.8% of US
     households -- costed from a Daganzo continuous approximation over
     the operator's 501 REAL delivery stations, median $1.1389 per parcel.
  2  The siting question is answered with a NEGATIVE, and it is
     pre-registered. The metro-entry model loses to a households baseline
     in 7 of 7 held-out years.
  3  Four prediction models have been specified, fitted and scored. None
     earns its parameters. Every failure is measured and published.
  4  693 facility rows / 687 buildings, from OSHA enforcement records plus
     an OCR pass over a published industry census.
  5  660 tests collected, 658 passing, ruff clean.
```

**Four things to know before you discuss this project with anyone.**

1. **The negative results are pre-registered measurements, not excuses.**
   [`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md) (md5
   `946f7ef75db69e5278eea409a04c3823`) fixed the question, sample,
   covariates, model forms, baselines and success criterion before anything
   was fitted, and wrote both outcomes' language in advance. The outcome was
   H0 and the H0 paragraph is quoted unsoftened.
2. **The cost model is the positive result and it is not small.** It runs on
   real data, it decomposes, and its sensitivity is reported across five
   scenarios.
3. **The load-bearing covariate was audited to the point of doubt and
   published anyway.** `warehousing_establishments` carries the choice model;
   the guard against it containing its own outcome is late by a median 34
   months; the decisive test was run and the covariate keeps 79% of its value
   on the 29 decisions that support the test.
4. **The engineering works and the science does not.** The pipeline, cost,
   depot network, optimiser and gates are all real and reproducible. The
   failure is contained to the prediction layer.

---

## 1. What works

Built, running on real data, and not in dispute.

```
  COMPONENT            ARTEFACT / EVIDENCE
  data pipeline        L0 acquire -> L1 normalise -> L2 warehouse ->
                       L3 panel. panel_report.json,
                       run 20260914-220244-d57b: 1,081,312 rows x 50 cols
  cost to serve        cost_by_station.json, run 20260916-131845-34f1
  depot network        OBSERVED, not solved. cost/stations.py, the 501
                       geocoded delivery stations; the p-median in
                       cost/depots.py is retired from the cost path
  portfolio optimiser  portfolio_report.json, run 20260914-002431-7419
  Monte Carlo          montecarlo_report.json + montecarlo_draws.parquet,
                       500 of 500 draws, seed 20260914
  NLRB coverage        nlrb_coverage.json
  edit registry        warehouse/edits.py, Fellegi-Holt dispositions
  flag gate            warehouse/flag_gate.py
  figures, dashboard   viz/build.py and app/dashboard.py share the chart
                       functions, so they cannot disagree
  tests                660 collected across 49 files; 658 passed,
                       2 xfail, 0 failures (2026-09-15, exit 0)
  ruff                 `ruff check src tests` clean
```

**Cost to serve** — `cost_by_station.json`, run `20260916-131845-34f1`,
2023Q4 baseline:

```
  median cost per parcel   $1.1389    p10 $1.0008   p90 $1.3445
  pooled cost per parcel   $1.1281    (sum dollars / sum parcels)
  ZCTAs costed              8,037    57.8% of US households (74.4M)
  total daily cost     $47,434,701    on 42,048,849 daily parcels
  vans                    250,291    ceil of summed van-days
  depots                      501    REAL geocoded stations, of which
                                      481 carry at least one costed ZCTA
  metros with a station       174
  median line haul        9.09 mi    against 4.02 on the retired pilot
  scenario span    -17.2% / +7.7%    dense_routing / congested
```

Stop-weighted cost decomposition: **service time 59.75%, vehicle 21.63%,
drive time 12.63%, distance 5.98%**. Labour at the door still carries the
bill, but **driving and fuel are now 18.6% of the stop against 10.1% on the
pilot**, because line haul to a real building is more than twice as long as
to a solved one. The old summary — "the routing mathematics is decoration" —
belongs to the pilot and should not be repeated. Any document quoting shares
that do not sum to 100% is quoting a historical bug recorded at
`optimize/runner.py:156`.

**What the change cost, and why it is a finding.** Deleting the 334-depot
p-median and substituting the 501 buildings the operator actually runs moves
the median **+5.2%** ($1.0830 → $1.1389) and the median line haul **×2.26**.
A p-median minimises demand-weighted distance by construction, so it is a
lower bound on line haul; real siting is constrained by land, labour, zoning
and lease terms. The 5.2% is the measured price of that constraint. Full
before/after: [`NUMBERS.md`](NUMBERS.md) §10.3.

**Coverage caveats.** 20 of 501 stations have no ZCTA within 15 miles. 316
ZCTAs (0.83% of catchment households) are dropped for having no OEWS driver
wage and **nothing is imputed**. 8 of the 501 are `announced` rather than
open. All 501 are Amazon, facility type `DS`. Regime bounds rose with the
sparser catchment: 6.17% of costed ZCTAs fall below one tour (was 5.40%) and
1.69% below the Larson–Odoni `n ≥ 15` floor (was 1.24%), carrying 0.077% and
0.0035% of households.

**The cheapest-decile statistic is withdrawn** — see [`NUMBERS.md`](NUMBERS.md)
§10.4. It is not restated with new digits; the test is not identified once
the depots are the facilities.

**Portfolio** — `portfolio_report.json`, run `20260914-002431-7419`:

```
  activations                 282   of a 500 capacity
  capital               $1.128bn    of a $2bn budget
  break-even margin        1.3431   upper bound 1.2129
  optimality gap            10.7%
```

**Monte Carlo, 500 draws** — `montecarlo_report.json`, seed 20260914:
activations p10 151.9 / p50 264.5 / p90 306.1. It settles three things. 282
sits at the 67th percentile and the superseded 330 at the 97th, so the drift
between published headlines was real and the parameters did not cause it.
`capital_usd` is exactly $4m × n in all 500 draws, so the three published
capital figures were the three activation counts restated. And
`cannibalisation_peak` dominates the spread (correlation −0.63 with n).
**It is not a confidence interval** — every range is ours, from
`data/PARAMETERS.md`, eight with no external source — and
`parcels_per_depot_per_day` was never sampled (`optimize/montecarlo.py:128`,
"excluded by oversight"), so every band is a floor.

**NLRB coverage** — `nlrb_coverage.json`. Chapman 630 cities / 54.0% OSHA
coverage (a ceiling); Chao 899 / 37.8% (a tighter ceiling); three-list
log-linear 314–417 / 33–44%. Dependence is **measured, not assumed**, because
OpenStreetMap supplies a third list whose capture mechanism is unrelated to
worker grievance.

### The facility panel

`data/external/facility_panel/national_facilities_expanded.csv`, with
`mwpvl_merge.json` (`20260915-195256-1c53`) as the accounting artefact.

```
  693  rows in the expanded panel        (was 104 before the merge)
  687  buildings -- 693 minus the six rows the OSHA E_operating_by edit
       rejects; the rows stay in the CSV so the exclusion is reversible
  691  distinct address+ZIP pairs        (a fourth number, not "buildings")
  551  rows carrying a numeric open_year; 434 also carry a quarter
  230  distinct CBSAs, 50 states, 0 coordinates in the CSV
```

`E_operating_by` on the 693-row panel: 551 dated, 136 linked to an OSHA
building, 6 falsified, **95.59% pass**, 415 unchecked because no OSHA match
exists. That is a different denominator from the 94.71% in the extraction
check below — same edit, different frame, both current. Neither is 93.6%.

**The only correct full sentence is "483 decisions on 687 buildings from 693
rows".** 700 rows and 694 buildings are stale and must be swept.

### Opening dates, from OCR of a published industry census

MWPVL International's public 2025 Q1 network article states opening months
and years in **table images**. All thirteen tables were read.
`mwpvl_extraction.json`, `20260915-195231-c54f`:

```
  1,904  facilities across 13 table images
  1,420  with an opening year
    873  with an opening month
     44  flagged "not confirmed" by the publisher itself
    635  US small-package delivery stations -- the only eligible class
```

Credit where it is due: the facts are MWPVL's; what this project did was read
them out of the images and test them. Three independent validations were run
before a row entered a panel.

```
  OSHA E_operating_by, all 1,420 dated rows   208 linked, 11 falsified,
    (mwpvl_validation.json,                   94.71% pass. By precision:
     20260915-195247-dbb5)                    month 160/9, year 25/2,
                                              quarter 23/0
  date plausibility                           99.5% = (1,420 - 7)/1,420
  OCR state column vs the ZIP crosswalk       604 agree of 606 comparable
    (mwpvl_merge.json ocr_state_grade)        = 99.67%; 613 parsed of 635
```

For scale on the same falsification test, the satellite method failed it on
36% of its output (§4). 94.71% is not a certificate — an unchecked row is not
a passing row — but it is the difference between a method and a guess.

The merge itself: 635 eligible rows in the file → 634 after internal dedup →
**589 added**, 40 already in the panel, 5 held for clerical review. A
facility-class filter at the panel boundary excludes 1,269 rows of the wrong
class; without it, fulfilment centres, Japanese mini-stations and Canadian
air hubs would have entered a US delivery-station panel silently.

### The measured visibility gap

`mwpvl_coverage.json`. Two independent city lists, not a numerator and a
denominator:

```
  488  cities where MWPVL lists an Amazon DELIVERY STATION
  340  cities where OSHA ever inspected ANY Amazon facility class
  138  in both
  350  MWPVL cities OSHA has never inspected
```

So of the 488 cities MWPVL says have a delivery station, OSHA has a record in
138 — **28.3%**. Two qualifications travel with it. The comparison is
**conservative**: OSHA's side is unrestricted by facility class, so narrowing
it would widen the gap. And it is a **floor, not an estimate** — a two-list
intersection, not capture-recapture, and MWPVL is itself incomplete. The
modelled estimate is in `nlrb_coverage.json`.

---

## 2. What is fitted

### The conditional ZCTA-choice model

`panel_experiments.json` (mtime 2026-09-15 13:37:43, **no `run_id` field**).
Large-metro top-10 lift, conditional logit, by panel arm:

```
  arm                     n_decisions   large-stratum   cond. logit lift
  original_only                    94             46              6.180
  mwpvl_only                      389            212              6.526
  mwpvl_clean                     360            194              6.779
  combined                        483            258              6.258
  combined_plus_network           483            258              6.290
```

**Quintupling the panel bought no ranking accuracy.** It did not cost any
either. The quantity is `arms.<arm>.methods.<method>.strata.top10.large_gt100.lift`;
always name arm **and** method **and** artefact, because four different
artefacts publish a "large-metro top-10 lift" on four different frames.
`lift_by_market_size.json` is **retired** — no emitter, no run_id, an
internally contradictory `finding` field — and its 6.14 / 6.42 pair must not
be quoted.

### The GBM benchmark

`gbm_benchmark.json`, `20260915-200312-1d51`. 94 decisions, 38 test, 50
repeats. **Quote `across_repeats`, never `headline_split`** — the artefact
carries its own `headline_split_warning` that perturbing the attraction
matrix by 1e-12 moves the single-split top-10 by up to 2 of 38, with no
LightGBM determinism flag fixing it.

```
  gbm stump/200 levels   22.26 of 38   sd 2.75   Brier 0.007681
  raw_count              20.96         sd 2.50   Brier 0.007793
  conditional_logit      20.60         sd 2.72   Brier 0.007550  <- best
  gbm deep/300 levels    18.76         sd 2.48   Brier 0.010392
```

A shallow GBM beats the fitted model by about 1.7 hits of 38; the conditional
logit still has the best Brier. The ordering is stable under perturbation.

### The covariate-leakage test — RUN, and the covariate mostly survives

`leakage_decisive.json`, seed 20260914, 50 paired re-splits, three arms on
the **same 29 decisions**. Write-up:
[`research/NOTES_LEAKAGE_DECISIVE.md`](research/NOTES_LEAKAGE_DECISIVE.md).

```
  arm            top-10 hits of 12   vs no_covariate
  osha_bound              9.24        +4.76, 50 wins / 0 losses
  true_date               8.22        +3.74, 50 wins / 0 losses
  no_covariate            4.48        --
```

Forced onto a CBP vintage strictly earlier than MWPVL's *stated* opening
rather than the OSHA bound, the covariate retains **3.74 / 4.76 = 79%** of
its measured value and still beats the floor on 50 of 50 re-splits. It does
not survive cleanly: the test cost 65 of the 94 working decisions (69%), it
cannot separate the leak from the staleness that removing the leak
introduces, and the test set is 12 decisions.

**Earlier documents said this test "has NOT been run". It was run, and this
is its result.**

### Gravity versus proximity

`gravity_network.json`, `20260915-210603-b780`, 483 decisions / 86,682
alternatives / 50 re-splits, 13 arms over the same decisions and splits.

```
  arm                     large top-10 lift   standardised   pooled Brier
  no_network (floor)               6.2585        2.7399        0.0050363
  proximity_published              6.2903        2.7682        0.0050303
  gravity_count_a3 (best)          6.2187        2.7671        0.0050165
```

**Do not quote a single scalar for "gravity vs proximity" — it depends on k.**
On large-metro top-10 the best fully-interior gravity arm is *below* both the
published proximity baseline and the no-network floor. Gravity wins on top-1
(+0.0116, 42 improved / 4 worsened), top-5 (+0.0126, 44 / 2) and Brier, and
loses top-10 by 0.0002 (18 / 22).

### The dispersion regularity

Same artefact, vintage 2030, 41 large metros. Of the 21 network terms with a
`mean_within_metro_cv`: 7 below 0.6, **0 between 0.6 and 1.3**, 14 above 1.3.
Reading each term's boundary state in the arm where it is fitted:

```
  cv < 0.6    7 terms    0 interior    7 not interior
  cv > 1.3   14 terms    9 interior    5 not interior
```

The strongest claim the evidence supports: low within-metro dispersion is
**sufficient for failure** (7 of 7 land at the boundary); high dispersion is
**necessary but not sufficient for success**. The 5 high-cv failures are all
sortation-side, 4 of them square-footage masses. With n = 21 non-independent
terms from one run at one vintage, this is a **descriptive regularity within
one artefact**, not an estimated relationship. Anything resting on
`boundary_census` alone covers 5 of the 21 terms and is too thin.

### The metro-entry model — H0, pre-registered

`metro_entry.json`, `20260915-231322-7d21`. Verdict arm `prereg_strict`,
form `logit`, declared before any model was fitted.

```
  years won on AUC vs the households baseline    0 of 7   clause 1 fails
  years calibrated at least as well as the
    constant null                                3 of 7   clause 2 fails

  pooled out-of-time AUC   model 0.7323
                           households baseline 0.8949
                           facilities baseline 0.7325
                           year-base-rate null 0.5367     6,545 rows,
                                                          306 events
  clustered bootstrap      AUC - households -0.1628,
                           95% [-0.2011, -0.1313]         2,000 draws,
                                                          935 clusters
```

**H0 on every arm × form** (prereg_strict / vintage_clean / vintage_relaxed ×
logit / poisson / negbin), and H0 also with 2020–21 excluded. Write-up:
[`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md).

### The hazard revival — retirement stands

`hazard_revival.json`, `20260915-224104-21a7`. The retired hazard model was
re-run on the expanded data to test whether its retirement was really about
sample size.

```
                          retired run        best revival arm
  events                          812                   5,441
  risk-set units                1,756                  11,230
  AUC, held out by unit        0.6894                  0.6832
  AUC, out of time             0.5551                  0.6323
  AUC, out of area             0.6168                  0.7104
```

**The constant null is better calibrated in 17 of 17 comparisons**;
`model_better_calibrated_at` is an empty list. The retirement was taken on the
unit of analysis, not on sample size or dates, and 6.7× the events does not
touch it. An opening switches on a median of **39** ZCTAs at the 15-mile
catchment (13 of them newly) — that is the independence violation, and it is
geometry, not data volume.

### Nested forward selection

`covariate_search.json`, `20260915-235210-ff92`, re-read from the completed
687-facility run. Nested forward selection is
**0.62 points worse** than the baseline *on the large-metro top-10 rate*
(30.473% → 29.852%, 50 re-splits, 5 wins / 19 ties / 26 losses). **The claim
must always name the stratum**: pooled, the same arm is **+0.36 pp**, i.e.
slightly better. Both the sign and the stratum-specificity survived the
re-run; only the magnitude moved, from −0.72 to −0.62.

---

## 3. What is blocked

```
  1  INFERENCE ON THE EXPANDED PANEL DOES NOT EXIST. choice_inference,
     choice_sandwich and the conformal sets were all run on the 104-row
     panel and none has been re-run on the 693-row one. Every bracket
     quoted from panel_experiments, gravity_network, metro_entry and
     refit_expanded is a PERCENTILE OVER RE-SPLITS of one fixed decision
     set -- the artefacts say so in a `spread_is_not_a_standard_error`
     field. Writing "95% CI" for one of them is wrong. So the project
     has the better sample and the worse inference on it.

  2  THE COEFFICIENT STILL CANNOT BE DISTINGUISHED FROM THE NUMERAIRE, and
     more data did not fix it. refit_expanded.json (20260915-195645-1f05)
     fits 94 decisions on 100 facilities in the original arm and 483 on
     687 in the expanded arm. The sample-size explanation has now been
     tested and is not sufficient.

  3  NATIONAL COVARIATES, and the expansion made this LARGER. The choice
     model joins households, land area, establishments and the CBP
     warehousing count. Rent, wages, permits and distance are not joined
     to the national frame, and the frame is now 230 CBSAs.

  4  GEOCODING. geocoded_expanded.csv reaches 72.3% (501 Match of 693,
     190 No_Match, 2 Tie) and the 501 points are NOT joined into the
     panel: national_panel_expanded.json records coordinates_present: 0,
     so every distance covariate resolves to a ZCTA centroid. The earlier
     "65.0%" was measured on the superseded 700-row panel and no file
     reproducing it survives.

  5  THE PANEL IS NOT COMMITTED. `git ls-files data/external/facility_panel/`
     returns only facilities.csv and national_facilities.csv.
     national_facilities_expanded.csv and geocoded_expanded.csv are
     untracked, so the 693-row panel exists only on one disk.

  6  78 OF 181 SOURCE MODULES ARE UNREACHABLE FROM ANY TEST, measured by an
     AST import-graph BFS seeded from every file under tests/. Every
     artefact quoted in section 2 is written by a module in that list.
     "660 tests pass" and "the headline artefacts have no test importing
     their emitter" are both true and must be quoted together.
```

---

## 4. What failed

Four programmes were run to completion and produced nothing usable as
prediction. All four are recorded as findings. Causes in
[`DECISION_LOG.md`](DECISION_LOG.md) §2.

### Satellite dating — 36% of its own estimates are logically impossible

`data/collection/satellite/colab_date_from_satellite.py`. 107 of 107 sites
returned an estimate from a median of 106 cloud-free Sentinel-2 scenes; on the
83 with a known year, 41% landed within one year, error sd 3.42 years.
**39 of 107 (36%) date construction AFTER the day an OSHA inspector found the
building already operating**, a median of 33 months after. That is not noise,
it is impossible. The confidence score does not separate the good from the
impossible (35% impossible at confidence > 2 against 30% at 1–2). The cause is
the changepoint detector, not the imagery. **Do not present the 68 surviving
estimates as dates.**

### The labelling programme — 96% wasted, by our own bug

Six batches, 362 sites labelled, 135 delivery stations, **13 genuinely new**.
`scripts/make_unlabelled_batches.py` selected rows the OSHA name regex could
not classify and never checked them against `NATIONAL_CLASSIFIED.csv`, which
already held 319 classified addresses: **289 of 362 worklist rows (79.8%) were
already classified before a prompt was sent.** "Unclassified by our regex" was
silently treated as "unknown to the project". The salvage is real but small:
the 122 already-known delivery stations are a labelled validation set for the
classifier in `ingest/osha.py`, whose agreement rate has never been measured.

**A caveat on the number 13.** It is not emitted by any code into any
artefact; it is counted by hand, it has already moved once, and rebuilding it
from the tree by address match gives 27 or 37 depending on the reference file.
**13 is a working figure and it is not reproducible from an artefact.**

### White space — the household baseline wins

`white_space.json`. The idea was to rank unserved places by a white-space
score. It wins **14 of 108 scored cells (13%)**, with **0 significant wins for
white space against 32 for the household baseline**. What it did produce is a
densification measurement worth keeping: at the headline 45-mile radius,
**68.7%–75.9%** of 2024–25 delivery-station openings land inside pre-2024
coverage (75.9% = 60 of 79 on real coordinates; 68.7% = 90 of 131 with ZCTA-
centroid fallback). **That range is across coordinate sets at one radius, not
across radii** — 67.1% is the real-coords 15-mile figure and quoting "67–77%"
silently mixes the two axes.

### The hazard model, and the metro-entry model

Both above, §2. The hazard model was retired on the unit of analysis and the
revival confirms the retirement. The metro-entry model returns a
pre-registered H0.

---

## 5. What is pending, ranked by what it buys

```
  1  COMMIT THE PANEL. The 693-row facility file and the geocoded side
     file are untracked. Everything in section 2 rests on a file that
     exists on one disk. This is the cheapest item here and the largest
     single risk on the page.

  2  RE-RUN THE INFERENCE ON THE 693-ROW PANEL. choice_inference,
     choice_sandwich and the conformal sets, on 483 decisions rather than
     94. Until then every interval on this page is a re-split percentile
     and the page has to say so each time.

  3  TESTS FOR THE EMITTERS. 78 of 181 modules are unreachable from any
     test, and they are exactly the modules that write the artefacts
     quoted above. Start with white_space*, metro_*, gravity_* and
     hazard_revival*.

  4  FIX THE run_id / written_at STAMP IN common/log_json.write_json. It
     builds {"run_id": .., "written_at": .., **payload}, so a payload that
     already carries those keys SHADOWS the fresh values. covariate_search
     resumes by reading its own artefact back in whole, so a resumed run
     inherits the previous run's id and the FIRST write's timestamp -- two
     materially different files carried one identical stamp. Strip the two
     keys from the payload before the spread; three lines, one file.
     (covariate_search.json's 694-vs-687 disagreement is RESOLVED: the
     completed re-run reads 687 at every stage. The stamp defect that made
     the two versions indistinguishable is what remains.)

  5  EMIT THE WORKING NUMBERS. Three figures still have to be labelled
     "measured by hand" and each is one line of code: the 3% OCR row-merge
     rate, the 42-row leakage lag distribution, and choice.build's drop
     ledger. Every one of them has already moved once.

  6  RETIRE lift_by_market_size.json AT ITS FIVE CITING SITES --
     research/NOTES_EXPANDED_REFIT.md, models/covariate_search.py,
     models/covariate_report.py, models/panel_strata.py -- and point all
     five at panel_experiments.json.

  7  FIX THE ACTIVATION UNIT in optimize/objective.py. The only open
     defect that moves a headline figure by a factor rather than a margin.

  8  A MISSINGNESS TREATMENT OF ANY KIND. Not-MCAR was measured and
     nothing was done; cost/runner.py:166 still does listwise deletion.

  9  MEASURE THE CLASSIFIER AGREEMENT RATE on the 122 already-known DS
     labels. The one asset the wasted batches produced.
```

---

## 6. Known open defects

```
  - optimize/objective.py prices an activation three inconsistent ways
    (:81-83 a ZCTA, :164 a facility, :158 a facility with a catchment).
    ~2.7x capital overcharge. The same unit-of-analysis error that killed
    the hazard model, in a second component.
  - 42% of depots exceed 40,000 parcels/day under nearest-depot
    assignment, heaviest 3.56x. Line haul is therefore a LOWER bound,
    biased optimistic in exactly the dense ZCTAs at the top of the ranking.
  - rent_index missing for 94.3% of ZCTAs; the observed stratum is 63.6x
    denser. Measured not-MCAR, still listwise-deleted.
  - national_facilities_expanded.csv fails ingest/facility_check: 142 rows
    have a non-numeric open_year. Carried deliberately -- the two ways to
    clear it are to drop the rows or invent a year.
  - 54 of the 634 merged rows are UNSCREENABLE for duplicates (no street
    at all); 580 are fully screenable. The ~3% OCR row-merge defect
    destroys rows rather than duplicating them, so a duplicate screen
    cannot see it by construction.
  - refit_expanded.json's arm key is "expanded_658" and the file it read
    has 693 rows. The DATA is current; only the label is behind. Quote
    `facilities`, not the key.
  - interval censoring is not implemented in models/risk_set.py.
  - enabled_flags takes min(open)/max(close), so a gap between one station
    closing and another opening is silently filled.
  - status = "announced" on expanded rows is not enforced anywhere. A
    not-yet-confirmed building enables a catchment exactly like a real
    one; mwpvl_vouched is the column a consumer has to test and no
    consumer tests it. This now reaches the cost model: 8 of the 501
    stations used as depots are "announced", 493 "open", 0 "closed".
  - depots.py:67 and params.py:220 give different depot counts (334 and
    329) in their docstrings. Both are right about different things --
    334 is per-metro ceil summed, 329 is one national division -- and
    neither says so. Both are now moot for the cost path, which no
    longer solves depots at all.
  - cost/stations.py's CATCHMENT_MILES docstring still claims the 15-mile
    costed set is DENSER than the pilot. It is sparser -- 350 against 475
    stops/sq mi. The docstring is out of date; NUMBERS.md §10.1 is right.
```

---

## 7. Decisions owed by the owner

```
  D1  Confirm the conditional-choice reframe in writing
      (adr/0004-model-change-conditional-choice.md is proposed, not
      accepted).
  D2  DS-032 (Austin) violates E_operating_by IN THE PILOT. Enforcing it
      removes Austin's only building: 1,257 ZCTAs, 27,914 cells, 39
      events. Currently REPORT disposition, pinned by a test.
  D3  source_type=permit is wrong on all 104 national and 27 pilot rows --
      they are OSHA-derived. Correcting it would let the Fellegi-Holt
      reliability weights rank dates that currently tie.
  D4  NAT-0036 was excluded only because risk_set.py has no interval
      censoring. Restore it with (panel start, 2024-04-17] when that lands.
  D5  Whether to keep the labelling programme running at all, given §4.
```

---

## 8. What this project can honestly claim today

1. **A cost model that works on real data** — 8,037 ZIP-code areas covering
   57.8% of US households, an **observed** depot layer of 501 real delivery
   stations, a decomposition that says where the money goes, and five
   sensitivity scenarios spanning −17.2% to +7.7% on the median.
   *(Rebuilt 2026-09-16 on `cost_by_station.json`. The previous claim —
   2,333 ZCTAs, a solved 334-depot network, −17.1% to +4.4% — is the retired
   pilot and is kept only as the comparison in [`NUMBERS.md`](NUMBERS.md)
   §10.2. Earlier still, that span was published as −16.6% to +4.8%, which no
   basis in any parquet reproduces.)*
2. **A pre-registered negative result on the siting question**, with both
   outcomes' language written before the model was fitted, and H0 returned on
   every arm and every model form.
3. **Four models specified, fitted, scored and beaten** — by a constant, by a
   households baseline, by a single raw covariate. Every failure is measured
   and diagnosed to a citation that survives someone opening the book (Train
   §3.7.1 printed p. 61, independence across observations — **not** §2.2).
4. **A measured ceiling on the project's own data coverage** — OSHA sees
   28.3% of the cities MWPVL names, and at most 54% of US cities with an
   Amazon facility under capture-recapture with source dependence estimated
   rather than assumed.
5. **A document-to-panel OCR pipeline with three independent validations
   attached before anything consumed it**, against a comparison that makes the
   validations mean something: the satellite method failed the first of those
   tests on 36% of its output.
6. **A load-bearing covariate audited to the point of doubt, tested, and
   published with the test's limits.**
7. **Three negative results from data-acquisition attempts** — satellite
   dating, SEC filings, and the labelling programme — each reported with the
   test that condemned it rather than quietly dropped.
8. **A sensitivity analysis that disproved its own convenient explanation.**
   The optimiser headline drifted three times and the Monte Carlo shows the
   parameters were not responsible.
