"""The three results figures the paper needs and the repository did not have.

Every value is read from an artefact at build time. None is typed in. That
rule exists because this project shipped a figure with nine hand-entered
values and a fabricated 95% confidence band, caught in its own audit; the
remedy was not "be careful" but "make it impossible".

Each figure is drawn at the IEEE single-column width it will occupy, so the
document never has to shrink it, and each is put through the geometry gate in
``figbase`` before it is written.

    python tools/figures/fig_paper.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import figbase as fb  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "figures")


def _load(rel: str) -> dict:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------- 1. metro AUC

def metro_auc() -> tuple[str, str]:
    d = _load("outputs/metrics/metro_entry.json")
    years = d["held_out_years"]
    f = d["out_of_time"]["prereg_strict"]["forms"]["logit"]
    model = [f[str(y)]["model"]["auc"] for y in years]
    house = [f[str(y)]["baseline2_households"]["auc"] for y in years]

    fig, ax = fb.figure(fb.COL_W, 2.45)
    low = fb.titles(
        fig,
        "The model loses in every held-out year",
        "Out-of-time AUC against a zero-parameter baseline that ranks\n"
        "metros by households. Pre-registered and hashed before fitting.")
    fig.subplots_adjust(top=low - 0.10, bottom=0.20, left=0.15, right=0.98)

    for y, m, h in zip(years, model, house, strict=True):
        ax.plot([y, y], [m, h], color=fb.FAINT, lw=3.2, zorder=1,
                solid_capstyle="round")
    ax.plot(years, house, "-o", color=fb.WARM, lw=1.4, ms=3.6, zorder=4,
            markeredgecolor="white", markeredgewidth=0.7)
    ax.plot(years, model, "-o", color=fb.HUE, lw=1.4, ms=3.6, zorder=3,
            markeredgecolor="white", markeredgewidth=0.7)

    ax.annotate("households baseline", (years[2], house[2]),
                xytext=(0, 5), textcoords="offset points",
                fontsize=fb.PT_ANNOT, color=fb.WARM, ha="center")
    ax.annotate("model", (years[2], model[2]), xytext=(0, -11),
                textcoords="offset points", fontsize=fb.PT_ANNOT,
                color=fb.HUE, ha="center")

    ax.set_xticks(years)
    ax.set_xticklabels([str(y)[2:] for y in years])
    ax.set_ylim(0.55, 1.02)
    ax.set_ylabel("out-of-time AUC", fontsize=fb.PT_LABEL, color=fb.MUTED)
    ax.set_xlabel("held-out year (20xx)", fontsize=fb.PT_LABEL,
                  color=fb.MUTED, labelpad=2)
    fb.frame(ax, ygrid=True)
    p = os.path.join(OUT, "fig_metro_auc.png")
    fb.save(fig, p, placed_width=fb.COL_W)
    return p, d["run_id"]


# ------------------------------------------------------- 2. dispersion

def dispersion() -> tuple[str, str]:
    g = _load("experiments/gravity-network/artefacts/gravity_network.json")
    cvs = g["terms"]["dispersion"]["mean_within_metro_cv"]
    state: dict[str, set] = {}
    for arm in g["arms"].values():
        for col, rec in (arm.get("verdicts") or {}).items():
            if col in cvs:
                state.setdefault(col, set()).add(rec.get("state"))
    # "Interior in ANY arm" is the rule behind the published 9-of-14, and it
    # is the one the errata's "all five failures are sortation-side" claim
    # depends on. Counting strictly (interior in EVERY arm) gives 8, because
    # fulfilment_proximity is interior in one arm and straddles the boundary
    # in another. That single term is drawn hollow rather than argued away.
    pts = sorted((cv,
                  "INTERIOR" in state.get(col, set()),
                  len(state.get(col, set())) > 1)
                 for col, cv in cvs.items())

    n_lo = sum(1 for cv, _, _ in pts if cv < 0.6)
    n_hi = len(pts) - n_lo
    n_hi_int = sum(1 for cv, it, _ in pts if cv > 1.3 and it)

    fig, ax = fb.figure(fb.COL_W, 2.15)
    low = fb.titles(
        fig,
        "Low variation guarantees failure.\n"
        "High variation guarantees nothing.",
        f"{len(pts)} network terms, one run. All {n_lo} below cv 0.6 fail;\n"
        f"only {n_hi_int} of {n_hi} above cv 1.3 succeed. The band is empty.\n"
        f"Hollow: interior in one arm, boundary-straddling in another.")
    fig.subplots_adjust(top=low - 0.10, bottom=0.24, left=0.30, right=0.97)

    ax.axvspan(0.6, 1.3, color="#f2f2f2", zorder=0)
    for cv, interior, mixed in pts:
        col = fb.HUE if interior else fb.WARM
        ax.plot([cv], [1 if interior else 0], "o", ms=4.4,
                color="white" if mixed else col,
                markeredgecolor=col if mixed else "white",
                markeredgewidth=1.1 if mixed else 0.6, zorder=3)

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["at the\nboundary", "interior"],
                       fontsize=fb.PT_TICK, color=fb.INK)
    ax.set_ylim(-0.75, 1.75)
    ax.set_xscale("log")
    ax.set_xlabel("within-metro coefficient of variation",
                  fontsize=fb.PT_LABEL, color=fb.MUTED, labelpad=2)
    fb.frame(ax, xgrid=True)
    p = os.path.join(OUT, "fig_dispersion.png")
    fb.save(fig, p, placed_width=fb.COL_W)
    return p, g["run_id"]


# --------------------------------------------------- 3. visibility gap

def visibility_gap() -> tuple[str, str]:
    c = _load("outputs/metrics/mwpvl_coverage.json")
    total = c["mwpvl_delivery_station_cities"]
    seen = c["cities_in_both"]
    unseen = c["cities_mwpvl_names_that_osha_never_inspected"]

    fig, ax = fb.figure(fb.COL_W, 1.55)
    low = fb.titles(
        fig,
        f"Federal records see {seen} of {total} cities",
        "US cities with an Amazon delivery station, against those with any\n"
        "OSHA inspection record. A floor on the gap, not an estimate.")
    fig.subplots_adjust(top=low - 0.12, bottom=0.06, left=0.0, right=1.0)

    ax.barh([0], [seen], color=fb.HUE, height=0.42, zorder=3)
    ax.barh([0], [unseen], left=[seen], color=fb.FAINT, height=0.42, zorder=3)
    ax.text(seen / 2, 0, str(seen), ha="center", va="center", color="white",
            fontsize=8.5, weight="bold", zorder=4)
    ax.text(seen + unseen / 2, 0, str(unseen), ha="center", va="center",
            color=fb.INK, fontsize=8.5, weight="bold", zorder=4)
    ax.text(seen / 2, -0.35, "in OSHA records", ha="center", va="top",
            color=fb.MUTED, fontsize=fb.PT_ANNOT)
    ax.text(seen + unseen / 2, -0.35, "invisible", ha="center", va="top",
            color=fb.MUTED, fontsize=fb.PT_ANNOT)

    ax.set_xlim(0, total)
    ax.set_ylim(-1.1, 0.45)
    ax.axis("off")
    p = os.path.join(OUT, "fig_visibility_gap.png")
    fb.save(fig, p, placed_width=fb.COL_W)
    return p, c.get("run_id", "unstamped")


# ------------------------------------------------------- 4. cost model

def cost_by_metro() -> tuple[str, str]:
    """A column-width cost figure for the paper.

    docs/figures/hero_cost_per_parcel.png says the same thing but is drawn
    8.97in wide for a README, where it is read on a screen. Dropped into a
    3.4in IEEE column it would be shown at 37% and its labels would reach the
    page at about 3pt. Same data, different medium, different figure.
    """
    import pandas as pd
    d = pd.read_parquet(os.path.join(
        ROOT, "outputs/tables/cost_to_serve_2023q4_baseline.parquet"))
    g = (d.groupby("metro_label")["cost_per_parcel"]
         .agg(median="median", lo=lambda s: s.quantile(.25),
              hi=lambda s: s.quantile(.75))
         .sort_values("median"))
    national = float(d["cost_per_parcel"].median())

    fig, ax = fb.figure(fb.COL_W, 2.55)
    low = fb.titles(
        fig,
        "About a dollar to a doorstep",
        f"Median and interquartile cost per parcel, {len(d):,} ZIP-code\n"
        f"areas. Computed from road geometry and density, not disclosure.")
    fig.subplots_adjust(top=low - 0.10, bottom=0.17, left=0.34, right=0.90)

    ax.axvline(national, color=fb.MUTED, lw=0.7, ls=(0, (3, 3)), zorder=1)
    for i, (_, r) in enumerate(g.iterrows()):
        ax.plot([r.lo, r.hi], [i, i], color=fb.FAINT, lw=3.0, zorder=2,
                solid_capstyle="round")
        ax.plot([r["median"]], [i], "o", color=fb.HUE, ms=4.0, zorder=3,
                markeredgecolor="white", markeredgewidth=0.7)
    xmax = float(g["hi"].max()) + 0.06
    for i, (_, r) in enumerate(g.iterrows()):
        ax.text(xmax + 0.01, i, f"${r['median']:.2f}", va="center",
                ha="left", fontsize=fb.PT_ANNOT, color=fb.INK)

    # "San Francisco Bay Area" runs off the left edge at column width. The
    # geometry gate caught it; this is the fix rather than a wider margin,
    # which would squeeze the plotting area for one label's sake.
    short = {"San Francisco Bay Area": "SF Bay Area"}
    ax.set_yticks(range(len(g)))
    ax.set_yticklabels([short.get(m, m) for m in g.index],
                       fontsize=fb.PT_TICK, color=fb.INK)
    ax.set_xlim(0.85, xmax)
    ax.set_ylim(-0.8, len(g) - 0.2)
    ax.set_xlabel("USD per parcel, 2023 Q4", fontsize=fb.PT_LABEL,
                  color=fb.MUTED, labelpad=2)
    fb.frame(ax, xgrid=True)
    p = os.path.join(OUT, "fig_cost_by_metro.png")
    fb.save(fig, p, placed_width=fb.COL_W)
    return p, "cost_to_serve_2023q4_baseline.parquet"


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    rc = 0
    for fn in (metro_auc, dispersion, visibility_gap, cost_by_metro):
        try:
            path, run = fn()
        except ValueError as exc:
            print(f"  FAIL {fn.__name__}: {exc}")
            rc = 1
            continue
        kb = os.path.getsize(path) / 1024
        print(f"  {os.path.relpath(path, ROOT):<40} {kb:5.0f} KB  "
              f"geometry OK  run {run}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
