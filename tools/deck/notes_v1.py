"""Presenter notes for the plain-language deck.

Written to be spoken. Each entry follows the same shape:
    OPEN     the line that starts the slide
    LAND     the one idea they should leave with
    IF ASKED the interruption this slide invites, and the answer
Timings assume a 25-minute talk with 10 minutes of questions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE
from hazard_metrics import HAZARD

NOTES = {
1: """
OPEN   "Siting Atlas. One sentence: we rebuild a private billion-dollar
       decision from public data, and then check whether we got it right."
LAND   The name is operator-neutral on purpose - it survives past delivery,
       and it keeps other people's trademarks out of our product name.
TIMING 30 seconds. Do not linger.
""",
2: """
OPEN   "Here is the whole project before any jargon."
LAND   The last line is the project: we get SCORED. Anyone can build a model;
       almost nobody submits it to reality.
IF ASKED  "Why does it matter that it's public?" - because a council that
       wants to contest a decision cannot contest a model it cannot see.
TIMING 1 minute.
""",
3: """
OPEN   "Three things to know about the decision itself."
LAND   Same-day is a BUILDING problem, decided ZIP by ZIP, at $3-5M each.
       That is why the unit of analysis is the ZIP.
IF ASKED  "Why not model at city level?" - because service is switched on per
       ZIP. Two neighbouring ZIPs in one city can differ.
TIMING 1.5 minutes.
""",
4: """
OPEN   "Before the method - who actually uses this."
LAND   The tax-abatement counterfactual. A council is asked for $2M and cannot
       answer 'would they have built here anyway?'. Our propensity score IS
       that answer.
IF ASKED  "Isn't this just helping competitors?" - competitive use is real but
       it is the least interesting user. The ones who cannot buy an
       alternative are councils, air districts and community groups.
TIMING 2 minutes. This slide earns the rest of the talk - do not rush it.
""",
5: """
OPEN   "What exactly are we predicting? This is the most important design
       choice we made."
LAND   Observable outcome = we can be scored.
IF ASKED  "Why not order volume?" - that is the next slide. Say so and move.
TIMING 1.5 minutes.
""",
6: """
OPEN   "We nearly got this wrong, and the way we nearly got it wrong is
       worth two minutes."
LAND   The talent-score analogy. Deliver it slowly - pause after 'and has
       learned nothing about talent.'
       Then: the better the score looked, the more it proved the bug.
IF ASKED  "How did you catch it?" - by asking what the metric would look like
       if the model were useless. It looked identical. That is the tell.
TIMING 2.5 minutes. This is the strongest story in the deck.
""",
7: """
OPEN   "Idea one of three. Why more orders is not more money."
LAND   8 to 9 orders is ONE new order and EIGHT switched to a costlier
       method. And it leaks into neighbours, which breaks the standard
       methods.
IF ASKED  "How big is the leak?" - next slide, we measured it.
TIMING 1.5 minutes.
""",
8: """
OPEN   "So the plan is to measure it rather than assume it."
LAND   Say plainly, before anyone asks: the curve on this slide is
       illustrative. This estimand has not been touched. Do not read the
       numbers off it - they are four literal arrays in the figure source.
       What is real is the design: rings around each launched ZIP, an effect
       estimated separately in each ring, and W derived from the result
       instead of assumed.
IF ASKED  "Is the method new?" - no. It is Pollmann's estimator and we credit
       it. The parameter would be what is new, if we estimate it.
IF ASKED  "Why show an unestimated curve?" - because it is the second
       estimand in the proposal and it may be more tractable than siting
       with the data we have. It is on the roadmap, not in the results.
TIMING 2 minutes.
""",
9: """
OPEN   "Idea two. This is the part that surprised us."
LAND   Walk the Plano example one line at a time. Land hard on:
       'The data is fine. The conclusion is broken.'
       Pause there. Then give gates 5 and 6.
IF ASKED  "Isn't that just a bug?" - no, it is a category of bug nobody
       checks for, because every existing gate protects the data.
TIMING 3 minutes. The most important slide in the deck.
""",
10: """
OPEN   "Drawn out, so you can see where the boundary is."
LAND   Four checks protect DATA. Two protect the CONCLUSION. Point at the
       orange boxes.
TIMING 1 minute - the previous slide did the work.
""",
11: """
OPEN   "Idea three. A shopping basket, not a ranked list."
LAND   Two ZIPs each lose money alone and make $1.1M together, because they
       share a station. A ranking never evaluates the pair.
IF ASKED  "Is that novel?" - no, and say so first. Supply-chain software has
       done multi-site optimisation for twenty years. We include it because
       a ranking is the wrong model of the decision.
TIMING 2 minutes.
""",
12: """
OPEN   "How we say how confident we are - accuracy means four things."
LAND   The fourth one. Rank stability is what an executive actually needs and
       almost nobody reports it. Say plainly that we have not run it yet.
IF ASKED  "What is conformal prediction?" - we give a range and then CHECK
       the range works on held-out data. A measured guarantee, not an assumed
       one.
TIMING 2 minutes.
""",
13: """
OPEN   "And this is the test that makes it a forecast rather than a fit.
       We ran it. We failed it."
LAND   Say the three numbers out loud: AUC {auc} against {null_auc} for a
       constant; Brier {brier} against {null_brier}; calibration error
       {ece} against {null_ece}. A model that ignores every covariate is better
       calibrated than ours. Then say why that is worth showing: most
       projects never find out.
IF ASKED  "So the project failed?" - no, the SPECIFICATION failed, and it
       failed for a statable reason. One station switches on a median of 58
       ZIP codes at once, so the events are not independent. We are
       respecifying as a conditional choice over ZIP codes given a station
       opens.
IF ASKED  "Why not quote the skill score?" - Gneiting and Raftery 2007,
       section 2.3: skill scores are generally improper even when the
       underlying score is proper. We quote the raw pair.
TIMING 2 minutes. This is the slide to slow down on.
""",
14: """
OPEN   "Now the uncomfortable part. Here is everything that already exists."
LAND   Read the right-hand column, not the left. The gap is not capability -
       it is CHECKABILITY.
IF ASKED  "So you built a worse version of Esri?" - a worse version on
       geometry, a different thing on causality, and the only one a council
       can open.
TIMING 2 minutes. Volunteering this buys credibility for the next slide.
""",
15: """
OPEN   "So what is actually new. Four claims."
LAND   Point at the wording rule at the bottom. We never say 'first'.
IF ASKED  "Isn't claim 3 just a descriptive statistic?" - yes, and nobody has
       computed it. 70 percent is a finding about transparency, 40 percent
       about opacity.
TIMING 2 minutes.
""",
16: """
OPEN   "And three we deliberately do not make."
LAND   We checked our own claims and three did not survive. Saying so is the
       reason to believe the four we kept.
IF ASKED  "How did you find these?" - a literature check and a commercial
       prior-art check, both documented.
TIMING 1.5 minutes.
""",
17: """
OPEN   "The three questions I would ask if I were you."
LAND   Every row has a mitigation AND a residual. Then the red banner: four
       things have no workaround and we say so.
IF ASKED  "Which is the weakest part?" - the cannibalisation coefficient.
       No public number to check it against. Have that answer ready.
TIMING 2.5 minutes.
""",
18: """
OPEN   "The data-is-old objection, in full."
LAND   The operator faced the SAME lag. There is no private census. And a
       2025 opening was decided in 2023 on 2021-22 data, so our vintage
       matches the decision.
TIMING 1.5 minutes.
""",
19: """
OPEN   "Can three people actually build this? We sized it first."
LAND   The routing story. We nearly put a 30 GB dependency on the critical
       path, then realised we needed a table, not a service.
IF ASKED  "What if you need routing later?" - regenerate that metro. It is
       an offline job.
TIMING 2 minutes.
""",
20: """
OPEN   "And the scale question, since a million rows sounds small."
LAND   Row count is the ONLY axis where this is small. Say the deliberate
       line: I would rather spend compute on {draws} uncertainty draws
       than on scanning rows I do not need.
WARNING  Never claim this is big data. It collapses in thirty seconds.
TIMING 1.5 minutes.
""",
21: """
OPEN   "Eleven sources, all free and public."
LAND   No paid API, no licensed panel, no login. That constraint IS the
       contribution, not a budget limit.
IF ASKED  "Wouldn't paid data be better?" - yes, and it would destroy the
       point. A model on licensed data produces conclusions nobody can check.
TIMING 1.5 minutes.
""",
22: """
OPEN   "How the pieces fit together."
LAND   Nothing above the feature layer knows where the bytes came from. That
       is why Volume II - data centres - is a data swap, not a rewrite.
TIMING 1.5 minutes.
""",
23: """
OPEN   "Nine weeks. Week zero is decisions."
LAND   Six decisions that are cheap now and expensive later. That is what we
       want signed off today.
TIMING 1 minute.
""",
24: """
OPEN   "Who does what - split by pipeline stage, not just module."
LAND   Read the italic question under each name. Assigning modules without
       stages is how a shared pipeline becomes nobody's job.
TIMING 1 minute.
""",
25: """
OPEN   "Budget. Eighty dollars, inside the hundred-dollar cap."
LAND   Compute is zero. The only cost is model inference, and it hard-stops
       in config.
IF ASKED  "Why drop the fine-tuned model?" - eleven days and ninety dollars
       for something that answers none of the three questions that matter.
TIMING 1 minute.
""",
26: """
OPEN   "What we would like from you today."
LAND   The six decisions, then the closing line - read it slowly:
       'Proprietary data produces conclusions nobody can check. For a
       decision communities have standing to contest, checkability is the
       product.'
THEN   Stop talking. Let the first question come.
TIMING 1.5 minutes, then questions.
""",
}

# Figures quoted in the notes are derived, never typed. `.replace` rather
# than `.format` because the note text contains braces of its own.
#: Measured figures are substituted rather than typed, so a re-fit that moves
#: a number cannot leave a presenter reading the old one out loud.
_SUBS = {
    "{draws}": SCOPE.draws,
    "{auc}": f"{HAZARD.auc:.4f}",
    "{null_auc}": f"{HAZARD.null_auc:.4f}",
    "{brier}": f"{HAZARD.brier:.6f}",
    "{null_brier}": f"{HAZARD.null_brier:.6f}",
    "{ece}": f"{HAZARD.ece:.5f}",
    "{null_ece}": f"{HAZARD.null_ece:.5f}",
}


def _fill(v: str) -> str:
    """Replace every measured-figure placeholder in one note."""
    for k, val in _SUBS.items():
        v = v.replace(k, val)
    return v


NOTES = {k: _fill(v) for k, v in NOTES.items()}
