# Notes — Train (2009) Ch. 8, Numerical Maximization

*Read in full on 2026-09-13, every page, as images. This is the chapter behind
the backlog's "bootstrapped standard errors (Train 8.6)" —
[`../STATUS.md`](../STATUS.md) §5 item 2. The section number is
right. The justification Train attaches to the bootstrap has a precondition our
sample fails, and it is stated in the same section — see part 6.*

---

## 1. Citation and local file

```
  Kenneth E. Train, Discrete Choice Methods with Simulation, 2nd edition.
  Cambridge University Press, 2009.  Chapter 8, "Numerical Maximization",
  printed pp. 185-204.  Part II, "Estimation".

  Local file:  ../Research/Ch08_p183-204.pdf   (22 PDF pages)
  PDF page 1 = printed p. 183 (the Part II divider).  PDF page 2 = p. 184,
  blank.  Chapter 8 starts on PDF page 3 = printed p. 185.
  So: PDF page = printed page - 182.  Printed p. 204 = PDF page 22.
  Verified: PDF page 3 carries the running foot "185" and the heading
  "8 Numerical Maximization".
```

Every page number below is the **printed** page.

Note the filename says `p183-204` but the chapter text runs 185-204; pages 183
and 184 are the part divider and a blank.

Text layer clean. Figures 8.1-8.8 are simple line drawings of log-likelihood
curves; their content is fully described in the prose and is summarised below.

---

## 2. What the chapter is for

Train's framing (§8.1, p. 185) is that the point of modern discrete choice
methods is to free the researcher from the handful of models that come
prepackaged, and the price of that freedom is having to maximise your own
likelihood:

> "The thrust of the wave of discrete choice methods is to free the researcher
> to specify models that are tailor-made to her situation and issues. Exercising
> this freedom means that the researcher will often find herself specifying a
> model that is not exactly the same as any in commercial software. The
> researcher will need to write special code for her special model."

The chapter covers five algorithms (Newton-Raphson, BHHH, BHHH-2, steepest
ascent, DFP/BFGS), when to stop iterating, the local-versus-global-maximum
problem, and — in §8.6 — how to get standard errors, by three routes: the
information matrix, the robust sandwich, and the bootstrap.

What we want from it: **§8.5**, because our utility is nonlinear in parameters
and therefore not globally concave, and **§8.6**, because the project has
prescribed a bootstrap without reading what Train says a bootstrap assumes.

---

## 3. Section-by-section walkthrough

### §8.1 Motivation (p. 185)

Half a page, quoted above. The key sentence for us is the last one: "Though not
usually taught in econometrics courses, the procedures for maximization are
fairly straightforward and easy to implement."

### §8.2 Notation (pp. 185-186)

`LL(beta) = sum_{n=1}^{N} ln P_n(beta) / N`, the **average** log-likelihood.
Dividing by `N` "does not affect the location of the maximum (since `N` is fixed
for a given sample) and yet facilitates interpretation of some of the
procedures". Gradient `g_t = (dLL/dbeta)` at `beta_t`, dimension `K x 1`;
Hessian `H_t = (d g_t / d beta')`, dimension `K x K`.

> "the Hessian can help us to know *how far* to step, given that the gradient
> tells us *in which direction* to step."
> — §8.2, p. 186

Figure 8.1 (p. 186) is the picture: `LL(beta)` a concave curve, `beta_t` the
current point, `beta_hat` the maximum. Note LL is always negative, "since the
likelihood is a probability between 0 and 1 and the log of any number between 0
and 1 is negative".

### §8.3 Algorithms (pp. 187-198)

#### §8.3.1 Newton-Raphson (pp. 187-192)

Second-order Taylor expansion, eq. (8.1), maximised to give

```
  beta_{t+1} = beta_t + (-H_t^{-1}) g_t
```

"the gradient vector premultiplied by the negative of the inverse of the
Hessian". Intuition: "Each step of `beta` is the slope of the log-likelihood
function divided by its curvature." Great curvature, small step (Figure 8.3).

Three issues.

**Quadratics** (pp. 188-189). If `LL` is exactly quadratic, NR reaches the
maximum in one step from any starting value, demonstrated for `K = 1`.

**Step size** (pp. 189-191). NR can overshoot (Figure 8.4). Insert a scalar:
`beta_{t+1} = beta_t + lambda (-H_t)^{-1} g_t`. The procedure is halving —
"Start with `lambda = 1`. If `LL(beta_{t+1}) > LL(beta_t)`, move to `beta_{t+1}`
and start a new iteration. If `LL(beta_{t+1}) < LL(beta_t)`, then set
`lambda = 1/2` and try again" — and then doubling while LL keeps rising
(Figure 8.5). A diagnostic worth carrying: "If this process results in a tiny
`lambda`, then little progress is made in finding the maximum. This can be taken
as a signal to the researcher that a different iteration procedure may be
needed."

**Concavity** (pp. 191-192). If `LL` is globally concave, `-H^{-1}` is positive
definite and NR guarantees an increase each iteration, shown via a first-order
expansion: `LL(beta_{t+1}) = LL(beta_t) + lambda g_t'(-H_t^{-1}) g_t` and the
quadratic form is positive. In convex regions the Hessian is positive definite,
`-H_t^{-1}` is negative definite, and **NR steps in the wrong direction**
(Figure 8.6). Train's verdict: "there is no reason for using the Hessian where
the function is not concave, since the Hessian in convex regions does not
provide any useful information on where the maximum might be."

Two drawbacks of NR: computing the Hessian is expensive, and no increase is
guaranteed off-concavity. Other methods replace `-H^{-1}` with a matrix `M_t`
that is "necessarily positive definite, so as to guarantee an increase at each
iteration even in convex regions".

#### §8.3.2 BHHH (pp. 192-195)

Score `s_n(beta_t) = d ln P_n(beta) / d beta`; gradient is the average score;
`B_t = sum_n s_n s_n' / N`, the average outer product of the scores. At the
maximum the average score is zero, so `B_t` is the variance of the scores. The
link to curvature: if all scores are similar the sample contains little
information and LL is flat; if scores differ greatly, LL is highly peaked
(Figure 8.7). Formalised by the **information identity**, `V = -H`.

BHHH: `beta_{t+1} = beta_t + lambda B_t^{-1} g_t`. Two advantages: `B_t` is far
cheaper than `H_t` (the scores are computed for the gradient anyway), and `B_t`
is necessarily positive definite, so an increase is guaranteed even in convex
regions. Drawbacks: `B -> -H` only at the true parameters as `N -> infinity`, so
the approximation is poor far from the maximum, and "If the function is highly
nonquadratic, NR does not perform well ... since BHHH is an approximation to NR,
BHHH would not perform well even if `B_t` were a good approximation to `-H_t`."

#### §8.3.3 BHHH-2 (pp. 195-196)

`W_t = sum_n (s_n - g_t)(s_n - g_t)' / N`, the covariance of the scores about
their mean rather than the raw outer product. Same guarantees. "For `beta`'s
that are close to the maximizing value, BHHH and BHHH-2 give nearly the same
results." Train: "The main value of BHHH-2 is pedagogical."

#### §8.3.4 Steepest Ascent (pp. 196-197)

`beta_{t+1} = beta_t + lambda g_t`; defining matrix is the identity. Derived by
maximising a first-order expansion subject to a fixed Euclidean step length.
Train deflates it: "the method's property is actually less grand than this
statement implies ... The correct statement of the result is that there is some
sufficiently small distance for which the method of steepest ascent gives the
greatest increase for that distance. This distinction is critical. Experience
indicates that the step sizes are often very small with this method."

#### §8.3.5 DFP and BFGS (pp. 197-198)

Both build an **arc Hessian** from how the gradient changes between points
actually visited, rather than the infinitesimal Hessian at one point. "When the
log-likelihood function is nonquadratic, the Hessian at any point provides
little information about the shape of the function. The arc Hessian provides
better information." Train's recommendation, which is the operative sentence for
our implementation:

> "Both methods are extremely effective — usually far more efficient that NR,
> BHHH, BHHH-2, or steepest ascent. BFGS refines DFP, and my experience indicates
> that it nearly always works better. BFGS is the default algorithm in the
> optimization routines of many commercial software packages."
> — §8.3.5, p. 198

### §8.4 Convergence Criterion (pp. 198-199)

The gradient is never exactly zero numerically. Use
`m_t = g_t' (-H_t^{-1}) g_t` and stop when `m_t < m_tilde`, "such as
`m_tilde = 0.0001`". `m_t` is the chi-squared test statistic for all gradient
elements being zero with `K` degrees of freedom, but the threshold "is usually
set far more stringently (that is, lower) than the critical value of a
chi-squared at standard levels of significance", because a coefficient with a
`t` of 1.96 has a wide non-rejection region and we do not want convergence
declared anywhere in it.

**The warning against the lazy test** (p. 199):

> "It is tempting to view small changes in `beta_t` from one iteration to the
> next, and correspondingly small increases in `LL(beta_t)`, as evidence that
> convergence has been achieved. However, as stated earlier, the iterative
> procedures may produce small steps because the likelihood function is not close
> to a quadratic rather than because of nearing the maximum. Small changes in
> `beta_t` and `LL(beta_t)` accompanied by a gradient vector that is not close to
> zero indicate that the numerical routine is not effective at finding the
> maximum."

Two alternatives based on the gradient itself: each element smaller in magnitude
than a threshold, or each element divided by the corresponding element of
`beta` smaller than a threshold. The second "normalizes for the units of the
parameters".

### §8.5 Local versus Global Maximum (pp. 199-200)

Short and, for us, decisive.

> "All of the methods that we have discussed are susceptible to converging at a
> local maximum that is not the global maximum, as shown in Figure 8.8. When the
> log-likelihood function is globally concave, as for logit with
> linear-in-parameters utility, then there is only one maximum and the issue
> doesn't arise. However, most discrete choice models are not globally concave."
> — §8.5, p. 199

The remedy: "use a variety of starting values and observe whether convergence
occurs at the same parameter values." Figure 8.8 shows a two-humped `LL`:
starting at `beta_0` converges to the lower peak `beta_1`, and "Unless other
starting values were tried, the researcher would mistakenly believe that the
maximum of `LL(beta)` had been achieved." Liu & Mahmassani (2000) propose
setting bounds on each parameter and drawing starting values within them.

### §8.6 Variance of the Estimates (pp. 200-202)

**The section the backlog cites.** Three routes to a covariance matrix.

**(1) Correctly specified model.** `sqrt(N)(beta_hat - beta*) -> N(0, (-H)^{-1})`
as `N -> infinity`, where boldface `H` is the expected Hessian in the population
and `-H` is the information matrix. Asymptotic covariance of `beta_hat` itself
is `-H^{-1}/N`, estimated by `-H^{-1}/N`, `B^{-1}/N` or `W^{-1}/N`, all evaluated
at `beta_hat`, all equivalent by the information identity.

**(2) Robust / sandwich.** If the model is not correctly specified, but the
expected score is zero at the true parameters,
`sqrt(N)(beta_hat - beta*) -> N(0, H^{-1} V H^{-1})`.

> "This matrix is called the *robust covariance matrix*, since it is valid
> whether or not the model is correctly specified."
> — §8.6, p. 201

Estimated as `H^{-1} W H^{-1}`, or with `B` instead of `W`. "This formula is
sometimes called the 'sandwich' estimator of the covariance, since the Hessian
inverse appears on both sides." Note that the Hessian must be computed at the
final iteration even if the algorithm did not otherwise need it.

**(3) Bootstrap**, Efron (1979). The four steps, verbatim in section 4 below.
`V = (1/R) sum_r (beta_r - beta_hat)(beta_r - beta_hat)'`. For a scalar statistic
`t(beta)`, sampling variance is `sum_r [t(beta_r) - t(beta_hat)]^2 / R`.

**And the logic, with its precondition** (p. 202) — quoted in section 4, because
this is the passage that qualifies that prescription.

Advantages and disadvantage, p. 202: "The advantage of the bootstrap is that it
is conceptually straightforward and does not rely on formulas that hold
asymptotically but might not be particularly accurate for a given sample size.
Its disadvantage is that it is computer-intensive since it entails estimating
the model numerous times."

### §8.7 Information Identity (pp. 202-204)

`V = -H` at the true parameters for a correctly specified model, where `V` is
the population covariance of the scores. Train calls it "a startling fact, not
something that would be expected or even believed if there were not proof". Two
consequences are stated as (1) and (2) on pp. 202-203 — `W -> -H` and `B -> -H`
as `N -> infinity` at the maximising `beta` — and then the identity is
demonstrated over pp. 203-204 by differentiating the zero-average-gradient
condition (8.2) with respect to the parameters and using
`d ln P / d beta = (1/P) dP / d beta`.

---

## 4. Verbatim quotes for anything load-bearing

### 4.1 §8.6, p. 201 — the bootstrap procedure, exactly as stated

> "An alternative way to estimate the covariance matrix is through
> bootstrapping, as suggested by Efron (1979). Under this procedure, the model
> is re-estimated numerous times on different samples taken from the original
> sample. Let the original sample be labeled `A`, which consists of the
> decision-makers that we have been indexing by `n = 1, ..., N`. That is, the
> original sample consists of `N` observations. The estimate that is obtained on
> this sample is `beta_hat`. Bootstrapping consists of the following steps:
>
> 1. Randomly sample *with replacement* `N` observations from the original sample
>    `A`. Since the sampling is with replacement, some decision-makers might be
>    represented more than once in the new sample and others might not be included
>    at all. This new sample is the same size as the original, but looks different
>    from the original because some decision-makers are repeated and others are
>    not included.
> 2. Re-estimate the model on this new sample, and label the estimate `beta_r`
>    with `r = 1` for this first new sample.
> 3. Repeated steps 1 and 2 numerous times, obtaining estimates `beta_r` for
>    `r = 1, ..., R` where `R` is the number of times the estimation is repeated
>    on a new sample.
> 4. Calculate the covariance of the resulting estimates around the original
>    estimate: `V = (1/R) sum_r (beta_r - beta_hat)(beta_r - beta_hat)'`."

### 4.2 §8.6, p. 202 — THE PRECONDITION, which the prescription does not carry

> "The logic of the procedure is the following. The sampling covariance of an
> estimator is, by definition, a measure of the amount by which the estimates
> change when different samples are taken from the population. Our original
> sample is one sample from the population. **However, if this sample is large
> enough, then it is probably similar to the population, such that drawing from
> it is similar to drawing from the population itself.** The bootstrap does just
> that: draws from the original sample, with replacement, as a proxy for drawing
> from the population itself. The estimates obtained on the bootstrapped samples
> provide information on the distribution of estimates that would be obtained if
> alternative samples had actually been drawn from the population."
> — emphasis added

### 4.3 §8.5, p. 199 — local versus global maximum

> "All of the methods that we have discussed are susceptible to converging at a
> local maximum that is not the global maximum, as shown in Figure 8.8. When the
> log-likelihood function is globally concave, as for logit with
> linear-in-parameters utility, then there is only one maximum and the issue
> doesn't arise. However, most discrete choice models are not globally concave.
> A way to investigate the issue is to use a variety of starting values and
> observe whether convergence occurs at the same parameter values."

### 4.4 §8.6, p. 201 — the robust covariance matrix

> "This matrix is called the *robust covariance matrix*, since it is valid
> whether or not the model is correctly specified."

### 4.5 §8.3.5, p. 198 — BFGS

> "Both methods are extremely effective — usually far more efficient that NR,
> BHHH, BHHH-2, or steepest ascent. BFGS refines DFP, and my experience indicates
> that it nearly always works better. BFGS is the default algorithm in the
> optimization routines of many commercial software packages."

### 4.6 §8.4, p. 199 — do not mistake small steps for convergence

> "Small changes in `beta_t` and `LL(beta_t)` accompanied by a gradient vector
> that is not close to zero indicate that the numerical routine is not effective
> at finding the maximum."

### 4.7 §8.3.1, p. 190 — the tiny-lambda diagnostic

> "If this process results in a tiny `lambda`, then little progress is made in
> finding the maximum. This can be taken as a signal to the researcher that a
> different iteration procedure may be needed."

---

## 5. Definitions the chapter gives formally

```
  AVERAGE LOG-LIKELIHOOD                                    §8.2, p. 185
      LL(beta) = sum_{n=1}^{N} ln P_n(beta) / N
    Divided by N.  "Doing so does not affect the location of the maximum
    (since N is fixed for a given sample)".

  GRADIENT / HESSIAN                                        §8.2, p. 186
      g_t = (dLL(beta)/dbeta) at beta_t          K x 1
      H_t = (dg_t/dbeta') = (d^2 LL/dbeta dbeta') at beta_t   K x K

  NEWTON-RAPHSON STEP                                       §8.3.1, p. 187
      beta_{t+1} = beta_t + (-H_t^{-1}) g_t
    with step size:  beta_{t+1} = beta_t + lambda (-H_t)^{-1} g_t

  SCORE                                                     §8.3.2, p. 193
      s_n(beta_t) = d ln P_n(beta) / d beta   evaluated at beta_t
      g_t = sum_n s_n(beta_t) / N             (the gradient is the average score)

  OUTER PRODUCT OF THE GRADIENT                             §8.3.2, p. 193
      B_t = sum_n s_n(beta_t) s_n(beta_t)' / N
    At the maximising beta the average score is zero, so B_t is the variance
    of the scores.

  BHHH / BHHH-2 / STEEPEST ASCENT STEPS          §8.3.2-8.3.4, pp. 194-196
      BHHH            beta_{t+1} = beta_t + lambda B_t^{-1} g_t
      BHHH-2          beta_{t+1} = beta_t + lambda W_t^{-1} g_t
        with W_t = sum_n (s_n - g_t)(s_n - g_t)' / N
      steepest ascent beta_{t+1} = beta_t + lambda g_t

  GENERAL STEP FORM                                         §8.3.1, p. 192
      beta_{t+1} = beta_t + lambda M_t g_t,  M_t a K x K matrix.
      NR: M_t = -H^{-1}.  Other procedures choose M_t "necessarily positive
      definite, so as to guarantee an increase at each iteration even in
      convex regions of the log-likelihood function".

  CONVERGENCE STATISTIC                                     §8.4, p. 198
      m_t = g_t' (-H_t^{-1}) g_t  <  m_tilde,   e.g. m_tilde = 0.0001.
      Distributed chi-squared with K degrees of freedom under the hypothesis
      that all gradient elements are zero, but set "far more stringently".

  ASYMPTOTIC DISTRIBUTION, CORRECT SPECIFICATION            §8.6, p. 200
      sqrt(N)(beta_hat - beta*)  ->d  N(0, (-H)^{-1})   as N -> infinity
      asymptotic covariance of beta_hat is -H^{-1}/N, estimable by
      -H^{-1}/N, B^{-1}/N or W^{-1}/N at beta_hat.

  ROBUST ("SANDWICH") COVARIANCE                            §8.6, p. 201
      sqrt(N)(beta_hat - beta*)  ->d  N(0, H^{-1} V H^{-1})
      estimated as H^{-1} W H^{-1} (or with B).  "valid whether or not the
      model is correctly specified."

  BOOTSTRAP COVARIANCE                                      §8.6, p. 201
      V = (1/R) sum_r (beta_r - beta_hat)(beta_r - beta_hat)'
      scalar statistic:  sum_r [t(beta_r) - t(beta_hat)]^2 / R

  INFORMATION IDENTITY                                      §8.7, p. 202
      V = -H  at the true parameters for a correctly specified model, where
      V is the population covariance of the scores and H the population
      average Hessian.
```

---

## 6. What this means for siting-atlas

### 6.1 THE CORRECTION: the bootstrap prescription needs its precondition attached

The backlog says "bootstrapped standard errors
(Train 8.6)" — [`../STATUS.md`](../STATUS.md) §5 item 2, which re-runs
`choice_inference` and `choice_sandwich` on the expanded panel. The section number checks out — the bootstrap is §8.6, pp. 201-202,
Efron (1979), four steps, reproduced in §4.1 above.

What is missing is the sentence immediately after the procedure (§4.2 above):

> "However, **if this sample is large enough**, then it is probably similar to
> the population, such that drawing from it is similar to drawing from the
> population itself."

That is the entire warrant for the bootstrap, and at 38 decisions it is exactly
the condition in doubt. A bootstrap over our sample resamples the same 38
buildings. It measures how much the estimate depends on *which of our 38* are
included — a real and useful quantity, and one worth reporting — but it does not
license treating the interval as the sampling variability of a fresh draw from
the population of Amazon siting decisions, because our 38 are not "probably
similar to the population".

**This is not a reason to abandon the bootstrap. It is a reason to report it
with its precondition and to report a second estimate beside it.**
`docs/MODEL_SPEC.md` §6.3 sets out what we do:

```
  1  Report BOTH the sandwich H^-1 V H^-1 / N (§8.6 p.201, "valid whether or
     not the model is correctly specified") AND the bootstrap, side by side.
     If they disagree, the disagreement is a finding about how little the
     sample constrains the model.
  2  Resample whole DECISIONS, never rows.  Train's step 1 says "randomly
     sample with replacement N observations", and an observation here is a
     decision with its whole choice set attached -- not one alternative.
     Resampling alternatives would be the hazard model's mistake in new
     clothes.
  3  Report PERCENTILE intervals, not bootstrap standard errors.  At n = 38
     there is no reason for the sampling distribution to be symmetric, and
     quoting "a standard error" invites the reader to form a normal interval.
     Train's step 4 gives a covariance, which presumes symmetry; we decline it.
  4  Put the p.202 quote in the table caption.
```

### 6.2 §8.5 is binding on us, because our likelihood is NOT globally concave

This is the most consequential thing in the chapter for the implementation, and
it follows from a chain across two chapters:

```
  Ch.3 §3.7.1 p.61   LL is globally concave for LINEAR-IN-PARAMETERS utility
  Ch.3 §3.4   p.52   nonlinear utility: "the log-likelihood function may not be
                     globally concave"
  our spec           V = ln(beta' a) is nonlinear in parameters
  Ch.8 §8.5   p.199  therefore multiple starting values are MANDATORY
```

`MODEL_SPEC.md` §6.2 accordingly requires a fixed, seeded grid of starting
values, and requires the metrics artefact to record how many converged to the
same optimum. A run where they disagree must say so rather than silently taking
the best one. Without this, a single-start fit of a non-concave likelihood is an
unforced error of exactly the kind this project has been documenting.

### 6.3 Convergence must be tested on the gradient, not on the step size

§8.4, p. 199 (§4.6 above) warns that small steps can mean a non-quadratic
likelihood rather than proximity to the maximum. `scipy.optimize`'s default
termination is on function and parameter tolerances, which is precisely the test
Train says not to trust. The implementation should assert `m_t < 1e-4` on the
returned gradient and approximate inverse Hessian, and record `m_t` in the
artefact. This is three lines and it converts an assumption into a measurement.

Related: Train's tiny-`lambda` diagnostic (§4.7 above) has a direct analogue — if
L-BFGS-B terminates after very few iterations with a large gradient, that is a
signal about the likelihood surface, not a success. Worth logging the iteration
count.

### 6.4 BFGS is Train's recommendation and we should just take it

§8.3.5, p. 198. `scipy.optimize.minimize(method="L-BFGS-B")` is the same family.
No need to hand-roll Newton-Raphson or BHHH; Train explicitly notes BFGS "is the
default algorithm in the optimization routines of many commercial software
packages" and that both quasi-Newton methods are "usually far more efficient"
than the alternatives he describes.

One reason this matters beyond convenience: BHHH and steepest ascent guarantee
an increase in convex regions because their defining matrices are positive
definite by construction (§8.3.1, p. 192). BFGS maintains a positive-definite
approximation too. Newton-Raphson does not, and would step the wrong way on our
possibly-non-concave surface (Figure 8.6, p. 192). So the choice is not just
about speed.

### 6.5 Every inferential tool here is asymptotic, and that is part of the power finding

`MODEL_SPEC.md` §8.3 asks whether the literature says this sample cannot identify
the model. Train gives no sample-size rule, and inventing one and attributing it
to him would be the kind of fabrication this project has a guard against. But
the chapter does bear on the question twice, and both times unfavourably:

- the asymptotic normality result is stated "as `N -> infinity`" (§8.6, p. 200);
- the bootstrap is justified only "if this sample is large enough" (§8.6, p. 202).

So every route to a standard error offered in Chapter 8 is a large-sample
argument, and `N = 38` is not where those arguments live. That is a citable
observation about our position and it is stronger than an appeal to a rule of
thumb. **The conventional floor of 10 events per parameter in
`hazard_report.json` is not from Train** — it is the epidemiological rule of
thumb — and nothing in this chapter should be cited for it.

### 6.6 What this chapter does NOT say, and should not be cited for

- It says nothing about clustered standard errors. The hazard model's
  `coefficients_clustered_by_zcta` is a sensible thing to have done, but Train
  Ch. 8 is not its authority; the sandwich in §8.6 is robust to
  misspecification, not to clustering.
- It says nothing about sample size, statistical power, or minimum events per
  parameter.
- The information identity (§8.7) is presented for a **correctly specified**
  model at the **true** parameters. Any claim that `B^{-1}` and `-H^{-1}` are
  interchangeable in our fit rests on an assumption we cannot check.

---

## 7. What I did NOT read, or did not understand

- **Every page of Chapter 8 was opened**, PDF pages 1-22, as rendered images, in
  two passes (1-20, 21-22). Pages 183 and 184 are the Part II divider and a
  blank. No stretch of the chapter body was skimmed.
- **The §8.7 demonstration of the information identity (pp. 202-204) I read line
  by line and followed, but did not re-derive independently.** The steps are
  complete in the text: differentiate the zero-average-gradient condition (8.2)
  with respect to `beta`, substitute
  `dP_i/dbeta' = [d ln P_i / d beta'] P_i`, rearrange, and replace
  `P_i(x,beta)` with `S_i(x)` at the true parameters. I did not verify the
  regularity conditions permitting differentiation under the integral sign.
- **Figures 8.1-8.8 are line drawings** of log-likelihood curves with labelled
  points (`beta_t`, `beta_{t+1}`, `beta_hat`, `beta_0`, `beta_1`, `beta_2`) and
  short captions. I read the labels and captions from the rendered images; the
  argument each figure makes is stated in the adjacent prose and is transcribed
  above. Figure 8.5's three `lambda` values (1, 2, 4) are legible. No numerical
  data appears in any of them.
- **The DFP and BFGS update formulas are NOT in the chapter.** Train describes
  the arc-Hessian idea and then says "The two procedures differ in how the
  updating is performed; see Greene (2000) for details." So I cannot state the
  update rule, and neither can this file. If the exact BFGS recursion ever
  matters, Greene is the reference and it is not in `../Research/`.
- **Cited works not consulted, none in `../Research/`:** Judge et al. (1985,
  Appendix B), Ruud (2000), Berndt, Hall, Hall & Hausman (1974), Theil (1971),
  Greene (2000), Liu & Mahmassani (2000), Efron (1979), Efron & Tibshirant
  (1993), Vinod (1993). Everything attributed to them is Train's
  characterisation. In particular I have not read Efron (1979) and cannot say
  whether Efron himself states the "large enough" precondition in the same terms
  Train does.
- **Not checked:** whether `scipy.optimize`'s L-BFGS-B returns an inverse-Hessian
  approximation adequate for computing Train's `m_t` convergence statistic, or
  whether the Hessian must be obtained separately (by numerical differentiation)
  at the final iterate. Train notes for non-NR procedures that the Hessian "must
  be calculated at the final iteration" for the covariance (p. 201). This is an
  implementation question and it is open.
