"""Merge the OCR'd MWPVL delivery stations into an EXPANDED facility panel.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.mwpvl_merge

Writes ``data/external/facility_panel/national_facilities_expanded.csv`` and
``outputs/metrics/mwpvl_merge.json``. It does not touch
``national_facilities.csv``, which is hand-verified and stays the reference.

Only the two SMALL-PACKAGE DELIVERY STATION tables are read -- 635 of the
1,904 rows in `mwpvl_facilities.csv`. See `DELIVERY_STATION_TABLES` for why
that filter exists and what it would have cost to omit it.

The part that has to be right is the duplicate screen
-----------------------------------------------------
``FACILITY_PANEL_PROVENANCE`` §19.2 is the warning: 362 rows went out for
hand-labelling and **289 of them were already classified**, because the
worklist was screened on an exact address key. The screen here is the
project's Fellegi-Sunter comparator over parsed addresses
(``common/linkage.py``), the same one that found HOLLYGLEN/HAWTHORNE and
GRANT LINE/GRANTLINE. No new matching rule is defined in this module.

Two screens, not one
--------------------
1. **MWPVL against the panel.** Cross-source pairs only, built exactly as
   ``warehouse/edits._tightest_bounds`` builds them, so "same building" means
   the same thing here as it does in the declared edit.
2. **MWPVL against itself**, through ``facility_dedup.adjudicate``. §13.1 of
   ``docs/data/MWPVL_OCR_PIPELINE.md`` measures a 3% row-merge defect — a
   facility whose postal code failed to OCR has no anchor and its words join
   the row above — so the same building can appear twice.

A REVIEW verdict is not a merge and is not a new row. Winkler's eq. (4) has
three outcomes and the middle one is "hold for clerical review"; those rows
are listed in the artefact with the panel row they resemble and are kept OUT
of the expanded file. A wrong panel is worse than a small one.

What is NOT done here
---------------------
Nothing is corrected and nothing is imputed. ``open_year`` still reads 2094
on the row where it read 2094; ``date_flag`` says so. No coordinate is
geocoded — there is no network on this machine and there would be no excuse
if there were.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.linkage import MATCH, REVIEW, LinkRecord, candidate_pairs
from ..common.linkage import compare as compare_pair
from ..common.log_json import write_json
from ..common.logging_setup import get_logger
from ..ingest.facility_check import _check_facility_panel
from ..ingest.mwpvl_panel import STATES, quarter_index
from . import edits, mwpvl_geo, mwpvl_print, mwpvl_report
from .facility_dedup import adjudicate
from .mwpvl_shape import align_national, to_panel_rows

_log = get_logger("warehouse.mwpvl_merge")

MWPVL = paths.INTERIM / "mwpvl_facilities.csv"

#: The only tables whose rows belong in a US delivery-station panel.
#:
#: THIS FILTER IS LOAD-BEARING AND WAS ADDED AFTER THE FACT. When this module
#: was written, `mwpvl_facilities.csv` held 591 rows from the two small-package
#: delivery station tables and nothing else, so reading the whole file was the
#: same as reading the delivery stations. Then the remaining eleven tables
#: finished OCR and the file became 1,904 rows: 385 US fulfilment centres, 114
#: sortation centres, 69 inbound cross docks, 458 rest-of-world sites, and so
#: on. Re-running unfiltered would have merged Japanese mini-delivery-stations
#: and million-square-foot fulfilment centres into a panel of US delivery
#: stations, and nothing would have complained -- the rows have the same
#: columns and geocode perfectly well.
#:
#: The panel is `facility_type == "DS"`. Everything else is a different
#: facility class serving different demand at a different scale.
#:
#: Heavy/bulky delivery stations (table 09) are DELIBERATELY EXCLUDED. MWPVL
#: describes them as a separate network launched in 2017 for 60-300 lb
#: merchandise requiring white-glove service (docs/data/MWPVL_2025.md §3.5).
#: They are delivery stations by name and a different business by economics.
#: Pooling them is a specification choice somebody should make on purpose.
DELIVERY_STATION_TABLES = (
    "08_us_delivery_station",
    "08_us_delivery_station_part2",
)
NATIONAL = paths.EXTERNAL / "facility_panel" / "national_facilities.csv"
EXPANDED = (paths.EXTERNAL / "facility_panel"
            / "national_facilities_expanded.csv")
ARTEFACT = paths.METRICS / "mwpvl_merge.json"


def _link_records(frame: pd.DataFrame, zip_col: str) -> list[LinkRecord]:
    """One LinkRecord per row, built the way ``edits._tightest_bounds`` does.

    The building code is deliberately NOT passed from MWPVL's ``code``
    column. ``linkage.compare`` short-circuits on a code pair, so an OCR'd
    code would override the address evidence in both directions — and the
    codes are OCR'd from the same picture as everything else. Whatever
    ``parse_address`` finds inside the street box still counts, exactly as it
    does for the OSHA match. The codes are used below as a DIAGNOSTIC on the
    matcher's output rather than as an input to it.
    """
    return [LinkRecord.build(str(r["facility_id"]),
                             str(r.get("site_address") or ""),
                             str(r.get("city") or ""),
                             str(r.get("state") or ""),
                             str(r.get(zip_col) or ""))
            for r in frame.to_dict("records")]


def _cross_screen(a: list[LinkRecord], b: list[LinkRecord],
                  left: pd.DataFrame) -> dict:
    """Which MWPVL rows (``a``) are already in the panel (``b``).

    Returns ``{"match": {left_id: [right_id, ...]}, "review": [...]}``. A
    left row matching TWO right rows is kept as a list, not collapsed: that
    is how §12.6's duplicate national pairs look from the outside, and
    flattening it would hide them.
    """
    n = len(a)
    matched: dict[str, list[str]] = {}
    review: list[dict] = []
    for x, y in candidate_pairs(a + b):
        if (x < n) == (y < n):
            continue
        i, j = (x, y - n) if x < n else (y, x - n)
        verdict = compare_pair(a[i], b[j])
        if verdict.call == MATCH:
            matched.setdefault(a[i].rid, []).append(b[j].rid)
        elif verdict.call == REVIEW:
            review.append({"mwpvl_id": a[i].rid, "panel_id": b[j].rid,
                           "why": verdict.why,
                           "score": round(verdict.score, 3),
                           "mwpvl_address": str(
                               left.loc[left["facility_id"] == a[i].rid,
                                        "site_address"].iloc[0])})
    return {"match": matched, "review": review}


def _code_diagnostics(frame: pd.DataFrame, folded: list[dict]) -> dict:
    """What MWPVL's own facility codes say about the address matcher's work.

    Two independent checks, both reported and neither acted on:

    * codes that DISAGREE inside a group the matcher merged — the §13.1
      row-merge defect seen from the code side;
    * the same non-empty code on rows the matcher did NOT merge — candidate
      duplicates the address evidence could not reach, usually because one
      of the two rows has no street at all.
    """
    by_id = frame.set_index("facility_id")["mwpvl_code"].to_dict()
    merged_disagree = [g["facility_ids"] for g in folded
                       if len({by_id.get(i, "") for i in g["facility_ids"]
                               if by_id.get(i, "")}) > 1]
    grouped = {i for g in folded for i in g["facility_ids"]}
    codes: dict[str, list[str]] = {}
    for rid, code in by_id.items():
        if code:
            codes.setdefault(code, []).append(rid)
    unmerged = [ids for code, ids in sorted(codes.items())
                if len(ids) > 1 and not any(
                    set(ids) <= set(g["facility_ids"]) for g in folded)]
    return {
        "groups_whose_codes_disagree": len(merged_disagree),
        "groups_whose_codes_disagree_ids": merged_disagree[:20],
        "unmerged_rows_sharing_a_code": len(unmerged),
        "unmerged_rows_sharing_a_code_ids": unmerged[:20],
        "rows_in_a_merged_group": len(grouped),
        "note": ("Reported, not acted on. linkage.compare would settle either "
                 "case outright on a code pair, but these codes are OCR'd "
                 "from the same image as the rest of the row, so letting them "
                 "override parsed-address evidence would be trusting the "
                 "weaker reading. Both lists are clerical review."),
    }


def run() -> dict:
    """Do the merge. Returns everything measured; writes both artefacts."""
    if not MWPVL.exists():
        raise SystemExit(f"  {paths.rel(MWPVL)} not found\n  run: python -m "
                         "siting_atlas.ingest.mwpvl_tables\n")
    raw = pd.read_csv(MWPVL, encoding="utf-8-sig", dtype=str)
    all_rows = len(raw)
    all_tables = raw["table"].nunique()
    raw = raw[raw["table"].isin(DELIVERY_STATION_TABLES)]
    raw = raw.reset_index(drop=True)
    national = pd.read_csv(NATIONAL, encoding="utf-8-sig", dtype=str)

    geo, geo_report = mwpvl_geo.resolve(raw["postcode"])
    ocr_grade = mwpvl_geo.grade_ocr_state(raw["addr_region"], geo, STATES)
    nat_geo, nat_geo_report = mwpvl_geo.resolve(national["zip"])

    shaped = to_panel_rows(raw, geo)
    shaped["open_q_index"] = [
        quarter_index(y, m) for y, m in
        zip(pd.to_numeric(raw["open_year"], errors="coerce"),
            pd.to_numeric(raw["open_month"], errors="coerce"), strict=True)]

    # SCREEN 2 first: deduplicating MWPVL against itself before comparing it
    # to the panel means a building present twice cannot be counted as one
    # duplicate and one new row.
    internal, folded = adjudicate(shaped)
    internal = internal.drop(
        columns=["open_q_index_lower", "open_q_index_upper"]
    ).reset_index(drop=True)
    dropped_internal = len(shaped) - len(internal)

    # SCREEN 1.
    left = _link_records(internal, "zip")
    right = _link_records(national, "zip")
    cross = _cross_screen(left, right, internal)
    already = set(cross["match"])
    held = {r["mwpvl_id"] for r in cross["review"]}
    new = internal[~internal["facility_id"].isin(already | held)].copy()
    new["duplicate_of"] = new["duplicate_of"].fillna("")
    unresolved = new[new["open_date_unresolved"]]
    if len(unresolved):
        # Today this is empty. The guard states the assumption rather than
        # leaving a later MWPVL vintage to discover it: adjudicate() leaves
        # open_q_index NaN when two folded rows disagree about the date and
        # their provenances tie, but open_year in the CSV still carries one
        # of the two. Shipping that pair silently would be the merge picking
        # a date, which is the one thing this module must not do.
        raise SystemExit(
            f"  {len(unresolved)} internally-duplicated MWPVL row(s) "
            f"disagree about the opening date and no reliability weight "
            f"separates them: {', '.join(unresolved['facility_id'])}.\n"
            f"  Fellegi & Holt Sec.1 option 2 — resolve by collection, not "
            f"by rule. Nothing written.\n")

    base = align_national(national, nat_geo)
    expanded = pd.concat([base, new[list(base.columns)]], ignore_index=True)
    EXPANDED.parent.mkdir(parents=True, exist_ok=True)
    expanded.to_csv(EXPANDED, index=False)

    validation = _validate(expanded)
    schema_errors, schema_warnings, schema_stats = _check_facility_panel(
        EXPANDED)
    report = {
        "mwpvl_rows_in_file": int(all_rows),
        # Parsed vs used. Conflating the two is what made the old caveat
        # wrong; naming both makes the distinction readable from the JSON.
        "mwpvl_tables_parsed": int(all_tables),
        "mwpvl_tables_used": list(DELIVERY_STATION_TABLES),
        "mwpvl_rows_excluded_wrong_facility_class": int(all_rows - len(raw)),
        "mwpvl_rows": int(len(raw)),
        "internal_duplicates_dropped": int(dropped_internal),
        "after_internal_dedup": int(len(internal)),
        "already_in_panel": len(already),
        "held_for_clerical_review": len(held),
        "new_rows_added": int(len(new)),
        "panel_rows_before": int(len(national)),
        "panel_rows_after": int(len(expanded)),
        "internal_duplicate_groups": folded,
        "cross_matches": dict(sorted(cross["match"].items())),
        "cross_review_band": cross["review"],
        "code_diagnostics": _code_diagnostics(shaped, folded),
        "screenability": mwpvl_report.screenability(left),
        "recall_probe_vs_postcode_and_house_number":
            mwpvl_report.recall_probe(left, right),
        "geography_mwpvl": geo_report,
        "geography_national": nat_geo_report,
        "ocr_state_grade": ocr_grade,
        "new_row_geography": mwpvl_report.geography(new),
        "new_row_dates": mwpvl_report.dates(new),
        "new_row_provenance": mwpvl_report.provenance(new),
        "expanded_panel": mwpvl_report.panel(expanded),
        "validation_E_operating_by": validation,
        "facility_check": {
            "passes": not schema_errors,
            "errors": schema_errors,
            "warnings": schema_warnings,
            "stats": schema_stats,
            "note": ("ingest/facility_check treats open_year as REQUIRED, so "
                     "the expanded file does not pass it: MWPVL prints no "
                     "year on a quarter of its rows. The alternatives are to "
                     "drop those rows, which throws away the location a "
                     "fourth capture list exists to supply, or to invent a "
                     "year. Neither is taken. The failure is reported here "
                     "so nobody discovers it by running --check."),
        },
        "output": paths.rel(EXPANDED),
        # Counted from this run, not typed: the typed list said "2 of 13
        # tables parsed" and "591 delivery stations" long after both had
        # stopped being true. See mwpvl_report.caveats.
        "caveats": mwpvl_report.caveats(
            rows_in_file=int(all_rows), tables_parsed=int(all_tables),
            rows_used=int(len(raw)), tables_used=DELIVERY_STATION_TABLES),
    }
    # `write_json`, not `json.dumps`, so the artefact carries the run that
    # produced it. Two merges of two MWPVL vintages are otherwise
    # indistinguishable on disk, and the project's tie-break rule -- "where a
    # run_id exists, the artefact wins" -- has nothing to work with.
    write_json(ARTEFACT, report)
    return report


def _validate(expanded: pd.DataFrame) -> dict:
    """Run the declared edit ``E_operating_by`` over the expanded panel.

    ``REPORT``, not ``EXCLUDE``. The pass rate is the measurement this whole
    merge is graded on, and excluding failures before counting them destroys
    it — the same argument ``ingest/mwpvl_panel`` makes.
    """
    frame = expanded.copy()
    year = pd.to_numeric(frame["open_year"], errors="coerce")
    quarter = pd.to_numeric(frame["open_quarter"], errors="coerce")
    frame["open_q_index"] = year * 4 + quarter.fillna(1) - 1
    dated = frame[frame["open_q_index"].notna()].reset_index(drop=True)

    osha = edits.load_operating_bounds()
    if osha is None:
        return {"evaluated": False,
                "reason": ("data/interim/osha_amazon.csv is absent, so "
                           "E_operating_by CANNOT BE EVALUATED. That is not "
                           "the same as passing."),
                "rows_it_would_have_checked": int(len(dated))}

    checked, failures = edits.apply_operating_by(
        dated, osha, disposition=edits.REPORT, label="expanded panel")
    return mwpvl_report.edit_result(checked, failures, len(frame), len(dated))


def main() -> int:
    from ..common.context import init_run
    from ..common.logging_setup import configure

    paths.ensure_dirs()
    init_run()
    configure()
    mwpvl_print.to_stdout(run())
    print(f"  -> {paths.rel(EXPANDED)}")
    print(f"  -> {paths.rel(ARTEFACT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
