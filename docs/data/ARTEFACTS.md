# The artefact set — all 43 JSON files in `outputs/metrics/`

*Built 2026-09-15 by a reconciliation pass over the whole directory. Every
figure quoted here was read out of the file named beside it on that date, or
measured by a probe whose command is given. Sizes and run ids are from
2026-09-15 20:15 UTC.*

## Why this file exists

The project's standing rule is **cite the artefact, not the figure**: when a
document and an artefact disagree, the artefact wins. That rule has two
preconditions, and both had failed somewhere in this directory.

1. **The artefact must be reproducible.** One file — `lift_by_market_size.json`
   — had no emitter anywhere in the tree. Nothing could re-derive it, so
   "cite the artefact" pointed at a dead end.
2. **The artefact must say when it is stale.** Several did not. An artefact
   whose `caveats` array describes a state the same file's own fields
   contradict is worse than no caveat, because it is asserted with the
   authority of the artefact.

A third failure is quieter and is what most of this pass found: **an artefact
with no `run_id` cannot be placed in time**, so when two of them disagree
there is no tie-break. 23 of the 43 had no stamp. `mwpvl_coverage.json` was
re-emitted twice while this pass was reading it, with different numbers each
time and nothing in the file to say so.

## How to read the table

| column | meaning |
| --- | --- |
| **stamped** | carries `run_id` + `written_at`, written through `common/log_json.write_json`. `emitter only` means the emitter was migrated on 2026-09-15 and the file will be stamped when it is next re-run. |
| **emitter** | the module that writes it. `python -m <module>` unless noted. |
| **status** | `current`, `stale` (contradicts a newer artefact — see §5), or `superseded` (do not cite; a pointer is inside the file). |

## 1. Ingest (L0–L1)

| artefact | size | stamped | emitter | measures | status |
| --- | --- | --- | --- | --- | --- |
| `source_probe.json` | 5 KB | yes* | `ingest.probe` | reachability + shape of every declared source | current |
| `acquire_report.json` | 2 KB | yes | `ingest.acquire` | what was fetched into the immutable cache | current |
| `normalise_report.json` | 2 KB | yes | `ingest.normalise` | cache → typed parquet, per source | current |
| `normalise_external_report.json` | 1 KB | yes | `ingest.normalise_external` | same, for the manually placed sources | current |
| `external_check.json` | 2 KB | yes | `ingest.external` | schema/row checks on the external drops | current |
| `mwpvl_extraction.json` | 5 KB | yes | `ingest.mwpvl_tables` | 13 OCR'd MWPVL tables, 1,904 rows, per-field coverage | current |
| `mwpvl_validation.json` | 5 KB | yes | `ingest.mwpvl_panel` | `E_operating_by` over 1,420 dated MWPVL rows; 208 linked to OSHA, 11 falsified | current |
| `mwpvl_coverage.json` | 1 KB | **emitter only** | `ingest.mwpvl_coverage` | direct two-list gap: 635 MWPVL delivery stations in 488 cities, OSHA has seen 138 | current |
| `nlrb_coverage.json` | 5 KB | **emitter only** | `ingest.nlrb_capture` | capture–recapture ESTIMATE of unseen cities (contrast with the direct floor above) | current |
| `nlrb_only_cities.json` | 45 KB | **emitter only** | `ingest.nlrb_capture` | the 96-city worklist behind it. A worklist, not a result. | current |
| `highway_access.json` | 39 KB | **emitter only** | `ingest.tiger_lift` | interchange-proximity covariate arms, 50 re-splits | current |
| `subsidies.json` | 2 KB | **emitter only** | `ingest.subsidies` | Good Jobs First tracker, $16.06 bn disclosed to Amazon parent | current |

\* `source_probe.json` carries `run_id: "20260912-doc-verify"`, which is a
hand-set `SITING_ATLAS_RUN_ID`, not a `new_run_id()` value. It is stamped but
not sortable against the others.

## 2. Warehouse and panel (L2–L3)

| artefact | size | stamped | emitter | measures | status |
| --- | --- | --- | --- | --- | --- |
| `warehouse_report.json` | 0 KB | yes | `warehouse.schema` | DuckDB star-schema build | current |
| `panel_report.json` | 6 KB | yes | `warehouse.panel` | the 1,081,312-row ZCTA×year panel, pilot facility frame | current |
| `panel_report_national.json` | 6 KB | yes | `warehouse.panel --facility-frame national` | same panel, national target | current |
| `panel_report_expanded.json` | 6 KB | yes | `warehouse.panel --facility-frame expanded` | same panel, expanded target | current |
| `national_panel.json` | 3 KB | **emitter only** | `warehouse.national --frame national` | 104 rows in `national_facilities.csv` | current |
| `national_panel_expanded.json` | 4 KB | **emitter only** | `warehouse.national --frame expanded` | 693 rows in `national_facilities_expanded.csv` | current |
| `mwpvl_merge.json` | 14 KB | yes | `warehouse.mwpvl_merge` | the merge: 1,904 rows in, 635 delivery stations used, 589 added, panel 104 → 693 | current |
| `catchment_band.json` | 13 KB | **emitter only** | `warehouse.catchment_band` | catchment radius sensitivity | current |
| `batch_candidates.json` | 30 KB | **emitter only** | `warehouse.batch_candidates` | 135 unlabelled delivery stations for hand review | current |
| `scope.json` | 1 KB | yes | `report.scope` | the declared scope of the run | current |

**All three `panel_report*.json` report `rows: 1081312`.** That is correct and
not a copy: the panel is ZCTA×year and the facility frame sets only the
target column. Read them for their `target` blocks, not their row counts.

## 3. Models and analysis (L4–L5)

| artefact | size | stamped | emitter | measures | status |
| --- | --- | --- | --- | --- | --- |
| `choice_report.json` | 14 KB | **emitter only** | `models.choice_runner` | the production conditional logit: 94 decisions, 56 fit / 38 held out | current |
| `hazard_report.json` | 20 KB | yes | `models.runner` | discrete-time hazard on the 40,358-row risk set | current |
| `gbm_benchmark.json` | 9 KB | yes | `models.gbm_benchmark` | MODEL_SPEC §9.4 atheoretical benchmark, 50 re-splits | current, **one block not quotable — see §6** |
| `leakage_test.json` | 3 KB | yes | `models.leakage_test` | warehousing-covariate ablation | current, **see §5c** |
| `leakage_decisive.json` | 7 KB | **emitter only** | `models.leakage_decisive` | the 29-decision OSHA-bounded intersection test | current |
| `refit_expanded.json` | 2 KB | yes | `models.refit_expanded` | original vs expanded panel, same code and seed | current |
| `panel_experiments.json` | 183 KB | **emitter only, and still unstamped after its 2026-09-15 re-run** | `models.panel_experiments` | five panel arms, stratified + standardised lift, 50 re-splits | current — see §5a |
| `covariate_search.json` | 157 KB | yes, but **one `run_id` reused across writes and `written_at` stamped at the FIRST write** | `models.covariate_search` | nested covariate selection inside the training fold, on its own frame (`core`: 477 decisions, 191 held out; `anchor`: 483/193; `permits`: 376/150), 687 facilities at every stage | current — re-run completed 2026-09-15, all five stages `ran_this_invocation`. Verify with `facilities: 687`, **not** with the stamp |
| `percapita_search.json` | 61 KB | **emitter only** | `models.percapita_search` | eight count columns as rates over the numeraire | **RETIRED** — moved to `experiments/percapita-logrel/artefacts/`; on the superseded 694-facility / 479-decision frame (baseline 6.3889), not comparable to `covariate_search`'s 6.2157. Will not be re-run |
| `logrel_search.json` | 85 KB | **emitter only** | `models.logrel_search` | log-relative specification arms, 41 repeats | **RETIRED** — moved to `experiments/percapita-logrel/artefacts/`; same superseded frame, and **no longer reproducible** against `choice.py`'s positivity guard, which raises on five of its ten arms |
| `logrel_gate.json` | 2.1 MB | **emitter only** | `models.logrel_search --stages gate` | the gate stage's full per-arm output | **absent from `outputs/metrics/` as of 2026-09-15** |
| `gravity_network.json` | 111 KB | yes | `models.gravity_network` | 13 network-proximity gravity arms, 483 decisions | current |
| `network_inference.json` | 46 KB | yes | `models.network_inference` | sandwich + cluster-bootstrap inference on the network arms, 483 decisions | current |
| `white_space.json` | 289 KB | **emitter only** | `analysis.white_space` | uncovered-ZCTA search over 1,286 real facilities | current |
| `lift_by_market_size.json` | 7 KB | no, and cannot be | **none** | pooled + stratified top-10 lift, one split | **SUPERSEDED — §6** |

## 4. Cost and optimisation

| artefact | size | stamped | emitter | measures | status |
| --- | --- | --- | --- | --- | --- |
| `cost_report.json` | 1 KB | yes | `cost.runner` | Daganzo cost-to-serve, per scenario | current |
| `portfolio_report.json` | 1 KB | yes | `optimize.runner` | the $2 bn portfolio selection | current |
| `montecarlo_report.json` | 1 KB | **emitter only** | `optimize.montecarlo` | 500 draws over the portfolio, 0 failed | current |
| `viz_report.json` | 2 KB | yes | `viz.build` | which figures were built from which artefacts | current |

## 5. Known cross-artefact disagreements

### 5a. RESOLVED 2026-09-15 — the two-generation split is closed

The MWPVL OCR was re-run on 2026-09-15, which changed
`national_facilities_expanded.csv`. For part of that day three artefacts
described the same named file at the old size. **They have all since been
re-run and every artefact below is now on the same generation:**

```
                              rows in file   buildings   decisions fitted
  CURRENT                             693         687                483
    mwpvl_merge.json  panel_rows_after 693
    national_panel_expanded.json  rows_in_file 693, buildings 687
    refit_expanded.json  arms.expanded_658  facilities 687, n_decisions 483
    panel_experiments.json  arms.combined.rows 687, n_decisions 483
    network_inference.json  arms.*.provenance.rows 687, n_decisions 483
    gravity_network.json    arms.*.n_decisions 483

  RETIRED (do not quote)              700         694                485
```

The 700 / 694 / 485 triple is the superseded generation. It survives in
documents, not in artefacts: nothing under `outputs/metrics/` reports it any
more. The correct full sentence is **483 decisions on 687 buildings from 693
rows**, and 691 — the count of distinct address+ZIP pairs in the CSV — is a
fourth number that is not "buildings".

`gravity_network.json` and `network_inference.json` now carry `run_id`s
(`20260915-210603-b780` and `20260915-210640-dbcd`).
**`panel_experiments.json` still does not**, so it is datable only by file
mtime and nothing inside it says which generation it describes. That is the
remaining cost of an unstamped emitter.

The standardised top-10 lifts this pass quotes from `panel_experiments.json`
are **2.868 (`original_only`) → 2.740 (`combined`)**; the 2.858 → 2.706 pair
that used to sit here came from the retired `lift_by_market_size.json` and
must not be quoted forward. They are cited by **field path** —
`arms.<arm>.methods.conditional_logit.standardised.top10.lift` — precisely so
that a re-run refreshes them rather than contradicting a frozen number, and
the arm must always be named.

### 5b. Two artefacts measure the same lift by different methods, on purpose

`panel_experiments.json` and the superseded `lift_by_market_size.json` cut the
data into the same three market-size strata (`models/panel_strata.BUCKETS`),
and report **different lifts**. That difference is declared, not accidental:

* `lift_by_market_size.json` used `choice.evaluate`'s empirical uniform null,
  which ranks a constant score and lets `np.argsort` break every tie by row
  order — so "uniform top-10" degenerates into "is the chosen ZCTA among the
  first ten rows of the frame".
* `panel_experiments.json` uses the analytic chance rate `min(k, J) / J`,
  which has no tie-break, and averages over 50 re-splits rather than one.

Neither corrects the other; the second replaces the first. Same for
`mwpvl_coverage.json` (a direct two-list floor) against `nlrb_coverage.json`
(a modelled capture–recapture estimate) — different questions, both valid,
and each file says so in its own text.

### 5c. `leakage_test.json` compares arms on different decision counts

`arms.with_warehousing.n_decisions` is 94 and
`arms.without_warehousing.n_decisions` is 100. `leakage_decisive.json`
reports the same asymmetry
(`n_decisions_osha_bound_unrestricted: 94`,
`n_decisions_no_covariate_unrestricted: 100`) and resolves it by fitting both
arms on the 29-decision intersection instead. The `leakage_test` pair is a
6-decision difference in the denominators of a paired comparison. **This was
not investigated in this pass** and is the one item below flagged as
unverified: it may be the intended consequence of the CBP-vintage rule
dropping decisions only when the covariate is present, or it may be a
comparison on non-identical choice sets. Read `leakage_decisive.json`, which
controls for it explicitly.

## 6. Superseded and not-to-be-quoted

### `lift_by_market_size.json` — SUPERSEDED, do not cite

Superseded by `outputs/metrics/panel_experiments.json`. The pointer, the
reasoning and an independent verification of both are inside the file under
`superseded_by`, `superseded_because` and `retirement_verified`.

**Why it was retired rather than given an emitter.** An emitter was
considered. It could not have reproduced the file: `models/panel_strata.py`
already owns the logic, and its analytic null yields different lifts, so a
new emitter would have published a *third* set of numbers for one quantity.
`panel_experiments.json` reproduced the file's decision counts exactly when
that check was made — `original_only` 7 / 41 / 46 and `combined` 66 / 162 /
257, checked against `n_decisions × size_mix` on 2026-09-15 — though the
`combined` arm has since moved to **65 / 160 / 258** on the 483-decision
panel, so the reconciliation no longer holds and the retired file can no
longer be tied to the current one decision-for-decision. It measures the same
thing at 50
re-splits, with an `informative` flag that marks the 7-decision small stratum
as too thin to compare, and with direct standardisation to a common market
mix, which is the operation the Simpson's-paradox claim actually needs.

**Its `finding` string was always wrong.** It reads "Pooled lift fell
3.68x→2.61x" while the fields beside it read 2.948 → 2.757. The
Simpson's-paradox conclusion it was cited for is correct and survives; the
two pooled figures do not. The like-for-like replacement is the standardised
top-10 lift in `panel_experiments.json`, **2.868 (`original_only`) → 2.740
(`combined`)**; the retired file's own 2.858 → 2.706 pair belongs to it and
must not be quoted forward. That wrong prose had been copied verbatim into
`models/panel_strata.py`'s docstring, which is now corrected.

### `gbm_benchmark.json` → `headline_split` — do not quote the GBM rows

The block is retained and its figures are unchanged; a warning now sits
beside it in the artefact (`headline_split_warning`) and in `caveats`.

Measured 2026-09-15: multiplying the attraction matrix by
`1 + 1e-12 × standard normal` — below the precision of any input, about what
a parquet float round-trip costs — moves the GBM top-10 **on this single
split** by up to 2 of 38 decisions over three perturbation draws
(`deep/300 shares` 20 → 19, 22, 18; `deep/300 levels` 18 → 17, 20, 19; the
four shallow arms by 1). `conditional_logit` (19) and `raw_count` (20) do not
move in any draw.

`across_repeats` is the block to quote. Over the same three draws its
`top10_mean` moves by at most 0.48 of a decision on a mean near 22, and the
ordering that carries the module's verdict is unchanged in every draw. Note
that `raw_count`'s own `top10_mean` moved 0.5 in one draw, so `across_repeats`
is stable to about half a decision rather than exactly.

**The obvious fix does not work.** `LGBMRanker(deterministic=True,
force_row_wise=True)` was tested against all six GBM arms and returned
bit-identical counts to the plain call in all eight comparisons — base, a
repeat of base, and three perturbations. At `n_jobs=1` the fit was already
reproducible on identical input; what moves is LightGBM's histogram binning
under a change in the **data**, which no determinism flag touches. The flags
were therefore **not** added: they would have cost a re-emit of published
numbers and bought a false sense of a fix.

## 7. Stamping: 25 of 42

Recounted 2026-09-15 against `outputs/metrics/*.json`.

Stamped on disk (25): `acquire_report`, `cost_report`, `covariate_search`,
`external_check`, `gbm_benchmark`, `gravity_network`, `hazard_report`,
`hazard_revival`, `leakage_test`, `metro_entry`, `mwpvl_extraction`,
`mwpvl_merge`, `mwpvl_validation`, `network_inference`,
`normalise_external_report`,
`normalise_report`, `panel_report`, `panel_report_expanded`,
`panel_report_national`, `portfolio_report`, `refit_expanded`, `scope`,
`source_probe`, `viz_report`, `warehouse_report`.

Unstamped on disk (17). Twelve of them were migrated to
`common/log_json.write_json` on 2026-09-15 and will carry a stamp when next
re-run: `catchment_band`, `choice_report`, `highway_access`,
`leakage_decisive`, `mwpvl_coverage`,
`montecarlo_report`, `nlrb_coverage`,
`nlrb_only_cities`, `panel_experiments`, `percapita_search`, `subsidies`,
`white_space`.

The migration has since paid off for three of them — `covariate_search`,
`gravity_network` and `network_inference` were re-run and now carry stamps.
**`panel_experiments` is the exception worth knowing about:** it was also
re-run on 2026-09-15 and still carries no `run_id`, so the single most-quoted
artefact in this project is datable only by file mtime.

Still unmigrated, deliberately:

* `national_panel.json`, `national_panel_expanded.json`,
  `batch_candidates.json` — `json.dump(fh)` on an open handle rather than
  `write_text`, so the swap is not the same one-line edit. Left for the next
  person to touch those modules.
* `logrel_search.json`, `logrel_gate.json` — written through
  `logrel_runner.save`, which also writes the checkpoint; the routing split
  went in first (§8) and the stamp should follow it.
* `lift_by_market_size.json` — has no emitter and is superseded. It will
  never carry a stamp, and that is now recorded inside the file.

**One cost of the migration, stated rather than discovered later.**
`write_json` passes `default=str` to `json.dump`; the raw `json.dumps(...)`
calls it replaced did not. A payload value that is not JSON-serialisable —
a `numpy.float32` or a `numpy.int64`, neither of which subclasses a Python
type — used to raise at write time and will now be written as a **string**.
That is the convention every already-stamped emitter has always had, so the
migration makes the directory consistent rather than introducing a new
hazard, but it is a real loosening. `models/refit_expanded.py` has a test
against exactly this (`test_the_artefact_is_json_serialisable_end_to_end`);
the fourteen migrated emitters do not, and should get one.

## 8. Checkpoints are not results

> **Note, 2026-09-15.** Neither checkpoint file described below is in
> `outputs/metrics/` any more, and `outputs/scratch/` does not exist. The
> section is left as the record of why they were tolerated; the disposal
> itself is not documented anywhere and is not reconstructed here.

`percapita_repeats.json` (2.3 MB) and `logrel_repeats.json` (6.7 MB) are
per-split resume dumps — 9 MB of intermediate fits sitting in the directory
that the "cite the artefact" rule makes quotable. Their own emitters say so:
`logrel_runner.CHECKPOINT`'s comment reads *"Not the deliverable; the
deliverable is ARTEFACT."* Their deliverables are `percapita_search.json` and
`logrel_search.json`, which sit beside them.

`paths.SCRATCH` (`outputs/scratch/`) was added on 2026-09-15 and both
emitters now write new checkpoints there. **The two existing files were not
moved.** `paths.checkpoint()` prefers an existing file under
`outputs/metrics/`, so relocating the directory cannot silently discard a
half-finished search and restart a run that takes hours. Both searches have
completed — their search artefacts exist and are newer — so these two
checkpoints are spent and can be deleted or moved by hand at any time. They
are left in place because deleting an artefact is not a thing this pass does.

## 9. What still cannot be trusted

1. ~~**`panel_experiments.json`, `network_inference.json`,
   `gravity_network.json`** — stale against the current expanded panel.~~
   **RESOLVED 2026-09-15 (§5a).** All three were re-run and all three now read
   the 693-row / 687-building / 483-decision panel. Two of them gained a
   `run_id` in the process; `panel_experiments.json` did not, so it remains
   datable only by mtime.
2. **`leakage_test.json`'s two arms** — 94 vs 100 decisions (§5c). Not
   investigated. Use `leakage_decisive.json`, which fits on the intersection.
3. **`gbm_benchmark.json`'s `headline_split` GBM rows** — quotable only as an
   illustration, never as a measurement (§6).
4. **`source_probe.json`'s `run_id`** — hand-set, not sortable.
5. **Anything in this directory dated before the 2026-09-15 MWPVL re-run that
   reads the expanded panel.** Seventeen files still carry no stamp, so
   for those the only evidence of vintage is the filesystem mtime, which any
   copy destroys.
