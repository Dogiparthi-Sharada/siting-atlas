"""Assemble Siting Atlas proposal v4 as a Word document with embedded figures.

    python tools/proposal/build_v4.py [--out docs/proposal] [--figures docs/figures]

Figures must be built first:  python tools/figures/build_all.py
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_kit import add_page_numbers, new_document          # noqa: E402
import sections_front as front                               # noqa: E402
import sections_related as related                           # noqa: E402
import sections_core as core                                 # noqa: E402
import sections_methods as methods                           # noqa: E402
import sections_back as back                                 # noqa: E402

META = {
    "p1": "Sharada Dogiparthi",
    "p2": "Srilekha Budithi",
    "p3": "Rakshitha Venigalla",
    "instructor": "Surendra Sarnikar, Ph.D.",
    "date": "September 2026",
}

REQUIRED_FIGURES = [
    "fig01_architecture", "fig02_star_schema", "fig03_agent_gates",
    "fig04_estimand", "fig05_decay", "fig06_portfolio", "fig07_tornado",
    "fig08_backtest", "fig09_conformal_coverage", "fig10_positioning",
    "fig11_stakeholders", "fig12_scale", "fig13_currency", "fig14_market",
]


def _here(*parts):
    """This script's directory, so sibling modules import when run directly."""
    return os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", *parts))


def check_figures(fig_dir: str) -> list[str]:
    """Verify every figure the document embeds exists before building.

    A missing PNG otherwise produces a document with a silent hole in it,
    which is the kind of thing nobody notices until it is printed.
    """
    return [n for n in REQUIRED_FIGURES
            if not os.path.exists(os.path.join(fig_dir, f"{n}.png"))]


def build(fig_dir: str, out_path: str) -> str:
    """Assemble every section into the proposal and save it."""
    doc = new_document()
    front.title_page(doc, META)
    front.executive_summary(doc)
    front.introduction(doc, fig_dir)
    related.related_work(doc, fig_dir)
    core.objectives(doc, fig_dir)
    core.data_section(doc, fig_dir)
    methods.methods(doc, fig_dir)
    back.references(doc)
    back.roles(doc)
    back.timeline(doc)
    back.budget(doc)
    add_page_numbers(doc)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    return out_path


def main() -> int:
    """Build the proposal. Returns non-zero if a figure is missing."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--figures", default=_here("docs", "figures"))
    ap.add_argument("--out", default=_here(
        "docs", "proposal", "Siting_Atlas_Proposal_v4.docx"))
    args = ap.parse_args()

    missing = check_figures(args.figures)
    if missing:
        print(f"[!] {len(missing)} figure(s) missing from {args.figures}:")
        for name in missing:
            print(f"      {name}.png")
        print("    run: python tools/figures/build_all.py")
        return 1

    path = build(args.figures, args.out)
    size = os.path.getsize(path) / 1e6
    print(f"Built {path}")
    print(f"  {size:.1f} MB, {len(REQUIRED_FIGURES)} figures embedded")
    print("  NOTE: open in Word and insert/refresh the Table of Contents "
          "(References > Table of Contents) - Word builds it from the "
          "heading styles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
