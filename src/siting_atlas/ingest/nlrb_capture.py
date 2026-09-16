"""How much of Amazon's footprint does our primary source actually see?

The project could not answer that, because it had one list and no
denominator. Two incomplete lists of the same population measure each other:
catch 100 fish and tag them, catch 100 again and find 20 tagged, and the lake
holds about 500. This module does that arithmetic on CITIES and reports it
three ways, because the three disagree and the disagreement is the finding.
The estimators live in `ingest.nlrb_estimators`; the write-up and every
caveat live in `docs/data/NLRB.md`.

The estimand, and it is not what it sounds like
-----------------------------------------------
NLRB carries no street address, so the finest key both lists share is
city+state. What is estimated here is **the number of US cities containing
at least one Amazon facility**, never the number of buildings. OSHA averages
1.39 buildings per city on the current extract, so a 54% city-coverage
figure does not imply 54% building coverage and must not be quoted as if it
did.

    python -m siting_atlas.ingest.nlrb_capture
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .nlrb import by_place, normalise_city, read_cases
from .nlrb_estimators import (
    chao_lower_bound,
    chapman,
    lincoln_petersen,
    loglinear_three_list,
    lognormal_ci,
    odds_ratio,
)

__all__ = ["load_lists", "three_list", "two_list"]

_log = get_logger("nlrb_capture")

#: The ten states the OpenStreetMap query was actually run over
#: (`docs/data/FACILITY_PANEL_HOWTO.md`, Job 1 step 3). Outside them the OSM
#: list has a STRUCTURALLY ZERO capture probability, which is not
#: heterogeneity and which no estimator repairs - so the three-list model is
#: fitted on this frame only, and the frame is declared rather than inferred
#: from where rows happen to appear.
OSM_FRAME = ("AZ", "CA", "CO", "FL", "ID", "IL", "NY", "TN", "TX", "WA")


def _read_places(path: Path, city_col: str, state_col: str,
                 normalise: bool = True) -> set[tuple[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if normalise:
        keys = {(normalise_city(r.get(city_col)),
                 (r.get(state_col) or "").strip().upper()) for r in rows}
    else:
        keys = {((r.get(city_col) or "").strip().upper(),
                 (r.get(state_col) or "").strip().upper()) for r in rows}
    return {p for p in keys if p[0] and p[1]}


def load_lists(nlrb_csv: Path, osha_csv: Path, osm_csv: Path) -> dict:
    places = by_place(read_cases(nlrb_csv))
    return {
        "nlrb": {p.key for p in places},
        "osha": _read_places(osha_csv, "site_city", "site_state"),
        "osm": _read_places(osm_csv, "city", "state"),
    }


def two_list(set1: set, set2: set, label: str = "") -> dict:
    """Every two-list number, with its direction of bias attached."""
    n1, n2, m = len(set1), len(set2), len(set1 & set2)
    s_obs = len(set1 | set2)
    est, var = chapman(n1, n2, m)
    chao, cvar = chao_lower_bound(s_obs, (n1 - m) + (n2 - m), m)
    lo, hi = lognormal_ci(est, s_obs, var)
    clo, chi = lognormal_ci(chao, s_obs, cvar)
    return {
        "label": label, "n_nlrb": n1, "n_osha": n2, "overlap": m,
        "observed_union": s_obs, "nlrb_only": n1 - m, "osha_only": n2 - m,
        "lincoln_petersen": lincoln_petersen(n1, n2, m),
        "chapman": est, "chapman_ci95": [lo, hi],
        "chao_lower_bound": chao, "chao_ci95": [clo, chi],
        "osha_coverage_upper_bound_chapman": n2 / est,
        "osha_coverage_upper_bound_chao": n2 / chao,
    }


def three_list(lists: dict, frame: tuple[str, ...]) -> dict:
    """The log-linear model, plus the dependence it was fitted to measure."""
    inside = {k: {p for p in v if p[1] in frame} for k, v in lists.items()}
    order = ("nlrb", "osha", "osm")
    union = set().union(*inside.values())
    cells = Counter(tuple(int(p in inside[k]) for k in order) for p in union)
    fits = loglinear_three_list({k: float(v) for k, v in cells.items()})
    s_obs = len(union)
    best = min(fits.values(), key=lambda f: f.aic)

    def c(a, b, d):
        return float(cells.get((a, b, d), 0))

    return {
        "frame_states": list(frame),
        "labels": list(order),
        "n_by_list": {k: len(v) for k, v in inside.items()},
        "observed_union": s_obs,
        "cells": {"".join(map(str, k)): v for k, v in sorted(cells.items())},
        # Conditioning on the third list is what makes these estimable at
        # all. Every one above 1 is positive dependence, which is the
        # direction that makes the two-list estimate too small.
        "measured_odds_ratios": {
            "nlrb_osha_given_osm": odds_ratio(c(1, 1, 1), c(1, 0, 1),
                                              c(0, 1, 1), c(0, 0, 1)),
            "nlrb_osm_given_osha": odds_ratio(c(1, 1, 1), c(1, 1, 0),
                                              c(0, 1, 1), c(0, 1, 0)),
            "osha_osm_given_nlrb": odds_ratio(c(1, 1, 1), c(1, 1, 0),
                                              c(1, 0, 1), c(1, 0, 0)),
        },
        "models": {
            f.name: {"df": f.df, "deviance": f.deviance, "aic": f.aic,
                     "population": s_obs + f.unseen,
                     "ci95": [s_obs + f.unseen_lo, s_obs + f.unseen_hi],
                     "osha_coverage": len(inside["osha"])
                     / (s_obs + f.unseen)}
            for f in fits.values()},
        "lowest_aic": best.name,
        "two_list_same_frame": two_list(inside["nlrb"], inside["osha"],
                                        "NLRB x OSHA, OSM frame only"),
    }


def naive_key_comparison(nlrb_csv: Path, osha_csv: Path) -> dict:
    """What the city key costs, measured rather than asserted.

    The first pass at this used a plain upper-and-strip city key and got
    209 / 340 / 108. Three of the differences were spelling variants of one
    place - CASTLETON-ON-HUDSON, ROBBINSVILLE (TOWNSHIP), BROWNSTOWN
    TOWNSHIP - and each one had invented a city that OSHA "never saw".
    Recording both keys makes the correction auditable instead of a claim.
    """
    raw_nlrb = {(r["city"].strip().upper(), r["state"])
                for r in read_cases(nlrb_csv)}
    raw_nlrb = {p for p in raw_nlrb if p[0] and p[1]}
    raw_osha = _read_places(osha_csv, "site_city", "site_state",
                            normalise=False)
    return {"nlrb": len(raw_nlrb), "osha": len(raw_osha),
            "overlap": len(raw_nlrb & raw_osha),
            "nlrb_only": len(raw_nlrb - raw_osha),
            "lincoln_petersen": lincoln_petersen(
                len(raw_nlrb), len(raw_osha), len(raw_nlrb & raw_osha))}


def _print(report: dict) -> None:
    nat, frame = report["national_two_list"], report["osm_frame_three_list"]
    print(f"\n  NLRB cities {nat['n_nlrb']}   OSHA cities {nat['n_osha']}"
          f"   in both {nat['overlap']}   union {nat['observed_union']}")
    print(f"  Chapman          {nat['chapman']:>8.0f}  "
          f"[{nat['chapman_ci95'][0]:.0f}, {nat['chapman_ci95'][1]:.0f}]"
          "   assumes independence")
    print(f"  Chao lower bound {nat['chao_lower_bound']:>8.0f}  "
          f"[{nat['chao_ci95'][0]:.0f}, {nat['chao_ci95'][1]:.0f}]"
          "   allows heterogeneity")
    print("\n  OSHA city coverage is AT MOST "
          f"{nat['osha_coverage_upper_bound_chapman']:.1%} and, once "
          "unequal catchability is allowed for, at most "
          f"{nat['osha_coverage_upper_bound_chao']:.1%}.")
    print("  Both are upper bounds. Neither is a point estimate.\n")
    ors = frame["measured_odds_ratios"]
    print("  measured dependence (1.0 would be independent): "
          + ", ".join(f"{k} {v:.2f}" for k, v in ors.items()))
    for name in ("[1][2][3]", "[12][13][23]"):
        model = frame["models"][name]
        print(f"  three-list {name:14} {model['population']:>6.0f} cities  "
              f"[{model['ci95'][0]:.0f}, {model['ci95'][1]:.0f}]  "
              f"OSHA sees {model['osha_coverage']:.1%}")


def main() -> int:
    ap = argparse.ArgumentParser(description="NLRB x OSHA coverage estimate")
    ap.add_argument("--nlrb", default=str(paths.EXTERNAL / "nlrb" /
                                          "nlrb_cases_amazon.csv"))
    ap.add_argument("--osha", default=str(paths.INTERIM / "osha_amazon.csv"))
    ap.add_argument("--osm", default=str(paths.RAW / "osm_amazon" /
                                         "_candidates_all.csv"))
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()
    for label, path in (("nlrb", args.nlrb), ("osha", args.osha),
                        ("osm", args.osm)):
        if not Path(path).exists():
            raise SystemExit(f"{label} list not found at {path}")

    with traced_layer("L4", "NLRB x OSHA capture-recapture"):
        with step("nlrb:lists"):
            lists = load_lists(Path(args.nlrb), Path(args.osha),
                               Path(args.osm))
            for k, v in lists.items():
                metric(f"nlrb_capture_{k}_cities", len(v))
        with step("nlrb:two_list"):
            national = two_list(lists["nlrb"], lists["osha"], "national")
            metric("nlrb_osha_overlap_cities", national["overlap"])
            metric("nlrb_osha_coverage_upper_bound",
                   round(national["osha_coverage_upper_bound_chao"], 4))
        with step("nlrb:three_list"):
            frame = three_list(lists, OSM_FRAME)

    report = {
        "estimand": ("US cities (city+state) containing at least one Amazon "
                     "facility. NOT buildings: OSHA holds 1.39 buildings "
                     "per city, and nothing here measures whether the "
                     "unseen cities hold as many."),
        "direction_of_bias": (
            "OSHA and NLRB are both driven by worker grievance, so presence "
            "on one raises the chance of presence on the other. Positive "
            "dependence inflates the overlap and deflates n1*n2/M. Every "
            "population figure here is therefore a LOWER BOUND and every "
            "coverage figure an UPPER BOUND."),
        "national_two_list": national,
        "osm_frame_three_list": frame,
        "naive_city_key": naive_key_comparison(Path(args.nlrb),
                                               Path(args.osha)),
        "nlrb_only_city_count": len(lists["nlrb"] - lists["osha"]),
    }
    out = paths.METRICS / "nlrb_coverage.json"
    write_json(out, report)
    artefact(out)

    only = lists["nlrb"] - lists["osha"]
    places = [p for p in by_place(read_cases(Path(args.nlrb)))
              if p.key in only]
    worklist = {
        "what": ("Cities with a confirmed Amazon NLRB case and no Amazon "
                 "building in the OSHA extract. Panel-expansion targets: "
                 "labour activity proves a worksite existed and our primary "
                 "source never saw it."),
        "caveats": [
            "city+state only, no street address - geocoding is manual",
            "a case may name a corporate office, not a warehouse; 100 of "
            "969 cases sit in the city of their own NLRB regional office",
            "operating_by is an upper bound on the opening date, never an "
            "opening date",
        ],
        "count": len(places),
        "cities": [asdict(p) | {"regions": list(p.regions)} for p in places],
    }
    wl = paths.METRICS / "nlrb_only_cities.json"
    write_json(wl, worklist)
    artefact(wl, rows=len(places))

    _print(report)
    print(f"\n  -> {out}\n  -> {wl}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
