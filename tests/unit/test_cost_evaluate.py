"""End-to-end behaviour of DaganzoCostModel.evaluate().

Two classes of failure are covered:

1. Conflating a parcel with a stop. Service time is paid once per door, so
   charging it per parcel overstates the cost of exactly the dense ZCTAs the
   ranking exists to identify as cheap. The output stays finite and ordered,
   so nothing catches it downstream.
2. Degenerate inputs. A zero or missing land area, a ZCTA with no households
   and a missing median income all occur in the real panel. Each must produce
   a value the caller can see, not an inf that sorts to the end of the
   ranking and poisons a mean.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd
import pytest

from siting_atlas.cost.daganzo import DaganzoCostModel
from siting_atlas.cost.params import BASELINE

COST_COLS = ("cost_distance", "cost_drive_time", "cost_service_time",
             "cost_vehicle", "cost_per_stop", "cost_per_parcel")


def frame(n: int = 1, **over) -> pd.DataFrame:
    """One well-formed ZCTA. Tests override one column to break it."""
    base = {"zcta": [f"{i:05d}" for i in range(n)],
            "households": [1000.0] * n,
            "median_household_income": [75_000.0] * n,
            "land_area_sqmi": [10.0] * n,
            "latitude": [40.0] * n, "longitude": [-74.0] * n,
            "population": [2500.0] * n,
            "wage_light_truck_driver": [45_000.0] * n,
            "diesel_usd_gal": [4.00] * n}
    for key, value in over.items():
        base[key] = value if isinstance(value, list) else [value] * n
    return pd.DataFrame(base)


def evaluate(params=BASELINE, **over) -> pd.DataFrame:
    rows = max((len(v) for v in over.values() if isinstance(v, list)),
               default=1)
    return DaganzoCostModel(params).evaluate(frame(rows, **over))


# ---------------------------------------------------------------------------
# parcels are not stops
# ---------------------------------------------------------------------------
def test_cost_per_parcel_is_cost_per_stop_divided_by_parcels_per_stop():
    """The identity that was actually broken once. Locked down exactly.

    Every cost component is accrued per STOP. Reporting the same number as a
    cost per parcel overstates unit cost by 40% at the baseline consolidation
    rate, and the error is invisible because both figures are plausible.
    """
    out = evaluate()
    assert out["cost_per_parcel"].iloc[0] == pytest.approx(
        out["cost_per_stop"].iloc[0] / BASELINE.parcels_per_stop, rel=1e-12)
    assert out["cost_per_parcel"].iloc[0] < out["cost_per_stop"].iloc[0]


def test_the_four_components_sum_to_cost_per_stop_not_cost_per_parcel():
    # The report prints component shares. If they are divided by cost per
    # parcel the shares sum to 140% — which is what happened.
    out = evaluate().iloc[0]
    parts = sum(out[c] for c in ("cost_distance", "cost_drive_time",
                                 "cost_service_time", "cost_vehicle"))
    assert parts == pytest.approx(out["cost_per_stop"], rel=1e-12)
    assert parts != pytest.approx(out["cost_per_parcel"])


def test_stops_are_parcels_consolidated_by_the_consolidation_rate():
    out = evaluate()
    assert out["daily_stops"].iloc[0] == pytest.approx(
        out["daily_parcels"].iloc[0] / BASELINE.parcels_per_stop)
    # 1000 households x 3.2 parcels/week / 6 delivery days = 533.33 parcels.
    assert out["daily_parcels"].iloc[0] == pytest.approx(1000 * 3.2 / 6.0)


def test_service_time_is_charged_per_door_not_per_parcel():
    """Doubling the number of parcels left at one door must not double the
    time spent standing at it. If it does, dense ZCTAs are penalised."""
    one = evaluate(dataclasses.replace(BASELINE, parcels_per_stop=1.0))
    two = evaluate(dataclasses.replace(BASELINE, parcels_per_stop=2.0))
    assert (one["cost_service_time"].iloc[0]
            == pytest.approx(two["cost_service_time"].iloc[0]))


def test_daily_cost_multiplies_the_per_stop_cost_by_stops():
    out = evaluate().iloc[0]
    assert out["daily_cost_usd"] == pytest.approx(
        out["cost_per_stop"] * out["daily_stops"])
    # and equivalently by parcels, which is the cross-check that the two
    # denominators have not drifted apart.
    assert out["daily_cost_usd"] == pytest.approx(
        out["cost_per_parcel"] * out["daily_parcels"])


def test_vans_required_rounds_up():
    # 380.95 stops at 120 per tour is 3.17 vans; you cannot hire 0.17 of a
    # van, and rounding down under-provisions every ZCTA in the network.
    out = evaluate().iloc[0]
    assert out["vans_required"] == math.ceil(out["daily_stops"] / 120)
    assert out["vans_required"] == 4.0


# ---------------------------------------------------------------------------
# monotonicity — the shape of the answer
# ---------------------------------------------------------------------------
def test_cost_is_strictly_decreasing_in_density():
    # Same demand, shrinking land area => rising stop density.
    out = evaluate(land_area_sqmi=[400.0, 100.0, 25.0, 5.0, 1.0])
    density = out["stop_density_per_sqmi"].tolist()
    cost = out["cost_per_parcel"].tolist()
    assert density == sorted(density), "fixture is not ordered by density"
    assert cost == sorted(cost, reverse=True), (
        "cost must fall as density rises — this is the whole siting argument")
    assert all(b < a for a, b in zip(cost, cost[1:], strict=False))


def test_cost_is_strictly_increasing_in_linehaul_distance():
    costs = [
        DaganzoCostModel(dataclasses.replace(
            BASELINE, default_linehaul_miles=d)).evaluate(
                frame())["cost_per_parcel"].iloc[0]
        for d in (5.0, 25.0, 60.0, 120.0)]
    assert costs == sorted(costs)
    assert all(b > a for a, b in zip(costs, costs[1:], strict=False))


def _cost_at_linehaul(miles: float) -> float:
    return DaganzoCostModel(
        dataclasses.replace(BASELINE, default_linehaul_miles=miles)
    ).evaluate(frame())["cost_per_parcel"].iloc[0]


def test_a_ten_mile_linehaul_error_costs_about_seventeen_cents_a_parcel():
    """The depot is a PROXY, so how much it can move the answer matters.

    ``linehaul_miles`` documents this as "a ten-mile error moves cost per
    parcel by well under a cent". It does not. At C=120 a mile of line haul
    adds 2/120 = 0.0167 miles per stop, and a mile costs $0.48 in fuel and
    wear plus $0.96 in driver time at 22 mph — about $0.024 per stop, i.e.
    $0.017 per parcel. Ten miles is therefore ~$0.17, roughly 12% of the
    $1.40 baseline, not "well under a cent".

    The number is pinned here because the proxy's error budget is an
    argument the reader is asked to accept on the strength of that sentence.
    """
    per_mile = _cost_at_linehaul(26.0) - _cost_at_linehaul(25.0)
    assert per_mile == pytest.approx(0.0171, abs=5e-4)
    ten = _cost_at_linehaul(35.0) - _cost_at_linehaul(25.0)
    assert ten == pytest.approx(0.171, abs=5e-3)
    assert ten > 0.01, ("the docstring's error budget is wrong by ~20x; a "
                        "bad depot moves the ranking materially")
    assert ten / _cost_at_linehaul(25.0) > 0.10


def test_line_haul_can_outweigh_a_large_density_advantage():
    """Follows from the test above and is the reason it matters.

    A 400x density advantage saves ~0.72 miles per stop. A 55-mile line-haul
    penalty adds ~0.92. So a very dense ZCTA far from the proxy depot ranks
    WORSE than a very sparse one next to it — the ranking is then driven by
    the weakest input in the model rather than the strongest.
    """
    dense_far = DaganzoCostModel(
        dataclasses.replace(BASELINE, default_linehaul_miles=60.0)
    ).evaluate(frame(land_area_sqmi=1.0))["cost_per_parcel"].iloc[0]
    sparse_near = DaganzoCostModel(
        dataclasses.replace(BASELINE, default_linehaul_miles=5.0)
    ).evaluate(frame(land_area_sqmi=400.0))["cost_per_parcel"].iloc[0]
    assert dense_far > sparse_near


def test_higher_wages_and_fuel_both_raise_cost():
    out = evaluate(wage_light_truck_driver=[45_000.0, 60_000.0])
    assert out["cost_per_parcel"].iloc[1] > out["cost_per_parcel"].iloc[0]
    out = evaluate(diesel_usd_gal=[3.00, 6.00])
    assert out["cost_per_parcel"].iloc[1] > out["cost_per_parcel"].iloc[0]


# ---------------------------------------------------------------------------
# degenerate inputs
# ---------------------------------------------------------------------------
def test_missing_income_falls_back_to_the_reference_and_is_flagged():
    out = evaluate(median_household_income=[np.nan, 75_000.0])
    assert out["income_imputed"].tolist() == [True, False]
    # The fallback must be neutral: scale factor 1.0, identical demand.
    assert out["daily_parcels"].iloc[0] == pytest.approx(
        out["daily_parcels"].iloc[1])
    assert not out[list(COST_COLS)].isna().any().any()


def test_income_moves_demand_in_the_right_direction():
    out = evaluate(median_household_income=[37_500.0, 75_000.0, 150_000.0])
    p = out["daily_parcels"].tolist()
    assert p[0] < p[1] < p[2]
    # elasticity 0.35: doubling income raises volume by 2**0.35 = 1.27x, well
    # short of proportional.
    assert p[2] / p[1] == pytest.approx(2.0 ** 0.35, rel=1e-9)


@pytest.mark.parametrize("land", [0.0, np.nan, -1.0])
def test_bad_land_area_yields_nan_and_never_inf(land):
    """Land area is 0 for a handful of real ZCTAs and NaN where the
    gazetteer join misses. An inf here sorts to one end of the ranking and
    silently drags any mean or sum with it; NaN at least propagates as
    'unknown' and is visible in a coverage report."""
    out = evaluate(land_area_sqmi=land)
    assert np.isnan(out["stop_density_per_sqmi"].iloc[0])
    assert not np.isinf(out[list(COST_COLS)].to_numpy(dtype=float)).any()
    assert np.isnan(out["cost_per_parcel"].iloc[0])


def test_a_nan_cost_is_silently_dropped_from_the_aggregate():
    """Documents the consequence of the NaN above, which is the dangerous
    half: pandas .sum() skips NaN, so one un-costed ZCTA quietly shrinks the
    reported network cost instead of raising."""
    out = evaluate(land_area_sqmi=[10.0, 0.0])
    assert out["daily_cost_usd"].isna().sum() == 1
    assert out["daily_cost_usd"].sum() == pytest.approx(
        out["daily_cost_usd"].iloc[0])


@pytest.mark.xfail(strict=True, reason=(
    "BUG: a ZCTA with zero households gives stop_density = 0, so "
    "k/sqrt(0) = inf and cost_per_parcel is inf. cost.runner filters "
    "households > 0 before calling evaluate(), but the model itself has no "
    "guard, so any other caller (a sensitivity sweep, a notebook, the "
    "optimiser) gets inf with no warning. Guard belongs in stop_density()."))
def test_zero_households_does_not_produce_an_infinite_cost():
    out = evaluate(households=0.0)
    assert not np.isinf(out["cost_per_parcel"].iloc[0])


def test_zero_households_today_produces_inf_and_a_nan_daily_cost():
    """Pins the current behaviour so the xfail above cannot be 'fixed' by
    accident into something equally wrong."""
    out = evaluate(households=0.0).iloc[0]
    assert np.isinf(out["cost_per_parcel"])
    assert np.isnan(out["daily_cost_usd"]), "inf * 0 stops = NaN"


def test_evaluate_does_not_mutate_its_input():
    src = frame(3)
    before = src.copy(deep=True)
    DaganzoCostModel(BASELINE).evaluate(src)
    pd.testing.assert_frame_equal(src, before)


def test_evaluate_preserves_the_row_index_for_joining_back():
    # runner.run() joins metro_label back on by position; a reset or reordered
    # index would attach the wrong metro to every row without raising.
    src = frame(4)
    src.index = [10, 11, 12, 13]
    out = DaganzoCostModel(BASELINE).evaluate(src)
    assert out.index.tolist() == [10, 11, 12, 13]
    assert out["zcta"].tolist() == src["zcta"].tolist()
