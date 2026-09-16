"""The panel's grain, and the year-over-year join that can fabricate a spike.

Two failures here are worse than a crash because the output stays plausible:

  * a fanned-out join duplicates rows at (zcta, date_id). Every mean is then
    weighted by an accident of the delineation file, and the row count is the
    only symptom.
  * a coverage break in BPS. A county that starts reporting in 2022 has no
    2021 row. If the year-over-year expression treated the missing prior year
    as zero it would report +100% growth — the largest value in the column,
    in exactly the counties where the data is worst. It must be NULL.

The panel is built here from a nine-row fixture through the real
``build_sql``, so the SQL under test is the SQL that ships.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.warehouse import panel

#: county_geoid and county_geoid_2022 are the same outside Connecticut, which
#: is the whole point of carrying both — see warehouse/geo_keys.py.
DIM_ZCTA = [("01890", "25017", "25017", "MA", "Boston", 10.0, 42.45, -71.15),
            ("02135", "25009", "25009", "MA", None, 5.0, 42.35, -71.13)]

FACT_COLS = [
    "zcta", "year", "population", "median_household_income",
    "median_home_value", "median_age", "households", "owner_occupied",
    "renter_occupied", "bachelors_degree", "in_labor_force",
    "vehicle_availability_total", "establishments", "employment",
    "annual_payroll", "median_home_value_topcoded",
    "median_home_value_bottomcoded", "median_household_income_topcoded",
    "median_household_income_bottomcoded",
]


def _interim(name: str, frame: pd.DataFrame) -> None:
    frame.to_parquet(paths.INTERIM / f"{name}.parquet", index=False)


@pytest.fixture
def sources(data_root):
    """Minimal L1 artefacts. Returns a mutator for the permits fixture."""
    _interim("zillow_zori", pd.DataFrame({
        "zcta": ["01890", "01890"],
        "month": pd.to_datetime(["2021-01-15", "2022-01-15"]),
        "rent_index": [1000.0, 1100.0], "year": [2021, 2022],
        "metro": ["Boston"] * 2, "county_name": ["Middlesex"] * 2,
        "state": ["MA"] * 2}))
    _interim("eia_energy", pd.DataFrame({
        "state": ["MA", "MA"],
        "month": pd.to_datetime(["2022-01-15", "2022-04-15"]),
        "electricity_cents_kwh": [20.0, 22.0],
        "diesel_usd_gal": [4.0, 4.4]}))
    _interim("cbsa_county", pd.DataFrame({
        "county_geoid": ["25017", "25009"],
        "county_name": ["Middlesex", "Essex"],
        "cbsa_code": ["14460", "14460"],
        "cbsa_title": ["Boston-Cambridge-Newton"] * 2,
        "csa_title": ["Boston-Worcester-Providence"] * 2,
        "area_type": ["Metropolitan Statistical Area"] * 2,
        "is_metro": [True, True], "county_role": ["Central", "Outlying"]}))
    return _interim


def permits(rows) -> None:
    """rows = [(county_geoid, year, units)]."""
    _interim("building_permits", pd.DataFrame({
        "county_geoid": [r[0] for r in rows],
        "county_name": ["C"] * len(rows),
        "year": [r[1] for r in rows],
        "permit_units_total": [float(r[2]) for r in rows],
        "u1_units": [1] * len(rows), "u5p_units": [0] * len(rows)}))


def build(blocks=()) -> pd.DataFrame:
    con = duckdb.connect(":memory:")
    try:
        con.execute("CREATE TABLE dim_zcta (zcta VARCHAR, county_geoid "
                    "VARCHAR, county_geoid_2022 VARCHAR, state VARCHAR, "
                    "metro VARCHAR, land_area_sqmi "
                    "DOUBLE, latitude DOUBLE, longitude DOUBLE)")
        con.executemany("INSERT INTO dim_zcta VALUES (?,?,?,?,?,?,?,?)",
                        DIM_ZCTA)
        con.execute("CREATE TABLE dim_date AS SELECT CAST(y AS VARCHAR)||'Q'"
                    "||CAST(q AS VARCHAR) AS date_id, y AS year, q AS quarter"
                    " FROM range(2021, 2023) t(y), range(1, 5) u(q)")
        con.execute("CREATE TABLE fact_zcta_year AS SELECT * FROM (VALUES "
                    "('01890',2021,1000,75000,5e5,40,400,200,200,100,600,380,"
                    "50,500,1e6,false,false,false,false),"
                    "('01890',2022,1000,75000,5e5,40,400,200,200,"
                    "100,600,380,50,500,1e6,false,false,false,false)) t("
                    + ",".join(FACT_COLS) + ")")
        con.execute("CREATE TEMP TABLE panel AS " + panel.build_sql(
            list(blocks)))
        return con.execute("SELECT * FROM panel").df()
    finally:
        con.close()


# ---------------------------------------------------------------------------
# grain
# ---------------------------------------------------------------------------
def test_the_panel_is_unique_on_zcta_and_date_id(sources):
    permits([("25017", 2021, 100), ("25017", 2022, 150)])
    frame = build()
    # 2 ZCTAs x 2 years x 4 quarters, dense by construction.
    assert len(frame) == 16
    assert len(frame[["zcta", "date_id"]].drop_duplicates()) == 16


def test_the_grid_is_dense_even_where_no_source_observed_the_zcta(sources):
    """02135 has no rent, no ACS and no permits and must still get 8 rows.

    Filtering to observed rows would hand the model a sample-selection bug,
    because the best-covered sources are the urban ones.
    """
    permits([("25017", 2022, 150)])
    frame = build()
    quiet = frame[frame.zcta == "02135"]
    assert len(quiet) == 8
    assert quiet["rent_index"].isna().all()
    assert (~quiet["rent_observed"]).all()


def test_rent_observed_distinguishes_no_coverage_from_no_rent(sources):
    permits([("25017", 2022, 150)])
    frame = build().set_index(["zcta", "date_id"])
    assert bool(frame.loc[("01890", "2021Q1"), "rent_observed"]) is True
    assert bool(frame.loc[("01890", "2021Q2"), "rent_observed"]) is False
    assert bool(frame.loc[("02135", "2021Q1"), "rent_observed"]) is False


def test_the_target_column_exists_typed_and_null(sources):
    permits([("25017", 2022, 150)])
    frame = build()
    assert "enabled" in frame.columns
    assert frame["enabled"].isna().all()


def test_the_zcta_keeps_its_leading_zero_through_the_whole_panel(sources):
    permits([("25017", 2022, 150)])
    frame = build()
    assert set(frame["zcta"]) == {"01890", "02135"}


# ---------------------------------------------------------------------------
# the year-over-year join — the BPS coverage-break case
# ---------------------------------------------------------------------------
def test_a_county_with_no_prior_year_gets_null_not_a_hundred_percent(sources):
    """25009 first reports in 2022. Its growth is unknown, not +100%.

    COALESCE(prior, 0) here would produce the column's maximum value in the
    counties with the worst data, and a tree would learn "new to BPS" as
    "booming". The CASE WHEN prior > 0 guard is what prevents it.
    """
    permits([("25017", 2021, 100), ("25017", 2022, 150),
             ("25009", 2022, 80)])
    frame = build().set_index(["zcta", "date_id"])

    broken = frame.loc[("02135", "2022Q1")]
    assert broken["permit_units_total"] == 80.0, "the level is still reported"
    assert pd.isna(broken["permits_yoy_pct"]), (
        "a missing prior year must be NULL, not a fabricated spike")

    intact = frame.loc[("01890", "2022Q1")]
    assert intact["permits_yoy_pct"] == pytest.approx(50.0)


def test_a_prior_year_of_zero_gives_null_rather_than_infinity(sources):
    # 0 -> 40 permits is an undefined percentage, and division by zero in
    # DuckDB yields NULL for integers but inf for doubles in some paths; the
    # guard must be explicit.
    permits([("25017", 2021, 0), ("25017", 2022, 40)])
    frame = build().set_index(["zcta", "date_id"])
    assert pd.isna(frame.loc[("01890", "2022Q1"), "permits_yoy_pct"])


def test_the_first_panel_year_has_no_growth_figure(sources):
    permits([("25017", 2021, 100), ("25017", 2022, 150)])
    frame = build()
    first = frame[(frame.year == 2021) & (frame.zcta == "01890")]
    assert first["permits_yoy_pct"].isna().all()


def test_permit_growth_repeats_across_the_four_quarters_of_a_year(sources):
    # BPS is annual; the panel is quarterly. Every quarter of 2022 carries
    # the same annual figure rather than a quarter of it.
    permits([("25017", 2021, 100), ("25017", 2022, 150)])
    frame = build()
    y22 = frame[(frame.year == 2022) & (frame.zcta == "01890")]
    assert y22["permits_yoy_pct"].tolist() == [50.0] * 4
    assert y22["permit_units_total"].tolist() == [150.0] * 4


def test_rent_growth_compares_like_quarter_with_like_quarter(sources):
    permits([("25017", 2022, 150)])
    frame = build().set_index(["zcta", "date_id"])
    # 1000 -> 1100 between 2021Q1 and 2022Q1.
    assert frame.loc[("01890", "2022Q1"), "rent_index_yoy_pct"] == (
        pytest.approx(10.0))
    # Q2 has no observation either year, so no growth figure is invented.
    assert pd.isna(frame.loc[("01890", "2022Q2"), "rent_index_yoy_pct"])


# ---------------------------------------------------------------------------
# fan-out: the grain is not actually defended anywhere
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason=(
    "BUG (unguarded invariant): nothing asserts the panel's grain. A "
    "duplicate (county_geoid, year) in building_permits, or a county listed "
    "twice in cbsa_county, silently multiplies every ZCTA row in that "
    "county. ingest.normalise de-duplicates both today, so the shipped "
    "panel is correct by luck rather than by contract — a publisher shape "
    "change re-introduces it with no error. Fix: after CREATE TABLE panel, "
    "assert COUNT(*) = COUNT(DISTINCT (zcta, date_id)) in warehouse."
    "panel.run()."))
def test_a_duplicate_county_year_in_permits_does_not_fan_out_the_panel(
        sources):
    permits([("25017", 2022, 100), ("25017", 2022, 150)])
    frame = build()
    assert len(frame) == len(frame[["zcta", "date_id"]].drop_duplicates())


def test_coverage_reports_percent_non_null_per_column(sources):
    """The first thing a reviewer looks at, so it must not lie by rounding.

    A column that is 0.4% populated has to read as 0.4, not 0 — 'a bit of
    data' and 'no data' lead to opposite decisions about whether to ship the
    feature.
    """
    con = duckdb.connect(":memory:")
    try:
        con.execute("CREATE TABLE t AS SELECT * FROM (VALUES "
                    "(1, 'a', NULL), (2, NULL, NULL), (3, NULL, NULL)) "
                    "v(full_col, half_col, empty_col)")
        report = {r["column"]: r for r in panel.coverage(
            _LoggedLike(con), "t")}
    finally:
        con.close()

    assert report["full_col"]["pct"] == 100.0
    assert report["half_col"]["non_null"] == 1
    assert report["half_col"]["pct"] == pytest.approx(33.33, abs=0.01)
    assert report["empty_col"]["pct"] == 0.0


class _LoggedLike:
    """The two methods coverage() uses, without a logging sink."""

    def __init__(self, con):
        self._con = con

    def df(self, sql):
        return self._con.execute(sql).df()

    def scalar(self, sql):
        return self._con.execute(sql).fetchone()[0]


def test_the_fan_out_is_silent_when_it_happens(sources):
    """Pins the damage, so the xfail above cannot be closed halfway."""
    permits([("25017", 2022, 100), ("25017", 2022, 150)])
    frame = build()
    doubled = frame[(frame.zcta == "01890") & (frame.date_id == "2022Q1")]
    assert len(doubled) == 2
    # Both rows are individually plausible; only the count gives it away.
    assert sorted(doubled["permit_units_total"]) == [100.0, 150.0]
