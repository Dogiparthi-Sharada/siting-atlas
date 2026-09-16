"""README-width versions of the three results figures.

Why this file exists
--------------------
``fig_paper.py`` draws these results at ``figbase.COL_W`` -- 3.40 inches, one
IEEE column. The README then displayed those same PNGs at full page width,
roughly 2.8x, and an upscaled figure does not degrade gracefully: a 7pt tick
becomes a 20pt tick, the plot area shrinks to a third of the frame, and an
annotation that cleared a marker at column width lands on top of it. Nudging
the column figure cannot fix that, because the fault is the medium.

    fig_paper.py    3.40in,  7-8.5pt  ->  the IEEE paper, printed
    fig_readme.py   9.60in, 8.2-17pt  ->  the README, read on a screen

They share their DATA LOADERS and nothing else. ``fig_paper.auc_data``,
``dispersion_data`` and ``gap_data`` read the artefacts and both modules call
them, so the two media can never disagree about a number. Composition is free
to differ, and does.

Colour, and the rule it follows
-------------------------------
An earlier pass made these three blue, slate and grey. That was legible and
drab, and drab is a real cost on a front page nobody is obliged to read.

The fix was NOT to tint things. Every hue below does a job, and the jobs are
what made the figures colourful:

  * **Red is reserved.** It means money, via ``figbase.COST_STOPS``, and only
    the map and the cost chart may use it. A red "baseline" line beside a red
    cost ramp reads as a cost.
  * **Blue is this project; amber is what it is measured against.** Used that
    way in both the AUC chart and the visibility bar, so the pairing carries
    across the page.
  * **The AUC band is ramped, not filled.** Its colour is how much the model
    lost that year, so the worst year is visibly the darkest -- magnitude
    encoded in a magnitude channel, which a flat grey fill threw away.
  * **The empty dispersion band is violet** because it is a REGION, a
    different kind of object from the points in it, and a grey box reads as
    absence rather than as a finding.
  * Nothing is encoded by colour alone: the AUC lines are dashed vs solid and
    directly labelled, the dispersion rows are named on the y-axis, and every
    bar segment carries its own number.

    python tools/figures/fig_readme.py
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fig_paper as fp  # noqa: E402
import figbase as fb  # noqa: E402
import readmebase as rb  # noqa: E402

ROOT = fp.ROOT
OUT = fp.OUT
W = rb.WIDTH


# --------------------------------------------------------------- 1. AUC

def auc_by_year() -> str:
    """Two lines, and the gap between them ramped by how big it is.

    The column version labelled the lines mid-plot, where "households
    baseline" landed on the 2020 marker. Labelling at the right-hand end is
    the standard fix for a time series: the reader's eye is already going left
    to right, the label is the last thing it meets, and the data has stopped
    so nothing can collide with it.

    The band is the subject. Seven connector segments drew one fact as seven
    objects; one region reads as one fact -- and shading each year's slice by
    that year's loss turns the region into a second, wordless reading of the
    same table the numbers give.
    """
    d, years, model, house = fp.auc_data()
    gaps = [h - m for m, h in zip(model, house, strict=True)]
    lo, hi = min(gaps), max(gaps)
    ramp = fb.amber_ramp()

    fig, ax = fb.figure(W, 5.0)
    with rb.scale():
        low = fb.titles(
            fig,
            "The model loses in every held-out year",
            "Out-of-time AUC for the pre-registered entry model against a "
            "zero-parameter baseline that ranks metros by\nhousehold count "
            "alone. Trained on everything before the held-out year, scored "
            "on that year. Higher is better;\n0.5 is a coin flip. The "
            "specification was hashed and sealed before it was fitted.",
            pad=0.026)
    fig.subplots_adjust(top=low - 0.050, bottom=0.255, left=0.075,
                        right=0.822)

    # One strip per YEAR, half a year either side, shaded by that year's loss.
    #
    # Splitting between years instead would be easier and would be wrong: the
    # number is printed at the year, so the shade under it has to be the same
    # year's. A strip spanning 2019-2020 has to pick one of two losses, and
    # whichever it picks, one of the two printed numbers sits on a shade that
    # contradicts it. Strips are sampled because the band's edges are only
    # defined at the year points and are linear between them.
    xlo, xhi = years[0] - 0.35, years[-1] + 0.12
    for y, gap in zip(years, gaps, strict=True):
        a, b = max(y - 0.5, xlo), min(y + 0.5, xhi)
        xs = np.linspace(a, b, 40)
        t = (gap - lo) / (hi - lo) if hi > lo else 0.5
        ax.fill_between(xs, np.interp(xs, years, model),
                        np.interp(xs, years, house),
                        color=ramp(0.16 + 0.66 * t), zorder=1, linewidth=0)

    ax.plot(years, house, "--o", color=fb.AMBER, lw=2.1, ms=7.0, zorder=3,
            dashes=(5, 2.6), markeredgecolor="white", markeredgewidth=1.4)
    ax.plot(years, model, "-o", color=fb.BLUE, lw=2.4, ms=7.0, zorder=4,
            markeredgecolor="white", markeredgewidth=1.4)

    # How much it lost by, printed in the band it lost by.
    for y, m, h, g in zip(years, model, house, gaps, strict=True):
        ax.text(y, (m + h) / 2, f"{g:.2f}", ha="center", va="center",
                fontsize=9.5, color=fb.AMBER_INK, weight="bold", zorder=5)

    # Direct labels past the last point. `right=0.822` reserves the margin, so
    # these sit outside the axes and cannot touch the data.
    ax.text(years[-1] + 0.14, house[-1],
            "households baseline\n(no parameters)",
            color=fb.AMBER, fontsize=10.0, va="center", ha="left",
            linespacing=1.4, weight="bold")
    ax.text(years[-1] + 0.14, model[-1], "the model\n(pre-registered)",
            color=fb.BLUE, fontsize=10.0, va="center", ha="left",
            linespacing=1.4, weight="bold")

    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=rb.PT_TICK)
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(0.55, 1.02)
    ax.set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylabel("out-of-time AUC", fontsize=rb.PT_LABEL, color=fb.MUTED,
                  labelpad=8)
    ax.set_xlabel("held-out year", fontsize=rb.PT_LABEL, color=fb.MUTED,
                  labelpad=9)
    fb.frame(ax, ygrid=True)
    ax.tick_params(labelsize=rb.PT_TICK)

    rb.foot(fig,
            f"Numbers in the band are the AUC the model gave away that year, "
            f"and the band darkens with them: {lo:.2f} at best "
            f"({years[gaps.index(lo)]}), {hi:.2f} at worst "
            f"({years[gaps.index(hi)]}).\nSeven years, one direction. "
            f"Reported rather than buried because the specification was "
            f"sealed before fitting — its md5 is recorded in the result "
            f"artefact and re-checked\nin CI, so the losing model is "
            f"demonstrably the one that was promised. Run {d['run_id']}.")

    p = os.path.join(OUT, "fig_auc_by_year.png")
    fb.save(fig, p, placed_width=W)
    return p


# -------------------------------------------------------- 2. dispersion

def dispersion_wide() -> str:
    """The screening rule, with the crowded left-hand end unstacked."""
    g, pts = fp.dispersion_data()
    n_lo = sum(1 for cv, _, _ in pts if cv < 0.6)
    n_hi = len(pts) - n_lo
    n_hi_int = sum(1 for cv, it, _ in pts if cv > 1.3 and it)

    fig, ax = fb.figure(W, 4.15)
    with rb.scale():
        low = fb.titles(
            fig,
            "Low variation guarantees failure. High variation guarantees "
            "nothing.",
            f"Each dot is one candidate covariate, placed by how much it "
            f"varies WITHIN a metro and by whether its coefficient\nreached "
            f"the interior of the parameter space or pinned at the boundary. "
            f"{len(pts)} terms, one run.", pad=0.026)
    fig.subplots_adjust(top=low - 0.070, bottom=0.315, left=0.135,
                        right=0.975)

    # The empty band is a finding, so it is drawn as an object rather than as
    # the absence of one. Violet: a third hue for a third kind of thing.
    ax.axvspan(0.6, 1.3, color=fb.VIOLET_TINT, zorder=0)
    for edge in (0.6, 1.3):
        ax.axvline(edge, color=fb.VIOLET, lw=1.0, alpha=0.45, zorder=1)
    ax.text(math.sqrt(0.6 * 1.3), 1.64, "nothing lands here", ha="center",
            va="center", fontsize=9.5, color=fb.VIOLET_INK, weight="bold")

    for level, want in ((1, True), (0, False)):
        rows = [(cv, mixed) for cv, it, mixed in pts if it is want]
        offs = rb.dodge([cv for cv, _ in rows], 0.055)
        col = fb.TEAL if want else fb.AMBER
        for (cv, mixed), off in zip(rows, offs, strict=True):
            ax.plot([cv], [level + off * 0.145], "o", ms=9.0,
                    color="white" if mixed else col, markeredgecolor=col,
                    markeredgewidth=2.0 if mixed else 1.0, zorder=3)

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["pinned at\nthe boundary", "reached the\ninterior"],
                       fontsize=rb.PT_TICK)
    ax.set_ylim(-0.78, 1.95)
    ax.set_xscale("log")
    ax.set_xlim(0.22, 12.0)
    ax.set_xticks([0.3, 0.6, 1.0, 1.3, 3.0, 10.0])
    ax.set_xticklabels(["0.3", "0.6", "1.0", "1.3", "3", "10"],
                       fontsize=rb.PT_TICK)
    ax.set_xlabel("within-metro coefficient of variation   (log scale)",
                  fontsize=rb.PT_LABEL, color=fb.MUTED, labelpad=9)
    fb.frame(ax, xgrid=True)
    ax.tick_params(axis="y", length=0)

    # AFTER fb.frame. frame() ends with tick_params(colors=MUTED), which
    # repaints every tick label -- setting these before it silently produced
    # two grey labels and no link between a row's name and its dots.
    for lab, col in zip(ax.get_yticklabels(), (fb.AMBER_INK, fb.TEAL),
                        strict=True):
        lab.set_color(col)
        lab.set_fontweight("bold")

    rb.foot(fig,
            f"All {n_lo} terms below cv 0.6 pin at the boundary; only "
            f"{n_hi_int} of the {n_hi} above cv 1.3 reach the interior. The "
            f"rule is therefore ONE-SIDED and is stated that way — low\n"
            f"within-metro variation predicts failure, high variation "
            f"predicts nothing — which makes it a cheap screen to run before "
            f"fitting, not a criterion for keeping a covariate.\nHollow: "
            f"interior in one arm and boundary-straddling in another. Points "
            f"are nudged off their row only where they would otherwise "
            f"overlap. Run {g['run_id']}.")

    p = os.path.join(OUT, "fig_dispersion_wide.png")
    fb.save(fig, p, placed_width=W)
    return p


# ---------------------------------------------------- 3. visibility gap

def visibility_gap_wide() -> str:
    """One bar, in the same blue-against-amber as the AUC chart.

    Blue is what the public record HOLDS; amber is what it misses. The column
    version made the missing share pale blue, which read as empty space --
    but 350 unrecorded cities are the finding, not the background, and a
    finding should not be the lightest thing on its own chart.
    """
    c, total, seen, unseen = fp.gap_data()

    fig, ax = fb.figure(W, 2.35)
    with rb.scale():
        low = fb.titles(
            fig,
            f"Federal records see {seen} of {total} cities",
            "US cities where an independent industry census lists an Amazon "
            "delivery station, against those carrying any\nOSHA inspection "
            "record. Two independent lists, counted — a floor on the gap, "
            "not an estimate.", pad=0.026)
    fig.subplots_adjust(top=low - 0.105, bottom=0.235, left=0.0, right=1.0)

    ax.barh([0], [seen], color=fb.BLUE, height=0.5, zorder=3)
    ax.barh([0], [unseen], left=[seen], color=fb.AMBER_TINT, height=0.5,
            zorder=3)
    ax.barh([0], [unseen], left=[seen], height=0.5, zorder=4,
            facecolor="none", edgecolor=fb.AMBER, linewidth=1.6)
    ax.text(seen / 2, 0, f"{seen}", ha="center", va="center", color="white",
            fontsize=17, weight="bold", zorder=5)
    ax.text(seen + unseen / 2, 0, f"{unseen}", ha="center", va="center",
            color=fb.AMBER_INK, fontsize=17, weight="bold", zorder=5)
    ax.text(seen / 2, -0.38, f"in OSHA records   {seen / total:.0%}",
            ha="center", va="top", color=fb.BLUE, fontsize=rb.PT_TICK,
            weight="bold")
    ax.text(seen + unseen / 2, -0.38,
            f"invisible to the public record   {unseen / total:.0%}",
            ha="center", va="top", color=fb.AMBER_INK, fontsize=rb.PT_TICK,
            weight="bold")

    ax.set_xlim(0, total)
    ax.set_ylim(-0.66, 0.38)
    ax.axis("off")

    p = os.path.join(OUT, "fig_visibility_gap_wide.png")
    fb.save(fig, p, placed_width=W)
    return p


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for fn in (auc_by_year, dispersion_wide, visibility_gap_wide):
        p = fn()
        print(f"  wrote {os.path.relpath(p, ROOT)}  "
              f"({os.path.getsize(p) / 1024:.0f} KB)")
    print("  geometry gate: clean (fb.save raises otherwise)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
