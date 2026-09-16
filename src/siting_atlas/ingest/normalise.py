"""L1 — turn raw downloads into one typed parquet per source.

Everything downstream reads parquet, never a raw file. This layer is where
publisher quirks are absorbed so no model has to know about them:

  * ZIP and ZCTA codes stay zero-padded strings, always. As integers `01890`
    becomes `1890` and every join silently loses those rows.
  * Wide month-per-column files become long (key, month, value).
  * Merged multi-row headers, BOMs and sentinel values are handled here.

    python -m siting_atlas.ingest.normalise            # everything present
    python -m siting_atlas.ingest.normalise --only cbp zillow_zori
"""

from __future__ import annotations

import argparse
import io

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .normalise_geo import cbsa_county, zcta_county
from .shapes import _latest, _member, _zpad

_log = get_logger("normalise")


def gazetteer() -> pd.DataFrame:
    """ZCTA centroid and land area — the geometry the cost model needs."""
    src = _latest(paths.RAW / "gaz_zcta", "*.zip")
    if src is None:
        raise FileNotFoundError("gazetteer not acquired; run ingest.acquire")

    raw = _member(src, ".txt")
    frame = pd.read_csv(io.BytesIO(raw), sep="\t", dtype={"GEOID": str},
                        encoding="latin-1")
    frame.columns = [c.strip() for c in frame.columns]
    frame = frame.rename(columns={
        "GEOID": "zcta", "ALAND_SQMI": "land_area_sqmi",
        "AWATER_SQMI": "water_area_sqmi",
        "INTPTLAT": "latitude", "INTPTLONG": "longitude"})
    frame["zcta"] = _zpad(frame["zcta"])
    keep = ["zcta", "land_area_sqmi", "water_area_sqmi", "latitude",
            "longitude"]
    frame = frame[[c for c in keep if c in frame.columns]]
    for col in ("land_area_sqmi", "water_area_sqmi", "latitude", "longitude"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def cbp() -> pd.DataFrame:
    """County Business Patterns: establishment counts per ZIP.

    ``est`` is the retail-density signal — the administrative alternative to
    a self-selected business directory.
    """
    src = _latest(paths.RAW / "cbp_zip", "*.zip")
    if src is None:
        raise FileNotFoundError("CBP not acquired; run ingest.acquire")

    raw = _member(src, ".txt")
    frame = pd.read_csv(io.BytesIO(raw), dtype={"zip": str},
                        encoding="latin-1")
    frame = frame.rename(columns={
        "zip": "zcta", "est": "establishments", "emp": "employment",
        "ap": "annual_payroll", "stabbr": "state",
        "cty_name": "county_name"})
    frame["zcta"] = _zpad(frame["zcta"])
    keep = ["zcta", "establishments", "employment", "annual_payroll",
            "state", "county_name"]
    frame = frame[[c for c in keep if c in frame.columns]]
    for col in ("establishments", "employment", "annual_payroll"):
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def building_permits() -> pd.DataFrame:
    """Building Permits Survey, county annual — the forward-looking signal.

    The publisher uses two merged header rows followed by a blank line, so
    column names are assigned positionally rather than parsed.
    """
    folder = paths.RAW / "bps_county"
    files = sorted(folder.glob("*.txt"))
    if not files:
        raise FileNotFoundError("permits not acquired; run ingest.acquire")

    names = ["yyyymm", "state_fips", "county_fips", "region", "division",
             "county_name",
             "u1_bldgs", "u1_units", "u1_value",
             "u2_bldgs", "u2_units", "u2_value",
             "u34_bldgs", "u34_units", "u34_value",
             "u5p_bldgs", "u5p_units", "u5p_value"]
    # One file per year. Concatenating them is what makes a year-over-year
    # feature possible at all; a single vintage yields an all-null column.
    parts = [pd.read_csv(f, skiprows=3, header=None, usecols=range(18),
                         names=names, dtype={"state_fips": str,
                                             "county_fips": str},
                         encoding="latin-1", skip_blank_lines=True)
             for f in files]
    frame = pd.concat(parts, ignore_index=True)
    frame = frame[frame["yyyymm"].notna()]
    frame["state_fips"] = _zpad(frame["state_fips"], 2)
    frame["county_fips"] = _zpad(frame["county_fips"], 3)
    frame["county_geoid"] = frame["state_fips"] + frame["county_fips"]
    frame["year"] = pd.to_numeric(frame["yyyymm"], errors="coerce") // 100

    unit_cols = [c for c in frame.columns if c.endswith("_units")]
    for col in unit_cols:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
    frame["permit_units_total"] = frame[unit_cols].sum(axis=1)
    frame["county_name"] = frame["county_name"].astype(str).str.strip()

    out = frame[["county_geoid", "county_name", "year",
                 "permit_units_total", "u1_units", "u5p_units"]]
    # A county can appear once per vintage file; keep one row per county-year.
    return out.drop_duplicates(["county_geoid", "year"], keep="last")


def zillow_zori() -> pd.DataFrame:
    """Zillow rent index: wide month-per-column to long (zcta, month, rent)."""
    src = _latest(paths.EXTERNAL / "zillow_zori", "*.csv", "*.txt")
    if src is None:
        raise FileNotFoundError(
            "ZORI not placed; see docs/data/ACQUISITION_GUIDE.md section 3")

    frame = pd.read_csv(src, dtype={"RegionName": str})
    month_cols = [c for c in frame.columns if c[:4].isdigit()]
    meta = frame[["RegionName", "Metro", "CountyName", "State"]].copy()
    meta.columns = ["zcta", "metro", "county_name", "state"]
    meta["zcta"] = _zpad(meta["zcta"])

    long = frame.melt(id_vars=["RegionName"], value_vars=month_cols,
                      var_name="month", value_name="rent_index")
    long["zcta"] = _zpad(long["RegionName"])
    long["month"] = pd.to_datetime(long["month"])
    long["year"] = long["month"].dt.year
    long = long.drop(columns=["RegionName"]).dropna(subset=["rent_index"])
    return long.merge(meta, on="zcta", how="left")


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
NORMALISERS = {
    "gazetteer": (gazetteer, "zcta"),
    "cbp": (cbp, "zcta"),
    "building_permits": (building_permits, "county_geoid"),
    "zcta_county": (zcta_county, "zcta"),
    "cbsa_county": (cbsa_county, "county_geoid"),
    "zillow_zori": (zillow_zori, "zcta"),
}


def run(only: list[str] | None = None) -> list[dict]:
    """Normalise every requested source, writing one parquet each.

    A source whose raw file has not been acquired is SKIPPED with a warning
    rather than raising, so one absent download does not cost the other ten
    conversions. Anything else — a shape change, a bad encoding — is left to
    propagate, because that is a defect and not a missing input.
    """
    targets = only or list(NORMALISERS)
    results: list[dict] = []

    with traced_layer("L1", f"normalise {len(targets)} source(s)"):
        for name in targets:
            fn, key = NORMALISERS[name]
            with step(f"normalise:{name}"):
                try:
                    frame = fn()
                except FileNotFoundError as exc:
                    _log.warning("%-18s SKIP  %s", name, exc)
                    results.append({"source": name, "status": "skipped",
                                    "reason": str(exc)})
                    continue

                out = paths.INTERIM / f"{name}.parquet"
                frame.to_parquet(out, index=False)
                artefact(out, rows=len(frame), cols=len(frame.columns))
                metric(f"{name}_rows", len(frame))
                _log.info("%-18s %7d rows x %2d cols | %s unique %s",
                          name, len(frame), len(frame.columns),
                          f"{frame[key].nunique():,}" if key in frame else "-",
                          key)
                results.append({"source": name, "status": "ok",
                                "rows": len(frame),
                                "cols": list(frame.columns),
                                "path": paths.rel(out)})
    return results


def main() -> int:
    """CLI entry point for L1. Writes a report to outputs/metrics/."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", choices=sorted(NORMALISERS))
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    results = run(args.only)
    write_json(paths.METRICS / "normalise_report.json", {"results": results})

    ok = [r for r in results if r["status"] == "ok"]
    print(f"\n  {len(ok)}/{len(results)} normalised -> "
          f"{paths.rel(paths.INTERIM)}")
    for r in ok:
        print(f"    {r['source']:20} {r['rows']:>9,} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
