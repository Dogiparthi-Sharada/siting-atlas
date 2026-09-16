"""Rendering one hazard run to a terminal, in reading order.

Separated from ``runner`` so the order of the sections is a decision that can
be reviewed on its own. It is a decision: the power block is printed BEFORE
the performance table, because a reader who meets AUC first anchors on it and
files everything after as caveats, while a reader who meets "nine independent
episodes per parameter" first reads the AUC as the caveat it is. Same numbers,
opposite conclusion, and the only difference is which one is at the top.
"""

from __future__ import annotations

import textwrap


def print_power(r: dict) -> None:
    """The two sample-size numbers, before any performance figure is shown.

    Printed above the metrics on purpose. A reader who sees AUC first
    anchors on it and reads the power line as a footnote; a reader who sees
    "nine independent episodes per parameter" first reads the AUC as the
    footnote it is.
    """
    p = r.get("power")
    if not p:
        return
    print("\n  POWER  (the number that decides whether the rest counts)")
    lo, hi = sorted((p["n_independent_episodes"],
                     p["n_usable_facilities"] or 0))
    print(f"  {p['n_events_zcta']:,} ZCTA-level training events, but "
          f"{lo}-{hi} independent decisions "
          f"(metro-quarter episodes .. buildings)")
    epp_lo = min(p["events_per_parameter_effective"],
                 p["events_per_parameter_optimistic"])
    print(f"  {p['n_parameters']} parameters -> "
          f"{p['events_per_parameter_nominal']:.1f} events/parameter "
          f"nominal, {epp_lo:.1f}-"
          f"{p['events_per_parameter_optimistic']:.1f} REAL "
          f"(floor {p['floor']:.0f}, judged on the optimistic end)")
    if not p["meets_floor"]:
        print("  ** BELOW THE FLOOR. Coefficients are indicative only. **")
    t = r.get("event_timing", {})
    if t:
        # `cause` is derived from the risk set, not a fixed sentence, so
        # this line stays true as open_quarter coverage improves.
        print(f"  {t['share_in_q1']:.0%} of events fall in Q1; "
              f"{t['rows_structurally_eventless']:.0%} of risk-set rows are "
              f"structural zeros.")
        print("  " + textwrap.fill(t["cause"], 74,
                                   subsequent_indent="  "))
    by_metro = r.get("events_by_metro") or []
    if by_metro:
        print("  events by fitting metro (a silent metro identifies "
              "nothing):")
        print("   " + "  ".join(f"{m['cbsa_code']}:{m['events']}"
                                for m in by_metro))
        silent = [m["cbsa_code"] for m in by_metro if m["events"] == 0]
        if silent:
            print(f"   {len(silent)} metro(s) contribute ZERO events: "
                  f"{', '.join(silent)}")
    print(f"\n  CONTAMINATION: {r.get('contamination', '')}")


def print_report(r: dict) -> None:
    w = 78
    print("\n" + "=" * w)
    label = "SYNTHETIC — NOT REAL DATA" if r["synthetic"] else "real panel"
    print(f"  DISCRETE-TIME HAZARD (cloglog)  -  {label}")
    print("=" * w)
    if r["synthetic"]:
        print("  The facility panel has not arrived. Everything below was\n"
              "  generated from a known process and validates the CODE.\n"
              f"  reason: {r['panel_detail'].get('reason', '')}")
        print("-" * w)

    rs = r["risk_set"]
    print(f"  risk set   {rs['units']:,} units   {rs['rows']:,} unit-quarters"
          f"   {rs['events']:,} events "
          f"({rs['event_rate']:.2%} per unit-quarter)")
    print(f"             mean {rs['mean_quarters_at_risk']:.1f} quarters at "
          f"risk per unit, t = {rs['t_min']}..{rs['t_max']}")
    for name, s in r["split"].items():
        print(f"  {name:12} {s['units']:>6,} units  {s['rows']:>8,} rows  "
              f"{s['events']:>5,} events")

    print_power(r)

    print("\n  HELD-OUT PERFORMANCE")
    ev, nl = r["evaluation"], r["null_model"]
    print(f"  {'':22} {'AUC':>7} {'Brier':>10} {'ECE':>8} {'skill':>8}")
    print(f"  {'cloglog hazard':22} {ev['auc']:>7.3f} {ev['brier']:>10.5f} "
          f"{ev['ece']:>8.4f} {r['brier_skill']:>8.4f}")
    print(f"  {'base rate only':22} {nl['auc']:>7.3f} {nl['brier']:>10.5f} "
          f"{nl['ece']:>8.4f} {0.0:>8.4f}")
    for key, title in (("temporal_secondary", "temporal split (SECONDARY)"),
                       ("annual_sensitivity", "annual grain (sensitivity)"),
                       ("transfer_smoke_test", "Phoenix+Boise (smoke)")):
        block = r.get(key, {})
        if block.get("ran"):
            e = block["evaluation"]
            print(f"  {title:22} {e['auc']:>7.3f} {e['brier']:>10.5f} "
                  f"{e['ece']:>8.4f} {block['brier_skill']:>8.4f}")

    print("\n  CONFORMAL COVERAGE (distribution-free)")
    c = r["conformal"]
    verdict = "within tolerance" if c["within_tolerance"] else "OUT OF BAND"
    print(f"  nominal {c['nominal_coverage']:.1%}   empirical "
          f"{c['empirical_coverage']:.1%} +/- {c['tolerance_2sigma']:.1%} "
          f"({verdict})")
    print(f"  tolerance is 2 sigma on {c['n_effective']:,} effective units, "
          f"not {c['n_test']:,} rows —")
    print("  quarters of the same ZCTA are not independent draws.")
    # q_hat is null in the report when the calibration sample was too small
    # to support the requested level; print the reason, not a fake number.
    q_hat = "infinite (too few calibration rows)" if c["q_hat"] is None \
        else f"{c['q_hat']:.4f}"
    print(f"  q_hat {q_hat}   mean set size {c['mean_set_size']:.3f}"
          f"   informative (singleton) {c['share_singleton']:.1%}"
          f"   empty {c['share_empty']:.1%}")

    print("\n  COEFFICIENTS")
    print(f"  {'term':22} {'coef':>9} {'se':>8} {'hazard ratio':>13} "
          f"{'p':>8}")
    for row in r["fit"]["coefficients"]:
        print(f"  {row['term'][:22]:22} {row['coefficient']:>9.4f} "
              f"{row['std_error']:>8.4f} {row['hazard_ratio']:>13.4f} "
              f"{row['p_value']:>8.4f}")

    if r["recovery"]:
        print("\n  RECOVERY OF THE KNOWN TRUTH (synthetic only)")
        print(f"  {'term':22} {'true':>8} {'estimate':>10} {'error':>8} "
              f"{'z from truth':>13}")
        for row in r["recovery"]:
            print(f"  {row['term']:22} {row['true']:>8.3f} "
                  f"{row['estimate']:>10.3f} {row['error']:>8.3f} "
                  f"{row['z_from_truth']:>13.2f}")
    print("=" * w)

