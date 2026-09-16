# Notes — Train (2009) Ch. 3, Logit

*Read in full on 2026-09-13, every page, as images. This is the chapter that
carries §3.4 Example 2 — the `V = ln(beta'a)` result the whole reframe rests on
— and §3.8.1, the "percent correctly predicted" passage the project has now got
wrong twice. It also carries, in §3.7.1, the sentence our documents should have
been citing instead of §2.2.*

---

## 1. Citation and local file

```
  Kenneth E. Train, Discrete Choice Methods with Simulation, 2nd edition.
  Cambridge University Press, 2009.  Chapter 3, "Logit", printed pp. 34-75.

  Local file:  ../Research/Ch03_p34-75.pdf   (42 PDF pages)
  PDF page 1 = printed p. 34 (the chapter opening).
  So: PDF page = printed page - 33.  Printed p. 75 = PDF page 42.
  Verified: PDF page 21 carries the running head "54  Behavioral Models" and
  the heading "Example 2: Geographic Aggregation".
```

Every page number below is the **printed** page.

Text layer clean. Figure 3.1 (p. 38, the logit sigmoid) and the tree diagrams
are line drawings with legible labels; Tables 3.1 (p. 72) and 3.2 (p. 74) are
typeset text and are reproduced in full below.

---

## 2. What the chapter is for

Logit is the workhorse and this chapter is the complete treatment: where the
closed form comes from, what it can and cannot represent, how to estimate it,
and how to judge the result.

Four things we specifically wanted from it, all of which it delivered:

1. **§3.4 Example 2** — whether zonal alternatives really require
   `V = ln(beta' a)`. They do, with caveats our documents omit. This is the
   single most load-bearing page in the project's reading list.
2. **§3.7.1** — the likelihood, including the independence assumption that the
   retired hazard model violated, and the sampled-alternatives result that makes
   a large choice set estimable.
3. **§3.8.1** — goodness of fit, and the "percent correctly predicted" sentence.
4. **§3.3.2** — IIA, because adjacent ZCTAs are near-perfect substitutes and we
   need to know exactly how bad that is.

---

## 3. Section-by-section walkthrough

### §3.1 Choice Probabilities (pp. 34-40)

Provenance first: Luce (1959) derived the formula from IIA axioms; Marschak
(1960) showed it consistent with utility maximisation; Marley (cited via Luce &
Suppes 1965) showed extreme value leads to logit; McFadden (1974) proved the
converse, that the logit formula "necessarily implies that unobserved utility is
distributed extreme value".

Each `eps_nj` iid extreme value (Gumbel, type I extreme value, "and sometimes,
mistakenly, Weibull"), density and CDF at eqs. (3.1)-(3.2), p. 34:

```
  f(eps_nj) = e^{-eps_nj} e^{-e^{-eps_nj}}          (3.1)
  F(eps_nj) = e^{-e^{-eps_nj}}                      (3.2)
```

Variance `pi^2 / 6`. The mean is not zero but "the mean is immaterial, since
only differences in utility matter". The difference of two extreme value
variables is logistic, eq. (3.3).

**The independence assumption, and Train's unusual defence of it** (pp. 35-36).
The key assumption "is not so much the shape of the distribution as that the
errors are independent of each other". Then:

> "It is important to realize that the independence assumption is not as
> restrictive as it might at first seem, and in fact can be interpreted as a
> natural outcome of a well-specified model. ... Under independence, the error
> for one alternative provides no information to the researcher about the error
> for another alternative. Stated equivalently, the researcher has specified
> `V_nj` sufficiently that the remaining, unobserved portion of utility is
> essentially 'white noise.' In a deep sense, the ultimate goal of the researcher
> is to represent utility so well that the only remaining aspects constitute
> simply white noise; that is, the goal is to specify utility well enough that a
> logit model is appropriate. Seen in this way, the logit model is the ideal
> rather than a restriction."
> — §3.1, pp. 35-36

Three options if the researcher thinks the errors *are* correlated (p. 36): a
different model (Chs. 4-6), respecify `V` so the source of correlation is
captured explicitly, or use logit as an approximation. "Violations of the logit
assumptions seem to have less effect when estimating average preferences than
when forecasting substitution patterns."

Derivation sketched at eqs. (3.4)-(3.6), pp. 36-37, with the full algebra
deferred to §3.10:

```
  P_ni = e^{V_ni} / sum_j e^{V_nj}                  (3.6)
```

Linear-in-parameters form `V_nj = beta' x_nj` (p. 37), and the fact that will
matter later: "McFadden (1974) demonstrated that the log-likelihood function
with these choice probabilities is globally concave in parameters `beta`".

Properties (pp. 37-38): `P_ni` strictly between 0 and 1, never exactly zero
("If the researcher believes that an alternative has actually no chance of being
chosen by a decision maker, the researcher can exclude that alternative from the
choice set"); probabilities sum to one automatically; the relation to `V` is
sigmoid (Figure 3.1, p. 38), so the effect of a change in a covariate is largest
when `P` is near 0.5 and small near 0 or 1. The policy gloss is worth keeping:
improving bus service "in areas where the service is so poor that few travelers
take the bus would be less effective ... than making the same improvement in
areas where bus service is already sufficiently good".

Gas/electric heating worked example, eqs. (3.7) and the binary form, pp. 38-40.
Willingness to pay as `beta_2 / beta_1`, with the derivation via
`dU = beta_1 dPP + beta_2 dOC = 0`. The oil-heater extension shows the
denominator growing and every other probability falling.

### §3.2 The Scale Parameter (pp. 40-42)

`U*_nj = V_nj + eps*_nj` with `Var(eps*) = sigma^2 (pi^2/6)`. Divide by `sigma`:

```
  P_ni = e^{V_ni / sigma} / sum_j e^{V_nj / sigma}
```

so with linear utility the estimated coefficients are `beta = beta* / sigma`.

> "Only the ratio `beta*/sigma` can be estimated; `beta*` and `sigma` are not
> separately identified."
> — §3.2, p. 41

"A larger variance in unobserved factors leads to smaller coefficients, even if
the observed factors have the same effect on utility." Ratios of coefficients
are unaffected, so willingness to pay and values of time are safe; only
magnitudes are affected. Heteroskedastic extension with `k = (sigma^C/sigma^B)^2`
estimated alongside `beta`, p. 41.

### §3.3 Power and Limitations of Logit (pp. 42-52)

The three-point summary on p. 42, verbatim:

```
  1  Logit can represent systematic taste variation (that is, taste variation
     that relates to observed characteristics of the decision maker) but not
     random taste variation (differences in tastes that cannot be linked to
     observed characteristics).
  2  The logit model implies proportional substitution across alternatives,
     given the researcher's specification of representative utility. To
     capture more flexible forms of substitution, other models are needed.
  3  If unobserved factors are independent over time in repeated choice
     situations, then logit can capture the dynamics of repeated choice,
     including state dependence. However, logit cannot handle situations
     where unobserved factors are correlated over time.
```

#### §3.3.1 Taste Variation (pp. 42-45)

Car-choice example with shoulder room `SR_j` and purchase price `PP_j`,
eq. (3.8). If `alpha_n = rho M_n` (household size) and `beta_n = theta / I_n`
(income), substitution gives
`U_nj = rho(M_n SR_j) + theta(PP_j / I_n) + eps_nj` — a standard logit with two
interaction terms. Systematic taste variation is fine.

If instead `alpha_n = rho M_n + mu_n` with `mu_n` unobserved, the new error
`eps~_nj = mu_n SR_j + eta_n PP_j + eps_nj` is necessarily correlated over
alternatives and heteroskedastic: `Var(eps~_nj)` "is different for different
`j`". Logit is then a misspecification. "As an approximation, logit might be
able to capture the average tastes fairly well ... However, there is no
guarantee."

#### §3.3.2 Substitution Patterns (pp. 45-50)

**IIA.** For any `i`, `k`: `P_ni / P_nk = e^{V_ni - V_nk}`, which "does not
depend on any alternatives other than `i` and `k`".

**Red-bus/blue-bus** (pp. 46-47) in full. Car and blue bus at `P = 1/2` each.
Introduce an identical red bus; logit is forced to `1/3, 1/3, 1/3`, whereas the
sensible answer is `1/2, 1/4, 1/4`. "the logit model, because of its IIA
property, overestimates the probability of taking either of the buses and
underestimates the probability of taking a car." Train concedes the example is
"rather stark and unlikely to be encountered in the real world" but the same
mispredicting arises "whenever the ratio of probabilities for two alternatives
changes with the introduction or change of another alternative".

**Proportional substitution** (pp. 47-48). Cross-elasticity
`E_{iz_nj} = -beta_z z_nj P_nj`, which "is the same for all `i`: `i` does not
enter the formula". So "an improvement in one alternative draws proportionately
from the other alternatives". The California Energy Commission example
(pp. 48): large gas .66, small gas .33, small electric .01; subsidise the
electric car to .10 and logit drops both gas cars by exactly ten percent, so the
.09 gain comes twice as much from large gas (.06) as from small gas (.03). "This
pattern of substitution is clearly unrealistic."

**Advantages of IIA** (pp. 48-49). Two, and the first is the one we need: IIA
makes it "possible to estimate model parameters consistently on a subset of
alternatives for each sampled decision maker". Second, a researcher interested
only in a subset of alternatives can estimate on that subset and exclude
decision makers who chose others.

**Tests of IIA** (pp. 49-50). Hausman & McFadden (1984) subset test; McFadden
(1987) cross-alternative-variable regression test; and testing `lambda = 1` in a
nested logit or zero mixing variance in a mixed logit. The trade-off is stated:
the newer tests assume the more general model is itself correctly specified,
while the older ones "operate under less restrictive maintained hypotheses" but
"do not provide as much guidance on the correct specification to use instead of
logit" when IIA fails.

#### §3.3.3 Panel Data (pp. 50-52)

If unobserved factors are independent over repeated choices, "logit can be used
to examine panel data in the same way as purely cross-sectional data" and "Each
choice situation by each decision maker becomes a separate observation",
eq. (3.9). Lagged dependent variables may be entered —
`V_njt = alpha y_nj(t-1) + beta x_njt` — and "The inclusion of a lagged dependent
variable does not induce inconsistency in estimation, since for a logit model
the errors are assumed to be independent over time." Train closes honestly:
"Of course, the assumption of independent errors over time is severe."

### §3.4 Nonlinear Representative Utility (pp. 52-54)

**The chapter's most important two pages for this project.**

Opening warning, p. 52:

> "In some contexts, the researcher will find it useful to allow parameters to
> enter representative utility nonlinearly. Estimation is then more difficult,
> since the log-likelihood function may not be globally concave and computer
> routines are not as widely available as for logit models with
> linear-in-parameters utility. However, the aspects of behavior that the
> researcher is investigating may include parameters that are interpretable only
> when they enter utility nonlinearly. In these cases, the effort of writing
> one's own code can be warranted."

**Example 1: The Goods-Leisure Tradeoff** (p. 53). Train & McFadden (1978).
Cobb-Douglas `U = (1-beta) ln G + beta ln L`; conditional on mode `j`,
`U_j = -alpha(c_j / w^beta + w^{1-beta} t_j)`. Cost divided by `w^beta`, time
multiplied by `w^{1-beta}`. `beta` is interpretable only nonlinearly.

**Example 2: Geographic Aggregation** (p. 54). Reproduced essentially in full
in section 4 below, because it is load-bearing. The argument in five steps:

```
  1  Destination-choice models partition a metro into ZONES; utility depends
     on travel time and cost PLUS "attraction" variables a_j such as
     residential population and retail employment.
  2  "Since it is these attraction variables that give rise to parameters
     entering nonlinearity, assume for simplicity that representative utility
     depends only on these variables."       <- the simplification, easily missed
  3  Zone size is arbitrary, so we WANT aggregation invariance:
     P_nj + P_nk = P_nc when zones j and k merge into c.
  4  For logit that requires exp(V_nj) + exp(V_nk) = exp(V_nc), and the
     attraction variables necessarily satisfy a_j + a_k = a_c because they
     are counts.
  5  V_nl = ln(beta' a_l) makes the identity hold.
```

Train's conclusion, p. 54: "Therefore, to specify a destination choice model
that is not sensitive to the level of zonal aggregation, representative utility
needs to be specified with parameters inside a log operation."

### §3.5 Consumer Surplus (pp. 55-57)

`E(CS_n) = (1/alpha_n) E[max_j (V_nj + eps_nj)]`, and Williams (1977) / Small &
Rosen (1981) give the closed form, eq. (3.10), p. 55:

```
  E(CS_n) = (1/alpha_n) ln( sum_{j=1}^{J} e^{V_nj} ) + C
```

the **log-sum term**. Train is careful to deflate the mystique (p. 56):

> "This resemblance between the two formulas has no economic meaning, in the
> sense that there is nothing about a denominator in a choice probability that
> makes it necessarily related to consumer surplus. It is simply the outcome of
> the mathematical form of the extreme value distribution."

`C` cancels in differences. `alpha_n` is the marginal utility of income, usually
the negative of the cost coefficient, and formula (3.10) "depends critically on
the assumption that the marginal utility of income is independent from income" —
so if you plan to compute consumer surplus, you may multiply cost by household
size but must not divide it by income.

### §3.6 Derivatives and Elasticities (pp. 57-60)

Own-derivative `dP_ni/dz_ni = (dV_ni/dz_ni) P_ni (1 - P_ni)`, largest at
`P = 0.5`. Cross-derivative `dP_ni/dz_nj = -(dV_nj/dz_nj) P_ni P_nj`. Derivatives
sum to zero across alternatives, demonstrated algebraically on p. 59, with the
gloss: "While obvious, this fact is often forgotten by planners who want to
improve demand for one alternative without reducing demand for other
alternatives." Own-elasticity `E_{iz_ni} = beta_z z_ni (1 - P_ni)`;
cross-elasticity `E_{iz_nj} = -beta_z z_nj P_nj`, "the same for all `i`", which
is IIA restated.

### §3.7 Estimation (pp. 60-67)

#### §3.7.1 Exogenous Sample (pp. 60-66)

The likelihood, and **the sentence our documents needed**:

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> `L(beta) = prod_{n=1}^{N} prod_i (P_ni)^{y_ni}`."
> — §3.7.1, p. 61

Log-likelihood eq. (3.11), first-order condition eq. (3.13):

```
  LL(beta) = sum_n sum_i y_ni ln P_ni                     (3.11)
  sum_n sum_i (y_ni - P_ni) x_ni = 0                      (3.13)
```

Two interpretations of (3.13) are given and both are useful. Rearranged as
eq. (3.14), it says the predicted average of each explanatory variable equals
its observed average in the sample. For an alternative-specific constant's dummy
this specialises to `S_j = S_hat_j`: "With alternative-specific constants, the
predicted shares for the sample equal the observed shares." And the residual
reading: the MLEs "make the residuals uncorrelated with the explanatory
variables", the same condition as OLS, which makes logit ML a method-of-moments
estimator.

**Estimation on a Subset of Alternatives** (pp. 64-66). Full set `F`, subset
`K`, `q(K|i)` the probability the researcher's procedure selects `K` given `i`
was chosen. Eq. (3.15):

```
  P_n(i | K) = e^{V_ni} q(K|i) / sum_{j in K} e^{V_nj} q(K|j)      (3.15)
```

Under McFadden's (1978) **uniform conditioning property** — `q(K|j)` the same
for all `j in K`, which holds when non-chosen alternatives are sampled with
equal probability — `q` cancels and the expression "is simply the logit formula
for a person who faces the alternatives in subset `K`". Maximising the resulting
conditional log-likelihood "provides a consistent estimator of `beta`. However,
since information is excluded from CLL that LL incorporates ... the estimator
based on CLL is not efficient."

If uniform conditioning fails, `z_nj = ln q(K_n|j)` is added to utility "with
the coefficient of this variable constrained to 1". The Train et al. (1987a)
telecoms motivation: with an enormous choice set where most alternatives are
hardly ever chosen, equal-probability sampling gives subsets "consisting nearly
entirely of alternatives that were hardly ever chosen", so they sampled in
proportion to population shares instead.

#### §3.7.2 Choice-Based Samples (pp. 66-67)

Samples drawn on the basis of the choice being analysed. The Manski & Lerman
(1977) result: with a *purely* choice-based sample and an alternative-specific
constant for each alternative, "estimating a logit model as if the sample were
exogenous produces consistent estimates for all the model parameters except the
alternative-specific constants", and those are biased by a known factor:

```
  E(alpha_hat_j) = alpha*_j - ln(A_j / S_j)
```

`A_j` the population share choosing `j`, `S_j` the sample share.

### §3.8 Goodness of Fit and Hypothesis Testing (pp. 67-71)

#### §3.8.1 Goodness of Fit (pp. 68-69)

Likelihood ratio index `rho = 1 - LL(beta_hat)/LL(0)`, range 0 to 1. Two
warnings, both of which our documents should carry:

> "It is important to note that the likelihood ratio index is not at all similar
> in its interpretation to the `R^2` used in regression, despite both statistics
> having the same range. ... The likelihood ratio has no intuitively
> interpretable meaning for values between the extremes of zero and one."
> — §3.8.1, p. 68

> "Two models estimated on samples that are not identical or with a different
> set of alternatives for any sampled decision maker cannot be compared via their
> likelihood ratio index values."
> — §3.8.1, p. 69

**Percent correctly predicted** (p. 69), the passage the project keeps
mis-citing, given in full in section 4.

#### §3.8.2 Hypothesis Testing (pp. 70-71)

`t`-statistics for single parameters; likelihood ratio test
`-2(LL(beta_hat^H) - LL(beta_hat))` distributed chi-squared with degrees of
freedom equal to the number of restrictions. Two worked null hypotheses:
several coefficients are zero (estimate with and without), and two coefficients
are equal (estimate separately, then with the two variables summed into one).

### §3.9 Case Study: Forecasting for a New Transit System (pp. 71-74)

BART. 771 commuters surveyed *before* BART opened; four modes (auto alone, bus
with walk access, bus with auto access, carpool); model estimated, then used to
forecast BART share; commuters recontacted after opening.

**Table 3.1** (p. 72), reproduced in full:

```
  Logit model of work trip mode choice
  Explanatory Variable                              Coefficient   t-Statistic
  ----------------------------------------------------------------------------
  Cost divided by post-tax wage, minutes (1-4)        -0.0284        4.31
  Auto on-vehicle time, minutes (1, 3, 4)             -0.0644        5.65
  Transit on-vehicle time, minutes (2, 3)             -0.0259        2.94
  Walk time, minutes (2, 3)                           -0.0689        5.28
  Transfer wait time, minutes (2, 3)                  -0.0538        2.30
  Number of transfers (2, 3)                          -0.1050        0.78
  Headway of first bus, minutes (2, 3)                -0.0318        3.18
  Family income with ceiling $7500 (1)             0.00000454        0.05
  Family income - $7500 with floor 0, ceiling $3000 (1) -0.0000572    0.43
  Family income - $10,500 with floor 0, ceiling $5000 (1) -0.0000543  0.91
  Number of drivers in household (1)                   1.02          4.81
  Number of drivers in household (3)                   0.990         3.29
  Number of drivers in household (4)                   0.872         4.25
  Dummy if worker is head of household (1)             0.627         3.37
  Employment density at work location (1)             -0.0016        2.27
  Home location in or near central business district (1) -0.502      4.18
  Autos per driver with ceiling one (1)                5.00          9.65
  Autos per driver with ceiling one (3)                2.33          2.74
  Autos per driver with ceiling one (4)                2.38          5.28
  Auto alone dummy (1)                                -5.26          5.93
  Bus with auto access dummy (3)                      -5.49          5.33
  Carpool dummy (4)                                   -3.84          6.36
  ----------------------------------------------------------------------------
  Likelihood ratio index                               0.4426
  Log likelihood at convergence                     -595.8
  Number of observations                               771
  ----------------------------------------------------------------------------
  Value of time saved as a percentage of wage:
    Auto on-vehicle time      227    3.20
    Transit on-vehicle time    91    2.43
    Walk time                 243    3.10
    Transfer wait time        190    2.01

  Modes: 1. Auto alone.  2. Bus with walk access.  3. Bus with auto access.
  4. Carpool.  Variable enters modes in parentheses and is zero in other modes.
```

Value of time is `beta/alpha` of the wage, from `dU = (alpha/w) dc + beta dt`.
Driving time is valued at 227% of wage against 91% for bus time — "Commuters
apparently choose cars not because they like driving *per se* but because
driving is usually quicker." Income enters piecewise and none of it is
significant, because "dividing travel cost by wage picks up whatever effect
income might have".

**Table 3.2** (p. 74), the forecast against outturn:

```
  Predictions for after BART opened
                        Actual Share    Predicted Share
  Auto alone                59.90            55.84
  Bus with walk access      10.78            12.51
  Bus with auto access       1.426            2.411
  BART with bus access       0.951            1.053
  BART with auto access      5.230            5.286
  Carpool                   21.71            22.89
```

BART forecast 6.3% against 6.2% actual — "This close correspondence is
remarkable." And immediately, the honest footnote that makes the case study
worth reading: walking to BART "was originally included as a separate mode. The
model forecasted this option very poorly, overpredicting the number of people
who would walk to BART by a factor of twelve", because walking to a BART station
is not like walking to a bus stop given where BART stations are.

### §3.10 Derivation of Logit Probabilities (pp. 74-75)

The integral `P_ni = int (prod_{j != i} e^{-e^{-(s + V_ni - V_nj)}}) e^{-s}
e^{-e^{-s}} ds` is evaluated by substituting `t = exp(-s)`, giving
`1 / sum_j e^{-(V_ni - V_nj)} = e^{V_ni} / sum_j e^{V_nj}`. Two pages, fully
worked, no gaps.

---

## 4. Verbatim quotes for anything load-bearing

### 4.1 §3.4 Example 2, Geographic Aggregation, p. 54 — the whole argument

This is the page the reframe rests on, so it is quoted at length rather than
summarised.

> "Models have been developed and widely used for travelers' choice of
> destination for various types of trips, such as shopping trips, within a
> metropolitan area. Usually, the metropolitan area is partitioned into *zones*,
> and the models give the probability that a person will choose to travel to a
> particular zone. The representative utility for each zone depends on the time
> and cost of travel to the zone plus a variety of variables, such as residential
> population and retail employment, that reflect reasons that people might want
> to visit the zone. These latter variables are called *attraction* variables;
> label them by the vector `a_j` for zone `j`. Since it is these attraction
> variables that give rise to parameters entering nonlinearity, assume for
> simplicity that representative utility depends only on these variables."

> "The difficulty in specifying representative utility comes in recognizing that
> the researcher's decision of how large an area to include in each zone is
> fairly arbitrary. It would be useful to have a model that is not sensitive to
> the level of aggregation in the zonal definitions. If two zones are combined,
> it would be useful for the model to give a probability of traveling to the
> combined zone that is the same as the sum of the probabilities of traveling to
> the two original zones. This consideration places restrictions on the form of
> representative utility."

> "Consider zones `j` and `k`, which, when combined, are labeled zone `c`. The
> population and employment in the combined zone are necessarily the sums of
> those in the two original zones: `a_j + a_k = a_c`."

> "This equality holds only when `exp(V_nj) + exp(V_nk) = exp(V_nc)`. If
> representative utility is specified as `V_nl = ln(beta' a_l)` for all zones
> `l`, then the equality holds: `exp(ln(beta' a_j)) + exp(ln(beta' a_k)) = beta'
> a_j + beta' a_k = beta' a_c = exp(ln(beta' a_c))`. Therefore, to specify a
> destination choice model that is not sensitive to the level of zonal
> aggregation, representative utility needs to be specified with parameters
> inside a log operation."

### 4.2 §3.4 opening, p. 52 — the price of a nonlinear utility

> "Estimation is then more difficult, since the log-likelihood function may not
> be globally concave and computer routines are not as widely available as for
> logit models with linear-in-parameters representative utility."

### 4.3 §3.7.1, p. 61 — the independence assumption, and the concavity condition

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> `L(beta) = prod_{n=1}^{N} prod_i (P_ni)^{y_ni}`."

> "McFadden (1974) shows that `LL(beta)` is globally concave for
> linear-in-parameters utility, and many statistical packages are available for
> estimation of these models. When parameters enter the representative utility
> nonlinearly, the researcher may need to write her own estimation code using the
> procedures described in Chapter 8."

### 4.4 §3.7.1, p. 65 — sampled alternatives

> "Suppose that the researcher has designed the selection procedure so that
> `q(K | j)` is the same for all `j` in `K`. ... McFadden (1978) calls this the
> 'uniform conditioning property,' since the subset of alternatives has a uniform
> (equal) probability of being selected conditional on any of its members being
> chosen by the decision maker. When this property is satisfied, `q(K | j)`
> cancels out of the preceding expression, and the probability becomes
> `P_n(i | K) = e^{V_ni} / sum_{j in K} e^{V_nj}`, which is simply the logit
> formula for a person who faces the alternatives in subset `K`."

> "Maximization of CLL provides a consistent estimator of `beta`. However, since
> information is excluded from CLL that LL incorporates (i.e., information on
> alternatives not in each subset), the estimator based on CLL is not efficient."

### 4.5 §3.8.1, p. 69 — "percent correctly predicted", in full

Quoted whole because the project has now mis-summarised it twice.

> "Another goodness-of-fit statistic that is sometimes used, but should actually
> be avoided, is the 'percent correctly predicted.' This statistic is calculated
> by identifying for each sampled decision maker the alternative with the highest
> probability, based on the estimated model, and determining whether or not this
> was the alternative that the decision maker actually chose. The percentage of
> sampled decision makers for which the highest-probability alternative and the
> chosen alternative are the same is called the percent correctly predicted."

> "This statistic incorporates a notion that is opposed to the meaning of
> probabilities and the purpose of specifying choice probabilities. The statistic
> is based on the idea that the decision maker is predicted by the researcher to
> choose the alternative for which the model gives the highest probability.
> However, as discussed in the derivation of choice probabilities in Chapter 2,
> the researcher does not have enough information to predict the decision maker's
> choice. The researcher has only enough information to state the probability
> that the decision maker will choose each alternative."

> "An example may be useful. Suppose an estimated model predicts choice
> probabilities of .75 and .25 in a two-alternative situation. ... the 'percent
> correctly predicted' statistic is based on the notion that the best prediction
> for each person is the alternative with the highest probability. This notion
> would predict that one alternative would be chosen by all 100 people while the
> other alternative would never be chosen. **The procedure misses the point of
> probabilities, gives obviously inaccurate market shares, and seems to imply that
> the researcher has perfect information.**"

(Emphasis added on the final sentence; it is the one with two limbs, and the
second limb — "gives obviously inaccurate market shares" — is the one AUC
inherits, because AUC is invariant to every strictly increasing transform of the
predictions and therefore says nothing about their level.)

### 4.6 §3.8.1, p. 68-69 — the likelihood ratio index is not an R-squared

> "It is important to note that the likelihood ratio index is not at all similar
> in its interpretation to the `R^2` used in regression, despite both statistics
> having the same range. `R^2` indicates the percentage of the variation in the
> dependent variable that is 'explained' by the estimated model. The likelihood
> ratio has no intuitively interpretable meaning for values between the extremes
> of zero and one."

> "Two models estimated on samples that are not identical or with a different set
> of alternatives for any sampled decision maker cannot be compared via their
> likelihood ratio index values."

### 4.7 §3.1, pp. 35-36 — independence as an ideal rather than a restriction

> "In a deep sense, the ultimate goal of the researcher is to represent utility
> so well that the only remaining aspects constitute simply white noise; that is,
> the goal is to specify utility well enough that a logit model is appropriate.
> Seen in this way, the logit model is the ideal rather than a restriction."

### 4.8 §3.5, p. 56 — the log-sum has no economic meaning per se

> "This resemblance between the two formulas has no economic meaning, in the
> sense that there is nothing about a denominator in a choice probability that
> makes it necessarily related to consumer surplus. It is simply the outcome of
> the mathematical form of the extreme value distribution."

---

## 5. Definitions the chapter gives formally

```
  LOGIT CHOICE PROBABILITY                            §3.1, p. 36, eq. (3.6)
      P_ni = e^{V_ni} / sum_j e^{V_nj}
    derived under eps_nj iid type I extreme value, variance pi^2/6.

  EXTREME VALUE DENSITY / CDF                    §3.1, p. 34, eqs. (3.1)-(3.2)
      f(eps) = e^{-eps} e^{-e^{-eps}}
      F(eps) = e^{-e^{-eps}}
    "also called Gumbel and type I extreme value (and sometimes, mistakenly,
     Weibull)".

  SCALE PARAMETER                                             §3.2, pp. 40-41
      P_ni = e^{V_ni/sigma} / sum_j e^{V_nj/sigma};  beta = beta*/sigma.
      "Only the ratio beta*/sigma can be estimated; beta* and sigma are not
       separately identified."

  IIA                                                         §3.3.2, p. 46
      P_ni / P_nk = e^{V_ni - V_nk}, independent of all other alternatives.

  PROPORTIONAL SUBSTITUTION / PROPORTIONATE SHIFTING     §3.3.2, pp. 47-48
      Cross-elasticity E_{i z_nj} = -beta_z z_nj P_nj, the SAME for all i.
      IIA requires P^1_ni / P^1_nk = P^0_ni / P^0_nk when an attribute of a
      third alternative j changes.

  NONLINEAR REPRESENTATIVE UTILITY FOR ZONES         §3.4 Ex. 2, p. 54
      V_nl = ln(beta' a_l), with a_l the vector of ATTRACTION variables for
      zone l.  Required for invariance to zonal aggregation, because
      a_j + a_k = a_c when zones merge.

  EXPECTED CONSUMER SURPLUS / LOG-SUM               §3.5, p. 55, eq. (3.10)
      E(CS_n) = (1/alpha_n) ln( sum_{j=1}^{J} e^{V_nj} ) + C
    valid when eps iid extreme value AND utility linear in income, so that
    alpha_n is constant with respect to income.

  OWN- AND CROSS-ELASTICITY                            §3.6, pp. 59-60
      E_{i z_ni} = beta_z z_ni (1 - P_ni)
      E_{i z_nj} = -beta_z z_nj P_nj

  LOG-LIKELIHOOD AND FIRST-ORDER CONDITION       §3.7.1, p. 61, (3.11),(3.13)
      LL(beta) = sum_n sum_i y_ni ln P_ni
      sum_n sum_i (y_ni - P_ni) x_ni = 0

  UNIFORM CONDITIONING PROPERTY (McFadden 1978)            §3.7.1, p. 65
      q(K | j) the same for all j in K.  Then estimation on the subset K is
      the ordinary logit on K, and is CONSISTENT but NOT EFFICIENT.

  CHOICE-BASED SAMPLE CONSTANT CORRECTION                  §3.7.2, p. 67
      E(alpha_hat_j) = alpha*_j - ln(A_j / S_j),  A_j the population share,
      S_j the sample share.

  LIKELIHOOD RATIO INDEX                                   §3.8.1, p. 68
      rho = 1 - LL(beta_hat) / LL(0).   NOT an R-squared.

  PERCENT CORRECTLY PREDICTED                              §3.8.1, p. 69
      Share of decision makers whose highest-probability alternative was the
      one chosen.  "should actually be avoided".

  LIKELIHOOD RATIO TEST                                    §3.8.2, p. 70
      -2 ( LL(beta_hat^H) - LL(beta_hat) )  ~  chi-squared, df = number of
      restrictions.
```

---

## 6. What this means for siting-atlas

### 6.1 The `V = ln(beta'a)` claim: right, and imprecise in a way that matters

The claim as this project first filed it — the literature table in the retired
`PLAN.md`, quoted in full at [`../MODEL_SPEC.md`](../MODEL_SPEC.md) §1 and
argued out at [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §5.3 — reads:
"with zonal alternatives, utility must be `V = ln(beta'a)`
with ADDITIVE attraction variables, or results are an artefact of how the Census
drew ZCTA boundaries."

Against the text (§4.1 above), **the substance is correct**. The form is
`ln(beta' a)`, the reason is invariance to arbitrary zone boundaries, and the
paraphrase about Census boundaries is fair — Train's own words are "not
sensitive to the level of aggregation in the zonal definitions", and ZCTAs are
built from postal delivery routes, so they carry no economic content at all.

Three corrections, all of which are now written up in `docs/MODEL_SPEC.md` §1:

**(a) "must" is stronger than Train.** He says it "would be useful" to have an
invariant model and that this "places restrictions on the form". A
linear-in-parameters zonal model is not inconsistent; it is not invariant. The
honest defence is "we imposed invariance, here is why", not "the literature
forbids the alternative".

**(b) "ADDITIVE attraction variables" is not an instruction, it is a fact about
a class of variables — and the operative content is the exclusion it implies.**
Additivity is a property population and employment *have*: merge two zones and
the counts add. The restriction that follows, and which the claim never states,
is that **only extensive quantities may sit inside the log.** Households,
population, establishments, land area, floor space — yes. Median income, a rent
index, any density, any rate, any share — no, because the median of a merged
zone is not the sum of the two medians and the derivation fails at
`a_j + a_k = a_c`.

This changes what we build. Read casually, the claim says "wrap the
covariates in a log", and the tempting covariates are exactly the intensive
ones. That model would pay the full price of a nonlinear, possibly non-concave
likelihood (§4.2 above) and buy nothing. The retired model's covariate list was
`("households", "median_household_income", "establishments")`
(`models/panel_source.py:50-54`); the middle one is now excluded on principle.

**(c) Train derives the result under `V` depending on attraction variables
ALONE.** The sentence is easy to skim past: "assume for simplicity that
representative utility depends only on these variables." In real
destination-choice models `V` also contains travel time and cost, and Train does
not show what invariance survives. So a mixed form `V = ln(beta'a) + gamma'z` is
**not** licensed by this page, and it is not invariant: adding `gamma' z_c`
breaks `exp(V_j) + exp(V_k) = exp(V_c)` unless `z` is constant across the merged
pair. This is why distance-to-nearest-station is handled as a pre-registered
sensitivity rather than a main-specification covariate (`MODEL_SPEC.md` §4.3).

### 6.2 THE CORRECTION our documents most need: §3.7.1 p. 61, not §2.2

The diagnosis as it stood when these notes were written — `PLAN.md` §3, since
retired, and `STATUS.md` — attributed the hazard model's failure to Train
§2.2 mutual exclusivity. Having read both chapters, that is the wrong citation
and it should be replaced — the replacement is *stronger*. **It has since been
replaced**, at [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.2 and
[`../STATUS.md`](../STATUS.md) §8.

§2.2 is about a choice set facing a decision maker, and a cloglog hazard on
ZCTA-quarters has no such decision maker, so exclusivity is not a property those
rows can have or lack. Worse for our rhetoric, Train calls the criterion "not
restrictive" and gives a two-line recipe for repairing any violation
(`NOTES_train_ch02_properties.md` §6.1).

The assumption the panel actually violated is in **this** chapter, at p. 61:
"Assuming that each decision maker's choice is independent of that of other
decision makers". A median of 58 ZCTAs switching on together with one building
destroys exactly that. The artefact measures the damage —
`hazard_report.json` `power` gives `n_events_zcta` 487 against
`n_independent_episodes` 28 and `n_usable_facilities` 38. The standard name is
clustering or pseudo-replication.

The *diagnosis* itself is right and stands. Only the section number
and the word needed to change.

### 6.3 §3.7.1 sampled alternatives is our insurance policy, and we do not need it yet

With `J_m` in the hundreds per metro and 38 decisions, an obvious objection is
"you cannot estimate a model with more alternatives than observations". §3.7.1
pp. 64-66 disposes of it: under the uniform conditioning property, estimating on
the chosen alternative plus a random sample of the rest is consistent. We do not
use it, because our choice sets are small enough to enumerate and we prefer the
efficient estimator — but it is the reason the objection does not land, and it is
the route if the national frame (104 stations, 62 CBSAs) is ever promoted.

The Train et al. (1987a) refinement is worth remembering for that day: with an
enormous choice set where most alternatives are hardly ever chosen,
equal-probability sampling produces subsets "consisting nearly entirely of
alternatives that were hardly ever chosen", which is uninformative. They sampled
in proportion to population shares. Our ZCTA choice set has exactly that shape —
1,257 of 33,791 ZCTAs were ever enabled.

### 6.4 §3.7.2 names a threat we have and have not addressed

Our 43 stations were discovered by searching OSHA enforcement records for
buildings that exist. We observe chosen alternatives *because* they were chosen.
That is a choice-based sample in Train's sense.

The Manski & Lerman (1977) result (p. 67) is partially reassuring — with a purely
choice-based sample and alternative-specific constants, everything except the
constants is consistently estimated as if the sample were exogenous — and we
have no alternative-specific constants (they are unidentified here, §2.5.1).
But the result is stated for a *purely* choice-based sample with known
population shares `A_j`, and ours is a convenience sample whose discovery process
(which buildings OSHA happened to inspect) is neither random nor known. Logged
in `MODEL_SPEC.md` §10.4 as an unquantified threat. Nobody had named it before.

### 6.5 §3.3.2 IIA is implausible for us, and we accept it anyway, on the record

Two ZCTAs two miles apart are near-perfect substitutes for a delivery station:
the catchments almost coincide. That is the red-bus/blue-bus structure with
geography instead of paint. Logit will therefore overstate how much probability
a new candidate site draws from distant ZCTAs and understate how much it draws
from its immediate neighbours.

We accept it because the repair — nested logit with metros as nests — costs a
`lambda` per nest and the sample cannot afford parameters
(`MODEL_SPEC.md` §8.3, §10.5). What we can do cheaply is Train's second option
from p. 36: "respecify representative utility so that the source of the
correlation is captured explicitly". Including land area alongside households
does a little of that, since adjacent ZCTAs differ mainly in size. It is not a
fix and should not be described as one.

### 6.6 §3.8.1 settles the metric argument, and closes one door we had left ajar

The "percent correctly predicted" passage (§4.5 above) is the authority for not
headlining top-1 hit rate. Two details our documents have handled badly:

- The corrected note on the metric,
  [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §5.4, is right that AUC
  "does not commit to ONE
  threshold" but does not escape thresholds, being the integral of the ROC over
  all of them. The second limb of Train's objection — "gives obviously
  inaccurate market shares" — **is** inherited by AUC, because AUC is invariant
  to every strictly increasing transform of the predictions and therefore
  carries no information about their level. The corrected note already says this;
  it should not be softened back.
- The likelihood ratio index cannot be compared across models with different
  samples or different choice sets (p. 69). That forbids comparing our `rho` to
  any published destination-choice `rho`, which is a comparison a reader will
  otherwise reach for.

There is also a positive result here worth using. From eq. (3.14) and the
alternative-specific-constant specialisation (p. 62): with ASCs, MLE forces
predicted shares to equal observed shares. **We have no ASCs, so we get no such
guarantee**, which means our predicted shares are a genuine, non-mechanical
check. Worth reporting.

### 6.7 §3.5's log-sum is the bridge to the two-factor decomposition

[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.3 factorises
`P(served) = P(a station opens in your metro) x
P(the chosen site is within 15 miles)`. §3.5's log-sum
`ln sum_j e^{V_nj}` is precisely the quantity that would link a lower model
(which ZCTA) to an upper model (which metro), and Chapter 4 makes that
explicit — see `NOTES_train_ch04_gev.md`. For now the two factors are estimated
separately and multiplied, which is the *sequential* estimation Train warns is
consistent but inefficient and gives downward-biased upper-model standard errors
(§4.2.4, p. 85). Since we are not estimating the upper model at all — the first
factor is a base rate, not a fitted logit — the bias does not arise, but the
structure should be named so nobody later claims we fitted a nested logit.

### 6.8 The BART case study is the model for how to write up a forecast

§3.9 is worth reading for tone, not content. Train reports a 6.3% forecast
against a 6.2% outturn and calls it remarkable — and then, in the next
paragraph, volunteers that the same model overpredicted walking to BART **by a
factor of twelve** and explains why. That is the standard this project's
write-up should meet: the good number and the embarrassing one on the same page,
with the mechanism for the second.

---

## 7. What I did NOT read, or did not understand

- **Every page of Chapter 3 was opened**, PDF pages 1-42, as rendered images, in
  three passes (1-20, 21-40, 41-42). No stretch was skimmed.
- **The §3.10 derivation (pp. 74-75) I read and followed but did not re-derive
  independently.** The substitution `t = exp(-s)` and the limits are legible and
  the steps are complete in the text; I did not verify the interchange of product
  and integral.
- **The algebra deriving eq. (3.13) from (3.11) (p. 63) I read line by line and
  it is complete in the text.** I did not independently re-derive it.
- **Figure 3.1 (p. 38) is a line drawing** of the logit sigmoid with axes `P_ni`
  and `V_ni` and no numerical gridlines. Nothing is extractable beyond the
  shape, which the prose describes anyway.
- **Table 3.1 (p. 72) and Table 3.2 (p. 74) are transcribed above from the
  rendered images.** I checked the four value-of-time figures against the prose
  on p. 73 (227%, 91%, 243%, 190%) and they agree, and I verified
  `(-0.0259 / -0.0284) x 100 = 91.2`, which matches the stated 91. The remaining
  coefficients were transcribed once and not double-entered; treat any single
  digit as possibly mis-transcribed and reopen p. 72 before quoting one.
- **§3.3.1's variance algebra** (`Var(eps~_nj) = Var(mu_n)SR_j^2 +
  Var(eta_n)PP_j^2 + Var(eps_nj)`, p. 44) I read and accept; I did not check the
  covariance expression for `Cov(eps~_nj, eps~_nk)`.
- **Cited works not consulted, and none is in `../Research/`:** Luce (1959),
  Marschak (1960), Luce & Suppes (1965), McFadden (1974, 1978, 1987, 2001),
  Chipman (1960), Debreu (1960), Ortuzar (1983), Brownstone & Train (1999),
  Hausman & McFadden (1984), Train, Ben-Akiva & Atherton (1989), Adamowicz
  (1994), Erdem (1996), Train & McFadden (1978), Williams (1977), Small & Rosen
  (1981), McFadden (1999), Karlstrom (2000), Manski & McFadden (1981), Cosslett
  (1981), Manski & Lerman (1977), Ben-Akiva & Lerman (1985), Train et al.
  (1987a), McFadden et al. (1977), Train (1978). Everything attributed to them
  above is Train's characterisation.
- **Not verified:** whether the Manski & Lerman result's conditions are met by
  our OSHA discovery process. I have flagged in §6.4 that they are probably not,
  but I have not read Manski & Lerman and cannot say what the failure costs.
- **§3.3.2's "Tests of IIA" (pp. 49-50) read but not pursued.** I did not look up
  the Hausman-McFadden statistic or work out whether it is computable at our
  sample size. It probably is not, but that is a guess and is labelled as one.
