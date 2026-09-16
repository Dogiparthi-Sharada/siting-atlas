"""The Daganzo maths, checked against hand-computed values.

The whole siting argument rests on one claim: local travel falls with the
SQUARE ROOT of stop density, so doubling density buys only a 29% saving. If
the exponent were wrong — 1/delta instead of 1/sqrt(delta) — every number in
the model would still be finite, positive and plausibly ordered, and the
ranking would be wrong. Nothing downstream can detect that, so it is pinned
here analytically rather than by regression against a stored output.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from siting_atlas.cost.daganzo import DaganzoCostModel, haversine_miles
from siting_atlas.cost.params import BASELINE


# ---------------------------------------------------------------------------
# haversine
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("a,b,known", [
    ((40.7128, -74.0060), (34.0522, -118.2437), 2445.0),   # New York - LA
    ((41.8781, -87.6298), (39.7392, -104.9903), 920.0),    # Chicago - Denver
    ((37.6213, -122.3790), (37.7213, -122.2208), 11.1),    # SFO - Oakland
])
def test_haversine_matches_published_city_distances(a, b, known):
    got = haversine_miles(a[0], a[1], b[0], b[1])
    assert got == pytest.approx(known, rel=0.01)


def test_one_degree_of_latitude_is_sixty_nine_miles():
    # A pure-latitude leg is the one case with a closed form, so it catches a
    # radians/degrees mix-up or a swapped lat/lon argument order, both of
    # which produce a finite wrong number rather than an error.
    assert haversine_miles(0.0, 0.0, 1.0, 0.0) == pytest.approx(69.09,
                                                                abs=0.01)


def test_identical_points_are_exactly_zero_not_nan():
    # Without the np.clip(a, 0, 1) guard, floating point can push the
    # argument of arcsin fractionally negative and return NaN. A NaN line
    # haul silently becomes the 25-mile default in linehaul_miles().
    assert haversine_miles(37.0, -122.0, 37.0, -122.0) == 0.0
    grid = np.linspace(-89.0, 89.0, 40)
    d = haversine_miles(grid, grid, grid, grid)
    assert not np.isnan(d).any()
    assert (d == 0.0).all()


def test_haversine_is_vectorised_and_symmetric():
    got = haversine_miles(np.array([40.0, 34.0]), np.array([-74.0, -118.0]),
                          np.array([34.0, 40.0]), np.array([-118.0, -74.0]))
    assert got.shape == (2,)
    assert got[0] == pytest.approx(got[1])


# ---------------------------------------------------------------------------
# the local term: k / sqrt(delta)
# ---------------------------------------------------------------------------
def _local(density, params=BASELINE):
    model = DaganzoCostModel(params)
    out = model.distance_per_stop(pd.Series([float(density)]),
                                  pd.Series([0.0]))
    return float(out["local_miles_per_stop"].iloc[0])


def test_local_distance_equals_k_over_sqrt_density_times_circuity():
    # Hand-computed: k=0.57, delta=400 stops/sq mi -> 0.57/20 = 0.0285
    # straight-line miles per stop, x 1.30 circuity = 0.03705 street miles.
    assert _local(400.0) == pytest.approx(0.57 / math.sqrt(400.0) * 1.30)
    assert _local(400.0) == pytest.approx(0.03705, abs=1e-6)


def test_doubling_density_cuts_local_distance_by_exactly_29_percent():
    """The model's central claim, stated as an exact ratio.

    1 - 1/sqrt(2) = 0.29289...  If the code ever used 1/delta the saving
    would be 50% and the ranking of dense against sparse ZCTAs would change,
    with no error and no implausible number anywhere in the output.
    """
    base, doubled = _local(50.0), _local(100.0)
    assert doubled / base == pytest.approx(1.0 / math.sqrt(2.0), rel=1e-12)
    saving = 1.0 - doubled / base
    assert saving == pytest.approx(0.2929, abs=1e-4)
    assert saving < 0.5, "a 50% saving means the exponent is 1, not 1/2"


def test_hundredfold_density_moves_local_distance_only_tenfold():
    # The worked pair in the module docstring: 4 vs 400 stops/sq mi.
    assert _local(4.0) / _local(400.0) == pytest.approx(10.0, rel=1e-12)


def test_local_distance_is_proportional_to_the_bhh_constant():
    # 0.57 (street sweeps) vs 0.71 (random TSP) is the stated optimism knob;
    # it must scale the local term exactly, not be buried in a fudge factor.
    pess = dataclasses.replace(BASELINE, bhh_constant=0.71)
    assert _local(100.0, pess) / _local(100.0) == pytest.approx(0.71 / 0.57)


# ---------------------------------------------------------------------------
# the line-haul term: 2L / C
# ---------------------------------------------------------------------------
def test_linehaul_per_stop_is_the_round_trip_shared_over_the_tour():
    model = DaganzoCostModel(BASELINE)
    out = model.distance_per_stop(pd.Series([100.0]), pd.Series([25.0]))
    # 2 x 25 miles / 120 stops = 0.416667 miles per stop.
    assert out["linehaul_miles_per_stop"].iloc[0] == pytest.approx(
        2.0 * 25.0 / 120.0)
    assert out["miles_per_stop"].iloc[0] == pytest.approx(
        out["local_miles_per_stop"].iloc[0]
        + out["linehaul_miles_per_stop"].iloc[0])


def test_a_bigger_tour_dilutes_line_haul_but_not_local_travel():
    """Line haul is shared; local travel is not. Conflating them would make
    a bigger van look like a cure for sparsity, which it is not."""
    big = DaganzoCostModel(dataclasses.replace(BASELINE, stops_per_tour=240))
    small = DaganzoCostModel(BASELINE)
    d, lh = pd.Series([100.0]), pd.Series([25.0])
    a, b = big.distance_per_stop(d, lh), small.distance_per_stop(d, lh)
    assert (a["linehaul_miles_per_stop"].iloc[0]
            == pytest.approx(b["linehaul_miles_per_stop"].iloc[0] / 2))
    assert (a["local_miles_per_stop"].iloc[0]
            == pytest.approx(b["local_miles_per_stop"].iloc[0]))


# ---------------------------------------------------------------------------
# depot geometry
# ---------------------------------------------------------------------------
def _geo(**over):
    base = {"zcta": ["a", "b"], "cbsa_code": ["1", "1"],
            "latitude": [40.0, 41.0], "longitude": [-74.0, -74.0],
            "population": [1000.0, 0.0]}
    base.update(over)
    return pd.DataFrame(base)


def _parcels(frame, volume=(1000.0, 0.0)):
    """Daily parcels per row.

    Depots are placed by parcel volume, not population, so the tests supply
    it explicitly rather than letting the model derive it from households —
    the point under test is the placement, not the demand model.
    """
    return pd.Series(list(volume)[:len(frame)], index=frame.index)


def _one_depot():
    """Parameters that force a single depot, so placement is predictable.

    A throughput far above the fixture's volume makes K = 1, which is what
    lets these tests assert an exact centroid. The multi-depot behaviour is
    covered separately in test_cost_depots.py.
    """
    return replace(BASELINE, parcels_per_depot_per_day=1e12)


def test_depot_lands_on_the_demand_not_the_geometric_middle():
    frame = _geo()
    miles = DaganzoCostModel(_one_depot()).linehaul_miles(
        frame, _parcels(frame))
    # Every parcel is in 'a', so the one depot sits on 'a' — not at the
    # midpoint, which is where an unweighted centroid would put it.
    assert miles.iloc[0] == pytest.approx(0.0)
    assert miles.iloc[1] == pytest.approx(
        haversine_miles(41.0, -74.0, 40.0, -74.0) * 1.30)


def test_circuity_is_applied_to_line_haul_exactly_once():
    # linehaul_miles() already converts straight-line to street distance.
    # distance_per_stop() must not multiply by circuity again, or the sparse
    # ZCTAs get a 1.69x line-haul penalty that is pure double counting.
    model = DaganzoCostModel(_one_depot())
    straight = haversine_miles(41.0, -74.0, 40.0, -74.0)
    frame = _geo()
    lh = model.linehaul_miles(frame, _parcels(frame)).iloc[1]
    per_stop = model.distance_per_stop(pd.Series([100.0]),
                                       pd.Series([lh]))
    assert per_stop["linehaul_miles_per_stop"].iloc[0] == pytest.approx(
        2.0 * straight * 1.30 / 120.0)


def test_metro_with_no_parcels_does_not_crash_or_return_nan():
    # A metro whose rows all have zero demand has nowhere to put a depot.
    # Dividing by a zero weight would take the whole of L4 down, and a NaN
    # would drop the metro out of every percentile in silence.
    frame = _geo()
    miles = DaganzoCostModel(_one_depot()).linehaul_miles(
        frame, _parcels(frame, volume=(0.0, 0.0)))
    assert not miles.isna().any()
    assert (miles == BASELINE.default_linehaul_miles).all()


def test_missing_cbsa_column_uses_the_documented_default():
    frame = pd.DataFrame({"zcta": ["a"], "latitude": [40.0],
                          "longitude": [-74.0], "population": [10.0]})
    miles = DaganzoCostModel(BASELINE).linehaul_miles(frame)
    assert miles.tolist() == [BASELINE.default_linehaul_miles]


def test_a_zcta_with_no_cbsa_gets_the_default_not_nan():
    # A NaN line haul would propagate to NaN cost and drop the ZCTA out of
    # every percentile silently.
    frame = _geo(cbsa_code=["1", None])
    miles = DaganzoCostModel(_one_depot()).linehaul_miles(
        frame, _parcels(frame))
    assert not miles.isna().any()
    assert miles.iloc[1] == pytest.approx(BASELINE.default_linehaul_miles)
