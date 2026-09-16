"""How many delivery-station cities does the best free source actually see?

    python -m siting_atlas.ingest.mwpvl_coverage

Writes `outputs/metrics/mwpvl_coverage.json`.

WHY THIS MODULE EXISTS AT ALL
-----------------------------
The numbers it emits were first computed in a throwaway shell command, quoted
in a progress memo, and then found to be unciteable — they appear in no
artefact, so under the project's own rule ("cite the artefact, not the
figure") they could not be used. That is the same defect as
`lift_by_market_size.json`, which is referenced by five documents and written
by nothing. A number worth putting in front of a reader is worth an emitter.

WHAT IT MEASURES
----------------
A DIRECT measurement of the visibility gap, as distinct from the estimated one
in `nlrb_coverage.json`.

The capture-recapture estimators answer "how many cities exist that no list
contains?" by modelling the overlap between lists. This asks something
narrower and harder to argue with: MWPVL names delivery stations in N cities;
how many of those has OSHA — the best free source — ever inspected?

No model, no assumption of independence, no heterogeneity correction. Two
lists, one intersection. It is a floor on the gap rather than an estimate of
it, because MWPVL is itself incomplete and says so.

WHY THE COMPARISON IS DELIBERATELY UNFAIR TO THE ARGUMENT
---------------------------------------------------------
MWPVL's side is restricted to SMALL-PACKAGE DELIVERY STATIONS, the project's
target class. OSHA's side is NOT restricted: it is every Amazon building of
any kind that OSHA ever inspected. So OSHA is allowed to score a match on a
fulfilment centre in a city where MWPVL names a delivery station.

That is the wrong comparison in OSHA's favour, on purpose. The resulting gap
is therefore a conservative one: tightening OSHA to delivery stations only
would widen it, and the honest direction of error should run against the
finding rather than toward it.
"""

from __future__ import annotations

import csv
import re

from ..common import paths
from ..common.log_json import write_json
from .mwpvl_fields import STATES as STATE_NAMES

#: Table directories holding the target class. Matches
#: `warehouse.mwpvl_merge.DELIVERY_STATION_TABLES`; heavy/bulky is a separate
#: network launched in 2017 and is excluded for the same reason it is there.
DELIVERY_STATION_TABLES = ("08_us_delivery_station",
                           "08_us_delivery_station_part2")

SOURCE = paths.INTERIM / "mwpvl_facilities.csv"
OSHA = paths.INTERIM / "osha_amazon.csv"
OUT = paths.METRICS / "mwpvl_coverage.json"



def _usps() -> dict[str, str]:
    """Full state name -> USPS code, built from the canonical list.

    Derived rather than typed out so it cannot drift from
    `mwpvl_fields.STATES`, which is what the address parser matched against.
    Two-word names need the initials of both words; one-word names do not
    follow any rule, so they are listed.
    """
    fixed = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
        "california": "CA", "colorado": "CO", "connecticut": "CT",
        "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI",
        "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
        "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
        "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
        "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
        "montana": "MT", "nebraska": "NE", "nevada": "NV", "ohio": "OH",
        "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
        "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
        "virginia": "VA", "washington": "WA", "wisconsin": "WI",
        "wyoming": "WY", "new hampshire": "NH", "new jersey": "NJ",
        "new mexico": "NM", "new york": "NY", "north carolina": "NC",
        "north dakota": "ND", "rhode island": "RI", "south carolina": "SC",
        "south dakota": "SD", "west virginia": "WV",
        "district of columbia": "DC",
    }
    missing = set(STATE_NAMES) - set(fixed)
    if missing:
        raise ValueError(f"no USPS code for {sorted(missing)}; "
                         "mwpvl_fields.STATES has grown")
    return fixed


def _city_key(city: str) -> str:
    """A city name reduced to letters, for matching across two sources."""
    return re.sub(r"[^A-Z]", "", (city or "").upper())


def collect() -> dict:
    """Both city sets, their overlap, and the rows that were unusable."""
    usps = _usps()

    mwpvl: set[tuple[str, str]] = set()
    rows = unusable = 0
    with open(SOURCE, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["table"] not in DELIVERY_STATION_TABLES:
                continue
            rows += 1
            code = usps.get((row["addr_region"] or "").strip().lower())
            key = _city_key(row["city"])
            if not code or not key:
                unusable += 1
                continue
            mwpvl.add((key, code))

    osha: set[tuple[str, str]] = set()
    with open(OSHA, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            key = _city_key(row["site_city"])
            code = (row["site_state"] or "").strip().upper()[:2]
            if key and code:
                osha.add((key, code))

    overlap = mwpvl & osha
    return {
        "mwpvl_delivery_station_rows": rows,
        "mwpvl_rows_without_a_usable_city_and_state": unusable,
        "mwpvl_delivery_station_cities": len(mwpvl),
        "osha_cities_all_facility_classes": len(osha),
        "cities_in_both": len(overlap),
        "cities_mwpvl_names_that_osha_never_inspected": len(mwpvl - osha),
        "share_of_mwpvl_cities_osha_has_seen":
            len(overlap) / len(mwpvl) if mwpvl else None,
        "unseen_examples": sorted(f"{c}, {s}" for c, s in
                                  sorted(mwpvl - osha))[:15],
        "comparison_is_conservative": (
            "MWPVL's side is restricted to small-package delivery stations; "
            "OSHA's side is every Amazon facility class it ever inspected. "
            "OSHA is therefore allowed to match a delivery-station city on a "
            "fulfilment centre. Restricting OSHA to delivery stations would "
            "WIDEN the measured gap."),
        "not_an_estimate": (
            "A direct two-list intersection, not a capture-recapture "
            "estimate. It is a FLOOR on the invisibility, because MWPVL is "
            "itself incomplete and states so about this very table: 'The data "
            "concerning this network is challenging to track so we provide "
            "the best information available.' For the modelled estimate see "
            "outputs/metrics/nlrb_coverage.json."),
    }


def main() -> int:
    for path in (SOURCE, OSHA):
        if not path.exists():
            raise SystemExit(f"\n  {paths.rel(path)} not found\n")
    result = collect()

    print("\n  === delivery-station cities: MWPVL vs the best")
    print("      free source ===\n")
    print(f"  MWPVL delivery-station rows read   "
          f"{result['mwpvl_delivery_station_rows']:>6}")
    print(f"    of which no usable city+state    "
          f"{result['mwpvl_rows_without_a_usable_city_and_state']:>6}")
    print(f"  MWPVL distinct cities              "
          f"{result['mwpvl_delivery_station_cities']:>6}")
    print(f"  OSHA distinct cities (ALL classes) "
          f"{result['osha_cities_all_facility_classes']:>6}")
    print(f"  in both                            "
          f"{result['cities_in_both']:>6}")
    print(f"  OSHA has never inspected           "
          f"{result['cities_mwpvl_names_that_osha_never_inspected']:>6}")
    share = result["share_of_mwpvl_cities_osha_has_seen"]
    if share is not None:
        print(f"\n  the best free source sees {share:.1%} of the cities "
              "MWPVL names")
    print("\n  This is a floor, not an estimate. See the artefact's "
          "`not_an_estimate` field.\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUT, result)
    print(f"  -> {paths.rel(OUT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
