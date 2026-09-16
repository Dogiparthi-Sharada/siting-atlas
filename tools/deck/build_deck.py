"""Build the Siting Atlas presentations.

    python tools/deck/build_deck.py                 # both variants
    python tools/deck/build_deck.py --variant v1    # overview only
    python tools/deck/build_deck.py --variant v2    # technical only

v1  overview, plain language, mixed audience (26 slides)
v2  technical supplement, methods audience (30 slides)

Both carry presenter notes. Figures must exist first:
    python tools/figures/build_all.py
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx_kit import new_deck, notes          # noqa: E402
import slides_story as story                  # noqa: E402
import slides_defence as defence              # noqa: E402
import slides_v2_method as m                  # noqa: E402
import slides_v2_results as r                 # noqa: E402
from notes_v1 import NOTES as NOTES_V1        # noqa: E402
from notes_v2 import NOTES as NOTES_V2        # noqa: E402

META = {
    "p1": "Sharada Dogiparthi",
    "p2": "Srilekha Budithi",
    "p3": "Rakshitha Venigalla",
    "instructor": "Surendra Sarnikar, Ph.D.",
}

REQUIRED = [
    "fig01_architecture", "fig03_agent_gates", "fig05_decay",
    "fig08_backtest", "fig10_positioning", "fig11_stakeholders",
    "fig12_scale", "fig13_currency", "fig14_market",
]


def _here(*p):
    """This script's directory, so sibling modules import when run directly."""
    return os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", *p))


def build_v1(fig_dir, out_path):
    """Build the story deck (slides 1-26) and return its path."""
    prs = new_deck()
    slides = [
        story.s01_title(prs, META), story.s02_one_sentence(prs),
        story.s03_problem(prs), story.s04_who_cares(prs, fig_dir),
        story.s05_target(prs), story.s06_circularity(prs),
        story.s07_cannibalisation(prs), story.s08_decay(prs, fig_dir),
        story.s09_gates(prs), story.s10_gates_fig(prs, fig_dir),
        story.s11_portfolio(prs), story.s12_accuracy(prs),
        story.s13_backtest(prs, fig_dir),
        defence.s14_market(prs, fig_dir), defence.s15_novelty(prs),
        defence.s16_not_claiming(prs), defence.s17_limitations(prs),
        defence.s18_currency(prs, fig_dir), defence.s19_feasible(prs),
        defence.s20_scale(prs, fig_dir), defence.s21_data(prs),
        defence.s22_architecture(prs, fig_dir), defence.s23_plan(prs),
        defence.s24_team(prs, META), defence.s25_budget(prs),
        defence.s26_ask(prs),
    ]
    for i, slide in enumerate(slides, start=1):
        if i in NOTES_V1:
            notes(slide, NOTES_V1[i])
    prs.save(out_path)
    return prs, len(slides)


def build_v2(fig_dir, out_path):
    """Build the method-and-results deck (slides v01-v30)."""
    prs = new_deck()
    slides = [
        m.v01_title(prs, META), m.v02_contribution(prs),
        m.v03_positioning(prs, fig_dir), m.v04_questions(prs),
        m.v05_setup(prs), m.v06_estimand_choice(prs), m.v07_hazard(prs),
        m.v08_selection(prs), m.v09_assumptions(prs), m.v10_scm(prs),
        m.v11_inference(prs), m.v12_interference(prs, fig_dir),
        m.v13_w_construction(prs), m.v14_rq2(prs), m.v15_generated(prs),
        m.v16_conformal(prs),
        r.v17_protocol(prs), r.v18_backtest(prs, fig_dir),
        r.v19_robustness(prs), r.v20_cost(prs), r.v21_npv(prs),
        r.v22_portfolio(prs), r.v23_agent_formal(prs),
        r.v24_gates_fig(prs, fig_dir), r.v25_agent_eval(prs),
        r.v26_threats(prs), r.v27_not_identified(prs), r.v28_extensions(prs),
        r.v29_repro(prs), r.v30_close(prs),
    ]
    for i, slide in enumerate(slides, start=1):
        if i in NOTES_V2:
            notes(slide, NOTES_V2[i])
    prs.save(out_path)
    return prs, len(slides)


def main() -> int:
    """Build the requested deck(s) and report where they landed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--figures", default=_here("docs", "figures"))
    ap.add_argument("--outdir", default=_here("docs", "proposal"))
    ap.add_argument("--variant", choices=["v1", "v2", "both"],
                    default="both")
    a = ap.parse_args()

    missing = [n for n in REQUIRED
               if not os.path.exists(os.path.join(a.figures, f"{n}.png"))]
    if missing:
        print(f"[!] missing figures: {', '.join(missing)}")
        print("    run: python tools/figures/build_all.py")
        return 1

    os.makedirs(a.outdir, exist_ok=True)
    targets = []
    if a.variant in ("v1", "both"):
        targets.append(("v1", build_v1,
                        os.path.join(a.outdir, "Siting_Atlas_Deck_v1_"
                                     "overview.pptx")))
    if a.variant in ("v2", "both"):
        targets.append(("v2", build_v2,
                        os.path.join(a.outdir, "Siting_Atlas_Deck_v2_"
                                     "technical.pptx")))

    for name, fn, path in targets:
        _, n = fn(a.figures, path)
        size = os.path.getsize(path) / 1e6
        print(f"  {name}  {os.path.basename(path)}")
        print(f"      {n} slides, {size:.1f} MB, 16:9, presenter notes on all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
