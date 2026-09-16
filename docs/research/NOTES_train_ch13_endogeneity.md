# Notes — Train (2009) Ch. 13, Endogeneity

*Read in full on 2026-09-13, every page, as images. Read to check two claims in
the backlog's control-function entry — now
[`../ROADMAP.md`](../ROADMAP.md) under "Identification": that a control function
(§13.4) is the route we should
take, and that BLP is unavailable to us because "Train notes BLP cannot be
implemented when observed shares are zero for some alternatives in some markets,
which is our case". The second claim is **verified verbatim** and is one of the
few claims in that backlog that survived checking without amendment.*

---

## 1. Citation and local file

```
  Kenneth E. Train, Discrete Choice Methods with Simulation, 2nd edition.
  Cambridge University Press, 2009.  Chapter 13, "Endogeneity",
  printed pp. 315-346.  Part II, "Estimation".

  Local file:  ../Research/Ch13_p315-346.pdf   (32 PDF pages)
  PDF page 1 = printed p. 315 (the chapter opening).
  So: PDF page = printed page - 314.  Printed p. 346 = PDF page 32.
  Verified: PDF page 1 carries the running foot "315" and the heading
  "13 Endogeneity"; PDF page 20 carries the running head "334 Estimation"
  and the heading "13.4 Control Functions".
```

Every page number below is the **printed** page.

Text layer clean. Tables 13.1 (p. 343) and 13.2 (p. 345) are typeset and are
reproduced in full below. There are no figures in this chapter.

---

## 2. What the chapter is for

Every other chapter assumes the explanatory variables are independent of the
unobserved factors. This one drops that assumption and describes three repairs:
BLP (§13.2), control functions (§13.4), and full-information maximum likelihood
(§13.5), with the supply side in between (§13.3) and a case study at the end
(§13.6).

Train's motivating cases (§13.1, pp. 315-316) are three, and the third is ours
with the labels changed:

```
  1  Unobserved attributes of a product can affect its price.
     Comfort, beauty of design, prestige -- unmeasurable, but priced.
  2  Marketing efforts can be related to prices.
     Advertising and discounts move together, in either direction.
  3  Interrelated choices of decision makers.
     "people who tend to like traveling on public transit (or dislike it
      less than the average person) might also tend to buy or rent homes
      that are near public transit. Travel time by transit is therefore
      lower for these people than for people who locate further from
      transit."
```

What we want from it: whether BLP is available (it is not, and the reason is
stated), what the control function costs, and how much of the apparatus is
premised on *price* specifically rather than on endogeneity in general.

---

## 3. Section-by-section walkthrough

### §13.1 Overview (pp. 315-318)

The three cases above, then the direction-of-bias argument (p. 316):

> "In situations such as these, estimation without regard to the correlation
> between observed and unobserved factors is inconsistent. The direction of bias
> can often be determined logically. For example, if desirable unobserved
> attributes are positively correlated with price, then estimation without regard
> to this correlation will result in an estimated price coefficient that is
> biased downward in magnitude. The reason is clear: since higher prices are
> associated with desirable attributes, consumers avoid the higher-priced
> products *less* than they would if the higher prices occurred without any
> compensating change in unobserved attributes. Essentially, the estimated price
> coefficient picks up both the price effect (which is negative) and the effect
> of the desirable unobserved attributes (which is positive), with the latter
> muting the former."

Then a preview of the three methods.

**BLP** (Berry 1994; BLP 1995, 2004). Berry's insight: include a constant for
each product in each market to absorb the average effect of *both* observed and
unobserved attributes; then regress the estimated constants on the observed
attributes by instrumental variables. "Essentially, he showed that the
endogeneity could be taken out of the choice model, which is inherently
nonlinear, and put into a linear regression model, where endogeneity can be
handled through standard instrumental variables estimation." BLP (1995) added
"the contraction" to make estimating a very large number of constants tractable.

**Control function** (Heckman 1978; Hausman 1978; the term from Heckman & Robb
1985; Rivers & Vuong 1988 for binary probit; Petrin & Train 2009 for multinomial
with random coefficients). Two steps: regress the endogenous variable on
exogenous variables, form a new variable from that regression, enter it in the
choice model.

> "Endogeneity arises when observed variables are correlated with unobserved
> factors. This correlation implies that the unobserved factors conditional on
> the observed variables do not have a zero mean, as is usually required for
> standard estimation. A control function is a variable that captures this
> conditional mean, essentially 'controlling' for the correlation."
> — §13.1, p. 317

**Full maximum likelihood** (Villas-Boas & Winer 1999; Park & Gupta). The same
two steps combined into one estimation criterion. "Additional assumptions are
required to allow the estimation to be performed simultaneously; however, the
procedure is more efficient when those assumptions are met."

### §13.2 The BLP Approach (pp. 318-328)

#### §13.2.1 Specification (pp. 319-321)

`M` markets, `J_m` options in market `m`, possibly including an outside good.
Price `p_jm`, observed nonprice attributes `x_jm`, unobserved attributes
`xi_jm`. Utility `U_njm = V(p_jm, x_jm, s_n, beta_n) + xi_jm + eps_njm`, with
`xi_jm` entering "the same for all consumers; in this setup, therefore, `xi_jm`
represents the average, or common, utility that consumers obtain from the
unobserved attributes of product `j` in market `m`."

The BLP move: split `V` into `V_bar` (constant over consumers) and `V_tilde`
(varying), then absorb `xi_jm` into a product-market constant, eq. (13.1)-(13.2),
p. 320:

```
  delta_jm = V_bar(p_jm, x_jm, beta_bar) + xi_jm                   (13.1)
  U_njm    = delta_jm + V_tilde(p_jm, x_jm, s_n, beta_tilde_n) + eps_njm   (13.2)
```

> "A choice model based on this utility specification does not entail any
> endogeneity. A constant is included for each product in each market, which
> absorbs `xi_jm`. The remaining unobserved portion of utility, `eps_njm`, is
> independent of the explanatory variables. ... Essentially, the term that caused
> the endogeneity, namely, `xi_jm`, has been subsumed into the product-market
> constant such that it is no longer part of the unobserved component of
> utility."
> — §13.2.1, p. 320

The choice probability is a mixed logit, eq. (13.3), p. 321. Estimating (13.3)
gives the constants and the distribution of tastes, but not `beta_bar` — those
live in eq. (13.4):

```
  delta_jm = beta_bar' v_bar(p_jm, x_jm) + xi_jm                   (13.4)
```

a linear regression of the estimated constants on price and attributes, with
error `xi_jm` correlated with price, estimated by instrumental variables.

#### §13.2.2 The Contraction (pp. 322-324)

With 200+ makes and models per year and five years of data, "more than a
thousand constants would need to be estimated". The contraction avoids
estimating them by gradient methods: constants determine predicted shares, so
set them to equate predicted and actual shares. The iteration is **the same
formula as Chapter 2's recalibration of constants** (§2.8, p. 33):

```
  delta_jm^{t+1} = delta_jm^t + ln( S_jm / S_hat_jm(delta^t) )
```

Berry (1994) showed a unique set of constants exists for any value of the other
parameters; BLP (1995) showed the adjustment is a contraction and converges.
"When used in the context of estimation instead of postestimation calibration,
the algorithm has come to be known as 'the contraction.'"

Two caveats Train adds (p. 323). Sample shares may be used in place of aggregate
market shares, "consistent for market shares provided that the sampling is
exogenous". And the contraction imposes a constraint: for standard logit with a
full set of constants, MLE already equates predicted and sample shares (§3.7.1),
so the constraint is free; for probit and mixed logit it is not, and "The
estimated constants that are obtained through the contraction are therefore not
the maximum likelihood estimates. Nevertheless, since the condition holds
asymptotically for a correctly specified model, imposing it seems reasonable."

#### §13.2.3 Estimation by MSL and IV (pp. 324-326)

Three steps: estimate (13.3) by maximum simulated likelihood with the
contraction for the constants; regress the estimated constants on attributes by
IV; optionally estimate the pricing equation. "From a programming perspective,
the maximization entails iterations within iterations" (footnote 3, p. 324).

Instruments (pp. 325-326). BLP (1994) proposed "the average nonprice attributes
of other products by the same manufacturer, and the average nonprice attributes
of other firms' products". Train & Winston (2007) used sums of squared
differences. Goolsbee & Petrin (2004), following Hausman (1997), used prices in
other cities served by the same franchise operator. A candid footnote (4, p. 325)
on the standard assumption:

> "This assumption is largely an expedient, since in general one would expect the
> unobserved attributes of a product to be related not only to price but also to
> the observed nonprice attributes. However, a model in which all observed
> attributes are treated as endogenous leaves little to use for instruments."

#### §13.2.4 Estimation by GMM (pp. 326-328)

Moment conditions from the choice probabilities, eq. (13.5), and from the
regression, eq. (13.6); stack them and minimise `g' Theta^{-1} g`. Train notes
that for a standard logit these moments *are* the ML first-order conditions, but
"In other models, this moment condition is not the same as the first-order
condition for maximum likelihood, such that there is a loss of efficiency."

### §13.3 Supply Side (pp. 328-334)

Why bother: forecasting under changed conditions needs supply as well as demand
(the merger-analysis example), and observed prices contain information about
demand elasticities that can be extracted. The trade-off is stated plainly
(p. 329): "Incorporation of the supply side has the potential to improve the
estimates of demand and expand the use of the model. However, it entails
assumptions about pricing behavior that might not hold, such that estimating
demand without the supply side might be safer."

```
  13.3.1  Marginal cost, eq. (13.7): MC_jm = W(x_jm, c_jm, gamma) + mu_jm,
          "separable in unobserved terms".                       p. 329
  13.3.2  MC pricing, eq. (13.8): p_jm = W(x_jm, c_jm, gamma) + mu_jm.
          Cost shifters c_jm become instruments.  Three-step estimation
          (MSL, IV on the constants, OLS on the pricing equation), or GMM
          with an extra moment.                                  pp. 330-331
  13.3.3  Fixed markup over MC: p = k MC, "has the same implications for
          demand estimation as MC pricing".  Shim and Sudit (1995) report
          that more than 80 percent of managers say they price this way.
                                                                 p. 331
  13.3.4  Monopoly / Nash for single-product firms, eq. (13.9):
          p_j + (p_j / e_j) = MC_j, with e_j the own-price elasticity.
          Now the pricing equation's dependent variable is p + p/e, which
          "includes the elasticity of demand, which is not observed
          directly" but is computable from the demand estimates. pp. 332-333
  13.3.5  Multiproduct firms: p + D^{-1} q = MC, with D the K x K matrix of
          demand derivatives.  "a generalized version of the one-product
          monopolist's rule".                                    p. 334
```

### §13.4 Control Functions (pp. 334-340)

**The section the backlog points at.** It opens with the limitation of BLP, and
the sentence our documents quote:

> "The BLP approach is not always applicable. If observed shares for some
> products in some markets are zero, then the BLP approach cannot be implemented,
> since the constants for these product markets are not identified. (Any finite
> constant gives a strictly positive predicted share, which exceeds the actual
> share of zero.) An example is Martin's (2008) study of consumers' choice
> between incandescent and compact fluorescent lightbulbs (CFLs), where
> advertising and promotions occurred on a weekly basis and varied over stores,
> and yet it was common for a store not to sell any CFLs in a given week."
> — §13.4, p. 334

And a second limitation, on p. 334-335, which also applies to us:

> "Endogeneity can also arise over the decision makers themselves rather than
> over markets (i.e., groups of decision makers), such that the endogeneity is
> not absorbed into product-market constants. For example, suppose people who
> like public transit choose to live near transit such that transit time in their
> mode choice is endogenous. Constants cannot be estimated for each decision
> maker, since the constants would be infinity (for the chosen alternative) and
> negative infinity (for the nonchosen alternatives), perfectly predicting the
> choices and leaving no information for estimation of parameters."

The set-up, eqs. (13.11)-(13.12), p. 335. Endogenous variable `y_nj`:

```
  U_nj = V(y_nj, x_nj, beta_n) + eps_nj                          (13.11)
  y_nj = W(z_nj, gamma) + mu_nj                                  (13.12)
```

with `eps_nj` and `mu_nj` independent of the instruments `z_nj` but correlated
with each other. Decompose `eps_nj = E(eps_nj | mu_nj) + eps~_nj`; the
conditional expectation is the **control function** `CF(mu_nj, lambda)`, and "The
simplest case is when `E(eps_nj | mu_nj) = lambda mu_nj`, such that the control
function is simply `mu_nj` times a coefficient to be estimated." Utility becomes
eq. (13.13):

```
  U_nj = V(y_nj, x_nj, beta_n) + CF(mu_nj, lambda) + eps~_nj      (13.13)
```

> "This is a choice model just like any other, with the control function
> entering as an extra explanatory variable. Note that the inside integral is
> over the conditional distribution of `eps~` rather than the original `eps`. By
> construction, `eps~` is not correlated with the endogenous variable, while the
> original `eps` was correlated. Essentially, the part of `eps` that is
> correlated with `y_nj` is entered explicitly as an extra explanatory variable,
> namely, the control function, such that the remaining part is not correlated."
> — §13.4, p. 336

Two-step estimation: fit (13.12), retain residuals `mu_hat_nj = y_nj -
W(z_nj, gamma_hat)`; then fit the choice model with `mu_hat_nj` (or a parametric
function of it) as an extra regressor.

**The central difficulty, stated twice** (p. 337 and p. 338):

> "The central issue with the control function approach is the specification of
> the control function and the conditional distribution of `eps~_n`. In some
> situations, there are natural ways to specify these elements of the model. In
> other situations, it is difficult, or even impossible, to specify them in a way
> that meaningfully represents reality. The applicability of the approach depends
> on the researcher being able to meaningfully specify these terms."

Three worked specifications (pp. 337-338):

```
  1  eps_nj and mu_nj jointly normal      -> CF = lambda mu_nj, choice model
                                             is a probit (or mixed probit).
  2  eps_nj = eps^1_nj + eps^2_nj, with
     eps^1 jointly normal with mu and
     eps^2 iid extreme value              -> U = V + lambda mu_nj
                                             + sigma eta_nj + eps^2_nj;
                                             a MIXED LOGIT, with sigma
                                             estimated.
  3  correlation across alternatives
     (eps_nj with mu_nk, k != j)          -> U_n = V + M mu_n + L eta_n
                                             + eps^2_n, L the Choleski
                                             factor of Omega.  Mixed logit.
```

**§13.4.1 Relation to Pricing Behavior (pp. 338-340).** Under MC pricing the
control function works cleanly. Under monopoly or Nash pricing it does not, and
this is the most useful passage in the section:

> "Unlike MC pricing, the unobserved component of demand, `eps^1_nj`, enters the
> pricing equation through the elasticity. The pricing equation includes two
> unobserved terms: `mu_nj` and a highly nonlinear transformation of `eps^1_nj`
> entering through `e_nj`."
> — §13.4.1, p. 339

so the residual we can retain "is not `mu_nj`; rather `u*_nj` incorporates both
`mu_nj` and the unobserved components of the elasticity-based markup", and "The
distribution of `eps^1_nj` conditional on this `u*_nj` has not been derived, and
may not be derivable. ... its conditional distribution is certainly not normal
if its unconditional distribution is normal. In fact, its conditional
distribution is not even independent of the exogenous variables" (p. 340).

Villas-Boas (2007) rescues it with an existence result: assume marginal cost is a
general (nonseparable) function `MC = W*(z_nj, gamma, mu_nj)`, and then "for any
specification of the control function and distribution of `eps^1_nj` conditional
on this control function, there exists a marginal cost function `W*(.)` and
distribution of unobserved terms `mu_nj` and `eps^1_nj` that are consistent with
them". Train's caveat: "Of course, this existence proof does not provide guidance
on what control function and conditional distribution are most reasonable, which
must still remain an important issue for the researcher."

### §13.5 Maximum Likelihood Approach (pp. 340-342)

Specify the *joint* distribution `g(eps_n, mu_n)` rather than the conditional,
express `mu_n = y_n - W(z_n, gamma)`, and maximise one likelihood over
`gamma`, `theta` and `Omega` together. The trade-off, p. 342:

> "The control function and maximum likelihood approaches provide a trade-off
> that is common in econometrics: generality versus efficiency. The maximum
> likelihood approach requires a specification of the joint distribution of
> `eps_n` and `mu_n`, while the control function requires a specification of the
> conditional distribution of `eps_n` given `mu_n`. Any joint distribution
> implies a particular conditional distribution, but any given conditional
> distribution does not necessarily imply a particular joint distribution. ...
> The control function approach is therefore more general than the maximum
> likelihood approach ... However, if the joint distribution can be correctly
> specified, the maximum likelihood approach is more efficient."

### §13.6 Case Study: Consumers' Choice among New Vehicles (pp. 342-346)

Train & Winston (2007). Why the Big Three lost share. Buyers of new vehicles in
2000, plus aggregate shares by make and model. No outside good, so the analysis
"gives the demand conditional on new vehicle purchase". Respondents gave the
vehicle bought plus the ones considered, treated as a ranking and modelled with
an **exploded logit** (§7.3) mixed over random coefficients. 200 makes and models,
199 constants estimated by the contraction, then regressed on attributes by IV.

**Table 13.1** (p. 343), reproduced in full:

```
  Mixed exploded logit model of new vehicle choice
                                                     Parameter   Std. Error
  ---------------------------------------------------------------------------
  Price (MRSP) divided by respondents' income
    Mean coefficient                                   -1.6025      0.4260
    Standard deviation of coefficient                   0.8602      0.4143
  Consumer Report's repair index, women aged >30 yrs    0.3949      0.0588
  Luxury or sports car, for lessors                     0.6778      0.4803
  Van, for households with an adolescent                3.2337      0.5018
  SUV or station wagon, for households w/ adolescent    2.0420      0.4765
  ln(1 + number of dealers within 50 miles of home)     1.4307      0.2714
  Horsepower: standard deviation of coefficient         0.0045      0.0072
  Fuel consumption (1/mpg): std dev of coefficient   -102.15       20.181
  Light truck, van, or pickup: std dev of coefficient   6.8505      2.5572
  Number of previous consecutive GM purchases           0.3724      0.1471
  Number of previous consecutive GM purchases, if rural 0.3304      0.2221
  Number of previous consecutive Ford purchases         1.1822      0.1498
  Number of previous consecutive Chrysler purchases     0.9652      0.2010
  Number of previous consecutive Japanese purchases     0.7560      0.2255
  Number of previous consecutive European purchases     1.7252      0.4657
  Manufacturer loyalty, error component: std deviation  0.3453      0.1712
  ---------------------------------------------------------------------------
  SLL at convergence                                -1994.93
```

**Table 13.2** (p. 345), the second-stage IV regression, reproduced in full:

```
  Regression of constants on vehicle attributes
                                              Parameter   Std. Error
  --------------------------------------------------------------------
  Price (MSRP, in thousands of dollars)         -0.0733      0.0192
  Horsepower divided by weight (in tons)         0.0328      0.0117
  Automatic transmission standard                0.6523      0.2807
  Wheelbase (in inches)                          0.0516      0.0127
  Length minus wheelbase (in inches)             0.0278      0.0069
  Fuel consumption (in gallons per mile)       -31.641      23.288
  Luxury or sports car                          -0.0686      0.2711
  SUV or station wagon                           0.7535      0.4253
  Van                                           -1.1230      0.3748
  Pickup truck                                   0.0747      0.4745
  Chrysler                                       0.0228      0.2794
  Ford                                           0.1941      0.2808
  General Motors                                 0.3169      0.2292
  European                                       2.4643      0.3424
  Korean                                         0.7340      0.3910
  Constant                                      -7.0318      1.4884
  --------------------------------------------------------------------
  R-squared                                      0.394
```

**The headline result, and the reason the chapter exists** (p. 345):

> "Interestingly, when the regression was estimated by ordinary least squares,
> ignoring endogeneity, the estimated price coefficient was considerably smaller:
> -0.0434 compared with the estimate of -0.0733 using instrumental variables.
> This direction of difference is expected, since a positive correlation of price
> with unobserved attributes creates a downward bias in the magnitude of the
> price coefficient. The size of the difference indicates the importance of
> accounting for endogeneity."

Ignoring endogeneity understated the price coefficient by **41%**. Note also the
closing point on p. 346: price enters *both* parts of the model, so the total
price coefficient is `-0.0773 - 1.602/Income + 0.860 * eta/Income`.

Train ends by naming the case studies for the other two methods: Petrin & Train
(2009) for the control function, Park & Gupta (forthcoming) for maximum
likelihood. Neither is in `../Research/`.

---

## 4. Verbatim quotes for anything load-bearing

### 4.1 §13.4, p. 334 — BLP is unavailable when shares are zero. THE CLAIM WE CAME TO CHECK.

> "The BLP approach is not always applicable. If observed shares for some
> products in some markets are zero, then the BLP approach cannot be implemented,
> since the constants for these product markets are not identified. (Any finite
> constant gives a strictly positive predicted share, which exceeds the actual
> share of zero.)"

### 4.2 §13.4, pp. 334-335 — the second reason BLP fails, which also applies to us

> "Endogeneity can also arise over the decision makers themselves rather than
> over markets (i.e., groups of decision makers), such that the endogeneity is
> not absorbed into product-market constants. For example, suppose people who
> like public transit choose to live near transit such that transit time in their
> mode choice is endogenous. Constants cannot be estimated for each decision
> maker, since the constants would be infinity (for the chosen alternative) and
> negative infinity (for the nonchosen alternatives), perfectly predicting the
> choices and leaving no information for estimation of parameters."

### 4.3 §13.1, p. 317 — what a control function is

> "Endogeneity arises when observed variables are correlated with unobserved
> factors. This correlation implies that the unobserved factors conditional on
> the observed variables do not have a zero mean, as is usually required for
> standard estimation. A control function is a variable that captures this
> conditional mean, essentially 'controlling' for the correlation."

### 4.4 §13.4, p. 337 — the central difficulty of the control function

> "The central issue with the control function approach is the specification of
> the control function and the conditional distribution of `eps~_n`. In some
> situations, there are natural ways to specify these elements of the model. In
> other situations, it is difficult, or even impossible, to specify them in a way
> that meaningfully represents reality. The applicability of the approach depends
> on the researcher being able to meaningfully specify these terms."

### 4.5 §13.1, p. 316 — the direction of bias

> "The direction of bias can often be determined logically. For example, if
> desirable unobserved attributes are positively correlated with price, then
> estimation without regard to this correlation will result in an estimated price
> coefficient that is biased downward in magnitude."

### 4.6 §13.6, p. 345 — how much endogeneity mattered in a real study

> "Interestingly, when the regression was estimated by ordinary least squares,
> ignoring endogeneity, the estimated price coefficient was considerably smaller:
> -0.0434 compared with the estimate of -0.0733 using instrumental variables.
> This direction of difference is expected, since a positive correlation of price
> with unobserved attributes creates a downward bias in the magnitude of the
> price coefficient. The size of the difference indicates the importance of
> accounting for endogeneity."

### 4.7 §13.2.1, p. 320 — what the BLP constants do

> "A choice model based on this utility specification does not entail any
> endogeneity. A constant is included for each product in each market, which
> absorbs `xi_jm`. The remaining unobserved portion of utility, `eps_njm`, is
> independent of the explanatory variables. ... Essentially, the term that caused
> the endogeneity, namely, `xi_jm`, has been subsumed into the product-market
> constant such that it is no longer part of the unobserved component of utility."

### 4.8 §13.3, p. 329 — when NOT to model the supply side

> "Incorporation of the supply side has the potential to improve the estimates of
> demand and expand the use of the model. However, it entails assumptions about
> pricing behavior that might not hold, such that estimating demand without the
> supply side might be safer."

### 4.9 §13.2.3, footnote 4, p. 325 — the instrument assumption is an expedient

> "This assumption is largely an expedient, since in general one would expect the
> unobserved attributes of a product to be related not only to price but also to
> the observed nonprice attributes. However, a model in which all observed
> attributes are treated as endogenous leaves little to use for instruments."

---

## 5. Definitions the chapter gives formally

```
  THE THREE SOURCES OF ENDOGENEITY                        §13.1, pp. 315-316
    1  unobserved attributes of a product affect its price
    2  marketing efforts are related to prices
    3  interrelated choices of decision makers

  BLP UTILITY AND THE PRODUCT-MARKET CONSTANT      §13.2.1, p. 320, (13.1)-(13.2)
      delta_jm = V_bar(p_jm, x_jm, beta_bar) + xi_jm
      U_njm    = delta_jm + V_tilde(p_jm, x_jm, s_n, beta_tilde_n) + eps_njm
    xi_jm is "the average, or common, utility that consumers obtain from the
    unobserved attributes of product j in market m".

  BLP SECOND-STAGE REGRESSION                       §13.2.1, p. 321, (13.4)
      delta_jm = beta_bar' v_bar(p_jm, x_jm) + xi_jm
    estimated by INSTRUMENTAL VARIABLES, not OLS, because price is endogenous.

  THE CONTRACTION                                     §13.2.2, p. 322
      delta_jm^{t+1} = delta_jm^t + ln( S_jm / S_hat_jm(delta^t) )
    Identical in form to the recalibration of constants at §2.8 p.33.
    Berry (1994): a unique set of constants exists for any value of the other
    parameters.  BLP (1995): the adjustment is a contraction and converges.

  CONTROL FUNCTION SET-UP                     §13.4, p. 335, (13.11)-(13.12)
      U_nj = V(y_nj, x_nj, beta_n) + eps_nj
      y_nj = W(z_nj, gamma) + mu_nj
    eps_nj and mu_nj independent of z_nj, but correlated with each other.

  CONTROL FUNCTION                                    §13.4, p. 336, (13.13)
      eps_nj = E(eps_nj | mu_nj) + eps~_nj
      CF(mu_nj, lambda) = E(eps_nj | mu_nj)
      U_nj = V(y_nj, x_nj, beta_n) + CF(mu_nj, lambda) + eps~_nj
    "The simplest case is when E(eps_nj | mu_nj) = lambda mu_nj, such that the
     control function is simply mu_nj times a coefficient to be estimated."

  TWO-STEP CONTROL-FUNCTION ESTIMATION                    §13.4, p. 336
    1  estimate (13.12); retain residuals mu_hat_nj = y_nj - W(z_nj, gamma_hat)
    2  estimate the choice model with mu_hat_nj, and/or a parametric function
       of it, entering as extra explanatory variables

  MARGINAL COST, SEPARABLE                          §13.3.1, p. 329, (13.7)
      MC_jm = W(x_jm, c_jm, gamma) + mu_jm

  MONOPOLY / NASH PRICING RULE                      §13.3.4, p. 332, (13.9)
      p_j + (p_j / e_j) = MC_j,   e_j the own-price elasticity (negative)
    multiproduct version (§13.3.5, p. 334):  p + D^{-1} q = MC

  GENERALITY VERSUS EFFICIENCY                            §13.5, p. 342
    control function  -> specify the CONDITIONAL distribution of eps given mu.
                         More general.
    maximum likelihood -> specify the JOINT distribution.  More efficient if
                         correctly specified.
```

---

## 6. What this means for siting-atlas

### 6.1 The backlog's BLP claim is VERIFIED VERBATIM, and should not be softened

[`../ROADMAP.md`](../ROADMAP.md) under "Identification" says: "Control function
for endogeneity (Train §13.4). **Not BLP** -
Train notes BLP cannot be implemented when observed shares are zero for some
alternatives in some markets, which is this case."

The quote is at §4.1 above, printed p. 334, in the opening paragraph of §13.4.
The paraphrase is accurate, the section number is right, and the application to
us is correct: in our choice model an "alternative" is a ZCTA and a "market" is a
metro-period, and the observed share of almost every ZCTA is exactly zero,
because at most one station is sited per decision. Train's parenthetical explains
why that is fatal rather than merely awkward — "Any finite constant gives a
strictly positive predicted share, which exceeds the actual share of zero."

**This is one of the few claims in that backlog that checked out with no amendment.
Say so.** Three of the four other Train claims needed correcting (see
`docs/MODEL_SPEC.md` §0), and it is worth recording which ones survived.

### 6.2 A SECOND reason BLP is unavailable, which nobody in this project had found

§4.2 above, pp. 334-335. Constants cannot be estimated per decision maker,
because they "would be infinity (for the chosen alternative) and negative
infinity (for the nonchosen alternatives), perfectly predicting the choices and
leaving no information for estimation of parameters."

Our decisions are individual station openings, not markets containing many
consumers. Even if shares were non-zero, we have one observation per decision, so
a per-decision constant is exactly Train's degenerate case. This is the same
arithmetic as §2.5.1's "at most `J - 1` alternative-specific constants", arriving
from the other direction.

So BLP fails for us **twice over**, independently. The argument in the backlog
is stronger than the backlog knows.

### 6.3 The endogeneity we have is Train's case 3, and it is not about price

§13.1, p. 316, case 3: "Interrelated choices of decision makers ... people who
tend to like traveling on public transit ... might also tend to buy or rent homes
that are near public transit."

Translate: ZCTAs that Amazon finds attractive for unobserved reasons — industrial
zoning, highway access, a landlord willing to do a build-to-suit — are plausibly
also ZCTAs whose *observed* attributes we measure. Warehouse-heavy ZCTAs have
particular establishment counts and particular land areas. Our `establishments`
covariate is the most exposed of the three.

**Note carefully what this means for how much of Chapter 13 is usable.** Most of
the chapter is about *price* specifically — §13.3 is entirely about pricing
behaviour, and §13.4.1 is about what pricing rule makes a control function
derivable. **We have no price.** Amazon's siting decision has no observed price
variable at all; rent would be the analogue and it is 88.77% missing in
`data/processed/panel.parquet`. So §13.3 in its entirety and §13.4.1's
elasticity difficulties are inapplicable to us, and citing them would be
padding. What transfers is the §13.4 set-up, eqs. (13.11)-(13.13), which is
stated for a generic endogenous `y_nj` and not for price.

### 6.4 Why we do not fit a control function, stated as a cost not a shrug

[`../ROADMAP.md`](../ROADMAP.md) lists the control function under
"Identification", as work that would make the result credible rather than work
on the critical path. Having read §13.4, it is the right tool and it is unaffordable
now. Three reasons, in order of how binding they are.

**(a) Parameters.** The simplest control function is `CF = lambda mu_nj`, which
adds one parameter to the choice model plus a first-stage regression. At three
parameters and 28-38 decisions (`MODEL_SPEC.md` §8) that is a 33% increase in the
parameter count for the choice model alone. Train's specifications 2 and 3
(pp. 337-338) add a `sigma` or a whole Choleski factor `L` and turn the model
into a mixed logit requiring simulation. Not available.

**(b) No instrument.** We need `z_nj` affecting the endogenous covariate but
independent of the unobserved attractiveness of the ZCTA. Nothing in the panel
obviously qualifies. The BLP-style instruments (attributes of *other* products by
the same firm) have no analogue when the "firm" chooses one site at a time. This
is a data problem, not a method problem, and no amount of care fixes it.

**(c) Train's own warning.** §4.4 above: the applicability "depends on the
researcher being able to meaningfully specify" the control function and the
conditional distribution, and in some situations it is "difficult, or even
impossible". We would be picking `CF = lambda mu` and joint normality because
they are the convenient choices, not because we have a reason. That is worse
than an acknowledged omission.

`MODEL_SPEC.md` §10.2 records the threat as present, named and unaddressed.

### 6.5 The case study gives us a magnitude for what we are leaving on the table

§4.6 above. Train & Winston's price coefficient moved from -0.0434 (OLS,
ignoring endogeneity) to -0.0733 (IV) — the naive estimate understated the
magnitude by **41%**.

That is one study, on a different variable, in a different industry, and it must
not be presented as an estimate of our bias. But it is a defensible order of
magnitude for the sentence "how much could this matter?", and it is better than
the alternative, which is silence. The direction is also predictable from §4.5:
if ZCTAs with attractive unobservables also have high establishment counts, our
`establishments` coefficient is biased *away* from zero — it is picking up the
unobservable as well as the measured effect. So the covariate most likely to look
significant is the one most likely to be overstated.

### 6.6 One thing this chapter offers that we CAN use for free

§13.2.2's contraction is the same formula as Chapter 2's recalibration of
constants (`alpha_j^1 = alpha_j^0 + ln(S_j / S_hat_j^0)`, §2.8, p. 33). We have
no constants to recalibrate, so the contraction itself is unusable. But the
underlying identity — that a full set of constants forces predicted shares to
equal observed shares — has a **negative** corollary that is useful to us, and it
comes from §13.2.2, p. 323:

> "As discussed in Section 3.7.1, maximum likelihood estimation of a standard
> logit model with alternative specific constants for each product in each market
> necessarily gives predicted shares that equal sample shares."

We have **no** alternative-specific constants (`MODEL_SPEC.md` §4.5). Therefore
our predicted shares are *not* mechanically forced to match observed shares, and
comparing them is a real, non-circular diagnostic. `MODEL_SPEC.md` §9.2 reports
it. In a BLP-style model that check would be vacuous; in ours it is informative.
That is a small consolation prize for being unable to run BLP, and it is worth
banking.

---

## 7. What I did NOT read, or did not understand

- **Every page of Chapter 13 was opened**, PDF pages 1-32, as rendered images, in
  two passes (1-20, 21-32). No stretch was skimmed.
- **§13.2.4 (GMM, pp. 326-328) read at the level of statements.** I can state
  that the moments are `sum_n sum_j (d_njm - P_njm) z_njm = 0` from the choice
  model and `sum_j sum_m [delta_jm - beta_bar' v_bar] z_jm = 0` from the
  regression, that they are stacked and minimised as `g' Theta^{-1} g`, and that
  the optimal weighting matrix is `sum_n sum_j g_njm g_njm'`. I did not follow
  the efficiency comparison between MSM and MSL in any depth; Train refers it to
  Chapter 10, which I did not read.
- **§13.3.4 and §13.3.5's pricing algebra (pp. 332-334) I followed.** The
  derivation from `d pi_j / d p_j = 0` to `p_j + (p_j/e_j) = MC_j`, and the
  matrix generalisation `p + D^{-1} q = MC`, are complete in the text. I did not
  verify the sign conventions on `e_j` beyond Train's own note that "the
  elasticity is negative, which implies that `p_j + p_j/e_j` is less than `p_j`".
  None of §13.3 is applicable to us (§6.3 above) so I did not press further.
- **§13.4's specification 3 (p. 338), the Choleski-factor version, I read but do
  not fully command.** I can state that `eps^1_n` conditional on `mu_n` is normal
  with mean `M mu_n` and variance `Omega`, and that `L` is the lower-triangular
  Choleski factor, but I did not work out what restrictions on `M` and `Omega`
  are needed for identification. It is inapplicable to us and I stopped there.
- **§13.5's likelihood (pp. 341-342) read; the change-of-variables step taken on
  trust.** Train writes the joint density of `eps_n` and `y_n` as
  `g(eps_n, y_n - W(z_n, gamma))` without showing a Jacobian. I assume the
  Jacobian of `mu = y - W(z, gamma)` with respect to `y` is the identity and
  therefore unity, which is why it does not appear, but Train does not say so and
  I did not verify it.
- **Villas-Boas (2007)'s existence result (p. 340) I can state but not assess.**
  Train gives it in two sentences with no proof and no citation to a page. Whether
  it is as strong as it sounds is not something these notes can tell you.
- **Tables 13.1 (p. 343) and 13.2 (p. 345) are transcribed above from the
  rendered images.** I checked two figures against the prose: the OLS-vs-IV price
  coefficients (-0.0434, -0.0733) match p. 345, and the total price coefficient
  expression on p. 346 (`-0.0773 - 1.602/Income + 0.860 * eta/Income`) uses
  -0.0773 where Table 13.2 prints **-0.0733**. That is a one-digit discrepancy
  **in Train's own text** — almost certainly a typo on p. 346 — and it is flagged
  here rather than silently harmonised. The remaining cells were transcribed once
  and not double-entered.
- **§7.3's exploded logit**, referenced at p. 342 for the ranking data, was not
  read. Chapter 7 was opened only at §7.7 (pp. 175-182) for a different question.
- **Cited works not consulted, none in `../Research/`:** Berry (1994), BLP
  (1995, 2004), Nevo (2001), Petrin (2002), Goolsbee & Petrin (2004),
  Chintagunta, Dube & Goh (2005), Train & Winston (2007), Yang, Chen & Allenby
  (2003), Jiang, Manchanda & Rossi (2007), Heckman (1978), Hausman (1978, 1997),
  Heckman & Robb (1985), Rivers & Vuong (1988), Petrin & Train (2009), Ferreira
  (2004), Guevara & Ben-Akiva (2006), Villas-Boas & Winer (1999), Park & Gupta,
  Martin (2008), Shim & Sudit (1995), Villas-Boas (2007), Ruud (2000), Greene
  (2000). Everything attributed to them is Train's characterisation.
- **Not verified, and it matters:** my claim in §6.3 that `establishments` is our
  most endogeneity-exposed covariate. That is a judgement about warehouse siting,
  not a measurement, and nothing in this chapter or this project tests it.
