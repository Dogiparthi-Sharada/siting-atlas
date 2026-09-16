"""The console view of the revival, and the three standing texts.

Kept out of ``hazard_revival`` so that the run module is the experiment and
this one is the writing-up. The texts are here rather than in a document
because a caveat that lives in a document can be dropped from a slide; one
that is emitted beside the number it qualifies cannot.
"""

from __future__ import annotations

#: The retired run, read off ``outputs/metrics/hazard_report.json`` on
#: 2026-09-15 and carried here so the comparison is on the page. That file is
#: never overwritten by this module; these are copies for the reader.
RETIRED = {
    "artefact": "outputs/metrics/hazard_report.json",
    "panel": "data/processed/panel.parquet (43-facility pilot frame)",
    "covariates": ["households", "median_household_income",
                   "establishments"],
    "risk_set": {"units": 1756, "rows": 40358, "events": 812},
    "usable_facilities": 38,
    "independent_episodes": 28,
    "held_out_by_unit": {"n_rows": 8044, "n_events": 161, "auc": 0.6894,
                         "brier": 0.019522, "brier_null": 0.019614,
                         "brier_skill": 0.00471, "ece": 0.00863,
                         "ece_null": 5e-05},
    "out_of_time": {"n_rows": 11871, "n_events": 245, "auc": 0.5551,
                    "brier": 0.020635, "brier_null": 0.020213,
                    "ece": 0.01196},
    "out_of_area": {"n_rows": 5544, "n_events": 32, "auc": 0.6168,
                    "brier": 0.006094, "ece": 0.01651},
}

COVARIATE_DECISION = {
    "question": "panel_source.REAL_COVARIATES was cut from five to three. "
                "Should the two be restored on the expanded panel?",
    "the_cut_rested_on_two_arguments": {
        "counting": "'49 delivery stations, 44 opening inside the window' "
                    "gives four events per parameter at five covariates.",
        "coverage": "rent_index_yoy_pct is present on 30% of pilot "
                    "ZCTA-quarters and dropping the incomplete rows took "
                    "the usable event count from 709 to 276.",
    },
    "what_changed": {
        "counting": "DEAD. The pre-expansion count is superseded: the "
                    "expanded frame attaches 540 facilities and the "
                    "three-covariate risk set carries thousands of "
                    "ZCTA-level events. Even on the conservative "
                    "metro-quarter episode count the floor of ten events "
                    "per parameter is cleared at five covariates. See "
                    "arms.*.power.",
        "coverage": "ALIVE AND WORSE. rent_index_yoy_pct's coverage falls "
                    "at national scope, because Zillow publishes for dense "
                    "urban ZIPs and the expansion is mostly not that. See "
                    "provenance.covariate_coverage_pct and "
                    "arms.new_dates_5cov.scope.pct_rows_lost_to_"
                    "missingness.",
    },
    "decision": "Run all three. new_dates_5cov restores both, as asked, and "
                "pays the coverage bill in full. new_dates_4cov restores "
                "permits_yoy_pct only -- the one the power argument blocked "
                "and the coverage argument does not -- and is the "
                "specification this evidence actually supports. "
                "new_dates_3cov is kept because it is the only arm "
                "comparable to the retired run.",
    "caveat": "The original five-tuple predates version control and is not "
              "recoverable as a literal. COVARIATES_ADDED reconstructs it "
              "from two pieces of evidence and says so where it is defined.",
    "missingness_is_not_at_random": "The rows rent_index_yoy_pct costs are "
                                    "the less dense ZCTAs, which is exactly "
                                    "the contrast the model is supposed to "
                                    "measure. A five-covariate arm is "
                                    "therefore fitted on a different "
                                    "population, not a smaller sample of "
                                    "the same one.",
}


def verdict(report: dict) -> dict:
    """The conclusion, assembled from the measurements rather than typed.

    Deliberately written so that the sentence does not depend on which way
    the AUC went. The retirement was taken on the unit of analysis, and the
    unit of analysis is measured here, not argued about.
    """
    live = {k: v for k, v in report["arms"].items() if v.get("ran")}
    load = report["provenance"]["catchment_load"]
    cal = report["calibration_against_constant"]
    auc = report["auc_across_arms"]
    best = max(live.values(),
               key=lambda a: a["held_out_by_unit"]["auc"], default=None)
    return {
        "retirement_stands": True,
        "why": "The retirement was taken on the unit of analysis, not on "
               "the sample size or the dates. One opening still switches on "
               f"a median of {load['zctas_per_opening']['median']:.0f} "
               "ZCTAs at the 15-mile catchment "
               f"(mean {load['zctas_per_opening']['mean']}, max "
               f"{load['zctas_per_opening']['max']}), and the likelihood "
               "still counts them as that many independent observations. "
               "Nothing in this run addresses that.",
        "discrimination": {
            "retired_auc": RETIRED["held_out_by_unit"]["auc"],
            "best_arm_auc": best["held_out_by_unit"]["auc"] if best else None,
            "auc_range_across_all_arms_and_holdouts":
                [auc["min"], auc["max"]],
            "reading": "AUC is a measurement of ranking, not evidence that "
                       "the probabilities may be quoted.",
        },
        "calibration": {
            "verdict": cal["verdict"],
            "n_comparisons": cal["n_comparisons"],
            "model_wins": cal["model_better_calibrated_at"],
        },
        "framing": "The honest framing of a good result and of a bad one is "
                   "the same sentence: the negative finding survives on the "
                   "best data available. That is stronger than retiring the "
                   "model on 39 events, because the obvious objection -- "
                   "'you never gave it enough data, or real dates' -- has "
                   "now been answered with a measurement.",
    }


def _arm_row(name: str, arm: dict) -> str:
    if not arm.get("ran"):
        return f"  {name:20} DID NOT RUN: {arm.get('reason', '')}"
    h, p = arm["held_out_by_unit"], arm["power"]
    t = arm["out_of_time"]
    return (f"  {name:20}{arm['risk_set']['events']:>8}"
            f"{p['n_independent_episodes']:>8}{h['auc']:>8.4f}"
            f"{h['brier']:>10.6f}{h['brier_null']:>10.6f}"
            f"{h['ece']:>9.5f}{h['ece_null']:>9.5f}"
            f"{(t.get('auc') if t.get('ran') else float('nan')):>8.4f}")


def print_report(report: dict) -> None:
    """One screen. Every line carries the null beside the model."""
    p = report["provenance"]
    load = p["catchment_load"]
    gap = p["date_gap_osha_minus_stated"]["mwpvl_dated"]
    print("\n  === hazard revival on the expanded panel ===\n")
    print(f"  panel                {p['panel']}")
    print(f"  facilities loadable  {p['facilities_loadable']}")
    print(f"  dated by the frame   {p['facilities_dated_frame']}"
          "   (MWPVL where MWPVL has one)")
    print(f"  with an OSHA bound   {p['facilities_with_osha_bound']}"
          f"   ({p['facilities_dropped_from_osha_arm']} dropped from the "
          "old-dates arm for want of one)")
    print(f"  dated both ways      {p['facilities_dated_both_ways']}"
          "   (the only clean date contrast)")
    if gap.get("n"):
        print(f"\n  the OSHA bound runs a median {gap['median_months']:.0f} "
              f"months late against the stated opening (n={gap['n']}, "
              f"{gap['pct_over_one_year']:.0f}% over a year)")
    print(f"\n  one opening switches on a median "
          f"{load['zctas_per_opening']['median']:.0f} ZCTAs "
          f"(mean {load['zctas_per_opening']['mean']}, "
          f"max {load['zctas_per_opening']['max']}); "
          f"{load['pct_zctas_served_by_2plus']}% of ZCTAs are inside two or "
          "more catchments")

    print(f"\n  {'arm':22}{'events':>8}{'episod':>8}{'AUC':>8}{'Brier':>10}"
          f"{'null':>10}{'ECE':>9}{'nullECE':>9}{'AUC_t':>8}")
    r = RETIRED
    print(f"  {'RETIRED (pilot)':20}{r['risk_set']['events']:>8}"
          f"{r['independent_episodes']:>8}"
          f"{r['held_out_by_unit']['auc']:>8.4f}"
          f"{r['held_out_by_unit']['brier']:>10.6f}"
          f"{r['held_out_by_unit']['brier_null']:>10.6f}"
          f"{r['held_out_by_unit']['ece']:>9.5f}"
          f"{r['held_out_by_unit']['ece_null']:>9.5f}"
          f"{r['out_of_time']['auc']:>8.4f}")
    for name, arm in report["arms"].items():
        print(_arm_row(name, arm))

    v = report["verdict"]
    print(f"\n  calibration against the constant null: "
          f"{report['calibration_against_constant']['verdict']} "
          f"({report['calibration_against_constant']['n_comparisons']} "
          "comparisons)")
    print(f"\n  RETIREMENT STANDS: {v['why']}\n")
    print(f"  {report['comparability']}\n")
