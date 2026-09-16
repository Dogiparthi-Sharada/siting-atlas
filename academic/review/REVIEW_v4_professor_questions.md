# Pre-Implementation Review — MSBA Capstone v3
## Answering the professor's three questions, and what must change before you write code

**Reviewed document:** `MSBA_Capstone_Proposal_Final_v3.docx`
**Review date:** 8 September 2026
**Scope:** novelty defence, accuracy/confidence architecture, public-data use case, and a
priority-ordered correction list.

> **Read this first.** Three of the proposal's five "Innovation" claims are stated in a form
> that a single Google Scholar search will falsify, and the headline accuracy metric
> (Objective 1, MAPE < 25%) currently measures nothing. Both are fixable in about a week of
> rewriting plus two weeks of re-scoped build. Neither is fixable after the professor asks
> the question in a viva. The fixes below make the project *more* defensible than v3, not
> less ambitious.

---

## Table of contents

1. [Question 1 — "What's the novelty if Amazon already does it?"](#q1)
2. [Question 2 — "What is the model confidence and prediction accuracy?"](#q2)
3. [Question 3 — "It's public data. What's the use? Where's the use case?"](#q3)
4. [Correction plan before implementation (P0 / P1 / P2 / P3)](#corrections)
5. [Scope challenge — what to cut](#scope)
6. [Viva scripts — 60-second answers to each question](#viva)

---

<a name="q1"></a>
## 1. Question 1 — "What is the novelty if Amazon is already doing it?"

### 1.1 First, reframe the question

"Amazon already does this" is not an objection to research. Nobody objects to weather models
on the grounds that the atmosphere already knows what it is doing. The professor is really
asking a sharper question:

> **What does this artifact do that no existing *accessible* artifact does, and for whom?**

There are three separable answers, and the proposal currently blurs them together:

| Axis | Claim | Strength |
|---|---|---|
| **Audience novelty** | Amazon's model exists but serves only Amazon | Strong, but v3 frames it badly (§3.3 below) |
| **Methodological novelty** | Mutable W, event-driven re-estimation | **Overstated in v3 — must be narrowed** |
| **Architectural novelty** | LLM writes into a *causal estimator*, not a data table | **Real, but v3 misses the actual novel bit** |

### 1.2 The citation you must add before anything else

> **Houde, J.-F., Newberry, P., & Seim, K. (2023). "Nexus Tax Laws and Economies of Density in
> E-Commerce: A Study of Amazon's Fulfillment Center Network." *Econometrica*.**
> (Earlier version: NBER Working Paper 23361, 2017, "Economies of Density in E-Commerce.")

This is a structural model of **Amazon's own fulfilment-centre entry decision**, estimating
economies of density, identified off state sales-tax nexus law changes. It is the closest
published work to your project and it is in *Econometrica* — a top-five economics journal.

**It is not cited anywhere in v3.** This is the single most dangerous omission in the
proposal. If the professor finds it before you cite it, the novelty question stops being a
question and becomes a verdict.

Cited properly, it becomes your **best** defence, because the deltas are clean and large:

| Houde, Newberry & Seim (Econometrica 2023) | This project |
|---|---|
| FC network for **2-day** standard fulfilment | **Sub-24-hour** nodes (DS / SDC / AMXL) |
| **State** grain, tax-nexus variation | **ZCTA** grain, ~5,200 units |
| Data through ~2018, pre-regionalisation | 2023–2026 regionalised, node-based network |
| Structural entry model; no runnable artifact | Deployable, open, reproducible artifact |
| Static information environment | Event-driven state updates from text |
| Identification from tax-law variation | Heckman selection + spatial synthetic control |
| Not reproducible by a third party | Public URL, open repo, open data |

Say this out loud in the viva: *"The definitive academic treatment of Amazon's network is
Houde, Newberry and Seim in Econometrica. They model the 2-day FC network at state grain
through 2018 using proprietary and licensed data. We model the sub-24-hour network at ZCTA
grain through 2026 using entirely public data, and we ship it."* That answer converts a
weakness into evidence you know the field.

### 1.3 Honest audit of the five claimed innovations

#### Innovation 1 — `Warehouse_Mutator` as an LLM safety pattern → **DOWNGRADE, then re-aim**

v3 claims: *"No prior published work introduces the pattern."* That is too strong. Prior art
exists on gated / validated LLM writes:

- *Toward Safe LLM Agents: A Survey of Specification, Verification, and Enforcement*
  (arXiv 2608.14590)
- *SafeNlidb: A Privacy-Preserving Safety Alignment Framework for LLM-based Natural Language
  Database Interfaces* (arXiv 2511.06778)
- *On the Vulnerabilities of Text-to-SQL Models* (arXiv 2211.15363)
- *Words Become SQL: Securing AI Assistants* (IEEE S&P 2026)
- Working open-source implementations: `sqlgate` ("a deterministic, fail-closed write gate for
  LLM-generated SQL"), `llm-safe-sql` ("let an LLM propose UPDATE/DELETE, run it for real
  inside a transaction")

Human-in-the-loop write approval is also a shipped product feature across the agent ecosystem.
So "LLM proposes a write → gates validate → human approves" is **well-trodden ground**.

**What actually survives — and it is better than the original claim.**

All the prior work protects **data integrity**: don't corrupt rows, don't leak PII, don't drop
tables. Your write target is not an operational table. It is **a parameter of a causal
estimator**. That creates a failure class nobody has studied:

> A mutation can be **syntactically valid, schema-conformant, correctly geocoded,
> high-confidence, and fully audit-logged** — passing all four of your gates — and still
> **silently invalidate a causal identification assumption downstream.**

**Worked example (use this one in the viva):**
The agent reads *"Walmart opens a new sortation centre in Plano, TX."* It extracts
`(33.0198, -96.6989, SORTATION)` and writes it to `dim_logistics_nodes`.

- Gate 1 schema conformance → ✅ passes
- Gate 2 geocoding reachability → ✅ passes, Plano is real
- Gate 3 confidence threshold → ✅ passes, 0.94
- Gate 4 audit-log immutability → ✅ passes, logged

Yet that row changes `W`, which changes which ZCTAs are neighbours, which changes the
synthetic-control **donor pool** for treated ZCTAs in the Dallas metro, which changes θ (the
cannibalisation coefficient), which moves NPV by millions. **Nothing in your four gates
checks any of that.** The write is "safe" and the inference is broken.

**Fix — add two identification gates.** This is the genuinely novel contribution:

- **Gate 5 — Donor-pool integrity.** Does this mutation move any unit that currently serves as
  a control/donor into a treated or spillover-contaminated state? If yes, the donor pool must
  be recomputed and the affected ZCTAs flagged, not silently re-weighted.
- **Gate 6 — Estimate stability.** Re-run θ with and without the mutation. If |Δθ| exceeds a
  **pre-registered** threshold, escalate to a human *regardless* of the `HITL_REQUIRED` flag,
  and surface the delta in the diff card.

Reframed claim, which is defensible and narrow:

> *"Existing work on gated LLM writes protects data integrity. We identify a distinct failure
> class — **inferential integrity** — in which a write that satisfies every data-integrity gate
> nonetheless invalidates a downstream causal identification assumption, and we propose two
> identification gates that detect it."*

That is a real, small, publishable contribution. It is also two days of work, because you
already run θ estimation; you just run it twice and diff.

#### Innovation 2 — Mutable spatial weight matrix W → **MUST REWRITE. Currently false.**

v3 claims: *"Spatial econometrics has treated the spatial weight matrix W as fixed ex ante for
four decades… Anselin (1988), LeSage and Pace (2009), and modern Bayesian spatial-econometric
work all assume W is specified at model definition and does not change."*

**This is not true, and it is trivially falsifiable.** There is an active literature on
estimating and selecting W:

- Souza (2019), *Estimation and selection of spatial weight matrix in a spatial lag model*
  (Warwick working paper series)
- Krisztin & Piribauer, *A Bayesian approach for estimation of weight matrices in spatial
  autoregressive models* (arXiv 2101.11938; *Spatial Economic Analysis*)
- *Parameterizing Spatial Weight Matrices in Spatial Econometric Models*
  (*Political Analysis*, 2024)
- Ahrens & Bhattacharjee — two-step Lasso estimation of the spatial weights matrix
- *A Comparison Study on Criteria to Select the Most Adequate Weighting Matrix* (*Entropy*, 2019)
- **LeSage & Pace (2014), "The Biggest Myth in Spatial Econometrics," *Econometrics* 2(4)** —
  which argues, prominently, that estimates are *less* sensitive to the choice of W than
  practitioners assume

A single search on "estimating spatial weight matrix" returns all of these. Leaving
Innovation 2 as written is the highest-risk sentence in the document.

**What survives — and it is still interesting.**

Every paper above estimates W **from the same outcome panel used for inference** — endogenously,
statistically, in-sample, once. It is a *statistical estimation* problem. Your W is updated
**from an exogenous text stream arriving after estimation**. That is a different object:
W as **event-driven state**, not W as **estimated parameter**.

Paste-ready replacement paragraph:

> *"Prior work relaxes the fixed-W assumption by estimating W from the same outcome panel used
> for inference (Bhattacharjee & Jensen-Butler; Souza 2019; Krisztin & Piribauer). We make no
> claim to improve on those estimators. Our contribution is a different update channel: W is
> revised between estimation cycles from an exogenous, unstructured text stream — competitor
> facility announcements parsed by an LLM under validation gates — rather than re-estimated
> from the outcome data. To our knowledge this streaming, event-driven update channel has not
> been implemented, and we treat the underlying spatial estimators as given."*

**Then turn LeSage & Pace into your empirical test — this is the single best upgrade in this
report.** They claim results are robust to W. Your project is a natural experiment on that
claim. So pre-register the question:

> **RQ2 (rewritten): Does event-driven revision of W materially change the estimated
> cannibalisation coefficient θ, or are spatial causal estimates robust to W revision as
> LeSage & Pace (2014) suggest?**

- If θ **moves materially** → you have a result that pushes back on a well-known claim in
  spatial econometrics, using a new update channel. That is workshop-paper material.
- If θ **does not move** → you have a clean negative result that confirms LeSage & Pace under a
  novel perturbation, *and* an honest engineering finding: the mutable-W machinery is elegant
  but not decision-relevant.

**You cannot lose this bet.** Both outcomes are publishable and both are honest. Right now v3
implicitly assumes the answer is "yes it moves" and has no plan for "no it doesn't" — which is
exactly the scenario where an unprepared team panics and starts p-hacking.

#### Innovation 3 — "Faster reaction time than Amazon" → **DELETE**

Three independent problems:

1. **Category error.** You compare your 60-second compute step to Amazon's 7–30 day *review
   cycle*. Amazon's cycle is slow because a human commits $4M of capital, not because their
   software is slow. A reviewer will say you are racing a governance process with a for-loop.
2. **Unverifiable.** You have no access to Amazon's internal cadence. The "7 to 30 days" figure
   is uncited and cannot be sourced.
3. **Self-undermined.** §5.7.1 concedes the 60-second benchmark is measured with
   `HITL_REQUIRED = OFF`, while the demo ships with it **ON**. You are benchmarking a mode you
   do not deploy.

Delete it, or fold the latency measurement into Innovation 1 as a pure system metric
("median evidence-propagation latency, measured end-to-end on our own system, no external
comparison"). Innovations 1, 2 and 5 carry the contribution claim without it.

#### Innovation 4 — "First public tool for competitors and regulators" → **STRONGEST claim, wrong framing**

See [Question 3](#q3) — this deserves its own section. Short version: drop the adversarial
"help Walmart beat Amazon" framing, adopt the **civic / regulatory** framing, and cite the
institutions that already need this. Also drop the uncited
"$500,000 to $2,000,000 per project" consulting figure — an uncited dollar amount invites
exactly the challenge you don't want.

#### Innovation 5 — Auditable expansion decisions → **KEEP**

Real, cheap, and it pairs naturally with the citation you already have (Rojas & Nakamura,
*Auditability requirements for LLM-mediated enterprise decision systems*, CACM 2024). Tie it
explicitly to the identification gates from Innovation 1: auditability is not just an
audit *log*, it is the ability to replay a decision and see which mutation changed it.

### 1.4 Other prior work you must cite (or be caught by)

Your §2.1 currently says SCM assumes no interference and implies nobody has fixed it. That is
also falsifiable:

- *Bayesian Synthetic Control Methods with Spillover Effects* (arXiv 2408.00291)
- *A robust regression approach to synthetic control with interference* (arXiv 2411.01249)
- *A review of spatial causal inference methods for environmental and epidemiological
  applications* (arXiv 2007.02714 — Reich et al., *International Statistical Review*)
- *Exploiting neighborhood interference with low-order interactions* (*Journal of Causal
  Inference*)

On the retail-expansion / cannibalisation side — this is your actual research question, in
structural form, already published:

- *Demand Expansion and Cannibalization Effects from Retail Store Entry: A Structural Analysis
  of Multichannel Demand*, **Management Science** 68(12), 2022, 8829–8856
- *Empirical Investigation of Retail Expansion and Cannibalization in a Dynamic Environment*,
  **Management Science** 58(11), 2012, 2001–2018
- Caoui, Hollenbeck & Osborne, *Dynamic Entry and Spatial Competition: An Application to Dollar
  Store Expansion*
- Schorung, Lecourt & Dablanc (2023), *Assessing the spatial patterns of Amazon warehouse
  network in the United States* (WCTR)
- *The Impact of Amazon Facilities on Local Economies*, **Journal of Policy Analysis and
  Management** (2025)

**Your delta against the Management Science papers:** they use structural demand models on
proprietary firm data at store grain, in a static information environment, with no artifact.
You use reduced-form spatial causal inference on public data at ZCTA grain, for a
service-tier (not store) expansion, with a shipped tool. That is a legitimate, statable delta.

### 1.5 The one-paragraph novelty answer

> *"Amazon does this internally, and Houde, Newberry and Seim published the definitive academic
> treatment in Econometrica in 2023 — for the 2-day fulfilment network, at state grain, through
> 2018, on data no one else can obtain. Our contribution is not that the problem is new. It is
> three specific things. First, we reproduce the decision at ZCTA grain for the sub-24-hour
> network using entirely public data, and we quantify how much of Amazon's revealed siting
> behaviour is explainable from public data alone — a number nobody has published. Second, we
> identify a failure class in LLM-agent systems that the existing gated-write literature does
> not cover: writes that preserve data integrity while destroying inferential integrity, and we
> propose two identification gates that catch them. Third, we test empirically whether
> event-driven revision of the spatial weight matrix moves causal estimates at all — which is a
> direct test of LeSage and Pace's claim that spatial results are robust to W. We do not claim
> the underlying estimators are new; we claim the combination, the grain, the data regime, and
> the two failure-mode findings are."*

---

<a name="q2"></a>
## 2. Question 2 — "What is the model confidence and prediction accuracy?"

### 2.1 The blunt answer: as written, the proposal cannot answer this

This is the most damaging of the three questions, because there is a structural problem
underneath it.

**§4.2 says the target variable is constructed:**

> *"The target variable — same-day-Prime order volume per ZCTA per month — is proxied via Amazon
> 10-K aggregate volume disclosures distributed across ZCTAs **proportionally to a composite of
> ACS e-commerce-friendliness features and Yelp retail density**."*

**§5.3 then fits a ZINB on ACS and Yelp features to predict that target.**

**That is circular.** You are predicting a variable you manufactured out of the predictors.

**Worked example.** Suppose your allocation rule is
`orders_i = TotalOrders × (0.6·income_i + 0.4·yelp_i) / Σ(0.6·income + 0.4·yelp)`.
Now you fit a model with `income` and `yelp` on the right-hand side. It will recover the
allocation almost perfectly — you might see **MAPE of 3–5%**. That will *look* like a triumph
and will actually be **proof of circularity**. The model has learned your arithmetic, not
Amazon's behaviour. A reviewer spots this in under a minute, and it invalidates Objective 1
as written.

**Second, separate problem: MAPE is the wrong metric for a zero-inflated count.** MAPE divides
by the actual value. Your entire modelling premise is that many ZCTAs are structural zeros.
Division by zero is undefined, so you must either drop the zeros — destroying the reason you
chose ZINB — or report an infinite MAPE. (Hyndman & Koehler 2006, *Another look at measures of
forecast accuracy*, is the standard citation; a reviewer in forecasting will cite it at you.)

So: the headline accuracy number is measured on a fabricated target using a metric that cannot
be computed. Both must change.

### 2.2 Layer 0 — Fix the target variable

Three options, ranked. **Do Option A as the headline and Option C as the fallback framing.**

#### Option A (recommended) — change the estimand to something you can actually observe

Stop asking *"how many same-day orders will ZCTA i generate?"* (unobservable) and start asking:

> **"Has Amazon enabled same-day service in ZCTA i, and when?"**

That is **genuinely observable** from public sources:
- Amazon's own delivery-speed checker, queried by ZIP
- MWPVL facility inventory with open dates
- Amazon's public announcements — including the June 2025 commitment of **$4bn+ to reach
  4,000+ rural communities with same-day/next-day delivery by end of 2026**

You immediately get real labels, and therefore real metrics.

| | Before (v3) | After (Option A) |
|---|---|---|
| Target | Fabricated volume | Observed service enablement + date |
| Model | ZINB only | Discrete-time hazard / panel logit (ZINB demoted to secondary) |
| Metrics | MAPE (undefined) | **AUC-ROC, PR-AUC, Brier score, calibration curve, ECE, precision@k** |
| Validation | Held-out ZCTAs | **Out-of-time backtest** |
| Framing | "demand forecast" (indefensible) | "Amazon-consistent expansion desirability" (**literally true**) |

Two things this unlocks that nothing else in the proposal can:

1. **It makes §4.5.1's framing honest.** v3 already hedges to "Amazon-consistent expansion
   desirability rather than objective demand." Under Option A that stops being a hedge and
   becomes the actual estimand. The hedge disappears because you are no longer pretending.

2. **It gives you a real out-of-time backtest.** Train on facilities open through **2023**.
   Predict openings in **2024–2025**. Score against what Amazon actually did.
   **This is the single most persuasive slide you can put in front of the professor** and
   nothing else in the proposal comes close. "We predicted 2024–25 openings from 2023 data and
   got AUC 0.84, precision@100 of 0.61" is an answer to "what is your accuracy". "MAPE 25% on a
   synthetic target" is not.

Honest, defensible target numbers to write into Objective 1:
`AUC-ROC 0.80–0.88` · `PR-AUC ≫ base rate` · `ECE < 0.05` · `precision@100 ≥ 0.60`.
Do **not** promise AUC 0.95 — with public data only, that would itself be a red flag.

#### Option B — keep volume, but find an independent target

Source a volume signal not built from your own covariates: foot-traffic panels (SafeGraph /
Advan — mostly not free), Census e-commerce parcel statistics, or BLS QCEW warehouse
employment by county as an intensity proxy. Weaker and mostly costs money. Not recommended
inside the budget.

#### Option C — keep the synthetic target, but relabel it honestly

If you keep the volume model, say plainly:

> *"Objective 1(b) evaluates whether ZINB recovers a known data-generating process under
> realistic covariate structure. It is a **specification-recovery exercise**, not a demand
> forecast. Reported fit is not evidence about Amazon's true order volumes."*

Then **every downstream NPV figure must carry the label "conditional on the volume-allocation
assumption."** This is the minimum-effort fix, it costs nothing, and it is still far better
than v3.

### 2.3 Layer 1 — Metric replacement table

| v3 metric | Problem | Replace with |
|---|---|---|
| `MAPE < 25%` (Obj 1) | Undefined at y=0; measured on circular target | Binary outcome: **AUC, PR-AUC, Brier**. Count outcome: **Poisson/NB deviance, RMSLE, MASE** |
| `RQ1 "within 15%"` | Contradicts Objective 1's 25% | Delete the number; point RQ1 at the Objective-1 metric set |
| `structural-zero F1 > 0.85` | F1 hides base rate; threshold-dependent | **PR-AUC + calibration curve**; state the chosen threshold and the reason |
| `Spearman > 0.80` (ZINB vs LightGBM) | Reasonable — keep | Keep, but add a **bootstrap CI on the correlation itself** |
| `SCM pre-treatment RMSE < 8% of mean` | Necessary but not sufficient | Add **placebo / permutation inference** (in-space and in-time) and the **post/pre RMSPE ratio p-value**. This is the Abadie–Diamond–Hainmueller standard; its absence is a red flag to any causal-inference reviewer |
| `Agent 85% of 40 questions` | n=40; single evaluator; self-authored benchmark | See §2.5 |
| `metro CapEx within 25%` | Good — keep | Keep. It is the only externally checkable number in the whole system. Feature it |

### 2.4 Layer 2 — Uncertainty that is honest about model risk

The Monte Carlo (§5.6) and bootstrap (§5.6.1) quantify **parameter** uncertainty. They do not
touch **specification** uncertainty or **proxy** uncertainty — which, in a project built on
proxies, dominate. Three additions:

**(a) Conformal prediction — highest return on effort in this entire report.**
Split conformal on the demand model gives **distribution-free, finite-sample coverage
guarantees**. It is roughly 30 lines of code (Angelopoulos & Bates 2021, *A Gentle Introduction
to Conformal Prediction*, arXiv 2107.07511). It lets you say:

> *"Our 90% prediction intervals empirically covered 90.2% of held-out ZCTAs."*

That is a **verified** coverage claim, not a modelling assumption. It is the most credible
sentence you can put in a methods paper for the least work. If you implement one thing from
this report, implement this.

**(b) Tornado / sensitivity plot over the 8 cost buckets.** One chart showing which bucket the
NPV ranking is actually sensitive to (almost certainly real estate and wages). This answers
"how do you know your cost model isn't garbage" — you don't need every bucket to be right, you
need the two that matter to be right, and the plot proves which two those are.

**(c) Decision-relevant accuracy — "Top-K Rank Stability".** This is a differentiator, and
almost no student project reports it. The executive's real question is not "what's your MAPE",
it's *"if your inputs are wrong within their uncertainty bands, does your recommendation
change?"* So report, across the 10,000 Monte Carlo draws:

> *"ZCTA 94608 appears in the top 10 in 87% of draws. ZCTA 94612 appears in 34% of draws — its
> ranking is not stable and should not drive a capital decision."*

That is the number a decision-maker needs, it falls straight out of simulation you are already
running, and it reframes uncertainty from an apology into a product feature.

### 2.5 Layer 3 — Agent accuracy, done properly

**Ground your target in the literature before you set it.** On the BIRD benchmark (Li et al.,
NeurIPS 2023, *Can LLM Already Serve as a Database Interface?*, arXiv 2305.03111), the best
public systems sit around **80% execution accuracy** (Gemini-SQL2 reported 80.04% on the BIRD
single-model leaderboard) against a **human baseline of ~92.96%**.

So v3's Objective 3 — **85% on a 40-question benchmark you wrote yourself** — is claiming
above-SOTA performance on an unfalsifiable test set. A reviewer who knows the field will read
that as either naive or unserious. Fixes:

1. **Grow n and report a confidence interval.** At n=40, an observed 85% has a 95% Wilson
   interval of roughly **[71%, 93%]** — so a "success" at 85% and a "failure" at 72% are
   statistically indistinguishable. Go to **n ≥ 100** and report the interval explicitly.
2. **Use execution accuracy as the primary metric**, not human judgement — does the generated
   SQL return the same result set as a gold query? Objective, reproducible, field-standard.
   Keep a small human-judged subset only for narrative-quality questions.
3. **Stratify by difficulty**: lookup / aggregation / spatial join / multi-hop. Aggregate
   numbers hide that spatial joins are exactly where these systems break, and your warehouse is
   spatial. Per-tier reporting is more informative and more honest.
4. **Audit your own gold set.** *Pervasive Annotation Errors Break Text-to-SQL Benchmarks and
   Leaderboards* (arXiv 2601.08778) shows that even curated public benchmarks carry
   substantial label noise. Report an audit of a sample of your gold queries.
5. **If you use LLM-as-judge** (you cite Zheng et al.), acknowledge its limits: position bias
   (*Judging the Judges*, arXiv 2406.07791), reliability-without-validity effects
   (arXiv 2606.19544), coin-flip behaviour on hard items (arXiv 2606.13685). Mitigations:
   randomise option order, use two judges plus a human tiebreak, and **report Cohen's κ**.

**And pre-register the minimum detectable effect for the §5.10 ablation.** With n=200 press
releases and a gate-hit rate near 0.8, the standard error is ≈2.8pp, so differences below
roughly **8pp** between Grok / Claude / GPT are not distinguishable. If the three models come
out at 82 / 84 / 85% and you have not said this in advance, you will be forced either to
over-claim a difference that isn't there, or to admit the study was underpowered. Stating the
MDE up front converts a weakness into evidence of rigour.

### 2.6 Layer 4 — What to say when the honest answer is "we can't measure that"

Keep this sentence ready:

> *"For the observable outcome — whether and when Amazon enables same-day service in a ZCTA — we
> report AUC, calibration, and an out-of-time backtest against 2024–25 openings. For the
> unobservable outcome — dollar NPV — we make **no accuracy claim**, because no public ground
> truth exists. Instead we report empirically validated interval coverage, rank stability under
> uncertainty, and we externally validate the one component that can be checked: metro-level
> capital expenditure against Amazon's 10-K disclosures."*

Precision about what you *cannot* measure reads as rigour. Vagueness reads as evasion.

---

<a name="q3"></a>
## 3. Question 3 — "It's public data. What's the use? Where's the use case?"

### 3.1 Reframe: the professor is asking "who makes a different decision because this exists?"

v3's answer (Innovation 4) is essentially *"Walmart, and consultants are expensive."* That is
thin, partly uncited, and academically weak. Here are four users with a **decision**, a
**counterfactual**, and an **institution** behind each — ordered by strength.

### 3.2 User 1 — Municipal planners and air-quality districts ⭐ *build the demo for this one*

**Decision:** approve, condition, or deny a warehouse permit; size mitigation requirements;
decide whether to offer a tax abatement.

**Why they need a forecast, with a real institution attached:**
**South Coast AQMD Rule 2305 — the Warehouse Indirect Source Rule (WAIRE Program)** — adopted
2021 and **approved by the US EPA**, requires warehouses at or above 100,000 sq ft to earn
emission-reduction points or pay mitigation fees. Other regions are actively considering
copies. A district that can forecast *where* warehouses will appear can plan mitigation
capacity instead of reacting to permit applications one at a time.

**The killer feature — and it is already in your model:**

> **"Would Amazon have built here anyway?"**

Your Heckman selection equation's propensity score *is* the answer to the tax-abatement
counterfactual. Cities routinely grant abatements to attract logistics facilities without ever
computing whether the facility was coming regardless — see *The Impact of Amazon Facilities on
Local Economies* (JPAM 2025). A city that learns "Amazon's revealed preference already ranks
you in the top decile; you are in the 60%-probability band for an opening within 18 months" has
just saved itself a subsidy. **That is public money, and it is the same model output read in
the opposite direction.**

**Deliverable:** one Streamlit page — *Public Planning View* — showing propensity score,
expected timing window, and a plain-language readout. Roughly a day of work on top of what you
are already building.

### 3.3 User 2 — Community and environmental-justice organisations

**Decision:** where to organise, comment, or litigate — **before** the permit application lands,
not after it is approved.

**Evidence base (all citable, all public):**
- METRANS, *Location of warehouses and environmental justice: Evidence from four metros in
  California*
- Urban Freight Lab, *Logistics Sprawl and Environmental Justice* — documents *"a significant
  spatial and racial mismatch between delivery supply and demand"*
- GWU Milken Institute School of Public Health — warehousing and health-harming pollutants
- Union of Concerned Scientists, *Warehouses as an Environmental Justice Issue*
- EDF, *Indirect Source Review: an answer to mega-warehouse pollution*

**This is where §4.5.5 stops being a compliance checkbox and becomes the product.** Overlay
predicted expansion probability on **EPA EJScreen** (free download, joins on census geography)
or CalEnviroScreen, and you produce a *predicted warehouse-burden map by demographic stratum*
that **does not currently exist publicly**.

**Estimated effort: ~2 days.** It converts the project from "Amazon fan-fiction" into
public-interest analytics, and it gives the professor something to be proud of rather than
something to be nervous about. **Highest-impact single addition to the deliverable.**

### 3.4 User 3 — Competing retailers and logistics firms *(keep, demote, de-fang)*

Legitimate — Walmart / Target / Costco defensive siting, 3PL lease decisions — but reframe from
"adversarial tool against Amazon" to **market-structure transparency**. And **delete the
"$500,000 to $2,000,000 per consulting project" figure** unless you can cite it. An uncited
dollar amount is a free attack surface.

### 3.5 User 4 — Researchers: the reproducibility contribution

This is the one the professor will value most academically. The *Econometrica* paper is not
reproducible by a student — the data are licensed and the code is not runnable. Your artifact
is a **public, open, re-runnable testbed for spatial expansion methods**:

- Publish the ZCTA-level panel of Amazon facility openings
- Publish the derived covariate matrix
- Publish the evaluation harness

Then anyone can swap in causal forests, DoubleML, or a GNN and compare against your baseline.
**"Dataset + benchmark" is a recognised publishable contribution category**, and it has value
entirely independent of whether your point estimates are right.

### 3.6 The framing sentence — use this verbatim

> *"Proprietary data produces conclusions nobody can check. Public data produces conclusions
> anyone can check. For a decision that municipalities, regulators, and affected communities
> have legal standing to contest, checkability **is** the product. Amazon's internal model is
> more accurate and less useful to everyone except Amazon."*

### 3.7 And the argument that makes the accuracy ceiling a finding rather than an excuse

> *"A central output of this project is a number nobody has published: **how much of Amazon's
> revealed siting behaviour is explainable from public data alone?** If it is 70%, that is a
> strong result about the transparency of logistics decisions. If it is 40%, that is a strong
> result about their opacity — and it tells regulators exactly how much disclosure would be
> needed to close the gap. Either answer is a contribution."*

You cannot lose that framing, and it directly disarms the "but it's only public data"
objection by making the public-data constraint the research question rather than the
limitation.

---

<a name="corrections"></a>
## 4. Correction plan before implementation

### P0 — Fatal if the professor finds them first. Fix before submitting v4.

| # | Issue | Location | Fix |
|---|---|---|---|
| 1 | **Circular target variable** — predicting a variable built from the predictors | §4.2, §5.3 | Adopt Option A (observable service-enablement outcome); relabel volume model as specification recovery |
| 2 | **Houde, Newberry & Seim (Econometrica 2023) not cited** | §2.5, §6 | Cite + add the delta table from §1.2 |
| 3 | **Innovation 2 factually false** — W-estimation literature exists | §5.8 | Replace with the narrowed claim in §1.3; add the LeSage–Pace robustness test |
| 4 | **§2.1 implies SUTVA problem unsolved** — SCM-with-interference literature exists | §2.1 | Cite arXiv 2408.00291, 2411.01249, 2007.02714; restate the delta |
| 5 | **MAPE undefined for zero-inflated counts** | Obj 1, §5.3 | Replace per §2.3 table |
| 6 | **Budget self-contradiction**: table says total $35 / hard cap $100 / "automatic B if exceeded"; §9 prose says $200 cap / $180 spend / $300 available | Budget table + §9 | Resolve to one budget. **Get written instructor sign-off if exceeding $100.** See §5 |
| 7 | **"Ten pilot metros" followed by five metros listed**; contradicts §4.5.4 | §4.3 | Rewrite §4.3 — it is stale v2 text |
| 8 | **Innovation 3 indefensible** | §5.8 | Delete or reduce to an internal latency metric |

### P1 — Substantive rigour. These are what actually answer the professor.

| # | Addition | Effort | Why |
|---|---|---|---|
| 9 | **Out-of-time backtest** (train ≤2023 → predict 2024–25 openings) | 3 d | Most persuasive single result in the project |
| 10 | **Conformal prediction intervals** | 1 d | Verified coverage claim; best credibility-per-hour in the report |
| 11 | **SCM placebo / permutation inference + RMSPE-ratio p-value** | 2 d | Abadie standard; its absence is a red flag |
| 12 | **Identification gates 5 & 6** on `Warehouse_Mutator` | 2 d | This is the real Innovation 1 |
| 13 | **"Does W actually matter?" test** (LeSage–Pace) | 2 d | Win-either-way result |
| 14 | **EJScreen equity overlay + Public Planning view** | 2 d | Answers Q3 concretely |
| 15 | **Top-K rank stability** reporting | 0.5 d | Decision-relevant accuracy; differentiator |
| 16 | **Cost-bucket tornado plot** | 0.5 d | Defends the cost model cheaply |
| 17 | Agent eval: n≥100, execution accuracy, Wilson CIs, difficulty tiers | 2 d | Current target is above-SOTA on a self-authored test |
| 18 | Pre-register MDE for the §5.10 ablation | 0.5 d | Prevents an unwinnable result |
| 19 | Reconcile RQ1 (15%) vs Objective 1 (25%) | 5 min | Internal contradiction |
| 20 | **Rural structural-zero assumption is now contradicted by events** — Amazon committed $4bn+ in June 2025 to reach 4,000+ rural communities by end-2026. §2.3's "rural ZCTAs generate zero same-day demand regardless of income" is no longer true | 0.5 d | Reframe zero-inflation as *service availability*, not latent demand — another argument for Option A. Also a great topicality hook |
| 21 | **Add MAUP to §4.4 limitations** — ZCTAs are postal delivery constructs, not statistical areas, and they change annually. Offer a robustness check at H3 hex grain | 1 d | Spatial reviewers *always* ask this (Openshaw 1984) |

### P2 — Document hygiene. Cheap, and their absence signals carelessness.

- **Objective 1 appears twice** with contradictory text ("two metros" vs "three metros") — the v2
  paragraph was never deleted
- **§7.3's body text is stranded at the top of the document, inside the Table of Contents**; the
  TOC line itself reads `7.3 Joint Ownership 217.4 Joint Ownership 217.4 Joint Ownership`
- **The `5. Proposed Methods` heading is missing from the body entirely** — the document jumps
  from §4.5.5 to §5.1
- **§5.11 is cited but does not exist** (referenced from §5.10)
- **§4.5.1 cites "Section 5.5 (NPV Optimizer)"** — §5.5 is the cost model; NPV is §5.6
- **§5.7.1 refers to "the four gates in Section 5.7"** — §5.7 never lists them; they appear only
  in §5.8. Move the list into §5.7
- **§5.9 and §5.10 are missing from the Table of Contents**
- **Two separate reference lists** with duplicated entries (Wager & Athey, Yao et al.,
  Chen & Guestrin all appear twice)
- **Reference [11] is wrong**: *"Chen, T., & Guestrin, C. (2016). LightGBM: A scalable tree
  boosting system"* — that paper is **XGBoost**. LightGBM is Ke et al. (2017), which you cite
  correctly elsewhere. Since §5.3.3 explicitly argues LightGBM beats XGBoost on your
  categorical features, citing the XGBoost paper as LightGBM is the kind of error a methods
  reviewer circles in red
- **Card & Krueger (1994)** cited in §5.8 but absent from both reference lists
- Angrist & Pischke, Glaeser & Gyourko, Zheng et al., Chen et al. (2024), Rojas & Nakamura all
  appear in the references but are never cited in the text
- **Wei et al.** cited as 2022 in text, listed as 2023 in references
- **"instacart"** → "Instacart" (§1.1)
- §2.1: the Reilly's Law passage is glued onto the end of the "Our delta" paragraph with no
  paragraph break
- **Timeline table Week 3 still says "5 pilot metros"** while scope is 10
- **P3 is never listed as lead for any week** (Week 6, the dashboard week, is "P1 + P2") despite
  §7.3 assigning her the dashboard, deployment, and executive deck. This reads badly against a
  rubric that requires each member to own a unique area — fix the Lead column

---

<a name="scope"></a>
## 5. Scope challenge — what I would cut, and the honest tradeoff

Your own note estimates the Tier 3 additions at **+20–24 person-days**. My read is that this is
**underestimated by roughly 2×** once integration and debugging are counted. But the more
important point is *which* additions:

**Cut §5.9 — the fine-tuned Phi-3.5-mini narrator.**
A LoRA fine-tune on a 500-example corpus you must first *write by hand*, plus Modal GPU setup,
plus a BLEU-based tone evaluation, plus a fallback path. Estimated 5–7 days. Contribution to
the professor's three questions: **zero**. It is an optimisation of dashboard copy.

**Demote §5.10 — the three-model LLM ablation — to a stretch goal.**
Genuinely interesting, but (a) it costs $60 of a contested budget, (b) as shown in §2.5 it is
probably underpowered at n=200, and (c) it answers "why Grok?", a question nobody has asked.

**Reallocate to P1 items 9–16.** Those cost roughly the same in days, cost **nothing** in
dollars, and they answer all three of the professor's questions directly.

**Secondary benefit:** cutting §5.9 and §5.10 removes $60 of LLM spend and the $30 Modal
budget, dropping estimated spend from $180 to roughly $90 — **back under the $100 cap**, which
dissolves correction #6 entirely and removes the "automatic B" exposure.

**The honest tradeoff, so you can decide rather than just take my word:** you lose two
impressive-sounding components. If the rubric rewards technique count and breadth of tooling,
that is a real cost, and I could be wrong about the professor's priorities. But the three
questions he actually asked are all about **substance** — novelty, confidence, and use — not
about surface area. A project that cannot answer "what is your accuracy" does not get rescued
by having fine-tuned a language model. Your call, but I would make the cut.

---

<a name="viva"></a>
## 6. Viva scripts — 60-second answers

**Q: "Amazon already does this. What's new?"**
> "The definitive academic treatment is Houde, Newberry and Seim in *Econometrica* 2023 — the
> 2-day fulfilment network, state grain, through 2018, on data nobody else can obtain. We do
> the sub-24-hour network at ZCTA grain through 2026 on entirely public data, and we ship a
> running tool. Beyond the reproduction, we contribute two things the literature doesn't have:
> a failure class in LLM-agent systems where a write passes every data-integrity gate but
> breaks a causal identification assumption — with two new gates that catch it — and a direct
> empirical test of whether event-driven revision of the spatial weight matrix actually moves
> causal estimates, which tests LeSage and Pace's robustness claim. We don't claim the
> estimators are new. We claim the grain, the data regime, and those two findings are."

**Q: "What's your model confidence and accuracy?"**
> "It depends on which output, and we're explicit about that. For the observable
> outcome — whether and when Amazon enables same-day in a ZCTA — we backtest: train on
> facilities open through 2023, predict 2024–25 openings, and report AUC, calibration error,
> and precision at 100. For the unobservable outcome — dollar NPV — we make no accuracy claim,
> because there is no public ground truth. Instead we report conformal prediction intervals
> with empirically verified coverage, and rank stability: how often a ZCTA stays in the top ten
> across ten thousand Monte Carlo draws. And we externally validate the one thing that can be
> checked — metro-level capital expenditure against Amazon's 10-K, targeting within 25%."

**Q: "It's public data. Who actually uses this?"**
> "Three users with real decisions. Air-quality districts operating warehouse indirect-source
> rules — South Coast AQMD's Rule 2305 is EPA-approved and others are copying it — need to
> forecast where warehouses appear so they can plan mitigation capacity. City councils deciding
> on tax abatements need to know whether Amazon would have built there anyway; our Heckman
> propensity score *is* that counterfactual, and it's public money. And environmental-justice
> organisations need to know where the burden lands before the permit is filed, which is why we
> overlay predicted expansion on EPA EJScreen by demographic stratum — a map that doesn't
> currently exist publicly. Proprietary data produces conclusions nobody can check. For a
> decision that communities have standing to contest, checkability is the product."

---

## Appendix — companion file

Paste-ready bibliography additions with a verification checklist:
`REFERENCES_to_add_v4.md`
