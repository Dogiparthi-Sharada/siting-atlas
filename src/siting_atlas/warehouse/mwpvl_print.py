"""Printing for :mod:`warehouse.mwpvl_merge`.

Separate from :mod:`warehouse.mwpvl_report`, which measures. Nothing here
computes anything that is not already in the artefact dict, so the console
output and ``outputs/metrics/mwpvl_merge.json`` cannot disagree.
"""

from __future__ import annotations


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def to_stdout(r: dict) -> None:
    """Print the merge. Every line carries its count."""
    g, d, p = r["new_row_geography"], r["new_row_dates"], r["expanded_panel"]
    v = r["validation_E_operating_by"]
    print("\n  === MWPVL 2025 Q1 -> expanded national facility panel ===\n")
    print(f"  MWPVL rows read                 : {r['mwpvl_rows']}")
    print(f"    dropped as INTERNAL duplicates: "
          f"{r['internal_duplicates_dropped']}")
    print(f"    already in national_facilities: {r['already_in_panel']}")
    print(f"    held for clerical review      : "
          f"{r['held_for_clerical_review']}")
    print(f"    genuinely NEW, added          : {r['new_rows_added']}")
    s, probe = r["screenability"], \
        r["recall_probe_vs_postcode_and_house_number"]
    print(f"    ...of which UNSCREENABLE      : "
          f"{s['no_street_at_all_unscreenable']} MWPVL rows carry no "
          f"comparable street,\n{'':36}so the comparator could not test them "
          f"at all")
    pairs = probe["pairs_sharing_postcode_and_house_number"]
    print(f"    recall probe: {pairs} pairs share a postcode and a house"
          f"\n{'':18}number -> {probe['verdicts']}")

    print(f"\n  geography of the {g['rows']} added rows")
    print(f"    with a ZCTA                   : {g['with_zcta']} "
          f"({_pct(g['with_zcta'], g['rows'])})")
    print(f"    with a CBSA code              : {g['with_cbsa_code']} "
          f"({_pct(g['with_cbsa_code'], g['rows'])}), "
          f"{g['distinct_cbsas']} distinct")
    print(f"    no ZCTA (postcode not a ZCTA) : {g['without_zcta']}")
    print(f"    ZCTA but county in no metro   : "
          f"{g['without_cbsa_county_in_no_metro']}")
    print(f"    ZCTA but Connecticut vintage  : "
          f"{g['without_cbsa_connecticut_vintage_gap']}")

    print(f"\n  dates on the {g['rows']} added rows")
    print(f"    with an opening year          : {d['with_open_year']}")
    print(f"    with a quarter                : {d['with_open_quarter']}")
    print(f"    dated AND in a CBSA (usable)  : "
          f"{d['dated_and_placed_in_a_cbsa']}")
    if d["date_flags"]:
        print(f"    flagged, not corrected        : {d['date_flags']}")

    print(f"\n  expanded panel  -> {r['output']}")
    print(f"    rows                          : {p['rows']} "
          f"(was {r['panel_rows_before']})")
    print(f"    DATED                         : {p['dated']}")
    print(f"    dated AND in a CBSA           : "
          f"{p['dated_and_placed_in_a_cbsa']}")
    print(f"    distinct CBSAs                : {p['distinct_cbsas']}")
    w = p["in_panel_window"]
    print(f"    within {w['first_year']}-{w['last_year']}                 : "
          f"{w['decisions']} decisions, {w['independent_episodes']} "
          f"independent episodes\n{'':36}({w['per_parameter_at_5_parameters']}"
          f" per parameter at 5, floor 10; projected, not fitted)")

    fc = r["facility_check"]
    print(f"\n  ingest/facility_check on the written file: "
          f"{'PASSES' if fc['passes'] else 'DOES NOT PASS'}")
    for e in fc["errors"]:
        print(f"    ERROR   {e}")
    for w in fc["warnings"]:
        print(f"    warning {w}")

    print("\n  E_operating_by on the expanded panel")
    if not v.get("evaluated"):
        print(f"    NOT EVALUATED: {v['reason']}")
    else:
        print(f"    rows with a date              : {v['rows_with_a_date']}")
        print(f"    linked to an OSHA building    : "
              f"{v['linked_to_an_osha_building']}")
        print(f"    falsified                     : {v['falsified']}")
        print(f"    PASS RATE                     : "
              f"{100 * v['pass_rate']:.1f}%" if v["pass_rate"] is not None
              else "    PASS RATE                     : n/a")
        for name, s in v["by_source_dataset"].items():
            print(f"      {name:28} {s['linked']:4d} linked, "
                  f"{s['falsified']:3d} falsified, "
                  f"{100 * s['pass_rate']:.1f}% pass")
    print()
