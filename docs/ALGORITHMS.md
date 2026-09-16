# Algorithms — every estimator in this project, plainly then precisely

*Written 2026-09-15. Each section explains what the method is to a reader who knows no
econometrics, then states it exactly, then names the file that implements it and the
notes that justify it.* [`NUMBERS.md`](NUMBERS.md) is the tie-breaker on any figure.
**No `TODO` marker exists anywhere in `src/`** — every known defect in this codebase is
written out as prose in a docstring, and the ones that matter are quoted below.
Companion: [`EXPERIMENTS.md`](EXPERIMENTS.md), what each was used for and how it scored.

| § | Algorithm | Implemented in | Justified in |
|---|---|---|---|
| [1](#a1) | Conditional logit, `V = ln(β′a)` | `models/choice.py` | `MODEL_SPEC.md` §§1–6; `NOTES_train_ch03_logit.md` |
| [2](#a2) | Positivity reparameterisation `β = exp(θ)` | `models/choice.py:246` | cost measured in `NOTES_LOG_RELATIVE.md` |
| [3](#a3) | Bootstrap over decisions and over metros | `models/choice_bootstrap.py` | `METHODS_RESEARCH.md` §5.10; Train §8.6 |
| [4](#a4) | Huber–White sandwich, with a refusal | `models/choice_sandwich.py` | `MODEL_SPEC.md` §6.3 |
| [5](#a5) | Why a re-split percentile is not a standard error | `models/metro_resample.py:6-14` | `PREREG_METRO_MODEL.md` §6 |
| [6](#a6) | Split conformal — adaptive prediction sets | `models/choice_conformal.py`, `conformal.py` | refused in `MODEL_SPEC.md` §7.1, then built |
| [7](#a7) | Gradient-boosted trees (LightGBM lambdarank) | `models/gbm_benchmark.py`, `covariate_gbm.py` | `MODEL_SPEC.md` §9.4 |
| [8](#a8) | Discrete-time survival, cloglog link | `experiments/hazard-model/code/hazard.py`, `models/risk_set.py` | **nowhere — see §8** |
| [9](#a9) | Daganzo continuous approximation | `cost/daganzo.py`, `cost/params.py` | `NOTES_daganzo_1984.md` — **read the caveat** |
| [10](#a10) | p-median depot solve | `cost/depots.py` | `NOTES_klose_drexl_2005.md`, `NOTES_hakimi_1964.md` |
| [11](#a11) | Fellegi–Sunter linkage + Jaro–Winkler | `common/linkage.py`, `linkage_group.py`, `address.py` | `NOTES_winkler_rr99_01.md`; `METHODS_RESEARCH.md` §7 |
| [12](#a12) | Fellegi–Holt edit systems | `warehouse/edits.py`, `facility_dedup.py` | `NOTES_fellegi_holt_1976.md` |
| [13](#a13) | OCR table geometry | `ingest/mwpvl_grid.py`, `tools/ocr/*` | `data/MWPVL_OCR_PIPELINE.md` |
| [14](#a14) | Scoring — lift, Brier, AUC, ECE, splits | `models/panel_strata.py`, `metrics.py`, `splits.py` | `NOTES_gneiting_raftery_2007.md` |

<a id="a1"></a>
## 1. The conditional logit — the project's main model

**Plainly.** Amazon opens one delivery station in Chicago; Chicago has ~200 candidate ZIP
codes. Which one? A conditional logit answers exactly that shape of question: give every
option a score, and the probability it is chosen is its share of all the scores in that
set. If a ZIP holds 10% of Chicago's total score, it has a 10% chance. Two things make it
the right tool rather than a regression. **One opening is one observation** — which is
exactly what killed the model it replaced (§8) — and it never has to say *how many*
stations will open, only which one given that one does. That is the question the data can
answer.

**Precisely.** Utility `V_j = ln(β′a_j)`, where `a_j` is the vector of *attraction*
variables. Substituting collapses the exponentials exactly:

```
    P(j | m) = exp(V_j) / Σ_k exp(V_k) = (β′a_j) / Σ_k (β′a_k)
```

— the alternative's **share of the choice set's total attraction**. That form is forced,
not chosen for convenience: **Train (2009) §3.4 Example 2, printed p. 54** shows that
invariance to how the Census drew zone boundaries requires `exp(V)` to be additive under a
merge, which holds only for **extensive** attractions — counts that add. `choice.py:63-65`
warns that medians, rates and densities break it; three experiments paid that price
deliberately and said so ([`EXPERIMENTS.md`](EXPERIMENTS.md) §§5, 7, 15).

Multiplying every β by a constant leaves every probability unchanged, so only *ratios* are
identified. `households` is pinned at 1.0 (`NUMERAIRE`, `choice.py:70`). Consequence that
must travel with every coefficient: **the null that matters is β = 1, not β = 0** — β = 1
means the covariate is worth exactly one household and the model cannot tell them apart.
`choice_inference.py` prints no zero test anywhere, deliberately. The likelihood is one
term per decision, `-Σ log(max(p[chosen], 1e-300))`; the independence assumption behind
that product is **Train §3.7.1, printed p. 61** — *not* §2.2, and getting that wrong is
logged as the largest citation error in the project (`METHODS_RESEARCH.md` §10, §14.2).

The optimiser runs **five starts, each BFGS then Nelder-Mead** ("Nelder-Mead after BFGS
because at two parameters it costs nothing and guards against a bad gradient at the
boundary"). Multiple starts are mandatory: McFadden's global concavity result holds only
for utility **linear in parameters**, and `ln(β′a)` is not. Two guards, each added after a
real failure — a NaN from the *first* start could never be displaced by `r.fun < best.fun`
and `fit` returned an all-NaN β looking normal (`choice.py:271-295`), and the positivity
guard of §2. Build-time: a facility whose own ZCTA is missing from its choice set is
**dropped**, not given a set excluding the observed choice; CBP counts are lagged
**strictly per decision**, because an Amazon delivery station is itself a warehousing
establishment.

**How it performed.** `combined` arm, 483 decisions: large-metro top-10 lift **6.2585**,
pooled top-10 rate 0.5196, Brier 0.0050363 — **the best Brier of any method tested**,
including every GBM configuration. It is also effectively a one-variable model:
`land_area_sqmi` is at the boundary in 50 of 50 re-splits, and removing
`warehousing_establishments` collapses the large-metro top-10 rate from 30.473% to
13.132%. Under a metro-clustered bootstrap **no coefficient is distinguishable from the
numeraire**. `MODEL_SPEC.md` §0.3 records where the fit departs from the written spec: the
parameter set gained `warehousing_establishments`, the two-period design was never built,
and the standard errors were built **better** than specified.

<a id="a2"></a>
## 2. `β = exp(θ)` — the positivity reparameterisation, and what it costs

**Plainly.** The scores must be positive: a share of a negative total is not a probability.
The simplest guarantee is to estimate the *logarithm* of each weight and exponentiate.
The price is that **the model cannot express a variable that repels** — if high house
prices make a site less attractive, the best this form can do is set the weight to zero.
That is a real restriction, and it is reported rather than hidden.

**Precisely.** `beta = np.concatenate([[1.0], np.exp(theta)])` (`choice.py:246`). A
discarded column walks θ towards −∞ and lands at β ≈ 1e-15. `BOUNDARY_TOL = 1e-6`
(`choice_sandwich.py:43`); the fitted values are ~3e-16, "so nothing depends on where
between 1e-16 and 1e-4 the line is drawn".

**"At the boundary" is a rule, not a fact, and the rule must always be named.** Two are in
use and they disagree on the same column. The *percentile* rule (`gravity_report.verdicts`)
asks whether a column's 2.5th percentile over 50 re-splits clears the tolerance; the
*point-estimate* rule (`network_inference.json`) asks whether the full-sample β does. Under
the first, `sortation_proximity` is "boundary inside the interval"; under the second it is
`at_boundary: false` (β = 0.097, 3.8% of bootstrap replicates at zero). Both current, both
right under their own rule.

**The failure mode the guard exists for.** The claim that `exp` *enforces* `β′a > 0` holds
only while every attraction column is non-negative. Add a centred or log-relative column
and a **positive coefficient on a negative column subtracts attraction**. Measured on the
log-relative arms: the optimiser went **19.6× to 77.2× past the feasibility ceiling**,
pushing 765 to 4 816 non-chosen alternatives below zero. Because the chosen alternative was
never one of them, this *shrank the denominator* and inflated `P(chosen)` from 0.078685 to
0.079346 — up to **+1.20** log-likelihood across 479 decisions, bought with arithmetic
rather than information, with nothing complaining. `choice.py:299-334` now raises, with the
remedy in the message: *"Enter such a covariate through a separate unconstrained linear
index, not inside `ln(beta'a)`."* The comment states that the non-finite-start guard does
**not** catch this, because an infeasible optimum has a perfectly finite log-likelihood.
The minimal fix — `V_j = ln(β′a_j) + γ′z_j` with γ unconstrained, the standard "size
variable plus linear index" form — is described and deliberately not implemented.

<a id="a3"></a>
## 3. The bootstrap — over decisions, and over metros

**Plainly.** We have 56 training decisions. How much would the answer change with a
different 56? Draw 56 from the 56 you have *with replacement*, refit, repeat a thousand
times; the spread approximates it. The critical choice is **what you draw**: whole
decisions, never individual ZIP codes — a metro's 200 ZIPs are not 200 independent things,
and a resample scattering them across replicates, possibly without the chosen one, would be
a draw from nothing.

**Precisely.** `models/choice_bootstrap.py`. Resampling unit: the **decision**, never an
alternative, with a cross-reference to `adr/0004` for the same error one level up in the
hazard model. `resample_decisions` deliberately avoids `ChoiceData.subset`, because a
decision drawn twice would collapse to one — "a draw WITHOUT replacement, understating the
spread, which is the flattering direction".

**Two bootstraps side by side**, per `MODEL_SPEC.md` §6.3, "on the grounds that a
disagreement is itself a finding about how little the sample constrains the model": 1 000
replicates over decisions, 1 500 over **metro clusters**. *Where they differ, the bootstrap
over metros is the conservative one and the one to quote.* Metro membership is recovered
from the choice sets themselves — the key is `(choice-set size, numeraire total to 6dp)` —
and verified against real CBSA codes in `tests/unit/test_choice_inference.py`.

Stopping is adaptive: batches of 250, minimum 500, ceiling 4 000, halting when for every
interior parameter the interval endpoint **nearest 1.0** has a Monte Carlo standard error
under 1% of the interval width *and* under one tenth of its distance from 1.0 — so Monte
Carlo noise cannot flip the verdict. The MCSE is a bootstrap-of-the-bootstrap (resample the
replicates 400 times, take the sd of the percentile), needing no refits. **The far endpoint
is measured and deliberately not chased**: a ratio has a heavy right tail here, so the
97.5th percentile "would need of the order of 100 000 replicates to settle and would still
be the 97.5th percentile of 56 decisions".

Interior parameters get a two-sided percentile interval plus BCa. **Boundary parameters get
a one-sided interval** — lower fixed at 0, all of α in the upper tail — because at the
boundary the sampling distribution has an atom at zero and a two-sided interval would be a
fiction; `share_of_replicates_at_boundary` is reported beside it (0.807 and 0.790 for the
two dead columns). BCa is refused there: with replicates pinned at zero the jackknife
acceleration estimates nothing.

**The caveat is written into the artefact, not a footnote.** `inference.train_precondition`
quotes Train §8.6 p. 202 in full, then: *"At 56 decisions that italicised precondition is
exactly what is in doubt. These intervals measure how much the estimate moves with WHICH OF
OUR 56 decisions are included… It is not a licence to read them as sampling variability
over the population of siting decisions."* **Status:** built on the 104-row panel only
(`choice_report.json`, `run_id 20260916-015437-7e89`); **inference on the 693-row panel
does not exist** ([`STATUS.md`](STATUS.md) §3).

<a id="a4"></a>
## 4. The sandwich estimator, and the refusal

**Plainly.** A sandwich standard error is the robust one: honest about wobble even if the
model's shape is wrong. It also assumes the fit landed at a proper peak, where the slope of
the likelihood is zero. Two of this model's three coefficients did not land at a peak —
they walked off the edge of the allowed region and stopped at the fence. At a fence the
slope is not zero, so the formula still returns a number and the number means nothing.
**The code refuses to print it.**

**Precisely.** Huber–White `H⁻¹ W H⁻¹` (Train §8.6, p. 201), with `W = S′S` the outer
product of **per-decision** scores — "which is what makes the clustering right by
construction: each decision contributes exactly one term to the log-likelihood, so there is
no within-cluster correlation left to correct for". Derivatives are **analytic**, because
"finite-differencing a log-likelihood that is flat to machine precision in two of its three
directions returns noise". With `u_j = β′a_j`, `U_n = Σ_j u_j`, `S_nk = Σ_j a_jk`, chosen
row *c*:

```
    ∂lnP_n/∂θ_k = β_k ( a_ck/u_c  −  S_nk/U_n )
```

The `β_k` factor from the reparameterisation leaves a term on the Hessian diagonal. Tests
are against **β = 1**, formed in θ and exponentiated — exact for a monotone transform, and
it keeps β positive.

**The refusal**, verbatim in `REFUSAL`: β = 0 requires θ → −∞, so the maximum is not
interior, the gradient does not vanish, and the Hessian block is not the information
matrix. "The number the formula returns is not a *wide* standard error — it is an arbitrary
one, whose size is set by how far the optimiser happened to wander before it stopped."
Those parameters get `{"available": false, "reason": REFUSAL}`. A second-order caveat is
recorded and **not** resolved: the interior block is itself conditional on the other two
being exactly zero rather than estimated at zero, and inference after boundary selection is
an open problem — surfaced as `conditional_on_boundary_selection`. Andrews (1999) is named
"as a lead to follow rather than as support".

<a id="a5"></a>
## 5. Why a percentile spread across re-splits is **not** a standard error

**Plainly.** Take one fixed set of 483 decisions, split it 60/40 fifty different ways, and
look at the spread. That tells you how sensitive the answer is to *which decisions you held
out*. It tells you nothing about what would happen with a different 483 — and that is what
a standard error answers. The two are not close, and the direction is not even fixed.

**Precisely.** The canonical statement is `PREREG_METRO_MODEL.md` §6 (**sealed — cite it,
never edit it**): *"A percentile spread across re-splits is not a standard error."* It is
enforced at `models/metro_resample.py:6-14`, which routes the quotable interval to a
metro-clustered bootstrap and stamps the emitted JSON with `"note": "spread across
re-splits, NOT a standard error (prereg section 6)"`. Three measurements of the gap, in
both directions: `COVARIATES_TRIED.md` finds a metro-clustered interval **5% wider** than
the re-split spread *despite being fitted on 483 decisions rather than 290*;
`PREREG_METRO_MODEL.md` §6 cites a clustered bootstrap **24–28% wider** on
`network_inference.json`; and `NOTES_METRO_ENTRY.md` §7 measures the opposite on the metro
problem — the re-split spread is **31% wider**, because the re-splits refit fifty times and
so include estimation variability the bootstrap conditions away. **The rule holds
universally; the direction is problem-specific and must not be carried forward.**

Every `[2.5, 97.5]` bracket in `gravity_network.json`, `panel_experiments.json`,
`metro_entry.json`, `refit_expanded.json`, `covariate_search.json`, `percapita_search.json`
and `logrel_search.json` is one of these, and the artefacts say so in their own
`spread_is_not_a_standard_error` / `interval_note` fields. **Any document that writes
"95% CI" for one of them is wrong.** A related trap from `MODEL_SPEC.md` §9.4: a top-10
count near 20 of 38 carries a **binomial standard error of about 3 decisions before any
split variation at all**.

<a id="a6"></a>
## 6. Split conformal prediction — adaptive prediction sets

**Plainly.** Instead of naming one ZIP, name a *set* and promise the true answer is in it
90% of the time. Hold out decisions the model never saw, measure how surprised it was by
each true answer, and cut at the 90th percentile of that surprise. The promise is honest
but modest: 90% **on average over decisions**, not 90% in Chicago specifically. The useful
output is the **size** of the set — 12 ZIPs out of 848 is a real narrowing; 400 out of 848
is a shrug with a confidence level attached.

**Precisely.** Still present and wired in: `models/choice_conformal.py`, imported by
`choice_runner.py:33` and emitted into `choice_report.json`. (`SplitConformalBinary` in
`conformal.py` also exists but is off the live path; only `conformal_quantile` is shared.)

**The score is Adaptive Prediction Sets**, not the naive `1 − p̂(true)`: the nonconformity
score is the **cumulative predicted probability, in descending order, up to and including
the true choice**, and the set takes alternatives in descending probability until the
cumulative mass reaches `q̂`. The reason: choice sets run from **4 to 848 ZCTAs**, so one
threshold on `1 − p̂` "would return two ZIPs in a small metro and several hundred in New
York". APS makes set size itself the statement of how much the model knows about that
metro.

The quantile is `k = ceil((n+1)(1−α))`, returned as an **order statistic**. Both details
are documented as breaking the method in a different direction: the `n + 1` is the proof's
treatment of the test point as one more exchangeable draw, and using `n` undercovers by
≈1/n, "invisible at n = 10 000 and fatal at n = 50"; and `np.quantile(..., method="higher")`
interpolates on an `(n−1)` grid, which is conservative, so "it never shows up as a failed
coverage check, only as sets that are quietly less useful than they should be". `k > n`
returns `inf` — "Returning a finite quantile there would fake a guarantee."

**Measured.** `choice_report.json` `conformal`, split 47 train / 23 calibrate / **24 test**:
α = 0.10 → empirical coverage 100.0%, median set 38.5 (71.4% of the choice set);
α = 0.20 → 95.8%, 34.0 (61.7%); α = 0.30 → 83.3%, 18.5 (34.0%). Coverage holds and
overshoots; the sets are wide, which is the honest reading of a model whose top-10 rate is
~0.52. Two caveats the code volunteers: coverage is **marginal, not conditional** ("a
promise of '90% in Chicago specifically' is not on offer and is not made"), and decisions
are split at random rather than by date, so with 94 decisions spanning 2018–2026
exchangeability "is a live risk and it is reported rather than assumed away". The
clustering measurement that motivates a tolerance band rather than a bare number: 40
replications at nominal 90% give mean 89.9% sd 0.45 pp splitting **by row**, and mean 89.8%
sd **1.66 pp** splitting **by unit** — the centre intact, the spread 3.7× wider.
`MODEL_SPEC.md` §7.1 originally **refused** conformal on sample-size grounds; it was built
anyway, and 24 test decisions is why the coverage column moves in whole-decision jumps.

<a id="a7"></a>
## 7. Gradient-boosted trees — the atheoretical benchmark

**Plainly.** A gradient-boosted tree ensemble builds hundreds of tiny decision trees, each
correcting the last one's mistakes, with no theory in it. It is here to referee: if a model
with no assumptions does much better, the structural model's *shape* is the problem; if it
does about the same, the **data** is the ceiling.

**Precisely.** LightGBM 4.7.0 `LGBMRanker`, `objective="lambdarank"`, `label_gain=[0,1]`,
`n_jobs=1`, groups = decisions, relevance 1 for the chosen ZCTA. Chosen because "it is the
only gradient-boosted *ranker* in the venv and lambdarank optimises within-group order,
which is the estimand". Six arms **reported in full and never collapsed to a winner** —
stump (2 leaves / depth 1 / 200 trees / lr 0.10), small (4/2/100/0.05), deep
(8/3/300/0.05), each on `levels` and on `shares`. The `shares` set adds each column's share
of its metro total, because "a tree scores each alternative from its own raw levels,
whereas the logit's probability is a SHARE of the metro total. Withholding the shares would
handicap the GBM and manufacture a data-ceiling verdict." Hyperparameters are **not tuned
and not pre-registered** — the grid had already been run once — "instead the whole grid is
reported with its intervals and the verdict is taken on the RANGE".

A ranker's scale is arbitrary, so scores map to within-metro probabilities through a
**one-parameter softmax whose temperature is fitted on training decisions only**, by
maximising the same conditional-logit likelihood. Strictly increasing, so no top-k count
changes; it exists only to make a Brier score meaningful. `covariate_gbm.py` reuses the
identical learner by importing `gbm_benchmark`'s privates — "a copy would drift the moment
either file was touched, and a drifted copy would be a comparison of two learners wearing
one name" — and drops the two deep arms; its `covariate_gbm.json` **was never written**
(the stage reached 45 of 50 re-splits and the emitter writes only at the end).

**How it performed** ([`EXPERIMENTS.md`](EXPERIMENTS.md) §10): a **data ceiling with a
measured, small model-ceiling term.** The tree takes 32.2% of its split gain from the two
columns the logit drove to the boundary, worth +1.30 top-10 hits of 38 over a zero-parameter
count — and it loses top-1 by 1.2–1.6 hits and loses the Brier. One of four quantities, and
the edge vanishes at 483 decisions.

**`gbm_benchmark.json:headline_split` is not a quantity.** Perturbing the attraction matrix
by `(1 + 1e-12 × standard normal)` moves the single-split GBM top-10 by up to 2 of 38, while
the conditional logit and the raw count do not move at all in any draw.
`deterministic=True, force_row_wise=True` were tested against every arm and returned
**bit-identical counts in all eight comparisons** — the call was already reproducible on
identical input; the sensitivity is to the *data*, through LightGBM's histogram bin
boundaries, and setting the flags anyway "would cost a re-emit of published numbers and buy
a false sense of a fix".

<a id="a8"></a>
## 8. Discrete-time survival with a complementary log-log link

**Plainly.** Survival analysis asks "has the event happened yet, and what is the chance it
happens now?" — the same mathematics as "will this patient relapse". Here the unit was a
ZIP code and a quarter. Quarters are a bookkeeping convenience; the real decision happens
on some particular day, and the **complementary log-log** link is what you get when a
smooth continuous-time process is observed in buckets. Its payoff is that the coefficients
mean the same thing whether you bucket by quarter or by month.

**Precisely.** `hazard.py`, class `DiscreteTimeHazard`, name `"cloglog-hazard"`:
`sm.families.Binomial(link=sm.families.links.CLogLog())`, i.e.

```
    P(event in quarter t | not yet) = 1 − exp(−exp(α_t + x′β))
```

predicted with `-np.expm1(-np.exp(np.clip(eta, -50, 50)))` for precision at small hazards.
β is a **log hazard ratio**, invariant to the time bucket: "Re-cut the panel into months
and the cloglog betas are unchanged in expectation; the logit betas are not." Honestly
quantified in the same docstring: at a 2% quarterly hazard the two agree to about 1%.

**Justification gap, stated plainly: nothing in `docs/` justifies the cloglog choice from a
source.** Neither `METHODS_RESEARCH.md` nor `MODEL_SPEC.md` cites Prentice–Gloeckler,
Allison or Jenkins. The reasoning above is the code's own — good reasoning, but unsourced.
The model appears in both documents only as the *retired* model being diagnosed.

**The risk set** (`models/risk_set.py`) is where most of the correctness lives: a unit
contributes rows for every quarter it was at risk and not one more, and enablement is
absorbing. Four details, each with a measured failure behind it. The time origin is the
earliest **year-quarter pair**, not the earliest year — otherwise a panel opening 2018Q3
starts the clock at 2, "asserting two quarters of exposure that were never observed".
**NULL is not False**: parsing goes through `truthy.as_boolean`, "because a CSV has no
boolean type: the text 'false' is a non-empty string and `astype(bool)` calls it True". The
event flag is **re-derived from the truncation** rather than trusted, which is what makes
the STATE and EVENT encodings produce an identical risk set. And left truncation drops both
the ambiguous units **and the whole of t = 0**; the half fix is documented as worse than
either whole one — dropping only the units left t = 0 with structurally zero events, "the
spline bent down to meet the hole, and the reported baseline came out ~30% low at the start
of the window". `validate_risk_set` runs before every fit: no unit with more than one event,
no unit with a row after its event — "every one of those rows is a fabricated non-event and
will bias every coefficient toward zero".

**The assumption it broke.** Clustered robust standard errors default to clustering on the
**ZCTA**, which the docstring itself calls wrong for a facility panel "where one delivery
station flips every ZCTA within fifteen miles in the same quarter: those are one draw, not
eighty"; the runner reports both ZCTA- and CBSA-clustered and warns below 30 clusters. None
of that repairs the violation, because the unit of decision is the **building**.
`hazard_revival.json:independence_violation`: *"Every standard error in this file is wrong
in that known direction."* Two smaller things worth keeping: an events-per-parameter guard
warns below ten, and `baseline_hazard()` is reported at the average **unit**, not the
average row, because a row mean "is a description of the survivors… That published this
curve **13% low at every quarter**."

**Status.** Retired and quarantined: `experiments/hazard-model/code/` has no `__init__.py`
while `hazard.py` still uses package-relative imports, so **the hazard model is not
importable where it now sits**. Interval censoring remains unimplemented, so the 139
OSHA-dated facilities enter as exact event times when they are upper bounds. Results:
[`EXPERIMENTS.md`](EXPERIMENTS.md) §13.

<a id="a9"></a>
## 9. Daganzo's continuous approximation — and a caveat that must travel with it

> **Read this before quoting anything in this section.**
>
> **[`research/NOTES_daganzo_1984.md`](research/NOTES_daganzo_1984.md) states in its own
> first line that the paper was never read and is not on disk.** It is the explicit
> exception to that directory's one-file-per-paper-read rule; there is not one page number,
> section number or quotation from Daganzo anywhere in it.
>
> **One of the two citations behind the cost model's central constant is a different author
> entirely.** `REFERENCES.md` §2 and `cost/params.py:47-49` cite *"Daganzo, C. F. (1984),
> Approximate formulas for average distances associated with zones, Transportation Science
> 18(3), 231-253"* as "the companion paper, and the source of the zone-geometry constants of
> which `bhh_constant = 0.57` is one". **That DOI belongs to R. J. Vaughan**, the pages are
> 231–244, and the paper is about average distances between random points in zones — not
> tour lengths, not constants, not Daganzo. Verified against OpenAlex twice, independently.
>
> The paper that probably *is* the source — Daganzo (1984), *The length of tours in zones of
> different shapes*, Transportation Research Part B 18(2), 135–145 — is **not cited at
> all**. And the one corroborating source that *was* retrieved and read in full, Larson &
> Odoni's *Urban Operations Research* §6.4.8, gives the constant as **K ≈ 0.765**, not 0.57.
>
> `bhh_constant = 0.57` may well be right. What is established is that **the derivation
> printed in `cost/daganzo.py:16-19` is not consistent with it**, and no retrievable source
> in this repository supports it. The notes file carries a numbered checklist of what must
> be checked against the original. Do not launder this.

**Plainly.** Nobody publishes what it costs Amazon to deliver one parcel to one ZIP, so it
is computed from geography. A van drives out, makes many stops, and drives back. If houses
are packed close the driver spends most of the time at doors; if spread out, the reverse. So
cost per parcel falls as density rises — as **one over the square root of density**. You
never route a single van; you approximate what a good route would cost from two numbers,
depot distance and stop density.

**Precisely.** `cost/daganzo.py`, `distance_per_stop`:

```
    d_stop = 2·L / C  +  k / sqrt(δ)
```

L = depot-to-zone distance, C = stops per tour, δ = stops per square mile, k = the BHH
constant. Derivation given in-file from Beardwood–Halton–Hammersley (1959): a tour through
*n* random points in area *A* has length ≈ `k·sqrt(nA)`; one van covering C stops works an
area `C/δ`, so local distance is `k·C/sqrt(δ)`, i.e. `k/sqrt(δ)` per stop. Circuity
multiplies the **local** term only — line haul is already inflated inside `linehaul_miles`,
and the 25-mile fallback deliberately is not, because "inflating it too turned the
documented 25-mile default into 32.5". Cost per stop is four additive terms — distance,
drive time, service time, vehicle lease ÷ stops per tour — divided by 1.4 parcels per stop.

**`cost/params.py` is the honest part.** Every constant is tagged SOURCE / ESTIMATE /
DISAGREES with its measured sensitivity, and the framing sentence is the one to quote:
*"the routing mathematics this module is named after is **DECORATION** (the BHH constant
moves the median 1.9% when wrong by half) while the unsourced labour and consolidation
assumptions carry the headline."* Confirmed by the decomposition — service time **66.96%**,
vehicle 22.93%, drive time 6.97%, distance 3.14%. The largest known error has its own
heading, **"DISAGREES WITH THE SOURCE OF ITS OWN INPUT"**: `labour_usd_per_hour` divides by
`9 × 6 × 52 = 2 808` hours, conflating how many days a week the *network* delivers with how
many hours a year one *driver* works; BLS OEWS builds the annual mean from 2 080, so this
recovers an hourly rate ~26% below the one BLS measured. Measured: the 2 080 denominator
moves the median $1.0875 → $1.3704, **+26.0%**, or +33.6% with the wage-loading correction.
**Not applied, because it changes the project's headline and that is the owner's call.**
`vans_required` carries an explicit prohibition: it **must not be summed across ZCTAs** —
2 333 per-ZCTA ceilings give 79 484 against the reported 78 292.

<a id="a10"></a>
## 10. The p-median depot solve

**Plainly.** Given a metro's ZIP codes and their parcel demand, where should depots go? The
**p-median** problem picks *p* locations minimising total demand-weighted distance. The
obvious shortcut — k-means — is **wrong here, and measurably so**: k-means minimises
*squared* distance and lands on the weighted **mean**, while this cost model bills line haul
linearly and the minimiser of weighted linear distance is the weighted **median**. 60
parcels at mile 0 and 40 at mile 50 gives the mean (mile 20) 2 400 parcel-miles and the
median (mile 0) 2 000. Across the pilot, switching removed **9.3% of billed parcel-miles**
and moved the ZCTA ranking by Spearman ρ 0.888.

**Precisely.** `cost/depots.py`, `solve_pmedian`, Klose & Drexl (2004) §4 eq. (1a)–(1e).
Candidates are **ZCTA internal points**, "so a depot always stands on a row of the panel
rather than on invented coordinates in an empty field" — Hakimi's node-optimality theorem
is the obvious citation, and `NOTES_hakimi_1964.md` records that it **does not license what
was claimed**; the node restriction is defended by a measured 0.45% instead.

Heuristic, two phases, because the exact problem is NP-hard and the largest pilot metro
reaches n = 848, p = 109. **Greedy add**, O(p·n²), scored as *"objective after opening j"*
rather than *"gain from opening j"* so no infinity is ever multiplied. Then **Teitz–Bart
vertex substitution**, tracking both nearest and **second**-nearest open site (closing one
sends its nodes to their second-nearest; without it each swap would need a recomputed row
minimum and the sweep would cost O(p·n³)). **Every improving swap is applied, not only the
best per pass** — with one swap per pass the largest metro hit the cap 3.5% above the bound
instead of 0.6%. The improvement threshold is strictly positive, because "float noise can
manufacture a gain of 1e-13 for ever". `MAX_INTERCHANGE_PASSES = 12`, "a guard, not a knob".

**Quality, stated honestly.** On termination the solution is a **1-opt local optimum** — "a
statement about the neighbourhood searched, not a ratio against the true optimum, and vertex
substitution has no constant-factor bound on the metric p-median". Over 150 enumerable
instances: exact on 139, mean gap 0.27%, worst 11.0% (all at small p, pinned in tests). On
the pilot it lands within **0.89% of a valid Lagrangean lower bound**. Deterministic by
construction. Depot count is `K = ceil(metro daily parcels / 40 000)`, summed over the 10
pilot metros = **334**; the 329 in `params.py:220` is one *national* division, both are
derivable, and `NUMBERS.md` §10 resolves it.

**The capacity caveat, quoted because it is a giving-up.** "We do not solve [the
capacitated problem]. We impose capacity only in the AGGREGATE… So a single depot can be
assigned more than its throughput while a neighbour sits idle; **the line haul reported here
is therefore a LOWER BOUND** on that of a capacity-feasible network." Measured consequence:
42% of depots exceed 40 000 parcels/day under nearest-depot assignment, heaviest 3.56× — and
the bias is optimistic in exactly the dense ZCTAs at the top of the ranking.

<a id="a11"></a>
## 11. Record linkage — Fellegi–Sunter, Jaro–Winkler, and a deliberate omission

**Plainly.** Two files list the same building and spell it differently: `1555 CHRISMAN RD`
and `1555 N CHRISMAN ROAD`. The standard method scores each pair on how surprising its
pattern of agreements would be if the records matched versus if they did not, then applies a
**three-way** rule: above a high threshold match, below a low one non-match, **in between
send it to a human**. That middle band is the point — a wrong merge deletes a building, and
a building that disappears is never noticed. For text, **Jaro–Winkler** scores shared
characters and transpositions with a bonus for an agreeing prefix, because typing errors get
likelier further right.

**Precisely.** `common/linkage.py`. **The decision rule is implemented; the likelihood ratio
deliberately is not**, and the reasons come from Winkler RR99-04 rather than convenience.
§3.1: frequency weighting is "seriously compromised" for lists with records that fail
standardisation and have high typographical error rates — free-text addresses typed by OSHA
inspectors are exactly that list. §3.1 positively: redundancy across many fields substitutes
for it, and there are seven here. §3.4: the only automatic error-rate estimator the paper
knows is Belin & Rubin (1995), which needs calibration data — "We have 516 records, no
calibration data… **Fitting EM here would produce a number that LOOKS like a probability and
is not one.**"

**Jaro** is implemented from §2.1 with a **documented correction to the paper**: RR99-04's
printed formula ends `+ 0.5 · #transpositions / #common`, which would make a pair score
*higher* the more transposed it is; "that is a transcription error in RR99-04; the term is
subtractive, as in Jaro (1989) and every implementation since". **Jaro–Winkler** adds
`n · 0.1 · (1 − j)` for an agreeing prefix up to 4 characters. §2.1 reports that without
approximate comparison "more than 25% of matches would not have been found", and the OSHA
extract contains BABBITT/BABBIT, LOGISTIC/LOGISTICS, WENDALL/WENDELL.

**Thresholds are measured, not borrowed.** `STREET_MATCH = 0.92`, `STREET_REVIEW = 0.78`.
Sweeping every within-state pair sharing a house number gives a sharply bimodal distribution
with an empty gap: 64 pairs at ~1.00, typos at 0.905 and 0.849, then **nothing at all**, then
different streets at 0.722 and below. `STREET_REVIEW` sits in the middle of the observed
gap. Winkler's Table 1 `Mn >= 0.6` bucket is explicitly rejected — it is for *person* names,
and "at 0.6 this dataset would admit CENTRAL/CANTON and merge two real New Jersey
facilities".

**Three-valued agreement** (`AGREE` / `MISSING` / `CONFLICT`) "is the entire reason the
addresses are parsed": two records both omitting a directional *agree*; one omitting what
the other states is weak evidence; two stating *different* directionals describe different
streets. **Blocking** is not from the paper — "Winkler's paper does not cover blocking at
all… so these are ours, and they are measured rather than asserted": three keys unioned
(state+house number, state+first 5 chars of street core, building code), because "a pair
that is never GENERATED is a false non-match that no threshold can recover".

`linkage_group.py` is **checked transitive closure, not blind closure.** Three real Tracy CA
records: A `1555 CHRISMAN RD`, B `1555 N CHRISMAN ROAD`, C `1555 S CHRISMAN RD`. A–B
matches, A–C matches, **B–C is a flat contradiction**, and connected components would give
one building where there are at least two. So: union-find over strong and weak edges, then
check every component of size ≥ 3 for a pair the comparator **explicitly rejected** (silence
is not rejection); an inconsistent component is rebuilt from strong edges only and the
leftovers go to clerical review. `common/address.py` keeps components in fixed slots
precisely so `N` vs `S` reads as CONFLICT while `N` vs absent reads as MISSING, with four
named traps: the operator-word cut fires only *after* a street suffix, because
`376 ZAPPOS.COM BLVD` is a real street; `_is_house` accepts grid addressing (`W6331`)
because a digits-only test silently **dropped** a Wisconsin facility — "a building that
disappears is the expensive kind of bug"; `SAINT → ST` only when not the final token; and a
bare trailing number is a unit only when there are more than two tokens, so `4412 W 300 N`
keeps its number.

<a id="a12"></a>
## 12. Fellegi–Holt edit systems

**Plainly.** An **edit** is a logical rule a record must satisfy — "a building cannot have
opened after the date an inspector found it already operating". Fellegi & Holt's 1976
insight was to declare the rules once and let the machine work out *which fields to change*.
The distinction this project turns on is between an **edit** and a **preference**: a
preference ranks values that are all admissible, so when two sources tie nothing separates
them and you stop; an edit expresses a **contradiction**, and a contradiction does not tie.

**Precisely.** `warehouse/edits.py` declares two edits, each with the minimal cover the
failure localises to (**Fellegi & Holt Corollary 2**): `E_date_contradiction` (two records
linked at or above `linkage.STREET_MATCH` must carry the same `open_q_index`) and
`E_operating_by` (`quarter_start(open_q_index) <= osha_operating_by`). The second's
validity: "An OSHA inspection is conducted at a site that EXISTS AND IS OPERATING, so its
date is an upper bound… A record claiming the building opened strictly after the date it was
already operating is not *less reliable* than its twin. **It is impossible.**" Quarter
**starts**, not ends, on purpose: a claimed 2017Q4 opening against a 2017-12-21 inspection
is consistent, and comparing quarter ends would falsify the true record along with the false
one.

**`CORRECT` is deliberately absent** from the dispositions (`EXCLUDE`, `REPORT`): "an edit
that rewrote the field it localised would be the imputation rule specified independently of
the edits that Fellegi & Holt's Criterion 2 exists to abolish." Nothing is overwritten, so
the uncorrected data is recoverable and an `EXCLUDE` is reversible from the report alone.
Matching for the edit reuses the project's own comparator and blocking rather than joining on
city, "so the two are not two different notions of 'same building'". **Three things the edit
is not**: independent corroboration for the national panel (all 104 rows were built by
classifying the OSHA extract, so it is an *internal* check that finds four rows departing
from the source they came from); a way to turn a bound into an opening (the measured lag runs
4 to 345 months); or a correction. `load_operating_bounds` returns `None`, not an exception,
when the extract is absent, and the run logs **"E_operating_by NOT EVALUATED… The edit is
declared and unchecked, which is not the same as passed."**

**The §7 reliability weights live one file over**, in `warehouse/facility_dedup.py`:
`DATE_RELIABILITY = ("press_release", "permit", "news", "company_site", "job_posting",
"osm", "other")`, most reliable first. **Ties are not resolved.** Fellegi & Holt §1 option 2
— *"one should, whenever possible, avoid manufacturing data instead of collecting it"* — so a
tie sets `open_q_index` to **NaN, not a guess**, is recorded as unresolved, and is made a
hard failure in the file the build reads, "so that a human does three permit lookups instead
of a rule inventing a date". All six rows of the three known contradicting pairs are
`source_type = permit`, so all three tie. Gap recorded in `METHODS_RESEARCH.md` §15: **the
consistency check on the edit set** (Winkler feature 2, FH §5.2) is not built.

<a id="a13"></a>
## 13. The OCR geometry — turning table images into rows

**Plainly.** MWPVL publishes its network census as **pictures of tables**. A generic OCR
pass returns a bag of words with pixel positions and no idea which column or row each
belongs to. **Columns** are found by looking down the page: count how many words cover each
pixel column, and the valleys — vertical stripes almost nothing crosses — are the gutters.
**Rows** are found by anchoring on something that reliably ends a row; here that is the
postal code, since every address ends in one. Both choices have a failure mode, and both
were measured rather than assumed.

**Precisely.** Tesseract CLI in **TSV mode** (word boxes, not text), `--psm 6`, 4× LANCZOS
upscale on a grayscale crop — chosen by measurement, not reputation: upscale 1×→23 ZIPs,
2×→26, 3×→26, 4×→26; `psm 4`→15 dates, `6`→17, `11`→5, `12`→6. Pages are processed in
1 400-px strips with **400 px of overlap**, because a printed row is ~60 px and a wrapped row
up to 250, so 400 guarantees no row is cut by both strips containing it. Boxes are rebased
into original page pixels, which makes strips stitchable and dedupable by position. Settings
are stamped into `SETTINGS.json` and a resumed run with different ones hard-exits, "so one
directory cannot silently blend two extractions".

**Column recovery** (`ingest/mwpvl_grid.py:213-248`): build an integer coverage array over
the page width, incrementing every pixel column spanned by every word box; set
`cutoff = max(cover) × GUTTER_FRACTION` with **`GUTTER_FRACTION = 0.10`**, a *relative*
threshold, **not zero**; a maximal run below the cutoff at least **`MIN_GUTTER = 12` px**
wide is a gutter and the cut is its midpoint; a *trailing* low-density run is deliberately
not cut, because that is the right margin. The 10%-not-0% decision carries its measurement:
the zero-coverage version returned `[0, 819]`, the whole six-column table as one column,
because over 540 rows some description always bleeds into the gutter. Measured depths: 1 385
words at the centre of the address column against **3** in the gutter beside it.
`MIN_GUTTER = 12` because the narrowest real gutter measured is 13 px. Words are assigned by
**centre**, not left edge.

**Row anchoring** — `ZIP_RE = r"(?:^|\D)\d{5}(?:-\d{0,4})?[.,]?$"`, anchored at the **end**
of the token so `143,200` and `2025` cannot match, and tolerant of `92081-2607` and
`USA36322`. A candidate must also **end its line**: reject if any word containing an
alphanumeric sits to its right on the same line. That is what separates a five-digit *house
number* from a ZIP in `20920 Krameria Ave … 92518`, and the `isalnum()` test exists because
the ruled border OCRs as `|` just right of the ZIP. Fallback for the three rest-of-world
tables (40% of the pixel rows): `CODE_RE = [A-Z]{2,4}\d{1,2}`, the Amazon facility code. The
anchor **column** is whichever yields the most anchors, not a fixed index, because
rest-of-world tables carry a flag glyph and a Country column that shift everything right. A
word joins the **first anchor at or below it**, because the ZIP sits on the row's last
printed line — so a row occupies the band *above* its anchor; midpoint banding was tried
first and fails on variable row heights.

**The known defect: ~3%, and it destroys rows rather than duplicating them.**
`data/MWPVL_OCR_PIPELINE.md` §13.1: *"This is the dominant loss mode and it is structural:
the anchor IS the postal code, so a code that does not come back is a row that does not
exist. Its words do not vanish — they join the row below."* **Measured on the
delivery-station table: 18 of 535 rows merged, 3%** — down from 41 of 510 (8%) before three
fixes. Two caveats the document volunteers: a merge is **under-counted by construction**,
because it removes a row and the denominator moves too; and **the merge count is not emitted
anywhere**, so 517/535 is a working figure and is **not reproducible from an artefact**. The
downstream consequence is named at `mwpvl_fields.py:246-248`: taking the street as
"everything before the first comma" pairs the lost facility's street with the anchored
facility's city and ZIP, and **42 of the 50 rows shaped like this failed to geocode**. The
defect is invisible to a duplicate screen by construction. Output: **1 904 facilities across
13 table images**, 1 420 with a year, 873 with a month, 635 US delivery stations
(`mwpvl_extraction.json`, `20260915-195231-c54f`).

<a id="a14"></a>
## 14. Scoring — lift, Brier, AUC, calibration, splits

**Lift, and its null.** Defined in `models/panel_strata.py`, **not** `metrics.py`.
`lift = model_rate / chance_rate`, and **the chance rate is analytic, `min(k, J)/J`**, not
empirical: `choice.evaluate`'s uniform null ranks a constant score, so `np.argsort` breaks
every tie by row order and "uniform top-10" degenerates into "is the chosen ZCTA in the
first ten rows of the frame". The empirical figure is still emitted alongside, with that
warning attached to the field.

**Lift is always stratified by choice-set size** — `small_le25`, `mid_26_100`,
`large_gt100` (J ≥ 101) — because pooling across heterogeneous choice sets is a Simpson trap
that has produced two wrong conclusions in this project already: a choice set of eleven gives
a random guess a top-10 hit 91% of the time, so small-market lift is capped near 1.5×
whatever the model does. `MIN_INFORMATIVE = 20` counts **distinct decisions, not
decision-evaluations** — "50 re-splits of 7 decisions produce 136 evaluations and no more
information than 7 decisions hold" — and below it a stratum is marked THIN and not compared.
Pooled figures are reported only after **direct standardisation** to the `combined` arm's
size mix, and `standardise` returns `None` rather than extrapolating into an empty cell.

**Brier is a raw pair — model against a uniform-within-choice-set null — and never a skill
score.** Gneiting & Raftery (2007) §2.3 p. 362: skill scores are generally improper even
when the underlying score is proper. Two traps travel with it: at a 2% event rate,
predicting 0.02 for everybody scores 0.0196, so differences must be read against the
base-rate Brier and not against zero; and Brier **cannot rank the panel arms**, because it
averages over alternative rows whose denominators run 11 715 to 86 682.

**AUC** is the rank identity (normalised Mann–Whitney U) with `scipy.stats.rankdata`, so
ties get average rank and count as half a win — "a threshold sweep that breaks ties by input
order silently rewards a constant predictor with an AUC of 1.0 if the data happen to be
sorted by outcome". It returns `nan`, not 0.5, when one class is absent, because "returning
0.5 would look like a measured result". Its propriety is **undefined rather than violated**:
it is a rank statistic over *pairs* and cannot be written as `S(P, x)` at all.

**Calibration** uses **quantile (equal-count) bins**, and the docstring is emphatic this is
not a detail: with equal-*width* bins 99.9% of rows land in the first one, the plot shows a
single point, and the model looks perfectly calibrated because nothing was measured. ECE is
the weighted mean absolute gap; "quoted without the bin strategy it is not reproducible".

**Splits** are **by unit, never by row** (`models/splits.py`), three ways: a risk set has up
to 32 rows per ZCTA, and splitting rows at random puts 2024Q1 for ZCTA 94608 in training and
2024Q2 in test — "held-out AUC comes back at 0.95, everyone is delighted, and the number
means nothing". The third split exists because conformal calibration must be on data the
model never saw. `split_by_time` is the honest backtest "and it will score worse… Worse, and
more like the real task."

**One seed runs through everything.** `SEED = 20260914` is the default in `choice.fit` and
the module constant in `choice_runner.py`, imported by `gbm_benchmark` and `covariate_gbm` —
so **repeat 0 of every benchmark is bit-identical to the published headline split**, and each
benchmark reproduces `choice_report.json` as its own correctness check.

---

**Where each of these came from.** [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §15 is the
ledger of which paper changed which line of code, and §10 is the corrections log — "every
claim that went into the first draft of this file and did not survive the source. Roughly
one in three." [`research/README.md`](research/README.md) indexes one notes file per paper
read in full. [`REFERENCES.md`](REFERENCES.md) marks every entry `[V]` read in full, `[T]`
title and venue checked, or `[K]` from memory, verify before use — and §9 above is why that
scale exists.
