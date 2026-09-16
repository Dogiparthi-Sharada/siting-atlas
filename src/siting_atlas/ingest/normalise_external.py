"""L1 — normalise the three large manually-placed sources.

These are separated from :mod:`siting_atlas.ingest.normalise` because none of
them can be fetched by the pipeline: a person downloads them and drops them
into ``data/external/``. They are also the three biggest files in the project
(118 MB CSV, 30 MB XLSX, 49 MB zipped CSV), so each one is trimmed *before*
it is reshaped rather than after:

  * ZHVI is cut to 2015-01 onward while still wide. Melting all 318 months
    would produce ~8M rows to then throw most of away; the ZORI series we
    already have starts at 2015-01, so anything earlier cannot be joined.
  * OES keeps four occupation codes out of ~830.
  * EJScreen reads 10 of 230 columns via ``usecols``.

    python -m siting_atlas.ingest.normalise_external
    python -m siting_atlas.ingest.normalise_external --only ejscreen_tract
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("normalise_external")

# ZHVI months before this cannot be joined to anything: ZORI starts here.
ZHVI_FROM = "2015-01-01"

# The occupations a distribution centre actually hires for, plus the
# all-occupations row as a denominator (is this metro expensive in general,
# or expensive for warehouse labour specifically?).
OES_OCCUPATIONS = {
    "53-3033": "light truck drivers",
    "53-7062": "labourers and material movers, hand",
    "53-1047": "first-line supervisors of transportation and material moving",
    "00-0000": "all occupations",
}

# EJScreen renamed TOTALPOP to ACSTOTPOP in the 2024 release. First name
# present in the header wins, so both vintages read.
EJ_COLUMNS: dict[str, tuple[str, ...]] = {
    "tract_geoid": ("ID",),
    "state_name": ("STATE_NAME",),
    "total_pop": ("TOTALPOP", "ACSTOTPOP"),
    "pm25": ("PM25",),
    "diesel_pm": ("DSLPM",),
    "traffic_proximity": ("PTRAF",),
    "low_income_pct": ("LOWINCPCT",),
    "people_of_colour_pct": ("PEOPCOLORPCT",),
    "demog_index_2": ("DEMOGIDX_2",),
    "demog_index_5": ("DEMOGIDX_5",),
}


# Deliberately a copy of normalise._zpad rather than an import. These two
# modules are run independently and neither should be able to break the
# other; one four-line function is a cheaper price than that coupling.
def _zpad(series: pd.Series, width: int = 5) -> pd.Series:
    """Zero-padded string codes. The single most important rule in L1."""
    return series.astype(str).str.strip().str.zfill(width)


def _require(path: Path, section: str) -> Path:
    """Existing file, or a FileNotFoundError that says what to go and get."""
    if not path.exists():
        raise FileNotFoundError(
            f"{paths.rel(path)} not placed; see "
            f"docs/data/ACQUISITION_GUIDE.md section {section}")
    return path


def _numeric_flagged(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Coerce a BLS wage column, reporting which cells were sentinels.

    Returns (values, was_sentinel). Blank cells are ordinary missing data and
    are NOT flagged — only an explicit sentinel is.
    """
    raw = series.astype(str).str.strip()
    values = pd.to_numeric(raw.str.replace(",", "", regex=False),
                           errors="coerce")
    # Test the ORIGINAL for nullness: astype(str) renders a missing cell as
    # 'nan' or '<NA>' depending on dtype, and either would read as a sentinel.
    flagged = values.isna() & series.notna() & raw.ne("")
    return values, flagged


# ---------------------------------------------------------------------------
# individual sources
# ---------------------------------------------------------------------------
def zillow_zhvi() -> pd.DataFrame:
    """Zillow home value index: wide month-per-column to long.

    ZHVI is the land-cost proxy. ZORI says what a tenant pays now; ZHVI says
    what the underlying property is worth, which is the part that shows up in
    a site's acquisition cost.
    """
    src = _require(
        paths.EXTERNAL / "zillow_zhvi"
        / "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv", "3")

    header = pd.read_csv(src, nrows=0)
    months = [c for c in header.columns
              if c[:4].isdigit() and c >= ZHVI_FROM]
    meta_cols = ["RegionName", "State", "Metro", "CountyName"]

    # usecols is the whole point: 9 metadata + 139 months instead of 328.
    frame = pd.read_csv(src, usecols=meta_cols + months,
                        dtype={"RegionName": str})

    meta = frame[meta_cols].copy()
    meta.columns = ["zcta", "state", "metro", "county_name"]
    meta["zcta"] = _zpad(meta["zcta"])

    long = frame.melt(id_vars=["RegionName"], value_vars=months,
                      var_name="month", value_name="home_value")
    long["zcta"] = _zpad(long["RegionName"])
    long["month"] = pd.to_datetime(long["month"])
    long["year"] = long["month"].dt.year
    long = long.drop(columns=["RegionName"]).dropna(subset=["home_value"])
    return long.merge(meta, on="zcta", how="left")


def bls_wages() -> pd.DataFrame:
    """OES metro wages for the occupations a warehouse actually staffs.

    Read from inside the zip: the xlsx is 30 MB and extracting it to disk
    would leave an untracked copy next to the immutable download.
    """
    src = _require(paths.EXTERNAL / "bls_oes" / "oesm25ma.zip", "5")
    with zipfile.ZipFile(src) as zf:
        member = next((n for n in zf.namelist()
                       if n.upper().endswith("MSA_M2025_DL.XLSX")), None)
        if member is None:
            raise FileNotFoundError(
                f"{paths.rel(src)} has no MSA_M2025_dl.xlsx member; see "
                "docs/data/ACQUISITION_GUIDE.md section 5")
        raw = zf.read(member)

    # Everything as text: the wage columns carry '*' and '#' sentinels and
    # pandas' own inference would silently decide the column is object anyway.
    frame = pd.read_excel(io.BytesIO(raw), dtype=str)
    frame["OCC_CODE"] = frame["OCC_CODE"].astype(str).str.strip()
    frame = frame[frame["OCC_CODE"].isin(OES_OCCUPATIONS)].copy()

    out = pd.DataFrame({
        "area_code": _zpad(frame["AREA"], 5),
        "area_title": frame["AREA_TITLE"].astype(str).str.strip(),
        "state": frame["PRIM_STATE"].astype(str).str.strip(),
        "occ_code": frame["OCC_CODE"],
        "occ_title": frame["OCC_TITLE"].astype(str).str.strip(),
    })
    out["total_employment"], _ = _numeric_flagged(frame["TOT_EMP"])

    median, median_flag = _numeric_flagged(frame["A_MEDIAN"])
    mean, mean_flag = _numeric_flagged(frame["A_MEAN"])
    out["annual_median_wage"] = median
    out["annual_mean_wage"] = mean
    # '*' means BLS withheld the estimate; '#' means it is top-coded at
    # >= $239,200/yr. Both land as NaN, so the flag is what stops a later
    # dropna from being read as "no data here" when it is really "very high".
    out["wage_suppressed"] = (median_flag | mean_flag).astype(bool)

    return out.sort_values(["area_code", "occ_code"]).reset_index(drop=True)


def ejscreen_tract() -> pd.DataFrame:
    """EJScreen tract indicators: the siting-friction / equity signal.

    230 columns of which we want 10. ``usecols`` keeps the 150 MB member from
    ever being fully materialised.
    """
    src = _require(
        paths.EXTERNAL / "ejscreen"
        / "EJScreen_2024_Tract_with_AS_CNMI_GU_VI.csv.zip", "4")

    with zipfile.ZipFile(src) as zf:
        member = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with zf.open(member) as fh:
            header = fh.readline().decode("utf-8-sig").strip().split(",")

    resolved: dict[str, str] = {}
    for out_name, candidates in EJ_COLUMNS.items():
        source = next((c for c in candidates if c in header), None)
        if source is None:
            raise KeyError(
                f"EJScreen file has none of {candidates} for '{out_name}'; "
                "the release layout changed, see docs/data/ejscreen.md")
        resolved[source] = out_name

    frame = pd.read_csv(src, compression="zip", usecols=list(resolved),
                        dtype={"ID": str}, encoding="utf-8-sig",
                        low_memory=False)
    frame = frame.rename(columns=resolved)

    # Tract GEOIDs are 11 digits; leading zeros are lost in any file where a
    # writer touched the column as a number.
    frame["tract_geoid"] = _zpad(frame["tract_geoid"], 11)
    frame["county_geoid"] = frame["tract_geoid"].str[:5]
    for col in frame.columns:
        if col not in ("tract_geoid", "county_geoid", "state_name"):
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame.reset_index(drop=True)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
NORMALISERS = {
    "zillow_zhvi": (zillow_zhvi, "zcta"),
    "bls_wages": (bls_wages, "area_code"),
    "ejscreen_tract": (ejscreen_tract, "tract_geoid"),
}


def run(only: list[str] | None = None) -> list[dict]:
    """Normalise the manually-placed sources, writing one parquet each.

    Same contract as ``normalise.run``: a file nobody has placed yet is a
    SKIP, anything else propagates.
    """
    targets = only or list(NORMALISERS)
    results: list[dict] = []

    with traced_layer("L1", f"normalise {len(targets)} external source(s)"):
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
    """CLI entry point. Writes normalise_external_report.json."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", choices=sorted(NORMALISERS))
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    results = run(args.only)
    write_json(paths.METRICS / "normalise_external_report.json",
               {"results": results})

    ok = [r for r in results if r["status"] == "ok"]
    print(f"\n  {len(ok)}/{len(results)} normalised -> "
          f"{paths.rel(paths.INTERIM)}")
    for r in ok:
        print(f"    {r['source']:20} {r['rows']:>9,} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
