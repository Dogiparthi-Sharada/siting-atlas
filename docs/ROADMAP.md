# Roadmap — what is not done yet

**Volume I: Last-Mile Delivery** is the capstone. Everything after it is why
the architecture is built the way it is.

*This is the only forward-looking document in the repository. Completed work
is not listed here — it is in [`STATUS.md`](STATUS.md), with a `run_id`
behind every number. Rewritten 2026-09-15.*

Status legend: `[ ]` not started · `[~]` in progress · `[-]` cut, with reason

---

## Decisions still owed

Phase-0 decisions that were never answered in writing. They are cheap to
settle and expensive to leave open.

- [ ] **D2 — Routing.** Precompute the OD matrix and delete OSRM, or keep the
      circuity approximation for v1? *(`engineering/DATA_ENGINEERING.md` §2.
      Today distance is great-circle × 1.30, a literature value never measured
      against a real road network.)*
- [ ] **D3 — Retail density.** Census CBP as primary, Yelp optional?
      *Resolved in CBP's favour in practice; the decision is unwritten.*
- [ ] **D4 — Scope.** Confirm the fine-tuned narrator and the three-model LLM
      ablation stay cut (see the cut list below).
- [ ] **D5 — Innovation set.** Adopt the four supported claims, drop the three
      broken ones? *(`README.md` "What is and isn't new" marks three of the
      four as ambitions.)*
- [ ] **D6 — Budget.** Resolve the $35/$100 table against the $200/$300 prose,
      in writing, with the instructor.
- [ ] **D7 — Name.** Confirm `siting-atlas`; no trademark in repo, domain,
      Space URL or dashboard title.

The model-change decision (unit of analysis moves from the ZCTA-quarter to the
station siting decision) is recorded in
[`adr/0004-model-change-conditional-choice.md`](adr/0004-model-change-conditional-choice.md)
and is **proposed, awaiting confirmation** — it is tracked in
[`STATUS.md`](STATUS.md) §7 as D1 rather than here, because the work it gates
is already built.

---

## Carried forward from the foundations

Items from Phases 1, 2 and 4 that were never built. The phases themselves are
closed; these are what is left of them.

### Ingest and normalise

- [ ] TIGER/Line ZCTA geometry normaliser — registered, gated behind
      `--include-large`, no L1 normaliser. Needed only for choropleths; the
      Gazetteer supplies the centroid and area the cost model uses.
- [ ] Tract-to-ZCTA crosswalk — EJScreen is aggregated to *county* because no
      tract-to-ZCTA crosswalk exists at L1. A genuine loss of resolution on
      the equity overlay, which is coarse enough to hide the effect it exists
      to measure.
- [ ] Connecticut geography break — 2023 replaces eight counties with nine
      planning regions; the 2020 crosswalk keeps the old codes, so CT carries
      permits to 2021 and NULL after. No pilot metro is affected.
- [ ] Reconcile the source registry with the reachability probe — three
      standing disagreements. Unblocked by deciding whether `Availability`
      records intent or measurement.
- [ ] Remove `eia_prices` from the manual `EXPECTED` list — it is registered
      as both an API and a manual source, so every run reports a permanent
      false `missing`. One line.
- [ ] Add `openpyxl` to `pyproject.toml` — undeclared, and without it a clean
      install cannot get past L1.

### Warehouse and panel

- [ ] Data contracts that fail the build. Row counts and null rates are
      *reported* in `panel_report.json`; nothing stops a build on drift. Wire
      one — the row count on `panel.parquet` is the cheapest — and the CI
      claim becomes true.
- [ ] Referential-integrity contract — the stage warns on a ZCTA with no
      county; nothing fails.
- [ ] Rent imputation, a coverage-conditioned model, or dropping rent as a
      feature. `rent_index` is missing for 94.3% of ZCTAs and the covered
      fraction is not a random fraction.
- [ ] MAUP robustness at H3 grain — `h3` is declared in `pyproject.toml` and
      not installed.
- [ ] Record the dbt decision as an ADR. There is no `dbt/` directory; L2 is
      SQL in `warehouse/schema.py`. That is a decision, and it is currently a
      drift.

### Identification

- [ ] Two structural periods, as `MODEL_SPEC.md` §5.1 specifies — a 2020Q4 /
      2021Q1 split with attraction variables measured at the start of each
      period and a likelihood-ratio test against the pooled model. The fitted
      model has one period and `models/choice.py` contains no period logic.
      **Unattempted, not rejected.**
- [ ] Inference on the expanded panel — `choice_inference`, `choice_sandwich`
      and the conformal sets, re-run on 483 decisions rather than 94. See
      [`STATUS.md`](STATUS.md) §3 blocker 1.
- [ ] Interval censoring in `models/risk_set.py`. It belongs to the retired
      hazard specification, so it is not urgent — but the reframe *factors*
      the timing question rather than deleting it,
      `P(served) = P(a station opens in the metro) × P(the site is within 15
      miles)`, and the first factor is still a timing model on dates that are
      still upper bounds.
- [ ] Heckman two-step on the pilot metro; report corrected *and* naive.
- [ ] Equity audit: per-stratum metrics by ZCTA majority-demographic group.
- [ ] Control function for endogeneity (Train §13.4). **Not BLP** — Train
      notes BLP cannot be implemented when observed shares are zero for some
      alternatives in some markets, which is this case.
- [ ] An assumption ladder over date error with a stated breakdown point:
      "robust to measurement error up to X months".
- [ ] Winkler's standardised score — proper, built for rare events, computable
      from `outputs/tables/hazard_predictions.parquet` without refitting. The
      cheapest literature gap outstanding.
- [ ] The consistency check on the edit set (Winkler feature 2;
      Fellegi & Holt §5.2).
- [ ] Macro / selective editing — rank records by influence on key totals. No
      outlier detection of any kind exists.

### Decision layer

- [ ] OD matrix per metro from OSRM; **delete the OSRM artefacts** *[per D2]*.
      This is also what would let circuity be measured per metro instead of
      assumed at 1.30.
- [ ] Eight-bucket capital decomposition; metro CapEx validation against
      public filings. The current table is operating cost per day only — no
      capital, no amortisation.
- [ ] Top-K rank stability under uncertainty. The frontier varies the margin
      and the Monte Carlo varies the parameters, but neither reports whether
      the *top-K ZCTAs* are stable across draws.
      `montecarlo_draws.parquet` holds one row per draw and no selection
      detail. Unblocked by emitting the selected set per draw.
- [ ] Resample `parcels_per_depot_per_day` in the Monte Carlo — excluded by
      oversight at `optimize/montecarlo.py:128,137`, so every published band
      is a floor.
- [ ] Cost-bucket tornado / sensitivity plot.
- [ ] Cannibalisation decay radius. The optimiser uses a fixed 20 km
      parameter; estimating it needs far more openings than this panel holds,
      or pooling metros and accepting one shared radius.

---

## Phase 3 — Causal layer

Never started. This is the second estimand from the original proposal —
spatial difference-in-differences with synthetic control — and it may be more
tractable than siting with the data in hand. It is the most plausible route to
a positive result.

- [ ] Spatial SCM with a donor pool; pre-treatment fit diagnostics
- [ ] Placebo / permutation inference + post-pre RMSPE ratio p-value
- [ ] Cannibalisation decay radius via distance bands (Pollmann)
- [ ] **Construct W from the estimated radius** rather than assuming contiguity
- [ ] Pre-registered test: does event-driven W revision move θ at all?
      *Win either way; record the prediction before running it, as
      [`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md) did.*
- [ ] Cross-operator transferability: fit on one operator, score on another.
      The panel currently holds one operator, so this needs a second.
- [ ] Correct for LLM-extracted variables as generated regressors (DSL / PPI)

---

## Phase 5 — Agent and surfaces

- [ ] MCP servers: `SQL_Generator`, `Spatial_Visualizer`, `Warehouse_Mutator`
- [~] **Gates 5–6 (identification integrity).** They run. Gate 5 escalates
      rather than passing or failing, which is the honest behaviour on a thin
      donor pool, and gate 6 should be expected to say "not enough units"
      rather than to pass. Gates 1–4 are done.
- [ ] `HITL_REQUIRED=ON` by default, with a diff card
- [ ] Agent eval: n ≥ 100, execution accuracy, Wilson intervals, difficulty
      tiers
- [ ] Gold-set audit; judge-bias mitigation (two judges + human tiebreak, κ)
- [ ] Operator view: ranked bundles, NPV bands, SHAP drilldown
- [ ] Public Planning view: propensity, timing window, EJ overlay
- [ ] A cost-per-parcel heat map. There is no hero figure in the repository
      and the root `README.md` carries a marked TODO where it should be.

---

## Phase 6 — Ship

- [ ] Deploy to HuggingFace Spaces; load time < 5 s. The Streamlit app exists
      (`app/dashboard.py`, reusing the batch chart functions so the app and the
      printed figures cannot disagree); only the deployment is outstanding.
- [ ] **Publish the facility-opening panel as an open dataset.** Arguably the
      most durable artifact the project could produce, and most of the work is
      done — but the 693-row file is still **untracked in git**
      ([`STATUS.md`](STATUS.md) §3 blocker 5), and `source_type` / `source_url`
      are still loose on the OSHA-derived rows.
- [ ] Methods paper draft
- [ ] Model card + data card + limitations register
- [ ] Reproducibility check: a stranger clones and rebuilds from scratch
- [ ] Public forecast registry: first timestamped prediction CSV, tagged
      release. `white_space.json` already carries a `falsification` clause
      that is exactly this in miniature.
- [ ] Executive deck and a written series

---

## Cut, with reasons

- [-] **Fine-tuned Phi-3.5-mini narrator** — ~7 days, $30, contributes nothing
      to novelty, accuracy or the use case. A runtime LLM call with caching is
      fine.
- [-] **Three-model LLM ablation** — underpowered at n=200 (MDE ≈ 8pp); answers
      a question nobody asked. Revisit as a workshop extension.
- [-] **Full-US OSRM** — not laptop-feasible; per-metro precompute replaces it.
- [-] **"Faster than Amazon" claim** — compares a compute step to a governance
      step; unverifiable.
- [-] **Moment inequalities (Holmes 2011 / Houde, Newberry & Seim 2023)** — the
      identifying variation is exactly the quantity this project cannot
      observe, and Holmes §8.3 states the estimator is inconsistent under this
      kind of measurement error. Reasoning in
      [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md).
- [-] **Buying MWPVL's dataset** — it would supply real opening dates and
      destroy the claim that a city can do this with free data. Ask instead for
      an academic slice for *validation*, to publish a measured error rate.
- [-] **Re-running the satellite pipeline** — tried, measured, rejected on a
      test it fails 36% of the time. The failure is in the changepoint
      detector, not the imagery.

---

## Volume II and beyond — why the architecture looks like this

The capstone is one volume of an atlas, not a finished product. Each item
below is a **data swap, not a rewrite**, because the pipeline is
source-agnostic below L3.

### Near term (post-capstone, 3–6 months)

- [ ] **Volume II: Data centres.** Same machinery, hotter subject. Opaque
      siting, enormous capital, tax abatements, communities with no forecast,
      and an active civic ecosystem already asking for exactly this.
- [ ] Quarterly forecast registry with public scoring
- [ ] Workshop paper: the inferential-integrity gates
- [ ] A second operator fully modelled → transferability becomes a headline
      result rather than an ambition

### Medium term (6–18 months)

- [ ] Volumes: warehouses generally · EV charging · grocery · last-mile lockers
- [ ] Causal forests / DoubleML to extend the selection correction beyond one
      metro
- [ ] GNN over the ZCTA adjacency graph as a cross-metro transfer baseline
- [ ] Public API over the panel
- [ ] Partner with one air district or planning department on a real decision

### Long term — what "success" means

- [ ] The panel is the reference dataset others cite for facility siting
- [ ] A regulator or council cites the tool in a published decision
- [ ] Someone outside the team submits a Volume III

---

## Future scope — if you are picking this up

Everything above is our backlog. This section is different: it is written for
**someone else**, and it is grounded in what this project measured rather than
in what would be nice.

### The rule that tells you what to try

The project's own evidence names the shape of a covariate that can work, and
it is not about the subject matter:

> **Covariates that work are computed as a distance *from* each candidate.
> Covariates that fail are looked up *against* it.**

A distance is ZCTA-specific by construction. A lookup inherits whatever grain
its publisher chose — and most US public data is published at county level,
arriving at a within-metro model as about nine distinct values across two
hundred alternatives. The two network-proximity terms are the only new class
that ever worked here, and they are the only ones of that shape.

Before fitting anything, run the screen: a covariate's **within-metro
coefficient of variation**. Below 0.6 it failed in every case tested (7 of 7).
Above 1.3 it may work (9 of 14). See
[`../docs/EXPERIMENTS.md`](EXPERIMENTS.md) §8.

### Four things worth doing, in order of expected value

**1. Parcel-level land data.** Acreage, zoning, van-staging capacity, lot
frontage. Finer than ZIP, uncorrelated with population, and computed per
candidate — it passes both filters, and it is the best untested idea this
project can name. It is blocked on roughly three thousand county GIS portals
with no common schema. **That is an infrastructure problem, not a modelling
one, and it is the paper's point restated as a task.** Anyone who assembles
even one state's parcel layer has done something this project could not.

**2. Interval-censored opening dates.** The panel carries an *upper* bound on
every opening date — an OSHA inspection proves the building was operating by
date X — and no lower bound. So "opened in 2019" is never available, only
"open by 2019", and that single gap is what stops the model using time
properly. Our satellite attempt failed (36% of its estimates were falsified,
see [`data/collection/README.md`](../data/collection/README.md)). Permit
filings, utility connections and local news archives are all untried. An
interval is a thing the econometrics can actually use.

**3. A second operator.** Nothing above L3 knows where the bytes came from, so
adding Walmart, UPS, FedEx or USPS is a data swap rather than a rewrite. This
is the single cheapest way to find out whether the null generalises or is
Amazon-specific — and it is the first question any reviewer asks.

**4. Ship the cost model as a tool.** It works, it needs no prediction to be
useful, and no county currently has any way to estimate what a parcel is worth
to an operator. A small web form taking an address and returning a
cost-to-serve estimate with its assumptions exposed would be used by people
who will never read this repository.

### What not to retry, and why

Saving you the time we spent:

| Do not | Because |
|---|---|
| Add more ACS demographic columns | Collinear with households by construction — twice the households is twice the cars, twice the labour force. Measured, not assumed |
| Widen the catchment radius | Tested 8.3 to 45 miles. One opening still switches on a median of 39 ZCTAs at every radius |
| Reach for a bigger model | A gradient-boosted benchmark wins by about 1.3 decisions in 38 and loses on probability quality. The ceiling is the data |
| Add county-grain covariates at ZIP grain | ~9 distinct values across 200 alternatives. A near-constant cannot rank |
| Assume more data fixes it | The panel was quintupled, 94 → 483 decisions, and lift did not move |
| Trust a prediction the model cannot calibrate | Ranking without calibration is not prediction — it is where the survival model died |

### The honest caveat on all of it

This is one operator, one facility class, one country, and a null result. None
of the above is promised to work. What the project can offer is a **screen
that says what to discard before you spend a week on it**, and a record of six
things that did not work, written down in enough detail that you do not have
to rediscover them.

---

## The one-line thesis

> **Private capital picks locations; the public bears the consequences; and
> there is currently no open, checkable model of how those decisions get
> made.** Volume I measures the cost side and reports a pre-registered
> negative on the siting side. The atlas is the point.
