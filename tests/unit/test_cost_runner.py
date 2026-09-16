"""L4 driver: picking the pilot slice and ranking it.

The slice is where a silent sample change happens. A ZCTA that falls out of
the crosswalk, or a metro whose CBSA code moved, does not raise — the run
simply costs fewer places and the headline median shifts. So the selection
rules are asserted, not assumed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.cost import runner

CHICAGO, NEW_YORK, NOT_PILOT = "16980", "35620", "99999"


def _panel(rows: list[dict]) -> None:
    defaults = {"year": 2023, "quarter": 4, "households": 1000.0,
                "median_household_income": 75_000.0,
                "land_area_sqmi": 10.0, "latitude": 41.88,
                "longitude": -87.63, "population": 2500.0,
                "wage_light_truck_driver": 45_000.0,
                "diesel_usd_gal": 4.0, "state": "IL",
                "cbsa_code": CHICAGO}
    pd.DataFrame([{**defaults, **r} for r in rows]).to_parquet(
        paths.PANEL, index=False)


@pytest.fixture
def pilot(data_root):
    """A two-county, three-ZCTA pilot. Returns the panel writer."""
    pd.DataFrame({
        "county_geoid": ["17031", "36061", "48001"],
        "county_name": ["Cook", "New York", "Anderson"],
        "cbsa_code": [CHICAGO, NEW_YORK, NOT_PILOT],
        "cbsa_title": ["Chicago", "New York", "Elsewhere"],
        "csa_title": [None, None, None],
        "area_type": ["Metropolitan Statistical Area"] * 3,
        "is_metro": [True] * 3, "county_role": ["Central"] * 3,
    }).to_parquet(paths.INTERIM / "cbsa_county.parquet", index=False)

    pd.DataFrame({
        "zcta": ["60601", "60602", "10001", "75801"],
        "county_geoid": ["17031", "17031", "36061", "48001"],
        "shared_land_area": [1.0] * 4,
    }).to_parquet(paths.INTERIM / "zcta_county.parquet", index=False)
    return _panel


# ---------------------------------------------------------------------------
# pilot_slice
# ---------------------------------------------------------------------------
def test_only_pilot_metro_zctas_are_costed(pilot):
    pilot([{"zcta": z, "county_geoid": c} for z, c in
           [("60601", "17031"), ("10001", "36061"), ("75801", "48001")]])
    frame = runner.pilot_slice(2023, 4)
    # 75801 sits in a CBSA that is not in the pilot registry.
    assert set(frame["zcta"]) == {"60601", "10001"}
    assert set(frame["metro_label"]) == {"Chicago", "New York"}


def test_the_slice_is_pinned_to_one_year_and_quarter(pilot):
    pilot([{"zcta": "60601", "county_geoid": "17031", "year": y, "quarter": q}
           for y in (2022, 2023) for q in (3, 4)])
    frame = runner.pilot_slice(2023, 4)
    assert len(frame) == 1
    assert (frame["year"].iloc[0], frame["quarter"].iloc[0]) == (2023, 4)


def test_an_empty_slice_raises_instead_of_costing_nothing(pilot):
    pilot([{"zcta": "60601", "county_geoid": "17031"}])
    with pytest.raises(ValueError, match="no pilot rows for 2019Q1"):
        runner.pilot_slice(2019, 1)


def test_a_panel_missing_a_required_column_names_it(pilot):
    pilot([{"zcta": "60601", "county_geoid": "17031"}])
    frame = pd.read_parquet(paths.PANEL).drop(columns=["diesel_usd_gal"])
    frame.to_parquet(paths.PANEL, index=False)
    with pytest.raises(KeyError, match="diesel_usd_gal"):
        runner.pilot_slice(2023, 4)


def test_zctas_with_no_households_are_dropped_before_the_model_sees_them(
        pilot):
    """The guard that stops the inf. Without it a household-free ZCTA gets
    stop density 0 and k/sqrt(0) = inf cost."""
    pilot([{"zcta": "60601", "county_geoid": "17031", "households": 1000.0},
           {"zcta": "60602", "county_geoid": "17031", "households": 0.0},
           {"zcta": "10001", "county_geoid": "36061",
            "households": np.nan}])
    frame = runner.pilot_slice(2023, 4)
    assert frame["zcta"].tolist() == ["60601"]


def test_the_slice_index_is_reset_so_the_metro_join_lines_up(pilot):
    # run() joins metro_label back onto the model output by index. A
    # non-contiguous index attaches the wrong metro to every row silently.
    pilot([{"zcta": z, "county_geoid": c} for z, c in
           [("75801", "48001"), ("60601", "17031"), ("10001", "36061")]])
    frame = runner.pilot_slice(2023, 4)
    assert frame.index.tolist() == list(range(len(frame)))


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def test_run_ranks_cheapest_first_and_writes_the_table(pilot):
    pilot([{"zcta": "60601", "county_geoid": "17031",
            "land_area_sqmi": 1.0},        # dense  -> cheap
           {"zcta": "60602", "county_geoid": "17031",
            "land_area_sqmi": 400.0},      # sparse -> dear
           {"zcta": "10001", "county_geoid": "36061",
            "land_area_sqmi": 10.0}])

    report = runner.run(2023, 4, "baseline")
    result = report["result"]

    assert result["rank"].tolist() == [1, 2, 3]
    assert result["cost_per_parcel"].is_monotonic_increasing
    assert result["zcta"].iloc[0] == "60601"
    assert result["zcta"].iloc[-1] == "60602"

    out = paths.TABLES / "cost_to_serve_2023q4_baseline.parquet"
    assert out.exists()
    assert len(pd.read_parquet(out)) == 3


def test_run_reports_the_parameters_that_produced_the_number(pilot):
    pilot([{"zcta": "60601", "county_geoid": "17031"}])
    report = runner.run(2023, 4, "congested")
    # Without this the median is an unattributable number in a JSON file.
    assert report["parameters"]["avg_speed_mph"] == 16.0
    assert report["scenario"] == "congested"
    assert report["zctas"] == 1


def test_a_slower_more_circuitous_scenario_costs_more(pilot):
    pilot([{"zcta": "60601", "county_geoid": "17031"}])
    base = runner.run(2023, 4, "baseline")["median_cost_per_parcel"]
    slow = runner.run(2023, 4, "congested")["median_cost_per_parcel"]
    assert slow > base


def test_the_reported_percentiles_bracket_the_median(pilot):
    pilot([{"zcta": z, "county_geoid": "17031", "land_area_sqmi": a}
           for z, a in [("60601", 1.0), ("60602", 10.0), ("60603", 100.0),
                        ("60604", 400.0)]])
    report = runner.run(2023, 4, "baseline")
    assert report["p10"] <= report["median_cost_per_parcel"] <= report["p90"]
    assert report["total_vans"] >= 1
    assert report["total_daily_cost_usd"] > 0


def test_every_scenario_runs_and_none_produces_a_nan_median(pilot):
    from siting_atlas.cost.params import SCENARIOS
    pilot([{"zcta": "60601", "county_geoid": "17031"},
           {"zcta": "10001", "county_geoid": "36061"}])
    for name in sorted(SCENARIOS):
        report = runner.run(2023, 4, name)
        assert np.isfinite(report["median_cost_per_parcel"]), name
        assert np.isfinite(report["total_daily_cost_usd"]), name
