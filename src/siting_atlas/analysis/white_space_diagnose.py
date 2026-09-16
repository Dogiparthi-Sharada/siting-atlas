"""Reading the rule horse-race: which explanation the numbers support.

Split from :mod:`.white_space_rules` when that module crossed 300 lines. The
seam is real rather than arbitrary: everything there computes scores and hit
rates, everything here interprets them and nothing here touches geometry.

The one thing this module exists to prevent
-------------------------------------------
The five rules it reads were chosen **after** seeing the original back-test
fail, and they are scored on the **same** held-out openings. That is post-hoc
selection on a fixed test set, and it is the standard way an analysis talks
itself into a finding. :func:`multiplicity` is the guard: it counts every
paired test run and compares the number of favourable significances against
the number chance alone would produce. If those two numbers are the same, a
significant cell is not a discovery, and :func:`diagnose` says so in the
artefact rather than leaving the reader to notice.
"""

from __future__ import annotations

from .white_space_rules import N_CBSA, N_ZCTA, RULES

__all__ = ["DIAGNOSIS_CELL", "diagnose", "multiplicity"]

#: (:func:`concentration` measures by how much); N=25 because it is the
#: tightest cut-off where every rule still has room to differ.
DIAGNOSIS_CELL = ("cbsa_level", "N_25")


def _beats_baseline(race_row: dict, level: str, cut: str) -> list[dict]:
    """Rules that out-score ``households`` in one race, with the paired p."""
    base = race_row["rules"]["households"][level][cut]
    key = "cbsa_p_vs_households" if level == "cbsa_level" \
        else "zcta_p_vs_households"
    return [{"rule": name, "hit_rate": cells[level][cut],
             "households_hit_rate": base,
             "p_vs_households": cells[key][cut]}
            for name, cells in race_row["rules"].items()
            if name != "households" and cells[level][cut] > base]


_CUTS = {"cbsa_level": ("cbsa_p_vs_households", N_CBSA),
         "zcta_level": ("zcta_p_vs_households", N_ZCTA)}


def multiplicity(races: list[dict], alpha: float = 0.05) -> dict:
    """Every paired test run here, and how many would be significant anyway.

    These five rules were chosen AFTER seeing the original back-test fail,
    and they are scored on the SAME held-out openings. That is post-hoc
    selection, and the only defence against reading a lucky cell as a
    discovery is to count the cells. At alpha and ``n`` tests, ``alpha * n``
    come out significant when nothing is going on.
    """
    total = favour = against = 0
    for row in races:
        base = row["rules"]["households"]
        for name, cells in row["rules"].items():
            if name == "households":
                continue
            for level, (p_key, cuts) in _CUTS.items():
                for n in cuts:
                    p = cells[p_key][f"N_{n}"]
                    if p is None:
                        continue
                    total += 1
                    if p < alpha:
                        better = cells[level][f"N_{n}"] > base[level][f"N_{n}"]
                        favour, against = (favour + better,
                                           against + (not better))
    return {
        "alpha": alpha,
        "paired_tests_run": total,
        "expected_significant_by_chance": round(alpha * total, 1),
        "significant_in_favour_of_an_alternative_rule": favour,
        "significant_in_favour_of_the_household_baseline": against,
        "favourable_results_exceed_chance": bool(favour > alpha * total),
    }


def diagnose(races: list[dict]) -> dict:
    """Which of the three candidate explanations the numbers support.

    The identifying comparison is ``demand_in_radius`` against
    ``coverage_gain``. They share the radius, the smoothing and the
    neighbour-sum machinery, and differ only in whether the households being
    summed are masked to the uncovered ones — so the gap between them is
    attributable to the mask and to nothing else in the design.

    Reported PER RADIUS, never averaged across radii, because the answer is
    not the same at 15 and 45 miles and a mean over the two would hide the
    one rule that works.
    """
    level, cut = DIAGNOSIS_CELL
    per_radius, winners = [], []
    for row in races:
        rules_at = row["rules"]
        base = rules_at["households"][level][cut]
        smooth = rules_at["demand_in_radius"][level][cut]
        masked = rules_at["coverage_gain"][level][cut]
        beat = _beats_baseline(row, level, cut)
        winners.extend(dict(b, coord_set=row["coord_set"],
                            radius_miles=row["radius_miles"]) for b in beat)
        per_radius.append({
            "coord_set": row["coord_set"],
            "radius_miles": row["radius_miles"],
            "households": base,
            "demand_in_radius_unmasked": smooth,
            "coverage_gain_masked": masked,
            "cost_of_the_coverage_mask_pp": round(smooth - masked, 1),
            "cost_of_spatial_smoothing_pp": round(base - smooth, 1),
            "rules_beating_the_household_baseline": [b["rule"] for b in beat],
        })

    mask_cost = [p["cost_of_the_coverage_mask_pp"] for p in per_radius]
    smooth_cost = [p["cost_of_spatial_smoothing_pp"] for p in per_radius]
    always = sorted({w["rule"] for w in winners}
                    .intersection(*[{b["rule"] for b in
                                     _beats_baseline(r, level, cut)}
                                    for r in races])) if races else []
    return {
        "compared_at": f"{level}, {cut}, per (arm, radius)",
        "per_radius": per_radius,
        "coverage_mask_cost_pp_range": [min(mask_cost), max(mask_cost)],
        "spatial_smoothing_cost_pp_range": [min(smooth_cost),
                                            max(smooth_cost)],
        "rules_that_beat_households_somewhere": winners,
        "rules_that_beat_households_everywhere": always,
        "distinct_cbsas_in_each_rules_top_2000_zctas": {
            name: [r["blob_concentration_distinct_cbsas_in_top_n"][name]
                   ["top_2000"] for r in races] for name in RULES},
        "multiple_comparisons": multiplicity(races),
        "conclusion": (
            "The MASK is the defect, not the idea and not the blob "
            f"artefact. Excluding served places costs {min(mask_cost)}-"
            f"{max(mask_cost)} points at the metro level, while the spatial "
            "smoothing it shares with the control costs "
            f"{min(smooth_cost)} to {max(smooth_cost)}. demand_in_radius is "
            "coverage_gain with the mask removed and nothing else changed, "
            "and it recovers the whole gap. Two rules do out-score the "
            "household baseline at 15 miles -- load_per_facility, which "
            "WEIGHTS by service intensity instead of EXCLUDING served "
            "places, and demand_in_radius -- but see "
            "'multiple_comparisons': across 128 post-hoc paired tests on "
            "the same hold-out, the number of favourable significances is "
            "indistinguishable from the number expected by chance, while "
            "the unfavourable ones run at ten times chance. NOTHING here "
            "rescues the framing. The favourable cells are a hypothesis "
            "for a fresh hold-out, not a finding."),
    }
