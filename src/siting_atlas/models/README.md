# models — the discrete-time hazard, and the record of its failure

L4. This package fits the model that answers "given a ZCTA was not served
at the start of this quarter, does it become served during it". It was
built, it was fitted on real data, and **it failed**. Read that sentence
before you read anything else here: this is not working machinery whose
results you can quote, it is a component whose headline result is a
documented negative finding.

**Start here:** `__init__.py` — it carries the intended reading order and
the warning about the target. Then `risk_set.py`, because the trap it
prevents is silent and biases every coefficient. Then
`docs/METHODS_RESEARCH.md` §14.1-§14.2 for what the failure was and why.

---

## The failure, in the numbers the code emitted

```
                         model      null (a constant)
  AUC                    0.6894     0.5000
  Brier skill           +0.00471     0.0000
  calibration (ECE)      0.00863     0.00005   <-- WORSE than a constant
  temporal hold-out     -0.02091
  geographic hold-out   -0.06184
  events per parameter      7.6     floor 10.0
```

Source artefact: `outputs/metrics/hazard_report.json`. The diagnosis is a
unit-of-analysis error — one delivery station switches on a median of 58
ZCTAs at once, so 812 "events" came from 104 decisions plus a circle — not
a sample-size problem. The replacement specification, a conditional
ZIP-choice model, is **not yet built**.

## Files

```
  file                  purpose                                  state
  --------------------  ---------------------------------------  ------
  __init__.py           package overview and the reading order.  current
                        Says the panel is real now and that
                        diagnostics.py must be read first
  base.py               the Model ABC. evaluate() is            works
                        implemented ONCE here in terms of
                        predict(), so a comparison between
                        specifications is not secretly a
                        comparison of scoring code. Also
                        BaselineOnly, the null model
  risk_set.py           dense ZCTA-quarter panel -> risk set.    works,
                        A unit leaves the sample after its       one gap
                        event and not one row later. READ
                        FIRST. Interval censoring is NOT
                        implemented here - see below
  timebasis.py          the baseline hazard in quarters:         works
                        per-quarter dummies or a restricted
                        cubic spline. Spline is the library
                        default; the real panel resolves to
                        a single linear trend instead
  hazard.py             DiscreteTimeHazard, complementary       works,
                        log-log link. The specification that     result
                        failed. cloglog because beta is then     FAILED
                        a log hazard ratio that does not
                        depend on how finely time was bucketed
  metrics.py            AUC, Brier, calibration curve and ECE,   works
                        from first principles. Three metrics
                        because each is blind to a different
                        failure; the rare-event binning is
                        not scikit-learn's default
  conformal.py          split conformal prediction. The one      works
                        guarantee that does not need the model
                        to be right - coverage holds for a
                        deliberately terrible model, it just
                        pays in wider sets
  conformal_report.py   what a conformal run writes into the     works
                        metrics file. Separate from the method
                        because an infinite q_hat is the
                        honest answer and `Infinity` is not
                        valid JSON
  coeftable.py          reports fitted coefficients in raw       works
                        units rather than standardised ones,
                        pushing the covariance through the
                        SAME matrix as the coefficients
  splits.py             train / calibration / test, split by     works
                        UNIT not by row, plus split_by_time
                        for the temporal question
  diagnostics.py        counting only - what the panel will      works
                        NOT support, measured. Independent
                        episodes, events per parameter, events
                        by metro, event timing, the OSHA
                        contamination note
  sensitivities.py      three PRE-REGISTERED refits: annual      works
                        grain, temporal hold-out, held-out
                        metros. Declared before the primary
                        model was scored, on purpose
  panel_source.py       decides whether a run is allowed to      works
                        call its panel real, and cuts the
                        national panel down to the metros a
                        fit may see. "Real" means at least one
                        observed enablement, not "file exists"
  fixtures.py           SYNTHETIC panel with a DGP we chose.     works
                        SYN-00001 ids and SYNTHETIC_ artefact
                        names so a fixture result can never be
                        mistaken for data
  truthy.py             parses the `enabled` column out of       works
                        whatever a CSV hands over. Raises on
                        an unrecognised token, because
                        pd.Series(["false"]).astype(bool) is
                        [True]
  console.py            the terminal report, in reading order.   works
                        The power block prints BEFORE the
                        performance table, deliberately
  runner.py             the CLI. `python -m                      works,
                        siting_atlas.models.runner`              stale
                                                                 comment
```

## Do not trust

```
  runner.py:64-66   STALE COMMENT. resolve_baseline()'s docstring says the
                    real panel has "SIX distinct event times, all of them
                    Q1 because open_quarter was never collected". The
                    artefact it produced disagrees:
                    hazard_report.json event_timing records 17 distinct
                    event times, spread across all four quarters of the
                    year (Q1 288, Q2 155, Q3 176, Q4 193 - Q1 is 35% of
                    events, not 100%). The Q1 pile-up was real once and is
                    no longer total. The CODE is unaffected - it returns
                    "linear" for the real panel either way - but the stated
                    REASON is out of date. Flagged here, not fixed.

  risk_set.py       Interval censoring is not implemented. Most facility
                    dates are OSHA inspection dates, which are "operating
                    by" UPPER BOUNDS with measured lags of 4, 13, 57, 69
                    and 345 months. They are right-hand endpoints of a
                    censoring interval, not event times. Every figure that
                    depends on WHEN an event happened inherits that, which
                    is why the temporal split is reported as secondary.

  any AUC quoted    monotone-invariant, so it cannot see the calibration
  from this         failure that actually sank the model. Quote Brier skill
  package           and ECE alongside it or the number misleads.

  transfer_smoke_   Phoenix and Boise hold two dated delivery stations
  test              between them. It is a check for gross failure, not a
                    test of geographic transfer.
```

## Producing the artefacts

```
  python -m siting_atlas.models.runner
  python -m siting_atlas.models.runner --baseline dummies --alpha 0.05
  python -m siting_atlas.models.runner --synthetic     # force the fixture
```

Writes `outputs/metrics/hazard_report.json` and
`outputs/tables/hazard_predictions.parquet`. Both are GENERATED — a hand
edit is lost on the next run. A synthetic run writes the same files under a
`SYNTHETIC_` prefix with `"synthetic": true` inside.
