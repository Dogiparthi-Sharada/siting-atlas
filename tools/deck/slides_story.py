"""Slides 1-13: the problem, what we predict, and the three hard ideas.

Written for a mixed audience — the professor and teammates who have not
read the proposal. No jargon without a plain-English gloss on the same slide.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE
from hazard_metrics import HAZARD

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from pptx_kit import (BLUE, BLUE_L, GREEN, GREEN_L, INK, INK_2, LINE, MARGIN,
                      MUTED, ORANGE, ORANGE_L, PLANE, RED, RED_L, W, WHITE,
                      banner, blank, bullets, card, figure_slide, footer,
                      picture, stat, table, text, title)

FOOT = "Siting Atlas  |  Volume I: Last-Mile Delivery"


def s01_title(prs, meta):
    """Title slide: the project name, volume and one-line premise."""
    s = blank(prs)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), W, Inches(0.16))
    bar.fill.solid(); bar.fill.fore_color.rgb = ORANGE
    bar.line.fill.background(); bar.shadow.inherit = False

    text(s, MARGIN, Inches(1.55), Inches(12), Inches(1.1), "SITING ATLAS",
         size=54, bold=True, color=BLUE)
    text(s, MARGIN, Inches(2.6), Inches(12), Inches(0.5),
         "Volume I  |  Last-Mile Delivery", size=19, color=ORANGE)
    text(s, MARGIN, Inches(3.35), Inches(11.4), Inches(1.0),
         "An open model of where private infrastructure gets built\n"
         "— and who bears the consequences.",
         size=22, color=INK, spacing=1.25)
    line = s.shapes.add_shape(1, MARGIN, Inches(4.62), Inches(3.2),
                              Inches(0.035))
    line.fill.solid(); line.fill.fore_color.rgb = LINE
    line.line.fill.background(); line.shadow.inherit = False

    text(s, MARGIN, Inches(4.95), Inches(6), Inches(1.2),
         f"{meta['p1']}   ·   {meta['p2']}   ·   {meta['p3']}\n"
         f"MS Business Analytics, CSU East Bay\n"
         f"Course instructor: {meta['instructor']}",
         size=13, color=INK_2, spacing=1.35)
    text(s, MARGIN, Inches(6.62), Inches(12.1), Inches(0.4),
         "Not affiliated with, endorsed by or sponsored by any operator "
         "analysed. Operator names are used descriptively.",
         size=9, color=MUTED, italic=True)
    return s


def s02_one_sentence(prs):
    """The project in one sentence, plus why 'anyone can rebuild it' is
    the claim that matters."""
    s = blank(prs)
    text(s, MARGIN, Inches(1.5), Inches(12.1), Inches(2.6),
         "Big retailers decide which ZIP codes get same-day delivery.\n"
         "Each one costs them $3–5 million.\n\n"
         "Those decisions happen inside private models nobody outside\n"
         "the company can see — but the consequences are public.",
         size=27, color=INK, spacing=1.3)
    banner(s, Inches(4.5),
           "We build an open version of that decision, from free public data "
           "— and then check whether it actually predicts what they did.")
    text(s, MARGIN, Inches(5.75), Inches(12.1), Inches(0.6),
         "That last part is the whole project. Anyone can build a model. "
         "Very few get scored against reality.",
         size=14, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 2)
    return s


def s03_problem(prs):
    """Frames the decision: what turning on same-day in one ZIP costs,
    and the three things that decide whether it pays."""
    s = blank(prs)
    top = title(s, "The decision, in plain terms",
                "Turning on same-day delivery in one ZIP code is a capital "
                "project, not a software setting.")
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for head, body, acc, fill in [
        ("IT NEEDS A BUILDING",
         "Same-day is not '2-day but faster'. It needs different "
         "buildings, closer to customers — a delivery station within "
         "about 30 minutes of the door.",
         BLUE, WHITE),
        ("IT IS DECIDED ZIP BY ZIP",
         "Service is switched on per ZIP code. Two neighbouring ZIPs in the "
         "same city can differ. So the ZIP is the unit of decision.",
         BLUE, WHITE),
        ("IT IS EXPENSIVE TO GET WRONG",
         f"{SCOPE.per_activation} per ZIP. Across the {SCOPE.zctas_label} ZIPs we model, that is {SCOPE.capital} "
         "billion of capital being allocated.",
         ORANGE, ORANGE_L),
    ]:
        card(s, x, top + Inches(0.1), w, Inches(2.5), head, body,
             accent=acc, fill=fill, bsize=13.5)
        x += w + gap

    banner(s, Inches(4.55),
           "And the three things that decide whether a ZIP is profitable all "
           "interact.", accent=BLUE, fill=BLUE_L)
    text(s, MARGIN + Inches(0.3), Inches(5.62), Inches(12), Inches(1.1),
         "1.  How many orders are genuinely NEW      "
         "2.  How DENSE the deliveries are      "
         "3.  How many orders were STOLEN from 2-day shipping",
         size=14.5, color=INK_2, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 3)
    return s


def s04_who_cares(prs, fig_dir):
    """The four stakeholder groups and the decision each one makes
    differently once the model exists. Embeds fig11_stakeholders."""
    return figure_slide(
        prs, fig_dir, "fig11_stakeholders",
        "Who actually uses this",
        "Four groups, each with a decision the model changes — and none "
        "of them can buy this today.")


def s05_target(prs):
    """The choice of target variable — enablement, not volume — which is
    the single most consequential design decision in the project."""
    s = blank(prs)
    top = title(s, "What exactly are we predicting?",
                "The single most important design choice in the project.")
    card(s, MARGIN, top, Inches(6.0), Inches(2.2),
         "THE QUESTION WE ASK",
         "For each ZIP code:\n\n"
         "     Will the operator turn on same-day\n"
         "     delivery here — and when?\n\n"
         "Both are visible from outside. You can type a ZIP into their own "
         "delivery checker.",
         accent=GREEN, fill=GREEN_L, bsize=13.5)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.2),
         "WHY THAT MATTERS",
         "Because it means we can be SCORED.\n\n"
         "We make a prediction. Reality tells us whether we were right.\n\n"
         "Most student projects cannot do this. It is the difference between "
         "a model and a forecast.",
         accent=BLUE, bsize=13.5)
    banner(s, Inches(4.15),
           "Example:  in 2023 the model says ZIP 85008 has a 72% chance of "
           "same-day within 18 months. Then we check 2024–25.",
           accent=BLUE, fill=BLUE_L, size=14)
    text(s, MARGIN, Inches(5.3), Inches(12.1), Inches(1.2),
         "The tempting alternative was to predict order VOLUME per ZIP. "
         "Nobody outside the company can see that number — so it would "
         "have to be invented. The next slide shows why inventing it is a "
         "trap.", size=15, color=INK_2, spacing=1.25)
    footer(s, FOOT, 5)
    return s


def s06_circularity(prs):
    """The circularity trap: why predicting order volume would have made
    the model learn its own output. The best story in the deck."""
    s = blank(prs)
    top = title(s, "The trap we avoided",
                "Worth understanding properly — it is the best story in "
                "the project.")
    card(s, MARGIN, top, Inches(6.0), Inches(2.75),
         "IF WE HAD PREDICTED ORDER VOLUME",
         "Step 1.  Nobody publishes volume per ZIP,\n"
         "            so we would have to invent it —\n"
         "            split total orders by income and\n"
         "            shop density.\n\n"
         "Step 2.  Then build a model that uses income\n"
         "            and shop density to predict it.\n\n"
         "The answer is made of the same ingredients\n"
         "as the question.",
         accent=RED, fill=RED_L, bsize=13)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.75),
         "THE SAME MISTAKE, IN EVERYDAY TERMS",
         "I define a student's 'talent score' as\n"
         "     0.6 x height  +  0.4 x shoe size\n\n"
         "Then I build a model predicting talent score\n"
         "from height and shoe size.\n\n"
         "It scores 97% accurate — and has learned\n"
         "nothing about talent. It rediscovered my own\n"
         "formula.",
         accent=RED, fill=RED_L, bsize=13)
    banner(s, Inches(4.68),
           "And the dangerous part: the BETTER the score looked, the more "
           "completely it proved the bug.", accent=RED, fill=RED_L)
    text(s, MARGIN, Inches(5.82), Inches(12.1), Inches(0.9),
         "Switching to \"did they turn it on here?\" fixes it, because that "
         "number comes from the world, not from us.",
         size=16, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 6)
    return s


def s07_cannibalisation(prs):
    """Idea 1, cannibalisation: why more orders is not more money."""
    s = blank(prs)
    top = title(s, "Idea 1 — cannibalization",
                "Why more orders does not mean more money.")
    card(s, MARGIN, top, Inches(6.0), Inches(2.5),
         "THE PROBLEM",
         "Before same-day, a household orders 8 items\n"
         "a month on 2-day shipping.\n\n"
         "After same-day launches, they order 9 —\n"
         "all same-day.\n\n"
         "Naive read: 'same-day generated 9 orders!'\n"
         "Reality: 1 new order, and 8 that were\n"
         "switched to a more expensive method.",
         accent=BLUE, bsize=13)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.5),
         "AND IT LEAKS NEXT DOOR",
         "Same-day launches in Berkeley — not in\n"
         "neighbouring Emeryville.\n\n"
         "But an Emeryville resident works in Berkeley,\n"
         "now has a same-day address at the office, and\n"
         "shifts their ordering.\n\n"
         "Emeryville's numbers move even though\n"
         "Emeryville was never switched on.",
         accent=ORANGE, fill=ORANGE_L, bsize=13)
    banner(s, Inches(4.42),
           "That leak is why the usual statistical methods break here — "
           "your 'untreated' comparison group was partly treated.",
           accent=ORANGE, fill=ORANGE_L)
    text(s, MARGIN, Inches(5.55), Inches(12.1), Inches(0.9),
         "So instead of assuming how far the leak reaches, we measure it.",
         size=17, bold=True, color=INK, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 7)
    return s


def s08_decay(prs, fig_dir):
    """Idea 1 measured — the distance-band spillover estimate.
    Embeds fig05_decay."""
    return figure_slide(
        prs, fig_dir, "fig05_decay",
        "Idea 1 — how far the leak reaches, and how we would measure it",
        "We draw rings around each launched ZIP and estimate the effect in "
        "each ring separately. The curve shown is illustrative: this "
        "estimand has not been touched.",
        note="Do NOT read a number off this slide. The decay curve is four "
             "literal arrays in the figure source; nothing has been "
             "estimated. What is real here is the design — Pollmann's "
             "distance-band estimator, credited, with the spatial weight "
             "matrix derived from the estimate rather than assumed. If "
             "asked why it is in the deck at all: because it is the second "
             "estimand in the proposal and it is the one that may be more "
             "tractable than siting with the data we have.")


def s09_gates(prs):
    """Idea 2, the agent: the four obvious safety checks, and the two
    nobody writes."""
    s = blank(prs)
    top = title(s, "Idea 2 — the AI agent, and the thing that surprised us",
                "The agent reads competitor news and updates our data. "
                "Letting it write is where it gets interesting.")
    card(s, MARGIN, top, Inches(5.7), Inches(2.35),
         "THE FOUR OBVIOUS SAFETY CHECKS",
         "1.  Is the data shaped correctly?\n"
         "2.  Do the coordinates exist on Earth?\n"
         "3.  Is the AI confident enough?\n"
         "4.  Is it logged so we can undo it?\n\n"
         "Everybody building these systems has these.",
         accent=BLUE, bsize=13)
    card(s, MARGIN + Inches(6.05), top, Inches(6.25), Inches(2.35),
         "A REAL EXAMPLE",
         "The agent reads: \"Walmart opens a sortation\n"
         "centre in Plano, Texas.\"  It writes the record.\n\n"
         "Schema OK.  Plano is real.  Confidence 0.94.\n"
         "Logged.     ALL FOUR CHECKS PASS.\n\n"
         "The data is perfect.",
         accent=ORANGE, fill=ORANGE_L, bsize=13)
    banner(s, Inches(4.28),
           "But Plano's neighbours just changed  ->  our comparison group "
           "changed  ->  the estimate changed  ->  the answer moved by "
           "millions.", accent=RED, fill=RED_L, size=14)
    text(s, MARGIN, Inches(5.42), Inches(12.1), Inches(0.55),
         "The data is fine. The conclusion is broken. And nothing checked "
         "for that.", size=19, bold=True, color=RED, align=PP_ALIGN.CENTER)
    text(s, MARGIN, Inches(6.05), Inches(12.1), Inches(0.7),
         "So we add two more checks:  (5) did this move a comparison ZIP into "
         "the treated group?   (6) did the answer move more than we agreed in "
         "advance? If so, stop and ask a human.",
         size=13.5, color=INK_2, align=PP_ALIGN.CENTER, spacing=1.2)
    footer(s, FOOT, 9)
    return s


def s10_gates_fig(prs, fig_dir):
    """Idea 2 drawn — six gates, data integrity versus inferential
    integrity. Embeds fig03_agent_gates."""
    return figure_slide(
        prs, fig_dir, "fig03_agent_gates",
        "Idea 2, drawn — six checks, not four",
        "Checks 1–4 protect the DATA. Checks 5–6 protect the CONCLUSION. "
        "That distinction is our main contribution.")


def s11_portfolio(prs):
    """Idea 3: the answer is a basket, not a ranked list, because two
    ZIPs judged alone do not add up."""
    s = blank(prs)
    top = title(s, "Idea 3 — it is a shopping basket, not a ranked list",
                "The instinct is to score every ZIP and take the top 20. "
                "That is wrong.")
    card(s, MARGIN, top, Inches(6.0), Inches(2.4),
         "TWO ZIPS, JUDGED ALONE",
         "ZIP A on its own:   loses $200,000\n"
         "     too few deliveries to justify a station\n\n"
         "ZIP B on its own:   loses $150,000\n"
         "     same problem\n\n"
         "A ranked list rejects both.",
         accent=RED, fill=RED_L, bsize=13.5)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.4),
         "THE SAME TWO, TOGETHER",
         "They are next to each other, so they can\n"
         "SHARE one delivery station.\n\n"
         "Combined deliveries cross the efficiency\n"
         "threshold. Cost per package drops 30%.\n\n"
         "Together:   makes $1,100,000",
         accent=GREEN, fill=GREEN_L, bsize=13.5)
    banner(s, Inches(4.35),
           "A ranked list never even evaluates the pair. So we choose "
           "bundles instead.")
    text(s, MARGIN, Inches(5.5), Inches(12.1), Inches(1.1),
         "Honest note: this is not our invention. Supply-chain software has "
         "optimised multi-site networks for twenty years. We include it "
         "because a ranked list is simply the wrong model of the decision "
         "— it is a correctness fix, not a claim to novelty.",
         size=13.5, color=MUTED, italic=True, spacing=1.22,
         align=PP_ALIGN.CENTER)
    footer(s, FOOT, 11)
    return s


def s12_accuracy(prs):
    """The four distinct things 'accuracy' means here, and why all four
    get reported rather than the flattering one."""
    s = blank(prs)
    top = title(s, "How we say how confident we are",
                "\"Accuracy\" means four different things. We report all four.")
    w, gap = Inches(2.94), Inches(0.2)
    x = MARGIN
    for head, body, acc in [
        ("DOES IT RANK WELL?",
         "AUC.  Pick one ZIP that got service and one that didn't — how "
         "often does the model score the right one higher?\n\n"
         f"0.5 = coin flip.  We targeted 0.80 and measured "
         f"{HAZARD.auc:.4f}.", BLUE),
        ("ARE THE ODDS HONEST?",
         "Calibration.  When the model says '60% chance', does it happen "
         "about 60% of the time?\n\n"
         "Matters because councils act on that number.", BLUE),
        ("HOW WRONG COULD WE BE?",
         "Conformal intervals.  We give a range — and then CHECK the "
         "range works on held-out data.\n\n"
         "A measured guarantee, not an assumed one.", ORANGE),
        ("WOULD THE ANSWER CHANGE?",
         "Rank stability.  Re-run everything many times with slightly "
         "different assumptions; does this ZIP stay in the top ten?\n\n"
         "SPECIFIED, NOT YET RUN.", ORANGE),
    ]:
        card(s, x, top, w, Inches(2.85), head, body, accent=acc,
             fill=ORANGE_L if acc == ORANGE else WHITE, hsize=12, bsize=11.5)
        x += w + gap
    banner(s, Inches(4.75),
           f"What the third one measured:  we asked for "
           f"{HAZARD.nominal_coverage * 100:.0f}% coverage and got "
           f"{HAZARD.empirical_coverage * 100:.2f}% — inside the "
           f"{HAZARD.coverage_tolerance * 100:.1f}pp band that "
           f"{HAZARD.n_effective} independent units allow.",
           accent=BLUE, fill=BLUE_L, size=14)
    text(s, MARGIN, Inches(5.9), Inches(12.1), Inches(0.6),
         "That is the question an executive actually has, and almost no "
         "student project answers it.",
         size=13.5, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 12)
    return s


def s13_backtest(prs, fig_dir):
    """The measured backtest, which the model failed. Embeds fig08_backtest."""
    return figure_slide(
        prs, fig_dir, "fig08_backtest",
        "We scored it, and it failed",
        f"AUC {HAZARD.auc:.4f} against {HAZARD.null_auc:.4f} for a constant. "
        f"Brier {HAZARD.brier:.6f} against {HAZARD.null_brier:.6f}. "
        f"Calibration error {HAZARD.ece:.5f} against {HAZARD.null_ece:.5f}.",
        note="Every number on this slide is read from "
             "outputs/metrics/hazard_report.json. The model ranks slightly "
             "better than chance and forecasts no better than a constant, "
             "and is worse calibrated than one. That is the finding: the "
             "unit of analysis was wrong, not the sample size.")
