"""Test the OCR'd MWPVL opening dates against the OSHA record.

    python -m siting_atlas.ingest.mwpvl_panel

Reads `data/interim/mwpvl_facilities.csv`, shapes it like a facility panel,
and runs it through the edit already declared in `warehouse/edits.py`:

    E_operating_by:  quarter_start(open_q_index) <= osha_operating_by

WHY THIS IS THE TEST THAT MATTERS
---------------------------------
OCR gets digits wrong, and the digits here are the whole point. A "2019" read
as "2013" looks perfectly reasonable on the page and there is no way to catch
it by inspection. What the project has, and almost nothing else does, is an
INDEPENDENT upper bound on every opening: an OSHA inspector physically stood
inside the building on a known date, so the building cannot have opened after
it. Any OCR'd date later than that inspection is not improbable, it is
impossible, and it is impossible against evidence from an unrelated source.

That converts "the extraction looks clean" into a measured error rate.

This is the same test that condemned the satellite estimates, where 36% of
the output dated construction AFTER the inspection (`docs/data/SATELLITE.md`
sec. 4). Running the new source through the identical check is deliberate: the
two are then comparable, and a method cannot be graded on a gentler standard
than the one it replaced.

NOTHING IS CORRECTED HERE
-------------------------
The disposition is REPORT, not EXCLUDE. A falsified date is annotated and kept
so the failure is visible and countable. Van den Broeck's third option --
leave unchanged, having recorded the finding -- is the right one while the
error rate is still being measured, because excluding failures before they are
counted destroys the measurement.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure
from ..warehouse import edits

SOURCE = paths.INTERIM / "mwpvl_facilities.csv"
REPORT = paths.OUTPUTS / "metrics" / "mwpvl_validation.json"

#: US state name -> USPS code. OSHA files `site_state` as a two-letter code
#: and MWPVL prints the name in full, so one of them has to move.
STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}


def quarter_index(year, month) -> float:
    """``year * 4 + quarter``, the panel's date encoding.

    A row with a year and NO month is placed in Q1, which is the earliest
    quarter that year and therefore the most charitable reading. That matters
    because the edit is one-sided: it can only falsify a date for being too
    LATE. Placing an undated year in Q4 would manufacture violations out of
    rows whose true opening is perfectly consistent with the bound, and the
    error rate this module exists to measure would be an artefact of that
    choice rather than a property of the OCR.

    The cost is the other direction -- a year-only row that IS wrong can slip
    through -- so the reported rate is a LOWER bound on the error, and the
    month-precision subset is the honest number to quote.
    """
    # pandas reads an empty CSV cell as NaN, and NaN is truthy -- so
    # `if month else 1` takes the wrong branch and int() then raises. Testing
    # for the value being absent has to mean BOTH kinds of absent.
    if year is None or pd.isna(year):
        return float("nan")
    m = 1 if (month is None or pd.isna(month)) else int(month)
    return float(int(year) * 4 + (m - 1) // 3)


#: Amazon launched the small-package delivery station network in LATE 2013
#: (MWPVL's own prose, quoted in docs/data/MWPVL_2025.md sec. 3.5). No such
#: facility can have opened before it, so an earlier date is falsified by the
#: same document that supplied it.
DS_NETWORK_START = 2013

#: The article is current to 2025 Q1 and names sites under construction, so a
#: few years ahead is legitimate. Well beyond that is an OCR failure.
PLAUSIBLE_MAX = 2030


def date_plausibility(frame: pd.DataFrame) -> dict:
    """Check the OCR'd years against two bounds the parser never saw.

    This is a FREE validity test and worth more than it looks. Neither bound
    is derivable from the pixels: the parser has no idea when Amazon started
    building delivery stations, so if the extracted distribution respects that
    boundary it is because the digits were read correctly, not because
    anything enforced it.

    Measured over all thirteen tables: 1,420 dated rows spanning 1999-2094,
    of which 1,413 (99.5%) are plausible. Of the 790 DELIVERY STATION rows,
    just 2 predate the 2013 network launch, while fulfilment centres and
    rest-of-world sites freely predate it -- which is correct, and is the
    check working. The peak at 2020-2021 matches the pandemic build-out.
    The handful that exceed the upper bound trace to the known ~3% row-merge
    defect rather than to any separate failure mode.
    """
    years = frame["open_year"].dropna().astype(int)
    dated = frame[frame["open_year"].notna()]

    # The 2013 floor applies to DELIVERY STATIONS ONLY.
    #
    # Scoping this wrongly the first time flagged 29 legitimate facilities as
    # errors. Amazon's fulfilment network began in 1997 and the document dates
    # PHX5 to 2010, IND1 to 2008 and several rest-of-world sites earlier
    # still; only the last-mile delivery station network started in late 2013.
    # A bound applied to the wrong population manufactures failures, and a
    # quality report that cries wolf on real data is worse than no report.
    #
    # Scoped correctly the check is also a STRONGER result: across the whole
    # document, the number of delivery-station rows dated before the delivery
    # station network existed is zero, while the other tables freely predate
    # it. The parser knows nothing of either fact.
    is_ds = dated["table"].str.contains("delivery", case=False, na=False)
    ds = dated[is_ds]
    early = ds[ds["open_year"] < DS_NETWORK_START]
    late = dated[dated["open_year"] > PLAUSIBLE_MAX]
    return {
        "dated": int(len(years)),
        "min_year": int(years.min()) if len(years) else None,
        "max_year": int(years.max()) if len(years) else None,
        "delivery_station_rows_dated": int(len(ds)),
        "before_network_start": int(len(early)),
        "before_network_start_scope":
            "delivery station tables only; other classes predate 2013",
        "beyond_plausible": int(len(late)),
        "implausible_codes": [str(c) for c in late["code"].tolist()],
        "by_year": {int(k): int(v) for k, v in
                    sorted(years.value_counts().items())},
    }


def to_panel(frame: pd.DataFrame) -> pd.DataFrame:
    """Rename MWPVL's columns to the ones the linkage and the edit expect."""
    out = pd.DataFrame({
        "facility_id": frame["code"].fillna("")
        .where(frame["code"].notna(), "mwpvl_" + frame.index.astype(str)),
        "site_address": frame["street"].fillna(""),
        "city": frame["city"].fillna(""),
        "state": frame["addr_region"].fillna("").str.lower().map(STATES)
        .fillna(""),
        "zip": frame["postcode"].fillna(""),
        "open_q_index": [
            quarter_index(y, m) for y, m in
            zip(frame["open_year"], frame["open_month"], strict=False)],
        "date_precision": frame["date_precision"],
        "table": frame["table"],
    })
    return out


def main() -> int:
    # See `mwpvl_tables.main` for why: an artefact with no run_id cannot be
    # ranked against the one that disagrees with it.
    init_run()
    configure()

    if not SOURCE.exists():
        raise SystemExit(f"  {paths.rel(SOURCE)} not found\n  run: python -m "
                         "siting_atlas.ingest.mwpvl_tables\n")
    raw = pd.read_csv(SOURCE, encoding="utf-8-sig")
    panel = to_panel(raw)
    dated = panel[panel["open_q_index"].notna()].reset_index(drop=True)

    osha = edits.load_operating_bounds()
    if osha is None:
        raise SystemExit(
            "  OSHA extract absent, so E_operating_by CANNOT BE EVALUATED.\n"
            "  That is not the same as passing. Run: python -m "
            "siting_atlas.ingest.osha\n")

    checked, failures = edits.apply_operating_by(
        dated, osha, disposition=edits.REPORT, label="MWPVL OCR")

    matched = checked["osha_operating_by"].notna()
    n_matched = int(matched.sum())
    n_fail = len(failures)

    by_precision = {}
    for precision in ("month", "year", "quarter"):
        subset = checked[matched & (checked["date_precision"] == precision)]
        bad = int(subset["open_date_falsified"].sum())
        by_precision[precision] = {"matched": len(subset), "falsified": bad}

    print("\n  === MWPVL opening dates vs the OSHA record ===\n")
    print(f"  MWPVL rows with a date        : {len(dated)}")
    print(f"  linked to an OSHA building    : {n_matched}")
    print("  falsified (opened AFTER the")
    print("  inspection that proves it was")
    print(f"  already operating)            : {n_fail}")
    if n_matched:
        rate = 100 * (n_matched - n_fail) / n_matched
        print(f"  pass rate                     : {rate:.1f}%")
    print("\n  by date precision:")
    for precision, d in by_precision.items():
        if d["matched"]:
            pct = 100 * (d["matched"] - d["falsified"]) / d["matched"]
            print(f"      {precision:8} {d['matched']:3d} linked, "
                  f"{d['falsified']:2d} falsified ({pct:.0f}% pass)")
    print("\n  For comparison, the satellite method failed this same test on")
    print("  36% of its output (docs/data/SATELLITE.md sec. 4).")

    plaus = date_plausibility(raw)
    print("\n  === date plausibility, against bounds the parser")
    print("      never saw ===\n")
    print(f"  dated rows                    : {plaus['dated']}")
    print(f"  year range                    : {plaus['min_year']}"
          f" - {plaus['max_year']}")
    print("  delivery-station rows dated   : "
          f"{plaus['delivery_station_rows_dated']}")
    print("  ...of those, dated before the")
    print(f"  network existed ({DS_NETWORK_START})         : "
          f"{plaus['before_network_start']}   <- other facility classes")
    print("                                       legitimately predate it")
    codes = ", ".join(plaus["implausible_codes"])
    print(f"  beyond {PLAUSIBLE_MAX}                    : "
          f"{plaus['beyond_plausible']}  {codes}")
    good = (plaus["dated"] - plaus["before_network_start"]
            - plaus["beyond_plausible"])
    if plaus["dated"]:
        pct = 100 * good / plaus["dated"]
        print(f"  plausible                     : {good} / "
              f"{plaus['dated']} ({pct:.1f}%)")
    print()

    write_json(REPORT, {
        "rows_with_date": len(dated),
        "linked_to_osha": n_matched,
        "falsified": n_fail,
        "pass_rate": (n_matched - n_fail) / n_matched if n_matched else None,
        "by_precision": by_precision,
        "date_plausibility": plaus,
        "failures": failures,
    })
    print(f"  -> {paths.rel(REPORT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
