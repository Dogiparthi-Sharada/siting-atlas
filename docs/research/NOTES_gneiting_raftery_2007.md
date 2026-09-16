# Notes — Gneiting & Raftery (2007), proper scoring rules

**Citation.** Gneiting, Tilmann, and Adrian E. Raftery (2007). "Strictly Proper
Scoring Rules, Prediction, and Estimation." *Journal of the American
Statistical Association* 102(477): 359-378. Review Article.
DOI 10.1198/016214506000001437. Received December 2005, revised September 2006.

**Local file.** `MSBA_Project/Research/Gneiting2007jasa.pdf` — 20 pages,
publisher typeset. **Every page number in this file came from that copy.**
Journal page = PDF page + 358, so PDF p.1 is journal p.359 and PDF p.20 is
journal p.378, which matches the printed page range 359-378. The text layer is
clean throughout: `pdftotext -layout` recovered the body, Table 1, Table 2,
Table 3, all numbered equations and the appendix, so no fallback was needed.

> **Do not use `Research/27639845.pdf`.** It is the same paper as a JSTOR scan
> with a cover page, so every PDF page number in it is one higher than in the
> copy used here. If you cite from that copy, subtract the cover page first.

---

## 1. What the paper is for

This is a review article, not a result. Its job is to take a body of theory
that had been scattered across decision theory (Savage 1971), psychometrics
(Shuford, Albert & Massengil 1966), meteorology (Brier 1950; Murphy 1973) and
information theory (Good 1952), and present it to statisticians as a single
coherent apparatus. The apparatus answers one question: *if you are going to
score a probabilistic forecast with a number, which numbers are legitimate?*
The answer is the class of **proper** scoring rules — those whose expected
value is maximised by quoting what you actually believe — and within that, the
**strictly proper** ones, where the true belief is the *unique* maximiser. The
paper characterises that class on general probability spaces (Theorem 1), on
finite sample spaces (Theorem 2, Savage), on binary sample spaces (Theorem 3,
Schervish), and then walks through the named scores — Brier, spherical,
logarithmic, zero-one, CRPS, energy, interval, quantile — saying which are
proper, which are strictly proper, and which are neither. Sections 7-9 extend
the apparatus to Bayes factors, cross-validation, and estimation (maximum
likelihood turns out to be the special case of "optimum score estimation" run
with the logarithmic score). Section 8 is a case study whose stated purpose is
to demonstrate, on real weather data, that an improper score can point you at
the wrong model.

For this project, the paper matters because it supplies the grounds on which a
metric can be defended *as a metric*, independently of what it happened to say
about our model.

---

## 2. Section-by-section walkthrough

### Abstract (p.359)

Worth reading as a definition in its own right, because it states propriety
twice in one paragraph, once for evaluation and once for elicitation.

> "Scoring rules assess the quality of probabilistic forecasts, by assigning a
> numerical score based on the predictive distribution and on the event or
> value that materializes. A scoring rule is proper if the forecaster maximizes
> the expected score for an observation drawn from the distribution `F` if he
> or she issues the probabilistic forecast `F`, rather than `G != F`. It is
> strictly proper if the maximum is unique. In prediction problems, proper
> scoring rules encourage the forecaster to make careful assessments and to be
> honest."
> — Abstract, p.359

Keywords listed include `Brier score`, `Skill score`, `Strictly proper`,
`Loss function`, `Prediction interval`. They do **not** include AUC, ROC,
discrimination, or any classification-accuracy term. That is the first sign of
what is in scope (see Sec. 6 of these notes).

### 1. Introduction (pp.359-360)

Three things happen here and all three are load-bearing for us.

**(a) The calibration/sharpness paradigm is stated, and endorsed.**

> "In earlier work (Gneiting, Raftery, Balabdaoui, and Westveld 2003; Gneiting,
> Balabdaoui, and Raftery 2006), we contended that the goal of probabilistic
> forecasting is to maximize the sharpness of the predictive distributions
> subject to calibration. Calibration refers to the statistical consistency
> between the distributional forecasts and the observations, and is a joint
> property of the forecasts and the events or values that materialize.
> Sharpness refers to the concentration of the predictive distributions and is
> a property of the forecasts only."
> — Sec. 1, p.359

Note the asymmetry, which is the whole point: calibration is a **constraint**,
sharpness is the **objective**. You are not trading one off against the other.
You establish calibration and then, among calibrated forecasts, you want the
most concentrated one. A forecast that is not calibrated is not in the feasible
set at all. Note also that they present this as their own prior contention,
carried over, not as something proved in this paper.

**(b) The formal set-up and the definition of propriety, in prose.**

> "We take scoring rules to be positively oriented rewards that a forecaster
> wishes to maximize. Specifically, if the forecaster quotes the predictive
> distribution `P` and the event `x` materializes, then his or her reward is
> `S(P, x)`. The function `S(P, .)` takes values in the real line `R` or in the
> extended real line `R̄ = [-inf, inf]`, and we write `S(P, Q)` for the expected
> value of `S(P, .)` under `Q`. Suppose, then, that the forecaster's best
> judgment is the distributional forecast `Q`. The forecaster has no incentive
> to predict any `P != Q` and is encouraged to quote his or her true belief,
> `P = Q`, if `S(Q, Q) >= S(P, Q)` with equality if and only if `P = Q`. A
> scoring rule with this property is said to be strictly proper. If
> `S(Q, Q) >= S(P, Q)` for all `P` and `Q`, then the scoring rule is said to be
> proper."
> — Sec. 1, pp.359-360

**Orientation warning.** The paper is written throughout in **positive**
orientation: higher score is better, and you *maximise*. The Brier score as
they define it (Example 1) is therefore negative — `S(p,1) = -(1-p)^2`. Our
codebase and every other convention uses the **negative** orientation, where
the Brier score is a mean squared error you minimise. The two differ by a sign
and are "equivalent" in the paper's own sense (eq. 2 with `c = -1`). When
reading any inequality in the paper, remember it points the other way from our
code.

**(c) The estimation motive.** Optimum score estimation is introduced on p.360:
fit `theta` by maximising `S_n(theta) = (1/n) sum_i S(P_theta, X_i)` for a
strictly proper `S`. Maximum likelihood is this with the logarithmic score.
Fully developed in Sec. 9.

### 2. Characterizations of Proper Scoring Rules (pp.360-362)

The authors flag this section as the technical one and tell applied readers
they may skip to 2.3 "without significant loss of continuity".

#### 2.1 Proper Scoring Rules and Convex Functions (pp.360-361)

Sample space `Omega`, sigma-algebra `A`, `P` a convex class of probability
measures. A **scoring rule** is any extended real-valued function
`S: P x Omega -> R̄` such that `S(P, .)` is `P`-quasi-integrable for all
`P` in `P`. Expected score:

```
    S(P, Q) = integral S(P, omega) dQ(omega)
```

The two definitions, exactly as printed:

```
    S is PROPER relative to P            if   S(Q, Q) >= S(P, Q)
                                              for all P, Q in P.        (1)

    S is STRICTLY PROPER relative to P   if   (1) holds with equality
                                              if and only if P = Q.
```

Equivalence transform, eq. (2): if `S` is proper, `c > 0` constant, `h`
integrable, then `S*(P, omega) = c S(P, omega) + h(omega)` is also proper, and
strictly proper if `S` is. Following Dawid (1998) they call `S` and `S*`
*equivalent*, and *strongly equivalent* if `c = 1`. This is why "the Brier
score" is not a single function: any positive affine rescaling of it is the
same rule for every purpose the paper cares about.

Provenance note, same page: "The term *proper* was apparently coined by Winkler
and Murphy (1968, p. 754), whereas the general idea dates back at least to
Brier (1950) and Good (1952, p. 112)." In a parametric context, Lehmann and
Casella (1998, p. 157) call the defining property in (1) *risk unbiasedness*.

**Definition 1** (p.361), verbatim:

> "A scoring rule `S: P x Omega -> R̄` is *regular* relative to the class `P` if
> `S(P, Q)` is real-valued for all `P, Q` in `P`, except possibly that
> `S(P, Q) = -inf` if `P != Q`."

**Theorem 1** (p.361), verbatim:

> "A regular scoring rule `S: P x Omega -> R̄` is proper relative to the class
> `P` if and only if there exists a convex, real-valued function `G` on `P`
> such that
>
> ```
>     S(P, omega) = G(P) - integral G*(P, omega) dP(omega) + G*(P, omega)   (5)
> ```
>
> for `P` in `P` and `omega` in `Omega`, where `G*(P, .): Omega -> R̄` is a
> subtangent of `G` at the point `P` in `P`. The statement holds with proper
> replaced by strictly proper, and convex replaced by strictly convex."

The one-sentence version, given by the authors immediately after the proof:

> "Expressed slightly differently, a regular scoring rule `S` is proper
> relative to the class `P` if and only if the expected score function
> `G(P) = S(P, P)` is convex and `S(P, omega)` is a subtangent of `G` at the
> point `P`, for all `P` in `P`."
> — Sec. 2.1, p.361

**This is the structural fact to carry away.** Proper scoring rules are in
bijection with convex functions. That is why propriety is not a taste: it is
the exact condition under which the expected-score surface has its peak over
the true distribution.

#### 2.2 Information Measures, Bregman Divergences, and Decision Theory (p.361)

For a proper `S`, define

```
    G(P) = sup_{Q in P} S(Q, P),      P in P                            (6)
```

the **information measure** or **generalized entropy function** — the maximally
achievable utility. If `S` is regular and proper,

```
    d(P, Q) = S(Q, Q) - S(P, Q),      P, Q in P                         (7)
```

is the **divergence function**. Note the argument order: "the true
distribution, `Q`, is preceded by an alternative probabilistic forecast, `P`".
`d` is nonnegative, and if `S` is strictly proper then `d(P, Q) > 0` unless
`P = Q`. When the sample space is finite and `G` is smooth, `d` is the
**Bregman divergence** associated with `G`.

Also here: any proper scoring rule can be manufactured from a decision problem.
Given utility `U(omega, a)` and the Bayes act `a_P` for forecast `P`, the rule
`S(P, omega) = U(omega, a_P)` is proper, "by the fact that the optimal Bayesian
decision maximizes expected utility".

#### 2.3 Skill Scores (p.362) — THE MOST IMPORTANT SECTION FOR US

Scores are aggregated by simple averaging over a fixed set of forecast
situations:

```
    S_n = (1/n) sum_{i=1}^{n} S(P_i, x_i)
```

Then the comparability condition:

> "Scores for competing forecast procedures are directly comparable if they
> refer to exactly the same set of forecast situations. If scores for distinct
> sets of situations are compared, then considerable care must be exercised to
> separate the confounding effects of intrinsic predictability and predictive
> performance. For instance, there is substantial spatial and temporal
> variability in the predictability of weather and climate elements (Langland
> et al. 1999; Campbell and Diebold 2005). Thus a score that is superior for a
> given location or season might be inferior for another, or vice versa."
> — Sec. 2.3, p.362

The skill score, eq. (8):

```
                  S_n^fcst  -  S_n^ref
    S_n^skill  =  ---------------------                                 (8)
                  S_n^opt   -  S_n^ref
```

`S_n^fcst` is the forecaster's score, `S_n^opt` "a hypothetical ideal or optimal
forecast", `S_n^ref` the score of a reference strategy. Value 1 for an optimal
forecast, 0 for the reference, negative for worse than the reference. On the
reference:

> "The reference forecast is typically a climatological forecast, that is, an
> estimate of the marginal distribution of the predictand. ... Climatological
> forecasts are independent of the forecast horizon; they are calibrated by
> construction, but often lack sharpness."
> — Sec. 2.3, p.362

And then the sentence that cuts against this project:

> "Unfortunately, skill scores of the form (8) are generally improper, even if
> the underlying scoring rule `S` is proper. Murphy (1973) studied hedging
> strategies in the case of the Brier skill score for probability forecasts of
> a dichotomous event. He showed that the Brier skill score is asymptotically
> proper, in the sense that the benefits of hedging become negligible as the
> number of independent forecasts grows. Similar arguments may apply to skill
> scores based on other proper scoring rules. Mason's (2004) claim of the
> propriety of the Brier skill score rests on unjustified approximations and
> generally is incorrect."
> — Sec. 2.3, p.362

Read that twice. **The Brier score is strictly proper. The Brier *skill* score
is not** — it is only asymptotically proper, and the one paper claiming
otherwise is named and rejected. This is dealt with in Sec. 7 of these notes.

### 3. Scoring Rules for Categorical Variables (pp.362-365)

#### 3.1 Savage Representation (pp.362-363)

`Omega = {1, ..., m}`, forecast is a probability vector `p` in the simplex
`P_m`. `S(., i): P_m -> R̄`.

**Definition 2** (p.362), verbatim:

> "A scoring rule `S` for categorical forecasts is *regular* if `S(., i)` is
> real-valued for `i = 1, ..., m`, except possibly that `S(p, i) = -inf` if
> `p_i = 0`."

**Theorem 2** (McCarthy, Savage) (p.362), verbatim:

> "A regular scoring rule `S` for categorical forecasts is proper if and only if
>
> ```
>     S(p, i) = G(p) - <G'(p), p> + G'_i(p)     for i = 1, ..., m,      (10)
> ```
>
> where `G: P_m -> R` is a convex function and `G'(p)` is a subgradient of `G`
> at the point `p`, for all `p` in `P_m`. The statement holds with proper
> replaced by strictly proper, and convex replaced by strictly convex."

Consequence stated on the same page: "every bounded convex function `G` on
`P_m` generates a regular proper scoring rule."

Then the four examples. The paper flags their status explicitly: "The scoring
rules in Examples 1-3 are strictly proper. The score in Example 4 is proper but
not strictly proper."

**Example 1 (Quadratic or Brier score), p.363.** Take
`G(p) = sum_j p_j^2 - 1`. Then (10) yields

```
                     m                          m
    S(p, i)  =  -  sum  (delta_ij - p_j)^2  =  2 p_i  -  sum p_j^2  -  1
                    j=1                                   j=1
```

with `delta_ij = 1` if `i = j` and 0 otherwise. Associated Bregman divergence
is the squared Euclidean distance `d(p, q) = sum_j (p_j - q_j)^2`. Attributed
to Brier (1950); axiomatic characterisation by Selten (1998).

**Example 2 (Spherical score), p.363.** `G(p) = (sum_j p_j^alpha)^(1/alpha)` for
`alpha > 1`; `S(p, i) = p_i^(alpha-1) / (sum_j p_j^alpha)^((alpha-1)/alpha)`.
Reduces to the traditional spherical score at `alpha = 2`.

**Example 3 (Logarithmic score), p.363.** Negative Shannon entropy
`G(p) = sum_j p_j log p_j` gives `S(p, i) = log p_i`. Bregman distance is
Kullback-Leibler. Dates to Good (1952). Criticised by Selten (1998, p.51) for
unboundedness — "it entails value judgments that are unacceptable".

**Example 4 (Zero-one score), p.363.** The one that matters for the Train
question.

```
                 { 1/#M(p)     if i belongs to M(p)
    S(p, i)  =   {
                 { 0           otherwise
```

where `M(p) = {i : p_i = max_j p_j}` is the set of modes. Verbatim:

> "The zero-one scoring rule rewards a probabilistic forecast if the mode of the
> predictive distribution materializes. In case of multiple modes, the reward is
> reduced proportionally ... This is also known as the *misclassification loss*,
> and the meteorological literature uses the term *success rate* to denote
> case-averaged zero-one scores (see, e.g., Toth, Zhu, and Marchok 2001)."
> — Sec. 3.1, Example 4, p.363

Its entropy function is `G(p) = max_j p_j`, which "is neither differentiable
nor strictly convex" — hence the divergence is not a Bregman divergence, and
hence the rule is proper but **not** strictly proper.

**Symmetry**, eq. (11), p.363: the foregoing rules are invariant to permuting
the labels. "Winkler (1994, 1996) argued that symmetric rules do not always
appropriately reward forecasting skill and called for asymmetric ones,
particularly in situations in which skills scores traditionally have been
used."

#### 3.2 Schervish Representation (pp.363-365)

Restrict to `Omega = {1, 0}` and a quoted probability `p` in `[0, 1]`. Every
regular proper scoring rule has the Savage form

```
    S(p, 1) = G(p) + (1 - p) G'(p)
    S(p, 0) = G(p) -     p   G'(p)                                     (12)
```

for convex `G: [0,1] -> R` with subgradient `G'`. Figure 1 (p.364) is the
geometric picture: `G` is a convex curve, `S(p, .)` is its tangent at `p`, the
expected score `S(p, q)` is the ordinate of that tangent read at `q`, and the
Bregman divergence `d(p, q)` is the vertical gap between `G` and the tangent.
Consequence (eq. 13): `S(p, 1)` is increasing in `p` and `S(p, 0)` is
decreasing, "as would be intuitively expected".

**Theorem 3 (Schervish)** (p.364), verbatim:

> "Suppose that `S` is a regular scoring rule. Then `S` is proper and such that
> `S(0, 1) = lim_{p->0} S(p, 1)`, and `S(0, 0) = lim_{p->0} S(p, 0)`, and both
> `S(p, 1)` and `S(p, 0)` are left continuous if and only if there exists a
> nonnegative measure `nu` on `(0, 1)` such that
>
> ```
>     S(p, 1) = S(1, 1) - integral (1 - c) 1{p <= c} nu(dc),
>                                                                      (14)
>     S(p, 0) = S(0, 0) - integral     c   1{p >  c} nu(dc),
> ```
>
> for all `p` in `[0, 1]`. **The scoring rule is strictly proper if and only if
> `nu` assigns positive measure to every open interval.**"

(Emphasis added. That last sentence is the criterion used throughout Sec. 7 of
these notes.)

The interpretation, same page, is the decision-theoretic heart of the paper:

> "A two-decision problem can be characterized by a cost-loss ratio
> `c` in `(0, 1)` that reflects the relative costs of the two possible types of
> inferior decision. The measure `nu(dc)` in Schervish's representation (14)
> assigns relevance to distinct cost-loss ratios. This result also can be
> interpreted as a Choquet representation, in that every left-continuous bounded
> scoring rule is equivalent to a mixture of cost-weighted asymmetric zero-one
> scores,
>
> ```
>     S_c(p, 1) = (1 - c) 1{p > c},      S_c(p, 0) = c 1{p <= c},       (15)
> ```
>
> with a nonnegative mixing measure `nu(dc)`."
> — Sec. 3.2, p.364

So: **every scoring rule for a binary event is a weighted average of
threshold-at-`c` decision rules, and the weighting `nu(dc)` is what
distinguishes one score from another.** A score is strictly proper exactly when
it puts weight on every band of cost-loss ratios.

**Table 1** (p.365), reproduced. This is the single most useful table in the
paper for us.

```
  Proper Scoring Rules for Probability Forecasts of a Dichotomous Event and
  the Respective Mixing Measure or Lebesgue Density in the Schervish
  Representation (14)

  Rule          S(p,1)            S(p,0)            nu(dc)
  ------------------------------------------------------------------------
  Brier         -(1-p)^2          -p^2              Uniform
  Spherical     p*D^(-1/2)        (1-p)*D^(-1/2)    E^(-3/2)
  Logarithmic   log p             log(1-p)          (c(1-c))^-1
  Zero-one      (1-c) 1{p>c}      c 1{p<=c}         Point measure in c

    where  D = 1 - 2p + 2p^2   and   E = 1 - 2c + 2c^2
```

Read the right-hand column top to bottom. The Brier score weights every
cost-loss ratio **equally**. The logarithmic score weights the extremes
`c -> 0` and `c -> 1` infinitely heavily (density `(c(1-c))^-1`, an infinite
measure). The zero-one score puts **all** its weight on one point `c`, which is
exactly why it fails the "positive measure on every open interval" test and is
therefore proper but not strictly proper.

**Example 5 (Beta family), p.365.** Buja, Stuetzle & Shen (2005)'s
two-parameter family with mixing density `c^(alpha-1) (1-c)^(beta-1)`, for
`alpha, beta > -1`. Contains the logarithmic score (`alpha = beta = 0`),
versions of the Brier score (`alpha = beta = 1`), and the zero-one score with
`c = 1/2` as the limit `alpha = beta -> inf`. Asymmetric members arise when
`alpha != beta`.

**Winkler's construction, eq. (16), p.365.** Given a symmetric proper `S` and
`c` in `(0,1)`,

```
    S*(p, 1) = [S(p, 1) - S(c, 1)] / T(c, p)
    S*(p, 0) = [S(p, 0) - S(c, 0)] / T(c, p)                           (16)
```

with `T(c, p) = S(0,0) - S(c,0)` if `p <= c` and `S(1,1) - S(c,1)` if `p > c`,
is also proper, "standardized in the sense that the expected score function
attains a minimum value of 0 at `p = c` and a maximum value of 1 at `p = 0` and
`p = 1`".

**Example 6 (Winkler's score), p.365.** The Brier special case of (16):

```
                      (1 - c)^2 - (1 - p)^2
    S*(p, 1) = -------------------------------------
               c^2 1{p <= c} + (1 - c)^2 1{p > c}
                                                                       (17)
                            c^2 - p^2
    S*(p, 0) = -------------------------------------
               c^2 1{p <= c} + (1 - c)^2 1{p > c}
```

> "with the value of `c` in `(0, 1)` adapted to reflect a baseline probability.
> This was suggested by Winkler (1994, 1996) as an alternative to using skill
> scores."
> — Sec. 3.2, Example 6, p.365

Tetlock (2005) used exactly this to adjust for forecast difficulty when
evaluating expert political predictions. **This is the paper's proper-scoring
alternative to a skill score for a skewed baseline, and it is the one thing in
the paper that speaks directly to a low base rate.**

Figure 2 (p.366) plots `G(p)`, `S(p,1)` and `S(p,0)` for the Brier score, the
logarithmic score, the asymmetric zero-one score (15) with `c = .6` and
Winkler's standardised score (17) with `c = .2`. The zero-one panel is visibly
a step function; the other three are smooth.

### 4. Scoring Rules for Continuous Variables (pp.365-368)

Motivated by Bremnes (2004, p.346): the literature here is sparse.

**4.1 Density forecasts (pp.365-366).** With `L_alpha` the class of measures
absolutely continuous w.r.t. `mu` with finite `alpha`-norm:

```
    Quadratic     QS(p, w) = 2 p(w) - ||p||_2^2                      (18)
    Pseudospher.  PseudoS(p, w) = p(w)^(a-1) / ||p||_a^(a-1)
    Logarithmic   LogS(p, w) = log p(w)                              (19)

      (w = omega, a = alpha)
```

QS is strictly proper relative to `L_2`, PseudoS relative to `L_alpha`, LogS
relative to `L_1`. LogS is the `alpha -> 1` limit of PseudoS suitably scaled;
also known as the *predictive deviance* and the *ignorance score*; its
divergence is Kullback-Leibler.

They then rule out two intuitive-but-improper scores. The **linear score**
`LinS(p, omega) = p(omega)` is not proper — they give an explicit
counterexample with a standard Gaussian and a uniform on `(-eps, eps)`:

> "Essentially, the linear score encourages overprediction at the modes of an
> assessor's true predictive density (Winkler 1969)."
> — Sec. 4.1, p.366

The **probability score** of Wilson, Burrows & Lanzinger (1999), which
integrates the predictive density over a neighbourhood of the observation, "is
not a proper score either". Both reappear as the villains of the Sec. 8 case
study.

Also here: an operational warning that improper scores create gameable
artefacts — "If Lebesgue densities on the real line are used to predict
discrete observations, then the logarithmic score encourages the placement of
artificially high density ordinates on the target values in question. This
problem emerged in the Evaluating Predictive Uncertainty Challenge at a recent
PASCAL Challenges Workshop."

**4.2 Continuous Ranked Probability Score (pp.366-367).**

```
    CRPS(F, x) = - integral_{-inf}^{inf} (F(y) - 1{y >= x})^2 dy       (20)
```

> "and corresponds to the integral of the Brier scores for the associated
> binary probability forecasts at all real-valued thresholds."
> — Sec. 4.2, p.367

Closed form, eq. (21): `CRPS(F, x) = (1/2) E_F|X - X'| - E_F|X - x|`. Gaussian
closed form given. CRPS is proper relative to the Borel measures and strictly
proper on the subclass with finite first moment. Its divergence is of
Cramer-von Mises type. In negative orientation
`CRPS*(F, x) = E_F|X - x| - (1/2)E_F|X - X'|`, which "generalizes the absolute
error to which it reduces if `F` is a deterministic forecast — that is, a point
measure. Thus the CRPS provides a direct way to compare deterministic and
probabilistic forecasts."

**4.3 Energy score (p.367).** `ES(P, x) = (1/2) E_P||X - X'||^beta - E_P||X -
x||^beta` for `beta` in `(0,2)`, eq. (22). Generalises CRPS to `R^m`. Strictly
proper by Szekely (2003, thm. 1). At `beta = 2` it degenerates to the negative
squared error `-||mu_P - x||^2`, which is proper but **not** strictly proper.

**4.4 Scoring rules depending on first and second moments only (pp.367-368).**
`S(P, x) = -log det Sigma_P - (x - mu_P)' Sigma_P^{-1} (x - mu_P)`, eq. (25), is
strictly proper relative to any convex class characterised by its first two
moments. Contrast with the **predictive model choice criterion** (PMCC) of Laud
& Ibrahim (1995) and Gelfand & Ghosh (1998),
`PMCC = sum_i (x_i - mu_i)^2 + sum_i sigma_i^2`, which corresponds to
`S(P, x) = -(x - mu_P)^2 - sigma_P^2`, eq. (26), and

> "is improper; if the forecaster's true belief is `P` and if he or she wishes
> to maximize the expected score, then he or she will quote the point measure at
> `mu_P` — that is, a deterministic forecast — rather than the predictive
> distribution `P`."
> — Sec. 4.4, p.368

This is the cleanest single illustration of what impropriety *does*: it rewards
pretending to be certain.

### 5. Kernel Scores and Negative Definite Functions (pp.368-369)

Mostly outside our needs. `g` is a *negative definite kernel* on `Omega` if
symmetric with `sum_i sum_j a_i a_j g(x_i, x_j) <= 0` for coefficients summing
to zero.

**Theorem 4** (p.368): for `Omega` Hausdorff and `g` a nonnegative continuous
negative definite kernel, `S(P, x) = (1/2) E_P g(X, X') - E_P g(X, x)`, eq.
(28), is proper relative to the Borel measures with `E_P g(X, X')` finite.
Proof is two lines from Berg, Christensen & Ressel (1984, thm. 2.1).

Examples 7-12 recover, as special cases: the Brier score (Ex. 7, with
`g(0,0)=g(1,1)=0`, `g(0,1)=g(1,0)=1`), the CRPS (Ex. 8, `g(x,x') = |x - x'|`),
the energy score (Ex. 9), a CRPS for circular variables (Ex. 10), non-Euclidean
energy scores (Ex. 11), and complex-kernel constructions (Ex. 12).

**Theorem 5** (p.369) sharpens Theorem 4 to strict propriety on `R^m` for
spherically symmetric `psi` with `-psi'` completely monotone.

**5.2** derives Hoeffding-type expectation inequalities, eqs. (31)-(34), as side
results. **5.3** extends to complex-valued positive definite kernels, and notes
this "allows for the construction of proper scoring rules in more general
settings, such as probabilistic forecasts of structured data, including strings,
sequences, graphs, and sets".

### 6. Scoring Rules for Quantile and Interval Forecasts (pp.370-371)

**6.1 Quantiles (p.370).** **Theorem 6:** for `s` nondecreasing and `h`
arbitrary,

```
    S(r; x) = alpha s(r) + (s(x) - s(r)) 1{x <= r} + h(x)              (40)
```

is proper for predicting the `alpha`-quantile. **Corollary 1** extends to `k`
quantiles jointly, eq. (42). With `s(x) = x` and `h(x) = -alpha x` this reduces
to

```
    S(r; x) = (x - r)(1{x <= r} - alpha)                                (41)
```

which the econometrics literature calls the **tick** or **check loss function**,
and which is the objective in Koenker & Bassett (1978) quantile regression. The
paper's contribution: "our results give a negative answer" to Cervera and
Munoz's conjecture that only their special case is proper — the class is larger.

**6.2 Interval score (p.370).** For the central `(1 - alpha) x 100%` interval
with endpoints `l, u`, in negative orientation:

```
    S_alpha^int(l, u; x) = (u - l) + (2/alpha)(l - x) 1{x < l}
                                   + (2/alpha)(x - u) 1{x > u}         (43)
```

Proper. Traces to Dunsmore (1968), Winkler (1972), Winkler & Murphy (1979).
"The forecaster is rewarded for narrow prediction intervals, and he or she
incurs a penalty, the size of which depends on `alpha`, if the observation
misses the interval."

**6.3 Case study, conditionally heteroscedastic process (p.371).** Stationary
bilinear process `X_{t+1} = (1/2)X_t + (1/2)X_t eps_t + eps_t`. Three candidate
95% one-step intervals: `I` the true conditional interval, `J` the unconditional
one, `K` a width-minimising one. 100,000 sequential forecasts.

**Table 2** (p.371):

```
  Interval forecast    Coverage    Avg width    Avg interval score
  -----------------------------------------------------------------
  I  (45)               95.01%        4.00             4.77
  J  (46)               95.08%        5.45             8.04
  K  (47)               94.98%        3.79             5.32
```

All three hit nominal coverage. `K` is the **sharpest** (narrowest, 3.79) and
still loses to `I` on the score, because `K` "collapses to a point forecast when
the conditional predictive variance is highest". A worked demonstration that
coverage plus width, examined separately, can be satisfied by a bad forecast,
and that the proper score is what separates them.

**6.4 (p.371).** Scores for distributional forecasts can be built by integrating
quantile scores over `alpha`, eq. (48), or binary scores over thresholds, eq.
(49). "If `S` is the Brier score and `nu` is a sum of point measures, then the
ranked probability score (Epstein 1969) emerges."

### 7. Scoring Rules, Bayes Factors, Random-Fold Cross-Validation (pp.371-373)

**7.1 (p.372).** With no estimated parameters, the log Bayes factor is exactly
the difference of logarithmic scores: `log B = LogS(H_1, X) - LogS(H_2, X)`,
eq. (51) — Good (1952)'s "weight of evidence". With parameters, `S_{k,B} = sum_t
log P(X_t | X^{t-1}, H_k)`, eq. (53), and Dawid (1984) showed this is
asymptotically equivalent to the plug-in MLE prequential score and to BIC. Two
limitations are flagged: it assumes the data come in a particular order, and it
uses only the logarithmic score.

**7.2 (pp.372-373).** Replacing the time-ordered conditioning set with a random
subsample `D` gives eqs. (55)-(56) and a scheme they name **random-fold
cross-validation**: "the amount of data left out would be random rather than
fixed". They conjecture the same asymptotic equivalences hold with the log score
replaced by any other proper score, such as the CRPS.

### 8. Case Study: Sea-Level Pressure, Pacific Northwest (pp.373-374)

Stated purpose, verbatim: "Our goals in this case study are to illustrate the
use and the properties of scoring rules and to demonstrate the importance of
propriety."

Data: 16,015 verification records, five-member MM5 ensemble, 48-hour forecasts,
January-June 2000. RMSE of the ensemble mean 3.30 mb, root mean ensemble
variance 2.13 mb, ratio `r_0 = 1.55` — the ensemble is **underdispersive**, so
the correct predictive standard deviation is roughly 1.55 times the ensemble
spread. The experiment: form Gaussian predictive densities
`N(mu_i, (r sigma_i)^2)` for a grid of **inflation factors** `r`, and ask which
`r` each score prefers. The right answer is known to be near 1.55.

**Table 3** (p.373):

```
  Score                              Argmax_r s(r)      Linear transformation
                                     in eq. (57)        plotted in Figure 3
  ---------------------------------------------------------------------------
  Quadratic score (QS)                   2.18                40s + 6
  Spherical score (SphS)                 1.84                108s - 22
  Logarithmic score (LogS)               2.41                 s + 13
  CRPS                                   1.62                10s + 8
  Linear score (LinS)                     .05                105s - 5
  Probability score (PS)                  .02                 60s - 5
```

The four proper scores put the optimum at `r` between 1.62 and 2.41 — all
comfortably above 1, correctly diagnosing underdispersion. The two improper
scores put it at `.05` and `.02`:

> "The linear and probability scores were maximized at `r = .05` and `r = .02`,
> thereby suggesting ignorable forecast uncertainty and essentially
> deterministic forecasts. The latter two scores have intuitive appeal, and the
> probability score has been used to assess forecast ensembles (Wilson et al.
> 1999). However, they are improper, and their use may result in misguided
> scientific inferences, as in this experiment."
> — Sec. 8.2, p.374

**This is the paper's argument for propriety reduced to one experiment.** Two
metrics with "intuitive appeal", used in published practice, chose a model that
claims near-zero uncertainty. Not because the model was good, but because the
metric rewarded overconfidence.

Also in 8.2, and directly relevant to a 2% base rate:

> "It is interesting to observe that the logarithmic score gave the highest
> maximizing value of `r`. The logarithmic score is strictly proper but involves
> a harsh penalty for low probability events and thus is highly sensitive to
> extreme cases. ... In our experience, the CRPS is less sensitive to extreme
> cases or outliers and provides an attractive alternative."
> — Sec. 8.2, p.374

**8.3 Interval forecasts (p.374).** Empirical coverage alone reaches nominal at
`r = 1.78` (`alpha = .50`) and `r = 2.11` (`alpha = .10`); the interval score is
optimised at `r = 1.56` and `r = 1.72`, i.e. closer to the truth.

> "This scoring rule assesses both calibration and sharpness, by rewarding
> narrow prediction intervals and penalizing intervals missed by the
> observation."
> — Sec. 8.3, p.374

### 9. Optimum Score Estimation (pp.374-376)

**9.1 Point estimation (pp.374-375).** Maximise `S_n(theta) = (1/n) sum_i
S(P_theta, X_i)` for strictly proper `S`; then `argmax_theta S_n(theta) ->
theta_0`, eq. (59). Pfanzagl (1969) and Birge & Massart (1993) studied these as
**minimum contrast estimators**. MLE is the special case with the logarithmic
score; optimum score estimation is a special case of M-estimation.

> "The appeal of optimum score estimation lies in the potential adaption of the
> scoring rule to the problem at hand. ... Buja et al. (2005) argued that
> strictly proper scoring rules are the natural loss functions or fitting
> criteria in binary class probability estimation, and proposed tailoring
> scoring rules in situations in which false positives and false negatives have
> different cost implications."
> — Sec. 9.1, p.375

Also cited: Copas (1983) and Friedman (1989), that maximum likelihood and least
squares plug-in estimates "can be suboptimal in prediction problems".

**9.2 Quantile estimation (p.375).** One sentence: Koenker & Bassett (1978) is
optimum score estimation with rule (41).

**9.3 Interval estimation (p.376).** Casella, Hwang & Robert (1993)'s paradox —
under the loss `L(I; theta) = c lambda(I) - 1{theta in I}`, eq. (60), the
classical `t`-interval is dominated by "a misguided interval estimate that
shrinks to the sample mean in the cases of the highest uncertainty". Casella et
al.: "we have a case where a disconcerting rule dominates a time honored
procedure. The only reasonable conclusion is that there is a problem with the
loss function." G&R concur and propose the interval score instead,
`L_alpha(I; theta) = lambda(I) + (2/alpha) inf_{eta in I} |theta - eta|`, eq.
(61), which "avoids paradoxes, as a consequence of the propriety of the interval
score".

### 10. Avenues for Future Work (p.376)

Open problems named: the relationship between proper scoring rules and
divergence functions is "not fully understood"; the characterisation of proper
scoring rules for quantiles is open; and —

> "Little is known about the propriety of skill scores, despite Murphy's (1973)
> pioneering work and their ubiquitous use by meteorologists. Briggs and Ruppert
> (2005) have argued that skill score departures from propriety do little harm.
> Although we tend to agree, there is a need for follow-up studies."
> — Sec. 10, p.376

Note that carefully: they "tend to agree" that the impropriety of skill scores
does little harm, but call it an open question. That is the most favourable
thing the paper says about skill scores, and it is a hedge, not a licence.

Also in Sec. 10, the only place in the paper that gestures at the classification
literature:

> "Briggs (2005), Briggs and Ruppert (2005), and Jolliffe (2006) have developed
> formal tests of forecast performance, skill, and value. This is a promising
> avenue for future work, particularly in concert with biomedical applications
> (Pepe 2003; Schumacher, Graf, and Gerds 2003)."
> — Sec. 10, p.376

Pepe (2003) is *The Statistical Evaluation of Medical Tests for Classification
and Prediction* — the standard ROC/AUC monograph. It is cited once, as future
work in a neighbouring field. Nothing in the paper engages with its content.

### Appendix: Statistical Depth Functions (p.376)

Half a page. A depth function `D(P, x)` gives a `P`-based centre-outward
ordering of points, which "formally resembles a scoring rule `S(P, x)`". The
analogy is called "superficial" in Sec. 1 and dismissed here:

> "Liu (1990) and Zuo and Serfling (2000) have listed desirable properties of
> depth functions, including maximality at the center, monotonicity relative to
> the deepest point, affine invariance, and vanishing at infinity. The latter
> two properties are not necessarily defendable requirements for scoring rules;
> conversely, propriety is irrelevant for depth functions."
> — Appendix, p.376

The remark that an *invariance* property is "not necessarily [a] defendable
requirement for scoring rules" is suggestive for the AUC question, but it is
about affine invariance of depth functions and is not a statement about AUC.
Do not stretch it.

### References (pp.377-378)

Two entries are worth knowing because they are easy to mis-cite:

- **Murphy, A. H. (1973)**, "Hedging and Skill Scores for Probability
  Forecasts," *Journal of Applied Meteorology*, 12, 215-223. This is the
  hedging paper cited in Sec. 2.3. It is **not** "A New Vector Partition of the
  Probability Score", which is the reliability-resolution-uncertainty
  decomposition paper. That paper is not in this reference list.
- **Mason, S. J. (2004)**, "On Using Climatology as a Reference Strategy in the
  Brier and Ranked Probability Skill Scores," *Monthly Weather Review*, 132,
  1891-1895. The claim G&R reject in Sec. 2.3.

---

## 3. Formal definitions, exactly as stated

Collected in one place, in the paper's own notation and positive orientation.

```
  SCORING RULE                                              Sec. 2.1, p.360
    A scoring rule is any extended real-valued function
        S : P x Omega -> R-bar
    such that S(P, .) is P-quasi-integrable for all P in P, where P is a
    convex class of probability measures on (Omega, A). If the forecast is
    P and omega materializes, the forecaster's reward is S(P, omega).

  EXPECTED SCORE                                            Sec. 2.1, p.360
        S(P, Q) = integral S(P, omega) dQ(omega)
    the expected score under Q when the probabilistic forecast is P.

  PROPER                                               Sec. 2.1, p.360, (1)
        S(Q, Q) >= S(P, Q)        for all P, Q in P.

  STRICTLY PROPER                                      Sec. 2.1, p.360, (1)
        (1) holds with equality if and only if P = Q,
        "thereby encouraging honest quotes by the forecaster."

  EQUIVALENT RULES                                     Sec. 2.1, p.360, (2)
        S*(P, omega) = c S(P, omega) + h(omega),  c > 0, h integrable,
    is proper if S is, and strictly proper if S is. Strongly equivalent
    if c = 1.

  REGULAR (general)                                  Sec. 2.1, p.361, Def 1
        S(P, Q) real-valued for all P, Q in P, except possibly
        S(P, Q) = -inf if P != Q.

  REGULAR (categorical)                              Sec. 3.1, p.362, Def 2
        S(., i) real-valued for i = 1..m, except possibly
        S(p, i) = -inf if p_i = 0.

  INFORMATION MEASURE / GENERALIZED ENTROPY            Sec. 2.2, p.361, (6)
        G(P) = sup_{Q in P} S(Q, P)
    the maximally achievable utility. Convex. Proper scoring rules are in
    bijection with convex G (Theorem 1).

  DIVERGENCE FUNCTION                                  Sec. 2.2, p.361, (7)
        d(P, Q) = S(Q, Q) - S(P, Q)
    Nonnegative; strictly positive unless P = Q when S is strictly proper.
    Equals the Bregman divergence of G when the space is finite and G is
    smooth.

  SKILL SCORE                                          Sec. 2.3, p.362, (8)
        S_n^skill = (S_n^fcst - S_n^ref) / (S_n^opt - S_n^ref)
    1 for an optimal forecast, 0 for the reference, negative for worse
    than the reference. "Generally improper, even if the underlying
    scoring rule S is proper."
```

Named scoring rules, with the paper's verdict on each:

```
  RULE                        WHERE           VERDICT
  ----------------------------------------------------------------------
  Brier / quadratic           Ex.1, p.363     strictly proper
    S(p,i) = -sum_j (delta_ij - p_j)^2
    binary: S(p,1) = -(1-p)^2, S(p,0) = -p^2      [Table 1, p.365]
    Schervish mixing measure: UNIFORM on (0,1)
    Bregman divergence: squared Euclidean distance

  Spherical / pseudospherical Ex.2, p.363     strictly proper

  Logarithmic                 Ex.3, p.363     strictly proper
    Shannon entropy; KL divergence; unbounded; "harsh penalty for low
    probability events" (Sec. 8.2, p.374)
    Schervish mixing density: (c(1-c))^-1, an INFINITE measure

  Zero-one / misclassification
  loss / "success rate"       Ex.4, p.363     PROPER BUT NOT STRICTLY
    Entropy G(p) = max_j p_j: neither differentiable nor strictly convex
    Schervish mixing measure: POINT MASS at a single c  [Table 1, p.365]

  Beta family                 Ex.5, p.365     proper; strictly proper when
    mixing density c^(a-1)(1-c)^(b-1) has mass on every interval

  Winkler's standardized      Ex.6, p.365     proper
    Brier, recentred on a baseline probability c; "an alternative to
    using skill scores"

  Quadratic score (density)   eq.(18), p.365  strictly proper on L_2
  Pseudospherical (density)   p.365           strictly proper on L_alpha
  Logarithmic (density)       eq.(19), p.365  strictly proper on L_1

  Linear score  LinS(p,x)=p(x)  p.366         IMPROPER
  Probability score (Wilson)    p.366         IMPROPER
  Predictive model choice
    criterion (PMCC)          eq.(26), p.368  IMPROPER

  CRPS                        eq.(20), p.366  proper; strictly proper on
    = integral of Brier scores over all thresholds   measures with finite
                                                     first moment
  Energy score                eq.(22), p.367  strictly proper, beta in (0,2)
    beta = 2 degenerates to -||mu_P - x||^2: proper, NOT strictly

  Quantile / tick / check     eq.(41), p.370  proper
  Interval score              eq.(43), p.370  proper; "assesses both
                                              calibration and sharpness"
```

---

## 4. Does the paper discuss AUC, ROC, or discrimination?

**No. Be exact about this, because it is easy to overclaim.**

`pdftotext -layout` over the whole 20-page file returns **zero** occurrences of:

```
  AUC                     0
  ROC                     0
  "receiver"              0
  "area under"            0
  "discrimination"        0
  "reliability"           0
  "resolution"            0 in the body
  "rare"                  0
  "base rate"             0
```

The only near-misses are two reference titles in the bibliography: Friedman
(1989) "Regularized **Discriminant** Analysis" and an unpublished dissertation
on a "High-**Resolution** Model". Neither is discussed.

The closest the paper comes to the classification-metrics literature is the
single sentence in Sec. 10 (p.376) citing Pepe (2003) — the standard ROC
monograph — as a pointer to biomedical applications for **future** work.

**What can honestly be said, therefore, is not that the paper criticises AUC. It
is that AUC is not the kind of object the paper's theory governs.** The argument
is structural and it is the one to use:

1. A scoring rule is `S: P x Omega -> R̄`, evaluated on a **single**
   forecast-observation pair (Sec. 2.1, p.360).
2. Scores are aggregated by simple averaging over cases,
   `S_n = (1/n) sum_i S(P_i, x_i)` (Sec. 2.3, p.362).
3. Propriety, eq. (1), is a property of `S` at that per-case level.
4. AUC is not of that form. It is a rank statistic over **pairs** of cases — the
   probability that a randomly drawn event outranks a randomly drawn non-event.
   It cannot be written as an average of per-case scores, so eq. (1) cannot be
   evaluated for it.

Conclusion: propriety is *undefined* for AUC, not violated by it. That is
weaker than "G&R says AUC is improper" — which would be a fabrication — and it
is enough, because what we want from a headline metric is precisely the
guarantee in eq. (1), and AUC cannot supply it.

The **related** object the paper does cover is the zero-one score (Example 4,
p.363), which it also calls the *misclassification loss* and, in meteorology,
the *success rate*. That is accuracy / percent-correctly-predicted, not AUC. Do
not conflate the two.

---

## 5. Does the paper say anything about rare events or low base rates?

**No section, and the phrases "rare event" and "base rate" do not occur.** Four
passages bear on it indirectly, in descending order of usefulness to us:

1. **Winkler's score, Example 6, eq. (17), p.365.** The Brier score recentred on
   a baseline probability `c`, "with the value of `c` in `(0,1)` adapted to
   reflect a baseline probability", offered explicitly "as an alternative to
   using skill scores". This is the paper's one purpose-built device for a
   skewed baseline and it is **proper**. At `c = 0.02` it applies to us
   directly. It is a better-founded answer to "0.02 base rate makes the raw
   Brier score uninformative" than a skill score is.

2. **Table 1 and the cost-loss reading, Sec. 3.2, pp.364-365.** The Brier score's
   mixing measure is *uniform* over cost-loss ratios `c`. That is a real and
   stateable property, and at a 2% base rate it is arguably the **wrong**
   weighting: the operationally interesting `c` for a rare event is nowhere near
   `0.5`, and the Brier score gives the band around `0.5` the same weight as the
   band near `0.02`. The beta family (Example 5) and Winkler's score (Example 6)
   exist to re-weight it. This is a weakness of the Brier score in our setting
   that we should volunteer rather than have found.

3. **Logarithmic score, Sec. 8.2, p.374.** "Strictly proper but involves a harsh
   penalty for low probability events and thus is highly sensitive to extreme
   cases." An argument for preferring the bounded Brier score over log loss at a
   low base rate — the only rare-event *guidance* the paper offers.

4. **Buja et al. tailoring, Sec. 9.1, p.375.** Strictly proper scoring rules are
   "the natural loss functions or fitting criteria in binary class probability
   estimation", with tailoring proposed "in situations in which false positives
   and false negatives have different cost implications". G&R cite this; they do
   not develop it. If we want the rare-event apparatus, Buja, Stuetzle & Shen
   (2005) is the paper to read next, not this one.

---

## 6. What this means for siting-atlas

### 6.1 The measured position, verified

Every figure below was re-read out of `experiments/hazard-model/artefacts/hazard_report.json` for
these notes, not copied from a summary.

```
  held-out test split, n = 8,044 rows, 161 events, base rate 0.020015

                             model      null
  ------------------------------------------------
  AUC                        0.6894     0.5000
  Brier (neg. orientation)   0.019522   0.019614
  Brier skill               +0.00471     0.0000
  ECE                        0.00863    0.00005
  ------------------------------------------------
  Brier skill, temporal     -0.02091
  Brier skill, geographic   -0.06184
```

Keys in `experiments/hazard-model/artefacts/hazard_report.json`: `evaluation.auc`,
`evaluation.brier`, `evaluation.ece` and the matching `null_model.*`;
`brier_skill` at the top level; `temporal_secondary.brier_skill` and the
`brier_skill` inside the geographic block.

All figures confirmed. Two notes on them:

- `1 - 0.019522/0.019614 = 0.004691`, against a stored `brier_skill` of
  `0.00471`. The difference is rounding in the stored Brier values, not an
  inconsistency.
- **The geographic hold-out figure must not travel without its caveat.** The
  report itself says so: "Phoenix and Boise hold two dated delivery stations
  between them, so this is a smoke test for gross failure and not a test of
  geographic transfer." `academic/defense/HANDBOOK_04_MODELS.md:126` repeats the
  instruction. Quoting `-0.06184` as evidence of failed geographic transfer
  overstates what was measured.

### 6.2 The null model is a climatological forecast, and the paper predicts its ECE

Our null predicts the constant 0.02006 everywhere. In the paper's vocabulary
that is exactly the **climatological forecast** of Sec. 2.3, p.362 — "an
estimate of the marginal distribution of the predictand". And the paper tells
us in advance what it will look like: "they are calibrated by construction, but
often lack sharpness."

So the headline embarrassment — "a constant is 170x better calibrated than our
model" — is, viewed through this paper, **half expected and half damning**, and
the honest version separates the halves:

- *Expected:* a constant equal to the base rate cannot be miscalibrated in
  aggregate. Getting beaten on ECE by a climatological reference is not by
  itself a scandal; that is what climatological references are.
- *Damning:* the entire job of the covariate model, under
  "maximise sharpness subject to calibration" (Sec. 1, p.359), was to buy
  sharpness **while keeping** calibration. It bought 0.5% of Brier skill and
  *lost* the calibration. It failed the constraint and barely moved the
  objective. Under the paradigm this paper endorses, that is not a marginal
  result; it is a clean failure.

That framing is better than the one currently in the docs, because it does not
lean on the reader being surprised by the null's ECE, and it makes the failure
larger, not smaller.

### 6.3 Our new headline is *nearly* the right one, and the gap is a real hit

This must be conceded before anyone finds it.

- The **Brier score** is strictly proper (Example 1, p.363). Reporting it is
  exactly what the paper recommends.
- The **Brier skill score** is not. Sec. 2.3, p.362: "skill scores of the form
  (8) are generally improper, even if the underlying scoring rule `S` is
  proper", with Murphy (1973) giving only *asymptotic* propriety and Mason
  (2004)'s propriety claim named as "generally incorrect".
- Sec. 10, p.376 softens this to an open question — "Briggs and Ruppert (2005)
  have argued that skill score departures from propriety do little harm.
  Although we tend to agree, there is a need for follow-up studies" — but a
  hedge in a future-work section is not an endorsement.

**What follows for the repo.** Report the raw Brier scores as the primary
figures, side by side, with the skill score presented as the ratio it is:

```
  Brier, model  0.019522
  Brier, null   0.019614      <- the proper comparison; same 8,044 rows,
                                 which is what Sec. 2.3 p.362 requires
  skill         +0.00471      <- a presentational normalisation of the above,
                                 not itself a proper scoring rule
```

Our own case is the benign one: Murphy's hedging benefit vanishes as `n` grows,
and `n = 8,044`. But the defensible claim is "the Brier score is our headline
and the skill score is how we display it", not "Brier skill is a proper scoring
rule". The second sentence is false and the paper says so on page 362.

Implementation note: `src/siting_atlas/models/metrics.py:82` defines
`brier_skill_score` against `np.full_like(y, y.mean())`, i.e. the in-sample mean
of the evaluation split. That is the climatological reference of Sec. 2.3, and
it is the right reference; it is worth stating in the docs that the reference is
fitted on the evaluation set itself, which is the standard convention and also
the most generous one to the null.

### 6.4 The Train/AUC claim gets a formal upgrade

Train (2009) §3.8.1 objects to "percent correctly predicted" in prose. This
paper gives the same object a name and a theorem. Train's PCP is G&R's
**zero-one score** (Example 4, p.363) — they even note that "the meteorological
literature uses the term *success rate*". Its status: **proper but not strictly
proper**, because its entropy function `G(p) = max_j p_j` is not strictly
convex, and equivalently because its Schervish mixing measure is a point mass at
a single cost-loss ratio rather than a measure with mass on every interval
(Theorem 3, p.364; Table 1, p.365).

That is Train's complaint stated exactly: a rule that is merely proper does not
*uniquely* identify the true probability, so a range of different forecasts all
maximise it, so the statistic cannot be used to choose among them. Worth adding
to `docs/METHODS_RESEARCH.md` §5.4, which currently rests on Train's prose alone.

It does **not** extend to AUC, for the reason in Sec. 4 of these notes: AUC is
not a per-case score, so neither Example 4 nor Theorem 3 applies to it.

### 6.5 The defence that does not depend on our result

The strongest thing in this paper for us is Sec. 8.2, p.374, and it is strong
precisely because it is about the weather in 2000 and not about us.

Two scores "with intuitive appeal", one of them in published operational use,
were run on 16,015 real forecasts and both chose a model claiming essentially
zero uncertainty (`r = .05` and `r = .02` against a truth near 1.55). Four
proper scores got it right. The authors' conclusion: "their use may result in
misguided scientific inferences, as in this experiment."

The rule that falls out — *report a strictly proper score, because an improper
one can prefer the wrong model* — was published in JASA in March 2007. It is
not a rule we invented in September 2026 after looking at an AUC of 0.6894.

### 6.6 Things in the repo this paper should change

```
  1  METHODS_RESEARCH.md Sec. 5.4 currently argues the AUC point from Train
     alone. Add the G&R mechanism (zero-one score = proper but not strictly
     proper; Schervish point mass vs uniform) and the honest statement that
     G&R never mentions AUC.                                      [DONE]

  2  Anywhere the phrase "Brier skill" is the headline, the raw Brier pair
     should sit beside it, and the skill score should be labelled a
     normalisation. Sec. 2.3, p.362 is the reason.                [DONE in
     METHODS_RESEARCH Sec. 12; the status documents were not owned by
     this agent and still showed skill alone]

  3  Winkler's score (17) at c = 0.02 is a proper, baseline-adjusted
     alternative to the skill score, computable from what we already store
     in hazard_predictions.parquet. Not implemented. Cheap.       [OPEN]

  4  ECE is not a scoring rule and is not in this paper. It is a diagnostic
     for the calibration constraint in the Sec. 1 paradigm. It should never
     be reported as though it were a score, and a model cannot be defended
     by a good ECE alone -- the constant null proves that, scoring 0.00005.
                                                                  [wording
     already correct in VIVA_QA D1]
```

---

## 7. What I did not read, or did not follow

Stated plainly so nobody assumes more coverage than there is.

- **Every page was opened.** PDF pages 1-20 of `Gneiting2007jasa.pdf` were read
  as images, and the full text layer was extracted and searched. No stretch was
  skimmed.
- **Proofs read but not verified.** I read the proofs of Theorem 1 (p.361),
  Theorem 4 (p.368) and Theorem 6 (p.370), and the sketch proof of Theorem 3
  (p.364). I did not check the convex-analysis steps against Rockafellar (1970,
  sects. 23-25) or Hendrickson & Buehler (1971), so I am taking the
  subgradient/subtangent arguments on trust. The statements are quoted exactly;
  the proofs are not something I can vouch for.
- **Section 5 understood only at the level of statements.** Kernel scores,
  negative definite functions, Schoenberg's theorem, Assumption 1 (p.369) and
  the Hoeffding-type inequalities (31)-(34): I can state what Theorems 4 and 5
  claim and which examples they recover, but I did not follow the harmonic
  analysis behind Assumption 1 or the Koldobskii/Zastavnyi conditions. Nothing
  in Sec. 5 is used in the arguments above.
- **Section 7 followed but not stress-tested.** The Bayes-factor and
  random-fold cross-validation equivalences rest on Dawid (1984), which I have
  not read. The conjecture in 7.2 that the equivalences survive replacing the
  log score with another proper score is explicitly a conjecture in the paper,
  and I have not checked whether it has since been settled.
- **Section 6.3's bilinear-process case study** was read and Table 2 transcribed,
  but I did not verify the construction of intervals `J` and `K` (eqs. 46-47) or
  the `gamma(y)` width-minimising function.
- **Not consulted at all:** every cited work. Buja, Stuetzle & Shen (2005),
  Schervish (1989), Savage (1971), Murphy (1973), Mason (2004), Winkler (1994,
  1996), Pepe (2003) and Briggs & Ruppert (2005) are all described here only as
  G&R describe them. In particular, the claim that "Mason's (2004) claim ... is
  generally incorrect" is G&R's, and I have not read Mason to check it. If the
  Brier-skill propriety question ever becomes load-bearing in the viva, read
  Murphy (1973) and Briggs & Ruppert (2005) directly; this paper's treatment of
  it is four sentences in Sec. 2.3 plus three in Sec. 10.
- **Not read:** `Research/27639845.pdf`, the JSTOR copy of the same paper.
