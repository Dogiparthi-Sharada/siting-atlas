# tests — 49 files, all of them unit tests

The suite is deliberately independent of `data/`: every fixture is built in
`tmp_path`, so a green run means the tests test the code and not the
developer's cache. CI proves that by pointing `SITING_ATLAS_ROOT` at an
empty directory.

**Start here:** `unit/conftest.py`. It is 127 lines and it explains the
mechanism the whole suite rests on — `common.paths` resolves its constants
at import time and every module reads them as attributes at call time, so
patching the attributes relocates an entire layer onto `tmp_path`.

```
  .venv/bin/python -m pytest -q
  make test                        # the same, with coverage
```

**660 tests across 49 files**, re-derived on 2026-09-15 with
`pytest --collect-only -q`. Quote that command, not this line: the count has
moved every time the tree has.

---

## Directories

```
  dir           state
  ------------  ---------------------------------------------------
  unit/         49 test files plus conftest.py. The whole suite
  integration/  EMPTY. No files, not even a .gitkeep, so it will
                not survive a clone. Dead directory
  fixtures/     EMPTY, same. Fixtures are built in tmp_path by
                conftest.py instead. Dead directory
```

`tests/__init__.py` and `tests/unit/__init__.py` are both empty and exist
only to make the tree a package.

**Eleven test files are not here any more.** They went to
`experiments/retired-tests/` with the code they protected, when the hazard
model, the conformal machinery, the portfolio optimiser and the agent were
taken out of `src/`:

```
  test_hazard.py        test_risk_set.py       test_timebasis.py
  test_conformal.py     test_real_panel.py     test_optimize.py
  test_gates.py         test_agent_runner.py   test_montecarlo.py
  test_donor_pool_parsing.py                   test_warehouse_view.py
```

They are archived evidence, not a suite. `pytest` does not collect them —
`testpaths = ["tests"]` in `pyproject.toml` — and they are not expected to
pass against the current `src/`. See
[`../experiments/README.md`](../experiments/README.md).

---

## unit/ — what each file protects

The common thread: almost every test here guards a failure that produces a
NUMBER rather than an error. That is why the docstrings are long.

### The pipeline plumbing

```
  file                          protects
  ----------------------------  -----------------------------------------
  conftest.py                   the throwaway data root every test uses
  test_common_paths_config.py   the filesystem layout and .env loading. A
                                wrong root writes artefacts where nobody
                                looks; a leaked key is only noticed by
                                whoever finds it
  test_common_context.py        run id and layer/stage propagation. A line
                                attributed to L1 that came from L3 sends a
                                post-mortem to the wrong module
  test_common_db.py             that sql.jsonl is COMPLETE - including the
                                failing statement, which is the one you
                                most need and lose exactly when the
                                pipeline breaks
  test_db_param_redaction.py    that sql.jsonl is SAFE. A credential must
                                not reach it through a bind parameter
  test_http_redaction.py        a regression test for a real incident: a
                                live EIA_API_KEY in three log files at
                                once, via a requests exception message
  test_common_shell.py          the same for commands.jsonl
  test_seeds.py                 seeds come from the manifest, and a
                                missing one fails loudly
  test_metros.py                the pilot metro crosswalk, against the
                                specific near-misses the real data makes
  test_geo_keys.py              Connecticut abolished its counties in
                                2022. EJScreen carries the new planning
                                regions, the pinned crosswalk carries the
                                retired ones, and the LEFT JOIN that
                                matched nothing for all 288 CT ZCTAs
                                raised nothing either
```

### Ingest and warehouse

```
  file                          protects
  ----------------------------  -----------------------------------------
  test_normalise_zeropad.py     L1's non-negotiable rule: '01890' read as
                                an integer is 1890, and 1890 joins to
                                nothing. New England and Puerto Rico
                                simply vanish
  test_normalise_permits.py     the Building Permits Survey, whose three
                                silent failures each destroy the
                                year-on-year feature rather than the row
                                count
  test_panel_grain.py           the panel's grain, and the YoY join that
                                can fabricate a +100% spike in exactly the
                                counties where the data is worst
  test_warehouse_optional.py    optional sources: skip loudly, never
                                guess. The bls_wages override exists
                                because a title-based join matched 325 of
                                708 metros and raised nothing
  test_flag_gate.py             the build gate that stops a quality flag
                                being silently dropped between the
                                computation and the panel. It failed on
                                the code as it stood, naming three flags
  test_facilities.py            the facility panel to `enabled` target
                                conversion - written BEFORE the real CSV
                                existed, deliberately
  test_facility_quarter_flag.py the Q1 convention made visible. 19 of 43
                                rows have no open_quarter, which puts
                                35.47% of fitted events in Q1 against 25%
                                expected. Split out of test_facilities.py
                                when that file crossed 300 lines
  test_censoring_flags.py       ACS interval-censoring codes. A top-coded
                                median read as a point estimate says a
                                place earns $250,001; read correctly it
                                says "at least that"
  test_edits.py                 the DECLARED edit set - Fellegi & Holt's
                                starting point - and the cross-source
                                edit that reads OSHA. Before this the
                                project had one edit and it was implicit
  test_address.py               address standardisation, on real values
                                from the 516-address OSHA extract
  test_linkage.py               the matcher must collapse the same
                                building and SPLIT different ones. A
                                spurious row shows up in a count; a wrong
                                merge deletes a real facility silently
  test_facility_dedup.py        the three pairs that score 1.000 and
                                DISAGREE about the opening date by 10, 6
                                and 3 quarters. DATA_QUALITY.md F4 named
                                this as "the test that would fail is not
                                written"; this is that test
  test_national_panel.py        what the edit unblocks: a 100-building,
                                62-CBSA frame that stayed out of the
                                warehouse while the model was fitted on 43
  test_nlrb.py                  city normalisation (the only join key this
                                source has), the capture-recapture
                                estimator, and the coverage ceiling it
                                computes
```

### The MWPVL OCR pipeline

Seven files, because the pipeline is seven stages and each one fails by
writing a plausible number rather than by raising.

```
  file                          protects
  ----------------------------  -----------------------------------------
  test_mwpvl_grid.py            grid recovery from OCR word boxes. Six
                                columns reported as one, a house number
                                promoted to a row anchor, a word
                                deduplicated twice - none raises
  test_mwpvl_fields.py          column identity measured from CONTENT.
                                Five of the thirteen tables shift every
                                field one to the right, and a
                                mis-identified column reads square footage
                                out of the date column
  test_mwpvl_geo.py             every row gets exactly one `geo_status`,
                                so unplaceable postcodes add up to the
                                total instead of looking like successes
  test_mwpvl_shape.py           schema drift. If the expanded frame and
                                the 104-row frame differ by one column,
                                pd.concat fills it with NaN and the panel
                                ships with half its rows short
  test_mwpvl_panel.py           the OCR'd dates validated against OSHA -
                                and a MISSING OSHA extract must not read
                                as a pass
  test_mwpvl_merge.py           the two duplicate screens. 362 rows went
                                out for labelling and 289 were already
                                classified, because the worklist was
                                screened on an exact address key
  test_mwpvl_tables.py          the entry point end to end. The bug class
                                is not "it crashed", it is "it wrote a
                                file, printed a total, and the total was
                                wrong"
  test_batch_candidates.py      what the hand-labelled batches actually
                                add, and on what terms
```

### The models

```
  file                          protects
  ----------------------------  -----------------------------------------
  test_choice.py                the two properties that DEFINE the
                                conditional ZCTA-choice model: aggregation
                                invariance, which is the whole reason for
                                the ln(beta'a) form, and scale invariance,
                                which is why one coefficient is fixed
  test_choice_inference.py      the four ways uncertainty lies quietly - a
                                bootstrap resampling the wrong unit, a
                                sandwich computed at a boundary, an
                                unseeded draw, a mislabelled one-sided
                                interval. Each produces output that looks
                                exactly like output
  test_refit_expanded.py        that the two-panel refit reports RATES,
                                not counts - the panels hold different
                                numbers of held-out decisions - and labels
                                every interval with what it is
  test_covariate_search.py      that every arm is a COLUMN SUBSET OF ONE
                                FRAME. Reorder the rows or let a
                                non-numeraire column lead and the arms are
                                scored on different data
  test_leakage_test.py          the PAIRED ablation on the warehousing
                                covariate: same 50 re-splits, same seeds,
                                one arm with and one without
  test_gbm_benchmark.py         the atheoretical benchmark of
                                MODEL_SPEC.md §9.4. The softmax turning
                                ranker scores into probabilities must not
                                reorder anything, or the Brier score and
                                the top-k table stop describing the same
                                model
  test_metrics.py               AUC, Brier and calibration against
                                hand-computed values. The tie case is the
                                one that matters
  test_truthy.py                pd.Series(["false"]).astype(bool) is
                                [True]. That one line is the whole file
  test_conformal_report.py      that the number describing the coverage
                                guarantee can survive being written down
                                and read back
```

### Cost, depots and figures

```
  file                          protects
  ----------------------------  -----------------------------------------
  test_cost_daganzo_math.py     the 1/sqrt(density) exponent, pinned
                                analytically. Get it wrong and every
                                number is still finite, positive and
                                plausibly ordered - and the ranking is
                                wrong
  test_cost_evaluate.py         the parcel-versus-stop distinction, and
                                the degenerate inputs the real panel
                                contains
  test_cost_params.py           the parameter set cannot drift after a run
                                starts, and the run record lists every
                                field
  test_cost_runner.py           the pilot slice. A ZCTA falling out of the
                                crosswalk does not raise, it just shifts
                                the headline median
  test_depots_pmedian.py        depot placement must optimise the
                                objective the cost model BILLS. k-means
                                minimises squared distance and converges
                                on the mean; line haul is linear in
                                distance and wants the median
  test_depots_network.py        what DepotNetwork promises its callers -
                                daganzo.linehaul_miles is the only one -
                                and what it deliberately does NOT promise,
                                which is per-depot capacity feasibility
  test_viz.py                   that a chart is produced, survives
                                degenerate frames, and that the
                                text-overflow audit does real work
  test_viz_regressions.py       four defects an audit found, each with the
                                reason written down so the next person
                                does not delete it as redundant
  test_dashboard.py             the two things that only exist inside the
                                app: figure lifetime, and what a tile
                                claims a number means
```

---

## Conventions worth knowing

`xfail_strict = true` in `pyproject.toml`. Each xfail documents a specific
defect, so an unexpected PASS fails the suite — a note must not outlive its
bug. There are seven, in five files: `test_common_shell.py`,
`test_common_db.py`, `test_common_paths_config.py`, `test_cost_evaluate.py`
and `test_panel_grain.py`.

Coverage is not in `addopts` on purpose: it costs about 20% on every run and
interferes with `pdb`. Use `make test` when you want it.

`addopts = "-q --strict-markers"` is already set, so passing `-q` again gives
you `-qq` and suppresses the collected-count summary line. Use
`-o addopts=""` when you want the total.

Nothing in this tree is generated. `tests/unit/__pycache__` is build output
and is gitignored.
