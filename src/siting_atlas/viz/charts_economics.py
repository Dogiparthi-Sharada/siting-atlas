"""L5 — the two figures about WHAT the money buys and HOW FAR it stretches.

``cost_decomposition`` splits cost per STOP, not per parcel, for the reason
recorded in cost.runner: the four components are each charged once per door,
so dividing them by parcels makes the shares sum to about 140%. It also
aggregates with a stops-weighted mean rather than a median. Medians are not
additive — four per-metro component medians do not add up to the per-metro
median total — so a stack built from medians is a bar chart whose segments
lie about their own sum. The stops-weighted mean is additive and is also the
economically correct aggregate: it is total dollars divided by total doors.

``cumulative_coverage`` answers the actual siting question ("how much can I
serve under $X?") and plots two series on ONE axis because both are shares:
the share of ZCTAs and the share of daily parcels. Those two curves apart is
the finding — the cheap ZCTAs are the dense ones, so they carry far more
parcels than their headcount suggests.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .data import COMPONENTS
from .style import (
    BLUE,
    GOOD,
    HUE_SLOTS,
    INK,
    INK_2,
    STACK_SLOTS,
    SURFACE,
    apply_style,
    caption,
    empty_figure,
    recede_axes,
)

_log = get_logger("viz.economics")


def _weighted_components(frame: pd.DataFrame) -> pd.DataFrame:
    """Stops-weighted mean of each cost component, one row per metro.

    Weighting by daily_stops keeps the segments additive (see module
    docstring) and stops a 40-household ZCTA from counting as much as a
    50,000-household one.

    Rows with ANY missing component are dropped up front, which is the same
    trap cost.runner already sprang and fixed. ``Series.sum()`` skips NaN,
    so an un-costed ZCTA left in the frame puts its doors into the
    denominator and no dollars into the numerator: that one segment shrinks
    by a plausible-looking amount, the stack stops adding up to cost per
    stop, and nothing anywhere says so. Dropping the row instead makes every
    segment a mean over the SAME set of ZCTAs, which is the only way the
    four of them are still additive. The pilot has no NaN components today,
    so this normally costs one dropna and nothing else — but "there are no
    NaNs today" is a property of the data, not of this function.
    """
    cols = [col for col, _ in COMPONENTS]
    work = frame.dropna(subset=["daily_stops", *cols]).copy()
    excluded = len(frame) - len(work)
    if excluded:
        # Counted and said out loud, never silently swallowed: a segment
        # computed over fewer ZCTAs than the chart claims is exactly the
        # wrong-but-believable picture this package exists to prevent.
        _log.warning("%d of %d ZCTA(s) have an incomplete cost breakdown and "
                     "are excluded from the decomposition", excluded,
                     len(frame))
    work = work[work["daily_stops"] > 0]
    if work.empty:
        return pd.DataFrame(columns=[c for c, _ in COMPONENTS])

    weights = work["daily_stops"]
    rows = {}
    for metro, grp in work.groupby("metro_label"):
        w = grp["daily_stops"]
        rows[metro] = {col: float((grp[col] * w).sum() / w.sum())
                       for col, _ in COMPONENTS}
    out = pd.DataFrame(rows).T
    out.loc["ALL PILOT METROS"] = {
        col: float((work[col] * weights).sum() / weights.sum())
        for col, _ in COMPONENTS}
    return out


def cost_decomposition(frame: pd.DataFrame, *, title: str | None = None):
    """Stacked bar: where each dollar per stop goes, by metro."""
    apply_style()
    comp = _weighted_components(frame)
    if comp.empty:
        return empty_figure("No ZCTAs with modelled stops in this selection.")

    totals = comp.sum(axis=1)
    # The pooled row is a reference line, not a competitor, so it is pinned
    # to the bottom instead of taking part in the ranking.
    metros = list(totals.drop("ALL PILOT METROS")
                        .sort_values(ascending=False).index)
    order = metros + ["ALL PILOT METROS"]
    comp = comp.loc[order]

    fig, ax = plt.subplots(figsize=(8.8, 0.44 * len(order) + 2.4))
    ypos = np.arange(len(order))
    left = np.zeros(len(order))
    for colour, (col, label) in zip(STACK_SLOTS, COMPONENTS, strict=True):
        vals = comp[col].to_numpy()
        # A 1.6pt surface-coloured edge is the 2px gap between segments; the
        # boundary has to read even when two adjacent hues are similar in
        # print.
        ax.barh(ypos, vals, left=left, height=0.66, color=colour,
                edgecolor=SURFACE, linewidth=1.6, label=label, zorder=3)
        left += vals

    _label_segments(ax, ypos, comp, totals=left)
    ax.set_yticks(ypos)
    ax.set_yticklabels(order, fontsize=8.4, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("Cost per delivery stop ($/day), stops-weighted mean")
    ax.set_title(title or "Where the money goes: driver time at the door "
                          "dominates everywhere", pad=26)
    recede_axes(ax, x_grid=True, y_grid=False)
    # Above the plot, not inside it: the bars fill the axes edge to edge at
    # every metro count, so there is no in-plot corner a legend can occupy
    # without covering a bar.
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.005, 1, 0.06),
              mode="expand", ncol=4, handlelength=1.0, columnspacing=1.0,
              borderaxespad=0)

    for y, total in zip(ypos, left, strict=True):
        ax.text(total * 1.01, y, f"${total:.2f}", va="center", ha="left",
                fontsize=7.8, color=INK_2)
    ax.set_xlim(0, float(left.max()) * 1.13)
    return fig


def _label_segments(ax, ypos, comp: pd.DataFrame, totals) -> None:
    """Percentage labels inside segments wide enough to hold one.

    Only inside — a label that spills onto the neighbouring segment reads as
    belonging to the wrong component, which is worse than no label at all.
    """
    left = np.zeros(len(comp))
    for col, _ in COMPONENTS:
        vals = comp[col].to_numpy()
        for i, (v, x0, tot) in enumerate(zip(vals, left, totals,
                                             strict=True)):
            share = v / tot if tot else 0.0
            # 15% is where the narrowest segment in the pilot still clears
            # the label; below it the number would sit half outside its own
            # block, which reads as belonging to the neighbour.
            if share >= 0.15:
                ax.text(x0 + v / 2, ypos[i], f"{share * 100:.0f}%",
                        ha="center", va="center", fontsize=7.2,
                        color=SURFACE, fontweight="bold", zorder=4)
        left = left + vals


def cumulative_coverage(frame: pd.DataFrame, *, threshold: float | None = None,
                        title: str | None = None):
    """How much of the pilot is servable under a given cost per parcel."""
    apply_style()
    valid = frame.dropna(subset=["cost_per_parcel"]).sort_values(
        "cost_per_parcel")
    if valid.empty:
        return empty_figure("No cost values to accumulate in this selection.")

    cost = valid["cost_per_parcel"].to_numpy()
    zcta_share = np.arange(1, len(cost) + 1) / len(cost) * 100.0
    parcels = valid["daily_parcels"].fillna(0).to_numpy()
    total = parcels.sum()
    parcel_share = (np.cumsum(parcels) / total * 100.0 if total > 0
                    else np.zeros_like(zcta_share))

    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.fill_between(cost, zcta_share, color=BLUE, alpha=0.10, zorder=2)
    ax.plot(cost, zcta_share, color=HUE_SLOTS[0], lw=2.2, zorder=4,
            label=f"Share of ZCTAs (n={len(cost):,})")
    if total > 0:
        ax.plot(cost, parcel_share, color=HUE_SLOTS[1], lw=2.2, zorder=4,
                label=f"Share of daily parcels ({total:,.0f}/day)")

    if threshold is not None:
        _mark_threshold(ax, cost, zcta_share, parcel_share, threshold,
                        has_parcels=total > 0)

    ax.set_xlabel("Cost ceiling ($ per parcel, per day)")
    ax.set_ylabel("Cumulative share servable at or below the ceiling (%)")
    ax.set_ylim(0, 104)
    ax.set_xlim(float(cost.min()) * 0.97, float(cost.max()) * 1.02)
    ax.set_title(title or "How much of the pilot is servable under a cost "
                          "ceiling")
    recede_axes(ax, x_grid=True)
    ax.legend(loc="lower right")

    caption(ax, "The parcel curve sits above the ZCTA curve because the "
                "cheap ZCTAs are the dense ones: a minority of areas "
                "carrying a majority of the volume. That gap is the case "
                "for serving them first.")
    return fig


def _mark_threshold(ax, cost, zcta_share, parcel_share, threshold: float,
                    *, has_parcels: bool) -> None:
    """Drop a rule at the chosen ceiling and state both readings on it."""
    n_under = int((cost <= threshold).sum())
    z = float(zcta_share[n_under - 1]) if n_under else 0.0
    p = float(parcel_share[n_under - 1]) if n_under and has_parcels else 0.0
    ax.axvline(threshold, color=GOOD, lw=1.3, ls=(0, (4, 3)), zorder=5)
    note = (f"at ${threshold:.2f}: {n_under:,} ZCTAs ({z:.0f}%)"
            + (f", {p:.0f}% of parcels" if has_parcels else ""))
    ax.annotate(note, xy=(threshold, 2), xytext=(6, 0),
                textcoords="offset points", ha="left", va="bottom",
                fontsize=8, color=GOOD, fontweight="bold", zorder=6)
    for share, colour in ((z, HUE_SLOTS[0]),
                          (p, HUE_SLOTS[1]) if has_parcels else (None, None)):
        if share is not None:
            ax.plot([threshold], [share], marker="o", markersize=7,
                    color=colour, markeredgecolor=SURFACE,
                    markeredgewidth=1.5, zorder=6)
