"""L5 — locate and load the cost-model output the figures are drawn from.

Every chart in this package reads the same artefact, so the "where is it and
is it usable?" question is answered once, here. Two failures are worth
naming:

* The parquet does not exist. The figures are downstream of a model run, and
  a missing input must produce an instruction ("run this command"), not a
  FileNotFoundError from three frames deep. That is what
  CostTableMissingError carries.
* The parquet exists but predates a schema change. A chart that silently
  drops a renamed column produces a plausible, wrong picture, which is worse
  than a crash — hence the explicit REQUIRED check.

Nothing here invents data. If a column is absent the loader says so; it does
not substitute a default.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger

_log = get_logger("viz.data")

#: Filenames the cost runner writes, e.g. cost_to_serve_2023q4_baseline.
_NAME = re.compile(r"^cost_to_serve_(\d{4})q(\d)_(.+)$")

#: Columns some chart needs. Checked up front so a schema drift fails loudly.
REQUIRED = ("zcta", "rank", "metro_label", "state", "cost_per_parcel",
            "cost_per_stop", "cost_service_time", "cost_drive_time",
            "cost_distance", "cost_vehicle", "stop_density_per_sqmi",
            "daily_parcels", "daily_stops", "daily_cost_usd",
            # van_days, not vans_required. vans_required is per-ZCTA ceiling
            # — the "if this ZCTA had a dedicated van" reading — and adding
            # up 2,333 of those overstates the fleet by about 1,200 vans,
            # because every sparse ZCTA rounds its 0.02 of a van up to one.
            # van_days is fractional and additive; round once, at the end.
            "van_days")

#: Display order of the decomposition, largest-and-most-fixed first, so the
#: stack reads outward from the part the operator cannot route away.
COMPONENTS = (
    ("cost_service_time", "Driver time at the door"),
    ("cost_vehicle", "Vehicle lease"),
    ("cost_drive_time", "Driver time driving"),
    ("cost_distance", "Fuel and wear"),
)


class CostTableMissingError(FileNotFoundError):
    """Raised when the cost parquet a figure needs has not been produced.

    Carries the exact command that produces it, so the message is actionable
    wherever it surfaces — a traceback, a log line, or a Streamlit banner.
    """

    def __init__(self, year: int, quarter: int, scenario: str, path: Path):
        self.year, self.quarter = year, quarter
        self.scenario, self.path = scenario, path
        self.command = (
            "PYTHONPATH=src .venv/bin/python -m siting_atlas.cost.runner "
            f"--year {year} --quarter {quarter} --scenario {scenario}")
        super().__init__(
            f"cost table not found: {paths.rel(path)}\n"
            f"generate it with:\n    {self.command}")


def table_path(year: int, quarter: int, scenario: str) -> Path:
    return paths.TABLES / f"cost_to_serve_{year}q{quarter}_{scenario}.parquet"


def available() -> list[tuple[int, int, str]]:
    """Every (year, quarter, scenario) already on disk, sorted.

    The dashboard builds its scenario picker from this rather than from
    cost.params.SCENARIOS, because offering a scenario that has never been
    run is offering a dead end.
    """
    found = []
    for p in sorted(paths.TABLES.glob("cost_to_serve_*.parquet")):
        m = _NAME.match(p.stem)
        if m:
            found.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    return sorted(found)


def load(year: int = 2023, quarter: int = 4,
         scenario: str = "baseline") -> pd.DataFrame:
    """Read one cost table, or explain how to make it."""
    path = table_path(year, quarter, scenario)
    if not path.exists():
        raise CostTableMissingError(year, quarter, scenario, path)

    frame = pd.read_parquet(path)
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise KeyError(
            f"{paths.rel(path)} is missing {missing} — it was written by an "
            "older cost model; re-run siting_atlas.cost.runner")

    # metro_label arrives as an Arrow-backed string; groupby and matplotlib
    # category handling are both happier with object dtype, and the frame is
    # only a few thousand rows so the copy costs nothing.
    frame["metro_label"] = frame["metro_label"].astype(object)
    _log.debug("loaded %d rows from %s", len(frame), paths.rel(path))
    return frame


def parcels_per_stop(frame: pd.DataFrame) -> float:
    """Recover the scenario's parcels-per-stop from the output itself.

    The parameter is not stored in the table, but cost_per_parcel is exactly
    cost_per_stop divided by it, so the ratio is recoverable. Deriving it
    beats importing cost.params: the figure then describes the file it was
    handed, even if the defaults have since moved on.
    """
    if frame.empty:
        return float("nan")
    ratio = frame["cost_per_stop"] / frame["cost_per_parcel"]
    return float(ratio.median())


def metro_order(frame: pd.DataFrame) -> list[str]:
    """Metros sorted cheapest-median first — the reading order everywhere.

    Ordering by the value being compared is what lets a reader rank ten
    categories without a legend, which is the whole reason these charts do
    not try to spend ten hues (see viz.style).
    """
    if frame.empty:
        return []
    medians = frame.groupby("metro_label")["cost_per_parcel"].median()
    return list(medians.sort_values().index)
