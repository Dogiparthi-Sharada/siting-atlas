"""Optional sources: the rule is skip loudly, never guess.

"A missing column is obvious in the coverage report; a wrong join is a
plausible number nobody questions." Everything here defends that sentence.
The bls_wages override exists because an earlier title-based join matched 325
of 708 metros and lost wages in exactly the low-density areas the cost model
needs them — a 54% match rate that raised nothing.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.common.db import LoggedConnection
from siting_atlas.warehouse import optional, panel


@pytest.fixture
def db():
    con = duckdb.connect(":memory:")
    try:
        yield LoggedConnection(con, ":memory:")
    finally:
        con.close()


def put(name: str, frame: pd.DataFrame) -> None:
    frame.to_parquet(paths.INTERIM / f"{name}.parquet", index=False)


# ---------------------------------------------------------------------------
# absence is normal
# ---------------------------------------------------------------------------
def test_an_absent_source_is_skipped_not_fabricated(db, data_root):
    assert optional.block(db, "bls_wages", set()) is None


def test_every_optional_source_is_genuinely_optional(db, data_root):
    # The panel must build with none of them present, or "optional" is a lie
    # and a late ingest track blocks L3.
    assert all(optional.block(db, n, set()) is None
               for n in optional.OPTIONAL_SOURCES)


# ---------------------------------------------------------------------------
# bls_wages: joined on the CBSA code, never on the title
# ---------------------------------------------------------------------------
def test_bls_wages_joins_on_the_cbsa_code_and_pivots_occupations(db,
                                                                 data_root):
    put("bls_wages", pd.DataFrame({
        "area_code": [14460, 14460, 14460, 19100],
        "area_title": ["Boston, MA"] * 3 + ["Dallas, TX"],
        "occ_code": ["00-0000", "53-3033", "53-7062", "53-3033"],
        "annual_mean_wage": [78000.0, 45000.0, 39000.0, 42000.0],
        "total_employment": [2_700_000.0, 20_000.0, 30_000.0, 25_000.0],
        "wage_suppressed": [False, False, True, False]}))

    got = optional.block(db, "bls_wages", set())
    assert "b.cbsa_code" in got["join"], (
        "joining on a metro title loses every renamed metro and every ZCTA "
        "with no Zillow listing")
    assert "area_title" not in got["join"]
    assert "wage_light_truck_driver" in got["names"]

    frame = db.df(f"SELECT * FROM ({got['cte'].split(' AS ', 1)[1][1:-1]})")
    boston = frame[frame.cbsa_code == "14460"].iloc[0]
    # One row per metro after the pivot, not one per occupation.
    assert len(frame) == 2
    assert boston["wage_light_truck_driver"] == 45000.0
    assert boston["wage_all_occupations"] == 78000.0
    # Dallas reports no freight handler; the column must be NULL, not the
    # driver's wage and not zero.
    dallas = frame[frame.cbsa_code == "19100"].iloc[0]
    assert pd.isna(dallas["wage_freight_handler"])
    # BLS suppression is a different fact from "no OES row for this metro",
    # and the panel could not tell them apart until the flag was carried.
    assert bool(boston["wage_suppressed"]) is True
    assert bool(dallas["wage_suppressed"]) is False


def test_the_cbsa_code_is_cast_to_varchar_to_match_the_delineation(db,
                                                                   data_root):
    # BLS ships area_code as an integer and the delineation as a string.
    # An int/varchar join silently matches nothing in DuckDB's strict mode
    # and everything-to-NULL in the LEFT JOIN.
    put("bls_wages", pd.DataFrame({
        "area_code": [14460], "occ_code": ["53-3033"],
        "annual_mean_wage": [45000.0], "total_employment": [20000.0],
        "wage_suppressed": [False]}))
    got = optional.block(db, "bls_wages", set())
    frame = db.df(f"SELECT * FROM ({got['cte'].split(' AS ', 1)[1][1:-1]})")
    assert frame["cbsa_code"].iloc[0] == "14460"
    assert isinstance(frame["cbsa_code"].iloc[0], str)


# ---------------------------------------------------------------------------
# ejscreen: population weighting
# ---------------------------------------------------------------------------
def test_ejscreen_is_population_weighted_not_a_plain_mean(db, data_root):
    put("ejscreen_tract", pd.DataFrame({
        "county_geoid": ["25017", "25017"], "total_pop": [9000.0, 200.0],
        "pm25": [8.0, 20.0], "diesel_pm": [0.3, 0.9],
        "traffic_proximity": [100.0, 900.0], "low_income_pct": [10.0, 60.0],
        "people_of_colour_pct": [20.0, 80.0]}))

    got = optional.block(db, "ejscreen_tract", set())
    frame = db.df(f"SELECT * FROM ({got['cte'].split(' AS ', 1)[1][1:-1]})")
    weighted = (8.0 * 9000 + 20.0 * 200) / 9200
    assert frame["pm25"].iloc[0] == pytest.approx(weighted)
    assert frame["pm25"].iloc[0] != pytest.approx(14.0), (
        "an unweighted mean lets a 200-person tract outvote a 9,000-person "
        "one")


def test_an_unpopulated_county_yields_null_rather_than_a_zero_divide(db,
                                                                     data_root):
    put("ejscreen_tract", pd.DataFrame({
        "county_geoid": ["25017"], "total_pop": [0.0], "pm25": [8.0],
        "diesel_pm": [0.3], "traffic_proximity": [100.0],
        "low_income_pct": [10.0], "people_of_colour_pct": [20.0]}))
    got = optional.block(db, "ejscreen_tract", set())
    frame = db.df(f"SELECT * FROM ({got['cte'].split(' AS ', 1)[1][1:-1]})")
    assert pd.isna(frame["pm25"].iloc[0])


# ---------------------------------------------------------------------------
# the sniffer, for sources with no override
# ---------------------------------------------------------------------------
def test_a_monthly_zcta_source_is_aggregated_to_zcta_year_quarter(db,
                                                                  data_root):
    put("zillow_zhvi", pd.DataFrame({
        "zcta": ["01890", "01890"],
        "month": pd.to_datetime(["2022-01-15", "2022-02-15"]),
        "home_value": [500_000.0, 520_000.0]}))
    got = optional.block(db, "zillow_zhvi", set())
    assert got["names"] == ["home_value"]
    for key in ("zillow_zhvi.zcta = b.zcta", "zillow_zhvi.year = b.year",
                "zillow_zhvi.quarter = b.quarter"):
        assert key in got["join"]
    frame = db.df(f"SELECT * FROM ({got['cte'].split(' AS ', 1)[1][1:-1]})")
    assert len(frame) == 1
    assert frame["home_value"].iloc[0] == pytest.approx(510_000.0)


def test_a_source_with_no_geography_is_skipped(db, data_root):
    put("zillow_zhvi", pd.DataFrame({"region": ["x"], "year": [2022],
                                     "v": [1.0]}))
    assert optional.block(db, "zillow_zhvi", set()) is None


def test_a_source_with_no_time_column_is_skipped(db, data_root):
    put("zillow_zhvi", pd.DataFrame({"zcta": ["01890"], "v": [1.0]}))
    assert optional.block(db, "zillow_zhvi", set()) is None


def test_key_columns_are_never_averaged_as_if_they_were_values(db, data_root):
    # AVG(year) is a number, and it is meaningless. The block must not offer
    # it as a feature.
    put("zillow_zhvi", pd.DataFrame({
        "zcta": ["01890"], "county_geoid": ["25017"], "year": [2022],
        "home_value": [500_000.0]}))
    got = optional.block(db, "zillow_zhvi", set())
    assert got["names"] == ["home_value"]


def test_a_source_never_silently_shadows_a_column_the_panel_already_has(
        db, data_root):
    put("zillow_zhvi", pd.DataFrame({
        "zcta": ["01890"], "year": [2022], "rent_index": [2500.0]}))
    # rent_index already comes from Zillow ZORI; two columns of the same name
    # would make the SELECT ambiguous or, worse, resolve to the wrong one.
    assert optional.block(db, "zillow_zhvi", {"rent_index"}) is None


# ---------------------------------------------------------------------------
# splicing into the panel query
# ---------------------------------------------------------------------------
def test_build_sql_splices_the_cte_columns_and_join(data_root):
    for name in ("zillow_zori", "building_permits", "eia_energy",
                 "cbsa_county"):
        pd.DataFrame({"x": [1]}).to_parquet(
            paths.INTERIM / f"{name}.parquet", index=False)

    sql = panel.build_sql([{"cte": "w AS (SELECT 1 AS cbsa_code, 2 AS wage)",
                            "join": "LEFT JOIN w ON w.cbsa_code = b.cbsa_code",
                            "cols": ["w.wage"], "names": ["wage"]}])
    assert "w AS (SELECT 1 AS cbsa_code, 2 AS wage)" in sql
    assert "w.wage" in sql
    assert "LEFT JOIN w ON w.cbsa_code = b.cbsa_code" in sql
    # The optional join must come after FROM base b, not inside the CTE list.
    assert sql.index("FROM base b") < sql.index("LEFT JOIN w")


def test_build_sql_raises_when_a_required_source_is_missing(data_root):
    with pytest.raises(FileNotFoundError, match="ingest.normalise"):
        panel.build_sql([])
