# The original proposal, read cold — what it had, what we kept, what we lost

*Written 2026-09-13. A fresh-eyes review of
`prime-expansion-twin_essentials.zip`, the ancestor of this project, against
the repository as it stands at commit `c76da04`.*

> **Moving target, recorded rather than papered over.** While this review was
> being written HEAD advanced to `9dc91ba`, "Batch 1 labelled: 33 delivery
> stations". Everything below was verified against `c76da04`; the one
> recommendation the new commit touches is §5.3, which has been updated in
> place and marked. Nothing else in the review is affected — but see §8.1,
> which is about exactly this failure mode and has now demonstrated itself on
> the document describing it.

Files read in full: 44 documents (17 `.md`, 27 `.txt`) plus all 52 `.py` files
under `src/` and `tests/`, the three `infra/` manifests, both CI workflows,
`seeds.toml`, `pyproject.toml` and the three `requirements*.txt`. The other
46 `.py` files are document builders (`scripts/build_*.py`,
`scripts/*_content.py`, `Audit/*/build_*.py`, 860 KB between them) and were
sampled, not read line by line; they contain prose, not method. The 48 `.png`,
5 `.pptx`, 8 `.docx` and 1 `.pdf` are renderings of text read elsewhere.

Extracted to a scratch directory for reading; the persistent copy cited
throughout is
`MSBA_Project/prime-expansion-twin/prime-expansion-twin/`.

Every claim below about the CURRENT repository was checked against the
repository, not against anybody's summary of it. Section 8 lists the places
where the summary I was given turned out to be wrong.

---

## Contents

```
  7  The verdict — does this help us?          the question that was asked
  3  The algorithm ledger                      the substance
  4  Dropped by decision, or dropped by drift
  5  What to take back, ranked
  1  Inventory
  2  What the original proposed
  6  What we have that the original did not
  8  Corrections to the current repo, found on the way
```

Sections are numbered for reading order and written in order of value. Read 7
first; it is the answer.

---

## 7. The verdict — does this help us?

**Mostly superseded. Take three things, and one of those three is worth more
than everything else in the archive combined.**

The long answer has four parts, and the order matters.

### 7.1 As a method source, the original is behind us, and not narrowly

The original named a great many methods and **implemented none of them**.
Counted directly: `models/zinb.py`, `models/synthetic_control.py`,
`models/cost_osrm.py` and `models/npv_montecarlo.py` between them contain
**eleven `raise NotImplementedError`** and not one fitted model. The whole
package is 3,133 lines including docstrings and `__init__.py` files; the four
"algorithms" are 439 lines of which roughly two thirds are commentary. The
tests assert that constructors construct.

So the comparison is not "their model versus our model". It is **their
docstring versus our artefact**. We have a hazard model that was fitted and
failed with the failure measured, a conditional choice model fitted on 94
decisions, conformal sets with verified coverage, a p-median depot solve
bounded 0.89% above a Lagrangean lower bound, and three capture-recapture
estimators. They have a plan for a ZINB.

Where the two overlap on method, we are usually also **more correct**. The
original's ZINB-on-ZCTA-weeks is the pseudo-replication error we already
diagnosed and retired, one layer deeper: it would have fitted 2,200 ZCTAs
times 60 months as independent draws from what are, at most, a few dozen
siting decisions plus a van radius. Its Huff gravity covariate is intensive
and would have broken the aggregation invariance that `MODEL_SPEC.md` §1
establishes as binding. Its headline metric was MAPE, which ADR-0001 already
dropped as undefined on zero-inflated counts.

**Reading the archive for methods to adopt is therefore mostly wasted time.**
That is the honest headline and the user should hear it plainly.

### 7.2 But it is not empty, and the three things it has are not small

```
  1  MONTE CARLO UNCERTAINTY PROPAGATION.  Designed in full, never built.
     We do not have it either, and we have a live credibility problem that
     it and only it would close: the portfolio headline has moved three
     times (317 -> 330 -> 282 activations) and nobody can say whether any
     of those moves is inside the noise.  docs/TODO.md already carries the
     row -- "needs a distribution over the parameters, not point values" --
     so this is not a new idea, it is an old idea with a finished design
     sitting in the archive.  No new data.

  2  THE SECOND ESTIMAND, WITH AN OUTCOME WE ACTUALLY HAVE.  The original's
     spatial DiD + synthetic control was aimed at CANNIBALISATION, whose
     outcome is order volume, which is unobservable, and we were right to
     leave it.  But the panel already carries `home_value` on 74.9% of
     1,081,312 rows across 26,262 ZCTAs and 32 quarters -- and it VARIES
     within all 26,262 of them, 77.7% of the 33,791 ZCTAs in the panel.
     `permit_units_total` (65.4%) and the two EJScreen equity columns
     (99.95%) are there too, and `enabled` marks 1,257 treated ZCTAs.
     Swap the outcome from Amazon's P&L to the public's and the machinery
     the original designed becomes runnable on data we hold today.
     NOT on pm25 -- see the correction below.

>   **Corrected 2026-09-14, evening. This item used to list `pm25 (98.6%)`
>   beside `home_value` as an outcome the second estimand could use. That
>   was WRONG, and it was wrong in the most expensive way a data claim can
>   be: the coverage is real and the variance is zero.** Measured on
>   `data/processed/panel.parquet`: `pm25` has **0 of 33,791 ZCTAs carrying
>   more than one distinct value across the 32 quarters**. It is one
>   cross-section repeated 32 times. A before/after design on a constant
>   has no before and no after, whatever its coverage. The same is true of
>   `median_home_value` (0 varying), `diesel_pm` (0) and
>   `traffic_proximity` (0). The only outcome column in the file that
>   actually moves through time is `home_value` (ZHVI), which varies in
>   **26,262 ZCTAs**. Quoting a coverage percentage as evidence that a
>   longitudinal design is feasible is the specific error this review was
>   written to catch, and this review committed it.
>   [`../ALTERNATIVES.md`](../ALTERNATIVES.md) §D.1 has the measurement.

  3  THE LLM EXTRACTION PIPELINE AS AN INGEST PATH.  We built the six gates
     and never built the thing they gate.  Unlabelled OSHA buildings sit in
     data/collection/prompts/ waiting for a human to paste them into a chat
     window; one batch of 70 was done by hand at commit 9dc91ba and took
     the panel from 100 buildings to 132, cutting single-facility metros
     from 43 of 62 to 36 of 65.  292 remain.  models/accessibility.py says
     in its own docstring that exactly this is what would make the
     line-haul covariate testable, and the first batch has now shown it.
```

Behind those three there is a fourth, smaller and duller: the original shipped
a `Dockerfile`, a `docker-compose.yml` with an OSRM sidecar, a `cloudrun.yaml`,
exact version pins with `--only-binary=:all:`, and a **scheduled** CI job that
re-runs the pipeline weekly and opens an issue on drift. We have a Streamlit
dashboard, `>=` version ranges, no container, no deploy target, and a CI
workflow with no `schedule:` trigger. That is a real reproducibility gap and it
is cheap to close.

### 7.3 The most valuable thing in the archive is not a method at all

It is **the failure mode**, recorded contemporaneously by the project's own
author, and it is the same failure mode this project has had twice since.

`AGENT_HANDOFF_2026-09-06.md` §0 opens: *"all of the AI-agent time on this
project went into proposal DOCX iteration + VS Code custom-agent building.
Zero code shipped to `src/` or `tests/` during that window."* Twelve days.
The archive contains **46 document-builder Python files totalling 860 KB**
against 3,133 lines of package source. Four proposal versions, a council
deliberation, a defence-prep pack, a walkthrough deck, an algorithms
glossary, an OSCAR pitch — and eleven `NotImplementedError`.

The handbook-to-artefact ratio in the current repository is better but it is
not good: `docs/` holds 84 markdown files against 105 source modules, and
`docs/defense/HANDBOOK_03_CAUSAL.md` is 700-odd lines of teaching about a
method whose status banner says *"NOT ONE LINE OF ANY OF IT EXISTS IN
src/."* That banner is honest and it is also the archive's ghost. The
original died of documentation. Reading it is worth an hour for that reason
alone, and the hour should be spent on the handoff note, not the glossary.

### 7.4 Did we lose anything important?

**One thing, and it is a label, not a method.**

Proposal v5 named querying the operator's own ZIP availability page as the
*preferred* source for the enablement target. The repository derives
enablement instead from a 15-mile disk drawn around an OSHA-dated building —
which is the precise geometry that destroyed the hazard model's independence
assumption. `docs/data/FACILITY_PANEL_PROVENANCE.md` §18 records five failed
attempts at sourcing dates, but all five were attempts to build a *facility*
panel. A direct service check is a different object, it is not in that list,
and no ADR or decision-log entry records it being tried or rejected. It
would give the target at ZIP grain with no catchment geometry at all.

It has a hard limitation that must be stated in the same breath: it returns a
**current cross-section**, not a history, so it cannot date anything. It
therefore cannot rescue the timing factor. What it can do is supply an
independent check on the catchment assumption — measure how far the 15-mile
disk disagrees with reality — and that is a measurement, which is this
project's established currency.

Everything else that went missing went missing for a reason somebody wrote
down. Section 4 separates the two cases and finds three genuine drifts, all
minor next to this one.

### 7.5 The one-sentence answer

> *"Read the handoff note and take three things — Monte Carlo uncertainty,
> the second estimand pointed at an outcome we can observe, and the
> extraction pipeline for the 292 buildings still unlabelled. Leave the rest. The
> archive's method stack is a list of intentions and we are past it; its
> real lesson is that the project it belonged to wrote sixty document
> builders and eleven `NotImplementedError`."*

---

## 3. The algorithm ledger

Every method the original names or implies, whether it adopted it, rejected it
or parked it as future work. Status is against the repository at `c76da04`.

```
  YES          we do this, and it runs
  PARTLY       some of it runs, or it runs on a narrower object
  SUPERSEDED   we deliberately do something else, with a reason on record
  NO           we do not do this
```

A note on how to read the original's side. **"Adopted" in the original means
"named in a proposal and given a docstring".** Nothing in the original's
`models/` was ever fitted; the eleven `NotImplementedError` are listed in §7.1.
So the evidence column for the original is a file path and a promise, and the
evidence column for us is a file path and an artefact. That asymmetry is the
review's main finding and it is not editorialising to state it once here.

### 3.1 Demand and specification

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| Zero-inflated negative binomial (ZINB) | ZCTA-week order counts with structural zeros and overdispersion | NO | original `models/zinb.py:83` raises; ours: `docs/ROADMAP.md:190` unticked, no statsmodels ZINB anywhere in `src/` | Correctly not done. ADR-0001 replaced constructed volume with observable enablement, so the count outcome the ZINB needs does not exist. `HANDBOOK_04_MODELS.md:360` also records that the zero-inflation story does not survive: our zeros are one mechanism, not two |
| Zero-inflated Poisson | fallback if the NB dispersion parameter is indistinguishable from zero | NO | original `DESIGN_DECISIONS.txt` D-08 "what would make us reconsider" | Moot with the outcome gone |
| Poisson regression | count baseline | NO (rejected by both) | original D-08 "ignores overdispersion" | Agreed |
| Plain negative binomial | count baseline | NO (rejected by both) | original D-08: treats structural zeros as random, "over-predicts rural ZIPs by 2-10x" | Agreed |
| Hurdle model | two-part alternative to zero inflation | NO (rejected by original) | `04_algorithms_glossary.md:71` "harder to fit, less standard" | A weak reason, but moot |
| OLS on counts | naive baseline | NO (rejected by both) | original: "would predict negative order counts" | Agreed |
| **Conditional / multinomial logit over zonal alternatives** | which ZCTA gets the station, given one opens | **YES — and the original rejected it for a reason that was wrong** | ours: `src/siting_atlas/models/choice.py`, fitted, `outputs/metrics/choice_report.json` 94 decisions. Original: `04_algorithms_glossary.md:118-119` rejects "multinomial logit choice model" and "random utility discrete choice" because both "require customer-level data we do not have" | **The single most important row in this table.** The rejection mistook the decision maker. The chooser is the firm siting one building, not a consumer picking a store, so no customer-level data is needed — one row per opening suffices. Our whole current specification is the thing the original crossed off. See §4.1 |
| `V = ln(beta'a)` with extensive attraction variables | zone-merger invariance for arbitrary Census boundaries | YES | `models/choice.py:20-34`, pinned by an aggregation-invariance test | Not in the original at all. Train §3.4 Ex.2 |
| Heckman two-step with inverse Mills ratio | correct selection bias in which ZIPs Amazon picked | NO | original: `plan.md` §2 `[O2]`, formal on SF Bay only, never coded. Ours: `docs/ROADMAP.md:189` unticked, `docs/TODO.md:529` "now feasible, none of them well-powered" | Deferred on both sides. `PROPOSAL_V5.md:49` withdraws the v4 claim that it was done. Our instrument would be no better than theirs |
| Instrumental variable: km to nearest USPS-classified commercial ZIP centroid | the exclusion restriction for the Heckman first stage | NO | original `04_algorithms_glossary.md:83` | We hold no USPS commercial-ZIP classification. `HANDBOOK_03_CAUSAL.md:153` calls our own candidate instrument "contestable" |
| Propensity score matching | alternative selection correction | NO (rejected by original) | `04_algorithms_glossary.md:93` "adds a separate ML model to defend" | Agreed by omission |
| Control function for endogeneity | Train §13.4 two-step residual-in-utility | NO | `docs/PLAN.md` §6 item 6; `MODEL_SPEC.md` §10.2 declines it | Declined with arithmetic: it costs a `lambda` plus a first stage on a sample that cannot afford three parameters, and we have no instrument |
| BLP / random-coefficients demand | market-share demand estimation | NO | `docs/READING_LIST.md` §3; `MODEL_SPEC.md` §10.3 quotes Train p.334 verbatim | Settled and correct. Zero observed shares for most alternatives, and no prices or transactions anywhere in the data |
| Nested logit over metros | relax IIA; the natural two-level shape for our own factorisation | NO | `MODEL_SPEC.md` §10.5 | Declined on parameter count, recorded as the first extension if the panel grows. Not in the original |
| Mixed logit | heterogeneous coefficients | NO | `MODEL_SPEC.md` §8.3 forbids it | Not in the original |
| Discrete-time cloglog hazard | when does a ZIP switch on | SUPERSEDED | `src/siting_atlas/models/hazard.py`, fitted and retired; `docs/adr/0004-model-change-conditional-choice.md` | **Not in the original at all** — introduced by the assistant in v4, per ADR-0004 provenance note. It failed, and the failure is the project's spine |
| Huff gravity pull factor, beta fixed at 2 | competitor-aware trade-area draw as a covariate | NO | original `04_algorithms_glossary.md:98`, `plan.md` §2. Ours: `HANDBOOK_04_MODELS.md:405` and `GLOSSARY.md:250` describe it; nothing in `src/` computes it; no ROADMAP or TODO row | Drift on our side — see §4.2. But it could not enter `ln(beta'a)` unmodified: a gravity share is intensive |
| Reilly's law of retail gravitation | two-store precursor to Huff | NO (rejected by original) | `04_algorithms_glossary.md:117` "too primitive" | Agreed |
| Line-haul marginal-gain covariate | position relative to unserved demand, from the existing network | PARTLY | `src/siting_atlas/models/accessibility.py`, built, tested, **off by default** | Ours, not theirs, and the closest thing we have to Huff's intent. Coefficient pinned at the positivity boundary; the docstring is explicit that the test was underpowered (65 of 100 facilities are the first in their metro) rather than that the effect is absent |
| Warehousing establishment count, NAICS 493, lagged vintage | the binding physical constraint on siting | YES | `src/siting_atlas/ingest/cbp_detail.py`; took held-out top-10 from 30% to 50% | Not in the original. The original's nearest equivalent is Yelp retail density, which measures the wrong industry |
| Industrial land area from OSM | "empty but zoned", which a count cannot express | PARTLY | `src/siting_atlas/ingest/osm_landuse.py`, verified on 3 CBSAs, 62-metro run blocked on Overpass 504 | Not in the original |

### 3.2 Causal identification

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| Synthetic control, donor weights by convex QP | build a counterfactual for a treated unit from a weighted average of donors | NO | original `models/synthetic_control.py:81` raises (cvxpy never even installed — no cp314 wheel, `LESSONS_LEARNT.txt` 2026-08-24). Ours: `HANDBOOK_03_CAUSAL.md:11` status banner, "not one line of any of it exists in `src/`" | **The project's declared second estimand, and the largest single thing neither side has built.** Documented, not drifted. See §5.2 for the argument that it is now runnable against a different outcome |
| Spatial difference-in-differences | isolate an opening's effect from everything else changing | NO | same banner | As above |
| Placebo / in-space and in-time inference | is the estimated effect distinguishable from noise | NO | original `synthetic_control.py:107` raises; ours `HANDBOOK_03_CAUSAL.md` §3.6, illustrative arithmetic only | Nothing to infer about yet |
| Plain DiD | simpler causal baseline | NO (rejected by original) | `DESIGN_DECISIONS.txt` D-09: parallel trends "not credibly satisfied" | Agreed |
| Regression discontinuity at the service boundary | sharp-boundary identification | NO (rejected by original) | D-09: "requires a boundary Amazon does not publish" | Agreed, and still true |
| Event study | fixed-effects alternative | NO (rejected by original) | D-09: same parallel-trends problem | Agreed |
| Matrix completion for causal panels | named as the thing that would supersede synthetic control | NO | D-09 "what would make us reconsider" | Neither side pursued it. Worth one line of a literature review, no more |
| Causal forests (Wager & Athey) | heterogeneous treatment effects | NO (future work both sides) | original `04_algorithms_glossary.md:94`; ours `docs/PLAN.md` §4 note | Agreed as out of scope |
| DoubleML | modern causal ML | NO (future work both sides) | original `plan.md` §2 deep-learning row | Agreed |
| Revealed-preference moment inequalities (Holmes 2011; Houde, Newberry & Seim 2023) | set-identify siting parameters by swapping opening dates | NO, with a written argument | `docs/PLAN.md` §6; ADR-0004 option C | **Not in the original** — we found and rejected it ourselves. The identifying variation is the dates we measure worst; Holmes §8.3 says the estimator is inconsistent under exactly our error |
| Interval-outcome partial identification (Molinari §2.3) | bounds rather than a point, from censored dates | NO | ADR-0004 option D, "kept open, unfunded" | Not in the original. Still the best-matched estimator to the data we hold |
| Mutable spatial weight matrix `W` | let an agent update the adjacency the estimator uses | PARTLY | original Innovation #2; ours `agent/gates_inference.py` gate 5 protects a donor pool | We built the guard rail, not the road. See §4.3 |
| Interval censoring in the risk set | treat OSHA dates as upper bounds, which they are | NO | `docs/PLAN.md` §7, `models/risk_set.py` | Open defect on our side, absent from the original entirely (the original assumed dates from MWPVL) |

### 3.3 Routing, facility location and cost

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| OSRM routing in Docker | real drive times on the OSM network | SUPERSEDED | original `models/cost_osrm.py:77` raises; `infra/docker-compose.yml` has the sidecar. Ours: `docs/adr/0002-routing-offline.md`, accepted | Reasoned, not drifted: OSRM needs ~30 GB retained for ten metros. We precompute offline per metro, delete the artefacts, ship ten parquet files. The original's economics argument against Google is identical to ours |
| Haversine x circuity as the distance metric | free road-distance approximation | YES | `src/siting_atlas/cost/daganzo.py`; circuity 1.30, derived as L1/L2 on a grid = 4/pi | Original called straight-line "wildly inaccurate" and rejected it. Our sensitivity sweep says `circuity` moves the median $/parcel by 1.2% across 1.15-1.45, so the original's objection is real in principle and negligible in magnitude |
| Google / Mapbox / HERE distance matrix | commercial routing | NO (rejected by both) | original D-12: "~$440 per metro before we do anything interesting" | Agreed |
| Daganzo continuous approximation | total tour distance from area and stop count | YES | `src/siting_atlas/cost/daganzo.py`, with the BHH constant cited to Daganzo (1984) | Both sides adopted it. Ours is fitted and sensitivity-tested; `bhh_constant` moves the headline 0.9% when wrong by half, which is why `READING_LIST.md` §1b downgraded the book |
| p-median facility location | place depots to minimise linear line-haul | YES | `src/siting_atlas/cost/depots.py:91`, greedy add plus all-improving-swap interchange, bounded 0.89% above a Lagrangean lower bound | **Not in the original**, which had no depot model at all. Klose & Drexl (2005) |
| k-means depot placement | the thing p-median replaced | SUPERSEDED | `docs/WHERE_WE_ARE.md` §3 | Ours, and retired for a stated reason: k-means minimises squared distance and we bill linear distance |
| Capacitated p-median | respect a per-depot throughput cap | NO | `docs/PLAN.md` §7, first open defect | Open and known: 42% of depots exceed 40,000 parcels/day, heaviest 3.56x, so line haul is a lower bound biased optimistic in exactly the dense ZCTAs at the top of the ranking |
| Hakimi node restriction | licence for putting depots only at demand nodes | NO | `docs/research/NOTES_hakimi_1964.md` | Read, and found **not** to license what we claimed: Hakimi (1964) proves the 1-median case on a graph, we place 334 in the plane. Replaced by a measured 0.45% cost of the restriction. A good example of the current project's standard |
| Weiszfeld continuous refinement | free depots from node positions | PARTLY | used once to measure the 0.45%, not in the pipeline | Not in the original |
| Eight-bucket cost decomposition | real estate, wages, fuel, vehicles, fitout, hiring, permitting, marketing | PARTLY | original `plan.md` §2 `[G2]`, tiered 4+4, never coded. Ours: `src/siting_atlas/cost/params.py` and `docs/data/PARAMETERS.md` | We have wages (BLS OES), fuel and electricity (EIA), vehicles (van lease), real estate (Zillow, 94.3% missing). We do not have fitout, hiring, permitting or marketing, and the original had no source for them either — its "public-data proxy" column was aspirational. Our sensitivity sweep says the four it lists as *secondary* are not where the headline lives anyway |
| Parameter sensitivity sweep | which constant actually moves the answer | YES | `src/siting_atlas/models/sensitivities.py`, `READING_LIST.md` §1b | Not in the original. It is what told us the routing mathematics is decoration and `service_minutes_per_stop` carries the headline (-25% / +44%) |

### 3.4 Optimisation and uncertainty

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| Monte Carlo NPV, 10,000 draws | propagate joint uncertainty into a per-ZCTA NPV distribution | **NO — and we should** | original `models/npv_montecarlo.py:114` raises, but the design is complete: draw sources, log-normal setup cost, uniform discount rate, P10/P50/P90, `P(NPV>0)`, an `ADD`/`HOLD` rule at 0.85. Ours: `docs/TODO.md:377` **TODO**, "needs a distribution over the parameters, not point values" | **Take this back.** Ranked first in §5.1 |
| Bootstrap confidence intervals over the whole pipeline | how confident are we in P50 itself | NO | original Tier 3, `04_algorithms_glossary.md:212`. Ours: `MODEL_SPEC.md` §6.3 specifies a bootstrap over *decisions*, R=2000 — not implemented | Both unbuilt. Ours is the better-specified version: it resamples decisions, never rows, and reports percentile intervals rather than standard errors |
| Sandwich / robust covariance | standard errors valid under misspecification | NO | `MODEL_SPEC.md` §6.3 prescribes reporting it beside the bootstrap; `choice_report.json` carries no standard errors of any kind | **Real gap.** The fitted choice model publishes point coefficients with no uncertainty at all. Neither original nor current |
| Point-estimate NPV | the thing Monte Carlo replaces | PARTLY (we are still here) | `src/siting_atlas/optimize/objective.py` prices everything at point values | The original rejected this in D-10 and it is what we currently do |
| Delta-method propagation | analytic alternative to Monte Carlo | NO (rejected by original) | D-10: breaks when the demand distribution is far from Gaussian "near zero, exactly where the decision is hardest" | Agreed, and well argued |
| Greedy construction plus 1-for-1 local search | pick a portfolio under a capital budget | YES | `src/siting_atlas/optimize/select.py:35,58,120` | Not in the original. Correctly refuses the submodularity guarantee: cannibalisation makes the objective neither submodular nor supermodular, so the greedy bound does not apply and an optimality *gap* (10.73%) is reported against an upper bound instead |
| Optimality gap against an upper bound | say how far from optimal the portfolio is | YES | `optimize/select.py:155` | Not in the original |
| Margin frontier | how the portfolio moves with the break-even margin | YES | `optimize/select.py:224` | Not in the original |
| Cannibalisation decay, `peak * (1 - exp(-exposure))` | discount overlapping catchments | PARTLY | `src/siting_atlas/optimize/params.py:141`, `cannibalisation_peak = 0.18` | It is **a parameter somebody typed**, with no standard error, no donor pool and no interval, and the docs say so. Holmes Table VIII implies nearer 0.10. This is the hole the second estimand exists to fill |
| Conformal prediction, split / fixed threshold | distribution-free coverage on the binary outcome | YES | `src/siting_atlas/models/conformal.py`; 88.2% empirical against 90% nominal | Not in the original |
| Adaptive prediction sets (APS) | coverage for a choice problem whose sets run 4 to 848 alternatives | YES | `src/siting_atlas/models/choice_conformal.py`; at alpha=0.10, empirical coverage 1.000 on 24 test decisions, median set 38.5 ZIPs = 71.4% of the median 59.5-ZIP choice set | Not in the original, and the clearest example of the current project's habit of converting weakness into a measurement |

### 3.5 Machine learning and benchmarking

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| LightGBM (was XGBoost) as a convergent-validity benchmark | an atheoretical second opinion on the structural model | NO (both sides) | original `plan.md` §7 `[G5]`, LightGBM chosen 2026-09-07, never coded. Ours: `docs/TODO.md:527` TODO with an explicit "Reversal" note commissioning it | Commissioned on our side, not drifted. Note `pyproject.toml` has no lightgbm and no xgboost; we would use `sklearn.ensemble` |
| Single-covariate ranking benchmarks | the bar the fitted model must clear | YES | `outputs/metrics/choice_report.json` `benchmarks_single_covariate` | Ours. And the finding is uncomfortable and correctly reported: **warehousing alone matches the fitted model on held-out data** (top-1 8 vs 7, top-10 20 vs 19 of 38 — one hit, on one split). The estimation buys nothing over ranking ZIPs by their existing warehouse count. Said "beats" until 2026-09-14; see below |
| Uniform-within-choice-set null | the honest "no information" comparator | YES | `models/choice.py:278` | Ours. The original had no null model of any kind |
| SHAP attribution | decompose one prediction into feature contributions | NO | original `04_algorithms_glossary.md:140`, for the drilldown card. Ours: `TODO.md:552` "do not report SHAP values as an account of Amazon's policy" | Correctly demoted. It is a description of a model, not of a firm |
| Spearman rank correlation >= 0.80 between structural and benchmark | convergent validity | NO | original Objective 1 metric | Would come free with the GBM benchmark. Worth adopting as the acceptance criterion when that lands |
| Kendall's tau against the actual expansion sequence | does our ranking recover the order Amazon really built in | NO | original `plan.md` §7 `[C3]`, accepted then dropped. Ours: nowhere | **Drift, and the reason for the drop has expired.** See §4.4 |
| Deep learning: GNN, transformers, small MLP | named as Phase 3 stretch | NO (future work both sides) | original `plan.md` §2 `[G3]` "yes if time permits, do not commit in proposal" | Agreed. At 94 decisions it would be indefensible |
| LoRA fine-tune of Phi-3.5-mini as a local narrator | generate drilldown prose on CPU without per-call LLM spend | NO | original §5.9, Tier 3, Modal $30 GPU | Not worth taking. It is presentation, it needs a GPU budget, and it solves a problem (LLM latency on dashboard load) that we do not have because our dashboard calls no LLM |
| LLM ablation across three frontier models | which model is safest at the mutation-proposal step | NO | original §5.10, Tier 3 | Interesting, and downstream of building an extractor we have not built |
| bge-small-en-v1.5 embedding retrieval for few-shot SQL | ground Text-to-SQL on schema plus retrieved examples | NO | original `mcp_sql.py`, raises | Not needed. We have no Text-to-SQL surface |

> **Corrected 2026-09-14 — this review got the single-covariate verdict wrong,
> and in its own favour as a reviewer.** The row above said **warehousing alone
> *beats* the fitted model on held-out data**, and §8.3 went further: it logged
> the repository's summary claim of "MATCHES" as a *defect*, with "ACTUAL it
> BEATS it". Both are withdrawn. The word is **matches**, and the repository's
> summary was right.
>
> The 8-vs-7 and 20-vs-19 figures are real and stay: they come from
> `choice_report.json`, seed 20260914, one 56/38 split. They are one hit.
> `outputs/metrics/gbm_benchmark.json` (`across_repeats.conditional_logit`)
> re-runs the same 94 decisions over **50 paired re-splits**: the raw count is
> ahead by a mean of **0.36 hits of 38 with a paired sd of 1.14**, and it
> *loses* 11 of the 50 splits and ties 16. Mean top-10 is 20.96 for the count
> against 20.6 for the model. That is a tie.
>
> This is a wrong claim being retracted, not a superseded one being updated.
> The review read a single split as a verdict — the same class of error it
> exists to catch. **What is not retracted is the substance:** the estimation
> buys nothing over ranking ZIPs by their existing warehouse count, and a
> three-parameter model that only draws with a free one-column sort has not
> earned its parameters.

### 3.6 Evaluation metrics

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| Brier score, reported as a raw model-null PAIR | strictly proper scoring | YES | `src/siting_atlas/models/metrics.py`; `models/choice.py:299` | Ours, and grounded: Gneiting & Raftery (2007) §3.1 p.363. The original used no proper score anywhere |
| Brier **skill** score as a headline | normalised readability number | NO, deliberately | `MODEL_SPEC.md` §9.1; §2.3 p.362, skill scores "are generally improper, even if the underlying scoring rule S is proper" | A distinction the original never drew |
| Calibration curve and expected calibration error | are the probabilities honest | YES | `models/metrics.py` | Ours. It is the metric that caught the hazard model: ECE 0.00863 against a constant's 0.00005 |
| AUC / ROC | rank discrimination | PARTLY, demoted | `models/metrics.py` computes it; `MODEL_SPEC.md` §9.3 forbids it as a headline | Ours. The original's whole Objective-1 gate was an AUC target |
| MAPE < 25% on held-out ZCTAs | the original's headline success metric | SUPERSEDED | original Objective 1; ours `docs/adr/0001-observable-estimand.md` | Dropped as undefined on zero-inflated counts, which is correct: MAPE divides by an actual that is zero for most ZCTAs |
| F1 > 0.85 on structural zeros | the original's classification gate | NO | original `plan.md` §2 ranking row | Moot with the ZINB gone |
| Top-k hit rate / "percent correctly predicted" | intuitive accuracy | PARTLY, labelled | `choice_report.json` top1/top5/top10; `MODEL_SPEC.md` §9.3 quotes Train §3.8.1 p.69, "should actually be avoided" | Reported because readers ask, never headlined |
| McFadden's rho-squared | logit goodness of fit | YES | `models/choice.py:287`, 0.1969 | With `MODEL_SPEC.md` §9.3's warning that it is not an R-squared and cannot be compared across samples |
| Precision@k, PR-AUC | rare-event ranking metrics | YES | `models/metrics.py`, `docs/ROADMAP.md` | Not in the original |
| Winkler's standardised score | proper, built for rare events | NO | `docs/WHERE_WE_ARE.md` §3, "cheapest win outstanding", computable without refitting | Ours, identified and unbuilt. Not in the original |
| Equity audit by ZCTA demographic majority | per-stratum error, flagged when a stratum is 50% worse | NO | original `plan.md` §7 `[C5]` including a remediation loop back into the mutator gate. Ours: `docs/ROADMAP.md` unticked | Deferred both sides. We hold EJScreen `low_income_pct` and `people_of_colour_pct` on 99.95% of panel rows, so the data side is solved. See §5.5 |
| MAUP robustness check at H3 grain | does the answer survive a change of spatial unit | NO | `docs/ROADMAP.md`, ADR-0004 residual risk | Ours, unbuilt. Not in the original. It is the named test for whether `ln(beta'a)` was applied carelessly |

### 3.7 Record linkage, data quality and coverage

Nothing in this family appears in the original in any form. It is listed so
the ledger is complete and so §6 can be read against something.

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| Jaro-Winkler string similarity with blocking | match the same building across OSHA, NLRB and OSM | YES | `src/siting_atlas/common/linkage.py:82,121,257,282` | Not in the original |
| Connected-component grouping on strong edges only | resolve transitive match chains without runaway merges | YES | `src/siting_atlas/common/linkage_group.py` | Not in the original |
| Fellegi-Holt declared edit registry | mechanical edits with EXCLUDE / REPORT dispositions | YES | `src/siting_atlas/warehouse/edits.py` | Not in the original. `CORRECT` is deliberately absent because it is the imputation rule FH Criterion 2 abolishes |
| Rahm & Do sentinel registry | one declared list of substitute codes | YES | `src/siting_atlas/common/sentinels.py` | Not in the original |
| Van den Broeck screen / diagnose / treat with a flag gate | a cleaning log that is defensible | YES | `src/siting_atlas/warehouse/flag_gate.py`, plus the uncorrected/corrected cross-tab | Not in the original, whose data-quality story was pandera contracts and a PII denylist |
| pandera schema contracts | column, dtype, nullability and range enforcement at the loader boundary | PARTLY | original `DESIGN_DECISIONS.txt` D-17; ours: typed parquet per source, no pandera dependency | Genuinely theirs. We validate by construction and by test rather than by declared contract. Defensible, but their version is more legible to a reviewer |
| Lincoln-Petersen / Chapman capture-recapture | how much of the population does one list miss | YES | `src/siting_atlas/ingest/nlrb_estimators.py:44`; 630 cities, 54.0% OSHA coverage | Not in the original, which had no notion that its facility list might be incomplete |
| Chao's lower bound under heterogeneous catchability | a tighter ceiling when capture probability varies | YES | `nlrb_estimators.py:59`; 899 cities, 37.8% | Not in the original |
| Three-list log-linear model | **measure** pairwise list dependence instead of assuming it away | YES | `nlrb_estimators.py:140`; OSM supplies a third list whose capture mechanism is unrelated to worker grievance | Not in the original. This is the repository's strongest single contribution and it has no ancestor in the archive |
| Log-normal confidence interval on the unseen count | honest interval on a capture-recapture estimate | YES | `nlrb_estimators.py:81` | Not in the original |
| Listwise deletion under measured not-MCAR | what we currently do, and should not | PARTLY | `cost/runner.py:166`; `rent_index` missing on 94.3% of ZCTAs and the observed stratum is 63.6x denser | Open defect, measured and unfixed. Little & Rubin read, no treatment built |
| Macro / selective editing by influence on key totals | rank records by how much they move the published number | NO | `docs/WHERE_WE_ARE.md` §3, gap 4 | Identified, unbuilt. "No outlier detection of any kind exists" |

### 3.8 LLM and agent layer

| method | what it is for | doing it? | evidence | verdict |
|---|---|---|---|---|
| LangChain ReAct loop | an agent that reasons then calls a tool | NO | original `agent/react_agent.py:?` raises; `prompts/react_system.txt` written. Ours: `pyproject.toml` has langchain under an optional `agent` extra, nothing imports it | Not worth taking. It is an interaction affordance, and our deliverable is an artefact trail, not a chat |
| Three MCP servers | portable tool surface: SQL, visualiser, mutator | NO | original D-06; all three raise | As above |
| Text-to-SQL over a read-only DuckDB handle | let a reviewer ask the warehouse questions | NO | original `mcp_sql.py` raises | Not worth taking |
| **Warehouse_Mutator four-gate pattern** | schema, geocoding, confidence threshold, immutable audit log | **YES, and extended** | original `04_algorithms_glossary.md:264`. Ours: `src/siting_atlas/agent/gates_data.py` implements exactly those four as gates 1-4 | Taken and surpassed. This is the one piece of the original's agent design that survived intact |
| Gates 5-6, inferential integrity | donor-pool contamination; does the write move the estimate past a pre-registered threshold | YES | `src/siting_atlas/agent/gates_inference.py` | **Ours, and the declared contribution.** Gate 5 protects a synthetic-control donor pool that does not exist — see §4.3 |
| Refuse-to-pass when the check cannot run | a gate with nothing to check must not report green | YES | `src/siting_atlas/agent/estimators.py`, `UnavailableThetaEstimator` raises | Ours, and the right instinct: "a gate that cannot run must not report a pass" |
| Human-in-the-loop config flag | require a human click before a write lands | YES | `agent/pipeline.py`, `hitl_required` default `True` | Both sides. Original `[O4]`, resolved 2026-09-07 to default ON |
| Pydantic validation of every LLM output before a write | structural gate on generated JSON | PARTLY | original AGENTS.md §7. Ours: `agent/types.py` dataclasses plus `SchemaGate` | Same intent, different mechanism |
| SHA-256 keyed LLM response cache | deterministic, offline-replayable LLM calls | NO | original `agent/cached_llm_call.py` raises; `secrets/llm_cache.salt.example` | **Worth taking if and only if we build an extractor.** See §5.3 |
| LLM extraction of facility events from press releases | turn unstructured text into warehouse rows | PARTLY, and manually | original Algorithm 6. Ours: `data/collection/prompts/*.txt` — batches generated, pasted into a chat window by hand, results in `data/collection/results/*.csv`; batch 1 of 6 landed at `9dc91ba` | We do this, but as a human clipboard operation with 292 buildings still queued. It demonstrably works (70 answers, zero UNKNOWN, each with a quote and a URL). The original's contribution is the automation, caching and audit trail around it |
| Prompt-injection defences | read-only handle, user text as data, version-pinned system prompts | NO | original ARCHITECTURE.txt §4.4 | No attack surface: we expose no chat |

### 3.9 Engineering and reproducibility

| item | doing it? | evidence | verdict |
|---|---|---|---|
| Seeds in one declared TOML, nothing hardcoded | YES both | original `reproducibility/seeds.toml`; ours `reproducibility/seeds.toml` + `common/seeds.py` | Same discipline, independently arrived at |
| Star schema on DuckDB | YES both | original D-11; ours `warehouse/schema.py`, `panel_sql.py` | Same choice, same reasoning |
| CI: ruff, type check, pytest on every push | YES both | original `.github/workflows/ci.yml`; ours `.github/workflows/ci.yml`, 4 jobs | Ours adds a `smoke` job and a `documents` job that diffs the `.txt` twins |
| **Exact dependency pins with `--only-binary=:all:`** | NO | original `requirements.txt` pins every version; ours `pyproject.toml` uses `>=` throughout with no lockfile | **Real gap.** See §5.6 |
| **`verify_repro.py` plus checked-in expected values** | NO | original `scripts/verify_repro.py` + `reproducibility/expected_manifests/`; ours: neither file exists | **Real gap and probable drift.** See §4.5 |
| **Scheduled drift check with auto-opened issue** | NO | original `.github/workflows/reproducibility.yml`, weekly cron + `create-an-issue`; ours: no `schedule:` trigger anywhere | As above |
| Raw-input manifest with hashes | YES | ours `data/raw/manifest.jsonl` | Original planned `manifest.json`, never generated |
| Per-run structured trace | YES | ours `common/trace.py`, `logs/run-*/`, every artefact stamped with a `run_id` | Not in the original, and it is what lets us say "quote `outputs/` with its run stamp, never a figure typed into prose" |
| Dockerfile and a public deploy target | NO | original `infra/Dockerfile`, `docker-compose.yml`, `cloudrun.yaml`; ours: none | See §5.6 |
| Streamlit dashboard | PARTLY | original `app/main.py` + 3 tab stubs; ours `app/dashboard.py`, real, cost-to-serve only | Ours runs and shares chart functions with the batch figure build so the two cannot disagree. Theirs does not run |
| 400-line file cap | PARTLY both | original AGENTS.md rule 4; ours: `cost/params.py` and several docs modules exceed it | Neither enforces it in CI |
| Pre-commit hooks | YES both | original planned; ours `.pre-commit-config.yaml` | — |

## 4. Dropped by decision, or dropped by drift

The test applied: **can I point at a document that says we are not doing this,
and why?** If yes it is a decision, however much one might disagree with it. If
the idea simply stops appearing, it is drift, and drift is a finding.

The result is more reassuring than expected. Most of the original's method
stack was retired deliberately and in writing — ADR-0001 for the estimand,
ADR-0002 for routing, ADR-0004 for the model class, `READING_LIST.md` §3 for
BLP, `DECISION_LOG.md` §1.7 for MWPVL, and the `HANDBOOK_03_CAUSAL.md` status
banner for the whole causal chapter. That banner in particular is a model of
how to retire something honestly: it keeps the teaching, changes the tense,
and says in a box that not one line exists.

Four genuine drifts, in descending order of consequence.

### 4.1 The conditional logit was crossed off for the wrong reason, and nobody noticed we un-crossed it

Not a drift in the usual sense — the opposite. The original **rejected** the
method we now use, and the rejection is still sitting in the archive:

> "**Multinomial logit choice model:** more sophisticated but requires
> customer-level data we do not have."
> "**Random utility discrete choice:** same problem — needs individual
> customer data."
> — `Audit/2026-09-08_0800_project-explainer/04_algorithms_glossary.md:118-119`

Both sentences assume the decision maker is a **shopper choosing a store**.
That is what Huff and the retail-gravity literature condition you to assume,
and under that reading the objection is correct. But the chooser in a siting
model is **the firm choosing a site**, and there is exactly one of those per
opening. No customer-level data is required, has ever been required, or would
help. One row per building is the whole dataset.

Why this matters beyond bookkeeping: it is direct evidence that **the
project's central specification was available from the first week and was
discarded on a category error**, and that the fourteen months of ZINB,
Heckman, Huff and spatial DiD scaffolding were built around the gap it left.
It also dates the error precisely — the glossary is 2026-09-08, five days
before ADR-0004 adopted the method it dismisses.

This belongs in the viva answer to "why did the method change again". The
current answer (`PLAN.md` §9) is *"I specified a model, built it, tested it,
and it failed"*. It is a better answer with the archive attached: *"and the
specification that replaced it had been rejected in week one, on a mistake
about who the decision maker is."*

### 4.2 Huff gravity — drifted, and the documents still describe it in the present tense

Huff was a locked, unanimous, council-endorsed part of the method stack
(`plan.md` §2 spatial-choice row; `04_algorithms_glossary.md:98`). In this
repository it survives only as **teaching material**: a formula and a
rationale at `docs/defense/HANDBOOK_04_MODELS.md:405`, a definition at
`docs/defense/GLOSSARY.md:250`, and a viva question at
`HANDBOOK_04_MODELS.md:920` ("Why is the Huff beta fixed rather than fitted?").

There is no ROADMAP item, no TODO row, no ADR, and nothing in `src/` computes
a gravity term. Nothing anywhere says we stopped.

**Why it is drift rather than a decision:** `MODEL_SPEC.md` §4.3 does reject
*distance to the nearest existing station*, carefully, on extensivity grounds
— and a Huff share is intensive too, so the same argument disposes of it. But
§4.3 never names Huff, and `HANDBOOK_04` §4.2.4 was not updated when §4.3 was
written. A reader who opens the handbook will be told we compute a Huff
factor. We do not.

**It is also partly answered without being named.** `models/accessibility.py`
is the same idea in an extensive-friendly form — position relative to unserved
demand rather than relative pull — and it was built, tested and switched off
with a measured reason. Nobody connected the two.

Cheapest fix: one paragraph in `HANDBOOK_04` §4.2.4 changing the tense and
pointing at `MODEL_SPEC.md` §4.3 and `accessibility.py`. Not my file to edit.

### 4.3 Gate 5 guards a donor pool that nothing is scheduled to create

`DonorPoolIntegrityGate` is gate 5 of six, and gates 5-6 are stated to be
**the project's contribution** (`agent/gates.py:1-13`: "Gates 1-4 protect DATA
integrity and have extensive prior art. Gates 5-6 protect INFERENTIAL
integrity, and that is the contribution"). Gate 5 exists to stop a warehouse
write from quietly moving a synthetic-control donor into treatment.

There is no synthetic control. There is no donor pool. `HANDBOOK_06_AGENT.md`
§324 says so in terms, so this is **documented, not hidden** — it is not drift
by the test above, and I will not call it that.

What *is* worth flagging is the structural position: the declared contribution
of the project is a safety property of an estimator nobody has scheduled. If
the second estimand is never built, gate 5 is a guard rail beside a road that
was never laid, and a hostile examiner will put it exactly that way. That is a
second, independent reason to take §5.2 seriously.

One live staleness, found while checking: `agent/warehouse_view.py:165-180`
justifies its fallback with "TODAY that column is entirely NULL, because the
facility panel **has not arrived**". The panel has arrived — 1,257 ZCTAs carry
`enabled = True` in `data/processed/panel.parquet`. The fallback behaviour is
still defensible, the stated reason is out of date.

### 4.4 Kendall's tau against the real expansion sequence — drifted, and the objection to it has expired

Council item `[C3]`, proposed by Marchetti, accepted into `plan.md` §7.2 with
a module named for it (`models/ranking_validation.py`), then cut in the v5
compression and never seen again. Nothing in this repository mentions it.

It was cut when the frame was 43 pilot buildings with 44.2% of opening
quarters filled by convention. **Both halves of that have changed.** The
national frame carries 100 buildings across 62 CBSAs with 104 of 104 opening
quarters reported, and the choice model is fitted on 94 of them.

So we can now ask a question we could not ask then: rank each metro's ZCTAs by
the fitted model and test whether that ranking correlates with the order
Amazon actually built in. It is a **held-out evaluation on the time dimension
the choice model deliberately dropped**, it needs no new data, and it is one
of the few checks that would distinguish our model from the warehousing-count
benchmark that currently matches it — because both rank space, and only one of
them has any claim on sequence.

Caveat that must travel with it: the dates are OSHA upper bounds with verified
lags of 4, 13, 57, 69 and 345 months, so the sequence is noisy. A rank
correlation is more robust to that than an event study would be, but the
measured lag distribution belongs in the caption.

### 4.5 `verify_repro.py` and the scheduled drift check — drifted

The original's reproducibility story had three moving parts: a
`verify_repro.py` that re-runs the pipeline and diffs against checked-in
expected values, a weekly cron job that runs it, and an issue template that
gets auto-filed on drift. All three are in the archive
(`scripts/verify_repro.py`, `.github/workflows/reproducibility.yml`,
`.github/ISSUE_TEMPLATE/reproducibility-drift.md`).

We kept `seeds.toml` and dropped the rest. The string `verify_repro` appears
nowhere in `docs/`; there is no expected-values file; `.github/workflows/`
contains one workflow with no `schedule:` trigger. No ADR, no decision-log
entry, no TODO row records the choice.

**And we have the exact failure it was built to catch.** `PLAN.md` §5 says the
optimiser headline "has drifted three times (317 -> 330 -> 282 activations;
$1.268bn -> $1.320bn -> $1.128bn)", the last time because depot placement
changed with nothing in `optimize/` touched. A scheduled diff against expected
values would have caught every one of those on the day it happened rather than
in a document audit weeks later.

Partial mitigation exists and should be credited: the `documents` CI job diffs
the generated `.txt` twins, and `common/trace.py` stamps every artefact with a
`run_id`. That is drift detection for the prose layer. There is none for the
numbers.

### 4.6 Deliberate drops, for the record

Listed so §4 is not read as a list of oversights. Each of these has a document
behind it, and each survives scrutiny:

```
  MWPVL purchase          DECISION_LOG.md 1.7.  Would supply real dates and
                          destroy the contribution; Houde et al. already
                          published the paid-data version in Econometrica.
  BLP and the whole       READING_LIST.md 3.  No prices, no shares, no
  price-index lineage     transactions.  Roughly half the supplied
                          curriculum, correctly skipped.
  OSRM live routing       ADR-0002.  ~30 GB retained for ten metros; the
                          precision was in the wrong place anyway.
  Constructed order       ADR-0001.  Circular and unscoreable: a good
  volume as the outcome   result would have been a bug.
  MAPE as the headline    ADR-0001.  Undefined on zero-inflated counts.
  Moment inequalities     PLAN.md 6, ADR-0004 option C.  Identifying
                          variation is the dates we measure worst.
  The "digital twin"      Original plan.md 0.1 [G4], dropped 2026-09-07,
  claim                   before the rename.  Good call, made early.
  The whole causal        HANDBOOK_03_CAUSAL.md 3.0 status banner.  The
  chapter                 model of how to retire something in writing.
  Yelp retail density     Not documented, but superseded in substance by
                          CBP establishment counts by NAICS, which are
                          free, national, historical and industry-specific.
                          Worth one line somewhere; not worth chasing.
```

## 5. What to take back, ranked

Ranked by expected value, which is not the same as by size. Item 2 is the
largest prize and the most likely to fail; it sits second for that reason and
not because it matters less.

Each entry states the cost, what it buys, and — the question that kills most
good ideas here — what data it needs that we do not have.

### 5.1 Monte Carlo uncertainty propagation

```
  COST     2-3 days.  The draw loop is ~80 lines; the work is choosing and
           sourcing a distribution for each of the ~17 cost parameters.
  BUYS     an answer to the question the project currently cannot answer.
  NEEDS    nothing we do not have.
```

The original designed this in full and never built it
(`models/npv_montecarlo.py`: 10,000 draws, log-normal setup cost, uniform
discount rate, joint sampling across demand, cost and cannibalisation,
returning P10/P50/P90 and `P(NPV>0)` per ZCTA with an `ADD`/`HOLD` rule at
0.85). We have not built it either. `docs/TODO.md:377` carries the row with
the right diagnosis — *"needs a distribution over the parameters, not point
values"* — and `TODO.md:440` adds *"the frontier now varies the margin, but
every other parameter is still a point value"*.

**Why it is first.** The portfolio headline has moved three times — 317, then
330, then 282 activations; $1.268bn, $1.320bn, $1.128bn — and `PLAN.md` §5
notes that **not one of those moves was caused by a parameter change**. The
project's current defence is to refuse to quote the number in prose and point
at the artefact instead. That is honest and it is a workaround. The actual
question is whether 282 and 330 are different answers or the same answer
twice, and only a distribution answers it.

It also converts three existing assets into one: `models/sensitivities.py`
already sweeps each parameter one at a time, `cost/params.py` already
documents plausible ranges for most of them, and `optimize/select.py` already
solves fast enough to run inside a loop. The missing piece is joint sampling.

Two design points worth carrying over from the original and one to reject:

```
  CARRY   Monte Carlo over the fitted-parameter distributions, not a
          bootstrap over raw rows -- D-10's reason is good: only the former
          preserves the correlation between demand and cost.
  CARRY   report the tail, not the mean.  "P50 $4m with 90% above zero"
          and "P50 $6m with 55% above zero" are different investments and
          a point estimate hides it.
  REJECT  the 0.85 ADD/HOLD threshold.  It is a decision rule dressed as a
          statistic, and we have no standing to set a firm's hurdle rate.
          Report the distribution; let the reader set the bar.
```

The honest caveat: a Monte Carlo over parameters whose ranges we chose
propagates our own priors, not the world's. It answers "how much does the
answer move across the range we consider plausible", which is a real and
useful question, and it must be labelled as that rather than as a confidence
interval. `cost/params.py` already writes in that register.

### 5.2 The second estimand, pointed at an outcome we can actually observe

```
  COST     1 week for a first credible cut, on top of the ~2 days
           LIMITATIONS_AND_WORKAROUNDS.md B3 already scopes.
  BUYS     the project's second estimand, a replacement for a parameter
           somebody typed, and the mission sentence made true.
  NEEDS    nothing new for the outcome.  Everything for the dates -- and
           that is the risk, not a detail.
```

**The reframe.** The original aimed spatial DiD plus synthetic control at
**cannibalisation**: how much of a new station's volume is stolen from an
existing one. That outcome is order volume. Order volume is unobservable, we
have no transactions, and ADR-0001 already settled that constructing it is
circular. Leaving it was right.

But look at what `HANDBOOK_03_CAUSAL.md` §3.11 lists as the prerequisites for
building the second estimand: real opening dates, interval censoring, a donor
pool that survives gate 5, and more than 43 buildings. **The outcome variable
is not on the list.** It is not on the list because the chapter silently
assumes the outcome is order volume throughout — §3.2 opens with "same-day
ZIPs have 30% higher order volume" and never revisits it. An unobservable
outcome is the first prerequisite and nobody wrote it down.

Once it is written down, the fix is obvious: **change the outcome, not the
method**. Measured on `data/processed/panel.parquet` today —

```
  column                  non-null      ZCTAs      what it would estimate
  --------------------------------------------------------------------
  column              non-null    ZCTAs   ZCTAs that VARY   what it
                                            over 32 quarters  would estimate
  ----------------------------------------------------------------------
  home_value           74.90%    26,262     26,262   USABLE  effect of an
                                                             opening on local
                                                             property values
  median_home_value    89.70%    30,311          0   CONSTANT
  pm25                 98.55%    33,300          0   CONSTANT
  diesel_pm            99.22%    33,529          0   CONSTANT
  traffic_proximity    99.95%    33,774          0   CONSTANT
  permit_units_total   65.44%    32,965          -   construction response
  low_income_pct       99.95%    33,774          0   equity STRATIFIER, not
  people_of_colour_pct 99.95%    33,774          0     an outcome
  rent_index           11.23%      6,592          -   too thin; do not use
  --------------------------------------------------------------------
  enabled                 100.00%       1,257 treated, on 32 quarters
                                              2018Q1-2025Q4
```

A 32-quarter panel, 26,262 units with a continuous outcome, 1,257 treated,
and staggered adoption. That is a textbook synthetic-control or
staggered-DiD setup and **the data is already in the file every model reads**.

**Why this is worth more than a cannibalisation estimate would have been.**
The proposal's own opening sentence is that "the public bears their
consequences — property values, air quality, municipal budgets, and tax
abatements". Cannibalisation is Amazon's P&L; it is the one question in the
document a city does not care about. Property values and PM2.5 near a new
delivery station are the questions a city council actually asks, they are
unstudied for delivery stations specifically (`DECISION_LOG.md` §3.2:
"delivery station" returns zero hits in Houde et al.), and answering them
turns the project from a worse-resourced replication into the thing its title
claims to be.

**Now the risk, stated at full strength.** `HANDBOOK_03_CAUSAL.md` §3.11
Part 3 is right and this does not repair it. Our dates are OSHA upper bounds
with measured lags of 4, 13, 57, 69 and 345 months. An event study uses the
date to decide which quarters are "before"; a 57-month error puts five years
of post-treatment into the pre-period, the parallel-trends check then looks
reassuringly flat for the wrong reason, and the synthetic weights get fitted
to reproduce the treatment effect. The chapter's verdict — *"a confidently
null result with a clean-looking pre-trend, which is the most dangerous kind
of wrong"* — stands unchanged.

So the honest claim is narrow and I will not inflate it: **swapping the
outcome removes one of two blockers, and it is the blocker nobody had
named.** The date blocker remains, it is already priced, and it is the reason
this sits second rather than first.

Three things that would make it tractable in spite of the dates, in order of
cost:

```
  1  Restrict to the subset with tight bounds.  Not every date is a
     345-month lag; the distribution has a short left tail.  Publish the
     bound distribution and fit on the tight stratum only, reporting n.
  2  Run it as an assumption ladder with a breakdown point -- "robust to
     date error up to X months" -- which is PLAN.md 6 item 7, already
     scheduled for a different purpose and reusable here whole.
  3  Use the measured lag distribution as a censoring interval rather than
     a point, which is Molinari 2.3 (ADR-0004 option D) applied to the
     second estimand instead of the first.  Highest cost, cleanest answer.
```

And one free diagnostic worth running before any of it: an event study on a
**placebo date** drawn from the measured lag distribution. If the placebo
produces the same effect as the real date, the design cannot see anything and
we have learned that for the price of an afternoon.

### 5.3 The extraction pipeline, so the remaining unlabelled buildings stop waiting for a human

> **UPDATED at commit `9dc91ba`, after this section was first drafted.** One
> batch of 70 has now been labelled — by hand, through a chat window, in an
> evening. It returned 33 delivery stations, took the panel from 100 buildings
> to 132 and from 62 CBSAs to 65, and **cut metros holding only one facility
> from 43 of 62 to 36 of 65**. That is the greenfield problem roughly halved
> in one sitting. 292 buildings remain. The argument below is unchanged and
> the evidence for it is now empirical rather than predicted; the numbers have
> been updated and one new blocker is recorded at the end.

```
  COST     2-3 days.  Cache, pydantic-equivalent validation, confidence
           gate, audit append -- and we already have gates 1-4 written.
  BUYS     132 facilities -> potentially several hundred; the one thing
           that makes the line-haul covariate testable; a real subject for
           gate 5.
  NEEDS    an LLM API key and a few dollars.  Nothing else.
```

The archive's Algorithm 6 — `cached_llm_call.py` keying on
`SHA256(prompt || model || temperature || top_p || seed)`, a confidence
threshold, pydantic validation, an append-only audit log, human-in-the-loop
before the write — is a complete and sensible design for turning unstructured
text into warehouse rows reproducibly. We have the gates
(`agent/gates_data.py` implements exactly its four) and not the pipeline.

`data/collection/prompts/` held six `UNLABELLED_BATCH_*.txt` files covering
**362 unclassified OSHA buildings, 175 of them in pilot states**, and the
workflow is a person pasting them into a chat window and saving the reply to
CSV. One batch is now done and 292 remain. The manual route **works** — zero
UNKNOWN across 70, every answer carrying a quote and a source URL — which
settles the question of whether an LLM can do this job. What it does not do is
scale, resume, or leave an audit trail a stranger can replay.

It is the bottleneck on three separate things, and the first is now measured
rather than argued:

```
  models/accessibility.py  the line-haul covariate returned a clean null
    because 65 of 100 facilities were the first in their metro, so the
    formula degenerated to demand-weighted centrality for two thirds of
    the sample.  Batch 1 densified 11 metros and added 3.  This is the
    exact lever, and it has now moved once.
  The choice model  94 decisions, 3 estimable parameters.  More decisions
    per metro is the only lever that moves both power and the covariate.
  Gate 5  needs a donor pool, which needs treated and untreated units,
    which needs a fuller facility list.
```

The LLM cache is the part worth copying most exactly. It is what makes an
LLM-labelled dataset auditable: the cache file goes in the repository, the
labels are replayable offline by anyone, and a reviewer can check that the
label was not quietly regenerated after seeing the result. That is a
reproducibility argument, not a convenience one, and it fits this project's
standard better than it fitted the original's.

Caveat carried from the archive: the provenance doc records that an earlier
language-model attempt at this **fabricated 33 of 35 dates**
(`FACILITY_PANEL_PROVENANCE.md:179`). So the pipeline must classify
(what type of building is this) and must not date. The dates keep coming from
OSHA. That constraint is not a reason to skip it; it is the specification —
and Batch 1 respected it, returning type with an evidence quote and no dates.

**The blocker that constraint creates, now live.** `9dc91ba` records it and
does not merge the rows into the model because of it: `choice.build()` needs
`open_year` to select a CBP vintage *strictly earlier* than the opening, and
the new rows carry only OSHA's `operating_by`, which is an **upper** bound. A
vintage chosen strictly before an upper bound can still fall after the true
opening, which reintroduces the exact circularity the lag exists to prevent —
an Amazon delivery station is itself a warehousing establishment, so the
covariate would contain the outcome.

That is a real design decision and it is the right place to have stopped. Two
routes, neither free: lag harder (pick the latest vintage strictly earlier
than `operating_by` minus the upper quantile of the measured lag
distribution, which costs recency and is defensible), or admit the vintage as
an interval and carry it through as a sensitivity. The measured lags — 4, 13,
57, 69, 345 months — make the first route expensive and the second honest.
Either way it is one decision, not a research programme, and 292 buildings
are waiting behind it.

### 5.4 Kendall's tau against the real expansion sequence

```
  COST     half a day.
  BUYS     the only held-out check that separates our model from the
           single-covariate benchmark currently matching it.
  NEEDS    nothing.  100 dated national facilities, 104 of 104 quarters
           reported.
```

Argued in §4.4. The reason it is worth a whole entry despite being small:
right now `choice_report.json` shows the fitted model level with
`warehousing_establishments` alone on held-out top-1 (7 vs 8 of 38) and
top-10 (19 vs 20), gaps of one hit that fifty re-splits reduce to nothing
(§3.5). The project reports that honestly, which is to its credit, but it
leaves the fitted model with no demonstrated advantage over a free one-column
sort. A rank correlation against build *order* is a dimension the raw
covariate has no access to, and it is the cheapest available test that could
give the estimation something to have bought.

If it draws there too, that is a finding and a clean one: *"ranking ZIPs by
existing warehousing does everything our fitted model does, in space and in
sequence, so the model is not earning its parameters."* The project has
published worse results than that and been stronger for it. (This paragraph
said the model was "losing to" the raw count and that the count "beats" it;
see the correction in §3.5.)

### 5.5 Equity audit, including the part the original added

```
  COST     1-2 days for the audit; the remediation loop is a further day.
  BUYS     a viva answer, and a use for two columns already at 99.95%.
  NEEDS    a tract-to-ZCTA crosswalk for full resolution (TODO.md:330).
           The county-level version runs today.
```

The stratified audit itself is already on our roadmap and unticked. What the
original added, and what is worth taking, is council item `[C5]`: **the audit
must change something**. The original wired a flagged stratum back into the
mutator gate so that a write touching a redlined ZIP triggers extra review.

That is a better idea in our repository than it was in theirs, because we
have a gate pipeline to wire it into and they had a stub. It would also give
gate 5 a sibling that can actually run today, which partly answers the §4.3
problem of a contribution whose subject does not exist.

Honest limitation: `docs/TODO.md:330` records that EJScreen is currently
aggregated to **county** because no tract-to-ZCTA crosswalk exists at L1, and
calls that "a genuine loss of resolution on the equity overlay". A
county-grain equity audit is worth running and must be labelled county-grain.

### 5.6 The reproducibility and deployment bundle

```
  COST     1 day for all of it.
  BUYS     closes the §4.5 drift and the two engineering gaps in §3.9.
  NEEDS    nothing.
```

Four small things, all of which the original shipped and we do not:

```
  1  Exact dependency pins, or a lockfile.  pyproject.toml is >= throughout.
     A re-run in six months resolves differently and nothing will say so.
     The original's --only-binary=:all: trick is also worth copying: it
     turns a slow source-build failure into a fast, legible one.
  2  verify_repro.py plus checked-in expected values.  See 4.5.  The
     three-times-moving portfolio headline is the argument.
  3  A schedule: trigger on the CI workflow that runs (2) weekly and
     opens an issue on drift.  The original's issue template is
     copy-pasteable.
  4  A Dockerfile and one public URL.  We have a working dashboard that
     nobody outside this machine can open.  The original's multi-stage
     build is sound; drop its OSRM sidecar, which ADR-0002 makes moot.
```

On (4) the original also has a critique worth repeating, council item `[C6]`
from Whitfield: **ship the demo URL before the paper**. For a project whose
stated product is checkability, a public artefact a stranger can open is not
polish.

### 5.7 What not to take, and why

```
  ZINB, Heckman, Huff     superseded or blocked, per 3.1.  Do not
                          reinstate them to look complete.
  LoRA / Phi-3.5-mini     presentation layer, needs a GPU budget, solves
                          a latency problem we do not have.
  LLM ablation study      downstream of an extractor we have not built.
  ReAct agent, 3 MCP      an interaction affordance.  Our deliverable is
  servers, Text-to-SQL    an artefact trail, and a chat surface would add
                          an attack surface and a dependency for it.
  Yelp Fusion             CBP by NAICS is strictly better: free, national,
                          historical, industry-specific.
  The 8-bucket cost       take the four primary buckets, which we largely
  decomposition           have.  The four secondary ones had no public
                          source in the original either -- that column of
                          the table was aspirational.
  The 0.85 P(NPV>0)       a hurdle rate is the reader's to set.
  ADD/HOLD rule
```

## 1. Inventory

228 files. The archive is **not one proposal** — it is the whole lineage, from
the August scaffold through four proposal revisions to the v5 redraft that
renamed the project Siting Atlas. Reading it as a single document is the first
mistake available, because the root-level files describe a project that the
`Audit/` folder later dismantles.

Three strata, and they disagree with each other:

```
  ROOT + docs/basics + src/ + tests/ + infra/     2026-08-24 to 09-07
      The v3/v4 project.  ZINB, Heckman, Huff, synthetic control,
      Monte Carlo NPV, ReAct agent, 5 metros, "digital twin".
      This is what people mean by "the original".

  Audit/2026-09-07 .. 2026-09-09                  the turn
      A council evaluation, an explainer set, then the v5 redraft.
      The digital-twin claim dies here; the project is renamed.

  Audit/2026-09-10 .. 2026-09-11                  already us
      A critique of v5 and a pitch deck.  These describe the
      repository we have now, not its ancestor.
```

### 1.1 Root documents

| file | size | what it is |
|---|---|---|
| `README.md` | 15K | The v4 pitch. 5 metros, 6 sources, 4 models, 3 MCP servers, $50-200. The clearest single statement of the original |
| `plan.md` | 23K | **The most useful file in the archive.** The living plan at 2026-09-06/07: the v1-to-v2 method-stack table, and a P0/P1/P2 dissent table with named disagreements and their resolutions |
| `PLAN.txt` | 24K | The superseded 2026-08-24 scaffold plan. Week-by-week, 4 gates, `[NOT STARTED]` markers |
| `DESIGN_DECISIONS.txt` | 37K | 24 locked decisions, each with date / alternatives / why / what would reverse it. The best-structured document in the archive and the one worth imitating |
| `ARCHITECTURE.txt` | 31K | Layer-by-layer system description with an ASCII data-flow diagram. Describes modules that are stubs as though they were built |
| `TODO.txt` | 16K | Work items in IMMEDIATE / NEAR-TERM / LATER / BACKLOG / BLOCKERS. Every IMMEDIATE box is unticked |
| `LESSONS_LEARNT.txt` | 14K | Nine entries, all 2026-08-24, all environment problems: Python 3.14 wheels, `openai` version conflict, PowerShell chaining, TIGER at 500 MB, Census returning strings, ZCTA spelling across sources, and cvxpy having no cp314 wheel |
| `AGENTS.md` | 17K | 17 hard coding rules. Rule 4 is a 400-line file cap; rule 14 is no PII ever; rule 17 mandates keeping the five tracking documents current |
| `AGENT_HANDOFF_2026-09-06.md` | 29K | **Read this one.** A contemporaneous audit of a 12-day drift into documentation, with an honest self-critique section and a hostile-reviewer paragraph |

### 1.2 `docs/basics/` — the teaching library, 340 KB

| file | size | what it is |
|---|---|---|
| `00_index.txt` | 4K | Reading order |
| `01_what_are_we_building.txt` | 13K | Plain-English project story |
| `02_ml_algorithms_glossary.txt` | 186K | 17 fundamentals, 7 algorithms with worked examples and pseudocode, 6 cross-cutting concepts, 39-term vocabulary. The single largest file |
| `03_tech_stack_glossary.txt` | 80K | 37 tools across 6 parts |
| `04_data_sources_glossary.txt` | 16K | 6 sources plus an excluded-datasets table |
| `05_defense_qa.txt` | 28K | 45 viva questions with answers |
| `07_budget_and_deals.txt` | 11K | Three budget tiers and a student-deals stack. There is no `06` |

### 1.3 `src/prime_expansion_twin/` — 3,133 lines, eleven `NotImplementedError`

| module | lines | state |
|---|---|---|
| `config.py`, `logging_setup.py` | 260 | Real. pydantic-settings and structlog, both functional |
| `data/` (7 loaders + base) | 530 | `base_loader.py`, `census_loader.py`, `tiger_loader.py` have bodies. `usps`, `zillow`, `mwpvl`, `yelp` each raise |
| `warehouse/` (3 + init) | 484 | `connection.py` and `schema.py` have bodies; `mutations.py` raises. No `.sql` DDL files exist despite six being planned |
| `models/` (4 + base) | 631 | `base_model.py` is real and rather good. **All four models raise.** zinb x3, synthetic_control x4, cost_osrm x2, npv_montecarlo x2 |
| `agent/` (5 + 2 prompts) | 441 | All raise. The two prompt `.txt` files are written |
| `viz/`, `app/` | 352 | Both viz builders raise; three tab stubs render placeholders |

`tests/` is 16 modules, ~27 KB. They assert that constructors construct and
that abstract classes refuse instantiation. There is no golden file.

### 1.4 `Audit/` — the lineage, and where the project turns

| folder | contents |
|---|---|
| `2026-09-07_1900_council/` | `session.md` (53K) — a multi-voice advisory-council evaluation with formal dissent capture. Source of the `[G*]`, `[O*]`, `[C*]` item codes in `plan.md` §7 |
| `2026-09-08_0800_project-explainer/` | Four documents: `README.md`, `01_amazon_vs_novelty.md` (12K, the novelty defence), `02_folder_vs_proposal_gap.md` (14K, **an audit of promise versus code**), `04_algorithms_glossary.md` (32K, the condensed method list — and the file containing the §4.1 finding) |
| `2026-09-09_0900_proposal-v5-redraft/` | The v5 build: a 3.1 MB `.docx`, a 1.9 MB `.pdf`, `_dev/_v5_proposal_extract.txt` (61K) holding the text, three `.pptx` decks, 12 generated diagrams, 12 reference renders, 14 extracted v4 images, and 10 builder scripts |
| `2026-09-10_1400_v5-critique/` | `v5_project_critique.md` (22K) — a critique of the v5 document |
| `2026-09-11_1000_oscar-balraman-pitch/` | `OSCAR_Pitch_Prep_Balraman.md` (28K) plus a deck |

### 1.5 Everything else

```
  infra/            Dockerfile (multi-stage, python:3.12-slim),
                    docker-compose.yml (app + OSRM sidecar, healthchecks),
                    cloudrun.yaml.  All three are real and complete.
  .github/          ci.yml (ruff, ruff format, mypy --strict, pytest
                    --cov-fail-under=60), reproducibility.yml (weekly
                    cron -> verify_repro.py -> auto-open an issue),
                    and the issue template it files.  All real.
  reproducibility/  seeds.toml (real, 8 sections, one per "Algorithm"),
                    README.md describing verify_repro.py's three
                    canonical checks.
  scripts/          26 files, 500 KB.  Four are pipeline orchestrators
                    (ingest_all, build_warehouse, train_models,
                    verify_repro) and twenty-two build documents.
  figures/          10 matplotlib diagrams for the proposal.
  requirements*.txt Three files.  Every version exactly pinned.  cvxpy is
                    quarantined into requirements-modeling.txt because it
                    had no Python 3.14 wheel -- which is why the synthetic
                    control was never even attempted.
  data/, output/,   Empty but for .gitkeep and README.md.  No data ships
  secrets/, _dev/   in the archive.
```

**The shape of the whole thing, in one line:** 860 KB of document-builder
Python, 340 KB of teaching prose, 3,133 lines of package source, and eleven
`NotImplementedError` where the four algorithms should be.

## 2. What the original proposed

Faithfully, in its own terms and largely in its own words. Assessment is
deferred to §3 onward; this section is the archive speaking.

### 2.1 The question

> *"Where should Amazon add same-day Prime delivery next — and does the added
> revenue survive cannibalization?"*
> — `README.md:3`

Two estimands, deliberately paired. The first is a **ranking** problem: which
ZCTAs to add. The second is a **causal** problem: how much of the apparent
revenue from an addition is genuinely new, and how much is 2-day Prime orders
shifting tier. The README states the pairing as the point of the project —
isolating cannibalisation is *"critically"* what *"turns 'positive revenue'
into 'positive contribution margin'"* (`README.md:57`).

The business framing is explicit about stakes: roughly $250K per-ZCTA setup,
$2-10M of five-year NPV per correctly-chosen ZCTA, and the claim that the
whole framework reproduces an internal Amazon Retail Analytics workflow *"at
~85% fidelity on public data alone"*.

### 2.2 The scope

Five pilot metros — SF Bay, NYC, Chicago, Austin, Seattle — about 2,200 ZCTAs,
*"Not fifty. Not national"* (`plan.md` §1). Eight weeks, 8 September to
8 November 2026, three phases, four gates. Later expanded at Tier 3 to ten
metros by adding Denver, Miami, Nashville, Phoenix and Boise. Aggregate data
only, no PII, enforced by a column-name denylist in `BaseLoader`.

### 2.3 The four algorithms

Numbered in `seeds.toml`, which is the closest thing the archive has to a
canonical list. Algorithms 1-4 are analytical, 5-7 are the agent layer.

```
  1  ZINB demand         ZCTA-week order counts.  A logit stage for
                         structural zeros ("Amazon is not available here")
                         and a negative binomial stage for the count, to
                         handle variance >> mean.  statsmodels.
                         Headline metric: MAPE < 25% on 500 held-out
                         ZCTAs; F1 > 0.85 on structural zeros.

  2  Synthetic control   Cannibalisation.  For each activated ZCTA build a
                         counterfactual from a convex combination of
                         never-activated donors matched on pre-treatment
                         characteristics.  Donor weights by convex QP in
                         cvxpy: minimise ||X_treated - X_donors w||^2
                         subject to sum(w) = 1, w >= 0.  Placebo tests
                         over the donor pool for inference.

  3  OSRM cost           Cost per delivery per ZCTA from real drive times
                         on the OpenStreetMap network, served by a local
                         Docker container, plus Daganzo's continuous
                         approximation for the last-mile tour.

  4  Monte Carlo NPV     10,000 draws propagating joint uncertainty from
                         the ZINB coefficients, the cost model, the
                         cannibalisation rate, a log-normal fixed setup
                         cost around $250K and a uniform 8-12% discount
                         rate, through a five-year discounted cash flow.
                         Reports P10 / P50 / P90 and P(NPV > 0).
```

The v2 revision, driven by six questions from the advisor, added four more:
a **Heckman two-step** selection correction with an instrumental variable
(kilometres to the nearest USPS-classified commercial ZIP centroid, on the
argument that commercial zoning drives Amazon's choice but not residential
demand); a **Huff gravity pull factor** with beta fixed at 2 as a ZINB
covariate, using MWPVL roof area as mass and adding Walmart and Costco to the
denominator so competitors pull customers away; an **XGBoost** benchmark —
globally swapped to **LightGBM** by council tiebreaker `[G5]` on
2026-09-07 — with SHAP attribution, accepted as convergent validity if
Spearman rank correlation on the top decile reaches 0.80; and an **eight-bucket
cost decomposition** replacing a single fixed `K`, tiered 4 primary (real
estate, wages, fuel, vehicles) plus 4 secondary (fitout, hiring, permitting,
marketing).

Also added: an **equity audit** stratifying error by ZCTA majority-demographic
group and flagging any stratum 50% worse than the population; **Kendall's tau**
against Amazon's actual expansion sequence as a ranking-quality metric; and
**out-of-metro validation** on named held-out metros.

### 2.4 The agent layer

> *"The analytics is the star; the agent layer is a helper."*
> — `README.md:94`

A LangChain ReAct loop driven by Grok 4.5 via OpenRouter, with three tools
each exposed as a Model Context Protocol server so that the toolkit works
standalone from any MCP client and not only from the dashboard:

```
  SQL_Generator        Text-to-SQL over a READ-ONLY DuckDB handle,
                       grounded on the schema plus few-shot examples
                       retrieved with BAAI/bge-small-en-v1.5 embeddings.
  Spatial_Visualizer   Builds PyDeck choropleth and hexbin layers on
                       demand.
  Warehouse_Mutator    An LLM proposes a write to the warehouse; four
                       gates must pass before it commits.
```

The four gates are schema conformance, geocoding resolution, a confidence
threshold of 0.85, and an append-only WORM audit log written before the
attempt. A fifth optional gate, `HITL_REQUIRED`, surfaces a diff card and
requires a human click; council item `[O4]` resolved it to default ON.

The novelty claim rests here: *"Every LLM analytics system in 2024-2026 is
read-only. Nobody has published the specific pattern of LLM-propose + 4 gates
+ optional HITL + audit trail"* (`04_algorithms_glossary.md:272`). The
loop-closing version in `ARCHITECTURE.txt` §4.4 is stronger: *"an LLM
autonomously updates the input to a spatial-econometric model, causing new
causal estimates to flow out without human intervention."*

Tier 3 adds a LoRA fine-tune of Phi-3.5-mini as a local CPU narrator for
drilldown cards, and a controlled ablation of three frontier models at the
mutation-proposal step scored on gate-hit rate, gate-violation rate,
semantic-equivalence rate and end-to-end latency.

### 2.5 Data, warehouse, delivery

Six sources at v1 — Census ACS 5-year, MWPVL, TIGER/Line, USPS zones, Zillow
ZORI and ZHVI, Yelp Fusion — growing to nine at v2 with BLS OES metro wages,
EIA regional fuel and electricity, and Amazon 10-K filings for cost
validation. All free. The warehouse is a single DuckDB file in a Kimball star
schema: `fact_zcta_week` at ZCTA-month grain, about 132,000 rows, surrounded
by five dimensions. Delivery is a four-tab Streamlit and PyDeck dashboard —
expansion map, ZCTA drilldown, economics with sensitivity sliders, AI copilot
— containerised to GCP Cloud Run with Hugging Face Spaces as a fallback.

### 2.6 The discipline it set for itself

This is the part of the original that reads best, and it is worth quoting
rather than paraphrasing.

Reproducibility is stated as *"a first-class concern, not an afterthought"*:
every seed in one TOML, every dependency pinned exactly, every LLM call cached
under `SHA256(prompt || model || temperature || top_p || seed)` with the cache
committed so *"anyone rebuilding gets identical LLM outputs offline"*, a
`verify_repro.py` that runs the pipeline end to end and asserts against
checked-in expected values, and a weekly CI cron that opens an issue on drift.

`DESIGN_DECISIONS.txt` requires four fields for every decision — date,
alternatives considered, why we picked this, and what would make us reconsider
— and states that *"if any of those four fields is unclear on a proposed new
decision, the decision is not yet ripe"*.

`AGENTS.md` rule 15 defines "production grade" as ten simultaneous conditions
and closes: *"If any of these is untrue, the branch is not ready to merge —
regardless of how impressive the demo looks."*

### 2.7 What the original itself admitted

Two documents in the archive assess the project honestly, and both should be
read before anyone treats §2.1-2.6 as a description of something that existed.

`README.md:150` has a section headed **"What's not yet built (blocked on kiki
approval)"**, listing the entire `src/` tree, the app, CI and the Dockerfile.

`AGENT_HANDOFF_2026-09-06.md` §0 is blunter, and it is the author's own
account:

> *"Between 2026-08-25 and 2026-09-06, all of the AI-agent time on this
> project went into proposal DOCX iteration + VS Code custom-agent building.
> Zero code shipped to `src/` or `tests/` during that window."*

Its instruction for the next session is to *"treat every non-loader file as
'stub of unknown depth until proven otherwise by a passing test'"*, and its
hostile-reviewer paragraph reads:

> *"You spent 12 days on documentation and agent-building infrastructure while
> your project code sat frozen. Your 8-week execution plan has 2 weeks of
> slack you have already burned."*

## 6. What we have that the original did not

For the comparison to be fair it has to run both ways, and this direction is
much the longer list.

### 6.1 The thing that has no ancestor at all: a measured coverage ceiling

The original had a facility list and no notion that it might be incomplete.
`MwpvlLoader` raises, so it never had a list either, but the design assumed
MWPVL was a census.

We have three capture-recapture estimators over two independent lists, and a
third list that lets us **measure** the dependence between them rather than
assume it away:

```
  estimator                          N cities   OSHA coverage
  Chapman (assumes independence)          630   54.0%   a ceiling
  Chao (allows heterogeneity)             899   37.8%   tighter ceiling
  3-list log-linear                   314-417   33-44%

  measured pairwise dependence, via OpenStreetMap as the third list
  NLRB x OSHA | OSM 1.84    NLRB x OSM | OSHA 1.72    OSHA x OSM | NLRB 3.82
```

`src/siting_atlas/ingest/nlrb_estimators.py`. The reason this matters beyond
the number: it converts *"our data is incomplete"* from an apology into a
bounded quantity, and the third list was chosen precisely because its capture
mechanism — volunteers mapping buildings — is unrelated to the mechanism of
the other two (workplace injury and worker grievance). That is the standard
objection to capture-recapture, answered with data rather than with a
paragraph.

### 6.2 Models that were fitted, and one that failed on the record

```
  ORIGINAL                          OURS
  4 models, 11 NotImplementedError  a cloglog hazard, FITTED and FAILED,
                                      with the failure measured:
                                      Brier 0.019522 vs a constant's
                                      0.019614; ECE 0.00863 vs 0.00005
                                    a conditional choice model, FITTED on
                                      94 decisions, rho-sq 0.197,
                                      held-out top-10 0.50
                                    split conformal, 88.2% against 90%
                                    adaptive prediction sets on the
                                      choice model, coverage 1.000 at
                                      alpha 0.10 on 24 test decisions
                                    p-median depots, bounded 0.89% above
                                      a Lagrangean lower bound
                                    a portfolio optimiser with a
                                      10.73% optimality gap
                                    three capture-recapture estimators
```

The failed hazard model belongs in this column, not against us. A
specification that was built, tested and retired for a stated reason is worth
more than four that were never stress-tested, and the negative result — *this
panel, at this unit of analysis, cannot identify a siting policy, and here is
the arithmetic* — is a finding the original had no mechanism to produce.

### 6.3 A diagnosis the original could not have reached

The pseudo-replication argument — one station switches on a median of 58
ZCTAs by drawing a 15-mile disk, so 812 "events" are 28 to 38 decisions plus
geometry, and Train §3.7.1 p.61's independence assumption is destroyed — is
the intellectual core of the current project.

It is also an argument that would have demolished the original's ZINB on
ZCTA-week grain even more comprehensively: 2,200 ZCTAs times 60 months is
132,000 rows generated by a few dozen real decisions. The original's nominal
power would have looked superb and meant nothing. Nothing in the archive
contains the check.

### 6.4 Literature read rather than cited

Sixteen notes files in `docs/research/`, each written to a seven-part
structure that requires a section-by-section walkthrough, verbatim quotes for
anything load-bearing, and a mandatory part 7 saying what the reader did
**not** read or understand.

The standard this produces is visible in the results. Three examples:

```
  Hakimi (1964)      read, and found NOT to license what we claimed.  It
                     proves the 1-median case on a graph; we place 334
                     depots in the plane.  Replaced by a measured 0.45%.
  Train  2.2         our own five documents said this was the assumption
                     the hazard model broke.  Reading it showed Train
                     calls the criterion "not restrictive".  The citation
                     was moved to  3.7.1, which is a SMALLER claim and a
                     true one.
  Gneiting & Raftery a text search for "AUC", "ROC" and "discrimination"
                     across twenty pages returned zero hits, so the claim
                     that they condemn AUC was withdrawn and replaced
                     with the weaker, correct one: propriety is undefined
                     for AUC, not violated by it.  There is now a
                     standing guard in the defence pack against the
                     fabricated version.
```

The original's citations are real and appropriate — Lambert 1992, Huff 1964,
Abadie 2010, Ke 2017, Lundberg & Lee 2017, Yao 2023, Hu 2022 — but they are
cited from standard knowledge. None was opened and argued with, and none
changed a decision.

### 6.5 Data sources the original did not have

```
  OURS ONLY                        WHAT IT BUYS
  OSHA enforcement records         the facility panel itself -- a date
                                   that is a defensible upper bound in
                                   all 50 states, where five other
                                   sourcing routes failed
  NLRB case filings                the second list, hence  6.1
  OSM (Overpass)                   the third list, plus industrial
                                   landuse and warehouse building stock
  CBP ZIP x NAICS detail           warehousing establishment counts --
                                   the single covariate that moved the
                                   choice model 30% -> 50% at top-10
  Census BPS building permits      construction response
  EJScreen                         PM2.5, diesel PM, traffic proximity
                                   and two equity columns at 99.95%
  ACS 1-year, metro grain          alongside 5-year at ZCTA grain

  THEIRS ONLY                      VERDICT
  MWPVL                            deliberately not purchased,
                                   DECISION_LOG.md 1.7
  Yelp Fusion                      superseded by CBP NAICS
  USPS zone tables                 unused; would be needed only for the
                                   Heckman instrument
  Amazon 10-K                      never automated on either side
```

### 6.6 Engineering the original planned and we shipped

```
  a real, running Streamlit dashboard that shares its chart functions with
    the batch figure build, so the app and the printed figures cannot
    disagree
  a four-job CI (lint, test, smoke, documents) where the documents job
    diffs the generated .txt twins -- drift detection for prose
  46 test modules, 618 passing, 2 xfail with xfail_strict on so a stale
    exemption cannot survive silently
  per-run structured tracing: every artefact carries a run_id, which is
    what lets PLAN.md say "quote outputs/ with its run stamp, never a
    figure typed into prose"
  four ADRs with options tables, consequences and residual risk
  a declared edit registry, a sentinel registry and a flag gate, all
    traceable to specific papers
  Jaro-Winkler record linkage with blocking and component grouping
  agent gates 5-6, the inferential-integrity pair, which is a genuinely
    new idea and has no ancestor in the original's four data gates
```

### 6.7 The habit that is the real difference

The original's documents describe what the system will do. The current
project's documents describe what it did, what that cost, and where it is
still wrong — `PLAN.md` §7 is a list of the project's own open defects,
including one headed *"THE OPTIMISER DOES NOT KNOW WHAT AN ACTIVATION IS,
AND THIS IS THE SAME DISEASE THAT KILLED THE HAZARD MODEL"*.

No document in the archive does that. `ARCHITECTURE.txt` describes stubs in
the present tense; `README.md` lists four algorithms as the "analytics
stack" when all four raise. The one exception is the handoff note, which is
why §7.3 recommends it as the only file in the archive worth an hour.

## 8. Corrections to the current repository, found on the way

The brief said to verify every claim about the current repository against the
repository, and to say so loudly where the summary I was given was wrong. It
was wrong in several places, and so are several of our own documents. None of
these files is mine to edit; they are reported here.

### 8.1 Three published documents say the choice model is not fitted. It is.

This is the largest one, and it affects the document we would hand to an
examiner.

```
  docs/WHERE_WE_ARE.md 1     "SPECIFIED, NOT FITTED   the conditional
                              ZIP-choice successor. Deliberately."
  docs/WHERE_WE_ARE.md 1     "warehouse/national.py joins no covariates.
                              It is a facility list, not a modelling
                              panel. NOTHING HAS BEEN FITTED ON IT."
  docs/MODEL_SPEC.md 0       "The Phase 3 decision: STOP. Do not fit."
  docs/proposal/PROPOSAL_V5.md
                             "It is specified and not yet fitted"
```

All four statements are false as of `c76da04`. Commit `9218625`, *"Fit the
conditional ZCTA-choice model on the national frame"*, fitted it;
`a7dc489` added the warehousing covariate; `outputs/metrics/choice_report.json`
holds 94 decisions, 56 train / 38 test, converged, McFadden rho-squared
0.1969.

`WHERE_WE_ARE.md` is dated 2026-09-14 and was written by commit `d1f6de8`,
which is the commit **immediately before** the fit. It was accurate for about
an hour. The mechanism is the same one the project has documented twice
before: a status document written at the end of one piece of work and not
revisited when the next piece landed.

Two sub-points worth separating, because one of them is still true:

```
  STILL TRUE   warehouse/national.py itself joins no covariates.
  NOW FALSE    the conclusion drawn from it.  models/choice.py:115 build()
               does the join -- it takes the national facilities AND the
               panel AND cbp_detail, and assembles choice sets from all
               three.  choice_runner.py imports load_national directly.
```

**Also superseded, and worth saying explicitly because it is a good news
story nobody wrote down:** `MODEL_SPEC.md` §0 and §10.1 refuse to fit because
19 of 43 opening quarters (44.2%) are `fillna(1)` conventions, and the
two-period design is maximally sensitive to that field. That blocker was
**dissolved, not overridden**. It was a *pilot* problem; the national file
reports 104 of 104 quarters. `choice_runner.py:5-13` explains this clearly in
a docstring — *"Going national is not only a power decision, it is what
removes the blocker"* — but that reasoning never reached `MODEL_SPEC.md` or
`WHERE_WE_ARE.md`, both of which still carry the refusal.

`MODEL_SPEC.md` §8's power arithmetic is superseded in the same way: it
computes 9.3 effective and 12.7 optimistic events per parameter at three
parameters on the pilot frame, against a floor of 10. On the fitted national
frame it is 94 decisions against 3 parameters, and `WHERE_WE_ARE.md` records
15.8-16.0 per parameter for the national panel — **the floor is met**. The
specification document still says `meets_floor: false`.

### 8.2 The fitted model publishes no uncertainty of any kind

`outputs/metrics/choice_report.json` `fit` block contains `beta`, `theta`,
`n_parameters`, `numeraire`, two log-likelihoods, `mcfadden_rho_squared`,
`n_decisions` and `converged`. **There is no standard error, no covariance
matrix and no interval.** `models/choice.py` computes none; there is no
bootstrap anywhere in the module.

`MODEL_SPEC.md` §6.3 is explicit that both a sandwich covariance and a
2,000-replicate bootstrap over decisions must be reported side by side, with
percentile intervals rather than standard errors, and with Train's "if this
sample is large enough" precondition quoted in the table caption. ADR-0004
goes further and names the bootstrap intervals as **the diagnostic** for
whether the successor has also failed: *"the most likely outcome is wide
bootstrap intervals covering zero on every coefficient."*

So the project currently cannot answer the question it pre-registered as the
test of its own successor model. Of everything in this review, this is the
cheapest high-value fix and it is not in §5 because it is not something the
original had — it is something we specified and did not build.

### 8.3 Corrections to the summary I was given

```
  CLAIMED   "Conformal prediction sets give 90% coverage at a cost of
             71% of a metro's ZIPs."
  ACTUAL    90% is the NOMINAL target.  Empirical coverage at alpha=0.10
            is 1.000 on 24 test decisions -- the sets OVER-cover, and the
            commit message explains why without apologising for it: with
            23 calibration decisions q_hat is the 22nd order statistic of
            23, so the finite-sample correction is conservative.  The 71%
            figure is right (median_share_of_choice_set 0.7143, a median
            set of 38.5 ZIPs against a median choice set of 59.5).

  CLAIMED   "a single raw covariate (warehousing alone) MATCHES the
             fitted model"
  CONFIRMED and this entry has been INVERTED, 2026-09-14.  It used to read
            "ACTUAL it BEATS it on held-out data", and it scolded the
            summary for softening the repository's own commit message.
            That was wrong.  The single-split numbers are right -- top-1
            8 vs 7, top-5 16 vs 16, top-10 20 vs 19, of 38, Brier 0.008951
            vs 0.008724, the one measure where the fitted model wins --
            but they are ONE seeded split, and a one-hit gap is not a
            verdict.  Over 50 paired re-splits of the same 94 decisions
            the raw count leads by 0.36 hits of 38, paired sd 1.14, and
            loses 11 of the 50 (gbm_benchmark.json, across_repeats).
            "MATCHES" was the right word all along.  The correction is in
            Sec. 3.5.  The finding is unchanged either way: the
            estimation buys nothing over a free one-column sort.

  CLAIMED   "a 94-decision national frame"
  CONFIRMED 100 national facilities, 6 dropped for having no CBP vintage
            strictly earlier than their opening year, leaving 94.

  CLAIMED   "the cost model, depot network (p-median) and portfolio
             optimiser work"
  CONFIRMED but all three carry open defects recorded in PLAN.md 7, and
            two are material: 42% of depots exceed 40,000 parcels/day
            under nearest-depot assignment (heaviest 3.56x), and
            optimize/objective.py prices an activation three inconsistent
            ways for a ~2.7x capital overcharge.  "Work" should not be
            read as "are right".
```

### 8.4 Smaller staleness, listed for whoever next touches these files

```
  agent/warehouse_view.py:165-180  justifies its donor-pool fallback with
      "TODAY that column is entirely NULL, because the facility panel has
      not arrived".  It has arrived: 1,257 ZCTAs carry enabled = True.
      The fallback behaviour is still right; the stated reason is not.

  docs/defense/HANDBOOK_04_MODELS.md:405  describes the Huff gravity
      factor in the present tense, and :920 sets a viva question about
      why its beta is fixed.  Nothing computes it.  See 4.2.

  docs/defense/HANDBOOK_03_CAUSAL.md 3.11  lists four prerequisites for
      the second estimand and omits the outcome variable, because the
      chapter assumes throughout that the outcome is order volume.  That
      omission is what hid the opportunity in 5.2.

  models/runner.py:64-66  claims six distinct event times, all Q1.  The
      artefact says 17 across all four quarters.  Already known and
      flagged at MODEL_SPEC.md 10.9 as out of that work's remit; still
      unfixed, and it is load-bearing for resolve_baseline().

  MODEL_SPEC.md 10.8  says "The repository is not under version control".
      It is, since commit 208e124.

  power.n_events_zcta  is the TRAIN split (487 of 812), not a count of
      ZCTA events.  Known, documented, and still badly named.
```

### 8.5 One thing I could not check

I did not re-run any model. Every number quoted from this repository was read
from a committed artefact (`outputs/metrics/*.json`), from source, or
measured directly against `data/processed/panel.parquet` with the project's
own interpreter. The panel measurements in §5.2 are mine and are reproducible
with a four-line script; the artefact numbers are whatever the last run
emitted, and §8.1 is a demonstration that artefacts and prose in this
repository go out of step quickly.

---

## Sources

Archive: `MSBA_Project/prime-expansion-twin/prime-expansion-twin/`.
Repository at commit `c76da04`, working tree clean.

Generated twin: `ORIGINAL_PROPOSAL_REVIEW.txt`, via
`tools/docs/md_to_txt.py`. Do not hand-edit the `.txt`.
