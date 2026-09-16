"""Build the IEEE-format .docx from paper/siting_atlas_ieee.tex.

    python tools/paper/build_docx.py

The .tex is the source of truth. This script converts it rather than holding
a second copy of the prose, so the two cannot drift -- which is the whole
reason it exists instead of a hand-written Word file.

Exit codes: 0 written, 2 source missing, 3 conversion failed.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ieee_style as style  # noqa: E402
import tex_blocks as tex  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL  # noqa: E402
from docx.shared import Inches, Pt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "paper", "siting_atlas_ieee.tex")
OUT = os.path.join(ROOT, "paper", "siting_atlas_ieee.docx")
IMG_DIRS = [os.path.join(ROOT, "docs", "figures"),
            os.path.join(ROOT, "outputs", "figures")]


def _find_image(name: str) -> str | None:
    base = os.path.basename(name)
    for d in IMG_DIRS:
        for cand in (base, base + ".png"):
            p = os.path.join(d, cand)
            if os.path.exists(p):
                return p
    return None


def build() -> tuple[int, dict[str, int]]:
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    blocks, cites, refs = tex.parse(src)

    doc = Document()
    style.page_setup(doc.sections[0])
    style.set_columns(doc.sections[0], 1)
    for st in ("Normal",):
        doc.styles[st].font.name = style.FONT
        doc.styles[st].font.size = Pt(style.BODY_PT)

    tally: dict[str, int] = {}
    two_col_started = False
    fig_no, tab_no = 0, 0
    last_was_image = False

    for kind, payload in blocks:
        tally[kind] = tally.get(kind, 0) + 1

        # The title, abstract and keywords span the page; the body is two
        # columns. The switch happens at the first section heading.
        if kind == "section" and not two_col_started:
            style.new_section(doc, 2)
            two_col_started = True

        if kind == "title":
            style.title_block(doc, payload, [])
        elif kind == "author":
            for line in payload:
                p = style.para(doc, align=AL.CENTER, space_after=2)
                style.emit_runs(p, [(line, "")], size=style.AUTHOR_PT)
            style.para(doc, space_after=8)
        elif kind == "boxed":
            p = style.para(doc, align=AL.CENTER, space_after=10,
                           space_before=4)
            style.emit_runs(p, tex.runs(payload, cites, refs),
                            size=style.ABSTRACT_PT,
                        base_bold=True)
        elif kind == "abstract":
            p = style.para(doc, align=AL.JUSTIFY, space_after=6)
            r = p.add_run("Abstract—")
            style._style_run(r, size=style.ABSTRACT_PT, bold=True, italic=True)
            style.emit_runs(p, tex.runs(payload, cites, refs),
                            size=style.ABSTRACT_PT,
                        base_bold=True, base_italic=True)
        elif kind == "keywords":
            p = style.para(doc, align=AL.JUSTIFY, space_after=10)
            r = p.add_run("Index Terms—")
            style._style_run(r, size=style.ABSTRACT_PT, bold=True, italic=True)
            style.emit_runs(p, tex.runs(payload, cites, refs),
                            size=style.ABSTRACT_PT,
                        base_bold=True, base_italic=True)
        elif kind == "section":
            style.heading(doc, payload[0], payload[1])
        elif kind == "subsection":
            style.subheading(doc, payload[0], payload[1])
        elif kind == "para":
            p = style.para(doc, align=AL.JUSTIFY, space_after=0, indent=0.2)
            style.emit_runs(p, tex.runs(payload, cites, refs))
        elif kind == "quote":
            p = style.para(doc, align=AL.JUSTIFY, space_after=6,
                           space_before=6)
            p.paragraph_format.left_indent = Inches(0.18)
            style.emit_runs(p, tex.runs(payload, cites, refs),
                            size=style.BODY_PT - 1,
                        base_italic=True)
        elif kind == "equation":
            p = style.para(doc, align=AL.CENTER, space_after=6, space_before=6)
            style.emit_runs(p, tex.runs(payload, cites, refs),
                            base_italic=True)
        elif kind in ("enumerate", "itemize"):
            for n, item in enumerate(payload, 1):
                p = style.para(doc, align=AL.JUSTIFY, space_after=2)
                p.paragraph_format.left_indent = Inches(0.22)
                lead = f"{n}) " if kind == "enumerate" else "• "
                style.emit_runs(p, [(lead, "")] + tex.runs(item, cites, refs))
        elif kind == "tabular":
            last_was_image = False
            # Cells carry the same inline markup as body text. They must go
            # through the parser too -- skipping it was how \textbf{...} and
            # bare $ leaked into the first build.
            clean = [["".join(t for t, _ in tex.runs(c, cites, refs))
                      for c in row] for row in payload]
            style.table(doc, clean)
            style.para(doc, space_after=6)
        elif kind == "image":
            last_was_image = True
            path = _find_image(payload)
            if path:
                fig_no += 1
                p = style.para(doc, align=AL.CENTER, space_before=6)
                # 3.40in is the IEEE single-column width, and the paper
                # figures are DRAWN at exactly that so nothing is scaled.
                p.add_run().add_picture(path, width=Inches(3.40))
            else:
                tally["image_MISSING"] = tally.get("image_MISSING", 0) + 1
        elif kind == "caption":
            # Captions carry the same markup as body text and were the last
            # place raw \texttt{} leaked through. They also need IEEE
            # numbering, which the .tex gets from \caption and we must supply.
            if last_was_image:
                label = f"Fig. {fig_no}.  "
            else:
                # Only captioned tables are numbered. Six of the seven tabulars
                # are informal in-column displays, as in the .tex.
                tab_no += 1
                label = f"TABLE {tex._roman(tab_no)}.  "
            style.caption_runs(doc, label, tex.runs(payload, cites, refs))
        elif kind == "bib":
            for n, item in enumerate(payload, 1):
                p = style.para(doc, align=AL.JUSTIFY, space_after=2)
                p.paragraph_format.left_indent = Inches(0.22)
                p.paragraph_format.first_line_indent = Inches(-0.22)
                style.emit_runs(
                    p, [(f"[{n}] ", "")] + tex.runs(item, cites, refs),
                    size=style.REF_PT)

    doc.save(OUT)
    _make_reproducible(OUT)
    return len(blocks), tally


def _make_reproducible(path: str) -> None:
    """Repack the .docx so two builds of the same source are byte-identical.

    A .docx is a zip, and python-docx stamps each member with the current
    time, so an unchanged document hashes differently on every build. That
    makes "has the paper changed?" impossible to answer with a checksum. We
    rewrite the archive with a fixed timestamp and a sorted member order,
    which changes nothing a reader sees and makes the output verifiable.
    """
    import shutil
    import zipfile

    fixed = (1980, 1, 1, 0, 0, 0)
    tmp = path + ".repack"
    with zipfile.ZipFile(path) as src:
        names = sorted(src.namelist())
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
            for name in names:
                info = zipfile.ZipInfo(name, date_time=fixed)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                dst.writestr(info, src.read(name))
    shutil.move(tmp, path)


def main() -> int:
    if not os.path.exists(SRC):
        print(f"  source not found: {SRC}", file=sys.stderr)
        return 2
    try:
        n, tally = build()
    except Exception as exc:  # noqa: BLE001 - report and fail loudly
        print(f"  conversion failed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 3
    size_kb = os.path.getsize(OUT) / 1024
    print(f"  wrote {os.path.relpath(OUT, ROOT)}  ({size_kb:.0f} KB)")
    print(f"  {n} blocks converted")
    for k in sorted(tally):
        print(f"    {k:<14} {tally[k]}")
    if tally.get("image_MISSING"):
        print("  WARNING: one or more figures could not be located",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
