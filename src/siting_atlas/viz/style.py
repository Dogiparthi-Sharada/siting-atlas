"""L5 — style tokens and text-fitting shared by every result figure.

Two unrelated defects are prevented here, which is why both halves live in
one module: every figure needs both, and neither is worth importing twice.

Colour
------
The palette is the validated default from the dataviz reference instance,
re-checked against THIS repo's surface (white — result PNGs are embedded in
the proposal and printed):

    node validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light \
        --surface "#ffffff" --pairs all
    -> all-pairs CVD dE 9.2 PASS, normal-vision dE 24.0 PASS

Only three categorical slots are exposed for all-pairs forms. That is a
finding, not a preference: in a scatter every series can sit beside every
other, and with all pairs in play no eight-hue set clears the colour-vision
floor. A ten-metro scatter coloured by metro is therefore unreadable to a
colour-blind reader *by construction*, however carefully the hues are picked.
So metro identity in this package is carried by POSITION (an ordered strip,
one bar per metro) and by direct labels; hue is spent on at most three
highlighted metros. STACK_SLOTS may use four because a stacked bar only ever
needs adjacent segments to separate, and the adjacent gate passes at four.

Text
----
The fitting machinery is the one proven in tools/figures/common.py. Result
figures are worse than the proposal diagrams in one specific way: their
labels are generated — metro names and dollar amounts that change whenever
the cost model is re-run — so a label that fits today silently overflows
tomorrow. audit_overflow() turns that into a logged failure instead.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import NamedTuple

import matplotlib

matplotlib.use("Agg")  # noqa: E402  - must precede pyplot; figures render
# headless in CI and inside a Streamlit worker thread, where an interactive
# backend either raises or leaks a window that never closes.

import matplotlib.pyplot as plt  # noqa: E402

from ..common import paths  # noqa: E402
from ..common.logging_setup import get_logger  # noqa: E402
from ..common.trace import artefact  # noqa: E402

_log = get_logger("viz.style")

# --- categorical slots (fixed order, never cycled) -------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"

HUE_SLOTS = (BLUE, ORANGE, AQUA)
STACK_SLOTS = (BLUE, ORANGE, AQUA, YELLOW)

# --- status (reserved; never reused as a series) ---------------------------
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"

# --- ink and chrome --------------------------------------------------------
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"
CLOUD = "#9ec5f4"   # sequential step 200: the un-highlighted point cloud

FONT = ["DejaVu Sans"]
DPI = 190


def apply_style() -> None:
    """Global rcParams. Idempotent; every chart function calls it."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": FONT,
        "font.size": 9,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titlesize": 11.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 2.0,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.20,
    })


def recede_axes(ax, *, x_grid: bool = False, y_grid: bool = True) -> None:
    """Drop the top/right spines and push the grid behind the marks."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.set_axisbelow(True)
    ax.yaxis.grid(y_grid)
    ax.xaxis.grid(x_grid)


def empty_figure(message: str, *, size=(8.0, 4.4)):
    """A legible placeholder for an empty selection.

    Every chart function returns one of these rather than raising, because
    the dashboard filters interactively: a metro filter that happens to
    select nothing must not take the whole app down with a traceback.
    """
    apply_style()
    fig, ax = plt.subplots(figsize=size)
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=10,
            color=MUTED, transform=ax.transAxes, wrap=True)
    return fig


# populated by fitted_text(); drained by audit_overflow() and _drop_closed()
_PENDING: list = []


def _drop_closed() -> None:
    """Forget deferred labels belonging to figures that are already closed.

    ``audit_overflow`` drains the queue for the figure it audits, which
    covers every figure that reaches ``save_figure``. Nothing drained it for
    a figure that is never audited — a chart drawn in a notebook, in a test,
    or by a caller that only wanted the Figure — and each queued entry holds
    an Axes, so ``_PENDING`` grew without bound AND kept every one of those
    Figures alive long after ``plt.close()`` was supposed to have released
    them. Ten unaudited charts left ten dead Figures reachable; a dashboard
    session or a sweep leaves thousands.

    "Closed" is read off ``canvas.manager``, which pyplot sets to None on
    close, rather than off ``fignum_exists``: matplotlib hands the number of
    a closed figure straight back to the next one, so a number-based check
    says "still open" about a figure that was closed two charts ago and the
    queue never shrinks.

    A Figure with no ``number`` never went through pyplot and has no manager
    to lose, so it is kept rather than guessed at — dropping a live entry
    would silently switch the overflow audit off for that figure, which is
    the failure this whole module exists to make impossible.
    """
    _PENDING[:] = [p for p in _PENDING
                   if getattr(p[0].figure, "number", None) is None
                   or p[0].figure.canvas.manager is not None]


def _shrink_to_fit(txt, box_px, *, pad: float = 0.94,
                   min_fs: float = 5.0) -> bool:
    """Shrink a Text artist until it fits inside a pixel-space box.

    Measure, shrink, repeat — eyeballing does not catch overflow, and these
    labels change on every model re-run. Returns False if it hit the floor
    still too big, which is a defect the caller must surface.
    """
    max_w, max_h = box_px[0] * pad, box_px[1] * pad
    renderer = txt.figure.canvas.get_renderer()
    for _ in range(40):
        bb = txt.get_window_extent(renderer=renderer)
        if bb.width <= max_w and bb.height <= max_h:
            return True
        fs = txt.get_fontsize()
        if fs <= min_fs:
            return False
        txt.set_fontsize(max(min_fs, fs * 0.94))
    return False


def fitted_text(ax, x, y, w, h, text, *, transform=None, **kw):
    """Place text that is guaranteed to fit inside a (x, y, w, h) rectangle.

    ``transform`` defaults to axes fractions rather than data coordinates:
    most annotations on these charts sit on a log x-axis, where a data-space
    rectangle is not a rectangle on screen.
    """
    tf = transform if transform is not None else ax.transAxes
    kw.setdefault("ha", "left")
    kw.setdefault("va", "top")
    kw.setdefault("fontsize", 8)
    kw.setdefault("color", INK_2)
    kw.setdefault("linespacing", 1.4)
    ha = kw["ha"]
    tx = x if ha == "left" else (x + w if ha == "right" else x + w / 2)
    ty = y + h if kw["va"] == "top" else y
    t = ax.text(tx, ty, text, transform=tf, zorder=6, **kw)
    # Sweep the queue on the way in, so it is bounded by the figures actually
    # open rather than by every figure ever drawn in this process.
    _drop_closed()
    _PENDING.append((ax, t, x, y, w, h, tf, text))
    return t


def caption(ax, text: str, *, y: float = -0.36, h: float = 0.22,
            wrap: int = 104, **kw):
    """A note in the margin BELOW the axes.

    Explanatory sentences were originally placed inside the plot area and
    collided with the marks on real data — an annotation that sits on top of
    the points it is explaining is worse than no annotation. The margin is
    the only region guaranteed to stay empty however the data moves.

    The text is hard-wrapped rather than left to the fitter, because a long
    single line can only be made to fit by shrinking it to an unreadable
    size; wrapping first means the fitter is trimming, not rescuing.
    """
    kw.setdefault("fontsize", 7.8)
    kw.setdefault("color", MUTED)
    kw.setdefault("style", "italic")
    return fitted_text(ax, 0.0, y, 1.0, h, textwrap.fill(text, wrap),
                       va="bottom", **kw)


def audit_overflow(fig, name: str) -> list[str]:
    """Fit every deferred label, then report the ones that still do not fit.

    Run once per figure after layout, because text extents are meaningless
    until a renderer exists.
    """
    fig.canvas.draw()
    _drop_closed()
    bad = []
    for ax, t, x, y, w, h, tf, text in list(_PENDING):
        if ax.figure is not fig:
            continue
        p0 = tf.transform((x, y))
        p1 = tf.transform((x + w, y + h))
        box_px = (abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))
        if not _shrink_to_fit(t, box_px):
            bad.append(text.split("\n")[0][:48])
    _PENDING[:] = [p for p in _PENDING if p[0].figure is not fig]
    for label in bad:
        _log.warning("%s: label still overflows its box -> %r", name, label)
    return bad


class Saved(NamedTuple):
    """What save_figure wrote, and what was wrong with it.

    The overflow list is returned rather than only logged because
    audit_overflow drains its queue: a caller that wanted the defect list had
    to audit first, which left save_figure recording zero defects for a
    figure that had them.
    """

    path: Path
    overflow: list[str]


def save_figure(fig, name: str, out_dir: Path | None = None) -> Saved:
    """Audit the labels, write the PNG, record it as a run artefact."""
    directory = Path(out_dir) if out_dir else paths.RUN_FIGURES
    directory.mkdir(parents=True, exist_ok=True)
    bad = audit_overflow(fig, name)
    path = directory / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    artefact(path, overflow=len(bad))
    return Saved(path, bad)
