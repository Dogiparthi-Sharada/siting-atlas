"""Word-document primitives shared by the proposal and defense builders.

Keeps every builder free of python-docx boilerplate so the content modules read
as content. Styling matches the figure palette in tools/figures/common.py.
"""

from __future__ import annotations

import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# palette, mirrored from the validated figure tokens
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK_2 = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xEB, 0x68, 0x34)
CRITICAL = RGBColor(0xD0, 0x3B, 0x3B)
GOOD = RGBColor(0x0C, 0xA3, 0x0C)

BODY_FONT = "Calibri"
MONO_FONT = "Consolas"


# --------------------------------------------------------------------------
# document setup
# --------------------------------------------------------------------------
def new_document() -> Document:
    """A Document with the project's page setup, styles and margins."""
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for attr, val in (("top_margin", 1.0), ("bottom_margin", 1.0),
                      ("left_margin", 1.0), ("right_margin", 1.0)):
        setattr(sec, attr, Inches(val))

    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    pf = normal.paragraph_format
    pf.space_after = Pt(8)
    pf.line_spacing = 1.15

    for name, size, color, before in (
        ("Heading 1", 17, BLUE, 20), ("Heading 2", 13.5, INK, 15),
        ("Heading 3", 11.5, INK_2, 12), ("Heading 4", 11, INK_2, 10),
    ):
        st = doc.styles[name]
        st.font.name = BODY_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = color
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.keep_with_next = True
    return doc


def add_page_numbers(doc: Document) -> None:
    """PAGE field in the footer of every section."""
    for section in doc.sections:
        p = section.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        for kind, text in (("begin", None), ("instrText", "PAGE"),
                           ("end", None)):
            el = OxmlElement(f"w:fld{kind}" if kind != "instrText"
                             else "w:instrText")
            if kind == "begin":
                el.set(qn("w:fldCharType"), "begin")
            elif kind == "end":
                el.set(qn("w:fldCharType"), "end")
            else:
                el.set(qn("xml:space"), "preserve")
                el.text = " PAGE "
            run._r.append(el)
        run.font.size = Pt(9)
        run.font.color.rgb = MUTED


def shade(cell, hex_color: str) -> None:
    """Apply a background fill to a table cell or paragraph."""
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(el)


# --------------------------------------------------------------------------
# content helpers
# --------------------------------------------------------------------------
def para(doc, text="", *, size=11, bold=False, italic=False, color=INK,
         align=None, space_after=8, indent=0.0, mono=False):
    """Add a paragraph in a named style and return it."""
    p = doc.add_paragraph()
    if align:
        p.alignment = {"c": WD_ALIGN_PARAGRAPH.CENTER,
                       "r": WD_ALIGN_PARAGRAPH.RIGHT,
                       "j": WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    if text:
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic
        r.font.color.rgb = color
        r.font.name = MONO_FONT if mono else BODY_FONT
    return p


def rich(doc, chunks, *, size=11, align=None, space_after=8, indent=0.0):
    """Paragraph from (text, style) chunks. style in {'', 'b', 'i', 'bi',
    'm'} plus an optional colour, e.g. ('text', 'b', ORANGE)."""
    p = doc.add_paragraph()
    if align:
        p.alignment = {"c": WD_ALIGN_PARAGRAPH.CENTER,
                       "j": WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    for chunk in chunks:
        text, style = chunk[0], chunk[1] if len(chunk) > 1 else ""
        color = chunk[2] if len(chunk) > 2 else INK
        r = p.add_run(text)
        r.bold = "b" in style
        r.italic = "i" in style
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = MONO_FONT if "m" in style else BODY_FONT
    return p


def bullets(doc, items, *, style="List Bullet", size=11, space_after=4):
    """Add a bulleted list, one paragraph per item."""
    for item in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(space_after)
        if isinstance(item, str):
            item = [(item,)]
        for chunk in item:
            text, st = chunk[0], chunk[1] if len(chunk) > 1 else ""
            color = chunk[2] if len(chunk) > 2 else INK
            r = p.add_run(text)
            r.bold, r.italic = "b" in st, "i" in st
            r.font.size = Pt(size)
            r.font.color.rgb = color


def callout(doc, title, body, *, accent=ORANGE, fill="FDF0EA"):
    """Single-cell shaded box used for emphasis notes."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    shade(cell, fill)
    cell.paragraphs[0].text = ""

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(title)
    r.bold, r.font.size, r.font.color.rgb = True, Pt(10), accent

    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(2)
    r2 = p2.add_run(body)
    r2.font.size, r2.font.color.rgb = Pt(10), INK_2
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def table(doc, header, rows, *, widths=None, size=9.5, header_fill="EAF2FC"):
    """Add a table from a header row and body rows, styled consistently."""
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, text in enumerate(header):
        cell = t.rows[0].cells[i]
        shade(cell, header_fill)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        r.bold, r.font.size, r.font.color.rgb = True, Pt(size), INK
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(str(text))
            r.font.size = Pt(size)
            r.font.color.rgb = INK_2
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def figure(doc, fig_dir, name, caption_text, *, width=6.5):
    """Insert a figure with its caption, scaled to the text width."""
    path = os.path.join(fig_dir, f"{name}.png")
    if not os.path.exists(path):
        para(doc, f"[missing figure: {name}.png]", color=CRITICAL, italic=True)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    p.add_run().add_picture(path, width=Inches(width))
    para(doc, caption_text, size=9, italic=True, color=MUTED, align="c",
         space_after=12)


def page_break(doc):
    """Force a page break."""
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def landscape_section(doc):
    """Start a landscape section (for wide figures)."""
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.page_width, sec.page_height = Inches(11), Inches(8.5)
    sec.left_margin = sec.right_margin = Inches(0.7)
    sec.top_margin = sec.bottom_margin = Inches(0.7)
    return sec


def portrait_section(doc):
    """Start a new portrait section, for returning from a landscape one."""
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(1.0)
    sec.top_margin = sec.bottom_margin = Inches(1.0)
    return sec
