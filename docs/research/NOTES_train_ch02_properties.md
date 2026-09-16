# Notes — Train (2009) Ch. 2, Properties of Discrete Choice Models

*Read in full on 2026-09-13, every page, as images. This is the chapter that
carries §2.2, which this project has been citing as the rule it broke. The
short version of section 6 below: **§2.2 says less than we have been claiming,
and the sentence we actually needed is in Chapter 3.***

---

## 1. Citation and local file

```
  Kenneth E. Train, Discrete Choice Methods with Simulation, 2nd edition.
  Cambridge University Press, 2009.  Chapter 2, "Properties of Discrete
  Choice Models", printed pp. 11-33.  Part I, "Behavioral Models".

  Local file:  ../Research/Ch02_p9-33.pdf   (25 PDF pages)
  PDF page 1 = printed p. 9 (the Part I divider).  PDF page 2 = p. 10, blank.
  Chapter 2 itself starts on PDF page 3 = printed p. 11.
  So: PDF page = printed page - 8.  Printed p. 33 = PDF page 25.
  Verified: PDF page 3 carries the running foot "11" and the heading
  "2 Properties of Discrete Choice Models".
```

Every page number below is the **printed** page.

Confusable with nothing else in `../Research/` — the Train chapters are split
one file per chapter and named by printed page range.

The text layer is clean. Figures 2.1 and 2.2 (p. 30) are line drawings; the
axis labels are legible in the rendered image and are transcribed below, but
the curves themselves are of course not extractable.

---

## 2. What the chapter is for

This is the chapter that defines the objects every later chapter manipulates.
It has four jobs. (i) It says what a *choice set* has to be before a discrete
choice model can be applied at all (§2.2). (ii) It derives choice probabilities
from random utility maximisation in a way that is common to logit, GEV, probit
and mixed logit, so that those models differ only in the assumed density of the
unobserved term (§2.3-2.4). (iii) It works out what is and is not *identified*,
which comes down to two slogans — only differences in utility matter, and the
scale of utility is arbitrary — and then chases their consequences through
alternative-specific constants, sociodemographic variables, and the covariance
matrix (§2.5). (iv) It says how to get from individual-level probabilities to
market-level quantities without introducing bias (§2.6-2.8).

What we want from it: the choice-set criteria, because the project's central
methodological claim rests on them; and §2.6, because our whole reframe ends in
an aggregation step (`P(served) = P(station opens) x P(site within 15 miles)`)
and §2.6 is about exactly how that aggregation may and may not be done.

---

## 3. Section-by-section walkthrough

### §2.1 Overview (p. 11)

Half a page. Announces the chapter: choice set, choice probabilities from
utility maximisation, the four model families, the fact that "Utility, as a
constructed measure of well-being, has no natural level or scale", and
aggregation and forecasting.

### §2.2 The Choice Set (pp. 11-14)

**Three characteristics are required.** Quoted in full in section 4 below,
because this is the passage the project keeps citing. In summary:

```
  1  MUTUALLY EXCLUSIVE  from the decision maker's perspective.
       "Choosing one alternative necessarily implies not choosing any of
        the other alternatives. The decision maker chooses only one
        alternative from the choice set."
  2  EXHAUSTIVE          all possible alternatives are included.
       "The decision maker necessarily chooses one of the alternatives."
  3  FINITE              the researcher can count the alternatives and
       eventually be finished counting.
```

**And then, immediately, the sentence our documents never quote (p. 12):**

> "The first and second criteria are not restrictive. Appropriate definition of
> alternatives can nearly always assure that the alternatives are mutually
> exclusive and the choice set is exhaustive."

He then gives the recipe. If `A` and `B` are not mutually exclusive because
both can be chosen, redefine the alternatives as "`A` only", "`B` only", and
"both `A` and `B`", which "are necessarily mutually exclusive". If the set is
not exhaustive, add an alternative "none of the other alternatives".

The worked example is household choice of heating fuel (pp. 12-13). Natural
gas, electricity, oil and wood "violate both mutual exclusivity and
exhaustiveness" — a household can have a gas central heater *and* electric room
heaters, and a household can have no heating at all. Two repairs are offered
for exclusivity: enumerate every combination of fuels as an alternative, or
define the choice as the choice of *primary* fuel under a researcher-specified
rule for which fuel is primary. The trade-off is spelled out: enumerating
combinations avoids an arbitrary "primary" rule and lets you study multi-fuel
use, but needs data that distinguish the combinations, and gives a much larger
choice set; restricting to primary fuel needs less data and is easier to
estimate and forecast. Two repairs are offered for exhaustiveness: include "no
heating" as an alternative, or redefine the choice as conditional on having
heating and drop the households without it.

The governing sentence (p. 12):

> "The appropriate specification of the choice set in these situations is
> governed largely by the goals of the research and the data that are available
> to the researcher."

**The third criterion is the restrictive one** (p. 13):

> "In contrast, the third condition, namely, that the number of alternatives is
> finite, is actually restrictive. This condition is the defining characteristic
> of discrete choice models and distinguishes their realm of application from
> that for regression models."

He then pushes back on the folk distinction that regressions do "how much" and
discrete choice does "which": number of cars owned (0, 1, 2, ...) is a
perfectly good discrete choice set, and Train et al. (1987a) modelled the number
and duration of phone calls with a discrete choice model rather than a
regression, to handle nonlinear price schedules.

### §2.3 Derivation of Choice Probabilities (pp. 14-17)

Thurstone (1927), Marschak (1960), the term *random utility model*. An
important disclaimer (p. 14):

> "It is important to note, however, that models derived from utility
> maximization can also be used to represent decision making that does not
> entail utility maximization. The derivation assures that the model is
> consistent with utility maximization; it does not preclude the model from
> being consistent with other forms of behavior."

Set-up: decision maker `n`, `J` alternatives, utility `U_nj`, chooses `i` iff
`U_ni > U_nj` for all `j != i`. The researcher observes `x_nj` (attributes of
alternatives) and `s_n` (attributes of the decision maker) and specifies
`V_nj = V(x_nj, s_n)`, *representative utility*. Decompose
`U_nj = V_nj + eps_nj`.

The definitional point about `eps` (p. 15) is worth holding on to:

> "Given its definition, the characteristics of `eps_nj`, such as its
> distribution, depend critically on the researcher's specification of `V_nj`.
> In particular, `eps_nj` is not defined for a choice situation *per se*.
> Rather, it is defined relative to a researcher's representation of that
> choice situation."

Choice probability, eqs. (2.1) and (2.2), p. 15:

```
  P_ni = Prob(U_ni > U_nj  for all j != i)
       = Prob(eps_nj - eps_ni < V_ni - V_nj  for all j != i)      (2.1)

       = integral  I(eps_nj - eps_ni < V_ni - V_nj  for all j != i)
                   f(eps_n) d eps_n                                (2.2)
```

A `J`-dimensional integral over the density of the unobserved utility. "Different
discrete choice models are obtained from different specifications of this
density."

Car/bus illustration (pp. 16-17): if `V_c = 4` and `V_b = 3`, the person takes
the bus iff `eps_b - eps_c > 1`. Three admissible interpretations of the density
are given (p. 17) — the share of a population facing the same observed utility,
the researcher's subjective probability, and quixotic factors internal to the
decision maker.

### §2.4 Specific Models (pp. 17-19)

A preview. Logit: `eps_nj` iid extreme value; the critical part is that the
unobserved factors are *uncorrelated over alternatives* and have the *same
variance*. GEV: generalised extreme value, allows correlation, collapses to
logit when correlations are zero, closed form so no simulation needed. Probit:
`eps_n ~ N(0, Omega)`, any correlation and heteroskedasticity, limited only by
reliance on the normal. Mixed logit: unobserved factors decompose into a part
with any distribution plus an iid extreme value part; can approximate any
discrete choice model.

Logit's independence assumption "also enters when a logit model is applied to
sequences of choices over time. The logit model assumes that each choice is
independent of the others" (p. 18).

### §2.5 Identification of Choice Models (pp. 19-29)

The two slogans, stated on p. 19: "Only differences in utility matter" and "The
scale of utility is arbitrary."

#### §2.5.1 Only Differences in Utility Matter (pp. 19-23)

Adding a constant `k` to every alternative's utility changes nothing.
"A colloquial way to express this fact is, 'A rising tide raises all boats.'"
Consequences:

**Alternative-specific constants** (pp. 20-21). With `V_nj = x'_nj beta + k_j`,
the ASC "captures the average effect on utility of all factors that are not
included in the model", the same function as a regression intercept. Including
them makes `E(eps_nj) = 0` by construction. But only *differences* in constants
are identified, so one must be normalised, usually to zero.

> "With `J` alternatives, at most `J - 1` alternative-specific constants can
> enter the model, with one of the constants normalized to zero. It is
> irrelevant which constant is normalized to zero: the other constants are
> interpreted as being relative to whichever one is set to zero."
> — p. 21

**Sociodemographic variables** (pp. 21-22). Attributes of the decision maker do
not vary over alternatives, so "They can only enter the model if they are
specified in ways that create differences in utility over alternatives." Two
ways: interact with an alternative dummy (`theta_b Y` on the bus alternative
only, with the car coefficient normalised to zero, so `theta_b` is the
*differential* effect of income on bus relative to car), or interact with an
alternative attribute (`beta M_nj / Y`, cost divided by income), in which case
"there is no need to normalize the coefficients".

**Number of independent error terms** (pp. 22-23). The `J`-dimensional integral
reduces to `J - 1` dimensions over the density `g` of error *differences*. And
then the identification statement: any `g(eps~_nk)` is consistent with an
infinite number of different `f(eps_n)`, so "one dimension of the density of
`f(eps_n)` is not identified and must be normalized by the researcher".

#### §2.5.2 The Overall Scale of Utility Is Irrelevant (pp. 23-29)

`U^0_nj = V_nj + eps_nj` and `U^1_nj = lambda V_nj + lambda eps_nj` give the
same choices for any `lambda > 0`. Standard fix: normalise the error variance.

*With iid errors* (pp. 24-25). Normalising one error variance normalises them
all. If `Var(eps^0_nj) = sigma^2` and we set it to 1, the estimated coefficients
are `beta / sigma` — "the effect of the observed variables *relative to* the
standard deviation of the unobserved factors". The logit convention is
`pi^2 / 6 ~ 1.6`, so logit coefficients are `sqrt(1.6)` times larger than
independent-probit coefficients on the same data. The Chicago/Boston worked
example (p. 25): cost and time coefficients `-0.55, -1.78` in Chicago and
`-0.81, -2.69` in Boston; the *ratio* is 0.309 vs 0.301, essentially identical,
but the Boston coefficients are about fifty percent larger, which means the
unobserved portion of utility has *less* variance in Boston.

*With heteroskedastic errors* (pp. 25-26). Normalise the variance in one segment
and estimate `k = Var(eps^C) / Var(eps^B)` for the other. Chicago utilities are
divided by `sqrt(k)`; `k_hat = 1.2` means unobserved variance is twenty percent
greater in Chicago.

*With correlated errors* (pp. 27-29). Now setting the variance of one *error* is
not enough; you must set the scale of one error *difference*. Worked in a
four-alternative example with `Omega` in eq. (2.3), the differenced covariance
matrix `Omega~_1`, and the normalised `Omega~*_1` in eq. (2.5). The count:

> "On recognizing that only differences matter and that the scale of utility is
> arbitrary, the number of covariance parameters drops from ten to five. A model
> with `J` alternatives has at most `J(J-1)/2 - 1` covariance parameters after
> normalization."
> — p. 28

Closing note (p. 29): for logit and nested logit "the normalization ... is
automatic with the distributional assumptions that are placed on the error
terms" — it is probit and mixed logit that require the researcher to think about
it.

### §2.6 Aggregation (pp. 29-32)

**This section is a warning, and it applies directly to our planned
decomposition.** Discrete choice models are nonlinear in the explanatory
variables, so (p. 29):

> "Discrete choice models are not linear in explanatory variables, and
> consequently, inserting aggregate values of the explanatory variables into the
> models will not provide an unbiased estimate of the average probability or
> average response."

Figure 2.1 (p. 30) is the picture. Two individuals with representative utilities
`a` and `b` on the horizontal axis, the sigmoid choice-probability curve above
them. The *average probability* `(P_a + P_b)/2` sits above the *probability at
the average representative utility* — the curve evaluated at `(a+b)/2`. ASCII
sketch of what the figure shows:

```
  P
  1 |                          ____----------
    |                      _--'
    |   average prob  .....*      <- (P_a + P_b)/2
    |                   _-'
    |  prob at avg  ....*         <- P((a+b)/2), LOWER here
    |              _-'
  0 |____......---'________________________  V
         a     (a+b)/2      b
```

> "In general, the probability evaluated at the average representative utility
> underestimates the average probability when the individuals' choice
> probabilities are low and overestimates when they are high."
> — p. 29

Figure 2.2 (p. 30) makes the same point for *derivatives*: the slope at `a` and
at `b` are both small, so the average derivative is small, but the slope at
`(a+b)/2` is very large. Talvitie (1976) found mode-choice elasticities at the
average representative utility "can be as much as two or three times greater or
less than the average of the individual elasticities".

Two legitimate routes are given.

**§2.6.1 Sample enumeration** (p. 31). "The most straightforward, and by far the
most popular, approach." Each sampled decision maker `n` carries a weight `w_n`,
the number of decision makers similar to him in the population. Then

```
  N_hat_i = sum_n w_n P_ni
```

and the market share is `N_hat_i / N`. Average derivatives and elasticities are
obtained the same way: compute per person, then take the weighted average.

**§2.6.2 Segmentation** (pp. 31-32). If the explanatory variables are few and
take few values, partition the population into segments (the example: four
education levels x two genders = eight segments) and use
`N_hat_i = sum_s w_s P_si` with `w_s` the number of decision makers in segment
`s`.

### §2.7 Forecasting (p. 32)

Adjust the sample or the weights so the sample "*looks like* a sample that would
be drawn in the future year" — either change the variable values per sampled
decision maker, or change the weights. Under segmentation only the weights can
move, "since the distinct values of the explanatory variables define the
segments".

### §2.8 Recalibration of Constants (p. 33)

If forecasting into an area or year whose unobserved factors differ from the
estimation sample, and market-share data are available for that area, the
alternative-specific constants can be *recalibrated* iteratively:

```
  alpha_j^1 = alpha_j^0 + ln( S_j / S_hat_j^0 )
```

where `S_j` is the actual share and `S_hat_j^0` the predicted share under the
current constants. "The adjustment is repeated until predicted shares equal
actual shares (within a tolerance)." Note for later: the identical formula
reappears in Chapter 13 as BLP's *contraction*.

---

## 4. Verbatim quotes for anything load-bearing

**The three criteria, §2.2, p. 11.** This is the passage the project cites.
Quoted in full so nobody has to paraphrase it again:

> "Discrete choice models describe decision makers' choices among alternatives.
> The decision makers can be people, households, firms, or any other
> decision-making unit, and the alternatives might represent competing products,
> courses of action, or any other options or items over which choices must be
> made. To fit within a discrete choice framework, the set of alternatives,
> called the *choice set*, needs to exhibit three characteristics. First, the
> alternatives must be *mutually exclusive* from the decision maker's
> perspective. Choosing one alternative necessarily implies not choosing any of
> the other alternatives. The decision maker chooses only one alternative from
> the choice set. Second, the choice set must be *exhaustive*, in that all
> possible alternatives are included. The decision maker necessarily chooses one
> of the alternatives. Third, the number of alternatives must be finite. The
> researcher can count the alternatives and eventually be finished counting."
> — §2.2, p. 11

**The qualifier, §2.2, p. 12:**

> "The first and second criteria are not restrictive. Appropriate definition of
> alternatives can nearly always assure that the alternatives are mutually
> exclusive and the choice set is exhaustive."

**Which criterion actually bites, §2.2, p. 13:**

> "In contrast, the third condition, namely, that the number of alternatives is
> finite, is actually restrictive. This condition is the defining characteristic
> of discrete choice models and distinguishes their realm of application from
> that for regression models."

**On how many constants, §2.5.1, p. 21:**

> "With `J` alternatives, at most `J - 1` alternative-specific constants can
> enter the model, with one of the constants normalized to zero."

**On aggregation, §2.6, p. 29:**

> "Discrete choice models are not linear in explanatory variables, and
> consequently, inserting aggregate values of the explanatory variables into the
> models will not provide an unbiased estimate of the average probability or
> average response."

**On the error term being relative to the model, not the world, §2.3, p. 15:**

> "In particular, `eps_nj` is not defined for a choice situation *per se*.
> Rather, it is defined relative to a researcher's representation of that choice
> situation."

---

## 5. Definitions the chapter gives formally

```
  CHOICE SET                                                  §2.2, p. 11
    The set of alternatives. Must be (1) mutually exclusive from the
    decision maker's perspective, (2) exhaustive, (3) finite.

  REPRESENTATIVE UTILITY                                      §2.3, p. 15
    V_nj = V(x_nj, s_n), the function the researcher specifies relating
    observed attributes of alternative j and of decision maker n to
    utility.  "Usually, V depends on parameters that are unknown to the
    researcher and therefore estimated statistically."

  RANDOM UTILITY MODEL                                        §2.3, p. 14
    A model derived under the assumption that the decision maker chooses
    the alternative with the greatest utility: choose i iff
    U_ni > U_nj for all j != i.

  CHOICE PROBABILITY                                     §2.3, p. 15, (2.2)
    P_ni = integral I(eps_nj - eps_ni < V_ni - V_nj  for all j != i)
                    f(eps_n) d eps_n

  ALTERNATIVE-SPECIFIC CONSTANT                              §2.5.1, p. 20
    k_j in V_nj = x'_nj beta + k_j.  "captures the average effect on
    utility of all factors that are not included in the model."

  SCALE PARAMETER / NORMALIZATION                            §2.5.2, p. 24
    U^0 = V + eps^0 with Var(eps^0) = sigma^2 is equivalent to
    U^1 = x'(beta/sigma) + eps^1 with Var(eps^1) = 1.  Estimated
    coefficients are beta/sigma.

  MAXIMUM NUMBER OF COVARIANCE PARAMETERS                    §2.5.2, p. 28
    J(J-1)/2 - 1, after normalising for differences and scale.

  SAMPLE ENUMERATION                                         §2.6.1, p. 31
    N_hat_i = sum_n w_n P_ni, with w_n the number of decision makers in
    the population similar to sampled decision maker n.

  RECALIBRATION OF CONSTANTS                                   §2.8, p. 33
    alpha_j^1 = alpha_j^0 + ln( S_j / S_hat_j^0 )
```

---

## 6. What this means for siting-atlas

### 6.1 THE CORRECTION. §2.2 does not say what our own documents said it says.

The diagnosis, as it stood when these notes were written, read:

> "Train (2009) §2.2 gives the test in one line: a choice set must be *mutually
> exclusive*. ZCTA-quarters are not — 'ZIP A switched on' and 'ZIP B switched
> on' are one outcome observed dozens of times, not two outcomes."

That was the text of `PLAN.md` §3, since retired; `STATUS.md` repeated it, and
the brief that commissioned these notes calls §2.2
"the rule this project broke". Having now read the section, three things are
wrong or overstated, and they should be fixed rather than defended.

> **Since fixed.** The correction below has been carried into
> [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.2, which is now the
> canonical statement of the diagnosis, and into
> [`../STATUS.md`](../STATUS.md) §8. Both now cite §3.7.1 p. 61.

**(a) §2.2 governs a CHOICE SET, and the hazard model did not have one.** Train's
mutual exclusivity is a property of a set of alternatives *facing a decision
maker*, and it means one specific thing: "Choosing one alternative necessarily
implies not choosing any of the other alternatives. The decision maker chooses
only one alternative from the choice set." A discrete-time cloglog hazard on
ZCTA-quarters is not a discrete choice model. There is no decision maker
choosing among ZCTA-quarters, so there is nothing for exclusivity to be true or
false of. Applying §2.2 to those rows is a category error, not a diagnosis. The
rule is real; the panel was simply not the kind of object the rule is about.

**(b) Train explicitly says the criterion is *not restrictive*.** Page 12: "The
first and second criteria are not restrictive. Appropriate definition of
alternatives can nearly always assure that the alternatives are mutually
exclusive." He then gives a two-line recipe for repairing any violation. That is
the opposite of a fatal test. Our documents present §2.2 as a check that "costs
nothing and would have prevented everything"; Train presents it as a modelling
convention you satisfy by naming the alternatives properly. The criterion Train
calls restrictive is the *third* one — finiteness — which the hazard model
satisfied trivially.

**(c) The sentence we actually needed is in Chapter 3, not Chapter 2.** The
defect in the hazard panel is that its ZCTA-level "events" were generated by a
far smaller number of siting decisions plus a fifteen-mile disk, so the rows are
not independent and the effective sample is an order of magnitude smaller than
the row count. The `power` block of `experiments/hazard-model/artefacts/hazard_report.json` bounds
it: `n_events_zcta` 487 against `n_independent_episodes` 28 and
`n_usable_facilities` 38. (Do **not** write "104 decisions" — that is the
*national* frame in `national_facilities.csv`, which nothing in `src/` reads.
The fitted panel is the 43-station pilot frame.) Train states the assumption
that this violates on p. 61, in §3.7.1, when he builds the likelihood:

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is `L(beta) = prod_n prod_i
> (P_ni)^{y_ni}`."
> — Train §3.7.1, p. 61 (Ch. 3, quoted here because it is the correct citation
>   for our claim)

That is the load-bearing assumption, it is about *independence across
observations*, and it is exactly what a 58-ZIP catchment breaks. The standard
name for the failure is clustering or pseudo-replication, not non-exclusivity.
See `NOTES_train_ch03_logit.md` §6 for the fuller version.

**What to change in the documents.** The *diagnosis* — unit of analysis, 812
ZCTA rows from a few dozen decisions, model capacity spent drawing circles — is
correct and should stand. Only the citation and the word are wrong. Suggested
replacement wording, since adopted at
[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.2:

> The hazard panel's 812 ZCTA-quarter events came from about 104 siting
> decisions plus a fifteen-mile catchment, so the rows are not independent.
> Train's logit likelihood (§3.7.1, p. 61) is built on "assuming that each
> decision maker's choice is independent of that of other decision makers", and
> that is the assumption the panel violated. Train §2.2 is then the authority
> for how to build the *successor* choice set, not the indictment of the old
> one: it requires alternatives that are mutually exclusive, exhaustive and
> finite, and it says the first two "are not restrictive" because the researcher
> can nearly always redefine alternatives to satisfy them.

This is a *smaller* claim and a *better* one, because it survives someone
opening the book.

### 6.2 §2.2 is, however, exactly the right authority for the NEW choice set

The demonstration that the successor specification satisfies §2.2 belongs in
`docs/MODEL_SPEC.md` and is written out there. The three checks are:

```
  mutually exclusive  one station opening is sited in exactly one ZCTA, and
                      siting it in ZCTA j necessarily means not siting it in
                      any other ZCTA in the metro.  Satisfied by construction.
  exhaustive          the station must go somewhere in the metro, so the set
                      of candidate ZCTAs in metro m is exhaustive CONDITIONAL
                      on a station opening there.  Train p. 13 licenses this
                      move explicitly: the heating example's second repair is
                      "redefine the choice situation as being the choice of
                      heating fuel conditional on having heating", and by
                      doing so the researcher "is relieved of the need for data
                      that relate to these households."
  finite              2,333 ZCTAs in the pilot frame.  Countable.
```

Note that the conditional construction is not a dodge we invented; it is the
second of the two repairs Train offers for exhaustiveness, with the cost stated
plainly — you give up the ability to model *whether* a station opens, and must
supply that factor separately.

### 6.3 §2.5.1 forbids alternative-specific constants in our model, and this is a real constraint

"With `J` alternatives, at most `J - 1` alternative-specific constants can enter
the model" (p. 21). With ZCTAs as alternatives, `J` is in the thousands and we
have 38 decisions. Alternative-specific constants are therefore not available:
they would be unidentified, and with one observation per chosen alternative they
would be infinite in the way Train describes for the individual-level case at
p. 335 (Ch. 13). **Every covariate in the utility must be a generic attribute of
the ZCTA with a coefficient common to all alternatives.** That rules out
per-ZCTA fixed effects, which is also why the BLP route is closed to us — see
`NOTES_train_ch13_endogeneity.md` §6.

### 6.4 §2.6 constrains how the `P(served)` decomposition may be computed

[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.3 states the derived
ZIP-level answer as

```
  P(your ZIP gets same-day service)
    =  P(a station opens in your metro)      from base rates
    x  P(the chosen site is within 15 miles) from the choice model
```

§2.6 says how the second factor may be aggregated and how it may not. It may
**not** be computed by averaging ZCTA covariates within a metro and evaluating
the choice model once at the average. Figure 2.1 shows why, and since our
per-ZCTA probabilities are *low* (of order `1/J`), Train's rule tells us the
direction of the error in advance: "the probability evaluated at the average
representative utility underestimates the average probability when the
individuals' choice probabilities are low" (p. 29). It **must** be computed by
sample enumeration (§2.6.1) — evaluate `P_nj` for every candidate ZCTA and sum
over the ones inside the fifteen-mile disk. That is cheap here and there is no
excuse for the shortcut.

Concretely, in `src/siting_atlas/models/`, the function that turns choice
probabilities into a served-ZIP probability must loop over alternatives and sum,
never average covariates first. This is a one-line rule with a citation and it
goes in the module docstring.

### 6.5 §2.8 is the honest route to other metros, and it is a route we cannot yet take

Recalibration of constants (p. 33) is the standard way to transfer a choice model
to a new area whose unobserved factors differ: adjust the constants so predicted
shares match observed shares in the new area. It requires observed shares in the
target area. We do not have them for the 52 CBSAs outside the pilot frame, which
is another way of saying the national panel (104 rows, 101 buildings) cannot be
used for validation until someone decides what its covariates are. Logged, not
actioned; it belongs to `STATUS.md` step 8.

### 6.6 Things this chapter confirms rather than changes

- The `V = ln(beta'a)` question is Chapter 3, not Chapter 2. Nothing in Chapter
  2 speaks to functional form.
- "Utility has no natural level or scale" (§2.1, p. 11) is the reason our
  estimated coefficients will not be comparable in magnitude to Houde, Newberry
  & Seim's cost parameters even though both describe Amazon siting. Their
  parameters are in dollars; ours will be in units of the standard deviation of
  unobserved utility (§2.5.2, p. 24). Do not put them in the same table.

---

## 7. What I did NOT read, or did not understand

- **Every page of Chapter 2 was opened**, PDF pages 1-25, as rendered images.
  No stretch was skimmed. Pages 9 and 10 are the Part I divider and a blank.
- **Figures 2.1 and 2.2 (p. 30) are line drawings.** I read the axis labels and
  the callouts ("Average probability", "Probability at average", `a`, `(a+b)/2`,
  `b`) from the rendered image and transcribed the argument from the surrounding
  prose, which states the conclusion explicitly. I did not attempt to read
  numerical values off the curves; there are none marked.
- **The algebra of §2.5.2's correlated-error case (eqs. 2.3-2.5, pp. 27-28) I
  followed but did not re-derive.** I can state that `Omega~_1` is the covariance
  of the error differences relative to alternative 1, that dividing by
  `sqrt(sigma_11 + sigma_22 - 2 sigma_12)` sets the scale, and that the count
  goes from ten parameters to five in the four-alternative case. I did not verify
  the general `J(J-1)/2 - 1` count by construction; I am taking it as stated.
- **Chapter 1 (pp. 1-8) was not read.** It is in `../Research/Ch01_p1-8.pdf`.
  Nothing in Chapter 2 forward-references it in a way that mattered here.
- **Cited works not consulted:** Thurstone (1927), Marschak (1960), McFadden
  (1974, 2001), Train et al. (1987a), Talvitie (1976), Swait & Louviere (1993),
  Bradley & Daly (1994), Ben-Akiva & Morikawa (1990). None is in
  `../Research/`. The Talvitie "two or three times" elasticity figure in §6.4
  above is Train's characterisation, not something I checked.
- **§3.7.1 is quoted in section 6.1 above and is from Chapter 3, not this
  chapter.** It was read in full as part of `NOTES_train_ch03_logit.md`; it is
  cross-quoted here because it is the correct citation for a claim our documents
  currently attach to §2.2.
