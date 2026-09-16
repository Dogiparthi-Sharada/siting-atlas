# ADR 0003 — Free, public, re-downloadable sources only

- **Status:** accepted
- **Date:** 2026-09-08
- **Deciders:** P1 / P2 / P3

## Context

Better data exists behind paywalls — mobility panels, licensed foot traffic,
commercial property databases. Using any of them would improve the model and
destroy the contribution.

## Decision

Every source must be **free, public, and re-downloadable by a stranger**. Where
a better paid source exists, we take the public one and report the cost of that
choice.

Concretely, this replaced a rate-limited commercial business directory with
Census County Business Patterns: bulk download instead of three days of
polling, no API key, and an administrative universe rather than a self-selected
one — which also removes a documented coverage bias against minority-owned,
cash-heavy and informal businesses.

## Consequences

- A third party can reproduce every number.
- The reproducibility story has no "obtain a licence" step.
- Accuracy is bounded by what public data can support — which is itself
  RQ4, not a defect.
- Compute and data cost is $0; the whole budget is model inference.

## Residual risk

The public-data accuracy ceiling may be below what the decision requires. If
so, we report that as a finding about opacity rather than suppressing it.

## Update — 2026-09-14: the residual risk has been realised

**It is no longer a risk. It has been observed, three times, by three
independent routes.** This ADR promised to report that as a finding rather than
suppress it, so here it is, stated as a result:

- **The fitted model is matched by a raw covariate.** The conditional ZCTA
  choice model, 94 decisions and three free parameters, was scored on 38
  held-out decisions against single-covariate rules. The raw count of
  warehousing establishments, with nothing estimated at all, gets 8 of 38 at
  top-1 against the fitted model's 7, and 20 of 38 at top-10 against 19. Two of
  the three free parameters sat at the boundary. On public data, the estimation
  buys nothing measurable over simply counting warehouses.

  > **Corrected 2026-09-14.** This bullet used to be headed *"The fitted model
  > is **beaten** by a raw covariate"*. It is now *matched*. The numbers in the
  > bullet have not changed and are correct — but they come from one seeded
  > 56/38 split, and the word "beaten" turned a one-hit gap into a verdict.
  > Fifty paired re-splits of the same 94 decisions put the raw count ahead by
  > **0.36 hits of 38 (paired sd 1.14)**, and it *loses* 11 of those 50 splits
  > (`../../outputs/metrics/gbm_benchmark.json`, `across_repeats`). So this
  > moved because the claim was **wrong** — noise read as signal — not because
  > the evidence moved on. What does not change is the point this ADR is making
  > with it: on public data, three estimated parameters buy no ranking
  > improvement over counting warehouses, and the accuracy ceiling this ADR
  > flagged as a residual risk has still been hit.
- **Satellite dating failed a logical-possibility test.** An attempt on
  2026-09-14 to recover construction dates from Sentinel-2 imagery returned an
  estimate for all 107 sites from a median of 106 cloud-free scenes. On the 83
  with a known year, 41% were within one year. But **39 of 107, 36%, date
  construction to after the day an OSHA inspector recorded the building
  operating** — a median of 33 months after. The confidence score does not
  discriminate between the possible and the impossible answers. The fault is in
  the changepoint detector, not the imagery, which means better public imagery
  would not fix it.
- **SEC filings disclose nothing usable.** They carry no facility locations and
  no facility dates. The disclosure regime simply does not require what this
  project needs.

Together these say something sharper than the original risk statement. It is
not that public data is noisy; it is that **the specific quantity this project
needs — where and when a private operator decided to build — is not disclosed
by anybody, and the public proxies for it carry most of their signal in a
single count variable.** That is the finding about opacity this ADR committed
to reporting, and it is a result rather than a defect in the work.

The decision itself is unchanged and is if anything strengthened: a paid
mobility panel would have produced a better fit and would have destroyed the
ability to say the above.

## Update — 2026-09-14: "a third party can reproduce every number" is overstated

The first consequence above should be read as an aspiration with three known
holes, not a statement of fact:

- **The satellite step is a manual Colab run.** It is not in the pipeline, not
  under test, and its source file `satellite_dates.csv` sits outside this
  repository altogether.
- **The labelling batches are LLM-classified CSVs.** A stranger re-running them
  would not get identical output, and the batch generator compared against the
  wrong reference, so 289 of 362 rows were already-classified duplicates.
- **Nothing is geocoded.** 0 of 104 facility rows carry a coordinate, so every
  distance covariate falls back to a ZCTA centroid.

The accurate claim is narrower and still worth making: every source is free and
re-downloadable, the DuckDB build runs cold from one command, and the numbers
in the metrics artefacts are reproducible from it. The manual and LLM-assisted
steps at the edges are not.
