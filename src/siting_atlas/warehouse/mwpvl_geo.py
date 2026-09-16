"""Postal code -> ZCTA -> county -> CBSA, from crosswalks already on disk.

Why this is a separate module from the merge
--------------------------------------------
The merge decides which buildings exist. This decides where they are. They
fail differently and they are measured differently, so they are counted
separately: a row can be genuinely new and still unusable by
``models/choice`` because its ZCTA sits in no metro.

The three assumptions, each stated rather than buried
-----------------------------------------------------
1. **A postal code is read as a ZCTA.** They are not the same object — USPS
   ZIPs are delivery routes, ZCTAs are Census tabulation areas built from
   blocks — and a ZIP with no residential delivery has no ZCTA at all. This
   is not a new liberty taken here: ``warehouse/facility_load`` already does
   ``frame["zcta"] = frame["zip"].str.zfill(5)`` for all 104 national rows.
   Doing the same thing keeps the expanded panel joinable with the panel it
   extends. What this module adds is the *count* of postcodes that are not
   ZCTAs, which nothing previously reported.

2. **State comes from the crosswalk, not from the OCR.** MWPVL's state column
   is OCR'd free text and arrives damaged — "Taxas", "Texas Texas",
   "lebanon: Tannesses:". The county GEOID's first two digits are a state
   FIPS code, which is a fact about the crosswalk rather than a reading of a
   picture. The OCR'd string is kept in ``addr_region`` and the disagreement
   between the two is reported, because that disagreement grades the OCR for
   free.

3. **Nothing is geocoded.** There is no network on this machine and no
   coordinate is invented. A row whose postcode is absent from the crosswalk
   gets an empty ZCTA and is counted, not placed.

Known gap, inherited not introduced
-----------------------------------
The CBSA delineation is OMB 2023 and uses Connecticut's nine planning
regions (FIPS 09110-09190); the ZCTA-to-county file is 2020 and uses the
eight legacy counties (09001-09015). The two do not join, so every
Connecticut row resolves to a state and to no CBSA. ``ingest/registry.py``
records this under ``cbsa_county`` and ``bps_county``; it is reported here
with its row count rather than silently producing a blank.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from .geo_keys import FIPS_STATE

_log = get_logger("warehouse.mwpvl_geo")

ZCTA_COUNTY = paths.INTERIM / "zcta_county.parquet"
CBSA_COUNTY = paths.INTERIM / "cbsa_county.parquet"

#: Connecticut's legacy state FIPS, for the gap named in the docstring.
CT_FIPS = "09"

#: What ``geo_status`` can say. Every row carries exactly one, so the
#: failures add up to the total and cannot be lost between two subtotals.
OK = "ok"
NO_ZCTA = "postcode_not_a_zcta"
NO_CBSA = "county_in_no_cbsa"
CT_VINTAGE = "connecticut_county_vintage_gap"
NO_XWALK = "crosswalk_absent"

COLUMNS = ("zcta", "county_geoid", "state", "cbsa_code", "cbsa_title",
           "geo_status")


def _dominant_county(xwalk: pd.DataFrame) -> pd.Series:
    """ZCTA -> the county holding most of its land.

    The delivered ``zcta_county.parquet`` already carries one row per ZCTA
    (33,791 rows, 33,791 distinct ZCTAs, measured 2026-09-14), so this is a
    no-op today. It is written as a reduction anyway because the registry
    describes the upstream file as one row per ZCTA-county *intersection*,
    and a future re-ingest that keeps the splits must not silently pick
    whichever row pandas saw first.
    """
    ordered = xwalk.sort_values(["zcta", "shared_land_area", "county_geoid"],
                                ascending=[True, False, True])
    return ordered.drop_duplicates("zcta").set_index("zcta")["county_geoid"]


def resolve(postcodes: pd.Series) -> tuple[pd.DataFrame, dict]:
    """Place each postal code. Returns ``(frame, report)``.

    ``frame`` has :data:`COLUMNS` and the index of ``postcodes``. Never
    raises on a missing crosswalk: it returns every row as :data:`NO_XWALK`
    and says in the report how many rows that cost, which is the difference
    between "we could not do it" and "there was nothing to do".
    """
    keys = postcodes.fillna("").astype(str).str.strip().str[:5]
    out = pd.DataFrame(dict.fromkeys(COLUMNS, ""),
                       index=postcodes.index)

    missing = [paths.rel(p) for p in (ZCTA_COUNTY, CBSA_COUNTY)
               if not p.exists()]
    if missing:
        out["geo_status"] = NO_XWALK
        _log.error("crosswalk(s) absent: %s. %d row(s) CANNOT be placed and "
                   "are NOT guessed. Run python -m siting_atlas.ingest.census "
                   "to build them.", ", ".join(missing), len(out))
        return out, {"crosswalks_present": False,
                     "crosswalks_missing": missing,
                     "rows": int(len(out)),
                     "rows_uncovered_by_the_missing_file": int(len(out)),
                     "with_zcta": 0, "with_cbsa": 0,
                     "by_status": {NO_XWALK: int(len(out))}}

    zcta_county = pd.read_parquet(ZCTA_COUNTY)
    cbsa = pd.read_parquet(CBSA_COUNTY).drop_duplicates("county_geoid")
    counties = _dominant_county(zcta_county)
    cbsa_code = cbsa.set_index("county_geoid")["cbsa_code"]
    cbsa_title = cbsa.set_index("county_geoid")["cbsa_title"]

    known = keys.isin(counties.index)
    out.loc[known, "zcta"] = keys[known]
    out["county_geoid"] = keys.map(counties).fillna("")
    out["state"] = out["county_geoid"].str[:2].map(FIPS_STATE).fillna("")
    out["cbsa_code"] = out["county_geoid"].map(cbsa_code).fillna("")
    out["cbsa_title"] = out["county_geoid"].map(cbsa_title).fillna("")

    out["geo_status"] = OK
    out.loc[out["cbsa_code"] == "", "geo_status"] = NO_CBSA
    ct = (out["county_geoid"].str[:2] == CT_FIPS) & (out["cbsa_code"] == "")
    out.loc[ct, "geo_status"] = CT_VINTAGE
    out.loc[out["zcta"] == "", "geo_status"] = NO_ZCTA

    report = {
        "crosswalks_present": True,
        "zcta_county": paths.rel(ZCTA_COUNTY),
        "cbsa_county": paths.rel(CBSA_COUNTY),
        "rows": int(len(out)),
        "with_zcta": int((out["zcta"] != "").sum()),
        "with_state": int((out["state"] != "").sum()),
        "with_cbsa": int((out["cbsa_code"] != "").sum()),
        "by_status": {k: int(v) for k, v in
                      out["geo_status"].value_counts().items()},
        "note": (
            "A postal code is read as a ZCTA, which is what "
            "warehouse/facility_load already does for the 104 national rows. "
            f"Rows counted under {NO_ZCTA} are postcodes with no ZCTA of that "
            "number in the 2020 relationship file; they are left unplaced, "
            f"not geocoded. {CT_VINTAGE} is the OMB-2023-vs-2020 county "
            "vintage gap recorded in ingest/registry.py, not a failure of "
            "this row."
        ),
    }
    _log.info("placed %d of %d postcodes: %d with a ZCTA, %d with a CBSA (%s)",
              report["with_cbsa"], report["rows"], report["with_zcta"],
              report["with_cbsa"],
              ", ".join(f"{k} {v}" for k, v in report["by_status"].items()))
    return out, report


def grade_ocr_state(ocr_state: pd.Series, resolved: pd.DataFrame,
                    name_to_code: dict) -> dict:
    """Compare MWPVL's OCR'd state name against the crosswalk's answer.

    A free measurement of the OCR that costs nothing and was flagged as not
    run in ``docs/data/MWPVL_OCR_PIPELINE.md`` §13.2. Only rows where BOTH
    sides speak can disagree, so the denominator is stated with the result.
    """
    spoken = ocr_state.fillna("").astype(str).str.strip().str.lower()
    mapped = spoken.map(name_to_code).fillna("")
    both = (mapped != "") & (resolved["state"] != "")
    agree = both & (mapped == resolved["state"])
    return {
        "ocr_state_parsed": int((mapped != "").sum()),
        "ocr_state_unparsed": int((mapped == "").sum()),
        "comparable": int(both.sum()),
        "agree": int(agree.sum()),
        "disagree": int((both & ~agree).sum()),
        "agreement_rate": (float(agree.sum()) / int(both.sum())
                           if int(both.sum()) else None),
    }
