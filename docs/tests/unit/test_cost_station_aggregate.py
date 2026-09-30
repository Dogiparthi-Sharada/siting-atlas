"""Rolling ZCTA costs up to a station, and the diagnostics that bound them.

The aggregation is arithmetic, so the tests are arithmetic. What they protect
against is the family of errors the pilot runner already sprang once and
documented at `runner.py:156`: averaging medians, dividing a per-stop quantity
by a per-parcel one, and letting a NaN contribute to a denominator but not to
its numerator. Each of those produces a plausible number.

The catchment and floor diagnostics are tested for the property that makes
them useful rather than for a value: shares that sum, counts that agree with a
hand count, and a radius sweep that cannot report a wider ring as denser.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.cost import station_report as rpt
from siting_atlas.cost.station_runner import aggregate_stations


def result(**over) -> pd.DataFrame:
    """Six costed ZCTAs across two stations, values chosen to be checkable."""
    base = {
        "zcta": [f"{i:05d}" for i in range(6)],
        "station_id": ["A", "A", "A", "A", "B", "B"],
        "cost_per_parcel": [1.0, 2.0, 3.0, 4.0, 10.0, 20.0],
        "daily_parcels": [100.0, 100.0, 100.0, 100.0, 50.0, 50.0],
        "daily_stops": [10.0, 20.0, 200.0, 400.0, 5.0, 500.0],
        "daily_cost_usd": [100.0, 200.0, 300.0, 400.0, 500.0, 1000.0],
        "households": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "linehaul_miles": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "stop_density_per_sqmi": [100.0, 200.0, 300.0, 400.0, 10.0, 20.0],
        "metro_label": ["M1"] * 4 + ["M2"] * 2,
    }
    base.update(over)
    return pd.DataFrame(base)


def station_table() -> pd.DataFrame:
    """The metadata `aggregate_stations` joins on."""
    return pd.DataFrame({
        "station_id": ["A", "B"],
        "station_lat": [40.0, 41.0], "station_lon": [-74.0, -75.0],
        "city": ["Newark", "Allentown"], "state": ["NJ", "PA"],
        "cbsa_title": ["New York, NY", None], "status": ["open"] * 2,
        "operator": ["Amazon"] * 2, "facility_type": ["DS"] * 2,
        "station_zcta": ["00000", "00004"]})


# -- aggregation -----------------------------------------------------------

def test_station_median_and_iqr_are_the_quantiles_not_a_mean():
    """A right-skewed catchment must report its middle, not its tail."""
    got = aggregate_stations(result(), station_table()).set_index("station_id")
    assert got.loc["A", "cost_per_parcel_median"] == pytest.approx(2.5)
    assert got.loc["A", "cost_per_parcel_q1"] == pytest.approx(1.75)
    assert got.loc["A", "cost_per_parcel_q3"] == pytest.approx(3.25)
    assert got.loc["A", "cost_per_parcel_iqr"] == pytest.approx(1.5)
    assert got.loc["A", "cost_per_parcel_min"] == pytest.approx(1.0)
    assert got.loc["A", "cost_per_parcel_max"] == pytest.approx(4.0)


def test_station_totals_are_sums_and_counts():
    """ZCTA count, parcels and households roll up by addition."""
    got = aggregate_stations(result(), station_table()).set_index("station_id")
    assert got.loc["A", "zctas"] == 4
    assert got.loc["B", "zctas"] == 2
    assert got.loc["A", "daily_parcels"] == pytest.approx(400.0)
    assert got.loc["B", "households"] == pytest.approx(110.0)


def test_pooled_cost_is_dollars_over_parcels_not_an_average_of_ratios():
    """The only additive cost-per-parcel there is."""
    got = aggregate_stations(result(), station_table()).set_index("station_id")
    assert got.loc["B", "cost_per_parcel_pooled"] == pytest.approx(
        1500.0 / 100.0)


def test_rows_are_sorted_cheapest_first():
    """The table is read top-down as a ranking."""
    got = aggregate_stations(result(), station_table())
    assert list(got["station_id"]) == ["A", "B"]
    assert got["cost_per_parcel_median"].is_monotonic_increasing


def test_station_without_a_cbsa_inherits_its_zctas_modal_metro():
    """Nineteen of the 501 have no CBSA; none may vanish from the by-metro
    table because of it."""
    got = aggregate_stations(result(), station_table()).set_index("station_id")
    assert got.loc["A", "metro"] == "New York, NY"
    assert got.loc["B", "metro"] == "M2"


def test_a_station_with_no_zctas_is_absent_rather_than_zero():
    """20 stations lose every ZCTA to a nearer neighbour. A zero-cost row for
    each would put them at the top of the cheapest list."""
    only_a = result()[result()["station_id"] == "A"]
    got = aggregate_stations(only_a, station_table())
    assert list(got["station_id"]) == ["A"]


# -- decomposition ---------------------------------------------------------

def costed(**over) -> pd.DataFrame:
    """A frame with the four cost components present."""
    base = {
        "cost_service_time": [1.0, 1.0], "cost_vehicle": [0.5, 0.5],
        "cost_drive_time": [0.3, 0.1], "cost_distance": [0.2, 0.4],
        "cost_per_stop": [2.0, 2.0], "daily_stops": [100.0, 300.0],
        "daily_parcels": [140.0, 420.0],
        "daily_cost_usd": [200.0, 600.0], "households": [10.0, 30.0]}
    base.update(over)
    return pd.DataFrame(base)


def test_decomposition_shares_sum_to_one_hundred():
    """The bug this identity replaced summed to 140%."""
    got = rpt.decomposition(costed())
    total = sum(got[f"{k}_share_pct"] for k, _ in rpt.COMPONENTS)
    assert total == pytest.approx(100.0)


def test_decomposition_is_stop_weighted_not_a_plain_mean():
    """The 300-stop row has to count three times as much as the 100-stop
    one. A plain mean of drive time would give 0.20."""
    got = rpt.decomposition(costed())
    assert got["drive_time_usd_per_stop"] == pytest.approx(
        (0.3 * 100 + 0.1 * 300) / 400)


def test_decomposition_drops_incomplete_rows_from_both_sides():
    """A NaN component must not donate doors to the denominator."""
    frame = costed(cost_distance=[0.2, np.nan])
    got = rpt.decomposition(frame)
    assert got["excluded_incomplete_rows"] == 1
    assert got["cost_per_stop"] == pytest.approx(2.0)
    assert got["drive_time_usd_per_stop"] == pytest.approx(0.3)


# -- tour floors -----------------------------------------------------------

def test_tour_floors_count_both_thresholds_independently():
    """5.4% and 1.2% in the pilot; the two are different objections."""
    frame = result()
    got = rpt.tour_floors(frame, stops_per_tour=120, min_points=15)
    # stops are 10, 20, 200, 400, 5, 500
    assert got["below_one_tour"] == 3
    assert got["below_bhh_floor"] == 2
    assert got["below_one_tour_pct"] == pytest.approx(50.0)
    assert got["below_bhh_floor_pct"] == pytest.approx(2 / 6 * 100)


def test_tour_floors_report_household_exposure_not_just_zcta_counts():
    """A count of sparse ZCTAs overstates how much demand is at risk."""
    got = rpt.tour_floors(result(), stops_per_tour=120, min_points=15)
    # households 10 + 20 + 50 below one tour, of 210 total
    assert got["below_one_tour_household_pct"] == pytest.approx(
        80 / 210 * 100)


def test_tour_floors_follow_the_scenarios_own_stops_per_tour():
    """dense_routing runs 150 stops, so its floor is 150, not 120."""
    tight = rpt.tour_floors(result(), stops_per_tour=150, min_points=15)
    assert tight["below_one_tour"] == 3
    assert tight["stops_per_tour"] == pytest.approx(150.0)


# -- radius sweep ----------------------------------------------------------

def sweep_frame(n: int = 40) -> tuple:
    """Concentric ZCTAs: density falls with distance, as in the real data."""
    miles = np.linspace(1.0, 44.0, n)
    frame = pd.DataFrame({
        "households": 4000.0 / miles,
        "land_area_sqmi": [2.0] * n,
        "median_household_income": [75_000.0] * n})
    assigned = pd.DataFrame({"station_id": ["A"] * n,
                             "station_miles": miles})
    return frame, assigned


def test_radius_sweep_is_monotone_in_coverage_and_in_density():
    """Wider rings add households and remove density. If a run ever shows
    otherwise, the assignment is wrong, not the geography."""
    frame, assigned = sweep_frame()
    rows = rpt.radius_sweep(frame, assigned, radii=(5.0, 15.0, 30.0, 45.0))
    assert [r["zctas"] for r in rows] == sorted(r["zctas"] for r in rows)
    shares = [r["household_share_pct"] for r in rows]
    assert shares == sorted(shares)
    dens = [r["median_households_per_sqmi"] for r in rows]
    assert dens == sorted(dens, reverse=True)


def test_radius_sweep_reports_both_densities():
    """Households per sq mi and stops per sq mi are not interchangeable: the
    pilot's published 475 is a stops figure and the two differ ~2.3x."""
    frame, assigned = sweep_frame()
    row = rpt.radius_sweep(frame, assigned, radii=(15.0,))[0]
    ratio = (row["median_households_per_sqmi"]
             / row["median_stops_per_sqmi"])
    assert ratio == pytest.approx(1.4 * 6.0 / 3.2, rel=1e-6)


# -- the cheapest-decile statistics ----------------------------------------

def test_decile_stats_count_the_cheapest_tenth_and_quarter():
    """Ranks are inclusive at the boundary, as the published test was."""
    rows = pd.DataFrame({"pct_rank": [0.05, 0.10, 0.25, 0.26, 0.90],
                         "linehaul_miles": [1.0, 2.0, 3.0, 4.0, 5.0]})
    got = rpt._decile_stats(rows, n_total=6)
    assert got["facilities_matched"] == 5
    assert got["facilities_considered"] == 6
    assert got["in_cheapest_decile"] == 2
    assert got["in_cheapest_quartile_pct"] == pytest.approx(60.0)
    assert got["median_pct_rank"] == pytest.approx(0.25)
    assert got["median_linehaul_miles"] == pytest.approx(3.0)


def test_rank_in_metro_ranks_within_a_metro_not_nationally():
    """A cheap ZCTA in a dear metro must not out-rank the dear metro."""
    frame = pd.DataFrame({
        "zcta": ["a", "b", "c", "d"],
        "metro_label": ["M1", "M1", "M2", "M2"],
        "cost_per_parcel": [1.0, 2.0, 10.0, 20.0],
        "linehaul_miles": [1.0] * 4})
    got = rpt._rank_in_metro(frame)
    assert list(got["pct_rank"]) == pytest.approx([0.5, 1.0, 0.5, 1.0])
