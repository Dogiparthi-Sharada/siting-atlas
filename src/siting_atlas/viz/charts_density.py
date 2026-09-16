"""L5 — the two figures about WHERE cost sits: density, and by metro.

These are the charts that argue the model's central claim, so both are built
to survive a hostile reading.

``cost_vs_density`` is log-x because stop density spans roughly six orders of
magnitude across the pilot; on a linear axis 95% of the ZCTAs collapse onto
the y-axis and the 1/sqrt(delta) curve looks like a right angle. The
horizontal floor line is the point of the figure: local travel falls without
limit as density rises, but service time and the van lease do not, so cost
per parcel flattens onto a floor no amount of density can beat.

``cost_by_metro`` is a box plot ordered by median, not a bar of means. A mean
would hide that the expensive tail inside New York is wider than the whole
distribution of Miami, and the tail is the part a siting decision lives in.

Both return a Figure and never raise on an empty or all-NaN selection — the
dashboard filters interactively, and a filter that selects nothing must not
crash the app.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from . import data as cost_data
from .style import (
    AXIS,
    BLUE,
    CLOUD,
    CRITICAL,
    HUE_SLOTS,
    INK,
    INK_2,
    MUTED,
    SURFACE,
    apply_style,
    caption,
    empty_figure,
    recede_axes,
)

_log = get_logger("viz.density")


def _plottable(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows a log-x scatter can actually draw.

    A ZCTA with zero land area yields infinite density and one with no
    modelled stops yields zero; both are legitimate model output and both are
    undefined on a log axis, so they are dropped here and counted, rather
    than silently swallowed by matplotlib as a blank gap.
    """
    keep = frame.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["stop_density_per_sqmi", "cost_per_parcel"])
    return keep[keep["stop_density_per_sqmi"] > 0]


def _default_highlight(frame: pd.DataFrame, n: int = 3) -> list[str]:
    """The metros to spend hue on: the largest by ZCTA count.

    Capped at three by the all-pairs colour-vision gate (see viz.style).
    Largest-by-count rather than most-extreme, so the coloured points are a
    visible mass inside the cloud instead of a handful of dots nobody can
    find.
    """
    counts = frame["metro_label"].value_counts()
    return list(counts.head(n).index)


def cost_vs_density(frame: pd.DataFrame, *, highlight: list[str] | None = None,
                    title: str | None = None):
    """Cost per parcel against stop density, log-x, with the cost floor."""
    apply_style()
    pts = _plottable(frame)
    if pts.empty:
        return empty_figure("No ZCTAs with a positive stop density in this "
                            "selection.")

    chosen = [m for m in (highlight if highlight is not None
                          else _default_highlight(pts))
              if m in set(pts["metro_label"])][:len(HUE_SLOTS)]

    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    rest = pts[~pts["metro_label"].isin(chosen)]
    ax.scatter(rest["stop_density_per_sqmi"], rest["cost_per_parcel"], s=7,
               c=CLOUD, alpha=0.55, linewidths=0, zorder=2,
               label=f"Other pilot ZCTAs (n={len(rest):,})")
    for colour, metro in zip(HUE_SLOTS, chosen, strict=False):
        sub = pts[pts["metro_label"] == metro]
        ax.scatter(sub["stop_density_per_sqmi"], sub["cost_per_parcel"], s=13,
                   c=colour, alpha=0.85, linewidths=0.4, edgecolors=SURFACE,
                   zorder=3, label=f"{metro} (n={len(sub):,})")

    _draw_floor(ax, pts)
    ax.set_xscale("log")
    ax.set_xlabel("Stop density (delivery stops per square mile of land, "
                  "log scale)")
    ax.set_ylabel("Cost to serve ($ per parcel, per day)")
    ax.set_title(title or "Density sets the cost floor, and the return to "
                          "density is only 1/sqrt")
    recede_axes(ax, x_grid=True)
    ax.legend(loc="upper right", markerscale=1.6, handletextpad=0.4)

    caption(ax, "Local travel per stop is k / sqrt(density), so doubling "
                "density cuts it by 29%, not 50% — and it is already small "
                "where density is high. Nothing can go below the dashed "
                "line.")
    return fig


def _draw_floor(ax, pts: pd.DataFrame) -> None:
    """The asymptote: the per-parcel cost that no density can remove.

    Service time and the vehicle lease are charged per stop regardless of how
    close the next door is, so they set a hard floor. Computed from the
    frame's own columns rather than from cost.params, so the line describes
    the file that was loaded.

    The MINIMUM of the per-row bound, not its median. A median is not a
    floor: half the rows have a lower bound below it, so on the pilot table
    99 real ZCTAs plotted underneath a dashed line captioned "Nothing can go
    below" (median 0.9489, true minimum 0.8518). A chart that contradicts
    its own annotation teaches the reader to distrust every other annotation
    on it, so the line is now the smallest bound in the frame — which every
    plotted point genuinely clears.
    """
    ratio = cost_data.parcels_per_stop(pts)
    if not np.isfinite(ratio) or ratio <= 0:
        return
    floor = float(
        ((pts["cost_service_time"] + pts["cost_vehicle"]) / ratio).min())
    ax.axhline(floor, color=CRITICAL, lw=1.3, ls=(0, (5, 3)), zorder=4)
    # Anchored at the left edge: the sparse, low-density corner is the one
    # region of this scatter that is empty at every scenario, so the label
    # cannot land on top of the cloud when the parameters change.
    ax.annotate(f"fixed-cost floor  ${floor:.2f}/parcel "
                "(service time + vehicle lease)",
                xy=(0.012, floor), xycoords=("axes fraction", "data"),
                xytext=(0, 5), textcoords="offset points",
                ha="left", va="bottom", fontsize=7.6, color=CRITICAL)


def cost_by_metro(frame: pd.DataFrame, *, title: str | None = None):
    """Cost distribution per metro, boxes ordered by median."""
    apply_style()
    valid = frame.dropna(subset=["cost_per_parcel"])
    order = cost_data.metro_order(valid)
    series = [valid.loc[valid["metro_label"] == m,
                        "cost_per_parcel"].to_numpy()
              for m in order]
    # Filter the PAIRS, never the two lists one after the other. Shrinking
    # `series` first and then zipping it back against the full `order` pairs
    # metro i with the i-th SURVIVING series, so an empty metro anywhere but
    # the end drops the LAST label instead of the empty one and every box
    # below it is labelled with its neighbour's name. Nothing raises and the
    # chart looks perfectly ordinary; it is simply about different metros
    # than it says it is.
    kept = [(m, s) for m, s in zip(order, series, strict=True) if s.size]
    order = [m for m, _ in kept]
    series = [s for _, s in kept]
    if not series:
        return empty_figure("No cost values to summarise in this selection.")

    fig, ax = plt.subplots(figsize=(8.6, 0.46 * len(order) + 2.1))
    bp = ax.boxplot(series, orientation="horizontal", patch_artist=True,
                    widths=0.62, showfliers=True, whis=(5, 95),
                    flierprops={"marker": ".", "markersize": 2.2,
                                "markerfacecolor": MUTED,
                                "markeredgecolor": "none", "alpha": 0.5},
                    medianprops={"color": SURFACE, "linewidth": 1.6},
                    whiskerprops={"color": AXIS, "linewidth": 1.0},
                    capprops={"color": AXIS, "linewidth": 1.0})
    for patch in bp["boxes"]:
        patch.set(facecolor=BLUE, edgecolor=SURFACE, linewidth=1.4,
                  alpha=0.92)

    ax.set_yticks(range(1, len(order) + 1))
    ax.set_yticklabels([f"{m}  (n={len(valid[valid.metro_label == m]):,})"
                        for m in order], fontsize=8.4, color=INK)
    ax.set_xlabel("Cost to serve ($ per parcel, per day)")
    ax.set_title(title or "Cost to serve by metro, cheapest median first")
    recede_axes(ax, x_grid=True, y_grid=False)
    ax.invert_yaxis()

    # Direct median labels, in a reserved gutter past the data rather than
    # beside each box: reading a median off a whisker plot by eye is exactly
    # the error these figures exist to remove, but a label placed next to a
    # box lands on the box as soon as the distribution shifts.
    hi = float(valid["cost_per_parcel"].max())
    lo = float(valid["cost_per_parcel"].min())
    # A one-ZCTA selection makes lo == hi, and a zero-width xlim is a
    # singular transform: matplotlib warns and invents its own limits, which
    # would drop the gutter off the canvas.
    span = max(hi - lo, max(abs(hi), 1.0) * 0.1)
    gutter = hi + span * 0.06
    ax.set_xlim(lo - span * 0.03, hi + span * 0.15)
    ax.text(gutter, 0.35, "median", fontsize=7.4, color=MUTED, ha="left",
            va="center", fontweight="bold")
    for i, metro in enumerate(order, start=1):
        med = float(np.median(valid.loc[valid.metro_label == metro,
                                        "cost_per_parcel"]))
        ax.text(gutter, i, f"${med:.2f}", fontsize=8, color=INK_2,
                ha="left", va="center")

    caption(ax, "Box is the interquartile range; whiskers reach the 5th and "
                "95th percentile; each dot beyond them is one ZCTA in the "
                "extreme 5% — the tail a siting decision actually lives in.",
            y=-0.42 / max(len(order), 4) * 4, h=0.60 / max(len(order), 4))
    return fig
