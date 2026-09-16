"""L1 geography: the crosswalks that let every other source find a ZCTA.

Separated from the attribute sources because these two decide the SHAPE of
the panel rather than its contents, and because both carry a judgement that
is easy to make silently and wrongly — which county a ZCTA belongs to when it
spans several, and which delineation vintage defines a metro.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from .shapes import _latest, _zpad


def zcta_county() -> pd.DataFrame:
    """ZCTA-to-county relationship, with the intersection land area.

    A ZCTA can span several counties. Carrying the shared area lets the join
    be area-weighted instead of assigning each ZCTA to one county
    arbitrarily.
    """
    src = _latest(paths.RAW / "zcta_county_xwalk", "*.txt")
    if src is None:
        raise FileNotFoundError("crosswalk not acquired; run ingest.acquire")

    frame = pd.read_csv(src, sep="|", dtype=str, encoding="utf-8-sig")
    frame.columns = [c.strip() for c in frame.columns]
    zcta_col = next(c for c in frame.columns if c.startswith("GEOID_ZCTA5"))
    cty_col = next(c for c in frame.columns if c.startswith("GEOID_COUNTY"))
    area_col = next((c for c in frame.columns
                     if c.startswith("AREALAND_PART")), None)

    out = pd.DataFrame({
        "zcta": _zpad(frame[zcta_col].fillna("")),
        "county_geoid": _zpad(frame[cty_col].fillna(""), 5),
        "shared_land_area": pd.to_numeric(frame[area_col], errors="coerce")
        if area_col else 1.0,
    })
    # Rows with no ZCTA are county records with no ZCTA intersection.
    out = out[(out.zcta != "00000") & (out.county_geoid != "00000")]
    out = out[out.zcta.str.len() == 5]

    # Keep the dominant county per ZCTA: the one sharing the most land.
    out = (out.sort_values("shared_land_area", ascending=False)
              .drop_duplicates("zcta", keep="first")
              .reset_index(drop=True))
    return out


def cbsa_county() -> pd.DataFrame:
    """OMB delineation: which counties constitute each metro area.

    This is what decides pilot membership. The alternative - taking whichever
    ZCTAs appear in the Zillow rent index - drops 35% of pilot-metro ZCTAs and
    selects for density, which is selection on a correlate of the outcome.
    """
    src = _latest(paths.RAW / "cbsa_county", "*.xlsx", "*.xls")
    if src is None:
        raise FileNotFoundError("delineation not acquired; run ingest.acquire")

    # Two title rows precede the header, and a footnote block follows the data.
    frame = pd.read_excel(src, dtype=str, header=2)
    frame = frame.rename(columns={
        "CBSA Code": "cbsa_code", "CBSA Title": "cbsa_title",
        "CSA Title": "csa_title",
        "Metropolitan/Micropolitan Statistical Area": "area_type",
        "FIPS State Code": "state_fips", "FIPS County Code": "county_fips",
        "County/County Equivalent": "county_name",
        "Central/Outlying County": "county_role"})
    frame = frame.dropna(subset=["cbsa_code", "state_fips", "county_fips"])

    frame["county_geoid"] = (_zpad(frame["state_fips"], 2)
                             + _zpad(frame["county_fips"], 3))
    frame["is_metro"] = (frame["area_type"].str.startswith("Metro")
                         .fillna(False))
    keep = ["county_geoid", "county_name", "cbsa_code", "cbsa_title",
            "csa_title", "area_type", "is_metro", "county_role"]
    return frame[keep].reset_index(drop=True)
