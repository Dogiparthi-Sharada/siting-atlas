# Notes — white space: where is there unserved demand, and does asking predict anything

*Built and run 2026-09-14. Artefact: `outputs/metrics/white_space.json`.
Code: `src/siting_atlas/analysis/white_space.py` and its three helpers. Every
number below is read out of that artefact. None is recalled.*

**The one-line result, and it is two results.** At the externally-sourced
45-mile radius, with every facility we know about on the map, **91.0% of US
households are already inside an Amazon service area** and **9,606 ZCTAs
holding 11.6M households are outside all of them** — a real, named,
inspectable gap. (Using only the Census-verified coordinates it is 87.1%
and 11,676 ZCTAs / 16.6M households; §3.1 says why both arms are reported and
§5.2 says why the difference matters more than either figure.) And the
framing **fails its own
back-test**: white space beat a no-coverage household ranking in **14 of 108**
scored cells, **0** of them significantly, against **32** cells where the
household baseline won significantly. **At the headline 45-mile radius,
68.7–75.9% of the 2024–25 delivery station openings landed inside coverage the
pre-2024 network already had** — 75.9% (60 of 79) on real coordinates and
68.7% (90 of 131) once ZCTA-centroid fallbacks are admitted — at a median of
7.5–10.1 miles from the nearest existing building. **That range is across the
two coordinate sets at one radius, not across radii**: quoting it as "67–77%"
mixes the two axes and inflates it. 67.1% is the *real*-coordinate figure at
**15** miles, a different radius; the full grid runs 45.0% (fallback, 8.3 mi)
to 75.9% (real, 45 mi).

§7.7 then isolates *why*. Five ranking rules on the same openings show it is
not the operationalisation and not a measurement artefact: it is **the
coverage conditioning itself**. Removing the coverage mask and changing
nothing else recovers the entire gap (6.3% → 46.8% at `real`/45mi/N=100). One
rule — weighting by demand-per-existing-facility rather than excluding served
places — does beat the baseline at 15 miles, but across 128 post-hoc tests on
one hold-out the favourable significances (9) are close to chance (6.4) while
the unfavourable ones (62) run at ten times it. Nothing tested rescues the
framing.

So: the map is a description worth publishing. The prediction it implies is
false, and the reason is identified rather than guessed. §9 argues the
capstone should say all three.

---

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes seven parts and one file per paper. This
is not a paper. It is an analysis of this project's own data whose only
external source is a commercial trade document, and the structure is adapted
the same way `NOTES_CATCHMENT_RADIUS.md` adapted it. Part 7, "what I did NOT
do", survives as §10 and is again the section to read if you only read one.

---

## 1. Why this question is different from every other one in the project

Everything in `models/` answers **"where did Amazon build?"** That question
has a measured ceiling. Five panel compositions crossed with three algorithms
(`NOTES_PANEL_EXPERIMENTS.md`, `NOTES_GBM_BENCHMARK.md`) all land between 2.5x
and 3.1x lift over chance — a spread narrower than one method's re-sampling
noise. The ceiling is not the algorithm; it is that there are 483 decisions
and they are the whole signal.

This asks the inverse: **"where is there unserved demand?"** Draw a service
area around every facility Amazon already operates; the populated places
falling outside all of them are the white space.

Three properties made it worth building:

1. **It needs no target variable.** Nothing is fitted, so nothing can overfit,
   and the 483 decisions do not cap it.
2. **It is falsifiable going forward.** If Amazon opens where this flags, that
   is a prediction that came true. If it opens inside existing coverage, the
   framing is wrong. §7 runs exactly that test retrospectively.
3. **It is the output a county planner can use**, which is the project's
   stated purpose. A ranked list of ZIP codes with nobody serving them is
   actionable in a way that a hazard coefficient is not.

Property 3 survives this analysis. Property 2 is what kills it.

---

## 2. What "covered" means here, and the three ways it is wrong

A ZCTA is **covered** when its centroid is within the radius, in
**straight-line great-circle miles**, of at least one Amazon facility. Not
drive time, not a road-network buffer, not a polygon intersection. Said
plainly because the temptation to imply drive time is strong and the data
does not support it: there is no routing matrix in this project.

This is the same geometry `warehouse/facilities.py` already uses to build the
`enabled` target, so coverage here and `enabled` there mean the same thing at
the same radius. Three known distortions, each with its direction named:

| Distortion | Direction |
|---|---|
| A straight line ignores rivers, mountains and the absence of a road, so real service areas are smaller than the disc | **under**-states white space |
| A ZCTA is reduced to its centroid, so a 900-square-mile rural ZCTA is covered or not as one unit | either; large at 8.3 mi, small at 45 mi |
| Every facility class gets the SAME radius, when a fulfilment centre serves hundreds of miles (Houde, Newberry & Seim 2023 use 150 for sortation) | **over**-states white space near big nodes |

None is corrected. Correcting any one means choosing a second unmeasured
parameter, and the radius sweep in §4 already moves the answer by more than
any of the three would.

---

## 3. The network: three sources, two coordinate arms

`src/siting_atlas/analysis/white_space_network.py`.

**Source 1 — delivery stations.** `national_facilities_expanded.csv`, 693
rows, all typed `DS`, with coordinates from `geocoded_expanded.csv`.

**Source 2 — support sites.** The non-delivery-station **US** tables of
`data/interim/mwpvl_facilities.csv`: fulfilment, sortation, inbound
cross-dock, air gateway, fresh, heavy-and-bulky. 811 US rows, of which 785
place (17 postcodes are not ZCTAs, 9 are flagged cancelled or closed).
Rest-of-world rows (458, MWPVL tables `10_row` and `11_row`) are dropped by
name rather than left to fall out of the postcode join, because "it happened
not to match" is not a reason a reader can check.

A metro served by a million-square-foot fulfilment centre is not unserved, so
leaving source 2 out would manufacture white space. Measured at 45 miles, the
support network is worth:

| Arm | DS only | + support sites | added |
|---|---:|---:|---:|
| real | 81.64% of households | 87.10% | **+5.46 pp (7.0M households)** |
| real_plus_fallback | 87.38% | 91.00% | **+3.62 pp (4.7M households)** |

**Source 3 — the universe.** `data/processed/panel.parquet`, one row per
ZCTA: 33,791 areas, 128.70M households, 335.6M people. Puerto Rico is in it;
see §6.

### 3.1 The coordinate split is the most important methodological choice here

501 of the 693 delivery stations have a real street geocode from the Census
batch geocoder. 189 more have their ZCTA centroid behind an explicit
`fallback_method` flag. 3 have neither.

That 72.3% match rate is **not missing at random**. Hand-collected rows matched
83.7%; OCR'd MWPVL rows matched 70.3%. A geocoder fails on a bad address
string, and bad address strings cluster in the places the source documented
badly — which is not a random sample of places. The gap between the two
sources narrowed from 22.0 points to 13.4 when the OCR was repaired
(`GEOCODING.md` §9), and narrowing it is not closing it. So every figure is
reported twice and the two arms are never averaged:

| | `real` | `real_plus_fallback` |
|---|---:|---:|
| delivery stations placed | 501 | 690 |
| support sites placed (always centroids) | 785 | 785 |
| total facilities | 1,286 | 1,475 |

Note what `real` does **not** mean: source 2 has no real coordinates at all,
because MWPVL publishes an OCR'd street address and nothing in this repo has
geocoded it. The `real` arm is real on the delivery-station side and centroid
on the support side. That is stated rather than averaged away.

**§5.2 shows the two arms disagree about 20 of the top 30 places.** That is
the single most important sentence in this document.

---

## 4. The radius is an input, not a finding

`warehouse/facilities.py` uses 15 miles and its own docstring calls it an
"ENGINEERING ESTIMATE" with "no published source". MWPVL's prose states
delivery stations are *"designed to service a 45-mile radius"*
(`docs/data/MWPVL_2025.md` line 383), and individual rows in the same document
state "deliver 60 miles in all directions", "60-70 mile radius" and "Same Day
Service Within 45 Minute Drive". `outputs/metrics/catchment_band.json` puts
the defensible band at **8.3–45.0 miles** and measures a 3.57x swing in
enabled ZCTAs across it.

A single radius here would be an assumption wearing a finding's clothes. The
sweep reuses `catchment_band.RADII` by value, including its 60-mile over-run
probe, and **45 is the headline because it is the only radius with an
external source attached to it.**

### 4.1 White space at every radius

`real_plus_fallback`:

| Radius (mi) | ZCTAs uncovered | Households uncovered | Households covered | Median mi to nearest, uncovered |
|---:|---:|---:|---:|---:|
| 8.3 | 26,153 | 59.1M | 54.1% | 35 |
| 12.7 | 23,449 | 44.1M | 65.8% | 38 |
| 15.0 | 22,204 | 38.9M | 69.8% | 40 |
| 19.6 | 19,948 | 32.2M | 75.0% | 44 |
| 25.0 | 17,407 | 25.9M | 79.9% | 48 |
| **45.0** | **9,606** | **11.6M** | **91.0%** | **69** |
| 60.0 * | 6,270 | 7.0M | 94.6% | 83 |

`real`:

| Radius (mi) | ZCTAs uncovered | Households uncovered | Households covered | Median mi to nearest, uncovered |
|---:|---:|---:|---:|---:|
| 8.3 | 26,671 | 62.8M | 51.2% | 40 |
| 12.7 | 24,088 | 47.7M | 62.9% | 44 |
| 15.0 | 22,960 | 42.4M | 67.0% | 46 |
| 19.6 | 20,933 | 35.9M | 72.1% | 49 |
| 25.0 | 18,709 | 30.1M | 76.6% | 54 |
| **45.0** | **11,676** | **16.6M** | **87.1%** | **74** |
| 60.0 * | 8,184 | 11.0M | 91.4% | 87 |

\* outside the band — an over-run probe, not part of the range.

Across the band the uncovered-household count moves **5.1x** (59.1M to 11.6M)
and the uncovered-ZCTA count **2.7x**. Anyone quoting one of these figures
without the radius beside it is quoting an assumption.

At the project's current 15 miles, **30.3% of US households — 39.0M — are
outside every Amazon service area.** At 45 miles it is 9.0%, 11.6M. Both
sentences are true and they are the same data.

---

## 5. The named list at 45 miles

An aggregate count is not usable by anyone. These are the deliverable.

### 5.1 `real_plus_fallback` — every facility we know about, on the map

| # | ZCTA | State | County | Metro | Households | Miles to nearest facility |
|---|------|-------|--------|-------|-----------:|--------------------------:|
| 1 | 77845 | TX | Brazos County | College Station-Bryan, TX | 28,825 | 53 |
| 2 | 85364 | AZ | Yuma County | Yuma, AZ | 27,669 | 127 |
| 3 | 78521 | TX | Cameron County | Brownsville-Harlingen, TX | 27,475 | 61 |
| 4 | 59901 | MT | Flathead County | Kalispell, MT | 23,954 | 89 |
| 5 | 42101 | KY | Warren County | Bowling Green, KY | 23,663 | 54 |
| 6 | 55901 | MN | Olmsted County | Rochester, MN | 23,461 | 53 |
| 7 | 77840 | TX | Brazos County | College Station-Bryan, TX | 21,769 | 57 |
| 8 | 97702 | OR | Deschutes County | Bend, OR | 21,679 | 100 |
| 9 | 85365 | AZ | Yuma County | Yuma, AZ | 20,893 | 89 |
| 10 | 78045 | TX | Webb County | Laredo, TX | 20,713 | 117 |
| 11 | 87507 | NM | Santa Fe County | Santa Fe, NM | 20,268 | 50 |
| 12 | 78520 | TX | Cameron County | Brownsville-Harlingen, TX | 20,034 | 47 |
| 13 | 56001 | MN | Blue Earth County | Mankato, MN | 19,894 | 48 |
| 14 | 00603 | PR | Aguadilla Municipio | Aguadilla, PR | 19,537 | 55 |
| 15 | 28546 | NC | Onslow County | Jacksonville, NC | 19,492 | 71 |
| 16 | 28412 | NC | New Hanover County | Wilmington, NC | 19,449 | 47 |
| 17 | 28645 | NC | Caldwell County | Hickory-Lenoir-Morganton, NC | 19,093 | 48 |
| 18 | 53081 | WI | Sheboygan County | Sheboygan, WI | 19,091 | 46 |
| 19 | 04401 | ME | Penobscot County | Bangor, ME | 19,090 | 110 |
| 20 | 73505 | OK | Comanche County | Lawton, OK | 19,090 | 76 |
| 21 | 28540 | NC | Onslow County | Jacksonville, NC | 18,869 | 70 |
| 22 | 28403 | NC | New Hanover County | Wilmington, NC | 18,610 | 52 |
| 23 | 79705 | TX | Martin County | Midland, TX | 18,548 | 106 |
| 24 | 84790 | UT | Washington County | St. George, UT | 18,477 | 99 |
| 25 | 66502 | KS | Riley County | Manhattan, KS | 18,378 | 82 |
| 26 | 78046 | TX | Webb County | Laredo, TX | 18,350 | 109 |
| 27 | 93436 | CA | Santa Barbara County | Santa Maria-Santa Barbara, CA | 18,135 | 74 |
| 28 | 78852 | TX | Maverick County | Eagle Pass, TX | 17,992 | 95 |
| 29 | 97701 | OR | Deschutes County | Bend, OR | 17,947 | 108 |
| 30 | 96720 | HI | Hawaii County | Hilo-Kailua, HI | 17,912 | 207 |

### 5.2 `real` — Census geocodes only, and why it disagrees

| # | ZCTA | State | County | Metro | Households | Miles to nearest facility |
|---|------|-------|--------|-------|-----------:|--------------------------:|
| 1 | 00926 | PR | San Juan Municipio | San Juan-Bayamón-Caguas, PR | 37,761 | 1039 |
| 2 | 00725 | PR | Caguas Municipio | San Juan-Bayamón-Caguas, PR | 31,121 | 1045 |
| 3 | 77845 | TX | Brazos County | College Station-Bryan, TX | 28,825 | 53 |
| 4 | 85364 | AZ | Yuma County | Yuma, AZ | 27,669 | 127 |
| 5 | 78521 | TX | Cameron County | Brownsville-Harlingen, TX | 27,475 | 61 |
| 6 | 47906 | IN | Tippecanoe County | Lafayette-West Lafayette, IN | 26,288 | 47 |
| 7 | 00956 | PR | Bayamón Municipio | San Juan-Bayamón-Caguas, PR | 26,223 | 1034 |
| 8 | 00949 | PR | Toa Baja Municipio | San Juan-Bayamón-Caguas, PR | 26,103 | 1027 |
| 9 | 65203 | MO | Boone County | Columbia, MO | 25,588 | 96 |
| 10 | 27834 | NC | Pitt County | Greenville, NC | 24,419 | 55 |
| 11 | 59901 | MT | Flathead County | Kalispell, MT | 23,954 | 89 |
| 12 | 00976 | PR | Trujillo Alto Municipio | San Juan-Bayamón-Caguas, PR | 23,850 | 1043 |
| 13 | 42101 | KY | Warren County | Bowling Green, KY | 23,663 | 54 |
| 14 | 31907 | GA | Muscogee County | Columbus, GA-AL | 23,632 | 55 |
| 15 | 27858 | NC | Pitt County | Greenville, NC | 23,563 | 60 |
| 16 | 55901 | MN | Olmsted County | Rochester, MN | 23,461 | 55 |
| 17 | 00612 | PR | Arecibo Municipio | Arecibo, PR | 23,438 | 1001 |
| 18 | 83301 | ID | Twin Falls County | Twin Falls, ID | 23,325 | 107 |
| 19 | 00953 | PR | Toa Alta Municipio | San Juan-Bayamón-Caguas, PR | 23,070 | 1028 |
| 20 | 28655 | NC | Burke County | Hickory-Lenoir-Morganton, NC | 22,141 | 51 |
| 21 | 77840 | TX | Brazos County | College Station-Bryan, TX | 21,769 | 57 |
| 22 | 97702 | OR | Deschutes County | Bend, OR | 21,679 | 100 |
| 23 | 38305 | TN | Madison County | Jackson, TN | 21,347 | 69 |
| 24 | 00693 | PR | Vega Baja Municipio | San Juan-Bayamón-Caguas, PR | 20,982 | 1017 |
| 25 | 85365 | AZ | Yuma County | Yuma, AZ | 20,893 | 89 |
| 26 | 67401 | KS | Saline County | Salina, KS | 20,831 | 76 |
| 27 | 00987 | PR | Carolina Municipio | San Juan-Bayamón-Caguas, PR | 20,772 | 1046 |
| 28 | 78045 | TX | Webb County | Laredo, TX | 20,713 | 122 |
| 29 | 39503 | MS | Harrison County | Gulfport-Biloxi, MS | 20,595 | 46 |
| 30 | 00727 | PR | Caguas Municipio | San Juan-Bayamón-Caguas, PR | 20,559 | 1043 |

**Only 10 of these 30 ZCTAs appear in both lists.** Twenty places are on one
list and not the other, and the difference is entirely the 240 facilities the
Census geocoder could not place. Reproduce it:

```python
import json
r = json.load(open("outputs/metrics/white_space.json"))
pick = lambda cs: {p["zcta"] for c in r["coverage"]
                   if c["coord_set"] == cs and c["radius_miles"] == 45.0
                   for p in c["top_uncovered_zctas"]}
len(pick("real") & pick("real_plus_fallback"))   # -> 10
```

This is the MNAR warning made concrete, and it is worth more than the lists
themselves. A reader handed only the `real` list would conclude that Amazon's
largest coverage gap in the United States is San Juan, Puerto Rico, at
797,364 uncovered households. The truth is that Amazon opened a delivery
station in Dorado, PR in 2025 (`MWP-0518`), and the Census geocoder returned
`No_Match / no_match_street_not_in_tiger` for its address. One un-geocodable
row moved a metro from "completely unserved" to "served", and it is the
largest single line in the whole analysis.

---

## 6. Rolled up to metros, which is the unit a decision is taken in

Thirty adjacent ZIP codes in one metro read as thirty opportunities when they
are one. `real_plus_fallback`, 45 miles:

| # | Metro | Uncovered households | Share of metro uncovered |
|---|-------|---------------------:|-------------------------:|
| 1 | Huntington-Ashland, WV-KY-OH | 150,124 | 100% |
| 2 | Beaumont-Port Arthur, TX | 146,688 | 99% |
| 3 | Wilmington, NC | 121,083 | 64% |
| 4 | San Luis Obispo-Paso Robles, CA | 107,346 | 100% |
| 5 | College Station-Bryan, TX | 101,198 | 99% |
| 6 | Bend, OR | 99,549 | 100% |
| 7 | Lake Havasu City-Kingman, AZ | 96,628 | 100% |
| 8 | Burlington-South Burlington, VT | 92,624 | 100% |
| 9 | Aguadilla, PR | 90,162 | 100% |
| 10 | Santa Maria-Santa Barbara, CA | 89,147 | 60% |
| 11 | Charleston, WV | 88,613 | 100% |
| 12 | Fort Smith, AR-OK | 86,898 | 98% |
| 13 | Green Bay, WI | 86,277 | 64% |
| 14 | Lake Charles, LA | 82,726 | 90% |
| 15 | Brownsville-Harlingen, TX | 81,333 | 60% |

**Seven of these fifteen survive the switch to the `real` arm.** The eight
that do not — San Juan PR, Portland ME, Shreveport LA, Peoria IL, Columbus
GA-AL, Longview TX, Prescott Valley AZ and Ponce PR — are metros where every
known Amazon building failed to geocode. They are the geocoder's list, not
Amazon's.

### 6.1 Puerto Rico, Hawaii and Alaska

`white_space_cover.OFFSHORE_STATES` marks them. They are genuinely uncovered
and they are counted in every total, but a great-circle distance of 1,000
miles to San Juan is not a siting opportunity a road network can close, so
the subtotal is reported beside the total. At 45 miles,
`real_plus_fallback`: 11.13M of the 11.56M uncovered households are on the
mainland; 0.44M are offshore. In the `real` arm it is 16.14M mainland, 1.49M
offshore — the difference being, again, Dorado.

At 45 miles, four territories are **entirely uncovered** in both arms (AS,
GU, MP, VI), Puerto Rico joins them in the `real` arm, and five states are
**entirely covered** in both (CT, DC, DE, NJ, RI). At 15 miles in the `real`
arm, Maine is entirely uncovered too.

---

## 7. The back-test — the thing that makes this more than a map

`src/siting_atlas/analysis/white_space_backtest.py`.

A coverage map is unfalsifiable on its own: it describes the present, and any
description of the present is true. This is the test that turns it into a
claim.

### 7.1 Design

1. Build the service network from facilities that opened **2023 or earlier**.
2. Rank the places it leaves uncovered by households; take the top N.
3. Look at where Amazon actually opened a delivery station in **2024 and
   2025**.
4. Compare against **the same N places ranked by raw household count, with no
   coverage logic at all**.

The baseline is the whole point and it is not a straw man. Amazon builds
where people are, so a household ranking will hit. If white space cannot beat
it, then the coverage layer adds nothing and "where is there unserved
demand?" resolves back to "where are there people?" — which the project
already knows.

Both rules score the **same** openings, so the difference is tested on the
discordant pairs with a two-sided **exact McNemar** test. An unpaired
chi-square would treat 131 openings as 262 independent draws.

### 7.2 Leakage control

`network(..., opened_by=2023)` drops every facility opened after 2023 **and
every undated facility**. Strict on purpose: `NOTES_COVARIATE_LEAKAGE.md`
documents what happens when a date that is really an upper bound is treated
as the opening — the guard passes and the number is worthless. An undated
MWPVL row could be a 2025 building, so it cannot be in a 2023 network. The
cost is large and is reported: **504 facilities dropped in the `real` arm,
610 in `real_plus_fallback`**, leaving networks of 782 and 865 against the
1,286 and 1,475 that exist today.

The dates are MWPVL's stated opening months, 1,420 of them, validated at
**94.71%** against the OSHA first-inspection upper bound — 208 of them link to
an OSHA building and 11 are falsified (`mwpvl_validation.json`, `run_id
20260915-195247-dbb5`). The 93.6%-over-157-rows figure this line used to carry
is superseded. 5.3% of the linked dates are wrong in an unknown direction,
nothing here corrects for that, and the 1,212 dated rows that link to no OSHA
building are untested rather than passing.

Held out: **79 delivery-station openings** in the `real` arm, **131** in
`real_plus_fallback` (130 with a CBSA).

### 7.3 The result at 45 miles

ZCTA level, 33,791 in the universe:

| Arm | N | White space | Household baseline | Chance | McNemar p |
|---|---:|---:|---:|---:|---:|
| real | 100 | 1.3% | 1.3% | 0.3% | 1.000 |
| real | 250 | 2.5% | 6.3% | 0.7% | 0.453 |
| real | 500 | 10.1% | 10.1% | 1.5% | 1.000 |
| real | 1000 | 15.2% | 17.7% | 3.0% | 0.845 |
| real | 2000 | 21.5% | 24.1% | 5.9% | 0.864 |
| real_plus_fallback | 100 | **3.1%** | 1.5% | 0.3% | 0.688 |
| real_plus_fallback | 250 | **6.9%** | 6.1% | 0.7% | 1.000 |
| real_plus_fallback | 500 | **16.0%** | 9.2% | 1.5% | 0.163 |
| real_plus_fallback | 1000 | **22.9%** | 18.3% | 3.0% | 0.480 |
| real_plus_fallback | 2000 | 29.0% | 29.8% | 5.9% | 1.000 |

CBSA level, 935 in the universe:

| Arm | N | White space | Household baseline | Chance | McNemar p |
|---|---:|---:|---:|---:|---:|
| real | 10 | 1.3% | 20.3% | 1.1% | **0.000** |
| real | 25 | 7.6% | 31.6% | 2.7% | **0.001** |
| real | 50 | 11.4% | 43.0% | 5.3% | **0.000** |
| real | 100 | 19.0% | 62.0% | 10.7% | **0.000** |
| real_plus_fallback | 10 | 2.3% | 15.4% | 1.1% | **0.001** |
| real_plus_fallback | 25 | 6.9% | 28.5% | 2.7% | **0.000** |
| real_plus_fallback | 50 | 10.8% | 43.1% | 5.3% | **0.000** |
| real_plus_fallback | 100 | 19.2% | 58.5% | 10.7% | **0.000** |

The household baseline beats chance everywhere. White space beats chance
almost everywhere and comes **level with it** in the worst cell — `real`, 45
miles, top-10 metros, where it caught 1 of 79 openings, 1.3%, against a 1.1%
chance rate. *This cell used to read 0 of 73 and "falls below chance"; on the
current network it is one opening above chance instead of below it, which
changes the adjective and not the verdict.*

### 7.4 The scoreboard, over all 108 cells

Six in-band radii x two arms x two levels x four or five cut-offs:

```
  cells scored                                     108
  white space wins                                  14   (13.0%)
  household baseline wins or ties                   94
  p < 0.05 in white space's favour                   0
  p < 0.05 in the household baseline's favour       32
```

Twelve of white space's 14 wins are at the ZCTA level, 13 of the 14 are in
the `real_plus_fallback` arm, and **none of them is significant**. The
baseline's 32 significant wins are concentrated at the CBSA level, where
white space loses by 20 to 48 percentage points. The single win in the
`real` arm is at 8.3 miles, the shortest radius in the band.

### 7.5 Why: Amazon densified

The mechanism is one number. The median distance from a 2024–25 delivery
station opening to the **nearest facility that already existed in 2023** is
**7.5 miles** (`real`) and **10.1 miles** (`real_plus_fallback`).

And the share of those openings that landed inside coverage the pre-2024
network already had. **Read this table down a column, not across one**: the
two columns are different coordinate sets scoring different numbers of
openings — 79 in `real`, 131 in `real_plus_fallback` — so a range taken across
a row is a range across coordinate sets, and a range taken down a column is a
range across radii. Collapsing both into one interval is how "67–77%" got into
circulation, and it is wrong in both directions.

| Radius (mi) | `real` (of 79) | `real_plus_fallback` (of 131) |
|---:|---:|---:|
| 8.3 | 54.4% (43) | 45.0% (59) |
| 12.7 | 64.6% (51) | 55.7% (73) |
| 15.0 | 67.1% (53) | 57.3% (75) |
| 19.6 | 68.4% (54) | 61.1% (80) |
| 25.0 | 70.9% (56) | 62.6% (82) |
| **45.0** | **75.9% (60)** | **68.7% (90)** |

**The headline is the bottom row and only the bottom row: 68.7–75.9% at 45
miles**, which is the one radius with an external source attached to it (§4).
The 67.1% that circulates beside it is the `real` column at **15** miles.

Amazon's 2024–25 build was overwhelmingly *infill* — a second and third
station inside a metro it already served, to cut the last-mile leg — not
expansion into new territory. A rule that looks only at unserved territory
cannot see that, and so cannot predict it.

### 7.6 It is not zero — the true positives, named

At 45 miles, `real_plus_fallback`, the top-25 white-space metros contained 9
of the 130 held-out openings that carry a CBSA:

> Anchorage AK, Columbus GA-AL, Duluth MN-WI, Erie PA, Portland-South
> Portland ME, Roanoke VA, San Juan-Bayamón-Caguas PR, Shreveport-Bossier
> City LA, Sioux Falls SD-MN.

At N=10 it is three: Portland ME, San Juan PR and Shreveport LA. Those are
real predictions that came true — 3 of 130 openings is a 2.3% hit rate
against a 1.1% chance rate, so twice chance. The problem is not that white
space is empty; it is that over the same 10 metros the household baseline
caught 20 of 130, 6.7 times as many, at p = 0.0005.

---

## 7.7 Why it failed — isolating the cause

`src/siting_atlas/analysis/white_space_rules.py`,
`white_space_diagnose.py`.

"It lost" is a result; it does not say **which part** of the idea is wrong.
Three candidates, and they imply completely different next steps:

1. **The operationalisation is blunt.** "Is this ZCTA uncovered?" is a binary.
   A planner asks *how many unserved households would a station HERE capture*,
   which scores a covered ZCTA on the edge of a metro highly. Maybe the idea
   is right and the rule is crude.
2. **A measurement artefact.** A spatially smoothed score picks contiguous
   blobs, so its top-N ZCTAs span far fewer distinct places. Comparing two
   such rules at fixed N is then not a fair fight.
3. **The coverage conditioning itself**, in which case no re-ranking helps.

Five rules, scored on the same held-out openings, pre-2024 network:

| Rule | What it ranks by | Uses coverage? |
|---|---|---|
| `households` | households in the ZCTA | no — the baseline |
| `white_space` | households, uncovered ZCTAs only | yes, as a **mask** |
| `coverage_gain` | unserved households within the radius | yes, as a **mask** |
| `load_per_facility` | households within the radius ÷ (1 + facilities in it) | yes, as a **weight** |
| `demand_in_radius` | households within the radius, coverage ignored | **no — the control** |

`demand_in_radius` is the design's whole point. It shares the radius, the
smoothing and the neighbour-sum machinery with `coverage_gain` and differs in
exactly one thing: whether the households being summed are masked to the
uncovered ones. Any gap between those two rows is the mask's doing and
nothing else's.

### Metro-level hit rates (chance = 1.1 / 2.7 / 5.3 / 10.7%)

| Arm | mi | Rule | N=10 | N=25 | N=50 | N=100 | distinct CBSAs in top-2000 ZCTAs |
|---|---:|---|---:|---:|---:|---:|---:|
| real | 15 | households | 10.1% | 21.5% | 36.7% | 50.6% | 312 |
| real | 15 | white_space | 0.0% | 11.4% | 17.7% | 35.4% | 712 |
| real | 15 | coverage_gain | 7.6% | 13.9% | 16.5% | 40.5% | 160 |
| real | 15 | **load_per_facility** | **17.7%** | **34.2%** | **39.2%** | **55.7%** | 88 |
| real | 15 | **demand_in_radius** | **20.3%** | **27.8%** | **43.0%** | **59.5%** | 22 |
| real | 45 | households | 10.1% | 21.5% | 36.7% | 50.6% | 312 |
| real | 45 | white_space | 0.0% | 2.5% | 3.8% | 8.9% | 549 |
| real | 45 | coverage_gain | 0.0% | 1.3% | 2.5% | 6.3% | 126 |
| real | 45 | load_per_facility | 1.3% | 3.8% | 8.9% | 13.9% | 251 |
| real | 45 | demand_in_radius | 12.7% | 25.3% | 39.2% | 46.8% | 12 |
| r+f | 15 | households | 9.2% | 22.3% | 37.7% | 48.5% | 312 |
| r+f | 15 | white_space | 0.8% | 9.2% | 15.4% | 30.0% | 735 |
| r+f | 15 | coverage_gain | 6.9% | 10.0% | 19.2% | 37.7% | 185 |
| r+f | 15 | **load_per_facility** | **15.4%** | **30.0%** | 36.9% | **56.2%** | 108 |
| r+f | 15 | **demand_in_radius** | **17.7%** | **27.7%** | **43.1%** | **53.8%** | 22 |
| r+f | 45 | households | 9.2% | 22.3% | 37.7% | 48.5% | 312 |
| r+f | 45 | white_space | 1.5% | 3.8% | 9.2% | 15.4% | 514 |
| r+f | 45 | coverage_gain | 0.8% | 3.1% | 5.4% | 8.5% | 129 |
| r+f | 45 | load_per_facility | 1.5% | 6.9% | 13.1% | 17.7% | 248 |
| r+f | 45 | demand_in_radius | 8.5% | 21.5% | 33.8% | 43.8% | 12 |

*The hit-rate columns are the current artefact. The right-hand
`distinct CBSAs` column is **not** emitted by `white_space.json` in this run
and has been left at its 2026-09-14 values; treat it as `[unverified]`. It
carries a qualitative point — smooth rules concentrate in few metros — that
the orders of magnitude still support, and none of the arithmetic below
depends on its exact values.*

### Candidate 2 is real, and it is controlled for

The right-hand column measures it. `demand_in_radius`'s top 2,000 ZCTAs sit
in **12 metros**; `households`'s sit in **312**; `white_space`'s in **735**. A
fixed-N ZCTA comparison therefore does penalise smooth rules for being smooth.
That is why every number above is **metro-level**, where the artefact cancels
— and it is why the ZCTA-level race in the artefact should be read as
diagnostic, not as a horse-race.

### Candidate 3 is the answer

At the metro level, the coverage **mask** costs **13.9 to 24.0 points**, while
the spatial smoothing the masked rule shares with the control costs **-6.3 to
+0.8** — that is, smoothing is free or helpful. Remove the mask and nothing
else (`coverage_gain` → `demand_in_radius`) and the whole gap comes back: at
45 miles, `real`, N=100, 6.3% becomes 46.8%.

So candidate 1 is ruled out too. Re-ranking the same idea more cleverly does
not rescue it, because the defect is not the ranking — it is conditioning on
non-coverage at all.

### The thing that looks like a rescue, and why I am not claiming it

`load_per_facility` — **weight** by service intensity instead of **excluding**
served places — beats the household baseline at 15 miles in both arms, at
p = 0.021 (`real`, N=25) and p = 0.039 (`r+f`, N=10). It is a coherent story:
build where the existing stations are over-subscribed, which is exactly the
densification §7.5 found. It also fails badly at 45 miles (p < 0.001 *against*
at N=50 and N=100), where coverage saturates and the denominator stops
discriminating.

**It is not a finding, and the artefact says so.** These five rules were
chosen *after* seeing the back-test fail and are scored on the *same*
hold-out. `white_space_diagnose.multiplicity` counts the exposure:

```
  paired tests run                                   128
  expected significant by chance at p < 0.05         6.4
  observed significant FOR an alternative rule         7   <- chance
  observed significant FOR the household baseline     64   <- 10x chance
```

Seven favourable significances against 6.4 expected is exactly what noise
produces. Sixty-four unfavourable ones is not. The correct reading is that
**nothing tested here rescues the framing**, and `load_per_facility` at a
short radius is a hypothesis for a fresh hold-out — 2026 openings, when they
exist — rather than a result. Promoting it now would be the same error the
project already documented in `NOTES_COVARIATE_LEAKAGE.md`, one level up: not
leakage of a date, but leakage of the test set into the choice of model.

---

## 8. What this does NOT show

**It does not show that the unserved households are not unserved.** The 11.6M
figure at 45 miles is a measurement of the facility geography, and it stands
whatever Amazon does next.

**It does not show that white space is useless to a planner.** A planner
asking "does my county have same-day coverage?" gets a defensible answer
here. A planner asking "will Amazon come?" does not.

**It does not show that Amazon will never enter these places.** The test
window is two years and 131 openings. A firm that has 91% household coverage
at 45 miles has, by construction, little territory left to expand into; the
infill result may be a statement about 2024–25 specifically rather than about
Amazon's strategy in general. Re-running this in 2027 is the check, and the
code takes a `CUT_YEAR` argument for exactly that.

**It does not survive a change of coordinate arm.** §5.2 and §6: the two arms
agree about 10 of 30 top ZCTAs and 7 of 15 top metros.

---

## 9. Verdict — should the capstone be built on this?

**No. It should be reported by it.**

The honest summary is two sentences that point in opposite directions, and
both are measured:

> At the 45-mile radius MWPVL itself states for delivery stations, 91.0% of
> US households already sit inside an Amazon service area, and 9,606 ZCTAs
> holding 11.6M households do not.
>
> Ranking those unserved places by household count does **not** predict where
> Amazon opened in 2024–25: it wins 14 of 108 scored comparisons against a
> ranking that ignores coverage entirely, none of them significantly, while
> losing 32 significantly — because **at that same 45-mile radius** 68.7–75.9%
> of the openings were infill inside territory Amazon already served — 75.9%
> of the 79 openings with real coordinates, 68.7% of the 131 once centroid
> fallbacks are admitted — at a median of 7.5 to 10.1 miles from an existing
> building.

That is a better capstone contribution than a coverage map would have been.
It is a pre-registered, leakage-controlled test of a plausible framing that
came out negative, with the mechanism identified. The project already has
five panel compositions and three algorithms agreeing on a 2.5-3.1x ceiling;
what it has been short of is a result that could have gone the other way and
didn't.

Three things to carry into the write-up:

1. **Lead with the coverage measurement, not the prediction.** It is the
   usable output and it is not contested by the back-test.
2. **Report the back-test as a finding, not a footnote.** "Unserved demand
   does not predict entry because incumbents densify" is a defensible
   sentence about retail logistics, and it has a literature to sit in —
   Holmes (2011) on cannibalisation and Houde, Newberry & Seim (2023) on
   Amazon's own network economics both describe firms trading off proximity
   against overlap.
3. **Never quote a white-space figure without the radius and the coordinate
   arm.** The radius moves it 5.1x and the coordinate arm changes two thirds
   of the named list.
4. **Carry §7.7's multiplicity guard with any "but this rule works" claim.**
   The most interesting-looking result in this document —
   `load_per_facility` beating the baseline at 15 miles — is within chance
   for the number of tests run, and the write-up is stronger for saying so
   than for burying it.

---

## 10. What I did NOT do

- **No drive-time isochrones.** No routing matrix exists in this project, and
  every radius here is straight-line. §2.
- **No facility-class-specific radii.** A fulfilment centre gets the same disc
  as a delivery station. HNS (2023) would give sortation 150 miles; adopting
  that would shrink white space and it would be a second unmeasured
  parameter.
- **No capacity model.** A ZCTA inside one station's disc and a ZCTA inside
  six are both "covered". Congestion, throughput and same-day cut-off times
  are all invisible here.
- **No competitor network.** UPS, FedEx, Walmart and USPS all serve these
  places. "Unserved by Amazon" is not "unserved".
- **No ZCTA-level geometry.** Centroids only. `data/interim/zcta_geom.parquet`
  exists and a polygon intersection would be a real improvement at the short
  radii; geopandas is an optional dependency in this repo precisely because
  GDAL is the most likely thing to break a clean install.
- **No attempt to re-geocode the 240 fallbacks.** That, not any modelling
  change, is the single highest-value next step: it would collapse the gap
  between the two arms in §5.2, and it is bounded work on 240 addresses.
- **No sensitivity to the household ranking itself.** Places could be ranked
  by population, by ACS households, by parcel volume proxies, or by
  households-per-uncovered-square-mile. Only households is tested, on the
  grounds that it is the unit a delivery network serves and the one covariate
  `catchment_band.json` finds significant at every radius.
- **No 2026 data.** `HELD_OUT_YEARS = (2024, 2025)` and the frame carries 17
  rows dated 2026 plus three obvious OCR errors dated 2028, 2075 and 2094.
  They are excluded from both the network and the held-out set.

---

## Files

```
  src/siting_atlas/analysis/white_space.py           orchestrator + CLI
  src/siting_atlas/analysis/white_space_network.py   the three sources
  src/siting_atlas/analysis/white_space_cover.py     geometry + named lists
  src/siting_atlas/analysis/white_space_backtest.py  the hold-out test
  src/siting_atlas/analysis/white_space_rules.py     the five-rule race
  src/siting_atlas/analysis/white_space_diagnose.py  why it failed + guard
  src/siting_atlas/analysis/white_space_print.py     console rendering
  outputs/metrics/white_space.json                   every figure above
```

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.analysis.white_space
```

Runs in about three minutes, most of it the four 1.1e9-element matmuls behind
§7.7. Nothing is fitted and nothing is seeded, so it is deterministic.
