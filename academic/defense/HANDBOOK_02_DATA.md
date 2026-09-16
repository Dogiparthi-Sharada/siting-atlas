# Handbook Part 2 — The Data

**Every source: what it is, what it contains, how to get it, what it costs, and
what will go wrong. Then the single most important design decision in the whole
project — what we are predicting.**

---

## 2.0 Read this before the rest of Part 2

```
  +--------------------------------------------------------------------+
  |  THE PROJECT'S SITING MODEL IS A CONDITIONAL ZCTA CHOICE MODEL.    |
  |  IT IS FITTED. ITS HEADLINE IS THAT THE DATA IN THIS CHAPTER DOES  |
  |  NOT SUPPORT IT.                                                   |
  |                                                                    |
  |  Fitted, converged, national frame, 3 free parameters, 94          |
  |  decisions, 56 train / 38 held out, seed 20260914. McFadden        |
  |  rho-squared 0.19691 in sample.                                    |
  |  Artefact outputs/metrics/choice_report.json.                      |
  |                                                                    |
  |  ON THE 38 HELD-OUT DECISIONS A SINGLE RAW CENSUS COUNT -          |
  |  warehousing establishments, NAICS 493, straight out of County     |
  |  Business Patterns with NOTHING FITTED FROM IT - MATCHES the       |
  |  fitted model:                                                     |
  |                                                                    |
  |                          top-1   top-5   top-10    Brier           |
  |     fitted model          7/38   16/38    19/38   0.008724         |
  |     warehousing count     8/38   16/38    20/38   0.008951         |
  |     households alone      1/38    5/38    10/38   0.009271         |
  |     uniform within metro  1/38    3/38     7/38   0.009316         |
  |                                                                    |
  |  AND THE INTERVALS AGREE WITH THE RANKING NULL. Inference          |
  |  landed 2026-09-14: sandwich AND bootstrap, as                     |
  |  docs/MODEL_SPEC.md Sec. 6.3 prescribes. The null that matters is  |
  |  beta = 1, NOT beta = 0 - households is the numeraire, so          |
  |  beta = 1 means "worth exactly one household".                     |
  |    warehousing_establishments, beta = 1.4428                       |
  |      sandwich 95%             [0.734, 2.835]  p = 0.287            |
  |      bootstrap over decisions [0.760, 4.762]                       |
  |      bootstrap over metros    [0.702, 10.013]                      |
  |      BCa                      [0.714, 3.522]                       |
  |    ALL FOUR COVER 1.0.                                             |
  |                                                                    |
  |  RETIRED / SUPERSEDED - the discrete-time hazard model on          |
  |  ZCTA-quarters. AUC 0.6894 vs a 0.5000 null, calibration 170x      |
  |  worse than a constant, negative Brier skill on both hold-outs.    |
  |  Kept in this pack as teaching, not as a result.                   |
  |                                                                    |
  |  WHY THAT BELONGS IN A DATA CHAPTER. The predictor that holds its  |
  |  own against the whole fitted model is a raw count from one free   |
  |  federal file. Everything the project spent its time collecting -  |
  |  the facility panel, the hand labelling (Sec. 2.2.10), the         |
  |  satellite dating (Sec. 2.2.11) - bought no measurable ground on   |
  |  that comparison. This chapter is the evidence for why.            |
  +--------------------------------------------------------------------+
```

> **Corrected 2026-09-14.** The banner said the raw CBP count **BEATS** the
> fitted model, and further down this chapter (Sec. 2.4.4) an instruction told
> you to say "beats", not "matches". Both are now inverted, because the word
> was wrong, not merely superseded. It was read off the one seeded 56/38
> split tabulated above. Across fifty paired re-splits of the same 94
> decisions the raw count is ahead by **0.36 hits out of 38, paired sd
> 1.14**, and it loses 11 of those 50
> (`outputs/metrics/gbm_benchmark.json`). One third of a decision is a tie,
> and the old wording mistook sampling noise for a result. The table above is
> still correct for its seed, and the uncomfortable conclusion is unchanged:
> three estimated parameters buy **no** ranking improvement over a free count
> of warehouses, so the data this chapter documents still did not earn its
> keep.

---

## 2.1 The rule that shapes everything

> **Every source must be free, public, and re-downloadable by a stranger.**

This is not frugality. It is the contribution. A model built on licensed data
produces conclusions nobody can check, which is precisely the situation we are
trying to fix. The moment one source requires a $50k licence, the project stops
being reproducible and becomes just another proprietary model with a worse
budget.

**Practical consequence:** when a better-but-paid source exists, we take the
worse-but-public one and *report the cost of that choice*.

---

## 2.2 Source-by-source

### 2.2.1 Census ACS (American Community Survey), 5-year estimates

**What it is.** The US Census Bureau's rolling survey of population
characteristics. The "5-year" version pools sixty months of responses, which is
what makes it reliable at small geographies like ZCTAs.

**What we take.** Median household income, age distribution, household size,
population, population density, educational attainment, vehicle availability,
housing tenure.

**Access.** Public API (`api.census.gov`), free key, generous limits.

**Size.** ~10 MB as parquet for our variable selection across all ZCTAs.

**Gotchas — and they matter:**

- **The 18–24 month lag.** The "2023" 5-year release describes 2019–2023.
  A neighbourhood that gentrified in 2024 looks like its 2021 self.
- **Margins of error are large at ZCTA level.** ACS publishes an MOE for every
  estimate and people ignore it. For a small ZCTA, a median income of "$64,000"
  might be ±$9,000. **We carry the MOE through as a source of uncertainty**
  rather than treating estimates as exact.

> **Example of why the MOE matters.** Two ZCTAs report median incomes of
> $71,000 and $68,000. Ranked naively, one is "richer." But if both MOEs are
> ±$8,000, the ranking is noise. Any model that treats these as precise inputs
> will produce spuriously confident rankings.

---

### 2.2.2 TIGER/Line shapefiles

**What it is.** The Census Bureau's official geographic boundary files —
the actual polygons.

**What we take.** ZCTA boundaries, plus state and county for joins.

**Access.** Bulk FTP download, free.

**Size.** ~600 MB raw nationally; ~100 MB after simplification.

**Gotchas:**

- **Detail you don't need.** TIGER polygons trace coastlines and rivers at
  survey precision. At metro zoom, that detail is invisible and expensive. We
  simplify to roughly 10 m tolerance at ingest.
- **Vintage changes.** ZCTA boundaries changed materially between 2010 and 2020.
  Mixing vintages silently corrupts a time series. **We pin 2020 and document
  the crosswalk.**

> **Example of a vintage bug.** A ZCTA that split into two between vintages will
> show a sudden 50% "population drop" that is purely an artefact of
> redistricting. A model reading that as a demand collapse would learn nonsense.

---

### 2.2.3 Zillow ZORI and ZHVI

**What it is.** Zillow Observed Rent Index and Zillow Home Value Index —
smoothed, seasonally adjusted measures of typical rent and home value.

**Why we want it.** Two roles at once: a proxy for household disposable income
(complementing ACS with something more current), and a proxy for **commercial
land cost**, which drives the largest capital bucket.

**Access.** Public research downloads, free CSV, monthly since ~2015.

**Size.** ~100 MB.

**Gotchas:**

- **Residential ≠ commercial.** Warehouse land is priced differently from homes.
  Correlated, not identical. We use it as a *proxy* and say so.
- **Coverage holes.** Thin markets have missing months. We forward-fill within a
  documented limit and flag ZCTAs where interpolation exceeded it.

**And the open defect, which is much worse than "coverage holes" implies.**
`rent_index` is missing on a scale that makes the phrase misleading, and it is
still **listwise deleted** at `src/siting_atlas/cost/runner.py:166`.

**Name your denominator, because there are three of them and they disagree.**
All three measured from `data/processed/panel.parquet` on 2026-09-14:

```
   94.3%   of ZCTAs are missing rent_index in AT LEAST ONE quarter
           31,864 of 33,791. This is the figure DATA_QUALITY.md reports.
   88.8%   of ZCTA-QUARTER ROWS are null
   80.5%   of ZCTAs have NO value in ANY quarter
           27,199 of 33,791
```

A bare "94.3% missing" invites a reader to recompute, land on 88.8%, and
conclude the number was invented. Attach the denominator every time.

**Why listwise deletion is a bias and not a loss of precision.** Deletion is
only harmless when data are missing completely at random, and here they are
emphatically not. Taking the 94.3% split — ZCTAs with a complete series versus
ZCTAs missing at least one quarter — the **median household density is
1,555.6 per square mile in the complete stratum against 24.5 in the incomplete
one, a ratio of 63.6x** (reproduced 2026-09-14; the 63.6 figure pairs with the
94.3% denominator specifically, and a different split gives a different ratio).
Zillow covers thick urban markets and skips thin rural ones, so dropping the
missing rows drops the sparse part of the country and keeps the dense part.

Density is the single variable Daganzo's law is most sensitive to (Part 1
Sec. 1.5). So the priced cost table is not a sample of the country; it is a
sample of the part of the country where delivery is cheapest, and every
cost-to-serve figure in the pack is conditioned on that without saying so.

---

### 2.2.4 Census County Business Patterns (CBP) — retail density

**What it is.** An annual administrative count of business establishments by
geography and industry code (NAICS).

**Why an administrative source beats a business directory.** Worth understanding fully,
because it is a good example of the kind of engineering judgement a reviewer
respects.

| | Yelp Fusion | Census CBP |
|---|---|---|
| Rate limit | 5,000 requests/day | None — bulk file |
| Acquisition time | **~3 days of continuous polling** | ~10 minutes |
| API key | Required | Not required |
| Coverage | Self-selected: businesses that chose to list | Administrative: every establishment with payroll |
| Known bias | Under-represents minority-owned, cash-heavy, informal businesses | Structural gaps only (sole proprietors without payroll) |

**The three-day figure.** 5,000 requests × 50 businesses = 250,000 per day. To
cover our metros adequately needs ~750,000 records → **3.0 days**. Three days
is survivable. *Discovering it in week four is not.*

**The bias point is the stronger argument.** A directory's own limitations are
usually disclosed by anyone using it, with CBP proposed as the *audit* on that
bias. If CBP is good enough to audit a directory, the obvious question is
whether it is good enough to replace it. It is.

> **Why this matters for the equity story.** If Yelp coverage is thinner in
> lower-income areas, then "retail density" is systematically understated there,
> the model reads those areas as commercially dead, and it ranks them low
> — for reasons that are an artefact of data collection, not reality. That
> is a fairness bug hiding inside a feature.

#### 2.2.4.1 The CBP lag guard is nominal, and it undercuts the headline

This is the most serious open defect in the chapter, and it sits directly under
the one predictor that works. State it before an examiner does.

**The problem.** The winning covariate is the CBP count of **warehousing
establishments** (NAICS 493) in a ZCTA. An Amazon delivery station *is* a
warehousing establishment. So a contemporaneous CBP count contains its own
outcome: the model would be told "a warehouse opened here" and asked to predict
whether a warehouse opened here.

**The guard.** `ingest/cbp_detail.py` scores each facility on the latest CBP
vintage **strictly earlier** than that facility's recorded `open_year`. In
principle that removes the leak with a year to spare.

**Why the guard is nominal.** `open_year` is not an opening date. On **all 100
loaded national rows**, `open_year` and `open_quarter` equal the quarter of the
**earliest OSHA inspection** — the "operating by" upper bound of Sec. 2.2.7,
restated under a different column name. A building first inspected in 2022 may
have opened in 2017, in which case the "strictly earlier" 2021 vintage already
counts the facility itself.

The five pilot addresses with an independently known opening month (Sec.
2.2.7.1) give lags from opening to first inspection of **4, 13, 57, 69 and 345
months**. Three of those five exceed twelve months. So the guard's true margin
is **zero or negative, not one year**.

> **Say it plainly.** The single predictor that matches the whole fitted model
> is the one most exposed to outcome leakage, and the control that was supposed
> to prevent that leakage is keyed on a date that is not an opening date. Both
> halves of the headline — "a raw count does the model's job for free" and "the
> raw count may be contaminated" — have to be said in the same breath. Quoting
> only the first oversells; quoting only the second hides a real finding.

**What would fix it.** Not a bigger lag. A genuine opening date, or an interval
with a credible lower bound. Sec. 2.2.11 describes the attempt to manufacture
that lower bound from satellite imagery, and why it failed.

---

### 2.2.5 BLS Occupational Employment Statistics (OES)

**What it is.** Bureau of Labor Statistics wage data by occupation and metro.

**What we take.** Median wages for delivery drivers (light truck), warehouse
workers (labourers and material movers), and first-line supervisors.

**Why.** Wages are the second-largest capital bucket and vary enormously by
metro. A national average erases the single biggest cross-metro cost difference.

**Access.** Bulk download, free. **Size.** < 20 MB.

---

### 2.2.6 EIA regional energy prices

**What it is.** Energy Information Administration data on fuel and industrial
electricity prices by region.

**Why.** Van fuel and warehouse electricity — a secondary but genuinely
metro-varying bucket.

**Access.** Bulk download / API, free. **Size.** < 10 MB.

---

### 2.2.7 The facility panel — now the target variable

**What it is.** A record of every relevant logistics facility: location, type,
square footage, **and opening date**.

**Sources.** Public facility inventories maintained by supply-chain analysts,
company press releases, local news, permit filings, and the operator's own
delivery-speed checker queried by ZIP.

**Size.** Kilobytes. The plan said "perhaps 4,000 rows across operators." What
was delivered is **two files, neither of which is close to that**:

```
   data/external/facility_panel/facilities.csv            43 rows   pilot
   data/external/facility_panel/national_facilities.csv  104 rows   national
```

Both are Amazon only. The pilot file is all delivery stations across the ten
pilot metros, 4.6 KB on disk. The national file is what the current choice
model is built from, and it shrinks twice on the way in:

```
   national_facilities.csv                    104 rows
     - the loader's cross-source edit drops 4 as impossible
                                              100 rows loaded
     - the choice builder drops 6 that opened in 2017 or earlier
       and therefore have no clean CBP vintage to score against
                                               94 DECISIONS
```

94 is the number in `outputs/metrics/choice_report.json`: 56 train, 38 held
out. That gap between 4,000 and 104 is the most important fact in this section,
and §2.2.7.1 below explains it.

> ## Updated 2026-09-15 — there is now a THIRD file, and it is seven times bigger. Everything above is still true of the two files it describes.
>
> `data/external/facility_panel/national_facilities_expanded.csv` —
> **693 rows, 687 buildings, 230 CBSAs, 50 states**
> (`outputs/metrics/national_panel_expanded.json`). The hand-verified
> `national_facilities.csv` was **not touched**; the expansion is a new file
> beside it, which is why both are live at once.
>
> **Where the 589 new rows came from.** Thirteen table images in an industry
> consultancy's 2025 network PDF were OCR'd into **1,904 facilities**, of
> which **1,420** carry an opening date
> (`outputs/metrics/mwpvl_extraction.json`). Filtering to the US
> small-package delivery-station class drops **1,269** rows of other classes
> — fulfilment centres, sortation centres, cross docks, Fresh and Whole Foods
> DCs, air gateways and rest-of-world buildings — on purpose, because this
> panel's unit is a delivery station. The remaining 635 were screened against
> the 104-row panel with `common/linkage.py`, the same Jaro-Winkler /
> Fellegi-Sunter machinery the declared edits use, so "the same building"
> means the same thing here as it does inside `warehouse/edits`:
>
> ```
>   MWPVL rows in the OCR file                      1,904
>     excluded as the wrong facility class          1,269
>   delivery-station rows                             635
>     internal duplicates dropped                       1
>     already in national_facilities.csv               40
>     held for clerical review                          5
>     ADDED                                           589
>   panel rows before / after                   104 / 693
> ```
>
> **Three independent validations, and none is a clean bill.**
>
> 1. **OSHA cross-check** (`mwpvl_validation.json`). 208 of the 1,420 dated
>    rows link to an OSHA building. 11 claim an opening *after* the date an
>    inspection proves the site was already operating, so the declared edit
>    `E_operating_by` passes on **94.7%**. By date precision: month 160/9,
>    year 25/2, quarter 23/0. **Blind spot: 1,212 dated rows cannot be
>    checked this way at all.**
> 2. **Date plausibility.** Two delivery-station rows predate the network and
>    **five are beyond plausible** — years 2045, 2075, 2090 and 2094 twice.
>    The worst, `GEFG1`, claims 2090Q2 against an OSHA record proving
>    operation by 2020-09-22, which is **279 quarters** after the bound.
>    Those rows are **excluded, not corrected**, and the CSV preserves
>    `claimed_open` so the exclusion is reversible from the artefact alone.
> 3. **OCR state cross-check** (`mwpvl_merge.json`, `ocr_state_grade`). The
>    state name the OCR read, against the state implied by the postcode →
>    county → state FIPS crosswalk — two independent readings of the same
>    row. **604 of 606 comparable rows agree: 99.67%.** This one costs
>    nothing and it is the strongest of the three. Blind spot: 22 state
>    strings did not parse at all.
>
> **Four blind spots that are not validations**, and they belong beside the
> counts rather than in a footnote:
>
> - **54 rows have no comparable street address**, so `compare()` calls every
>   pair a non-match and they enter the panel **as new by default rather than
>   by evidence**. That is the size of the screen's blind spot.
> - **One known duplicate survived** on a damaged street string.
> - **The source PDF is not in the repository.** 589 of the 693 rows trace to
>   an 11 MB file outside the tree; the archived file with a similar name is
>   a different document. This is the top CRITICAL finding of
>   `docs/AUDIT_2026_09_14.md` §1.1, and it is a **reproducibility** defect,
>   not a data-quality one.
> - **`date_flag` is populated on 2 rows of the 693** against at least 15
>   known-bad dates.
>
> **The geocoding defect below is unchanged and is now larger in absolute
> terms: 0 of 693 rows carry a coordinate**, exactly as with the two older
> files. `resolve_coordinates` falls back to the ZCTA centroid, so every
> distance covariate in the project is known only to that precision.
>
> **Which file does which artefact read?** This is the easiest thing to get
> wrong in the whole project and it should be said out loud before any number
> is quoted:
>
> ```
>   national_facilities.csv  (104 / 100 loaded / 94 decisions)
>     choice_report.json, gbm_benchmark.json, leakage_test.json,
>     the published figures, the proposal
>
>   national_facilities_expanded.csv  (693 / 687 / 483 decisions)
>     refit_expanded.json, panel_experiments.json, hazard_revival.json,
>     metro_entry.json, covariate_search.json
> ```
>
> The audit's own headline is that the production model, the panel, the
> warehouse, the figures and the proposal are **all still on the 104-row
> frame**, and the expanded frame exists only in experiment artefacts.

> **And the defect that a reviewer will find in thirty seconds.** **Zero of the
> 104 national rows and zero of the 43 pilot rows are geocoded.** `latitude`
> and `longitude` are null on every row of both files — verified on
> 2026-09-14 by reading the two CSVs. Coordinates fall back to ZCTA centroids,
> so **every distance quantity in the project inherits a centroid
> approximation**: the 15-mile catchment, the 20 km cannibalisation radius,
> Gate 5's spillover ring, the line-haul stem distances. None of those is
> measured from a building. Do not say "we geocoded the facilities". We did
> not.

> **This tiny table is the most important data in the project.** It is not a
> covariate — it *is the thing we predict.* Its quality is therefore a
> first-order concern, not a footnote.

**The quality problem, stated honestly:**

- Opening dates are often approximate ("opened in 2024")
- Facility type classifications differ between sources
- Small delivery stations are under-reported relative to large FCs
- Announcements sometimes describe facilities that were never built

All four turned out to be true, and a fifth turned out to matter more than
any of them: **for most rows there is no opening date at all, only a date by
which the building demonstrably existed.**

#### 2.2.7.1 What was actually delivered

**The pilot file, which the RETIRED hazard model was fitted on:**

```
  file          data/external/facility_panel/facilities.csv
  validator     facility_panel ok  43 facilities, 2015-2025, 1 operator(s)
  rows          43 buildings, all Amazon, all facility_type DS
  geocoded      0    latitude and longitude are null on every row
  usable        38   buildings the RETIRED hazard model used as decisions
                      (source: outputs/metrics/hazard_report.json,
                       field "n_usable_facilities")
  independent   28   independent metro-period episodes -- the lower bound
  closures      1    Chicago 2801 S. Western Ave (DCH1), closed 2021
  metros        Seattle 11 | Chicago 8 | Bay Area 7 | New York 6
                Denver 6 | Miami 2 | Austin 1 | Nashville 0
                Phoenix 1, Boise 1  (both held out)
```

**The national file, which the CURRENT choice model is fitted on:**

```
  file          data/external/facility_panel/national_facilities.csv
  rows          104 buildings, all Amazon
  geocoded      0    latitude and longitude are null on every row
  loaded        100  four dropped by the loader's cross-source edit as
                     impossible
  decisions     94   six more dropped by the choice builder: they opened in
                     2017 or earlier, so no clean CBP vintage exists to
                     score them against
  split         56 train / 38 held out, seed 20260914
```

**Read 38 and 28 as a bracket, not as two competing numbers.** An earlier
draft of this handbook put a single figure of 39 in that block. The artefact
says 38, and the retired model's own power check divides by it: 38 usable
facilities over 5 parameters gives the 7.6 events-per-parameter figure quoted
in Part 4. So 38 is the number to use for that model -- but it is the **upper**
bound on how many independent decisions the pilot panel contains, because it
assumes every building was a separate decision. The **lower** bound is 28,
which merges openings that happened in the same metro in the same quarter on
the grounds that they were plausibly one planning decision executed twice. The
truth is somewhere between 28 and 38. Quote the bracket; a defence that quotes
only the flattering end invites the question of why.

> **The same bracketing question applies to the 94, and nobody has answered
> it.** The choice model treats each of the 94 as an independent decision. No
> merge of same-metro same-quarter openings has been computed on the national
> frame, so there is no published lower bound for it. If asked, say that: the
> figure does not exist rather than equals 94.

> **Why the bracket exists at all, in one sentence.** If Amazon signed one
> lease decision in Denver in 2022 and it produced two buildings, counting
> those as two independent observations double-counts the evidence, and the
> honest response to not knowing which happened is to report both counts
> rather than to pick one.

Two further properties of that table are load-bearing and neither should be
smoothed over in a defence.

**The dates are "operating by" upper bounds.** Most come from the date the
US Department of Labor opened an OSHA inspection case at the address. That
proves the building was operating by then. It says nothing about when it
opened. The date is therefore the right-hand endpoint of a censoring interval
`(panel start, X]`, and the specification the data calls for is **interval
censoring**.

That specification is **not implemented**. `docs/STATUS.md` marks interval
censoring NOT STARTED, and `models/risk_set.py` consumes the bound as though
it were the event time. So the delivered model is fitted on dates it treats as
exact when they are not, and every timing-dependent result inherits that.
Say this before an examiner finds it; it is written down in the project's own
status file.

**The coverage is uneven, and the unevenness is an artefact of the source.**
Seattle contributes 11 of the 43 because Washington runs an unusually active
state-plan OSHA programme, not because Amazon builds more there. Nashville
is a *fitting* metro with **zero** events, because all five of its OSHA
addresses are fulfilment centres rather than delivery stations. A model that
reports a Seattle effect may be reporting an inspection effect.

**What we do — and what changed.** The original plan was to hand-verify a
random sample of 100 facilities and publish the measured error rate. On a
43-row panel that is not a sample, it is more rows than exist, so the plan
had to change. It was replaced by two things that are achievable and, on a
table this small, strictly stronger:

1. **A census instead of a sample.** Every one of the 43 rows carries its
   source, and the hand-researched subset carries a URL and a quotable
   sentence in `data/collection/results/DATES_FOUND.csv`. There is no
   sampling error because there is no sampling.
2. **A measured bound, instead of an assumed error rate.** Five addresses
   appear both in MWPVL's 2012 network census, which states real opening
   months, and in the OSHA extract. That gives five cases where the true
   opening and our bound are both known:

```
   BFI1 Sumner WA        opened Jun 2011   first inspected Oct 2011     4 mo
   PHX4 Goodyear AZ      opened Jun 2008   first inspected Jul 2009    13 mo
   PHX6 Phoenix AZ       opened Oct 2010   first inspected Jul 2015    57 mo
   PHX7 Phoenix AZ       opened Sep 2011   first inspected Jun 2017    69 mo
   PHL1 New Castle DE    opened Nov 1997   first inspected Aug 2026   345 mo
```

The bound **held in 5 cases out of 5** — no inspection ever predates an
opening, which is what a valid upper bound requires — and it is **extremely
loose**, median lag 57 months, with one site opened in 1997 and first
inspected in 2026. Quote that measurement rather than saying "there is some
date uncertainty".

> **Example of why this matters more than it sounds.** If the bound is a
> year late, the out-of-time backtest is partly scoring against noise: the
> model is being marked against a date that is not the date the thing
> happened. An earlier draft illustrated this with a hypothetical -- "a
> genuine AUC of 0.88 might measure as 0.81" -- which is no longer needed,
> because the model has been fitted and the real numbers are in. **The
> measured out-of-time AUC is 0.5551, with a Brier skill of -0.02091**,
> meaning the model scored worse on a held-out future than predicting the
> base rate for every ZIP would have. That is the actual bill for a loose
> date, combined with everything else that went wrong. See
> `HANDBOOK_04_MODELS.md` Sec. 4.1 and Sec. 4.9 for the full result and the
> diagnosis.
>
> The five-case check is what lets us say how late the bound can be instead
> of guessing. It also says plainly what the panel cannot do: with intervals
> that can be years wide, the honest claim is about *which* ZIPs were served,
> not *when*. Interval censoring is the specification this target actually
> calls for, and `docs/STATUS.md` marks it **NOT STARTED** -- the current
> risk-set builder treats an upper bound as if it were an event time.

The full provenance — including the collection methods that failed before
this one worked, the quantified selection bias, and the defects still in the
delivered file — is in
[`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md).
Cross-reference it rather than restating it; it is the single source of
truth for this table.

---

### 2.2.8 EPA EJScreen

**What it is.** The EPA's environmental justice screening tool — combines
environmental burden indicators (particulate matter, diesel PM, traffic
proximity, hazardous waste) with demographic indicators.

**Why.** It powers the equity overlay, which is the deliverable that converts
this from an operator tool into a public-interest one.

**Access.** Bulk download, free. **Size.** 1–2 GB. **Grain.** Census block group
— finer than ZCTA, so it aggregates up cleanly.

---

### 2.2.9 OpenStreetMap — used once, then discarded

**What it is.** The crowd-sourced global map, including the road network.

**Why.** Drive times from a candidate facility to each ZCTA.

**Access.** Free extracts (Geofabrik by region, BBBike by custom bounding box).

**Size.** This is the one that hurts, and it is covered in detail in Part 7:
metro bbox ~150–500 MB, full US ~12 GB, and processed routing artifacts 2–5 GB
*per metro*.

**The design decision:** we use it **once, offline**, to produce a drive-time
matrix, then delete every intermediate file. The deployed system reads a 10 MB
lookup table and has no routing dependency at all.

---

### 2.2.10 The hand-labelling programme — finished, and mostly wasted

This section was absent from earlier versions of the defence pack. Its absence
was the problem: four evenings of manual work produced a result that is 80%
duplicate, and a defence pack that does not mention it is hiding a process
failure rather than reporting one. Failure first, then the recoverable part.

**What was done.** 362 OSHA sites were hand-labelled across six batches, each
row given a facility type with a supporting quote and a source URL. Files:
`data/collection/results/UNLABELLED_BATCH_1..6_CLASSIFIED.csv`.

```
   labelled          362 sites, 6 batches
   delivery stations 135 of the 362
   GENUINELY NEW      13 of the 135 were new to the delivered facility frames
   ALREADY KNOWN     289 of the 362 (80%) were ALREADY CLASSIFIED in
                     data/collection/results/NATIONAL_CLASSIFIED.csv
```

**The cause, and it is a process bug not a data bug.**
`scripts/make_unlabelled_batches.py` selected rows that the OSHA establishment
-name regex in `ingest/osha.py` could not classify, and shipped them to the
worklist. It never checked those rows against `NATIONAL_CLASSIFIED.csv`, which
already held classifications for most of them from a different route. **It
compared against the wrong reference.** The worklist was therefore "rows the
regex could not read", not "rows nobody has classified", and those are very
different sets.

> **The lesson, which generalises past this project.** A de-duplication step is
> only as good as the reference it de-duplicates against. Before you send
> anybody — a human, a contractor, a paid API — a worklist, write down
> which table you are claiming the worklist is *not* already in, and then
> actually join against it. The join is five lines. Four evenings is what it
> cost not to write them.

**The recoverable part, and it is genuinely real.** Of the 135 delivery
stations, 13 were new; the other **122 are independent confirmations of
classifications the pipeline had already made**, each from a different source,
each carrying a quote and a URL. That is exactly the shape of a **validation
set for the name-based classifier in `ingest/osha.py`** — an independently
sourced label for a row the classifier had already labelled by other means.

Say both halves, in this order. It was **produced by accident rather than by
design**: nobody set out to build a validation set, and presenting it as
planned work would be a lie a reviewer can check by reading
`make_unlabelled_batches.py`. But an accidental validation set is still a
validation set, and the project did not have one before.

> **What has NOT been done with it.** No accuracy figure for `ingest/osha.py`
> has been computed against those 122 rows. The set exists; the measurement
> does not. Do not quote a classifier accuracy — there isn't one.

---

### 2.2.11 Satellite dating — attempted, and it failed

Also absent from earlier versions of the pack, and also disclosed here. This is
a **negative result**. Report it as one.

**The idea, and it was a good one.** OSHA gives an **upper** bound on an opening
date (Sec. 2.2.7). If Sentinel-2 imagery could give a **lower** bound — the
date the building first appears on the ground — then upper plus lower is an
**interval**, and interval censoring is the specification this target has needed
all along (Sec. 2.2.7, `docs/STATUS.md`).

**What was run.** `data/collection/satellite/colab_date_from_satellite.py`, in
Google Colab, on 2026-09-14. A changepoint detector over the Sentinel-2 scene
history at each site's coordinates. Output:
`satellite_dates.csv`, 107 rows by 16 columns. **That file sits OUTSIDE this
repository**, one directory up in the wider MSBA project folder; cite it with
that caveat or a reader will look for it in `data/` and not find it.

**Coverage was not the problem.**

```
   sites attempted                        107
   sites that produced an estimate        107   (100%)
   median cloud-free Sentinel-2 scenes    106
```

**Accuracy was poor.** Against the 83 sites with a known year: only **41%
within one year**, with an error standard deviation of **3.42 years**.

**And then the test that kills it outright.** The estimate is supposed to be a
*lower* bound — construction cannot post-date operation. So check it against
the OSHA date, which is a hard fact: an inspector physically stood in the
building on that day.

```
   LOGICALLY IMPOSSIBLE ESTIMATES
   -------------------------------------------------------------
   39 of 107 sites  (36%)  date CONSTRUCTION to AFTER the day an
                           OSHA inspector found the building
                           already operating.
   median overshoot         33 months
```

A lower bound that lands 33 months above a known upper bound is not a noisy
lower bound. It is not a bound.

**The confidence score does not save it.** Filtering on the script's own
confidence changes nothing: **35% impossible at confidence above 2, versus 30%
at confidence 1–2.** The score does not discriminate, so there is no
high-confidence subset to keep.

**The cause is the changepoint detector, not the imagery.** 106 median
cloud-free scenes is ample; the detector is finding the wrong change in a
series that has plenty of signal in it.

> **Do NOT present the 68 surviving estimates as dates.** They are the subset
> that happened not to fail the impossibility check, which is a different thing
> from the subset that is right. With 36% of the output demonstrably impossible
> and a 3.42-year error standard deviation, selecting the survivors is
> selecting on the outcome. If anybody asks whether the interval-censoring
> specification can now be implemented, the answer is no, and this is why.

**What it costs the project to admit.** The count of date-collection methods
attempted is now **six**, of which **five failed**. The one that worked gives
upper bounds only. That is the honest state of the target variable.

---

## 2.3 The sources at a glance

Fourteen are registered in `ingest/registry.py`, thirteen of them analytical.
The nine below are the ones that carry the argument. The other five are the
plumbing and the second-order features: the Gazetteer (`gaz_zcta`, centroid
and land area), two crosswalks (`cbsa_county`, `zcta_county_xwalk`), ACS
1-year at metro grain, and county building permits (`bps_county`).

| Source | Grain | Role | Size | Risk |
|---|---|---|---|---|
| Census ACS | ZCTA | Demographics | 10 MB | Lag, large MOEs |
| TIGER/Line | ZCTA polygon | Geometry | 100 MB | Vintage changes |
| Zillow | ZIP | Income + land cost proxy | 100 MB | Residential ≠ commercial |
| Census CBP | ZIP × NAICS | Retail density | 50 MB | Annual only |
| BLS OES | Metro | Wages | 20 MB | Occupation mapping |
| EIA | Region | Energy prices | 10 MB | Coarse grain |
| Facility panel | Facility | **Target variable** | 43 pilot rows + 104 national rows | **Dates are upper bounds; 0 rows geocoded** |
| EPA EJScreen | Block group | Equity overlay | 1–2 GB | Aggregation choices |
| OpenStreetMap | Road network | Drive times (offline) | 12 GB | **Preprocessing cost** |

**Total analytical footprint after processing: about 14 MB** — the built
ZCTA-quarter panel is 1,081,312 rows by **50 columns** (measured from
`data/processed/panel.parquet` on 2026-09-14; any "44 columns" in an older
draft is stale) and compresses to that.
Everything else is scaffolding that gets thrown away. The estimate in an
earlier draft was ~260 MB; columnar compression over slowly-moving quarterly
demographics beat it by a factor of eighteen, which is worth knowing before
anyone sizes infrastructure for a job like this.

---

## 2.4 The target variable — the most important section in the handbook

Everything above is input. This is output, and getting it wrong invalidates
everything.

### 2.4.1 The tempting alternative

One might want to predict **order volume per ZIP per month**. Nobody outside the
company can observe that. So an earlier draft constructed it:

```
   orders_i  =  TotalDisclosedOrders  x  ------------------------------
                                          0.6·income_i + 0.4·retail_i
                                          ---------------------------
                                          Σ (0.6·income + 0.4·retail)
```

A model using **income** and **retail density** would then predict that number.

### 2.4.2 Why that is circular, in full

The target was **manufactured out of the predictors**. The model is not learning
about the world; it is reverse-engineering our own arithmetic.

> **The clearest analogy.** I define a "talent score" as
> `0.6 × height + 0.4 × shoe size`. I then train a model to predict talent score
> from height and shoe size. It achieves 3% error.
>
> Have I discovered anything about talent? **No.** I have rediscovered my own
> formula. The 3% is not skill — it is the residual from a slightly
> different functional form.

**The genuinely dangerous part:** the metric would have looked *excellent*. A
MAPE of 3–5% reads like triumph in a results table. The better the number, the
more completely the model had learned the allocation rule rather than the
phenomenon.

**A reviewer spots this in under a minute** — and would spot it *after*
eight weeks of building. Which is why the estimand is settled in week zero.

### 2.4.3 The estimand we use

> **For each ZCTA and quarter: did the operator offer same-day service, and in
> which quarter did they first do so?**

**Why this works:**

| Property | Constructed volume | Observed enablement |
|---|---|---|
| Comes from | Our own formula | The world |
| Verifiable | No | Yes — check the delivery checker |
| Can be scored | No | Yes |
| Enables backtest | No | **Yes** |
| Metric | MAPE (undefined at zero) | AUC, Brier, calibration |
| Honest framing | Required a hedge | Literally accurate |

> **And the correction that this handbook owes the reader.** Everything in
> that table is still true: the estimand is observable, scoreable and not
> manufactured from the predictors, which is a genuine improvement on what it
> replaced. What it is *not* is a valid unit of analysis. A delivery station
> switches on every ZCTA within a 15-mile catchment **at once** -- median 58
> ZCTAs, mean 88, largest 307 on the delivered panel. So "Amazon chose ZIP
> 60608 in 2021Q2" is not a decision; it is one of about 88 simultaneous
> consequences of one decision about one building.
>
> **The assumption that breaks is independence across observations**, Train
> (2009) Sec. 3.7.1, printed page 61: *"Assuming that each decision maker's
> choice is independent of that of other decision makers, the probability of
> each person in the sample choosing the alternative that he was observed
> actually to choose is L(beta) = prod_n prod_i (P_ni)^{y_ni}."* The likelihood
> is a product over observations because the observations are independent.
> Eighty-eight rows from one building are not. The standard name for the
> failure is **clustering**, or **pseudo-replication**.
>
> That is why the hazard model failed, and it is diagnosed in full in
> `HANDBOOK_04_MODELS.md` Sec. 4.1 and `docs/METHODS_RESEARCH.md` Sec. 5.1.

> **A citation corrected.** This box used to cite Train (2009) Sec. 2.2 — the
> requirement that alternatives be mutually exclusive from the decision maker's
> perspective. That is the wrong section, and citing it would lose you the
> point in a viva. Sec. 2.2 is about the choice set facing a decision maker; a
> panel of area-quarters has no decision maker choosing among those rows, so
> exclusivity is not a property they can have or lack. Train calls that
> criterion "not restrictive" and writes that "Appropriate definition of
> alternatives can nearly always assure that the alternatives are mutually
> exclusive" (p. 12) — he offers it as a two-line repair, not a fatal
> objection. Corrected 2026-09-14. Train Sec. 2.2 remains the right authority
> for building the *successor's* choice set, where there really is a decision
> maker.

> **A claim withdrawn.** This box used to end "No successor specification has
> been chosen." That is now false. The successor is a conditional ZCTA choice
> model, one decision per building conditional on metro and period, and it is
> fitted on 94 decisions — see Sec. 2.0 and
> `outputs/metrics/choice_report.json`. Fixing the circularity in Sec. 2.4.2
> was necessary and not sufficient; fixing the unit of analysis was also
> necessary and also not sufficient. The correctly specified model is still
> only matched on held-out data by a single raw CBP count (Sec. 2.0's
> correction block).

### 2.4.4 What this unlocks — the backtest

```
   TIME ------------------------------------------------------->

   |<-------- TRAIN: facilities open through 2023 -------->|
                                                            |
                                     |<-- PREDICT: 2024-25 -->|
                                                            |
                                     score against what
                                     the operator ACTUALLY did
```

**This is the difference between a model and a forecast.** A model fits data. A
forecast makes a claim about the future and then finds out. Almost every student
project does the former; the latter is what makes an interviewer lean forward.

**Targets we pre-registered, and what we actually measured against each.**
This is the table to have in front of you in a viva, because it is the one an
examiner will build if you do not. **Every figure in it belongs to the RETIRED
hazard model**; the current choice model's own scorecard follows it.

```
   target             pre-registered   measured    source
   -------------------------------------------------------------------------
   AUC                  >= 0.80         0.6894     hazard_report.json
   ECE                   < 0.05        0.00863     hazard_report.json
   precision@100        >= 0.60      NOT COMPUTED  no such field exists
   -------------------------------------------------------------------------
   verdict              AUC: MISSED, and not narrowly
                        ECE: "PASSED" -- see below, this is the trap
                        precision@100: unanswered, not passed or failed
```

**AUC.** We pre-registered 0.80 and measured 0.6894. Say "missed", not
"approached". And note which split that is: 0.6894 is the **primary
unit-clustered** hold-out, the most favourable of the four splits that were
run. The out-of-time split that this section is actually about -- train on the
past, predict the future -- measured **0.5551**, a coin flip. If you quote one
number in the context of a backtest, quote that one.

**precision@100.** Never computed. `outputs/metrics/hazard_report.json`
reports AUC, Brier, ECE, a ten-bin calibration table and conformal coverage,
and nothing else. A pre-registered threshold with no measurement against it is
an open item, and calling it anything else is dishonest.

**ECE, and the lesson worth spelling out.** We cleared the threshold: 0.00863
is comfortably under 0.05. And it means nothing, because a **constant
predictor** -- a model that hands every ZCTA-quarter the base rate 0.02006 and
never varies -- scores an ECE of **0.00005** on the same data. We are roughly
**170 times worse calibrated than a model with no inputs at all**, and we
"passed".

> **The generalisable lesson.** When events are rare, calibration and squared
> error live on a tiny numeric scale, so any round-number threshold on that
> scale is cleared by doing nothing. We set < 0.05 without first asking what
> the null model would score. Had we asked, we would have known the target was
> unfalsifiable before a line of model code was written. **Pre-register
> against the null, not against a round number** -- a threshold that a
> no-information model passes is not a test, it is decoration.

Part 4 Sec. 4.5 works this through with the full calibration table.

**And the same discipline applied to the current model, which is why the
benchmark row matters more than the fit statistic.** Having learned the lesson
above, the choice model was scored against three no-information or
one-covariate benchmarks on the same 38 held-out decisions and 3,998
alternatives, rather than against a round number:

```
   held out, 38 decisions          top-1   top-5   top-10    Brier
   ---------------------------------------------------------------
   fitted choice model (3 params)   7/38   16/38    19/38   0.008724
   warehousing_establishments       8/38   16/38    20/38   0.008951
   households alone                 1/38    5/38    10/38   0.009271
   uniform within metro             1/38    3/38     7/38   0.009316
   ---------------------------------------------------------------
   source  outputs/metrics/choice_report.json
```

On this seed the fitted model is one hit **behind** at top-1 and at top-10 and
**level** at top-5 against a raw CBP count with nothing estimated from it, and
ahead on Brier by 0.000227. Say "matches", not "beats", when describing the raw
count: over fifty re-splits the gap is 0.36 hits of 38 and the raw count loses
11 of the 50, so none of those single-split leads is a win either way (Sec.
2.0's correction block). What the comparison establishes is unchanged: the
estimation buys nothing measurable. In-sample
McFadden rho-squared of 0.19691 looks respectable and is not evidence against
any of this, because the benchmark comparison is out of sample and the
rho-squared is not.

**The third leg, and it is the one that redeems the pre-registration lesson
above.** `docs/adr/0004-model-change-conditional-choice.md`, in its Residual
risk section, predicted *before* the model was fitted that the most likely
outcome was "wide bootstrap intervals covering zero on every coefficient", and
named the bootstrap as *the* diagnostic. The diagnostic was run on 2026-09-14
and the prediction held — against the correct null of **beta = 1**, not zero,
because households is the numeraire and only ratios are identified. Every one
of the four intervals on the single working parameter covers 1.0, at p = 0.287
on the sandwich. That is a **fourth negative result**, not a rescue, and it is
exactly what you would expect of a covariate that adds nothing over a raw count
out of sample.

> **Quote the precondition with the intervals, because the artefact does.**
> Train (2009) Sec. 8.6, p. 202, justifies the bootstrap on the grounds that a
> *large enough* sample resembles the population. At 56 decisions that
> precondition is precisely what is in doubt. These intervals measure how much
> the estimate moves with **which of our 56 decisions are included** — a real
> and useful quantity, and not sampling variability over the population of
> siting decisions. Note also that the metro-clustered bootstrap is much wider
> than the decision bootstrap (upper 10.01 against 4.76), because six or seven
> facilities share the Los Angeles choice set. When the two disagree, quote the
> metro-clustered one; it is the conservative one.
>
> **Status.** The inference module landed on 2026-09-14
> (`models/choice_inference.py`, `choice_sandwich.py`, `choice_bootstrap.py`,
> plus `tests/unit/test_choice_inference.py`) and was committed as `b29071e`.
> It sat untracked on disk for several hours first, during which it had already
> changed the published `choice_report.json`. Re-read that artefact before
> relying on any figure above.

> **Read that against Sec. 2.2.4.1 before you celebrate the benchmark.** The
> covariate that carries the comparison is the one most exposed to outcome
> leakage, and the lag guard meant to prevent that leakage is keyed on an
> inspection date rather than an opening date. The clean statement is: *a raw
> count matches the fitted model, and we cannot currently rule out that the raw
> count is partly counting the answer.*

**And here is what the delivered panel does to that picture, which you
should say before an examiner says it for you.** The design above is sound
and the data is thin. Of the 43 buildings, **two** fall in the 2024–25
prediction window (Richmond CA and Newark NJ, both 2025; zero in 2024),
against 1,177 ZCTAs first enabled in 2018–23. The backtest runs, and its
statistical power is close to nil — a pre-registered AUC threshold evaluated
on two openings is a coin flip with a decimal point.

Two honest responses, and we take both. Quote the **event count next to
every metric**, always, so nobody reads 0.8 as though it came from a
thousand events. And treat the backtest as a demonstration that the
*machinery* is real — the split is by time, the score is against what the
operator actually did, nothing leaks — rather than as evidence about
Amazon. Note also that a 2024–25 opening is the hardest cohort for this
source: the date is an OSHA inspection bound, and a building opened in 2025
may simply not have been inspected yet, so it is missing rather than
negative. That is the same censoring problem in its most acute form.

### 2.4.5 The volume model's remaining role

It survives as a **secondary analysis, honestly relabelled**:

> *"Objective 1(b) evaluates whether ZINB recovers a known data-generating
> process under realistic covariate structure. It is a specification-recovery
> exercise, not a demand forecast."*

And every downstream dollar figure carries the label *"conditional on the volume
allocation assumption."* That is not a weakness — it is the difference
between a number a reviewer can accept and one they must reject.

---

## 2.5 Proxies — the honest defence

A reviewer will ask: *can a model built on proxies produce decision-relevant
output?*

**The precedent argument.** Economics has used observable substitutes for latent
constructs for seventy years. GDP proxies economic activity. Unemployment claims
proxy labour conditions. Housing starts proxy investor sentiment. Entire
industries — property valuation models, alternative-data products — are
built on proxy foundations.

**The validation argument, which is stronger.** Precedent is an appeal to
authority. What actually defends a proxy is an *external check*:

- Aggregate our ZCTA-level capital estimates to metro level
- Compare against the operator's **publicly disclosed capital expenditure**
- Target: within 25%

This is one degree of freedom, checked against a number we did not construct. It
is not a substitute for internal data, but it is the strongest external
validation available in the public domain — and crucially, **it can fail.**
A check that cannot fail is not a check.

---

## 2.6 What will actually go wrong

Ordered by probability × damage.

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| Facility open dates are wrong | **Materialised** | **High** | Superseded: a census of the panel, plus the measured five-case bound in Sec. 2.2.7.1. The satellite attempt to add a lower bound **failed** (Sec. 2.2.11) |
| **CBP lag guard is nominal; the headline predictor may contain its own outcome** | **Materialised** | **High** | **None yet.** Needs real opening dates, not a bigger lag (Sec. 2.2.4.1) |
| **No facility is geocoded** | **Materialised** | **High** | **None yet.** 0 of 104 national and 0 of 43 pilot rows have coordinates; everything distance-based uses ZCTA centroids (Sec. 2.2.7) |
| **`rent_index` missing for most ZCTAs and listwise deleted** | **Materialised** | **High** (biased, not noisy) | **None yet.** `cost/runner.py:166` still drops the rows; observed stratum 63.6x denser (Sec. 2.2.3) |
| **A worklist sent to humans without de-duplicating against the right table** | **Materialised** | Medium | Cost four evenings; 80% duplicate. Left a 122-row accidental validation set (Sec. 2.2.10) |
| OSRM preprocessing defeats a laptop | **High** | High | Per-metro, delete as you go; circuity fallback |
| Rate-limited source discovered late | Medium | Medium | Already fixed — CBP replaces Yelp |
| ZCTA vintage mixing | Medium | **High** (silent) | Pin 2020; contract-test the ZCTA count |
| ACS MOEs ignored | Medium | Medium | Carry MOE into the uncertainty model |
| Nobody owns the pipeline | Medium | High | Stage ownership assigned in §7 |

> **The silent one is the dangerous one.** Vintage mixing does not throw an
> error. It produces a plausible-looking time series with fabricated
> discontinuities. This is why data contracts fail the build on unexpected row
> counts rather than warning.

---

## 2.7 Part 2 self-check

1. Why must every source be free and public — what is the *argument*, not
   the budget?
2. Explain the circularity in an earlier draft's target to someone non-technical, with an
   analogy.
3. Why would a *good* MAPE have been evidence of the bug?
4. Give two independent reasons CBP beats Yelp.
5. Why is the tiny facility table now the most important data in the project?
6. What is an ACS margin of error and why does ignoring it produce false
   confidence?
7. What external check can *falsify* our cost model?
8. Which data risk is silent, and why is silence the problem?
9. The pilot panel holds 43 buildings. Why is the number the retired hazard
   model could use 38, why is the lower bound 28, and where does each figure
   come from? Then do the same for the national file: 104 rows becomes how many
   decisions, and what is dropped at each of the two steps?
10. We pre-registered ECE < 0.05 and measured 0.00863. Why is clearing that
    threshold not evidence of anything, and what should the threshold have
    been set against?
11. The estimand in Sec. 2.4.3 fixed the circularity problem. Name the problem
    it did not fix, say how many ZCTAs one delivery station switches on at
    once, and name the Train section and the failure mode.
12. The single best predictor is a raw CBP warehousing count. Explain, without
    hedging, why that is simultaneously the project's most interesting finding
    and its most exposed one. (Hint: Sec. 2.2.4.1.)
13. How many facilities in the two panel files are geocoded, and name three
    downstream quantities that inherit the answer.
14. The hand-labelling programme produced 362 labels. How many were already
    classified, what caused that, and what is the one genuinely useful thing
    that came out of it?
15. Satellite dating: what was it trying to produce, what single test killed
    it, and why is it wrong to keep the 68 estimates that survived that test?
16. `rent_index` is missing for most ZCTAs and the rows are dropped. Why is
    that a *bias* rather than a loss of precision, and in which direction?

---

**Next:** `HANDBOOK_03_CAUSAL.md` — selection bias, counterfactuals, synthetic
control, and why "correlation is not causation" is an understatement here.
