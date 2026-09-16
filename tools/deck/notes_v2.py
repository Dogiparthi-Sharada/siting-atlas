"""Presenter notes for the technical supplement.

Audience: the professor and anyone with methods training. These notes assume
you can already state the equation — they cover what to EMPHASISE, what the
likely objection is, and where to stop talking.
"""

NOTES = {
1: """
OPEN   "This is the technical companion. I'll assume potential outcomes,
       panel methods and synthetic control."
LAND   Set expectations: this deck defends identification, not the story.
TIMING 20 seconds.
""",
2: """
OPEN   "Four claims, and I want to be precise about what each excludes."
LAND   The 'Bounded by' column is the point. Each claim is fenced by the
       prior art that would otherwise falsify it.
IF ASKED  "Why is C2 only a parameter claim?" - because the estimator is
       Pollmann's. Claiming the method would be false.
TIMING 2.5 minutes. Do not rush - this slide is the thesis.
""",
3: """
OPEN   "Two prior-art reviews - literature and shipped product."
LAND   Left column is closed, right column is open. We report both.
IF ASKED  "Did you find these before or after writing the claims?" - after
       writing, before submitting. Three claims did not survive.
TIMING 1.5 minutes.
""",
4: """
OPEN   "Four questions. RQ2 is pre-registered."
LAND   RQ2's note. Fixing the prediction in advance is what makes a null
       result a finding rather than a rationalisation.
IF ASKED  "Is RQ4 a research question or a descriptive statistic?" - it is
       descriptive and unreported. Both can be true.
TIMING 2 minutes.
""",
5: """
OPEN   "Notation, briefly, so the rest is unambiguous."
LAND   Two estimands: hazard of first enablement is primary; theta is
       secondary. Point at the right-censoring in E_i.
TIMING 1.5 minutes. Do not read the whole block aloud.
""",
6: """
OPEN   "Why enablement rather than volume. This is an identification
       argument, not a data-availability excuse."
LAND   The left panel. R-squared is bounded below by the approximation error
       of f to g. It tells you nothing about the phenomenon.
IF ASKED  "Couldn't you validate the allocation externally?" - only in
       aggregate, which does not identify the cross-sectional split, which
       is exactly what the model is being asked to produce.
TIMING 3 minutes. The strongest methodological slide in the deck.
""",
7: """
OPEN   "The siting model."
LAND   Cloglog is the grouped-duration analogue of proportional hazards, so
       the interval width we chose does not drive the specification.
IF ASKED  "Why not Cox?" - the data are grouped into quarters, ties are
       pervasive, and discrete time handles that natively.
IF ASKED  "Random effects or fixed?" - random, because many metros have few
       events and we want partial pooling. Say we report both.
TIMING 2 minutes.
""",
8: """
OPEN   "Selection. Treatment assignment is endogenous by construction."
LAND   Do NOT defend the instrument. Say the exclusion restriction is
       contestable, then show the sensitivity path.
       'Survival under a plausible violation is worth more than a claim of
       no violation.'
IF ASKED  "Your instrument is weak / invalid" - agree that it is
       contestable, give the correlation with employment density yourself,
       and go to the sign-flip point.
TIMING 3 minutes. Expect the hardest question of the session here.
""",
9: """
OPEN   "Every assumption, labelled testable, partially testable or not."
LAND   Three rows say 'known violated'. That is deliberate - we handle them
       rather than assume them away.
IF ASKED  "SUTVA is violated and you still use SCM?" - yes, and we estimate
       the violation rather than assume it away. Next slides.
TIMING 2 minutes.
""",
10: """
OPEN   "Synthetic control, with one modification."
LAND   The donor pool line. Contamination defined by estimated rho-hat, not
       by contiguity - that is what keeps the pool non-empty in saturated
       metros.
IF ASKED  "How many donors survive?" - we report pool size and weight
       concentration per estimate, and 'not estimable' where it collapses.
TIMING 2.5 minutes.
""",
11: """
OPEN   "Inference. With one treated unit an asymptotic standard error is not
       credible."
LAND   The null is built from the data. Then the RMSPE ratio and why the
       denominator matters.
IF ASKED  "Isn't the permutation p-value coarse with a small donor pool?" -
       yes, and we report the pool size alongside it. With 40 donors the
       finest attainable p is 1/41.
TIMING 2.5 minutes.
""",
12: """
OPEN   "The spillover kernel, estimated rather than assumed."
LAND   Credit Pollmann explicitly and immediately. The parameter is the
       contribution.
IF ASKED  "Why bands rather than a smooth kernel?" - bands are
       non-parametric in the decay shape. A smooth kernel imposes one.
TIMING 2 minutes.
""",
13: """
OPEN   "And then W is built from the estimate."
LAND   The right-hand panel first, not the left. Say what we do NOT claim
       before saying what we do.
IF ASKED  "Souza and Krisztin already estimate W" - correct, and that is on
       the slide. Our difference is the update CHANNEL: exogenous text
       between cycles, not in-sample fitting once.
TIMING 2.5 minutes.
""",
14: """
OPEN   "RQ2, pre-registered."
LAND   Both branches are publishable, and kappa is fixed in advance.
IF ASKED  "How did you choose kappa?" - from the decision, not the data:
       the change in theta that would move a ZIP across the top-100
       boundary. Have a number ready.
TIMING 2 minutes.
""",
15: """
OPEN   "A quieter problem: generated regressors."
LAND   Almost nobody in the agent literature corrects for this. It is not
       novel, it is correct, and it costs a day because the labelled sample
       already exists.
IF ASKED  "How large is the correction?" - unknown until we run it, which is
       precisely why we run it.
TIMING 1.5 minutes.
""",
16: """
OPEN   "Uncertainty."
LAND   The guarantee holds for ANY underlying model. Then the caveat slide
       tile: exchangeability fails under drift, so we report coverage by
       year.
IF ASKED  "Doesn't the out-of-time split break exchangeability?" - yes, and
       that is why we report coverage by year rather than pooled. Good
       question to concede.
TIMING 2 minutes.
""",
17: """
OPEN   "The evaluation protocol, fixed before estimation."
LAND   The last two rows - label noise and H3 - exist because the first
       seven could all be artefacts.
TIMING 1.5 minutes.
""",
18: """
OPEN   "And here is what those targets actually produced."
LAND   Every target on the previous slide was missed. The proper score is
       the row to read: the model's Brier is essentially the constant's on
       the unit-clustered split and WORSE than the constant's on the
       temporal one. Calibration is worse than a constant outright.
IF ASKED  "Random splits would have looked better" - yes, and that is the
       point. Whole units are held out because a random row split lets the
       model see 2025 rows for a ZIP while predicting its 2024 rows.
IF ASKED  "Where is the geographic hold-out?" - deliberately absent. The two
       withheld metros hold two dated stations between them. It is a smoke
       test for gross failure, not a test of transfer, and quoting it as
       one would overstate the evidence against our own model.
TIMING 2 minutes.
""",
19: """
OPEN   "Each robustness check targets one specific way the result could be
       an artefact."
LAND   Read the third column, not the second. 'Failure would mean' is what
       makes each check meaningful.
TIMING 2 minutes.
""",
20: """
OPEN   "Cost. Continuous approximation, and one engineering consequence."
LAND   d_stem is a finite set, so routing is an offline job. Peak disk 8 GB
       rather than 60, and no runtime dependency.
IF ASKED  "Doesn't circuity lose road topology?" - yes, and Daganzo is
       already an approximation. We calibrate k and report the residual.
TIMING 2 minutes.
""",
21: """
OPEN   "NPV without an observable margin."
LAND   Ranking is invariant to a common positive scale factor. Six of eight
       outputs are unaffected. Then immediately the failure case: if m
       varies systematically the ranking moves.
IF ASKED  "So you can't say what a ZIP is worth?" - correct, and we say so.
       We give a_i, b_i and the break-even m.
TIMING 2.5 minutes.
""",
22: """
OPEN   "The decision layer."
LAND   Neither submodular nor supermodular, so the greedy bound does not
       apply and the gap is empirical.
IF ASKED  "Is this a contribution?" - no, and it is on the slide. Textbook
       OR and a mature commercial category. We include it because ranking is
       the wrong model.
TIMING 2 minutes.
""",
23: """
OPEN   "Now the definition that carries claim C1."
LAND   Read the CLAIM line aloud. There exist M with data integrity 1 and
       inferential integrity 0, and no published gate detects them.
IF ASKED  "Is that not just a stale-cache problem?" - no. The state is
       correct and current. It is the ESTIMATOR's assumptions that break.
TIMING 3 minutes. This is the slide the workshop paper comes from.
""",
24: """
OPEN   "Drawn, with the boundary marked."
LAND   Point at where data integrity ends and identification begins.
TIMING 1 minute.
""",
25: """
OPEN   "Agent evaluation, positioned against a public benchmark."
LAND   The Wilson interval. At n=40 a pass and a fail are indistinguishable.
       Then the MDE for the deferred comparison.
IF ASKED  "Why defer the model comparison entirely?" - because at the sample
       size we can afford, an 8-point difference is the smallest detectable,
       and the plausible spread is smaller than that.
TIMING 2 minutes.
""",
26: """
OPEN   "Threats to validity, by type."
LAND   Do not read the table. Pick the two you think this room cares about
       and speak to those.
TIMING 1.5 minutes.
""",
27: """
OPEN   "And what we cannot identify at all."
LAND   Four items, no mitigation. Say clearly: this is the reason to believe
       everything on the previous twenty-five slides.
IF ASKED  "What is the weakest part?" - the cannibalization coefficient.
       Say it before they do.
TIMING 2 minutes. Do not apologise while delivering it.
""",
28: """
OPEN   "Named extensions - directions, not commitments."
LAND   The 'why not now' column. Each is a scoping decision with a reason.
TIMING 1.5 minutes.
""",
29: """
OPEN   "Reproducibility, since the whole argument rests on checkability."
LAND   dim_scenario. A system whose parameters change in response to text is
       not auditable by default; this is what makes it so.
TIMING 1.5 minutes.
""",
30: """
OPEN   "To summarise: what we claim, and what we explicitly do not."
LAND   Read the right-hand panel slowly. Volunteering the second list is
       what makes the first credible.
THEN   Read the banner. Then stop.
TIMING 1.5 minutes, then questions.
""",
}
