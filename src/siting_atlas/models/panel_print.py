"""Console rendering for `panel_experiments`. No measurement happens here.

Split out for the reason `gbm_report.py` was: a runner that both measures
and formats grows past the point where either half can be read, and a
printer that computes anything can disagree with the artefact.
"""

from __future__ import annotations

from .panel_strata import BUCKETS, MIN_INFORMATIVE


def _fmt(value, spec: str = "6.3f", blank: str = "    --") -> str:
    return blank if value is None else format(value, spec)


def _header(report: dict) -> list[str]:
    net = report["network_covariates"]
    return [
        "",
        "  === panel composition experiments ===",
        f"  {report['repeats']} paired re-splits, seed {report['seed']}, "
        "every method refitted inside every repeat",
        "",
        f"  network covariates: {net['kept']} of {net['non_ds_us_rows']} "
        "non-DS US facilities placed in space and time",
        f"    excluded {net['excluded_no_numeric_open_year']} with no "
        f"numeric open_year, {net['excluded_postcode_not_a_panel_zcta']} "
        "whose postcode is not a panel ZCTA",
        "",
    ]


def _sizes(report: dict) -> list[str]:
    lines = ["  SAMPLE AND MARKET MIX  (share of decisions by choice-set "
             "size)", f"    {'arm':24}{'facs':>6}{'decisions':>11}"
             f"{'<=25':>9}{'26-100':>9}{'>100':>8}{'median J':>10}"]
    for name, arm in report["arms"].items():
        mix = arm["size_mix"]
        lines.append(
            f"    {name:24}{arm['ledger']['facilities_loaded']:>6}"
            f"{arm['n_decisions']:>11}"
            + "".join(f"{100 * mix[b]:>8.1f}%" for b, _, _ in BUCKETS)
            + f"{arm['choice_set']['median']:>10.0f}")
    return [*lines, ""]


def _ledger(report: dict) -> list[str]:
    lines = ["  WHERE THE FACILITIES GO  (emitted, not measured by hand -- "
             "NOTES_EXPANDED_REFIT.md Sec.8 item 3)",
             f"    {'arm':24}{'loaded':>8}{'no ZCTA':>9}{'no year':>9}"
             f"{'no vintage':>12}{'fitted':>8}"]
    for name, arm in report["arms"].items():
        led = arm["ledger"]
        lines.append(
            f"    {name:24}{led['facilities_loaded']:>8}"
            f"{led['dropped_no_panel_zcta']:>9}"
            f"{led['dropped_no_numeric_open_year']:>9}"
            f"{led['dropped_no_earlier_cbp_vintage']:>12}"
            f"{arm['n_decisions']:>8}")
    return [*lines, ""]


def _lift(report: dict, method: str) -> list[str]:
    ref = report["reference_mix_arm"]
    lines = [f"  TOP-10 LIFT OVER CHANCE, STRATIFIED  [{method}]",
             "  chance is min(10,J)/J, the expected hit rate of a uniform "
             "guess. n is DISTINCT",
             f"  decisions; a stratum holding fewer than {MIN_INFORMATIVE} "
             "is marked THIN and is NOT compared.",
             f"    {'arm':24}" + "".join(f"{b:>18}" for b, _, _ in BUCKETS)
             + f"{'std. to ' + ref:>20}"]
    for name, arm in report["arms"].items():
        cells = arm["methods"][method]["strata"]["top10"]
        row = f"    {name:24}"
        for bucket, _, _ in BUCKETS:
            c = cells[bucket]
            tag = "" if c["informative"] else " THIN"
            cell = f"{_fmt(c['lift'], '.2f', '--')}x n={c['decisions']}{tag}"
            row += f"{cell:>18}"
        std = arm["methods"][method]["standardised"]["top10"]
        row += f"{_fmt(std and std['lift'], '19.2f')}x"
        lines.append(row)
    return [*lines, ""]


def _raw(report: dict, method: str) -> list[str]:
    lines = [f"  RAW POOLED RATES  [{method}]  -- NOT comparable across arms",
             f"    {'arm':24}{'top-1':>9}{'top-5':>9}{'top-10':>9}"
             f"{'sd(top10)':>11}{'Brier':>11}{'null Brier':>12}"]
    for name, arm in report["arms"].items():
        m = arm["methods"][method]
        raw, sd = m["raw_pooled"], m["raw_pooled_sd"]
        null = arm["empirical_uniform_null"]
        lines.append(
            f"    {name:24}{raw['top1']:>9.3f}{raw['top5']:>9.3f}"
            f"{raw['top10']:>9.3f}{sd['top10']:>11.3f}"
            f"{raw['brier']:>11.6f}{null['brier']:>12.6f}")
    return [*lines, ""]


#: `choice.py` parameterises beta_k = exp(theta_k), so a covariate the
#: optimiser wants to discard is pushed towards theta = -inf and beta
#: lands at 1e-15 or below rather than at an interior value. Such a
#: coefficient formally "excludes 1.0" and that is meaningless: it is a
#: boundary solution, the Hessian there is not the information matrix,
#: and `choice_inference` already refuses to put a sandwich interval on
#: it. Anything below this is called a boundary rather than a finding.
BOUNDARY = 1e-6


def verdict(lo: float, hi: float) -> str:
    """How to read one interval against the numeraire. Derived, in full,
    from the two percentiles the artefact holds."""
    if hi < BOUNDARY:
        return "  AT THE BOUNDARY (beta ~ 0), not a finding"
    if not (lo > 1.0 or hi < 1.0):
        return ""
    return ("  excludes 1.0, boundary INSIDE the interval" if lo < BOUNDARY
            else "  EXCLUDES 1.0")


def _coefficients(report: dict) -> list[str]:
    lines = ["  COEFFICIENTS  (ratio to households, the numeraire; 2.5-97.5 "
             "percentile over re-splits)",
             "  The null that matters is 1.0. Nothing that spans it is "
             "distinguishable from a household,",
             f"  and nothing below beta = {BOUNDARY:g} has escaped the "
             "positivity boundary."]
    for name, arm in report["arms"].items():
        lines.append(f"    {name}")
        for cov in arm["beta_mean"]:
            lo, hi = arm["beta_p025"][cov], arm["beta_p975"][cov]
            lines.append(f"      {cov:26}{arm['beta_mean'][cov]:10.4f}  "
                         f"[{lo:8.4f}, {hi:8.4f}]  width {hi - lo:8.4f}"
                         f"{verdict(lo, hi)}")
    return [*lines, ""]


def _network(report: dict) -> list[str]:
    gain = report["network_gain"]
    if not gain["comparable"]:
        return ["  NETWORK COVARIATES: not comparable -- " + gain["reason"],
                ""]
    lines = ["  WHAT THE NETWORK COVARIATES BOUGHT  (paired: same "
             "decisions, same 50 splits)",
             "  The only valid paired comparison in this file. W-L is not a "
             "sign test: the",
             "  re-splits resample the same decisions and are not "
             "independent.",
             f"    {'method':24}{'d top-1':>10}{'d top-5':>10}"
             f"{'d top-10':>10}{'sd':>8}{'better/worse':>14}{'d Brier':>12}"]
    for method, rows in gain["methods"].items():
        ten = rows["top10"]
        record = f"{ten['repeats_improved']}-{ten['repeats_worsened']}"
        lines.append(
            f"    {method:24}"
            f"{rows['top1']['paired_mean_difference']:>10.4f}"
            f"{rows['top5']['paired_mean_difference']:>10.4f}"
            f"{ten['paired_mean_difference']:>10.4f}"
            f"{ten['paired_sd']:>8.4f}{record:>14}"
            f"{rows['brier']['paired_mean_difference']:>12.6f}")
    return [*lines, ""]


def report_text(report: dict) -> str:
    lines = [*_header(report), *_sizes(report), *_ledger(report)]
    for method in report["arms"][next(iter(report["arms"]))]["methods"]:
        lines += _lift(report, method)
        lines += _raw(report, method)
    lines += _network(report)
    lines += _coefficients(report)
    lines += [
        "  Read in this order: interval width and whether it excludes 1.0; "
        "then the",
        "  standardised lift; then the Brier. Raw top-k across arms is not a "
        "valid",
        "  comparison and is printed only as the input to the first two.",
        ""]
    return "\n".join(lines)
