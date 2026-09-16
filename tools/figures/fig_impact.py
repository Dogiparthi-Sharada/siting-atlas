"""Figures 11-12: stakeholder / use-case map, and scale-and-impact."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE

import numpy as np
import matplotlib.pyplot as plt

from common import (AQUA, AXIS, BLUE, CRITICAL, GOOD, GRID, INK, INK_2, MUTED,
                    ORANGE, PLANE, SEQ, SURFACE, arrow, band, blank_canvas,
                    box, newtag, recede_axes, save)


def fig11_stakeholders(out):
    """Who makes a different decision because this exists."""
    fig, ax = blank_canvas(10.4, 5.0)

    box(ax, 33, 79, 34, 15,
        "SITING ATLAS\nranked propensity + timing window\n+ NPV bands + EJ "
        "overlay", edge=BLUE, face="#eaf2fc", lw=2.0, fs=8, weight="bold")

    users = [
        (1.5, "MUNICIPAL PLANNERS\n& AIR DISTRICTS",
         "DECISION\napprove / condition / deny a\npermit; size mitigation;\n"
         "offer a tax abatement?",
         "South Coast AQMD Rule 2305\n(WAIRE) is EPA-approved and\n"
         "is being copied elsewhere", ORANGE, "#fdf0ea"),
        (26, "COMMUNITY & EJ\nORGANISATIONS",
         "DECISION\nwhere to organise, comment\nor litigate  -  BEFORE the\n"
         "permit is filed",
         "predicted burden by\ndemographic stratum;\nno public equivalent "
         "exists", ORANGE, "#fdf0ea"),
        (50.5, "COMPETING OPERATORS\n& 3PLs",
         "DECISION\ndefensive siting; where to\nlease; which trade areas\n"
         "are exposed",
         "market-structure\ntransparency, not\nadversarial intelligence",
         BLUE, SURFACE),
        (75, "RESEARCHERS",
         "DECISION\nwhich method to test; what\nto benchmark against",
         "open panel + harness =\na dataset-and-benchmark\ncontribution",
         BLUE, SURFACE),
    ]
    for x, title, decision, why, edge, face in users:
        box(ax, x, 30, 23.5, 40, "", edge=edge, face=face, lw=1.5)
        ax.text(x + 11.75, 66, title, ha="center", va="top", fontsize=7.8,
                fontweight="bold", color=INK, linespacing=1.4)
        ax.text(x + 1.6, 57.5, decision, ha="left", va="top", fontsize=6.9,
                color=INK_2, linespacing=1.5)
        ax.text(x + 1.6, 40.5, why, ha="left", va="top", fontsize=6.5,
                color=MUTED, style="italic", linespacing=1.45)
        arrow(ax, (50, 79), (x + 11.75, 70), color=AXIS, rad=0.08)

    box(ax, 1.5, 12, 47.5, 14,
        "THE KILLER QUESTION  -  already in your model\n\n"
        "\"Would they have built here anyway?\"\n"
        "The Heckman selection propensity IS the tax-abatement "
        "counterfactual.",
        edge=GOOD, face="#eaf7ea", fs=7.4, align="left")
    box(ax, 51, 12, 47.5, 14,
        "AND THE CEILING IS ITSELF A FINDING\n\n"
        "70% explainable -> a result about TRANSPARENCY\n"
        "40% explainable -> a result about OPACITY, and how much\n"
        "disclosure would close it.  You cannot lose.",
        edge=GOOD, face="#eaf7ea", fs=7.4, align="left")

    ax.text(50, 6,
            "\"Proprietary data produces conclusions nobody can check. For a "
            "decision that communities have\nstanding to contest, "
            "checkability IS the product.\"",
            ha="center", va="top", fontsize=7.8, color=INK, style="italic",
            linespacing=1.5)

    ax.set_title("Who makes a different decision because this "
                 "exists", loc="left", x=0.01, y=1.01)
    return save(fig, out, "fig11_stakeholders")


def fig12_scale(out):
    """Row count is the only axis where this is small."""
    fig = plt.figure(figsize=(10.4, 4.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.18], wspace=0.22)

    # -- left: the reframe ---------------------------------------------------
    ax = fig.add_subplot(gs[0])
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    box(ax, 0, 74, 100, 22,
        "WHAT A MANAGER HEARS\n\n"
        f"\"{SCOPE.panel_rows_label} rows  /  {SCOPE.panel_mb:.0f} MB\"\n-> college project",
        edge=CRITICAL, face="#fbeaea", fs=8, align="left")
    arrow(ax, (50, 72), (50, 62), color=ORANGE, lw=2.0)
    ax.text(52, 67, "measure the right thing", fontsize=7.2, color=ORANGE,
            style="italic", va="center")
    box(ax, 0, 34, 100, 26,
        "WHAT IT ACTUALLY RANKS\n\n"
        f"{SCOPE.zctas_label} markets  x  {SCOPE.per_activation} per activation\n"
        f"= {SCOPE.capital} of capital allocation\n"
        "national, if scaled:  $99B - $165B",
        edge=GOOD, face="#eaf7ea", fs=8, align="left", weight="bold")
    ax.text(0, 26, "Managers do not fund rows. They fund decisions.",
            fontsize=8, color=INK, fontweight="bold", va="top")
    ax.text(0, 18,
            "\"I deliberately kept the panel small. The contribution\n"
            "is identification, not throughput  -  I would rather spend\n"
            f"the compute on {SCOPE.draws} uncertainty draws than on\n"
            "scanning rows I do not need.\"",
            fontsize=7.3, color=INK_2, va="top", style="italic",
            linespacing=1.6)
    ax.set_title("A.  Decision value, not row count", loc="left", fontsize=10)

    # -- right: every other axis is large ------------------------------------
    ax = fig.add_subplot(gs[1])
    axes_lbl = ["Row count", "Data volume", "Integration\ncomplexity",
                "Temporal\ndepth", "Compute\n(MC draws)",
                "Search space\n(portfolio)", "Decision value"]
    score = [1.0, 1.4, 7.2, 6.0, 8.6, 10.0, 9.4]
    note = [f"{SCOPE.panel_rows_label} rows", "~15 GB through",
            "13 sources, 5 grains", "11 yrs, 156 wks", SCOPE.draws,
            SCOPE.search_space, SCOPE.capital]
    y = np.arange(len(axes_lbl))[::-1]
    colors = [CRITICAL] + [BLUE] * 5 + [GOOD]

    ax.barh(y, score, color=colors, height=0.6, zorder=3)
    for yi, s, n in zip(y, score, note):
        ax.text(s + 0.18, yi, n, va="center", fontsize=7.6, color=INK,
                fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(axes_lbl, fontsize=7.8)
    ax.set_xlim(0, 14.5)
    ax.set_xticks([])
    ax.set_xlabel("relative magnitude (illustrative)")
    ax.set_title("B.  Row count is the ONLY axis where this is small",
                 loc="left", fontsize=10)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.set_axisbelow(True)

    fig.suptitle("Scale and impact  -  answering \"isn't this just "
                 "a college project?\"", x=0.008, y=1.03, ha="left",
                 fontsize=11, fontweight="bold")
    fig.text(0.008, -0.05,
             "Because the panel is small, national coverage is nearly free:  "
             "all 33,000 US ZCTAs at quarterly grain = 0.46 GB.",
             fontsize=7.3, color=MUTED, style="italic")
    return save(fig, out, "fig12_scale")


def fig13_currency(out):
    """Data currency: why a lagged covariate is the right covariate."""
    fig = plt.figure(figsize=(10.4, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.26)

    # -- left: sources ordered by reporting lag ------------------------------
    ax = fig.add_subplot(gs[0])
    srcs = [("ACS 5-year (ZCTA)", 21, BLUE),
            ("Census CBP", 18, BLUE),
            ("BLS OES wages", 12, BLUE),
            ("ACS 1-year (metro)", 9, ORANGE),
            ("Building permits", 2, ORANGE),
            ("EIA energy prices", 2, ORANGE),
            ("Zillow ZORI / ZHVI", 1, ORANGE),
            ("Facility openings", 1, AQUA)]
    y = np.arange(len(srcs))[::-1]
    for yi, (lab, lag, col) in zip(y, srcs):
        ax.barh(yi, lag, color=col, height=0.6, zorder=3)
        ax.text(lag + 0.5, yi, f"{lag} mo", va="center", fontsize=7.6,
                color=INK, fontweight="bold")
    ax.axvspan(18, 36, color=GRID, zorder=0)
    ax.text(27, 4.2, "operator's own\ndecision lead time\n18 - 36 months",
            ha="center", va="center", fontsize=7.4, color=INK_2,
            style="italic", linespacing=1.4)
    ax.set_yticks(y)
    ax.set_yticklabels([s[0] for s in srcs], fontsize=8)
    ax.set_xlabel("reporting lag (months)")
    ax.set_xlim(0, 38)
    ax.set_title("A.  Sources by reporting lag", loc="left", fontsize=10)
    recede_axes(ax, x_grid=True, y_grid=False)

    # -- right: the argument -------------------------------------------------
    ax2 = fig.add_subplot(gs[1])
    ax2.axis("off")
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    box(ax2, 0, 68, 100, 28,
        "THE LAG IS SHARED, NOT A HANDICAP\n\n"
        "A facility opening in 2025 was decided in\n"
        "2023 on 2021-22 covariates. The operator's\n"
        "planners read the same public releases we do.\n"
        "Aligning covariate vintage to DECISION vintage\n"
        "is correct specification, not a compromise.",
        edge=GOOD, face="#eaf7ea", fs=7.4, align="left")
    box(ax2, 0, 34, 100, 28,
        "AND WE BLEND BY FREQUENCY\n\n"
        "slow sources  ->  LEVEL features\n"
        "fast sources  ->  RATE-OF-CHANGE features\n\n"
        "permits are a FORWARD signal: construction\n"
        "precedes population.",
        edge=ORANGE, face="#fdf0ea", fs=7.4, align="left")
    box(ax2, 0, 2, 100, 26,
        "RESIDUAL RISK, STATED\n\n"
        "An area that changed sharply in the last 18\n"
        "months with no permit or rent signal will be\n"
        "misclassified. Where fast and slow signals\n"
        "disagree, the area is flagged low-confidence.",
        edge=CRITICAL, face="#fbeaea", fs=7.4, align="left")
    ax2.set_title("B.  Why this is defensible", loc="left", fontsize=10)

    fig.suptitle("Data currency  -  blending slow and fast sources",
                 x=0.008, y=1.02, ha="left", fontsize=11, fontweight="bold")
    return save(fig, out, "fig13_currency")


BUILDERS = [fig11_stakeholders, fig12_scale, fig13_currency]
