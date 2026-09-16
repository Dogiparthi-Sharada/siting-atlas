"""Where the highway layer reaches, and what it found when it got there.

Two jobs, both about the EDGE of the artefact rather than its contents,
which is why they sit apart from the measurement code:

`mark_coverage` writes NULL where the ramp layer was not fetched. That is
not a formality. Outside the downloaded counties an interchange count of
zero would be read by every consumer as a measurement — "this ZCTA has no
exit" — when the true statement is "nobody looked". `docs/data/` records
that the same confusion, an empty answer presented as a zero answer, has
already cost this project a wrong conclusion about industrial land.

`summarise` reports the distributions that decide whether the covariate
can carry information at all. The one to read first is
``interstate_dist_zero_share``: polygon distance is exactly zero whenever
an interstate clips the ZCTA anywhere, and a column that is zero for half
its rows has already thrown away half of what it could have said. That
number is the argument for the mileage and count columns existing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths

#: Set to NULL outside the counties the ramp layer covers.
RAMP_COLUMNS = ("interchange_dist_km", "interchanges")

__all__ = ["RAMP_COLUMNS", "mark_coverage", "summarise"]


def mark_coverage(frame: pd.DataFrame, covered: set[str]) -> pd.DataFrame:
    """Add `ramp_coverage` and NULL the ramp columns outside it."""
    xwalk = paths.INTERIM / "zcta_county.parquet"
    if not xwalk.exists():
        frame["ramp_coverage"] = frame["interchanges"].notna()
        return frame
    link = pd.read_parquet(xwalk)
    col = "county_geoid" if "county_geoid" in link.columns else "geoid"
    inside = set(link.loc[link[col].astype(str).isin(covered),
                          "zcta"].astype(str))
    frame["ramp_coverage"] = frame["zcta"].isin(inside)
    for c in RAMP_COLUMNS:
        frame.loc[~frame["ramp_coverage"], c] = np.nan
    return frame


def _share(series: pd.Series, value: float = 0.0) -> float | None:
    return float((series == value).mean()) if len(series) else None


def summarise(frame: pd.DataFrame) -> dict:
    """The coverage and distribution facts the run prints and records."""
    cov = frame[frame["ramp_coverage"]]
    return {
        "zctas": int(len(frame)),
        "ramp_covered_zctas": int(len(cov)),
        "interstate_dist_km_median": float(
            frame["interstate_dist_km"].median()),
        "interstate_dist_zero_share": _share(frame["interstate_dist_km"]),
        "primary_road_dist_km_median": float(
            frame["primary_road_dist_km"].median()),
        "primary_road_dist_zero_share": _share(frame["primary_road_dist_km"]),
        "interstate_miles_total": float(frame["interstate_miles"].sum()),
        "interstate_miles_zero_share": _share(frame["interstate_miles"]),
        "interchanges_total": float(cov["interchanges"].sum()),
        "interchanges_zero_share": _share(cov["interchanges"]),
        "interchange_dist_km_median": float(
            cov["interchange_dist_km"].median()) if len(cov) else None,
        "interchange_dist_zero_share": _share(cov["interchange_dist_km"]),
    }
