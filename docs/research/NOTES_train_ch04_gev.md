# Notes — Train (2009) Ch. 4, GEV

*Read in full on 2026-09-13, every page, as images. Read because logit imposes
IIA and adjacent ZCTAs are near-perfect substitutes, and because the two-factor
decomposition at
[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.3 — `P(served) = P(a station opens in your metro) x
P(the chosen site is within 15 miles)` — is structurally a nested logit whether
we call it one or not. Part 6 says why we are nevertheless not fitting one.*

---

## 1. Citation and local file

```
  Kenneth E. Train, Discrete Choice Methods with Simulation, 2nd edition.
  Cambridge University Press, 2009.  Chapter 4, "GEV", printed pp. 76-96.

  Local file:  ../Research/Ch04_p76-96.pdf   (21 PDF pages)
  PDF page 1 = printed p. 76 (the chapter opening).
  So: PDF page = printed page - 75.  Printed p. 96 = PDF page 21.
  Verified: PDF page 1 carries the running foot "76" and the heading "4 GEV".
```

Every page number below is the **printed** page.

Text layer clean. Figures 4.1 (p. 79) and 4.2 (p. 87) are tree diagrams; their
labels are legible and are transcribed below. Table 4.1 (p. 78) is typeset text
and is reproduced in full.

---

## 2. What the chapter is for

GEV is the family of closed-form models that relax logit's independence
assumption without going to simulation. The unifying property (§4.1, p. 76) is
that "the unobserved portions of utility for all alternatives are jointly
distributed as a generalized extreme value", which "allows for correlations over
alternatives and, as its name implies, is a generalization of the univariate
extreme value distribution that is used for standard logit models. When all
correlations are zero, the GEV distribution becomes the product of independent
extreme value distributions and the GEV model becomes standard logit."

The chapter's shape: nested logit in detail (§4.2-4.3), because it is the member
everyone uses and the background for the rest; then overlapping-nest models,
paired combinatorial logit and generalised nested logit (§4.4); heteroskedastic
logit (§4.5); and finally McFadden's (1978) recipe for generating new GEV models
from a function `G` (§4.6).

What we want: the nested logit decomposition in §4.2.3, because it is the exact
formal object our two-factor decomposition resembles; and the parameter counts,
because parameters are what we cannot afford.

---

## 3. Section-by-section walkthrough

### §4.1 Introduction (pp. 76-77)

IIA restated as either a restriction or "the natural outcome of a well-specified
model that captures all sources of correlation over alternatives into
representative utility, so that only white noise remains". When the researcher
cannot capture them, GEV.

Nested logit is "the most widely used member of the GEV family", with a simple
functional form and "a rich set of possible substitution patterns". Train notes
the family is underexploited: "Only a small portion of the possible models within
the GEV class have ever been implemented", citing Karlstrom (2001), who
"specified a GEV model of a different form than had ever been used before and
found that it fitted his data better than previously implemented types of GEV
models". The practical attraction: "GEV models have the advantage that the choice
probabilities usually take a closed form, so that they can be estimated without
resorting to simulation."

### §4.2 Nested Logit (pp. 77-86)

#### §4.2.1 Substitution Patterns (pp. 77-79)

A nested logit is appropriate when the alternatives partition into subsets
(*nests*) such that:

```
  1  For any two alternatives in the SAME nest, the ratio of probabilities is
     independent of the attributes or existence of all other alternatives.
     That is, IIA holds WITHIN each nest.
  2  For any two alternatives in DIFFERENT nests, the ratio of probabilities
     can depend on the attributes of other alternatives in the two nests.
     IIA does not hold in general for alternatives in different nests.
```

The diagnostic question, p. 78: "The relevant question in partitioning these
alternatives is: by what proportion would each probability increase when an
alternative is removed?"

**Table 4.1** (p. 78), reproduced in full — the worked example that makes the
partition visible:

```
  Example of IIA holding within nests of alternatives:
  Change in probabilities when one alternative is removed

                              Probability, with alternative removed
  Alternative   Original   Auto Alone    Carpool      Bus         Rail
  -------------------------------------------------------------------------
  Auto alone      .40         --        .45 (+12.5%) .52 (+30%)  .48 (+20%)
  Carpool         .10      .20 (+100%)     --        .13 (+30%)  .12 (+20%)
  Bus             .30      .48 (+60%)   .33 (+10%)      --       .40 (+33%)
  Rail            .20      .32 (+60%)   .22 (+10%)   .35 (+70%)     --
```

Read the columns. Remove auto alone: bus and rail both rise by 60%, so IIA holds
between them — they form a "transit" nest. Remove bus: auto alone and carpool
both rise by 30%, so they form an "auto" nest. But remove auto alone and carpool
rises 100% while bus and rail rise 60%, so IIA fails across nests. Figure 4.1
(p. 79) is the two-branch tree: root, branches "Auto" and "Transit", twigs
{auto alone, carpool} and {bus, rail}. "There is proportional substitution
across twigs within a branch but not across branches."

#### §4.2.2 Choice Probabilities (pp. 79-81)

Daly & Zachary (1978), McFadden (1978), Williams (1977), independently. `J`
alternatives partitioned into `K` nests `B_1, ..., B_K`. The GEV cumulative
distribution, eq. (4.1), p. 79:

```
  exp( - sum_{k=1}^{K} ( sum_{j in B_k} e^{-eps_nj / lambda_k} )^{lambda_k} )
```

Marginals are univariate extreme value; `eps_nj` correlated with `eps_nm` within
a nest, uncorrelated across nests.

> "The parameter `lambda_k` is a measure of the degree of independence in
> unobserved utility among the alternatives in nest `k`. A higher value of
> `lambda_k` means greater independence and less correlation. The statistic
> `1 - lambda_k` is a measure of correlation ... As McFadden (1978) points out,
> the correlation is actually more complex than `1 - lambda_k`, but
> `1 - lambda_k` can be used as an indication of correlation. A value of
> `lambda_k = 1` indicates complete independence within nest `k`, that is, no
> correlation."
> — §4.2.2, pp. 79-80

Choice probability, eq. (4.2), p. 80:

```
              e^{V_ni/lambda_k} ( sum_{j in B_k} e^{V_nj/lambda_k} )^{lambda_k - 1}
  P_ni  =  ------------------------------------------------------------------------
            sum_{l=1}^{K} ( sum_{j in B_l} e^{V_nj/lambda_l} )^{lambda_l}
```

When `lambda_k = 1` for all `k`, this collapses to standard logit. The ratio
argument on p. 80 shows IIA holds within a nest (the parenthesised factors
cancel) and not across (they do not), and that the cross-nest ratio "does not
depend on the attributes of alternatives in nests other than those containing
`i` and `m`. A form of IIA holds, therefore, even for alternatives in different
nests. This form of IIA can be loosely described as 'independence from
irrelevant nests' or IIN."

**The admissible range of `lambda`** (p. 81), which is a real estimation
constraint:

> "The value of `lambda_k` must be within a particular range for the model to be
> consistent with utility-maximizing behavior. If `lambda_k` for all `k` is
> between zero and one, the model is consistent with utility maximization for all
> possible values of the explanatory variables. For `lambda_k` greater than one,
> the model is consistent with utility-maximizing behavior for some range of the
> explanatory variables but not for all values. A negative value of `lambda_k` is
> inconsistent with utility maximization and implies that improving the attributes
> of an alternative (such as lowering its price) can decrease the probability of
> the alternative being chosen."

`lambda_k` may be constrained equal across nests, and testing `lambda_k = 1` for
all `k` "is equivalent to testing whether the standard logit model is a
reasonable specification against the more general nested logit", via the
likelihood ratio statistic of §3.8.2. Bhat (1997a) allows `lambda = exp(alpha' z_n)`
so correlations vary with observed characteristics, the exponential guaranteeing
positivity.

#### §4.2.3 Decomposition into Two Logits (pp. 81-84)

**The section that matters most to us.** Decompose observed utility into a part
constant within a nest and a part varying within it, eq. (4.3), p. 82:

```
  U_nj = W_nk + Y_nj + eps_nj     for j in B_k

    W_nk  depends only on variables that describe nest k.  These variables
          differ over nests but not over alternatives within each nest.
    Y_nj  depends on variables that describe alternative j.  These variables
          vary over alternatives within nest k.
```

"Note that this decomposition is fully general, since for any `W_nk`, `Y_nj` is
defined as `V_nj - W_nk`."

Then `P_ni = P_{ni | B_k} P_{n B_k}` exactly, and both factors are logits,
eqs. (4.4)-(4.5), p. 82:

```
  P_{n B_k}    =  e^{W_nk + lambda_k I_nk} / sum_{l=1}^{K} e^{W_nl + lambda_l I_nl}   (4.4)

  P_{ni | B_k} =  e^{Y_ni / lambda_k} / sum_{j in B_k} e^{Y_nj / lambda_k}            (4.5)

  where        I_nk = ln sum_{j in B_k} e^{Y_nj / lambda_k}
```

Terminology, p. 83: the marginal probability (choice of nest) is the **upper
model**, the conditional probability (choice within the nest) is the **lower
model**. `I_nk` is the **inclusive value**, **inclusive utility**, or **log-sum
term** of nest `B_k`, and `lambda_k` is the **log-sum coefficient**.

The interpretation is the link back to §3.5:

> "Recall from the discussion of consumer surplus for a logit model
> (Section 3.5) that the log of the denominator of the logit model is the
> expected utility that the decision maker obtains from the choice situation, as
> shown by Williams (1977) and Small and Rosen (1981). The same interpretation
> applies here: `lambda_k I_nk` is the expected utility that decision maker `n`
> receives from the choice among the alternatives in nest `B_k`."
> — §4.2.3, p. 83

And the economic reading of the upper model, pp. 83-84: "the probability of
choosing nest `B_k` depends on the expected utility that the person receives
from that nest. This expected utility includes the utility that he receives no
matter which alternative he chooses in the nest, which is `W_nk`, plus the
expected extra utility that he receives by being able to choose the best
alternative in the nest, which is `lambda_k I_nk`."

A specification warning (p. 84). Some software does not divide the lower-model
coefficients by `lambda_k`; STATA's `nlogit` is named. Koppelman & Wen (1998) and
Hensher & Greene (2002) show the undivided model "is not consistent with utility
maximization when any coefficients are common across nests (such as a cost
coefficient that is the same for bus and car modes)". Heiss (2002) gives the
converse: with no common coefficients it is consistent, because the division is
accomplished implicitly.

#### §4.2.4 Estimation (pp. 84-85)

Simultaneous maximum likelihood on eq. (4.2) is "consistent and efficient
(Brownstone and Small, 1989)". A warning we must carry over:

> "Numerical maximization is sometimes difficult, since the log-likelihood
> function is not globally concave and even in concave areas is not close to a
> quadratic. The researcher may need to help the routines by trying different
> algorithms and/or starting values, as discussed in Chapter 8."
> — §4.2.4, pp. 84-85

**Sequential estimation** — fit the lower models, compute `I_nk`, then fit the
upper model with `I_nk` as a regressor — is consistent but not efficient, and
has two named defects (p. 85):

1. "the standard errors of the upper-model parameters are biased downward, as
   Amemiya (1978) first pointed out. This bias arises because the variance of the
   inclusive value estimate that enters the upper model is not incorporated into
   the calculation of standard errors. With downwardly biased standard errors,
   smaller confidence bounds and larger `t`-statistics are estimated for the
   parameters than are true, and the upper model will appear to be better than it
   actually is." Ben-Akiva & Lerman (1985, p. 298) give a correction.
2. Common parameters appearing in several submodels get separate estimates.

Train's verdict: "Since commercial software is available for simultaneous
estimation, there is little reason to estimate a nested logit sequentially." The
decomposition's real value "comes not in its use as an estimation tool but
rather as an heuristic device: the decomposition helps greatly in understanding
the meaning and structure of the nested logit model."

#### §4.2.5 Equivalence of Nested Logit Formulas (p. 86)

Six lines of algebra verifying `P_{ni|B_k} P_{n B_k} = P_ni` from eq. (4.2),
using `e^x b^c = e^{x + c ln b}`. Complete in the text.

### §4.3 Three-Level Nested Logit (pp. 86-88)

Partition into nests, then each nest into subnets. The San Francisco housing
example (Figure 4.2, p. 87): neighbourhoods (Nob Hill, Haight Ashbury, Telegraph
Hill, Mission District) at the top, number of bedrooms (1, 2, 3+) in the middle,
individual housing units at the bottom. The motivation is that unobserved factors
are common within a neighbourhood *and* common within a size class, "even more
highly correlated among units of the same size in the same neighborhood than
between units of different size in the same neighborhood".

Parameters: `lambda_k` for nest `k`, `sigma_mk` for subnest `m` of nest `k`. In
the logit decomposition, `sigma_mk` is the coefficient of the inclusive value in
the middle model and `lambda_k sigma_mk` the coefficient in the top model.
Consistency: "If `0 < lambda_k < 1` and `0 < sigma_mk < 1`, then the model is
consistent with utility maximization for all levels of the explanatory
variables."

The three IIA statements on p. 88 are worth reading once for the intuition about
what nesting does and does not buy; they are reproduced in the source and not
repeated here.

### §4.4 Overlapping Nests (pp. 89-92)

Motivation: carpooling shares unobserved attributes with auto alone (private
vehicle) *and* with bus and rail (fixed schedule). "It would be useful for the
carpool alternative to be in two nests."

**§4.4.1 Paired Combinatorial Logit** (pp. 90-91), Chu (1981, 1989). Every *pair*
of alternatives is a nest, so each alternative is in `J - 1` nests, with
`lambda_ij` per pair. Probability at eq. (4.6). "PCL becomes a standard logit
when `lambda_ij = 1` for all pairs." Koppelman & Wen (2000) found PCL beat both
nested and standard logit in their application. The parameter arithmetic, p. 91:
a PCL has `J(J-1)/2` lambdas, "The number of lambda's exceeds the number of
identifiable covariance parameters by exactly one", so at least one constraint
is needed, usually normalising one lambda to 1. And: "With a large number of
alternatives, the researcher will probably need to impose some form of structure
on the `lambda_ij`'s, simply to avoid the proliferation of parameters."

**§4.4.2 Generalized Nested Logit** (pp. 91-92), Wen & Koppelman (2001). An
*allocation* parameter `alpha_jk >= 0` "reflects the extent to which alternative
`j` is a member of nest `k`", normalised `sum_k alpha_jk = 1`. Probability at
eq. (4.7). Reduces to nested logit when each alternative is in one nest with
`alpha = 1`, and to logit when additionally `lambda_k = 1`. Decomposes as
`P_ni = sum_k P_{ni|B_k} P_{nk}`.

### §4.5 Heteroskedastic Logit (p. 92)

Steckel & Vanhonacker (1988), Bhat (1995), Recker (1995). HEV: no correlation,
but `eps_nj` has variance `(theta_j pi)^2 / 6` differing by alternative. One
variance normalised to `pi^2/6`. No closed form; the probability is a
one-dimensional integral over the extreme value density, simulable in three
steps or, per Bhat (1995), computable "effectively with quadrature rather than
simulation" since the integral is one-dimensional.

### §4.6 The GEV Family (pp. 93-96)

McFadden's (1978) recipe. Let `Y_j = exp(V_j)`, necessarily positive, and let
`G = G(Y_1, ..., Y_J)` with `G_i = dG/dY_i`. If `G` satisfies four properties,
then

```
  P_i = Y_i G_i / G                                        (4.8)
```

is a choice probability consistent with utility maximisation, and "Any model
that can be derived in this way is a GEV model. This formula therefore defines
the family of GEV models."

The four properties, p. 93:

```
  1  G >= 0 for all positive values of Y_j.
  2  G is homogeneous of degree one: G(rho Y_1, ..., rho Y_J) = rho G(...).
     (Ben-Akiva and Francois (1983) showed this can be relaxed to allow any
      degree of homogeneity.)
  3  G -> infinity as Y_j -> infinity for any j.
  4  The cross partial derivatives change signs in a particular way:
     G_i >= 0 for all i;  G_ij = dG_i/dY_j <= 0 for all j != i;
     G_ijk = dG_ij/dY_k >= 0 for any distinct i, j, k; and so on.
```

Train is candid about property 4: "There is little economic intuition to motivate
these properties, particularly the last one." And balanced about what that costs
and buys: "The disadvantage is that the researcher has little guidance on how to
specify a `G` that provides a model that meets the needs of his research. The
advantage is that the purely mathematical approach allows the researcher to
generate models that he might not have developed while relying only on his
economic intuition."

Three derivations follow, each complete:

```
  LOGIT           G = sum_{j=1}^{J} Y_j                       p. 94
                  All four properties verified explicitly.
                  P_i = Y_i / sum_j Y_j = e^{V_i} / sum_j e^{V_j}.

  NESTED LOGIT    G = sum_{l=1}^{K} ( sum_{j in B_l} Y_j^{1/lambda_l} )^{lambda_l}
                  with each lambda between zero and one.      pp. 94-95
                  G_i and G_im computed; G_ij <= 0 requires lambda_k <= 1;
                  higher cross-partials work "if 0 < lambda_k <= 1".
                  Recovers eq. (4.2).

  PCL             G = sum_{k=1}^{J-1} sum_{l=k+1}^{J}
                        ( Y_k^{1/lambda_kl} + Y_l^{1/lambda_kl} )^{lambda_kl}   p. 96
                  Recovers eq. (4.6).

  GNL             G = sum_{k=1}^{K} ( sum_{j in B_k} (alpha_jk Y_j)^{1/lambda_k} )^{lambda_k}
                  Stated; the reader is invited to verify.    p. 96
```

Closing line of the chapter, p. 96: "Using the same process, researchers can
generate other GEV models."

---

## 4. Verbatim quotes for anything load-bearing

### 4.1 §4.2.3, p. 83 — the inclusive value is an expected utility

> "Recall from the discussion of consumer surplus for a logit model
> (Section 3.5) that the log of the denominator of the logit model is the
> expected utility that the decision maker obtains from the choice situation, as
> shown by Williams (1977) and Small and Rosen (1981). The same interpretation
> applies here: `lambda_k I_nk` is the expected utility that decision maker `n`
> receives from the choice among the alternatives in nest `B_k`. ... `I_nk` is
> often called the *inclusive value* or *inclusive utility* of nest `B_k`. It is
> also called the 'log-sum term' because it is the log of a sum (of
> exponentiated representative utilities)."

### 4.2 §4.2.2, p. 81 — the admissible range of lambda

> "The value of `lambda_k` must be within a particular range for the model to be
> consistent with utility-maximizing behavior. If `lambda_k` for all `k` is
> between zero and one, the model is consistent with utility maximization for all
> possible values of the explanatory variables. For `lambda_k` greater than one,
> the model is consistent with utility-maximizing behavior for some range of the
> explanatory variables but not for all values. A negative value of `lambda_k` is
> inconsistent with utility maximization and implies that improving the
> attributes of an alternative (such as lowering its price) can decrease the
> probability of the alternative being chosen."

### 4.3 §4.2.4, pp. 84-85 — nested logit is not globally concave either

> "Numerical maximization is sometimes difficult, since the log-likelihood
> function is not globally concave and even in concave areas is not close to a
> quadratic. The researcher may need to help the routines by trying different
> algorithms and/or starting values, as discussed in Chapter 8."

### 4.4 §4.2.4, p. 85 — sequential estimation understates the standard errors

> "First, the standard errors of the upper-model parameters are biased downward,
> as Amemiya (1978) first pointed out. This bias arises because the variance of
> the inclusive value estimate that enters the upper model is not incorporated
> into the calculation of standard errors. With downwardly biased standard
> errors, smaller confidence bounds and larger `t`-statistics are estimated for
> the parameters than are true, and the upper model will appear to be better than
> it actually is."

### 4.5 §4.2.4, p. 85 — the decomposition's real value

> "The main value of the decomposition of the nested logit into its upper and
> lower components comes not in its use as an estimation tool but rather as an
> heuristic device: the decomposition helps greatly in understanding the meaning
> and structure of the nested logit model."

### 4.6 §4.2.3, p. 82 — the decomposition is fully general

> "Note that this decomposition is fully general, since for any `W_nk`, `Y_nj`
> is defined as `V_nj - W_nk`."

### 4.7 §4.4.1, p. 91 — parameter proliferation

> "With a large number of alternatives, the researcher will probably need to
> impose some form of structure on the `lambda_ij`'s, simply to avoid the
> proliferation of parameters that arises with large `J`. This proliferation of
> parameters, one for each pair of alternatives, is what makes the PCL so
> flexible. The researcher's goal is to apply this flexibility meaningfully for
> his particular situation."

---

## 5. Definitions the chapter gives formally

```
  NESTED LOGIT, WHEN APPROPRIATE                            §4.2.1, p. 77
    The alternatives partition into nests such that
      (1) for any two alternatives in the SAME nest, the ratio of
          probabilities is independent of the attributes or existence of
          all other alternatives -- IIA holds within each nest;
      (2) for any two alternatives in DIFFERENT nests, the ratio of
          probabilities can depend on the attributes of other alternatives
          in the two nests -- IIA does not hold in general across nests.

  GEV DISTRIBUTION FOR NESTED LOGIT                   §4.2.2, p. 79, (4.1)
      exp( - sum_{k=1}^{K} ( sum_{j in B_k} e^{-eps_nj / lambda_k} )^{lambda_k} )

  NESTED LOGIT PROBABILITY                            §4.2.2, p. 80, (4.2)
      P_ni = e^{V_ni/lambda_k} ( sum_{j in B_k} e^{V_nj/lambda_k} )^{lambda_k - 1}
             / sum_{l=1}^{K} ( sum_{j in B_l} e^{V_nj/lambda_l} )^{lambda_l}
    Collapses to standard logit when lambda_k = 1 for all k.

  LAMBDA                                                  §4.2.2, pp. 79-80
    "a measure of the degree of independence in unobserved utility among the
     alternatives in nest k. A higher value of lambda_k means greater
     independence and less correlation."  1 - lambda_k indicates correlation.

  IIN -- INDEPENDENCE FROM IRRELEVANT NESTS                 §4.2.2, p. 80
    The ratio of probabilities for alternatives in different nests "does not
    depend on the attributes of alternatives in nests other than those
    containing i and m".

  UTILITY DECOMPOSITION                               §4.2.3, p. 82, (4.3)
      U_nj = W_nk + Y_nj + eps_nj   for j in B_k
      W_nk  varies over nests, not within them
      Y_nj  varies over alternatives within nest k
    "fully general, since for any W_nk, Y_nj is defined as V_nj - W_nk."

  UPPER AND LOWER MODELS                        §4.2.3, p. 82, (4.4)-(4.5)
      P_{n B_k}    = e^{W_nk + lambda_k I_nk} / sum_l e^{W_nl + lambda_l I_nl}
      P_{ni | B_k} = e^{Y_ni/lambda_k} / sum_{j in B_k} e^{Y_nj/lambda_k}
      P_ni = P_{ni | B_k} P_{n B_k}

  INCLUSIVE VALUE / LOG-SUM TERM                            §4.2.3, p. 82
      I_nk = ln sum_{j in B_k} e^{Y_nj / lambda_k}
    lambda_k is the LOG-SUM COEFFICIENT.  lambda_k I_nk is the expected
    utility from the choice among the alternatives in nest B_k.

  THREE-LEVEL CONSISTENCY CONDITION                          §4.3, p. 88
      0 < lambda_k < 1 and 0 < sigma_mk < 1.

  PCL PROBABILITY                                    §4.4.1, p. 90, (4.6)
      one lambda_ij per PAIR; each alternative is in J - 1 nests;
      J(J-1)/2 lambdas, one more than the identifiable covariance
      parameters, so at least one normalisation is required.

  GNL ALLOCATION PARAMETER                              §4.4.2, pp. 91-92
      alpha_jk >= 0, "reflects the extent to which alternative j is a member
      of nest k", normalised sum_k alpha_jk = 1 for all j.

  HEV                                                        §4.5, p. 92
      eps_nj independent extreme value with variance (theta_j pi)^2 / 6;
      one variance normalised to pi^2/6.  No closed form; one-dimensional
      integral, computable by quadrature (Bhat 1995).

  THE GEV FAMILY                                       §4.6, p. 93, (4.8)
      With Y_j = exp(V_j) and G_i = dG/dY_i,  P_i = Y_i G_i / G
      for any G satisfying the four properties (nonnegativity, homogeneity
      of degree one, G -> infinity as any Y_j -> infinity, and the
      alternating-sign condition on cross partials).
      "Any model that can be derived in this way is a GEV model."
```

---

## 6. What this means for siting-atlas

### 6.1 Our two-factor decomposition IS the nested logit decomposition, and we should stop pretending otherwise

[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.3 states the derived
answer as

```
  P(your ZIP gets same-day service)
    =  P(a station opens in your metro)         from base rates
    x  P(the chosen site is within 15 miles)    from the choice model
```

Set that beside eq. (4.4)-(4.5) with **metros as nests** and **ZCTAs as
alternatives within a nest**, and it is the same object: a marginal probability
of choosing a nest times a conditional probability of choosing within it.
Train's `P_ni = P_{ni | B_k} P_{n B_k}` (p. 82) is the exact formal statement,
and "This equality is exact, since any probability can be written as the product
of a marginal and a conditional probability."

Two consequences, one comforting and one not.

**Comforting: the factorisation is not an ad hoc hack.** It is the standard
decomposition of a nested logit, and Train supplies the interpretation — the
upper model's `lambda_k I_nk` is the expected utility from the choice among the
alternatives in the nest (§4.1 above). Our write-up can say so.

**Not comforting: we are not fitting the upper model, so it is not a nested
logit and must not be called one.** We estimate only the lower model
(`P_{ni|B_k}`, which ZCTA given a station opens in metro `m`), and supply the
first factor from base rates rather than from a fitted `P_{n B_k}`. There is no
`lambda_k`, no inclusive value is computed, and no information flows from the
lower model to the upper one. **Anyone who describes the result as a nested logit
is overstating it.** `MODEL_SPEC.md` §10.5 records this.

A small mercy: because we do not fit an upper model at all, Amemiya's
downward-biased standard errors (§4.4 above) do not arise. Train's warning is
about *sequential estimation of both levels*; we estimate one level. But the
moment anyone fits the metro-choice factor as a logit with a log-sum regressor,
the bias appears and Ben-Akiva & Lerman (1985, p. 298) is the correction.

### 6.2 Nested logit is the right repair for our IIA problem, and we cannot afford it

Adjacent ZCTAs are near-perfect substitutes for a delivery station — two miles
apart, almost the same catchment — so logit's proportional substitution
(Ch. 3 §3.3.2) is implausible here. §4.2.1's diagnostic question, "by what
proportion would each probability increase when an alternative is removed?", has
an obvious answer in our setting: remove a ZCTA and its immediate neighbours
should absorb almost all of its probability, not every ZCTA in the metro
proportionately.

So a nested logit is indicated. **We do not fit one, on parameter grounds.**
Each nest adds a `lambda_k`, and `MODEL_SPEC.md` §8 records 5.6 effective /
7.6 optimistic events per parameter against a floor of 10 at the retired model's
five parameters. The whole design of the successor specification is three
parameters. Adding one `lambda` per metro to a ten-metro frame would add ten.

Worth stating precisely what the cheaper variants would cost, because "we cannot
afford it" should be a number and not a shrug:

```
  standard logit, our spec            3 parameters
  + one common lambda across metros   4       the cheapest relaxation; tests
                                              IIA with a single extra df
  + one lambda per metro (10 metros) 13       not affordable
  PCL over ZCTAs                J(J-1)/2      absurd here: J is in the
                                              hundreds per metro
  GNL                          + alpha_jk     worse
```

**The four-parameter version is the one to try first if anything is tried.**
Train notes `lambda_k` "can be constrained to be the same for all (or some)
nests" (p. 81), and testing `lambda = 1` against the standard logit is a
one-restriction likelihood ratio test (§3.8.2). That is a defensible, cheap
diagnostic — it asks "is the metro-level correlation detectable at all?" — and
it does not commit us to a per-metro nest structure. Logged as the first
extension, not done.

### 6.3 A second, more honest nesting exists and nobody has considered it

Figure 4.2's three-level housing example (p. 87) — neighbourhood, then number of
bedrooms, then unit — is suggestive. The natural analogue for us is not
metro/ZCTA at all; it is **distance band**, because the correlated unobservable
is proximity to the existing network, not the metro. Small's (1987) OGEV, cited
at §4.4 (p. 89), is built for exactly this: alternatives with a natural order,
"such as the number of cars that a household owns (0, 1, 2, 3, ...) or the
destination for shopping trips, with the shopping areas ordered by distance from
the household's home", where "the correlation in unobserved utility between any
two alternatives depends on their proximity in the ordering".

That is our problem described by someone else, in Train's own list of examples,
and it is a better structural story than metro nests. It is recorded here and
nowhere else in the repo. It is also unaffordable. If the national frame is ever
promoted (104 stations, 62 CBSAs), this is the specification to reach for, and
Small (1987) is the paper to read — it is **not** in `../Research/`.

### 6.4 §4.2.4's concavity warning compounds one we already have

Train says the nested logit log-likelihood "is not globally concave and even in
concave areas is not close to a quadratic" (§4.3 above). Our specification is
already non-concave for a different reason — `V = ln(beta'a)` is nonlinear in
parameters (Ch. 3 §3.4, p. 52). Should anyone combine the two, the multiple-
starting-values requirement in `MODEL_SPEC.md` §6.2 becomes more important, not
less, and the number of starts should go up.

### 6.5 What this chapter does NOT support

- It does not support calling anything we currently plan a "GEV model". We plan
  a standard logit with a nonlinear-in-parameters representative utility. That
  is a logit, and §4.6 shows logit is the GEV member with `G = sum_j Y_j`, but
  calling it GEV would be technically true and rhetorically misleading.
- It gives no guidance on sample size. Nothing in the chapter says how many
  observations a `lambda` needs. Our refusal to fit one is an argument from the
  events-per-parameter arithmetic in `MODEL_SPEC.md` §8, not from Train.
- Heteroskedastic logit (§4.5) is *not* the answer to our problem. It allows
  variances to differ across alternatives but imposes "no correlation in
  unobserved factors over alternatives" (p. 92), and correlation is exactly what
  adjacent ZCTAs have.

---

## 7. What I did NOT read, or did not understand

- **Every page of Chapter 4 was opened**, PDF pages 1-21, as rendered images, in
  two passes (1-20, 21). No stretch was skimmed.
- **The §4.2.5 equivalence algebra (p. 86) I read and followed** — the six-line
  chain from eq. (4.2) to `P_{ni|B_k} P_{nB_k}`, turning on
  `e^x b^c = e^{x + c ln b}` — but I did not re-derive it independently.
- **The §4.6 verifications of the four `G` properties** for logit (p. 94) and
  nested logit (pp. 94-95) I read line by line. For nested logit I can state
  that `G_i >= 0` follows from `Y_j >= 0`, and that `G_im <= 0` requires
  `lambda_k <= 1` because the factor is `(lambda_k - 1)/lambda_k`. I did **not**
  verify the higher-order cross-partials; Train asserts they "exhibit the
  required property if `0 < lambda_k <= 1`" and computes none of them, so
  neither can I. The PCL derivation (p. 96) I followed; the GNL derivation is
  left to the reader in the text and I did not attempt it.
- **Figures 4.1 (p. 79) and 4.2 (p. 87) are tree diagrams.** Labels transcribed
  from the rendered images: Figure 4.1 has branches "Auto" and "Transit" over
  twigs "Auto alone", "Carpool", "Bus", "Rail"; Figure 4.2 has "Neighborhood"
  (Nob Hill, Haight Ashbury, Telegraph Hill, Mission District), "Number of
  bedrooms" (1, 2, 3+) and "Housing unit". No numerical content.
- **Table 4.1 (p. 78) is transcribed above from the rendered image.** I checked
  the internal consistency of two cells: `.40 -> .52` is `+30%` and
  `.30 -> .48` is `+60%`, both as printed. The remaining cells were transcribed
  once.
- **§4.3's three IIA statements (p. 88) were read but are summarised rather than
  quoted.** They are three paragraphs about Pacific Heights and Russian Hill;
  nothing in our analysis turns on them.
- **§4.4.1's eq. (4.6) and §4.4.2's eq. (4.7)** I transcribed structurally but
  did not manipulate. I can say what they reduce to in the limiting cases
  because Train says so; I have not checked those limits myself.
- **Cited works not consulted, none in `../Research/`:** Ben-Akiva (1973), Train
  (1986), Train et al. (1987a), Forinash & Koppelman (1993), Lee (1999),
  Karlstrom (2001), Daly & Zachary (1978), McFadden (1978), Williams (1977),
  Kling & Herriges (1995), Herriges & Kling (1996), Bhat (1997a, 1995), Tversky
  (1972), Daly (1987), Greene (2000), Koppelman & Wen (1998, 2000), Hensher &
  Greene (2002), Heiss (2002), Brownstone & Small (1989), Amemiya (1978),
  Ben-Akiva & Lerman (1985), Vovsha (1997), Bierlaire (1998), Ben-Akiva &
  Bierlaire (1999), Small (1987, 1994), Bhat (1998b), Chu (1981, 1989), Wen &
  Koppelman (2001), Steckel & Vanhonacker (1988), Recker (1995), Ben-Akiva &
  Francois (1983). Everything attributed to them is Train's characterisation.
  **Small (1987) on OGEV is the one I most wish I had**, for the reason in §6.3.
- **Not verified:** my claim in §6.3 that a distance-band nesting is a better
  structural story than metro nests. That is my judgement from reading Train's
  one-sentence description of OGEV, not a result, and it is labelled as such.
