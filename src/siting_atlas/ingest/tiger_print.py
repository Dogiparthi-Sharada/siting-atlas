"""The console table for `tiger_lift`. Reading, not computing.

Split out so the experiment file stays under the project's 300-line
limit, and because the two jobs fail differently: a wrong number here is
a typo in an f-string, a wrong number there is a wrong result.
"""

from __future__ import annotations

from ..models.panel_strata import BUCKETS, TOP_KS

__all__ = ["print_report"]


def _cell(arm: dict, key: str, bucket: str) -> str:
    cell = arm["strata"][key][bucket]
    if cell["lift"] is None:
        return f"{'--':>15}"
    mark = "" if cell["informative"] else "*"
    delta = arm["paired"][key][bucket]
    return f"{cell['lift']:>8.2f}{mark:1}{delta['mean_pp']:>+6.1f}"


def print_report(report: dict) -> None:
    """Lift per stratum, the paired delta beside it, then the betas."""
    cov = report["coverage"]
    print(f"\n  {cov['decisions']} decisions, {cov['alternatives']:,} "
          f"alternatives, {report['repeats']} paired re-splits")
    print("  distinct decisions by choice-set size: "
          + ", ".join(f"{k} {v}" for k, v in
                      report["distinct_by_stratum"].items()))
    if report["non_finite_fits"]:
        print("\n  WARNING: " + "; ".join(
            f"{n} produced a non-finite fit on {c} of "
            f"{report['repeats']} splits"
            for n, c in report["non_finite_fits"].items())
            + "\n  those splits are excluded from that arm and from "
              "nothing else; see the note at the top of tiger_lift")

    for k in TOP_KS:
        key = f"top{k}"
        print(f"\n  TOP-{k}: LIFT OVER A UNIFORM GUESS, and the PAIRED "
              "CHANGE IN HIT RATE vs baseline (percentage points)")
        head = "  {:32}".format("arm")
        for b, _, _ in BUCKETS:
            head += f"{b:>15}"
        print(head)
        for name, arm in report["arms"].items():
            row = f"  {name:32}"
            for b, _, _ in BUCKETS:
                row += _cell(arm, key, b)
            print(row)
    print("\n  * stratum holds fewer than 20 distinct decisions; "
          "reported, not compared")

    print("\n  IS THE PAIRED CHANGE DISTINGUISHABLE FROM ZERO? "
          "(top-10, large metros, 2 s.e. of the paired mean)")
    for name, arm in report["arms"].items():
        if name == "baseline":
            continue
        d = arm["paired"]["top10"]["large_gt100"]
        lo, hi = d["mean_pp"] - 2 * d["se_pp"], d["mean_pp"] + 2 * d["se_pp"]
        verdict = "no" if lo <= 0 <= hi else "yes"
        print(f"  {name:32}{d['mean_pp']:+6.2f} pp  "
              f"[{lo:+.2f}, {hi:+.2f}]  better on "
              f"{100 * d['share_better']:3.0f}% of splits  -> {verdict}")

    print("\n  COEFFICIENT ON THE ADDED COLUMN. beta is in mean-scaled "
          "units, so it reads\n  as 'at its mean this column contributes "
          "beta times what households does\n  at theirs'. Boundary means "
          f"the optimiser drove beta below {report['boundary']:g}.")
    for name, arm in report["arms"].items():
        for c in arm["coefficients"]:
            print(f"  {name:32}{c['column']:20}"
                  f"beta={c['beta_median']:.4g} "
                  f"[{c['beta_p10']:.3g}, {c['beta_p90']:.3g}]  "
                  f"{'INTERIOR' if c['interior'] else 'BOUNDARY'}, "
                  f"at it on {100 * c['at_boundary_share']:.0f}% of splits")

    print("\n  MEAN PROBABILITY ASSIGNED TO THE CHOSEN ZCTA "
          "(higher is better calibrated)")
    for name, arm in report["arms"].items():
        print(f"  {name:32}{arm['mean_prob_of_chosen']:.5f}"
              f"  max |score - baseline| on a split: "
              f"{arm['max_gap_vs_baseline']:.3g}")
