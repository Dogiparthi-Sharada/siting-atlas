# Architecture Decision Records — index

*Index last updated 2026-09-14.*

Four decisions were formal enough to be written down and dated. An ADR is a
decision that would be expensive to revisit and that somebody will later ask
"why?" about. Everything smaller lives in `../DECISION_LOG.md`.

---

## What is in this folder

Each `.md` has a generated `.txt` twin (see "The .txt twins" below). The twins
are not listed separately.

```
  0000-template.md            The blank form. Copy it to start a new ADR:
                              Context / Options / Decision / Consequences /
                              Residual risk. Not a decision itself.
                              TEMPLATE — nothing to read here but the shape.

  0001-observable-estimand.md Why the target variable is "did the operator
                              offer same-day service in this ZCTA, and in
                              which quarter", rather than order volume.
                              Order volume would have had to be constructed
                              from the same covariates used to predict it, so
                              a good score would have been evidence of a bug.
                              Carries two dated updates: 2026-09-13 on two
                              consequences that did not survive the data, and
                              2026-09-14 on three planned consequences that
                              were never executed at all (precision@k, PR-AUC
                              and the label-noise simulation).
                              ACCEPTED, STILL BINDING — but several passages
                              are out of date. See below.

  0002-routing-offline.md     Why no routing engine was to ship with the app.
                              The DESIGN was: run OSRM once per metro,
                              offline, extract the origin-destination matrix,
                              delete every intermediate artefact.
                              ACCEPTED AND NEVER IMPLEMENTED. No OSRM was ever
                              run, no OD matrix exists, and no disk figure in
                              the ADR was ever measured. The cost model uses
                              great-circle distance x a circuity factor of
                              1.30 — not the 1.35 "calibrated against routed
                              truth" the ADR describes, since no routed truth
                              exists. A dated update of 2026-09-14 in the body
                              records all of this. Do not quote "peak disk
                              ~60 GB to ~8 GB" as an achievement.

  0003-public-sources-only.md Why every source must be free, public and
                              re-downloadable by a stranger, and what that
                              costs. Concretely: Census County Business
                              Patterns replaced a rate-limited commercial
                              business directory.
                              ACCEPTED, AND ITS RESIDUAL RISK HAS BEEN
                              REALISED. The "public-data accuracy ceiling may
                              be below what the decision requires" is no
                              longer a risk: a single unfitted covariate
                              matches the fitted model (this said "beats"
                              until 2026-09-14; see below), satellite dating
                              produced 36% logically impossible estimates,
                              and SEC filings disclose no facility locations
                              or dates at all.
                              Two dated updates of 2026-09-14 record that, and
                              also qualify "a third party can reproduce every
                              number", which is overstated.

  0004-model-change-           Why the discrete-time cloglog hazard was
  conditional-choice.md        retired and replaced by a conditional
                               ZIP-choice model. The cause was the UNIT OF
                               ANALYSIS, not the sample size: one station
                               switches on a whole catchment of ZCTAs at once,
                               so 812 ZCTA-quarter "events" were 94 decisions
                               plus geometry. The assumption violated is
                               INDEPENDENCE ACROSS OBSERVATIONS — Train (2009)
                               3.7.1, printed p.61 — and the standard name for
                               the failure is clustering, or
                               pseudo-replication. Records the original spec
                               and why it was chosen, the measured failure,
                               and four rejected alternatives including the
                               Holmes/Houde moment-inequality route.
                               PROPOSED, NOT RATIFIED — but the successor it
                               proposes HAS NOW BEEN FITTED (2026-09-14). The
                               status is unchanged: STATUS.md 7's decision D1
                               is the owner's to take, and fitting a model does
                               not ratify the ADR that proposed it. See below
                               for what the fit showed.
```

---

## Start here

Read `0001-observable-estimand.md` and then `0004-model-change-conditional-
choice.md`, in that order. They are the two that touch the model and they are
a pair: `0001` settled *what* is observed — service enablement rather than
constructed order volume — and `0004` settles *whose decision* the observation
records. The observable estimand survives the change of model unchanged; the
unit it is measured on does not.

`0002` and `0003` are engineering and sourcing. Read them when somebody asks
"why is there no routing service?" or "why didn't you just buy the data?"

**Careful with the label D1.** `../ROADMAP.md`'s Phase-0 D1 is the estimand
question, settled by `0001`. `../STATUS.md` §7's D1 is the unit-of-analysis
question, addressed by `0004`. They are different decisions with the same
name.

---

## What is stale, and the gap

**The gap is closed, and the ADR that closes it is PROPOSED rather than
accepted.** This entry used to read: *"There is no ADR for the change of
model. This is the important thing to know about this folder."* That was true
until 2026-09-13. `0004-model-change-conditional-choice.md` now records the
original cloglog hazard spec and why it was chosen, the measured failure, the
unit-of-analysis diagnosis, the alternatives considered and the successor. It
is deliberately left at **proposed**: `../STATUS.md` §7 lists D1 as a decision
the *owner* owes in writing, and an assistant cannot sign that off. Until
someone does, the reframe is argued for but not ratified.

**The successor has now been FITTED — and it did not rescue the result.** This
happened on 2026-09-14, after `0004` was written, and it does not change
`0004`'s status: the ADR is still `proposed`, still not ratified, and fitting
a model is not the same as accepting the decision to change models.
`../../outputs/metrics/choice_report.json` records a conditional ZCTA choice on
the national frame: 94 decisions, 56 train and 38 held out, seed 20260914,
three free parameters, converged, McFadden rho-squared 0.19691 in sample.

The part that matters is the benchmark, not the fit:

```
  HELD OUT, 38 decisions        top-1   top-5   top-10    Brier
  ----------------------------  -----   -----   ------    --------
  fitted model                   7/38   16/38    19/38    0.008724
  warehousing count alone        8/38   16/38    20/38    0.008951
  households alone               1/38    5/38    10/38    0.009271
  uniform within metro           1/38    3/38     7/38    0.009316
```

**A single raw covariate matches the fitted model on ranking.** Do *not* say
"beats" — see the correction below. Two of the three free parameters — land
area and total establishments — sat at the boundary at around 3e-16 and
5e-16, so one parameter of three does any work. The estimation buys nothing
measurable over counting warehouses. Anyone quoting this model must quote
that alongside it.

> **Corrected 2026-09-14, and this index was one of the places giving the
> instruction.** The paragraph above used to read *"a single raw covariate
> **beats** the fitted model at top-1 and top-10 and ties it at top-5. Say
> 'beats'."* It now reads **matches**, and the standing instruction is
> inverted: say "matches", not "beats". The reason is not that the work moved
> on — it is that "beats" was **wrong**. It was read off the single seeded
> split tabulated above. Re-split the same 94 decisions fifty times and the
> raw count's margin is **+0.36 hits out of 38, paired sd 1.14**, with the
> raw count *losing* 11 of the 50 re-splits and tying 16
> (`../../outputs/metrics/gbm_benchmark.json`, `across_repeats`). A third of
> one decision is sampling noise, not a win, and an index that told every
> other document to say "beats" was propagating noise as a finding. The
> table's own numbers are correct for their seed. **The conclusion is
> unchanged and is still the uncomfortable one:** estimating three parameters
> buys no ranking improvement over counting warehouses. The model is not
> rescued by this; it is merely no longer being beaten by arithmetic.

**Uncertainty: read this as a snapshot, because it changed during the day.**
For the whole life of the project up to 2026-09-14 there were no standard
errors and no confidence intervals anywhere in it: `../MODEL_SPEC.md` §6.3
prescribed a sandwich covariance and a bootstrap over decisions, and neither
was computed. An `inference` block appeared in `choice_report.json` at 00:40 on
2026-09-14 carrying both, with the supporting modules still untracked by git
and the runner still being edited minutes afterwards. Treat it as landing, not
landed; confirm it is committed and tested before relying on it.

What it shows, if it holds, is a **fourth negative result** rather than a
rescue:

- The two boundary parameters get no sandwich standard error at all, correctly
  — at `beta = 0` the maximum is not interior, so the Hessian block is not the
  information matrix and any printed standard error would be uninterpretable.
  The artefact says so and prints the bootstrap instead.
- For `warehousing_establishments`, the only parameter doing work, the
  percentile bootstrap over decisions runs roughly **0.76 to 4.76** and so
  **includes 1.0**; the sandwich z against a ratio of one is about 1.06. The
  BCa interval, about 0.71 to 3.52, also includes 1.0.

So the one covariate that carries the model is not statistically
distinguishable from the numeraire, which is consistent with the held-out
finding that the raw count matches the fitted model on ranking (corrected
from "beats ... outright" on 2026-09-14 — see the block above).

**`0004` surfaces a disagreement between two other documents rather than
papering over it.** `../METHODS_RESEARCH.md` §8 and `../DECISION_LOG.md` §1.8
both say the choice of estimator is OPEN with **no winner declared**, while
`../ROADMAP.md`'s "Cut, with reasons" lists the Holmes/Houde moment-inequality
route as cut. `0004` resolves that in the roadmap's favour and states
the argument so it can be attacked; whoever accepts the ADR should also amend
§8 and §1.8 to point at it, or reject that paragraph.

**Two passages inside `0001` are superseded, though the decision itself
stands.**

```
  line 36-37  "Evaluation moves to AUC, PR-AUC, Brier, ECE, precision@k and
              conformal coverage."
              AUC is no longer the headline. METHODS_RESEARCH.md §14.3
              moves it to the
              Brier score plus calibration, precisely because AUC is
              monotone-invariant and therefore cannot see the calibration
              failure that sank the model. Report the raw Brier PAIR
              (0.019522 model, 0.019614 null, same 8,044 rows) and not a
              skill score: Gneiting & Raftery (2007) 2.3 p.362 finds skill
              scores generally improper even when the underlying rule is
              proper. Conformal coverage IS built; see the separate note on
              it below, which corrects an over-generous reading in an earlier
              version of this entry. PR-AUC and precision@k were NEVER
              COMPUTED, on either model -- 0001 carries a dated update of
              2026-09-14 saying so, along with the label-noise simulation its
              residual risk promised and which was never built.

  line 64-66  "...which strengthens the case for the observable estimand --
              a hazard model handles censoring natively."
              True of hazard models, but the hazard model is the thing that
              was abandoned. The observable estimand survives on its own
              merits; this particular supporting argument no longer applies.
              Interval censoring is in any case still not implemented
              (models/risk_set.py) — see STATUS.md §6.

  line 68-69  "The backtest this ADR made possible is real but thin: 2
              facilities fall in the 2024-25 prediction window."
              Accurate and worth quoting, but note the backtest has since
              been run and the temporal hold-out lost to a constant
              outright: Brier 0.020635 against 0.020213 over the same
              11,871 rows. Do NOT reach for the geographic hold-out as a
              second confirmation -- hazard_report.json:819 records that
              Phoenix and Boise hold two dated stations between them, so it
              is "a smoke test for gross failure and not a test of
              geographic transfer".
```

Nothing in `0001` was silently edited to hide this; the update section at the
bottom is the project's normal way of recording a decision that partly did
not survive contact with data. Keep that habit — append a dated update, do
not rewrite history.

**Conformal coverage: what is live, and do not report it as a success.** An
earlier version of this index described the project's conformal result as the
hazard model's 88.19% against a nominal 90%. That is still true *of the hazard
model*, but it omitted the 10.09% of prediction sets that came back **empty**,
and the hazard model has since been retired. The live conformal is the choice
model's, from `../../outputs/metrics/choice_report.json`:

```
  alpha   nominal   empirical   median set   median choice set   share named
  -----   -------   ---------   ----------   -----------------   -----------
   0.10     0.90      1.000         38.5            59.5             71%
   0.20     0.80      0.958         34.0            59.5             62%
```

Coverage of 1.000 is not an achievement here. It is bought by naming 71% of
the metro, which makes the set nearly vacuous as a decision aid. Report it
that way. Quoting "coverage 1.000" without the set size would be the worst
single misuse of a number in this repository.

**Also record, because neither is yet written down elsewhere in this index:**

- **`0002` was never implemented.** It is an accepted ADR for an OSRM
  precompute that nobody ran. See its 2026-09-14 update. Anywhere this folder
  or `../career/` quoted "peak disk ~60 GB to ~8 GB" as achieved engineering,
  that has been corrected.
- **`0004`'s successor has been fitted but `0004` is still `proposed`.** The
  fit is above. Fitting is not ratification, and the fit is negative anyway.
- **The power figure in this index was wrong.** It previously gave "7.6
  decisions per parameter, floor 10" as the *successor's* power problem. That
  is the retired hazard model's number, computed on its effective sample (97.4
  nominal, 5.6 effective, 7.6 optimistic per parameter, against a floor of
  10). The fitted successor has **94 decisions and 3 parameters**, so it does
  not have that particular problem. It has a different one: the estimation
  does not beat a raw covariate.

---

## The .txt twins

Every `.md` in this repo is rendered to a plain-ASCII `.txt` of the same name
by `scripts/build_docs.sh` (80 columns, pure ASCII). **The `.txt` files are
generated. Hand edits to them are lost on the next build.** Edit the `.md` and
re-run:

```
  bash scripts/build_docs.sh
```

---

## Writing a new one

Copy `0000-template.md` to `NNNN-short-slug.md`, take the next number, and
fill in all five sections — the "Residual risk" section in particular, since
it is the one that makes an ADR useful a year later. Add a row to the table
above. If an ADR replaces an older one, set the older one's status to
`superseded by ADR-NNNN` rather than deleting it.
