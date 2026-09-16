"""The console report for `network_inference`, regenerable from the JSON.

Every number printed here is read out of the artefact. Nothing is
recomputed, so the table and the file cannot disagree, and a reader who
wants the table without a two-hour refit can get it with

    import json
    from siting_atlas.models.network_print import report_text
    print(report_text(json.load(open(
        "outputs/metrics/network_inference.json"))))
"""

from __future__ import annotations

from .choice import CBP_ATTRACTIONS
from .panel_network import NETWORK_COLUMNS
from .panel_strata import MIN_INFORMATIVE

WAREHOUSING = CBP_ATTRACTIONS[0]

#: The three parameters the claim is about.
FOCUS = (WAREHOUSING, *NETWORK_COLUMNS[:2])

SHORT = {WAREHOUSING: "warehousing", "sortation_proximity": "sortation_prox",
         "fulfilment_proximity": "fulfilment_prox",
         "network_within_50mi": "network_50mi",
         "land_area_sqmi": "land_area", "establishments": "establishments"}

__all__ = ["FOCUS", "report_text"]


def _span(ci: dict, boundary: bool) -> str:
    if boundary:
        return f"one-sided, < {ci['upper']:.4f}"
    return f"[{ci['lower']:.4f}, {ci['upper']:.4f}]"


def _verdict(ci: dict, boundary: bool) -> str:
    """Which SIDE of the numeraire, because the side is the whole point.

    `choice_inference._interval` sets one flag for both, so a proximity
    whose upper end is 0.26 and a warehouse coefficient whose lower end
    is 1.04 both come back "excludes 1.0". Printing them with the same
    words is how the second gets mistaken for the first.
    """
    if boundary:
        return "BOUNDARY"
    if not ci["excludes_ratio_one"]:
        return "contains 1.0"
    return "ABOVE 1.0" if ci["lower"] > 1.0 else "below 1.0"


def _intervals(out: list, block: dict) -> None:
    pub = block.get("published_resplit_spread", {})
    out.append(f"  {block['n_decisions']} decisions in {block['n_metros']} "
               f"metros, {block['n_alternatives']:,} alternatives")
    reps = block["replicates"]
    out.append("  bootstrap: " + ", ".join(
        f"{v['replicates']} over {k} in {v['seconds'] / 60:.0f} min "
        f"(capped={v['capped']})" for k, v in reps.items()))
    out.append("")
    out.append(f"    {'covariate':18}{'beta':>9}{'over metros':>22}"
               f"{'verdict':>15}{'over decisions':>22}")
    for name, p in block["parameters"].items():
        b = p["at_boundary"]
        dec = p.get("bootstrap_over_decisions")
        out.append(
            f"    {SHORT.get(name, name):18}{p['beta_point']:>9.4f}"
            f"{_span(p['bootstrap_over_metros'], b):>22}"
            f"{_verdict(p['bootstrap_over_metros'], b):>15}"
            f"{('not run' if dec is None else _span(dec, b)):>22}")
    if pub.get("available"):
        out.append("")
        out.append(f"    the published re-split percentile spread, for "
                   f"comparison only ({pub['repeats']} re-splits,")
        out.append(f"    {pub['n_fitted_decisions_per_repeat']} decisions "
                   f"fitted in each). NOT A STANDARD ERROR.")
        for name in block["parameters"]:
            if name not in pub["beta_p025"]:
                continue
            lo, hi = pub["beta_p025"][name], pub["beta_p975"][name]
            span = f"[{lo:.4f}, {hi:.4f}]"
            out.append(f"    {SHORT.get(name, name):18}"
                       f"{pub['beta_mean'][name]:>9.4f}{span:>22}")


def _mcse(out: list, block: dict) -> None:
    out.append("")
    out.append("    Monte Carlo error of the metro-clustered endpoints. An "
               "endpoint whose distance")
    out.append("    from 1.0 is small against its own MC error is a verdict "
               "more replicates could flip.")
    out.append(f"    {'covariate':18}{'lower':>10}{'mcse':>10}"
               f"{'upper':>10}{'mcse':>10}{'|lo-1|/mcse':>14}")
    for name in FOCUS:
        p = block["parameters"].get(name)
        if p is None or "metro_endpoint_mcse" not in p:
            continue
        e = p["metro_endpoint_mcse"]
        # A Monte Carlo error of machine zero means the endpoint is
        # pinned at the positivity boundary in every resample. Dividing
        # by it prints 5.6e17 where the honest answer is that the ratio
        # is not defined.
        margin = (f"{abs(e['lower'] - 1.0) / e['mcse_lower']:.1f}"
                  if e["mcse_lower"] > 1e-12 else "pinned at 0")
        out.append(f"    {SHORT.get(name, name):18}{e['lower']:>10.4f}"
                   f"{e['mcse_lower']:>10.4f}{e['upper']:>10.4f}"
                   f"{e['mcse_upper']:>10.4f}{margin:>14}")


def _sandwich(out: list, block: dict) -> None:
    for key, label in (("sandwich_over_decisions",
                        "SANDWICH, independent decisions "
                        "(choice_sandwich, as published)"),
                       ("sandwich_over_metros",
                        "SANDWICH, clustered by metro (network_sandwich)")):
        out.append("")
        out.append(f"  {label}")
        meta = block[key].get("_meta")
        if meta:
            out.append(f"    {meta['n_clusters']} clusters, "
                       f"{meta['n_decisions']} decisions; small-cluster "
                       f"correction NOT applied "
                       f"({meta['small_cluster_correction_not_applied']:.4f})")
        for name, s in block[key].items():
            if name == "_meta":
                continue
            if not s["available"]:
                out.append(f"    {SHORT.get(name, name):18}REFUSED at the "
                           f"boundary (beta = {s['beta']:.2e})")
                continue
            ratio = s.get("se_ratio_vs_independent_decisions")
            tail = "" if ratio is None else f"   se x{ratio:.3f}"
            out.append(f"    {SHORT.get(name, name):18}"
                       f"[{s['lower']:.4f}, {s['upper']:.4f}]   "
                       f"z vs 1.0 = {s['z_against_ratio_one']:>6.2f}   "
                       f"p = {s['p_two_sided_against_ratio_one']:.4f}{tail}")


def _sensitivity(out: list, s: dict) -> None:
    """How far the point estimates move when two facilities come out."""
    out.append("")
    out.append(f"  facility-set sensitivity: {s['draws']} refits, each "
               f"dropping one random sortation centre")
    out.append(f"  and one random fulfilment centre from the "
               f"{s['facilities_placed']} that can be placed")
    out.append(f"    {'covariate':18}{'mean':>10}{'min':>10}{'max':>10}"
               f"{'range':>10}")
    for name in FOCUS:
        b = s["beta"].get(name)
        if b is None:
            continue
        out.append(f"    {SHORT.get(name, name):18}{b['mean']:>10.4f}"
                   f"{b['min']:>10.4f}{b['max']:>10.4f}{b['range']:>10.4f}")


def _merger(out: list, m: dict) -> None:
    out.append("")
    out.append("## 2. What the invariance break costs, measured")
    out.append("")
    out.append("  Merge one pair of ZCTAs at a time and compare P(merged) "
               "with P(j) + P(k).")
    out.append("  Train §3.4 Example 2 makes this exactly zero when every "
               "attraction is a count.")
    out.append("")
    out.append(f"    {'specification':28}{'pairs':>8}{'median':>12}"
               f"{'p90':>12}{'max':>12}")
    for key, label in (("extensive_only_control", "combined (control)"),
                       ("network", "combined_plus_network")):
        e = m[key]["abs_relative_probability_error"]
        out.append(f"    {label:28}{m[key]['pairs_merged']:>8,}"
                   f"{e['median']:>12.2e}{e['p90']:>12.2e}"
                   f"{e['max']:>12.2e}")
    leak = m["network"]["attraction_lost_share"]
    out.append(f"    attraction lost per merged pair, network arm: median "
               f"{leak['median']:.3%}, max {leak['max']:.3%}")
    out.append("")
    out.append("  And the estimate itself, refitted under randomly redrawn "
               "ZCTA maps:")
    out.append("")
    out.append(f"    {'specification':28}{'beta':>9}{'merged mean':>13}"
               f"{'min':>9}{'max':>9}{'mean |shift|':>14}")
    for label, v in m["drift_under_a_redrawn_map"].items():
        out.append(f"    {label:28}{v['beta_unmerged']:>9.4f}"
                   f"{v['beta_merged_mean']:>13.4f}{v['beta_merged_min']:>9.4f}"
                   f"{v['beta_merged_max']:>9.4f}"
                   f"{v['mean_absolute_shift_pct_of_point']:>13.1f}%")


def _strata(out: list, arm: dict) -> None:
    three = arm.get("three_measures")
    if not three:
        return
    out.append("")
    out.append("  top-10 lift over min(10,J)/J, per stratum, with DISTINCT "
               f"decisions. Fewer than {MIN_INFORMATIVE} is THIN")
    out.append("  and is not compared. The standardised column is printed "
               "and must not be ranked on.")
    for method, block in three["methods"].items():
        out.append("")
        out.append(f"    {method}")
        for name, cell in block["strata"].items():
            if cell["lift"] is None:
                out.append(f"      {name:14}no decisions")
                continue
            thin = "" if cell["informative"] else "   THIN"
            out.append(f"      {name:14}lift {cell['lift']:.2f}x   "
                       f"n={cell['decisions']:<5} model "
                       f"{cell['model_rate']:.3f}  chance "
                       f"{cell['chance_rate']:.3f}{thin}")
        std = block["standardised_top10"]
        out.append(f"      {'standardised':14}"
                   f"{std['lift']:.2f}x   (not a ranking)")
        out.append(f"      {'Brier':14}{block['raw_pooled']['brier']:.6f}")


def report_text(r: dict) -> str:
    out: list[str] = []
    out.append("")
    out.append("# NETWORK ARM, PROPER INFERENCE")
    out.append(f"  seed {r['seed']}, replicate cap {r['replicate_cap']}, "
               f"{r['repeats']} re-splits for the prediction measures")
    out.append(f"  stages completed: "
               f"{', '.join(r.get('stages_completed', ['none']))}")
    agree = r.get("parallel_matches_sequential")
    if agree:
        out.append(f"  parallel driver matches the sequential one to "
                   f"{agree['max_abs_difference_in_beta']:.2e} in beta over "
                   f"{agree['replicates_compared']} replicates")
    out.append("")
    out.append("## 1. combined_plus_network")
    _intervals(out, r["arms"]["combined_plus_network"])
    _mcse(out, r["arms"]["combined_plus_network"])
    _sandwich(out, r["arms"]["combined_plus_network"])
    if "facility_set_sensitivity" in r:
        _sensitivity(out, r["facility_set_sensitivity"])
    if "merger_invariance" in r:
        _merger(out, r["merger_invariance"])
    out.append("")
    out.append("## 3. mwpvl_clean_plus_network, the arm nobody ran")
    _intervals(out, r["arms"]["mwpvl_clean_plus_network"])
    _mcse(out, r["arms"]["mwpvl_clean_plus_network"])
    _sandwich(out, r["arms"]["mwpvl_clean_plus_network"])
    _strata(out, r["arms"]["mwpvl_clean_plus_network"])
    return "\n".join(out)
