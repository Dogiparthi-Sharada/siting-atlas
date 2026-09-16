# Experiments

Five lines of work that were built, run, and then taken out of the main
codebase. They are kept here rather than deleted because each one answered a
question, and the answer is worth more than the code.

Nothing in this directory is imported by `src/siting_atlas`. Removing the
whole folder would not change a single result in `outputs/`. It is archived
evidence, not a dependency.

**Numbers here are as recorded at retirement.** `docs/NUMBERS.md` is the
current source of truth for anything quoted elsewhere.

---

## What is in here

| Directory | The question it asked | What came back |
|---|---|---|
| [`hazard-model/`](hazard-model/) | Will a station open in this ZIP this quarter? | A constant predicted better. Retired twice, the second time on 6.7× the data |
| [`gravity-network/`](gravity-network/) | Is the *whole* network's pull a better covariate than distance to the nearest facility? | A better measurement that does not predict better, and it costs the model its theoretical justification |
| [`percapita-logrel/`](percapita-logrel/) | Do per-household and log-relative transforms rescue the covariates? | No — and one of them broke the estimator in a way worth reading about |
| [`portfolio-optimiser/`](portfolio-optimiser/) | Given a budget, which set of sites should an operator build? | Works, but it optimises against a prediction the project could not validate |
| [`agent-demo/`](agent-demo/) | Can the analysis be driven by an LLM agent with gates? | A working demo; not part of the research result |
| [`superseded-artefacts/`](superseded-artefacts/) | — | Results computed on the 104-facility pilot panel, before the expansion |

Each directory holds `code/`, the `artefacts/` it produced, and where one
exists, the `notes/` written at the time.

---

## hazard-model

**The idea.** Treat each ZIP-quarter as a survival problem: has the event
happened yet, and what is the hazard that it happens now? Standard technique,
same mathematics as "will this patient relapse".

**Why it was retired.** Not because it scored badly — because it broke an
assumption that no amount of tuning repairs. When one station opens, it
switches on a median of **39 ZCTAs** in the data. The model treats those as 39
independent observations. They are one decision counted 39 times, so the
standard errors mean nothing. No radius between 8.3 and 45 miles brings that
below 14.

**The revival, and why it matters.** The obvious objection to the first
retirement was that it had only 812 events. So it was rebuilt on **5,441**
events with real opening dates recovered from the extraction — 6.7× the data.

```
  AUC            0.6894  ->  0.6832
  calibration    beaten by a constant in 17 of 17 comparisons
```

More data did not help, which is the point. A defect in the unit of analysis
is not a sample-size problem.

**Evidence:** `artefacts/hazard_report.json`, `artefacts/hazard_revival.json`,
`notes/NOTES_HAZARD_REVIVAL.md`

---

## gravity-network

**The idea.** Instead of "distance to the nearest sortation centre", use the
summed pull of every facility, each discounted by distance — a gravity model.
Better physics, and it uses information the nearest-neighbour measure throws
away.

**It won on measurement.** It is the only specification whose coefficients
never hit the boundary of the parameter space across 50 re-samples. Offered
both variables at once, the model **keeps gravity and discards
nearest-distance**. As a measurement of network pull, it is clearly better.

**It lost on prediction, and the comparison is not one number.**

```
  large-metro top-10 lift          no network   6.2585
                                   proximity    6.2903
                                   gravity      6.2187
```

Gravity loses at top-10 — but wins at top-1 and top-5. **Do not quote a single
scalar from this experiment**; the ranking depends on *k*, and reporting only
the top-10 figure was how it was first misread.

**What it costs.** The model's justification requires that merging two ZIPs
adds their attractions. Counts do that; distances and gravity pulls do not.
The specification still runs, but the argument for its shape does not survive.

**Evidence:** `artefacts/gravity_network.json`,
`artefacts/network_inference.json`, `notes/NOTES_GRAVITY_NETWORK.md`

---

## percapita-logrel

**The idea.** Two reframings of the same suspicion — that the covariates fail
because of scale, not content. Divide by households; or express each ZIP
relative to its metro's mean, in logs.

**What happened.** Neither predicted better. The log-relative arm is the more
interesting failure: because the model constrains coefficients positive via
`β = exp(θ)`, log-relative columns let the optimiser buy likelihood by pushing
non-chosen alternatives below zero probability. It reported a *better*
objective at a point that was **20–77× past the feasibility ceiling**.

That bug is now guarded against in `src/siting_atlas/models/choice.py`, which
raises if any fitted utility is non-positive. **The experiment is retired; the
guard it produced is live.**

**Evidence:** `artefacts/percapita_search.json`,
`artefacts/logrel_search.json`, `notes/`

*The per-replicate dumps from these two arms (11 MB of bootstrap draws) were
deleted rather than archived. The summaries carry the findings.*

---

## portfolio-optimiser

**The idea.** Given a capital budget, choose the set of sites that maximises
return — a selection problem on top of the cost model, with a Monte Carlo over
parameter uncertainty.

**Why it is here rather than in the repo.** It works. The reason it is
archived is honesty about what it sits on: it optimises against a *predicted*
value per site, and the prediction never beat its baseline. A tool that
confidently ranks portfolios built from a ranking that does not work is a way
to launder uncertainty into a decision.

The cost model underneath it stays in the main repo, but note what that does
and does not mean. It is a published method with sourced parameters, stress-
tested across five scenarios spanning −17.1% to +4.4% on the median — **it is
not validated against Amazon's realised costs, because nobody publishes
them.** No delivery-cost model built from public data can be. See
`docs/ALTERNATIVES.md`.

**Evidence:** `artefacts/portfolio_report.json`,
`artefacts/montecarlo_report.json`

---

## agent-demo

An LLM-driven analysis loop with data gates and inference gates. Interesting
engineering, unrelated to the research question, and it produced no result the
project relies on.

---

## superseded-artefacts

Results computed on the **104-facility pilot panel**, before the extraction
expanded it to 693. They are kept so that any claim traceable to the pilot era
can be checked against what was actually run at the time.

They are **not** wrong — they are answers to the same questions asked of a
smaller sample. Where a current artefact exists, it supersedes these.

---

## Running any of this again

The code here is archived, not maintained. Its imports point at
`siting_atlas.*` modules that have since moved or changed, so expect to fix
paths before anything runs. The artefacts are the reliable record.
