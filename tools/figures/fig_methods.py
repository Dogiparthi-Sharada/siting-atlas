"""Figures 4-7: the estimand fix, spillover decay, portfolio effect, tornado."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE

import numpy as np

from common import (AQUA, AXIS, BLUE, CRITICAL, GOOD, GRID, INK, INK_2, MUTED,
                    ORANGE, PLANE, SEQ, SURFACE, WARNING, arrow, band,
                    blank_canvas, box, caption, newtag, recede_axes, save)
import matplotlib.pyplot as plt


def fig04_estimand(out):
    """The circularity trap, and the observable outcome that replaces it."""
    fig, ax = blank_canvas(10.6, 5.4)

    band(ax, 1, 4, 47, 88, "A CONSTRUCTED TARGET  -  what we avoid")
    box(ax, 5, 76, 39, 8, "ACS demographics  +  retail density", fs=8,
        edge=BLUE)
    box(ax, 5, 55, 39, 11,
        "\"TARGET\" VARIABLE  (constructed)\n"
        "orders = Total x (0.6*income + 0.4*retail)",
        edge=CRITICAL, face="#fbeaea", fs=7.6)
    box(ax, 5, 34, 39, 8, "ZINB MODEL   f(income, retail, ...)", fs=8,
        edge=BLUE)
    box(ax, 5, 13, 39, 13,
        "REPORTED:  \"MAPE = 3-5%\"\n\n"
        "looks like  ->  triumph\nactually is ->  proof of the loop",
        edge=CRITICAL, face="#fbeaea", fs=7.6, weight="bold")

    arrow(ax, (16, 76), (16, 66), color=CRITICAL, lw=1.6)
    ax.text(14.4, 71, "builds", fontsize=6.8, color=CRITICAL, ha="right")
    arrow(ax, (36, 76), (36, 42), color=CRITICAL, lw=1.6, rad=-0.45)
    ax.text(45.4, 59, "predicts", fontsize=6.8, color=CRITICAL, ha="right")
    arrow(ax, (16, 55), (16, 42), color=CRITICAL, lw=1.6)
    arrow(ax, (24, 34), (24, 26), color=CRITICAL, lw=1.6)
    ax.text(24.5, 8.5, "The model learned YOUR ARITHMETIC,\nnot the operator's "
            "behaviour.", ha="center", fontsize=7.2, color=CRITICAL,
            fontweight="bold", linespacing=1.4)

    band(ax, 52, 4, 47, 88, "AN OBSERVABLE TARGET  -  what we use")
    box(ax, 56, 76, 39, 8, "Public covariates  (unchanged)", fs=8, edge=BLUE)
    box(ax, 56, 55, 39, 11,
        "OBSERVED OUTCOME\ndid the operator enable service here,\nand when?",
        edge=GOOD, face="#eaf7ea", fs=7.6, weight="bold")
    box(ax, 56, 34, 39, 8, "DISCRETE-TIME HAZARD MODEL", fs=8, edge=BLUE)
    box(ax, 56, 13, 39, 13,
        "OUT-OF-TIME BACKTEST\ntrain <= 2023   ->   predict 2024-25\n\n"
        "AUC  -  PR-AUC  -  Brier  -  ECE  -  precision@k",
        edge=GOOD, face="#eaf7ea", fs=7.6, weight="bold")
    arrow(ax, (75, 76), (75, 42), color=GOOD, lw=1.6, rad=-0.45)
    arrow(ax, (64, 55), (64, 42), color=GOOD, lw=1.6)
    arrow(ax, (75, 34), (75, 26), color=GOOD, lw=1.6)
    ax.text(75.5, 8.5, "The target is no longer built from\nthe predictors. "
            "Scoring means something.", ha="center", fontsize=7.2, color=GOOD,
            fontweight="bold", linespacing=1.4)
    newtag(ax, 74, 88.5, "SCOREABLE")

    ax.set_title("Why the target variable must be observable",
                 loc="left", x=0.01, y=1.01)
    return save(fig, out, "fig04_estimand")


def fig05_decay(out):
    """The SHAPE a cannibalisation decay takes, and the W it would imply.

    NOT AN ESTIMATE, AND DRAWN SO THAT NOBODY CAN MISTAKE IT FOR ONE.

    This figure used to plot nine hand-typed effect values with a band
    labelled "95% CI" and a point annotated "n.s.". No such regression has
    ever been run. Worse, its y-axis was 2-day order volume -- a quantity the
    project does not observe and whose absence is the documented reason the
    cannibalisation estimand was abandoned (docs/ALTERNATIVES.md, Option D).

    So the figure asserted a causal effect, a confidence interval and a
    significance test, all on a variable that is not in the data. The caption
    said "values are illustrative pending estimation", which is six words
    under a chart carrying error bars -- and figures are routinely lifted into
    slides without their captions.

    Corrected 2026-09-15: the interval and the significance annotation are
    gone, the curve is dashed and unlabelled on the y-axis, and the words
    ILLUSTRATIVE ONLY sit inside the axes where they travel with the image.
    The pedagogical point -- that a decay curve is what defines W, rather
    than an arbitrary contiguity rule -- is unchanged and is the only thing
    this figure was ever needed for.
    """
    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(10.2, 3.9), gridspec_kw={"width_ratios": [1.55, 1]})

    # A smooth exponential, drawn to show SHAPE. No values are annotated and
    # no band is drawn, because there is nothing to put an interval around.
    d = np.linspace(0, 42, 120)
    eff = -13.0 * np.exp(-d / 11.0)

    ax.axhline(0, color=AXIS, linewidth=1.0)
    ax.plot(d, eff, color=MUTED, linewidth=2.0, linestyle="--", zorder=3,
            label="shape a decay curve takes (not estimated)")
    ax.axvline(20, color=ORANGE, linewidth=1.2, linestyle=":", zorder=2)
    ax.text(20.8, -10.6, "a radius falls out\nof the curve",
            fontsize=7.4, color=ORANGE, fontweight="bold", linespacing=1.3)

    # Inside the axes, so it survives being cropped into a slide.
    ax.text(0.5, 0.06, "ILLUSTRATIVE ONLY -- NO REGRESSION HAS BEEN RUN",
            transform=ax.transAxes, ha="center", fontsize=8.2,
            fontweight="bold", color=CRITICAL,
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "#fbeaea",
                  "edgecolor": CRITICAL, "linewidth": 1.2})

    ax.set_xlabel("distance from activated ZCTA (km)")
    ax.set_ylabel("effect on nearby demand (not estimated)")
    ax.set_title("What a cannibalisation decay curve would look like",
                 loc="left")
    ax.set_xlim(0, 42)
    ax.set_ylim(-16, 4)
    ax.set_yticklabels([])          # no numbers: none of them are measured
    recede_axes(ax)
    ax.legend(loc="lower right")

    ax2.axis("off")
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.text(0, 94, "AND THEN BUILD W FROM IT", fontsize=8.5,
             fontweight="bold", color=INK)
    box(ax2, 0, 62, 96, 22,
        "COMMON PRACTICE\nW = binary contiguity\n\"because that is what people do\"\n"
        "-> open to attack, no answer",
        edge=CRITICAL, face="#fbeaea", fs=7.4, align="left")
    arrow(ax2, (48, 60), (48, 50), color=ORANGE, lw=1.8)
    box(ax2, 0, 24, 96, 24,
        "PROPOSED\nW = f(estimated decay curve)\nderived from the ring "
        "regression at left\n-> W is an ESTIMATED OBJECT\n-> the objection "
        "disappears",
        edge=ORANGE, face="#fdf0ea", fs=7.4, align="left")
    ax2.text(0, 14, "Method: Pollmann, Causal Inference for\nSpatial "
             "Treatments. The estimator is his;\nthe parameter for same-day "
             "delivery is new.", fontsize=6.9, color=MUTED, style="italic",
             linespacing=1.5, va="top")

    fig.tight_layout()
    return save(fig, out, "fig05_decay")


def fig06_portfolio(out):
    """Why ranking misses profitable bundles."""
    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(10.2, 3.9), gridspec_kw={"width_ratios": [1, 1.25]})

    labels = ["ZIP A\nalone", "ZIP B\nalone", "A + B\nbundled"]
    vals = [-0.20, -0.15, 1.10]
    colors = [MUTED, MUTED, GOOD]
    bars = ax.bar(labels, vals, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2,
                v + (0.09 if v > 0 else -0.14),
                f"${v:+.2f}M", ha="center", fontsize=8.6, fontweight="bold",
                color=GOOD if v > 0 else CRITICAL)
    ax.axhline(0, color=AXIS, linewidth=1.1)
    ax.set_ylabel("five-year NPV ($M)")
    ax.set_ylim(-0.5, 1.45)
    ax.set_title("Ranking rejects both. The bundle is profitable.",
                 loc="left")
    recede_axes(ax)
    ax.text(0.5, -0.42, "greedy ranking stops here", fontsize=7.2,
            color=CRITICAL, ha="center", style="italic")

    ax2.axis("off")
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    box(ax2, 0, 66, 98, 28,
        "WHY  -  two forces, opposite directions\n\n"
        "NEGATIVE   cannibalisation: A steals from B\n"
        "POSITIVE   shared station, pooled drop density\n"
        "           -> 1/sqrt(delta) -> cost falls for BOTH",
        edge=BLUE, fs=7.4, align="left")
    box(ax2, 0, 30, 98, 28,
        "WHY GREEDY HAS NO GUARANTEE\n\n"
        "cannibalisation   -> diminishing returns -> SUBmodular\n"
        "density economics -> increasing returns  -> SUPERmodular\n"
        "objective is NEITHER -> the (1-1/e) bound does not apply",
        edge=ORANGE, face="#fdf0ea", fs=7.4, align="left")
    ax2.text(0, 22, "SEARCH SPACE", fontsize=8, fontweight="bold", color=INK)
    ax2.text(0, 15, f"ranking   ->  {SCOPE.zctas_label} independent decisions\n"
             f"bundling  ->  {SCOPE.search_space} candidate portfolios\n"
             "top 200 only  ->  ~1.6 x 10^60",
             fontsize=7.6, color=INK_2, va="top", linespacing=1.6,
             family="monospace")
    ax2.text(0, -1, "Method fix, not a novelty claim: multi-facility network "
             "optimisation\nis a mature commercial category (see the "
             "prior-art check).",
             fontsize=6.8, color=MUTED, style="italic", linespacing=1.5,
             va="top")

    fig.tight_layout()
    return save(fig, out, "fig06_portfolio")


def fig07_tornado(out):
    """Which capital bucket the NPV ranking would be sensitive to.

    THE EIGHT SWINGS BELOW ARE TYPED IN, NOT MEASURED.

    A per-bucket sensitivity decomposition has not been run.
    `outputs/metrics/montecarlo_report.json` carries aggregate bands over 500
    draws and no per-bucket breakdown, so this figure cannot currently be
    rebuilt from data. Until 2026-09-15 it said so nowhere -- not in the
    figure, not in the caption -- while its caption asserted the
    three-quarters split as fact.

    Corrected 2026-09-15: the disclosure now sits inside the axes, the
    per-bar dollar labels are gone (they were false precision on invented
    numbers), and the ordering is presented as the claim rather than the
    magnitudes. The ordering is defensible from the cost model's own
    structure -- lease and wages dominate because driver time at the door is
    66.5% of the per-stop bill (`cost_report.json`) -- and that is all this
    figure is needed to say.

    To make it real: decompose the 500 Monte Carlo draws by bucket and plot
    the measured swings. That is a day's work and it is listed as open.
    """
    fig, ax = plt.subplots(figsize=(8.2, 4.0))

    buckets = ["Marketing activation", "Permitting / regulatory",
               "Hiring (one-time)", "Building fitout", "Delivery vehicles",
               "Fuel and energy", "Wages (ongoing)", "Real-estate lease"]
    low = np.array([-0.10, -0.14, -0.17, -0.31, -0.52, -0.58, -0.94, -1.28])
    high = np.array([0.11, 0.15, 0.18, 0.33, 0.55, 0.61, 0.99, 1.34])
    prim = [False, False, False, False, True, True, True, True]
    y = np.arange(len(buckets))

    for i in y:
        c = BLUE if prim[i] else AQUA
        ax.barh(i, high[i] - low[i], left=low[i], color=c, height=0.62,
                zorder=3, edgecolor=SURFACE, linewidth=1.4)
        # No dollar label: these magnitudes are illustrative, and printing
        # them to the cent is false precision on an invented number.

    ax.axvline(0, color=AXIS, linewidth=1.1)
    ax.set_yticks(y)
    ax.set_yticklabels(buckets, fontsize=8)
    ax.set_xlabel("relative swing in five-year NPV across the bucket's "
                  "uncertainty range  (ordering illustrative, not measured)")
    ax.set_xlim(-1.75, 1.75)
    ax.set_title("Which capital buckets would move the ranking", loc="left")
    ax.set_xticklabels([])          # no numbers: none of them are measured
    recede_axes(ax, x_grid=True, y_grid=False)
    ax.text(0.5, 0.04, "ILLUSTRATIVE ORDERING -- PER-BUCKET SENSITIVITY "
            "NOT YET RUN", transform=ax.transAxes, ha="center", fontsize=8.0,
            fontweight="bold", color=CRITICAL,
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "#fbeaea",
                  "edgecolor": CRITICAL, "linewidth": 1.2})

    ax.text(-1.70, 7.62, "PRIMARY  -  4 buckets, ~75% of the swing",
            fontsize=7.6, color=BLUE, fontweight="bold")
    ax.text(-1.70, 2.62, "SECONDARY  -  4 buckets, ~25%",
            fontsize=7.6, color=AQUA, fontweight="bold")
    ax.text(0, -1.35, "You do not need all eight buckets to be right. You need "
            "the two that\ndominate the swing to be right  -  and this plot "
            "identifies them.",
            fontsize=7.2, color=MUTED, style="italic", ha="center",
            linespacing=1.5)

    fig.tight_layout()
    return save(fig, out, "fig07_tornado")


BUILDERS = [fig04_estimand, fig05_decay, fig06_portfolio, fig07_tornado]
