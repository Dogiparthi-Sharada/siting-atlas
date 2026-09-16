"""L2 — typed parquet becomes a Kimball star schema in DuckDB.

L1 gives one parquet per publisher, each on its own grain (ZCTA, county,
state, month). Nothing can be joined without knowing which. This layer pins
the grains down once:

  * four conformed dimensions — ZCTA, county, quarter, scenario
  * one fact, ``fact_zcta_year``, at ZCTA x year

Everything that follows reads the warehouse, not the parquet, so a grain
mistake is made once here instead of in every model.

``dim_scenario`` carries no data yet. It exists so that a published number
can be traced back to the weight vector, mutation and seed that produced it;
adding the column later would mean rewriting every fact row.

    python -m siting_atlas.warehouse.schema
    python -m siting_atlas.warehouse.schema --show
"""

from __future__ import annotations

import argparse

from ..common import paths
from ..common.config import PANEL_END_YEAR, PANEL_START_YEAR
from ..common.context import init_run
from ..common.db import connect
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.seeds import seed
from ..common.trace import artefact, metric, step, traced_layer
from .geo_keys import ct_zcta_regions, fips_state_sql

_log = get_logger("schema")

TABLES = ("dim_zcta", "dim_county", "dim_date", "dim_scenario",
          "fact_zcta_year")


def _src(name: str) -> str:
    """A read_parquet() call for an L1 artefact, or a hard failure.

    The warehouse has no sensible degraded mode: a missing source silently
    becomes a column of NULLs across a quarter of a million rows.
    """
    path = paths.INTERIM / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{paths.rel(path)} is missing; run ingest.normalise first")
    return f"read_parquet('{path.as_posix()}')"


# ---------------------------------------------------------------------------
# dimensions
# ---------------------------------------------------------------------------
def build_dim_zcta(db) -> None:
    """One row per ZCTA in the 2020 gazetteer — the spine of the panel.

    The gazetteer is authoritative for which ZCTAs exist. CBP knows about
    35,002 ZIP codes, which is more than there are ZCTAs; the extra codes are
    point ZIPs and retired vintages, and joining from the gazetteer outward
    is what keeps them out.

    Two county keys, not one. ``county_geoid`` is the 2020 code the pinned
    ZCTA vintage implies, left exactly as the crosswalk gives it;
    ``county_geoid_2022`` is the same place under the current delineation and
    differs only in Connecticut, which retired its counties in 2022. Keeping
    both makes the correction additive and reversible rather than an edit to
    a key other layers already trust. See ``geo_keys``.
    """
    db.register("ct_regions", ct_zcta_regions(
        db.df(f"SELECT zcta, county_geoid FROM {_src('zcta_county')}"),
        db.df(f"SELECT zcta, county_name FROM {_src('cbp')}")))
    db.execute(f"""
        CREATE OR REPLACE TABLE dim_zcta AS
        SELECT
            g.zcta,
            g.land_area_sqmi,
            g.water_area_sqmi,
            g.latitude,
            g.longitude,
            zc.county_geoid,
            COALESCE(ct.county_geoid_2022, zc.county_geoid)
                AS county_geoid_2022,
            COALESCE(c.state, fips.state_abbr) AS state,
            z.metro
        FROM {_src('gazetteer')} g
        LEFT JOIN {_src('zcta_county')} zc USING (zcta)
        LEFT JOIN {_src('cbp')} c USING (zcta)
        LEFT JOIN ct_regions ct ON ct.zcta = g.zcta
        LEFT JOIN {fips_state_sql()}
               ON fips.state_fips = substr(zc.county_geoid, 1, 2)
        -- Zillow is the only ZCTA-level metro label available; it covers
        -- about a quarter of ZCTAs, so metro is nullable by construction.
        LEFT JOIN (SELECT DISTINCT zcta, metro FROM {_src('zillow_zori')}) z
               ON z.zcta = g.zcta
    """)


def build_dim_county(db) -> None:
    """County names, unioned from the two sources that carry them.

    The permits file names counties for the 3,022 that report to BPS; CBP
    names them per ZIP. Neither alone covers the 3,211 counties the crosswalk
    references, so both are used and BPS wins ties.
    """
    db.execute(f"""
        CREATE OR REPLACE TABLE dim_county AS
        WITH from_cbp AS (
            SELECT DISTINCT zc.county_geoid, c.county_name
            FROM {_src('zcta_county')} zc
            JOIN {_src('cbp')} c USING (zcta)
            WHERE c.county_name IS NOT NULL
        ), from_bps AS (
            SELECT DISTINCT county_geoid, county_name
            FROM {_src('building_permits')}
            WHERE county_name IS NOT NULL
        )
        SELECT
            zc.county_geoid,
            COALESCE(MAX(b.county_name), MAX(k.county_name)) AS county_name
        FROM (SELECT DISTINCT county_geoid FROM {_src('zcta_county')}) zc
        LEFT JOIN from_bps b USING (county_geoid)
        LEFT JOIN from_cbp k USING (county_geoid)
        GROUP BY zc.county_geoid
    """)


def build_dim_date(db) -> None:
    """Quarterly calendar, PANEL_START_YEAR Q1 .. PANEL_END_YEAR Q4.

    Quarter rather than month because the slowest input that actually moves
    (rent) is noisy monthly, and quarter rather than year because a siting
    decision made in Q1 should not see Q4 information.
    """
    db.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        SELECT
            CAST(y AS VARCHAR) || 'Q' || CAST(q AS VARCHAR) AS date_id,
            y AS year,
            q AS quarter
        FROM range(?, ? + 1) AS t(y), range(1, 5) AS u(q)
        ORDER BY year, quarter
    """, [PANEL_START_YEAR, PANEL_END_YEAR])


def build_dim_scenario(db) -> None:
    """Replay key for any published number: weights, mutation, seed.

    Seeded with the single default scenario so facts can reference it from
    day one. Scenario runs append rows; they never edit this one.
    """
    db.execute("""
        CREATE OR REPLACE TABLE dim_scenario (
            scenario_id VARCHAR PRIMARY KEY,
            w_version   VARCHAR,
            mutation_id VARCHAR,
            seed        BIGINT
        )
    """)
    # The seed is read from reproducibility/seeds.toml, not typed here. This
    # row is the replay key for every published number, so a literal in this
    # line would have been the one hardcoded seed in a project whose whole
    # claim is that it has none - and it was: 20240101, matching nothing.
    db.execute(
        "INSERT INTO dim_scenario VALUES ('default', 'w0', 'none', ?)",
        [seed("global", "seed")],
    )


# ---------------------------------------------------------------------------
# fact
# ---------------------------------------------------------------------------
def build_fact_zcta_year(db) -> None:
    """ZCTA x year, one row per ZCTA per panel year — a dense grid.

    Dense, not sparse: a ZCTA with no Zillow index and no permits still gets
    a row with NULLs. A model that only ever sees rows where rent exists
    learns "covered by Zillow" as a feature, and Zillow coverage is urban.

    ACS and CBP are single-vintage and therefore repeat down the years. That
    is deliberate and the vintage is pinned in common.config — it is a level,
    not a trend, and the trend features come from the monthly sources.
    """
    db.execute(f"""
        CREATE OR REPLACE TABLE fact_zcta_year AS
        WITH grid AS (
            SELECT z.zcta, d.year
            FROM dim_zcta z
            CROSS JOIN (SELECT DISTINCT year FROM dim_date) d
        ), rent AS (
            SELECT zcta, year, AVG(rent_index) AS rent_index
            FROM {_src('zillow_zori')}
            GROUP BY zcta, year
        ), energy AS (
            SELECT state, year,
                   AVG(electricity_cents_kwh) AS electricity_cents_kwh,
                   AVG(diesel_usd_gal)        AS diesel_usd_gal
            FROM {_src('eia_energy')}
            WHERE state <> 'US'          -- national row is not a state
            GROUP BY state, year
        )
        SELECT
            g.zcta,
            g.year,
            a.population,
            a.median_household_income,
            a.median_home_value,
            a.median_age,
            a.households,
            a.owner_occupied,
            a.renter_occupied,
            a.bachelors_degree,
            a.in_labor_force,
            a.vehicle_availability_total,
            -- Censoring flags travel WITH the value they describe. Computed
            -- in ingest/census_api.py and dropped here until 2026-09-13,
            -- which left 86 ZCTAs reporting exactly $250,001 of income in
            -- the panel as if that were a measurement. warehouse/flag_gate.py
            -- now fails the build if one goes missing again.
            a.median_home_value_topcoded,
            a.median_home_value_bottomcoded,
            a.median_household_income_topcoded,
            a.median_household_income_bottomcoded,
            c.establishments,
            c.employment,
            c.annual_payroll,
            p.permit_units_total,
            r.rent_index,
            e.electricity_cents_kwh,
            e.diesel_usd_gal
        FROM grid g
        JOIN dim_zcta z USING (zcta)
        LEFT JOIN {_src('acs5_zcta_2023')} a ON a.zcta = g.zcta
        LEFT JOIN {_src('cbp')} c            ON c.zcta = g.zcta
        LEFT JOIN {_src('building_permits')} p
               ON p.county_geoid = z.county_geoid AND p.year = g.year
        LEFT JOIN rent   r ON r.zcta  = g.zcta  AND r.year = g.year
        LEFT JOIN energy e ON e.state = z.state AND e.year = g.year
    """)


BUILDERS = {
    "dim_zcta": build_dim_zcta,
    "dim_county": build_dim_county,
    "dim_date": build_dim_date,
    "dim_scenario": build_dim_scenario,
    "fact_zcta_year": build_fact_zcta_year,   # depends on dim_zcta, dim_date
}


def run() -> dict:
    """Rebuild every table. Idempotent — CREATE OR REPLACE throughout."""
    paths.ensure_dirs()
    counts: dict[str, int] = {}

    with traced_layer("L2", f"star schema -> {paths.rel(paths.WAREHOUSE)}"):
        with connect(paths.WAREHOUSE) as db:
            for name, builder in BUILDERS.items():
                with step(f"build:{name}"):
                    builder(db)
                    counts[name] = db.scalar(f"SELECT COUNT(*) FROM {name}")
                    metric(f"{name}_rows", counts[name])

            orphans = db.scalar("""
                SELECT COUNT(*) FROM dim_zcta WHERE county_geoid IS NULL
            """)
            if orphans:
                _log.warning("%d ZCTAs have no county in the crosswalk",
                             orphans)
        artefact(paths.WAREHOUSE, tables=len(counts))
    return counts


def main() -> int:
    """CLI entry point for L2. Rebuilds every table and prints row counts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show", action="store_true",
                    help="print each table's columns as well as its rows")
    args = ap.parse_args()

    init_run()
    configure()
    counts = run()
    write_json(paths.METRICS / "warehouse_report.json", {"tables": counts})

    print(f"\n  {len(counts)} tables -> {paths.rel(paths.WAREHOUSE)}")
    for name, n in counts.items():
        print(f"    {name:18} {n:>9,} rows")
    if args.show:
        with connect(paths.WAREHOUSE, read_only=True) as db:
            for name in counts:
                cols = db.df(f"DESCRIBE {name}")["column_name"].tolist()
                print(f"\n  {name}\n    {', '.join(cols)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
