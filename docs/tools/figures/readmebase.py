"""Shared furniture for the README-width figures.

Split out of ``fig_readme`` when that file crossed 300 lines. The boundary is
real rather than arbitrary: everything here is about the MEDIUM -- how wide a
README figure is, how big its type has to be, where its footnote sits, how to
stop two points landing on each other -- and nothing here knows what any
figure is about.

``fig_readme`` imports this and draws; ``fig_paper`` does not, because a
printed column wants none of it.
"""

from __future__ import annotations

import contextlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import figbase as fb  # noqa: E402

#: Inches. A GitHub README renders at roughly 900 CSS pixels; drawing at 9.6in
#: and 400 dpi gives a figure that is sharp on a retina display and is never
#: UPSCALED, which is the fault this whole module exists to avoid.
WIDTH = 9.6

# Type that reaches a screen, not an IEEE column. figbase's defaults are
# 7-8.5pt and would be a whisper across ten inches.
PT_TITLE = 16.5
PT_SUB = 10.0
PT_TICK = 10.0
PT_LABEL = 10.5
PT_FOOT = 8.2


@contextlib.contextmanager
def scale(title: float = PT_TITLE, sub: float = PT_SUB):
    """Borrow ``figbase.titles`` at README sizes, then put it back.

    The point sizes are module globals in ``figbase``, so raising them without
    restoring would shrink -- or rather inflate -- every figure built later in
    the same process, including the paper's.
    """
    old = (fb.PT_TITLE, fb.PT_SUB)
    fb.PT_TITLE, fb.PT_SUB = title, sub
    try:
        yield
    finally:
        fb.PT_TITLE, fb.PT_SUB = old


def foot(fig, text: str) -> None:
    """The caveat block under a figure, in the figure rather than the README.

    Deliberately part of the PNG. A README caption is lost the moment someone
    screenshots the chart into a slide deck, and these lines are the ones that
    keep a number honest.
    """
    fig.text(0.0, 0.006, text, fontsize=PT_FOOT, color=fb.MUTED, va="bottom",
             ha="left", linespacing=1.6)


def dodge(xs, min_sep: float) -> list[int]:
    """Lane indices that keep near-coincident points apart, deterministically.

    No random jitter. A figure here must rebuild identically from the same
    artefact, and ``np.random`` without a seed breaks that; a seed would fix
    reproducibility but still move every point for a reason the reader cannot
    see. This walks the points in order and pushes one into the next lane only
    when it would otherwise sit on its neighbour, so a point moves if and only
    if it has to.

    ``min_sep`` is in log10 units, the axis these points are drawn on.
    Returns 0, +1, -1, +2, -2 ... so the first lane stays on the row's line.
    """
    lanes: list[float] = []          # last x placed in each lane
    idx = []
    for x in xs:
        for i, last in enumerate(lanes):
            if math.log10(x) - math.log10(last) >= min_sep:
                lanes[i] = x
                idx.append(i)
                break
        else:
            lanes.append(x)
            idx.append(len(lanes) - 1)
    return [(0 if i == 0 else (1 if i % 2 else -1) * ((i + 1) // 2))
            for i in idx]
