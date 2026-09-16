"""L4 — refit the retired hazard model on the expanded panel, and report.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.models.hazard_revival

Writes ``outputs/metrics/hazard_revival.json``. It does NOT touch
``outputs/metrics/hazard_report.json``, which is the record of the retired
run and this run's only baseline.

WHAT THIS IS AND IS NOT
-----------------------
The hazard model was retired on 2026-09-13 at AUC 0.689, ECE 0.00863 against
a constant null's 0.00005, on 39 events across 8 metros. Two of its three
handicaps have since gone: the panel holds 687 loadable facilities instead of
43, and 545 of them carry a stated MWPVL opening date instead of an OSHA
"operating by" upper bound that runs a measured 32 months late.

**The third handicap has not gone and cannot be removed by data.** One
delivery station switches on a whole catchment of ZCTAs in one quarter, and
the likelihood counts them as that many independent observations — Train
(2009) §3.7.1, printed p. 61: the likelihood assumes "each decision maker's
choice is independent of that of other decision makers". Every standard
error below is therefore wrong in a known direction, and no amount of extra
data repairs it. ``hazard_revival_measure.catchment_load`` re-measures
the size of the violation on this frame; it is larger, not smaller.

So the discrimination and calibration figures here are MEASUREMENTS, not a
rehabilitation. If AUC improves, the model is still not usable. The honest
framing of a good result and of a bad one is the same sentence: the negative
finding survives on the best data available, which is a stronger statement
than retiring it on 39 events.

THE FOUR-WAY COMPARISON
-----------------------
Old dates against new, three covariates against five, so that "more events"
and "better dates" cannot be confused for each other. ``ARMS`` below names
them and ``hazard_revival_frames`` explains why the clean date contrast is
only 30 facilities wide.
"""

from __future__ import annotations

import os

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from . import hazard_revival_frames as frames
from . import hazard_revival_measure as measure
from . import hazard_revival_print as show
from .hazard_revival_fit import (
    compare,
    constant_null_verdict,
    fit_arm,
    worst_case_auc,
)

_log = get_logger("models.hazard_revival")
ARTEFACT = paths.METRICS / "hazard_revival.json"

#: ``(arm name, dating, covariate tuple)``. ``dating`` is one of:
#:
#:   ``frame``   the expanded file's own dates — MWPVL where MWPVL has one,
#:               the OSHA-derived national date otherwise. 545 dated.
#:   ``osha``    every date replaced by that facility's OSHA bound; a
#:               facility without one is DROPPED, never imputed. 139 dated.
#:   ``pair_*``  the 130 facilities dated under both, so that facility
#:               membership is identical and only the dates move. This is
#:               the only clean date contrast and it is 30 facilities wide.
ARMS = (
    ("new_dates_3cov", "frame", frames.COVARIATES_3),
    ("new_dates_5cov", "frame", frames.COVARIATES_5),
    ("old_dates_3cov", "osha", frames.COVARIATES_3),
    ("old_dates_5cov", "osha", frames.COVARIATES_5),
    ("new_dates_4cov", "frame", frames.COVARIATES_4),
    ("matched_new_3cov", "pair_frame", frames.COVARIATES_3),
    ("matched_old_3cov", "pair_osha", frames.COVARIATES_3),
)

INDEPENDENCE = (
    "Unchanged and unfixable by data. One station opening switches on a "
    "whole catchment in one quarter and the likelihood counts each ZCTA as "
    "an independent observation (Train 2009 sec. 3.7.1, printed p. 61). "
    "Every standard error in this file is wrong in that known direction. "
    "Clustering the covariance on the CBSA reduces the damage and does not "
    "remove it, because the unit of decision is the building, not the metro "
    "and certainly not the ZIP.")

COMPARABILITY = (
    "Brier and ECE are NOT comparable across arms: each arm has a different "
    "target, a different test set and a different base rate. Each arm "
    "therefore carries the constant-predicting null scored on its own test "
    "rows, and the MODEL-AGAINST-ITS-OWN-NULL pair is the comparison. AUC "
    "is comparable in the weaker sense that 0.5 means the same thing "
    "everywhere.")


def _facility_sets(fac: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The facility frames behind each dating, built once and shared."""
    osha = frames.redate_to_osha_bound(fac)
    both = osha.loc[osha["open_year"].notna()
                    & fac.loc[osha.index, "open_year"].notna()]
    return {"frame": fac, "osha": osha,
            "pair_frame": fac.loc[both.index], "pair_osha": osha.loc[
                both.index]}


def run() -> dict:
    """Build every arm, fit it, and hand back the whole comparison."""
    panel = pd.read_parquet(frames.EXPANDED_PANEL)
    geo = panel.drop_duplicates("zcta")[["zcta", "latitude", "longitude"]]
    fac = frames.load_expanded_facilities(geo)

    with step("hazard_revival:frames"):
        check = measure.reproduces_disk(panel, fac, geo)
        sets = _facility_sets(fac)
        provenance = {
            "panel": paths.rel(frames.EXPANDED_PANEL),
            "panel_rows": int(len(panel)),
            "facilities_loadable": int(len(fac)),
            "facilities_dated_frame": int(fac["open_year"].notna().sum()),
            "facilities_with_osha_bound": int(len(sets["osha"])),
            "facilities_dated_both_ways": int(len(sets["pair_frame"])),
            "facilities_dropped_from_osha_arm": int(
                len(fac) - len(sets["osha"])),
            "drop_rule": "a facility with no OSHA bound is dropped from the "
                         "osha arm; no date is invented for it",
            "target_rebuild_check": check,
            "date_gap_osha_minus_stated": measure.date_gap(fac),
            "catchment_load": measure.catchment_load(fac, geo),
            "catchment_load_band": measure.catchment_load_band(fac, geo),
            "truncation_cost": {
                name: measure.truncation_cost(panel, sets[name], geo)
                for name in ("frame", "osha", "pair_frame", "pair_osha")},
            "covariate_coverage_pct": measure.coverage_by_covariate(panel),
        }

    arms: dict[str, dict] = {}
    for name, dating, covariates in ARMS:
        with step(f"hazard_revival:{name}"):
            source = sets[dating]
            arm = frames.scoped_frame(panel, source, geo, covariates)
            held = frames.heldout_frame(panel, source, geo, arm.covariates)
            if arm.frame.empty or not arm.frame["enabled"].any():
                arms[name] = {"ran": False, "reason": "no enabled cell in "
                                                      "scope", **arm.detail}
                continue
            arms[name] = {"ran": True, "dating": dating,
                          "scope": arm.detail,
                          **fit_arm(arm.frame, arm.covariates,
                                    heldout=held)}
            metric(f"hazard_revival_{name}_auc",
                   arms[name]["held_out_by_unit"]["auc"])

    live = {k: v for k, v in arms.items() if v.get("ran")}
    report = {
        "provenance": provenance,
        "baseline_retired_run": show.RETIRED,
        "arms": arms,
        "date_contrast": {
            "full_frame_new_vs_osha_3cov": compare(
                live["new_dates_3cov"], live["old_dates_3cov"])
            if {"new_dates_3cov", "old_dates_3cov"} <= live.keys() else None,
            "matched_facilities_new_vs_osha_3cov": compare(
                live["matched_new_3cov"], live["matched_old_3cov"])
            if {"matched_new_3cov", "matched_old_3cov"} <= live.keys()
            else None,
            "note": "The full-frame contrast changes the facility set as "
                    "well as the dates (545 dated against 139), so it does "
                    "not isolate dating. The matched contrast holds the "
                    "facility set at 130 and moves only the dates -- but "
                    "only 30 of those 130 dates actually move, because the "
                    "104 national rows were derived from the OSHA bound in "
                    "the first place. Neither contrast is clean and strong "
                    "at once; that is a property of the data, not a "
                    "presentation choice.",
        },
        "calibration_against_constant": constant_null_verdict(live),
        "auc_across_arms": worst_case_auc(live),
        "covariate_decision": show.COVARIATE_DECISION,
        "independence_violation": INDEPENDENCE,
        "comparability": COMPARABILITY,
    }
    # Assembled from the measurements, after them, so that no sentence in it
    # can have been written before the numbers were known.
    report["verdict"] = show.verdict(report)
    return report


def main() -> int:
    os.nice(19)
    paths.ensure_dirs()
    init_run()
    configure()
    with traced_layer("L4", "hazard revival on the expanded panel"):
        report = run()
        metric("hazard_revival_arms",
               sum(1 for a in report["arms"].values() if a.get("ran")))
    show.print_report(report)
    write_json(ARTEFACT, report)
    artefact(ARTEFACT, arms=len(report["arms"]))
    print(f"  -> {paths.rel(ARTEFACT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
