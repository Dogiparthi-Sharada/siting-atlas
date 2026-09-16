"""Slide primitives for the Siting Atlas deck.

One place for layout and colour so every slide looks the same by construction.
Palette mirrors tools/figures/common.py, which was validated for print.
"""

from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import textfit

# 16:9
W, H = Inches(13.333), Inches(7.5)

INK = RGBColor(0x0B, 0x0B, 0x0B)
INK_2 = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
BLUE_L = RGBColor(0xEA, 0xF2, 0xFC)
ORANGE = RGBColor(0xEB, 0x68, 0x34)
ORANGE_L = RGBColor(0xFD, 0xF0, 0xEA)
GREEN = RGBColor(0x0C, 0xA3, 0x0C)
GREEN_L = RGBColor(0xEA, 0xF7, 0xEA)
RED = RGBColor(0xD0, 0x3B, 0x3B)
RED_L = RGBColor(0xFB, 0xEA, 0xEA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PLANE = RGBColor(0xF9, 0xF9, 0xF7)
LINE = RGBColor(0xE1, 0xE0, 0xD9)

FONT = "Calibri"
MARGIN = Inches(0.62)


def new_deck() -> Presentation:
    """An empty 16:9 presentation at the project's slide size."""
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    return prs


def blank(prs):
    """Add a slide using the blank layout — every element is placed."""
    return prs.slides.add_slide(prs.slide_layouts[6])


def _tf(shape, text, *, size, bold=False, color=INK, align=PP_ALIGN.LEFT,
        italic=False, spacing=1.0, font=FONT):
    """A configured text frame in a new textbox at the given rectangle."""
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = font
    return tf


def text(slide, x, y, w, h, body, *, size=16, bold=False, color=INK,
         align=PP_ALIGN.LEFT, italic=False, spacing=1.0, anchor=MSO_ANCHOR.TOP,
         font=FONT, fit=True, min_pt=8.0):
    """Text box whose contents are shrunk until they fit the given rectangle.

    python-pptx does not lay text out, so a hand-placed box will silently
    overflow. Measuring here means tools/deck/check_layout.py cannot disagree
    with what was built.
    """
    box = slide.shapes.add_textbox(x, y, w, h)
    if fit and body.strip():
        pad_w = Inches(0.16) / 914400.0 * 72.0      # _tf margins, in points
        pad_h = Inches(0.08) / 914400.0 * 72.0
        avail_w = max(12.0, w / 914400.0 * 72.0 - pad_w)
        avail_h = max(8.0, h / 914400.0 * 72.0 - pad_h)
        size = textfit.fit_size(body.split("\n"), avail_w, avail_h, size,
                                bold=bold, spacing=spacing, min_pt=min_pt)
    _tf(box, body, size=size, bold=bold, color=color, align=align,
        italic=italic, spacing=spacing, font=font)
    box.text_frame.vertical_anchor = anchor
    return box


def title(slide, heading, sub=None):
    """Standard slide header: rule, title, optional one-line subtitle."""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, Inches(0.42),
                                 Inches(0.09), Inches(0.46))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ORANGE
    bar.line.fill.background()
    bar.shadow.inherit = False

    text(slide, MARGIN + Inches(0.22), Inches(0.36), Inches(11.9), Inches(0.6),
         heading, size=27, bold=True, color=INK)
    if sub:
        text(slide, MARGIN + Inches(0.24), Inches(1.02), Inches(11.9),
             Inches(0.4), sub, size=13.5, color=INK_2, italic=True)
    return Inches(1.62) if sub else Inches(1.28)


def card(slide, x, y, w, h, heading, body, *, accent=BLUE, fill=None,
         hsize=13.5, bsize=12, mono=False):
    """Rounded panel with a bold heading and body text."""
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill if fill else WHITE
    shp.line.color.rgb = accent
    shp.line.width = Pt(1.4)
    shp.shadow.inherit = False
    shp.adjustments[0] = 0.06
    shp.text_frame.text = ""

    pad = Inches(0.2)
    if heading:
        text(slide, x + pad, y + Inches(0.13), w - 2 * pad, Inches(0.34),
             heading, size=hsize, bold=True, color=accent)
        by = y + Inches(0.55)
        bh = h - Inches(0.68)
    else:
        by, bh = y + Inches(0.16), h - Inches(0.3)
    if body:
        text(slide, x + pad, by, w - 2 * pad, bh, body, size=bsize,
             color=INK_2, spacing=1.18,
             font="Consolas" if mono else FONT)
    return shp


def stat(slide, x, y, w, h, value, label, *, accent=BLUE, fill=None):
    """Big-number tile."""
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill if fill else PLANE
    shp.line.color.rgb = accent
    shp.line.width = Pt(1.3)
    shp.shadow.inherit = False
    shp.adjustments[0] = 0.08
    shp.text_frame.text = ""
    text(slide, x, y + Inches(0.16), w, Inches(0.62), value, size=30,
         bold=True, color=accent, align=PP_ALIGN.CENTER)
    text(slide, x, y + Inches(0.84), w, h - Inches(0.9), label, size=11.5,
         color=INK_2, align=PP_ALIGN.CENTER, spacing=1.12)
    return shp


def bullets(slide, x, y, w, h, items, *, size=15, gap=1.5, color=INK_2,
            marker="—"):
    """Add a bulleted list, one paragraph per item."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        bold_head = None
        if isinstance(item, tuple):
            bold_head, item = item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.2
        p.space_after = Pt(gap * 5)
        r0 = p.add_run()
        r0.text = f"{marker}  "
        r0.font.size = Pt(size)
        r0.font.color.rgb = ORANGE
        r0.font.name = FONT
        if bold_head:
            rb = p.add_run()
            rb.text = bold_head
            rb.font.size = Pt(size)
            rb.font.bold = True
            rb.font.color.rgb = INK
            rb.font.name = FONT
        r = p.add_run()
        r.text = item
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = FONT
    return box


def picture(slide, path, x, y, w=None, h=None):
    """Place an image, scaled to fit the given box."""
    if not os.path.exists(path):
        card(slide, x, y, w or Inches(6), h or Inches(3), "MISSING FIGURE",
             os.path.basename(path), accent=RED, fill=RED_L)
        return None
    return slide.shapes.add_picture(path, x, y, width=w, height=h)


def figure_slide(prs, fig_dir, name, heading, sub, note=None):
    """A slide that is mostly one figure."""
    s = blank(prs)
    top = title(s, heading, sub)
    path = os.path.join(fig_dir, f"{name}.png")
    reserve = Inches(0.95) if note else Inches(0.5)
    pic = picture(s, path, Inches(0.7), top + Inches(0.06), w=Inches(11.93))
    if pic and pic.height > H - top - reserve:
        scale = (H - top - reserve) / pic.height
        pic.height = int(pic.height * scale)
        pic.width = int(pic.width * scale)
        pic.left = int((W - pic.width) / 2)
    if note:
        text(s, MARGIN, H - Inches(0.78), Inches(12.1), Inches(0.66), note,
             size=11.5, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    return s


def notes(slide, body: str) -> None:
    """Attach presenter notes. Written to be READ ALOUD, not skimmed:
    an opening line, the point to land, and the likely interruption."""
    slide.notes_slide.notes_text_frame.text = body.strip()


def eq(slide, x, y, w, body, *, size=15, color=INK, align=PP_ALIGN.CENTER):
    """A centred monospace equation block on a recessive plane."""
    lines = body.strip("\n").split("\n")
    h = Inches(0.30 * len(lines) + 0.26)
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = PLANE
    shp.line.color.rgb = LINE
    shp.line.width = Pt(1.0)
    shp.shadow.inherit = False
    shp.adjustments[0] = 0.05
    shp.text_frame.text = ""
    text(slide, x, y + Inches(0.10), w, h - Inches(0.2), body.strip("\n"),
         size=size, color=color, align=align, font="Consolas", spacing=1.16,
         anchor=MSO_ANCHOR.MIDDLE)
    return shp, y + h


def footer(slide, left_text, page=None):
    """Add the standard slide footer (title and number)."""
    text(slide, MARGIN, H - Inches(0.42), Inches(9), Inches(0.3), left_text,
         size=9.5, color=MUTED)
    if page is not None:
        text(slide, W - Inches(1.3), H - Inches(0.42), Inches(0.7),
             Inches(0.3), str(page), size=9.5, color=MUTED,
             align=PP_ALIGN.RIGHT)


def banner(slide, y, msg, *, accent=GREEN, fill=GREEN_L, size=15):
    """Full-width emphasis strip."""
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MARGIN, y,
                                 W - 2 * MARGIN, Inches(0.86))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = accent
    shp.line.width = Pt(1.5)
    shp.shadow.inherit = False
    shp.adjustments[0] = 0.14
    shp.text_frame.text = ""
    text(slide, MARGIN + Inches(0.2), y + Inches(0.12), W - 2 * MARGIN -
         Inches(0.4), Inches(0.62), msg, size=size, bold=True, color=accent,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return shp


def table(slide, x, y, w, rows, *, col_w=None, size=11.5, head_fill=BLUE_L,
          row_h=Inches(0.42)):
    """Simple table. rows[0] is the header.

    Row heights are computed from wrapped cell content rather than assumed,
    because PowerPoint grows a row to fit its text and would otherwise push
    the table over whatever was placed beneath it. Returns (table, bottom_y).
    """
    nr, nc = len(rows), len(rows[0])
    widths = list(col_w) if col_w else [int(w / nc)] * nc
    pad_pt = Inches(0.18) / 914400.0 * 72.0

    heights = []
    for ri, row in enumerate(rows):
        tallest = 0.0
        for ci, val in enumerate(row):
            avail = max(20.0, widths[ci] / 914400.0 * 72.0 - pad_pt)
            _, hpt = textfit.block_size(str(val).split("\n"), size, avail,
                                        bold=(ri == 0), spacing=1.05)
            tallest = max(tallest, hpt)
        heights.append(max(row_h, Inches((tallest + 8) / 72.0)))

    shape = slide.shapes.add_table(nr, nc, x, y, w, sum(heights))
    tbl = shape.table
    for i, cw in enumerate(widths):
        tbl.columns[i].width = cw
    for ri, row in enumerate(rows):
        tbl.rows[ri].height = heights[ri]
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.text = ""
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = Inches(0.09)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.fill.solid()
            cell.fill.fore_color.rgb = head_fill if ri == 0 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.line_spacing = 1.05
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(size)
            r.font.bold = (ri == 0)
            r.font.color.rgb = INK if ri == 0 else INK_2
            r.font.name = FONT
    return tbl, y + sum(heights)
