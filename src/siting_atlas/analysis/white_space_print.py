"""The console rendering of ``white_space.json``.

Split out so :mod:`.white_space` stays about the analysis. The tables are
printed rather than only written because a JSON artefact nobody opens is a
result nobody checks, and the named list — the thing a planner would actually
use — is the part that has to be legible without a JSON viewer.
"""

from __future__ import annotations

__all__ = ["console"]

_RULE = "  " + "-" * 74


def _coverage_table(report: dict) -> str:
    head = (f"  {'mi':>6}{'ZCTAs out':>11}{'hh out (M)':>12}"
            f"{'hh covered':>12}{'med mi':>8}  anchor")
    lines = []
    for coords in ("real", "real_plus_fallback"):
        lines.append(f"\n  coordinates: {coords}\n{head}")
        for row in report["coverage"]:
            if row["coord_set"] != coords:
                continue
            flag = " " if row["in_band"] else "*"
            lines.append(
                f" {flag}{row['radius_miles']:>5.1f}"
                f"{row['zctas_uncovered']:>11,}"
                f"{row['households_uncovered'] / 1e6:>12.1f}"
                f"{row['households_covered_pct']:>11.1f}%"
                f"{row['median_miles_to_nearest_uncovered']:>8.0f}"
                f"  {row['anchor'][:34]}")
    return "\n".join(lines)


def _named_list(report: dict, coords: str) -> str:
    row = next(r for r in report["coverage"]
               if r["coord_set"] == coords
               and r["radius_miles"] == report["headline_radius_miles"])
    lines = [f"  {'#':>3} {'ZCTA':<6}{'ST':<4}{'households':>11}  "
             f"{'mi to nearest':>13}  county / metro"]
    for i, p in enumerate(row["top_uncovered_zctas"], 1):
        where = p["cbsa_title"] or p["county_name"] or "no CBSA"
        lines.append(f"  {i:>3} {p['zcta']:<6}{p['state']:<4}"
                     f"{p['households']:>11,}"
                     f"{p['miles_to_nearest_facility']:>14.0f}  {where[:34]}")
    return "\n".join(lines)


def _metro_list(report: dict, coords: str) -> str:
    row = next(r for r in report["coverage"]
               if r["coord_set"] == coords
               and r["radius_miles"] == report["headline_radius_miles"])
    lines = [f"  {'#':>3} {'uncovered hh':>13} {'of metro':>9}  metro"]
    for i, m in enumerate(row["top_uncovered_cbsas"], 1):
        lines.append(f"  {i:>3} {m['uncovered_households']:>13,} "
                     f"{100 * m['uncovered_share_of_metro']:>8.0f}%  "
                     f"{m['cbsa_title'][:44]}")
    return "\n".join(lines)


def _backtest_table(report: dict) -> str:
    lines = [f"  {'coords':<19}{'mi':>5}{'open':>6}{'inside':>8}"
             f"{'lvl':>5}{'N':>6}{'white':>8}{'hh base':>9}{'chance':>8}"
             f"{'p':>8}"]
    for b in report["backtest"]:
        for level in ("zcta_level", "cbsa_level"):
            for r in b[level]:
                p = r["mcnemar"]["p_value"]
                lines.append(
                    f"  {b['coord_set']:<19}{b['radius_miles']:>5.1f}"
                    f"{b['openings_scored']:>6}"
                    f"{b['openings_inside_existing_coverage_pct']:>7.0f}%"
                    f"{level[:4]:>5}{r['n_flagged']:>6}"
                    f"{r['white_space_hit_rate']:>7.1f}%"
                    f"{r['household_baseline_hit_rate']:>8.1f}%"
                    f"{r['chance_hit_rate']:>7.1f}%"
                    f"{'  n/a' if p is None else f'{p:>8.3f}'}")
    return "\n".join(lines)


def _rule_race(report: dict) -> str:
    lines = [f"  {'coords':<19}{'mi':>5}  {'rule':<20}"
             f"{'metro N=10':>11}{'N=25':>7}{'N=50':>7}{'N=100':>7}"
             f"{'CBSAs/2k':>10}"]
    for r in report["rule_race"]:
        for name, cells in r["rules"].items():
            blob = r["blob_concentration_distinct_cbsas_in_top_n"][name]
            c = cells["cbsa_level"]
            lines.append(
                f"  {r['coord_set']:<19}{r['radius_miles']:>5.1f}  "
                f"{name:<20}{c['N_10']:>10.1f}%{c['N_25']:>6.1f}%"
                f"{c['N_50']:>6.1f}%{c['N_100']:>6.1f}%{blob['top_2000']:>10}")
        ch = r["chance_cbsa"]
        lines.append(f"  {'':<19}{'':>5}  {'(chance)':<20}"
                     f"{ch['N_10']:>10.1f}%{ch['N_25']:>6.1f}%"
                     f"{ch['N_50']:>6.1f}%{ch['N_100']:>6.1f}%{'':>10}")
    return "\n".join(lines)


def _multiplicity(report: dict) -> str:
    m = report["why_it_failed"]["multiple_comparisons"]
    return (f"MULTIPLICITY GUARD: {m['paired_tests_run']} post-hoc paired "
            f"tests on one hold-out; {m['expected_significant_by_chance']} "
            f"significant cells expected by chance at p<{m['alpha']}. "
            f"Observed {m['significant_in_favour_of_an_alternative_rule']} "
            f"favouring an alternative rule and "
            f"{m['significant_in_favour_of_the_household_baseline']} "
            f"favouring the household baseline.")


def console(report: dict) -> str:
    """The whole report as one printable block."""
    head = report["headline_radius_miles"]
    board = report["scoreboard"]
    n_named = len(next(r for r in report["coverage"]
                       if r["radius_miles"] == head)["top_uncovered_zctas"])
    return (
        f"\n  === white space: where is there unserved demand? ===\n"
        f"\n  {report['geometry']}\n"
        f"\n  1. COVERAGE BY RADIUS   (* = over-run probe, outside the band)"
        f"\n{_coverage_table(report)}\n"
        f"\n{_RULE}\n"
        f"\n  2. THE NAMED LIST — top {n_named} uncovered ZCTAs at "
        f"{head:.0f} miles, real coordinates only\n"
        f"{_named_list(report, 'real')}\n"
        f"\n     ... and with the ZCTA-centroid fallbacks included:\n"
        f"{_named_list(report, 'real_plus_fallback')}\n"
        f"\n{_RULE}\n"
        f"\n  3. THE SAME GAP, ROLLED UP TO METROS at {head:.0f} miles "
        f"(real_plus_fallback)\n{_metro_list(report, 'real_plus_fallback')}\n"
        f"\n{_RULE}\n"
        f"\n  4. BACK-TEST — coverage from pre-2024 facilities only, scored\n"
        f"     on 2024-25 delivery-station openings\n"
        f"{_backtest_table(report)}\n"
        f"\n     'inside' = share of the held-out openings that landed inside"
        f"\n     coverage the pre-2024 network ALREADY had. 'p' is a two-sided"
        f"\n     exact McNemar on the openings the two rules disagree about.\n"
        f"\n  white space wins {board['white_space_wins']} of "
        f"{board['cells_scored']} cells. p<0.05 in white space's favour: "
        f"{board['significant_wins_for_white_space']}; in the household "
        f"baseline's: {board['significant_wins_for_the_household_baseline']}."
        f"\n"
        f"\n{_RULE}\n"
        f"\n  5. WHY IT FAILED — five ranking rules on the same openings\n"
        f"{_rule_race(report)}\n"
        f"\n     'CBSAs/2k' = distinct metros inside the rule's top 2,000"
        f"\n     ZCTAs, which is how spatially smooth a rule is. "
        f"'demand_in_radius'\n     is 'coverage_gain' with the coverage mask "
        f"removed and nothing else\n     changed, so the gap between those "
        f"two rows is the mask's doing.\n"
        f"\n  {_multiplicity(report)}\n"
        f"\n  {report['why_it_failed']['conclusion']}\n"
        f"\n{_RULE}\n\n  VERDICT\n\n  {report['verdict']}\n"
        f"\n  {report['falsification']}\n")
