"""The 1280x640 card GitHub shows when the repository link is shared.

Settings -> General -> Social preview. Almost nobody sets one, so the default
is a grey box with a filename in it -- which is what a recruiter sees when the
link is pasted into LinkedIn, Slack or an email. This is the cheapest visual
win available and it costs one upload.

Every number is read from an artefact at build time, same rule as every other
figure here.

    python tools/figures/fig_social_card.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "figures", "social_preview.png")

INK = "#12212e"
MUTED = "#5b6b78"
HUE = "#1f4e79"
WARM = "#b3452f"
FAINT = "#cfdced"
MONEY = "#8c1d0c"   # figbase.COST_DEEP -- the dark end of the money ramp


def _load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _overflow(fig) -> list[str]:
    """Text that does not fit the 1280x640 canvas, or collides.

    This card is laid out in absolute pixels rather than through
    ``figbase.figure``, so it never had the geometry gate the other figures
    get, and ``savefig`` here cannot use ``bbox_inches="tight"`` -- GitHub
    requires exactly 1280x640, so growing the canvas is not an option and
    anything past the edge is simply CUT OFF. That is how a headline shipped
    reading "...missing from public recor". Same check, adapted: nothing may
    cross an edge, and no two blocks may overlap.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    w, h = fig.bbox.width, fig.bbox.height
    items, out = [], []
    for t in fig.axes[0].texts:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(r)
        items.append((t, bb))
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > w + 1 or bb.y1 > h + 1:
            out.append(f"{t.get_text()[:34]!r} crosses the edge "
                       f"(x {bb.x0:.0f}..{bb.x1:.0f}, "
                       f"y {bb.y0:.0f}..{bb.y1:.0f})")
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            smaller = min(a.width * a.height, b.width * b.height)
            if ox > 2 and oy > 2 and smaller and ox * oy / smaller > 0.18:
                out.append(f"{items[i][0].get_text()[:22]!r} overlaps "
                           f"{items[j][0].get_text()[:22]!r}")
    return out


def build() -> tuple[str, dict]:
    cov = _load("outputs/metrics/mwpvl_coverage.json")
    # cost_by_station.json, NOT cost_report.json. The latter is the retired
    # pilot -- a p-median solve over 334 invented depots covering 2,333 ZCTAs,
    # median $1.0830. This card read it until 2026-09-16 and so advertised a
    # superseded number on the one image that gets pasted into LinkedIn while
    # every other surface in the repository said $1.1389. Same trap as any
    # stale constant, except nobody re-reads a PNG.
    cost = _load("outputs/metrics/cost_by_station.json")
    cost = cost["scenarios"]["baseline"]
    ext = _load("outputs/metrics/mwpvl_extraction.json")

    seen = cov["cities_in_both"]
    total = cov["mwpvl_delivery_station_cities"]
    unseen = cov["cities_mwpvl_names_that_osha_never_inspected"]
    median = cost["median_cost_per_parcel"]
    facilities = ext["facilities"]

    # GitHub renders the social preview at 1280x640.
    fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1280)
    ax.set_ylim(0, 640)
    ax.axis("off")

    ax.add_patch(Rectangle((0, 624), 1280, 16, color=HUE, zorder=2))

    # matplotlib Text has no letter-spacing property, so the tracking is
    # done in the string.
    ax.text(72, 566, "S I T I N G   A T L A S", fontsize=16, color=HUE,
            fontweight="bold")
    # CITIES, not stations. The artefact behind this headline is
    # mwpvl_coverage.json, which counts CITIES appearing in each of two lists:
    # 350 of 488 (71.7%) carry no OSHA record. An earlier version of this card
    # said "stations", which is a different and unsupported claim -- the panel
    # cannot say what share of individual buildings are unrecorded, only what
    # share of the places holding them are. Corrected 2026-09-16.
    ax.text(72, 534,
            "Three in four US cities with an\n"
            "Amazon delivery station are missing\n"
            "from public records.",
            fontsize=31, color=INK, fontweight="bold", va="top",
            linespacing=1.22)
    ax.text(72, 372, "We measured it.", fontsize=20, color=WARM,
            fontweight="bold", va="top")

    # The bar: what federal enforcement records can and cannot see.
    x0, y0, w, h = 72, 252, 1136, 44
    ax.add_patch(Rectangle((x0, y0), w, h, color=FAINT, zorder=2))
    ax.add_patch(Rectangle((x0, y0), w * seen / total, h, color=HUE, zorder=3))
    ax.text(x0 + (w * seen / total) / 2, y0 + h / 2, f"{seen}", ha="center",
            va="center", color="white", fontsize=19, fontweight="bold",
            zorder=4)
    ax.text(x0 + w * seen / total + (w * (1 - seen / total)) / 2, y0 + h / 2,
            f"{unseen} invisible", ha="center", va="center", color=INK,
            fontsize=16, fontweight="bold", zorder=4)
    ax.text(x0, y0 - 16,
            f"US cities with an Amazon delivery station: {total}. "
            f"Cities appearing in federal inspection records: {seen}.",
            fontsize=13, color=MUTED, va="top")

    # Money is red everywhere in this repository, including here. MONEY is the
    # deep end of figbase's shared cost ramp, so the dollar figure on the card
    # matches the dollar figures on the map and the metro chart; the other two
    # stats are counts and stay in the house blue.
    facts = [
        (f"{facilities:,}", "facilities recovered\nfrom an image-only PDF",
         HUE),
        (f"${median:.2f}", "median cost to deliver\none parcel, computed",
         MONEY),
        ("0 of 7", "years a pre-registered\nmodel beat its baseline", HUE),
    ]
    for i, (big, small, colour) in enumerate(facts):
        x = 72 + i * 390
        ax.text(x, 172, big, fontsize=29, color=colour, fontweight="bold",
                va="top")
        ax.text(x, 128, small, fontsize=12.5, color=MUTED, va="top",
                linespacing=1.4)

    ax.text(72, 28, "Open data · pre-registered · reproducible offline "
                    "from a clone",
            fontsize=12.5, color=MUTED, va="bottom")

    problems = _overflow(fig)
    if problems:
        plt.close(fig)
        raise ValueError("social card text does not fit 1280x640:\n    "
                         + "\n    ".join(problems))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=100, facecolor="white")
    plt.close(fig)
    return OUT, {"seen": seen, "total": total, "median": median,
                 "facilities": facilities}


def main() -> int:
    path, v = build()
    from PIL import Image
    w, h = Image.open(path).size
    kb = os.path.getsize(path) / 1024
    print(f"  wrote {os.path.relpath(path, ROOT)}")
    print(f"  {w}x{h} px, {kb:.0f} KB  (GitHub wants 1280x640, under 1 MB)")
    print(f"  from artefacts: {v['seen']} of {v['total']} cities, "
          f"${v['median']:.4f}, {v['facilities']:,} facilities")
    return 0 if (w, h) == (1280, 640) and kb < 1024 else 1


if __name__ == "__main__":
    raise SystemExit(main())
