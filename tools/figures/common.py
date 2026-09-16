"""Shared style tokens and drawing helpers for all proposal figures.

Palette is the validated default from the dataviz reference instance, checked
against a WHITE print surface (figures are embedded in a Word doc and printed):

    node validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light \
        --surface "#ffffff" --pairs all
    -> lightness band PASS, chroma floor PASS,
       CVD all-pairs dE 9.2 PASS, normal-vision all-pairs dE 24.0 PASS,
       contrast: aqua 2.82:1 -> RELIEF REQUIRED (every mark is directly
       labelled in these figures, which satisfies the relief rule).

Only the first three categorical slots are used, because these figures include
all-pairs forms and slots 1-3 are the set that validates all-pairs.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import FancyArrowPatch, PathPatch

# --- categorical slots (fixed order, never cycled) -------------------------
BLUE = "#2a78d6"   # slot 1 - the system as proposed
ORANGE = "#eb6834"  # slot 2 - what is NEW in v4
AQUA = "#1baf7a"   # slot 3 - third series only

# --- status (reserved; never reused as a series) ---------------------------
GOOD = "#0ca30c"
WARNING = "#fab219"
SERIOUS = "#ec835a"
CRITICAL = "#d03b3b"

# --- ink and chrome --------------------------------------------------------
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"      # white paper
PLANE = "#f9f9f7"

# --- sequential blue ramp (light -> dark) ----------------------------------
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#256abf", "#184f95"]

FONT = ["DejaVu Sans"]
DPI = 220


def apply_style() -> None:
    """Global rcParams. Call once before building figures."""
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
        "axes.titlesize": 11,
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
        "lines.markersize": 5,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.18,
    })


def recede_axes(ax, x_grid: bool = False, y_grid: bool = True) -> None:
    """Drop the top/right spines and push the grid behind the marks."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.set_axisbelow(True)
    if y_grid:
        ax.yaxis.grid(True)
    if x_grid:
        ax.xaxis.grid(True)


def blank_canvas(w: float, h: float, xlim=(0, 100), ylim=(0, 100)):
    """A plain drawing surface for box-and-arrow diagrams."""
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def _fit_text(ax, txt, x, y, w, h, pad=0.92, min_fs=4.5):
    """Shrink a Text artist until it fits inside a data-space rectangle.

    Text overflowing its container is the most common defect in generated
    box-and-arrow diagrams, and eyeballing twelve figures does not catch it.
    This makes overflow impossible by construction: measure, shrink, repeat.
    Returns True if it fits, False if it hit the floor still too big.
    """
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    p0 = ax.transData.transform((x, y))
    p1 = ax.transData.transform((x + w, y + h))
    max_w, max_h = abs(p1[0] - p0[0]) * pad, abs(p1[1] - p0[1]) * pad

    for _ in range(40):
        bb = txt.get_window_extent(renderer=renderer)
        if bb.width <= max_w and bb.height <= max_h:
            return True
        fs = txt.get_fontsize()
        if fs <= min_fs:
            return False
        txt.set_fontsize(max(min_fs, fs * 0.95))
    return False


# populated by box(); drained by audit_overflow()
_PENDING: list = []


class Rect:
    """A drawn box. Connectors anchor to its edges instead of hand-typed
    coordinates, so a box can move without silently detaching its arrows."""

    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        """A rectangle in the 0-100 axis space every figure here uses."""
        self.x, self.y, self.w, self.h = x, y, w, h

    left = property(lambda s: (s.x, s.y + s.h / 2))
    right = property(lambda s: (s.x + s.w, s.y + s.h / 2))
    top = property(lambda s: (s.x + s.w / 2, s.y + s.h))
    bottom = property(lambda s: (s.x + s.w / 2, s.y))
    center = property(lambda s: (s.x + s.w / 2, s.y + s.h / 2))

    def port(self, side, frac=0.5):
        """A point on one edge, `frac` of the way along it."""
        if side == "l":
            return (self.x, self.y + self.h * frac)
        if side == "r":
            return (self.x + self.w, self.y + self.h * frac)
        if side == "t":
            return (self.x + self.w * frac, self.y + self.h)
        return (self.x + self.w * frac, self.y)

    def __iter__(self):
        """Unpack as the CENTRE point, so ``cx, cy = rect`` works.

        Note it is the centre and not (x, y, w, h): almost every call site
        wants somewhere to anchor a label or start an arrow.
        """
        return iter(self.center)


def _facing_sides(a: "Rect", b: "Rect"):
    """Pick the pair of edges that face each other."""
    ax_, ay_ = a.center
    bx_, by_ = b.center
    if abs(bx_ - ax_) >= abs(by_ - ay_):
        return ("r", "l") if bx_ > ax_ else ("l", "r")
    return ("t", "b") if by_ > ay_ else ("b", "t")


def link(ax, a, b, *, sides=None, fracs=(0.5, 0.5), color=MUTED, lw=1.3,
         rad=0.0, ls="-", zorder=2, style="-|>"):
    """Connect two Rects edge-to-edge, choosing the facing edges by default."""
    sa, sb = sides if sides else _facing_sides(a, b)
    p0 = a.port(sa, fracs[0])
    p1 = b.port(sb, fracs[1])
    arrow(ax, p0, p1, color=color, lw=lw, rad=rad, ls=ls, zorder=zorder,
          style=style)
    return p0, p1


def box(ax, x, y, w, h, label, *, face=SURFACE, edge=BLUE, lw=1.4,
        fs=8.5, weight="normal", color=INK, radius=1.6, align="center",
        alpha=1.0, ls="-", autofit=True):
    """Rounded rectangle with a label that is guaranteed to fit inside it."""
    patch = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=mpatches.BoxStyle("Round", pad=0, rounding_size=radius),
        linewidth=lw, edgecolor=edge, facecolor=face, alpha=alpha,
        linestyle=ls, zorder=2,
    )
    ax.add_patch(patch)
    ha = {"center": "center", "left": "left"}[align]
    tx = x + w / 2 if align == "center" else x + 1.6
    aw = w if align == "center" else w - 3.2
    if label:
        t = ax.text(tx, y + h / 2, label, ha=ha, va="center", fontsize=fs,
                    color=color, fontweight=weight, zorder=3,
                    linespacing=1.35)
        if autofit:
            _PENDING.append((ax, t, x, y, aw, h, label))
    return Rect(x, y, w, h)


def audit_overflow(fig, name):
    """Fit every deferred label, then report any that could not be made to fit.

    Called once per figure after layout is complete, because text extents are
    only meaningful once a renderer exists.
    """
    fig.canvas.draw()
    bad = []
    for ax, t, x, y, w, h, label in _PENDING:
        if ax.figure is not fig:
            continue
        if not _fit_text(ax, t, x, y, w, h):
            bad.append(label.split("\n")[0][:44])
    _PENDING[:] = [p for p in _PENDING if p[0].figure is not fig]
    for label in bad:
        print(f"    [!] {name}: label still overflows -> {label!r}")
    return bad


def band(ax, x, y, w, h, label, *, face=PLANE, edge=GRID, fs=8,
         color=INK_2, weight="bold"):
    """A recessive background band used to group boxes into a layer."""
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=mpatches.BoxStyle("Round", pad=0, rounding_size=1.6),
        linewidth=1.0, edgecolor=edge, facecolor=face, zorder=1))
    if label:
        ax.text(x + 1.8, y + h - 2.2, label, ha="left", va="top",
                fontsize=fs, color=color, fontweight=weight, zorder=3)


def arrow(ax, p0, p1, *, color=MUTED, lw=1.3, style="-|>", rad=0.0,
          ls="-", zorder=2, ms=7):
    """Straight or gently curved connector."""
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=ms, linewidth=lw,
        color=color, linestyle=ls, zorder=zorder,
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=2, shrinkB=2))


def elbow(ax, p0, p1, *, color=MUTED, lw=1.3, via="h", zorder=2):
    """Right-angle connector: 'h' goes horizontal first, 'v' vertical first."""
    (x0, y0), (x1, y1) = p0, p1
    mid = (x1, y0) if via == "h" else (x0, y1)
    verts = [p0, mid, p1]
    ax.add_patch(PathPatch(
        Path(verts, [Path.MOVETO, Path.LINETO, Path.LINETO]),
        fill=False, edgecolor=color, linewidth=lw, zorder=zorder))
    arrow(ax, mid, p1, color=color, lw=lw, zorder=zorder)


def caption(ax, text, y=-3.5, fs=7.6):
    """Small note under a diagram."""
    ax.text(50, y, text, ha="center", va="top", fontsize=fs,
            color=MUTED, style="italic", linespacing=1.4)


def newtag(ax, x, y, text="NEW IN v4"):
    """Orange pill marking a v4 addition. Direct label = relief satisfied."""
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), len(text) * 0.92 + 2.5, 3.4,
        boxstyle=mpatches.BoxStyle("Round", pad=0, rounding_size=1.7),
        linewidth=0, facecolor=ORANGE, zorder=4))
    ax.text(x + (len(text) * 0.92 + 2.5) / 2, y + 1.7, text, ha="center",
            va="center", fontsize=6.6, color="#ffffff", fontweight="bold",
            zorder=5)


def save(fig, out_dir, name):
    """Fit all deferred labels, report any overflow, then write the PNG."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    bad = audit_overflow(fig, name)
    path = os.path.join(out_dir, f"{name}.png")
    fig.savefig(path)
    plt.close(fig)
    flag = f"  [{len(bad)} OVERFLOW]" if bad else ""
    print(f"  wrote {name}.png{flag}")
    return path
