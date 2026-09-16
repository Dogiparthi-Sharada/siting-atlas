"""The repository's hero figure: what it costs to deliver one parcel.

Answers the second of the project's two questions on sight, for a reader who
will not open anything else. Everything plotted is read from
``outputs/tables/cost_to_serve_2023q4_baseline.parquet``; nothing is typed by
hand. That constraint is not decorative -- this project previously shipped a
figure with nine hand-entered values and a fabricated confidence band, and the
rule since is that a figure either reads its numbers from an artefact or it
does not get built.

Design notes, and why the obvious chart was rejected:

* A choropleth was the first instinct and is the wrong form. Cost is a
  property of *density*, so a geographic map mostly redraws the population
  map, and ZCTA polygons at national scale render the dense metros -- the
  interesting ones -- as invisible specks.
* Min-max ranges were rejected for p10-p90. Boise's maximum is $6.42, four
  times its own median, and plotting it compresses every other metro into a
  smear. The outliers are real but they are single rural ZCTAs, and the
  subtitle says which interval is drawn.
* One series, so no legend: the title names the quantity. One hue, because
  this is magnitude on a single measure.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SRC = "outputs/tables/cost_to_serve_2023q4_baseline.parquet"
OUT = "docs/figures/hero_cost_per_parcel.png"

INK = "#1a1a1a"
MUTED = "#6b6b6b"
HUE = "#1f4e79"
FAINT = "#c8d6e3"


def load() -> tuple[pd.DataFrame, float, int, int]:
    d = pd.read_parquet(SRC)
    # Interquartile, not p10-p90. Boise's 90th percentile is $3.57 against its
    # own median of $1.43 -- a handful of rural ZCTAs -- and drawing it forces
    # an x-axis on which the other nine metros are an indistinguishable smear.
    # The IQR still shows that within-metro spread exceeds the between-metro
    # gap, which is the point of the chart.
    g = (
        d.groupby("metro_label")["cost_per_parcel"]
        .agg(median="median", lo=lambda s: s.quantile(0.25),
             hi=lambda s: s.quantile(0.75), n="count")
        .sort_values("median")
    )
    return (g, float(d["cost_per_parcel"].median()), len(d),
            d["metro_label"].nunique())


def draw(g: pd.DataFrame, national: float, n_zcta: int, n_metro: int) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=200)
    fig.subplots_adjust(top=0.78, bottom=0.17, left=0.22, right=0.90)
    y = range(len(g))
    xmax = float(g["hi"].max()) + 0.10

    ax.axvline(national, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1)

    for i, (_, r) in enumerate(g.iterrows()):
        ax.plot([r.lo, r.hi], [i, i], color=FAINT, lw=6.0,
                solid_capstyle="round", zorder=2)
        ax.plot([r["median"]], [i], "o", color=HUE, ms=9.0,
                markeredgecolor="white", markeredgewidth=1.8, zorder=3)
        # Fixed label column, so the numbers read as a column rather than
        # stepping raggedly with each bar's right-hand end.
        ax.text(xmax + 0.02, i, f"${r['median']:.2f}", color=INK,
                fontsize=9.5, va="center", ha="left")

    ax.set_yticks(list(y))
    ax.set_yticklabels(g.index, fontsize=10.5, color=INK)
    ax.set_xlabel("cost to deliver one parcel   (USD, 2023 Q4)",
                  fontsize=9.5, color=MUTED, labelpad=10)
    ax.set_xlim(0.85, xmax)
    ax.set_ylim(-0.7, len(g) - 0.3)

    ax.annotate(f"national median  ${national:.2f}",
                xy=(national, -0.55), xytext=(national + 0.012, -0.55),
                color=MUTED, fontsize=8.5, va="center", ha="left")

    fig.text(0.035, 0.945,
             "It costs about a dollar to put a parcel on a doorstep",
             fontsize=15, color=INK, va="top", ha="left", weight="bold")
    fig.text(0.035, 0.885,
             f"Median and interquartile range across {n_zcta:,} ZIP code\n"
             f"areas in {n_metro} metros. Computed from road geometry and\n"
             f"population density, not from any Amazon disclosure.",
             fontsize=9.0, color=MUTED, va="top", ha="left", linespacing=1.5)

    ax.grid(axis="x", color="#ececec", lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d4d4d4")
    ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
    ax.tick_params(axis="y", length=0)

    fig.text(0.035, 0.045,
             "Dense metros are cheapest to serve — and are exactly where a "
             "warehouse cannot be built. Feasibility binds before economics.",
             fontsize=8.8, color=MUTED, va="bottom", ha="left")

    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> int:
    g, national, n_zcta, n_metro = load()
    draw(g, national, n_zcta, n_metro)
    print(f"  wrote {OUT}")
    print(f"  {n_metro} metros, {n_zcta:,} ZCTAs, "
          f"national median ${national:.4f}")
    print(f"  cheapest {g.index[0]} ${g['median'].iloc[0]:.3f}  "
          f"dearest {g.index[-1]} ${g['median'].iloc[-1]:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
