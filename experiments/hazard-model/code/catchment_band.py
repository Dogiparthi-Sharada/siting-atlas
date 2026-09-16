"""The sensitivity band `facilities.py` asks for and never ran.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.catchment_band

``facilities.CATCHMENT_MILES["DS"] = 15.0`` sets which ZCTAs are ``enabled``
and so the whole sample the hazard stage learns from. The docstring beside it
measures a 4.7x swing in treated units from 5 to 25 miles and then asks, in
terms, for "a band across this radius, not a point estimate at 15";
`docs/AUDIT_2026_09_14.md` §3.4 records that the band was never run. This runs
it: at each radius rebuild ``enabled``, rebuild the risk set, refit the same
spec on the same seeded split.

**Not a confidence interval**, for the reason ``optimize/montecarlo`` states
about its own. There is one radius in the world and we do not know it. This
measures how far the answer travels across the range we can defend from the
evidence, and propagates our reading of that evidence. Brier and AUC are NOT
comparable ACROSS radii either — each radius is a different target over a
different test set with a different base rate — so every point also carries
the constant-predicting null scored on its own test rows. Endpoints:
:data:`RADII`. Full write-up: `docs/research/NOTES_CATCHMENT_RADIUS.md`.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from ..cost.daganzo import haversine_miles
from ..models.base import BaselineOnly
from ..models.hazard import DiscreteTimeHazard, HazardSpec
from ..models.metrics import brier_skill_score
from ..models.panel_source import REAL_COVARIATES, restrict_to_scope
from ..models.risk_set import build_risk_set, summarise
from ..models.splits import split_by_unit
from . import facility_load as fl

__all__ = ["BASELINE_MILES", "RADII", "catchment_pairs", "enabled_at",
           "reproduces_baseline", "run", "main"]

_log = get_logger("warehouse.catchment_band")
ARTEFACT = paths.METRICS / "catchment_band.json"

#: `facilities.CATCHMENT_MILES["DS"]` today.
BASELINE_MILES = 15.0

#: `models/runner.REAL_CLUSTER_COL` copied by value; this is the tripwire.
CLUSTER_COL = "cbsa_code"

#: (radius, in_band, anchor). Each drive-time conversion is
#: `speed x 0.75 h / circuity`, both from this project's own cost parameters
#: so the band is not anchored on a second set of guesses. "45 minute drive
#: time" is MWPVL's most frequent same-day statement -- 37 rows of it in
#: `data/interim/mwpvl_facilities.csv`, 36 SubSameDay FCs and 1 DS.
RADII = (
    (8.3, True, "45-min drive, congested profile (params.py:295: 16 / 1.45)"),
    (12.7, True, "45-min drive, cost baseline (22.0 mph / 1.30)"),
    (15.0, True, "CURRENT VALUE, facilities.CATCHMENT_MILES['DS']"),
    (19.6, True, "45-min drive, fast end of COST_RANGES (30 mph / 1.15)"),
    (25.0, True, "Holmes (2011) choice radius; HNS (2023) FC-to-SC rule"),
    (45.0, True, "MWPVL line 383: DS 'designed to service a 45-mile radius'"),
    (60.0, False, "OVER-RUN PROBE: MWPVL rows stating 50-90 are rural"),
)

#: Already in `docs/data/PARAMETERS.md` §5 and the `CATCHMENT_MILES`
#: docstring. Re-measured so a disagreement is caught, not believed.
RECORDED_ZCTAS = {5.0: 383, 10.0: 882, 15.0: 1257, 20.0: 1593, 25.0: 1819,
                  30.0: 2006}

#: Each asks "at WHICH RADII does this hold?", never just yes or no.
CHECKS = {
    "auc_at_or_above_0_80_at": lambda p: p["meets_v4_auc_criterion"],
    "beats_constant_null_on_brier_at": lambda p: p["beats_null_on_brier"],
    "null_better_calibrated_at": lambda p: p["ece_null"] < p["ece"],
    "households_significant_at":
        lambda p: "households" in p["covariates_p_lt_0_05"],
    "all_three_covariates_significant_at":
        lambda p: len(p["covariates_p_lt_0_05"]) == 3,
}

INTERPRETATION = (
    "NOT a confidence interval. There is one true catchment radius and we do "
    "not know it. This is a sensitivity range over an assumption, in the "
    "sense optimize/montecarlo states about its own output: how far the "
    "answer moves across the range we can defend from MWPVL's own "
    "statements, propagating our reading of them, not the world's.")


def catchment_pairs(fac: pd.DataFrame, zcta_geo: pd.DataFrame,
                    miles: float) -> pd.DataFrame:
    """``facilities.catchments`` with the radius as an argument.

    Re-implemented, not called, because `facilities.py` reads its radius from
    a module constant. :func:`reproduces_baseline` checks it against disk.
    """
    cols = ["zcta", "facility_id", "open_q_index", "close_q_index"]
    live = fac[fac["facility_type"].isin(fl.LAST_MILE_TYPES)].dropna(
        subset=["latitude", "longitude", "open_year"])
    zlat = zcta_geo["latitude"].to_numpy(float)
    zlon = zcta_geo["longitude"].to_numpy(float)
    rows = []
    for _, f in live.iterrows():
        d = haversine_miles(zlat, zlon, f["latitude"], f["longitude"])
        hit = zcta_geo.loc[d <= miles, "zcta"]
        if not hit.empty:
            rows.append(pd.DataFrame({
                "zcta": hit.to_numpy(),
                "facility_id": f.get("facility_id", ""),
                "open_q_index": f["open_q_index"],
                "close_q_index": f["close_q_index"]}))
    return (pd.concat(rows, ignore_index=True) if rows
            else pd.DataFrame(columns=cols))


def enabled_at(panel_keys: pd.DataFrame, fac: pd.DataFrame,
               zcta_geo: pd.DataFrame, miles: float) -> pd.DataFrame:
    """The ``enabled`` column at an arbitrary radius.

    ``facilities.enabled_flags``'s rule: on from the earliest quarter any
    serving facility opened to the latest quarter any was still operating.
    ``open_quarter_imputed`` is not reproduced: the radius does not move it.
    """
    keys = panel_keys[["zcta", "year", "quarter"]].copy()
    keys["q_index"] = keys["year"] * 4 + keys["quarter"] - 1
    cover = catchment_pairs(fac, zcta_geo, miles)
    if cover.empty:
        keys["enabled"] = False
        return keys.drop(columns="q_index")
    span = cover.groupby("zcta").agg(first_open=("open_q_index", "min"),
                                     last_close=("close_q_index", "max"))
    merged = keys.merge(span, on="zcta", how="left")
    merged["enabled"] = ((merged["q_index"] >= merged["first_open"])
                         & (merged["q_index"] <= merged["last_close"]))
    merged["enabled"] = merged["enabled"].fillna(False)
    return merged[["zcta", "year", "quarter", "enabled"]]


def reproduces_baseline(keys: pd.DataFrame, fac: pd.DataFrame,
                        zcta_geo: pd.DataFrame, disk: pd.Series) -> dict:
    """Match disk at 15 miles, or refuse to go on: a sweep whose baseline
    disagrees with the delivered panel is measuring its own bug."""
    ours = enabled_at(keys, fac, zcta_geo,
                      BASELINE_MILES)["enabled"].to_numpy(bool)
    theirs = disk.fillna(False).to_numpy(bool)
    mismatch = int((ours != theirs).sum())
    if mismatch:
        raise RuntimeError(
            f"the local catchment re-implementation disagrees with "
            f"data/processed/panel.parquet on {mismatch:,} cells at "
            f"{BASELINE_MILES} miles; the sweep below would be meaningless")
    _log.info("baseline check PASSED: %d enabled cells, 0 mismatches",
              int(ours.sum()))
    return {"radius_miles": BASELINE_MILES,
            "panel_parquet_enabled_cells": int(theirs.sum()),
            "recomputed_enabled_cells": int(ours.sum()),
            "mismatched_cells": mismatch}


def _fit(panel: pd.DataFrame, flags: pd.DataFrame) -> dict:
    """Swap in the target, then rerun exactly what `models.runner.run` does."""
    frame = panel.drop(columns=["enabled"]).merge(
        flags, on=["zcta", "year", "quarter"], how="left")
    scoped, scope = restrict_to_scope(frame, heldout=False)
    risk = build_risk_set(scoped)
    shape, parts = summarise(risk), split_by_unit(risk)
    spec = HazardSpec(
        covariates=tuple(c for c in REAL_COVARIATES if c in scoped.columns),
        baseline="linear", n_knots=4, cluster_col=CLUSTER_COL)
    model = DiscreteTimeHazard(spec).fit(parts["train"])
    report = model.evaluate(parts["test"], label="cloglog-hazard")
    # Carries the headline: the same test rows scored by a model predicting
    # one constant. Brier across radii is not comparable; against this, is.
    null = BaselineOnly().fit(parts["train"]).evaluate(parts["test"])
    coefs = {c["term"]: c for c in model.summary()["coefficients"]}
    test, pred = parts["test"], model.predict(parts["test"]).to_numpy()
    keep = ("coefficient", "p_value", "hazard_ratio")
    return {
        "units_in_scope": scope["units_in_scope"],
        # `units` FALLS as the radius grows: a wider catchment left-truncates
        # more ZCTAs (already enabled at t=0) than it adds treated ones.
        "risk_set": {k: shape[k] for k in ("units", "rows", "events")},
        "test_events": int(test["event"].sum()),
        "auc": round(report.auc, 4), "brier": round(report.brier, 6),
        "brier_null": round(null.brier, 6),
        "beats_null_on_brier": bool(report.brier < null.brier),
        "brier_skill": round(
            brier_skill_score(test["event"].to_numpy(), pred), 5),
        "ece": round(report.ece, 5), "ece_null": round(null.ece, 5),
        "coefficients": {k: {j: v[j] for j in keep} for k, v in coefs.items()},
        "covariates_p_lt_0_05": sorted(
            k for k, v in coefs.items()
            if k not in ("intercept", "t") and v["p_value"] < 0.05),
        "meets_v4_auc_criterion": bool(report.auc >= 0.80),
    }


def _point(panel: pd.DataFrame, fac: pd.DataFrame, geo: pd.DataFrame,
           miles: float, in_band: bool, anchor: str) -> dict:
    cover = catchment_pairs(fac, geo, miles)
    flags = enabled_at(panel[["zcta", "year", "quarter"]], fac, geo, miles)
    on = flags["enabled"].to_numpy(bool)
    per_zcta = cover.groupby("zcta")["facility_id"].nunique()
    n_fac = max(int(cover["facility_id"].nunique()), 1)
    row = {
        "radius_miles": miles, "in_band": in_band, "anchor": anchor,
        "zctas_ever_enabled": int(flags.loc[on, "zcta"].nunique()),
        "enabled_cells": int(on.sum()),
        "pct_of_panel": round(100.0 * on.mean(), 3),
        # `facilities_attached` is flat at every radius here: a facility sits
        # inside a ZCTA, so it attaches at least its own. Radius buys ZCTAs
        # PER facility. Overlap is what it costs: a ZCTA served by several
        # stations cannot separate one station's effect.
        "facilities_attached": int(cover["facility_id"].nunique()),
        "zctas_per_facility": round(len(cover) / n_fac, 1),
        "zctas_served_by_2plus_pct": round(
            100.0 * float((per_zcta > 1).mean()), 1) if len(per_zcta) else 0.0,
    }
    row.update(_fit(panel, flags))
    _log.info("%.1f mi -> %d ZCTAs, AUC %s", miles,
              row["zctas_ever_enabled"], row["auc"])
    return row


def run() -> dict:
    """Sweep the radius and report the band."""
    panel = pd.read_parquet(paths.PANEL)
    geo = panel.drop_duplicates("zcta")[["zcta", "latitude", "longitude"]]
    fac = fl.resolve_coordinates(fl.load_facilities(), geo)
    keys = panel[["zcta", "year", "quarter"]]

    check = reproduces_baseline(keys, fac, geo, panel["enabled"])
    recorded = []
    for m, n in sorted(RECORDED_ZCTAS.items()):
        got = int(enabled_at(keys, fac, geo, m)
                  .query("enabled")["zcta"].nunique())
        recorded.append({"radius_miles": m, "recorded": n, "remeasured": got,
                         "agrees": got == n})
        if got != n:
            _log.warning("%.0f mi: PARAMETERS.md sec.5 records %d, "
                         "re-measured %d", m, n, got)
    points = [_point(panel, fac, geo, m, b, a) for m, b, a in RADII]
    band = [p for p in points if p["in_band"]]
    base = next(p for p in band if p["radius_miles"] == BASELINE_MILES)

    def spread(key: str) -> dict:
        v = [p[key] for p in band]
        return {"low": min(v), "baseline": base[key], "high": max(v),
                "ratio_high_low": round(max(v) / min(v), 3) if min(v) else 0}

    report = {
        "conclusion_robustness": {
            name: [p["radius_miles"] for p in band if pred(p)]
            for name, pred in CHECKS.items()},
        "baseline_reproduction": check,
        "recorded_vs_remeasured": recorded,
        "band_endpoints_miles": [band[0]["radius_miles"],
                                 band[-1]["radius_miles"]],
        "points": points,
        "band": {k: spread(k) for k in
                 ("zctas_ever_enabled", "enabled_cells",
                  "facilities_attached", "zctas_served_by_2plus_pct",
                  "auc", "brier_skill")},
        "interpretation": INTERPRETATION,
    }
    write_json(ARTEFACT, report)
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    with (traced_layer("L4", "catchment radius band"),
          step("catchment_band:run")):
        r = run()
        metric("catchment_band_points", len(r["points"]))

    rows = "\n".join(
        f" {' ' if p['in_band'] else '*'}{p['radius_miles']:>5.1f}"
        f"{p['zctas_ever_enabled']:>8}{p['risk_set']['units']:>7}"
        f"{p['risk_set']['events']:>8}{p['auc']:>8}{p['brier']:>10}"
        f"{p['brier_null']:>10}{len(p['covariates_p_lt_0_05']):>5}"
        f"  {p['anchor'][:40]}" for p in r["points"])
    print(f"\n  === catchment radius: sensitivity band ===\n\n"
          f"  {'mi':>6}{'ZCTAs':>8}{'units':>7}{'events':>8}{'AUC':>8}"
          f"{'Brier':>10}{'null':>10}{'sig':>5}  anchor\n{rows}\n"
          "\n  * outside the band — an over-run probe, not part of the range."
          "\n  'sig' = covariates with p < 0.05, of 3. Brier and AUC are NOT"
          "\n  comparable ACROSS rows -- compare each Brier to its own null."
          f"\n\n  {r['interpretation']}\n")
    artefact(ARTEFACT, points=len(r["points"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
