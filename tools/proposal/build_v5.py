"""Render the v5 proposal Markdown into Word, reusing the v4 styling kit.

    python tools/proposal/build_v5.py [--src docs/proposal/PROPOSAL_V5.md]
                                      [--out docs/proposal/PROPOSAL_V5.docx]
                                      [--figures docs/figures]

Unlike build_v4.py, which assembles the document from Python section modules,
v5's content lives in Markdown so the .md, the .txt twin and the .docx cannot
drift apart. This script is a renderer, not a source of content.

Figures are embedded from lines of the form

    **Figure 4.** Caption text. (figure: docs/figures/fig08_backtest.png)

which read as ordinary prose in the .md and the .txt. Only figures named that
way are embedded, and a missing PNG fails the build rather than leaving a
silent hole -- same rule as build_v4.py, same reason.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.shared import Pt  # noqa: E402
from docx_kit import (  # noqa: E402
    BLUE,
    INK_2,
    MONO_FONT,
    MUTED,
    add_page_numbers,
    bullets,
    figure,
    new_document,
    para,
    rich,
)

#: A figure reference, e.g. "(figure: docs/figures/fig08_backtest.png)".
FIG_RE = re.compile(r"\s*\(figure:\s*([^)]+?\.png)\)\s*$")

#: Inline emphasis: **bold**, *italic*, `mono`. Order matters -- bold first.
INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")


def _here(*parts: str) -> str:
    """A path relative to the repository root."""
    return os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", *parts))


def _chunks(text: str) -> list[tuple[str, str]]:
    """Split a line of Markdown into (text, style) runs for docx_kit.rich."""
    out: list[tuple[str, str]] = []
    for piece in INLINE_RE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            out.append((piece[2:-2], "b"))
        elif piece.startswith("`") and piece.endswith("`"):
            out.append((piece[1:-1], "m"))
        elif piece.startswith("*") and piece.endswith("*"):
            out.append((piece[1:-1], "i"))
        else:
            out.append((piece, ""))
    return out or [(text, "")]


def _flush(doc, buf: list[str], *, style: str = "body",
           fig_dir: str = "", embedded: list[str] | None = None) -> None:
    """Emit a buffered paragraph and clear the buffer.

    A paragraph whose assembled text is a figure reference becomes an embedded
    image plus its caption. Captions wrap across source lines, so this has to
    happen after the paragraph is joined rather than line by line.
    """
    if not buf:
        return
    text = " ".join(s.strip() for s in buf).strip()
    buf.clear()
    if not text:
        return

    match = FIG_RE.search(text)
    if match and text.startswith("**Figure") and embedded is not None:
        name = os.path.splitext(os.path.basename(match.group(1)))[0]
        caption = FIG_RE.sub("", text).strip().replace("**", "")
        figure(doc, fig_dir, name, caption)
        embedded.append(name)
        return

    if style == "quote":
        rich(doc, _chunks(text), size=10, indent=0.35, space_after=10)
    else:
        rich(doc, _chunks(text), align="j")


def _code(doc, lines: list[str]) -> None:
    """Emit a fenced block verbatim in the mono font, one paragraph."""
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(10)
    pf.space_before = Pt(4)
    pf.left_indent = 0
    run = p.add_run("\n".join(lines))
    run.font.name = MONO_FONT
    run.font.size = Pt(8.5)
    run.font.color.rgb = INK_2


def title_block(doc, lines: list[str]) -> None:
    """The title page: everything above the first '---' in the Markdown."""
    para(doc, "SITING ATLAS", size=30, bold=True, color=BLUE, align="c",
         space_after=4)
    para(doc, "Volume I  |  Last-Mile Delivery", size=13, bold=True,
         color=INK_2, align="c", space_after=18)
    para(doc,
         "Agent-Assisted Spatial Analysis of Sub-24-Hour Delivery Territory "
         "Expansion", size=14, italic=True, align="c", space_after=10)
    para(doc,
         "An open, reproducible model of where private infrastructure gets "
         "built — and who bears the consequences.",
         size=11, color=INK_2, align="c", space_after=26)
    para(doc, "Applied Research Project Proposal, version 5", size=12,
         bold=True, align="c", space_after=22)
    for name in ("P1: Sharada Dogiparthi", "P2: Srilekha Budithi",
                 "P3: Rakshitha Venigalla"):
        para(doc, name, size=11, align="c", space_after=2)
    para(doc, "", space_after=14)
    for line in ("Master of Science in Business Analytics",
                 "California State University, East Bay",
                 "Course Instructor: Surendra Sarnikar, Ph.D.",
                 "September 2026"):
        para(doc, line, size=11, color=INK_2, align="c", space_after=2)
    para(doc, "", space_after=26)
    para(doc,
         "Not affiliated with, endorsed by, or sponsored by Amazon.com, Inc., "
         "Walmart Inc., Costco Wholesale Corporation, or any other operator "
         "analysed. All operator names are used descriptively to identify the "
         "subject of study.",
         size=9, italic=True, color=MUTED, align="c", space_after=0)
    doc.add_page_break()


def render(md: str, fig_dir: str, doc) -> list[str]:
    """Render the Markdown body into `doc`. Returns the figures embedded."""
    lines = md.splitlines()
    # Everything before the first horizontal rule is the title block.
    cut = next(i for i, ln in enumerate(lines) if ln.strip() == "---")
    title_block(doc, lines[:cut])

    embedded: list[str] = []
    buf: list[str] = []
    fence: list[str] | None = None
    quote = False
    pending: list[tuple[str, str]] = []

    def flush_list() -> None:
        if pending:
            bullets(doc, [_chunks(t) for t, _ in pending])
            pending.clear()

    def flush(style: str = "body") -> None:
        _flush(doc, buf, style=style, fig_dir=fig_dir, embedded=embedded)

    for raw in lines[cut + 1:]:
        line = raw.rstrip()

        if line.strip().startswith("```"):
            if fence is None:
                flush("quote" if quote else "body")
                flush_list()
                quote = False
                fence = []
            else:
                _code(doc, fence)
                fence = None
            continue
        if fence is not None:
            fence.append(raw)
            continue

        if not line.strip():
            flush("quote" if quote else "body")
            flush_list()
            quote = False
            continue

        if line.startswith("#"):
            flush("quote" if quote else "body")
            flush_list()
            quote = False
            level = len(line) - len(line.lstrip("#"))
            text = line.lstrip("#").strip()
            doc.add_paragraph(text, style=f"Heading {min(level - 1, 4) or 1}")
            continue

        if line.strip() == "---":
            flush("quote" if quote else "body")
            flush_list()
            quote = False
            continue

        if line.startswith("> "):
            if not quote:
                flush()
                flush_list()
            quote = True
            buf.append(line[2:])
            continue

        if line.lstrip().startswith("- "):
            flush("quote" if quote else "body")
            quote = False
            pending.append((line.lstrip()[2:], ""))
            continue

        if pending:
            # A wrapped continuation of the current bullet.
            text, style = pending[-1]
            pending[-1] = (f"{text} {line.strip()}", style)
            continue

        buf.append(line)

    flush("quote" if quote else "body")
    flush_list()
    return embedded


def main() -> int:
    """Build the document. Non-zero if a referenced figure is missing."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=_here("docs", "proposal",
                                           "PROPOSAL_V5.md"))
    ap.add_argument("--figures", default=_here("docs", "figures"))
    ap.add_argument("--out", default=_here("docs", "proposal",
                                           "PROPOSAL_V5.docx"))
    args = ap.parse_args()

    with open(args.src, encoding="utf-8") as handle:
        md = handle.read()

    wanted = [os.path.splitext(os.path.basename(p))[0]
              for p in FIG_RE.findall(md)]
    missing = [n for n in wanted
               if not os.path.exists(os.path.join(args.figures, f"{n}.png"))]
    if missing:
        print(f"[!] {len(missing)} figure(s) missing from {args.figures}:")
        for name in missing:
            print(f"      {name}.png")
        return 1

    doc = new_document()
    embedded = render(md, args.figures, doc)
    add_page_numbers(doc)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    doc.save(args.out)

    size = os.path.getsize(args.out) / 1e6
    print(f"Built {args.out}")
    print(f"  {size:.1f} MB, {len(embedded)} figures embedded: "
          f"{', '.join(embedded)}")
    print("  NOTE: open in Word and insert a Table of Contents "
          "(References > Table of Contents) - Word builds it from the "
          "heading styles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
