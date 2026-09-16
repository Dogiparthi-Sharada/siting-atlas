# NUMBERS — single source of truth

Every value below was **re-derived from `outputs/metrics/*.json` and the data files
on 2026-09-15**. No markdown document was trusted as a source; the documents are what
this file exists to correct. Where a number could not be derived from an artefact it is
in the "cannot be verified" section rather than restated.

Artefacts with no `run_id`/`written_at` field are stamped with their file mtime
(local time, `-0700`) and marked `mtime only`.

> **`covariate_search.json` has settled.** The re-run that was live while this file
> was first written has completed, and every figure taken from it below has been
> re-derived from the finished artefact (`run_id 20260915-235210-ff92`,
> `written_at 2026-09-15T23:52:16+00:00`, `facilities: 687`). **That stamp is not a
> reliable version marker for artefacts written before 2026-09-16** — that
> emitter reused one `run_id` across successive writes and stamped
> `written_at` at the first write. The cause is fixed in
> `src/siting_atlas/common/log_json.py` and locked in by a test, but artefacts
> produced before the fix still carry the old stamps, so check `facilities: 687`
> and the `stage_ledger` rather than trusting them.

---

## 1. Panel size

| Quantity | Correct value | Source artefact | run_id / written_at | Stale variants to sweep |
|---|---|---|---|---|
| Rows in the expanded facility panel | **693** | `data/external/facility_panel/national_facilities_expanded.csv` (694 lines incl. header; 693 distinct `facility_id`) and `national_panel_expanded.json:rows_in_file` | mtime only, 2026-09-15 12:56:32 | 700, 658, 104 |
| Buildings (rows that survive edit `E_operating_by`) | **687** | `national_panel_expanded.json:buildings`; 693 − 6 `excluded` records | mtime only, 2026-09-15 12:56:32 | 694, 700, 658 |
| Panel rows after merge | **693** (from 104) | `mwpvl_merge.json:panel_rows_after` / `panel_rows_before` | `20260915-195256-1c53`, 2026-09-15T19:52:58Z | 700, 658 |
| MWPVL delivery-station rows merged in | **635** in file → 634 after internal dedup → **589 new rows added**, 40 already in panel, 5 held for clerical review | `mwpvl_merge.json` | same | 591 in / 554 added / 596 added |
| Refit arm sizes | `original_104`: **94 decisions**, 100 facilities. `expanded_658`: **483 decisions**, **687 facilities** | `refit_expanded.json:arms` | `20260915-195645-1f05`, 2026-09-15T19:58:06Z | 658 facilities; 700 |
| Distinct CBSAs / states / coordinates in the CSV | **230 / 50 / 0** | derived from the CSV; `national_panel_expanded.json` agrees | mtime only | 210, 214 CBSAs |

**Verdict: 693 rows / 687 buildings is correct. 700/694 is stale.** The two counts are
*not* rows-vs-deduplicated-buildings: the CSV holds 691 distinct address+ZIP pairs.
687 = 693 minus the six rows rejected by the OSHA `E_operating_by` edit, which stay in
the CSV so the exclusion is reversible.

**Not committed.** `git ls-files data/external/facility_panel/` returns only
`facilities.csv` and `national_facilities.csv`; `national_facilities_expanded.csv` and
`geocoded_expanded.csv` are untracked. The 693-row panel exists only on this disk.

---

## 2. Coverage / the visibility gap

| Quantity | Correct value | Source artefact | run_id / written_at | Stale variants |
|---|---|---|---|---|
| MWPVL delivery-station cities | **488** | `mwpvl_coverage.json:mwpvl_delivery_station_cities` | mtime only, 2026-09-15 12:58:52 | 459, 420 |
| Cities OSHA inspected (all Amazon facility classes) | **340** | `:osha_cities_all_facility_classes` | same | — |
| Cities in both lists | **138** | `:cities_in_both` | same | 124, 106 |
| MWPVL cities OSHA never inspected | **350** | `:cities_mwpvl_names_that_osha_never_inspected` | same | 335, 314 |
| Share of MWPVL cities OSHA has seen | **0.2828 (28.3%)** | `:share_of_mwpvl_cities_osha_has_seen` | same | 27%, 25% |
| MWPVL rows with no usable city+state | **39** (of 635) | `:mwpvl_rows_without_a_usable_city_and_state` | same | — |

Internally consistent: 138/488 = 0.28279 and 488 − 138 = 350.

**Correct phrasing of the 488/340 pair.** Two independent city lists, not a numerator
and denominator. 488 = distinct cities where MWPVL lists an Amazon **delivery station**.
340 = distinct cities where OSHA ever inspected **any** Amazon facility class.
Intersection 138. So: *of the 488 cities MWPVL says have a delivery station, OSHA has a
record in only 138 — 28.3%; the other 350 are invisible to OSHA entirely.* Two
qualifications must travel with it: (a) the comparison is **conservative** — OSHA's side
is unrestricted by facility class, so narrowing it would widen the gap; (b) it is a
**floor, not an estimate** — a two-list intersection, not capture-recapture, and MWPVL
is itself incomplete. The modelled estimate is in `nlrb_coverage.json`.

---

## 3. Large-metro top-10 lift — every arm

The quantity is at `arms.<arm>.methods.<method>.strata.top10.large_gt100.lift`, **not**
`arms.*.strata.*` (the arm-level `strata` key does not exist). Chance rate and decision
count are fixed within an arm, so only the model differs.

Source: `outputs/metrics/panel_experiments.json` — **no `run_id` field**; mtime
2026-09-15 13:37:43 −0700.

| Arm | n_decisions (n_test) | large-stratum decisions | conditional_logit | gbm stump/200 levels | gbm deep/300 levels |
|---|---|---|---|---|---|
| `original_only` | 94 (38) | 46 | **6.180** | 7.041 | 4.994 |
| `mwpvl_only` | 389 (156) | 212 | **6.526** | 6.232 | 5.128 |
| `mwpvl_clean` | 360 (144) | 194 | **6.779** | 6.227 | 5.378 |
| `combined` | 483 (193) | 258 | **6.258** | 6.410 | 5.522 |
| `combined_plus_network` | 483 (193) | 258 | **6.290** | 6.457 | 5.825 |

Attribution of the circulating values:

| Value | What it actually is | Status |
|---|---|---|
| 6.14 | `lift_by_market_size.json` → `original.large_gt100.lift` = 6.1381 | **Retired artefact.** That file carries a `superseded_by: panel_experiments.json` stamp, has no emitter in the tree, no run_id, one split, and a tie-broken empirical null. Do not quote. |
| 6.18 | `panel_experiments` `original_only` / conditional_logit = 6.1804 | **Current** |
| 6.26 | `combined` / conditional_logit = 6.2585 | **Current** |
| 6.42 | `lift_by_market_size.json` → `expanded.large_gt100.lift` = 6.4246 | **Retired artefact** |
| 6.31, 6.33, 6.37 | No match in any current artefact | **Stale — sweep out** |

Two other large-stratum top-10 lifts exist in other artefacts and must not be confused
with these: `gravity_network.json` (see §4) and `covariate_search.json` `core.baseline`
= **6.2157** on a *different* frame (477 decisions, 191 test, 21 768 frame ZCTAs).
Its `anchor.baseline`, on the full 483-decision frame, is **6.2585** and reproduces
`panel_experiments.json`'s `combined` arm exactly.

---

## 4. Gravity vs proximity

Source: `experiments/gravity-network/artefacts/gravity_network.json`, `run_id 20260915-210603-b780`,
`written_at 2026-09-15T21:46:53+00:00`, 483 decisions / 86 682 alternatives / 50 re-splits.
All 13 arms hold the same decisions and the same splits, so lift differences are model
differences.

| Arm | Role | large-stratum top-10 lift | standardised top-10 lift | pooled Brier |
|---|---|---|---|---|
| `no_network` | **floor** — no network term at all | **6.2585** | 2.7399 | 0.0050363 |
| `proximity_published` | **baseline** — the published proximity claim | **6.2903** | 2.7682 | 0.0050303 |
| `proximity_only` | proximity without `network_within_50mi` | 6.2823 | 2.7671 | 0.0050303 |
| `gravity_count_a3` | **best gravity** (selection rule: highest large-stratum lift among arms with *both* columns interior) | **6.2187** | 2.7671 | 0.0050165 |
| `gravity_best_plus_proximity` | best gravity + proximity | 6.1988 | 2.7655 | 0.0050163 |
| `gravity_sqft_a1` | highest raw large lift of any gravity arm, but **not fully interior** | 6.2585 | — | — |

**The unambiguous comparison.** On large-metro top-10 lift, the best fully-interior
gravity arm (6.219) is **below** both the published proximity baseline (6.290) and the
no-network floor (6.259) — gravity does not beat proximity there. Gravity wins on
top-1, top-5 and Brier: `gravity_count_a3` vs `proximity_published`, paired over 50
re-splits, is +0.0116 on top-1 (42 improved / 4 worsened) and +0.0126 on top-5 (44 / 2),
while top-10 is −0.0002 (18 / 22). `best_gravity.any_gravity_arm_fully_interior` is
`true`. Do not quote a single scalar for "gravity vs proximity" — it depends on k.

---

## 5. The dispersion finding — resolved

Source: `gravity_network.json`, same run as §4. `terms.dispersion` is computed at
vintage 2030, over 41 large metros (≥101 candidate ZCTAs) and 8 271 candidate ZCTAs.

**Counts, exactly as asked:**

| Question | Answer |
|---|---|
| Terms with a `mean_within_metro_cv` | **21** |
| cv **below 0.6** | **7** (0.2975 – 0.5918) |
| cv **between 0.6 and 1.3** | **0** — the band is empty |
| cv **above 1.3** | **14** (1.3993 – 8.5046) |
| Of the 21, how many appear in `boundary_census` at all | **5** — `sortation_proximity`, `fulfilment_proximity`, `network_within_50mi`, `sortation_gravity_count_a3`, `fulfilment_gravity_count_a3`. `boundary_census` covers 4 of the 13 arms. |
| Of those 5, how many match "low cv fails / high cv works" | **3 clean matches** (`network_within_50mi` low-cv and at the boundary in 42/50 re-splits; both `*_gravity_count_a3` high-cv and interior in every re-split in both arms). **1 clear counterexample** (`sortation_proximity`, cv 1.40, at the boundary in all three arms it appears in). **1 mixed** (`fulfilment_proximity`, cv 1.44, interior in both proximity arms but at the boundary in 22/50 re-splits once it competes with gravity). |

**The evidence base is much larger than `boundary_census`.** `arms.<arm>.verdicts.<col>.state`
in the *same file* gives a boundary/interior call, by the same percentile rule, for **all
21 terms** in the arm where each is fitted. Extending to that:

| cv band | n | interior in own arm | not interior |
|---|---|---|---|
| < 0.6 | 7 | **0** | **7** |
| 0.6 – 1.3 | 0 | — | — |
| > 1.3 | 14 | **9** | **5** |

The 5 high-cv failures are `sortation_proximity`, `sortation_gravity_sqft_a2`,
`sortation_gravity_count_sqft_subset_a2`, `sortation_gravity_sqft_a3`,
`sortation_gravity_count_sqft_subset_a3` — all on the **sortation** side, four of the
five carrying square footage. Every **fulfilment**-side high-cv term is interior (7 of
7), as are the pure-count sortation gravity terms.

`network_inference.json` (`20260915-210640-dbcd`, 2026-09-15T21:21:38Z) adds an
independent read on three terms under a 500-replicate cluster bootstrap over 194 metros:
`network_within_50mi` `at_boundary: true` (80.8% / 67.4% of replicates at the boundary);
`sortation_proximity` and `fulfilment_proximity` `at_boundary: false`.
`covariate_search.json`, `logrel_search.json` and `percapita_search.json` all contain
boundary machinery (196 / 110 / 80 mentions) but **zero** mentions of any gravity,
proximity or `network_within_50mi` column — they add nothing on these 21 terms.

**The strongest claim the evidence supports, and no stronger:**

> Across all 21 network terms, low within-metro dispersion is **sufficient for failure**:
> every term with cv < 0.6 (7 of 7) lands at the coefficient boundary. High dispersion is
> **necessary but not sufficient for success**: 9 of the 14 terms with cv > 1.3 are
> interior; the 5 that are not are all sortation-side, 4 of them square-footage masses.
> No term is observed in the 0.6–1.3 band, so the finding says nothing about intermediate
> dispersion. With n = 21 terms from one run at one vintage, and the terms not
> independent (each is one of two columns in one of 13 arms over the same 483 decisions),
> this is a **descriptive regularity within one artefact**, not an estimated relationship.

Sweep out: any statement that dispersion "predicts" whether a term works in *both*
directions; any statement resting on `boundary_census` alone (5 of 21 terms); any claim
that the rule is exceptionless.

---

## 6. Densification

| Quantity | Correct value | Source artefact | run_id / written_at | Stale variants |
|---|---|---|---|---|
| 2024-25 delivery-station openings landing inside pre-2024 coverage, at the headline 45 mi | **68.7% – 75.9%** | `white_space.json:backtest` | mtime only, 2026-09-15 13:24:50 | 67-77%, 67-76% |
| ↳ real coordinates | **75.9%** = 60 of **79** openings | same | | |
| ↳ real + ZCTA-centroid fallback | **68.7%** = 90 of **131** openings | same | | |
| Headline radius | **45.0 mi**, great-circle centroid-to-facility | `:headline_radius_miles`, `:geometry` | | |
| White-space scoreboard | wins **14 of 108** cells (13%); **0** significant wins for white space vs **32** for the baseline | `:scoreboard`, `:verdict` | | |
| Median miles from opening to nearest pre-cut facility | 7.5 (real) / 10.1 (with fallback) | `:backtest` | | |

**The range is across coordinate sets at one radius, not across radii.** 67.1% is the
*real-coords, 15-mile* figure and 45.0/62.6 etc. are other radii — quoting "67-77%"
silently mixes the two axes. The full grid runs 45.0% (fallback, 8.3 mi) to 75.9%
(real, 45 mi).

---

## 7. Extraction and validation counts

| Quantity | Correct value | Source artefact | run_id / written_at | Stale variants |
|---|---|---|---|---|
| Facilities extracted from the MWPVL PDF | **1 904** across 13 tables | `mwpvl_extraction.json:facilities` | `20260915-195231-c54f`, 2026-09-15T19:52:37Z | 591 |
| …with a year | **1 420** | `:with_year` | same | 446, 524 |
| …with a month | **873** | `:with_month` | same | 306 |
| …`not_confirmed` | **44** | `:not_confirmed` | same | 18, 43 |
| **OSHA cross-check** (`E_operating_by`) on the extraction, all 1 420 dated rows | **208 linked, 11 falsified, pass rate 94.71%** | `mwpvl_validation.json` | `20260915-195247-dbb5`, 2026-09-15T19:52:48Z | 157/10/93.6%; 36 linked/97.2%; 96.0% |
| ↳ by precision | month 160 matched / 9 falsified; year 25 / 2; quarter 23 / 0 | same | same | 119/8, 21/2, 17/0 |
| **Date plausibility** | **99.5%** = (1 420 − 7) / 1 420; 2 before the network start (delivery-station tables only), 5 beyond plausible | `:date_plausibility` | same | 99.8% |
| **State cross-check** (OCR state vs geocoded state) | **604 agree of 606 comparable = 99.67%**; 613 parsed, 22 unparsed of 635 | `mwpvl_merge.json:ocr_state_grade` | `20260915-195256-1c53`, 2026-09-15T19:52:58Z | 517/518, 556/557 |
| Screenability of the merged rows | 634 rows; **54 unscreenable** (no street at all); 580 fully screenable | `mwpvl_merge.json:screenability` | same | 72 unscreened, 74 unscreened |
| `facility_check` on the expanded file | **fails**: 142 rows have a non-numeric `open_year` | `mwpvl_merge.json:facility_check` | same | 134 errors, 144 errors |

**1 904 / 1 420 verified.** Both 157/10/93.6% and 208/11/94.71% are real measurements
of the *same edit on different denominators over time*; **208/11/94.71% is current**.

---

## 8. Metro model

Source: `outputs/metrics/metro_entry.json`, `run_id 20260915-231322-7d21`,
`written_at 2026-09-15T23:13:41+00:00`. Verdict arm `prereg_strict`, form `logit`,
declared before any model was fitted. Prereg `docs/PREREG_METRO_MODEL.md`,
md5 `946f7ef75db69e5278eea409a04c3823`.

| Quantity | Correct value | Notes |
|---|---|---|
| Held-out years | 2019–2025, **7 years** | |
| **Years won on AUC vs the households baseline** | **0 of 7** (clause 1 fails) | Per-year model AUC 0.6098–0.8119; baseline2 AUC 0.8363–0.9682; every yearly diff negative, −0.112 to −0.271 |
| Years the model is at least as well calibrated as the constant null | **3 of 7** (2020, 2021, 2025 — clause 2 fails) | |
| **Pooled out-of-time AUC** | model **0.7323** vs households baseline **0.8949** vs facilities baseline **0.7325** vs year-base-rate null 0.5367 | 6 545 rows, 306 events |
| Pooled top-50 hits | model 29, households 32, facilities 32, null 4 (uniform expectation 2.338) | |
| **Clustered bootstrap interval** | model AUC mean **0.7319**, 95% **[0.6876, 0.7706]**; AUC − households **−0.1628**, 95% **[−0.2011, −0.1313]** | 2 000 draws, clustered on `cbsa_code`, 935 clusters, seed 20260913 |
| **Re-split record** | 50 repeats, 280 hold-out metros, seed 20260915. Model AUC **0.7251** [0.6482, 0.7873]; households **0.9001** [0.8735, 0.9291]; top-50 model **22.72** vs households **26.22** | The spread is over re-splits, not a standard error (prereg §6) |
| Verdict | **H0** on every arm × form (prereg_strict / vintage_clean / vintage_relaxed × logit / poisson / negbin), and H0 also when 2020–21 are excluded | |

---

## 9. Hazard revival

Source: `experiments/hazard-model/artefacts/hazard_revival.json`, `run_id 20260915-224104-21a7`,
`written_at 2026-09-15T22:42:02+00:00`. Retired baseline read from
`hazard_report.json` (`20260914-002509-2374`).

| Quantity | Before (retired run) | After (best revival arm `new_dates_3cov`) |
|---|---|---|
| **Events** | **812** | **5 441** |
| Risk-set units / rows | 1 756 / 40 358 | 11 230 / 256 081 |
| Usable facilities / independent episodes | 38 / 28 | 687 loadable, 545 dated, 540 attached at 15 mi |
| **AUC, held-out-by-unit** | **0.6894** | **0.6832** |
| AUC, out-of-time | 0.5551 | 0.6323 |
| AUC, out-of-area | 0.6168 | 0.7104 |
| AUC range across all 7 arms × 3 hold-outs | — | **0.4527 – 0.7515**, median 0.6459, 17 comparisons |

| Quantity | Correct value | Notes |
|---|---|---|
| **Calibration record** | The constant null is better calibrated in **17 of 17** comparisons. `model_better_calibrated_at` is an **empty list**. | `calibration_against_constant` |
| **Median ZCTAs switched on per opening** | **39** (mean 52.4, p10 11.9, p90 105, max 317) at the 15-mile catchment; **13** median newly-switched-on (mean 20.3, max 228, over 459 facilities) | `provenance.catchment_load`. Band: median 14 at 8.3 mi, 30 at 12.7 mi, 39 at 15 mi |
| ZCTAs covered / % served by 2+ facilities | 9 113 / 58.4% at 15 mi | |
| Verdict | **Retirement stands.** The retirement was taken on the unit of analysis, not sample size or dates. | `verdict` |

The **39** and the **13** are different quantities and both appear in circulation —
see §14.

---

## 10. Cost model

Source: `outputs/metrics/cost_report.json`, `run_id 20260916-024154-0aa8`,
`written_at 2026-09-16T02:42:22+00:00`; underlying tables
`outputs/tables/cost_to_serve_2023q4_*.parquet` (all five, mtime 2026-09-15 19:42). Every
figure below was recomputed from the parquet and matches the report unless noted.

**Regenerated 2026-09-16.** The report previously carried `run_id
20260914-002418-0623` / `written_at 2026-09-14T00:24:23+00:00` and held **only**
the `baseline` key. All five scenarios are present again and every value below
is unchanged — this is a re-run of the same model on the same inputs, not a
correction. Any document still citing the 2026-09-14 id for a cost figure is
citing a file that no longer exists in that form.

| Quantity | Correct value | Notes |
|---|---|---|
| **Median cost per parcel** | **$1.0830** | 2023Q4 baseline scenario |
| **p10 / p90** | **$0.9778 / $1.4180** | |
| **ZIPs (ZCTAs) costed** | **2 333** | |
| Total daily cost | $14 001 626 | |
| Total vans | **78 292** | = `ceil(sum(van_days))` = 78 291.6. The parquet's `vans_required` column sums to **79 484** because it ceilings per ZCTA first. Report the 78 292. |
| **Depots solved** | **334** | **Resolved.** 334 = Σ over the 10 pilot metros of `ceil(metro daily parcels / 40 000)`. 329 = 13 152 992 / 40 000 = 328.8, the *national* division that ignores per-metro rounding. Both are derivable; the solver opens 334. The `depots.py:67` docstring and the `params.py:220` docstring are both right about different things and should say so. |
| Total daily parcels | 13 152 992 | |
| **Cost decomposition (stop-weighted shares)** | service time **66.96%**, vehicle **22.93%**, drive time **6.97%**, distance **3.14%** | Recomputed from the parquet. Consistent with `params.py`'s "local travel is 3.3% of the bill" and with the claim that routing mathematics is decoration while labour carries the headline. `runner.py:156` records a historical bug where "shares summed to 140%" — any document quoting shares that do not sum to 100% is quoting that bug. |
| Portfolio breakeven margin | $1.3431 (greedy) / $1.3431 exact, upper bound $1.2129, gap 10.7%; 282 activations | `portfolio_report.json`, `20260914-002431-7419` |

---

## 11. GBM benchmark

Source: `outputs/metrics/gbm_benchmark.json`, `run_id 20260915-200312-1d51`,
`written_at 2026-09-15T20:04:30+00:00`. National frame, 94 decisions, 38 test, 50 repeats,
seed 20260914.

**Quote `across_repeats`, never `headline_split`.** The artefact carries an explicit
`headline_split_warning`: perturbing the attraction matrix by 1e-12 moves the
single-split GBM top-10 by up to 2 of 38 decisions, and no LightGBM determinism flag
fixes it (tested). Any document quoting single-split GBM counts (24, 23, 20, 18 of 38)
is quoting noise.

| Method | top-10 mean of 38 | sd | [p2.5, p97.5] | mean Brier | vs raw_count (mean, W/L) |
|---|---|---|---|---|---|
| `gbm stump/200 levels` | **22.26** | 2.75 | [18.00, 27.00] | 0.007681 | +1.30, 30/11 |
| `gbm stump/200 shares` | 22.20 | 2.70 | [18.00, 27.77] | 0.007839 | +1.24, 30/10 |
| `gbm small/100 levels` | 22.18 | 2.64 | [17.23, 27.00] | 0.007782 | +1.22, 34/10 |
| `gbm small/100 shares` | 22.14 | 2.81 | [18.00, 27.77] | 0.007863 | +1.18, 33/10 |
| `raw_count` | 20.96 | 2.50 | [17.23, 25.77] | 0.007793 | — |
| `conditional_logit` | **20.60** | 2.72 | [16.23, 25.00] | **0.007550** | −0.36, 11/23 |
| `gbm deep/300 levels` | 18.76 | 2.48 | [14.22, 24.00] | 0.010392 | −2.20, 10/36 |
| `gbm deep/300 shares` | 18.56 | 2.55 | [14.00, 22.77] | 0.011016 | −2.40, 7/39 |

Best GBM by CV top-10: `gbm stump/200 levels`. Gain importance:
`warehousing_establishments` 0.535, `land_area_sqmi` 0.185, `households` 0.143,
`establishments` 0.137. The ordering that carries the verdict — shallow GBM ≈ 22.1–22.3
> raw_count ≈ 21.0 ≈ conditional_logit 20.6 > deep GBM ≈ 18.6–18.8 — is stable under
perturbation; the conditional logit still has the **best Brier**.

---

## 12. Test count and coverage

| Quantity | Correct value | How derived | Stale variants |
|---|---|---|---|
| **Tests collected** | **660** across 49 test files | `pytest --collect-only -q -o addopts=""`, 2026-09-16 | 798, 796, 787, 650. 798/60 was correct until 11 test files retired to `experiments/retired-tests/` with their code, taking 138 tests |
| **Result** | **658 passed, 2 xfail, 0 failures** | full `pytest -q -p no:randomly` run, exit 0, 2026-09-15 | "787 tests passing" |
| **Source modules** (`src/siting_atlas/**/*.py`, excluding `__init__.py`) | **138** (148 files including 10 `__init__.py`) | filesystem count, 2026-09-16 | 181, 193, 133. 56 `.py` files moved to `experiments/` on 2026-09-15 |
| **Modules unreachable from any test** | **75 of 138** | AST import-graph BFS seeded from every file under `tests/`, following relative and absolute `siting_atlas.*` imports and package `__init__` ancestors. No `importlib`/dynamic imports in `tests/` that could produce a false negative. | 39 of 133; 78 of 181; 81 of 193. All three predate the retirement. Re-measured 2026-09-16 |

**The audit's "39 of 133" (`docs/AUDIT_2026_09_14.md` §2.2, measured 2026-09-14 at 650
tests) is stale, and the gap has widened, not closed.** The MWPVL sprint modules it named
are now reachable; the modules written since are not. Unreachable today: every
`white_space*` (7), `metro_*` (9), `hazard_revival*` (5), `gravity_*` (5), `network_*` (8)
and `tiger_*` (8) module, plus `models/panel_experiments.py`, `models/covariate_search.py`,
`models/logrel_*`, `models/percapita_*`, `report/scope.py`, `viz/build.py`,
`app/dashboard.py`, `optimize/runner.py`, `ingest/registry.py`.

Every artefact in §§3–9 is written by a module in that list. **"660 tests pass" and "the
headline artefacts have no test importing their emitter" are both true and must be
quoted together.**

---

## 13. Geocoding rate

| Quantity | Correct value | Source | Label |
|---|---|---|---|
| Geocode match rate, `data/external/facility_panel/geocoded_expanded.csv` | **72.3% = 501 Match of 693** (190 No_Match, 2 Tie) | derived from the CSV | **Untracked working-tree file** — `git ls-files` does not list it; `.gitignore:123` un-ignores it but it was never added. There is **no committed version at all.** |
| Geocode match rate, `data/interim/geocoded_expanded_rebuilt.csv` | **72.3% = 501 of 693** | derived | Uncommitted (`data/interim/` holds only `.gitkeep` in git). **Byte-identical to the file above** (`diff` reports no difference). |
| The claimed "before" figure | **65.0% = 455 of 700** | no current artefact holds it | **Stale.** Both its numerator and its denominator belong to the retired 700-row panel. |

**Resolution.** The documents say the improved run "may live only in uncommitted
`data/interim/*_rebuilt.csv`" and that "the committed `geocoded_expanded.csv` is still
the 65.0% run". **Both halves are now wrong.** The canonical file and the rebuilt copy
are byte-identical and both read 72.3%; neither is committed, so no "before" file exists
on disk. Correct statement: *72.3% (501 of 693) on the current panel; the earlier 65.0%
(455 of 700) was measured on the superseded 700-row panel and no file reproducing it
survives.*

Related: `national_panel_expanded.json` records `coordinates_present: 0` — the panel CSV
carries **no** latitude/longitude, so every distance covariate resolves to a ZCTA
centroid. The 501 geocoded points live in the side file and are not joined into the panel.

---

## Numbers that cannot be verified

| Claim | Where it appears | Status |
|---|---|---|
| Nested forward selection came out **"0.72 points WORSE"** | `docs/PREREG_METRO_MODEL.md:9`; `academic/defense/VIVA_QA.md:677` records that it could not be reproduced | **REPRODUCED IN DIRECTION, RESTATED IN MAGNITUDE — the settled figure is −0.62 pp, not −0.72.** On the completed 687-facility / 477-decision run, `covariate_search.json` → `core.arms["forward (nested, honest)"].vs_baseline_large_top10.mean_rate_difference` = **−0.006201**, i.e. **−0.6201 percentage points**. Directly: the large-stratum top-10 hit rate falls from **30.473%** (`core.arms.baseline`) to **29.852%** (nested forward) = **−0.6201 pp**, over 50 re-splits, **5 wins / 19 ties / 26 losses**. The earlier check most likely failed because it looked for a *lift* difference (that is −0.1268) or a *pooled* difference. **The figure is stratum-specific and the stratum must always be named**: it is the large-metro top-10 rate. **Pooled across all choice-set sizes the comparison goes the other way and still does** — 52.419% → 52.775% = **+0.3560 pp BETTER** (it was +0.08 pp on the superseded copy, so the pooled sign has *not* flipped; it has grown). Unqualified, "0.72 points worse" is both stale and contradicted by a number in the same block. The sealed `PREREG_METRO_MODEL.md` keeps the 0.72 wording by design; the correction lives in `PREREG_METRO_MODEL_ERRATA.md`. |
| `covariate_search.json` `facilities_offered` | formerly: `core` and `permits` reported **694** against **687** elsewhere in the same file | **RESOLVED by the completed 2026-09-15 re-run.** The artefact now reads **687** at the top level and in all three staged frames, and the string `694` does not occur in it. Every stage's drop ledger balances on 687: `anchor` 687−13−142−49 = 483, `core` 687−19−142−49 = 477, `permits` 687−72−142−49−24−24 = 376. **The emitter defect that let two versions share a stamp is NOT fixed** — see the row below. |
| `covariate_search.json` `run_id` / `written_at` | `outputs/metrics/covariate_search.json:2-3` | **Live defect, unfixed.** `common/log_json.write_json` builds `{"run_id": …, "written_at": …, **payload}`, and `covariate_harness.load()` reads the previous artefact back in whole — so the payload carries the *previous* run's `run_id` and `written_at` and they shadow the fresh ones. A resumed run therefore inherits the old id and the first write's timestamp for the life of the file. **`run_id` cannot be used to tell two versions of this artefact apart.** Check `facilities` and `stage_ledger` instead. |
| `panel_experiments.json`, `white_space.json`, `mwpvl_coverage.json`, `national_panel_expanded.json`, `subsidies.json`, `logrel_*.json`, `percapita_*.json` provenance | — | **No `run_id` and no `written_at` field.** Only a file mtime backs them. Any document citing a run for these numbers is citing something the artefact does not record. |
| `lift_by_market_size.json` | cited by `docs/STATUS.md`, `docs/research/NOTES_EXPANDED_REFIT.md`, `models/covariate_search.py`, `models/covariate_report.py`, `models/panel_strata.py` | **Formally retired and unregenerable** — no emitter exists in the tree, no run_id, written by an ad-hoc inline script. Its own `finding` field is internally contradictory (prose says "3.68x→2.61x", the fields beside it say 2.948→2.757). All five citing sites should point at `panel_experiments.json`. |
| Any GBM figure taken from `gbm_benchmark.json:headline_split` | — | **Measured non-reproducible** by the artefact itself; not a quantity. |

---

## Quantities that are easily confused

1. **Rows vs buildings vs decisions vs facilities.** 693 CSV rows → 687 buildings
   (693 minus 6 `E_operating_by` exclusions) → 483 decisions in the `combined` arm
   (687 minus 21 with no panel ZCTA, 136 with no numeric open year, 49 with no earlier
   CBP vintage) → 193 test decisions per re-split. **"483 decisions on 687 buildings
   from 693 rows"** is the only correct full sentence. 691 distinct address+ZIP pairs is
   a fourth number and is not "buildings".

2. **Which large-metro top-10 lift.** Four artefacts publish one:
   `panel_experiments.json` (5 arms × 3 methods, 6.18–6.78 for conditional logit),
   `gravity_network.json` (13 arms, 6.10–6.29), `covariate_search.json` `core.baseline`
   (6.2157, a different frame with 477 decisions), and the retired
   `lift_by_market_size.json` (6.138 / 6.425). They are not the same quantity: the frames,
   the null (analytic `min(k,J)/J` vs a tie-broken empirical null), and the number of
   splits all differ. Always name arm **and** method **and** artefact.

3. **Stratum lift vs standardised lift vs pooled lift.** In `gravity_network.json`
   `proximity_published` the large-stratum top-10 lift is **6.290** and the standardised
   top-10 lift is **2.768** — same arm, same run. `lift_by_market_size.json`'s retirement
   note records the same trap: "standardised to the combined mix, top-10 lift moves
   2.858 → 2.706; the pooled 2.948 → 2.757 is not like-for-like."

4. **`no_network` vs `proximity_only` vs `proximity_published`.** Three distinct gravity
   arms. `no_network` is the floor (no network term); `proximity_only` drops
   `network_within_50mi`; `proximity_published` is the published baseline with all three
   network columns. Their large lifts are 6.259 / 6.282 / 6.290 — close enough that they
   are routinely swapped.

5. **The two OSHA cross-check rates.** `mwpvl_validation.json` tests all 1 420 dated
   *extraction* rows → 208 linked, 11 falsified, **94.71%**. `mwpvl_merge.json`
   `validation_E_operating_by` tests the 693-row *panel* → 551 dated, 136 linked,
   6 falsified, **95.59%**. Different denominators, same edit, both current. Neither is
   93.6%.

6. **Median ZCTAs per opening: 39 vs 13.** 39 is the median size of a facility's
   15-mile catchment. 13 is the median number of ZCTAs an opening switches on *for the
   first time* (the rest were already covered). Both are in
   `hazard_revival.json:provenance.catchment_load`, and only 39 supports the
   independence-violation argument.

7. **Densification: coordinate set, not radius.** 75.9% is real coordinates on 79
   openings; 68.7% is real-plus-fallback on 131. 67.1% is real coordinates at **15**
   miles, a different radius. Quoting "67–77%" mixes the two axes and inflates the range.

8. **"At the boundary" is a rule, not a fact.** `gravity_network.json` uses a re-split
   *percentile* rule and calls `sortation_proximity` "boundary inside the interval";
   `network_inference.json` uses the *point estimate* and calls the same column
   `at_boundary: false` (β = 0.097, 3.8% of bootstrap replicates at the boundary). Both
   are current and both are right under their own rule. Always name the rule.

9. **In-sample vs held-out for the metro model.** Pooled out-of-time AUC 0.7323 (one
   pass over 6 545 metro-years), re-split mean AUC 0.7251 (50 random 280-metro
   hold-outs), clustered bootstrap mean 0.7319 [0.6876, 0.7706] (2 000 draws over 935
   metro clusters). Three numbers near 0.73 that mean three different things; only the
   bootstrap carries an interval that is a bootstrap interval, and only the re-split
   spread is explicitly *not* a standard error.

10. **Every `[2.5, 97.5]` bracket in `gravity_network.json`, `panel_experiments.json`,
    `metro_entry.json` and `refit_expanded.json` is a percentile over re-splits of one
    fixed decision set — not a confidence interval and not a standard error.** The
    artefacts say so in a `spread_is_not_a_standard_error` / `interval_note` field. Any
    document that writes "95% CI" for one of these is wrong.

11. **334 vs 329 depots.** 334 = per-metro `ceil`, summed over 10 metros — what the
    solver opens. 329 = one national division of 13.2M by 40 000. Not a discrepancy once
    stated; a discrepancy every time it is not.

12. **78 292 vs 79 484 vans.** 78 292 = `ceil` of the summed van-days (the reported
    figure). 79 484 = sum of the per-ZCTA `vans_required` column, which ceilings 2 333
    times. Only the first is in `cost_report.json`.
