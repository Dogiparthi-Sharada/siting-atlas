"""Where is there unserved demand? — and does that question predict anything.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.analysis.white_space

Every model in this project answers *"where did Amazon build?"*, and that
question has a measured ceiling: five panel compositions crossed with three
algorithms land between 2.5x and 3.1x lift over chance, a spread narrower than
one method's re-sampling noise. This asks the inverse. Draw a service area
around every Amazon facility that exists; the populated places falling outside
all of them are the white space.

The inverse question needs no target variable, so it is not capped by the 485
decisions — and it is what a county planner can actually act on, which is the
project's stated purpose. What it is NOT is automatically true. §"backtest"
below holds out 2024-25 and asks whether the places this flagged are the
places Amazon then built in, against the baseline that has to be beaten:
**the same number of places ranked by raw household count, with no coverage
logic at all.** The answer to that is in ``verdict`` and it is not the
flattering one.

The radius is an input, not a finding
-------------------------------------
``warehouse/facilities.py`` uses 15 miles and calls it an engineering
estimate. MWPVL's own prose says delivery stations are *"designed to service a
45-mile radius"* (``docs/data/MWPVL_2025.md`` §3.2), and individual rows in
the same document say "60 miles in all directions" and "60-70 mile radius".
``outputs/metrics/catchment_band.json`` measures the defensible band at
8.3-45 miles and finds it moves enabled ZCTAs by 3.57x. A single radius here
would be an assumption wearing a finding's clothes, so every figure is
reported at :data:`RADII`, with 45 — the only radius with an external source
attached to it — as the headline.

Distance is **straight-line great-circle**, not drive time. That is what the
rest of the project already uses; see ``white_space_cover`` for the three
ways it is wrong and which direction each one pushes.

Artefact: ``outputs/metrics/white_space.json``.
Write-up: ``docs/research/NOTES_WHITE_SPACE.md``.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from . import white_space_backtest as bt
from . import white_space_cover as cover
from . import white_space_diagnose as diagnose
from . import white_space_network as net
from . import white_space_rules as rules
from .white_space_print import console

__all__ = ["ARTEFACT", "HEADLINE_MILES", "RACE_RADII", "RADII", "TOP_N",
           "main", "run"]

_log = get_logger("analysis.white_space")
ARTEFACT = paths.METRICS / "white_space.json"

#: The externally-sourced radius, and the one every headline quotes.
HEADLINE_MILES = 45.0

#: Copied by value from ``warehouse/catchment_band.RADII`` rather than
#: imported, because importing it would pull ``models.hazard`` and half the
#: modelling stack into an analysis that fits nothing. ``(miles, in_band,
#: anchor)``; the 60-mile row is an over-run probe and is excluded from the
#: band summaries exactly as it is there.
RADII = (
    (8.3, True, "45-min drive, congested profile (params.py:295: 16 / 1.45)"),
    (12.7, True, "45-min drive, cost baseline (22.0 mph / 1.30)"),
    (15.0, True, "CURRENT VALUE, facilities.CATCHMENT_MILES['DS']"),
    (19.6, True, "45-min drive, fast end of COST_RANGES (30 mph / 1.15)"),
    (25.0, True, "Holmes (2011) choice radius; HNS (2023) FC-to-SC rule"),
    (45.0, True, "MWPVL line 383: DS 'designed to service a 45-mile radius'"),
    (60.0, False, "OVER-RUN PROBE: MWPVL rows stating 50-90 are rural"),
)

#: Radii for the rule horse-race in ``white_space_rules``. Two, not seven:
#: each point costs two 1.1e9-element matmuls, and the question it answers
#: (WHY the back-test failed) does not need the full sweep. 15.0 is the
#: project's current value, 45.0 the headline.
RACE_RADII = (15.0, HEADLINE_MILES)

#: Length of the named list. An aggregate count is not usable by anyone.
TOP_N = 30

#: Length of the metro roll-up beside it.
TOP_N_CBSA = 15

GEOMETRY = (
    "A ZCTA is covered when its centroid is within the radius, in "
    "straight-line great-circle miles, of at least one Amazon facility. Not "
    "drive time, not a road-network buffer, not a polygon intersection. The "
    "same geometry warehouse/facilities.py uses to build the 'enabled' "
    "target, so the two mean the same thing at the same radius.")

FALSIFICATION = (
    "This analysis is falsifiable going forward. If Amazon opens a delivery "
    "station in a place flagged here, that is a prediction that came true. "
    "If it opens inside coverage that already existed, the framing is wrong. "
    "The 'backtest' block runs exactly that test on 2024-25 retrospectively, "
    "and reports the result whichever way it came out.")


def _coverage_rows(zctas: pd.DataFrame, coords: str,
                   nearest) -> list[dict]:
    """Every radius for one coordinate arm, with its named list."""
    rows = []
    for miles, in_band, anchor in RADII:
        row = {"coord_set": coords, "in_band": in_band, "anchor": anchor}
        row.update(cover.summarise(zctas, nearest, miles))
        row["top_uncovered_zctas"] = cover.top_uncovered(
            zctas, nearest, miles, TOP_N)
        metros = cover.by_cbsa(zctas, nearest, miles).head(TOP_N_CBSA)
        row["top_uncovered_cbsas"] = [
            {"cbsa_code": m.cbsa_code, "cbsa_title": m.cbsa_title,
             "uncovered_households": int(m.uncovered_households),
             "uncovered_share_of_metro": round(float(m.uncovered_share), 3)}
            for m in metros.itertuples()]
        rows.append(row)
    return rows


def _support_contribution(zctas: pd.DataFrame, coords: str) -> dict:
    """What the 783 non-delivery-station sites add, at the headline radius.

    A metro served by a million-square-foot fulfilment centre is not white
    space, so the support network belongs in the coverage map. This measures
    how much of the map it is responsible for, because "we included them" is
    a claim and "they moved coverage by X households" is a measurement.
    """
    ds_only, prov = net.network(coords, support=False, zctas=zctas)
    near = cover.nearest_miles(zctas, ds_only)
    return {"coord_set": coords, "radius_miles": HEADLINE_MILES,
            "delivery_stations_only": prov["facilities"],
            **{f"ds_only_{k}": v for k, v in
               cover.summarise(zctas, near, HEADLINE_MILES).items()
               if k in ("zctas_covered", "households_covered",
                        "households_covered_pct")}}


def _scoreboard(backtests: list[dict]) -> dict:
    """How often white space beat the household baseline, over every cell."""
    cells = [(b, level, row) for b in backtests
             for level in ("zcta_level", "cbsa_level") for row in b[level]]
    wins = [c for c in cells if c[2]["white_space_beats_baseline"]]

    def sig(subset):
        return [c for c in subset if c[2]["mcnemar"]["p_value"] is not None
                and c[2]["mcnemar"]["p_value"] < 0.05]

    losses = [c for c in cells if not c[2]["white_space_beats_baseline"]]

    def label(c):
        return (f"{c[0]['coord_set']}/{c[0]['radius_miles']}mi/"
                f"{c[1].split('_')[0]}/N={c[2]['n_flagged']}")

    return {
        "cells_scored": len(cells),
        "white_space_wins": len(wins),
        "household_baseline_wins_or_ties": len(losses),
        "win_share": round(len(wins) / len(cells), 3) if cells else 0.0,
        # Split, because "significant in 34 cells" reads as 34 successes and
        # is the opposite: every one of them is the baseline winning.
        "significant_wins_for_white_space": len(sig(wins)),
        "significant_wins_for_the_household_baseline": len(sig(losses)),
        "won_at": [label(c) for c in wins],
        "lost_significantly_at": [label(c) for c in sig(losses)],
    }


def _verdict(board: dict, backtests: list[dict]) -> str:
    inside = [b["openings_inside_existing_coverage_pct"] for b in backtests
              if b["radius_miles"] == HEADLINE_MILES]
    lo, hi = min(inside), max(inside)
    stance = ("beats" if board["win_share"] > 0.5 else "does NOT beat")
    return (
        f"White space {stance} the household baseline: it wins "
        f"{board['white_space_wins']} of {board['cells_scored']} scored "
        f"cells, and p<0.05 is reached "
        f"{board['significant_wins_for_white_space']} times in white space's "
        f"favour against "
        f"{board['significant_wins_for_the_household_baseline']} times in "
        f"the baseline's. At the headline {HEADLINE_MILES:.0f} miles, "
        f"{lo:.1f}-{hi:.1f}%"
        f" of the 2024-25 delivery-station openings landed INSIDE the "
        f"coverage the pre-2024 network already had. Amazon densified where "
        f"it already served; it did not fill the gaps this analysis names. "
        f"The map is a real description of who is unserved and is usable as "
        f"that. It is not a predictor of where Amazon builds next, and the "
        f"capstone should not be built on the claim that it is.")


def run() -> dict:
    """Build the coverage map at every radius, then try to falsify it."""
    zctas = net.zcta_universe()
    coverage, networks, backtests, support, races = [], {}, [], [], []
    for coords in net.COORD_SETS:
        live, prov = net.network(coords, support=True, zctas=zctas)
        networks[coords] = prov
        nearest = cover.nearest_miles(zctas, live)
        coverage.extend(_coverage_rows(zctas, coords, nearest))
        support.append(_support_contribution(zctas, coords))
        ctx = bt.prepare(zctas, coords)
        backtests.extend(bt.score(zctas, ctx, coords, m)
                         for m, in_band, _ in RADII if in_band)
        races.extend(rules.race(zctas, ctx, coords, m) for m in RACE_RADII)

    board = _scoreboard(backtests)
    report = {
        "headline_radius_miles": HEADLINE_MILES,
        "geometry": GEOMETRY,
        "universe": {
            "zctas": int(len(zctas)),
            "households": float(zctas["households"].sum()),
            "population": float(zctas["population"].sum()),
            "source": "data/processed/panel.parquet, one row per ZCTA"},
        "networks": networks,
        "support_site_contribution": support,
        "coverage": coverage,
        "backtest": backtests,
        "backtest_design": {
            "coverage_built_from": f"facilities opened {bt.CUT_YEAR} or "
                                   "earlier, undated rows excluded",
            "scored_on": f"delivery stations opened {bt.HELD_OUT_YEARS}",
            "baseline": "the same N places ranked by households alone",
            "paired_test": "two-sided exact McNemar on discordant openings"},
        "scoreboard": board,
        "rule_race": races,
        "why_it_failed": diagnose.diagnose(races),
        "verdict": _verdict(board, backtests),
        "falsification": FALSIFICATION,
    }
    write_json(ARTEFACT, report)
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    with (traced_layer("L4", "white space / unserved demand"),
          step("white_space:run")):
        report = run()
        metric("white_space_coverage_points", len(report["coverage"]))
        metric("white_space_backtest_points", len(report["backtest"]))
    print(console(report))
    artefact(ARTEFACT, points=len(report["coverage"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
