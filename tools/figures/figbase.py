"""Shared layout and a geometry gate for print figures.

Two faults kept recurring and neither is caught by looking at a PNG on screen:

1. **Silent downscaling.** A figure drawn 6.4 inches wide and placed in a
   3.3-inch IEEE column is shown at 52%, so its 8.6pt labels reach the page at
   4.5pt. On a monitor it looks fine. In print it is unreadable. The fix is to
   draw at the width the figure will actually occupy and never rely on the
   document to shrink it.

2. **Guessed text positions.** Placing a title at y=0.985 and a subtitle at
   y=0.915 works until the title wraps to two lines, at which point they
   overlap. Positions have to be *measured* from the rendered text, not
   assumed.

:func:`save` refuses to write a figure that fails either check, so a broken
layout cannot reach the repository by being overlooked.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# IEEE conference: 8.5in page, 0.625in margins, 0.25in gutter.
#   single column = (8.5 - 1.25 - 0.25) / 2 = 3.50in
# Draw marginally under that so a hairline rounding error cannot overflow.
COL_W = 3.40
FULL_W = 7.00          # spans both columns, for a \figure* environment
DPI = 400

# At 1:1 these are the sizes that reach the page. IEEE wants >= 8pt in
# figures; 7pt is the hard floor used by the checker for tick labels.
PT_TITLE = 8.5
PT_SUB = 7.0
PT_LABEL = 7.5
PT_TICK = 7.0
PT_ANNOT = 7.0
MIN_PT = 6.5

INK = "#1a1a1a"
MUTED = "#5f5f5f"
HUE = "#1f4e79"
WARM = "#b3452f"
FAINT = "#c3d3e2"
GRID = "#e9e9e9"

# ------------------------------------------------------- money is red
#
# One rule, enforced by one object: anything encoding dollars uses this ramp,
# and every figure imports it rather than keeping a copy. Two figures with
# their own near-identical red drift apart the first time one is edited, and
# a reader who has learned "dark = dear" on the map then mis-reads the chart
# below it.
#
# Light to dark in a single hue. Monotonic in LIGHTNESS, which is the property
# that makes it survive greyscale printing and red-green colour deficiency --
# a darker mark is dearer whether or not the hue is visible. Red rather than
# the repository's blue because cost is the one quantity a reader already has
# a convention for: dark red reads as expensive before the legend is found.
COST_STOPS = ["#fde4dd", "#f4a58c", "#d94f36", "#8c1d0c"]

#: Where on the ramp the cheapest mark sits. Not 0.0: #fde4dd is a whisper on
#: white, so a small marker at the ramp's floor disappears. Bubbles on the map
#: are large enough to survive it; a 7pt dot in a chart is not, so callers
#: drawing small marks pass this floor to :func:`cost_color`.
COST_FLOOR = 0.34

#: The recessive companion for a range/IQR bar behind a cost mark. Warm enough
#: to belong to the red family, desaturated enough that it never competes with
#: the mark it is carrying.
COST_TRACK = "#efdcd6"

#: The ramp's dark end, for rules and emphasis text about cost.
COST_DEEP = "#8c1d0c"


def cost_cmap():
    """The shared red ramp. Built on demand to keep import side effects out."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("cost", COST_STOPS)


def cost_color(value, lo, hi, *, floor: float = COST_FLOOR):
    """Colour for one dollar value, compressed into ``[floor, 1]``.

    ``lo``/``hi`` are the ends of the range being shown, so the ramp always
    spans the data actually drawn rather than some absolute dollar scale.
    A degenerate range (one row, or every value equal) maps to the midpoint
    instead of dividing by zero.
    """
    span = hi - lo
    t = 0.5 if span <= 0 else (value - lo) / span
    return cost_cmap()(floor + (1.0 - floor) * min(max(t, 0.0), 1.0))


def figure(width: float = COL_W, height: float = 2.4):
    fig, ax = plt.subplots(figsize=(width, height), dpi=DPI)
    return fig, ax


def frame(ax, *, xgrid=False, ygrid=False) -> None:
    if xgrid or ygrid:
        ax.grid(axis="x" if xgrid else "y", color=GRID, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#d4d4d4")
        ax.spines[s].set_linewidth(0.7)
    ax.tick_params(colors=MUTED, labelsize=PT_TICK, length=0)


def titles(fig, title: str, subtitle: str = "", *, pad=0.035):
    """Place title, then measure it and hang the subtitle beneath.

    Returns the y of the lowest text drawn, in figure coordinates, so the
    caller can reserve space for it.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    h_px = fig.bbox.height

    t = fig.text(0.0, 1.0, title, fontsize=PT_TITLE, color=INK,
                 va="top", ha="left", weight="bold", linespacing=1.3)
    low = t.get_window_extent(r).y0 / h_px
    if subtitle:
        s = fig.text(0.0, low - pad, subtitle, fontsize=PT_SUB, color=MUTED,
                     va="top", ha="left", linespacing=1.45)
        low = s.get_window_extent(r).y0 / h_px
    return low


def _texts(fig):
    """Text artists that are actually drawn.

    Matplotlib keeps label artists for ticks outside the view limits and for
    axes switched off with ``axis("off")``. They report positions far off the
    canvas but never render, so counting them produced a page of phantom
    failures on the first run of this checker.
    """
    out = list(fig.texts)
    for ax in fig.axes:
        out += list(ax.texts)
        if ax.get_legend():
            out += ax.get_legend().get_texts()
        if not ax.axison:
            continue
        out += [ax.title, ax.xaxis.label, ax.yaxis.label]
        xlo, xhi = sorted(ax.get_xlim())
        for t in ax.get_xticklabels():
            if xlo - 1e-9 <= t.get_position()[0] <= xhi + 1e-9:
                out.append(t)
        ylo, yhi = sorted(ax.get_ylim())
        for t in ax.get_yticklabels():
            if ylo - 1e-9 <= t.get_position()[1] <= yhi + 1e-9:
                out.append(t)
    return [t for t in out if t.get_text().strip() and t.get_visible()]


def check(fig, *, placed_width: float | None = None) -> list[str]:
    """Report geometry faults. Empty list means the figure is sound."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    w_px, h_px = fig.bbox.width, fig.bbox.height
    problems: list[str] = []

    drawn_w = fig.get_size_inches()[0]
    scale = (placed_width / drawn_w) if placed_width else 1.0
    if scale < 0.95:
        problems.append(
            f"will be downscaled to {scale:.0%} "
            f"(drawn {drawn_w:.2f}in, placed {placed_width:.2f}in)")

    items = []
    for t in _texts(fig):
        try:
            bb = t.get_window_extent(r)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        items.append((t, bb))
        eff = t.get_fontsize() * scale
        if eff < MIN_PT:
            problems.append(
                f"text {t.get_text()[:28]!r} reaches the page at "
                f"{eff:.1f}pt (floor {MIN_PT})")
        # Only a PARTIAL crossing is a fault. savefig(bbox_inches="tight")
        # grows the canvas to enclose whatever sits just beyond it, so fully
        # outside is either harmless or an artefact we already filtered.
        inside = (min(bb.x1, w_px) - max(bb.x0, 0) > 0
                  and min(bb.y1, h_px) - max(bb.y0, 0) > 0)
        crosses = (bb.x0 < -1 or bb.y0 < -1
                   or bb.x1 > w_px + 1 or bb.y1 > h_px + 1)
        if inside and crosses:
            problems.append(f"text {t.get_text()[:28]!r} crosses the edge")

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 2 and oy > 2:
                area = ox * oy
                smaller = min(a.width * a.height, b.width * b.height)
                if smaller and area / smaller > 0.18:
                    problems.append(
                        f"overlap: {items[i][0].get_text()[:22]!r} and "
                        f"{items[j][0].get_text()[:22]!r}")
    return problems


def save(fig, path: str, *, placed_width: float | None = None,
         strict: bool = True) -> list[str]:
    """Run the geometry gate, then write. Raises if strict and it fails."""
    problems = check(fig, placed_width=placed_width)
    if problems and strict:
        plt.close(fig)
        raise ValueError(
            "geometry check failed for {}:\n    {}".format(
                os.path.basename(path), "\n    ".join(problems)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=DPI)
    plt.close(fig)
    return problems
