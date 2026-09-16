# Notes — the gradient-boosted benchmark, MODEL_SPEC.md §9.4

*Built and run 2026-09-14. Artefact: `outputs/metrics/gbm_benchmark.json`.
Code: `src/siting_atlas/models/gbm_benchmark.py` (297 lines) and
`src/siting_atlas/models/gbm_report.py` (109 lines). Every number below was
read out of the artefact or printed by the runner; none is recalled.*

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes seven parts for a notes file and says
the directory holds **one file per paper**. This is not a paper. It is a
benchmark this project specified on 2026-09-13, did not build, and has now
built. It is filed here because that is where the brief asked for it, and
the seven-part structure is adapted rather than followed: there is no
citation to a PDF, no page offsets, and no verbatim quotes from an author.
Part 7 ("what I did NOT read") survives as §8, "what this does not settle",
and it is the most important section.

---

## 1. What §9.4 asked for, verbatim

> "A **gradient-boosted ranker** is fitted on the same splits, scored on the
> same rows, and reported in the same table. No causal claim attaches to it.
> ... The GBM is scored on Brier and calibration exactly like the structural
> model, not on AUC."
> — `docs/MODEL_SPEC.md` §9.4

And the reason it gave:

> "The reason is that a structural model with nothing to lose to has never
> been tested. If the GBM out-predicts the structural model, that is a
> finding: it says the `ln(beta' a)` restriction is costing predictive
> accuracy, and the size of the gap measures what invariance is worth. If the
> structural model holds its own, that is a finding too."

By 2026-09-14 the section had been annotated: *"A GBM is no longer the first
reference point the project needs; it is the second."* The raw warehousing
count had already beaten the fitted model. So the question the GBM answers is
no longer "does the structural model lose" — it does — but **why**:

```
  DATA CEILING    the four covariates do not carry the signal, and no
                  learner can do better with them
  MODEL CEILING   V = ln(beta'a) is too rigid, and a flexible learner
                  finds structure the single linear index cannot express
```

---

## 2. What was built, and the four choices §9.4 left open

LightGBM 4.7.0 `LGBMRanker`, `objective="lambdarank"`, groups = decisions,
relevance 1 for the chosen ZCTA and 0 for the rest. Four things the
specification does not say, and what was chosen. All four are also in the
module docstring.

```
  1  LIBRARY      lightgbm 4.7.0, the only gradient-boosted RANKER in the
                  venv (xgboost is not installed). lambdarank optimises
                  within-group order, which is exactly the estimand.

  2  FEATURES     the same four attraction columns the logit gets, and
                  nothing else, so the comparison isolates functional form
                  rather than data. TWO feature sets are run, because the
                  choice is not innocent -- see below.

  3  HYPERPARMS   not tuned, and NOT pre-registered either, because the
                  grid had already been run once by the time a primary
                  would have been declared. The whole grid is reported and
                  the verdict is taken on the RANGE.

  4  BRIER        a ranker emits scores on an arbitrary scale, so a Brier
                  score from them means nothing. Scores are mapped to
                  within-metro probabilities by a one-parameter softmax
                  whose temperature is fitted ON TRAINING DECISIONS ONLY,
                  by maximising the same conditional-logit likelihood the
                  structural model maximises. The map is strictly
                  increasing, so no top-k count changes under it.
```

**On choice 2, which is the one that could have rigged the answer.** The
logit's probability is a *share* of the metro total — `beta'a_j` divided by
the sum over the metro. A tree scores each alternative from its own raw
levels and cannot construct that ratio. Withholding the within-metro shares
would have handicapped the GBM and manufactured a data-ceiling verdict. So
both feature sets are run: `levels` (the four raw columns) and `shares` (the
four columns plus each one's share of its metro total). The shares are a
deterministic transform of the same columns plus the group structure the
logit already uses, so supplying them adds no information the logit lacks.

Measured outcome of that worry: **it did not matter.** `stump/200 shares`
takes 22.20 mean top-10 hits and `stump/200 levels` takes 22.26. The
precaution was right to take and changed nothing.

---

## 3. Matching the evaluation protocol exactly

This was the requirement that could most easily have been faked, so here is
the proof rather than the assurance.

```
  data          choice.build(load_national(), panel, cbp_detail,
                CBP_ATTRACTIONS) -- the identical call choice_runner makes
  decisions     94, median choice set 92, 11,715 alternatives
  split         SEED and TEST_FRACTION are IMPORTED from choice_runner,
                not re-declared. Same default_rng(20260914), same
                permutation, same cut -> 56 train / 38 test
  top-k         _top_k_hits is copied line for line from choice.evaluate,
                including the np.argsort(-score) tie-breaking
  Brier         same formula over the same rows, same uniform null
```

The check that it worked: on repeat 0, which is bit-identical to
`choice_runner`'s split, this module reproduces the published artefact
exactly — conditional logit **19/38** top-10, raw warehousing count
**20/38**, Brier 0.008724 and 0.008951. Those are the numbers in
`choice_report.json` and in [`../STATUS.md`](../STATUS.md) §2, to six decimal
places.
Nothing is being compared across different rows.

---

## 4. Why no single accuracy number is reported

38 held-out decisions. A top-10 count near 20 of 38 carries a binomial
standard error of about 3 decisions *before* any variation from which
decisions landed in the fold. A GBM fitted on 56 training groups will
overfit whatever it is given, and a single split will report whichever way
that overfit happened to fall.

So everything is measured over **50 re-splits** of the same 94 decisions,
60/40 over decisions, seeds `SEED + r`. Every method is re-fitted inside
every repeat, so the comparison is **paired**: a fold that happens to
contain easy decisions inflates all eight rows at once, and the paired
difference removes that.

How much that matters is visible in the numbers. The spread of the
conditional logit's top-10 over re-splits is 16 to 25 hits, sd 2.72 — the
published 19 sits near the bottom of its own distribution. The single
published number was not unlucky enough to be wrong, but it was one draw
from a distribution three decisions wide, and it has been quoted as a fact.

---

## 5. The result

**Headline split (repeat 0, identical to `choice_runner`), hits of 38:**

```
                          top-1   top-5  top-10       Brier
  conditional_logit           7      16      19    0.008724
  raw_count                   8      16      20    0.008951
  gbm stump/200  shares       4      18      24    0.009313
  gbm small/100  shares       3      20      23    0.009365
  gbm deep/300   shares       2      16      20    0.013116
  gbm stump/200  levels       5      18      23    0.009000
  gbm small/100  levels       4      15      23    0.009086
  gbm deep/300   levels       1      15      18    0.012781
```

On that one split the GBM looks like a clear win at top-10: 24 against 19
and 20. **Do not read that row.** It is exactly the number §4 says not to
trust, and the grid already disagrees with itself on it (18 to 24). The
artefact now carries its own `headline_split_warning` saying the same thing
with a measurement behind it: perturbing the attraction matrix by 1e-12 — far
below the precision of any input — moves the single-split GBM top-10 by up to
2 of 38 decisions, and no LightGBM determinism flag fixes it. The
`conditional_logit` (19) and `raw_count` (20) rows do not move at all. **The
GBM rows of this table are not quantities and must not be quoted.**

**Across 50 re-splits. This is the table.** Counts are of 38 held-out
decisions; `vs count` is the paired mean difference against the raw count on
the same re-split; W-L counts re-splits won and lost against it.

```
                        top-1  top-5  top-10    sd   2.5-97.5  vs count   +/-    W-L
  conditional_logit      6.70  15.44   20.60  2.72      16-25     -0.36  1.14  11-23
  raw_count              7.08  15.88   20.96  2.50      17-26     +0.00  0.00    0-0
  gbm stump/200 shares   5.54  16.34   22.20  2.70      18-28     +1.24  2.23  30-10
  gbm small/100 shares   5.90  16.42   22.14  2.81      18-28     +1.18  1.83  33-10
  gbm deep/300  shares   3.90  13.22   18.56  2.55      14-23     -2.40  2.61   7-39
  gbm stump/200 levels   5.50  16.30   22.26  2.75      18-27     +1.30  2.25  30-11
  gbm small/100 levels   5.46  16.70   22.18  2.64      17-27     +1.22  1.76  34-10
  gbm deep/300  levels   3.96  13.70   18.76  2.48      14-24     -2.20  2.67  10-36
```

**Mean Brier over the same 50 re-splits**, lower is better. This is the
project's headline proper score, not top-k:

```
  conditional_logit      0.007550     <- best of all eight
  raw_count              0.007793
  gbm stump/200 levels   0.007681
  gbm stump/200 shares   0.007839
  gbm small/100 levels   0.007782
  gbm small/100 shares   0.007863
  gbm deep/300  levels   0.010392
  gbm deep/300  shares   0.011016
```

### Four things that table says

**1. The four shallow GBMs beat the raw count on top-10, by about one
decision in 38.** Paired mean +1.18 to +1.30 hits, winning 30-34 of 50
re-splits and losing 10-11. As rates: 22.14 to 22.26 of 38 is 58.3% to 58.6%
top-10, against the raw count's 20.96 of 38 = 55.2%. A gain of **3.1 to 3.4
percentage points**. It is consistent in sign and it is real at this sample.
It is also smaller than the split-to-split spread of any single method (sd
2.5 to 2.8 hits), so a reader handed one split could not detect it.

**2. The GBM buys top-10 by selling top-1.** Every GBM configuration is
*worse* than the raw count at top-1 (5.46-5.90 against 7.08) and worse than
the conditional logit (6.70). It is worse at picking the ZIP and better at
drawing a shortlist. That is a trade, not a dominance, and both halves must
be reported.

**3. On the proper score the structural model still wins.** Mean Brier
0.007550 against the raw count's 0.007793 and the best GBM's 0.007681. The
project's own reporting rule (`MODEL_SPEC.md` §9.1, Gneiting & Raftery 2007
§3.1) makes the Brier pair the headline and top-k a thing shown "because
readers ask for it". On the headline, the conditional logit is the best of
the eight. It loses only on the metric §9.3 says is not the headline.

**4. Capacity hurts.** The two `deep/300` configurations — eight leaves,
depth 3, 300 trees — lose to the raw count by 2.2-2.4 decisions and lose
36 and 39 of 50 re-splits. Their Brier is 35-41% worse than the stumps'. At 56
training groups the sample cannot support the capacity, and a benchmark
tuned by someone who only tried the deep configuration would have reported
the opposite finding. This is why the grid is published whole.

### What the GBM actually splits on

Total split gain of the best configuration (`stump/200 levels`), fitted on
repeat 0:

```
  warehousing_establishments   53.5%
  land_area_sqmi               18.5%
  households                   14.3%
  establishments               13.7%
```

**This is the sharpest single finding in the file.** The conditional logit
drove two of those columns to the boundary — `beta_land_area_sqmi` = 3.04e-16
and `beta_establishments` = 4.72e-16, `theta` = -35.73 and -35.29, the
optimiser walking to minus infinity down a flat likelihood
(`MODEL_SPEC.md` §0.3). The logit concluded those columns were worth
nothing. The tree puts **32.2% of its total split gain on exactly those two
columns**, plus a further 14.3% on households — which the logit cannot
weight at all, because households is the numeraire fixed at 1.000. Only
53.5% of the ensemble's gain goes to the one covariate the logit kept free.

Those columns are therefore not empty. They contain structure — thresholds,
non-monotonicity, interaction with the warehousing count — that a strictly
positive additive weight inside a log cannot express. `choice.py` enforces
`beta_k = exp(theta_k) > 0`, so the logit can only say "more land area is
more attractive"; it cannot say "too much land area is a warehouse-free
exurb". When the only two things it can say are "positive" and "zero", zero
is the better of them, and the coefficient goes to the boundary.

**And that structure is worth about one decision in 38.**

---

## 6. Verdict: a data ceiling, with a measured and small model-ceiling term

The question was binary and the answer is not, so here it is with its
arithmetic.

```
  IS THERE A MODEL CEILING?   Yes, and it is measured for the first time.
      A flexible learner extracts signal from land area and establishments
      that the logit set to zero -- 32.2% of its split gain -- and converts
      it into +1.18 to +1.30 top-10 hits of 38 over the raw count.

  IS IT THE BINDING CONSTRAINT?  No.
      +1.2 to +1.3 of 38 is 3.1 to 3.4 percentage points. A linear index,
      a single raw count and a 200-tree ensemble land at 20.60, 20.96 and
      22.26 top-10 hits of 38 -- a total range of 1.66 hits against a
      within-method sd of 2.5 to 2.8. Everything is in the same place.
      That is the signature of a data ceiling.

  AND THE FLEXIBLE LEARNER IS NOT UNIFORMLY BETTER.
      It loses 1.2 hits at top-1 and loses on the Brier score, which is
      the project's declared headline. It wins on exactly one of the four
      reported quantities.
```

**So: the ceiling is the data, and `ln(beta'a)` is costing roughly one
held-out decision in thirty-eight.** Both halves are publishable. The first
is the finding; the second stops it being an overclaim, and it is the honest
answer to §9.4's question "the size of the gap measures what invariance is
worth". The gap is 3.1 to 3.4 percentage points of top-10 accuracy, bought
at 3.1 to 4.3 points of top-1 accuracy (7.08 hits down to 5.46-5.90) and a
worse Brier score.

The sentence for the write-up: *four covariates, a structural model, a
zero-parameter count and a gradient-boosted ranker all place the true ZIP in
the top ten of its metro between 55% and 58% of the time. Nothing available
to this project moves that number, and the functional form is not what is
holding it down.*

**What this rules out.** The reading that the conditional logit's failure is
an artefact of Train's aggregation-invariance restriction, and that dropping
`ln(beta'a)` for something flexible would rescue the project's predictive
claim. It would not. It would buy 3.4 points of top-10 and cost the Brier
score, the interpretability, and the whole §1 invariance argument.

---

## 7. Where this leaves the specification

`MODEL_SPEC.md` §9.4 currently reads "Still not built, 2026-09-14". That is
now false and the section needs an update. This file does **not** edit it —
the section is owned by the specification and the owner should decide the
wording — but the two facts it needs are:

```
  1  §9.4 is BUILT. src/siting_atlas/models/gbm_benchmark.py,
     outputs/metrics/gbm_benchmark.json, 50 re-splits, seed 20260914.
  2  Its own prediction -- "if the GBM out-predicts the structural model
     ... the size of the gap measures what invariance is worth" -- is
     answered: the gap is +1.18 to +1.30 top-10 hits of 38 against the raw
     count and +1.54 to +1.66 against the fitted logit, and it is NEGATIVE
     on both Brier and top-1.
```

The backlog then ranked the GBM benchmark seventh of seven pending items
with the note *"Lower value than it was: the model already has something to
lose to, and it lost."* That ranking was defensible and is now spent; the
item is done, and what it produced is the first interval this project has
ever put around a top-k number.

One correction it forces on our own documents. The status page (then
`WHERE_WE_ARE.md` §2, now [`../STATUS.md`](../STATUS.md) §2) and
`MODEL_SPEC.md` §0.3 both stated, without qualification, that a single raw
covariate **beats** the fitted model on top-1 and top-10. Over 50 re-splits
the raw count's margin is **+0.36 top-10 hits of 38 with a paired sd of
1.14**, and it loses 11 of the 50 re-splits outright. The claim is true in
direction and far weaker than the bare 20-versus-19 suggests. The honest
version is: *the raw count matches the fitted model to within a third of a
decision, so the estimation bought nothing* — which is the same conclusion,
correctly sized.

> **Update 2026-09-14, evening — this correction has landed, and it went
> further than the two documents named above.** The status page and
> `MODEL_SPEC.md` §0.3 now say **MATCHES**, each with a dated block recording
> that they said "beats". A sweep the same evening found the "beats" claim in
> roughly two dozen more documents — the defense handbooks, the ADRs,
> `PROPOSAL_V5.md`, the career files, and the four status documents since
> merged into [`../STATUS.md`](../STATUS.md), plus
> `ALTERNATIVES.md` — several of them carrying an explicit
> instruction to *"say 'beats', not 'matches'"*. All are corrected and the
> instruction is inverted rather than deleted. **This paragraph is where that
> correction started**, and the numbers in it are the ones every one of those
> blocks cites: `outputs/metrics/gbm_benchmark.json`,
> `across_repeats.conditional_logit` — `vs_raw_count_mean` -0.36,
> `vs_raw_count_sd` 1.1386, `vs_raw_count_wins` 11 of 50, 23 losses, 16 ties.
> The negative conclusion is unchanged.

---

## 8. What this does NOT settle, and what would change the verdict

Ranked by how much each would move the answer.

**1. The warehousing covariate may be contaminated, and all eight rows ride
on it.** [`../STATUS.md`](../STATUS.md) §2, "The covariate-leakage test",
records the defect: `open_year` is the
OSHA inspection quarter, not an opening date, for 100 of 100 matched
national rows, and `ingest/cbp_detail.py` lags the CBP vintage off that
upper bound with margin zero. An Amazon delivery station **is** a
warehousing establishment. This benchmark measures that the GBM gives that
column 53.5% of its split gain. If the column contains the outcome, then all
three of the numbers in §5 are inflated by the same leak and the comparison
between them survives while the *level* does not. **This is the caveat most
likely to change the verdict**, and nothing here tests it. The test is
cheap: re-run with `CBP_ATTRACTIONS` empty and see where all three methods
land on three covariates.

**2. The data ceiling is a ceiling on FOUR COLUMNS, not on the question.**
Households, land area, establishments, warehousing establishments. Rent,
wages, permits, and every distance covariate are not joined to the national
frame ([`../STATUS.md`](../STATUS.md) §3 blocker 3), and the facilities are
ungeocoded in the panel (blocker 4). A GBM with a distance-to-nearest-existing-station feature is
untested and is the obvious next experiment. "No learner can do better with
these four columns" is what was measured; "no learner can predict Amazon
siting" is not, and the two must not be conflated.

**3. The splits are not clustered by metro.** Six of the 94 decisions are in
Los Angeles and share a choice set (`MODEL_SPEC.md` §6.3). Random splits over
decisions put correlated decisions on both sides, which inflates every
method's apparent accuracy. This was matched to `choice_runner` deliberately
— an unclustered comparison against an unclustered baseline is still a fair
comparison — but the absolute levels are optimistic for all eight rows.
`choice_inference.py` already clusters its bootstrap over metros; this does
not.

**4. The 50 re-splits are not independent.** They resample the same 94
decisions, so the reported sd understates the true sampling variability and
the W-L records must not be read as a sign test. There is no p-value in this
file and there should not be one.

**5. The hyperparameter grid is three configurations wide.** A wider search
could find something better. Two observations against that worry: the deep
configuration is the *worst* of the three, so the binding constraint is
sample size and not search effort; and any configuration selected by
performance on these same 50 re-splits would be selected on the test data,
which is the error this whole file exists to avoid.

**6. Top-10 is partly free.** The smallest choice set in the frame has 9
alternatives, so top-10 is a certain hit there for every method including the
uniform null. The artefact records this; it inflates all eight rows equally
and does not affect the comparison.

**7. Calibration is not reported, and §9.4 asked for it.** The module
computes what `choice.evaluate` computes — Brier, the uniform-null Brier,
mean probability of the chosen alternative, and top-k — because "exactly like
the structural model" was read as "the fields the structural model emits".
`choice.evaluate` does not emit an ECE, so neither does this. `MODEL_SPEC.md`
§9.2's reporting table has an ECE row and **neither model fills it.** That is
a gap in both, and it predates this work.

---

## 9. How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.models.gbm_benchmark
```

Roughly 75 seconds for the 50 re-splits on one core. Writes
`outputs/metrics/gbm_benchmark.json` and prints the table in §5. Requires
`data/interim/cbp_detail.parquet`; the runner raises `FileNotFoundError`
naming the ingest command rather than quietly fitting three covariates and
producing a number that is not comparable to the published one.
