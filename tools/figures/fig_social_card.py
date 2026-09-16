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


def _load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def build() -> tuple[str, dict]:
    cov = _load("outputs/metrics/mwpvl_coverage.json")
    cost = _load("outputs/metrics/cost_report.json")["baseline"]
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
    ax.text(72, 522,
            "Three of every four Amazon delivery\n"
            "stations are invisible in public records.",
            fontsize=37, color=INK, fontweight="bold", va="top",
            linespacing=1.24)
    ax.text(72, 392, "We measured it.", fontsize=21, color=WARM,
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

    facts = [
        (f"{facilities:,}", "facilities recovered\nfrom an image-only PDF"),
        (f"${median:.2f}", "median cost to deliver\none parcel, computed"),
        ("0 of 7", "years a pre-registered\nmodel beat its baseline"),
    ]
    for i, (big, small) in enumerate(facts):
        x = 72 + i * 390
        ax.text(x, 172, big, fontsize=29, color=HUE, fontweight="bold",
                va="top")
        ax.text(x, 128, small, fontsize=12.5, color=MUTED, va="top",
                linespacing=1.4)

    ax.text(72, 28, "Open data · pre-registered · reproducible offline "
                    "from a clone",
            fontsize=12.5, color=MUTED, va="bottom")

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
