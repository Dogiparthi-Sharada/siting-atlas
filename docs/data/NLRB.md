# NLRB — the second list, and the measured coverage it buys

*Written 2026-09-13. Every figure in this document was re-derived from the artefacts on that date; section 11 is the ledger. The code is `src/siting_atlas/ingest/nlrb.py`, `nlrb_names.py`, `nlrb_estimators.py` and `nlrb_capture.py`; the tests are `tests/unit/test_nlrb.py`.*

---

## 1. In one paragraph

The National Labor Relations Board publishes every unfair-labour-practice charge and election petition it dockets. We hold 970 of them naming Amazon, spanning 2009 to 2026 and 208 cities. They are not worth much as facility rows — they carry no street address, so a filing locates a worksite to a city and no closer. They are worth a great deal as a **second list**. Until now this project had one source of Amazon locations and no way to say what a single source misses. Two incomplete lists of the same population measure each other, and the answer is that our primary source, OSHA, sees **at most about half** the cities that contain an Amazon facility, and probably nearer a third. That is the deliverable. The extra cities are a by-product.

---

## 2. What we hold, verified

```
  data/external/nlrb/nlrb_cases_amazon.csv                        877 KB
      970 rows, 16 columns, one row per case, no duplicate case numbers
      filed 2009-06-24 .. 2026-09-08
      Case Type  C 958 (unfair labour practice)  R 12 (election petition)
      209 distinct City+State as typed; 208 after normalisation
      290 distinct spellings of the employer name
      Employees on charge/petition populated 968/970, median 1,000
      NO STREET ADDRESS COLUMN.  City and state only.

  data/external/nlrb/nlrb_elections_TRUNCATED_unfiltered.csv      816 KB
      UNUSABLE.  Exactly 10,000 rows, which is an export cap and not a
      count.  Unfiltered.  Five Amazon rows, every one with a blank city,
      and all five case numbers (29-CA-261755, 29-CA-280153, 13-CA-275270,
      12-CA-308502, 29-RC-288020) are already present in the cases file.
      It contributes nothing and should be deleted, or re-pulled properly
      via Route B of HOWTO.md, which does carry street addresses.
```

Nothing in that block was taken on trust. The five duplicate case numbers were checked against the cases file individually, and the 10,000 is an exact round number in a file that was meant to be a full national extract — that is a cap, not a coincidence.

One row of the 970 is dropped by the ingest: `Amazon Construction`, which the shared namesake filter in `ingest/osha.py` excludes. We cannot tell whether it is the retailer's building programme or a firm named after the river, and dropping an ambiguous row is the conservative direction — a spurious city shows up in a count, a wrong one does not. **969 cases, 208 cities** is what everything below is built on.

---

## 3. What the source can and cannot establish

### It can bound an opening from above

`Date Filed` is the date a charge was docketed. What it proves is that Amazon was **operating at that place on that date**. That is an upper bound on the opening, the same interval-censored form OSHA gives, and it plugs into the same machinery. It will never say "opened in 2019".

### It cannot locate a building

There is no street address. The finest key the source supports is city + state, and that is the binding limitation — it shapes the estimand, the matching, and what any of this is allowed to claim. See section 4.1.

### It is not a random sample, and the non-randomness is on the confounder

NLRB cases arise where workers organise, or where one worker is wronged enough to file. Union activity correlates with facility size, with urban density and with state labour law. **Density is the variable the project's whole cost argument turns on**, so NLRB presence is selective on the confounder — the same trap as the Zillow rent data, which is missing for 94.3% of ZCTAs and observed on ZCTAs 64 times denser than average. This is a good way to expand the frame and a poor way to complete it.

The concentration is extreme and worth seeing:

```
  Staten Island, NY        195 cases     20% of the file in one city
  Florence, KY              54
  Castleton-on-Hudson, NY   41
  Bessemer, AL              33
  Seattle, WA               28
  ...
  114 of 208 cities have exactly ONE case
```

---

## 4. The coverage estimate

### 4.1 The estimand is cities, not buildings

What is estimated below is **the number of US cities (city + state) containing at least one Amazon facility**. It is not a building count, and it must never be quoted as one. OSHA's 474 distinct Amazon buildings sit in 340 cities — **1.39 buildings per city**. A 54% city-coverage figure translates into a building-coverage figure only if the cities we cannot see hold as many buildings each as the ones we can, and there is no way to test that from inside the data. If anything the unseen cities are likely to be smaller and hold fewer buildings, which would make building coverage *higher* than city coverage — but that is an argument, not a measurement, and it is not claimed here.

### 4.2 The two lists, matched on a normalised city key

```
                                         count
  NLRB cities                              208
  OSHA cities                              340
  in both                                  112
  NLRB-only (OSHA never saw them)           96
  OSHA-only                                228
  observed union                           436
```

The brief that commissioned this work quoted 209 / 340 / 108 / 101, from a plain upper-and-strip city key. That key is reproduced in the artefact under `naive_city_key` and it is exactly right for what it does; it is just the wrong key. Three of its differences were spelling variants of one place:

```
  CASTLETON-ON-HUDSON (NLRB)     vs   CASTLETON ON HUDSON (OSHA)
  ROBBINSVILLE (TOWNSHIP) (NLRB) vs   ROBBINSVILLE (OSHA)
  BROWNSTOWN (NLRB)              vs   BROWNSTOWN TOWNSHIP (OSHA)
```

Each one invented a city that "OSHA never saw" and shifted the estimate. Correcting them moves the naive Lincoln-Petersen figure from **658 to 631** and the implied coverage from **51.7% to 54.0%**. The direction is worth noting: cleaning the key made our own coverage look *better*, which is the direction one should be most suspicious of, so the normaliser was written to be end-anchored only and never to merge on string similarity. `normalise_city` is in `ingest/nlrb_names.py` and every rule in it is a pair observed in these two files, not speculative tidying.

### 4.3 The estimators, and what each is allowed to claim

```
  estimator              N        95% CI          OSHA city coverage
  --------------------------------------------------------------------
  Lincoln-Petersen     631       --                        53.9%
  Chapman              630       [575, 705]                54.0%
  Chao lower bound     899       [778, 1062]               37.8%
```

Chapman's correction is reported instead of the bare ratio because the ratio has no finite expectation when the overlap can be zero and is biased upward at small overlaps. It barely moves here (631 to 630), which is itself reassuring.

Chao's (1987) lower bound is valid under **heterogeneous catchability** — the realistic case in which some facilities are far more likely to be captured by any list than others. It returns 899 against Chapman's 630, a factor of 1.4. That gap is not noise. It is the price of the independence assumption, and it says that the simple estimate is materially too small.

### 4.4 The independence assumption is violated, and here is the measurement

This is the front of the argument, not a footnote.

Lincoln-Petersen requires that being on one list does not change your chance of being on the other. **Ours does.** OSHA inspects where workers are injured and where workers complain. NLRB dockets where workers organise. Both are driven by worker grievance, so a facility on one list is *more* likely to be on the other. Positive dependence inflates the overlap M, which deflates `n1*n2/M`.

Therefore:

> **Every population figure in this document is a LOWER BOUND on the true number of cities, and every coverage figure is an UPPER BOUND on what OSHA sees. 54% is a ceiling. It is not an estimate and it must not be written as one.**

With two lists that is where the argument would have to stop, as an assertion about a sign. We have a third list, and with three the pairwise dependence becomes estimable. Measured on the ten states where the OpenStreetMap extract exists, conditioning each pair on the third list:

```
  odds ratio                                  value    1.0 = independent
  ---------------------------------------------------------------------
  NLRB x OSHA, given OSM presence              1.84
  NLRB x OSM,  given OSHA presence             1.72
  OSHA x OSM,  given NLRB presence             3.82
```

All three are above 1. The dependence is positive, it is large, and it is now a number rather than a claim. The largest is OSHA against OpenStreetMap, which makes sense: both are biased towards big, conspicuous, long-established buildings.

### 4.5 The three-list log-linear model

Fitted on the ten states the OpenStreetMap query actually covered (`docs/data/FACILITY_PANEL_HOWTO.md`, Job 1 step 3): AZ CA CO FL ID IL NY TN TX WA. Outside them OSM has a *structurally zero* capture probability, which is not heterogeneity and which no estimator repairs, so the frame is declared rather than inferred from where rows happen to appear.

```
  within the frame:   NLRB 103    OSHA 139    OSM 110    union 228

  capture pattern (NLRB, OSHA, OSM)      cities
  ---------------------------------------------
  1 1 1                                      26
  1 1 0                                      22
  1 0 1                                      13
  1 0 0                                      42
  0 1 1                                      37
  0 1 0                                      54
  0 0 1                                      34
  0 0 0                                       ?    <- what we are estimating
```

Every hierarchical model on three lists, by Fienberg (1972). `[12]` means a dependence term between lists 1 and 2:

```
  model            df   deviance    AIC      N      95% CI       OSHA sees
  -------------------------------------------------------------------------
  [1][2][3]         3     10.84    55.5    286   [269,  309]        48.7%
  [12][3]           2     10.46    57.1    281   [262,  310]        49.5%
  [13][2]           2     10.81    57.5    285   [266,  312]        48.9%
  [23][1]           2      3.08    49.8    314   [284,  360]        44.3%  <- lowest AIC
  [12][13]          1     10.30    59.0    278   [257,  313]        50.1%
  [12][23]          1      2.31    51.0    338   [282,  451]        41.1%
  [13][23]          1      2.21    50.9    331   [286,  412]        42.0%
  [12][13][23]      0      0.00    50.7    417   [298,  742]        33.3%
```

Read three things off that table.

First, **AIC does not pick a winner.** Four models sit within 1.3 of each other (49.8, 50.7, 50.9, 51.0) and the conventional threshold for a meaningful difference is about 2. Quoting `[23][1]` because it is nominally lowest would be overfitting a model-selection statistic on seven data points. The defensible statement is the range those four span: **314 to 417 cities**, OSHA seeing **33% to 44%**.

Second, every model that carries the OSHA-OSM dependence term — the one measured at 3.82 — separates cleanly from every model that does not. Deviance drops from about 10.5 to about 2.3 the moment `[23]` enters. That is where the structure is.

Third, and this is the point of the exercise: **allowing dependence raises the population every time.** Independence says 286; the fully pairwise model says 417. The direction predicted in `HOWTO.md` section 4, before any of this data was collected, is the direction that came out.

For comparison on the identical frame, the two-list estimators give Chapman **296** and Chao **410**. The three-list pairwise model at 417 lands next to Chao, and the two agree by different routes — Chao by allowing unequal catchability, the log-linear model by estimating the dependence directly.

### 4.6 What to quote

> OSHA, our primary source of Amazon facility locations, sees **at most 54% of the US cities that contain an Amazon facility, and plausibly as little as a third**. The upper figure assumes the two sources are independent; they are not, and the dependence has been measured at an odds ratio of 1.8, which is why 54% is a ceiling rather than an estimate. Dependence-aware estimators — Chao's lower bound nationally, and a three-list log-linear model on ten states — put coverage between 33% and 44%. The estimand is cities, not buildings.

Intervals, since a point estimate is not what the assumptions support: Chapman 630 [575, 705]; Chao 899 [778, 1062]; three-list pairwise 417 [298, 742] within the ten-state frame. The last interval is enormous because the model has zero residual degrees of freedom — it is exactly identified, there is nothing left to test it with, and the width is honest rather than a defect.

### 4.7 Sensitivity: the observation windows do not match

OSHA's inspections run 1999-03-22 to 2026-09-02; NLRB's filings run 2009-06-24 to 2026-09-08. A closed-population assumption wants one window. Only **four** OSHA cities have no inspection inside the NLRB window (Coffeyville KS, Fernley NV, Reno NV, Huntington WV). Restricting OSHA to 2009+ gives 336 cities, Chapman 622, Chao 884, coverage 54.0% — unchanged to one decimal. The mismatch is real and it does not matter.

---

## 5. Were the third and fourth lists usable?

**OpenStreetMap: yes, within a declared ten-state frame. MWPVL: no.**

### 5.1 OpenStreetMap — usable, with a frame

`data/raw/osm_amazon/_candidates_all.csv` holds 202 Amazon facilities with a building code, a city and a state, in 110 cities across nine states. `osm_by_state.zip` holds the raw Overpass exports it came from: 272 features in ten states, 259 of them carrying an Amazon `operator` tag.

It is a genuine third list, and it is the useful kind. Its capture mechanism — a volunteer mapped the building — has nothing to do with worker grievance, which is what makes it able to break the OSHA-NLRB dependence rather than compound it.

Two things constrain it, both handled rather than ignored:

```
  1  It covers ten states and only ten. The query was run over
     AZ CA CO FL ID IL NY TN TX WA and nowhere else. Outside them the
     capture probability is structurally zero, so the three-list model is
     fitted INSIDE that frame and the national two-list estimate is left
     alone. Mixing them would silently assume OSM had a chance of seeing
     an Ohio delivery station.
  2  Coverage inside the frame is wildly uneven: AZ 30 features, TN 1,
     ID 4, FL 9 against CA 83 and TX 50. That is heterogeneous
     catchability of the exact kind Chao's estimator exists for, and the
     reason the independence model's 286 is not believable.
```

Tennessee is kept in the frame with zero captures, because it was queried and returned effectively nothing. Dropping it would be selecting the frame on the outcome.

The curated 202-row file is used rather than the raw 259 features, because 49 of the raw features have no `addr:city` tag at all and the curated file has cities for all 202. The raw features do yield 126 distinct city+state against the curated file's 110, so a more careful geocoding of the raw export would add cities and push the estimate up. That is an open improvement, and it moves the answer in the direction of *less* coverage, not more.

### 5.2 MWPVL's 2012 copy — not usable, and this is measurable

> **Scope, added 2026-09-14.** Everything in this section is about the **April
> 2012** file named below, and it stands. It does **not** extend to MWPVL's
> **2025 Q1** article, obtained 2026-09-14, which carries a twenty-eight-page
> delivery-station table and therefore does not have the structural zero that
> is the whole argument here. That file is assessed in
> [`MWPVL_2025.md`](MWPVL_2025.md) and the decision there is the opposite one:
> it enters the design as a fourth capture list. Two vintages of one source,
> thirteen years apart, reach opposite conclusions for a reason that is stated
> in the last paragraph of this section — read it before reusing the verdict.

`data/raw/mwpvl/Amazon.com Distribution Network Strategy.pdf` is MWPVL's network census frozen at **April 2012**: 32 North American fulfilment centres, plus seven sites then under construction. It is a PDF with no machine-readable table, which is an inconvenience. The reason it is unusable is not the format.

Recovering the US cities from the PDF text gives 20 distinct city+state. Of those, **19 are in the OSHA extract**. OSHA captures 95% of MWPVL's cities.

Compare that with the 33-54% it captures of the population as a whole and the problem is obvious. MWPVL's list is not a sample of Amazon's network; it is a list of the largest, oldest, most conspicuous fulfilment centres in the country, which are precisely the buildings OSHA is near-certain to have inspected. Running Lincoln-Petersen on (MWPVL, OSHA) would return `20 * 340 / 19 = 358` cities and announce that OSHA sees 95% of everything. That number would be a heterogeneity artefact and nothing else.

Stated structurally: **this vintage of** MWPVL has a **capture probability of zero** for every facility that did not exist in April 2012, and for every delivery station ever, because delivery stations did not exist as a facility class in 2012. Delivery stations are this project's target. A list with structural zeros over most of the population cannot estimate that population's size; it can only estimate the size of the sub-population it covers, which we already know. It is excluded, and the exclusion is a finding rather than a shortcut.

The qualifier matters more than it looks. The exclusion rests entirely on a **date**, not on anything about who MWPVL are or how they work — a 2012 list cannot see facilities built after 2012, and that is the end of it. So the argument is fragile to exactly one fact changing, and in 2026 it did: the same publisher's 2025 Q1 article covers the delivery-station network directly. Nothing above was wrong; it was scoped to a file and the scope was left implicit in the section title, which is how a correct finding turns into a wrong rule. See [`MWPVL_2025.md`](MWPVL_2025.md).

It remains valuable for the thing it is actually good at, which `FACILITY_PANEL_PROVENANCE.md` already uses it for: validating that our OSHA "operating by" bounds really do hold, with measured lags of 4 to 345 months.

---

## 6. The 96-city worklist

```
  outputs/metrics/nlrb_only_cities.json
```

96 cities with a confirmed Amazon NLRB case and no Amazon building anywhere in the OSHA extract. Labour activity proves a worksite existed; our primary source never saw it. This is the most directly actionable panel-expansion target the project has, and each entry carries the earliest filing date, the case count, the case-type split and the size proxy, so the highest-value targets can be worked first.

```
  by state:  CA 15   NY 13   TX  9   AZ  6   IL  5   NJ  5   OH  5
             PA  5   MI  4   CO  3   GA  3   MD  3   ... 96 total
```

Three caveats travel with the file and are written into it:

```
  1  City+state only. Geocoding each one to a building is manual work.
  2  A case may name a corporate office rather than a warehouse. 100 of
     the 970 rows sit in the city of their own NLRB regional office
     (Seattle 25, Chicago 20, San Francisco 10, Atlanta 8, Detroit 8).
     Most of those cities do hold real Amazon facilities, so this is a
     rate to check rather than a set to delete - but it cannot be
     resolved without opening the case detail pages.
  3  operating_by is an upper bound on the opening, never an opening.
```

---

## 7. The three limitations, in full

### 7.1 The DSP problem — and the source contains its own proof

Delivery-station drivers are employed by Delivery Service Partners, separate legal companies. A charge arising at a delivery station may name the DSP and never mention Amazon, which makes it invisible to a search on "Amazon". **Delivery stations are this project's target**, so the source is blindest exactly where it hurts most.

The export contains the demonstration. One case names Amazon jointly with twenty-five DSPs, individually: Activ Enterprises, Accuswift Logistics, Andiamo Logistics, Atom Logistics, ASB Global, A-Team Delivers, Blue Cardinal Logistics, BTK Rush, Clear Logistics, C&T Logistics, DirectPro Logistics, DnA Logistics, EY Parker Logistics, EZ Logistix, Fast Track Delivery, HK Logistics, Kavac Logistics, Metro Deliveries & Logistics, Molock's Logistics, Next Stop Logistics, Paolino Logistics, Pure Deliver, Quick Trip Delivery, Satriano Logistics and Valuable Logistics. Every one of those is a company whose other charges would not surface in an Amazon search.

This has a direct consequence for the ingest. An early version matched `^amazon` at the start of the employer name and silently dropped nine cases — all of them joint-employer or DSP filings, including `MOLOCK Logistics and Amazon, as joint employers` and `Elite Line Services at Amazon CLT2`. The matcher now looks for `amazon` as a whole word anywhere in the name, and there is a test naming all seven of the real strings it must keep.

**This is also the strongest argument for re-pulling the source properly.** HOWTO.md section 4 prescribes the mitigation: search the DSP names too, and match on address rather than employer name. That needs Route B, the election spreadsheets, which carry street addresses. We do not have them; the file we hold is Route A. Twenty-five DSP names are now known and are a ready-made search list.

### 7.2 Selection on density — the confounder, not a nuisance

Covered in section 3. The short form: union activity tracks size, urbanness and state labour law; density is the variable the cost argument turns on; NLRB presence is therefore selective on the confounder and must not be treated as a random draw. The practical consequence for this document is that the 96 NLRB-only cities are a *biased* sample of what OSHA missed — biased towards the large and the urban — so the buildings they contain are probably easier to find than the buildings nobody has found at all.

### 7.3 No opening dates

Same as OSHA. `operating_by` bounds from above and never says "opened in 2019". This is not a defect to be fixed but a property to be modelled — Train (2009) §7.5 treats a known, observation-specific upper bound as single-bounded contingent valuation with a standard likelihood, not as a data problem.

---

## 8. Other defects found while doing this

**The size proxy is contaminated.** `Employees on charge/petition` is the only facility-size measure this project has from any source, and it cannot be used as it stands. 65 of 968 values exceed 100,000 and **53 are exactly 1,000,000** — those are national-scope charges against the Teamsters, where the filer recorded Amazon's entire workforce against a single city. Worse, the modal value is 1,000, appearing 86 times, which is also the file's median: a perfectly plausible fulfilment-centre headcount that is almost certainly a default. That is a textbook **erroneous inlier** in Van den Broeck et al.'s (2005) sense — "data points generated by error but falling within the expected range" — and no range check will ever find it.

Treated as that paper prescribes: a **soft cutoff** at 20,000 that flags for diagnosis, no hard cutoff, and no editing. The value is carried through untruncated (the largest US fulfilment centres genuinely run to five figures) and each place records `n_employees_over_cutoff` beside `n_with_employees`, so nobody can average the field without seeing the problem.

**A residual city duplicate the normaliser does not catch.** `MARCH AIR RESERVE BASE, CA` and `MARCH ARB, CA` are one place under two names, and both appear in the 96-city worklist. Fixing it would mean merging on abbreviation expansion inside the string, which is the class of rule that also merges real distinct cities. It is left as two, reported here, and it makes the NLRB list one city too long — which biases the estimated population *up* and our coverage *down*, the conservative direction.

**The city key is unstable in large metros, and this is the most serious methodological weakness here.** New York is the worst case. NLRB records BRONX, BROOKLYN, QUEENS, NEW YORK, LONG ISLAND CITY, MASPETH, WOODSIDE and MELVILLE; OSHA records BETHPAGE, FLUSHING, NEW WINDSOR, ROCK TAVERN, STATEN ISLAND and CASTLETON ON HUDSON. MASPETH, WOODSIDE, LONG ISLAND CITY, FLUSHING and QUEENS are all the same borough under different postal place names. Every such pair is a false non-match, and false non-matches inflate the estimated population. Fixing it needs a USPS place-name crosswalk, which we do not have. The direction of the resulting error is at least known: **it makes our measured coverage too low**, so the ceiling of 54% is genuinely a ceiling.

---

## 9. What this does NOT license

It is worth being explicit, because a coverage number is the kind of figure that escapes its caveats.

- It does not say the facility panel is 54% complete. The panel is 43 pilot stations and 104 national rows, built from OSHA *and* OpenStreetMap *and* hand research. This measures OSHA alone, against a city frame.
- It does not say anything about buildings. See 4.1.
- It does not give a national three-list estimate. The three-list model is fitted on ten states because that is where the third list exists. Extrapolating it nationally would assume the other forty states behave like these ten, and these ten were chosen as the pilot metros precisely because they are not typical.
- It does not identify *which* facilities are missing, only how many cities. The 96-city worklist is the closest thing to a list of misses, and it is itself a biased sample of them.

---

## 10. Reproduce

```
  .venv/bin/python -m pytest tests/unit/test_nlrb.py -q

  PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.nlrb
      -> data/interim/nlrb_amazon.csv          208 rows, one per city

  PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.nlrb_capture
      -> outputs/metrics/nlrb_coverage.json
      -> outputs/metrics/nlrb_only_cities.json  96 rows
```

`nlrb_capture` reads `data/interim/osha_amazon.csv`, so run `ingest.osha` first if it is stale. Every figure in section 4 is in `nlrb_coverage.json`, including the naive city key, so the correction in 4.2 is auditable rather than a claim about somebody else's arithmetic. Two tests in `test_nlrb.py` assert the published counts and the sign of the measured dependence directly against the real files, and they skip rather than fail if the downloads are absent.

---

## 11. Figure ledger

Every number in this document and where it came from. "Verified" means re-derived from the artefact on 2026-09-13.

```
  figure                                value    source                          status
  ---------------------------------------------------------------------------------------
  NLRB rows in the export                 970    nlrb_cases_amazon.csv           verified
  rejected as a namesake                    1    ingest.nlrb log                 verified
  Amazon cases used                       969    ingest.nlrb log                 verified
  distinct city+state, naive key          209    nlrb_coverage.json              verified
  distinct city+state, normalised         208    ingest.nlrb log                 verified
  distinct employer spellings             290    nlrb_cases_amazon.csv           verified
  case types                        C 958 R 12   nlrb_cases_amazon.csv           verified
  filing window          2009-06-24..2026-09-08  nlrb_cases_amazon.csv           verified
  employees populated                 968/970    nlrb_cases_amazon.csv           verified
  employees median                      1,000    nlrb_cases_amazon.csv           verified
  employees above 100,000                  65    nlrb_cases_amazon.csv           verified
  employees exactly 1,000,000              53    nlrb_cases_amazon.csv           verified
  employees exactly 1,000                  86    nlrb_cases_amazon.csv           verified
  Staten Island cases                     195    nlrb_cases_amazon.csv           verified
  cities with exactly one case            114    nlrb_cases_amazon.csv           verified
  cases in their own region office city   100    nlrb_cases_amazon.csv           verified
  OSHA buildings                          474    data/interim/osha_amazon.csv    verified
  OSHA cities                             340    same                            verified
  OSHA buildings per city                1.394   474/340                         verified
  OSHA window            1999-03-22..2026-09-02  same                            verified
  overlap, naive key                      108    nlrb_coverage.json              verified
  overlap, normalised key                 112    nlrb_coverage.json              verified
  NLRB-only, naive key                    101    nlrb_coverage.json              verified
  NLRB-only, normalised key                96    nlrb_only_cities.json           verified
  Lincoln-Petersen, naive key             658    nlrb_coverage.json              verified
  Lincoln-Petersen, normalised            631    nlrb_coverage.json              verified
  Chapman                                 630    nlrb_coverage.json              verified
  Chapman 95% CI                   [575, 705]    nlrb_coverage.json              verified
  Chao lower bound                        899    nlrb_coverage.json              verified
  Chao 95% CI                     [778, 1062]    nlrb_coverage.json              verified
  coverage ceiling, Chapman             54.0%    340/629.7                       verified
  coverage ceiling, Chao                37.8%    340/899.1                       verified
  OSM curated facilities                  202    _candidates_all.csv             verified
  OSM raw Amazon features                 259    osm_by_state.zip                verified
  OSM states queried                       10    FACILITY_PANEL_HOWTO.md         verified
  OSM cities (curated)                    110    _candidates_all.csv             verified
  frame union                             228    nlrb_coverage.json              verified
  OR NLRB x OSHA | OSM                   1.84    nlrb_coverage.json              verified
  OR NLRB x OSM  | OSHA                  1.72    nlrb_coverage.json              verified
  OR OSHA x OSM  | NLRB                  3.82    nlrb_coverage.json              verified
  three-list independence                 286    nlrb_coverage.json              verified
  three-list lowest AIC ([23][1])         314    nlrb_coverage.json              verified
  three-list all pairwise                 417    nlrb_coverage.json              verified
  frame two-list Chapman                  296    nlrb_coverage.json              verified
  frame two-list Chao                     410    nlrb_coverage.json              verified
  MWPVL snapshot                   April 2012    MWPVL PDF, para 2               verified
  MWPVL US fulfilment centres              32    MWPVL PDF                       verified
  MWPVL US cities recovered                20    pdftotext -layout               verified
  MWPVL cities also in OSHA                19    set intersection                verified
  window-matched Chapman                  622    sensitivity run                 verified
  OSHA cities outside the NLRB window       4    sensitivity run                 verified
```

**Figures reported to us that the artefacts do not support:**

```
  claim                          reality
  ---------------------------------------------------------------------
  "209 NLRB city+state"          209 as typed, 208 once three spelling
                                   variants of one place are collapsed
  "108 in both"                  112 on the corrected key
  "101 NLRB-only"                96 on the corrected key
  "naive Lincoln-Petersen 658"   correct for the naive key; 631 for the
                                   corrected one
  "implied OSHA coverage 51.7%"  54.0% on the corrected key, and it is a
                                   CEILING, not an implied rate
```

None of those is a large error and all five point the same way — the brief's numbers were the right calculation on a slightly wrong key. The estimate they support is unchanged in substance: our primary source sees roughly half the cities at best.

---

## 12. Pending registration

`ingest/external.py` is owned by another agent, so the `--check` gate does not yet validate this source. The patch to apply, verbatim, inside the `EXPECTED` tuple (after the `facility_panel` entry, so that a missing NLRB file is reported next to the other manually placed sources):

```python
    Expectation("nlrb", ("nlrb_cases_amazon.csv", "nlrb_cases*.csv"),
                "NLRB Amazon case search export: the second list, and the "
                "only measurement of how incomplete the first one is",
                500_000),
```

Three notes for whoever applies it.

The patterns deliberately do not match `nlrb_elections_TRUNCATED_unfiltered.csv`. Under a bare `*.csv` glob the "largest match wins" rule in `_find` would be a coin toss between an 877 KB good file and an 816 KB useless one — the same failure the `facility_panel` comment already documents for `national_facilities.csv`.

`min_bytes` is 500,000 against a real size of 877 KB. That catches a one-page export (the case search paginates, and a single page is a few tens of kilobytes) without failing on a legitimately smaller refresh.

It is not marked `critical`. Nothing in the modelling path reads it; it feeds a measurement about the modelling path. If it goes missing the coverage estimate goes stale, which is a warning, not a broken build.
