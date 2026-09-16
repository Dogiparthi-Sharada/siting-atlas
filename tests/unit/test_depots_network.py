"""The depot NETWORK: the capacity rule, the interface, and the edges.

Split from ``test_depots_pmedian.py``, which covers the objective and the
solver. This file covers what ``DepotNetwork`` promises its callers —
`daganzo.linehaul_miles` is the only one — and what it deliberately does
not promise, which is per-depot capacity feasibility.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.cost.daganzo import haversine_miles
from siting_atlas.cost.depots import DepotNetwork

MILES_PER_DEGREE_LAT = haversine_miles(0.0, 0.0, 1.0, 0.0)


def _line(offsets_miles, parcels, cbsa="1", lat0=40.0, lon=-74.0):
    """ZCTAs strung along a north-south line, at the given mile offsets."""
    return (pd.DataFrame({
        "zcta": [f"z{i}" for i in range(len(offsets_miles))],
        "cbsa_code": [cbsa] * len(offsets_miles),
        "latitude": [lat0 + m / MILES_PER_DEGREE_LAT for m in offsets_miles],
        "longitude": [lon] * len(offsets_miles)}),
        pd.Series(list(parcels), dtype=float))


# ---------------------------------------------------------------------------
# what the capacity rule does and does not promise
# ---------------------------------------------------------------------------
def test_depot_count_follows_the_aggregate_capacity_rule():
    """K = ceil(demand / throughput), capped at the candidate count."""
    frame, parcels = _line(list(range(10)), [10_000.0] * 10)
    assert len(DepotNetwork(40_000.0).fit(frame, parcels).depots) == 3
    assert len(DepotNetwork(100_000.0).fit(frame, parcels).depots) == 1
    # Cannot open more depots than there are places to put them.
    assert len(DepotNetwork(1.0).fit(frame, parcels).depots) == 10


def test_per_depot_capacity_is_not_enforced_and_says_so():
    """Documenting the giving-up, not asserting it is fine.

    We solve the p-median with p fixed by the AGGREGATE capacity constraint,
    not the capacitated p-median. Nearest-depot assignment can therefore
    overload one depot. This test exists so that the day somebody needs the
    capacitated model, the gap is already written down and measured rather
    than discovered.
    """
    # Nine ZCTAs bunched at one end, one far away. Two depots are bought.
    frame, parcels = _line([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 200.0],
                           [9_000.0] * 9 + [1_000.0])
    net = DepotNetwork(40_000.0).fit(frame, parcels)
    assert len(net.depots) == 3

    d = net.distance_miles(frame)
    nearest = np.argmin(
        haversine_miles(frame["latitude"].to_numpy()[:, None],
                        frame["longitude"].to_numpy()[:, None],
                        net.depots["depot_lat"].to_numpy()[None, :],
                        net.depots["depot_lon"].to_numpy()[None, :]), axis=1)
    load = pd.Series(parcels.to_numpy()).groupby(nearest).sum()
    assert load.max() > 40_000.0, (
        "if this ever stops holding, the aggregate-capacity caveat in "
        "depots.py has become conservative and can be relaxed")
    assert not d.isna().any()


# ---------------------------------------------------------------------------
# interface and edge cases kept from the k-means version
# ---------------------------------------------------------------------------
def test_metro_with_no_demand_is_skipped_not_crashed():
    frame, parcels = _line([0.0, 10.0], [0.0, 0.0])
    net = DepotNetwork().fit(frame, parcels)
    assert net.depots.empty
    assert (net.distance_miles(frame, fallback=25.0) == 25.0).all()


def test_rows_with_unusable_coordinates_do_not_produce_nan_depots():
    frame, parcels = _line([0.0, 10.0, 20.0], [100.0, 100.0, 100.0])
    frame.loc[1, "latitude"] = np.nan
    net = DepotNetwork(40_000.0).fit(frame, parcels)
    assert not net.depots[["depot_lat", "depot_lon"]].isna().any().any()


def test_summary_still_counts_depots_per_metro():
    frame, parcels = _line([0.0, 10.0, 20.0, 30.0], [30_000.0] * 4)
    frame["cbsa_code"] = ["1", "1", "2", "2"]
    s = DepotNetwork(40_000.0).fit(frame, parcels).summary()
    assert list(s.columns) == ["cbsa_code", "depots"]
    assert s.set_index("cbsa_code")["depots"].to_dict() == {"1": 2, "2": 2}


def test_distance_is_to_the_nearest_depot_not_the_metro_one():
    frame, parcels = _line([0.0, 100.0], [40_000.0, 40_000.0])
    net = DepotNetwork(40_000.0).fit(frame, parcels)
    assert len(net.depots) == 2
    assert net.distance_miles(frame).max() == pytest.approx(0.0, abs=1e-6)


def test_unfitted_network_returns_the_fallback():
    frame, _ = _line([0.0], [1.0])
    assert (DepotNetwork().distance_miles(frame, fallback=17.0) == 17.0).all()
    assert DepotNetwork().summary().empty
