"""L2 key bridges — the lookups that make two vintages of a code system join.

Split out of ``schema.py`` because these are reference tables, not warehouse
structure, and because the Connecticut bridge below needs enough explanation
that inlining it would bury ``build_dim_zcta``.

Three bridges live here:

1. **State FIPS -> USPS abbreviation.** CBP supplies an abbreviation directly
   but only for the 30,928 ZCTAs that have a business establishment; the
   remaining 2,863 are rural and would otherwise lose their EIA energy price.
   ``county_geoid`` is present for every ZCTA, so its first two digits are the
   reliable source.

2. **Connecticut legacy county -> 2022 planning region.** See below.

3. **ZCTA -> CBSA title**, which is (1) composed with the OMB delineation and
   is only correct because (2) runs first.

The Connecticut problem
-----------------------
Connecticut abolished its eight counties as statistical geographies in 2022
and replaced them with nine Councils of Government, published as "planning
regions" with new county-equivalent FIPS codes 09110-09190. The old codes
(09001-09015) are retired.

This project pins ZCTA geography at the 2020 vintage (``config.ZCTA_VINTAGE``)
and the ZCTA-to-county crosswalk is the 2020 Census relationship file, so
every Connecticut ZCTA carries a legacy county code. Three county-grain
sources joined to it are on the NEW vintage:

    EJScreen 2024 tracts   09110-09190   (884 CT tracts)
    OMB 2023 delineation   09110-09190   (9 CT rows, all nine regions)
    BPS permits            09110-09190   from 2023 on; legacy 2017-2021

For the other 49 states the two vintages are the same codes and nothing
notices. For Connecticut the join matches nothing at all, and because it is a
LEFT JOIN onto a dense spine the result is 288 ZCTAs of silent NULL rather
than an error. Measured on the panel of 2026-09-13: all 288 Connecticut ZCTAs
missing all five EJScreen columns (46,080 cells) — and, separately, all 288
missing ``cbsa_code`` and therefore all five BLS wage columns.

Why the bridge is at ZCTA grain, not county grain
-------------------------------------------------
Planning regions do not nest inside the legacy counties: both are unions of
towns, and the unions cut across each other. Litchfield County (09005) alone
splits three ways. A county-to-region crosswalk would therefore have to pick
one region per county and would be wrong for 11 of the 288 ZCTAs.

There is a better key available on disk. CBP 2022 is published on the new
geography and names the planning region per ZIP, so ``cbp.parquet`` already
holds a ZCTA-level ZIP -> planning-region mapping for 283 of the 288. The
remaining 5 ZIPs have no CBP row (no business establishment), and they are
assigned the modal region of their legacy county among the 283 — a rule
computed from the data rather than typed from memory, and recorded per row in
``region_source`` so the two kinds of assignment never blur together.

The nine codes and names below are NOT from memory: they are the intersection
of ``cbsa_county.parquet`` (OMB 2023 delineation, 9 CT rows) and
``building_permits.parquet`` (BPS 2023-2025), which agree exactly.
"""

from __future__ import annotations

import pandas as pd

from ..common.logging_setup import get_logger

_log = get_logger("warehouse.geo_keys")

# SIM905 is silenced because ruff's fix expands the split() into a 56-element
# list literal on one 700-column line. The whitespace-separated form is the
# readable one and makes an added state a one-token diff.
FIPS_STATE = dict(p.split(":") for p in (  # noqa: SIM905
    "01:AL 02:AK 04:AZ 05:AR 06:CA 08:CO 09:CT 10:DE 11:DC 12:FL 13:GA 15:HI "
    "16:ID 17:IL 18:IN 19:IA 20:KS 21:KY 22:LA 23:ME 24:MD 25:MA 26:MI 27:MN "
    "28:MS 29:MO 30:MT 31:NE 32:NV 33:NH 34:NJ 35:NM 36:NY 37:NC 38:ND 39:OH "
    "40:OK 41:OR 42:PA 44:RI 45:SC 46:SD 47:TN 48:TX 49:UT 50:VT 51:VA 53:WA "
    "54:WV 55:WI 56:WY 60:AS 66:GU 69:MP 72:PR 78:VI").split())

#: Connecticut's nine 2022 planning regions, county-equivalent FIPS -> name.
#: Verified against two independent artefacts on disk, see module docstring.
CT_PLANNING_REGIONS = {
    "09110": "CAPITOL PLANNING REGION",
    "09120": "GREATER BRIDGEPORT PLANNING REGION",
    "09130": "LOWER CONNECTICUT RIVER VALLEY PLANNING REGION",
    "09140": "NAUGATUCK VALLEY PLANNING REGION",
    "09150": "NORTHEASTERN CONNECTICUT PLANNING REGION",
    "09160": "NORTHWEST HILLS PLANNING REGION",
    "09170": "SOUTH CENTRAL CONNECTICUT PLANNING REGION",
    "09180": "SOUTHEASTERN CONNECTICUT PLANNING REGION",
    "09190": "WESTERN CONNECTICUT PLANNING REGION",
}

CT_STATE_FIPS = "09"


def fips_state_sql() -> str:
    """The FIPS map as an inline VALUES list, so the lookup stays in SQL."""
    rows = ", ".join(f"('{k}','{v}')" for k, v in FIPS_STATE.items())
    return f"(VALUES {rows}) AS fips(state_fips, state_abbr)"


def _region_from_name(name) -> str | None:
    """Match a CBP county_name to a planning-region FIPS.

    CBP truncates the name to 30 characters and upper-cases it, so
    "NORTHWEST HILLS PLANNING REGIO" has to resolve to 09160. A prefix match
    is used rather than equality, and it is unambiguous: no two of the nine
    names share a 30-character prefix.
    """
    # A ZCTA with no CBP row arrives as NaN, not as "". Testing for a string
    # first is what keeps the modal fallback below reachable.
    if not isinstance(name, str):
        return None
    key = name.strip().upper()
    if not key:
        return None
    hits = [fips for fips, full in CT_PLANNING_REGIONS.items()
            if full.startswith(key)]
    return hits[0] if len(hits) == 1 else None


def ct_zcta_regions(zcta_county: pd.DataFrame,
                    cbp: pd.DataFrame) -> pd.DataFrame:
    """ZCTA -> 2022 planning-region FIPS, for Connecticut only.

    Returns ``zcta``, ``county_geoid_2022`` and ``region_source`` (``cbp`` for
    a ZIP CBP places directly, ``modal`` for one inferred from its legacy
    county). Empty for a crosswalk with no Connecticut rows, so this is safe
    to call on any fixture.
    """
    legacy = zcta_county.loc[
        zcta_county["county_geoid"].astype(str).str.startswith(CT_STATE_FIPS),
        ["zcta", "county_geoid"]].copy()
    if legacy.empty:
        return pd.DataFrame(columns=["zcta", "county_geoid_2022",
                                     "region_source"])

    names = cbp[["zcta", "county_name"]] if "county_name" in cbp.columns \
        else pd.DataFrame(columns=["zcta", "county_name"])
    merged = legacy.merge(names, on="zcta", how="left")
    merged["county_geoid_2022"] = merged["county_name"].map(_region_from_name)
    merged["region_source"] = merged["county_geoid_2022"].notna().map(
        {True: "cbp", False: "modal"})

    # Modal fallback, computed from the ZIPs CBP does place rather than
    # asserted. Ties are impossible in the delivered data (the smallest
    # majority is 28 of 38 in Litchfield) but `mode()` is order-stable, so a
    # tie would resolve to the lowest FIPS and stay reproducible.
    placed = merged.dropna(subset=["county_geoid_2022"])
    modal = (placed.groupby("county_geoid")["county_geoid_2022"]
             .agg(lambda s: s.mode().iloc[0]) if len(placed) else pd.Series(
                 dtype=object))
    fallback = merged["county_geoid"].map(modal)
    merged["county_geoid_2022"] = merged["county_geoid_2022"].fillna(fallback)

    unresolved = int(merged["county_geoid_2022"].isna().sum())
    if unresolved:
        _log.warning("%d Connecticut ZCTA(s) could not be placed in a 2022 "
                     "planning region; they keep their legacy county code and "
                     "will still miss every county-grain 2022 source",
                     unresolved)
    out = merged.dropna(subset=["county_geoid_2022"])
    _log.info("Connecticut vintage bridge: %d ZCTA(s) remapped to planning "
              "regions (%d from CBP, %d modal by legacy county)", len(out),
              int((out["region_source"] == "cbp").sum()),
              int((out["region_source"] == "modal").sum()))
    return out[["zcta", "county_geoid_2022", "region_source"]].reset_index(
        drop=True)


def zcta_cbsa_titles(zcta_county: pd.DataFrame, cbsa_county: pd.DataFrame,
                     cbp: pd.DataFrame) -> pd.Series:
    """ZCTA -> CBSA title, indexed by ZCTA, NaN outside any metro or micro.

    A ZCTA can straddle a county line, so the county holding the largest
    share of its LAND AREA wins. Population would be the better weight and
    the relationship file does not carry it; land area is what is on disk and
    the choice is recorded rather than left to be inferred from the sort.

    The Connecticut bridge runs first and is not optional. Without it every
    Connecticut ZCTA joins nothing and comes back unplaced, which reads as
    "not in a metro" -- a silent wrong answer rather than a missing one.
    """
    bridged = zcta_county.merge(ct_zcta_regions(zcta_county, cbp),
                                on="zcta", how="left")
    bridged["county_geoid"] = bridged["county_geoid_2022"].fillna(
        bridged["county_geoid"])
    return (bridged.sort_values("shared_land_area", ascending=False)
            .drop_duplicates("zcta")
            .merge(cbsa_county[["county_geoid", "cbsa_title"]],
                   on="county_geoid", how="left")
            .set_index("zcta")["cbsa_title"])
