"""The real-station depot layer: loading, assignment and the line haul.

What is actually at risk here, in the order it would hurt:

1. LOADING THE WRONG ROWS. 192 of the 693 facility rows carry a coordinate
   imputed to the ZCTA centroid. Let one through and that ZCTA's line haul
   collapses towards zero, which is the single most cost-reducing mistake
   available in this module.
2. THE WRONG NEAREST STATION. Assignment is chunked, so an off-by-one in the
   chunk bookkeeping would mis-assign a block of ZCTAs and nothing downstream
   would look wrong.
3. CIRCUITY APPLIED TWICE, OR NOT AT ALL. The parent class applies it to
   measured distances only; the override has to do exactly the same.
4. THE LEAVE-ONE-OUT MASK SILENTLY NOT BITING. If it fails to exclude the
   station in a ZCTA, the cheapest-decile test measures its own circularity
   and reports a finding.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.cost.daganzo import haversine_miles
from siting_atlas.cost.params import BASELINE
from siting_atlas.cost.stations import (
    STATION_FILE,
    StationCostModel,
    StationNetwork,
    catchment,
    load_stations,
)


def stations(**over) -> pd.DataFrame:
    """Three stations on a rough north-south line near New York."""
    base = {"station_id": ["A", "B", "C"],
            "station_lat": [40.0, 41.0, 42.0],
            "station_lon": [-74.0, -74.0, -74.0],
            "station_zcta": ["10001", "10002", "10003"]}
    base.update(over)
    return pd.DataFrame(base)


def zctas(lats, lons=None, codes=None) -> pd.DataFrame:
    """A minimal panel slice: coordinates and a ZCTA code."""
    n = len(lats)
    return pd.DataFrame({
        "zcta": codes or [f"{90000 + i:05d}" for i in range(n)],
        "latitude": lats,
        "longitude": lons if lons is not None else [-74.0] * n})


# -- loading ---------------------------------------------------------------

def test_load_stations_keeps_only_address_level_coordinates():
    """The committed panel must yield exactly the geocoded subset."""
    raw = pd.read_csv(STATION_FILE)
    got = load_stations()
    expected = int((raw["latitude"].notna()
                    & raw["longitude"].notna()).sum())
    assert len(got) == expected
    assert got["station_lat"].notna().all()
    assert got["station_lon"].notna().all()
    # The excluded rows are the ZCTA-centroid fallbacks, and there are some:
    # a run where every row survived would mean the fallback column moved.
    assert len(got) < len(raw)


def test_load_stations_pins_the_published_count():
    """501 of 693. Quoted in the module docstring and in the write-up."""
    assert len(load_stations()) == 501


# -- assignment ------------------------------------------------------------

def test_assign_picks_the_nearest_station():
    """A point just north of B belongs to B, not to A or C."""
    got = StationNetwork(stations()).assign(zctas([41.05]))
    assert got["station_id"].iat[0] == "B"
    assert got["station_miles"].iat[0] == pytest.approx(
        haversine_miles(41.05, -74.0, 41.0, -74.0), rel=1e-9)


def test_assign_is_chunk_invariant():
    """Chunking is bookkeeping; it must not change a single assignment."""
    frame = zctas(list(np.linspace(39.0, 43.0, 97)))
    net = StationNetwork(stations())
    big = net.assign(frame, chunk=1000)
    small = net.assign(frame, chunk=7)
    pd.testing.assert_frame_equal(big, small)


def test_assign_matches_brute_force_on_a_random_cloud():
    """The chunked loop against the obvious O(n*m) answer."""
    rng = np.random.default_rng(20260916)
    frame = zctas(list(rng.uniform(25, 48, 250)),
                  list(rng.uniform(-124, -68, 250)))
    net = StationNetwork(stations(
        station_id=list("ABCDE"),
        station_lat=list(rng.uniform(25, 48, 5)),
        station_lon=list(rng.uniform(-124, -68, 5)),
        station_zcta=["10001", "10002", "10003", "10004", "10005"]))
    got = net.assign(frame, chunk=13)
    d = haversine_miles(frame["latitude"].to_numpy()[:, None],
                        frame["longitude"].to_numpy()[:, None],
                        net.stations["station_lat"].to_numpy()[None, :],
                        net.stations["station_lon"].to_numpy()[None, :])
    assert got["station_miles"].to_numpy() == pytest.approx(d.min(axis=1))
    want = net.stations["station_id"].to_numpy()[d.argmin(axis=1)]
    assert list(got["station_id"]) == list(want)


def test_assign_leaves_a_coordinateless_row_unassigned():
    """No coordinate means no station and NaN miles, never a fallback."""
    got = StationNetwork(stations()).assign(zctas([41.0, np.nan]))
    assert got["station_id"].iat[0] == "B"
    assert pd.isna(got["station_id"].iat[1])
    assert np.isnan(got["station_miles"].iat[1])


def test_assign_preserves_the_caller_index():
    """Results are joined back by index, so it has to survive."""
    frame = zctas([40.0, 41.0, 42.0])
    frame.index = [11, 22, 33]
    assert list(StationNetwork(stations()).assign(frame).index) == [11, 22, 33]


def test_empty_station_table_is_refused():
    """A silent fallback here would price the whole country at 25 miles."""
    with pytest.raises(ValueError, match="no geocoded stations"):
        StationNetwork(stations().iloc[:0])


# -- the leave-one-out mask ------------------------------------------------

def test_exclude_own_zcta_masks_the_station_standing_in_the_zcta():
    """ZCTA 10002 hosts B, so its haul must be measured to A or C."""
    frame = zctas([41.0], codes=["10002"])
    net = StationNetwork(stations())
    plain = net.assign(frame)
    away = net.assign(frame, exclude_own_zcta=True)
    assert plain["station_id"].iat[0] == "B"
    assert plain["station_miles"].iat[0] == pytest.approx(0.0, abs=1e-9)
    assert away["station_id"].iat[0] in {"A", "C"}
    assert away["station_miles"].iat[0] > 60.0


def test_exclude_own_zcta_leaves_other_rows_alone():
    """The mask is per-row; a ZCTA with no station in it must not move."""
    frame = zctas([41.4], codes=["99999"])
    net = StationNetwork(stations())
    pd.testing.assert_frame_equal(net.assign(frame),
                                  net.assign(frame, exclude_own_zcta=True))


def test_unknown_zcta_codes_never_match_each_other():
    """Two missing codes are not the same place. NA == NA would mask a
    station out of a ZCTA it has no relationship with."""
    net = StationNetwork(stations(station_zcta=[None, None, "10003"]))
    frame = zctas([40.0], codes=[None])
    away = net.assign(frame, exclude_own_zcta=True)
    assert away["station_id"].iat[0] == "A"
    assert away["station_miles"].iat[0] == pytest.approx(0.0, abs=1e-9)


# -- catchment -------------------------------------------------------------

def test_catchment_is_inclusive_and_nan_safe():
    """On the boundary is inside; unassignable is outside."""
    assigned = pd.DataFrame({"station_id": ["A", "B", None],
                             "station_miles": [15.0, 15.0001, np.nan]})
    assert list(catchment(assigned, 15.0)) == [True, False, False]


# -- the line-haul override ------------------------------------------------

def cost_frame(n: int = 2) -> pd.DataFrame:
    """A frame `DaganzoCostModel.evaluate` accepts."""
    return pd.DataFrame({
        "zcta": [f"{i:05d}" for i in range(n)],
        "households": [1000.0] * n,
        "median_household_income": [75_000.0] * n,
        "land_area_sqmi": [10.0] * n,
        "latitude": [40.0] * n, "longitude": [-74.0] * n,
        "population": [2500.0] * n,
        "wage_light_truck_driver": [45_000.0] * n,
        "diesel_usd_gal": [4.00] * n})


def test_linehaul_is_great_circle_times_circuity():
    """Exactly the parent's convention: measured miles get circuity."""
    frame = cost_frame(2)
    model = StationCostModel(BASELINE, pd.Series([10.0, 4.0]))
    got = model.linehaul_miles(frame)
    assert list(got) == pytest.approx([10.0 * BASELINE.circuity,
                                       4.0 * BASELINE.circuity])


def test_linehaul_falls_back_without_inflating_the_fallback():
    """The fallback is already a road distance. Inflating it turned the
    documented 25 miles into 32.5 once; it must not happen again."""
    model = StationCostModel(BASELINE, pd.Series([np.nan, 4.0]))
    got = model.linehaul_miles(cost_frame(2))
    assert got.iat[0] == pytest.approx(BASELINE.default_linehaul_miles)


def test_model_refuses_to_run_without_an_assignment():
    """Better a loud failure than a national run at the fallback distance."""
    with pytest.raises(ValueError, match="straight_miles"):
        StationCostModel(BASELINE).linehaul_miles(cost_frame(1))


def test_no_pmedian_is_solved():
    """The point of the module. `evaluate` must not build a DepotNetwork."""
    model = StationCostModel(BASELINE, pd.Series([5.0, 5.0]))
    out = model.evaluate(cost_frame(2))
    assert not hasattr(model, "network")
    assert out["linehaul_miles"].iat[0] == pytest.approx(
        5.0 * BASELINE.circuity)


def test_station_costs_beat_a_distant_depot():
    """Sanity on direction: a nearer station is a cheaper ZCTA."""
    near = StationCostModel(BASELINE, pd.Series([1.0])).evaluate(cost_frame(1))
    far = StationCostModel(BASELINE, pd.Series([40.0])).evaluate(cost_frame(1))
    assert near["cost_per_parcel"].iat[0] < far["cost_per_parcel"].iat[0]
