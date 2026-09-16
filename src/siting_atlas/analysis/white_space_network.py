"""The facility network a coverage map is drawn from, and what it costs.

Three sources, joined here and nowhere else:

1. **Delivery stations** — ``national_facilities_expanded.csv`` (700 rows,
   all typed ``DS``) with coordinates from ``geocoded_expanded.csv``. 455 of
   those coordinates are real street geocodes from the Census batch geocoder;
   240 more are the ZCTA centroid behind an explicit ``fallback_method``
   flag; 5 have neither.

2. **Support sites** — the non-delivery-station US tables of
   ``data/interim/mwpvl_facilities.csv``: fulfilment, sortation, cross-dock,
   air gateway, fresh, heavy-and-bulky. 811 US rows. A metro served by a
   million-square-foot fulfilment centre is not unserved, so leaving these
   out would manufacture white space. **They have no real coordinates at
   all** — every one is placed at its postcode's ZCTA centroid — so the
   "real coordinates only" arm is real on the delivery-station side and
   centroid on this side. That is stated rather than averaged away.

3. **The ZCTA universe** — ``data/processed/panel.parquet``, one row per
   ZCTA, 33,791 of them, carrying households, population, state and CBSA.

Why the coordinate split is not a formality
-------------------------------------------
The 65% geocoder match rate is **not missing at random**. Hand-collected rows
matched 83.7%; OCR'd MWPVL rows matched 61.7%. A geocoder fails on a bad
address string, and bad address strings cluster in the places the source
documented badly, which are not a random sample of places. So a coverage map
built from real coordinates alone is a map of the well-documented metros.
Every figure this package reports is therefore reported twice, once per
:data:`COORD_SETS` arm, and the two arms are never combined into one number.

Rest-of-world rows (MWPVL tables ``10_row`` and ``11_row``, 458 of them) are
dropped by name rather than left to fall out of the postcode join, because
"it happened not to match" is not a reason a reader can check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger

__all__ = ["COORD_SETS", "REAL", "REAL_PLUS_FALLBACK", "delivery_stations",
           "network", "support_sites", "zcta_universe"]

_log = get_logger("analysis.white_space")

PANEL_DIR = paths.EXTERNAL / "facility_panel"
DS_FRAME = PANEL_DIR / "national_facilities_expanded.csv"
GEOCODED = PANEL_DIR / "geocoded_expanded.csv"
MWPVL = paths.INTERIM / "mwpvl_facilities.csv"
CBSA_COUNTY = paths.INTERIM / "cbsa_county.parquet"

#: Census-geocoder matches only. The conservative arm: fewer facilities, so
#: MORE white space, and the white space it finds cannot be an artefact of a
#: centroid sitting a few miles from the real door.
REAL = "real"

#: Census matches plus ZCTA-centroid fallbacks. The complete arm: every
#: facility we know about is on the map, at the cost of up to a few miles of
#: placement error on 240 of them.
REAL_PLUS_FALLBACK = "real_plus_fallback"

COORD_SETS = (REAL, REAL_PLUS_FALLBACK)

#: MWPVL tables that are not in the United States.
_ROW_PREFIXES = ("10_row", "11_row")

#: MWPVL tables that ARE small-package delivery stations. Excluded from the
#: support network because ``national_facilities_expanded.csv`` already
#: carries them (596 of its 700 rows are ``source_dataset = mwpvl_2025q1``)
#: and counting a building twice would not change a union of discs, but
#: would corrupt every facility COUNT reported beside it.
_DS_PREFIXES = ("08_us_delivery_station",)

#: A row MWPVL marks cancelled, or marks closed, is not serving anyone.
#: ``not_confirmed`` and ``delayed`` are KEPT: both describe a building
#: MWPVL believes exists, and dropping them would be a judgement about
#: MWPVL's confidence rather than about the world.
_DEAD_FLAGS = ("cancelled", "closed")


def zcta_universe() -> pd.DataFrame:
    """One row per ZCTA: centroid, households, population, place labels.

    Read from the delivered panel rather than the gazetteer so that the
    denominator here is the same denominator every other stage uses.
    ``households`` is NULL for 19 ZCTAs and is filled with 0 — those are
    ZCTAs the ACS suppressed, and a suppressed count contributes no
    measurable demand, so it cannot raise a place up the ranking.
    """
    cols = ["zcta", "households", "population", "state", "county_geoid",
            "cbsa_code", "cbsa_title", "latitude", "longitude"]
    panel = pd.read_parquet(paths.PANEL, columns=cols)
    z = panel.drop_duplicates("zcta").reset_index(drop=True)
    z["households"] = z["households"].fillna(0.0)
    z["population"] = z["population"].fillna(0.0)
    if CBSA_COUNTY.exists():
        names = (pd.read_parquet(CBSA_COUNTY)
                 .drop_duplicates("county_geoid")
                 .set_index("county_geoid")["county_name"])
        z["county_name"] = z["county_geoid"].map(names)
    else:
        z["county_name"] = pd.NA
    _log.info("ZCTA universe: %d areas, %.1fM households, %.1fM people",
              len(z), z["households"].sum() / 1e6,
              z["population"].sum() / 1e6)
    return z


def delivery_stations(coords: str) -> pd.DataFrame:
    """The 700-row DS frame with one coordinate pair per row, or none.

    ``coords`` is :data:`REAL` or :data:`REAL_PLUS_FALLBACK`. Rows with no
    coordinate under the chosen arm are DROPPED rather than placed somewhere
    plausible. Returns ``facility_id``, ``zcta``, ``open_year``,
    ``latitude``, ``longitude``, ``coord_source``.
    """
    if coords not in COORD_SETS:
        raise ValueError(f"coords must be one of {COORD_SETS}, got {coords!r}")
    frame = pd.read_csv(DS_FRAME, dtype=str, encoding="utf-8-sig")
    geo = pd.read_csv(GEOCODED, dtype=str, encoding="utf-8-sig")
    keep = ["facility_id", "latitude", "longitude", "fallback_latitude",
            "fallback_longitude"]
    out = frame[["facility_id", "zcta", "state", "open_year"]].merge(
        geo[keep], on="facility_id", how="left")
    for col in keep[1:] + ["open_year"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["coord_source"] = np.where(out["latitude"].notna(), "census_geocode",
                                   np.where(out["fallback_latitude"].notna(),
                                            "zcta_centroid", "none"))
    if coords == REAL_PLUS_FALLBACK:
        out["latitude"] = out["latitude"].fillna(out["fallback_latitude"])
        out["longitude"] = out["longitude"].fillna(out["fallback_longitude"])
    placed = out[out["latitude"].notna() & out["longitude"].notna()].copy()
    _log.info("delivery stations (%s): %d of %d placed", coords, len(placed),
              len(out))
    return placed[["facility_id", "zcta", "state", "open_year", "latitude",
                   "longitude", "coord_source"]]


def support_sites(zctas: pd.DataFrame | None = None) -> pd.DataFrame:
    """US non-delivery-station Amazon sites, at their ZCTA centroid.

    One coordinate arm only, for the reason in the module docstring: MWPVL
    publishes a street address as OCR'd text and nothing in this repo has
    geocoded it, so there is no "real" version of this frame to report.

    ``zctas`` is :func:`zcta_universe` if the caller already has it; passing
    it avoids re-reading the 1.08M-row panel once per network.
    """
    zc = (zcta_universe() if zctas is None
          else zctas).set_index("zcta")[["latitude", "longitude"]]
    mw = pd.read_csv(MWPVL, dtype=str, encoding="utf-8-sig")
    us = mw[~mw["table"].str.startswith(_ROW_PREFIXES)]
    non_ds = us[~us["table"].str.startswith(_DS_PREFIXES)].copy()
    for flag in _DEAD_FLAGS:
        non_ds = non_ds[non_ds[flag].fillna("False") != "True"]
    non_ds["zcta"] = non_ds["postcode"].fillna("").str.strip().str[:5]
    non_ds["zcta"] = non_ds["zcta"].str.zfill(5)
    non_ds["open_year"] = pd.to_numeric(non_ds["open_year"], errors="coerce")
    placed = non_ds.join(zc, on="zcta")
    unmatched = int(placed["latitude"].isna().sum())
    placed = placed[placed["latitude"].notna()].copy()
    placed["facility_id"] = ("MWPVL-" + placed["table"] + "-"
                             + placed["row"].astype(str))
    placed["coord_source"] = "zcta_centroid"
    _log.info("support sites: %d US non-DS rows placed, %d postcodes not a "
              "ZCTA", len(placed), unmatched)
    return placed[["facility_id", "zcta", "open_year", "latitude",
                   "longitude", "coord_source", "table"]]


def network(coords: str, support: bool = True,
            opened_by: int | None = None,
            zctas: pd.DataFrame | None = None
            ) -> tuple[pd.DataFrame, dict]:
    """Assemble one service network and say exactly what went into it.

    ``opened_by`` is the LEAKAGE CONTROL. When it is set, only facilities
    with a stated ``open_year`` at or before that year enter the network, and
    every undated row is dropped — an undated MWPVL building could have
    opened in 2025, and letting one into a network used to score 2025
    openings is the failure ``docs/research/NOTES_COVARIATE_LEAKAGE.md``
    documents. When it is ``None`` every placed facility enters, dated or
    not, because the question is what is served today.
    """
    ds = delivery_stations(coords).assign(kind="delivery_station")
    parts = [ds]
    if support:
        parts.append(support_sites(zctas).assign(kind="support"))
    net = pd.concat(parts, ignore_index=True)

    dropped_undated = 0
    if opened_by is not None:
        before = len(net)
        net = net[net["open_year"].notna() & (net["open_year"] <= opened_by)]
        dropped_undated = before - len(net)
    prov = {
        "coord_set": coords,
        "includes_support_sites": support,
        "opened_by_year": opened_by,
        "facilities": len(net),
        "delivery_stations": int((net["kind"] == "delivery_station").sum()),
        "support_sites": int((net["kind"] == "support").sum()),
        "real_coordinates": int((net["coord_source"]
                                 == "census_geocode").sum()),
        "zcta_centroid_coordinates": int((net["coord_source"]
                                          == "zcta_centroid").sum()),
        "dropped_as_undated_or_too_late": int(dropped_undated),
    }
    _log.info("network(%s, support=%s, opened_by=%s): %d facilities",
              coords, support, opened_by, len(net))
    return net.reset_index(drop=True), prov
