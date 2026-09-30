"""National map: the whole network, and what it costs where it clusters.

Two layers. Every geocoded delivery station in the facility panel is one
small faint dot -- coverage, unlabelled, 501 of them. Over that, the metros
with the most costed stations are drawn as bubbles whose **area is the number
of stations** and whose **colour is the median cost to put one parcel on a
doorstep** there. Only the extremes are named.

What this replaces, and why
---------------------------
The previous version drew ten rings, one per metro in a p-median cost model
over 334 invented depots, and every ring was labelled. That model is retired.
The current one prices 8,037 ZIP-code areas against the operator's real
stations, so a cost now exists in 174 metros rather than ten, and the old
form breaks twice: ten labelled rings is now a misleading crop, and 174 rings
is a mesh.

Three choices follow, and a reader is entitled to see them stated.

**Sizing by station count is not decoration.** New York holds 33 stations and
the smallest metro drawn holds five. A ring per point hid that; it drew an
80-station metro and a 2-station metro identically. Area carries the count,
which is the one thing about a metro this map can state without a second
artefact.

**One sequential hue, light to dark, with a colourbar.** Cost is magnitude on
a single measure. A rainbow would imply categories and a ring per point would
imply none. The scale runs over the drawn metros' own range so the contrast
is spent where the data is.

**About eight labels, chosen by rule.** The four cheapest metros, the four
dearest, and the largest if it is not already among them -- so the label set
is derived, not curated, and the bubble whose size is the headline is named.
Positions are searched at build time against everything else already on the
canvas rather than hand-tuned, and figbase's geometry gate rules on the
result.

Kept from the previous version
------------------------------
**Fallback coordinates are NOT drawn.** ``geocoded_expanded.csv`` carries
``fallback_latitude``/``fallback_longitude`` for the rows the Census geocoder
could not match to a street address; those are ZCTA centroids. At this scale
their error would be invisible -- a ZCTA is a few miles across, an inch of
this map is 250 -- so the case for including them is real. They are excluded
anyway: a mark should mean one thing, and here it means "resolved to a street
segment". The cost model excludes them for a harder reason, which is that a
ZCTA centroid puts a depot in the middle of its own catchment and drives the
line haul to zero.

**Alaska, Hawaii and Puerto Rico are excluded, not inset.** Four geocoded
facilities (two AK, two HI) fall outside the viewport; Puerto Rico's single
record has no street-level match and was already out. An inset for four dots
is more furniture than information, so the footnote states the count instead,
computed at build time.

**State outlines are derived, not fetched.** ``cartopy`` is absent, modern
``geopandas`` bundles no Natural Earth data and PyPI is unreachable here, so
the basemap is built from the TIGER ZCTA shapefile and the Census
ZCTA-to-county file already on disk. ``tools/figures/usboundary.py`` has the
method and its limits; it is an approximation good to a few miles.

**Projection.** Albers equal-area conic on a unit sphere, standard USA
Contiguous parameters. Every plotted value -- coordinate, count and cost --
is read at build time.

    python tools/figures/fig_national_map.py
"""

from __future__ import annotations

import contextlib
import math
import os
import sys

import numpy as np
import pandas as pd
from matplotlib.colors import Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import costmetros as cm  # noqa: E402
import figbase as fb  # noqa: E402
import maplabels as ml  # noqa: E402
from usboundary import albers, load_conus, project  # noqa: E402

ROOT = cm.ROOT
FACIL = "data/external/facility_panel/geocoded_expanded.csv"
OUT = "docs/figures/hero_national_map.png"

WIDTH = 10.0
HEIGHT = 7.05

#: The basemap. Deliberately a cool, desaturated grey-blue so it never
#: competes with the red cost ramp -- the land is the stage, not a series.
#: Strengthened on 2026-09-16: the first version was so pale that the state
#: lines vanished at README display width, and a map whose geography you
#: cannot read is a scatter plot with a decorative background.
LAND = "#e4eaf0"      # was #eef2f5 -- a shade deeper so the coast reads
BORDER = "#9aabbb"    # was #dce3e9 then #b9c6d2 -- state lines read
COAST = "#8d9eae"     # was #bcc8d3 -- the national outline anchors the shape
DOT = "#5b708a"

#: The shared money ramp, defined once in ``figbase`` and imported by every
#: figure that encodes dollars. It used to be declared here as its own
#: ``LinearSegmentedColormap``, which meant the map and the metro dot plot
#: each owned a red and only agreed by accident.
COST_CMAP = fb.cost_cmap()

#: Points of marker area per station. A bubble's area is its station count;
#: the constant only sets how big "one station" is on a 10-inch canvas.
AREA_PER_STATION = 13.0

# ------------------------------------------------------------------- data

def load_dots(box):
    """Geocoded stations inside the viewport, plus the counts to report.

    ``box`` is the lower-48 bounding box taken from the derived landmass, so
    the viewport is not a typed-in guess either.
    """
    w, s, e, n = box
    d = pd.read_csv(os.path.join(ROOT, FACIL))
    geo = d[d["latitude"].notna() & d["longitude"].notna()]
    inside = (geo["longitude"].between(w, e)
              & geo["latitude"].between(s, n))
    counts = {
        "rows": len(d),
        "geocoded": len(geo),
        "drawn": int(inside.sum()),
        "offmap": int((~inside).sum()),
        "offmap_states": sorted(geo.loc[~inside, "claimed_state"].unique()),
    }
    return geo[inside], counts


def load_bubbles():
    """The metros to draw, the whole-run facts, and an integrity check."""
    j, sc = cm.report()
    st = cm.stations()
    metros = cm.by_metro(st)
    sel = cm.largest(metros, cm.MIN_WIDE)
    facts = {
        "run_id": j["run_id"],
        "catchment": j["catchment_miles"],
        "fallback": j["stations"]["excluded_zcta_centroid_fallback"],
        "geocoded": j["stations"]["geocoded_used"],
        "uncosted": j["coverage"]["stations_with_no_zcta"],
        "hh_share": j["coverage"]["costed_household_share"],
        "zctas": sc["zctas"],
        "stations": len(st),
        "metros": len(metros),
        "shown": int(sel["stations"].sum()),
        "national": float(st["cost_per_parcel_median"].median()),
    }
    return sel, facts


def label_rows(sel, n_end: int = 4) -> list[int]:
    """The extremes by cost, plus the largest metro if it is not one.

    ``sel`` is ordered by cost and carries a 0..n-1 index, so these are
    positions as well as labels.
    """
    idx = list(range(n_end)) + list(range(len(sel) - n_end, len(sel)))
    big = int(sel["stations"].idxmax())
    if big not in idx:
        idx.append(big)
    return idx


# ------------------------------------------------------------------- draw

@contextlib.contextmanager
def _type_scale(title, sub):
    """Borrow figbase.titles() at hero sizes, then put it back.

    figbase's point sizes are set for an IEEE column. This is a README hero
    ten inches wide; at 8.5pt the title would be a whisper. The globals are
    restored so importing this module cannot shrink anyone else's figure.
    """
    old = (fb.PT_TITLE, fb.PT_SUB)
    fb.PT_TITLE, fb.PT_SUB = title, sub
    try:
        yield
    finally:
        fb.PT_TITLE, fb.PT_SUB = old


def _pad(v, frac=0.02):
    lo, hi = float(np.min(v)), float(np.max(v))
    m = (hi - lo) * frac
    return lo - m, hi + m


def _radius(n: int) -> float:
    """Marker radius in points for a bubble of ``n`` stations."""
    return math.sqrt(n * AREA_PER_STATION / math.pi)


def bubble_labels(fig, ax, sel, mx, my):
    """Hand the extremes to the placer in maplabels, with their radii."""
    rows = label_rows(sel)
    text = {i: (f"{cm.short(sel['metro'].iloc[i])}  "
                f"${sel['median'].iloc[i]:.2f}") for i in rows}
    radii = [_radius(int(n)) for n in sel["stations"]]
    placed = ml.place(fig, ax, np.column_stack([mx, my]), radii, text,
                      color=fb.INK)
    return [(cm.short(sel["metro"].iloc[i]), ha, va, pen)
            for i, ha, va, pen in placed]


def draw(dots, counts, sel, facts, states, nation):
    fig, ax = fb.figure(WIDTH, HEIGHT)
    n_lab = len(label_rows(sel))

    with _type_scale(16.0, 9.5):
        low = fb.titles(
            fig,
            "We know where the network is. "
            "Now we know what it costs.",
            f"{facts['geocoded']:,} Amazon delivery stations geocoded to a "
            f"street address, of {counts['rows']:,} in the panel — one faint "
            f"dot each. Over them, the {len(sel)} largest metros,\nwhich "
            f"hold half the network: bubble area is the metro's station "
            f"count, colour is the median cost to put one parcel on a "
            f"doorstep there.\nThe four cheapest, the four dearest and the "
            f"largest are labelled; the other {len(sel) - n_lab} are not.",
            pad=0.028)
    fig.subplots_adjust(top=low - 0.030, bottom=0.085, left=0.0, right=1.0)

    nation.plot(ax=ax, facecolor=LAND, edgecolor="none", zorder=1)
    states.boundary.plot(ax=ax, color=BORDER, linewidth=1.15, zorder=2)
    nation.boundary.plot(ax=ax, color=COAST, linewidth=1.7, zorder=3)

    fx, fy = albers(dots["longitude"].to_numpy(), dots["latitude"].to_numpy())
    ax.scatter(fx, fy, s=9.5, c=DOT, alpha=0.75, linewidths=0, zorder=4)

    norm = Normalize(float(sel["median"].min()), float(sel["median"].max()))
    mx, my = albers(sel["station_lon"].to_numpy(),
                    sel["station_lat"].to_numpy())
    sizes = sel["stations"].to_numpy() * AREA_PER_STATION
    ax.scatter(mx, my, s=sizes, c=sel["median"], cmap=COST_CMAP, norm=norm,
               edgecolors="white", linewidths=1.1, zorder=6)

    ax.set_xlim(*_pad(nation.total_bounds[[0, 2]]))
    ax.set_ylim(*_pad(nation.total_bounds[[1, 3]]))
    ax.set_aspect("equal")
    ax.axis("off")

    _colourbar(fig, ax, norm, facts)
    _size_key(ax, sel)
    _footnote(fig, counts, facts)

    return fig, bubble_labels(fig, ax, sel, mx, my)


def _colourbar(fig, ax, norm, facts):
    """A horizontal key, ticked at the ends and at the network median.

    Three ticks, not five: the bar is 1.4in wide and the reader needs the
    range and where the middle of the network sits, not a ruler. It sits in
    the bottom-left, which on an Albers lower-48 is ocean and northern
    Mexico -- the one corner of this map with nothing to say.
    """
    cax = ax.inset_axes([0.015, 0.145, 0.145, 0.018])
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    cax.imshow(grad, aspect="auto", cmap=COST_CMAP,
               extent=(norm.vmin, norm.vmax, 0, 1))
    cax.set_yticks([])
    for s in cax.spines.values():
        s.set_color("#c9d2da")
        s.set_linewidth(0.6)
    ticks = [norm.vmin, facts["national"], norm.vmax]
    cax.set_xticks(ticks)
    cax.set_xticklabels([f"${v:.2f}" for v in ticks])
    cax.tick_params(colors=fb.MUTED, labelsize=8.0, length=2.0, pad=1.5,
                    width=0.6, color="#c9d2da")
    cax.set_xlim(norm.vmin, norm.vmax)
    ax.annotate("median cost per parcel", (0.015, 0.163),
                xycoords="axes fraction", xytext=(0, 5),
                textcoords="offset points", fontsize=8.6, color=fb.INK,
                ha="left", va="bottom", zorder=9)
    ax.annotate("middle tick: the network median", (0.015, 0.145),
                xycoords="axes fraction", xytext=(0, -13),
                textcoords="offset points", fontsize=7.4, color=fb.MUTED,
                ha="left", va="top", zorder=9)


def _size_key(ax, sel):
    """Two bubbles, the smallest and largest drawn, with their counts.

    Beside the colourbar rather than under it: stacking the two keys needs
    more vertical room than the empty corner has, and the footnote owns the
    space below.
    """
    lo, hi = int(sel["stations"].min()), int(sel["stations"].max())
    r_hi = _radius(hi)
    y = 0.145
    for k, n in enumerate((lo, hi)):
        x = 0.232 + k * 0.062
        ax.scatter([x], [y], s=n * AREA_PER_STATION,
                   transform=ax.transAxes, facecolors="none",
                   edgecolors=fb.MUTED, linewidths=0.9, zorder=9,
                   clip_on=False)
        ax.annotate(f"{n}", (x, y), xycoords="axes fraction",
                    xytext=(0, -r_hi - 5), textcoords="offset points",
                    fontsize=8.0, color=fb.MUTED, ha="center", va="top",
                    zorder=9)
    ax.annotate("stations in the metro", (0.212, y), xycoords="axes fraction",
                xytext=(0, r_hi + 5), textcoords="offset points",
                fontsize=8.6, color=fb.INK, ha="left", va="bottom", zorder=9)


def _footnote(fig, counts, facts):
    off = ", ".join(counts["offmap_states"])
    fig.text(
        0.0, 0.008,
        f"One dot per station at its geocoded street address. The "
        f"{facts['fallback']} addresses the Census geocoder could not match "
        f"are not drawn — the panel offers only a ZIP-code centroid for "
        f"those, and a\ncentroid would put a depot inside its own catchment. "
        f"{counts['offmap']} stations outside the lower 48 ({off}) are "
        f"excluded, not inset. {facts['uncosted']} of the "
        f"{facts['geocoded']} stations have no ZIP-code area within the\n"
        f"{facts['catchment']:.0f}-mile catchment and carry no cost, so a "
        f"bubble sizes and colours only the {facts['stations']} that do: "
        f"{facts['shown']} of them here, in {facts['metros']} metros in all. "
        f"Costs are {cm.period_label()} medians over\n{facts['zctas']:,} "
        f"ZIP-code areas holding {facts['hh_share']:.1%} of US households. "
        f"Albers equal-area; outlines derived from TIGER ZCTAs. Cost run "
        f"{facts['run_id']}.",
        fontsize=7.0, color=fb.MUTED, va="bottom", ha="left",
        linespacing=1.65)


# ------------------------------------------------------------------- main

def main() -> int:
    states, nation = load_conus()
    dots, counts = load_dots(tuple(nation.total_bounds))
    sel, facts = load_bubbles()
    if counts["geocoded"] != facts["geocoded"]:
        raise SystemExit(
            f"the panel has {counts['geocoded']} geocoded stations but the "
            f"cost run used {facts['geocoded']}; the dot layer and the "
            "bubble layer would be describing different networks")

    fig, placed = draw(dots, counts, sel, facts,
                       project(states), project(nation))
    path = os.path.join(ROOT, OUT)
    problems = fb.save(fig, path, placed_width=WIDTH)

    print(f"  wrote {OUT}  ({os.path.getsize(path) / 1e6:.2f} MB)")
    print(f"  panel {counts['rows']} rows, {counts['geocoded']} geocoded, "
          f"{counts['drawn']} drawn, {counts['offmap']} off-map "
          f"({', '.join(counts['offmap_states'])}), "
          f"{facts['fallback']} fallback-only (excluded)")
    print(f"  bubbles {len(sel)} metros of {facts['metros']}, "
          f"{facts['shown']} of {facts['stations']} costed stations "
          f"({facts['shown'] / facts['stations']:.1%}), "
          f"{facts['zctas']:,} ZCTAs; {len(states)} state outlines")
    print(f"  colour {sel['median'].min():.4f} "
          f"({cm.short(sel['metro'].iloc[0])}) to "
          f"{sel['median'].max():.4f} "
          f"({cm.short(sel['metro'].iloc[-1])}), "
          f"size {sel['stations'].min()} to {sel['stations'].max()}")
    print(f"  labels {len(placed)}: "
          + ", ".join(f"{n}->{h}/{v}{'*' if p else ''}"
                      for n, h, v, p in placed))
    print(f"  geometry gate: {problems or 'clean'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
