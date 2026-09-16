"""Acquire American Community Survey estimates from the Census API.

Separate from ``acquire.py`` because the API behaves unlike a bulk file: it
is paginated by geography, it answers a missing credential with an HTML page
carrying HTTP 200, and it returns everything — including numbers — as
strings with sentinel values for suppressed cells.

    python -m siting_atlas.ingest.census_api            # ACS5 at ZCTA
    python -m siting_atlas.ingest.census_api --acs1     # ACS1 metro context

Writes one typed parquet per dataset into data/interim/.
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from ..common import config, paths
from ..common.context import init_run
from ..common.http import fetch
from ..common.logging_setup import configure, get_logger
from ..common.sentinels import flag_sentinels
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("census")

BASE = "https://api.census.gov/data/{year}/acs/{dataset}"

# The API encodes unavailable data as large negative sentinels rather than
# nulls. Treating them as numbers silently poisons every downstream mean.
#
# These are Van den Broeck's IMPOSSIBLE band, not his inlier band: they are
# out of range by construction, so mapping them to NULL is a correction and
# needs no flag beside it. The codes that sit INSIDE the plausible range —
# $250,001, $2,499 — are a different class and are declared in
# common/sentinels.py, where they are flagged and never edited.
SENTINELS = {-666666666, -999999999, -888888888, -222222222, -333333333,
             -555555555}



def _to_numeric(series: pd.Series) -> pd.Series:
    """Coerce an API column to float, mapping sentinels to missing."""
    out = pd.to_numeric(series, errors="coerce")
    return out.mask(out.isin(SENTINELS))


def fetch_acs(dataset: str, year: int, variables: dict[str, str],
              geo: str, *, moe_for: tuple[str, ...] = ()) -> pd.DataFrame:
    """Fetch one ACS dataset for one geography level.

    Parameters
    ----------
    dataset
        ``acs5`` or ``acs1``.
    geo
        A ``for=`` clause, e.g. ``zip code tabulation area:*``.
    moe_for
        Estimate variables whose margin of error should also be requested.
        The API exposes these by swapping the trailing ``E`` for ``M``.
    """
    codes = list(variables)
    codes += [v[:-1] + "M" for v in moe_for if v in variables]
    url = BASE.format(year=year, dataset=dataset)
    params = {"get": "NAME," + ",".join(codes), "for": geo,
              "key": config.require_census_key()}

    # expect="json" guards the documented failure mode: without a key the
    # endpoint returns an HTML error page with a 200 status.
    got = fetch(url, source=f"{dataset}_{year}", params=params, expect="json")
    payload = json.loads(got.path.read_text(encoding="utf-8"))

    frame = pd.DataFrame(payload[1:], columns=payload[0])
    rename = dict(variables)
    rename.update({v[:-1] + "M": variables[v] + "_moe" for v in moe_for
                   if v in variables})
    frame = frame.rename(columns=rename)

    for col in list(rename.values()):
        if col in frame.columns:
            frame[col] = _to_numeric(frame[col])

    artefact(got.path, dataset=dataset, year=year, rows=len(frame))
    return frame


def acs5_zcta(year: int | None = None) -> pd.DataFrame:
    """ACS 5-year estimates for every ZCTA in the country."""
    year = year or config.ACS_YEAR
    frame = fetch_acs("acs5", year, config.ACS_VARIABLES,
                      "zip code tabulation area:*",
                      moe_for=config.ACS_MOE_FOR)

    # The geography column name has changed between vintages; accept either.
    geo_col = next((c for c in frame.columns
                    if "zip code tabulation area" in c.lower()), None)
    if geo_col is None:
        raise RuntimeError(
            f"no ZCTA column in response: {list(frame.columns)}")

    frame = frame.rename(columns={geo_col: "zcta"})
    # Keep ZCTA as a zero-padded string. As an integer, 01890 becomes 1890
    # and every downstream join silently drops it.
    frame["zcta"] = frame["zcta"].astype(str).str.zfill(5)
    frame["acs_year"] = year
    frame = frame.drop(columns=[c for c in ("NAME",) if c in frame.columns])

    return flag_censoring(frame)


def flag_censoring(frame: pd.DataFrame) -> pd.DataFrame:
    """Mark the ACS substitute codes, without changing a value.

    A thin alias over ``common.sentinels.flag_sentinels(frame, "acs5_zcta")``
    — the codes themselves are declared there, with the other source that has
    the same defect, because they are one class and not two. See that module
    for why $250,001 is Rahm & Do's *missing value* rather than a measurement,
    and for the reason no range check will ever find it.

    Screening, in Van den Broeck's sense, kept strictly apart from editing:
    the value is left exactly as the Census published it. Nothing here is
    reversible-unsafe because nothing here is an edit; recovering the pre-flag
    frame is dropping the four boolean columns.

    ``cost/daganzo.py`` is the consumer that should condition on the income
    pair: ``daily_parcels`` scales with an income elasticity, so a top-coded
    ZCTA has its parcel demand — and therefore its cost advantage —
    understated by construction. 36 of the 2,333 ZCTAs in the published cost
    ranking carry a top-coded income and 46 a top-coded home value. What the
    cost model should do about that is a modelling choice, not a cleaning one,
    so this function only makes the choice available.
    """
    return flag_sentinels(frame, "acs5_zcta")


def acs1_metro(year: int | None = None) -> pd.DataFrame:
    """ACS 1-year estimates at metro grain — the shorter-lag context series."""
    year = year or config.ACS_YEAR
    geo = ("metropolitan statistical area/micropolitan statistical area:*")
    frame = fetch_acs("acs1", year,
                      {"B01003_001E": "population",
                       "B19013_001E": "median_household_income"}, geo)
    geo_col = next((c for c in frame.columns
                    if "statistical area" in c.lower()), None)
    frame = frame.rename(columns={geo_col: "cbsa"})
    frame["cbsa"] = frame["cbsa"].astype(str).str.zfill(5)
    frame["acs_year"] = year
    return frame


def _report(frame: pd.DataFrame, label: str) -> None:
    """Log coverage so a silently-truncated response is visible immediately."""
    metric(f"{label}_rows", len(frame))
    numeric = [c for c in frame.columns
               if frame[c].dtype.kind in "if" and not c.endswith("_moe")
               and not c.endswith("_topcoded") and c != "acs_year"]
    for col in numeric:
        present = frame[col].notna().mean()
        _log.info("  %-28s %5.1f%% populated  median=%s", col,
                  present * 100,
                  f"{frame[col].median():,.0f}" if present else "n/a")


def main() -> int:
    """CLI entry point: fetch ACS and write it to data/interim/."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=config.ACS_YEAR)
    ap.add_argument("--acs1", action="store_true",
                    help="also fetch the 1-year metro context series")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L0", f"Census API, ACS {args.year}"):
        with step("acs5:zcta"):
            acs5 = acs5_zcta(args.year)
            _report(acs5, "acs5")
            out = paths.INTERIM / f"acs5_zcta_{args.year}.parquet"
            acs5.to_parquet(out, index=False)
            artefact(out, rows=len(acs5), cols=len(acs5.columns))

        if args.acs1:
            with step("acs1:metro"):
                acs1 = acs1_metro(args.year)
                _report(acs1, "acs1")
                out1 = paths.INTERIM / f"acs1_metro_{args.year}.parquet"
                acs1.to_parquet(out1, index=False)
                artefact(out1, rows=len(acs1), cols=len(acs1.columns))

    print(f"\n  ACS {args.year}: {len(acs5):,} ZCTAs, "
          f"{len(acs5.columns)} columns -> "
          f"{paths.rel(paths.INTERIM / f'acs5_zcta_{args.year}.parquet')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
