"""Console report for `gravity_network.json`.

Separate from the runner for the reason `panel_print` is separate from
`panel_experiments`: the tables can then be regenerated from the artefact
alone, without refitting anything, so a number in the prose can always be
traced to a stored field rather than to a run nobody can repeat.

    import json
    from siting_atlas.models.gravity_print import report_text
    print(report_text(json.load(open("outputs/metrics/gravity_network.json"))))
"""

from __future__ import annotations

from .panel_strata import BUCKETS, MIN_INFORMATIVE

__all__ = ["report_text"]

_LABEL = {"small_le25": "J<=25", "mid_26_100": "26-100",
          "large_gt100": "J>100"}

_STATE = {"INTERIOR": "INTERIOR", "AT THE BOUNDARY": "AT THE BOUNDARY",
          "boundary inside the interval": "boundary inside"}


def _f(x, spec: str = ".4f") -> str:
    return "--" if x is None else format(x, spec)


def _header(r: dict) -> list[str]:
    t = r["terms"]
    p = t["placement"]
    return [
        "",
        "=" * 78,
        "  GRAVITY TERMS OVER THE AMAZON NON-DELIVERY-STATION NETWORK",
        "=" * 78,
        f"  facility arm {r['facility_arm']}, {r['checks']['n_decisions']} "
        f"decisions, {r['checks']['n_alternatives']} alternatives, "
        f"{r['repeats']} re-splits, seed {r['seed']}",
        f"  identical decision sets across all arms: "
        f"{r['checks']['decision_sets_identical']};  warehousing column "
        f"identical: {r['checks']['warehousing_identical']}",
        f"  network: {p['kept']} of {p['non_ds_us_rows']} non-DS US "
        f"facilities placed in space AND time "
        f"({p['excluded_no_numeric_open_year']} undated, "
        f"{p['excluded_postcode_not_a_panel_zcta']} not a panel ZCTA)",
        f"  {t['vintages']} annual vintages over {t['candidate_zctas']} "
        "candidate ZCTAs; a decision sees only facilities already open",
        f"  square footage stated for {t['square_feet_stated']} of "
        f"{t['placeable_facilities']} placeable facilities "
        f"({100 * t['square_feet_stated_share']:.1f}%)",
    ] + [
        f"      {kind:<11} {v['placeable']:>4} placeable, "
        f"{v['square_feet_stated']:>4} with sq ft, median "
        f"{_f(v['median_square_feet'], ',.0f')}"
        for kind, v in t["by_type"].items()
    ]


def _drift(r: dict) -> list[str]:
    """Level growth, and the within-metro dispersion that decides grain."""
    d = r["terms"]["dispersion"]
    cv = d["mean_within_metro_cv"]
    lines = ["", "  1. LEVEL DRIFT, AND WITHIN-METRO DISPERSION",
             "     A gravity term grows as the network grows. In "
             "P_j = beta'a_j / sum_k beta'a_k a shift common to a choice",
             "     set does NOT cancel; it flattens the distribution "
             "towards uniform.",
             "     `cv` is the mean within-CBSA sd/mean at vintage "
             f"{d['vintage']} over the {d['large_metros']} metros with "
             f">= {d['large_metro_min_candidates']}",
             "     candidate ZCTAs. A conditional logit differences away "
             "everything BETWEEN metros, so this column",
             "     is the whole of what the covariate has to work with "
             "(COVARIATES_TRIED.md SS1.1).",
             "",
             "       column                                    2017      "
             "2020      2030        cv"]
    drift = r["terms"]["mean_by_vintage"]
    for col in list(cv):
        vals = "".join(f"{_f(v, '10.4f')}" for v in
                       drift.get(col, {}).values()) or " " * 30
        lines.append(f"       {col:<40}{vals}{_f(cv[col], '10.4f')}")
    return lines


def _coefficients(r: dict) -> list[str]:
    lines = [
        "",
        "  2. COEFFICIENTS  (ratio to households, the numeraire)",
        "     The bracket is the 2.5-97.5 PERCENTILE OVER RE-SPLITS. "
        "It is NOT a standard error.",
        "     A beta at or below 1e-6 is the positivity boundary, not a "
        "finding: choice.py sets beta = exp(theta).",
        "",
        f"       {'arm':<30}{'covariate':<40}{'beta':>9}"
        f"{'p2.5':>9}{'p97.5':>9}  verdict"]
    for name, arm in r["arms"].items():
        first = True
        for cov, v in arm["verdicts"].items():
            lines.append(
                f"       {name if first else '':<30}{cov:<40}"
                f"{_f(v['beta_mean']):>9}{_f(v['p025']):>9}"
                f"{_f(v['p975']):>9}  {_STATE[v['state']]}")
            first = False
    return lines


def _census(r: dict) -> list[str]:
    n = r["repeats"]
    lines = [
        "",
        "  3. BOUNDARY CENSUS -- the strict version of \"interior\"",
        f"     A 2.5th percentile cannot say \"interior in ALL {n} "
        f"re-splits\". This refits the same {n} training",
        "     halves and counts. `reproduces` = the census percentiles "
        "match the harness's, so it is the same fits.",
        ""]
    for name, block in r["boundary_census"].items():
        lines.append(f"       {name}   (reproduces harness percentiles: "
                     f"{block['reproduces_harness_percentiles']})")
        for cov, v in block["columns"].items():
            flag = "INTERIOR IN ALL" if v["interior_in_all_resplits"] else ""
            lines.append(
                f"         {cov:<42}"
                f"{v['resplits_at_boundary']:>3} of {v['resplits']} at the "
                f"boundary   min beta {_f(v['min_beta'], '.3e')}   {flag}")
    return lines


def _lift(r: dict) -> list[str]:
    lines = [
        "",
        "  4. TOP-10 LIFT, STRATIFIED BY CHOICE-SET SIZE, against the "
        f"baseline arm `{r['baseline_arm']}`",
        f"     n is DISTINCT DECISIONS. A stratum under {MIN_INFORMATIVE} "
        "distinct decisions is THIN and is NOT compared:",
        f"     {r['repeats']} re-splits of 7 decisions hold 7 decisions' "
        "worth of information however many evaluations they make.",
        "     All arms hold the same decisions and the same splits, so the "
        "chance rate is identical across arms",
        "     and a lift difference is a model difference.",
        ""]
    head = "".join(f"{_LABEL[n]:>26}" for n, _, _ in BUCKETS)
    lines.append(f"       {'arm':<32}{head}")
    top10 = r["arms"][r["baseline_arm"]]["strata"]["top10"]
    ns = ""
    for name, _, _ in BUCKETS:
        cell = top10[name]
        tag = f"n={cell['decisions']}" + ("" if cell["informative"]
                                          else " THIN")
        ns += f"{tag:>26}"
    lines.append(f"       {'':<32}{ns}")
    for name, arm in r["arms"].items():
        cells = ""
        for bucket, _, _ in BUCKETS:
            cell = arm["top10_lift_vs_baseline"][bucket]
            if not cell["informative"]:
                cells += f"{_f(cell['lift'], '.2f') + 'x THIN':>26}"
            elif name == r["baseline_arm"]:
                cells += f"{_f(cell['lift'], '.2f') + 'x':>26}"
            else:
                cells += (f"{_f(cell['lift'], '.2f')}x "
                          f"({_f(cell['lift_delta'], '+.2f')})").rjust(26)
        lines.append(f"       {name:<32}{cells}")
    return lines


def _paired(r: dict) -> list[str]:
    lines = [
        "",
        "  5. PAIRED DIFFERENCE AGAINST THE BASELINE, over the re-splits",
        "     Paired: identical decisions, identical seeds. NOT a sign "
        "test -- the re-splits are not independent.",
        "",
        f"       {'arm':<32}{'d top1':>10}{'d top5':>10}{'d top10':>10}"
        f"{'sd(top10)':>11}{'W-L top10':>11}{'d Brier':>12}"]
    for name, arm in r["arms"].items():
        p = arm["paired_vs_baseline"]
        if p is None:
            lines.append(f"       {name:<32}{'(the baseline)':>10}")
            continue
        wl = (f"{p['top10']['repeats_improved']}-"
              f"{p['top10']['repeats_worsened']}")
        lines.append(
            f"       {name:<32}"
            f"{_f(p['top1']['paired_mean_difference'], '+.4f'):>10}"
            f"{_f(p['top5']['paired_mean_difference'], '+.4f'):>10}"
            f"{_f(p['top10']['paired_mean_difference'], '+.4f'):>10}"
            f"{_f(p['top10']['paired_sd'], '.4f'):>11}{wl:>11}"
            f"{_f(p['brier']['paired_mean_difference'], '+.7f'):>12}")
    return lines


def _verdict(r: dict) -> list[str]:
    best = r["best_gravity"]
    large = BUCKETS[2][0]
    base_lift = r["arms"][r["baseline_arm"]]["strata"]["top10"][large]["lift"]
    return [
        "",
        "  6. VERDICT",
        f"     best gravity arm by the pre-stated rule: {best['arm']}",
        f"     both gravity columns interior: {best['both_columns_interior']}"
        f"   (any gravity arm fully interior: "
        f"{best['any_gravity_arm_fully_interior']})",
        f"     large-stratum top-10 lift "
        f"{_f(best['large_stratum_top10_lift'], '.3f')}x against the "
        f"baseline's {_f(base_lift, '.3f')}x",
        "",
        "     " + r["aggregation_invariance_cost"].replace(
            ". ", ".\n     "),
        "",
        "     " + r["spread_is_not_a_standard_error"].replace(
            ". ", ".\n     "),
    ]


def report_text(report: dict) -> str:
    parts = (_header(report) + _drift(report) + _coefficients(report)
             + _census(report) + _lift(report) + _paired(report)
             + _verdict(report))
    return "\n".join(parts) + "\n"
