"""Counting for :mod:`warehouse.mwpvl_merge`. Printing is in mwpvl_print.

Split out so the merge module stays under 300 lines and so every figure the
write-up quotes has exactly one function behind it. Nothing here decides
anything; it only measures what the merge did.

The project's standing rule is that a claim carries its measurement, so each
function returns counts and never a summary adjective. "Most rows matched" is
not an output any function here can produce.
"""

from __future__ import annotations

import pandas as pd

from ..common.linkage import LinkRecord, compare
from .mwpvl_geo import CT_VINTAGE, NO_CBSA, NO_ZCTA
from .mwpvl_shape import DATE_OK, FLAGS

#: The feature panel's window, read from ``warehouse/national`` so the
#: projected episode count below is comparable with the one that module
#: publishes rather than being a second definition of the same thing.
FIRST_YEAR, LAST_YEAR = 2018, 2025

#: The caveats that do not depend on how much of MWPVL has been parsed.
#: Split from the counted ones below so that only one of the two lists can
#: ever go stale, and the stale-able one is derived rather than typed.
_FIXED_CAVEATS = (
    "MWPVL declares its own incompleteness five times and line 391 — 'the "
    "data concerning this network is challenging to track' — is about this "
    "exact table (docs/data/MWPVL_2025.md §6).",
    "A date here is a claim by a consultancy, not a record from a registry. "
    "source_type is 'other', which ranks last in "
    "facility_dedup.DATE_RELIABILITY, and that is the intended rank.",
    "The OCR has a measured ~3% row-merge defect: 18 of 535 rows on table "
    "08_us_delivery_station carry two facilities' text and one facility's "
    "code (docs/data/MWPVL_OCR_PIPELINE.md §13.1). That denominator is table "
    "08 alone, which is where the defect was measured; it is NOT the row "
    "count this merge used, and §13.1 records that the merge count is not "
    "emitted by any artefact. A merged row is a row this merge cannot see "
    "as two buildings.",
    "No coordinate is geocoded and none is present. Every distance covariate "
    "downstream still falls back to a ZCTA centroid.",
    "A postal code is read as a ZCTA. They are different objects; this is "
    "what warehouse/facility_load already does for all national rows.",
    "Nothing is corrected. A date that fails a check is flagged in "
    "date_flag and left at its OCR'd value.",
)


def caveats(rows_in_file: int, tables_parsed: int, rows_used: int,
            tables_used: tuple[str, ...]) -> list[str]:
    """The caveats, with the counted one COUNTED rather than typed.

    This function exists because the typed version went stale. It said "only
    2 of MWPVL's 13 tables have been parsed" and "591 is 591 delivery
    stations" for as long as those were true, and kept saying it after all 13
    were parsed and the class held 635 rows. A caveat that misreports the
    data it is warning about is worse than no caveat, and a literal in a
    module is the one thing a re-run cannot refresh.

    The distinction the old text lost is between PARSED and USED. All of
    MWPVL is parsed; this merge admits one facility class from it. Both
    numbers are named, because "635 rows" read as "635 Amazon buildings" is
    the specific misreading the caveat is for.
    """
    n_used = len(tables_used)
    return [
        *_FIXED_CAVEATS[:3],
        f"All {tables_parsed} of MWPVL's tables are parsed — "
        f"{rows_in_file:,} Amazon buildings worldwide across eight facility "
        f"classes (docs/data/MWPVL_OCR_PIPELINE.md §13.3). This merge USES "
        f"{n_used} of them ({', '.join(tables_used)}), which hold "
        f"{rows_used:,} rows; the remaining {rows_in_file - rows_used:,} are "
        f"a different facility class and are excluded, table 09 "
        f"(heavy/bulky) deliberately so. {rows_used:,} is {rows_used:,} US "
        f"small-package delivery stations, NOT {rows_used:,} Amazon "
        f"buildings and NOT all of MWPVL.",
        *_FIXED_CAVEATS[3:],
    ]


def screenability(records: list[LinkRecord]) -> dict:
    """How many rows the duplicate screen can say anything at all about.

    ``linkage.compare`` returns "no comparable street" when one side has no
    parsed street, and refuses to merge on city and ZIP alone. So a row with
    no street address is not "screened and found new" — it is UNSCREENED, and
    counting it as new without saying so is the failure this project was
    burned by. MWPVL prints a cross-street or a development name instead of
    an address on some rows, and the OCR loses the street on others.
    """
    no_street = [r.rid for r in records if not r.addr.street]
    no_number = [r.rid for r in records if r.addr.street and not r.addr.number]
    return {
        "rows": len(records),
        "no_street_at_all_unscreenable": len(no_street),
        "street_but_no_house_number": len(no_number),
        "fully_screenable": len(records) - len(no_street) - len(no_number),
        "unscreenable_ids": sorted(no_street)[:25],
        "note": ("compare() calls a pair with no comparable street a "
                 "NONMATCH, so these rows enter the panel as new by default "
                 "rather than by evidence. The count is the size of that "
                 "blind spot."),
    }


def recall_probe(left: list[LinkRecord], right: list[LinkRecord]) -> dict:
    """Grade the matcher against a cheaper key it is supposed to beat.

    Every pair sharing a five-digit postcode AND a house number is compared
    and its verdict tallied. A NONMATCH there is a pair the cheap key would
    have caught and the comparator rejected — which is usually correct (two
    buildings can share a number in one ZIP) and is occasionally a miss. Both
    kinds are listed so the miss rate is a number rather than a worry.
    """
    tally: dict[str, int] = {}
    rejected: list[dict] = []
    for a in left:
        for b in right:
            if not (a.zip and a.zip == b.zip and a.addr.number
                    and a.addr.number == b.addr.number):
                continue
            v = compare(a, b)
            tally[v.call] = tally.get(v.call, 0) + 1
            if v.call == "nonmatch":
                rejected.append({"mwpvl_id": a.rid, "panel_id": b.rid,
                                 "why": v.why,
                                 "mwpvl_street": a.addr.core,
                                 "panel_street": b.addr.core})
    return {"pairs_sharing_postcode_and_house_number": sum(tally.values()),
            "verdicts": tally, "rejected": rejected,
            "note": ("A rejected pair is EITHER two buildings at the same "
                     "number in one ZIP OR a miss caused by a damaged street "
                     "string. Each is listed so it can be read rather than "
                     "assumed.")}


def geography(new: pd.DataFrame) -> dict:
    """How many added rows can be placed, and why the rest cannot."""
    status = new["geo_status"].value_counts().to_dict()
    return {
        "rows": int(len(new)),
        "with_zcta": int((new["zcta"] != "").sum()),
        "with_cbsa_code": int((new["cbsa_code"] != "").sum()),
        "without_zcta": int(status.get(NO_ZCTA, 0)),
        "without_cbsa_county_in_no_metro": int(status.get(NO_CBSA, 0)),
        "without_cbsa_connecticut_vintage_gap": int(status.get(CT_VINTAGE, 0)),
        "distinct_cbsas": int(new.loc[new["cbsa_code"] != "",
                                      "cbsa_code"].nunique()),
        "by_status": {k: int(v) for k, v in status.items()},
    }


def dates(new: pd.DataFrame) -> dict:
    """How many added rows carry a date, at what precision, and what failed."""
    year = pd.to_numeric(new["open_year"], errors="coerce")
    usable = year.notna() & (new["cbsa_code"] != "") & (new["zcta"] != "")
    return {
        "with_open_year": int(year.notna().sum()),
        "without_open_year": int(year.isna().sum()),
        "with_open_quarter": int((new["open_quarter"] != "").sum()),
        "by_precision": {k: int(v) for k, v in
                         new["date_precision"].value_counts().items()},
        "dated_and_placed_in_a_cbsa": int(usable.sum()),
        "date_flags": {k: int(v) for k, v in
                       new.loc[new["date_flag"] != DATE_OK,
                               "date_flag"].value_counts().items()},
        "note": ("dated_and_placed_in_a_cbsa is the count models/choice can "
                 "actually use: build() drops a facility with no cbsa_code "
                 "and scores it on a CBP vintage keyed to open_year."),
    }


def provenance(new: pd.DataFrame) -> dict:
    """MWPVL's own caveats on the rows that were added."""
    return {
        "source_dataset": "mwpvl_2025q1",
        "vouched_by_mwpvl": int(new["mwpvl_vouched"].sum()),
        "not_vouched_by_mwpvl": int((~new["mwpvl_vouched"]).sum()),
        "flags": {f: int(new[f].sum()) for f in FLAGS},
        "status": {k: int(v) for k, v in new["status"].value_counts().items()},
        "confidence": {k: int(v) for k, v
                       in new["confidence"].value_counts().items()},
        "note": ("not_confirmed / delayed / cancelled are MWPVL declining to "
                 "vouch for the row. They are kept, marked and countable, "
                 "never dropped and never silently promoted."),
    }


def panel(expanded: pd.DataFrame) -> dict:
    """The shape of the file that was written."""
    year = pd.to_numeric(expanded["open_year"], errors="coerce")
    by_source = expanded["source_dataset"].value_counts().to_dict()
    dated = expanded[year.notna()]
    usable = dated[(dated["cbsa_code"] != "") & (dated["zcta"] != "")]
    uy = pd.to_numeric(usable["open_year"], errors="coerce")
    window = usable[(uy > FIRST_YEAR) & (uy <= LAST_YEAR)]
    episodes = window[["cbsa_code", "open_year",
                       "open_quarter"]].drop_duplicates()
    return {
        "rows": int(len(expanded)),
        "by_source_dataset": {k: int(v) for k, v in by_source.items()},
        "dated": int(len(dated)),
        "undated": int(len(expanded) - len(dated)),
        "dated_and_placed_in_a_cbsa": int(len(usable)),
        "distinct_cbsas": int(expanded.loc[expanded["cbsa_code"] != "",
                                           "cbsa_code"].nunique()),
        "distinct_zctas": int(expanded.loc[expanded["zcta"] != "",
                                           "zcta"].nunique()),
        "year_range": [int(year.min()), int(year.max())],
        "in_panel_window": {
            "first_year": FIRST_YEAR, "last_year": LAST_YEAR,
            "decisions": int(len(window)),
            "independent_episodes": int(len(episodes)),
            "per_parameter_at_5_parameters": round(len(episodes) / 5, 1),
            "note": ("Projected, not fitted — the same move "
                     "warehouse/national.summarise makes, applied to the "
                     "facility frame because no national risk set exists. "
                     "warehouse/national reports 80 decisions and 79 "
                     "episodes on the 104-row file, against a floor of 10 "
                     "events per parameter. Nothing has been refitted; "
                     "models/ is untouched."),
        },
    }


def edit_result(checked: pd.DataFrame, failures: list[dict], rows: int,
                dated: int) -> dict:
    """The ``E_operating_by`` result, with its denominator stated twice.

    The pass rate is over rows the matcher LINKED to an OSHA building, which
    is the only subset the edit can speak about. A row with no OSHA match is
    unchecked, and unchecked is not passed.
    """
    linked = checked["osha_operating_by"].notna()
    n_linked = int(linked.sum())
    n_fail = len(failures)
    by_source: dict[str, dict] = {}
    for name, part in checked[linked].groupby("source_dataset"):
        by_source[str(name)] = {
            "linked": int(len(part)),
            "falsified": int(part["open_date_falsified"].sum()),
            "pass_rate": round(1 - part["open_date_falsified"].mean(), 4),
        }
    return {
        "evaluated": True,
        "disposition": "report",
        "panel_rows": int(rows),
        "rows_with_a_date": int(dated),
        "linked_to_an_osha_building": n_linked,
        "unchecked_no_osha_match": int(dated - n_linked),
        "falsified": n_fail,
        "pass_rate": round((n_linked - n_fail) / n_linked, 4) if n_linked
        else None,
        "by_source_dataset": by_source,
        "failures": failures,
        "note": ("An unchecked row is not a passing row. The edit can only "
                 "speak about the rows an OSHA building was matched to."),
    }
