"""Glyph-accurate text measurement, shared by the deck builder and its linter.

The builder uses it to shrink text until it fits its box; the linter uses it to
verify that it did. Same measurement on both sides, so a passing build cannot
disagree with a passing check.
"""

from __future__ import annotations

import glob
import os
import textwrap

from PIL import ImageFont

FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts"]
_CACHE: dict = {}
LINE_FACTOR = 1.22          # rendered line height as a multiple of point size


def font(size_pt: float, bold: bool):
    """Load and cache the measuring font at one size."""
    key = (round(size_pt, 1), bool(bold))
    if key not in _CACHE:
        want = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        path = None
        for root in FONT_DIRS:
            hits = glob.glob(os.path.join(root, "**", want), recursive=True)
            if hits:
                path = hits[0]
                break
        # DejaVu is slightly wider than Calibri, so both fitting and checking
        # are conservative in the same direction.
        _CACHE[key] = (ImageFont.truetype(path, max(6, int(round(size_pt))))
                       if path else ImageFont.load_default())
    return _CACHE[key]


def width_pt(s: str, size_pt: float, bold: bool = False) -> float:
    """Rendered width of a string in points, for overflow checking."""
    f = font(size_pt, bold)
    try:
        return f.getlength(s)
    except AttributeError:
        return f.getsize(s)[0]


def wrap(line: str, avail_pt: float, size_pt: float, bold: bool = False):
    """Wrap one logical line to the available width, in points."""
    if not line.strip():
        return [""]
    full = width_pt(line, size_pt, bold)
    if full <= avail_pt:
        return [line]
    n = max(4, int(len(line) * avail_pt / max(1.0, full)))
    for _ in range(8):
        parts = textwrap.wrap(line, n) or [line]
        if max(width_pt(p, size_pt, bold) for p in parts) <= avail_pt:
            return parts
        n = max(4, int(n * 0.92))
    return textwrap.wrap(line, n) or [line]


def block_size(lines, size_pt, avail_pt, *, bold=False, spacing=1.0,
               space_after_pt=0.0):
    """(width_pt, height_pt) of a text block wrapped to avail_pt."""
    widest = 0.0
    total = 0.0
    for line in lines:
        parts = wrap(line, avail_pt, size_pt, bold)
        widest = max(widest, max(width_pt(p, size_pt, bold) for p in parts))
        total += len(parts) * size_pt * LINE_FACTOR * spacing + space_after_pt
    return widest, total


def fit_size(lines, avail_w_pt, avail_h_pt, start_pt, *, bold=False,
             spacing=1.0, min_pt=8.0, step=0.94):
    """Largest font size at or below start_pt whose block fits the box."""
    size = float(start_pt)
    while size > min_pt:
        _, h = block_size(lines, size, avail_w_pt, bold=bold, spacing=spacing)
        if h <= avail_h_pt:
            return size
        size *= step
    return min_pt
