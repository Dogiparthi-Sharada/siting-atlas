# Handbook Part 6 — The Agent and the Six Gates

**What an LLM agent is, what ours does, and the one genuinely novel idea in the
project: a write can be perfectly safe for the data and still destroy the
analysis.**

---

## 6.0 What is built, and what is not

```
  +--------------------------------------------------------------------+
  |  THE SIX GATES ARE REAL AND THEY RUN ON REAL DATA.                 |
  |                                                                    |
  |  All six are implemented and all six execute against the actual    |
  |  33,791-ZCTA DuckDB warehouse - not a fixture, not a mock. Every   |
  |  invocation writes an audit record, INCLUDING the invocations      |
  |  that end in a rejection.                                          |
  |                                                                    |
  |    SchemaGate              gate 1   data integrity                 |
  |    GeocodingGate           gate 2   data integrity                 |
  |    ConfidenceGate          gate 3   data integrity                 |
  |    AuditLogGate            gate 4   data integrity                 |
  |    DonorPoolIntegrityGate  gate 5   INFERENTIAL integrity          |
  |    EstimateStabilityGate   gate 6   INFERENTIAL integrity          |
  |                                                                    |
  |  Source: src/siting_atlas/agent/, entry point                      |
  |    python -m siting_atlas.agent.runner --demo-plano                |
  |  Records: outputs/audit/<mutation_id>.json  and                    |
  |           outputs/audit/mutations.jsonl (append-only)              |
  +--------------------------------------------------------------------+
```

**In a project whose headline model failed, this is a component that works, and
you should say so plainly.** The gates are not a slide; they execute.

### But be equally plain about the three things that do NOT exist

```
  +--------------------------------------------------------------------+
  |  1. THE THREE TOOLS IN SEC. 6.3 ARE A DESIGN.                      |
  |     There is no SQL_Generator, no Spatial_Visualizer and no        |
  |     Warehouse_Mutator in src/. There is no MCP server and no       |
  |     LLM call anywhere in the package. What exists is the GATE      |
  |     PIPELINE that a mutator would have to clear, plus a runner     |
  |     that feeds it a mutation from a JSON file or the built-in      |
  |     Plano demo.                                                    |
  |                                                                    |
  |  2. GATE 5 GUARDS A STUDY THAT WAS NEVER BUILT.                    |
  |     Synthetic control is the project's second estimand and not     |
  |     one line of it exists (HANDBOOK_03_CAUSAL.md, Sec. 3.0).       |
  |     Gate 5 protects the donor-pool MACHINERY, not a published      |
  |     estimate. It escalates often, because the pool is thin.        |
  |                                                                    |
  |  3. GATE 6 IS NOT WIRED TO THE PROJECT'S CURRENT MODEL.            |
  |     Gate 6 CAN compute a delta today - it refits on the real       |
  |     panel and returns one. But what it refits is the RETIRED       |
  |     hazard model, not the conditional choice model that is now     |
  |     the project's siting model. So the number it produces is a     |
  |     coefficient of a specification the project has withdrawn.      |
  |     Its refusal path, for when no target exists at all, is still   |
  |     the best thing in the module. See Sec. 6.7.1.                  |
  +--------------------------------------------------------------------+
```

> **A claim withdrawn.** Box item 3 used to read "GATE 6 CANNOT CURRENTLY
> COMPUTE A DELTA - AND SAYS SO." That is false on two counts, both checked on
> 2026-09-14. First, `siting_atlas.agent.runner.build_estimator()` returns the
> basis string `refit-on-real-panel` and a `HazardThetaEstimator`, which
> computes a baseline theta of 4.48e-05 on the term `households` — the gate
> runs. Second, the premise behind the old wording — that there was no
> estimate in the project to re-run — stopped being true when the conditional
> choice model was fitted. Rewritten to say what is actually wrong, which is a
> wiring gap rather than an absence.

**Why the honest version is still a strong story.** The claim in this chapter
was never "we built a chatbot". It was "here is a failure class nobody guards
against, and here is a working control for it". The control is built and
tested. The chatbot that would have supplied it with mutations is not, and
nobody should care - Sec. 6.1 explains why the chatbot was the least
interesting part from the beginning.

---

## 6.1 Start here: why the agent is *not* the headline

Before any of the mechanics, internalise this positioning.

> **In 2026, "I built an AI chatbot over a database" is close to a negative
> signal.** Every applicant has a retrieval-augmented-generation project. It
> reads as "followed a tutorial."

So the agent is not the contribution. **The contribution is what we discovered
while making it safe.** Lead with the failure class and the gates; the chatbot is
plumbing.

If you take one thing from this Part, take §6.6.

---

## 6.2 The vocabulary, defined properly

### 6.2.1 LLM

A model trained to predict the next token of text, which turns out to be enough
to follow instructions, write code, and extract structure from prose. For us it
does exactly one useful thing: **turn unstructured text into structured records.**

> **Example.** Input: *"Walmart today announced a new 350,000 sq ft sortation
> centre in Plano, Texas, opening Q3."* Output:
> `{operator: "Walmart", type: "SORTATION", city: "Plano", state: "TX",
> sqft: 350000, open_quarter: "2026Q3"}`
>
> That transformation used to be a manual research job. That is the whole reason
> an LLM is in this project.

### 6.2.2 RAG — Retrieval-Augmented Generation

Instead of relying on what the model memorised in training, **retrieve relevant
documents first** and let the model answer from them.

> **Why it matters here.** Asked "where did Walmart open facilities in 2025?" a
> bare model will confidently invent an answer. With retrieval, it reads our
> actual facility table and answers from it. The difference between fiction and
> a query.

### 6.2.3 ReAct — Reasoning + Acting

A loop pattern (Yao et al., 2023). Rather than answering in one shot, the model
alternates:

```
   THOUGHT       "I need the facility count for Texas."
       |
       v
   ACTION        SQL_Generator("SELECT COUNT(*) ... WHERE state='TX'")
       |
       v
   OBSERVATION   "47"
       |
       v
   THOUGHT       "Now I need last year's, to compute growth."
       |
       v
   ACTION        ...
       |
       v
   (loop until it can answer)
```

**Why it beats one-shot:** each step is grounded in a real result rather than a
guess, and the trace is inspectable — you can see *why* it answered.

### 6.2.4 MCP — Model Context Protocol

A standard interface for exposing tools to a model (Anthropic, 2024). Rather than
hard-wiring tools into one application, you expose them as MCP servers and **any
compliant client can use them**.

> **The practical benefit.** Our three tools work inside our app, and also from
> any other MCP client. The tool surface is not locked to our UI. That is
> genuine portability, not just a checkbox.

---

## 6.3 Our three tools

| Tool | Access | What it does |
|---|---|---|
| `SQL_Generator` | **read-only** | Natural language → DuckDB SQL → results |
| `Spatial_Visualizer` | **read-only** | Query result → choropleth or hexbin map |
| `Warehouse_Mutator` | **WRITE** | Competitor news → facility record → writes to the warehouse |

Two are unremarkable. The third is the interesting one, and the dangerous one.

> **All three are specified, none is implemented** (Sec. 6.0). Read this section
> as "the tool surface the gates were designed against". What the codebase
> actually accepts is a `Mutation` object - the same `(lat, lon, operator,
> facility_type, zcta, confidence)` record an extractor would produce - handed
> to the pipeline from a JSON file or from the built-in Plano demo. That is
> deliberate and defensible: **the gates are the contribution, and gates are
> tested by feeding them mutations, not by generating the mutations with an
> LLM first.** Swapping a real extractor in later changes nothing downstream of
> the `Mutation` boundary.

### What the mutator actually does

```
   press release
        |
        v
   LLM extracts (lat, lon, operator, facility_type, open_date)
        |
        v
   writes to dim_logistics_node
        |
        v
   ... which changes W
        |
        v
   ... which changes the donor pool
        |
        v
   ... which changes theta
        |
        v
   ... which changes every NPV downstream
```

**A single row insert propagates into a causal estimate.** Hold that thought.

---

## 6.4 The four standard gates

These protect **data integrity**, and they have extensive prior art.

| Gate | Question | Failure it prevents |
|---|---|---|
| 1 — Schema conformance | Are the fields present and correctly typed? | Malformed rows breaking queries |
| 2 — Geocoding reachability | Do these coordinates resolve to a real place? | Hallucinated locations |
| 3 — Confidence threshold | Is the extraction confidence above the bar? | Guesses entering as facts |
| 4 — Audit-log immutability | Is the write recorded in an append-only log? | Silent, untraceable changes |

**It would be wrong to claim no prior work introduces this pattern.** Existing work includes a survey of safe-LLM-agent specification and
enforcement (arXiv:2608.14590), privacy-preserving alignment for database
interfaces (arXiv:2511.06778), text-to-SQL vulnerability analysis
(arXiv:2211.15363), an IEEE S&P 2026 paper on securing AI assistants, and shipped
open-source write gates.

Human-in-the-loop write approval is also a standard product feature. So "LLM
proposes, gates validate, human approves" is well-trodden.

---

## 6.5 The insight — where all that prior art stops

Read the list above again and notice what every one of them protects:

> **Do not corrupt rows. Do not leak records. Do not drop tables.**

All of it protects **the data**.

**Our write target is not a data table. It is a parameter of a causal
estimator.** And that creates a failure class nobody has studied, because in
every prior setting the worst case was "the data is wrong," which the gates
catch.

Here the worst case is: **the data is right, and the inference is wrong.**

---

## 6.6 The worked example — the most important thing in this handbook

Learn this cold. It is the best sixty seconds you have in any interview or viva.

```
   PRESS RELEASE
   "Walmart opens a new sortation centre in Plano, TX"
        |
        v
   LLM extracts:  (33.0198, -96.6989, SORTATION, Walmart)
        |
        v
   +--------------------------------------------------------+
   |  GATE 1  schema conformance ..................  PASS    |
   |  GATE 2  geocoding reachability ..............  PASS    |
   |          (Plano is real, coordinates resolve)           |
   |  GATE 3  confidence threshold (0.94) .........  PASS    |
   |  GATE 4  audit-log immutability ..............  PASS    |
   +--------------------------------------------------------+
        |
        |  ALL FOUR GATES PASS. THE DATA IS PERFECT.
        |  System reports SUCCESS.
        v
   ~~~~~~~~~~~~~~~~ BUT DOWNSTREAM ~~~~~~~~~~~~~~~~
        |
        v
   W changes           which ZIPs count as neighbours
        |
        v
   donor pool changes  a Dallas control ZIP is now adjacent to a
        |              competitor facility -> contaminated
        v
   theta changes       the cannibalisation estimate moves
        |
        v
   NPV moves by MILLIONS
        |
        v
   +--------------------------------------------------------+
   |  NOTHING IN GATES 1-4 CHECKED ANY OF THIS.              |
   |                                                        |
   |  The write is safe. The inference is broken.           |
   +--------------------------------------------------------+
```

**Say the punchline exactly:** *"The data is fine. The inference is broken."*

---

## 6.7 The two gates that are our contribution

### Gate 5 — donor-pool integrity

**The question:** does this mutation move a unit currently serving as a *control*
into a *treated or contaminated* state?

**Why it matters.** Synthetic control builds a counterfactual from untreated
donor units. If one of them silently becomes treated — or adjacent to a new
facility and therefore contaminated — the comparison is corrupted, and
nothing in the output signals it.

> **The everyday analogy.** You are running a drug trial. Halfway through,
> someone quietly gives the placebo group the drug. Nobody logged it as an
> error, the data collection is flawless, and your trial is meaningless.

**What the gate does:** recompute the donor pool and **escalate** on the
affected units — never silently re-weight. A silent re-weight is the actual
danger, because the number keeps looking plausible. It escalates rather than
rejects, because the write is probably *correct*; the right response is a human
deciding how to recompute the pool, which is not a decision a gate should make.

**What it actually does in the shipped code:** takes the mutation's ZCTA, finds
every unit within a spillover radius (default **20 km**), intersects that with
the current donor pool, and escalates if the mutation's own ZCTA is a donor or
if any donor falls inside the radius.

> **Two honest footnotes, both worth volunteering.**
>
> **(a) The 20 km is assumed, not estimated.** The code comment says the default
> comes from "the estimated cannibalisation decay: material within ~8 km, fading
> to ~20". **That decay curve has never been estimated.** It is the plan from
> `HANDBOOK_03_CAUSAL.md` Sec. 3.7.3, and it is illustrative there too. The 20 km
> is a placeholder that deliberately matches the optimiser's
> `cannibalisation_radius_km`, so that the two components cannot disagree about
> what "nearby" means - which is a good reason for the number to be *consistent*
> and no reason at all for it to be *right*.
>
> **(b) There is no synthetic control for it to protect yet.** Gate 5 guards the
> donor-pool machinery ahead of a study that has not been built. It still earns
> its place, and here is the evidence: **running it against the real warehouse
> escalates often, because the donor pool genuinely is thin.** That is a finding
> about feasibility delivered by a safety control before the analysis it guards
> exists - which is, if anything, the right order to learn it in.

### Gate 6 — estimate stability

**The question:** how much does this mutation move the answer?

**The procedure:**
1. Estimate θ **without** the mutation.
2. Estimate θ **with** it.
3. If `|Δθ|` exceeds a **pre-registered** threshold → escalate to a human,
   regardless of automation settings, and surface the delta in the diff card.

> **Why "pre-registered" is doing work.** If you set the threshold after seeing
> results, you will set it wherever is convenient. Fixing it in advance is what
> makes the gate a control rather than a rationalisation.

The same discipline applies to *which* coefficient θ refers to. The shipped
estimator fixes it before the gate runs — by default the first covariate in the
hazard specification, which on the real panel is `households`. Which one it is
matters less than that it is chosen in advance: picking the coefficient after
seeing which one moved would turn Gate 6 into a search for a reason to approve.

### 6.7.0 What Gate 6 is actually re-running today, and why that is the defect

**Lead with the bad news.** Gate 6 runs, and it re-runs the wrong model.

Checked on 2026-09-14: `siting_atlas.agent.runner.build_estimator()` finds the
real panel usable, returns a `HazardThetaEstimator` with the audit basis string
`refit-on-real-panel`, and computes a baseline θ of **4.48e-05** on the term
`households`. So there is a delta, the gate produces a verdict, and the audit
record records a real check.

**The problem is what it is a check on.** That θ is a coefficient of the
**retired** discrete-time hazard model. The project's siting model is now the
conditional ZCTA choice model (`outputs/metrics/choice_report.json`). Gate 6 is
not wired to it. So the gate is, in its own terms, answering "how much does this
mutation move the answer?" about an answer nobody is using any more.

> **Why that is worse than it sounds, and it is the same mistake Sec. 6.7.1
> warns about in a different costume.** Sec. 6.7.1's point is that a control
> which degrades to "pass" manufactures false assurance. A control which
> silently keeps checking a **superseded** estimate does the same thing: the
> audit record says "estimate stability checked", and a reader has no way to
> tell from the record that the estimate checked is not the estimate published.
> The refusal path is honest about *absence*. Nothing in the current design is
> honest about *staleness*.

**What would be needed to point Gate 6 at the choice model.** This is a live
question and it has not been answered, so answer it as an open list rather than
as work done:

1. **A `ChoiceThetaEstimator`.** None exists; there is no reference to the
   choice model anywhere in `src/siting_atlas/agent/`.
2. **A different mutation-application step.** `apply_mutation` writes an
   *enablement state flag* onto a ZCTA-quarter panel. That is the retired
   model's input object. A choice model consumes decisions plus a choice set
   with CBP covariates, so a competitor facility would have to enter as a
   change to the *covariates* of an alternative — plausibly the warehousing
   establishment count — and that mapping is not written.
3. **A threshold on the right scale.** The shipped default is an absolute
   `theta_threshold = 0.02`. The choice model's betas are **ratios against a
   numeraire**, not absolute effects, so an absolute 0.02 has no meaning on
   them; the threshold would have to be stated on log beta or as a relative
   move, and pre-registered before anything is run.
4. **An answer to the hard one, which is not an engineering problem.** Two of
   the choice model's three parameters sit **at the boundary** at about 3e-16,
   so a delta on either is not a measurement of anything. The one interior
   parameter has a sandwich interval of [0.734, 2.835] around a point of
   1.4428. A 0.02-scale threshold sits far inside that noise, so a Gate 6 wired
   naively to this model would escalate on essentially every mutation — and a
   control that always escalates carries the same information as one that never
   does.

**So the honest status: Gate 6 runs, on a retired estimate; wiring it to the
current one is specified here and not built.** Point 4 is the reason nobody
should promise it as a week of work.

### 6.7.1 The best thing in this module: a gate that cannot run must not pass

Gate 6 needs to fit the estimate twice, with and without the mutation. Fitting
requires a usable model, and a usable model requires a populated target. For
much of the project's life there was no target variable at all, and on any
environment where the panel has not been built there still is not. So what
should Gate 6 do when it cannot compute a delta?

> **The tempting wrong answer.** Hand Gate 6 an estimator that returns a
> constant. Both fits agree, the delta is zero, the gate passes, and the audit
> record shows six green ticks. It takes about ten seconds to write.
>
> **And it is the single most damaging thing a safety control can do**, because
> it silently converts *"we did not check"* into *"we checked and it was fine"*.
> The second sentence is a lie, and it is a lie that leaves a clean paper trail.

The shipped code refuses. `UnavailableThetaEstimator` **raises** rather than
returning a number, and `AvailabilityAwareStabilityGate` turns that exception
into an **ESCALATE with the reason attached** - so the audit record says "gate 6
could not run, here is why", not "gate 6 passed".

> **Which path fires today.** `build_estimator()` checks whether the real panel
> is usable and picks accordingly. On this repository, with the panel built, it
> picks the *refit* path, not the refusal path (Sec. 6.7.0). The refusal path is
> live code on a live branch, exercised by the test suite and by any environment
> without a built panel — it is not a hypothetical — but do not claim in a viva
> that the gate is currently refusing. It is currently refitting the retired
> model.

```
   WHEN AN ESTIMATE IS AVAILABLE        WHEN IT IS NOT
   --------------------------------     --------------------------------
   fit without mutation                 estimator raises
   fit with mutation                        |
   delta = |theta_1 - theta_0|              v
       |                                ESCALATE
       v                                reason: no usable target
   delta > threshold ? ESCALATE         audit record says CANNOT RUN,
   else PASS                            never PASS
```

**This is the most defensible thing in the agent module**, and it generalises
well beyond this project: *a control that degrades to "pass" when its
precondition is missing is worse than no control, because it manufactures
false assurance.* Have that sentence ready.

> **A claim withdrawn.** This section used to end "**Cost: about two days**,
> once there is an estimate to re-run. There is not one today, which is exactly
> why the escalation path above had to be built first." The second sentence is
> now false — there is a fitted estimate, and the gate is in any case already
> refitting the retired one (Sec. 6.7.0). The cost figure went with it: two days
> was a guess at engineering time, and the blocking item is not engineering but
> point 4 of Sec. 6.7.0 — deciding what a meaningful threshold is on a
> parameter whose own interval spans [0.734, 2.835]. Withdrawn 2026-09-14; no
> replacement estimate of cost is offered, because there is not a defensible
> one.

**What does survive, and it survives unharmed:** the escalation path had to be
built first regardless, because "no usable target" is a state the system can
enter at any time — a fresh clone, a failed ingest, a contract that fires. The
design principle is independent of whether a target happens to exist today.

### The restated claim, narrow enough to survive

> *"Existing work on gated LLM writes protects data integrity. We identify a
> distinct failure class — inferential integrity — in which a write
> satisfying every data-integrity gate nonetheless invalidates a downstream
> causal identification assumption, and we propose two identification gates
> that detect it."*

Notice what it does **not** say: not "first," not "novel," not "no prior work."
It says *distinct failure class*, which remains true regardless of what anyone
else ships.

---

## 6.8 Human-in-the-loop

A configuration flag, **defaulting to ON** for any public demonstration.

When ON, every mutation clearing all six gates *still* surfaces a diff card
requiring explicit human approval before the write lands.

> **Why default it on.** A demo failure in front of a committee is unrecoverable,
> and the marginal cost of a click is zero. In production the six-gate argument
> may be sufficient; in a live demo, defaulting to caution is simply correct.

**An inconsistency to avoid:** an earlier draft measured its headline latency
benchmark with the flag OFF while shipping the demo with it ON — benchmarking
a mode it did not deploy. If you report latency, report it for the mode you
actually run.

---

## 6.9 Auditability — and why `dim_scenario` is not bookkeeping

A system whose parameters change in response to text is **not auditable by
default.** If someone asks "why did this ZIP rank third in October but eleventh
in November?", you need to be able to answer.

The scenario dimension records, for every result: **which version of W, which
mutation, which random seed.**

```
   dim_scenario
     scenario_id
     W_version          which weight matrix
     mutation_id        which agent write produced it
     seed               the random seed
     created_at
```

> **What this enables.** *"That change came from mutation #4471, a competitor
> facility in Plano parsed on 14 October, which moved θ from 0.31 to 0.38."*
>
> Without it, you have a model that changes its mind and cannot explain why
> — which for a tool aimed at regulators is disqualifying.

> **Status: the table exists, the history does not.** `dim_scenario` is one of
> the five tables in the DuckDB star schema and it is created on every build,
> but it currently holds a single default row (`w0`, mutation `none`). It cannot
> yet tell the October-versus-November story above, because no mutation has ever
> been applied to a published estimate.
>
> **Building the empty table anyway was the right call**, and it is worth being
> able to say why: provenance columns are almost impossible to retrofit. If the
> first thing you record is a result with no scenario key, every result before
> the retrofit is permanently unattributable. Reserving the key from day one
> costs nothing and cannot be recovered later.
>
> The audit trail that *does* carry real history is the gate log -
> `outputs/audit/mutations.jsonl`, append-only, one record per invocation
> including rejections. That is the file to show someone who asks whether the
> safety argument is falsifiable.

---

## 6.10 Evaluating the agent honestly

Covered in detail in Part 4 §4.10. The short version:

- Ground the target in the field: best public systems ≈ **80%** on BIRD, humans
  ≈ 93%. an earlier draft's 85% on 40 self-authored questions was an above-SOTA claim on an
  unfalsifiable test set.
- At n = 40, an observed 85% has a Wilson interval of roughly **[71%, 93%]**
  — pass and fail are indistinguishable. Use **n ≥ 100**.
- Primary metric = **execution accuracy** (does the SQL return the gold result
  set), not human judgement.
- **Stratify by difficulty** — spatial joins are where these systems break,
  and our warehouse is spatial.
- If using an LLM as judge: position bias, reliability-without-validity, and
  coin-flip behaviour on hard items are all documented. Randomise order, use two
  judges plus a human tiebreak, report Cohen's κ.

**And a gate-specific metric:** on a seeded adversarial set of 50 perturbations,
at least 90% of mutations that materially move θ must be caught by Gate 6.

> **Not measurable yet — and the reason has changed, so update your answer.**
> This used to say that you cannot score a detector of "mutations that
> materially move θ" when θ cannot be estimated. θ *can* be estimated: Gate 6
> refits the real panel and returns a number (Sec. 6.7.0). The adversarial set
> is still specified and unrun, but the blocker is now a different and more
> awkward one: the θ the gate can compute belongs to the **retired** hazard
> model, so a measured catch rate against it would be a catch rate for
> perturbations of a specification the project has withdrawn. Scoring that
> would be precision about the wrong thing.
>
> **What has been tested is the gate pipeline itself, exercised against the
> real warehouse.** That is the fact that matters here, and it does not depend
> on a suite-wide count. Do not blur testing and scoring together: "the gates
> are tested" is true, "the gates have a measured catch rate" is not.

> **A claim corrected.** This paragraph said "483 tests pass and 2 are
> xfailed". That count was stale, and it was also the wrong kind of evidence to
> put in this chapter. The suite moved through five different states on the
> morning of 2026-09-14 — including two red ones — before settling at 648
> passed, 2 xfailed at 08:13 UTC. See `HANDBOOK_07_ENGINEERING.md` Sec. 7.6 for
> the full account and the lesson. **Part 7 owns the number; this chapter
> should never have quoted one**, so the count has been removed rather than
> replaced.

---

## 6.11 Three claims we deliberately do not make

Being able to state these calmly is itself a defence — it demonstrates you
checked your own work.

| Tempting claim | Why it fails | What we say instead |
|---|---|---|
| "No prior work gates LLM writes" | Extensive prior art (§6.4) | The narrow inferential-integrity claim (§6.7) |
| "Spatial econometrics treats W as fixed" | Souza, Krisztin & Piribauer, *Political Analysis*, LeSage & Pace | W as event-driven state, plus the pre-registered RQ2 test |
| "We react faster than the operator" | Compares a compute step to a governance step; the figure is unsourceable; and it was benchmarked in a mode we don't ship | Deleted |

> **How to handle this if asked "why no speed claim against the operator?"**
>
> *"Because it compared our compute time to their review cycle. Their cycle is
> slow because a human is committing four million dollars, not because their
> software is slow. It was a category error, and I couldn't source the number."*

That answer is worth more than the claim ever was.

---

## 6.12 Part 6 self-check

1. Why should you *not* lead with the agent in an interview?
2. Explain ReAct as a loop and say why it beats one-shot answering.
3. What does MCP buy you, concretely?
4. Name the four standard gates and what each prevents.
5. What do *all* four have in common — and where does that stop?
6. Deliver the Plano example from memory, ending on the punchline.
7. What does Gate 5 protect, and what is the drug-trial analogy?
8. Why must Gate 6's threshold be pre-registered?
9. Why is `dim_scenario` necessary rather than nice-to-have — and what does it
   actually contain today?
10. State the inferential-integrity claim without using the word "first."
11. Which parts of this chapter are **built** and which are **specified**? Name
    the three things in the Sec. 6.0 box.
12. What does Gate 6 compute today, on which model, and why is that the defect
    rather than the achievement? Name the four things that would have to change
    to point it at the current choice model, and say which of the four is not
    an engineering problem.
13. When Gate 6 genuinely *cannot* run, what does it do, and why is returning a
    constant so much worse than escalating? Then state the generalisation about
    staleness that Sec. 6.7.0 adds to that lesson.
14. Where does Gate 5's 20 km radius come from, and why is "consistent with the
    optimiser" not the same as "correct"?

---

**Next:** `HANDBOOK_07_ENGINEERING.md` — pipeline architecture, reproducibility,
and how three people ship this on laptops.
