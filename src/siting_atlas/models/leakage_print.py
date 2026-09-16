"""The console report for ``models/leakage_decisive``.

Split out for one reason: the measurement module was over this project's
300-line ceiling with the formatting inside it. Everything here reads the
finished artefact dict and prints; nothing is computed, so the terminal and
``outputs/metrics/leakage_decisive.json`` cannot disagree.
"""

from __future__ import annotations

import textwrap

ARMS = ("osha_bound", "true_date", "no_covariate")

__all__ = ["render"]


def _beta_span(arm: dict) -> str:
    key = next((k for k in arm if k.startswith("beta_")), None)
    if key is None:
        return "--"
    b = arm[key]
    flag = "*" if b["splits_at_boundary"] else ""
    return f"{b['median']:.2f} [{b['p2_5']:.2f},{b['p97_5']:.2f}]{flag}"


def _header(report: dict) -> None:
    n = report["n_decisions_intersection"]
    n_test = report["arms"]["osha_bound"]["n_test"]
    lost = report["n_decisions_lost"]
    pct = 100 * lost / report["n_decisions_osha_bound_unrestricted"]
    print("\n  === decisive leakage test: a CBP vintage before the TRUE "
          "opening ===\n")
    print(f"  {n} decisions, {n_test} held out, {report['repeats']} "
          f"re-splits. All three arms fit\n  the SAME {n} decisions, so no "
          f"difference below is a difference in sample size.")
    print(f"  {report['n_decisions_no_covariate_unrestricted']} decisions "
          f"exist with no covariate and "
          f"{report['n_decisions_osha_bound_unrestricted']} on the OSHA "
          f"bound;\n  requiring a stated opening date AND a CBP vintage "
          f"before it leaves {n}\n  ({lost} lost, {pct:.0f}% of the working "
          f"sample).\n")


def _table(report: dict) -> None:
    n_test = report["arms"]["osha_bound"]["n_test"]
    print(f"  {'':15}{'top-10':>11}{'sd':>7}{'lift':>7}{'Brier':>12}"
          f"{'beta warehousing':>22}")
    for name in ARMS:
        arm = report["arms"][name]
        print(f"  {name:15}{arm['top10_hits_mean']:7.2f}/{n_test:<3}"
              f"{arm['top10_hits_sd']:7.2f}{arm['lift_over_own_null']:7.2f}"
              f"{arm['brier_mean']:12.6f}{_beta_span(arm):>22}")
    print(f"  {'uniform null':15}"
          f"{report['arms']['osha_bound']['uniform_null_hits']:7.2f}"
          f"/{n_test:<3}")
    if any(report["arms"][a].get("beta_warehousing_establishments", {})
           .get("splits_at_boundary") for a in ARMS[:2]):
        print("\n  * at least one split drove beta to the boundary: the "
              "covariate separated\n    that choice set outright and the "
              "likelihood is flat above it. Counted,\n    not dropped, which "
              "is why the median and not the mean is quoted.")


def _differences(report: dict) -> None:
    print()
    for name, p in report["paired_differences"].items():
        print(f"  {name:30}{p['mean_difference_hits']:+7.2f} hits  "
              f"(sd {p['sd_of_difference']:.2f})   "
              f"{p['first_wins']}W {p['ties']}T {p['second_wins']}L")
    share = report["share_of_covariate_value_retained"]
    print(f"\n  The covariate keeps {100 * share:.0f}% of its measured value "
          f"when the vintage is\n  forced behind the STATED opening date "
          f"instead of the OSHA bound.")

    ratio = report["beta_per_establishment_osha_over_true"]
    print(f"  Per ESTABLISHMENT, on the raw column rather than the "
          f"mean-scaled one, the\n  osha_bound weight is {ratio:.3f} times "
          f"the true_date weight: the column's level\n  moves between the "
          f"two vintages, its price does not.")

    s = report["self_count_check"]
    print(f"\n  self-count check, no model fitted. Between the two vintages "
          f"the chosen\n  ZCTA gains {s['chosen_delta_mean']:+.2f} "
          f"establishments against {s['peer_mean_delta_mean']:+.2f} for the "
          f"average\n  alternative in its own metro: an excess of "
          f"{s['excess_mean']:+.2f} (sd {s['excess_sd']:.2f}, median "
          f"{s['excess_median']:+.2f}),\n  on {s['n_facilities']} facilities "
          f"of which {s['vintage_unchanged']} have the same vintage in both "
          f"arms.")

    ds = report["delivery_station_tables_only"]
    d = ds["paired_osha_minus_true"]
    print(f"\n  sensitivity, stated dates from a DELIVERY STATION table only:"
          f" {ds['n_decisions']} decisions,\n  osha_bound - true_date = "
          f"{d['mean_difference_hits']:+.2f} hits (sd "
          f"{d['sd_of_difference']:.2f}), {d['first_wins']}W {d['ties']}T "
          f"{d['second_wins']}L. Too small to settle\n  anything; reported so "
          f"the headline set is not the only number on the page.")


def render(report: dict) -> None:
    """Print the whole report. Reads the artefact dict, computes nothing."""
    _header(report)
    _table(report)
    _differences(report)
    print("\n  Reading this:")
    print("    true_date COLLAPSING toward no_covariate would mean the")
    print("    covariate was substantially self-counting and the headline")
    print("    prediction result cannot be defended as it stands.")
    print("    true_date HOLDING near osha_bound would mean agglomeration,")
    print("    and the result survives an audit it previously lacked.")
    for line in report["caveats"]:
        body = textwrap.wrap(line, 68)
        print(f"\n  CAVEAT  {body[0]}")
        for extra in body[1:]:
            print(f"          {extra}")
    print()
