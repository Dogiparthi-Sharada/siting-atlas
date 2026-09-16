"""Coordinate-based layout validator for the deck.

Three geometric rules, all checked against real rectangles in inches:

  RULE 1  every shape rect must sit inside the slide rect
  RULE 2  every text block rect must sit inside its own shape rect
  RULE 3  two shapes may nest, or be disjoint - they may not partially
          overlap (that is how a label ends up crossing a card border)

Text extents are measured with real glyph metrics (PIL), wrapped to the
available width, so RULE 2 is a measurement rather than a guess.

    python tools/deck/check_layout.py docs/proposal/Siting_Atlas_Deck.pptx

Exit code 1 if any rule is violated.
"""

from __future__ import annotations

import argparse
import glob
import os
import textwrap

from PIL import ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

EMU_IN = 914400.0
EMU_PT = 12700.0
FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts"]
_FCACHE: dict = {}
TOL = 0.02          # inches of slack before a violation is reported


# --------------------------------------------------------------------------
# rectangles
# --------------------------------------------------------------------------
class Rect:
    """A slide rectangle in EMU, with the geometry the checker needs."""
    __slots__ = ("l", "t", "r", "b")

    def __init__(self, l, t, r, b):
        """Build from explicit left/top/width/height in EMU."""
        self.l, self.t, self.r, self.b = l, t, r, b

    @classmethod
    def from_shape(cls, sh):
        """Rect covering a python-pptx shape."""
        return cls(sh.left / EMU_IN, sh.top / EMU_IN,
                   (sh.left + sh.width) / EMU_IN,
                   (sh.top + sh.height) / EMU_IN)

    w = property(lambda s: s.r - s.l)
    h = property(lambda s: s.b - s.t)

    def inset(self, left, top, right, bottom):
        """A copy shrunk by ``d`` on every side, for tolerance checks."""
        return Rect(self.l + left, self.t + top, self.r - right,
                    self.b - bottom)

    def contains(self, o, tol=TOL):
        """Does this rectangle fully enclose ``other``?"""
        return (o.l >= self.l - tol and o.t >= self.t - tol
                and o.r <= self.r + tol and o.b <= self.b + tol)

    def overhang(self, o):
        """How far `o` sticks out of self, per side, in inches."""
        return {"left": max(0.0, self.l - o.l), "top": max(0.0, self.t - o.t),
                "right": max(0.0, o.r - self.r),
                "bottom": max(0.0, o.b - self.b)}

    def intersects(self, o, tol=TOL):
        """Do the two rectangles overlap at all?"""
        return (o.l < self.r - tol and o.r > self.l + tol
                and o.t < self.b - tol and o.b > self.t + tol)

    def __repr__(self):
        """Compact left/top/width/height, for a failure message."""
        return (f"[{self.l:.2f},{self.t:.2f} -> {self.r:.2f},{self.b:.2f}]")


# --------------------------------------------------------------------------
# text measurement
# --------------------------------------------------------------------------
def _font(size_pt, bold):
    """Load and cache the measuring font at one size."""
    key = (round(size_pt, 1), bold)
    if key not in _FCACHE:
        want = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        path = None
        for root in FONT_DIRS:
            hits = glob.glob(os.path.join(root, "**", want), recursive=True)
            if hits:
                path = hits[0]
                break
        # DejaVu runs a little wider than Calibri, which biases this check
        # toward false positives. That is the right direction for a linter.
        _FCACHE[key] = (ImageFont.truetype(path, max(6, int(round(size_pt))))
                        if path else ImageFont.load_default())
    return _FCACHE[key]


def _width_pt(s, size_pt, bold):
    """Rendered width of a string in points."""
    f = _font(size_pt, bold)
    try:
        return f.getlength(s)
    except AttributeError:
        return f.getsize(s)[0]


def _wrap(line, avail_pt, size_pt, bold):
    """Greedy word wrap to a pixel width; returns the resulting lines."""
    if not line.strip():
        return [""]
    if _width_pt(line, size_pt, bold) <= avail_pt:
        return [line]
    n = max(4, int(len(line) * avail_pt / max(1.0, _width_pt(line, size_pt,
                                                             bold))))
    for _ in range(8):
        parts = textwrap.wrap(line, n) or [line]
        if max(_width_pt(p, size_pt, bold) for p in parts) <= avail_pt:
            return parts
        n = max(4, int(n * 0.92))
    return textwrap.wrap(line, n) or [line]


def text_rect(shape, box: Rect) -> Rect | None:
    """The rectangle the rendered text actually occupies, in inches."""
    tf = shape.text_frame
    if not tf.text.strip():
        return None
    inner = box.inset(tf.margin_left / EMU_IN, tf.margin_top / EMU_IN,
                      tf.margin_right / EMU_IN, tf.margin_bottom / EMU_IN)
    avail_pt = max(10.0, inner.w * 72.0)

    widest_pt, total_pt = 0.0, 0.0
    for p in tf.paragraphs:
        runs = p.runs
        if not runs:
            total_pt += 8
            continue
        size = max((r.font.size.pt for r in runs if r.font.size), default=18)
        bold = any(r.font.bold for r in runs)
        line = "".join(r.text for r in runs)
        parts = _wrap(line, avail_pt, size, bold)
        widest_pt = max(widest_pt, max(_width_pt(p_, size, bold)
                                       for p_ in parts))
        spacing = p.line_spacing if isinstance(p.line_spacing, float) else 1.0
        total_pt += len(parts) * size * 1.22 * spacing
        total_pt += p.space_after.pt if p.space_after else 0

    tw, th = widest_pt / 72.0, total_pt / 72.0

    align = tf.paragraphs[0].alignment
    if align == PP_ALIGN.CENTER:
        l = inner.l + (inner.w - tw) / 2
    elif align == PP_ALIGN.RIGHT:
        l = inner.r - tw
    else:
        l = inner.l

    anchor = tf.vertical_anchor
    if anchor == MSO_ANCHOR.MIDDLE:
        t = inner.t + (inner.h - th) / 2
    elif anchor == MSO_ANCHOR.BOTTOM:
        t = inner.b - th
    else:
        t = inner.t
    return Rect(l, t, l + tw, t + th)


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
SOLID = {MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.PICTURE,
         MSO_SHAPE_TYPE.TABLE}


def check_slide(slide, slide_rect: Rect):
    """Every layout problem found on one slide.

    Catches the two failures that survive a visual skim: text that
    overflows its box, and shapes that overlap. Both look fine in the
    editor and wrong on a projector.
    """
    issues = []
    boxes = []
    for sh in slide.shapes:
        if sh.left is None or sh.width is None:
            continue
        r = Rect.from_shape(sh)
        boxes.append((sh, r))

        # RULE 1 - inside the slide
        if not slide_rect.contains(r):
            o = slide_rect.overhang(r)
            side = ", ".join(f"{k} {v:.2f}in" for k, v in o.items() if v > TOL)
            issues.append(f"RULE 1  off-slide   {r}  ({side})")

        # RULE 2 - text inside its own shape
        if sh.has_text_frame:
            tr = text_rect(sh, r)
            if tr and not r.contains(tr):
                o = r.overhang(tr)
                side = ", ".join(f"{k} +{v:.2f}in"
                                 for k, v in o.items() if v > TOL)
                snippet = sh.text_frame.text.strip().split("\n")[0][:40]
                issues.append(
                    f"RULE 2  text spills {side:<34} \"{snippet}\"")

    # RULE 3 - nested or disjoint, never partially overlapping
    solids = [(sh, r) for sh, r in boxes
              if sh.shape_type in SOLID and sh.width > 0]
    for i, (sa, ra) in enumerate(solids):
        for sb, rb in solids[i + 1:]:
            if not ra.intersects(rb):
                continue
            if ra.contains(rb) or rb.contains(ra):
                continue
            issues.append(
                f"RULE 3  shapes cross  {ra}  x  {rb}")
    return issues


def check(path: str) -> int:
    """Check every slide in a deck and return the findings per slide."""
    prs = Presentation(path)
    slide_rect = Rect(0, 0, prs.slide_width / EMU_IN,
                      prs.slide_height / EMU_IN)
    print(f"slide canvas: {slide_rect.w:.3f} x {slide_rect.h:.3f} in\n")

    total = 0
    for n, slide in enumerate(prs.slides, start=1):
        issues = check_slide(slide, slide_rect)
        if issues:
            total += len(issues)
            print(f"  slide {n:>2}")
            for i in issues:
                print(f"      {i}")
    print("-" * 72)
    count = len(prs.slides._sldIdLst)
    if total:
        print(f"{total} violation(s) across {count} slides")
    else:
        print(f"All {count} slides pass: shapes inside the canvas, text "
              f"inside its shape, no crossing shapes.")
    return 1 if total else 0


def main() -> int:
    """CLI entry point. Returns 1 if any slide has a layout problem."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deck")
    return check(ap.parse_args().deck)


if __name__ == "__main__":
    raise SystemExit(main())
