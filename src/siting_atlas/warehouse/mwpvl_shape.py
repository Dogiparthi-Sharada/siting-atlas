"""Shape OCR'd MWPVL rows into the national facility-panel schema.

Nothing here corrects a value. Three things happen and they are all
relabelling or arithmetic:

  * columns are renamed into ``national_facilities.csv``'s schema so the two
    frames stack;
  * a month becomes a quarter, which is a unit conversion (October -> Q4) and
    not a judgement;
  * MWPVL's own caveats are copied across unchanged and summarised into one
    boolean, ``mwpvl_vouched``, so a row the publisher does not stand behind
    is one column away downstream instead of seven.

A date that looks wrong is FLAGGED, never repaired. ``date_flag`` carries the
finding and ``open_year`` still carries ``2094``.

Why ``source_type`` is ``other`` and not ``mwpvl``
--------------------------------------------------
``ingest/facility_check.VALID_SOURCE_TYPES`` is a closed vocabulary, and its
own comment says why: "an unenforced vocabulary drifts ... a typo silently
creates a provenance class of one". MWPVL is a consultancy census and is none
of press_release / permit / news / company_site / job_posting / osm, so it is
``other`` — which is also last in ``facility_dedup.DATE_RELIABILITY``, and
that is the correct rank for a source that declares its own incompleteness
five times (``docs/data/MWPVL_2025.md`` §6). The precise provenance travels
in a new column, ``source_dataset``, where it cannot be confused for one of
the seven.
"""

from __future__ import annotations

import pandas as pd

#: MWPVL's own per-record caveats, copied through verbatim. §9 of
#: ``docs/data/MWPVL_OCR_PIPELINE.md`` calls these "the per-record
#: reliability weight Fellegi & Holt §7 asks for and almost no source
#: supplies", which is exactly what they are used as below.
FLAGS = ("not_confirmed", "delayed", "cancelled", "closed", "sqft_estimated",
         "colocated", "rural_wagon_wheel")

#: The three flags that say the publisher does not vouch for the building
#: existing as described. ``closed`` is NOT one of them — MWPVL is confident
#: about a closure — and the other three are about square footage or
#: topology, not about existence.
NOT_VOUCHED = ("not_confirmed", "delayed", "cancelled")

SOURCE_DATASET = "mwpvl_2025q1"
SOURCE_URL = "https://mwpvl.com/html/amazon_com.html"

#: The article states its own vintage as 2025 Q1. A bare year outside this
#: window is flagged, not fixed. The lower edge is MWPVL's own prose: the
#: small-package delivery-station network launched in late 2013
#: (``docs/data/MWPVL_2025.md`` §3.5), so an earlier date is falsified by the
#: same document. The upper edge allows five years of announced pipeline past
#: the vintage, which admits the one 2028 row as a plausible announcement and
#: catches the one 2094 row as OCR damage.
YEAR_FLOOR, YEAR_CEILING = 2013, 2030

DATE_OK = ""
DATE_BEFORE_NETWORK = "before_ds_network_launch_2013"
DATE_IMPLAUSIBLE = "year_outside_2013_2030"

#: Columns of ``data/external/facility_panel/national_facilities.csv``, in
#: file order. The expanded panel leads with these so the existing schema is
#: a prefix of the new one and any reader that selects by name still works.
NATIONAL_COLUMNS = ("facility_id", "operator", "facility_type", "city",
                    "state", "zip", "site_address", "latitude", "longitude",
                    "open_year", "open_quarter", "close_year", "close_quarter",
                    "square_feet", "status", "source_url", "source_type",
                    "confidence", "cbsa_title")

#: Everything the expansion adds. Present and empty on the 104 existing rows,
#: which is what makes a source distinguishable downstream by a column test
#: rather than by an id prefix.
ADDED_COLUMNS = ("source_dataset", "zcta", "cbsa_code", "geo_status",
                 "date_precision", "date_flag", "mwpvl_vouched",
                 "mwpvl_code", "mwpvl_table", "mwpvl_row", "mwpvl_region_ocr",
                 "mwpvl_description", "duplicate_of",
                 "open_date_contradicted", "open_date_unresolved", *FLAGS)

#: Added columns whose empty value is ``False`` rather than the empty string.
BOOLEAN_COLUMNS = (*FLAGS, "mwpvl_vouched", "open_date_contradicted",
                   "open_date_unresolved")


def _flag(frame: pd.DataFrame, name: str) -> pd.Series:
    """One MWPVL boolean column, read from the CSV's ``True``/``False``."""
    if name not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[name].astype(str).str.strip().str.lower().eq("true")


def _quarter(month, quarter) -> str:
    """Q from an explicit quarter, else from a month. Never invented.

    MWPVL prints a quarter directly on 26 rows and a month on 306. Where it
    prints neither the cell is left EMPTY rather than defaulted to Q1:
    ``warehouse/facility_load`` already applies the Q1 convention at load and
    records it in ``open_quarter_imputed``, so writing Q1 into the file here
    would destroy the distinction that module exists to preserve.
    """
    if quarter is not None and not pd.isna(quarter):
        return str(int(quarter))
    if month is None or pd.isna(month):
        return ""
    return str((int(month) - 1) // 3 + 1)


def _date_flag(year) -> str:
    """Localise an impossible date. Fellegi-Holt: flag the field, keep it."""
    if year is None or pd.isna(year):
        return DATE_OK
    y = int(year)
    if y < YEAR_FLOOR:
        return DATE_BEFORE_NETWORK
    return DATE_IMPLAUSIBLE if y > YEAR_CEILING else DATE_OK


def _status(not_confirmed: pd.Series, cancelled: pd.Series) -> pd.Series:
    """MWPVL's words mapped onto ``facility_check.VALID_STATUS``.

    "Not yet confirmed" is an announcement and ``announced`` is a declared
    status, so the row enters the panel saying what the publisher said about
    it. ``delayed`` deliberately does NOT move the status: a delayed building
    can be open, announced or abandoned and MWPVL's phrasing does not say
    which. It stays a flag.

    And neither does ``closed``, which is the harder call. The flag fires on
    two rows and **both are false positives**, read off the description text:

        DBM5  "...Currently the site of the Century Plaza closed in 2009."
              the shopping mall closed; the delivery station is what replaced
              it
        DLA2  "Delivery Station closed in June, 2017; Reopened in 2017"
              closed and reopened, so open

    A ``closed`` status with no ``close_year`` — and MWPVL prints no closing
    date in either row — reaches ``warehouse/facilities`` as a close index of
    positive infinity, which ``facility_check._closure_errors`` calls out as
    "the catchment stays enabled forever and the closure is lost". Promoting
    a flag that is 0 for 2 into the operative field would be manufacturing
    that failure. The flag itself is carried through untouched in the
    ``closed`` column, so nothing is hidden and nothing is corrected; this
    function simply declines to derive from it.
    """
    out = pd.Series("open", index=not_confirmed.index)
    out[not_confirmed | cancelled] = "announced"
    return out


def to_panel_rows(raw: pd.DataFrame, geo: pd.DataFrame,
                  id_prefix: str = "MWP") -> pd.DataFrame:
    """MWPVL rows in the national schema, with provenance columns attached.

    ``raw`` is ``data/interim/mwpvl_facilities.csv`` read as strings; ``geo``
    is :func:`mwpvl_geo.resolve`'s frame on the same index. Row order and row
    count are preserved so ``facility_id`` is stable across runs and a
    reported id can be traced back to a line of the OCR output.
    """
    flags = {name: _flag(raw, name) for name in FLAGS}
    year = pd.to_numeric(raw.get("open_year"), errors="coerce")
    month = pd.to_numeric(raw.get("open_month"), errors="coerce")
    quarter = pd.to_numeric(raw.get("open_quarter"), errors="coerce")
    vouched = ~(flags["not_confirmed"] | flags["delayed"] | flags["cancelled"])

    out = pd.DataFrame(index=raw.index)
    out["facility_id"] = [f"{id_prefix}-{i:04d}"
                          for i in range(1, len(raw) + 1)]
    out["operator"] = "Amazon"
    # Both parsed tables are the article's US delivery-station table
    # (docs/data/MWPVL_OCR_PIPELINE.md §0), so the type is the SOURCE's
    # classification of its own section, not a rule applied to a code.
    out["facility_type"] = "DS"
    out["city"] = raw["city"].fillna("").str.strip()
    out["state"] = geo["state"]
    out["zip"] = raw["postcode"].fillna("").str.strip().str[:5]
    out["site_address"] = raw["street"].fillna("").str.strip()
    out["latitude"] = ""
    out["longitude"] = ""
    out["open_year"] = year.astype("Int64").astype(str).replace("<NA>", "")
    out["open_quarter"] = [_quarter(m, q) for m, q in zip(month, quarter,
                                                          strict=True)]
    out["close_year"] = ""
    out["close_quarter"] = ""
    out["square_feet"] = raw["sqft"].fillna("")
    out["status"] = _status(flags["not_confirmed"], flags["cancelled"])
    out["source_url"] = SOURCE_URL
    out["source_type"] = "other"
    # MWPVL's own vouching, used as the confidence grade. Not a new ranking:
    # it is the publisher's statement about its own row.
    out["confidence"] = pd.Series("medium", index=raw.index).mask(~vouched,
                                                                 "low")
    out["cbsa_title"] = geo["cbsa_title"]

    out["source_dataset"] = SOURCE_DATASET
    out["zcta"] = geo["zcta"]
    out["cbsa_code"] = geo["cbsa_code"]
    out["geo_status"] = geo["geo_status"]
    out["date_precision"] = raw["date_precision"].fillna("")
    out["date_flag"] = [_date_flag(y) for y in year]
    out["mwpvl_vouched"] = vouched
    out["mwpvl_code"] = raw["code"].fillna("").str.strip()
    out["mwpvl_table"] = raw["table"].fillna("")
    out["mwpvl_row"] = raw["row"].fillna("")
    out["mwpvl_region_ocr"] = raw["addr_region"].fillna("")
    out["mwpvl_description"] = raw["description"].fillna("")
    for name, series in flags.items():
        out[name] = series
    return out


def align_national(national: pd.DataFrame, geo: pd.DataFrame) -> pd.DataFrame:
    """The 104 existing rows widened to the expanded schema, unchanged.

    Every added column is filled with the empty string or ``False`` — never
    with a value that could be mistaken for a measurement. ``source_dataset``
    says ``national_facilities`` so the two provenances are separable by one
    equality test. The three geography columns are filled from the same
    crosswalk the MWPVL rows use, because a panel where half the rows carry a
    ``cbsa_code`` and half do not is a join waiting to drop the older half.
    ``cbsa_title`` is NOT touched: it is the curated file's own value.
    """
    out = national.copy()
    for column in ADDED_COLUMNS:
        out[column] = False if column in BOOLEAN_COLUMNS else ""
    out["source_dataset"] = "national_facilities"
    out["zcta"] = geo["zcta"]
    out["cbsa_code"] = geo["cbsa_code"]
    out["geo_status"] = geo["geo_status"]
    return out
