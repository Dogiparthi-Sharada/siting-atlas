"""Place labels on a bubble map without a hand-tuned offset table.

Hand-tuned offsets are how the previous national map worked: a dictionary of
ten metro names against ten ``(dx, dy, ha, va)`` tuples. They rot silently.
The moment the underlying model changes and a metro moves -- which is exactly
what happened -- the table still applies and the figure still renders, just
wrongly. This searches instead, at build time, against what is actually on
the canvas.

Two rules, and the second is the one that matters.

**Clearance.** Eight directions off the marker's rim at three distances,
scored by the area of ink a label would cover: other labels, the title, the
legend, the axis text, and the markers themselves. Zero wins immediately; if
nothing is clear, the least bad is used rather than the label being dropped.

**Ownership.** Not overlapping anything is not enough. The first version of
this put "Cleveland  $1.03" in genuinely clear space to the left of
Cleveland, where it came to rest beneath Chicago's much larger bubble and
read as Chicago's caption. Clearance is a geometric test; ownership is the
perceptual one. A candidate is therefore also rejected when the marker
nearest the label's centre is not the marker it belongs to -- the rule a
reader applies, applied here.

The penalties are in square pixels, the same units as the overlap area, so
they compose: a little overlap always beats a misattributed label, and
anything beats running off the page.
"""

from __future__ import annotations

import numpy as np
from matplotlib import patheffects as pe
from matplotlib.transforms import Bbox

OWNERSHIP_PENALTY = 2e6
OFFCANVAS_PENALTY = 1e7

#: Unit offsets from the marker's rim. Rightward first and leftward last on
#: purpose: a left-set label runs back across the map, so its far end is the
#: one most likely to land beside somebody else's marker.
_D = 0.7071
DIRS = ((1, 0, "left", "center"),
        (_D, _D, "left", "bottom"), (_D, -_D, "left", "top"),
        (0, 1, "center", "bottom"), (0, -1, "center", "top"),
        (-1, 0, "right", "center"),
        (-_D, _D, "right", "bottom"), (-_D, -_D, "right", "top"))

GAPS = (2.5, 12.0, 24.0)


def overlap(a, b) -> float:
    """Area shared by two pixel boxes."""
    dx = min(a.x1, b.x1) - max(a.x0, b.x0)
    dy = min(a.y1, b.y1) - max(a.y0, b.y0)
    return dx * dy if dx > 0 and dy > 0 else 0.0


def text_boxes(fig, renderer) -> list:
    """Every text already drawn, as pixel boxes a label must avoid."""
    out = [t.get_window_extent(renderer) for t in fig.texts if t.get_text()]
    for ax in fig.axes:
        out += [t.get_window_extent(renderer) for t in ax.texts
                if t.get_text()]
        if ax.axison:
            out += [t.get_window_extent(renderer)
                    for t in ax.get_xticklabels() if t.get_text()]
    return out


def place(fig, ax, xy, radii, labels, *, fontsize=9.4, color="#1a1a1a",
          zorder=9, halo=2.6):
    """Annotate ``labels`` -- a mapping of index to string -- on ``ax``.

    ``xy`` is an (n, 2) array of marker positions in data coordinates and
    ``radii`` their radii in typographic points; only the indices present in
    ``labels`` are drawn, but every marker is an obstacle. Returns one
    ``(index, ha, va, penalty)`` per label so the build can report how hard
    each one was to place; a non-zero penalty means the layout is crowded.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    w, h = fig.bbox.width, fig.bbox.height
    px = fig.dpi / 72.0
    effects = [pe.withStroke(linewidth=halo, foreground="white")]

    pix = ax.transData.transform(np.asarray(xy))
    blocked = text_boxes(fig, r)
    for (x, y), rad in zip(pix, np.asarray(radii) * px, strict=True):
        blocked.append(Bbox.from_extents(x - rad, y - rad, x + rad, y + rad))

    placed = []
    for i, text in labels.items():
        rad = float(radii[i])
        t = ax.annotate(text, tuple(np.asarray(xy)[i]), xytext=(0, 0),
                        textcoords="offset points", fontsize=fontsize,
                        color=color, zorder=zorder, path_effects=effects)
        best = (float("inf"), None)
        for gap in GAPS:
            for dx, dy, ha, va in DIRS:
                t.xyann = ((rad + gap) * dx, (rad + gap) * dy)
                t.set_horizontalalignment(ha)
                t.set_verticalalignment(va)
                bb = t.get_window_extent(r).expanded(1.05, 1.45)
                pen = sum(overlap(bb, o) for o in blocked)
                d = np.hypot(pix[:, 0] - (bb.x0 + bb.x1) / 2,
                             pix[:, 1] - (bb.y0 + bb.y1) / 2)
                if int(np.argmin(d)) != i:
                    pen += OWNERSHIP_PENALTY
                if (bb.x0 < 1 or bb.y0 < 1
                        or bb.x1 > w - 1 or bb.y1 > h - 1):
                    pen += OFFCANVAS_PENALTY
                if pen < best[0]:
                    best = (pen, (t.xyann, ha, va, bb))
                if pen == 0:
                    break
            if best[0] == 0:
                break
        t.xyann, ha, va, bb = best[1]
        t.set_horizontalalignment(ha)
        t.set_verticalalignment(va)
        blocked.append(bb)
        placed.append((i, ha, va, best[0]))
    return placed
