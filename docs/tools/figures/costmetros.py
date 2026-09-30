"""One metro definition, read from the station-based cost artefacts.

Three figures -- the README hero, the README national map and the paper's
column-width cost figure -- all have to answer "which metros?" the same way,
or a reader who sees two of them side by side is being shown two different
networks. The rule lives here once.

**The unit is a station, not a ZCTA.** ``cost_by_station_<period>_<scenario>
.parquet`` is one row per delivery station with a median, an IQR and a
coordinate. Grouping it by ``metro`` gives 174 metros over 481 stations, which
is what ``cost_by_station.json`` publishes.

**Selection is by station count, and by a threshold rather than a rank.**
Ranking the metros and taking the top *k* looks cleaner and is not: eight
metros are tied at five stations each, so "top 25" silently decides between
St. Louis and Portland on whatever order the sort happened to produce. A
threshold cannot do that. ``>= 5`` stations lands on exactly 25 metros and
``>= 8`` on exactly 15, both without a tie at the boundary, and the resulting
counts are computed at build time rather than written down here.

For the record, since the same question was asked of the raw facility panel:
176 metros hold one of the 501 geocoded stations and the top 25 of *those*
hold 251, an alphabetical coin-flip at the boundary away from this set --
they differ by one metro. The 20 stations with no ZCTA inside the catchment
carry no cost, so they are drawn on the map but cannot size or colour a
bubble.

Costs, coordinates, counts and the period all come out of the artefacts.
"""

from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REPORT = "outputs/metrics/cost_by_station.json"
STATION_TBL = "outputs/tables/cost_by_station_{period}_{scenario}.parquet"
PERIOD = "2023q4"

#: Minimum costed stations for a metro to be drawn. A layout choice -- how
#: many rows or bubbles the medium can carry -- so the number of metros each
#: one yields is counted from the data, never asserted.
MIN_WIDE = 5      # README width
MIN_COLUMN = 8    # IEEE single column


def report(scenario: str = "baseline") -> tuple[dict, dict]:
    """The run-level report and the block for one scenario."""
    with open(os.path.join(ROOT, REPORT), encoding="utf-8") as fh:
        j = json.load(fh)
    return j, j["scenarios"][scenario]


def stations(scenario: str = "baseline") -> pd.DataFrame:
    """One row per station that has at least one costed ZCTA."""
    rel = STATION_TBL.format(period=PERIOD, scenario=scenario)
    return pd.read_parquet(os.path.join(ROOT, rel))


def by_metro(st: pd.DataFrame) -> pd.DataFrame:
    """Median, interquartile range, count and centroid, per metro.

    The spread drawn is across the metro's *stations*, not across its ZCTAs.
    A row whose size says "33 stations" and whose bar says "the middle half
    of some other population" would be two units in one mark.
    """
    g = st.groupby("metro")["cost_per_parcel_median"]
    out = pd.DataFrame({
        "stations": g.size(),
        "median": g.median(),
        "q1": g.quantile(0.25),
        "q3": g.quantile(0.75),
    })
    pos = st.groupby("metro")[["station_lat", "station_lon"]].mean()
    return out.join(pos).reset_index()


def largest(metros: pd.DataFrame, min_stations: int) -> pd.DataFrame:
    """Metros at or above the station threshold, ordered by cost."""
    sel = metros[metros["stations"] >= min_stations]
    return sel.sort_values("median").reset_index(drop=True)


def short(title: str) -> str:
    """"Miami-Fort Lauderdale-West Palm Beach, FL" -> "Miami".

    The anchor city of a CBSA title is everything before the first hyphen or
    comma. Layout, not data: the full title is what was read, this is what
    fits beside a bubble.
    """
    return title.split(",")[0].split("-")[0].strip()


def short_state(title: str) -> str:
    """The anchor city and its first state: "New York, NY"."""
    if "," not in title:
        return short(title)
    return f"{short(title)}, {title.rsplit(',', 1)[1].strip().split('-')[0]}"


def period_label() -> str:
    """"2023q4" -> "2023 Q4", taken from the artefact naming."""
    return f"{PERIOD[:4]} {PERIOD[4:].upper()}"
