# Lessons

*Everything this project learned the hard way, written for someone building
something else. Every entry names the file that establishes it.*

---

## Why this document exists, and how to read it

The central result of this project is a negative one. A pre-registered model
failed to predict where a large operator puts a delivery station, at both of
the geographic grains tested: at metro grain it lost to a zero-parameter "rank
metros by households" baseline in **0 of 7** held-out years, and at ZIP grain
a conditional choice model over 483 within-metro decisions turned out, on
measurement, to be a single covariate
([`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md) §7, verdict **H0**;
[`NUMBERS.md`](NUMBERS.md) §8).

A null is the easiest result in the world to produce by accident. You get one
from a NaN that never raised, from a covariate that leaked, from a baseline
nobody really tried, from a unit of analysis that was wrong from the first
line of code, or simply from stopping early. Every one of those happened here
at some point — which is exactly why the result is worth believing now. The
hypothesis was fixed and hashed before the model was fitted; the baselines
were chosen to be hard and declared trivial-or-not in advance; and the errors
were written down as they were found, including the ones that ran against the
project's interest.

So this is not a confession and it is not a victory lap. It is the audit trail
the result rests on, reorganised so that someone who will never read the rest
of this repository can use it.

**The test applied to every entry below:** would this save a stranger a day?
Several true and slightly embarrassing things are therefore absent, and
several unglamorous ones — how to check a `.gitignore` negation, why you must
not sum a per-row `ceil` — are in.

### How to read an entry

Each is a bolded rule, then **what happened** with the file or artefact that
proves it, **why it was easy to get wrong** (usually the most useful part —
a reader who understands the trap will recognise the next one; a reader with
only the rule will not), **what it cost**, and **whether it is fixed**.

Where a lesson is still open, or only half-closed, it says so. A lessons
document that reports only closed items is a marketing document, which is a
phrase this project borrowed from its own corrections log
([`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §10).

### Conventions and warnings

- **Figures come from [`NUMBERS.md`](NUMBERS.md) or from the artefact itself,
  never from prose.** This matters doubly here, because "corrections inherit
  errors" is one of the lessons (§4.1). Several numbers that circulate in this
  repository's own documents did not survive being re-derived for this file,
  and where that happened it is flagged inline.
- Paths are relative to the repository root. No absolute paths appear.
- Where a lesson points at work someone else could pick up, it links
  [`ROADMAP.md`](ROADMAP.md) § *Future scope*, which is written for exactly
  that reader and is grounded in what was measured rather than what would be
  nice.
- Line numbers were correct when this was written. Grep for the quoted text if
  they have moved.

### If you only read one section

[**The five that generalise**](#the-five-that-generalise), at the end. It is
the whole document compressed, with pointers back into the evidence. The rest
is a reference: 53 entries, grouped by the kind of mistake rather than by when
it happened.

---

## Contents

**[Part 1 — Design decisions, made before the data can argue back](#part-1--design-decisions-made-before-the-data-can-argue-back)**
| 1.1 A pre-registration is cheap, and it changes what you do
| 1.2 Seal the pre-registration with a hash — and know that the obvious repair defeats the seal
| 1.3 The unit of analysis is the first thing to get right, and checking it costs nothing
| 1.4 Count distinct values per unit before you freeze the covariate list
| 1.5 Stratify before you believe a pooled number
| 1.6 A percentile spread across re-splits is not a standard error
| 1.7 Resample the unit the decision was made at

**[Part 2 — Estimators that fail quietly](#part-2--estimators-that-fail-quietly)**
| 2.1 `r.fun < nan` is always False
| 2.2 An optimiser can report a better objective at an infeasible point
| 2.3 At a boundary the formula still returns a number, and it is arbitrary
| 2.4 A reparameterisation that buys positivity silently forbids repulsion
| 2.5 A ratio objective is degenerate by construction

**[Part 3 — Parameters, and the things that are not parameters](#part-3--parameters-and-the-things-that-are-not-parameters)**
| 3.1 A docstring that argues an error is small is an untested hypothesis
| 3.2 A radius is not a parameter; it is the definition of the dependent variable
| 3.3 Never sum a per-unit ceiling
| 3.4 Sampling a derived parameter independently draws impossible worlds
| 3.5 The biggest lever may not be classified as a parameter at all

**[Part 4 — Believe the artefact, not the document](#part-4--believe-the-artefact-not-the-document)**
| 4.1 Verify against the artefact, never against a corrected document
| 4.2 A stamp a payload can shadow is not an identity
| 4.3 Record whether a stage ran or was carried forward
| 4.4 Generated duplicates rot, and the generator is the thing to delete
| 4.5 Derive every headline figure — and know what that does not protect

**[Part 5 — Checks that do not check](#part-5--checks-that-do-not-check)**
| 5.1 A check that reads the answer off the name cannot fail
| 5.2 A check that shares an assumption with the thing it checks is not a check
| 5.3 A green test suite is not a covered one
| 5.4 Resolving ambiguity by size validates the wrong file
| 5.5 A guard whose threshold comes from an unreliable field has no margin
| 5.6 A guard can sit in its own blind spot

**[Part 6 — Methods and claims that always return an answer](#part-6--methods-and-claims-that-always-return-an-answer)**
| 6.1 A method that answers every question is not thereby a good method
| 6.2 Cite what you read — and grade every citation
| 6.3 A scoring rule can be proper while its skill score is improper
| 6.4 A figure must not contain a number that was never computed
| 6.5 A test can stop being identified because your model got better

**[Part 7 — Data that lies quietly](#part-7--data-that-lies-quietly)**
| 7.1 A geography can change underneath a join
| 7.2 County values wearing ZCTA column names
| 7.3 Filtering on availability can be selection on the outcome's main driver
| 7.4 When two sources contradict, the honest output is NaN
| 7.5 A naive outlier screen would delete Manhattan
| 7.6 Three extractor bugs, each plausible, none raising
| 7.7 A quality flag nothing reads is provenance, not repair

**[Part 8 — Near-misses, where the mechanism that caught it is the lesson](#part-8--near-misses-where-the-mechanism-that-caught-it-is-the-lesson)**
| 8.1 A licensed dataset one `git add` from public
| 8.2 Credentials: three layers, because each one alone leaks
| 8.3 The `.gitignore` negation trap, and the flag that lies about it
| 8.4 Environment-specific tooling does not belong in a public repository

**[Part 9 — The project around the project](#part-9--the-project-around-the-project)**
| 9.1 A negative result has no natural home
| 9.2 Five documents agreeing on a wrong cause reads as corroboration
| 9.3 An accepted ADR in the past tense becomes fabricated history
| 9.4 A fix with no correction marker is invisible
| 9.5 Measure the programme's output in the unit you actually want
| 9.6 Checkpoint after every stage
| 9.7 A question about data quality is not a question about model choice
| 9.8 A stale checklist trains you to ignore the checklist
| 9.9 The right answer to "should we buy better data" can be no
| 9.10 Read the survey with your data in hand

**[The five that generalise](#the-five-that-generalise)**

---

# Part 1 — Design decisions, made before the data can argue back

## 1.1 A pre-registration is cheap, and it changes what you do

**What happened.** [`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md) was written
on 2026-09-15 before the metro-level model was fitted. It fixed the question,
the hypothesis, the sample, the covariate list, two model forms, three
baselines, the evaluation protocol, five invalidating conditions, a numeric
success criterion, and — unusually — **both outcome paragraphs, verbatim**, so
that whichever way the result went the language was already written.

Two of those clauses did real work.

**§5 named the bar.** Three baselines were declared, with an explicit ranking
of which one counted:

```
  1  uniform across metros                 the no-information floor
  2  rank by households                    THE ONE THAT MATTERS
  3  rank by facilities already present    the densification null
```

and, in the same section: *"If the metro model cannot beat 'rank by
population', it has not worked, whatever its absolute accuracy."* Uniform was
declared trivial in advance, on the stated ground that beating it across 935
metros is worth nothing.

The result, `outputs/metrics/metro_entry.json`
(`run_id 20260916-070832-260d`, arm `prereg_strict`, form `logit`): the model
beat the uniform floor comfortably — pooled out-of-time AUC **0.7323** against
a year-base-rate null of **0.5367** — and lost to households, **0.7323 against
0.8949**, in every one of the seven held-out years, by between −0.112 and
−0.271. Had the bar not been fixed in advance, "substantially better than
chance across 935 metropolitan areas" was available, true, and publishable.

**§9 named a second criterion.** *"H1 is supported if, out of time, the metro
model beats the households baseline on AUC in a majority of held-out years
**AND** its calibration is at least as good as the constant null in a majority
of years."* The model ranks tolerably and calibrates badly: 3 of 7. That clause
exists because the hazard model had already died that way —
*"it lost 17 of 17 calibration comparisons while scoring AUC 0.689. **Ranking
without calibration is not prediction** — it tells a county it is more likely
than its neighbour and cannot tell it whether that means 5% or 40%."*

**Why it was easy to get wrong without one.** Both clauses point at the same
trap, and it is not dishonesty. After a result arrives, every framing looks
like a modelling judgement rather than a choice: *of course* the uniform
baseline is the right comparison at 935 metros; *of course* AUC is the metric
for a ranking problem. Each of those is defensible in isolation, which is
precisely why the defence is worthless after the fact. The pre-registration's
own preamble names the mechanism: the project had already measured that
choosing covariates after seeing the answer cost something, and *"choosing a
FRAMING after seeing a result is the same error one level up."*

**What it cost.** Less than the first model run. There is no record of exactly
how long it took to write and this document will not invent one.

**A third thing it bought, which was not the plan.** The pre-registration
produced criticisms of itself. [`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md)
§12, *"Where I think the prereg is wrong"*, was written after the result and
against the project's interest, and its sharpest finding is §1.4 below. A
document that fixes a claim in advance gives you something specific to be
wrong about later, which a vaguer plan does not.

**Rule.** Before you fit, write down the baseline you would be embarrassed to
lose to, the second criterion your favourite metric does not capture, and the
sentence you will publish under each outcome. The last of those is the cheapest
and the one most often skipped.

## 1.2 Seal the pre-registration with a hash — and know that the obvious repair defeats the seal

**What happened.** `docs/PREREG_METRO_MODEL.md` hashes to md5
`946f7ef75db69e5278eea409a04c3823`. That string is recorded in three places:
inside the result artefact (`metro_entry.json:prereg_md5`), in a byte-identical
reference copy at `reproducibility/seals/PREREG_METRO_MODEL.946f7ef7.md`, and
in `reproducibility/seals/SHA.md5`. CI re-derives it on every push, as the
**first** step of the `documents` job — before `pip install`, so it fails in
seconds and costs nothing (`.github/workflows/ci.yml:179-193`):

```yaml
      # The pre-registration seal. docs/PREREG_METRO_MODEL.md fixed the
      # hypothesis before the metro model was fitted, and its md5 is recorded
      # inside the result artefact. If the two ever disagree, either the
      # pre-registration was edited after the fact or the artefact was
      # regenerated against a different one -- and the whole claim to having
      # pre-registered evaporates. Corrections belong in the ERRATA file,
      # which is deliberately not covered by this hash.
      - name: Pre-registration seal matches the recorded hash
        run: |
          set -euo pipefail
          recorded=$(python -c "import json;print(json.load(open('outputs/metrics/metro_entry.json'))['prereg_md5'])")
          actual=$(md5sum docs/PREREG_METRO_MODEL.md | cut -d' ' -f1)
          echo "recorded in artefact : $recorded"
          echo "actual on disk       : $actual"
          test "$recorded" = "$actual"
```

**All of that machinery exists because the seal was broken twice and restored
twice.** Both breaks were well-intentioned improvements:

1. **2026-09-15, for a few hours.** Three motivating figures quoted in the
   pre-registration turned out to be wrong, and someone corrected them in
   place. [`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md)
   §1 records it: *"That was true for a few hours on 2026-09-15, when three
   wrong motivating figures were corrected inside the pre-registration itself.
   Those edits were reverted and the corrections moved to the errata file,
   precisely so this check keeps working — a pre-registration nobody can verify
   is worth very little."*
2. **A repo-wide path sweep.** When the hazard and gravity lines of work were
   retired to `experiments/`, an automated edit updated three now-stale
   artefact paths across `docs/` — and caught the sealed file.
   [`PREREG_METRO_MODEL_ERRATA.md`](PREREG_METRO_MODEL_ERRATA.md):
   *"**The paths in the sealed file were deliberately left wrong**, because
   correcting them would change the file and break the hash — which is exactly
   what happened once already."*

**Why it was easy to get wrong.** Nobody set out to weaken a pre-registration.
Both edits made the document *more accurate*, and a reviewer watching either
change land would have approved it. The property a seal protects is not
accuracy — it is **immutability**, and immutability is invisible in a diff.
That is also why the second one happened to a document the author never opened:
an automated sweep has no notion of a file that must not improve.

**And the repair is the part most people get wrong.** When the CI gate goes
red, the two obvious fixes both destroy the thing it protects.
`reproducibility/seals/README.md`:

> *"That gate is the right shape but it has one bad failure mode: when it goes
> red, the obvious repairs are both wrong. Re-running `make metro` re-stamps
> `prereg_md5` from whatever is on disk, which makes a broken seal invisible.
> Editing the pre-registration to match is worse. **The only honest repair is
> to put the original bytes back**, and that requires having them."*

So the design has four parts, and the fourth is the one worth copying:

- corrections go to a **separate errata file** the hash deliberately does not
  cover, so a correction never has to touch the sealed bytes;
- a **reference copy** on disk, making the honest repair a one-liner
  (`cp reproducibility/seals/PREREG_METRO_MODEL.946f7ef7.md docs/PREREG_METRO_MODEL.md`);
- the copy's **filename contains the hash**, so *"the file names its own hash
  and a silent swap is visible from an `ls`"*;
- the error message **names the remedy**, not just the failure.
  `scripts/preflight_publish.sh:227-228` prints
  `seal BROKEN … restore: cp reproducibility/seals/…`, and
  `scripts/README.md:107-109` states the general rule: *"'seal BROKEN' is
  useless; 'seal BROKEN in `docs/PREREG_METRO_MODEL.md` — restore it with
  `cp reproducibility/seals/...`' is not."*

**Still open.** `.pre-commit-config.yaml` has no seal hook, so a local
automated sweep still breaks it and you find out at push time. There is no
executable restore script; the restore is a documented `cp`.

**Rule.** A pre-registration nobody can verify is worth very little. Hash it,
put the hash inside the result artefact, keep a reference copy whose filename
is the hash, route every correction to a file the hash does not cover, and make
the failure message name the repair — because the intuitive repairs both make a
broken seal invisible. Stale paths inside a sealed document are a feature: it
records what was true when it was written.

## 1.3 The unit of analysis is the first thing to get right, and checking it costs nothing

**What happened.** The project's first model was a discrete-time hazard on
ZCTA-quarters: *will a delivery station open in this ZIP code this quarter?*
That names the outcome correctly and the **decision** incorrectly. Amazon does
not switch on ZIP codes; it signs a lease on a building, and coverage follows
mechanically from the van drive-time radius. One station switches on every ZCTA
within fifteen miles at once.

Measured on the delivered panel: the median station covers **58** ZCTAs, the
mean **88**, the maximum **307**, the minimum 4
([`DECISION_LOG.md`](DECISION_LOG.md) §2.1). The model treated those as
independent observations. The consequence is in the model's own diagnostics,
`experiments/hazard-model/artefacts/hazard_report.json`:

```
   risk set                          1,756 units, 40,358 rows, 812 events
   events per parameter, NOMINAL                             97.4
   events per parameter, effective (metro-quarter episodes)   5.6
   events per parameter, optimistic (usable facilities)       7.6
   floor                                                     10.0
```

**812 ZCTA-level "events" are not 812 decisions.** They are, on the report's own
upper bound, **38 usable facility decisions plus geometry**. A nominal 97.4
events per parameter looks like a well-powered study; the honest figure is 7.6,
below the conventional floor.

**Why it was easy to get wrong.** Every row was individually valid. A
ZCTA-quarter with a correct `enabled` flag, correct covariates and a correct
date is not a data error, and *nothing in the test suite could have caught it* —
there is no assertion you could have written over that dataframe that would have
failed. The violation is a property of the *mapping from rows to decisions*,
which lives in nobody's schema.

It also survived because the available explanation was better. Five documents
— `STATUS.md`, the backlog, `ROADMAP.md`, `ARCHITECTURE.md` and `REPRODUCE.md`
— reported the negative result correctly and all attributed it to **sample
size**. See §9.2; that is its own lesson.

**What caught it.** Reading Train (2009) on 2026-09-13. Note that the citation
then had to be corrected: the entry twice named **§2.2**, mutual exclusivity of
the choice set, and that is the wrong rule — a cloglog hazard on ZCTA-quarters
has no decision maker, so exclusivity is not a property it can violate, and
Train calls the criterion "not restrictive" on p. 12. The assumption actually
violated is **§3.7.1, printed p. 61** — independence across observations, the
assumption the likelihood itself is built on. Smaller claim, and a true one.
See §6.2.

**What it cost, and the uncomfortable half.** The model was retired, respecified
as *which ZIP, conditional on a station opening in metro m*, and refitted. At
94 decisions and 3 parameters that is **18.7 events per parameter**, clearing
the floor comfortably. On the held-out decisions the fitted model takes 19 of 38
at top-10 — and **the warehousing establishment count on its own, with nothing
estimated, takes 20 of 38.**

[`DECISION_LOG.md`](DECISION_LOG.md) §2.1: *"fixing the diagnosed fault did not
produce a working model, which means the diagnosis was incomplete, not wrong."*
`adr/0004`'s pre-registered residual risk — *"the reframe could be mistaken for
a rescue"* — is described there as having aged better than anything else in the
document: *"It was not a rescue. It fixed the question and left the answer where
it was."*

The retirement was later tested against the obvious objection, which is that it
only had 812 events. Rebuilt on **5,441** events with real opening dates — 6.7×
the data — AUC moved 0.6894 → **0.6832** and the constant null was better
calibrated in **17 of 17** comparisons
(`experiments/hazard-model/artefacts/hazard_revival.json`,
`run_id 20260915-224104-21a7`). **More data does not fix a defect in the unit of
analysis**, and demonstrating that is worth more than the original retirement.

**Rule.** Before writing any code, write down one row of your dataset and the
sentence "this row is one decision by one decision-maker." If you cannot, you
do not have a modelling problem yet. This check needs no data, takes minutes,
and no test suite will ever perform it for you.

## 1.4 Count distinct values per unit before you freeze the covariate list

**What happened.** The metro model's Tier 1 covariates — the ones that generated
the hypothesis, chosen deliberately "by mechanism not by trial" — were county
figures joined down to every ZCTA in the county.
[`research/COVARIATES_TRIED.md`](research/COVARIATES_TRIED.md) measures the
damage in a single column, `mean_distinct_values_per_large_metro`:

```
  usable at ZIP grain                 dead on arrival
    land_area_sqmi        200           traffic_proximity      9.2
    households            193           diesel_pm              9.2
    in_labor_force        195           low_income_pct         9.2
    employment            192           people_of_colour_pct   9.2
                                        permit_units_total     8.0
                                        permits_yoy_pct        7.9
```

Six of eighteen candidate columns offer a conditional choice model about **nine
distinct values** to discriminate among **two hundred** alternatives.

**Why it was easy to get wrong.** Every instinct you have for spotting a bad
covariate points the wrong way here. Coverage is excellent —
`traffic_proximity` is populated on 99.9% of panel rows. Cross-sectional
variance is high: `pm25` has 3,091 distinct values *across ZCTAs nationally*.
It correlates with the outcome. It passes a missingness check, a dtype check
and a contract. It is a real measurement of a real thing at a real place.

It is simply **near-constant inside the comparison the model actually makes**.
A conditional logit uses only variation *within* a choice set, and a county
figure has none. Nothing in a standard data-quality workflow computes
within-group distinct values, because that quantity only means something once
you know what the model conditions on — which is a modelling fact, not a data
fact, so it falls between the two roles.

**What it cost.** The pre-registration's own self-criticism
([`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md) §12) prices
it exactly: *"the check is two lines. Had they done so, the covariate list
would have been three or four columns long and the prereg would have said so."*
Downstream, the vintage gate dropped 8 of the 12 pre-registered covariates and
the coverage floor dropped 2 more, leaving two — so **the Tier 1 mechanism that
generated H1 was never testable on this panel at all**
([`EXPERIMENTS.md`](EXPERIMENTS.md) §14).

**Fixed, partially.** The check now runs as the first stage of the covariate
search, `models/covariate_audit.py:audit()`:

```python
def audit(panel: pd.DataFrame, columns: tuple[str, ...]) -> dict:
    """Coverage, grain and within-metro collinearity for every column."""
    ...
    for col in columns:
        have = big.dropna(subset=[col])
        per_metro = have.groupby("cbsa_code")[col].nunique()
        out[col] = {
            "populated_panel_wide": float(panel[col].notna().mean()),
            "zctas_time_varying": float(
                (panel.groupby("zcta")[col].nunique() > 1).mean()),
            "constant_within_large_metro": float((per_metro <= 1).mean()),
            "county_grain_share": float(
                (have.groupby("county_geoid")[col].nunique() <= 1).mean()),
            "mean_distinct_values_per_large_metro": float(per_metro.mean()),
            "within_metro_corr_with_baseline": _within_metro_corr(big, col),
        }
    return out
```

Be clear about what that is: a **printed diagnostic, not a gate**. Nothing
raises and nothing is dropped automatically; a human still has to read the
column.

**The general form of the rule, which the project only found afterwards,** is in
[`ROADMAP.md`](ROADMAP.md) § *Future scope*:

> **Covariates that work are computed as a distance *from* each candidate.
> Covariates that fail are looked up *against* it.**

A distance is unit-specific by construction. A lookup inherits whatever grain
its publisher chose, and most US public data is published at county level.

**Rule.** Before freezing a covariate list, print
`df.groupby(unit)[col].nunique().mean()` for every candidate, where `unit` is
whatever your model conditions on. Coverage, variance and correlation tell you
nothing about whether a column can discriminate *within* the comparison you are
actually making. If you want one screening statistic, use the within-group
coefficient of variation: below 0.6 it failed in 7 of 7 cases here; above 1.3
it worked in 9 of 14 ([`EXPERIMENTS.md`](EXPERIMENTS.md) §8).

## 1.5 Stratify before you believe a pooled number — this project hit Simpson's paradox twice

**First time.** The panel expansion appeared to make the model worse: pooled
top-10 lift fell **2.95× → 2.76×**. Stratified by choice-set size, no stratum
fell except the one where lift is capped by construction. In a choice set of
≤25 alternatives a uniform guess already lands in the top ten about two thirds
of the time, so lift cannot exceed roughly 1.5× however good the model is. The
new rows skew towards small markets, so the share of such decisions went from
**7.4% to 13.5%**. The pooled figure was measuring the *mix*
([`research/NOTES_EXPANDED_REFIT.md`](research/NOTES_EXPANDED_REFIT.md), the
correction block).

**Second time, and this one is textbook.** The metro model's pooled out-of-time
AUC is **0.7323**. Its AUC within each household tercile
(`metro_entry.json`, `strata.tiers`):

```
  tier 1   312 metros, 2,184 metro-years,   6 events    AUC 0.4125
  tier 2   311 metros, 2,177 metro-years,  27 events    AUC 0.5666
  tier 3   312 metros, 2,184 metro-years, 273 events    AUC 0.6961
  ---------------------------------------------------------------
  pooled                6,545 rows,       306 events    AUC 0.7323
```

**The pooled number is higher than the model's AUC in every stratum it pools.**
It is collecting the between-tier signal that "big metros get more facilities"
supplies for free. Stratifying *strengthened* the negative finding: the
direction against the households baseline is unchanged in all three tiers, so
the conclusion is not an artefact of pooling.

**Why it was easy to get wrong.** A pooled metric is the default output of every
evaluation function ever written, and a stratified one requires you to have
already decided what the strata are. More subtly: the pooled figure is not
*wrong*. 0.7323 is exactly what it says it is. It is a true answer to a question
nobody asked — "can you separate events from non-events across the whole
sample, including across strata?" — and it reads as an answer to the one you
did ask.

**What caught it the second time.** Prereg §6 had ordered it in advance:
*"Stratify by metro size tier and report distinct-metro n per tier. Pooling
across heterogeneous strata is a Simpson's-paradox trap this project has fallen
into twice, the second time inside a standardisation."* The emitter now prints
the warning into the artefact itself (`models/metro_entry.py:218`), so it
travels with the numbers rather than living in a document.

**Rule.** A pooled metric over heterogeneous strata is a statement about the
mix. Always report per-stratum n *and* per-stratum metric. If the pooled value
sits outside the range of the strata, you have found the paradox, not a result.
And put the warning in the artefact, not in the write-up — the artefact is what
gets quoted.

## 1.6 A percentile spread across re-splits is not a standard error, and the direction of the gap does not transfer

**What happened.** Almost every interval this project publishes is a
`[2.5, 97.5]` percentile over 50 re-splits of **one fixed decision set** —
in `gravity_network.json`, `panel_experiments.json`, `metro_entry.json`,
`refit_expanded.json`, `covariate_search.json`, `percapita_search.json` and
`logrel_search.json`. Each of those artefacts carries a
`spread_is_not_a_standard_error` or `interval_note` field saying so, and
`models/metro_resample.py:6-14` routes the *quotable* interval to a
metro-clustered bootstrap instead.

The rule is easy. What is not easy is that the project measured the gap
**three times and got three different answers, in both directions**
([`ALGORITHMS.md`](ALGORITHMS.md) §5):

```
  COVARIATES_TRIED.md     metro-clustered interval   5% WIDER  than re-split
                          (and on 483 decisions vs the re-split's 290)
  PREREG_METRO_MODEL.md   clustered bootstrap     24-28% WIDER
                          (measured on the ZIP-level problem)
  NOTES_METRO_ENTRY.md    re-split spread            31% WIDER
                          (measured on the metro-level problem)
```

`docs/data/FIGURES.md` adds a fourth, recomputed per-parameter from
`network_inference.json` (`run_id 20260915-210640-dbcd`), and it is the one that
settles the matter:

```
  establishments               1.242x wider
  warehousing_establishments   0.954x   <- NARROWER
  sortation_proximity          1.399x
  fulfilment_proximity         1.479x
  --------------------------------------
  mean 1.268    median 1.320
```

**The direction is not even uniform across parameters within a single run** —
and it flips on `warehousing_establishments`, the one parameter the headline
rests on. Clustering over *metros* also gives **narrower** intervals than
clustering over *decisions* (ratios 0.73–0.97), so metro-clustering is not the
conservative choice by default either.

**Why the direction moves, which is the part worth understanding.** Re-splits
resample a fixed set of decisions and **refit fifty times**, so they include
estimation variability. A clustered bootstrap resamples the clusters and
conditions that away. They answer different questions, so there is no reason
for them to agree in magnitude *or* in sign — and here they do not.
[`ALGORITHMS.md`](ALGORITHMS.md) §5: *"The rule holds universally; the direction
is problem-specific and must not be carried forward."*

**What it cost.** The pre-registration generalised the ZIP-level measurement to
the metro-level problem without saying so. That is Errata Correction 4 — a
correction against the project's own document, on a clause used to justify
reporting both intervals. The substantive conclusion was unaffected.

**A related trap from the same section, worth its own sentence.** A top-10 count
near 20 of 38 carries a **binomial standard error of about 3 decisions before
any split variation at all** (`MODEL_SPEC.md` §9.4). A one-hit difference
between two methods is noise, and §9.2 below records a case where exactly that
was read as a verdict.

**Rule.** Name which resampling you did and on which problem, every time. Never
substitute one for the other because you have a number from the neighbouring
analysis, and never carry the *direction* of the gap across problems — it is
not a property of the methods, it is a property of your data.

## 1.7 Resample the unit the decision was made at, and beware the resample that quietly draws without replacement

**What happened.** `models/choice_bootstrap.py` resamples **whole decisions**,
never individual alternatives. [`ALGORITHMS.md`](ALGORITHMS.md) §3 states why:
*"a metro's 200 ZIPs are not 200 independent things, and a resample scattering
them across replicates, possibly without the chosen one, would be a draw from
nothing."* It is the same error as §1.3, one level up, and the module
cross-references `adr/0004` to say so.

A second, subtler decision sits beside it. `resample_decisions` deliberately
avoids the existing `ChoiceData.subset` helper, because a decision drawn twice
would collapse to one — *"a draw WITHOUT replacement, understating the spread,
which is the flattering direction."*

**Why it was easy to get wrong.** `subset` is the obvious tool; it is already
written, already tested, and does what the name says. The bug it would have
introduced is not visible in any output — the intervals come out narrower, which
looks like a better-behaved estimator, not a broken one. Every failure mode in
this section flatters the result.

**Two more choices in the same module worth copying.** Two bootstraps are run
side by side (1,000 over decisions, 1,500 over metro clusters) on the explicit
ground from `MODEL_SPEC.md` §6.3 that *"a disagreement is itself a finding about
how little the sample constrains the model"*; where they differ, the metro one
is the conservative one and the one to quote. And stopping is adaptive with a
**measured, deliberately unchased far endpoint**: a ratio has a heavy right tail
here, so the 97.5th percentile *"would need of the order of 100,000 replicates
to settle and would still be the 97.5th percentile of 56 decisions."*

**Rule.** The resampling unit must equal the decision unit. Check explicitly
whether your resampler draws with replacement — a helper designed for subsetting
usually does not, and the resulting error makes your intervals narrower, which
is the direction nobody investigates.

---

# Part 2 — Estimators that fail quietly

Everything in this part shares one property: **nothing raised, nothing warned,
and the output looked like a result.** That is the class of bug worth building
habits against, because the loud ones take care of themselves.

## 2.1 `r.fun < nan` is always False, so a NaN start is never displaced

**What happened.** `models/choice.py:fit` runs a five-start optimisation and
keeps the best by `if best is None or r.fun < best.fun`. Every comparison
against NaN evaluates False. So a NaN objective from the **first** start is
never displaced by any later start, however good, and `fit` returns an all-NaN
β — with no exception, no warning, and no failing test — which propagates into
every downstream metric.

The mechanism: the positivity reparameterisation `β = exp(θ)` overflows, `β′a`
becomes `inf`, and `inf/inf` is NaN. The symptom that finally exposed it, on
2026-09-14, was **a single `nan` in a printed mean**.

The current code, `choice.py:266-295`, and its comment is the clearest
statement of the trap anywhere in the repository:

```python
    for start in [np.zeros(k), *(rng.normal(0, 1.0, size=(4, k)))]:
        r = minimize(_neg_log_likelihood, start, args=(d,), method="BFGS")
        r = minimize(_neg_log_likelihood, r.x, args=(d,), method="Nelder-Mead")
        # A non-finite objective is a FAILED start, not a candidate.
        #
        # The guard is not defensive tidiness; without it the multi-start is
        # silently defeated by its own comparison. `r.fun < best.fun` is False
        # whenever `best.fun` is NaN, because every comparison against NaN is
        # False. So a NaN from the FIRST start is never displaced by any later
        # start, however good, and `fit` returns a NaN model with no error, no
        # warning, and a `beta` of all-NaN that propagates into every metric
        # downstream. It was found on 2026-09-14 by a covariate experiment
        # whose only symptom was a `nan` in a printed mean.
        if not np.isfinite(r.fun):
            continue
        if best is None or r.fun < best.fun:
            best = r

    if best is None:
        # Every start failed. Raising beats returning NaN: a caller that gets
        # an exception stops, and a caller that gets NaN carries it into a
        # published number.
        raise RuntimeError(...)
```

Note the two halves. `continue` on a non-finite objective fixes the comparison;
the `raise` when *all* starts failed fixes the thing that matters more — *"a
caller that gets an exception stops, and a caller that gets NaN carries it into
a published number."*

**Why it was easy to get wrong.** `best.fun` comparison is the canonical
multistart idiom and appears in every optimisation tutorial. It is correct for
every value except one, and that one does not raise. Worse, the multi-start
structure makes it *look* robust — five starts is more careful than one — while
the NaN case turns five starts into one bad one.

**The part that generalises further than the bug.** The identical pattern was
copied into the bootstrap and **survived the first fix by two days**. The comment
now in `models/choice_bootstrap.py:107-113` dates it:

```python
        # The same guard as choice.fit, and for the same reason. Without the
        # finiteness test a non-finite first start is never displaced: every
        # later `r.fun < nan` is False, so `best` keeps the NaN result and this
        # returns NaN parameters with no warning. That failure was found in
        # choice.py on 2026-09-14; this copy of the loop was missed and still
        # had it on 2026-09-16.
```

A bootstrap replicate is the worst possible place for it: *"a replicate that
silently yields NaN parameters poisons the percentile it feeds without ever
failing a test."*

**Rule.** Any `best`-tracking loop over a floating-point objective needs an
`isfinite` guard on the candidate and a raise if nothing was feasible. When you
fix an instance of a pattern, **grep the repository for the pattern** — this
project fixed one of two copies and did not notice for two days.

## 2.2 An optimiser can report a better objective at an infeasible point

**What happened.** The log-relative experiment expressed each ZIP's covariate
relative to its metro mean, in logs — a reasonable reframing of the suspicion
that the covariates failed on scale rather than content. Five arms came back
with a non-zero coefficient where the untransformed columns had reported
nothing. **All five were infeasible.**

`β = exp(θ)` constrains the *coefficients* positive, which is what makes
`P(j|m) = β′a_j / Σ_k β′a_k` a probability — but only while every attraction
column is non-negative. Add a centred or log-relative column and *a positive
coefficient on a negative column subtracts attraction*. The optimiser found
that it could buy likelihood by pushing **non-chosen** alternatives below zero,
shrinking the denominator. Measured
([`NOTES_LOG_RELATIVE.md`](../experiments/percapita-logrel/notes/NOTES_LOG_RELATIVE.md)
§3.1, [`ALGORITHMS.md`](ALGORITHMS.md) §2):

```
  past the feasibility ceiling            19.55x  to  77.19x
  non-chosen alternatives driven negative    765  to   4,816
  P(chosen) inflated                    0.078685  ->  0.079346
  log-likelihood bought                             up to +1.20
  negative AND chosen                                        0
```

That last line is why nothing complained. The chosen alternative stayed
positive throughout, so no term in the objective ever became undefined.

**Why it was easy to get wrong — two layers.** First, the module docstring said
the exp parameterisation *"enforces"* positivity, and that sentence had been
true for the entire life of the codebase, because every attraction column had
been non-negative. The guarantee was real and its precondition was undocumented.
Second, a transform that suddenly makes dead covariates work is exactly the
result you were hoping for. Five arms reporting signal after fifteen covariates
reported nothing is a story, and the story is more interesting than the
arithmetic.

**What caught it: a pattern across arms, not a failure within one.**
*In all five columns, the direction with the lower feasibility ceiling was the
one that "found" a coefficient.* Success was predicted by how cheap it was to
violate positivity. No single run misbehaved; the correlation across runs did.

**The guard**, `choice.py:297-334`, checks the fitted *quantities* rather than
the parameters, and its comment records the crucial relationship to §2.1:

```python
    # The non-finite-start guard above does NOT catch this. An infeasible
    # optimum has a perfectly finite log-likelihood; that is the whole problem.
    utility = d.a @ beta
    n_bad = int((utility <= 0).sum())
    if n_bad:
        raise ValueError(... "Enter such a covariate through a separate "
            "unconstrained linear index, not inside ln(beta'a). "
            "See docs/research/NOTES_LOG_RELATIVE.md.")
```

Two things worth copying: the error message **names the remedy**, not just the
fault; and the remedy is a specific, standard alternative
(`V_j = ln(β′a_j) + γ′z_j` with γ unconstrained — the textbook "size variable
plus linear index" form), which is described in the codebase and deliberately
not implemented, so the next person is not left to rediscover it.

**What it cost.** The experiment is retired and **no longer reproduces**:
re-running it now raises on all five arms. It is kept anyway, because the guard
is the finding ([`experiments/README.md`](../experiments/README.md)).

**Rule.** Constraining the parameters is not constraining the model. Check
feasibility of the fitted *quantities* at the optimum, and raise. If an unusual
transform suddenly makes a dead covariate work, suspect the estimator before
you believe the result — and look for a pattern *across* arms, because the
single-run diagnostics will all be clean.

## 2.3 At a boundary the formula still returns a number, and the number is arbitrary — not wide

**What happened.** The project implements a Huber–White sandwich estimator,
`H⁻¹WH⁻¹` (Train §8.6, p. 201), in `models/choice_sandwich.py`. Two of the
model's three coefficients went to the boundary: under `β = exp(θ)` a discarded
column walks θ towards −∞ and lands at β ≈ 3e-16.

At a boundary the maximum is not interior, the gradient does not vanish, and
the Hessian block is not the information matrix. The formula still evaluates.
**The code refuses to print the result.** The `REFUSAL` string, verbatim:

> *"The number the formula returns is not a **wide** standard error — it is an
> arbitrary one, whose size is set by how far the optimiser happened to wander
> before it stopped."*

Those parameters get `{"available": false, "reason": REFUSAL}`.

**Why it was easy to get wrong, and this is the crux.** *A wide standard error
and an arbitrary one look identical in a table.* A reader seeing `SE = 4.2`
concludes "imprecisely estimated" — a modest, honest-sounding claim. The truth
is "this number is a function of the optimiser's stopping tolerance, not of the
data." Nothing errors, nothing warns, and the misreading is the natural one.
Printing it would have been *more* informative-looking than refusing.

**Two supporting decisions worth stealing.** Derivatives are **analytic**, on
the stated ground that *"finite-differencing a log-likelihood that is flat to
machine precision in two of its three directions returns noise."* And a
second-order caveat is surfaced rather than resolved, as an artefact field
named `conditional_on_boundary_selection`: the interior block is itself
conditional on the other two parameters being *exactly* zero rather than
*estimated at* zero, and inference after boundary selection is an open problem.
Andrews (1999) is cited *"as a lead to follow rather than as support"* — a
citation grade this project invented and should keep (§6.2).

**A corollary that bites elsewhere: "at the boundary" is a rule, not a fact.**
Two rules are in use in this repository and **they disagree on the same column**
([`ALGORITHMS.md`](ALGORITHMS.md) §2, [`NUMBERS.md`](NUMBERS.md) confusable
quantity 8). The *percentile* rule asks whether a column's 2.5th percentile over
50 re-splits clears `BOUNDARY_TOL = 1e-6`; the *point-estimate* rule asks
whether the full-sample β does. Under the first, `sortation_proximity` is
"boundary inside the interval"; under the second it is `at_boundary: false`
(β = 0.097, 3.8% of bootstrap replicates at zero). Both are current and both
are right under their own rule.

**Rule.** When an estimator's assumptions fail, refuse to emit the number rather
than emitting it with a caveat — a caveat in prose does not travel with a value
in a table. And if you report "n parameters at the boundary", name the rule that
decided it.

## 2.4 A reparameterisation that buys positivity silently forbids repulsion

**What happened.** `beta = np.concatenate([[1.0], np.exp(theta)])`
(`choice.py:246`) guarantees positive weights so that shares are probabilities.
[`ALGORITHMS.md`](ALGORITHMS.md) §2 states the price plainly: *"the model cannot
express a variable that repels — if high house prices make a site less
attractive, the best this form can do is set the weight to zero."*

**What it cost, concretely.** `land_area_sqmi` went to the boundary. The
proposal had claimed that *"a positive loading on households beside a negative
loading on land area would constitute a density preference"* — a hypothesis
that, in this specification, **was never available to be tested**. It has been
withdrawn from the proposal (`adr/0004-model-change-conditional-choice.md`).

**Why it was easy to get wrong.** The reparameterisation is textbook and it is
the *right* fix for the positivity problem. Its restriction is invisible in
every diagnostic: a repelling variable does not error, does not warn, and does
not fail to converge. It converges beautifully to zero — which reads as *"this
covariate does not matter"* rather than *"this model cannot represent what you
asked."* The two conclusions are opposite and the output is identical.

**Fixed?** No. The minimal structural fix is described and deliberately not
implemented; it is the same `V_j = ln(β′a_j) + γ′z_j` form named in §2.2.

**Rule.** For every constraint you impose for numerical convenience, write down
the hypothesis it makes untestable, and check that list against the claims you
have already published.

## 2.5 A ratio objective is degenerate by construction — plot the objective before you trust its argmax

**What happened.** The portfolio optimiser's objective was "minimise the
marginal break-even margin." Plotted against the number of activations:

```
  n =   1   marginal break-even  $1.1910   <- the minimum
  n =  10                        $1.4903
  n = 100                        $1.5278
  n = 317                        $1.5193
  n = 500                        $1.5516
```

**The objective said "build one facility."**
[`DECISION_LOG.md`](DECISION_LOG.md) §2.5: *"and it was not wrong on its own
terms; the terms were wrong. Break-even margin is a ratio, and the best ratio is
always the single best site."*

**Why it was easy to get wrong.** The objective was a perfectly reasonable
*metric* — break-even margin is exactly what you would report per site — and
somebody made it the thing to optimise. The optimiser converged, the code ran,
and the output was a plausible portfolio, because the greedy was stopped by a
budget rather than by the objective. Nobody plotted it.

**What nearly shipped, and what it cost.** The project's actual headline — *at a
$2bn budget the optimiser funds only part of the fundable activations and leaves
the rest unspent* — **could not have been produced by the old objective at all**.
"Do not spend the whole budget" is a finding; "minimise a ratio" can only ever
return "build one."

**Two arithmetic bugs were found alongside, and both flattered the same
conclusion** (that clustering is valuable):

- annual flows used **365** days; the network delivers **312** (6 × 52). Capital
  does not scale with flow, so this understated break-even by ~3.5%.
- the line-haul cost pool applied a *mileage* share to *total* cost. Door time
  and van lease are paid whatever route was driven, so the shareable pool was
  **2.9× too large**.

The decision log's summary is the transferable part: *"Three of these four
errors were invisible in the output — the portfolio still printed, the metros
still looked plausible, the gap still looked small."* What found them was asking
**"what does this objective do at n = 1"** and **"what calendar is this
annualised on"** — neither of which requires the data to have arrived.

**Fixed, and the fix anticipates its own recurrence.** NPV maximisation
`NPV(S) = m·A(S) − B(S) − K(S)`, with the same degeneracy *pre-emptively
re-flagged in the sibling code path that computes the upper bound*, on the
stated ground that *"an error found once tends to recur in the sibling code
path."* Because the margin `m` is unobservable, the deliverable is a **frontier
over six margins**, not a point.

**A neighbouring restraint worth copying**, from the same optimiser
(`experiments/portfolio-optimiser/code/pkg/objective.py:20-35`): shared line
haul is a *positive* interaction, cannibalisation a *negative* one, and
*"a set function with both positive and negative interactions is neither
submodular nor supermodular, so the classic (1 − 1/e) greedy guarantee does NOT
apply. Anyone claiming that bound here is wrong."* The code reports an achieved
objective plus a computed gap instead. That is a guarantee correctly *not*
claimed, which is rarer than a guarantee correctly claimed.

**Rule.** Plot your objective against the decision variable before you believe
its argmax, and evaluate it at the degenerate endpoints by hand. A ratio
objective almost always optimises to n = 1. And ask what calendar every
annualised quantity is on — that question needs no data and catches a class of
error that never surfaces as a failure.

---

# Part 3 — Parameters, and the things that are not parameters

## 3.1 A docstring that argues an error is small is an untested hypothesis

**What happened.** The first cost model put one depot per metro at the
population-weighted centroid. Its own docstring argued the choice barely
mattered, because line haul enters divided by capacity `C`: verbatim,
*"at C=120 a ten-mile error moves cost per parcel by well under a cent."* The
sentence survives as a quotation in `docs/data/COST_MODEL.md:380-383` and
`tests/unit/test_cost_evaluate.py:146-151`.

Then somebody measured it
([`DECISION_LOG.md`](DECISION_LOG.md) §2.2):

```
  implied line-haul distance   min 0.4 mi   max 145.7 mi   p90 60.2 mi
  cost of one extra mile                    $0.0192 per parcel
  worst-case geometric artefact             ~$2.79 per parcel
  median cost per parcel under the proxy    $1.5094
```

"Well under a cent" was wrong by roughly twentyfold, and in the worst ZCTA the
pure geometric artefact (**$2.79**) *exceeded the entire median cost* ($1.51).

**Why it was easy to get wrong.** The argument was **correct algebra on an
unmeasured premise**. `2L/C` genuinely is small when `L` is small. Nobody had
looked at the distribution of `L`, and a p90 of 60 miles is not "a ten-mile
error." Locally valid, globally false — the hardest kind to spot, because
reading the docstring critically still leaves you agreeing with it. And it was
written by the person who had the data to check it, in ten minutes, and did not.

**What it cost.** The entire depot layer was rebuilt as a solved 334-depot
p-median network (`src/siting_atlas/cost/depots.py`). Median cost per parcel
fell **$1.5145 → $1.0875**; line-haul p90 fell **60.2 → 10.05 mi**; the
`congested` scenario's spread fell from +14.5% to +4.4% — *"the old sensitivity
table was partly measuring the proxy."* And a published ranking was wrong at the
top: **ZCTA 11222 (Greenpoint) fell from 6th cheapest to 306th**, because *"it
had been rewarded for sitting near an imaginary point."*

**Still open, in the same voice.** `income_elasticity = 0.35` ("set
conservatively") and `parcels_per_stop = 1.4` in `cost/params.py` are both
defended by argument rather than measurement. The decision log's standing
instruction is the rule: ***"Treat a docstring that says an assumption does not
matter as an open ticket."***

**Rule.** "This approximation is small" is a hypothesis with a number attached.
Either measure the distribution of the quantity it depends on, or delete the
sentence — because left in place it will be read as evidence by the next person,
including by you.

## 3.2 A radius is not a parameter. It is the definition of the dependent variable

**What happened.** `CATCHMENT_MILES = {"DS": 15.0, "SDC": 10.0}`
(`warehouse/facilities.py:125`). The 15 miles is a judgement — a conservative
reading of an unsourced trade claim that a delivery station serves a 20–30
minute drive. The comment above it is unusually honest about that, and about
what the number actually controls:

```
#: ENGINEERING ESTIMATE. No published source was found for either figure, and
#: the "20-30 minutes" is itself an unsourced trade claim. ...
#:
#: This parameter touches no cost figure at all, and it is still one of the
#: most consequential numbers in the project, because it sets the SAMPLE SIZE
#: for the causal stage. Measured against the delivered panel (2026-09-13):
#:
#:      5 mi ->    383 ZCTAs ever enabled        15 mi -> 1,257  (baseline)
#:     10 mi ->    882                           20 mi -> 1,593
#:                                               25 mi -> 1,819
#:
#: The error is not symmetric: a radius that is too LARGE labels untreated
#: ZIPs as treated, which attenuates every hazard coefficient toward zero.
```

[`DECISION_LOG.md`](DECISION_LOG.md) §1.5 states the point in one line:
***"The radius is not a tuning knob; it is the target variable."***

**The band now exists, and it is more damning than the entry suggests.**
`outputs/metrics/catchment_band.json` (emitted by
`warehouse/catchment_band.py`) sweeps seven radii, each attached to a named
external anchor rather than chosen for roundness:

```
  8.3 mi  45-min drive, congested profile        721 ZCTAs   AUC 0.7081
 12.7 mi  45-min drive, cost baseline          1,093         AUC 0.6689
 15.0 mi  CURRENT VALUE                        1,257         AUC 0.6894
 19.6 mi  45-min drive, fast end               1,568         AUC 0.6829
 25.0 mi  Holmes (2011) choice radius          1,819         AUC 0.6406
 45.0 mi  MWPVL: DS "designed to service a
          45-mile radius"                      2,572         AUC 0.6269
 60.0 mi  OVER-RUN PROBE (excluded)            3,153
```

Three findings, all verified today against the artefact:

1. **The sample size nearly quintuples across a defensible range of one
   unsourced constant.** `zctas_ever_enabled` runs 721 → 2,572 (3.57×) and
   `enabled_cells` 4.76×.
2. **The radius manufactures statistical significance.**
   `"households_significant_at"` is all six radii, but
   `"all_three_covariates_significant_at": [25.0, 45.0]`. At 15 miles only
   `households` clears p<0.05; widen the assumption in the *outcome* and
   `establishments` and `median_household_income` become significant — **with no
   new data**.
3. **The negative result is robust, which is the good news.**
   `"null_better_calibrated_at"` is *all six* radii, and
   `"auc_at_or_above_0_80_at"` is empty. The conclusion does not depend on the
   radius; the covariate p-values do.

The artefact's own closing line is the one to steal verbatim: *"NOT a confidence
interval. There is one true catchment radius and we do not know it."*

**Why it was easy to get wrong.** A radius *looks* like a parameter — it is a
float in a dict with a unit. It is actually a definition of the dependent
variable, and definitions do not appear in sensitivity tables, because
sensitivity tables are for parameters. The distinction is invisible in the type
system and invisible in the code.

**Two live discrepancies, reported rather than smoothed over.**
`DECISION_LOG.md` §1.5 quotes 874 / 1,231 / 1,530 at 10/15/20 mi;
`catchment_band.json` records `recorded` = `remeasured` = **882 / 1,257 / 1,593**
with `"agrees": true`. The denominators differ (2,413 pilot ZCTAs versus
`units_in_scope: 2206`) and **neither document says so** — two independently
"verified" measurements of the same quantity, disagreeing by about 2%, each
self-certified. Separately, `analysis/white_space.py:64` sets
`HEADLINE_MILES = 45.0` — *"the externally-sourced radius, and the one every
headline quotes"* — while `facilities.py:125` builds the target at 15.0. **The
project has two headline radii in two subsystems**, which is how the
densification range came to be quoted as "67–77%" when 67.1% is a 15-mile figure
and 75.9% is a 45-mile one ([`NUMBERS.md`](NUMBERS.md) §6).

**Rule.** For every constant, ask whether it enters the *model* or the
*definition of the outcome*. If the latter, it is not a parameter — sweep it,
report the band, anchor each point to something external, and check
specifically whether any inferential conclusion appears or disappears across
the sweep.

## 3.3 Never sum a per-unit ceiling

**What happened.** Verified today against
`outputs/tables/cost_to_serve_2023q4_baseline.parquet`:

```
  sum(vans_required)     79,484
  ceil(sum(van_days))    78,292
  difference              1,192      <- pure rounding artefact
  rows                     2,333
```

[`DECISION_LOG.md`](DECISION_LOG.md) §2.6's example is the whole lesson:
*"Two ZCTAs each needing 0.6 of a van's day. Round each up and you have 2 vans;
a real depot sends one van to both and uses 1.2 van-days. Multiply that across
2,333 ZCTAs and you have invented 1,192 vans."*

**Why it was easy to get wrong.** `vans_required` is the **correct** column for
a single ZCTA — you cannot send 0.6 of a van. It becomes wrong only under
aggregation, and nothing about the column's name, dtype or contract says so.
Every row is individually valid; the defect lives in the `.sum()`, which is
somewhere else entirely, written by someone reasonably assuming a column named
`vans_required` can be added up.

**Fixed, with the fix placed where the mistake happens.**
`cost/daganzo.py:204-217` adds a `van_days` column and keeps `vans_required`
with an explicit **"must NOT be summed"** warning attached to the column;
`cost/runner.py:102` reports `ceil(result["van_days"].sum())`. Guarded at
`tests/unit/test_viz.py:226-237`.

**A postscript that is itself a lesson.** `DECISION_LOG.md:1113` still lists
three documents as publishing the buggy 79,484. Re-checked today, every
surviving occurrence across `docs/` is inside an explicit retrospective
correction (`REPRODUCE.md:534` — *"This block said 79,484 … until 2026-09-13"*;
`engineering/PIPELINE.md:672`; `COST_MODEL.md:543-547`). **The defect register
is now behind the tree in the opposite direction** — it reports as open
something that has been closed. That is the mirror image of §4.1 and it is just
as misleading to a reader.

**Rule.** A per-row quantity that has been rounded, clipped, floored or
ceilinged must not be aggregated. Emit the unrounded quantity beside it, name it
so the difference is obvious, and put the warning on the column rather than in a
document.

## 3.4 Sampling a derived parameter independently draws physically impossible worlds

**What happened.** `optimize/params.py:213` defines
`delivery_days_per_year = delivery_days_per_week * 52.0`, so the baseline
identity is 6 × 52 = 312. But the Monte Carlo samples **both sides of that
identity, independently, from two different dictionaries**:

```
  montecarlo.py:87   COST_RANGES        delivery_days_per_week   (5.0, 7.0)
  montecarlo.py:111  PORTFOLIO_RANGES   delivery_days_per_year   (260.0, 365.0)
```

[`AUDIT_2026_09_14.md`](AUDIT_2026_09_14.md) §3.5: *"The Monte Carlo can draw 5
days/week and 365 days/year in the same replicate — a physically impossible
portfolio. How often, and how much it widens or distorts the band, is
unmeasured."* `docs/data/UNCERTAINTY.md`: *"until they are tied this study is
propagating an inconsistency rather than an uncertainty."*

**Why it was easy to get wrong.** Two range dictionaries live in two
subsystems, each internally consistent and each reviewable on its own. The
identity that binds them sits in a **default-argument expression on one line of
a dataclass**, more than a hundred lines from either sampler. Nothing that reads
either dictionary can see the other, and no type or test expresses the
constraint.

**How it was found, which is the better half of the story.** It surfaced *while
writing the missing documentation*. `delivery_days_per_year` appeared in the
parameter sweep table with **no entry in the parameter register at all** — the
one sampled constant with no recorded source, classification or justification.
Completing the paperwork surfaced the bug. **The documentation gap and the code
bug had the same root cause:** nobody had ever written down where the number came
from, so nobody noticed it came from somewhere else.

**A compounding defect, and an unusually honest retraction.**
`delivery_days_per_week` turns out to be the second-strongest single driver of
the activation count of any parameter in the model (ρ = +0.280), ahead of every
portfolio parameter. `UNCERTAINTY.md` then argues *against its own headline*:
the parameter *"conflates how many days a week the network delivers with how
many hours a year one driver works. Sampling it therefore moves two things at
once, and part of its apparent power here is that conflation rather than genuine
economic leverage… read this row as **'a defect is doing a lot of work'**, not as
'network delivery frequency is the second-biggest lever'."*

**And a caveat on the whole method**, from the same file: independent sampling is
itself a generous assumption — *"if `service_minutes_per_stop` is wrong it is
probably wrong because `stops_per_tour` is also wrong… Drawing them
independently lets errors cancel. Correlated draws would widen the bands, not
narrow them."*

**Not fixed.** Estimated at one hour.

**Rule.** Before running a Monte Carlo, list every parameter and mark which are
*derived* from others. Derived quantities must be computed inside the draw loop,
never sampled. And write the provenance register first: the parameter with no
recorded source is where the bug is.

## 3.5 The biggest lever in your model may not be classified as a parameter at all

**What happened.** The portfolio result moved twice during verification:
activations **317 → 330 → 282**, capital **$1.268bn → $1.320bn → $1.128bn**.
[`DECISION_LOG.md`](DECISION_LOG.md) §4.2 refused to edit around the question —
*"Before any document is edited, somebody should establish **why** it moved — an
input drift that nobody intended is a bigger problem than a stale number"* — and
the answer, when it came, was *"not the flattering one"*:

```
  1  A 500-draw Monte Carlo over every documented cost and portfolio
     parameter puts the activation count at p10 152, p50 264, p90 306.
     The current 282 sits at the 67th percentile and the superseded 330
     at the 97th. So the drift is REAL -- wider than parameter
     uncertainty -- and cannot be blamed on parameter choice.
  2  capital_usd is exactly $4m x n in all 500 draws. The three published
     capital figures were never independent evidence; they are the three
     activation counts restated. "$1.268bn -> $1.320bn -> $1.128bn"
     communicated three facts and contained one.
  3  Depot placement moves the answer more than any documented parameter
     and is not classified as a parameter at all. That is the defect.
```

The third move was caused by depot placement changing from k-means to p-median,
**with nothing in `optimize/` touched at all**.

**Why it was easy to get wrong.** A sensitivity analysis enumerates the things
you called parameters. Anything implemented as an **algorithm choice** rather
than a constant is structurally invisible to it — it has no entry in a range
dictionary, so it cannot be swept, so it never appears in a tornado chart, so it
reads as settled. And point 2 is the subtler half: a *derived* output can
masquerade as corroborating evidence. Three capital figures looked like three
pieces of evidence about capital; they were one activation count wearing three
costumes.

**Why k-means was the wrong choice**, since that is transferable
([`ALGORITHMS.md`](ALGORITHMS.md) §10): *"k-means minimises **squared** distance
and lands on the weighted **mean**, while this cost model bills line haul
**linearly** and the minimiser of weighted linear distance is the weighted
**median**. 60 parcels at mile 0 and 40 at mile 50 gives the mean (mile 20)
2,400 parcel-miles and the median (mile 0) 2,000."* Switching to p-median removed
**9.3% of billed parcel-miles** and reordered the published ranking (Spearman
ρ 0.888). It was easy to get wrong because k-means is the default "put points in
groups" tool, it converges, and it looks sensible on a map — the loss-function
mismatch is invisible in the output.

**Rule.** Your uncertainty analysis covers the things you wrote in a range
dictionary. Before you publish a band, list every *algorithmic* choice — the
clustering method, the solver, the tie-break, the aggregation order — and ask
which of them could move the answer further than your widest parameter. Then
check whether any two of your headline figures are deterministic functions of
each other.

**Closed, 2026-09-16, and the close is worth as much as the finding.** Point 3
above is no longer true of the cost model, because the lever was **deleted
rather than tuned**. The facility panel turned out to carry 501
address-geocoded delivery stations, so `cost/stations.py` uses those as the
depots and `cost/depots.py` is retired from the cost path. There is no
placement algorithm left to be invisible to a sensitivity sweep, and
`parcels_per_depot_per_day` — the largest *rank* mover in the model, Spearman
0.90 — no longer enters the cost path at all.

The price of the repair is the interesting part, and it is a measurement:
median cost per parcel $1.0830 → **$1.1389 (+5.2%)**, median line haul
**4.02 → 9.09 miles** (`cost_by_station.json`, `run_id 20260916-131845-34f1`;
`NUMBERS.md` §10.3). A p-median minimises demand-weighted distance by
construction, so it is a **lower bound** on line haul — the solved network was
not merely arbitrary, it was *optimistic*, and every cost figure this project
published before 2026-09-16 was biased downward for a reason nobody had
stated. **When your unclassified lever is an optimiser, the bias has a known
sign.** That is a stronger statement than "it moves the answer", and it is
available for free the moment you notice the lever is a solve.

**The generalisable version.** The fix for a lever that is not a parameter is
usually not to promote it to a parameter and sweep it. It is to find the
observation that makes it unnecessary. Ask of every invented layer: *is there a
dataset in which this thing is simply recorded?* Here the answer had been
sitting in the project's own `data/external/` directory for a week.

---

# Part 4 — Believe the artefact, not the document

## 4.1 Verify against the artefact. Never against a corrected document

**What happened.** Corrections in this project have a habit of being wrong in a
new way. Four sequences, all verified:

- **Cost per parcel** went $2.10 → $1.51 → $1.0875 — three corrections, each of
  which made the number *more* right
  ([`DECISION_LOG.md`](DECISION_LOG.md) §3.6) — `cost_report.json`
  (`run_id 20260916-064133-4d65`) reads **$1.0830**, and the current artefact
  `cost_by_station.json` (`run_id 20260916-131845-34f1`) reads **$1.1389** on a
  different and better depot layer. **Five published values, and the fifth is
  not a correction of the fourth** — it is a different model, and saying so is
  the whole point of §4.5.
  Note also that the first figure is itself a correction: the widely-quoted
  "$2.12" **appears nowhere in this repository**; reconstructed under the old
  depot proxy the median is **$2.1023**.
- **Portfolio activations** went 317 → 330 → 282, capital $1.268bn → $1.320bn →
  $1.128bn — and §3.5 above establishes that the three capital figures were one
  number restated.
- **`lift_by_market_size.json`** carries a `finding` field reading *"Pooled lift
  fell 3.68x->2.61x"* sitting beside its own fields reading 2.948 → 2.757. The
  numbers were recomputed; the prose next to them was not. That artefact is now
  formally retired, has **no emitter anywhere in the tree**, and cannot be
  regenerated — yet five sites still cite it
  ([`NUMBERS.md`](NUMBERS.md), "numbers that cannot be verified").
- **The "genuinely new facilities" count** moved twice — ten after five batches,
  thirteen after six, with an intermediate estimate computed against the wrong
  reference file — and **still cannot be reproduced from the tree**, because it
  is counted by hand into commit messages and emitted by no code
  ([`DECISION_LOG.md`](DECISION_LOG.md) §2.13).

**The two entanglement traps.** First, the two cost fixes are not separable:
$2.10 → $1.51 is the parcels/stops fix measured *under the old depot proxy*,
while against today's solved network the same fix is $1.5145 → $1.0875. Quoting
a single "improvement" for either fix alone is not well defined. Second, a
correction can be *right about the numbers and wrong about the verb*: `adr/0003`
originally said the fitted model was **"beaten"** by a raw covariate, and was
corrected to **"matched"**. The numbers never changed and were always correct —
8 of 38 at top-1 against 7, 20 against 19 — but from **one seeded split**. Over
fifty paired re-splits the raw count is ahead by **0.36 hits of 38** with a
paired sd of **1.14**, and it loses 11 of the 50. *"So this moved because the
claim was wrong — noise read as signal — not because the evidence moved on."*

**Why it was easy to get wrong.** A corrected document is one that has been
edited under time pressure by someone who already believed they knew the answer,
and who was concentrating on the part they were fixing. It also carries social
authority: a paragraph headed "Corrected 2026-09-14" reads as *more* reliable
than an uncorrected one, which is exactly backwards for anything in it other
than the specific clause that was corrected. The "beaten"/"matched" case is the
purest form — a one-word upgrade is the edit an author makes for readability, it
was in the document's favour, and the surrounding conclusion survived either
way, so nobody re-checked.

**What it cost.** [`CONTRIBUTING.md`](../CONTRIBUTING.md) records the durable
response, and it is a standing rule rather than a fix: *"Cite the artefact, not
the figure… Several published headlines have been invalidated by re-running the
code that produced them, and not one of those moves was caused by a parameter."*
[`NUMBERS.md`](NUMBERS.md) exists solely to be the tie-breaker, and its opening
line is the method: *"No markdown document was trusted as a source; the
documents are what this file exists to correct."*

**And a corollary, since it bit twice.** The register of open defects can also
drift *in the safe-looking direction*: §3.3 above documents a defect still listed
as open in `DECISION_LOG.md` whose three named documents have all since been
corrected. A stale "still broken" costs a reader just as much time as a stale
"fixed".

**Rule.** Check every figure against the artefact that emitted it and quote the
`run_id`. If a number is counted by hand, make code print it — every
hand-counted figure in this project's history has moved at least once, and one
of them still cannot be reproduced at all.

## 4.2 A stamp a payload can shadow is not an identity

**What happened.** `common/log_json.write_json` built its output as
`{"run_id": ..., "written_at": ..., **payload}`. Harmless — until an emitter
resumes from its own artefact. `covariate_harness.load()` reads the previous
`covariate_search.json` back in **whole**, stamps included, and hands it
straight to `write_json`. Because the payload was spread *last*, the old stamps
shadowed the fresh ones.

The consequence: **two materially different results shipped under one
`run_id`**, with `written_at` frozen at the first write. The artefact on disk
still shows the fingerprint — `run_id 20260915-235210-ff92`,
`written_at 2026-09-15T23:52:16Z`, and an mtime an hour and a half later.

The fix is four lines, `common/log_json.py:16-35`:

```python
def write_json(path: Path | str, payload: dict, *, indent: int = 2) -> Path:
    """Write a result artefact, stamped with the run that produced it."""
    ...
    # A stamp describes the WRITE, never the payload. Emitters that resume by
    # reading their own artefact back in (covariate_harness.load does exactly
    # this) carry the previous run's stamps inside `payload`; spreading it last
    # let them shadow the fresh ones, so a resumed run inherited the earlier
    # run's id AND its first-write timestamp, permanently. Two materially
    # different versions of covariate_search.json shipped under one stamp
    # before this was caught on 2026-09-15.
    stamps = ("run_id", "written_at")
    body = {
        "run_id": context.run_id(),
        "written_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **{k: v for k, v in payload.items() if k not in stamps},
    }
```

**Why it was easy to get wrong.** `{**defaults, **payload}` is the idiomatic
Python merge and the ordering is *deliberate* in every other use — you want the
caller's values to win. It is correct for every key except the ones the helper
itself owns. And the bug needs three things to line up that live in three
different files: a helper that spreads last, an emitter that resumes, and a
resume path that reads the whole artefact rather than a sub-key. Each is
reasonable alone.

**Note what created it.** The resume path was itself a fix, for the
checkpointing problem in §9.6. *The feature that prevented one class of data loss
created a provenance bug.* That is not an argument against checkpointing; it is
an argument for asking, of every resume path, what else comes back in with the
state.

**What it cost, and the residue.** The stamp of the project's most-cited
covariate artefact became useless as a version marker.
[`NUMBERS.md`](NUMBERS.md) still carries the workaround —
*"`run_id` cannot be used to tell two versions of this artefact apart. Check
`facilities` and the `stage_ledger` instead."* **No test locks the fix in**, and
[`NUMBERS.md`](NUMBERS.md) and [`EXPERIMENTS.md`](EXPERIMENTS.md) still describe
the defect as live, having been edited after the code was fixed — §4.1, again.

**A related and unfixed gap in the same area.** Nine of thirty artefacts in
`outputs/metrics/` carry **no `run_id` and no `written_at` at all**, backed only
by a file mtime: `panel_experiments.json`, `white_space.json`,
`national_panel_expanded.json`, `lift_by_market_size.json`,
`nlrb_coverage.json`, `nlrb_only_cities.json`, `batch_candidates.json`,
`catchment_band.json` and `highway_access.json`. The project's stated tie-break
rule — "where a `run_id` exists, the artefact wins" — therefore cannot be
applied to several of the most-quoted numbers.

**Rule.** Stamps describe the write, never the payload: write them last and
strip them from anything you read back in. If an emitter can resume from its own
output, assume it inherits its own identity until you have proved otherwise —
and lock the fix in with a test, because this is exactly the kind of correctness
property that silently regresses.

## 4.3 Record whether a stage ran or was carried forward

**What happened.** Once the covariate harness could resume, an artefact stopped
being the product of a single run. `covariate_harness.py:141-152` therefore
emits a per-stage ledger:

```python
def ledger(report: dict, ran: tuple[str, ...]) -> dict:
    """Which stages are in this artefact, and how they got there.

    `ran_this_invocation` is claimed only for the stages THIS call ran.
    An earlier ledger's claim is deliberately not carried over: a stage
    that ran an hour ago and was reused now is `carried_forward`, and
    saying otherwise would let an artefact assert it was regenerated when
    it was not -- which is the exact thing the ledger exists to prevent.
    """
```

and the module docstring states the condition under which reuse is legitimate:
*"A carried-forward stage is legitimate ONLY while the scientific code is
unchanged. Recording it is what makes that checkable, which is the whole reason
it is recorded rather than silently reused."*

**Why it matters, and why it is easy to skip.** The natural implementation of
resume is "if the key is present, skip the stage" — which is correct behaviour
and produces an artefact indistinguishable from a full run. The information that
is lost is not the *result*, it is the *warrant*: whether this number was
computed by the code currently on disk. Once a project has any resumable step,
its artefacts silently become mixtures, and there is no way to tell from the
outside.

This is also the practical replacement for the broken stamp in §4.2:
[`NUMBERS.md`](NUMBERS.md) tells readers to check `facilities` and the
`stage_ledger` precisely because the `run_id` cannot be trusted on that file.

**Rule.** Any pipeline with a resume path must record, per stage, whether it ran
or was reused, and must not let a previous run's claim carry forward. A
partially-regenerated artefact that cannot say which parts are fresh is not
reproducible, however honest its top-level stamp.

## 4.4 Generated duplicates rot, and the generator is the thing to delete

**What happened.** `scripts/build_docs.sh` rendered a plain-ASCII `.txt` twin of
every Markdown file in the repository, at 80 columns. Doubling the file count
meant every correction sweep had to touch two copies of each document — and
**five twins had drifted from their `.md` source, including two defence
documents a reader would have trusted** (`scripts/build_all.sh:45-53`).

They were deleted, and so were the generator and its renderer
`tools/docs/md_to_txt.py`, because *"leaving the generator in place means the
next `make docs` silently recreates all 113 of them"*
([`CONTRIBUTING.md`](../CONTRIBUTING.md)).

**That second half is the lesson.** Deleting the output of a generator you leave
callable buys you exactly one clean commit. The next `make docs` undoes it,
silently, with exit code 0.

**Why it was easy to get wrong in the first place.** The twins were a *good
idea*: a plain-text rendering is greppable, diffable and readable without a
renderer, and the script even failed loudly on non-ASCII. The failure mode is
not the format, it is the **unenforced invariant** — two files that must agree,
with nothing checking that they do. A generated artefact is safe when it is
regenerated in CI and diffed; it rots when regeneration is manual and
occasional, which is the default state of every docs generator ever written.

**Two residues, both of which are themselves lessons.** The figure **113**
appears in exactly two prose locations and nowhere else, while the working tree
shows **97** deleted `.txt` files, 93 of them with an `.md` sibling — a
hand-typed count, which is §4.1 again. And three documents still instruct a
reader to run the deleted script: `docs/README.md:180`,
`docs/adr/README.md:283`, `docs/engineering/README.md:166`.

**The same pattern, with the worst possible victim.** A hand-authored file
*outside* the generator is invisible precisely because everything else is
handled. `helper.txt` — the **spoken-answer crib sheet**, the document a
presenter reads last and then says out loud — had no `.md` twin, so the
generator never touched it and every correction sweep missed it. Its section
"NUMBERS TO KNOW COLD" instructed the presenter to assert
([`DECISION_LOG.md`](DECISION_LOG.md) §4.1):

```
   helper.txt says          the tree says
   -----------------------------------------------------------------
   5,200 ZCTAs              2,413
   811,200 panel rows       1,081,312
   52 billion MC draws      24.13 billion
   0.84 target AUC          0.6894 measured, and the result is NEGATIVE
```

The last line is not a stale figure. It is **a contradiction of the project's
headline finding, in the one document that gets read aloud.**

**Rule.** If two files must agree and one is generated, either remove the
duplicate or make CI diff them. Remove the generator in the same commit and grep
for callers. And enumerate the files your generator does *not* cover — that set
is small, invisible, and where the worst error will be.

## 4.5 Derive every headline figure — and know exactly what that discipline does not protect

**What happened.** The proposal claimed ~5,200 ZCTAs. The measured figure is
**2,413** (`outputs/metrics/scope.json`: `"zctas": 2413`,
`"definition": "OMB 2023 CBSA delineation"`, emitted by
`src/siting_atlas/report/scope.py`). The fix was structural rather than
editorial: `scope.json` exists so that no headline geography figure is ever
typed, and eleven current mentions of "5,200" survive across ten files, all
correctly retrospective.

**Be careful with the famous part of the story, because it is not checkable.**
The claim that the figure was "typed once and copied into nine places" is
*itself asserted* in `report/scope.py:5-8` and `tools/scope.py:15`, and the
proposal artefacts have since been regenerated — unzipping the deck and the
`.docx` today gives **zero** occurrences of 5,200 and six of 2,413.
*"The nine originals no longer exist to count."*

**That is itself the sharpest lesson here: fixing a defect destroys the evidence
for it.** If you want to be able to say how bad something was, count it before
you sweep.

**Why the structural fix was easy to over-trust.** Generated documentation
creates a *false sense of completeness*. Once nine of ten consumers are
generated, the tenth becomes invisible — not despite the discipline but because
of it. That tenth was `helper.txt` (§4.4), and it was the one that would have
been read aloud.

**Rule.** Derive every headline figure from an artefact at build time. Then
write down the list of consumers that are *not* generated, because that list is
where your remaining errors live — and record the size of a defect before you
fix it, or you will not be able to describe it afterwards.

---

# Part 5 — Checks that do not check

A guard that cannot fail is worse than no guard, because it consumes the
attention that would otherwise have gone to the problem. Each entry here is a
real check, written in good faith, that could not catch the thing it was
pointed at.

## 5.1 A check that reads the answer off the name cannot fail

**What happened.** `facility_type` was originally derived by a rule of the form
*"the building code starts with D, therefore delivery station."* Applied to 202
OSM candidates it produced 76 `DS` and 126 `FC`, and never errored.

[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) §11.2:
*"That rule is a **tautology, not a check.** It reads the type off the name and
then reports the name as evidence for the type. It cannot fail, which is
precisely why it tells you nothing."*

`DEN5` is the clean counter-example. It starts with `D`, so the rule calls it a
delivery station. It is a **sortation centre** — because `DEN` is Denver's
*airport* code and the `D` is doing no work at all. At least five D-prefixed
codes are mistyped this way; two are firmly established against independent
evidence (`DEN5` against an OSHA record at 19799 E 36th Dr, Aurora CO; `DWA6`
against a contractor page).

**The same trap ruins the geography.** Amazon names buildings after the nearest
airport, not the city they sit in (§11.1):

```
  OAK3  reads as Oakland    ->  is in Patterson, CA, ~70 mi inland
  OAK4  reads as Oakland    ->  is in Tracy, CA
  SMF5  reads as Sacramento ->  is in Vacaville, CA, its own MSA
```

None of those three is in the San Francisco Bay Area CBSA.

**Why it was easy to get wrong.** The identifier *does* encode the fact, most of
the time. The rule has high accuracy, produces a full column with no missing
values, and validates against your intuition every time you spot-check a
familiar code. It fails exactly where the encoding was never meant to carry the
meaning you are extracting — and those cases look identical to the ones that
work.

**The same shape, elsewhere.** The batch generator in §9.5 treated *"unclassified
by our regex"* as *"unknown to the project"*. Those are different sets and
nothing asserted they were the same.

**Rule.** If a validation rule cannot fail on your data, it is a restatement,
not a check. Test every derived field against an independent source, and
distrust any identifier that encodes the fact you are trying to measure.

## 5.2 A check that shares an assumption with the thing it checks is not a check

**What happened.** When this repository was made public, two files had to stop
being committable: a Good Jobs First Subsidy Tracker extract purchased under a
USD 25 subscription licence, and MWPVL International's industry PDFs, which are
third-party copyright. Both were protected by `.gitignore` rules — and the
project then wrote a second, independent check that **deliberately does not
consult `.gitignore` at all**. `scripts/export_public.sh:135-142`:

```bash
# ------------------------------------------- independent re-check, pass two
# Deliberately does NOT consult .gitignore. If the ignore rules are wrong, the
# first pass is wrong in the same way, and a check that shares an assumption
# with the thing it is checking is not a check.
section "safety re-check (does not trust .gitignore)"

for pat in ".env" ".venv" "subsidy_tracker" "mwpvl_2025q1" \
           "Distribution Network Strategy" ".coverage" "vnc_logs" "id_rsa" "*.pem"; do
```

The comment is the rule and it generalises well beyond publishing.

**The same principle, applied to credentials.** `.pre-commit-config.yaml:36-42`:

```yaml
  - repo: local
    hooks:
      # Gitignore is advisory: `git add -f` beats it. This does not.
      # See the module docstring - a live EIA key really did reach logs/.
      - id: no-secrets
        name: block run logs and live credentials
        entry: python scripts/check_no_secrets.py
```

and `scripts/check_no_secrets.py:12-21` runs three checks on the explicit ground
that *"each catches something the other two miss"* — a path check (because
gitignore is advisory), a **literal-value** check against every secret in
`.env` (because *"this is the only check that catches a bare key pasted into a
message with no `name=` around it, which is exactly how the leak looked"*), and
a pattern check for a key belonging to someone else's account.

**Why it was easy to get wrong.** The natural way to verify "is this file
excluded?" is to ask the exclusion mechanism. That check passes whenever the
mechanism *believes* it is excluding the file — which is the same condition
under which the mechanism is broken. It is a tautology dressed as a test, the
same shape as §5.1 one level up. See §8.1 for what nearly happened, and §8.3 for
the specific way the obvious verification command lies.

**Rule.** A verification pass must not share its premise with the thing it
verifies. Where the cost of being wrong is high, write a second check with a
different mechanism — enumerate the files and grep for forbidden patterns rather
than asking the tool whether it would have excluded them.

## 5.3 A green test suite is not a covered one — import every module

**What happened.** 660 tests collected, 658 passing, 2 xfail, 0 failures. Also
true, from the same measurement: **75 of 138 source modules are not imported by
any test**, directly or transitively — and **every artefact behind the headline
results is written by a module on that list**
([`NUMBERS.md`](NUMBERS.md) §12).

The sharp version appeared during the retirement of the hazard, gravity,
portfolio and agent lines of work to `experiments/`. Eleven test files moved out
alongside the code they protected, taking 138 tests with them. Moving code that
*other* modules still import breaks those modules at import time — and **no test
fails**, because the tests that would have imported them left in the same commit.

The guard that exists is `scripts/preflight_publish.sh:272-292`:

```bash
import importlib, os, sys
bad = []
for d, _, fs in os.walk('src/siting_atlas'):
    ...
            try:
                importlib.import_module(m)
            except Exception:
                bad.append(m)
sys.exit(1 if bad else 0)
```

failing with *"a module under src/ does not import — a retirement probably moved
its dependency"*, and printing the command to find the culprit.

**Why it was easy to get wrong.** Coverage tooling measures the lines your tests
execute, and a suite that never imports a module reports nothing about it at all
— it does not show as 0% coverage, it shows as absent. "658 passing" is the
number that gets quoted, and it is a statement about the tests that exist, not
about the code. The retirement made it worse in the one way nobody watches for:
the test count *went down* (798 → 660) and the suite *stayed green*, which reads
as a clean removal.

**Still a gap.** The importlib walk is a **publish gate, not a test**. CI checks
only `import siting_atlas` plus a hand-maintained list of stage entry points, so
the walk runs only when someone remembers to run `preflight_publish.sh`.

**Rule.** Add an import-everything check and run it in CI, not just before
publishing. "The suite is green" and "the code imports" are different claims, and
a large refactor can satisfy the first while breaking the second. Quote
`N modules unreachable from any test` next to your pass count, always.

## 5.4 A helper that resolves ambiguity by size will validate the wrong file the day another file grows

**What happened.** `ingest/external.py:_find()` returns the **largest** file
matching a pattern. That is a deliberate and defensible rule: an interrupted
download leaving a short truncated file beside a good one should not win.

Under a bare `*.csv` glob, the moment `national_facilities.csv` outgrew
`facilities.csv`, the `--check` command **issued a clean bill of health for a
file nothing in `src/` reads**, while the actual model input went unvalidated.
`facilities.csv` is 43 rows / 4,778 bytes; `national_facilities.csv` is 104 rows
/ 17,497 bytes, and *"it grew from 70 rows to 104 during the afternoon of
2026-09-13"* ([`DECISION_LOG.md`](DECISION_LOG.md) §2.9).

**Why it was easy to get wrong.** The largest-wins rule was **good engineering
solving a different problem**. Two decisions, each correct in isolation — prefer
the larger file; accept a permissive `*.csv` glob — compose into a silent
validator bypass. And a validator that *passes* is the single output nobody ever
investigates.

**Fixed.** An ordered pattern tuple, `("facilities.csv", "*.csv")`, with `_find`
returning on the first pattern that has any hits
(`external.py:57-67`). **Residual risk, named in the document:** the `*.csv`
fallback is still in the tuple, so renaming or deleting `facilities.csv` brings
the bug back silently.

**Rule.** A resolution rule for ambiguity is a policy, and policies compose
badly. Make the selector *ordered and explicit* rather than *derived from a
property of the file*, and have the check print which file it validated — the
one-line change that would have caught this in seconds.

## 5.5 A guard whose threshold comes from an unreliable field has no margin

**What happened.** An Amazon delivery station **is** a warehousing
establishment, so a contemporaneous count of warehousing establishments in a ZIP
contains its own outcome. `ingest/cbp_detail.py` installs a vintage lag against
exactly that: each facility is scored on the latest CBP vintage **strictly
earlier than its recorded `open_year`**. Correct in design, documented, tested.

It fails one level down. On all 100 loaded national rows, `open_year` equals the
quarter of the **earliest OSHA inspection** — it is not an opening date, it is
the "operating by" upper bound, restated. A building first inspected in 2022 may
have opened in 2017, in which case the "strictly earlier" 2021 vintage already
counts the facility itself. The five pilot addresses with an independently known
opening month give lags of **4, 13, 57, 69 and 345 months**
(`adr/0004`): *"three of the five exceed twelve months, so on the only evidence
available the guard is defeated more often than it holds. Its margin is zero or
negative, not a year."*

**Why it was easy to get wrong.** The guard is *visibly* a leakage guard. It is
named as one, documented as one, and reads as diligence. The flaw is in the
semantics of its input: the column is called `open_year`, so everything
downstream treats it as an opening year, because that is what it is called. The
gap between a column's **name** and its **meaning** does not appear in any
schema, contract or test.

**What it cost, and an unusually direct retraction.** `adr/0004` withdraws its
own sentence. The claim that the upper-bound date *"stops being a defect and
becomes a conditioning variable"* is now recorded as ***"the least defensible
sentence in the document. The date did not stop being a defect; it moved into the
covariate."***

**Partly tested, at a price.** `leakage_decisive.json`
(`run_id 20260916-071556-3d83`) runs three arms over 50 paired re-splits on the
**same 29 decisions**: forced onto a CBP vintage strictly earlier than MWPVL's
*stated* opening rather than the OSHA bound, the covariate retains
**3.74 / 4.76 = 79%** of its value and beats the no-covariate floor 50 of 50.
But reaching those 29 cost **65 of the 94 working decisions (69%)**, the test
set is 12 decisions, and — the limitation that matters — *the leak and the
staleness are one intervention*: `true_date` reads a vintage that is older **as
well as** cleaner, so the measured gap is an **upper bound** on the leak, not a
measurement of it ([`EXPERIMENTS.md`](EXPERIMENTS.md) §9).

**Rule.** When a guard has a threshold, ask where the threshold's *value* comes
from and what its semantics actually are. A column named `open_year` that holds
an upper bound gives you a guard with a margin of zero — and it will still read,
to every reviewer, as a guard.

## 5.6 A guard can be written for exactly the right defect and still sit in its blind spot

**What happened.** `tools/ocr/grid_ocr.py` carries a settings guard whose
docstring names precisely the failure it exists to prevent: *"the directory
silently becomes a blend of two extractions that no downstream consumer can tell
apart. The row counts would look fine."* It writes a `SETTINGS.json` on first
use and raises on mismatch.

The delivery-station table — the one supplying the rows that became most of the
expanded panel — was OCR'd by a run whose log does not exist, and
`data/raw/mwpvl/tsv/SETTINGS.json` has an mtime **after** those files were
written ([`AUDIT_2026_09_14.md`](AUDIT_2026_09_14.md) §1.3). The guard had
nothing to compare them against. *"The defect the guard was written to catch is
the defect that occurred, in the guard's blind spot."*

**Why it was easy to get wrong.** A first-use guard is empty on first use. That
is not a bug in the guard; it is the unavoidable shape of "record the settings
the first time, then compare." The window in which it cannot protect you is
exactly the window in which the most important run happens, because the most
important run is usually the first one.

**Rule.** For any guard that establishes a baseline on first use, ask what
happens during the run that creates the baseline — and write the settings file
*before* the work rather than after it, so a run that predates the record is
distinguishable from a run that matches it.

---

# Part 6 — Methods and claims that always return an answer

## 6.1 A method that answers every question is not thereby a good method

**Two instances, and the second is the one that nearly shipped.**

### Satellite dating: 107 of 107, falsified on 36%

A Sentinel-2 changepoint pipeline was built to recover true opening dates,
because the CBP lag guard (§5.5) could not be defended without them. It returned
an estimate for **107 of 107** sites, from a median of 106 cloud-free scenes
each. The validation looked survivable
([`DECISION_LOG.md`](DECISION_LOG.md) §2.14):

```
  sites with a known year                        83
  estimates within 1 year                       41%
  error standard deviation                  3.42 years
```

The **logical** test condemned it:

```
  estimates dating CONSTRUCTION AFTER the day an OSHA inspector
    recorded the building as already operating      39 of 107 = 36%
  median lateness of those                          33 months
  impossible rate at confidence > 2                 35%
  impossible rate at confidence 1-2                 30%
```

An estimate that post-dates the proof of operation is not imprecise, it is
**impossible**. And the confidence score does not separate the two populations —
35% impossible above confidence 2 against 30% below — so there is no threshold
that rescues the rest. The cause is structural, not a tuning problem:
*"It cannot return 'no change'. Any series of 12 or more points returns a date."*

**The trap it nearly walked into.** 68 estimates survive the logical test, and
68 dates is a tempting deliverable. *"They are not dates. They are the subset of
a method that fails a third of the time which happened not to fail visibly, and
selecting on a test the method fails at random is exactly how a project ends up
publishing noise."*

### Language-model date lookup: 33 of 35 fabricated, and not one gap

An earlier attempt asked a model with web search when each facility opened. It
**fabricated 33 of 35 dates**, every row citing the same URL, which supported
none of them. Two independent checks caught it: a **planted known answer**
(Chicago 60628 opened Oct 2020, per a chicago.gov press release; the model
returned 2024 Q3) and a second source on a different facility. A later, more
careful attempt produced *"roughly 60 queries produced 4 dates, of which one was
a genuine opening date"* — the rest were announcements, lease signings or
construction milestones.

The transferable observation is
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) §3.3,
and it is the single most portable sentence in this repository:

> *"The failure was not 'the model was wrong sometimes'. It was that the output
> was **uniformly plausible**: 35 rows, every one with a year, a quarter and a
> URL, no hedging, no gaps. **A dataset with no missing values, produced by a
> process that should have produced many, is evidence of fabrication rather than
> of diligence.**"*

**The contrast that explains it.** The same tool *succeeded* at a different task
— classifying what kind of building sits at an address — and §5.1 of the same
document explains why the difference is not about the model:

```
  ASKED:  "When did the Amazon facility in Kent WA open?"
  GIVEN:  a city name.
  TRUTH:  exists in maybe one local news story, maybe nowhere.
  RESULT: fabrication, because the model has nothing to ground on.

  ASKED:  "What kind of facility is 20202 84th Ave S, Kent WA 98032?"
  GIVEN:  a real street address, from a federal record.
  TRUTH:  leasing listings, DSP directories, planning agendas, job
          adverts and square-footage figures all name the address.
  RESULT: a verifiable answer with a quotable sentence.
```

*"The address is the difference. A federal citation hands the model a key that
the open web is actually indexed on. 'When did it open' has no such key."*

**Why both were easy to get wrong.** A complete output column reads as success.
Missingness is the thing everyone is trained to treat as a defect, so a method
that produces none clears the check that would have caught it. And both methods
supplied their own quality signal — a confidence score, a citation URL — which
made the output look self-auditing while being uninformative about exactly the
failure mode that mattered.

**Rule.** Build a falsification test that is **logically independent of the
method's own error model**, and apply it before you look at accuracy.
"Impossible given something else I already know" beats "accurate on the subset I
can check." And treat a 100% answer rate on a question the world does not always
answer as a red flag, not a feature.

## 6.2 Cite what you read — and grade every citation

**What happened.** `cost/params.py:38` sets `bhh_constant = 0.57`, the constant
carrying the entire cost-to-serve branch. Its source comment cited Daganzo
(1984) and a companion paper by DOI. Both citations were defective:

1. **Nobody had opened the paper.**
   [`research/NOTES_daganzo_1984.md`](research/NOTES_daganzo_1984.md) opens:
   *"THE PAPER WAS NOT READ. IT IS NOT ON DISK… nothing below is a report of
   what Daganzo (1984) says."*
2. **One of the two citations is a different author entirely.** DOI
   `10.1287/trsc.18.3.231` belongs to R. J. Vaughan, pp. 231–244, on average
   distances between random points in zones — not tour lengths, not constants,
   not Daganzo. Verified against OpenAlex twice.

**The response was disclosure rather than a quiet edit.**
`paper/siting_atlas_ieee.tex:185-196` says so in the methods section, and a
subsection titled "The cost model's central constant is undefended" records that
of the four sources offered for 0.57, *"one is a different author's paper about
a different quantity, one is real but unread, and two state a value 31–34%
higher."*

**The general scale of the problem.** [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md)
§10 is a corrections log of claims that did not survive opening the source — 22
rows — and its framing sentence is the reason it exists: ***"a research log that
only records the claims that worked is a marketing document."*** The failure
taxonomy is more useful than any individual row:

1. **Right content, wrong section.** *"Train §7.7.2: define as few time periods
   as possible"* — content exact, it is **§7.7.3**. Same for Houde et al. §3.5,
   where the estimator is actually §4.3.
2. **A quantifier silently strengthened.** "BLP fails when **many** alternatives
   have zero share" — Train's condition is *"if observed shares for **some**
   products in **some** markets are zero. No threshold, no count."*
3. **"Presents" upgraded to "recommends."** Two methods described as
   *recommended* by Train are *"presented with balanced pros and cons."*
4. **The pessimistic of two numbers quoted as the number.** A "~10%" efficiency
   figure is in §11.4 not §11.3, *"and it is the pessimistic of two metrics —
   the same table gives **40%** on the other, which is Train's own headline
   reading."*
5. **A contrast attributed to an author who never drew it.** *"Train never says
   'known universe' and never contrasts it with an unknown choice set. Do not
   attribute that contrast to him."*
6. **A word added that carries technical weight.** "The posterior mean is a
   **precision-weighted** average" — the maths is right, but *"the word
   'precision' appears nowhere in chapters 1-14 or the index."*
7. **Citing a paper for something it does not contain.** Of Winkler:
   *"the word 'block' appears zero times in the paper"*; the Fellegi–Sunter
   optimality theorem is not there either; *"the paper contains three numbers in
   total."*
8. **Right verdict, wrong argument** — the most seductive. AUC was said to
   "inherit the defect" of percent-correctly-predicted. *"It does not inherit
   that defect… Same conclusion, different argument."*
9. **The correction itself needed correcting.** "AUC never thresholds" was the
   *fix* applied in an earlier pass, and §10 later overturns it: *"AUC is the
   integral of the ROC curve **over** all thresholds. It never commits to
   **one** threshold, which is a different and weaker statement."*
10. **Our own arithmetic, unchecked.** "Our panel has ~80 quarters" → **32**.
    "One station switches ~90 ZIPs" → 90 is the *mean* (87.6); median 58, range
    4 to 307. *"The argument survives; the number should be stated as a
    distribution."*

**The largest single instance, and it propagated to six documents.** The claim
that *Train §2.2, mutual exclusivity, is the assumption the hazard model broke*
is wrong — §2.2 governs a choice set facing a decision maker, which a cloglog
hazard on ZCTA-quarters does not have, and Train calls the criterion *"not
restrictive"* (p. 12) while supplying a two-line repair recipe. The assumption
actually violated is §3.7.1, p. 61, independence across observations.

**Why this class is so dangerous:** *the conclusion was right*. The model really
was invalid, so no downstream number moved, so nothing failed — and an examiner
opening the book finds the project's central methodological claim citing a
section that says roughly the opposite of what is attributed to it.

**Why it was easy to get wrong.** Every one of these was written by someone who
had genuinely read the material and remembered the **content** correctly. Memory
reliably preserves an argument and loses the locator. There is no test, no
linter and no reviewer in a normal workflow that checks a section number, and
the cost of being wrong is asymmetric and delayed: zero today, credibility-fatal
in front of someone holding the book.

**The durable fix is cheap and worth copying wholesale.**
[`REFERENCES.md`](REFERENCES.md) grades every entry:

```
  [V]  read in full
  [T]  title and venue checked
  [K]  from memory, verify before use
```

and the codebase uses a fourth grade in prose — `choice_sandwich.py` names
Andrews (1999) *"as a lead to follow rather than as support"*. A citation you
cannot defend is not deleted, it is **downgraded**, which keeps the lead without
the claim.

**Rule.** A citation is a claim you are making, not decoration. If a constant is
load-bearing, read the source or mark the citation a lead. Grade every reference
by how thoroughly you actually checked it, and when you find one you cannot
defend, disclose it where the number is used — a reader who finds it themselves
will discount everything else you wrote.

## 6.3 A scoring rule can be proper while its skill score is improper

**What happened.** The project switched to the Brier **skill** score, believing
it was the proper rule that fixed AUC's problems. Reading Gneiting & Raftery
(2007) cover to cover overturned three claims at once
([`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §10, §12.4):

- §2.3, p. 362: *"skill scores of the form (8) are generally improper, even if
  the underlying scoring rule S is proper."* Murphy (1973) gives only
  *asymptotic* propriety, and Mason (2004)'s propriety claim is named **in the
  paper itself** as "generally incorrect." The **Brier score** is strictly
  proper (Example 1, p. 363); the **skill score** is a normalisation of it, and
  the normalisation is what destroys the property.
- *"Gneiting & Raftery is the citation against AUC"* — **they never mention AUC
  or ROC.** Zero occurrences in twenty pages. Propriety is *undefined* for AUC
  rather than violated: a scoring rule in their sense is `S(P,x)` on one
  forecast–observation pair, and AUC is a rank statistic over *pairs of cases*,
  which cannot be written in that form. *"Do not write 'Gneiting and Raftery
  show AUC is improper'."*
- *"They give the reliability–resolution–uncertainty decomposition"* — they do
  not; they give the **Savage/Bregman** decomposition, eq. (7), p. 361.
  *"Murphy's vector-partition paper is not even in their reference list."*

**Why it was easy to get wrong.** "Brier skill score" contains the words "Brier"
and "score"; the underlying rule genuinely is proper; and normalising against a
baseline is universally treated as a harmless readability improvement — it makes
a number with an unintuitive scale into a percentage. Nothing about the operation
looks like it could change a mathematical property.

**Fixed**, and the prereg locked it in advance:
*"reporting — raw Brier and top-k against a uniform null, never a skill score
(Gneiting & Raftery 2007 sec. 2.3, p.362: skill scores are improper)."* Two
traps documented alongside: at a 2% event rate, predicting 0.02 for everybody
scores 0.0196, *"so differences must be read against the base-rate Brier and not
against zero"*; and Brier **cannot rank the panel arms**, because it averages
over alternative rows whose denominators run 11,715 to 86,682.

**Still open**, and named as *"the cheapest win outstanding"*: Winkler's
standardised score is proper, built for rare events, and computable from
`outputs/tables/hazard_predictions.parquet` **without refitting**. Identified,
not implemented.

**Rule.** Propriety is a property of a scoring rule, not of the quantity inside
it. Normalising, rescaling or differencing a proper score can destroy it. And
check whether the paper you are citing against a metric ever mentions that
metric.

## 6.4 A figure must not contain a number that was never computed

**What happened.** The self-audit found `fig05_decay` in the proposal figure
set: a cannibalisation decay curve with **nine hand-typed effect values**, a
shaded band labelled **"95% CI"**, and one point annotated **"n.s."** The
deleted code is quoted at [`data/FIGURES.md`](data/FIGURES.md):

```python
eff = np.array([-12.1, -9.4, -6.2, -4.1, -2.3, -0.9, -0.4, -0.2, 0.1])
lo  = eff - np.array([2.2, 2.0, 1.9, 1.8, 1.7, 1.7, 1.6, 1.6, 1.6])
...
ax.fill_between(d, lo, hi, ..., label="95% CI")
```

No such regression had ever been run. Worse, the y-axis was **2-day order
volume** — a quantity this project does not observe, and whose absence is the
documented reason the cannibalisation estimand was abandoned (ADR-0001). So the
figure asserted a causal effect, a confidence interval and a significance test,
on a variable that is not in the data.

**Why it was easy to get wrong, in the figure author's own words.** The docstring
now at `tools/figures/fig_methods.py:69-92` is the best statement of it:

```
    This figure used to plot nine hand-typed effect values with a band
    labelled "95% CI" and a point annotated "n.s.". No such regression has
    ever been run. ...

    So the figure asserted a causal effect, a confidence interval and a
    significance test, all on a variable that is not in the data. The caption
    said "values are illustrative pending estimation", which is six words
    under a chart carrying error bars -- and figures are routinely lifted into
    slides without their captions.
```

The disclosure **existed**. It was in the caption, it was honest, and it was
useless, because a figure and its caption are separable and a figure travels.
That is the generalisable half: an uncertainty band is a strong visual claim
that overrides six words of prose, and the moment the image is cropped into a
deck the prose is gone.

**Be precise about the remedy**, because the tempting summary is not what
happened. Only **4 of 14** figures in that set read a measured artefact —
`fig08`/`fig09` load `outputs/metrics/hazard_report.json` at build time via
`tools/hazard_metrics.py`, where "nothing is typed."

`fig05` **could not be wired to anything**, because the quantity does not exist.
So it was **de-quantified** instead: the interval and the significance
annotation removed, the curve dashed and explicitly labelled *"shape a decay
curve takes (not estimated)"*, `set_yticklabels([])` — *"no numbers: none of
them are measured"* — and the words `ILLUSTRATIVE ONLY -- NO REGRESSION HAS BEEN
RUN` placed **inside the axes**, *"where they travel with the image."*

**The second figure, which was worse and had no disclosure at all.**
`fig07_tornado` hard-codes eight bucket swings; its caption asserted "four
primary buckets account for roughly three-quarters of the swing in net present
value" as measured fact, and *"until 2026-09-15 it said so nowhere — not in the
figure, not in the caption."* It cannot be rebuilt from data, because
`montecarlo_report.json` carries aggregate bands only and no per-bucket
decomposition. It too was de-quantified: per-bar dollar labels removed —
*"they were false precision on invented numbers"* — x-tick labels blanked, and
the **ordering** presented as the claim rather than the magnitudes, which is
defensible from the cost model's structure.

**A postscript that is §4.1 again.** [`data/FIGURES.md`](data/FIGURES.md) still
describes the invented interval as currently committed. It is dated 2026-09-15
and both figures were corrected the same day; the document did not follow.

**Rule.** Either a figure's values come from an artefact at build time, or the
figure carries no numbers and says so **inside the frame**. The intermediate
state — hand-typed values drawn with the visual grammar of a measurement — is
the failure mode, and the uncertainty band is the element that turns a sketch
into a fabrication. A caption is not a mitigation, because captions do not
travel.

---

## 6.5 A test can stop being identified because your model got better

**What happened.** For most of this project's life the cost model's headline
secondary finding was a clean, memorable statistic: *"of 43 facilities ranked
by cost-to-serve within their own metro, **zero** sit in their metro's cheapest
decile."* It appeared in the README, the paper's abstract, the paper's
conclusion, the explainer, the alternatives document and the numbers document.
It was re-derived from an artefact every time it was quoted. It was not wrong.

Then the depot layer was rebuilt on the operator's 501 real geocoded delivery
stations instead of a solved 334-site p-median (§3.5). **The statistic did not
change value — it stopped being a statistic.**

```
  decile_test, cost_by_station.json, run 20260916-131845-34f1

  arm            facility set        in cheapest decile   median rank   haul
  as_costed      501 stations (476)   275  57.8%             0.080      2.1 mi
  as_costed      43 pilot facilities   26  60.5%             0.074      1.9 mi
  leave_one_out  501 stations (476)    33   6.9%             0.642     10.4 mi
  leave_one_out  43 pilot facilities    7  16.3%             0.333      6.8 mi

  chance rate under uniform placement: 10%
```

**Why.** Once the depots ARE the facilities, a ZCTA that contains a station has
a line haul of roughly zero **because the station is inside it**. Line haul
enters the cost identity as `2L/C` per stop, and drive plus distance is 18.6% of
the bill, so the model now makes every facility's own ZCTA cheap **by
construction**. Ranking facilities on that surface measures the circularity, not
the siting: the finding inverts from 0% to 57.8% and it means nothing either
time. *The improvement to the model is precisely what destroyed the test.* The
test was identified only while the depot layer was wrong in a way that happened
to be independent of where facilities are.

**And the repair does not rescue it.** The obvious counterfactual is
leave-one-out: re-price every ZCTA against the nearest station *outside* it, and
ask how expensive this place would be if the operator had not built here. Run
it, and the 501 stations give **6.9%** — under-represented against chance, the
direction the old claim wanted — while the original 43 give **16.3%**,
over-represented, the opposite sign. Same frame, same mask, same run. The mask
under-corrects in dense metros, where a masked station's neighbour is two miles
away, and the two facility sets differ in exactly how dense their metros are
(median masked haul 6.8 mi against 10.4 mi). **A statistic whose sign depends on
which set you draw the counterfactual over is not evidence for either sign.**

**What we did.** Withdrew it everywhere, and kept the conclusion by re-sourcing
it. *Feasibility binds before economics* is a claim about the cost function and
the land market: cost falls as `1/√δ`, so the cheapest places to serve are the
densest, and the densest are where a warehouse cannot be built. That argument
needs the Daganzo form and the observation that a raw warehouse count is the
only covariate that predicts siting — it never needed a decile count. Removing
the number cost the sentence nothing except its air of measurement, which it
was not entitled to.

**Why it was easy to get wrong**, and this is the transferable part. Nothing in
the usual defences catches this. The statistic was derived from an artefact, not
typed into prose. It was recomputed on every run. It had a test. It had a
chance-rate comparison. Every discipline this project adopted after its earlier
failures was satisfied — because all of those disciplines check whether the
number is *computed correctly*, and none of them checks whether the number is
*identified*. Identification is a property of the relationship between your
estimand and your data-generating process, and it can be silently destroyed by a
change that improves the model in every other respect.

**Rule.** When you change a model's structure, do not only re-run its numbers —
**re-ask what each number identifies.** For every claim of the form "X is
unusually high/low relative to a reference set", write down the counterfactual
explicitly ("how expensive would this place be if the facility were not here?")
and check that the new model still lets you construct it. If the improved model
makes the treated units special *by construction*, the comparison is gone, and a
leave-one-out patch is a hypothesis to be tested, not a fix to be applied:
report every arm of it, and if the arms disagree in sign, withdraw the claim
rather than picking one. **A test that becomes unidentified when the model
improves is itself a finding — record it, because the alternative is that
someone reinstates the statistic the next time it reads well.**

*(§3.5 is the change that caused this; `NUMBERS.md` §10.4 is the canonical
record of the withdrawal; `EXPERIMENTS.md` E17 is the run.)*

---

# Part 7 — Data that lies quietly

## 7.1 A geography can change underneath a join, and a LEFT JOIN reports the loss as NULL

**What happened.** Connecticut abolished its eight counties as statistical
geographies in 2022 and replaced them with **nine planning regions carrying new
county-equivalent FIPS codes** (09110–09190). This project pins ZCTA geography
at 2020, so its crosswalk carries 09001–09015, while EJScreen 2024 tract GEOIDs
carry the new codes. The county-grain join at `warehouse/optional.py:70` matched
**nothing** for every Connecticut ZCTA:

```
  CT ZCTAs                                     288
  ... with pm25, diesel_pm, traffic_proximity,
      low_income_pct, people_of_colour_pct       0
  cells lost                  288 x 5 x 32 = 46,080
```

***"Nobody noticed because the loss is 0.9% of panel rows and the coverage
report shows it as a national percentage."***

**Why it was easy to get wrong.** Nothing in the pipeline failed, and nothing
*should* have: a `LEFT JOIN` onto a dense spine is *designed* to return NULL for
unmatched keys — that is the reason you choose it. The FIPS codes are still
5-digit and still parse. The loss is a rounding error nationally. And the root
cause is a real-world administrative change in one state, which no code review
anticipates and no schema encodes.

**A second-order finding that inverts a natural assumption.** The resulting
missingness runs **the opposite way** to every other gap in the project. Where
environmental and energy columns are missing, household density is **7.3× to
12× denser** than where present — because the cause is not a density mechanism
at all, but two clean coverage rules (EIA publishes no territory series;
EJScreen 2024 drops AK/HI on some indicators) plus this bug. "Missing means
rural" is wrong here, and would have been the natural reading.

**The fix is a model of how to do it**, and every element is transferable:

- **A second key, not an edited one.** `dim_zcta` now carries both
  `county_geoid` (2020, byte-identical) and `county_geoid_2022`. Additive,
  therefore reversible.
- **The bridge runs at ZCTA grain, not county grain**, because **planning
  regions do not nest inside legacy counties** — both are unions of towns,
  cutting across each other. Litchfield County alone splits three ways, so a
  county→region crosswalk would be wrong for 11 of 288 ZCTAs.
- **The mapping comes from data already on disk, not from memory.** CBP 2022 is
  published on the new geography and names the planning region per ZIP, placing
  **283 of 288**. The remaining 5 take the modal region of their legacy county
  among the 283 — *"a rule computed from the data, not typed from memory"* — and
  are marked `region_source = 'modal'` so the two kinds never blur.
- **Rejected alternatives are recorded**: remapping `county_geoid` itself
  (changes a key three layers trust, and flips CT's permit coverage from
  2018-2021 to 2023-2025 *as a side effect*); rolling EJScreen up to state for
  CT (*"one value for 288 ZCTAs, which looks like data and is not"*).
- Guarded by ten tests including
  `test_no_state_loses_ejscreen_to_a_key_mismatch`.

**Still broken, and reported rather than fixed:** the same vintage mismatch
leaves all 288 CT ZCTAs with `cbsa_code` NULL, hence NULL on all five BLS wage
columns and `metro_employment`.

**Rule.** Every join on an administrative code needs a per-stratum match-rate
check, not a national one — a state-sized hole is a rounding error at national
scale. And when you fix a geography mismatch, add a second key rather than
editing the first, bridge at the finest grain available, and derive the mapping
from data you already hold.

## 7.2 County values wearing ZCTA column names, and standard errors wrong by sqrt(10.5)

**What happened.** `warehouse/optional.py` rolls EJScreen tracts up to counties
— population-weighted, with a good comment explaining why — and then joins
county to ZCTA. The resulting panel columns look like ZCTA measurements and are
not:

```
  column                    source grain    distinct values   ZCTAs   ZCTAs/value
  pm25                      EJScreen tract           3,082   33,012      10.7
  low_income_pct            EJScreen tract           3,195   33,486      10.5
  permit_units_total        BPS county               2,639   32,965      12.5
  electricity_cents_kwh     EIA state                1,279   33,642      26.3
  wage_light_truck_driver   BLS OES CBSA               349   18,475      52.9
```

[`data/DATA_QUALITY.md`](data/DATA_QUALITY.md): *"86,082 tracts were read to
produce 3,195 numbers. A ZCTA-level model regressing anything on `pm25` is
really regressing on a county fixed effect with 3,195 levels, and its standard
errors — computed as if there were 33,012 independent observations — are wrong
by roughly sqrt(10.5)."* Fifty-three ZCTAs share each wage value.

**Why it was easy to get wrong, and this is the sharp part:** ***"The code knows
this. The comment at `optional.py:63-66` states it plainly. What is missing is
any trace of it in the data"*** — no `_grain` suffix, no companion column
recording the source geography, nothing that would stop a reader of
`panel.parquet` treating `pm25` as a ZCTA measurement. **A comment in the module
that produced a column does not travel with the column.** A parquet file has no
comments, and the person who writes the join is almost never the person who
writes the regression.

**The same shape, on time.** Every row labelled `2018Q1` asserts May-2025 metro
wages, 2024 environmental indicators, 2019–2023 pooled ACS, 2022 business counts
and 2020 boundaries as contemporaneous facts — *"the spread between the earliest
and latest vintage inside a single row is seven years."* Of 35 numeric panel
columns, **26 are identical in all 32 quarters**: 1,081,312 nominal rows against
33,791 independent draws, a **32× inflation**. Two named hazards: the BLS wages
parquet **has no year column at all** (the vintage exists only in the source
ZIP's filename — *"If `oesm24ma.zip` were dropped in tomorrow, nothing in the
pipeline would notice"*), and any backtest training through 2023 and predicting
2024–25 has *"look-ahead leakage in the strict sense… probably small, but it is
unmeasured and it is structural, not accidental."*

**And the diagnostic gap.** Every unmatched-join rate in the project was
computed **by hand, for the audit**. The worst is BLS OES: **540 of 928 CBSAs
unmatched (58.19%)**, producing 45.33% missingness on five wage columns, missing
exactly where it correlates with size (a **14× density gap** between the present
and missing strata). *"The finding is not any individual rate. It is that none
of these numbers is computed by the pipeline."* The panel report emits percent
non-null per column — the **symptom** — so "45% of wages are missing" cannot be
traced back to "OES covers 388 of our 928 CBSAs" without an audit.

**Not fixed.** All three are in the cleaning changelog's "still open."

**Rule.** Carry grain in the data, not in a comment: suffix the column, or ship a
companion column naming the source geography and vintage. Emit unmatched-join
rates per source from the pipeline itself — a coverage percentage is a symptom,
and a join rate is a cause.

## 7.3 Filtering on data availability can be selection on the outcome's main driver

**What happened.** Panel membership comes from the OMB delineation, not from
Zillow rent coverage — a decision taken deliberately
([`DECISION_LOG.md`](DECISION_LOG.md) §1.3). Had it gone the other way: Zillow
covers 36.0% of pilot ZCTAs (869 of 2,413), and *"the ZCTAs Zillow does not
cover are **seven times smaller** than the ones it does."*

The worked example in the log is the clearest statement of the trap I have seen
anywhere:

> *"Suppose Amazon is less likely to serve small ZIPs. Drop every ZIP without a
> rent series and you have dropped mostly small ZIPs, so the remaining sample
> looks like Amazon serves nearly everywhere, and the model learns that
> population does not matter — **because you removed the variation.**"*

**Why it was easy to get wrong.** Dropping rows with missing data is the single
most routine operation in applied work. It is the default in most estimators. It
never errors, it makes every subsequent step simpler, and the resulting sample
is *cleaner on every metric you would check*. The damage is invisible because
the thing you destroyed — variation in the outcome's driver — is not something a
completeness report measures.

**And it recurred, in the place nobody looked.**
[`DECISION_LOG.md`](DECISION_LOG.md) §4.4: *"rent is missing for 94.3% of ZCTAs,
the ZCTAs where it is observed are **64× denser**, and `cost/runner.py:166`
drops every incomplete row. That is listwise deletion under non-random
missingness… **The same mechanism had already been caught once, in the Zillow
metro filter — and nobody thought to look for it elsewhere, because there was no
checklist to look against.**"*

That sentence is the whole argument for §9.7.

**A live residue.** The stale figures 35% / 4,731 / 30,589 are still quoted in
`common/metros.py`, `ingest/registry.py` and `docs/data/cbsa_county.md`; the
measured values are 36.0% / 4,450 / 30,625.

**Rule.** Before dropping incomplete rows, compare the dropped and kept strata on
the variable your outcome most depends on, and report the ratio. If they differ
by more than a factor of two you are selecting, not cleaning. Then grep your
codebase for every other `dropna` and do it again — this class of error recurs
because it is invisible one site at a time.

## 7.4 When two sources contradict and nothing ranks them, the honest output is NaN

**What happened.** The record linker over `national_facilities.csv` returns three
matches at score **1.000** with zero false positives — and the paired rows
**disagree about the opening date** by 10, 6 and 3 quarters:

```
  NAT-0011 / NAT-0012  '2815 W EL SEGUNDO BL' HAWTHORNE CA
                       '2815 W. EL SEGUNDO BLVD.' HOLLYGLEN CA
                       open 2020 Q2  vs  2017 Q4
  NAT-0025 / NAT-0026  TRACY CA 95304       2025 Q1  vs  2026 Q3
  NAT-0078 / NAT-0079  PORTLAND OR 97210    2017 Q4  vs  2018 Q3
```

*"A duplicate row you can delete. A contradicted date you have to
**adjudicate**, and nobody has."*

**The silent resolution was the dangerous part.** `enabled_flags`
(`facilities.py:206-210`) takes `min(open_q_index)` across every facility whose
catchment covers a ZCTA, so **the earlier of the two dates always wins**. For the
Hawthorne pair that switches a fifteen-mile Los Angeles catchment on **ten
quarters early** — and the contradicted attribute is the one the entire siting
model exists to explain.

**Why it was easy to get wrong.** `min()` is the natural aggregator for "when was
this first enabled", it never errors, it always returns a value, and it is
*correct* whenever the inputs agree. The three pairs differ only by abbreviation
(`BL`/`BLVD.`, `GRANT LINE`/`GRANTLINE`, `SAINT HELENS`/`ST HELENS`) — textbook
cryptic-values variation, *"and `linkage.py` handles it perfectly, and the
solution is not connected to the data."* **The matcher that would catch it
exists, works, and was not run on the file that needed it.**

**The test gap is the sharpest detail.** `tests/unit/test_linkage.py:212` runs
the matcher over `facilities.csv` — the 43-row pilot file, which is clean — and
the docstring three lines above *states* that the same check over
`national_facilities.csv` finds three contradicted pairs. **The test that would
fail is not written.** A known defect, documented in a test file's own docstring,
with the test deliberately pointed at the clean input.

**The fix, and its explicit refusal to guess.** `warehouse/facility_dedup.py`
declares a reliability ordering over source types — and **ties are not
resolved**. Per Fellegi & Holt, *"one should, whenever possible, avoid
manufacturing data instead of collecting it"*, so a tie sets `open_q_index` to
**NaN, not a guess**, and is a hard failure in the file the build reads,
*"so that a human does three permit lookups instead of a rule inventing a
date."* All six rows are `source_type = permit`, so all three tie. Note also
that `CORRECT` is deliberately absent from the available dispositions — only
`EXCLUDE` and `REPORT` — because *"an edit that rewrote the field it localised
would be the imputation rule specified independently of the edits that Fellegi
& Holt's Criterion 2 exists to abolish."*

**And the cost of the refusal is stated rather than hidden.** That refusal
*"is what kept a 100-building, 62-CBSA frame out of the warehouse while the model
was fitted on 43 buildings."* It was resolved not by a better ranking but by a
**second edit**, `E_operating_by` (`quarter_start(open_q_index) <=
osha_operating_by`), whose validity is a logical impossibility rather than a
preference: *"A record claiming the building opened strictly after the date it
was already operating is not less reliable than its twin. **It is
impossible.**"* Note the deliberate use of quarter **starts**, not ends: a
claimed 2017Q4 opening against a 2017-12-21 inspection is consistent, and
*"comparing quarter ends would falsify the true record along with the false
one."*

**One more sentence worth stealing**, from the same subsystem's logs:
`load_operating_bounds` returns `None` rather than raising when the OSHA extract
is absent, and the run logs then say *"E_operating_by NOT EVALUATED… The edit is
declared and unchecked, which is not the same as passed."*

**Rule.** When two sources disagree and you have no principled ranking, emit
NaN and fail loudly. A silent aggregator — `min`, `max`, `first` — is a
tie-break policy nobody chose. And where you do adjudicate, prefer a rule
grounded in logical impossibility over one grounded in preference.

## 7.5 A naive outlier screen would delete Manhattan

**What happened.** Nothing in `src/` screens for outliers — *"Not a z-score, not
an IQR fence, not a winsorisation, not a plausibility band."* A robust screen
run for the audit (modified z on median/MAD, |z| > 3.5) flags **9,578 of 33,772
ZCTAs (28.36%)** on household density alone, and 20.93% of rows on
`traffic_proximity`.

The verdict is the lesson: *"The rates are high because the distributions are
heavy-tailed by nature, not because the data is dirty."* Worked through
([`data/DATA_QUALITY.md`](data/DATA_QUALITY.md)):

- **Extreme and correct.** ZCTA 10069 is 6,669 people on 0.041 sq mi =
  **162,659/sq mi**. *"A 3-sigma filter deletes Manhattan, which for a
  delivery-siting project **deletes the answer**."*
- **Extreme and correct.** `cost_per_parcel` = $6.41 at a Boise-area ZCTA with
  550 people, 64 stops/day and 61 miles of line haul. The model is doing exactly
  what it should.
- **Extreme and probably an artefact.** `rent_index` = **$68,623/month** at ZCTA
  11976 (Water Mill, NY) — Zillow's rent index in Hamptons ZIPs contaminated by
  summer whole-house lettings. **126 panel rows exceed $10,000/month across 8
  ZCTAs. Nothing flags them.**
- **Extreme and structurally wrong.** `permits_yoy_pct` hits **+5,900%** and
  exactly **−100%** on 6,232 rows — a county going from one unit to sixty, or to
  zero. *"Both are arithmetically defensible ratios on tiny denominators and
  both are useless as features. **There is no denominator floor anywhere.**"*

> *"The honest verdict is not 'we have 28% outliers'. It is '**we have never once
> looked, so we do not know which of our extremes are Manhattan and which are
> Water Mill**'."*

**Why it is easy to get wrong in both directions.** Not screening is obviously
bad. But the audit's own conclusion is that the literature points *away* from the
screen it was about to build. Rahm & Do's detection rule is **metadata-driven** —
a declared permissible range per column, not a distributional test. *"A robust-z
on household density contains no notion of a permissible range and therefore
cannot distinguish ZCTA 10069's correct 162,659/sq mi from an error. Running a
screen with no domain knowledge in it is precisely how we got 9,578 flagged
ZCTAs and zero information."* Winkler reframes it as **prioritisation**: rank
records by which cause the largest deviations of the key published total.

**Deliberately not done, with the reason recorded:** *"A robust-z screen puts
9,578 rows in front of a human and therefore never runs. When this is built it
should emit Van den Broeck's four-way **diagnosis** — erroneous / true extreme /
true normal / idiopathic — not a boolean."*

**Rule.** Do not build a distributional outlier screen. Declare a permissible
range per column from domain knowledge, and separately rank records by their
influence on the total you actually publish. A screen that flags 28% of your
rows will never be run by anyone, which makes it identical to no screen at all.

## 7.6 Three extractor bugs, each producing plausible output, none raising

**What happened.** The OCR pipeline that recovered facility rows from table
images had three defects, and the framing in the cleaning changelog is the
important part: *"it is not an edit on a delivered value, it is three defects in
an **extractor**… each of these three produced a facility row that looked
exactly like a correct one."*

**(a) Midpoint banding, defeated by variable row heights.** A table row was taken
as the band between the midpoints of neighbouring anchors. But the postal code
sits on the **last** printed line of a row, so a row occupies the space *above*
its anchor — and row heights vary with address wrapping (gaps of 48 px and 64 px
measured in the same table). The midpoint then falls above the next row's first
line, which joins that line to the previous facility's address. *"Two corrupted
rows, no error, and the row count unchanged."*

**(b) Five-digit street numbers invented facilities that do not exist.**
`20920 Krameria Ave, … California, USA, 92518` — **both `20920` and `92518`
match `\d{5}`**. Treating the house number as an anchor *"manufactures a
record"*: an observed row containing only `20920 Krameria Ave, March Air`, while
the real facility loses its first address line. *"A merge loses a facility, an
invented anchor adds one that was never there."* The fix tests **position, not
shape** — does the token end its line? Note the rejected fix: testing for
"leftmost" fails, because a postal code that wraps onto its own line is both
leftmost and rightmost.

**(c) A table border broke the test that fixed (b).** The table has ruled
borders, and a vertical rule OCRs as `|` just right of the last word. `94561 |`
therefore reads as "a postal code with something after it", (b)'s test rejects
the anchor, and that facility merges into its neighbour. *"A fix that
reintroduces the defect it was written to remove, in a narrower form, is the
reason (b) and (c) are two entries and not one."*

**The numbers, and how to read them:**

```
                          rows   clean   merged
  before the three fixes   510     469      41     92% clean
  after  the three fixes   535     517      18     97% clean
```

***"Read the merge rate, not the clean rate."*** 8% → 3% is the real improvement;
92% → 97% understates it, *"and the denominator moves too, because a merge
deletes a row, so the two percentages are not on quite the same base."*

**Why they were easy to get wrong.** Every one is a heuristic that is right most
of the time, validated by eyeballing output that looks like addresses. **There is
no oracle** — the ground truth is a picture. All three were found *"by measuring
the rows that failed to anchor rather than by anticipating anything"*, which is
the transferable technique: **instrument the failure-to-parse count, not the
parse.**

**Fixed in code; not guarded.** ***"There is no test file for `mwpvl_grid.py`,
`mwpvl_fields.py` or `mwpvl_tables.py`"*** — verified by searching `tests/` for
`mwpvl`, which returns nothing. *"Every other fix in this changelog names a test
that would fail if the defect returned; this one cannot. The three cases above
are each a two-line fixture."* A second gap: the merge count is emitted into no
artefact, so 517/535 is a hand-figure *"of the same sort as the '13 genuinely
new' facilities… the figure this project has already been burned by once"*
(§4.1).

**One deliberate non-feature worth noting.** The pipeline **cleans nothing**:
*"a year that reads `9022` is written out as `9022`, because `warehouse/edits.py`
can test a date against the OSHA `operating_by` bound, which is **evidence**,
rather than against plausibility."*

**Rule.** For any extractor without an oracle, instrument the **failure-to-parse
rate** and watch it, because correctness is unobservable and failure is not. Pin
each fix with a two-line fixture — an extractor fix that reintroduces an earlier
bug in narrower form is the normal case, not the exception. And emit the quality
counts into an artefact rather than reading them off a terminal.

## 7.7 Half-closure: a quality flag nothing reads is provenance, not repair

**What happened.** The project built real machinery for censoring and imputation
flags: `common/sentinels.py` (one declared registry, TOP/BOTTOM/ABSENT kinds,
`detect()` emits a boolean and **never edits a value**) plus
`warehouse/flag_gate.py`, an L3 build gate that **raises** if any registry flag,
or any interim column ending in `_imputed`/`_topcoded`/`_censored`/`_suppressed`
and friends, fails to appear in the panel — **with no exemption list,
deliberately**. The panel went from 44 columns and 1 flag to 50 columns and 7.

**And then nothing reads them.** [`data/DATA_QUALITY.md`](data/DATA_QUALITY.md):
*"What replaced it is **provenance, not repair**. The flags now survive; no
model, no cost function and no report conditions on a single one of them. The
censored values are still being read as measurements by every consumer that
reads them at all."*

**The concrete cost.** `warehouse/facility_load.py:107-108` still does
`frame["open_quarter"].fillna(1)`. **19 of 43 rows (44.2%)** have no quarter,
producing **35.47%** of fitted events in Q1 against 25.00% expected under
uniformity — ten percentage points of spurious Q1 seasonality injected into the
target of a model that fits a four-knot spline in calendar time. And:
***"The 35.47% is not my number — it is already in `hazard_report.json` under
`event_timing/share_in_q1`, which means the project measures the artefact and
does not act on it."***

**Why it was easy to get wrong.** Building the flag *feels like* fixing the
problem. It closes a ticket, adds a column, passes a test, and `flag_gate.py`
even enforces its presence. The remaining half — a consumer that conditions on
it — has no natural owner, no failing test and no visible symptom. *"Under the
framework a suspect without a verdict is an unfinished job, not a finished one —
the whole point of separating the stages is that screening produces suspects,
not conclusions."*

**The cheap treatment the literature asks for, not done:** retain the flag and
the original, run the model **with and without** the 19 imputed-quarter
facilities, and publish the difference.

**Two related facts from the same file.** All 43 facility coordinates are NULL
and all 43 are filled from the ZCTA centroid, so *"every catchment in the
project is a fifteen-mile circle drawn around a centroid, not a building."* And
`facilities.py:215` does `enabled.fillna(False)`: *"'Not covered by any known
catchment' and 'known not to be served' have been collapsed into the same
`False`, which is exactly the encoding the docstring was written to prevent."*

**How the alternatives were rejected — a template worth copying.** *Delete
top-coded ZCTAs* → drops Palo Alto and Atherton, selection on the outcome.
*Impute a tail expectation* → invents a number and hides the censoring. *Drop
the 19 undated rows* → shrinks events 43 → 24 and biases toward well-documented
metros. *Move the default to Q3 as a compromise* → *"Changes the target with no
more evidence than Q1 had."*

**Rule.** A flag that reaches your dataset and that no consumer conditions on is
provenance, not repair — useful, but do not close the ticket. The finishing move
is cheap: run the analysis with and without the flagged rows and publish the
difference.

---

# Part 8 — Near-misses, where the mechanism that caught it is the lesson

Nothing in this part did damage. Each is included because the thing that
stopped it is reusable, and because a near-miss is the only kind of evidence
you get that a control works.

## 8.1 A USD 25 licensed dataset and 12 MB of third-party copyright, one `git add` from public

**What happened.** While this repository was private, the governing concern was
**preserving sources that cannot be re-downloaded**, and `.gitignore` was
written accordingly. It explicitly *un-ignored* both the purchased subsidy
extract and the MWPVL PDFs (`.gitignore:136-141`):

```
# Good Jobs First Subsidy Tracker, Amazon parent, downloaded 2026-09-14.
# PAID (USD 25) and NOT re-fetchable from this host, which gets HTTP 403 from
# the endpoint. 349 KB. Tracked for the same reason as the MWPVL article: a
# source that cannot be re-downloaded is evidence, not a cache.
!data/external/subsidies/
!data/external/subsidies/*.csv
```

That reasoning was correct, and publishing inverted it. The reversal sits last
in the file so it wins, and the comment is the lesson verbatim
(`.gitignore:149-170`):

```
# PUBLIC REPOSITORY OVERRIDE (2026-09-15)
#
# Everything above was written while this repository was private, where the
# governing concern was preserving sources that cannot be re-downloaded.
# Publishing inverts that reasoning for two of them: a file we cannot re-fetch
# is still a file we have no right to redistribute. Both were verified as
# COMMITTABLE by `git check-ignore -q` before these rules were added. They sit
# last in the file so they win.
...
# MWPVL International industry reports: third-party copyright, and the
# publisher states in the article that it is being withdrawn from free
# circulation. The FACTS extracted from them do ship, attributed, as
# data/interim/mwpvl_facilities.csv -- facts are not copyrightable, the
# document is.
```

**Why it was easy to get wrong.** Nobody made a mistake. A rule that was right
under one set of constraints became wrong when a single external fact changed —
the repository's audience — and *nothing in the codebase represents that fact*.
There is no test for "the threat model changed." The dangerous form of this is
that the original reasoning is still persuasive when you re-read it: "a source
that cannot be re-downloaded is evidence, not a cache" is *true*, and it is the
wrong consideration.

**The distinction that made the fix workable**, and it is worth knowing: **facts
are not copyrightable, documents are.** The derived facts ship, attributed; the
PDFs do not. Similarly, the subsidy aggregates ship in
`outputs/metrics/subsidies.json` while the purchased CSV does not, and
`docs/DATA_SOURCES.md` says where to buy the original.

**Two mechanisms came out of it**, and the pairing is the point:

- `scripts/preflight_publish.sh`, whose origin statement is at lines 13-14 —
  *"Written after a near-miss in which a USD 25 licensed dataset and an 11 MB
  copyrighted PDF were both one `git add` away from being public"* — and whose
  licensing section enumerates the files by name and fails with
  `WOULD BE PUBLISHED: <path>` plus a remedy line.
- `scripts/export_public.sh`, which exists because **`.gitignore` protects
  `git add` and nothing else**: *"Anyone uploading the working folder through
  github.com's web page, or zipping it to send somewhere, ships .env, a USD 25
  licensed dataset and 12 MB of third-party copyright."* Its second pass
  deliberately does not consult `.gitignore` at all — see §5.2.

**Current state, verified.** Neither is tracked; both are ignored by rules at
`.gitignore:163` and `:170`.

**Two live gaps, reported rather than smoothed over.** `subsidies.json` — the
derived artefact that is supposed to ship *instead* — is itself **untracked**,
and nothing in preflight checks that the substitute is present. And
`export_public.sh:180` tells the operator to "see PUBLISHING.md", which **does
not exist**.

**Rule.** When the audience for an artefact changes, re-derive your exclusion
rules from scratch rather than auditing the existing ones — the old reasoning
will still read as correct. Protect the *folder*, not just the *commit*, because
`.gitignore` has no opinion about a zip file. And when you exclude a source,
check that the substitute you promised actually ships.

## 8.2 Credentials: three layers, because each one alone leaks

**What happened.** A live `EIA_API_KEY` was written into `console.log`,
`events.jsonl` and `errors.log` **at once**. The cause is one most people would
not predict: `requests` embeds the fully expanded URL, query string included, in
its exception messages, and the exception was logged verbatim. The incident is
recorded in the docstring of the function written to stop it,
`common/http.py:81-102`:

> *"A credential also arrives by routes we do not control: `requests` embeds the
> fully expanded URL — query string included — in its exception messages, so
> logging an exception verbatim writes the live key into console.log,
> events.jsonl and errors.log at once. **That happened, with a real
> EIA_API_KEY, before this function existed.**"*

`_scrub` runs **three passes, because each alone leaks** — a `name=value`
pattern; an `Authorization: Bearer`/`Basic` scheme match, which has no `name=`
for pass one to key off; and a **literal-value** pass over the actual contents
of the credential environment variables, *"so a bare key pasted into a message
with no `name=` around it is still caught."* All three are idempotent by
construction.

**A second, entirely different vector**, `http.py:114-127` — the server echoes
the key back:

> *"The EIA v2 API replies with a `request.params.api_key` block containing the
> key just sent. Cached verbatim, that writes a live credential into
> `data/raw/`. It is gitignored and the committed manifest carries only the
> redacted URL, so nothing was publishable — but **the cache is exactly what
> gets copied to a colleague or a cluster**."*

and the reasoning for rewriting the cached file is the best argument in the
file:

> *"Rewriting the file changes its hash, which looks like it breaks the
> 're-download and verify' promise. It does the opposite: the echoed key differs
> per user, so an un-scrubbed EIA response could **never** hash the same for two
> people. Removing it is what makes the artefact reproducible."*

**Why it was easy to get wrong.** Redacting the URLs you construct is the
obvious control and it is what everyone builds. It covers the outbound path and
misses three inbound ones: the exception message, the argv, and the response
body. Every one of those is a place a credential arrives *without you putting it
there*.

**Defence in depth, and the layer ordering is the transferable part.** Source
redaction (`_scrub`) → `logs/` gitignored with the reasoning written into
`.gitignore:29-32` → a pre-commit hook, because *"Gitignore is advisory:
`git add -f` beats it. This does not"* → a publish-time scan over every value in
`.env`. Four layers, each defeating a different bypass of the one above.

**Verified clean.** A scan for the current key across the whole tree returns
`.env` and nothing else; `.env` has never been committed; the 962 log entries
show the redaction firing, including the literal-value pass.

**One gap found while checking, reported as found.** `_scrub` covers log
*messages*, but **captured subprocess output is not scrubbed** —
`commands.jsonl` carries a `stdout_tail` with an unredacted key-shaped literal
(it is a test fixture, so nothing real leaked, but a real key printed to stdout
by a child process would land there).

**Rule.** Enumerate every path by which a credential can arrive in text you
write to disk — constructed URLs, exception messages, argv, response bodies,
subprocess stdout — because redacting the one you control covers less than half
of them. Then layer the controls so that each one catches a bypass of the last,
and note that gitignore is advisory while a hook is not.

## 8.3 The `.gitignore` negation trap, and the flag that lies about it

**Two things, and this repository got one right and one wrong.**

**The directory-descent rule is real**, and is recorded verbatim at
`.gitignore:75-79`:

> *"`data/external/*` above excludes the SUBDIRECTORY itself, and git will not
> descend into an excluded directory, so a bare
> `!data/external/facility_panel/facilities.csv` silently never matches. The
> directory has to be re-admitted first, then its contents re-excluded, then the
> wanted files admitted."*

**The obvious way to verify that is the wrong way round.** Measured today on git
2.52.0, against a file that is *not* ignored because a negation re-admits it:

```
  git check-ignore -v path  ->  prints ".gitignore:130:!data/external/..."  exit 0
  git check-ignore -q path  ->  prints nothing                              exit 1
```

Under `-v`, exit 0 means *"some pattern matched"* — **including a negation** — so
both the printed output and the exit code read as "ignored" when the file is
emphatically not. The correct form is `-q`, where exit 1 means not ignored.

**Why it was easy to get wrong.** `-v` is the verbose flag; verbose flags are
supposed to add information, not change semantics. And the output it prints is
*true* — a rule did match, and the rule is even shown with its `!` prefix. You
have to notice that the tool is answering "which pattern decided this?" while
you are asking "is this file ignored?", and that those questions have different
answers under a negation.

**And getting the rule right is not the same as getting the file in.** All four
files the publish gate lists as `must_ship` — including
`data/external/facility_panel/national_facilities_expanded.csv`, the 693-row
panel behind most of this project's results — are correctly un-ignored, and
**none of them is tracked**. Nobody ran `git add`. The preflight
`reproducibility` section tests *existence + not-ignored*, not *tracked-ness*,
so it prints `ok: ships:` for all four. **A guard that checks a proxy for the
property you care about is §5.2 in a different costume**, and this one is live.

**Rule.** To re-admit a file under an excluded directory: un-exclude the
directory, re-exclude its contents, then admit the file. Verify with
`git check-ignore -q` and read the **exit code**, never with `-v`. Then check
`git ls-files` — "not ignored" and "committed" are different properties, and it
is the second one you actually wanted.

## 8.4 Environment-specific tooling does not belong in a public repository

**What happened.** Three shell scripts once lived in `scripts/grid/`, relocating
a tesseract build and 14 non-system shared libraries so that OCR could run on a
locked-down Python 3.6 compute grid. They worked, and the OCR they enabled
produced most of the expanded panel. They were removed, and the OCR itself moved
to `tools/ocr/`. `tools/ocr/README.md:102-108` gives the reason:

> *"they are useless to anyone else — they solved one institution's environment,
> not an OCR problem. They were removed rather than published, because **a
> script that appears necessary and is not costs a reader more than it
> saves**."*

**Why it was tempting to keep them.** They represented real, hard-won work; they
were the difference between the extraction happening and not happening; and
deleting working code feels like destroying evidence of effort. The counter-test
is the reader's, not the author's.

**A residue worth noting**, because it is the predictable cost of deleting
something: `.gitignore:143-147` still names `scripts/grid/bundle_tesseract.sh`
as the builder of the 20 MB `vendor/` directory it excludes — a comment pointing
at a script that no longer exists. (That `vendor/` exclusion is itself a closed
near-miss: it was 20 MB of non-portable ELF binaries, untracked and **not
ignored**, one `git add -A` from permanent history, flagged as item 3 of ten in
the audit and now excluded at `.gitignore:147`.)

**Rule.** Before publishing, ask of every script whether a stranger on an
ordinary machine would need it. If not, delete it and leave one paragraph of
prose saying what it did — and grep for comments that referenced it.

---

# Part 9 — The project around the project

## 9.1 A negative result has no natural home. Assign it a page

**What happened.** At one point **not one of seven status documents stated the
project's negative result**, and four implied the model had never run on real
data. Nobody lied and nobody was hiding anything.
[`DECISION_LOG.md`](DECISION_LOG.md) §2.12 diagnoses the mechanism:

> *"The failure mode was not that anyone lied. It was that a negative result has
> no natural home: it is nobody's deliverable, no test fails because of it, and
> every document has a more encouraging thing to say. **Silence is the default
> outcome unless someone assigns it a page.**"*

**Why it was easy to get wrong.** Consider what each document is *for*. A README
introduces. An architecture doc describes structure. A reproduce guide gives
commands. A roadmap looks forward. None of them has a section whose job is "and
here is what did not work", so the null has nowhere to go that is not an
interruption — and the author of each document is, quite correctly, staying on
topic.

**Fixed structurally.** Nine documents now state it and `STATUS.md` leads with
it. The paper's title is *"A Pre-Registered Negative Result at Two Geographic
Grains"*, which is the strongest available form of assigning it a page. The
prereg had also, in advance, written both outcome paragraphs and noted of the
null: *"Both are complete findings. The second is harder and arguably more
valuable."*

**Rule.** Name a document that owns the negative result, make it the first thing
the top-level README links to, and write the sentence before you know the
answer. Silence about a null is not neutrality; it is a slow drift back towards
the hypothesis.

## 9.2 Five documents agreeing on a wrong cause reads as corroboration

**What happened.** `STATUS.md`, the backlog, `ROADMAP.md`, `ARCHITECTURE.md` and
`REPRODUCE.md` all reported the negative result **correctly** — and all five
attributed it to **sample size**: "39 usable events across 43 buildings cannot
identify a siting model." That is the explanation the methods document opens by
*rejecting*. The actual cause was the unit of analysis (§1.3).
`adr/0004`:

> *"It is recorded here rather than quietly overwritten, because several
> independent documents agreeing on a wrong cause reads as corroboration, which
> is worse than one document being blank."*

> *"A panel ten times larger at ZCTA-quarter grain would have failed in the same
> way, because the alternatives still would not have been mutually exclusive."*

**Why it was easy to get wrong.** The five documents were not independent — they
were copied from each other, and the fifth agreeing with the first is not
evidence. And "small sample" is the **always-available** explanation for a weak
result: it is never false (n *was* small), it is never actionable in a way that
threatens the design, and it flatters everyone, because it implies the method
was fine and the world was stingy. It is the diagnosis that requires no
diagnosis.

**The claim was later tested and falsified**, which is the part that makes this
credible rather than merely self-aware: the hazard model was rebuilt on 6.7× the
events and did not move (§1.3).

**Rule.** When several documents agree, check whether they are independent
observations or copies. And treat "the sample was too small" as a hypothesis
requiring a test — the test is cheap (get more data, or simulate it) and it is
the explanation most likely to be wrong in your favour.

## 9.3 An accepted ADR written in the past tense becomes fabricated engineering history

**What happened.** `docs/adr/0002-routing-offline.md`, status **accepted**,
describes precomputing origin–destination matrices per metro with OSRM, deleting
intermediates, and shipping ten parquet files — with the headline consequence
*"Peak disk falls from ~60 GB to ~8 GB."* The 2026-09-14 update reads:

> ***"Everything above the line is a design. None of it was built."***

Specifically: **no OSRM was ever run**, on any metro; **no OD matrix exists**;
**no disk figure in the ADR was ever measured** — 2–5 GB, 15–25 GB, ~30 GB,
64–128 GB RAM and the 60 → 8 GB headline are all estimates made before the work;
the circuity approximation is not the fallback, it *is* the implementation; and
the constant is wrong in the text twice over — the ADR says "great-circle × 1.35,
calibrated on one metro against routed truth", the implemented value is **1.30**,
*"and it cannot have been calibrated against routed truth, because no routing was
ever run."*

The update also names the specific harm: *"Do not put the 60 GB → 8 GB figure on
a CV: it was billed that way in `career/SCALE_AND_IMPACT.md` and has been removed
from it."*

**Why it was easy to get wrong, and this one is structural.** The ADR template's
"Decision" and "Consequences" sections are **written in the past or imperative
tense by convention** — "Process one metro at a time… Peak disk falls from…" The
genre forces the tense, so a design document reads as a completion report. And
ADRs are explicitly never edited, so it reads that way *indefinitely*. Worse, the
status field says **accepted**, which a reader correctly interprets as "this is
settled" and then incorrectly extends to "this is done."

**The same pattern hits ADR-0001**, where three "Consequences" were never
executed: precision@k and PR-AUC were never computed — and an earlier draft of a
career document quoted *"a precision@100 of 0.61"* as a bullet, **a number never
measured by anybody** — and the label-noise simulation was never built, so the
ADR's residual risk is *"still open and unbounded, not mitigated."*

**The generalised rule the project drew from it:** ***a "Consequences" section is
a set of promises, and nothing in any workflow ever audits it.***

**The honest residual** is also worth copying. The app does carry no routing
dependency, which is what ADR-0002 wanted — *"That was achieved — by not
building the thing at all rather than by precomputing it, which is a weaker
claim than the one this ADR makes."*

**Rule.** Write decision records in the **future conditional** until the thing is
built, then add a dated "as built" section. Give every ADR a status beyond
accepted/rejected — `accepted, not implemented` is the state most of them are
actually in — and periodically audit the Consequences sections as a checklist,
because nothing else will.

## 9.4 A fix with no correction marker is invisible, and it costs you the credibility you earned

**What happened.** Two real defects — the parcels/stops conflation and the
linear cannibalisation rule — are fixed in code and covered by tests, and
**neither carries a RESOLVED marker anywhere**. `COST_MODEL.md:169` presents the
parcels/stops issue as *"where naive versions of this model go wrong"* — a
**design rationale**, not a correction that was made.
[`DECISION_LOG.md`](DECISION_LOG.md): *"A reader cannot tell this was ever a
bug."*

**Why this matters more than it sounds.** Two costs, and the second is the one
people miss. First, a defect presented as design rationale **loses the
provenance that tells the next person why the guard exists**, so the guard looks
removable — and someone will remove it. Second, in a project whose stated
product is *"checkability is the product"*, it quietly converts an
error-found-and-fixed — the most credible thing a project can show — into
ordinary competence.

**Why it was easy to get wrong.** The instinct to write "we designed it this
way" rather than "we got this wrong on 2026-09-12 and here is the diff" is
overwhelming, especially when the current code *is* right. It reads better, it
is shorter, and it is not untrue.

**A related trap named in the same entry**: an open roadmap item called
"Cannibalisation decay radius" concerns *estimating the radius* — a **different
question** from the functional form that was actually wrong. An open ticket with
a similar name reads as "this is tracked" when the real defect is untracked.

**For completeness, the two defects.** *Parcels vs stops*: service time is paid
once **per door**, not per parcel, and charging it per parcel *"overstates
labour cost precisely in the dense, high-volume ZCTAs the ranking exists to
identify as cheap."* It was easy to get wrong because both are integer counts of
things a van handles, both live in the same dataframe, and at
`parcels_per_stop = 1.4` they differ by only 40% — small enough that the output
stays plausible, large enough to reorder a ranking. Service time was **66.96%
of total cost** on the solved-depot pilot this was measured on, and is
**59.75%** on the current station-based model, so the entire headline still
rides on that one unit conversion — a little less of it than before, because
real line haul is more than twice as long as solved line haul and drive plus
fuel now take 18.6% of the stop rather than 10.1%.
*Cannibalisation*: a linear decay at 0.18 per unit of neighbour exposure, where
exposure reaches 99.2 for the most crowded ZCTA, claimed nearby activations
destroy **90% of each other's demand**. `optimize/params.py:37-51` records the
verdict: ***"That is arithmetic, not economics."*** It was easy to get wrong
because a linear decay is the obvious first draft and is *correct in the regime
you hand-check* — with three neighbours it is fine. The failure appears only at
the density the optimiser actually explores, which is the regime you never
inspect by hand. Fixed with a saturating form, `peak · (1 − exp(−exposure))`.

**Rule.** When you fix a defect, leave a dated marker at the site — in the
docstring, the test name, or a changelog — saying what it used to do and why it
changed. "We designed it this way" is the version of the story that loses both
the warning and the credit.

## 9.5 Measure the programme's output in the unit you actually want

**What happened.** Six sittings of manual labelling sent **362 sites** through a
classification worklist. 135 came back as delivery stations. **289 of the
worklist rows — 79.8% — were already in `NATIONAL_CLASSIFIED.csv`**, and the
whole exercise produced **13** facilities genuinely new to the panel
([`DECISION_LOG.md`](DECISION_LOG.md) §2.13). Roughly 96% of the effort produced
nothing.

The generator built its worklist from rows where a name-based regex had left
`facility_type` empty, and never joined that against what was already labelled.
*"'Unclassified by our regex' was treated as 'unknown to the project'. Those are
different sets, and nothing in the script asserted that they were the same."*
(That is §5.1 again, in a different guise.)

**What caught it, three batches late.** Joining a batch back to the panel after
batch 4 and finding **76 of 85** delivery stations already there. The commit
message is unusually direct: *"Batch 4 in; 76 of 85 DS were already in the panel
-- my batch generator was wrong."*

**Why it took four batches, which is the actual lesson.** *"The programme
measured its output in **sites labelled** rather than in **facilities added**."*
Sites labelled is the number the process emits naturally, it goes up every
session, and it feels like progress. Facilities added requires a join back
against the thing you were trying to improve, which nobody does until something
looks wrong.

**And one number in the entry still cannot be reproduced**, which the log says
plainly: "genuinely new" was reported as ten after five batches and thirteen
after six, with an intermediate estimate computed against the wrong reference
file; rebuilding it from the tree by address match gives 27 or 37 depending on
the reference. *"13 is the working figure and it cannot currently be checked."*
It is emitted by no code — §4.1.

**The salvage was recognised, and named as salvage.** The 122 already-known
delivery stations are a hand-labelled validation set for the classifier, whose
agreement rate had never been measured.

**Rule.** Instrument the metric you care about — net new usable rows — not the
one the process emits naturally. Join your output back against the thing it is
supposed to improve **after the first batch**, not the fourth. And when a
programme goes wrong, check whether a by-product is worth more than the original
goal.

## 9.6 Checkpoint after every stage, and measure before you parallelise

**What happened.** On 2026-09-14 a monolithic version of the covariate
experiment wrote its artefact once, at the very end, after four stages.
`models/covariate_harness.py:19-34`:

> *"The machine it shares was at **load average 44 on six cores**, the run had to
> be stopped, and **forty-five minutes of completed, correct, finished work was
> discarded because it existed only in memory**."*

**Why it was easy to get wrong.** Writing once at the end is the natural shape
for a script that produces one artefact, and it is *correct* for a run that
finishes. It is also the shape that converts any interruption — a stop, an OOM,
a shared-machine problem, a power cut — into total loss rather than partial
loss. The probability of interruption is invisible when you are writing the
script and obvious when you are watching a progress bar.

**Fixed**, with `save` after every stage plus the provenance ledger of §4.3. Note
the coupling: that fix created the resume path that caused the stamp bug in
§4.2.

**The shared-machine half, stated honestly.** The harness still runs a
five-process pool and still never calls `os.nice`, so that half was solved by
convention rather than by code. Most long-running entry points *do* call
`os.nice(19)` — `metro_entry.py:299`, `gravity_network.py:242`,
`hazard_revival.py:194` and others — and one experiment note records the right
reasoning for the default:
*"parallelism buys wall clock and nothing else because the repeats are
independent by construction."*

**Rule.** Write a checkpoint after every stage that took longer than it takes to
write one. On shared hardware, nice long jobs and read the load average before
adding workers — and ask what parallelism actually buys you, because for
embarrassingly parallel repeats the answer is often only wall clock, at the cost
of everyone else's.

## 9.7 A question about data quality is not a question about model choice

**What happened.** The project's owner asked, on **six separate occasions**,
whether best-in-class **data cleaning and validation** had been done, and asked
for proof. Phrasings included *"are you employing best in class data cleaning,
data validation, algorithms, prove it"* and finally *"did you read any research
papers on data cleaning — this is 6th time i asked you, and you are ignoring
me"*.

Every one of those was answered with **econometrics** — discrete choice, moment
inequalities, hazard specification
([`DECISION_LOG.md`](DECISION_LOG.md) §4.4). One record-linkage paper was
delegated and then treated as covering the whole subject, which it does not:
record linkage decides whether two rows are the same thing, and says nothing
about missingness, outliers, range validation, cross-field constraints or
integration conflicts. The material evidence that the complaint was correct: the
reading folder held Train chapters 3–14 and four econometrics papers, and
**zero** data-cleaning papers.

**Why it happened**, in the log's own words: *"The project's visible failure was
a modelling failure, so every 'is this good enough' question was routed to the
modelling literature. Data quality was treated as something already handled
because individual defects had been fixed as they surfaced… **Fixing defects one
at a time is not the same as auditing against a taxonomy, and the difference is
exactly what a taxonomy is for.**"*

**What it cost.** At least one finding that changes a result went unseen until a
taxonomy was applied — the listwise-deletion-under-non-random-missingness case
in §7.3, which had **already been caught once elsewhere** and was not looked for
again, *"because there was no checklist to look against."* Applying Rahm & Do,
Little & Rubin, Fellegi–Holt and Van den Broeck subsequently produced the
material in Part 7 of this document: the Connecticut join, the grain problem,
the outlier framing, the flag half-closure. Essentially all of Part 7 is the
answer to the question that was asked six times.

**Rule.** Data quality and model specification are different literatures with
different taxonomies. Audit against a published taxonomy rather than against
your own memory of what you have fixed — the memory is a list of *symptoms you
happened to trip over*, and a taxonomy is a list of *places to look*. And when
someone asks the same question a third time, the answer you have been giving is
to a different question.

## 9.8 A stale checklist trains you to ignore the checklist

**What happened.** Seven Phase-0 decisions sit unticked in
[`ROADMAP.md`](ROADMAP.md) under a header reading ***"Nothing in Phase 1 should
start until they are answered in writing"*** — while Phases 1, 2 and 4 are the
built spine of the project. At least four of the seven are demonstrably resolved
elsewhere and were simply never back-filled: one by an accepted ADR, one by a
later roadmap line, one by the repository's own name.

**The reading that matters is not the checkboxes.** It is that **Phase 3, the
causal layer, is at zero of seven** — and the proposal's headline claims lean on
Phase 3.

**Why it was easy to get wrong.** A checklist with four false negatives on it
teaches its readers that the checklist is out of date, and a checklist nobody
believes stops surfacing the one item that matters. The failure is not the four
stale boxes; it is the credibility they spend.

**Rule.** Either maintain a gating checklist or delete it. A gate that is
routinely passed without being ticked is worse than no gate, because it
suppresses the one entry that is genuinely still open.

## 9.9 The right answer to "should we buy better data" can be no — and the reason is not budget

**What happened.** The commercial panel this project could not afford was
confirmed, from a published paper that used it, to carry *"location, size in
square feet of floor space, employment, facility type, opening date, and closing
date"* — item for item the panel that took a day to fail to build. The argument
against buying it is not cost
([`DECISION_LOG.md`](DECISION_LOG.md) §1.7):

> *"Houde et al. already published the paid-data version, in Econometrica.
> Buying MWPVL moves us from 'the free-data version of a question nobody has
> asked about delivery stations' to 'a smaller, later, worse-resourced version
> of an Econometrica paper'. **It would buy better data and destroy the
> contribution.**"*

**And the entry does not let itself off.** *"Today the entire calibration of the
OSHA bound rests on **five** addresses from MWPVL's 2012 public table, all
fulfilment centres from 2008-2011, with lags of 4, 13, 57, 69 and 345 months.
**Five is not a measurement.**"* The proposed compromise — buy a small academic
slice **for validation only** and publish a measured error rate — is named and
not yet actioned.

**Why it was easy to get wrong in both directions.** "We could not afford the
data" is an excuse that is always available and always slightly true, and it
converts a design choice into a constraint. The opposite error is equally easy:
buying the data feels unambiguously like an upgrade, and nobody asks whether the
upgrade removes the reason the work is interesting. The distinction that resolves
it — buy it for **validation**, not for **estimation** — is available in almost
every version of this situation and is rarely considered.

**Rule.** Before buying the data that would make your study "proper", write down
what your contribution is *because* you do not have it. If the answer is
nothing, buy the data. If it is something, buy the smallest slice that lets you
measure your own error rate, and publish that.

## 9.10 Read the survey with your data in hand, not only with your question

**What happened.** The project read a survey of partial identification to find
out whether the estimator it was considering was respectable. It found the
answer and stopped. [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §11:

> *"We read Molinari's survey to find out whether the Holmes/Houde estimator was
> respectable. **The section that describes our data is Sec. 2.3, and we walked
> past it.**"*

The project's outcome is not a mismeasured date. It is a date **known to lie in
an interval** — after the panel start, on or before the OSHA inspection — which
is Molinari's Identification Problem 2.2 exactly, with a sharp identified set, a
convex set with a support function, a simple sample-analogue estimator, and
shipping software. *"It turns the panel's worst defect into the estimator's
input."*

**The related finding, from the same reading.** The estimator the project *was*
attracted to is identified by exactly the quantity it measures worst: Holmes's
measurement-error result assumes `x` and the instruments are directly observed
and puts the error on profits, and §8.3 is explicit that the procedure *"yields
inconsistent estimates of the identified set when there is measurement error in
the `x` variables."* ***"Holmes protects the side we have clean and assumes
clean the side we do not."***

**Why it was easy to get wrong.** You read a survey **with a question in hand**,
you find the section that answers it, and you stop — which is efficient and
correct behaviour for the question you asked. The section that describes your
*data* is not the section that answers your *question*, and nothing prompts you
to look for it.

**The fix carries its own warning**, which should travel with any partial
identification result: misspecification makes these sets **spuriously tight**, so
*"a narrow interval from 43 buildings would be a reason for suspicion, not
celebration."*

**Where this goes next.** Interval-censored opening dates are item 2 of four in
[`ROADMAP.md`](ROADMAP.md) § *Future scope*: *"An interval is a thing the
econometrics can actually use."*

**Rule.** When you read a methods survey, make two passes: one for your question,
and one for the section that describes the shape of your data. The second pass
is where the estimator you did not know to ask for lives.

---

# The five that generalise

Thirty-odd entries is a reference, not a lesson. These five are what is left
when you remove everything specific to siting, warehouses, discrete choice,
and this dataset. Each names the entries it came from, so you can go back for
the evidence.

### 1. Write the bar down before you fit, and make the writing verifiable

Name the baseline you would be embarrassed to lose to, and a second criterion
your favourite metric does not capture. Write the sentence you will publish
under each outcome, *before* you know which one you get. Then hash the
document, put the hash inside the result artefact, keep a reference copy whose
filename is the hash, route every correction to a file the hash does not cover,
and make the CI failure message name the repair — because when a seal breaks,
the two intuitive fixes both make the break invisible.

This is the cheapest thing in this document and the only one that changes what
you *do* rather than what you *know*. Here it fixed the households baseline
before anyone knew the model would clear only the uniform one, and fixed the
calibration clause before anyone knew the model would rank tolerably and
calibrate badly. It also produced three criticisms of itself, which a vaguer
plan cannot do: you can only be specifically wrong about something you
specifically wrote down.

*(§1.1, §1.2; and §9.1 — a null needs an owner as well as a plan.)*

### 2. Check the grain and the strata before you check anything else

Two statistics, both two lines of code, that between them caught more here than
any modelling decision:

```python
df.groupby(unit)[col].nunique().mean()        # can this column discriminate?
metric_by_stratum(df, strata)                 # is the pooled number real?
```

The first would have cut a pre-registered covariate list from twelve columns to
about four, before it was frozen — six of them were county figures offering
**nine distinct values across two hundred alternatives**, at 99.9% coverage and
high national variance, so every standard data-quality check passed them. The
second caught a pooled AUC of **0.7323** sitting **above the model's AUC in every
tercile** (0.4125 / 0.5666 / 0.6961).

Both failures share a structure worth internalising: *coverage, variance and
correlation are properties of a column; discriminating power is a property of a
column **relative to the comparison your model makes**.* Nothing in a data
contract knows what your model conditions on, so nothing in a data contract can
catch this.

And the closely related third: your grain must be recorded **in the data**, not
in a comment. A county value in a column named like a ZCTA measurement gives you
standard errors wrong by a factor you will never notice.

*(§1.4, §1.5, §7.2; and §1.3 — the same question one level up, about rows and
decisions.)*

### 3. A method that always returns an answer is under suspicion, not above it

Build a falsification test that is **logically independent of the method's own
error model**, and run it before you look at accuracy. "Impossible, given
something else I already know" beats "accurate on the subset I can check", and
it is usually available: here it was *an opening date that post-dates a
regulator's proof that the building was already operating*, which killed a
satellite pipeline that had returned an estimate for **107 of 107** sites and
was falsified on **36%** of them.

Treat completeness as evidence against you when the world is incomplete. The
single most portable sentence this project produced:

> *"A dataset with no missing values, produced by a process that should have
> produced many, is evidence of fabrication rather than of diligence."*

Thirty-five rows, every one with a year, a quarter and a URL, no hedging and no
gaps — **thirty-three of them invented.** Note also what the method's own
confidence score bought in both cases: nothing. A self-reported quality signal
tells you about the failures the method anticipated, which are not the ones that
will hurt you.

And the corollary for tempting partial output: the subset that survives your
test is not clean data, it is *the subset of a method that fails a third of the
time which happened not to fail visibly*.

*(§6.1; and §7.5 — the same instinct inverted, where a screen that flags 28% of
your rows is identical to no screen at all.)*

### 4. Verify against the artefact that emitted the number — never a document that quotes it, and least of all a corrected one

Corrections here inherited errors four separate times. $2.10 → $1.51 → $1.0875
→ $1.0830, with the current artefact reading **$1.1389** on a rebuilt depot
layer — a *model change*, not a fifth correction, and the two must not be
collapsed into one sequence. Activations 317 → 330 → 282, where the
three accompanying capital figures turned out to be one number in three costumes.
A retired artefact whose own summary field contradicts the fields beside it. And
a correction that got every number right and changed one verb —
*"matched"* → *"beaten"* — on a one-hit gap inside a paired sd of 1.14.

A corrected document carries social authority precisely where it deserves least:
the header "Corrected 2026-09-14" makes a reader trust the *whole page*, when
what was checked was one clause. Correction logs also drift the other way — this
project's defect register currently reports as open a defect whose three named
documents have all been fixed, which costs a reader exactly as much time.

Two operational consequences. **If a number is counted by hand, make code print
it** — every hand-counted figure in this project's history has moved at least
once, and one of them still cannot be reproduced at all. And **stamps describe
the write, never the payload**: an emitter that resumes from its own artefact
will inherit its own identity unless you strip the stamp keys, which is how two
different results here shipped under one `run_id`.

*(§4.1, §4.2, §4.3, §4.5; and §3.5 — check whether two of your headline figures
are deterministic functions of each other.)*

### 5. A check that cannot fail is not a check — and silence is the default outcome for everything inconvenient

These are one lesson because they have one cause: **nothing in a normal workflow
fails when something important is absent.**

No test fails for an unstated null, a fabricated figure, an unread citation, an
uncommitted data file, a module no test imports, a quality flag no consumer
reads, or a "Consequences" section nobody built. Each therefore needs a named
owner, a build-time gate, or a page — and by default gets none.

The guards you do write need the same scepticism you apply to results. A check
that reads the answer off the name cannot fail (`DEN5` starts with `D` and is a
sortation centre). A check that consults the mechanism it is checking is a
tautology — *"a check that shares an assumption with the thing it is checking is
not a check"* — which is why the strongest control here is a second pass that
deliberately ignores `.gitignore`. A check that resolves ambiguity by file size
validates the wrong file the day another file grows. A check whose threshold
comes from a field whose *name* and *meaning* differ has a margin of zero. And a
green suite is not a covered one: **660 tests passing** and **75 of 138 modules
unreachable from any test** were true at the same time, of the same repository,
on the same day.

The habit that ties it together is the one thing in this document that is free:
**write the defect down when you find it, at the site, with a date** — not as
design rationale. "We designed it this way" loses both the warning and the
credit, and the credit is the most valuable thing a project like this has.

*(§2.1–§2.5, §4.4, §5.1–§5.6, §6.2, §6.4, §7.7, §9.1, §9.3, §9.4.)*

---

## Where to go next

- [`ROADMAP.md`](ROADMAP.md) § *Future scope* — written for someone picking this
  up: the screening rule that says what to try, four things worth doing in order
  of expected value, and a table of what **not** to retry with the measurement
  behind each.
- [`NUMBERS.md`](NUMBERS.md) — the source of truth for any figure, plus twelve
  quantities that are routinely confused with one another.
- [`DECISION_LOG.md`](DECISION_LOG.md) §2 — every error, in the order they would
  have done damage.
- [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §10 — the corrections log for
  claims that did not survive opening the source.
- [`experiments/README.md`](../experiments/README.md) — five lines of work that
  were built, run and retired, each with what came back.
