# ADR 0001 — Model observable service enablement, not order volume

- **Status:** accepted
- **Date:** 2026-09-08
- **Deciders:** P1 / P2 / P3

## Context

The natural target is order volume per ZCTA. It is not observable outside the
operator, so it would have to be constructed — typically by allocating
disclosed aggregate volume across areas in proportion to demographics and
retail density.

A model of demographics and retail density would then be fitted to predict it.
The target would be built from its own predictors: any fit statistic would
measure how well the model reproduces our own allocation arithmetic, and a
*good* score would be evidence of the defect.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Constructed volume | Direct dollar interpretation | Circular; unscoreable; a good result is a bug |
| Buy a volume proxy | Closer to truth | Licensed, breaks reproducibility, out of budget |
| **Observable enablement + timing** | Scoreable; enables a real backtest | No direct dollar figure |

## Decision

The primary estimand is: **for each ZCTA and quarter, did the operator offer
same-day service, and in which quarter did they first do so.** The volume model
survives as a clearly-labelled specification-recovery exercise.

## Consequences

- An out-of-time backtest becomes possible: train ≤2023, predict 2024–25.
- Evaluation moves to AUC, PR-AUC, Brier, ECE, precision@k and conformal
  coverage. MAPE is dropped as undefined on zero-inflated counts.
- The facility panel becomes the target variable, so its quality is now
  first-order: 100-facility verification plus a label-noise simulation.
- Dollar NPV is reported in units of contribution margin with break-even
  thresholds rather than as an asserted figure.

## Residual risk

Facility open dates carry an error rate. We publish the measured rate and bound
its effect on AUC by simulation rather than hoping it is small.

## Update — 2026-09-13, after the panel was delivered

The decision stands and is unchanged. Two of its *consequences* did not
survive contact with the data, and are recorded here rather than silently
edited above.

- **"100-facility verification" is not possible.** The delivered panel is
  **43 buildings**, so there are not 100 facilities to verify. It was
  replaced by a census — every row carries its source — plus a direct
  measurement of how loose the date is: five addresses appear in both
  MWPVL's 2012 census and the OSHA extract, the bound held 5 of 5, and the
  lag between opening and first inspection was 4, 13, 57, 69 and 345 months.
- **"Error rate" was the wrong frame.** Most dates are not wrong openings;
  they are **"operating by" upper bounds** from OSHA inspection records. The
  model therefore consumes an interval `(panel start, X]` rather than an
  event time, which is a censoring problem rather than a noise problem. That
  strengthens the case for the observable estimand — a hazard model handles
  censoring natively — while weakening any claim about *when* a ZIP was
  enabled, as opposed to *whether*.

The backtest this ADR made possible is real but thin: 2 facilities fall in
the 2024–25 prediction window. Quote the event count beside the metric.
See [`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md).

## Update — 2026-09-14: three planned consequences were never executed

The decision stands. This update exists because the "Consequences" section
above reads as a description of what was done, and three of its items were
never done. They are recorded here rather than quietly dropped.

- **precision@k and PR-AUC were never computed.** The consequences list names
  six evaluation measures. AUC, Brier, ECE and conformal coverage were all
  computed and are in `../../experiments/hazard-model/artefacts/hazard_report.json`. PR-AUC and
  precision@k are not, on the hazard model or on its successor. An earlier
  draft of `../career/PORTFOLIO_PLAYBOOK.md` quoted a "precision@100 of 0.61"
  as a CV bullet; that number was never measured by anybody and has been
  removed from that file.
- **The label-noise simulation was never built.** Both the consequences list
  ("plus a label-noise simulation") and the residual risk ("bound its effect
  on AUC by simulation rather than hoping it is small") promise it. Nothing in
  `src/` performs it. The residual risk is therefore still open and unbounded,
  not mitigated. The 2026-09-13 update above reframed the date problem as
  censoring rather than noise, which changes what the simulation should be but
  does not discharge the obligation to run one.
- **The "100-facility verification" was already retired** by the 2026-09-13
  update, on the grounds that the panel held only 43 buildings. Note that the
  national frame delivered since is 104 rows and 100 buildings, so the
  arithmetic objection no longer holds — but the verification still has not
  been run, and 0 of those 104 rows carry a coordinate
  (`../../experiments/superseded-artefacts/national_panel.json`).

A separate labelling programme has since hand-labelled 362 sites over six
batches with a quote and a URL apiece. It was not designed as the verification
this ADR asked for, and 289 of the 362 rows turned out to be already
classified, but the 122 non-new rows function as an accidental validation set
for the name-based classifier in `ingest/osha.py`. That is the closest thing to
the promised verification that exists, and it should be labelled as accidental
rather than presented as the plan having been carried out.
