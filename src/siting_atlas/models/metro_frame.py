"""The CBSA x year frame the prereg fixes in section 3.

Universe is every CBSA in `panel.parquet` -- 935 of them -- not the 195 that
received a facility. Section 8.2 names restricting it as an invalidating
condition, so the 740 that never received one are carried as rows with a
zero outcome and are the comparison group.

Three things this file is careful about
---------------------------------------
**Grain.** The ZCTA panel mixes three grains under one schema. Summing a
county figure over the ZCTAs of a county multiplies it by the number of
ZCTAs; summing a metro figure over its ZCTAs multiplies it by hundreds.
Measured on the panel: `permit_units_total` has exactly 1 distinct value per
(county, year) and `metro_employment` exactly 1 per CBSA, so each is
de-duplicated to its own grain before it is combined.

**Lag.** Every genuinely time-varying covariate is carried at lag 1 -- the
row for year t holds the year t-1 observation. That is what makes the
vintage gate in `metro_vintage` pass by construction rather than by
assertion, and it costs the first year of the window.

**Missingness.** Nothing here is imputed or corrected. A metro with no
building-permit county keeps a NaN, and how an unscorable row is handled is
a decision made once, visibly, at prediction time -- not silently here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger

_log = get_logger("models.metro_frame")

__all__ = ["WINDOW", "build_frame", "TIER1", "TIER2", "TIER3", "PREREG_COLS"]

#: Prereg section 3: "unit CBSA x year, window 2018-2025".
WINDOW = (2018, 2025)

TIER1 = ("permit_units_total", "permits_yoy_pct", "wage_freight_handler",
         "wage_all_occupations", "metro_employment", "traffic_proximity",
         "diesel_pm")
TIER2 = ("households", "population", "median_household_income")
TIER3 = ("facilities_open_prior", "dist_nearest_outside_prior")
PREREG_COLS = TIER1 + TIER2 + TIER3

_FACILITIES = (paths.EXTERNAL / "facility_panel"
               / "national_facilities_expanded.csv")
_GEOCODED = paths.EXTERNAL / "facility_panel" / "geocoded_expanded.csv"

_EARTH_MI = 3958.7613


def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle miles between two arrays of degree coordinates."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * _EARTH_MI * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _zcta_level(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per ZCTA: the columns the panel repeats 32 times each."""
    cols = ["zcta", "cbsa_code", "county_geoid", "latitude", "longitude",
            "population", "households", "median_household_income",
            "traffic_proximity", "diesel_pm"]
    z = panel[cols].drop_duplicates("zcta")
    return z[z["cbsa_code"].notna()].copy()


def _metro_static(z: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the ZCTA-grain, single-vintage columns to CBSA."""
    g = z.groupby("cbsa_code")
    out = pd.DataFrame({
        "households": g["households"].sum(min_count=1),
        "population": g["population"].sum(min_count=1),
    })
    # Income is a rate, so it is weighted by the households it describes.
    # An unweighted mean would let a 400-household ZCTA move a metro as far
    # as a 40,000-household one.
    def _wmean(frame, value, weight):
        v = frame[value].to_numpy(float)
        w = frame[weight].to_numpy(float)
        m = np.isfinite(v) & np.isfinite(w) & (w > 0)
        return float(np.average(v[m], weights=w[m])) if m.any() else np.nan

    out["median_household_income"] = g.apply(
        _wmean, "median_household_income", "households", include_groups=False)
    for col in ("traffic_proximity", "diesel_pm"):
        out[col] = g.apply(_wmean, col, "population", include_groups=False)
    return out.reset_index()


def _metro_cbsa_grain(panel: pd.DataFrame) -> pd.DataFrame:
    """The columns already published at metro grain, de-duplicated."""
    cols = ["cbsa_code", "metro_employment", "wage_all_occupations",
            "wage_freight_handler"]
    m = panel[cols].dropna(subset=["cbsa_code"]).drop_duplicates("cbsa_code")
    return m.reset_index(drop=True)


def _metro_permits(panel: pd.DataFrame) -> pd.DataFrame:
    """County building permits, summed to CBSA, one row per metro-year.

    Read from the L1 source rather than from the panel for one reason: the
    panel's window starts in 2018, and a lag-1 covariate for 2018 needs the
    2017 file, which the source has and the panel does not. The county key
    matches on 3,011 of the source's 3,043 counties.

    De-duplicated to (county, year) first. The panel repeats each county
    figure once per ZCTA per quarter, so a sum taken over panel rows would
    inflate a metro's permits by roughly 4 x (ZCTAs per county).
    """
    xwalk = (panel[["county_geoid", "cbsa_code"]]
             .dropna().drop_duplicates("county_geoid"))
    bps = pd.read_parquet(paths.INTERIM / "building_permits.parquet")
    bps = bps[["county_geoid", "year", "permit_units_total"]]
    bps = bps.drop_duplicates(["county_geoid", "year"])
    c = bps.merge(xwalk, on="county_geoid", how="inner")
    out = (c.groupby(["cbsa_code", "year"])["permit_units_total"]
           .sum(min_count=1).reset_index())
    # yoy is recomputed from the metro totals rather than averaged from the
    # county rates: a mean of ratios is not the ratio of the sums, and the
    # metro figure is the one the model uses.
    out = out.sort_values(["cbsa_code", "year"])
    prev = out.groupby("cbsa_code")["permit_units_total"].shift(1)
    out["permits_yoy_pct"] = np.where(
        (prev > 0) & prev.notna(),
        100.0 * (out["permit_units_total"] - prev) / prev, np.nan)
    return out


def _centroids(z: pd.DataFrame) -> pd.DataFrame:
    """Population-weighted centroid of each metro, from its ZCTAs."""
    rows = []
    for code, grp in z.groupby("cbsa_code"):
        w = grp["population"].to_numpy(float)
        la = grp["latitude"].to_numpy(float)
        lo = grp["longitude"].to_numpy(float)
        m = np.isfinite(w) & np.isfinite(la) & np.isfinite(lo) & (w > 0)
        if not m.any():
            m = np.isfinite(la) & np.isfinite(lo)
            w = np.ones_like(la)
        if not m.any():
            rows.append((code, np.nan, np.nan))
            continue
        rows.append((code, float(np.average(la[m], weights=w[m])),
                     float(np.average(lo[m], weights=w[m]))))
    return pd.DataFrame(rows, columns=["cbsa_code", "lat", "lon"])


def load_events() -> tuple[pd.DataFrame, dict]:
    """Dated, located delivery-station openings, plus the exclusion counts.

    Prereg section 3: a facility with no numeric opening year cannot
    contribute an event and is excluded from the event set but not from the
    universe, and the count is reported. The same logic is applied, and
    recorded as a deviation, to a facility with no CBSA code: it cannot be
    assigned to a metro, so it cannot switch one on.
    """
    f = pd.read_csv(_FACILITIES, dtype=str, low_memory=False)
    oy = pd.to_numeric(f["open_year"], errors="coerce")
    prov = {
        "facility_rows": int(len(f)),
        "undated": int(oy.isna().sum()),
        "dated": int(oy.notna().sum()),
        "dated_without_cbsa": int((oy.notna() & f["cbsa_code"].isna()).sum()),
    }
    ev = f[oy.notna() & f["cbsa_code"].notna()].copy()
    ev["open_year"] = oy[ev.index].astype(int)
    g = pd.read_csv(_GEOCODED, dtype=str, low_memory=False)
    lat = pd.to_numeric(g["latitude"], errors="coerce")
    lon = pd.to_numeric(g["longitude"], errors="coerce")
    flat = pd.to_numeric(g["fallback_latitude"], errors="coerce")
    flon = pd.to_numeric(g["fallback_longitude"], errors="coerce")
    g = pd.DataFrame({"facility_id": g["facility_id"],
                      "fac_lat": lat.fillna(flat),
                      "fac_lon": lon.fillna(flon),
                      "coord_exact": lat.notna()})
    ev = ev.merge(g, on="facility_id", how="left")
    prov["dated_located"] = int(len(ev))
    prov["dated_located_with_coord"] = int(ev["fac_lat"].notna().sum())
    prov["coord_exact_match"] = int(ev["coord_exact"].fillna(False).sum())
    prov["cbsa_with_any_event"] = int(ev["cbsa_code"].nunique())
    return ev[["facility_id", "cbsa_code", "open_year",
               "fac_lat", "fac_lon"]], prov


def _network_features(ev: pd.DataFrame, cent: pd.DataFrame,
                      years: list[int]) -> pd.DataFrame:
    """Tier 3, strictly as of the end of year t-1."""
    cen = cent.dropna(subset=["lat", "lon"])
    rows = []
    for t in years:
        prior = ev[ev["open_year"] <= t - 1]
        counts = prior.groupby("cbsa_code").size()
        pl = prior.dropna(subset=["fac_lat", "fac_lon"])
        for code, la, lo in cen.itertuples(index=False):
            out = pl[pl["cbsa_code"] != code]
            d = (float(_haversine(la, lo, out["fac_lat"].to_numpy(float),
                                  out["fac_lon"].to_numpy(float)).min())
                 if len(out) else np.nan)
            rows.append((code, t, int(counts.get(code, 0)), d))
    return pd.DataFrame(rows, columns=[
        "cbsa_code", "year", "facilities_open_prior",
        "dist_nearest_outside_prior"])


def build_frame(panel_path=None) -> tuple[pd.DataFrame, dict]:
    """The full CBSA x year design, the outcome, and the provenance block."""
    panel = pd.read_parquet(panel_path or paths.PANEL)
    lo, hi = WINDOW
    years = list(range(lo, hi + 1))

    z = _zcta_level(panel)
    static = _metro_static(z)
    cbsa_grain = _metro_cbsa_grain(panel)
    permits = _metro_permits(panel)
    cent = _centroids(z)

    universe = pd.DataFrame(
        [(c, y) for c in sorted(static["cbsa_code"]) for y in years],
        columns=["cbsa_code", "year"])

    ev, prov = load_events()
    ev = ev[ev["cbsa_code"].isin(set(universe["cbsa_code"]))]
    win = ev[(ev["open_year"] >= lo) & (ev["open_year"] <= hi)]
    counts = (win.groupby(["cbsa_code", "open_year"]).size()
              .rename("events").reset_index()
              .rename(columns={"open_year": "year"}))

    fr = universe.merge(counts, on=["cbsa_code", "year"], how="left")
    fr["events"] = fr["events"].fillna(0).astype(int)
    fr["any_event"] = (fr["events"] > 0).astype(int)

    fr = fr.merge(static, on="cbsa_code", how="left")
    fr = fr.merge(cbsa_grain, on="cbsa_code", how="left")
    fr = fr.merge(_network_features(ev, cent, years),
                  on=["cbsa_code", "year"], how="left")

    # Lag 1 on the genuinely annual columns: the row for year t carries the
    # t-1 observation, so nothing on the row is known only at t or later.
    lagged = permits.copy()
    lagged["year"] = lagged["year"] + 1
    fr = fr.merge(lagged, on=["cbsa_code", "year"], how="left")

    prov.update({
        "panel": str(paths.rel(panel_path or paths.PANEL)),
        "panel_rows": int(len(panel)),
        "window": list(WINDOW),
        "metros": int(fr["cbsa_code"].nunique()),
        "metro_years": int(len(fr)),
        "events_in_window": int(fr["events"].sum()),
        "event_metro_years": int(fr["any_event"].sum()),
        "events_by_year": {int(k): int(v) for k, v in
                           fr.groupby("year")["events"].sum().items()},
        "event_metros_by_year": {int(k): int(v) for k, v in
                                 fr.groupby("year")["any_event"].sum().items()},
        "coverage_pct": {c: round(100.0 * fr[c].notna().mean(), 2)
                         for c in PREREG_COLS},
    })
    _log.info("metro frame: %d metro-years, %d events, %d event metro-years",
              len(fr), fr["events"].sum(), fr["any_event"].sum())
    return fr, prov
