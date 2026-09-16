"""Slides 14-26: novelty, market comparison, limitations, feasibility, plan."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from pptx_kit import (BLUE, BLUE_L, GREEN, GREEN_L, INK, INK_2, LINE, MARGIN,
                      MUTED, ORANGE, ORANGE_L, PLANE, RED, RED_L, W, WHITE,
                      banner, blank, bullets, card, figure_slide, footer,
                      picture, stat, table, text, title)

FOOT = "Siting Atlas  |  Volume I: Last-Mile Delivery"


def s14_market(prs, fig_dir):
    """How this differs from what the market already sells — and the
    admission that every technique in it already exists."""
    return figure_slide(
        prs, fig_dir, "fig14_market",
        "How this differs from what the market already sells",
        "The honest version: every single technique here already exists "
        "somewhere, behind a paywall.")


def s15_novelty(prs):
    """The four novelty claims, each bounded so a product brochure
    cannot disprove it."""
    s = blank(prs)
    top = title(s, "So what is actually new?",
                "Four claims. Each written so a product brochure cannot "
                "disprove it.")
    rows = [
        ["#", "What we claim", "Why it survives checking"],
        ["1", "A new kind of safety check for AI systems that write to a "
              "statistical model",
         "Everyone else protects the DATA. Nobody checks whether a valid "
         "write breaks the CONCLUSION."],
        ["2", "The first published number for how far delivery "
              "cannibalization reaches",
         "The method is borrowed and credited. The number for same-day "
         "delivery is not published anywhere."],
        ["3", "How much of a giant company's expansion is visible from "
              "public data alone",
         "Nobody has measured this. 70% is a finding about transparency; "
         "40% is a finding about opacity."],
        ["4", "The artifact itself — free, open, checkable",
         "Every commercial equivalent is licensed and unauditable. A council "
         "cannot inspect any of them."],
    ]
    _, tbot = table(s, MARGIN, top, W - 2 * MARGIN, rows,
                    col_w=[Inches(0.42), Inches(5.2), Inches(6.48)], size=12,
                    row_h=Inches(0.62))
    banner(s, tbot + Inches(0.16),
           "We never write \"first\" or \"novel\". We write \"not published "
           "in the open literature\" and \"not available as something anybody "
           "can check.\"", accent=GREEN, fill=GREEN_L, size=14)
    text(s, MARGIN, tbot + Inches(1.14), Inches(12.1), Inches(0.42),
         "Those statements stay true no matter what Esri ships or what the "
         "operator runs internally — because none of it can be inspected.",
         size=12.5, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 15)
    return s


def s16_not_claiming(prs):
    """Three things deliberately NOT claimed. Stating them is what makes
    the remaining claims worth believing."""
    s = blank(prs)
    top = title(s, "And three things we deliberately do NOT claim",
                "We checked our own claims against the literature and the "
                "market. Three did not survive.")
    rows = [
        ["Tempting claim", "Why it fails", "What we say instead"],
        ["\"Nobody has gated an AI write before\"",
         "Extensive published work and shipped open-source tools already do "
         "this.",
         "We claim only the identification check — a distinct failure "
         "nobody covers."],
        ["\"Spatial models always fix the neighbour matrix\"",
         "Several papers estimate it. One prominent paper argues results "
         "barely depend on it.",
         "We use it as live state instead, and TEST whether that changes "
         "anything."],
        ["\"We react faster than the operator\"",
         "Compares our compute time to their approval process. Their process "
         "is slow because a human signs off $4M.",
         "Dropped entirely. It was a category error and the number was "
         "unsourceable."],
    ]
    _, tbot = table(s, MARGIN, top, W - 2 * MARGIN, rows,
                    col_w=[Inches(3.5), Inches(4.4), Inches(4.2)], size=12,
                    row_h=Inches(0.6))
    banner(s, tbot + Inches(0.18),
           "Saying this out loud is not a weakness. It is the reason to "
           "believe the four claims we kept.", accent=BLUE, fill=BLUE_L)
    footer(s, FOOT, 16)
    return s


def s17_limitations(prs):
    """Every limitation paired with the mitigation — including the four
    that have no workaround."""
    s = blank(prs)
    top = title(s, "The awkward questions, answered",
                "Every limitation, paired with what we do about it.")
    rows = [
        ["The objection", "What we do", "What still bites"],
        ["\"Census data is two years old\"",
         "The operator faced the SAME lag — there is no private census. "
         "And decisions take 18–36 months, so old data matches the "
         "decision date. We add monthly rents and building permits for what "
         "moves fast.",
         "An area that changed in the last 18 months with no permit signal. "
         "We flag it."],
        ["\"You cannot measure revenue\"",
         "Six of our eight outputs do not need it — ranking does not "
         "change if every number is scaled the same. We report profit as a "
         "multiple of margin, with the break-even value.",
         "If margin varies by area, ranking shifts. We test that as a worst "
         "case."],
        ["\"Your facility dates might be wrong\"",
         "Hand-check 100, publish the error rate, and deliberately corrupt "
         "dates in a simulation to measure how much accuracy would drop.",
         "Small stations are under-reported. Stated."],
    ]
    _, tbot = table(s, MARGIN, top, W - 2 * MARGIN, rows,
                    col_w=[Inches(2.85), Inches(6.15), Inches(3.1)],
                    size=11, row_h=Inches(0.6))
    banner(s, tbot + Inches(0.14),
           "Four things have NO workaround, and we say so. That is what makes "
           "the rest believable.", accent=RED, fill=RED_L, size=14)
    footer(s, FOOT, 17)
    return s


def s18_currency(prs, fig_dir):
    """The 'but the data is old' objection, answered in full.
    Embeds fig13_currency."""
    return figure_slide(
        prs, fig_dir, "fig13_currency",
        "\"But the data is old\" — the full answer",
        "We are not behind the decision-maker. They read the same public "
        "releases we do.")


def s19_feasible(prs):
    """Whether three people can actually build this, and the one thing
    that would have made it impossible."""
    s = blank(prs)
    top = title(s, "Can three people actually build this?",
                "We sized it before committing. The answer is yes, and here "
                "is why.")
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for v, lab, acc in [
        (SCOPE.panel_rows_label, "rows in the table we actually model on.\n"
                                 "This fits in memory on any laptop.", BLUE),
        ("$0", "compute cost. Everything runs locally or\non free tiers.",
         GREEN),
        ("16 GB", "RAM is enough. No GPU is needed\nanywhere in the "
                  "project.", BLUE),
    ]:
        stat(s, x, top, w, Inches(1.72), v, lab, accent=acc,
             fill=GREEN_L if acc == GREEN else PLANE)
        x += w + gap

    card(s, MARGIN, top + Inches(2.0), Inches(6.0), Inches(2.35),
         "THE ONE THING THAT WOULD HAVE BROKEN IT",
         "Road-network processing. Doing it for ten cities at once needs "
         "about 30 GB of working files and more memory than a student "
         "laptop has.\n\n"
         "We nearly put that on the critical path.",
         accent=RED, fill=RED_L, bsize=13)
    card(s, MARGIN + Inches(6.3), top + Inches(2.0), Inches(6.0),
         Inches(2.35),
         "THE FIX — DELETE IT AFTERWARDS",
         "We do not need a routing SERVICE. We need a TABLE of drive times.\n"
         "\nProcess one city, save the table, delete everything else, move "
         "on. Peak disk drops from 60 GB to 8 GB, and the finished app "
         "carries a 10 MB file instead of a routing engine.",
         accent=GREEN, fill=GREEN_L, bsize=13)
    text(s, MARGIN, Inches(6.35), Inches(12.1), Inches(0.5),
         "This is the kind of decision that makes a project ship on time.",
         size=13.5, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 19)
    return s


def s20_scale(prs, fig_dir):
    """Row count is the only dimension on which the project is small.
    Embeds fig12_scale."""
    return figure_slide(
        prs, fig_dir, "fig12_scale",
        f"\"Isn't {SCOPE.panel_rows_label} rows small?\"",
        "Row count is the only dimension on which this project is small "
        "— and it is small on purpose.")


def s21_data(prs):
    """The eleven sources: all free, all public, all re-downloadable."""
    s = blank(prs)
    top = title(s, "Where the data comes from",
                "Eleven sources. All free, all public, all re-downloadable "
                "by a stranger.")
    rows = [
        ["Source", "What it gives us", "How fresh"],
        ["Census ACS (5-year and 1-year)", "Income, age, population, "
         "household size", "9–24 months"],
        ["Census TIGER/Line", "The map — ZIP-area boundaries", "Annual"],
        ["Zillow rent and value indices", "Local cost of space", "Monthly"],
        ["Census County Business Patterns", "How many shops and businesses "
         "are nearby", "Annual"],
        ["Census Building Permits Survey", "Construction — a signal of "
         "change BEFORE it shows up", "Monthly"],
        ["BLS wages  ·  EIA energy prices", "What it costs to run a station "
         "in each city", "Monthly–annual"],
        ["Facility openings", "What we are predicting", "Continuous"],
        ["EPA EJScreen", "Pollution and demographic burden, for the equity "
         "map", "Periodic"],
        ["OpenStreetMap", "Drive times — used once, then deleted",
         "Continuous"],
    ]
    _, tbot = table(s, MARGIN, top, W - 2 * MARGIN, rows,
                    col_w=[Inches(4.1), Inches(6.0), Inches(2.0)], size=11,
                    row_h=Inches(0.4))
    banner(s, tbot + Inches(0.14),
           "No paid API, no licensed panel, no login. That is what makes the "
           "whole thing reproducible — and it is the point.",
           accent=GREEN, fill=GREEN_L, size=14)
    footer(s, FOOT, 21)
    return s


def s22_architecture(prs, fig_dir):
    """How the layers fit together, sources down to decision.
    Embeds fig01_architecture."""
    return figure_slide(
        prs, fig_dir, "fig01_architecture",
        "How the pieces fit together",
        "Public sources on top, the decision at the bottom. Orange marks "
        "the parts that carry the contribution.")


def s23_plan(prs):
    """The nine-week plan, including why week 0 exists."""
    s = blank(prs)
    top = title(s, "The plan",
                "Nine weeks. Week 0 exists because some decisions are cheap "
                "now and expensive later.")
    rows = [
        ["Week", "What happens", "Done when…"],
        ["0", "Decisions: what we predict, routing strategy, scope, budget",
         "All six settled in writing"],
        ["1–2", "Pipeline and the facility table",
         "Builds from scratch in one command, offline"],
        ["3", "Drive times and cost model", "Tables saved, big files deleted"],
        ["4", "The model and the backtest",
         "A real accuracy number we can defend"],
        ["5", "Cannibalization and the decay curve",
         "A published number with error bars"],
        ["6", "Money layer and the app", "Deployed, loads in under 5 seconds"],
        ["7", "The agent and the six checks",
         "Adversarial test set passing"],
        ["8", "Paper, dataset release, write-up", "Dataset public"],
        ["9", "Buffer", "Presentation delivered"],
    ]
    table(s, MARGIN, top, W - 2 * MARGIN, rows,
          col_w=[Inches(1.0), Inches(6.2), Inches(4.9)], size=11.5,
          row_h=Inches(0.4))
    footer(s, FOOT, 23)
    return s


def s24_team(prs, meta):
    """Who does what, split by pipeline stage so nothing is unowned."""
    s = blank(prs)
    top = title(s, "Who does what",
                "Split by pipeline stage, not just by module — so nothing "
                "is nobody's job.")
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for name, role, owns, q, acc in [
        (meta["p1"], "Modelling and identification",
         "Warehouse and data models\nThe siting and timing model\n"
         "Cannibalization and the decay curve\nThe agent and the six checks",
         "\"How do you know it's cause,\nnot coincidence?\"", BLUE),
        (meta["p2"], "Data and reproducibility",
         "All eleven data sources\nDrive-time tables\nAutomated data checks\n"
         "Tests and continuous integration",
         "\"Does it build from scratch,\nin one command?\"", ORANGE),
        (meta["p3"], "Delivery and communication",
         "The application, both views\nCharts and the equity map\n"
         "Executive deck and write-ups\nThe public dataset release",
         "\"What decision does\nsomeone actually make?\"", BLUE),
    ]:
        card(s, x, top, w, Inches(3.5), name.upper(),
             f"{role}\n\n{owns}", accent=acc,
             fill=ORANGE_L if acc == ORANGE else WHITE, hsize=14, bsize=12.5)
        text(s, x + Inches(0.2), top + Inches(3.62), w - Inches(0.4),
             Inches(0.8), f"Owns the answer to:\n{q}", size=11.5,
             color=MUTED, italic=True, spacing=1.2)
        x += w + gap
    footer(s, FOOT, 24)
    return s


def s25_budget(prs):
    """The budget, and the two costs a reader would expect to see that
    are not there."""
    s = blank(prs)
    top = title(s, "Budget",
                "One number, inside the cap. Compute is free; the only cost "
                "is AI usage.")
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for v, lab, acc, fill in [
        ("$80", "estimated total spend", GREEN, GREEN_L),
        ("$100", "hard cap from the course rubric", BLUE, PLANE),
        ("$0", "compute, hosting, storage and data", GREEN, GREEN_L),
    ]:
        stat(s, x, top, w, Inches(1.7), v, lab, accent=acc, fill=fill)
        x += w + gap
    rows = [
        ["Line item", "Cost", "How it is controlled"],
        ["AI usage — reading news, agent tools", "$55",
         "Responses cached; a hard stop fires at $80"],
        ["Contingency", "$25", "Only released by an explicit decision"],
        ["Storage, hosting, database, pipeline, CI", "$0",
         "Free tiers and open-source tools"],
        ["All eleven data sources", "$0", "Public — no paid API, no key"],
    ]
    _, tbot = table(s, MARGIN, top + Inches(2.0), W - 2 * MARGIN, rows,
                    col_w=[Inches(5.4), Inches(1.5), Inches(5.2)], size=12,
                    row_h=Inches(0.44))
    banner(s, tbot + Inches(0.16),
           "Two components a reader might expect — a fine-tuned writing "
           "model and a multi-model comparison — are out of scope. Neither "
           "answers any question that matters here.",
           accent=BLUE, fill=BLUE_L, size=13.5)
    footer(s, FOOT, 25)
    return s


def s26_ask(prs):
    """The six decisions this presentation is asking to have signed off."""
    s = blank(prs)
    top = title(s, "What we would like from you today")
    card(s, MARGIN, top, Inches(6.0), Inches(2.9),
         "SIX DECISIONS WE NEED SIGNED OFF",
         "1.  Predict service enablement, not order volume\n"
         "2.  Precompute drive times, then delete the engine\n"
         "3.  Use Census business counts, not a paid directory\n"
         "4.  Keep the fine-tuned writer and model comparison\n"
         "     out of scope\n"
         "5.  Four claims, not seven\n"
         "6.  Budget of $80, inside the $100 cap",
         accent=ORANGE, fill=ORANGE_L, bsize=13.5)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.9),
         "WHAT WE WILL BRING BACK",
         "A real accuracy number from a real forecast —\n"
         "trained on data through 2023, scored against\n"
         "what actually happened in 2024–25.\n\n"
         "A public dataset nobody else has published.\n\n"
         "A working tool a city council could open.",
         accent=GREEN, fill=GREEN_L, bsize=13.5)
    banner(s, Inches(4.85),
           "Proprietary data produces conclusions nobody can check. For a "
           "decision communities have standing to contest, checkability IS "
           "the product.", accent=BLUE, fill=BLUE_L, size=15)
    text(s, MARGIN, Inches(6.0), Inches(12.1), Inches(0.6),
         "Thank you — questions welcome.",
         size=18, bold=True, color=INK, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 26)
    return s
