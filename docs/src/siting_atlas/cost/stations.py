"""Depots are the operator's real delivery stations, not a p-median solve.

What changed and why
--------------------
`depots.py` invents the depot layer. It divides a metro's daily parcels by a
delivery station's throughput, gets ``ceil(...)`` sites, and solves a p-median
for where they go — 334 buildings the operator never chose. The p-median is a
good solve of the wrong problem: the paper's own audit lists depot placement
as moving the headline more than any parameter *classified* as a parameter,
which is exactly what an unclassified assumption looks like.

The facility panel now carries 501 geocoded Amazon delivery stations, so the
assumption can be deleted rather than improved. Depots are those 501 points.
There is no placement step, no throughput constant, no per-metro decomposition
and no capacity story to apologise for — the network is observed.

Three things that got better, and one that got worse, stated up front:

  + The line-haul term is measured against a building that exists.
  + `parcels_per_depot_per_day` stops entering the cost path. It was the
    largest RANK mover in the model (Spearman 0.90) and it is now inert here.
  + A cost per STATION becomes definable for the first time. A p-median site
    is a modelling artefact; you cannot report an operating cost for one.
  - Coverage is now decided by where the operator built, not by where the
    pilot's ten metros are. See `CATCHMENT_MILES`.

The catchment
-------------
A ZCTA is costed only if its internal point lies within `CATCHMENT_MILES`
great-circle miles of its nearest station. Outside that, the ZCTA is served —
if at all — by a station not in this panel, or by a line haul long enough that
the continuous approximation's "one depot, one tour" geometry stops
describing the operation. Costing it anyway would produce a number, and the
number would be about the panel's incompleteness rather than about the place.

Great-circle for the catchment test, circuity-adjusted for the bill. The
radius is a statement about geography and is measured as such; the mile the
model then CHARGES for goes through `params.circuity` exactly as it does in
`daganzo.linehaul_miles`, so the economics are untouched.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from .daganzo import DaganzoCostModel, haversine_miles
from .params import BASELINE, CostParameters

_log = get_logger("cost.stations")

#: The geocoded facility panel. 693 rows, of which 501 carry a true
#: address-level coordinate from the Census batch geocoder.
STATION_FILE = paths.EXTERNAL / "facility_panel" / "geocoded_expanded.csv"

#: The same facilities with their operator, type and CBSA attached.
STATION_META = (paths.EXTERNAL / "facility_panel"
                / "national_facilities_expanded.csv")

#: Miles from a station inside which a ZCTA is costed.
#:
#: NOT tuned to a result, and not free. 15 miles is the radius already
#: pre-registered for the catchment analysis elsewhere in this project
#: (`docs/EXPERIMENTS.md` E12, where the hazard conclusion was shown not to
#: depend on it), so reusing it costs no new degree of freedom.
#:
#: CORRECTED 2026-09-16. An earlier version of this comment claimed the
#: costed set is DENSER than the pilot and that the 1/sqrt(density)
#: approximation is therefore better supported here. That was wrong, and it
#: was wrong because it compared households per square mile against the
#: pilot's published figure, which is STOPS per square mile. Like for like
#: the catchment is sparser on both measures:
#:
#:     stops / sq mi        pilot 474.8   catchment 350.2
#:     households / sq mi   pilot 1074.7  catchment  866.1
#:
#: and both tour floors move the wrong way (below one tour 5.40 -> 6.17%,
#: below the n>=15 BHH floor 1.24 -> 1.69%), though each is under a tenth of
#: a percent of catchment households.
#:
#: The real trade is COVERAGE AGAINST REGIME, and `station_report.radius_sweep`
#: recomputes it on every run rather than asking the reader to trust a comment:
#: 5 miles gives 588 stops/sq mi on 21.9% of US households, 45 miles gives 44
#: on 81.6%. No radius is both denser than the pilot and covers a majority of
#: the country. 15 is chosen because it is the pre-registered figure and
#: because it keeps the sparse tail small, not because it improves the regime.
CATCHMENT_MILES = 15.0

#: Larson and Odoni, *Urban Operations Research* (1981) §6.4.8: the BHH
#: asymptotic that `daganzo.py` rests on is quoted as usable from about
#: fifteen points in the tour. Below it the continuous approximation is
#: outside its stated regime — reported, never silently dropped.
MIN_TOUR_POINTS = 15


def load_stations(path=STATION_FILE, meta_path=STATION_META) -> pd.DataFrame:
    """The real depot layer: one row per geocoded delivery station.

    Only rows the Census geocoder actually matched to an address are kept.
    The other 192 carry a `fallback_latitude` imputed to the ZCTA centroid,
    and a ZCTA centroid is not a building: using one would put a depot in the
    middle of its own catchment by construction and drive the line haul for
    that ZCTA to roughly zero. That is the single most cost-reducing error
    available here, so the exclusion is not a nicety.
    """
    raw = pd.read_csv(path, dtype={"facility_id": str, "zcta_of_point": str})
    keep = raw["latitude"].notna() & raw["longitude"].notna()
    out = raw.loc[keep, ["facility_id", "latitude", "longitude",
                         "zcta_of_point"]].copy()
    out = out.rename(columns={"facility_id": "station_id",
                              "latitude": "station_lat",
                              "longitude": "station_lon",
                              "zcta_of_point": "station_zcta"})

    meta = pd.read_csv(meta_path, dtype={"facility_id": str,
                                         "cbsa_code": str, "zip": str})
    cols = ["facility_id", "operator", "facility_type", "city", "state",
            "cbsa_title", "cbsa_code", "status"]
    out = out.merge(meta[[c for c in cols if c in meta.columns]]
                    .rename(columns={"facility_id": "station_id"}),
                    on="station_id", how="left")

    _log.info("%d of %d facility rows carry an address-level coordinate "
              "(%d excluded as ZCTA-centroid fallbacks)",
              len(out), len(raw), len(raw) - len(out))
    return out.reset_index(drop=True)


def _codes(s: pd.Series, missing: str) -> np.ndarray:
    """Five-digit ZCTA codes as plain strings, missing values given a
    sentinel so that two unknowns never compare equal to each other."""
    return (s.astype("string").str.zfill(5)
             .fillna(missing).to_numpy(dtype=object))


class StationNetwork:
    """Nearest real station, and the distance to it, for every ZCTA.

    No `fit`. That is the point: `DepotNetwork.fit` is where the invented
    layer came from, and there is nothing left to fit.
    """

    def __init__(self, stations: pd.DataFrame):
        if stations.empty:
            raise ValueError("no geocoded stations; nothing to serve from")
        self.stations = stations.reset_index(drop=True)

    @classmethod
    def load(cls, **kw) -> StationNetwork:
        """Build the network straight from the facility panel."""
        return cls(load_stations(**kw))

    def assign(self, frame: pd.DataFrame, chunk: int = 4096,
               exclude_own_zcta: bool = False) -> pd.DataFrame:
        """Nearest station id and great-circle miles for each row.

        Brute force, chunked. 33k ZCTAs x 501 stations is 17M haversines —
        under a second — and it bills the SAME metric the cost model charges,
        with no tree, no projection and no tolerance to argue about. A KD-tree
        would be faster and would need a proof that chord order and
        great-circle order agree; at this size that proof buys nothing.

        Rows without a usable coordinate get no station and NaN miles, so the
        catchment filter drops them rather than the cost model silently
        pricing them at the fallback distance.

        ``exclude_own_zcta`` masks out every station standing INSIDE the row's
        own ZCTA. That is not a variant of the cost model — the headline never
        uses it — it exists for one question. "Do facilities sit in cheap
        ZCTAs?" is circular the moment the depot layer is the facilities
        themselves: a ZCTA containing a station has a line haul of roughly
        zero BECAUSE the station is there, which makes it cheap by
        construction. The mask answers the counterfactual the claim actually
        needs: what would this ZCTA cost if the operator had NOT built here?
        """
        lat = frame["latitude"].to_numpy(float)
        lon = frame["longitude"].to_numpy(float)
        slat = self.stations["station_lat"].to_numpy(float)
        slon = self.stations["station_lon"].to_numpy(float)
        own = None
        if exclude_own_zcta:
            # Sentinels, not NA: a station whose ZCTA is unknown must never
            # compare equal to a ZCTA whose code is also unknown, and numpy's
            # `==` on pd.NA raises rather than returning False.
            sz = _codes(self.stations["station_zcta"], "?station")
            own = _codes(frame["zcta"], "?zcta")

        idx = np.full(len(frame), -1, dtype=int)
        miles = np.full(len(frame), np.nan, dtype=float)
        usable = np.isfinite(lat) & np.isfinite(lon)
        rows = np.flatnonzero(usable)
        for start in range(0, len(rows), chunk):
            take = rows[start:start + chunk]
            d = haversine_miles(lat[take, None], lon[take, None],
                                slat[None, :], slon[None, :])
            if own is not None:
                d = np.where(own[take, None] == sz[None, :], np.inf, d)
            j = np.argmin(d, axis=1)
            idx[take] = j
            miles[take] = d[np.arange(len(take)), j]

        # Built by assignment rather than `np.where`, which coerces the None
        # branch to a float nan and so hands the caller a station id column
        # that is silently numeric for the unassignable rows.
        ids = np.full(len(frame), None, dtype=object)
        keep = idx >= 0
        ids[keep] = self.stations["station_id"].to_numpy(object)[idx[keep]]
        if (~usable).any():
            _log.warning("%d row(s) have no usable coordinate and cannot be "
                         "assigned to a station", int((~usable).sum()))
        return pd.DataFrame({"station_id": ids,
                             "station_miles": miles}, index=frame.index)


class StationCostModel(DaganzoCostModel):
    """`DaganzoCostModel` with the depot layer swapped for real stations.

    A subclass rather than an edit: `daganzo.py` is the published model and
    its structure is unchanged. The ONLY override is where the line-haul
    distance comes from. Every parameter, every component and the whole cost
    identity are inherited untouched, so any difference between this and the
    pilot is attributable to the depot layer and to nothing else.
    """

    def __init__(self, params: CostParameters = BASELINE,
                 straight_miles: pd.Series | None = None):
        super().__init__(params)
        self.straight_miles = straight_miles

    def linehaul_miles(self, frame: pd.DataFrame,
                       parcels: pd.Series | None = None) -> pd.Series:
        """Road miles to the nearest REAL station.

        Same two steps as the parent — great-circle distance, then circuity —
        with the p-median solve deleted from between them. `parcels` is
        accepted and ignored: demand chose where the invented depots went and
        has no say over where the built ones are.
        """
        if self.straight_miles is None:
            raise ValueError("StationCostModel needs straight_miles; call "
                             "StationNetwork.assign first")
        straight = self.straight_miles.reindex(frame.index).astype(float)
        return (straight * self.params.circuity).fillna(
            self.params.default_linehaul_miles)


def catchment(assigned: pd.DataFrame,
              radius: float = CATCHMENT_MILES) -> pd.Series:
    """Boolean mask: rows inside the catchment of some real station."""
    return assigned["station_miles"].le(radius).fillna(False)
