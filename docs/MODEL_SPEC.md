# Model specification — the conditional ZIP-choice model

*Written 2026-09-13, after reading Train (2009) chapters 2, 3, 4, 8 and 13 in
full and §7.7.2-7.7.3 in part. Every Train citation below was opened. Page
numbers are printed pages; the PDF-to-printed offsets are recorded in the five
`docs/research/NOTES_train_ch*.md` files.*

This document says what we intend to estimate, on what, and under what
licence. It was deliberately written before any model code. The code came the
next day and does not match it in three places; §0.3 lists them.

---

## 0. Reader's summary

**The specification is written, and the model IS FITTED.** This section used
to say "it is not fitted, on purpose", and that sentence stood for about an
hour. The decision it recorded was correct on the evidence available at the
time; §0.2 keeps it, because the reasoning is good and an examiner is
entitled to see how it was overturned. §0.3 records what was actually fitted
and where the fit departs from the specification in §1-§9 below.

### 0.1 What this document specifies

```
  ESTIMAND     given one station opens in metro m in period tau, which ZCTA
  CHOICE SET   ZCTAs of metro m; mutually exclusive by tessellation (§3.3)
  UTILITY      V_nj = ln(beta' a_j),  a_j EXTENSIVE counts only  (§4)
  PARAMETERS   3  (households, land area, establishments)
  PERIODS      2  (2018-2020, 2021-2025), for POWER not for Train §7.7.3 (§5.2)
  SE           robust sandwich AND bootstrap over decisions, both shown (§6.3)
  SPLIT        60/40 over DECISIONS, seeded; ~15 decisions in test (§7)
  POWER        5.6 effective / 7.6 optimistic events per parameter at the
               retired model's 5 params; 9.3 / 12.7 at this model's 3.
               Floor is 10.  meets_floor: false.  (§8)
  HEADLINE     raw Brier PAIR + calibration.  Never Brier skill, never AUC (§9)
  BENCHMARK    gradient-boosted ranker, atheoretical, same rows (§9.4)
```

Three of those lines did not survive contact with the fit. See §0.3.

**Four things the literature said that we had wrong.** Each is written up where
it belongs, with the verbatim text.

> **The plan, and where it went.** The four claims below were inherited from
> the literature table in `docs/PLAN.md`, which was retired on 2026-09-15.
> That terse table did not survive the merge, so each claim it made is quoted
> verbatim at the section that checks it, and the argument it was standing in
> for now lives in
> [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §5 (Train) and §14 (the
> unit-of-analysis diagnosis). "The plan" below means that retired table.

```
  1  §3.4 Ex.2  The V = ln(beta'a) claim is RIGHT but the plan's phrasing
                licenses a model we must not fit.  "Additive" is not an
                instruction, it is a fact about EXTENSIVE variables, and it
                excludes median income, rent and every density or rate from
                the log.  Train also assumes utility depends on attraction
                variables ALONE, which the plan omits.              -> §1
  2  §2.2       Is NOT the rule the hazard model broke.  Train calls mutual
                exclusivity "not restrictive".  The assumption that was
                actually violated is independence ACROSS OBSERVATIONS, in
                §3.7.1 p.61.  Smaller claim, and it survives someone opening
                the book.                                        -> §3.5
  3  §7.7.3     Says "as few time periods as possible" for reasons of
                COMPUTATIONAL feasibility in a dynamic programme.  We are
                fitting a static logit, so the citation does not transfer.
                Our real reason is power.                         -> §5.2
  4  §8.6       The bootstrap the plan prescribes is justified by Train only
                "if this sample is large enough" -- the precondition our
                sample fails.                                     -> §6.3
```

**Two claims in the plan that checked out exactly as written**, and should not
be softened: BLP is unavailable because observed shares are zero for some
alternatives in some markets (§13.4 p.334, verbatim, §10.3), and Rust's
simplification gives a closed form resembling the upper level of a nested logit
(§7.7.3 pp.180-182, §5.3).

### 0.2 The Phase 3 decision: STOP. Do not fit. — TAKEN, THEN DISSOLVED

**Status: superseded 2026-09-14 by the national frame. Kept in full, because
the argument was right and the way it ended is the point.** Everything from
here to the end of §0.2 is the decision as it was written on 2026-09-13.

The brief's condition was explicit — *"Do not fit to a target that is still 44%
imputed"*. Measured on the tree today:

```
  facilities.csv        43 rows,  19 with no open_quarter  =  44.19%
  facility_load.py:79-81    open_quarter.fillna(1)  STILL PRESENT
```

The repair agent's work is real and worth having — `open_quarter_imputed` now
reaches the panel, ACS top *and* bottom codes are preserved end to end, and the
three contradicting national records raise instead of silently taking `min()`.
But none of that makes the 19 missing quarters known. It makes them *visible*.

And this specification is unusually exposed to that particular field: it uses
two structural periods split at 2020Q4/2021Q1 (§5.1), so 19 of 43 stations would
be assigned to a period on the strength of a quarter we invented. Fitting now
would produce a coefficient table whose period structure rests on a convention,
which is the same species of error the project has already documented twice.

**What would unblock it**, in the order of value per day:

```
  1  Resolve the 19 missing open_quarter values, or drop to ONE period so
     the quarter stops mattering and only open_year is used.  The one-period
     variant is cheap, loses the time dimension, and is honest.
  2  Three permit lookups on the contradicting pairs (Hawthorne, Tracy,
     Portland) unblock national_facilities.csv: 104 stations, 100%
     open_quarter, 62 CBSAs.  That roughly triples the independent episode
     count and is the single highest-leverage move available.
  3  Geocode the addresses.  Gates every distance covariate (§10.7).
  4  Put the repo under version control BEFORE any of the above (§10.8).
```

Note that item 1 has a variant that needs no new data. **A single-period
specification is fittable today**, because it uses only `open_year`, which is
100% observed on all 43 rows. It gives up the period contrast and is a weaker
model, but it is not built on an invented field. That is a real decision for the
inspirator and it is not the assistant's to take.

*(End of the 2026-09-13 decision.)*

### 0.3 What dissolved it, and what was actually fitted

**The blocker was not overridden. It dissolved, because it was a property of
the PILOT frame and the fit went national.**

```
                                 pilot frame        national frame
  file            facilities.csv (43 rows)   national_facilities.csv (104)
  open_year observed            43 of 43              104 of 104
  open_quarter observed         24 of 43              104 of 104
  imputed quarters                44.19%                   0%
```

Measured 2026-09-14 by reading both CSVs. §0.2's objection was that 19 of 43
stations would be assigned to a structural period on the strength of a quarter
we invented. On the national frame there are no invented quarters, so the
objection has nothing left to attach to. Item 2 of §0.2's own unblocking list
— *"104 stations, 100% open_quarter, 62 CBSAs ... the single highest-leverage
move available"* — is precisely what happened. The decision was not reversed
by argument; it was satisfied.

**Do not read that as a vindication of fitting.** Two of §0.2's four unblocking
items are still outstanding: the addresses are still not geocoded (§10.7), and
the national dates remain OSHA upper bounds, which is a different defect from
an imputed quarter and is not cured by going national. §10.1 below is rewritten
to say which part of the blocker survived. Item 4 (version control) is done.

**The fit, from `outputs/metrics/choice_report.json`** (`frame: national`,
`seed: 20260914`). Read the artefact, not this table, if the two disagree:

```
  decisions            94 total; 56 train, 38 held out
  free parameters       3, households fixed as the numeraire
  converged             true
  McFadden rho-sq       0.1969  against a uniform-within-choice-set null

                        top-1    top-5   top-10     Brier
  model, held out        7/38    16/38    19/38   0.008724
  uniform null           1/38     3/38     7/38   0.009316
  warehousing count      8/38    16/38    20/38   0.008951
    alone, nothing fitted
```

**Read the last row twice. A single raw covariate, with nothing estimated,
MATCHES the fitted model on ranking.** Whatever the estimation is buying, it
is not placement accuracy.

> **Corrected 2026-09-14.** This said **BEATS** on top-1 and top-10, on the
> strength of the single seeded split in the table above. Over fifty paired
> re-splits of the same 94 decisions the margin is **+0.36 hits of 38 (paired
> sd 1.14)** and the raw count loses 11 of the 50
> ([`research/NOTES_GBM_BENCHMARK.md`](research/NOTES_GBM_BENCHMARK.md)).
> One third of a decision is not a win. The table's own numbers are correct
> for their seed; the word "beats" read a difference into them that fifty
> splits do not support. The conclusion — that estimating three parameters
> buys no ranking improvement over counting warehouses — is unchanged.

Why that can happen is visible in the coefficients. `fit.theta` is log-beta,
and two of the three free parameters have run off to the boundary:

```
  beta_households                  1.0        numeraire, fixed
  beta_land_area_sqmi              3.04e-16   theta = -35.73
  beta_establishments              4.72e-16   theta = -35.29
  beta_warehousing_establishments  1.4428     theta =  +0.3666
```

`theta` is unconstrained in `choice.fit()`, so -35.7 is not a constrained
optimum: it is the optimiser walking towards minus infinity because the
likelihood is flat in that direction. Two of three parameters are effectively
unidentified, and what survives is a one-covariate model with extra steps.

**And the intervals, added later the same day, finish the argument.**
`choice_report.json` now carries an `inference` block from
`models/choice_inference.py` and `models/choice_sandwich.py`. Households is
the numeraire, so every interval is on a **ratio** and the null that matters
is **beta = 1**, not beta = 0. At alpha 0.05, clustered over metros:

```
  parameter                        point    95% interval     excludes 1?
  land_area_sqmi                 3.04e-16   [0, 0.228]       YES, from below
  establishments                 4.72e-16   [0, 1.238]       no
  warehousing_establishments       1.4428   [0.702, 10.013]  no
```

**Not one coefficient is distinguishable from the numeraire in the direction
that would matter.** The only thing established is that a square mile of land
is worth less than a household. Warehousing establishments — the covariate
that carries the model — spans 1 under every method: bootstrap over decisions
[0.760, 4.762], BCa [0.714, 3.522], sandwich [0.734, 2.835] with p = 0.287.
That is the finding to lead with, ahead of the top-k table above. See §6.3.

**Where the fit departs from this specification.** Each of these is a real
deviation, not a documentation lag:

```
  PARAMETERS  spec §0.1: households, land area, establishments.
              FITTED: households (numeraire), land area, establishments AND
              warehousing_establishments -- models/choice.py ATTRACTIONS
              plus CBP_ATTRACTIONS. Still 3 free parameters, not the same
              three. The added one is the only one that survives.
  PERIODS     spec §5.1: two structural periods split at 2020Q4/2021Q1.
              FITTED: ONE period. models/choice.py contains no period logic
              at all. The period contrast is unbuilt, not merely unreported.
  SE          spec §6.3: sandwich AND bootstrap, both shown.
              FITTED: BOTH, and better than specified. Added later on
              2026-09-14 as models/choice_inference.py and
              models/choice_sandwich.py, wired into choice_runner. All four
              of §6.3's steps are honoured, and two things §6.3 did not
              anticipate are handled: the sandwich REFUSES to report on the
              two boundary parameters and prints the reason, and those two
              get one-sided intervals because 79-81% of bootstrap
              replicates sit on the boundary. A clustered bootstrap over
              metros is added beside the one over decisions.
              STILL OPEN: the new inference modules and their test are untracked in git and one test
              fails on a renamed private helper, so the suite is red.
  SPLIT       spec §7: 60/40 over decisions, ~15 in test.
              FITTED: 56/38 over decisions, seeded 20260914. A larger test
              set than specified, because the frame is larger. No conflict.
  POWER       spec §8 counts the PILOT frame. The national frame reports 79
              independent episodes and 15.8-16.0 events per parameter
              against the floor of 10 -- met for the first time
              (experiments/superseded-artefacts/national_panel.json). §8 is not rewritten;
              read it as the pilot arithmetic it was.
```

**Now "three of those lines did not survive contact with the fit" is two:**
PARAMETERS and PERIODS. SE did not survive either, and then it did.

**What may be claimed from this fit.** That a conditional choice model on the
national frame converges, clears the power floor for the first time in the
project, does not beat a single raw covariate, and — once given intervals —
has no coefficient distinguishable from its own numeraire. That is a negative
result of the same family as the hazard model's, arrived at honestly and with
the uncertainty stated rather than omitted. Every prohibition in §9.3 still
binds.

---

## 1. The `V = ln(beta'a)` claim, checked against the text

*Checked by the parent on 2026-09-13 against `Ch03_p34-75.pdf`, §3.4
"Nonlinear Representative Utility", Example 2 "Geographic Aggregation",
printed page 54. It is the claim the whole reframe rests on, so it was
verified against the text rather than inherited.*

> **Page correction, 2026-09-13.** An earlier draft of this section cited
> printed page 53. It is **54**. §3.4 opens on p. 52, Example 1 (the
> goods-leisure tradeoff) runs on p. 53, and Example 2 begins at the top of
> p. 54 under the running head "54 Behavioral Models". In
> `Ch03_p34-75.pdf` that is PDF page 21 (PDF page = printed page - 33).
> Recorded rather than silently edited, because a wrong page in a citation
> this load-bearing is exactly the failure mode this project keeps having.

### What the plan asserted

Quoted here in full because the line itself is all that is left of it: this is
the retired `docs/PLAN.md` literature table, whose surviving argument is now
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §5.3.

> §3.4 Ex.2 — with zonal alternatives, utility must be `V = ln(beta'a)` with
> ADDITIVE attraction variables, or results are an artefact of how the Census
> drew ZCTA boundaries.

### What Train actually says

The set-up: destination-choice models partition a metropolitan area into
zones, and the zone boundaries are the researcher's arbitrary choice. Train
states the property we want:

> "It would be useful to have a model that is not sensitive to the level of
> aggregation in the zonal definitions. If two zones are combined, it would
> be useful for the model to give a probability of traveling to the combined
> zone that is the same as the sum of the probabilities of traveling to the
> two original zones."

Formally, for zones `j` and `k` merged into `c`, we need
`P_nj + P_nk = P_nc`, and for logit that reduces to a single condition:

> "This equality holds only when `exp(V_nj) + exp(V_nk) = exp(V_nc)`."

And the reason `ln(beta'a)` satisfies it is that attraction variables ADD:

> "The population and employment in the combined zone are necessarily the
> sums of those in the two original zones: `a_j + a_k = a_c`."

giving `exp(ln(b'a_j)) + exp(ln(b'a_k)) = b'a_j + b'a_k = b'a_c`. He closes:

> "Therefore, to specify a destination choice model that is not sensitive to
> the level of zonal aggregation, representative utility needs to be
> specified with parameters inside a log operation."

### Verdict: the claim stands, with two corrections and one addition

**Correction 1 — the requirement is weaker than "must be `ln(beta'a)`".**
The necessary condition is on `exp(V)`, which must be additive across a
merger. Train's own words are "parameters inside a log operation";
`ln(beta'a)` is the canonical instance he demonstrates, not a uniqueness
result. Our documents should say "inside a log operation" and cite
`ln(beta'a)` as the form we adopt.

**Correction 2 — the invariance is exact only when utility depends on
NOTHING ELSE.** Train opens the example by saying representative utility
depends on travel time and cost *as well as* the attraction variables, and
then writes: "assume for simplicity that representative utility depends only
on these variables." The derivation is carried out under that simplification.
Add a travel-cost term outside the log and the equality no longer holds
exactly. That caveat is not in the plan's line above and it constrains what
else we may put in `V`.

**The addition, and it is the sharp one: ADDITIVE means EXTENSIVE, and most
of our covariates are not.**

`a_j + a_k = a_c` holds for counts. It does not hold for rates, medians,
ratios or densities — the median income of a merged zone is not the sum of
the two medians. So our covariate list splits, and only the left column may
sit inside the log as an attraction variable:

```
  EXTENSIVE - may enter beta'a        INTENSIVE - may NOT
  ---------------------------        --------------------
  households                          median_household_income
  population                          rent_index
  land_area_sqmi                      wage_* (all of them)
  permit_units_total                  stop / household density
  employment counts                   permits_yoy_pct
                                      any share, rate or median
```

This rules out, by construction, several covariates the failed hazard model
used. It is a real restriction on the specification and nobody had stated it.

**On the consequence clause.** The plan says that otherwise the results are
"an artefact of how the Census drew ZCTA boundaries". Train's own phrasing is
"sensitive to the level of aggregation in the zonal definitions", which is
the same claim in weaker language. ZCTAs are arbitrary Census constructs
built from postal delivery routes, so the paraphrase is fair. Keep it, but
quote Train's wording in the proposal rather than ours.

### What this means for the specification

1. Attraction variables go inside the log and must be extensive counts.
2. Intensive variables cannot be attraction variables. If they are needed,
   they enter elsewhere in `V` and we lose exact aggregation invariance —
   which must then be stated as a limitation, not left implicit.
3. The property is worth having here for the same reason it is in Train's
   destination-choice setting: our alternatives are ZCTAs, and ZCTA
   boundaries are not a behavioural object.

---

## 2. The estimand

> **Conditional on Amazon opening one last-mile delivery station in metro `m`
> during structural period `tau`, the probability that the station is sited in
> ZCTA `j` rather than in any other ZCTA of metro `m`.**

Three things that sentence deliberately does *not* claim.

It is **not** "when does a ZIP get switched on". That was the retired hazard
specification, and the timing factor has been taken out of the estimand
entirely. It survives only as a *conditioning* variable — the factorisation in
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14.3,
`P(served) = P(a station opens in your metro) x P(the chosen site
is within 15 miles)`. This specification supplies the second factor and nothing
else. The first factor is a base-rate exercise on dates that are upper bounds,
and it is out of scope here.

It is **not causal.** Nothing below identifies what *would* happen to Amazon's
siting if a ZCTA's households changed. The coefficients describe the observed
association between ZCTA attributes and where stations landed, under a random
utility representation. Train is explicit that the representation does not
commit us to the behaviour: "models derived from utility maximization can also
be used to represent decision making that does not entail utility maximization.
The derivation assures that the model is consistent with utility maximization;
it does not preclude the model from being consistent with other forms of
behavior" (§2.3, p. 14). Section 10 lists the endogeneity we are not fixing.

It is **not a market-share model.** With one observed choice per decision and
thousands of alternatives, there is no share to match. This closes off BLP —
see §10.3.

---

## 3. The choice set, and the §2.2 demonstration

This is the check that was skipped last time, so it is written out in full
rather than asserted.

### 3.1 The definition being applied

> "To fit within a discrete choice framework, the set of alternatives, called
> the *choice set*, needs to exhibit three characteristics. First, the
> alternatives must be *mutually exclusive* from the decision maker's
> perspective. Choosing one alternative necessarily implies not choosing any of
> the other alternatives. The decision maker chooses only one alternative from
> the choice set. Second, the choice set must be *exhaustive*, in that all
> possible alternatives are included. The decision maker necessarily chooses one
> of the alternatives. Third, the number of alternatives must be finite. The
> researcher can count the alternatives and eventually be finished counting."
> — Train §2.2, p. 11

### 3.2 The choice set we adopt

```
  DECISION MAKER      Amazon, siting one last-mile delivery station.
  DECISION (obs. n)   one station opening, indexed by (metro m, period tau).
  ALTERNATIVES        every ZCTA in the pilot frame whose centroid lies in
                      metro m's CBSA.  J_m ranges roughly 50-600.
  CHOSEN ALTERNATIVE  the ZCTA containing the station's address.
```

### 3.3 The three checks, one at a time

**Mutually exclusive — SATISFIED, and by construction rather than by
assumption.** A delivery station is one building at one street address. The
address lies in exactly one ZCTA, because ZCTAs tessellate: the Census
constructs them to partition the land area without overlap. Siting the building
in ZCTA `j` therefore *necessarily* means not siting it in ZCTA `k` for every
`k != j`. This is Train's condition read literally — "Choosing one alternative
necessarily implies not choosing any of the other alternatives" — and it holds
as a fact about geometry, not as a modelling convenience.

Contrast with what the retired specification had. There, the "alternatives" were
ZCTA-quarters and the outcome was "this ZIP switched on". One station switches
on a median of 58 ZIPs at once by drawing a fifteen-mile catchment, so "ZIP A
switched on" and "ZIP B switched on" were *jointly* true, dozens at a time. Note
carefully what was actually wrong there, because our own documents have been
saying it slightly wrong — see §3.5.

**Exhaustive — SATISFIED CONDITIONALLY, which Train licenses explicitly.** The
station must be somewhere. Conditional on a station opening in metro `m`, the
set of ZCTAs in `m` is exhaustive. It is *not* exhaustive unconditionally: a
station could have opened in a different metro, or not at all. We are using the
second of the two repairs Train offers, and he states both the move and its
price (§2.2, p. 13):

> "In our case of heating-fuel choice, the researcher can either include 'no
> heating' as an alternative or can redefine the choice situation as being the
> choice of heating fuel conditional on having heating. ... Under the second
> approach, the researcher excludes from the analysis households without heating
> and, by doing so, is relieved of the need for data that relate to these
> households."

The price is that we cannot say anything about *whether* or *when* a station
opens. That is precisely the factorisation in
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14.3, and it is a
deliberate scope cut, not an oversight.

One boundary case to record honestly: a station sited just outside the CBSA
boundary but serving the metro would be outside the choice set. On the 43-station
pilot panel this does not arise — every dated station's ZCTA resolves inside its
metro. It would need re-checking if the national frame is ever promoted.

**Finite — SATISFIED.** 2,333 ZCTAs in the pilot cost frame; 33,791 nationally.
Countable, and counted. This is the criterion Train calls "actually restrictive"
(p. 13) and it is the one we meet most comfortably.

### 3.4 Estimation on a subset of alternatives, and why it is legitimate

With `J_m` in the hundreds and 38 decisions, most alternatives are never chosen
by anyone. Train §3.7.1, "Estimation on a Subset of Alternatives" (pp. 64-66),
licenses sampling the non-chosen alternatives. Under McFadden's (1978) **uniform
conditioning property** — the subset has equal probability of being selected
conditional on any of its members being the chosen one, which holds if we take
the chosen ZCTA plus a simple random sample of the rest —

> "`q(K | j)` cancels out of the preceding expression, and the probability
> becomes `P_n(i | K) = e^{V_ni} / sum_{j in K} e^{V_nj}`, which is simply the
> logit formula for a person who faces the alternatives in subset `K`."
> — Train §3.7.1, p. 65

and the resulting conditional log-likelihood "provides a consistent estimator of
`beta`", though "not efficient" because it discards information.

**Decision: we do NOT sample alternatives.** The full choice set is small enough
to enumerate (hundreds, not the hundred thousand that motivates the technique),
so we take the efficient estimator. The section is cited because it is the
fallback if the national frame is promoted and `J` grows, and because it
disposes in advance of the objection "you cannot estimate this with so many
alternatives".

### 3.5 The correction our own documents needed — MADE

The diagnosis of the retired hazard model was first filed against Train §2.2,
mutual exclusivity of the choice set. Having read §2.2 in full, that citation
is wrong in a way worth fixing, and the fix makes the argument *stronger*, not
weaker. The correction has since been carried into both places that carried
the wrong citation: [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14.2, which
is now the canonical statement of the diagnosis, and
[`STATUS.md`](STATUS.md) §8. What follows is the reasoning behind it.

**§2.2 governs a choice set facing a decision maker.** A discrete-time cloglog
hazard on ZCTA-quarters has no decision maker choosing among those rows, so
exclusivity is not a property those rows can have or lack. Worse for our
rhetoric, Train says the criterion is easy to satisfy: "The first and second
criteria are not restrictive. Appropriate definition of alternatives can nearly
always assure that the alternatives are mutually exclusive" (p. 12). Presenting
§2.2 as a fatal test the project failed misreads a design convention as a
prohibition.

**The assumption the hazard panel actually violated is in Chapter 3**, where
Train builds the likelihood (§3.7.1, p. 61):

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> `L(beta) = prod_n prod_i (P_ni)^{y_ni}`."

*Independence across observations.* That is what a 58-ZIP catchment destroys,
and the artefact measures the damage: `hazard_report.json` `power` reports
`n_events_zcta` 487 against `n_independent_episodes` 28 and
`n_usable_facilities` 38. The standard name is clustering, or pseudo-replication
— not non-exclusivity.

The diagnosis itself (unit of analysis; the model spent its capacity
learning to draw circles) is correct and stands. Only the citation and the
word needed replacing. Fuller treatment in
`docs/research/NOTES_train_ch02_properties.md` §6.1.

**A reported inconsistency that turned out NOT to be one. Resolved
2026-09-13 by the parent.** An earlier draft of this section said
`hazard_report.json` "disagrees with itself" because it reports
`risk_set.events = 812` and `power.n_events_zcta = 487`, and that "nothing in
the artefact explains the gap". Both halves are wrong. The artefact explains
it completely and is internally consistent:

```
  risk_set.events               812     every event in the risk set
    split.train.events          487
    split.calibration.events    164
    split.test.events           161
                                ---
                                812     exactly
```

`power.n_events_zcta` is the TRAIN split, which is the correct basis for a
power calculation — power is a property of the estimation sample, not of data
the model never saw. Every derived figure follows: 487/5 = 97.4 nominal,
28/5 = 5.6 effective, 38/5 = 7.6 optimistic.

What is real is a **naming** defect, not an arithmetic one. `n_events_zcta`
reads as "ZCTA events" (all of them) when it means "ZCTA-quarter events in the
training split". Checked across the repo, the consumers already say so
correctly — `models/console.py:30` prints "ZCTA-level training events" and
`academic/defense/HANDBOOK_04_MODELS.md:162` labels the row "ZCTA-quarter events
in train". So the claim that "both are quoted around the repo as the number of
events" did not survive checking either.

Left as a rename to do when `diagnostics.py:153` is next touched, since
changing the key requires regenerating the artefact and every document that
cites it by name. Not worth a rerun on its own.

---

## 4. The utility function

### 4.1 The form

For decision `n` (a station opening in metro `m`, period `tau`) and alternative
ZCTA `j`:

```
  V_nj  =  ln( beta' a_j(tau) )
```

with `a_j(tau)` the vector of **extensive** attraction variables for ZCTA `j`
measured in period `tau`, and `beta` a common (generic) coefficient vector. No
alternative-specific constants, no intercept outside the log.

Licensed by Train §3.4 Example 2, p. 54, quoted and dissected in §1 above:
"to specify a destination choice model that is not sensitive to the level of
zonal aggregation, representative utility needs to be specified with parameters
inside a log operation."

### 4.2 The attraction variables

Chosen on two criteria jointly: **extensive** (so §1's aggregation invariance
survives) and **observed at a usable rate** in `data/processed/panel.parquet`.
Null rates below were measured on the panel rebuilt 2026-09-13 09:30.

```
  VARIABLE              EXTENSIVE?   NULL RATE   IN?
  --------------------------------------------------------------------
  households            yes  count      0.06%    YES
  land_area_sqmi        yes  area       0.00%    YES
  establishments        yes  count      8.47%    YES
  population            yes  count      0.06%    no - collinear with
                                                 households, and one
                                                 size measure is enough
                                                 at n = 38
  --------------------------------------------------------------------
  median_household_income   NO  median  9.39%    EXCLUDED - intensive
  rent_index                NO  index  88.77%    EXCLUDED - intensive
                                                 AND 89% missing
  permits_yoy_pct           NO  rate   44.56%    EXCLUDED - intensive
  wage_*                    NO  rate   45.33%    EXCLUDED - intensive
  household density         NO  ratio    --      EXCLUDED - intensive,
                                                 and implied anyway (4.4)
```

**Three parameters, not five.** At 38 decisions this is not a stylistic
preference; see §8.

Note what this costs us relative to the retired model, which used
`("households", "median_household_income", "establishments")`
(`src/siting_atlas/models/panel_source.py:50-54`). Median household income was
the one covariate with any economic story attached and it is now excluded on
principle, because a median does not add when zones merge. That is the
specification paying for its own invariance, and it should be said out loud
rather than discovered by a reader.

### 4.3 The honest weak point: distance

Distance to the nearest existing station is the variable a siting model most
obviously wants, and it is **not extensive**. It cannot go inside
`ln(beta' a_j)` without breaking the §1 derivation, and Train's Example 2 never
addresses what happens when a non-additive term is added outside the log
(§1.2(c)).

Three options, and we take the third.

```
  (a) put it inside the log anyway     -> invariance lost, and we would have
                                          paid for a nonlinear likelihood and
                                          got nothing.  Rejected.
  (b) V = ln(beta'a) + gamma*dist      -> honest but no longer invariant.  The
                                          merged-zone identity fails unless
                                          dist happens to be constant across
                                          the merged pair.  Rejected for the
                                          main specification.
  (c) omit it from the main spec, and  -> what we do.
      fit (b) as a PRE-REGISTERED
      sensitivity, reported alongside
```

Option (c) keeps the headline model clean and turns the problem into a measured
quantity rather than a buried choice. If (b) moves the coefficients materially,
that is a finding about how much the invariance restriction costs, and it is
worth more than either model alone.

A separate limitation compounds this and is worth flagging here rather than in
§10: **every facility coordinate in the data is empty.** Both `facilities.csv`
and `national_facilities.csv` are 0.0% populated on latitude/longitude;
`facility_load.resolve_coordinates()` fills from the ZCTA centroid. So facility
location is known only to ZCTA-centroid precision, and any distance covariate
inherits that error. `STATUS.md` step 8 is geocoding, and it gates this.

### 4.4 Why no density variable is needed

A pleasant consequence of taking §1 seriously. Because both `households` and
`land_area_sqmi` are in `a_j`, a coefficient pattern that loads positively on
households and negatively on land area *is* a density preference, expressed
without any intensive variable entering the model. The restriction that looked
like a cost buys a cleaner way of saying the same thing.

Caveat: `beta' a_j` must be **positive** for the log to exist. A negative
coefficient on land area can drive the index negative for a large, empty ZCTA.
The estimator must either constrain the index positive or fail loudly; it must
not silently produce `nan`. This is a real implementation hazard and it is
recorded in §6.

### 4.5 No alternative-specific constants, and why that is forced

Train §2.5.1, p. 21: "With `J` alternatives, at most `J - 1` alternative-specific
constants can enter the model, with one of the constants normalized to zero."
With `J` in the hundreds per metro and one observation per decision, ASCs are
not identified — in the individual-level case Train notes they "would be
infinity (for the chosen alternative) and negative infinity (for the nonchosen
alternatives), perfectly predicting the choices and leaving no information for
estimation of parameters" (§13.4, p. 335). Every covariate must therefore be a
**generic** attribute of the ZCTA with a coefficient common to all alternatives.
This is also the reason BLP is unavailable (§10.3).

---

## 5. Structural time periods

### 5.1 Decision: TWO periods

```
  tau = 1   2018Q1 - 2020Q4    pre-pandemic build-out
  tau = 2   2021Q1 - 2025Q4    post-2020 acceleration
```

Attraction variables `a_j(tau)` are measured at the start of each period.
Coefficients are estimated **pooled** across periods, with period entering only
through the values of `a_j`. A second, pre-registered specification allows
`beta` to differ by period and is tested against the pooled model by likelihood
ratio (Train §3.8.2, p. 70).

**NOT BUILT, 2026-09-14.** The fitted model has one period. `models/choice.py`
contains no period logic, the attraction variables are not measured per period,
and no likelihood-ratio test was run. Every number in §0.3 is single-period.
The design above is unattempted, not rejected.

### 5.2 Verifying the §7.7.3 citation, which does not say what the plan implied

The plan cited "§7.7.3 define as few time periods as possible,
structurally" — the claim now written up at
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §5.6. I opened §7.7 (printed
pp. 175-182). **The words are there and
the reason is not the one we have been assuming.**

The sentence, verbatim, printed p. 180:

> "The first suggestion is for the researcher to consider ways to capture the
> nature of the choice situation with as few time periods as possible.
> Sometimes, in fact usually, time periods will need to be defined not by the
> standard markers, such as the year or month, but rather in a way that is more
> structural with respect to the decision process."

So "structurally" is Train's own word and the plan had it right. But two
things need correcting.

**(a) The section is titled "Uncertainty about Future Effects", not anything
about time periods,** and it begins on p. 178. The quoted passage is on p. 180.
Cite `§7.7.3, p. 180`, not `§7.7.3` bare.

**(b) The reason Train gives is computational, not statistical.** The passage
sits immediately after his discussion of the **curse of dimensionality** in
dynamic optimisation: "With `J` alternatives in `T` time periods, the recursion
requires calculation of `(J^T)T` utilities" (p. 178), which "is the main
stumbling block to application of the procedures with more than a few time
periods and/or alternatives". Few periods is advice about making a
*forward-looking dynamic programme* tractable.

**We are not estimating a dynamic programme.** We are estimating a static
conditional logit. Train's §7.7.3 justification therefore does not transfer, and
citing it as our reason would be citing the right words for the wrong reason —
the exact failure mode this document exists to stop.

**The honest reason we use two periods is power, not computation.** With 38
usable decisions (§8), every additional period is a further split of an already
inadequate sample. Two periods is the smallest number that lets covariates move
at all while keeping roughly 19 decisions per period. That argument stands on
its own and needs no citation from Train; what §7.7.3 legitimately supplies is
the *principle* that period boundaries should be structural rather than
calendar, which is why the boundary is 2020/2021 (a break in Amazon's build-out
regime) rather than an arbitrary midpoint.

### 5.3 The other §7.7.3 claim, which does check out

The plan also cited "§7.7.3 Rust's simplification: a forward-looking siting
model has a CLOSED FORM resembling the upper level of a nested logit" — now
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §5.7. Verified,
pp. 180-182. Rust (1987) noted that if the factors the decision maker does not
know beforehand are the same as those the researcher does not observe, and are
iid extreme value, the expected future utility collapses to a log-sum and
(p. 182):

> "The model takes the same form as the upper part of a nested logit model: the
> first-period choice probability is the logit formula with a log-sum term
> included as an extra explanatory variable. Multiple periods are handled the
> same way as multilevel nested logits."

Two caveats our documents omit. Train calls the enabling assumption "admittedly
restrictive" (p. 181), and closes the chapter with: "It is doubtful that the
researcher, in reality, observes everything that the decision maker knows
beforehand" (p. 182). **We do not use this result.** It is recorded because it
is the route to a forward-looking specification if the sample ever supports one,
and because the claim is accurate and should not be quietly
dropped.

---

## 6. Estimation and standard errors

### 6.1 The likelihood

Standard conditional logit log-likelihood, Train §3.7.1 eq. (3.11), p. 61:

```
  LL(beta) = sum_n sum_i  y_ni  ln P_ni      with  P_ni = e^{V_ni} / sum_j e^{V_nj}
```

with `V_nj = ln(beta' a_j)` substituted in.

**One warning that must not be skipped.** McFadden's global-concavity result
does *not* apply here. Train states the condition precisely: "McFadden (1974)
shows that `LL(beta)` is globally concave for **linear-in-parameters** utility"
(§3.7.1, p. 61, emphasis added). Ours is not linear in parameters — that is the
whole point of §3.4, whose opening paragraph (p. 52) warns:

> "Estimation is then more difficult, since the log-likelihood function may not
> be globally concave and computer routines are not as widely available as for
> logit models with linear-in-parameters representative utility. However, the
> aspects of behavior that the researcher is investigating may include
> parameters that are interpretable only when they enter utility nonlinearly. In
> these cases, the effort of writing one's own code can be warranted."

So we are in Train's "write your own code" case, and §8.5 applies.

### 6.2 Maximisation

BFGS, on Train's recommendation (§8.3.5, p. 198): "BFGS refines DFP, and my
experience indicates that it nearly always works better. BFGS is the default
algorithm in the optimization routines of many commercial software packages."
Implemented via `scipy.optimize.minimize(method="L-BFGS-B")` on the negative
log-likelihood.

**Multiple starting values are mandatory, not optional.** Train §8.5, p. 199:

> "All of the methods that we have discussed are susceptible to converging at a
> local maximum that is not the global maximum ... When the log-likelihood
> function is globally concave, as for logit with linear-in-parameters utility,
> then there is only one maximum and the issue doesn't arise. However, most
> discrete choice models are not globally concave. A way to investigate the
> issue is to use a variety of starting values and observe whether convergence
> occurs at the same parameter values."

Since we have just established we are *not* in the globally concave case, this
is binding. The implementation uses a fixed, seeded grid of starting values and
records in the metrics artefact how many converged to the same optimum. A run
where they do not agree must report that rather than silently take the best.

**Convergence** on Train's `m_t = g_t' (-H_t^{-1}) g_t < m_tilde` criterion
(§8.4, p. 198), with his suggested `m_tilde = 0.0001`. He also warns against the
lazy test: "Small changes in `beta_t` and `LL(beta_t)` accompanied by a gradient
vector that is not close to zero indicate that the numerical routine is not
effective at finding the maximum" (p. 199).

**Positivity of `beta' a_j`.** Required for `ln` to exist (§4.4). Enforced by
returning `+inf` for the negative log-likelihood whenever any
`beta' a_j <= 0`, which keeps the optimiser inside the feasible region without a
hard constraint. A run must report how often this fired.

### 6.3 Standard errors — and a caveat on the method the backlog prescribes

The backlog prescribes "bootstrapped standard errors (Train 8.6)" — the
prescription now sits at [`STATUS.md`](STATUS.md) §5 item 2, re-running
`choice_inference` and `choice_sandwich` on the expanded panel.
The section number is right — bootstrapping is described in §8.6,
"Variance of the Estimates", pp. 201-202, attributed to Efron (1979), with the
four-step procedure and `V = (1/R) sum_r (beta_r - beta_hat)(beta_r - beta_hat)'`.

**But Train's justification for the bootstrap has a precondition we cannot
meet, and it is stated in the same section** (p. 202):

> "The logic of the procedure is the following. The sampling covariance of an
> estimator is, by definition, a measure of the amount by which the estimates
> change when different samples are taken from the population. Our original
> sample is one sample from the population. **However, if this sample is large
> enough, then it is probably similar to the population, such that drawing from
> it is similar to drawing from the population itself.**"
> — emphasis added

"If this sample is large enough" is doing all the work, and with 38 decisions it
is exactly the condition in doubt. A bootstrap over 38 units resamples the same
38 buildings; it measures the sensitivity of the estimate to *which of our 38*
are included, which is a genuine and useful quantity, but it is not a licence to
treat the resulting interval as the sampling variability of a draw from the
population of Amazon siting decisions.

**What we do.**

```
  1  Report BOTH, side by side, and let the disagreement be visible:
       (a) the sandwich / robust covariance  H^-1 V H^-1 / N   (Train §8.6,
           p. 201: "valid whether or not the model is correctly specified")
       (b) the nonparametric bootstrap over DECISIONS, R = 2000, seeded
  2  Resample whole DECISIONS, never rows.  A decision is the unit of
     independence -- this is the same lesson the hazard model learned the
     expensive way.
  3  Report bootstrap PERCENTILE intervals, not bootstrap standard errors.
     At n = 38 the sampling distribution has no reason to be symmetric and a
     reported "standard error" invites a reader to form a normal interval.
  4  State the precondition in the results table caption, with the p.202
     quote, rather than in a footnote nobody reads.
```

If (a) and (b) disagree materially, that disagreement is itself a reportable
finding about how little the sample constrains the model.

**BUILT 2026-09-14, and it went further than this section asked.**
`models/choice_inference.py` and `models/choice_sandwich.py`, wired into
`choice_runner`, emit an `inference` block in `choice_report.json`. All four
numbered steps are honoured: both estimators side by side, resampling over
decisions and never over rows, percentile intervals rather than standard
errors, and the p.202 quote carried in the artefact's own
`train_precondition` field.

Three things it adds that this section did not anticipate, and each is the
right call:

```
  1  THE SANDWICH REFUSES TO REPORT on land_area_sqmi and establishments.
     beta = exp(theta), so beta = 0 is theta -> -inf and the optimum is not
     interior. The gradient does not vanish, the Hessian block is not the
     information matrix the asymptotics assume, and the number the formula
     returns would be arbitrary -- its size set by where the optimiser
     happened to stop. The module prints the reason instead of the number.
  2  ONE-SIDED intervals for those two, because the sampling distribution
     has an atom at zero: 80.7% and 79.0% of replicates sit on the
     boundary. A two-sided interval there would be a fiction.
  3  A CLUSTERED bootstrap over metros (1,500 replicates) beside the one
     over decisions (1,000). Six of the 94 decisions are in Los Angeles and
     share a choice set; the clustered interval is the one to quote when
     the two disagree. This is §7.1's lesson applied a second time.
  4  A convergence trace with a stated stopping rule, which declines to
     chase the far endpoint: "the right tail of a ratio at this sample size
     does not settle."
```

**The null is beta = 1, not beta = 0**, because households is the numeraire
and only ratios are identified. The artefact says so in `null_that_matters`
and refuses to print a zero test. Under the clustered bootstrap, only
`land_area_sqmi` excludes 1 — from below, upper endpoint 0.228 — and
`warehousing_establishments`, the covariate the model rests on, spans it
[0.702, 10.013]. See §0.3.

**Open.** Inference after a boundary selection: the interior sandwich block is
conditional on the other two parameters being exactly zero rather than
estimated at zero (Andrews 1999). `choice_sandwich.py` records the caveat and
does not resolve it. *(The second item recorded here — that the new inference
modules and their test were untracked in git and that
`tests/unit/test_choice_inference.py` failed on an `ImportError` for a renamed
private helper — is resolved as of 2026-09-15. `choice_inference.py`,
`choice_sandwich.py` and the test are all tracked, and the test passes in the
full suite: 660 collected, 658 passed, 2 xfail, 0 failures.)*

---

## 7. The train/test split

The user's instruction, from earlier in the project and quoted so it is not
lost: *"keep something aside for testing as well, don't train your models on
whole set of data."*

### 7.1 The unit of splitting is the DECISION

```
  train        ~60% of decisions
  test         ~40% of decisions
  seeded, deterministic, recorded in the metrics artefact
```

Three-way splits (train/calibration/test), as used by the hazard model via
`src/siting_atlas/models/splits.py`, are **not** used here. Conformal
calibration needs a third split and we are not doing conformal prediction on 38
units; spending a third of 38 decisions on calibration would leave roughly 12
per fold. Two-way, and say so.

**Splitting by decision, not by row, is the non-negotiable part.** The existing
`splits.split_by_unit` docstring (`splits.py:3-13`) already makes the argument
for the hazard model — random row splits leak, because two quarters of the same
ZCTA are near-identical, and held-out AUC comes back around 0.95 and means
nothing. The same trap exists here in a different costume: the rows of one
decision are the `J_m` alternatives of a single choice, and they must travel
together. Splitting alternatives across folds would put the chosen ZCTA in train
and its competitors in test, which is not a hold-out at all.

### 7.2 Which split, geographic or random

**Random over decisions, stratified by metro**, as the headline. A geographic
hold-out is more demanding and more interesting, and we cannot afford it: the
artefact already records that Phoenix and Boise "hold two dated delivery
stations between them, so this is a smoke test for gross failure and not a test
of geographic transfer" (`hazard_report.json:819`). Repeating that as though it
were a transfer test would repeat a mistake `STATUS.md` has already documented.

A temporal hold-out (`tau = 1` train, `tau = 2` test) is run as a **secondary,
pre-registered** check and reported with the same honesty: about 19 decisions
either side, which is a direction-of-travel indication and not a test.

### 7.3 What the split can and cannot settle

With roughly 15 decisions in the test fold, the test set can detect a model that
is grossly broken. It cannot distinguish a good model from a mediocre one. That
sentence belongs in the results table, not in a caveats appendix.

---

## 8. Power, stated plainly

### 8.1 The arithmetic, from the artefact

Read from `experiments/hazard-model/artefacts/hazard_report.json`, key `power`, on 2026-09-13:

```
  n_events_zcta                     487
  n_independent_episodes             28     lower bound on real decisions
  n_usable_facilities                38     upper bound on real decisions
  n_parameters                        5     (the RETIRED model's count)
  events_per_parameter_nominal     97.4     counts ZCTAs; not evidence
  events_per_parameter_effective    5.6     28 / 5
  events_per_parameter_optimistic   7.6     38 / 5
  floor                            10.0
  meets_floor                     false
```

The artefact's own note is worth quoting because it pre-empts the obvious
objection: "The nominal ratio counts ZCTAs and is not evidence of power.
Independent decisions lie between the metro-quarter episode count (lower bound,
merges same-year openings in one metro) and the usable-facility count (upper
bound). The verdict is taken on the upper bound."

**So: 5.6 effective, 7.6 optimistic, against a conventional floor of 10. The
model does not meet the floor on either bound.**

At this specification's **three** parameters (§4.2) the ratio improves to
`28/3 = 9.3` effective and `38/3 = 12.7` optimistic. That is why the parameter
count was cut to three, and it is the one lever this specification actually
pulls. It still does not clear the floor on the lower bound.

### 8.2 What the reframe buys, and what it does not

It buys **validity**, not power.

```
  FIXED by the reframe      the unit of analysis.  Alternatives are now
                            mutually exclusive (§3.3), observations are now
                            independent decisions rather than 58 correlated
                            ZCTA rows per building, and the likelihood's
                            independence assumption (§3.5) is satisfied.

  NOT FIXED                 there are still 28-38 real decisions.  A valid
                            specification fitted to 38 observations is still
                            fitted to 38 observations.
```

Honestly imprecise beats dishonestly confident. The retired model's nominal
`events_per_parameter` of 97.4 was the dishonest version: it counted 487 ZCTAs
as though they were 487 decisions. This specification will produce wide
intervals, and wide intervals that are *correct* are the improvement.

### 8.3 Does the literature say this sample cannot identify the model?

The brief asked for a straight answer. Here it is, in three parts.

**Train does not give a sample-size rule, and it would be wrong to invent one
and attribute it to him.** The floor of 10 events per parameter in the artefact
is the conventional epidemiological rule of thumb (Peduzzi et al.), not
something in Train. Nothing in chapters 2, 3, 4, 8 or 13 states a minimum `N`.
Do not cite Train for the floor.

**What Train does say bears on it twice, and both are unfavourable.** The
asymptotic distribution of the estimator is stated "as `N -> infinity`" (§8.6,
p. 200), and the bootstrap's justification is conditioned on the sample being
"large enough" (§8.6, p. 202, quoted in §6.3). Every inferential tool this
specification uses is an asymptotic one, and `N = 38` is not where those results
live.

**The verdict.** This panel can support a *descriptive* conditional-choice model
with three parameters and honest, wide intervals. It cannot support:

```
  - a claim that any individual coefficient is distinguishable from zero,
    unless the interval is extraordinarily clear
  - any of the parameter-hungry extensions: nested logit over metros
    (Train Ch. 4 -- one lambda per nest on top of beta), a control function
    (Ch. 13 -- adds lambda and a first stage), period-varying coefficients
    (doubles the count), or mixed logit
  - a policy recommendation of the form "Amazon should site where X"
```

**That is itself the finding, and it is the one to write up.** "This panel, at
this unit of analysis, cannot identify a siting policy, and here is the
arithmetic" is a defensible, measured result. It is worth more than a fitted
coefficient nobody believes, and it is the project's established currency.

---

## 9. What is reported, and what may not be claimed

### 9.1 The headline

**The raw Brier score PAIR — model and null, over the same rows — and
calibration alongside it.** Never the Brier skill score as a headline.

Grounds: Gneiting & Raftery (2007) §3.1 p.363 establishes the Brier score is
strictly proper; §2.3 p.362 states that skill scores "are generally improper,
even if the underlying scoring rule `S` is proper", names Murphy (1973) as
proving only *asymptotic* propriety and Mason (2004)'s propriety claim as
"generally incorrect". Full treatment in
`docs/research/NOTES_gneiting_raftery_2007.md` §6.3. A skill number may be
emitted as a readability normalisation, labelled as such, never as the estimand.

The null for a choice model is **uniform over the choice set**, `1/J_m`. That is
the analogue of the climatological reference, and it is the honest thing to lose
to. A second null — choose in proportion to households alone, no estimated
parameters — is also reported, because beating uniform is trivial and beating
"go where the people are" is the actual bar. The retired model's one
distinguishable covariate was `households` with a hazard ratio of 1.00005, which
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14.1 fairly translates as
*"Amazon builds where the people are. True,
and not worth a model."* The households-proportional null is what makes that
comparison explicit rather than rhetorical.

### 9.2 The reporting table

```
                              model    uniform null   households null
  Brier (same rows)              .           .              .
  log-likelihood                 .           .              .
  calibration (ECE, 10 bins)     .           .              .
  top-1 hit rate                 .           .              .        <- NOT a
                                                                        headline
  n decisions (test)            ~15
```

### 9.3 What may NOT be claimed

**AUC is not the headline.** [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §5.4
records that this was got wrong twice
already, and the corrected position is: Train §3.8.1 (p. 69) objects to "percent
correctly predicted" in terms that have two limbs — the procedure "misses the
point of probabilities, gives obviously inaccurate market shares, and seems to
imply that the researcher has perfect information" — and AUC inherits the second
limb, being invariant to every strictly increasing transform.

> **NEVER SAY:** that Gneiting & Raftery criticise, condemn or discuss AUC.
> They do not mention AUC, ROC or discrimination anywhere in twenty pages.
> `NOTES_gneiting_raftery_2007.md` §4 documents the zero-hit text search and
> supplies the correct, weaker, sufficient claim: AUC is not a per-case score,
> so propriety is *undefined* for it rather than violated by it. There is a
> standing guard in the defence pack against the fabricated version.

**"Percent correctly predicted" / top-1 hit rate may be shown but not
headlined.** Train §3.8.1, p. 69, verbatim: "Another goodness-of-fit statistic
that is sometimes used, but should actually be avoided, is the 'percent
correctly predicted.'" Gneiting & Raftery give the same object a name and a
theorem — it is their zero-one score, Example 4 p. 363, **proper but not
strictly proper**, with a Schervish mixing measure that is a point mass at one
cost-loss ratio. It is reported only because readers ask for it, and it is
labelled with Train's sentence.

**The likelihood ratio index is not an R-squared.** Train §3.8.1, p. 68: "It is
important to note that the likelihood ratio index is not at all similar in its
interpretation to the `R^2` used in regression, despite both statistics having
the same range." And p. 69: "Two models estimated on samples that are not
identical or with a different set of alternatives for any sampled decision maker
cannot be compared via their likelihood ratio index values." That forbids
comparing our rho to any published destination-choice rho.

### 9.4 The atheoretical benchmark

A **gradient-boosted ranker** is fitted on the same splits, scored on the same
rows, and reported in the same table. No causal claim attaches to it.

The reason is that a structural model with nothing to lose to has never been
tested. If the GBM out-predicts the structural model, that is a finding: it says
the `ln(beta' a)` restriction is costing predictive accuracy, and the size of
the gap measures what invariance is worth. If the structural model holds its
own, that is a finding too. Either way the project stops being a single number
with no reference point.

**BUILT 2026-09-14.** `src/siting_atlas/models/gbm_benchmark.py`, results in
`outputs/metrics/gbm_benchmark.json`, written up in
[`research/NOTES_GBM_BENCHMARK.md`](research/NOTES_GBM_BENCHMARK.md). A
LightGBM `lambdarank` over 50 paired re-splits, protocol imported from
`choice_runner` rather than re-declared so the comparison is exact — repeat 0
reproduces `choice_report.json` to six decimals.

```
  over 50 re-splits              top-10 of 38    sd      Brier
  conditional logit                  20.60      2.72   0.007550  <- best Brier
  warehousing count, unfitted        20.96      2.50   0.008951
  GBM, best of 4 shallow configs     22.30      2.4-2.8
  GBM, 2 deep configs                18.8       2.6-2.9  <- worse than either
```

**The answer is a data ceiling with a small model-ceiling term.** The flexible
learner does find something `ln(beta'a)` cannot express, and it is worth about
**one decision in 38** — while costing top-1 accuracy and the Brier score,
where the conditional logit is the best of all eight. The spread between all
methods (1.70) is smaller than any one method's spread across splits (2.4-2.9).

Two things that would have been missed by reporting a winner. The two
`deep/300` configs *lose* by 2.2 decisions, so a single unlucky configuration
choice would have produced the opposite headline. And the GBM puts 31.1% of
its split gain on `land_area_sqmi` and `establishments` — precisely the two
columns the logit drove to the boundary — which is what the model-ceiling term
is made of.

**A caveat in that report turned out to matter more than the report.** It
noted, without testing, that the warehousing covariate may contain its own
outcome. It was tested the same day and it probably does:
[`research/NOTES_COVARIATE_LEAKAGE.md`](research/NOTES_COVARIATE_LEAKAGE.md).

The GBM is scored on Brier and calibration exactly like the structural model,
not on AUC.

---

## 10. Known threats this specification does not fix

### 10.1 The PILOT target is 44% imputed; the NATIONAL one is not. NO LONGER THE BLOCKER.

**Retitled 2026-09-14.** This section was headed "THIS IS THE BLOCKER" and it
was, for the pilot frame, for one day. The fit went national and the national
frame reports 104 of 104 opening quarters, so the blocker does not apply to
what was actually fitted. Nothing below is withdrawn — every measurement in it
is still true of `facilities.csv` — but the conclusion at the end of it has
been superseded by §0.3, and the two must not be read independently.

Verified against the tree on 2026-09-13:

```
  data/external/facility_panel/facilities.csv   43 rows
    open_quarter real     24
    open_quarter missing  19        44.19%
  src/siting_atlas/warehouse/facility_load.py:79-81
    frame["open_q_index"] = frame["open_year"]*4 + frame["open_quarter"].fillna(1) - 1
```

The repair agent's work **landed and is good, but it is provenance, not
repair.** `flag_sentinels` now runs first, `open_quarter` keeps its NULL, and a
boolean `open_quarter_imputed` reaches the panel (True on 13,856 of 1,081,312
rows; 433 of the 1,257 ever-enabled ZCTAs were switched on by an imputed Q1).
The ACS top-code *and* bottom-code flags are now genuinely preserved end to end.
The three contradicting national records now raise a `ValueError` instead of
silently taking `min()`.

But `fillna(1)` is still there and 44.2% of the opening quarters are still a
convention rather than an observation. The brief for this work says: *"Do not
fit to a target that is still 44% imputed — if the fixes are not in, say so and
stop at Phase 2 rather than wasting the specification."*

**The fixes, in the sense that matters for fitting, are not in. We stop at the
specification and do not fit.** See §0.

Why this bites *this* specification specifically, and not just the retired one:
the structural period boundary (§5.1) is 2020Q4/2021Q1, and period assignment
depends on the quarter. Nineteen of 43 stations would be assigned to a period
using a quarter we invented. Two structural periods is a design that is
*maximally* sensitive to exactly the field that is 44% fabricated.

**SUPERSEDED 2026-09-14, and what survives of it.** The model was fitted on
`national_facilities.csv`, where 104 of 104 rows carry a real quarter, so the
"44% fabricated" objection never reaches the estimate. Two consequences follow
and neither is comfortable:

```
  1  The period design that made this section bite was never built. The
     fitted model has ONE period (§0.3). So the sensitivity described above
     is untested rather than avoided: if two periods are ever added, this
     section becomes live again for any frame that includes pilot rows.
  2  The pilot frame is still 44.19% imputed and fillna(1) is still at
     facility_load.py:79-81. The retired hazard model, every figure derived
     from the 1,081,312-row panel, and the `enabled` target all still run
     through it. This is not a historical note.
```

And the deeper defect is the one this section never named. An opening quarter
that is *observed* is still an OSHA inspection quarter, not an opening: on all
100 loaded national rows `open_year`/`open_quarter` equal the quarter of the
earliest OSHA inspection exactly (measured 2026-09-14). Going national replaced
a 44% imputation problem with a 100% upper-bound problem. The second is
smaller and better documented, and it is not nothing. See
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) §6,
the central caveat, and [`STATUS.md`](STATUS.md) §6 for the open-defect
register it feeds.

### 10.2 Endogeneity is present, named, and not addressed

Train §13.1, p. 316, case 3, "Interrelated choices of decision makers", is our
case with the labels changed: unobserved attributes of a ZCTA that make it
attractive to Amazon also plausibly drive the observed attributes we measure.
Rent is the textbook channel and ours is 89% missing.

The control function (§13.4, pp. 334-340) is the right tool and we cannot use
it. It is a two-step procedure — regress the endogenous variable on instruments,
put the residual into the utility — and it costs at minimum one extra parameter
`lambda` plus a first stage, on a sample that cannot afford three. It also
requires an instrument we do not have. Recorded in
[`ROADMAP.md`](ROADMAP.md) under "Identification" and left there.

### 10.3 BLP is unavailable, and the backlog's reason is correct

That same [`ROADMAP.md`](ROADMAP.md) entry says "**Not BLP** — Train notes BLP
cannot be implemented when
observed shares are zero for some alternatives in some markets, which is this
case". **Verified verbatim**, §13.4, p. 334:

> "The BLP approach is not always applicable. If observed shares for some
> products in some markets are zero, then the BLP approach cannot be
> implemented, since the constants for these product markets are not identified.
> (Any finite constant gives a strictly positive predicted share, which exceeds
> the actual share of zero.)"

Almost every ZCTA has an observed share of exactly zero. The claim stands as
written.

### 10.4 Choice-based sampling

Our 43 stations were found by searching OSHA enforcement records for buildings
that *exist*. We observe the chosen alternatives because they were chosen. Train
§3.7.2 (pp. 66-67) covers samples "drawn at least partially on the basis of the
decision maker's choice" and gives the Manski & Lerman (1977) result: with a
purely choice-based sample and alternative-specific constants, estimating as if
exogenous is consistent for everything *except* the constants.

We have no alternative-specific constants (§4.5), which is convenient but is not
the same as being safe: the result is stated for a *purely* choice-based sample
with a known population share, and ours is a convenience sample with an unknown
and non-random discovery process (OSHA inspects some buildings and not others).
Flagged as an unquantified threat. It is not addressed.

### 10.5 IIA

Conditional logit imposes independence from irrelevant alternatives (§3.3.2,
pp. 45-48) and hence proportional substitution. Adjacent ZCTAs are near-perfect
substitutes for a siting decision — a building two miles away serves almost the
same catchment — so IIA is implausible here in the red-bus/blue-bus way.

The natural repair is a nested logit with metros as nests (Train §4.2), which is
also structurally the right shape for the two-factor decomposition in
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14.3:
the upper model is "which metro", the lower model is "which ZCTA in it", linked
by the log-sum `I_nk = ln sum_{j in B_k} e^{Y_nj / lambda_k}` (§4.2.3, eq. 4.4-4.5,
p. 82). **We do not fit it.** Each nest adds a `lambda_k`, and §8.3 forbids the
extra parameters. Recorded as the first extension to attempt if the sample ever
grows. Train's own warning applies if anyone does: nested logit "is not globally
concave" (§4.2.4, p. 84).

### 10.6 Interval censoring, still not implemented

`STATUS.md` defect A. Most dates are OSHA "operating by" upper bounds, with
externally verified lags of 4, 13, 57, 69 and 345 months. This specification
*reduces* the exposure, because the date is now a conditioning variable that
assigns a decision to one of two periods rather than being the event time — but
it does not eliminate it, because a 345-month lag would put a decision in the
wrong period, or outside the frame entirely. Unaddressed.

### 10.7 Coordinates are ZCTA centroids

0.0% of facility coordinates are populated in either panel;
`facility_load.resolve_coordinates()` fills from the ZCTA centroid. Every
distance quantity in this project inherits that error. Gates §4.3.

### 10.8 The repository is not under version control — FIXED 2026-09-14

**Closed.** This section read: *"Not a modelling threat, but it is the
highest-risk finding of the day ... `git status` reports 'not a git
repository'; there is no `.git`, `.sl` or `.hg`. Multiple agents are editing
`src/` concurrently and none of that work is recoverable."*

The repository is now a git repository, with `208e124 Initial commit: Siting
Atlas as of 2026-09-13` at its root and history through the fit, the batches
and the Monte Carlo. Kept rather than deleted, because several documents still
excuse themselves on the grounds that there is no history to check — notably
`DECISION_LOG.md`'s TESTIMONY tag, which is correct only for claims about the
tree *before* that first commit.

### 10.9 A stale docstring that will mislead the next reader

`src/siting_atlas/models/runner.py:64-66` states the real panel has "SIX distinct
event times, all of them Q1 because `open_quarter` was never collected", and
forces `baseline="linear"` on that basis. The artefact says **17** distinct event
times spread across all four quarters (`share_in_q1` 0.3547). The prose is wrong
and it is load-bearing for `resolve_baseline()`. Flagged, **not fixed** —
`models/runner.py` serves the retired specification and is outside this work's
remit.
