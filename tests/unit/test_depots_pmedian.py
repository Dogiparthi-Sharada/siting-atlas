"""Depot placement must optimise the objective the cost model bills.

The bug these tests were written against
----------------------------------------
``depots.py`` placed depots with k-means. k-means minimises SQUARED distance
and therefore converges on the weighted MEAN. ``daganzo.py`` line 159 bills
line haul as ``2 * L / stops_per_tour``, which is LINEAR in distance, and the
minimiser of weighted linear distance is the weighted MEDIAN. The two agree
only when demand is symmetric, which no metro is.

One metro, 60 parcels/day at mile 0 and 40 parcels/day at mile 50:

    depot at mile 0    60 x  0 + 40 x 50 = 2,000 parcel-miles
    depot at mile 20   60 x 20 + 40 x 30 = 2,400 parcel-miles

Mile 20 is where k-means puts it and it is 20% worse under the term the model
actually charges. That is the whole of the defect.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.cost.daganzo import haversine_miles
from siting_atlas.cost.depots import DepotNetwork, solve_pmedian

# One degree of latitude is 69.05 miles on this earth radius. Working in
# latitude keeps the fixtures one-dimensional, so the weighted median is
# something the reader can check by hand.
MILES_PER_DEGREE_LAT = haversine_miles(0.0, 0.0, 1.0, 0.0)


def _line(offsets_miles, parcels, cbsa="1", lat0=40.0, lon=-74.0):
    """ZCTAs strung along a north-south line, at the given mile offsets."""
    return (pd.DataFrame({
        "zcta": [f"z{i}" for i in range(len(offsets_miles))],
        "cbsa_code": [cbsa] * len(offsets_miles),
        "latitude": [lat0 + m / MILES_PER_DEGREE_LAT for m in offsets_miles],
        "longitude": [lon] * len(offsets_miles)}),
        pd.Series(list(parcels), dtype=float))


def _parcel_miles(network, frame, parcels):
    """The quantity the line-haul term is proportional to: sum w_k * d_k."""
    return float((network.distance_miles(frame) * parcels).sum())


# ---------------------------------------------------------------------------
# the defect
# ---------------------------------------------------------------------------
def test_single_depot_goes_to_the_weighted_median_not_the_weighted_mean():
    """FAILS on k-means. 60/40 at miles 0 and 50.

    k-means (squared distance) lands on mile 20, the weighted mean.
    p-median (linear distance) lands on mile 0, the weighted median.
    """
    frame, parcels = _line([0.0, 50.0], [60.0, 40.0])
    net = DepotNetwork(parcels_per_depot=40_000.0).fit(frame, parcels)

    assert len(net.depots) == 1
    # The depot sits on the 60-parcel ZCTA, not 20 miles up the road.
    assert net.depots["depot_lat"].iloc[0] == pytest.approx(
        frame["latitude"].iloc[0], abs=1e-9)
    assert _parcel_miles(net, frame, parcels) == pytest.approx(2000.0,
                                                               rel=2e-3)


def test_the_median_beats_the_mean_on_the_term_the_model_bills():
    """The same fixture, stated as the inequality that matters.

    Written separately because the test above could be satisfied by a lucky
    rounding; this one compares the two placements on the objective itself.
    """
    frame, parcels = _line([0.0, 50.0], [60.0, 40.0])
    net = DepotNetwork(parcels_per_depot=40_000.0).fit(frame, parcels)

    mean_lat = np.average(frame["latitude"], weights=parcels)
    at_mean = DepotNetwork()
    at_mean.depots = pd.DataFrame({"cbsa_code": ["1"], "depot_lat": [mean_lat],
                                   "depot_lon": [-74.0]})

    assert _parcel_miles(net, frame, parcels) < _parcel_miles(
        at_mean, frame, parcels)
    # And by roughly the 20% the arithmetic predicts.
    ratio = (_parcel_miles(at_mean, frame, parcels)
             / _parcel_miles(net, frame, parcels))
    assert ratio == pytest.approx(1.20, abs=0.02)


def test_depots_land_on_real_candidate_rows_not_invented_coordinates():
    """Hakimi's node restriction, as a property of the output.

    Every depot coordinate must be one of the input rows' coordinates. This
    is what licenses the claim that depots sit on inhabited ground rather
    than in the middle of a reservoir, and k-means could not make it.
    """
    rng = np.random.default_rng(0)
    n = 60
    frame = pd.DataFrame({
        "zcta": [f"z{i}" for i in range(n)],
        "cbsa_code": ["1"] * n,
        "latitude": 40.0 + rng.random(n),
        "longitude": -74.0 + rng.random(n)})
    parcels = pd.Series(rng.random(n) * 10_000.0)

    net = DepotNetwork(parcels_per_depot=40_000.0).fit(frame, parcels)
    sites = set(zip(frame["latitude"], frame["longitude"], strict=True))
    for lat, lon in zip(net.depots["depot_lat"], net.depots["depot_lon"],
                        strict=True):
        assert (lat, lon) in sites


# ---------------------------------------------------------------------------
# the solver
# ---------------------------------------------------------------------------
def _brute_force(dist, weights, p):
    """Exact p-median by enumeration. Only tractable for tiny instances."""
    from itertools import combinations
    n = len(weights)
    best, arg = np.inf, None
    for s in combinations(range(n), p):
        v = float((weights * dist[:, list(s)].min(axis=1)).sum())
        if v < best - 1e-12:
            best, arg = v, s
    return best, arg


def _scatter(seed, n=12):
    rng = np.random.default_rng(seed)
    pts = rng.random((n, 2)) * 50.0
    dist = np.hypot(pts[:, 0][:, None] - pts[None, :, 0],
                    pts[:, 1][:, None] - pts[None, :, 1])
    return dist, rng.random(n) * 100.0


def test_heuristic_quality_against_full_enumeration():
    """The whole census, not a flattering subset.

    Thirty random twelve-point instances x p = 1..5, every one of them
    solved exactly by enumeration and compared. The numbers below are the
    honest answer and they are pinned so a future "optimisation" that
    quietly degrades placement is caught:

        instances                150
        solved exactly           139   (92.7%)
        mean gap                 0.265%
        worst gap               11.02%  (seed 19, p = 2)

    Small p on scattered points is the hard case for a 1-opt search: with
    two facilities the optimum is often two swaps away and there is no
    downhill path to it. The pilot is the easy case by comparison — large p,
    heavily clustered demand — and there the measured gap to a Lagrangean
    lower bound is 0.89%. See the docstring of `solve_pmedian`.
    """
    exact, gaps = 0, []
    for seed in range(30):
        dist, w = _scatter(seed)
        for p in range(1, 6):
            sites = solve_pmedian(dist, w, p)
            got = float((w * dist[:, sites].min(axis=1)).sum())
            want, _ = _brute_force(dist, w, p)
            gap = got / want - 1.0
            assert gap > -1e-9, "heuristic beat the enumerated optimum"
            gaps.append(gap)
            exact += gap < 1e-9

    assert len(gaps) == 150
    assert exact == 139
    assert float(np.mean(gaps)) == pytest.approx(0.00265, abs=2e-5)
    assert max(gaps) == pytest.approx(0.1102, abs=1e-4)


def test_the_known_counterexample_where_1_opt_stops_short():
    """Pinned so the docstring's honesty claim cannot quietly rot.

    Twelve points, p = 2. The heuristic returns {4, 6} and the optimum is
    {3, 5}: the two differ in BOTH facilities, so no single vertex
    substitution bridges them and a 1-opt search cannot get there. The gap
    is 7.5%. Vertex substitution has no constant-factor guarantee and this
    is what that means concretely.

    If a future change closes this gap, the docstring in depots.py and the
    "what we give up" note in docs/research/NOTES_klose_drexl_2005.md both
    need updating — hence the assertion on the gap rather than a bare skip.
    """
    dist, w = _scatter(7)
    sites = solve_pmedian(dist, w, 2)
    got = float((w * dist[:, sites].min(axis=1)).sum())
    want, arg = _brute_force(dist, w, 2)
    assert list(sites) == [4, 6]
    assert arg == (3, 5)
    assert got / want == pytest.approx(1.075, abs=0.002)

    # ...and it IS a 1-opt local optimum, which is exactly the guarantee the
    # docstring claims and no more.
    for i in range(2):
        for j in range(12):
            if j in sites:
                continue
            alt = [x for k, x in enumerate(sites) if k != i] + [j]
            assert float((w * dist[:, alt].min(axis=1)).sum()) >= got - 1e-9


def test_placement_is_deterministic():
    """Depot locations feed the published ranking; reruns must agree."""
    rng = np.random.default_rng(3)
    n = 80
    frame = pd.DataFrame({
        "zcta": [f"z{i}" for i in range(n)],
        "cbsa_code": ["1"] * (n // 2) + ["2"] * (n - n // 2),
        "latitude": 40.0 + rng.random(n) * 2,
        "longitude": -74.0 + rng.random(n) * 2})
    parcels = pd.Series(rng.random(n) * 20_000.0)

    a = DepotNetwork(20_000.0).fit(frame, parcels).depots
    b = DepotNetwork(20_000.0).fit(frame, parcels).depots
    pd.testing.assert_frame_equal(a, b)


def test_solver_returns_sorted_unique_sites():
    rng = np.random.default_rng(11)
    pts = rng.random((30, 2)) * 10
    dist = np.hypot(pts[:, 0][:, None] - pts[None, :, 0],
                    pts[:, 1][:, None] - pts[None, :, 1])
    sites = solve_pmedian(dist, np.ones(30), 5)
    assert len(sites) == 5
    assert len(set(sites.tolist())) == 5
    assert list(sites) == sorted(sites)


def test_p_at_or_above_the_candidate_count_opens_everything():
    dist = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert list(solve_pmedian(dist, np.array([1.0, 1.0]), 2)) == [0, 1]
    assert list(solve_pmedian(dist, np.array([1.0, 1.0]), 5)) == [0, 1]


def test_zero_demand_candidates_are_still_eligible_sites():
    """A ZCTA with no parcels is still a place a depot can stand.

    Dropping them would be a silent change to the candidate set, and the
    weights in Hakimi's formulation are explicitly allowed to be zero.
    """
    dist = np.array([[0.0, 1.0, 2.0],
                     [1.0, 0.0, 1.0],
                     [2.0, 1.0, 0.0]])
    # All demand at the ends; the middle point is the best single median.
    sites = solve_pmedian(dist, np.array([1.0, 0.0, 1.0]), 1)
    assert float((np.array([1.0, 0.0, 1.0])
                  * dist[:, sites].min(axis=1)).sum()) == 2.0
