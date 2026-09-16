"""Daganzo continuous-approximation cost of serving a ZCTA.

The idea
--------
You cannot solve a vehicle-routing problem for 2,413 ZCTAs inside a Monte
Carlo loop. You do not need to. Daganzo's continuous approximation gives the
cost of a *good* route without constructing one, from three numbers: how many
stops, how big the area, how far the depot is.

The one equation that matters, distance per stop:

    d_stop  =  2 * L / C          <- line haul, shared across the tour
             +  k / sqrt(delta)   <- local travel between stops

where L is depot-to-zone distance, C stops per tour, delta stops per square
mile, and k the BHH constant. It follows from the Beardwood-Halton-Hammersley
theorem: a tour through n random points in area A has length ~ k*sqrt(n*A).
One van covering C stops works an area C/delta, so its local distance is
k*sqrt(C * C/delta) = k*C/sqrt(delta), and per stop that is k/sqrt(delta).

Why the 1/sqrt(delta) term is the whole argument
------------------------------------------------
Local cost per parcel falls with the *square root* of density, so it falls
slowly. Doubling density cuts local travel by only 29%, not 50%. Meanwhile
line haul is divided across the tour, so it is nearly free per stop in a dense
zone and punitive in a sparse one.

A worked pair, baseline parameters, 25 miles from the depot:

    dense ZCTA    delta = 400 stops/sq mi -> local 0.037 mi/stop
    sparse ZCTA   delta =   4 stops/sq mi -> local 0.371 mi/stop

(Those include the 1.30 circuity factor that `distance_per_stop` applies;
without it they would be 0.029 and 0.285, which is what an earlier version of
this docstring quoted and the code never produced.)

A hundredfold density difference moves local distance per stop only tenfold -
and that tenfold is what separates a profitable ZIP from an unprofitable one.
This is the mechanism the whole siting decision turns on, and it is why the
model needs density right and can tolerate approximation elsewhere.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .params import BASELINE, CostParameters

_log = get_logger("cost.daganzo")

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance, vectorised over arrays."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


class DaganzoCostModel:
    """Cost to serve each ZCTA for one day, under one parameter set.

    A class because a run carries configuration (the parameters) and several
    steps share it, and because a sensitivity sweep is then just a list of
    instances. Every method returns a new frame; nothing mutates its input.
    """

    def __init__(self, params: CostParameters = BASELINE):
        self.params = params

    # -- demand ----------------------------------------------------------
    def daily_parcels(self, frame: pd.DataFrame) -> pd.Series:
        """Expected parcels per day in each ZCTA.

        Households, not population: parcels are consigned to an address. A
        four-person household is one delivery, and treating it as four would
        overstate demand exactly where households are largest.
        """
        p = self.params
        households = frame["households"].astype(float)

        income = frame["median_household_income"].astype(float)
        # Median income is missing for ~5% of ZCTAs. Falling back to the
        # reference income makes the scale factor 1.0 there - a neutral
        # assumption, and flagged in the output rather than hidden.
        income = income.fillna(p.reference_income_usd)
        scale = (income / p.reference_income_usd) ** p.income_elasticity

        weekly = households * p.parcels_per_household_per_week * scale
        return weekly / p.delivery_days_per_week

    def daily_stops(self, frame: pd.DataFrame) -> pd.Series:
        """Doors visited per day — parcels consolidated into single visits.

        The routing model is driven by stops, not parcels: the van travels
        between doors and the driver is paid per door.
        """
        return self.daily_parcels(frame) / self.params.parcels_per_stop

    def stop_density(self, frame: pd.DataFrame, stops: pd.Series) -> pd.Series:
        """Stops per square mile of LAND area.

        Land, not total: a coastal ZCTA whose area is mostly water has its
        deliveries concentrated on the land, and using total area would make
        it look artificially cheap to serve.
        """
        land = frame["land_area_sqmi"].astype(float)
        return stops / land.where(land > 0)

    # -- geometry --------------------------------------------------------
    def linehaul_miles(self, frame: pd.DataFrame,
                       parcels: pd.Series | None = None) -> pd.Series:
        """Road miles from each ZCTA to its nearest depot.

        Line haul is NOT a negligible term, and an earlier version of this
        method assumed it was. One extra mile costs $0.018 per parcel, so ten
        miles is $0.18 against a $1.51 median — 12%. Placing a single depot at
        each metro's centroid produced implied hauls from 0.4 to 145.7 miles
        and injected up to $2.62 per parcel of pure artefact into the ranking.

        So the depot network is solved instead of assumed: see `depots.py`,
        where the number of depots per metro falls out of parcel volume
        divided by a delivery station's throughput. Still a model of the
        network rather than the real one — the facility panel replaces it —
        but it is the right size and the right shape, which the centroid was
        not.
        """
        p = self.params
        if "cbsa_code" not in frame.columns:
            return pd.Series(p.default_linehaul_miles, index=frame.index)

        # Imported here rather than at module scope: depots.py imports
        # haversine_miles from this module, and a top-level import would be
        # circular.
        from .depots import DepotNetwork

        if parcels is None:
            parcels = self.daily_parcels(frame)
        network = DepotNetwork(p.parcels_per_depot_per_day).fit(frame, parcels)
        self.network = network

        # Circuity converts straight-line to street distance, so it applies
        # ONLY to distances actually measured against a depot. The fallback is
        # already expressed as a road distance; inflating it too turned the
        # documented 25-mile default into 32.5.
        straight = network.distance_miles(frame, fallback=np.nan)
        return (straight * p.circuity).fillna(p.default_linehaul_miles)

    def distance_per_stop(self, density: pd.Series,
                          linehaul: pd.Series) -> pd.DataFrame:
        """The core equation, split so each term can be inspected."""
        p = self.params
        local = p.bhh_constant / np.sqrt(density) * p.circuity
        line = 2.0 * linehaul / p.stops_per_tour
        return pd.DataFrame({"local_miles_per_stop": local,
                             "linehaul_miles_per_stop": line,
                             "miles_per_stop": local + line})

    # -- cost ------------------------------------------------------------
    def evaluate(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Cost per parcel for every row, with the components kept."""
        p = self.params
        out = frame[["zcta"]].copy()

        parcels = self.daily_parcels(frame)
        stops = parcels / p.parcels_per_stop
        density = self.stop_density(frame, stops)
        linehaul = self.linehaul_miles(frame, parcels)
        dist = self.distance_per_stop(density, linehaul)

        out["daily_parcels"] = parcels
        out["daily_stops"] = stops
        out["stop_density_per_sqmi"] = density
        out["linehaul_miles"] = linehaul
        out = out.join(dist)

        wage = frame["wage_light_truck_driver"].astype(float)
        hourly = p.labour_usd_per_hour(wage)
        per_mile = p.distance_usd_per_mile(
            frame["diesel_usd_gal"].astype(float))

        drive_hours = dist["miles_per_stop"] / p.avg_speed_mph
        service_hours = p.service_minutes_per_stop / 60.0

        out["cost_distance"] = dist["miles_per_stop"] * per_mile
        out["cost_drive_time"] = drive_hours * hourly
        out["cost_service_time"] = service_hours * hourly
        # The van is paid for whether or not it is full, so its daily lease is
        # spread over the stops actually made.
        out["cost_vehicle"] = p.van_lease_usd_per_day / p.stops_per_tour

        # Every component above is a cost per STOP. A parcel is cheaper than a
        # stop whenever more than one arrives at the same door.
        out["cost_per_stop"] = (out["cost_distance"] + out["cost_drive_time"]
                                + out["cost_service_time"]
                                + out["cost_vehicle"])
        out["cost_per_parcel"] = out["cost_per_stop"] / p.parcels_per_stop
        out["daily_cost_usd"] = out["cost_per_stop"] * stops
        # Van-days, NOT whole vans, and deliberately fractional. `cost_vehicle`
        # above charges each stop 1/C of a daily lease, which assumes marginal
        # utilisation — a real route crosses ZCTA boundaries, so a ZCTA with
        # two stops a day is two stops on somebody else's round, not a
        # dedicated van. Rounding up here while charging a fraction there
        # contradicted itself: ZCTA 60183 has 1.9 stops/day and was reported as
        # needing a whole van. Round up when aggregating a whole network, where
        # the question "how many vans do we buy" is actually being asked.
        out["van_days"] = stops / p.stops_per_tour
        # Kept, but it is the "if this ZCTA had a dedicated van" reading and
        # must NOT be summed across ZCTAs: 145 sparse ZCTAs each rounding up
        # to a whole van overstates the fleet. Aggregate `van_days` instead
        # and round once, at the network level.
        out["vans_required"] = np.ceil(out["van_days"])

        # Provenance for the rows where an input was substituted.
        out["income_imputed"] = frame["median_household_income"].isna()
        return out
