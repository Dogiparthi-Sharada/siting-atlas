"""Figures 8 and 9: the measured backtest, and the conformal coverage check.

These are the only two figures in the proposal set whose numbers are results.
Every value drawn here is read from ``outputs/metrics/hazard_report.json`` via
``tools/hazard_metrics.py``; nothing is typed. The previous versions of both
figures were hand-typed illustrations -- fig08 printed a target AUC of 0.84
under an ROC curve synthesised to have that area, and fig09 invented eight ZIP
codes and their rank-stability shares. The backtest has since run and the
model failed, so the figures now show the failure, which is the finding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hazard_metrics import HAZARD                              # noqa: E402

from common import (AXIS, BLUE, GRID, INK, INK_2, MUTED,  # noqa: E402
                    ORANGE, SEQ, recede_axes, save)

MODEL_LABEL = "cloglog discrete-time hazard"
NULL_LABEL = "null model: one constant, the base rate"


def _footer(fig, lines, y=-0.055, gap=0.052):
    """Source stamp and reading notes, left-aligned under the panels."""
    for i, line in enumerate(lines):
        fig.text(0.006, y - i * gap, line, fontsize=6.9, color=MUTED,
                 style="italic", linespacing=1.4)


def _panel_auc(ax):
    """Discrimination against its own null, which is exactly 0.5."""
    rows = [("held out\nby TIME", HAZARD.t_auc),
            ("held out\nby UNIT", HAZARD.auc)]
    y = np.arange(len(rows))
    null = HAZARD.null_auc

    ax.barh(y, [v - null for _, v in rows], left=null, height=0.30,
            color=BLUE, zorder=3)
    ax.axvline(null, color=ORANGE, linestyle="--", linewidth=1.4, zorder=4)
    for yi, (_, v) in zip(y, rows):
        ax.text(v + 0.007, yi, f"{v:.4f}", va="center", fontsize=8.0,
                fontweight="bold", color=INK)
    ax.text(null - 0.007, len(rows) - 0.75, f"{null:.3f}", ha="right",
            va="center", fontsize=7.6, fontweight="bold", color=ORANGE)

    ax.set_yticks(y)
    ax.set_yticklabels([lab for lab, _ in rows], fontsize=7.8)
    ax.set_xlim(0.455, 0.775)
    ax.set_xticks([0.5, 0.6, 0.7])
    ax.set_ylim(-0.55, len(rows) - 0.45)
    ax.set_xlabel("AUC  (higher is better)")
    ax.set_title("A.  Ranking", loc="left", fontsize=9.5)
    recede_axes(ax, x_grid=True, y_grid=False)


def _panel_brier(ax):
    """The proper score, model against the constant, on the same rows."""
    rows = [("held out\nby TIME", HAZARD.t_brier, HAZARD.t_null_brier),
            ("held out\nby UNIT", HAZARD.brier, HAZARD.null_brier)]
    y = np.arange(len(rows))

    for yi, (_, model, null) in zip(y, rows):
        ax.plot([model, null], [yi, yi], color=AXIS, linewidth=1.6, zorder=2)
        ax.plot([null], [yi], marker="D", markersize=7, color=ORANGE,
                zorder=3)
        ax.plot([model], [yi], marker="o", markersize=8, color=BLUE, zorder=4)
        lo_is_model = model < null
        ax.text(model + (-1 if lo_is_model else 1) * 0.00005, yi - 0.20,
                f"{model:.6f}", ha="right" if lo_is_model else "left",
                va="top", fontsize=7.6, fontweight="bold", color=INK)
        ax.text(null + (1 if lo_is_model else -1) * 0.00005, yi + 0.20,
                f"{null:.6f}", ha="left" if lo_is_model else "right",
                va="bottom", fontsize=7.6, color=INK_2)

    ax.annotate("model worse\nthan the constant",
                xy=(rows[0][1], 0.22), xytext=(0.019780, 0.86),
                fontsize=7.2, color=INK_2, linespacing=1.35,
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0,
                                shrinkA=2, shrinkB=4,
                                connectionstyle="arc3,rad=-0.2"))

    ax.set_yticks(y)
    ax.set_yticklabels([lab for lab, _, _ in rows], fontsize=7.8)
    ax.set_xlim(0.01928, 0.02092)
    ax.set_xticks([0.0194, 0.0198, 0.0202, 0.0206])
    ax.set_ylim(-0.70, len(rows) + 0.20)
    ax.set_xlabel("Brier score  (lower is better)")
    ax.set_title("B.  Forecast quality", loc="left", fontsize=9.5)
    recede_axes(ax, x_grid=True, y_grid=False)


def _panel_calibration(ax):
    """Ten equal-count bins against the 45-degree line, plus the constant."""
    bins = HAZARD.calibration
    pred = np.array([b["mean_predicted"] for b in bins]) * 100
    obs = np.array([b["mean_observed"] for b in bins]) * 100
    np_, no_ = (v * 100 for v in HAZARD.null_point)
    top = 5.0

    ax.plot([0, top], [0, top], color=AXIS, linestyle="--", linewidth=1.1,
            zorder=1)
    ax.text(0.72, 0.30, "perfect", fontsize=6.8, color=MUTED, rotation=40,
            ha="center", va="center")
    ax.plot(pred, obs, color=BLUE, marker="o", markersize=4.6,
            markeredgecolor="#ffffff", markeredgewidth=0.7, zorder=3)
    ax.plot([np_], [no_], marker="D", markersize=7.5, color=ORANGE,
            markeredgecolor="#ffffff", markeredgewidth=0.8, zorder=4)

    ax.text(4.90, 0.12,
            f"error vs perfect\n"
            f"  model  {HAZARD.ece:.5f}\n"
            f"  null   {HAZARD.null_ece:.5f}",
            fontsize=7.2, family="monospace", color=INK, va="bottom",
            ha="right", linespacing=1.6)

    ax.set_xlim(0, top)
    ax.set_ylim(0, top)
    ax.set_xlabel("predicted probability, % per quarter")
    ax.set_ylabel("observed frequency, %")
    ax.set_title("C.  Calibration, unit-clustered hold-out", loc="left",
                 fontsize=9.5)
    recede_axes(ax, x_grid=True)


def fig08_backtest(out):
    """The measured out-of-sample result, against a constant, three ways."""
    fig = plt.figure(figsize=(10.8, 4.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.12, 1.0], wspace=0.42)
    _panel_auc(fig.add_subplot(gs[0]))
    _panel_brier(fig.add_subplot(gs[1]))
    _panel_calibration(fig.add_subplot(gs[2]))

    fig.suptitle("Backtest, measured  -  the model ranks a little better "
                 "than chance and forecasts no better than a constant",
                 x=0.006, y=1.065, ha="left", fontsize=10.6,
                 fontweight="bold")
    handles = [plt.Line2D([], [], color=BLUE, marker="o", markersize=7,
                          linewidth=2.0, label=MODEL_LABEL),
               plt.Line2D([], [], color=ORANGE, marker="D", markersize=6.5,
                          linewidth=1.6, linestyle="--", label=NULL_LABEL)]
    fig.legend(handles=handles, loc="upper left", ncol=2,
               bbox_to_anchor=(0.006, 1.018), fontsize=8.2,
               handletextpad=0.5, columnspacing=2.2)

    _footer(fig, [
        HAZARD.stamp,
        f"Primary hold-out: {HAZARD.n_rows:,} ZCTA-quarters, "
        f"{HAZARD.n_events} events, base rate {HAZARD.base_rate * 100:.2f}%, "
        f"whole units held out.  Temporal hold-out (secondary): "
        f"{HAZARD.t_n_rows:,} rows, {HAZARD.t_n_events} events.",
        "Both Brier scores in a row are over the same rows. The raw pair is "
        "reported rather than a skill score: Gneiting & Raftery (2007) "
        "section 2.3 p.362, skill scores are generally improper.",
    ])
    return save(fig, out, "fig08_backtest")


def _panel_coverage(ax):
    """One measured coverage figure inside the band clustering implies."""
    nom = HAZARD.nominal_coverage * 100
    tol = HAZARD.coverage_tolerance * 100
    emp = HAZARD.empirical_coverage * 100

    ax.add_patch(plt.Rectangle((nom - tol, -0.20), 2 * tol, 0.40,
                               facecolor=SEQ[0], edgecolor=GRID,
                               linewidth=0.8, zorder=1))
    ax.plot([nom, nom], [-0.27, 0.27], color=ORANGE, linestyle="--",
            linewidth=1.6, zorder=3)
    ax.plot([emp], [0], marker="o", markersize=11, color=BLUE, zorder=4,
            markeredgecolor="#ffffff", markeredgewidth=1.0)

    ax.text(nom, 0.34, f"asked for {nom:.0f}%", ha="center", va="bottom",
            fontsize=8.0, fontweight="bold", color=ORANGE)
    ax.text(emp - 0.45, 0, f"measured\n{emp:.2f}%", ha="right", va="center",
            fontsize=8.2, fontweight="bold", color=BLUE, linespacing=1.4)
    ax.text(nom, -0.36, f"two-sigma band, +/- {tol:.1f} pp",
            ha="center", va="top", fontsize=7.2, color=INK_2)

    ax.set_xlim(nom - 2.0 * tol, nom + 1.5 * tol)
    ax.set_ylim(-0.80, 0.75)
    ax.set_yticks([])
    ax.set_xticks([86, 88, 90, 92, 94])
    ax.set_xticklabels(["86%", "88%", "90%", "92%", "94%"])
    ax.set_xlabel("share of test rows whose prediction set held the truth")
    ax.set_title("A.  Coverage held", loc="left", fontsize=9.5)
    recede_axes(ax, x_grid=True, y_grid=False)
    ax.spines["left"].set_visible(False)


def _panel_sets(ax):
    """What the sets actually contain, which is where the cost shows up."""
    rows = [("both labels\n(no information)", HAZARD.share_full),
            ("EMPTY\n(refuses to answer)", HAZARD.share_empty),
            ("one label\n(an actual answer)", HAZARD.share_singleton)]
    y = np.arange(len(rows))
    ax.barh(y, [v * 100 for _, v in rows], height=0.52, color=BLUE, zorder=3)
    for yi, (_, v) in zip(y, rows):
        ax.text(v * 100 + 1.6, yi, f"{v * 100:.2f}%", va="center",
                fontsize=8.2, fontweight="bold", color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([lab for lab, _ in rows], fontsize=7.6)
    ax.set_xlim(0, 108)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("share of prediction sets, %")
    ax.set_title("B.  What the sets contain", loc="left", fontsize=9.5)
    recede_axes(ax, x_grid=True, y_grid=False)


def fig09_conformal_coverage(out):
    """The one guarantee that survives the model failing, and what it cost."""
    fig = plt.figure(figsize=(9.2, 3.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.12], wspace=0.30)
    _panel_coverage(fig.add_subplot(gs[0]))
    _panel_sets(fig.add_subplot(gs[1]))

    fig.suptitle("Split conformal prediction  -  the coverage guarantee does "
                 "not need the model to be right",
                 x=0.006, y=1.055, ha="left", fontsize=10.6,
                 fontweight="bold")
    _footer(fig, [
        HAZARD.stamp,
        f"{HAZARD.n_conformal_test:,} test rows, but only "
        f"{HAZARD.n_effective} independent units: whole units go to "
        f"calibration or to test, so the calibration sample is clustered and "
        f"a single split is a noisy estimate of coverage. The band in panel A "
        f"is that two-sigma spread, not a confidence interval.",
        "Panel B is the price. At a 2% base rate the procedure answers "
        "\"neither label\" on a tenth of rows -- honest, and useless for "
        "ranking. Top-K rank stability over Monte Carlo draws is specified "
        "in section 5.6 of the proposal and has not been run; it is not "
        "shown here.",
    ], y=-0.075, gap=0.062)
    return save(fig, out, "fig09_conformal_coverage")


BUILDERS = [fig08_backtest, fig09_conformal_coverage]
