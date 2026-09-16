# Decision log

**What we decided, what we got wrong, and what has already been answered.**

This file exists because the same three things kept being re-derived: a
decision whose reasoning had been forgotten, an error that had already been
found once, and a question that had already been answered. Written down, none
of them costs a second day.

It is deliberately unflattering. Section 2 is longer than section 1.

| Document | Job |
|---|---|
| [`STATUS.md`](STATUS.md) | the measured state, with a `run_id` or a `file:line` behind every number |
| [`NUMBERS.md`](NUMBERS.md) | every headline figure re-derived from its artefact; the tie-breaker |
| [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) | what the **literature** says, with a section number behind every claim |
| **this file** | what **we** decided, what **we** got wrong, and what has already been asked |

---

## How to read the claims in this file

Every figure below was re-checked against the tree on 2026-09-13. Several did
not survive. Rather than quietly dropping them, each carries a tag.

```
  VERIFIED     Reproduced from an artefact on disk today. The command
               or the file+line is given.

  CORRECTED    The claim was made, the substance holds, but the NUMBER
               was wrong. Both numbers are shown, so nobody "fixes" it
               back.

  TESTIMONY    Stated from memory of work already done, and NOT
               checkable from the tree -- usually because the tree has
               since been repaired and this repository has no git
               history. Believe it or not on its own merits; do not
               cite it as measured.
```

**UPDATED 2026-09-14.** This section used to say, flatly, *"The repository is
not a git repo, so 'what it used to say' is only ever recoverable from what a
document now records about itself."* It is a git repo now — `208e124 Initial
commit: Siting Atlas as of 2026-09-13` is the root, and everything since is
in history. The TESTIMONY tag remains correct for claims about the tree
**before** that commit, which is most of section 2, and is no longer an
excuse for anything after it. Anything dated 2026-09-14 or later is checkable
with `git log -p` and should be tagged VERIFIED or not made.

---

## 1. Decisions taken

### 1.1 Pilot metros are identified by OMB CBSA **code**, never by title

**VERIFIED** — `src/siting_atlas/common/metros.py:101-115`.

**The question.** How do we name the ten pilot metros so that a join does not
break when someone re-downloads a reference file?

**The options.** Title strings (readable, what Zillow publishes) or five-digit
CBSA codes (opaque, stable).

**Chosen.** Codes. `PILOT` is a tuple of frozen `Metro(slug, label,
cbsa_codes, heldout)` records; every consumer (`models/panel_source.py:139`,
`cost/runner.py:39`, `report/scope.py:61`) filters on `cbsa_code`.

**Why.** Titles churn every delineation vintage. **Six of the ten pilot
metros** — six of eleven codes, since the Bay Area is composite — have a
different title in the 2023 OMB delineation than in the 2020 one:

```
  41860   SF-Oakland-BERKELEY, CA      ->  SF-Oakland-FREMONT, CA
  35620   New York-Newark-JC, NY-NJ-PA ->  ... NY-NJ        (PA dropped)
  16980   Chicago-Naperville, IL-IN-WI ->  ... IL-IN        (WI dropped)
  12420   Austin-RR-GEORGETOWN, TX     ->  Austin-RR-SAN MARCOS, TX
  19740   Denver-Aurora-LAKEWOOD, CO   ->  Denver-Aurora-CENTENNIAL, CO
  33100   Miami-FL-POMPANO BEACH, FL   ->  Miami-FL-WEST PALM BEACH, FL
```

A title join would have silently dropped six of ten metros on a routine
reference-file refresh, and the symptom would have been "fewer rows", not an
error.

**Caveat worth knowing.** The repo holds only the **2023** OMB delineation
(`data/raw/cbsa_county/`, pinned in `data/raw/manifest.jsonl` to
`list1_2023.xlsx`). The 2020 titles above come from Zillow's `Metro` column,
which is the vintage Zillow still publishes. So "six of ten" is verified
against Zillow's strings, not against an archived OMB file.

**What would reverse it.** Nothing. The cost of codes is readability, and
`MetroRegistry` already indexes by slug, label *and* code.

### 1.2 The Bay Area is CBSA 41860 + 41940 only

**VERIFIED** — `metros.py:102`; Santa Rosa (42220), Vallejo (46700) and Napa
(34900) are all present in `data/interim/cbsa_county.parquet` and absent from
`PILOT`.

**The question.** Where does "the Bay Area" stop?

**Why.** A same-day territory is a contiguous drive-time envelope, not a
regional identity. San Francisco and San Jose are one continuous urbanised
corridor; Santa Rosa is over an hour north of it, Napa and Vallejo are across
the strait. Including them would blend two density regimes, and in the Daganzo
cost model cost per drop goes as `1/sqrt(density)`, so blending regimes does
not average — it produces a number that describes nowhere.

**What would reverse it.** Evidence that Amazon runs a Santa Rosa or Vallejo
delivery station off Bay Area routing. The module docstring already flags this
as a judgement call rather than a derivation.

### 1.3 Panel membership comes from OMB, not from Zillow rent coverage

**VERIFIED** for the decision (`warehouse/panel.py:57-70`: the grid is
`dim_zcta CROSS JOIN dim_date LEFT JOIN cbsa_county`; Zillow enters only as a
LEFT-JOINed feature with an explicit `rent_observed` flag at L141).

**CORRECTED** for the measurement. It was recorded as *"the rent filter drops
35% of pilot ZCTAs, median population 4,731 dropped versus 30,589 kept."*
Recomputed today from `data/processed/panel.parquet` and
`data/interim/zillow_zori.parquet` over all 2,413 pilot ZCTAs:

| Figure | As recorded | Measured today |
|---|---|---|
| share dropped | 35% | **36.0%** (869 of 2,413) |
| median population, dropped | 4,731 | **4,450** |
| median population, kept | 30,589 | **30,625** |

The substance is untouched and is the whole point: the ZCTAs Zillow does not
cover are **seven times smaller** than the ones it does. Filtering on rent
coverage would therefore select on population density — which is a correlate
of the outcome we are trying to predict. That is not a missing-data
inconvenience; it is sample selection on the dependent variable's main driver.

**The example.** Suppose Amazon is less likely to serve small ZIPs. Drop every
ZIP without a rent series and you have dropped mostly small ZIPs, so the
remaining sample looks like Amazon serves nearly everywhere, and the model
learns that population does not matter — because you removed the variation.

**Also worth knowing, and it makes the case stronger.** The panel's own
`rent_observed` flag gives a much larger gap than 36%: only 48.7% of pilot
ZCTAs have rent observed *ever*, and 77.5% do not have it in every quarter,
because the panel runs 2018-2025 while ZORI coverage thins out going back. 36%
is the generous framing.

**Action outstanding.** The 35% / 4,731 / 30,589 figures are quoted in three
places — `common/metros.py` (docstring), `ingest/registry.py`, and
`docs/data/cbsa_county.md` plus its `.txt` twin — and should be updated to
36.0% / 4,450 / 30,625. Not done here; this file is docs-only and two of the
three are in `src/`.

### 1.4 Only DS and SDC set the `enabled` target

**VERIFIED** — `warehouse/facilities.py:55`, `LAST_MILE_TYPES = {"DS",
"SDC"}`, enforced at L139 where only those rows generate catchment pairs.

**Why.** A fulfilment centre is a regional node serving hundreds of miles; it
does not put a van on a residential street. Same-day service is a last-mile
property, so only last-mile buildings may switch a ZIP on. Fulfilment and
sortation centres are loaded and carried as covariates, never as the target.

**Moot in practice today.** All 43 rows of `facilities.csv` are `DS`, so the
filter currently removes nothing and the `SDC` branch is never exercised on
real data. It is a guard against a future panel, not a live transformation.

**What would reverse it.** Evidence that Amazon runs same-day out of a
sortation centre directly. That is not currently how the network is described.

### 1.5 Catchment radius: 15 miles for DS, 10 for SDC

**VERIFIED** — `facilities.py:60`, `CATCHMENT_MILES = {"DS": 15.0, "SDC":
10.0}`. Note the fallback at L148 is `.get(type, 15.0)`, i.e. an unlisted type
silently gets the DS radius rather than raising. Unreachable today because
L139 already restricts to DS/SDC.

**VERIFIED** — the sensitivity, recomputed today over 2,413 pilot ZCTAs, with
the 43 facilities geocoded by ZIP centroid from `data/interim/gazetteer.parquet`
(`facilities.csv` has **zero** populated lat/lon) and distance from the repo's
own `cost.daganzo.haversine_miles`:

```
   radius     ZCTAs reachable     share of pilot ZCTAs
   -----------------------------------------------------
   10 mi              874                 36.2%
   15 mi            1,231                 51.0%   <- production
   20 mi            1,530                 63.4%
```

**Why this matters more than it looks.** The radius is not a tuning knob; it
*is* the target variable. Moving it from 10 to 20 miles nearly doubles the
number of ZIPs the model is asked to explain. Any result must be quoted with
the radius attached, and the 15-mile choice (a 20-30 minute drive, which is
how a delivery-station service area is commonly described) is an assumption
carried into every downstream number.

**What would reverse it.** A real drive-time isochrone from an OD matrix.
That is `STATUS.md`'s "OD matrix from OSRM — NOT STARTED"; until then distance
is great-circle times 1.30.

### 1.6 The national panel stays in a separate file

**VERIFIED** — `grep -rn "national_facilities" src/` returns exactly one hit
and it is a **comment** (`ingest/external.py:59`). Both loaders hardcode
`facilities.csv` (`warehouse/facilities.py:69` and `:220-221`). The two files
share zero `facility_id` values. `facilities.csv` = 43 rows / 4,778 bytes;
`national_facilities.csv` = 104 rows / 17,497 bytes.

**Why.** They are different frames answering different questions. The 43-row
file is ten metros with full ACS, CBP, BLS and Zillow covariates. The 104-row
file is 62 CBSAs with none of that. Merging them would quietly change what the
model is estimating — you would gain events and lose the covariates that make
an event interpretable.

**What would reverse it.** Building national covariates at ZCTA grain for 62
metros. That is weeks, and it is `STATUS.md` defect D.

### 1.7 MWPVL will not be purchased

**Decision: do not buy.** The full reasoning, with the quotes from Houde et
al. that settle it, is in
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) Sec. 9. The compressed version:

- **For.** It would supply real opening dates and dissolve the worst problem
  in the project. Houde et al. Sec. 2.2 confirms MWPVL carries "location, size
  in square feet of floor space, employment, facility type, opening date, and
  closing date" — item for item, the panel we spent a day failing to build.
- **Against, and this is what settles it.** Houde et al. **already published
  the paid-data version**, in *Econometrica*. Buying MWPVL moves us from "the
  free-data version of a question nobody has asked about delivery stations" to
  "a smaller, later, worse-resourced version of an Econometrica paper". It
  would buy better data and destroy the contribution — and it would falsify
  the claim the project rests on: "Checkability is the product."

**The proposed alternative, not yet actioned.** Request a small academic slice
for **validation only** and publish a measured error rate for the free
pipeline. Today the entire calibration of the OSHA bound rests on **five**
addresses from MWPVL's 2012 public table, all fulfilment centres from
2008-2011, with lags of 4, 13, 57, 69 and 345 months. Five is not a
measurement.

**What would reverse it.** A supervisor ruling that a defensible estimate
matters more than a reproducible one. That is a legitimate position; it is
just not this project's.

### 1.8 UNRESOLVED — which estimator

**OPEN.** Two routes, no winner, and the decision has not been made. The
trade-off table is in [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) Sec. 8. In
one line each:

- **(A) Holmes / Houde moment inequalities.** Set identification, no
  distributional assumption on what the firm knew. But Holmes Sec. 7 assumes
  opening dates are measured *without* error, and Sec. 8.3 says error in `x`
  makes the estimator inconsistent — and dates are the one thing we measure
  worst.
- **(B) Train Sec. 7.7.3 closed-form dynamic logit.** Cheap, standard
  software, interpretable. But it assumes the firm's ex-ante unknowns are our
  unobservables, which Train himself calls doubtful.
- **(C), which neither of us proposed at the outset.** Molinari Sec. 2.3,
  interval-outcome partial identification. It is the closest match to the data
  we actually have. See `METHODS_RESEARCH.md` Sec. 11.

### 1.9 UNRESOLVED — the seven Phase-0 decisions

**VERIFIED** — `docs/ROADMAP.md:16-31`. All seven Phase-0 decisions are
**unticked**, under a header that reads *"Nothing in Phase 1 should start
until they are answered in writing."* Phases 1, 2 and 4 are largely built.

```
  [ ] D1  Estimand: adopt the observable outcome as primary target?
  [ ] D2  Routing: precompute the OD matrix, or circuity for v1?
  [ ] D3  Retail density: Census CBP as primary, Yelp optional?
  [ ] D4  Scope: cut the fine-tuned narrator, demote the LLM ablation?
  [ ] D5  Innovation set: adopt four claims, drop three?
  [ ] D6  Budget: resolve $35/$100 table vs $200/$300 prose
  [ ] D7  Name: confirm `siting-atlas`, no trademark anywhere
  ---------------------------------------------------------------
  Phase 1  11 done / 15    Phase 2  4/9    Phase 4  4/9
  Phase 3   0 done /  7    Phase 5  1/8    Phase 6  0/8
```

**This is bookkeeping, not paralysis — but read it carefully.** At least four
of the seven are demonstrably resolved elsewhere and were simply never
back-filled: D1 by `adr/0001-observable-estimand.md` (an accepted ADR adopting
exactly that estimand), D3 by `ROADMAP.md:77` (*"[x] Census CBP ... [D3
resolved in CBP's favour]"*), D7 by the repository being called `siting-atlas`
with a `TRADEMARKS.md` at the root. D2, D4, D5 and D6 have no such trace.

**The thing worth noticing is not the checkboxes.** It is that **Phase 3, the
causal layer, is at zero of seven** while Phases 1, 2 and 4 are the built
spine. The proposal's headline claims lean on Phase 3.

---

## 2. Errors made, and what caught them

Ordered by how much damage each would have done if it had shipped. The last
one is the largest and is not a coding error.

### 2.1 The unit of analysis was wrong — the biggest one

**TESTIMONY** for the provenance: this was introduced in the v4 proposal and
is not in the user's original v3. The repository's history begins after the
fact, so that cannot be confirmed from `git log`.

**CITATION CORRECTED 2026-09-14.** This entry twice cited **Train Sec. 2.2**,
mutual exclusivity of the choice set, as the rule the hazard model broke.
That is the wrong citation and it would not survive an examiner opening the
book: Sec. 2.2 governs a choice set facing a decision maker, a cloglog hazard
on ZCTA-quarters has no such decision maker, and Train calls the criterion
"not restrictive" on p. 12 while supplying a two-line repair recipe. The
assumption actually violated is **Sec. 3.7.1, printed p. 61** — independence
across observations, the assumption the likelihood itself is built on. It is
a smaller claim and a true one. `METHODS_RESEARCH.md` Sec. 14 and
`MODEL_SPEC.md` Sec. 3.5 carry the full argument; this entry is brought into
line with them.

**VERIFIED** for the substance and the numbers, and they are worse and better
than the shorthand suggests.

Amazon does not switch on ZIP codes. It signs a lease on a **building**, and
coverage follows mechanically from the van drive-time radius. Modelling
"the decision to add a ZCTA" therefore names the *outcome* correctly and the
*decision* incorrectly: one station switches on every ZCTA within 15 miles at
once.

Measured on the delivered panel: the median station covers **58** ZCTAs, the
mean **88**, the maximum **307**, the minimum 4. (The shorthand "~90 ZIPs at
once" is the mean; the distribution is what matters.)

The consequence is legible in the model's own diagnostics —
`experiments/hazard-model/artefacts/hazard_report.json` records it rather than hiding it:

```
   risk set                          1,756 units, 40,358 rows, 812 events
   events per parameter, NOMINAL                             97.4
   events per parameter, effective (metro-quarter episodes)   5.6
   events per parameter, optimistic (usable facilities)       7.6
   floor                                                     10.0
```

**812 ZCTA-level "events" are not 812 decisions.** They are, on the
report's own upper bound, **38 usable facility decisions** plus geometry. A
nominal 97.4 events per parameter looks like a well-powered study; the honest
figure is 7.6, which is below the floor. The report's `power.note` says so in
plain language: *"The nominal ratio counts ZCTAs and is not evidence of
power."*

**What caught it.** Reading Train (2009) on 2026-09-13. The sentence that
first drew attention was Sec. 2.2's *"the alternatives must be mutually
exclusive from the decision maker's perspective"*; the assumption the
likelihood actually rests on, and the one violated, is Sec. 3.7.1 p. 61,
*"assuming that each decision maker's choice is independent of that of other
decision makers"*. Nothing in the test suite could have caught either — every
ZCTA-quarter row is individually valid.

**Status, updated 2026-09-14: both the diagnostic AND the specification are
now fixed, and the model still does not predict.** The report publishes all
three power ratios instead of the flattering one. The reframe — *which ZIP,
conditional on a station opening in metro m* — was implemented in
`models/choice.py` and fitted on the national frame: 94 decisions, 56 train,
38 held out, converged, McFadden rho-squared 0.1969
(`outputs/metrics/choice_report.json`).

On the held-out decisions it takes 19 of 38 at top-10. **The warehousing
establishment count on its own, with nothing estimated, takes 20 of 38.** The
unit-of-analysis repair was necessary and it was not sufficient. That is the
uncomfortable half of this entry and it belongs in it: fixing the diagnosed
fault did not produce a working model, which means the diagnosis was
incomplete, not wrong.

### 2.2 The depot was a metro centroid, and the docstring said so harmlessly

**VERIFIED**, and this is the cleanest error in the project because the
assertion and the measurement are both on the record.

The first cost model put **one depot per metro at the population-weighted
centroid**. Its own docstring argued the choice barely mattered: line haul
enters divided by capacity `C`, so *"at C=120 a ten-mile error moves cost per
parcel by well under a cent"*. The wording survives as a quotation in
`docs/data/COST_MODEL.md:380-383` and
`tests/unit/test_cost_evaluate.py:146-151`.

It was then measured. Reproducing the old proxy today:

```
   implied line-haul distance      min 0.4 mi   max 145.7 mi   p90 60.2 mi
   cost of one extra mile                       $0.0192 per parcel
   worst-case artefact                          ~$2.79 per parcel
   median cost per parcel under the old proxy   $1.5094
```

So the "well under a cent" claim was wrong by roughly **twentyfold**, and in
the worst ZCTA the pure geometric artefact exceeded the entire median cost.

**CORRECTED — two numbers in the shorthand.**

| As recorded | Measured today |
|---|---|
| `$0.018` per parcel per mile | **$0.0192**. And the repo carries three different values for this one quantity: `$0.018` in `cost/depots.py:9-12` and `cost/daganzo.py:121`, `$0.019` in `docs/data/COST_MODEL.md:388` and `docs/engineering/PIPELINE.md:545`, and `$0.017` pinned in `tests/unit/test_cost_evaluate.py:157-159` from a synthetic fixture row |
| `$2.62` worst-case artefact | quoted consistently in four places, but it is `145.3 x $0.018`. At the measured rate it is **$2.76-$2.79** |

The `0.4` and `145.7` reproduce exactly. `$1.51` reproduces exactly ($1.5094).

**What caught it.** Someone measured the assertion instead of believing it.
That is the general lesson and it is worth more than the fix: *a docstring
that asserts an error is small is a hypothesis, and it costs ten minutes to
test.*

**Status. RESOLVED.** The fix is a solved depot network
(`src/siting_atlas/cost/depots.py`, 334 depots over the 10 pilot metros,
39,380 daily parcels each), and the median fell to **$1.0875**.

**Why the replacement is believable rather than merely different.** `K` is
fixed by `ceil(metro daily parcels / 40,000)`, a throughput figure, which
makes it an external check rather than a second free parameter. 334 depots
for 13,152,992 daily parcels is 39,380 each. (334 is the sum of the per-metro
`ceil` over the 10 pilot metros, which is what the solver opens; the single
national division 13,152,992 / 40,000 = 328.8 gives 329 and ignores per-metro
rounding. Both are derivable and they are not in conflict — but the figure to
quote is 334.) Amazon alone runs ~700–900 US
delivery stations; the pilot holds 17.6% of US population, so Amazon's share
here is ~125–160 and all operators together ~250–320. The implied network is
the right size, which it had no way of being if the throughput were badly
wrong.

**What moved.** Line-haul p90 60.2 → 10.05 miles. Median cost $1.51 → $1.09.
The `congested` scenario's spread fell from +14.5% to +4.4%, because the old
sensitivity table was partly measuring the proxy. And ZCTA 11222 (Greenpoint)
fell from 6th cheapest to 306th — it had been rewarded for sitting near an
imaginary point.

**The lesson to carry forward, and it names two live tickets.** Two other
assumptions in `cost/params.py` are currently asserted rather than measured,
in exactly the same voice: `income_elasticity = 0.35` ("set conservatively")
and `parcels_per_stop = 1.4`. Neither has been sensitivity-tested end to end.
**Treat a docstring that says an assumption does not matter as an open
ticket.**

**Still open, and it damages the story.** The three-way disagreement on
$0.018 / $0.019 / $0.017 is the one inconsistency that undercuts a narrative
whose whole point is "we asserted a number and then measured it". Two of the
three live in `src/` and `tests/` and are out of scope for this file.

### 2.3 Parcels and stops were conflated

**VERIFIED** for the substance. **CORRECTED** for one number.

Service time is paid once **per door**, not per parcel. Charging 2.4 minutes
to every parcel overstates labour cost precisely in the dense, high-volume
ZCTAs the ranking exists to identify as cheap — so the error pushed the answer
in the most misleading available direction.

The fix is `cost/params.py:69-76` (`parcels_per_stop: float = 1.4`) and
`cost/daganzo.py:197-202` (`cost_per_parcel = cost_per_stop /
parcels_per_stop`).

**CORRECTED.** It was recorded as moving the median from **$2.12** to $1.51.
The string `2.12` appears **nowhere** in the repository. Reconstructed: with
`parcels_per_stop = 1.0` under the old centroid depot the median is
**$2.1023**. So the figure is **$2.10 -> $1.51**.

Note also that the two fixes are **entangled**: $2.10 -> $1.51 is the
parcels/stops fix measured *under the old depot proxy*. Against today's solved
depot network the same fix is $1.5145 -> $1.0875.

**Status.** Fixed in code and tested (`tests/unit/test_cost_evaluate.py:55-90`),
but **carrying no status marker anywhere**. Unlike C1 and C2 there is no
RESOLVED ticket; `COST_MODEL.md:169` presents it as "where naive versions of
this model go wrong" — a design rationale, not a correction that was made. A
reader cannot tell this was ever a bug.

### 2.4 Cannibalisation summed additively over neighbours

**VERIFIED** for the mechanism and the framing. **NOT FOUND** for one number.

The first demand-cannibalisation rule was linear in neighbour exposure. With
all 2,333 pilot ZCTAs active, exposure reaches **99.2** for the most crowded
ZCTA, so a linear rule at 0.18 per unit claimed that nearby activations
destroy 90% of each other's demand. `optimize/params.py:37-51` records the
verdict: *"That is arithmetic, not economics."*

**CORRECTED / NOT FOUND.**

| As recorded | Measured today |
|---|---|
| "500 nearby ZCTAs" | 500 is the **budget capacity** (500 activations), not a neighbour count. The measured maximum number of ZCTAs within the 20 km radius is **230**; the mean is 55.8 |
| "90% of each other's demand" | **VERIFIED verbatim** in `optimize/params.py:37-51` and `tests/unit/test_optimize.py:52-56`. Max exposure 99.2 all-active, 53.7 against the real 317-row selection |
| "98% of rows hit the cap" | **NOT FOUND.** No such figure in source, docs or tests. Reconstructing the additive rule gives **78.9%** of rows at 0.9+ loss with everything active, and **18.6%** against the actual selection. Neither is 98% |

**The fix.** A saturating form, `peak * (1 - exp(-exposure))`, at
`optimize/objective.py:157` (`decay = -np.expm1(-exposure)`), guarded by
`tests/unit/test_optimize.py:51-70`.

**Status.** Fixed, but like 2.3 it carries **no status marker**. The open
open `ROADMAP.md` item "Cannibalisation decay radius" is about *estimating the
radius*, a different question.

### 2.5 The portfolio objective was degenerate

**VERIFIED, and RESOLVED.**

The objective was "minimise the marginal break-even margin". Measured:

```
   n =   1     marginal break-even  $1.1910   <- the minimum
   n =  10                          $1.4903
   n = 100                          $1.5278
   n = 317                          $1.5193
   n = 500                          $1.5516
```

Minimised at `n = 1`. **The objective said "build one facility"** — and it was
not wrong on its own terms; the terms were wrong. Break-even margin is a
*ratio*, and the best ratio is always the single best site.

**What caught it.** Plotting the objective against `n` instead of reading off
its optimum.

**The fix.** NPV maximisation at an assumed margin, `NPV(S) = m*A(S) - B(S) -
K(S)` at `optimize/objective.py:254-271`, with a real stopping rule at
`optimize/select.py:87-93`. The same degeneracy is re-flagged for the upper
bound at `select.py:173-177`, which is the right instinct — an error found
once tends to recur in the sibling code path.

**The consequence is the headline, and the old objective could not have
produced it.** At a $2bn budget the optimiser now funds only part of the 500
fundable activations and **leaves the rest of the budget unspent**, because
those activations lose money at the neutral margin. "Do not spend the whole
budget" is a finding; "minimise a ratio" could only ever return "build one".

**The margin is unobservable, so the deliverable is a frontier.** NPV is
linear in `m`, so choosing one value would choose the answer. `--margin`
defaults to the break-even of a full-budget portfolio, which is
self-referential rather than arbitrary; `--frontier` solves across six margins
so a reader can see where the answer turns.

**Two arithmetic bugs were fixed alongside, and both flattered the same
conclusion** — that clustering is valuable:

- annual flows used **365** days; the network delivers **312** (6 × 52).
  `delivery_days_per_year` is now derived from `cost/params.py`. Capital does
  not scale with the flow, so the error understated break-even by ~3.5%.
- the line-haul cost pool applied a *mileage* share to *total* cost. Door time
  and the van lease are paid whatever route the van drove, so the shareable
  pool was **2.9×** too large.

**The lesson, same as 2.2.** Three of these four errors were invisible in the
output — the portfolio still printed, the metros still looked plausible, the
gap still looked small. What caught them was someone asking "what does this
objective do at n = 1" and "what calendar is this annualised on". Neither
question needs the data to arrive first.

**Do not restore any typed count into this section.** `n = 317` above is a
probe of the *old* objective's shape, measured 2026-09-12; it is not a
selection size. The current counts are `detail.n`, `detail.capital` and
`optimality_gap` in `experiments/portfolio-optimiser/artefacts/portfolio_report.json`, run
`20260914-002431-7419`.

### 2.6 `vans_required` was rounded per ZCTA and then summed

**VERIFIED exactly**, computed today from
`outputs/tables/cost_to_serve_2023q4_baseline.parquet`:

```
   sum(vans_required)        79,484
   ceil(sum(van_days))       78,292
   difference                 1,192   <- pure rounding artefact
```

**The example.** Two ZCTAs each needing 0.6 of a van's day. Round each up and
you have 2 vans; a real depot sends one van to both and uses 1.2 van-days.
Multiply that across 2,333 ZCTAs and you have invented 1,192 vans.

**The fix.** `cost/daganzo.py:204-217` adds `van_days = stops /
stops_per_tour` and leaves `vans_required` in place with a "must NOT be
summed" warning; `cost/runner.py:102` reports
`ceil(result["van_days"].sum())`. Tested at `tests/unit/test_viz.py:226-237`.

**Still open, and live.** Three documents still publish the **buggy** figure:
`docs/data/COST_MODEL.md:535`, `docs/REPRODUCE.md:513` and
`docs/engineering/PIPELINE.md:537` all say "79,484 vans/day", while
`cost_report.json` now reports `78,292`. `COST_MODEL.md:495` also still makes
`vans_required` the headline column and omits `van_days` from its column
table. The exact 1,192 is recorded nowhere; the nearest is
`viz/data.py:41`, "about 1,200".

### 2.7 `facility_type` was read off the first letter of the building code

**VERIFIED** for the tautology and the DEN case. **CORRECTED** for the count.

The original rule was of the form *"code starts with D, therefore delivery
station"*. Applied to 202 OSM candidates it produced 76 `DS` and 126 `FC`.
`FACILITY_PANEL_PROVENANCE.md:669-675` puts it correctly: *"That rule is a
tautology, not a check. It reads the type off the name and then reports the
name as evidence for the type. It cannot fail, which is precisely why it tells
you nothing."*

The counter-example: **`DEN5` is a sortation centre.** `DEN` is Denver's
*airport* code, so the leading `D` is doing no work at all.

**CORRECTED.** It was recorded as "five sortation centres mislabelled". The
documented claim is *"at least five D-prefixed codes are mistyped this way"*,
and of those only **two are firmly established** — `DEN5` (a **sortation
centre**) and `DWA6` (a **fulfilment centre**). `DEN3`, `DWA9` and `DPX6` are
contradicted by OSHA records matched at **ZIP rather than address**, which
the provenance doc rightly calls "strong suspicion rather than proof". So:
five suspected, one confirmed sortation centre.

**The same trap, spatially.** `OAK3` and `OAK4` read as Oakland and are in
Patterson and Tracy, California — **60 to 70 miles inland**, in the Central
Valley, outside the Bay Area CBSA (see
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md)
"The airport-code trap"). (The ~70-mile
figure in `FACILITY_PANEL_PROVENANCE.md:655-658` is for OAK3 specifically.)
A third case, `SMF5` in Vacaville, sits in its own MSA. A building code is a
*label*, not a location and not a type.

**Status: acknowledged, not undone.** All 43 rows of `facilities.csv` are
still `DS`, and `FACILITY_PANEL_PROVENANCE.md:68` lists that as a known
weakness. Section 11.3 of that document proposes the replacement — classify
on the OSHA operating entity, "Amazon Logistics, Inc." for DS versus "Amazon
Fulfillment Services, Inc." for FC — and it has not been applied.

### 2.8 `open_quarter` was discarded and defaulted to Q1

**VERIFIED as historical and FIXED.** Several of the numbers in the shorthand
are **NOT FOUND**.

The defect was real: quarter information was dropped from most source dates
and an unknown quarter defaults to Q1 (`warehouse/facilities.py:87-91`, which
states the convention openly). A true Q4 opening dated to Q1 asserts the
building was operating **nine months** earlier than any evidence supports.

| Sub-claim | Verdict |
|---|---|
| "30 of 31 source dates discarded" | **NOT FOUND.** No such figure in the tree. The nearest real numbers: `DATES_FOUND.csv` has 35 rows, 20 with a year, **only 3 with a quarter** |
| "asserting nine months early" | **Sound arithmetic, but stated nowhere.** Q4 -> Q1 is nine months. Treat as inference |
| "100% of events in Q1" | **VERIFIED as historical.** The now-removed hardcoded string is quoted at `STATUS.md:222` |
| "77% of the risk set structurally eventless" | **NOT FOUND.** The metric exists (`diagnostics.event_timing`) and its current value is **0.0**. Under an all-Q1 regime the arithmetic gives 75%, not 77% |

**Current state**, from `experiments/hazard-model/artefacts/hazard_report.json`: 24 of 43 rows
carry a real quarter, there are **17 distinct event times**, events fall in all
four quarters (Q1 288, Q2 155, Q3 176, Q4 193), Q1 is 35.5% not 100%, and
`rows_structurally_eventless` is 0.0.

**What caught it.** A JSON file contradicting itself. `hazard_report.json` was
emitting the hardcoded string *"open_quarter is empty for all 49 facilities,
so every opening is dated to Q1"* while, a few keys away, reporting events in
all four quarters. Recorded at `STATUS.md:213-230`. The field is now derived
from the risk set instead of being a fixed string.

**The lesson, and it generalises.** A hand-written explanation sitting beside
a computed number will drift, and it will drift in the flattering direction,
because nobody re-reads prose that agrees with what they expect. Derive the
explanation or delete it.

**One stale artefact remains, and it is load-bearing.**
`src/siting_atlas/models/runner.py:64-66` still says the real panel has *"SIX
distinct event times, all of them Q1 because `open_quarter` was never
collected"* — against an artefact reporting 17 and 35%. That sentence is the
stated justification for `resolve_baseline()` returning `"linear"` rather than
`"spline"`. The choice may still be right at 39 events, but **the reason given
for it no longer describes the data**, so it needs re-deriving rather than
re-wording. In `src/`, out of scope for this file.

### 2.9 `--check` validated the largest CSV in the folder, not the right one

**VERIFIED and FIXED.**

`ingest/external.py:_find()` returns the **largest** file matching a pattern —
a deliberate rule, so that an interrupted download leaving a short file beside
a good one does not win. Under a bare `*.csv` glob, once
`national_facilities.csv` outgrew `facilities.csv`, the validator issued a
clean bill of health for **a file nothing in `src/` reads**, while the actual
model input went unvalidated.

**The fix** is an ordered pattern tuple, `("facilities.csv", "*.csv")` at
`external.py:57-67`; `_find` returns on the first pattern with any hits, so
the exact name now wins. Confirmed: `experiments/superseded-artefacts/external_check.json`
reports `"path": ".../facilities.csv"`, `"bytes": 4778`, `"rows": 43`.

**The size gap is now larger than the docs say.** `STATUS.md:218` and the
source comment both quote "10KB"; measured today the national file is
**17,497 bytes** against 4,778 — the provenance doc explains why
(*"It grew from 70 rows to 104 during the afternoon of 2026-09-13"*). The fix
is size-independent, so it holds regardless.

**Residual risk, named.** The `*.csv` fallback is still in the tuple. Rename
or delete `facilities.csv` and the bug returns silently.

### 2.10 A live EIA API key was written into three log files

**VERIFIED as historical; fully remediated.**

`requests` embeds the fully expanded URL, query string included, in its
exception messages. Logging an exception verbatim therefore wrote the live key
into **`console.log`, `events.jsonl` and `errors.log` at once**. The incident
is recorded in the docstring of the function written to stop it,
`src/siting_atlas/common/http.py:82-89`, which says plainly: *"That happened,
with a real EIA_API_KEY, before this function existed."*

A second, distinct vector is documented at `http.py:116-126`: the EIA v2 API
echoes `request.params.api_key` back in its **response body**, which was being
cached verbatim into `data/raw/`.

**Remediation, verified today.** `logs/` is in `.gitignore` (L29-32, with the
reasoning written out). `.env` and `*.key` are ignored. The scrubber is three
passes: known secret parameter names, a Bearer/Basic regex, and literal
replacement of the values of `CENSUS_API_KEY`, `EIA_API_KEY` and
`BLS_API_KEY`. Searching all 415 log run-directories and the whole tree for
the current key returns **zero** files outside `.env`.

**Residual risk, correctly flagged as WIP** in `ARCHITECTURE.md:608-610`:
a new keyed source added without redaction would leak. The
literal-value pass actually covers that for any variable added to
`_SECRET_ENV_VARS`, so the docs are more pessimistic than the code.

### 2.11 The proposal claimed ~5,200 ZCTAs; the measured figure is 2,413

**VERIFIED** for the numbers. **TESTIMONY** for "nine places".

The measured figure is **2,413**, in `outputs/metrics/scope.json` (`"zctas":
2413`, `"definition": "OMB 2023 CBSA delineation"`), produced by
`src/siting_atlas/report/scope.py`.

The "typed once, copied into nine places" claim is **not checkable from the
tree**: it is itself asserted at `report/scope.py:5-8` and `tools/scope.py:15`,
and the proposal artefacts have since been regenerated. Unzipping
`Siting_Atlas_Proposal_v4.docx` and both decks today gives **zero**
occurrences of 5,200 and **six** of 2,413. The nine originals no longer exist
to count.

**The structural fix is the point.** `scope.json` exists so that no headline
figure is ever typed. Eleven current mentions of "5,200" survive across ten
files and all are correctly *retrospective* — describing the defect, not
committing it.

**Except one, and it is the worst place for it.** See Sec. 4.1.

### 2.12 No status document stated the negative result

**TESTIMONY** — the tree has been repaired, so the historical silence ("not
one of seven status documents stated it; four implied it had never run on real
data") cannot be verified from the tree.

**Current state, measured today.** Thirteen documents stated the negative
result when this entry was written; the ones that still ship are
`README.md`, `STATUS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `REPRODUCE.md`,
`METHODS_RESEARCH.md`, `engineering/PIPELINE.md`,
`data/FACILITY_PANEL_PROVENANCE.md` and `data/ACQUISITION_GUIDE.md`. (The
`defense/` and `career/` documents named here have since been moved out of the
repository.) `STATUS.md` leads with it. **No** document
implies the model has not run on real data; every `SYNTHETIC` hit is a
negative assertion confirming the fixture branch is retired.

**One exception.** See Sec. 4.1.

**Why this error is worth keeping in the log even though it is fixed.** The
failure mode was not that anyone lied. It was that a negative result has no
natural home: it is nobody's deliverable, no test fails because of it, and
every document has a more encouraging thing to say. Silence is the default
outcome unless someone assigns it a page.

---

### 2.13 The batch generator sent 362 sites for labelling and 289 were already labelled

**VERIFIED 2026-09-14**, reproducible from the tree:

```
  labelled across six batches                     362 sites
  of which delivery stations                      135
  of which genuinely new to the panel              13
  worklist rows ALREADY in NATIONAL_CLASSIFIED.csv 289   =  79.8%
```

`scripts/make_unlabelled_batches.py` builds its worklist from
`data/interim/osha_amazon.csv`, taking every row where `facility_type` is
empty. That field is set by the **name-based regex** in `ingest/osha.py`,
which is silent whenever the inspector typed a generic establishment name.
The script never checks the resulting rows against
`data/collection/results/NATIONAL_CLASSIFIED.csv`, which already held 319
addresses classified by hand. Measured today, every one of the 135 delivery
stations in the six batches appears in the union of `NATIONAL_CLASSIFIED.csv`
and `OSHA_CLASSIFIED.csv`.

**The error, stated precisely.** "Unclassified by our regex" was treated as
"unknown to the project". Those are different sets, and nothing in the script
asserted that they were the same — the module docstring simply says *"for 362
of the 474 buildings it is silent"* and moves straight to generating prompts.
It is the same shape as Sec. 2.1: a definition assumed rather than checked,
with the check costing nothing.

**What it cost.** Six sittings of manual labelling, for 13 usable facilities.
Roughly 96% of the effort produced nothing new.

**What caught it.** Joining a batch back to the panel after batch 4 and
finding 76 of 85 delivery stations already there. The commit is
`d6a9e5e Batch 4 in; 76 of 85 DS were already in the panel -- my batch
generator was wrong`. It was caught three batches too late, and the reason
is that no batch before 4 was ever joined back — the programme measured its
output in *sites labelled* rather than in *facilities added*.

**One count in this entry has moved twice, is not reproducible, and that is
itself the finding.** "Genuinely new" was reported as ten after five batches
and thirteen after six, with an intermediate estimate computed against the
wrong reference file. It is emitted by no code into no artefact; it is counted
by hand into commit messages. Rebuilding it from the tree on 2026-09-14 by
address match gives 27 delivery stations absent from `NATIONAL_CLASSIFIED.csv`
and 37 absent from `national_facilities.csv` — neither is 13, so "the panel"
means something nobody has written down. **13 is the working figure and it
cannot currently be checked.** The comparison is small and fiddly, which is
exactly why it should be emitted by `scripts/ingest_batch.py` rather than
typed. It is not. Open.

**The salvage, and it should be called salvage.** The 122 already-known
delivery stations are a hand-labelled validation set for the classifier in
`ingest/osha.py`, whose agreement rate has never been measured. Half a day.
[`STATUS.md`](STATUS.md) §5 item 9.

---

### 2.14 Satellite dating: 107 estimates, and 36% of them are impossible

**VERIFIED as a negative result, 2026-09-14.** Not an error of execution — the
pipeline ran, cheaply, and did what it was asked. The error is that its output
was very nearly believed.

`data/collection/satellite/colab_date_from_satellite.py` was built to recover
true opening dates from Sentinel-2 imagery, because the CBP lag guard could
not be defended without them. It returned an estimate
for **107 of 107** sites, from a median of 106 cloud-free scenes each.

The validation looked survivable:

```
  sites with a known year                        83
  estimates within 1 year                       41%
  error standard deviation                  3.42 years
```

The logical test is what condemns it:

```
  estimates dating CONSTRUCTION AFTER the day an OSHA inspector
    recorded the building as already operating      39 of 107 = 36%
  median lateness of those                          33 months
  impossible rate at confidence > 2                 35%
  impossible rate at confidence 1-2                 30%
```

**An estimate that post-dates the proof of operation is not imprecise, it is
impossible.** A third of the output is in that class, and the confidence score
the pipeline emits does not separate the two populations, so there is no
threshold that rescues the rest. The cause is the changepoint detector, not
the imagery.

**The trap this nearly walked into.** 68 estimates survive the logical test,
and 68 dates is a tempting deliverable. They are not dates. They are the
subset of a method that fails a third of the time which happened not to fail
visibly, and selecting on a test the method fails at random is exactly how a
project ends up publishing noise. **Do not present them as dates.**

**What it means for the plan.** Opening dates are still unobtainable. The SEC
route was checked the same day and Amazon discloses no facility locations and
no facility dates at all — "delivery station" appears four times in all its
filings, Item 2 gives aggregate square footage only. The plan therefore
stopped waiting for dates. **What actually settled it was the MWPVL OCR
pass**, which supplied stated openings for a subset of the panel and made the
decisive leakage test runnable — it was run, and the result is in
[`STATUS.md`](STATUS.md) §2 and
[`research/NOTES_LEAKAGE_DECISIVE.md`](research/NOTES_LEAKAGE_DECISIVE.md).

---

## 3. Questions already answered

So that none of these is re-derived from scratch.

### 3.1 "Why a hazard model at all?"

Because the estimand is *whether and when* a ZIP was first switched on, and
that is a time-to-event question with right-censoring: most ZIPs have not been
enabled **yet**. A plain classifier would have to either discard the timing or
treat "not enabled by 2025" as "never enabled", and both throw away the thing
we are trying to measure. See `adr/0001-observable-estimand.md`.

The follow-on, which is now the largest open item: the data calls for
**interval** censoring, not just right-censoring, because the OSHA date is an
upper bound. `models/risk_set.py` handles right-censoring correctly and treats
`open_year` as an exact event time. `STATUS.md` defect A.

### 3.2 "Are we the first to do this?"

**No, and the honest answer is better than a yes.** Holmes (2011) did
Wal-Mart in *Econometrica*; Houde, Newberry and Seim (2023) did Amazon in
*Econometrica*. Both used the same estimator we would use.

What is different, verified against the papers themselves:

- **Facility type.** "delivery station" returns **zero** hits in Houde et al.
  They study fulfilment and sortation centres and explicitly drop specialised
  centres including 'PrimeNow Hubs'. Delivery stations are unstudied.
- **Data provenance.** Holmes bought store data from "Trade Dimensions, a unit
  of ACNielsen". Houde et al.: "We obtain information on Amazon's distribution
  network from the supply-chain consulting company MWPVL, International."
  Neither used a reproducible free-data pipeline.
- **The question.** Theirs is nexus tax policy and welfare. Ours is who gets
  served and whether a city can check it.

Full evidence in [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) Sec. 4.

**One correction that keeps resurfacing.** Houde et al. are repeatedly
described as working "at state grain". Their demand side is at **county**
grain and their supply side is a 20-mile cluster; state is the unit of the
*tax variation*, not of the analysis.

### 3.3 "Should we buy MWPVL?"

No. Sec. 1.7 above, and `METHODS_RESEARCH.md` Sec. 9.

### 3.4 "If we model WHERE a station goes, how does that answer ZIP coverage?"

This is the conceptual crux, and it was pushed back on, so here is the answer
as given.

Amazon does not switch on ZIP codes. It signs a lease on a building, and
coverage follows from the van drive-time radius. So "the decision to add a
ZCTA" names the **outcome** correctly and the **decision** incorrectly.

The ZIP-level answer is **recovered, not abandoned**:

```
  P(ZIP z served by period t)
        =  P(a station opens in metro m in period t)          <- timing
        x  P(the chosen site is within 15 miles of z)         <- siting
```

Two models, multiplied, giving back exactly the quantity a city wants — with
the difference that each factor is estimated from a decision that was actually
taken.

**The analogy.** You do not model 500 houses flooding as 500 independent
events. You model **where the river breaches**, and then compute which houses
are below the water line. Modelling the houses separately would give you 500
"events" from one breach, count them as 500 pieces of evidence, and report
spectacular confidence in a conclusion drawn from a single observation.

That is precisely the arithmetic in Sec. 2.1: 812 ZCTA-level events, 38
decisions, a nominal 97.4 events per parameter against an honest 7.6.

### 3.5 "Is 38 events enough?"

**No, and this is now measured rather than feared.** The fitted model is worse
calibrated than predicting one constant for every ZIP in every quarter — ECE
0.00863 against the null's 0.00005 — and its out-of-sample skill is
**negative** both out of time (-0.0209) and out of geography (-0.0618). One of
three covariates is distinguishable from zero. The full table is in
`STATUS.md`.

Two notes on the number itself. The count is **39** by the honest definition
and **38** as the diagnostic currently reports it, because
`diagnostics.usable_facilities()` filters on `open_year > first_year` and so
discards the whole of 2018 including Q2-Q4 (`STATUS.md` defect D2). It errs in
the safe direction. And per `METHODS_RESEARCH.md` Sec. 2.5, the effective
sample size for any standard error is the count of **buildings**, not of
ZCTA-quarters.

**This is a result, not a failure to produce one.** "43 buildings, dated this
way, cannot identify a siting policy" is a defensible finding with a
measurement behind it. "Our model achieves AUC 0.69" is not.

**Follow-up, 2026-09-14: 94 decisions is not enough either, and that is more
informative than 38 not being enough.** The national frame clears the
conventional power floor for the first time — 79 independent episodes,
15.8-16.0 events per parameter against a floor of 10
(`experiments/superseded-artefacts/national_panel.json`) — and the model fitted on it still
loses to a single raw covariate on top-1 and top-10
(`outputs/metrics/choice_report.json`). Two of its three free parameters run
to exp(-35), which is a flat likelihood rather than a small one. So the
binding constraint is no longer obviously sample size. It is either the
covariates or the dates, and this project cannot currently tell which.

**And "enough" has now been tested against an interval, which is the whole
point of asking.** The `inference` block added later on 2026-09-14 gives a
sandwich, a bootstrap over the 56 training decisions and a clustered
bootstrap over 38 metros. Households is the numeraire, so the null is a ratio
of one, and under the clustered bootstrap **no coefficient is distinguishable
from it in the direction that would matter**: `warehousing_establishments` is
[0.702, 10.013], `establishments` [0, 1.238], and only `land_area_sqmi`
excludes one, from below. The honest answer to "is 94 decisions enough" is
therefore: enough to clear a conventional power floor, and not enough to
separate any covariate from a household.

### 3.6 "Why did the numbers keep changing?"

Three distinct reasons, and it is worth separating them because only one is
alarming.

1. **Defects were found and fixed.** $2.10 -> $1.51 -> $1.0875 on cost per
   parcel is three corrections, each of which made the number *more* right.
   Sections 2.2, 2.3, 2.6.
2. **The panel itself was rebuilt.** 49 rows describing 44 buildings became 43
   rows describing 43 buildings on 2026-09-13, and every downstream artefact
   had to be regenerated. Anything quoting "49" or "44" is stale.
3. **The artefacts move under you while you read them.** This is the alarming
   one, and it happened during the writing of this file. See Sec. 4.2.

The structural answer to all three is `scope.json`: derive every headline
figure, never type one. Sec. 2.11.

---

## 4. Found while writing this log, and not yet fixed

Two things surfaced during verification that nobody asked about.

### 4.1 `helper.txt` is the one document nobody updated

*Historical. `helper.txt` lived in `academic/defense/`, which has since been moved
out of this repository. The entry is kept because the failure mode — a
hand-authored file with no generated twin, therefore missed by every
correction sweep — is general.*

**VERIFIED.** It has no `.md` twin, so `scripts/build_docs.sh` never
regenerates it and every correction sweep has missed it. It is the
**spoken-answer crib sheet** — the thing a candidate reads last and then says
out loud.

Its section "5. NUMBERS TO KNOW COLD" instructs the presenter to assert:

```
   helper.txt says          the tree says
   -----------------------------------------------------------------
   5,200 ZCTAs              2,413
   33,000 US ZCTAs          33,791
   $15.6-26B capital        $7.2B-$12.1B
   811,200 panel rows       1,081,312
   260 MB panel             14.6 MB
   52 billion MC draws      24.13 billion
   2^5,200 search space     2^2,413
   0.84 target AUC          0.6894 measured, and the result is NEGATIVE
```

Every other document in the repository was brought into line. This is the one
that would be read aloud, and the last line is not a stale figure but a
contradiction of the project's headline finding. **Highest-value single fix in
the tree.** Not done here: it is authored directly rather than generated, and
repairing it is a content decision rather than a rebuild.

### 4.2 The optimiser outputs changed mid-verification

**VERIFIED.** `experiments/portfolio-optimiser/artefacts/portfolio_report.json` and
`outputs/tables/portfolio_2023q4.parquet` were regenerated at 14:43 today by a
parallel process. They now report:

```
                     documented        outputs/ now
   ------------------------------------------------
   activations       317 of 500        330 of 500
   capital           $1.268bn          $1.320bn
   unspent           $732m             $680m
   naive break-even  $1.5516           $1.5567
```

`ARCHITECTURE.md:330-332` and `REPRODUCE.md:556-558` still cite the older set;
the status pages that did have since been rewritten. The baseline cost median
also moved, `1.08744349` -> `1.08749057`, which suggests an input changed
rather than a parameter.

**Why this is in the log rather than silently fixed.** "$732m unspent" is a
headline finding. Before any document is edited, somebody should establish
*why* it moved — an input drift that nobody intended is a bigger problem than
a stale number. Left as-is deliberately.

**SUPERSEDED AND ANSWERED, 2026-09-14.** Both figure sets above are now
historical. The current artefact is
`experiments/portfolio-optimiser/artefacts/portfolio_report.json`, run `20260914-002431-7419`:
**282 activations, $1.128bn capital, break-even 1.3431, optimality gap
10.73%.** The full sequence is 317 -> 330 -> 282 and $1.268bn -> $1.320bn ->
$1.128bn. The third move was caused by depot placement changing from k-means
to p-median, with nothing in `optimize/` touched.

The question this entry refused to edit around — *why did it move* — now has
an answer, and it is not the flattering one:

```
  1  A 500-draw Monte Carlo over every documented cost and portfolio
     parameter puts the activation count at p10 152, p50 264, p90 306
     (experiments/portfolio-optimiser/artefacts/montecarlo_report.json). The current 282 sits at
     the 67th percentile and the superseded 330 at the 97th, measured on
     outputs/tables/montecarlo_draws.parquet. So the drift is REAL --
     wider than parameter uncertainty -- and cannot be blamed on
     parameter choice.
  2  capital_usd is exactly $4m x n in all 500 draws. The three published
     capital figures were never independent evidence; they are the three
     activation counts restated. "$1.268bn -> $1.320bn -> $1.128bn"
     communicated three facts and contained one.
  3  Depot placement moves the answer more than any documented parameter
     and is not classified as a parameter at all. That is the defect.
```

**The standing rule this entry produced, and it is the durable fix.** Cite the
artefact by `run_id`; never retype a figure into prose. Every document that
hardcoded one of these numbers has had to be corrected at least twice.

### 4.3 Smaller, each a one-liner

| Where | What |
|---|---|
| `docs/data/COST_MODEL.md:535`, `REPRODUCE.md:513`, `engineering/PIPELINE.md:537` | publish **79,484** vans/day, the pre-fix summed-ceiling figure. The code emits **78,292** (Sec. 2.6) |
| `cost/depots.py:32`, `cost/params.py:100` | say "~329 depots"; the solved network has **334** |
| `ingest/external.py:59` | calls the national panel a "70-row panel"; it is **104** |
| `tests/unit/test_cost_evaluate.py:146` | says `linehaul_miles` "documents" the well-under-a-cent claim. It no longer does — `daganzo.py:120-131` says the opposite |
| `common/metros.py`, `ingest/registry.py`, `docs/data/cbsa_county.md` | quote 35% / 4,731 / 30,589 for the Zillow selection; measured today it is 36.0% / 4,450 / 30,625 (Sec. 1.3) |

---

## 4.4 The assistant answered the wrong question six times

**2026-09-13.** The user asked, on six separate occasions, whether the
project employs best-in-class **data cleaning and validation**, and asked for
proof. Phrasings included *"was data validation, cleaning done to best of
your knowledge"*, *"are you employing best in class data cleaning, data
validation, algorithms, prove it"*, and finally *"did you read any research
papers on data cleaning — this is 6th time i asked you, and you are ignoring
me"*.

Every one of those was answered with **econometrics** — discrete choice,
moment inequalities, hazard specification. One record-linkage paper
(Winkler `rr99-04.pdf`) was delegated and then treated as though it covered
the whole subject. It does not: record linkage decides whether two rows are
the same thing, and says nothing about missingness, outliers, range
validation, cross-field constraints or integration conflicts.

The material evidence that the complaint was correct: `../Research/` held
Train chapters 3–14 and four econometrics papers, and **zero** data-cleaning
papers.

**Why it happened.** The project's visible failure was a modelling failure,
so every "is this good enough" question was routed to the modelling
literature. Data quality was treated as something already handled because
individual defects had been fixed as they surfaced — the BPS single-year
ingest, the Zillow density selection, the parcels/stops conflation. Fixing
defects one at a time is not the same as auditing against a taxonomy, and the
difference is exactly what a taxonomy is for.

**What it cost.** At least one finding that changes a result went unseen
until the taxonomy was applied: rent is missing for 94.3% of ZCTAs, the ZCTAs
where it is observed are **64x denser** than the ones where it is not, and
`cost/runner.py:166` drops every incomplete row. That is listwise deletion
under non-random missingness, biased against precisely the sparse ZCTAs the
siting question is about. The same mechanism had already been caught once, in
the Zillow metro filter (Sec. 1.3) — and nobody thought to look for it
elsewhere, because there was no checklist to look against.

**Standing correction.** A question about data quality is not a question
about model choice. Treat them as different literatures, because they are.

New: [`data/CLEANING_LITERATURE.md`](data/CLEANING_LITERATURE.md) and
[`data/DATA_QUALITY.md`](data/DATA_QUALITY.md).

---

## 5. Where to go next

| Document | For |
|---|---|
| [`STATUS.md`](STATUS.md) | the measured state today: what works, what is fitted, what is blocked, what failed, what is pending |
| [`NUMBERS.md`](NUMBERS.md) | every headline figure re-derived from its artefact, with the stale variants named |
| [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) | the literature behind every method choice, with a corrections log of its own |
| [`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) | how the target was collected and every defect in it |
| [`ROADMAP.md`](ROADMAP.md) | the phase view, and the seven unticked Phase-0 decisions of Sec. 1.9 |
| [`adr/`](adr/) | the three decisions formal enough to have their own record |
| [`data/CLEANING_LITERATURE.md`](data/CLEANING_LITERATURE.md) | the data-cleaning reading list, why each paper matters here, and the missingness finding |
