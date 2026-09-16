"""README-width versions of the three results figures.

Why this file exists
--------------------
``fig_paper.py`` draws these results at ``figbase.COL_W`` -- 3.40 inches, one
IEEE column. The README then displayed those same PNGs at full page width,
which is roughly 2.8x, and an upscaled figure does not degrade gracefully: a
7pt tick label becomes a 20pt tick label, a 1.4pt line becomes a slab, the
plot area shrinks to a third of the frame, and an annotation that cleared a
marker by two points at column width sits on top of it. That is what "looks
like someone zoomed to 200% and the text is bleeding" means, and no amount of
nudging the column figure fixes it, because the fault is the medium.

So the two are kept apart, on purpose:

    fig_paper.py    3.40in, 7-8.5pt type   ->  the IEEE paper, printed
    fig_readme.py   9.60in, 9.5-17pt type  ->  the README, read on a screen

They share their DATA LOADERS and nothing else. ``fig_paper.auc_data``,
``dispersion_data`` and ``gap_data`` read the artefacts; both modules call
them, so the two media can never disagree about a number. The composition is
free to differ, and does -- the wide versions spend their extra inches on
direct labels at the line ends, per-year gap values, dodged points and full
four-digit years, none of which fit a column.

Colour
------
Red means money in this repository -- see ``figbase.COST_STOPS``. None of
these three figures is about money, so none of them is red. The previous
versions used ``figbase.WARM`` for "households baseline" and for "at the
boundary", which put a red mark next to a cost ramp and invited exactly the
wrong reading.

  * The baseline is a REFERENCE, not a rival series, so it is slate and
    dashed. Lightness and dash pattern both separate it from the model, so it
    survives greyscale and colour-vision deficiency.
  * Interior / at-the-boundary is a two-state outcome, so it takes a green
    and a slate -- and the y-axis names both states, so nothing is encoded in
    colour alone.

    python tools/figures/fig_readme.py
"""

from __future__ import annotations

import contextlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fig_paper as fp  # noqa: E402
import figbase as fb  # noqa: E402

ROOT = fp.ROOT
OUT = fp.OUT

WIDTH = 9.6

MODEL = "#1f4e79"    # the fitted model
BENCH = "#78889a"    # the zero-parameter benchmark: a reference, not a rival
BAND = "#e2e9ef"     # the gap between them
GOOD = "#1f6f4f"     # a term that reached the interior of the parameter space
POOR = "#93a0ac"     # a term pinned at the boundary
SEEN = "#1f4e79"
HIDDEN = "#ccd8e4"


@contextlib.contextmanager
def _scale(title, sub):
    """figbase's point sizes are set for an IEEE column; this is a README."""
    old = (fb.PT_TITLE, fb.PT_SUB)
    fb.PT_TITLE, fb.PT_SUB = title, sub
    try:
        yield
    finally:
        fb.PT_TITLE, fb.PT_SUB = old


def _foot(fig, text):
    fig.text(0.0, 0.006, text, fontsize=8.2, color=fb.MUTED, va="bottom",
             ha="left", linespacing=1.6)


# --------------------------------------------------------------- 1. AUC

def auc_by_year() -> str:
    """Two lines and the gap between them, named at the right-hand end.

    The old column version labelled the lines in the middle of the plot,
    where "households baseline" landed on the 2020 marker. Labelling at the
    right end instead is the standard fix for a time series: the reader's eye
    is already travelling left to right, the label is the last thing it
    reaches, and nothing can collide with it because the data stops there.

    The filled band is the figure's actual subject. Seven separate connector
    segments drew the same thing as seven objects; one region reads as one
    fact, and the number printed inside each year is how much the model lost
    by -- which the column version had no room to state at all.
    """
    d, years, model, house = fp.auc_data()
    gaps = [h - m for m, h in zip(model, house, strict=True)]

    fig, ax = fb.figure(WIDTH, 5.0)
    with _scale(16.5, 10.0):
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
                        right=0.845)

    ax.fill_between(years, model, house, color=BAND, zorder=1)
    ax.plot(years, house, "--o", color=BENCH, lw=2.0, ms=7.0, zorder=3,
            dashes=(5, 2.6), markeredgecolor="white", markeredgewidth=1.4)
    ax.plot(years, model, "-o", color=MODEL, lw=2.2, ms=7.0, zorder=4,
            markeredgecolor="white", markeredgewidth=1.4)

    # How much it lost by, printed in the band it lost by.
    for y, m, h, g in zip(years, model, house, gaps, strict=True):
        ax.text(y, (m + h) / 2, f"{g:.2f}", ha="center", va="center",
                fontsize=9.0, color="#4a5b6b", zorder=5)

    # Direct labels past the last point. `right=0.845` above reserves the
    # margin, so these sit outside the axes and cannot touch the data.
    ax.text(years[-1] + 0.14, house[-1],
            "households baseline\n(no parameters)",
            color=BENCH, fontsize=10.0, va="center", ha="left",
            linespacing=1.4)
    ax.text(years[-1] + 0.14, model[-1], "the model\n(pre-registered)",
            color=MODEL, fontsize=10.0, va="center", ha="left",
            linespacing=1.4, weight="bold")

    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=10.0)
    ax.set_xlim(years[0] - 0.35, years[-1] + 0.12)
    ax.set_ylim(0.55, 1.02)
    ax.set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylabel("out-of-time AUC", fontsize=10.5, color=fb.MUTED,
                  labelpad=8)
    ax.set_xlabel("held-out year", fontsize=10.5, color=fb.MUTED, labelpad=9)
    fb.frame(ax, ygrid=True)
    ax.tick_params(labelsize=10.0)

    worst = years[gaps.index(max(gaps))]
    best = years[gaps.index(min(gaps))]
    _foot(fig,
          f"Numbers in the band are the AUC the model gave away that year: "
          f"{min(gaps):.2f} at best ({best}), {max(gaps):.2f} at worst "
          f"({worst}). Seven years, one direction.\nReported rather than "
          f"buried because the specification was sealed before fitting — its "
          f"md5 is recorded in the result artefact and re-checked in CI, so "
          f"the losing\nmodel is demonstrably the one that was promised. "
          f"Run {d['run_id']}.")

    p = os.path.join(OUT, "fig_auc_by_year.png")
    fb.save(fig, p, placed_width=WIDTH)
    return p


# -------------------------------------------------------- 2. dispersion

def _dodge(xs, min_sep: float):
    """Row offsets that keep near-coincident points apart, deterministically.

    No random jitter. A figure in this repository must rebuild identically
    from the same artefact, and `np.random` without a seed breaks that; a
    seed would fix it but still moves every point for a reason the reader
    cannot see. This walks the points in order and pushes one down only when
    it would otherwise sit on its neighbour, so a point moves if and only if
    it has to. ``min_sep`` is measured in log10 units, the axis the points
    are actually drawn on.
    """
    lanes: list[float] = []          # last x placed in each lane
    out = []
    for x in xs:
        for i, last in enumerate(lanes):
            if math.log10(x) - math.log10(last) >= min_sep:
                lanes[i] = x
                out.append(i)
                break
        else:
            lanes.append(x)
            out.append(len(lanes) - 1)
    # 0, +1, -1, +2, -2 ... so the first lane stays on the row's own line.
    return [(0 if i == 0 else (1 if i % 2 else -1) * ((i + 1) // 2))
            for i in out]


def dispersion_wide() -> str:
    """The screening rule, with the crowded left-hand end unstacked."""
    g, pts = fp.dispersion_data()
    n_lo = sum(1 for cv, _, _ in pts if cv < 0.6)
    n_hi = len(pts) - n_lo
    n_hi_int = sum(1 for cv, it, _ in pts if cv > 1.3 and it)

    fig, ax = fb.figure(WIDTH, 4.15)
    with _scale(16.5, 10.0):
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

    ax.axvspan(0.6, 1.3, color="#f1f3f5", zorder=0)
    ax.text(math.sqrt(0.6 * 1.3), 1.62, "nothing lands here",
            ha="center", va="center", fontsize=9.0, color="#98a2ac")

    for level, want in ((1, True), (0, False)):
        rows = [(cv, mixed) for cv, it, mixed in pts if it is want]
        offs = _dodge([cv for cv, _ in rows], 0.055)
        col = GOOD if want else POOR
        for (cv, mixed), off in zip(rows, offs, strict=True):
            ax.plot([cv], [level + off * 0.145], "o", ms=8.5,
                    color="white" if mixed else col,
                    markeredgecolor=col, markeredgewidth=1.6 if mixed else 0.9,
                    zorder=3)

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["pinned at\nthe boundary", "reached the\ninterior"],
                       fontsize=10.0, color=fb.INK)
    ax.set_ylim(-0.78, 1.95)
    ax.set_xscale("log")
    ax.set_xlim(0.22, 12.0)
    ax.set_xticks([0.3, 0.6, 1.0, 1.3, 3.0, 10.0])
    ax.set_xticklabels(["0.3", "0.6", "1.0", "1.3", "3", "10"], fontsize=10.0)
    ax.set_xlabel("within-metro coefficient of variation   (log scale)",
                  fontsize=10.5, color=fb.MUTED, labelpad=9)
    fb.frame(ax, xgrid=True)
    ax.tick_params(axis="y", length=0)

    _foot(fig,
          f"All {n_lo} terms below cv 0.6 pin at the boundary; only "
          f"{n_hi_int} of the {n_hi} above cv 1.3 reach the interior. The "
          f"rule is therefore ONE-SIDED and is stated that way — low\n"
          f"within-metro variation predicts failure, high variation predicts "
          f"nothing — which makes it a cheap screen to run before fitting, "
          f"not a criterion for keeping a covariate.\nHollow: interior in one "
          f"arm and boundary-straddling in another. Points are nudged off "
          f"their row only where they would otherwise overlap. "
          f"Run {g['run_id']}.")

    p = os.path.join(OUT, "fig_dispersion_wide.png")
    fb.save(fig, p, placed_width=WIDTH)
    return p


# ---------------------------------------------------- 3. visibility gap

def visibility_gap_wide() -> str:
    """One bar. The column version reserved a third of its canvas for
    nothing, which at README width became a third of a screen of nothing."""
    c, total, seen, unseen = fp.gap_data()

    fig, ax = fb.figure(WIDTH, 2.35)
    with _scale(16.5, 10.0):
        low = fb.titles(
            fig,
            f"Federal records see {seen} of {total} cities",
            "US cities where an independent industry census lists an Amazon "
            "delivery station, against those carrying any\nOSHA inspection "
            "record. Two independent lists, counted — a floor on the gap, "
            "not an estimate.", pad=0.026)
    fig.subplots_adjust(top=low - 0.105, bottom=0.235, left=0.0, right=1.0)

    ax.barh([0], [seen], color=SEEN, height=0.5, zorder=3)
    ax.barh([0], [unseen], left=[seen], color=HIDDEN, height=0.5, zorder=3)
    ax.text(seen / 2, 0, f"{seen}", ha="center", va="center", color="white",
            fontsize=17, weight="bold", zorder=4)
    ax.text(seen + unseen / 2, 0, f"{unseen}", ha="center", va="center",
            color=fb.INK, fontsize=17, weight="bold", zorder=4)
    ax.text(seen / 2, -0.38, f"in OSHA records   {seen / total:.0%}",
            ha="center", va="top", color=fb.MUTED, fontsize=10.0)
    ax.text(seen + unseen / 2, -0.38,
            f"invisible to the public record   {unseen / total:.0%}",
            ha="center", va="top", color=fb.MUTED, fontsize=10.0)

    ax.set_xlim(0, total)
    ax.set_ylim(-0.66, 0.38)
    ax.axis("off")

    p = os.path.join(OUT, "fig_visibility_gap_wide.png")
    fb.save(fig, p, placed_width=WIDTH)
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
