"""Validation for the facility panel — the target variable.

Given its own module because it is the only manually-placed source checked at
column level, and because it is the file most likely to arrive damaged. Every
rule here exists because a real batch broke it:

  * leading zeros stripped by a spreadsheet, so 01890 joins to nothing;
  * an `open_quarter` of 0 or 5, which lands the event in the wrong year;
  * `company_page` vs `company_site` — an unvalidated vocabulary drifts, and
    both spellings reached the file before anything checked;
  * a batch of seven fulfillment centres and zero delivery stations, which
    answers a different question than the model asks.
"""

from __future__ import annotations

import csv
from pathlib import Path

FACILITY_REQUIRED = ("facility_id", "operator", "facility_type", "city",
                     "state", "zip", "open_year", "source_url", "source_type")
FACILITY_OPTIONAL = ("latitude", "longitude", "open_quarter", "close_year",
                     "close_quarter", "site_address", "square_feet",
                     "status", "confidence")

VALID_TYPES = {"FC", "SC", "DS", "SDC", "AMXL"}

# Provenance classes, ordered loosely by how much weight a row deserves. This
# set is validated because an unenforced vocabulary drifts: two collectors
# wrote `company_page` and `company_site` for the same thing, and nothing
# caught it. The value feeds the confidence audit, so a typo silently creates
# a provenance class of one.
VALID_SOURCE_TYPES = {
    "press_release",   # the operator's own announcement; strongest
    "permit",          # a building or occupancy permit with a filed date
    "news",            # local or trade press reporting the opening
    "company_site",    # an operator page listing the site, undated
    "job_posting",     # hiring for a named facility code; proves it operates
    "osm",             # OpenStreetMap; location only, never a date
    "other",
}

VALID_STATUS = {"open", "closed", "announced"}



def _closure_errors(rows: list[dict]) -> list[str]:
    """A closed facility must say WHEN, and it must close after it opened.

    Silence here is expensive in a way the other rules are not. A row marked
    ``closed`` with no ``close_year`` reaches ``warehouse.facilities`` as a
    close index of positive infinity, so the site enables its catchment
    forever — the panel then asserts service in a ZIP that lost it, and
    nothing downstream can tell the difference between "still open" and
    "we never wrote down the closing date". A close_year before the
    open_year produces an empty service window, which is the same failure
    with the sign flipped: the facility never enables anything and its
    event silently vanishes from the target.
    """
    errors: list[str] = []
    closed_undated = [r["facility_id"] for r in rows
                      if r.get("status") == "closed"
                      and not str(r.get("close_year", "")).strip()]
    if closed_undated:
        errors.append(
            f"{len(closed_undated)} row(s) are marked closed with no "
            f"close_year (e.g. {', '.join(closed_undated[:4])}); without it "
            f"the catchment stays enabled forever and the closure is lost")

    bad_q = [str(r.get("close_quarter")) for r in rows
             if str(r.get("close_quarter", "")).strip()
             and str(r["close_quarter"]).strip() not in {"1", "2", "3", "4"}]
    if bad_q:
        errors.append(f"{len(bad_q)} row(s) have a close_quarter outside 1-4")

    backwards = [r["facility_id"] for r in rows
                 if str(r.get("close_year", "")).strip().isdigit()
                 and str(r.get("open_year", "")).strip().isdigit()
                 and int(r["close_year"]) < int(r["open_year"])]
    if backwards:
        errors.append(
            f"{len(backwards)} row(s) close before they open "
            f"(e.g. {', '.join(backwards[:4])}); the service window is empty "
            f"and the facility will enable nothing")
    return errors


def _check_facility_panel(path: Path) -> tuple[list[str], list[str], dict]:
    """Column and content validation for the target variable.

    Returns (errors, warnings, stats). Errors block use; warnings do not.
    """
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict = {}

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = set(reader.fieldnames or [])
        missing = [c for c in FACILITY_REQUIRED if c not in cols]
        if missing:
            errors.append(f"missing required column(s): {', '.join(missing)}")
            return errors, warnings, stats

        rows = list(reader)

    stats["rows"] = len(rows)
    if not rows:
        errors.append("file has a header but no data rows")
        return errors, warnings, stats

    # Leading-zero damage is the single most common handoff failure: a
    # spreadsheet turns 01890 into 1890 and every join silently drops it.
    short_zips = [r["zip"] for r in rows
                  if r.get("zip") and len(r["zip"].strip()) < 5]
    if short_zips:
        errors.append(
            f"{len(short_zips)} ZIP code(s) shorter than 5 characters "
            f"(e.g. {', '.join(sorted(set(short_zips))[:4])}) — a spreadsheet "
            f"has stripped leading zeros; re-export with the column as Text")

    bad_year = [r["open_year"] for r in rows
                if not str(r.get("open_year", "")).strip().isdigit()]
    if bad_year:
        errors.append(f"{len(bad_year)} row(s) have a non-numeric open_year")

    bad_type = sorted({r["facility_type"] for r in rows
                       if r.get("facility_type") not in VALID_TYPES})
    if bad_type:
        warnings.append(
            f"unrecognised facility_type value(s): {', '.join(bad_type[:6])} "
            f"(expected {', '.join(sorted(VALID_TYPES))})")

    bad_src = sorted({r["source_type"] for r in rows
                      if r.get("source_type") not in VALID_SOURCE_TYPES})
    if bad_src:
        warnings.append(
            f"unrecognised source_type value(s): {', '.join(bad_src[:6])} "
            f"(expected {', '.join(sorted(VALID_SOURCE_TYPES))})")

    bad_status = sorted({r["status"] for r in rows
                         if r.get("status")
                         and r["status"] not in VALID_STATUS})
    if bad_status:
        warnings.append(
            f"unrecognised status value(s): {', '.join(bad_status[:6])} "
            f"(expected {', '.join(sorted(VALID_STATUS))})")

    # A quarter that is present must be 1-4. A blank is fine and honest; a
    # 0 or a 5 is a conversion error that would land the event in the wrong
    # year once the panel maps it to a date_id.
    bad_q = [r["open_quarter"] for r in rows
             if str(r.get("open_quarter", "")).strip()
             and str(r["open_quarter"]).strip() not in {"1", "2", "3", "4"}]
    if bad_q:
        errors.append(
            f"{len(bad_q)} row(s) have an open_quarter outside 1-4 "
            f"(e.g. {', '.join(sorted(set(map(str, bad_q)))[:4])}); leave it "
            f"blank if the quarter is unknown rather than guessing")

    errors.extend(_closure_errors(rows))

    # DS is the node that actually enables a ZIP for same-day service. A batch
    # that is all FC is answering a different question, so say so early.
    ds = sum(1 for r in rows if r.get("facility_type") == "DS")
    stats["delivery_stations"] = ds
    if rows and ds == 0:
        warnings.append(
            "no DS (delivery station) rows — fulfillment centres are regional "
            "nodes and do not by themselves enable a ZIP for same-day "
            "service, so a panel without delivery stations will not identify "
            "the outcome the model is about")

    no_source = sum(1 for r in rows if not (r.get("source_url") or "").strip())
    if no_source:
        warnings.append(f"{no_source} row(s) have no source_url — provenance "
                        f"is incomplete for those facilities")

    years = [int(r["open_year"]) for r in rows
             if str(r.get("open_year", "")).strip().isdigit()]
    if years:
        stats["year_range"] = f"{min(years)}-{max(years)}"
    stats["operators"] = sorted(
        {r["operator"] for r in rows if r.get("operator")})
    stats["types"] = sorted({r["facility_type"] for r in rows
                             if r.get("facility_type")})
    stats["states"] = len({r["state"] for r in rows if r.get("state")})
    stats["with_quarter"] = sum(
        1 for r in rows if str(r.get("open_quarter", "")).strip().isdigit())
    return errors, warnings, stats
