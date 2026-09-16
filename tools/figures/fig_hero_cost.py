"""The repository's hero figure: what it costs to deliver one parcel.

Answers the second of the project's two questions on sight, for a reader who
will not open anything else. Every value is read from
``outputs/tables/cost_by_station_2023q4_baseline.parquet`` and
``outputs/metrics/cost_by_station.json`` at build time; nothing is typed by
hand. That constraint is not decorative -- this project previously shipped a
figure with nine hand-entered values and a fabricated confidence band, and the
rule since is that a figure either reads its numbers from an artefact or it
carries none.

What changed, and the decision it forced
----------------------------------------
The cost model used to run on a p-median solve over ten metros. It now runs
on the operator's 501 real delivery stations, which put a cost on 8,037 ZCTAs
in 174 metros. **A 174-row dot plot is not a hero figure**, so something had
to be dropped. The two honest forms were:

* the distribution of all 481 station medians, extremes annotated -- complete,
  but it names no place, and the first question a reader brings to this chart
  is "what about here?";
* a subset of metros, named, with their spread.

The subset wins for a README, and the price of winning is stated on the
figure: the subtitle gives how many metros are drawn of 174 and what share of
the 481 stations they carry, and the footnote gives the full-network extremes
so the reader knows what the crop hides. ``fig_paper.py`` takes the other
branch at IEEE column width, where names do not fit.

**Which metros, and why not "the top 20".** Selection is by a threshold on
station count, not by a rank -- see ``costmetros``. Eight metros are tied at
five stations, so any "top 20" or "top 25" decides between them on sort order.
``>= 5`` stations lands on a clean 25.

**Spread is across stations, not ZCTAs.** The row is a metro whose weight is
its station count, so the bar is the interquartile range of that metro's
station medians. Min-max was rejected: single rural ZCTAs run to several
times their own metro's median and compress everything else into a smear.

* One series, so no legend: the title names the quantity.
* One hue, because this is magnitude on a single measure.

Colour
------
The dots carry ``figbase``'s shared money ramp -- the same object the national
map uses, not a second red that happens to look similar. A reader who has
learned "pale is cheap, dark is dear" from the map two inches above arrives
here already able to read it.

Colour here is REDUNDANT, deliberately. Every row's dollar value is also
printed at the right-hand end and the rows are sorted by it, so nothing is
encoded in colour alone -- the figure is unchanged in greyscale and for a
reader with a red-green deficiency. The ramp is doing emphasis, not work.

It starts at ``figbase.COST_FLOOR`` rather than at the ramp's pale end: a
7.5pt dot filled with #fde4dd is invisible on white, and the cheapest metro is
exactly the one a reader looks for first.
"""

from __future__ import annotations

import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import costmetros as cm  # noqa: E402
import figbase as fb  # noqa: E402

OUT = "docs/figures/fig_cost_per_parcel_by_metro.png"

WIDTH = 9.6
HEIGHT = 7.0


@contextlib.contextmanager
def _type_scale(title, sub):
    """figbase's point sizes are set for an IEEE column; this is a README."""
    old = (fb.PT_TITLE, fb.PT_SUB)
    fb.PT_TITLE, fb.PT_SUB = title, sub
    try:
        yield
    finally:
        fb.PT_TITLE, fb.PT_SUB = old


def load():
    """Metro rows to draw, plus every count the figure states."""
    _, sc = cm.report()
    st = cm.stations()
    metros = cm.by_metro(st)
    sel = cm.largest(metros, cm.MIN_WIDE)

    lo = st.loc[st["cost_per_parcel_median"].idxmin()]
    hi = st.loc[st["cost_per_parcel_median"].idxmax()]
    facts = {
        "national": float(st["cost_per_parcel_median"].median()),
        "stations": len(st),
        "metros": len(metros),
        "shown_stations": int(sel["stations"].sum()),
        "zctas": sc["zctas"],
        "households": sc["median_cost_per_parcel"],
        "share": float(sel["stations"].sum()) / len(st),
        "cheap": (cm.short_state(lo["metro"]),
                  float(lo["cost_per_parcel_median"])),
        "dear": (cm.short_state(hi["metro"]),
                 float(hi["cost_per_parcel_median"])),
    }
    return sel, facts, sc


def draw(sel, facts, sc):
    fig, ax = fb.figure(WIDTH, HEIGHT)

    n_hidden = facts["metros"] - len(sel)
    with _type_scale(16.5, 10.0):
        low = fb.titles(
            fig,
            "It costs about a dollar to put a parcel on a doorstep",
            f"Median cost to deliver one parcel, by metro. The dot is the "
            f"median of the metro's delivery stations and the bar is their\n"
            f"interquartile range; the count beside each name is how many "
            f"stations it has. Drawn are the {len(sel)} metros with "
            f"{cm.MIN_WIDE} or more\ncosted stations — "
            f"{facts['shown_stations']} of {facts['stations']} stations, "
            f"{facts['share']:.0%} of the network, out of "
            f"{facts['metros']} metros in all.", pad=0.026)
    fig.subplots_adjust(top=low - 0.050, bottom=0.185, left=0.180,
                        right=0.930)

    xhi = float(sel["q3"].max()) + 0.022
    xlo = float(sel["q1"].min()) - 0.030
    ax.axvline(facts["national"], color=fb.MUTED, lw=1.0, ls=(0, (4, 3)),
               zorder=1)

    # The ramp spans the DRAWN medians, so the contrast is spent on the range
    # the reader can actually see rather than on the full-network extremes
    # (Enid at $1.71) which would push every metro here into the pale end.
    clo = float(sel["median"].min())
    chi = float(sel["median"].max())

    for i, r in sel.iterrows():
        ax.plot([r.q1, r.q3], [i, i], color=fb.COST_TRACK, lw=5.5,
                solid_capstyle="round", zorder=2)
        ax.plot([r["median"]], [i], "o",
                color=fb.cost_color(float(r["median"]), clo, chi), ms=8.0,
                markeredgecolor="white", markeredgewidth=1.5, zorder=3)
        # A fixed label column, so the numbers read as a column rather than
        # stepping raggedly with each bar's right-hand end.
        ax.text(xhi + 0.012, i, f"${r['median']:.2f}", color=fb.INK,
                fontsize=9.0, va="center", ha="left")

    ax.set_yticks(range(len(sel)))
    ax.set_yticklabels(
        [f"{cm.short_state(m)}  ({n})"
         for m, n in zip(sel["metro"], sel["stations"], strict=True)],
        fontsize=9.0, color=fb.INK)
    ax.set_xlabel(f"cost to deliver one parcel   (USD, {cm.period_label()})",
                  fontsize=9.5, color=fb.MUTED, labelpad=9)
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(-0.9, len(sel) - 0.25)
    ax.invert_yaxis()

    ax.text(facts["national"] + 0.006, -0.62,
            f"median of all {facts['stations']} stations  "
            f"${facts['national']:.2f}",
            color=fb.MUTED, fontsize=8.5, va="center", ha="left")

    fb.frame(ax, xgrid=True)
    ax.tick_params(axis="y", length=0)

    fig.text(
        0.0, 0.006,
        f"Costs are {cm.period_label()} baseline, computed from road "
        f"geometry, wages and population density over {sc['zctas']:,} ZIP "
        f"code areas, not from\nany Amazon disclosure. Across all "
        f"{facts['stations']} stations the median runs "
        f"\\${facts['cheap'][1]:.2f} ({facts['cheap'][0]}) to "
        f"\\${facts['dear'][1]:.2f} ({facts['dear'][0]}); the {n_hidden} "
        f"metros with\nfewer than {cm.MIN_WIDE} stations are not drawn. "
        f"Dense metros are cheapest to serve — and are exactly where a "
        f"warehouse cannot be\nbuilt. Feasibility binds before economics.",
        fontsize=8.2, color=fb.MUTED, va="bottom", ha="left",
        linespacing=1.6)
    return fig


def main() -> int:
    sel, facts, sc = load()
    fig = draw(sel, facts, sc)
    path = os.path.join(cm.ROOT, OUT)
    problems = fb.save(fig, path, placed_width=WIDTH)

    print(f"  wrote {OUT}  ({os.path.getsize(path) / 1e6:.2f} MB)")
    print(f"  {len(sel)} metros drawn of {facts['metros']}, "
          f"{facts['shown_stations']} of {facts['stations']} stations "
          f"({facts['share']:.1%}), {sc['zctas']:,} ZCTAs")
    print(f"  station median of medians ${facts['national']:.4f}; "
          f"cheapest {facts['cheap'][0]} ${facts['cheap'][1]:.4f}, "
          f"dearest {facts['dear'][0]} ${facts['dear'][1]:.4f}")
    print(f"  cheapest metro {cm.short_state(sel['metro'].iloc[0])} "
          f"${sel['median'].iloc[0]:.3f}  dearest "
          f"{cm.short_state(sel['metro'].iloc[-1])} "
          f"${sel['median'].iloc[-1]:.3f}")
    print(f"  geometry gate: {problems or 'clean'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
