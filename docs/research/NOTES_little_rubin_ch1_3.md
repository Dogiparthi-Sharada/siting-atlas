# Notes — Little & Rubin, missing-data mechanisms

## 1. Citation and provenance

Little, R. J. A. & Rubin, D. B., *Statistical Analysis with Missing Data*,
Wiley. Chapters 1-3 (the introductory material on patterns, mechanisms and
complete-case analysis).

**PROVENANCE WARNING — read this before citing anything below.**

This file is NOT notes from a reading. The book is a textbook and could not
be downloaded; the host proxy blocks retrieval. The content below is a
**summary supplied by the user on 2026-09-13**, captured here so the project
does not lose it. No page of the book has been opened by anyone on this
project.

Treat every claim here as correct-in-substance but **unverified in
attribution**. Before any of it reaches the proposal, someone must open the
book and check the section numbers. See section 6 for a specific concern.

There is no PDF in `../Research/` for this entry.

## 2. What it is for

Little & Rubin is the standard reference for deciding whether you are allowed
to ignore *why* data is missing. Everything in the early chapters builds to
one question: when can you analyse the observed data with standard methods
and not model the missingness at all?

For this project it settles the treatment of `rent_index` (missing for 94.3%
of ZCTAs, and the observed stratum is 63.6x denser), the 43-vs-38 usable
facilities, and the listwise deletion at `cost/runner.py:166`.

## 3. The framework

Two objects, and the whole theory is about the relationship between them.

```
  Y   the COMPLETE data matrix — what you would have with no missingness.
      Partitioned per unit as Y = (Y_obs, Y_mis).

  R   the RESPONSE INDICATOR matrix. 1 = observed, 0 = missing.
      Has its own parameter, phi.

  The joint model is   P(Y, R | theta, phi).
```

`theta` parameterises the data you care about; `phi` parameterises the
missingness process. The question is when you may drop the second half and
work with `L(theta | Y_obs)` alone.

**A point that is easy to miss: "missing" is not one thing.** Nonresponse,
censoring, data-entry blanks, gaps created by merging files, and analyst
filtering ("38 usable of 43") are all missing-data problems with *different*
R processes. Each needs naming separately.

For us that means at least five distinct R processes, and we have never
written them down:

```
  rent_index          Zillow does not publish where transactions are thin
  wage_light_truck..  BLS OES matches only 388 of 928 CBSAs
  EJScreen (CT)       a broken FIPS join — a BUG, not a mechanism
  open_quarter        19 of 43 facilities have no month in the source
  43 of 101           scope restriction: the pilot metros
```

Note the third. A broken join is not a missingness mechanism at all; it is a
defect, and the correct treatment is to fix it, not to model it. Conflating
the two would be a category error.

## 4. Patterns

```
  univariate    one variable has gaps, the rest complete. Easiest case.
  monotone      variables can be ordered so that if Y_j is missing, every
                later Y_k (k > j) is missing too. Classic longitudinal
                dropout; also arises when records are enriched in stages
                (buildings -> costs -> volumes).
  general       holes anywhere. What facility panels usually look like.
```

Cross-cutting distinction: **planned vs unplanned** missingness. Planned
(you chose not to collect it) is far more benign than unplanned (a field that
should exist and does not).

For us: the panel is general-pattern and *partly planned*. The 43-of-101
restriction is planned scope. The rent gaps are unplanned. Those deserve
different sentences in the write-up, and currently get none.

## 5. Mechanisms — the core

The mechanism is `P(R | Y, phi) = P(R | Y_obs, Y_mis, phi)`.

```
  MCAR   P(R | Y) = P(R)
         Missingness depends on nothing, observed or unobserved.
         Example: a random sensor outage.
         PARTIALLY TESTABLE — compare the observed distributions of
         respondents against non-respondents on fully-observed covariates.
         Rare in practice.

  MAR    P(R | Y) = P(R | Y_obs)
         Missingness may depend on what you DO observe, but given that,
         not on what is missing.
         Example: small depots are less likely to report costs, but
         within size bands the missingness is random.
         NOT DIRECTLY TESTABLE. It makes a claim about Y_mis, which by
         construction you cannot see. You defend it by argument plus a
         rich conditioning set.

  MNAR   P(R | Y) depends on Y_mis even after conditioning on Y_obs.
         Example: facilities with embarrassingly high costs do not report
         costs. Requires modelling R (selection models, pattern-mixture
         models) or a sensitivity analysis.
```

### Ignorability — the payoff

If the mechanism is **MAR** *and* `theta` and `phi` are **distinct** (no
functional link between them; independent priors in the Bayesian version),
then likelihood and Bayesian inference may ignore the missingness model and
use `L(theta | Y_obs)`.

Two consequences that matter operationally, and that this project had wrong:

```
  MCAR licenses complete-case summaries.
  MAR  does NOT license naive complete-case means.
  MAR  DOES license likelihood-based methods.
```

That distinction is the whole practical content. Our `cost/runner.py:166`
does listwise deletion and then reports medians — a complete-case *summary*.
That is licensed only under MCAR, and we have measured that MCAR is false.

**The distinctness condition is separate from MAR and is easy to forget.**
Ignorability needs both.

## 6. The attribution problem — verify before citing

The summary as supplied attributes patterns to Chapter 2 and mechanisms to
Chapter 3. **That does not match my recollection of the book's structure**,
in either the 2nd or 3rd edition, where:

```
  §1.2   missing data patterns
  §1.3   missing data mechanisms
  Ch 3   Complete-Case and Available-Case Analysis, Including
         Weighting Methods
```

If that recollection is right, two things follow. First, citing "Little &
Rubin Ch. 3" for MAR in the proposal sends an examiner to a chapter about
complete-case analysis, which would be embarrassing. Second, and more
usefully: **Chapter 3 would then be the chapter we most need**, because
complete-case analysis and weighting is precisely our defect — and the
supplied summary does not cover its actual content at all.

I am not certain of this and have not opened the book. It must be checked.
If Chapter 3 really is complete-case analysis, we should read it: it will
contain the weighting-based alternatives to the deletion we currently do.

## 7. What this means for siting-atlas

```
  1  Never claim MCAR. We have measured it false for rent_index (63.6x
     density gap between strata). At n=43 a single selective dropout
     breaks MCAR anyway.

  2  Claim MAR conditional on named observed covariates, and say which.
     MAR is not testable, so this is an ARGUMENT, not a finding. Our
     docs have been sloppy here — see the correction below.

  3  Prefer likelihood-based estimation over deletion-then-summarise.
     The conditional choice model is already likelihood-based, which
     puts it on the right side of the line. Say so explicitly.

  4  The dropped rows need a table: ID, which fields are missing, the
     reason, and which observed covariates predict being dropped. That
     is Van den Broeck's "diagnose" step meeting the mechanism taxonomy.

  5  Sensitivity analysis is the MNAR answer. At n=43 a serious
     selection model is not fittable. Re-run the headline under two or
     three explicit stories ("the dropped are 20% costlier") and report
     the range. Same logic as the partial-identification work already
     adopted elsewhere.

  6  Multiple imputation buys little here, with one exception: if we
     impute inputs to a step that requires complete rectangular data,
     IMPUTE THEN OPTIMISE INSIDE EACH IMPUTED SET — do not optimise once
     on averaged data.
```

Item 6 has a live instance nobody has noticed. `cost/daganzo.py:91` imputes
median income to the reference value, income feeds `daily_parcels`, and
`daily_parcels` is the sample weight for depot placement in
`cost/depots.py:110`. So the depot network is already being optimised on
singly-imputed data, once, with the imputation uncertainty discarded. That is
exactly the pattern item 6 warns against. Flagged, not fixed.

## 8. A correction this forces on our own documents

`docs/data/CLEANING_LITERATURE.md` §3 says of the rent missingness: *"This is
MAR at best, given we observe density directly — and arguably MNAR."*

That overstates what was measured. What the 63.6x density gap establishes is
that the missingness is **not MCAR**. Whether it is MAR or MNAR is *not
testable from the data*, because it turns on whether missingness depends on
the unobserved rent value after conditioning on density — and the unobserved
rent is, by construction, unobserved.

The honest formulation is: measured not-MCAR; MAR is an assumption we would
be *arguing for*, not a finding; and since Zillow's publication threshold
plausibly depends on the rent level itself and not only on density, MNAR
cannot be ruled out. That is what licenses bounds rather than imputation.

## 9. What I did NOT read

Everything. No page of this book has been opened. Chapters 4 and onward
(single imputation, imputation uncertainty, likelihood theory) are not
covered here at all, and Chapter 3's actual content is not covered — see
section 6.

Outstanding: obtain the book, verify the section numbering in section 6,
and read Chapter 3 properly.
