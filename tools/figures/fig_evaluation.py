"""Figures 10 and 14: novelty positioning, and the competitive landscape.

Both are text-and-box schematics with no results in them. Figures 8 and 9
used to live here and were hand-typed illustrations; they are now measured
and live in fig_backtest.py.
"""

from __future__ import annotations

import matplotlib.patches as mpatches

from common import (CRITICAL, GOOD, GRID, INK, INK_2, MUTED, ORANGE, PLANE,
                    SURFACE, band, blank_canvas, box, save)


def fig10_positioning(out):
    """What the literature already owns, and what is left to claim."""
    fig, ax = blank_canvas(10.4, 5.2)

    band(ax, 1, 50, 47.5, 46, "ALREADY PUBLISHED  -  cite, do not claim")
    items = [
        ("Amazon's FC network, modelled structurally",
         "Houde, Newberry & Seim,\nEconometrica 2023"),
        ("Spatial treatments with distance decay",
         "Pollmann, Causal Inference\nfor Spatial Treatments"),
        ("Estimating W rather than fixing it",
         "Souza 2019; Krisztin &\nPiribauer; Polit. Analysis 2024"),
        ("SCM under interference / spillovers",
         "arXiv 2408.00291, 2411.01249"),
        ("Gated LLM writes to a database",
         "survey 2608.14590; SafeNlidb;\nsqlgate, llm-safe-sql"),
    ]
    for i, (what, who) in enumerate(items):
        y = 84 - i * 7.4
        ax.text(3.5, y, "x", fontsize=9, color=CRITICAL, fontweight="bold")
        ax.text(7, y + 0.6, what, fontsize=7.3, color=INK, va="center")
        ax.text(7, y - 2.4, who, fontsize=6.3, color=MUTED, va="center",
                style="italic", linespacing=1.25)

    band(ax, 51.5, 50, 47.5, 46, "STILL OPEN  -  claim exactly this")
    ours = [
        ("Inferential-integrity gates",
         "a write can pass every data gate and\nstill break identification"),
        ("Cannibalisation radius for same-day",
         "the parameter is unpublished; the\nestimator is Pollmann's"),
        ("Public-data explainability ceiling",
         "how much siting behaviour is visible\nfrom outside? nobody reports it"),
        ("Cross-operator transferability",
         "fit on one operator, score another;\nwins either way"),
    ]
    for i, (what, why) in enumerate(ours):
        y = 84 - i * 9.2
        ax.text(54, y, "v", fontsize=9, color=GOOD, fontweight="bold")
        ax.text(57.5, y + 0.8, what, fontsize=7.6, color=INK,
                fontweight="bold", va="center")
        ax.text(57.5, y - 2.6, why, fontsize=6.4, color=MUTED, va="center",
                style="italic", linespacing=1.3)

    box(ax, 1, 25, 98, 19,
        "COMMERCIAL PRIOR ART IS A DIFFERENT KIND OF DANGER\n\n"
        "Esri ArcGIS ships a tool called Measure Cannibalization. Coupa, AIMMS "
        "and Optilogic have sold\n"
        "multi-facility network optimisation for twenty years. Neither makes a "
        "claim FALSE  -  they make the\n"
        "words \"first\" and \"novel\" naive. The delta that survives: theirs "
        "is trade-area OVERLAP (geometry);\n"
        "ours is a CAUSAL effect with a counterfactual, a decay curve and a "
        "standard error.",
        edge=ORANGE, face="#fdf0ea", fs=7.3, align="left")

    box(ax, 1, 3, 98, 18,
        "THE FRAMING RULE  -  apply to every claim in the document\n\n"
        "NEVER   \"first\"  -  \"novel\"  -  \"no prior work\"  -  \"nobody "
        "has done this\"\n"
        "ALWAYS  \"not published in the open literature\"\n"
        "        \"not available as a public, reproducible artifact\"\n\n"
        "The second form stays true whatever Esri ships or Amazon runs "
        "internally, because those are\n"
        "proprietary and unreproducible. A product datasheet cannot falsify "
        "it.",
        edge=GOOD, face="#eaf7ea", fs=7.3, align="left")

    ax.set_title("Novelty positioning after the prior-art check",
                 loc="left", x=0.01, y=1.01)
    return save(fig, out, "fig10_positioning")


def fig14_market(out):
    """What already exists in the market, and the gap none of it fills."""
    fig, ax = blank_canvas(11.0, 6.0)

    cols = [("WHO", 2, 15.5), ("WHAT THEY DO WELL", 21, 27),
            ("WHAT THEY CANNOT DO", 49, 30), ("OPEN?", 80.5, 17.5)]
    for label, x, w in cols:
        ax.text(x + 0.6, 92.5, label, fontsize=7.6, fontweight="bold",
                color=INK, va="center")

    rows = [
        ("Esri ArcGIS\nBusiness Analyst",
         "Trade-area geometry, drive-time\npolygons, overlap measurement",
         "Overlap is not a causal effect.\nNo counterfactual, no donor pool,\n"
         "no standard error.", "Licensed"),
        ("Buxton, Kalibrate,\nPlacer.ai",
         "Site scoring from foot-traffic\nand mobility panels",
         "Models their own client's sites.\nCannot forecast a competitor's\n"
         "network. Panel data is licensed.", "Licensed"),
        ("Coupa, AIMMS,\nanyLogistix, Optilogic",
         "Multi-facility network\noptimisation at industrial scale",
         "Optimises YOUR network with\nASSUMED demand and KNOWN costs.\n"
         "No estimated causal interaction.", "Licensed"),
        ("Strategy consultancies",
         "Bespoke analysis, deep\ndomain judgement",
         "Six-figure engagements.\nDeliverable is a slide deck,\n"
         "not a re-runnable model.", "Private"),
        ("The operator's own\ninternal model",
         "Actual order data.\nThe ground truth we lack.",
         "Serves one company. Cannot be\ninspected, contested or reused\n"
         "by a council or a regulator.", "Never"),
        ("Academic literature\n(Econometrica, MS)",
         "Rigorous identification,\npeer-reviewed",
         "Licensed data, state grain,\nthrough ~2018, no runnable\n"
         "artifact.", "Paper only"),
    ]
    y = 84
    for who, does, cannot, open_ in rows:
        h = 11.5
        ax.add_patch(mpatches.Rectangle(
            (2, y - h), 96, h, facecolor=PLANE if y % 23 < 12 else SURFACE,
            edgecolor=GRID, linewidth=0.8, zorder=1))
        ax.text(2.6, y - h / 2, who, fontsize=7.0, fontweight="bold",
                color=INK, va="center", linespacing=1.35, zorder=3)
        ax.text(21.6, y - h / 2, does, fontsize=6.7, color=INK_2,
                va="center", linespacing=1.4, zorder=3)
        ax.text(49.6, y - h / 2, cannot, fontsize=6.7, color=CRITICAL,
                va="center", linespacing=1.4, zorder=3)
        ax.text(81.1, y - h / 2, open_, fontsize=7.0, fontweight="bold",
                color=CRITICAL, va="center", zorder=3)
        y -= h

    box(ax, 2, 2.5, 96, 12,
        "SITING ATLAS  -  the gap none of the above fills\n\n"
        "Forecasts a COMPETITOR's network  -  from PUBLIC data  -  with a "
        "CAUSAL cannibalisation estimate  -  and\n"
        "publishes the model, the panel and the code so a council, a "
        "regulator or a community group can check it.",
        edge=GOOD, face="#eaf7ea", lw=2.0, fs=7.8, weight="bold")

    ax.text(50, -1.5,
            "We claim no novelty in any single technique. Every one has a "
            "paywalled commercial equivalent. What does not exist is a "
            "version anybody can check.",
            ha="center", va="top", fontsize=7.2, color=MUTED, style="italic")

    ax.set_title("How this differs from what the market already sells",
                 loc="left", x=0.01, y=1.015)
    return save(fig, out, "fig14_market")


BUILDERS = [fig10_positioning, fig14_market]
