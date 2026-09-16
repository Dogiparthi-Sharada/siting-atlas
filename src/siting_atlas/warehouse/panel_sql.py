"""L3 SQL — the text of the panel query, split from the code that runs it.

Separated from ``panel.py`` when that module crossed 300 lines. The seam is
the same one ``optional.py`` already uses: this file says what the panel IS,
``panel.py`` orchestrates building it and checks the contracts it has to meet.
"""

from __future__ import annotations

from ..common import paths

__all__ = ["build_sql"]


def _src(name: str) -> str:
    """A read_parquet() call for an L1 artefact, or a hard failure.

    No degraded mode on purpose: a missing source would otherwise become a
    column of NULLs across a million rows, which reads as "this place has
    no data" rather than as "this pipeline was not run".
    """
    path = paths.INTERIM / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{paths.rel(path)} is missing; run ingest.normalise first")
    return f"read_parquet('{path.as_posix()}')"


# ---------------------------------------------------------------------------
# panel SQL
# ---------------------------------------------------------------------------
_BASE_CTES = """
    grid AS (
        -- cbsa_code comes from the OMB delineation, and is the key every
        -- metro-grain source joins on. Titles are revised with each
        -- delineation and a title join silently drops the renamed metros;
        -- codes are stable.
        SELECT z.zcta, d.date_id, d.year, d.quarter,
               -- county_geoid_2022 differs from county_geoid only in
               -- Connecticut and exists so a source on the post-2022
               -- geography can join. Not selected into the panel: it is a
               -- join key, not a fact about the place. See geo_keys.
               z.county_geoid, z.county_geoid_2022, z.state, z.metro,
               c.cbsa_code, c.cbsa_title,
               z.land_area_sqmi, z.latitude, z.longitude
        FROM dim_zcta z
        CROSS JOIN dim_date d
        -- Joined on county_geoid_2022, not county_geoid. The OMB 2023
        -- delineation carries Connecticut as its nine 2022 planning regions
        -- (09110-09190); the legacy 2020 counties (09001-09015) appear
        -- nowhere in it, so the old key matched nothing and left all 288
        -- Connecticut ZCTAs with a NULL cbsa_code and therefore NULL on
        -- every BLS wage column. Safe as a universal key because schema.py
        -- builds it as COALESCE(ct.county_geoid_2022, zc.county_geoid), so
        -- outside Connecticut it IS county_geoid. This is the second half of
        -- the same vintage break that optional.py fixed for EJScreen.
        LEFT JOIN {cbsa} c ON c.county_geoid = z.county_geoid_2022
    ),
    rent_q AS (
        SELECT zcta, year(month) AS year, quarter(month) AS quarter,
               AVG(rent_index) AS rent_index
        FROM {zori} GROUP BY 1, 2, 3
    ),
    rent AS (
        -- Year-on-year against the same quarter, not the previous quarter:
        -- rents are seasonal and a QoQ change would mostly measure summer.
        SELECT r.zcta, r.year, r.quarter, r.rent_index,
               CASE WHEN p.rent_index > 0
                    THEN 100.0 * (r.rent_index - p.rent_index) / p.rent_index
               END AS rent_index_yoy_pct
        FROM rent_q r
        LEFT JOIN rent_q p
               ON p.zcta = r.zcta AND p.year = r.year - 1
              AND p.quarter = r.quarter
    ),
    permits AS (
        SELECT c.county_geoid, c.year, c.permit_units_total,
               CASE WHEN p.permit_units_total > 0
                    THEN 100.0 * (c.permit_units_total - p.permit_units_total)
                         / p.permit_units_total
               END AS permits_yoy_pct
        FROM {bps} c
        LEFT JOIN {bps} p
               ON p.county_geoid = c.county_geoid AND p.year = c.year - 1
    ),
    energy AS (
        SELECT state, year(month) AS year, quarter(month) AS quarter,
               AVG(electricity_cents_kwh) AS electricity_cents_kwh,
               AVG(diesel_usd_gal) AS diesel_usd_gal
        FROM {eia} WHERE state <> 'US' GROUP BY 1, 2, 3
    ),
    base AS (
        SELECT g.*,
               f.population, f.median_household_income, f.median_home_value,
               f.median_age, f.households, f.owner_occupied,
               f.renter_occupied, f.bachelors_degree, f.in_labor_force,
               f.vehicle_availability_total, f.establishments, f.employment,
               f.annual_payroll,
               f.median_home_value_topcoded, f.median_home_value_bottomcoded,
               f.median_household_income_topcoded,
               f.median_household_income_bottomcoded,
               r.rent_index, r.rent_index_yoy_pct,
               p.permit_units_total, p.permits_yoy_pct,
               e.electricity_cents_kwh, e.diesel_usd_gal
        FROM grid g
        LEFT JOIN fact_zcta_year f ON f.zcta = g.zcta AND f.year = g.year
        LEFT JOIN rent    r ON r.zcta = g.zcta AND r.year = g.year
                           AND r.quarter = g.quarter
        LEFT JOIN permits p ON p.county_geoid = g.county_geoid
                           AND p.year = g.year
        LEFT JOIN energy  e ON e.state = g.state AND e.year = g.year
                           AND e.quarter = g.quarter
    )
"""

_BASE_SELECT = """
    b.zcta, b.date_id, b.year, b.quarter,
    b.county_geoid, b.state, b.metro, b.cbsa_code, b.cbsa_title,
    b.land_area_sqmi, b.latitude, b.longitude,
    b.population, b.median_household_income, b.median_home_value,
    b.median_age, b.households, b.owner_occupied, b.renter_occupied,
    b.bachelors_degree, b.in_labor_force, b.vehicle_availability_total,
    b.establishments, b.employment, b.annual_payroll,
    -- ACS interval-censoring flags. $250,001 of income and $2,000,001 of home
    -- value are the Census's top codes and $2,499 / $9,999 its bottom codes:
    -- bounds published as points. COALESCE to FALSE rather than leaving NULL
    -- because "this ZCTA has no ACS row at all" is already carried by the
    -- value column being NULL, and a three-valued boolean is a trap.
    -- cost/daganzo.py should condition on the income pair - see
    -- ingest.census_api.flag_censoring.
    COALESCE(b.median_home_value_topcoded, FALSE)
        AS median_home_value_topcoded,
    COALESCE(b.median_home_value_bottomcoded, FALSE)
        AS median_home_value_bottomcoded,
    COALESCE(b.median_household_income_topcoded, FALSE)
        AS median_household_income_topcoded,
    COALESCE(b.median_household_income_bottomcoded, FALSE)
        AS median_household_income_bottomcoded,
    b.permit_units_total, b.permits_yoy_pct,
    b.rent_index, b.rent_index_yoy_pct,
    -- Zillow publishes a rent index for ~25% of ZCTAs, and those are the
    -- dense urban ones. Without this flag a tree splits on rent_index IS
    -- NULL and learns "no Zillow coverage" as a proxy for "rural" - a
    -- feature about Zillow's publication policy, not about the place.
    -- Made explicit so the model can condition on it and so an imputation
    -- step downstream has something to key off.
    (b.rent_index IS NOT NULL) AS rent_observed,
    b.electricity_cents_kwh, b.diesel_usd_gal
"""


def build_sql(blocks: list[dict]) -> str:
    """Assemble the panel query, with whatever optional sources exist."""
    ctes = _BASE_CTES.format(zori=_src("zillow_zori"),
                             bps=_src("building_permits"),
                             eia=_src("eia_energy"),
                             cbsa=_src("cbsa_county"))
    extra_cte = "".join(",\n    " + b["cte"] for b in blocks)
    extra_sel = "".join(",\n    " + c for b in blocks for c in b["cols"])
    joins = "\n        ".join(b["join"] for b in blocks)
    return f"""
        WITH {ctes.strip()}{extra_cte}
        SELECT {_BASE_SELECT.strip()}{extra_sel},
            -- Target placeholder. The facility panel has not arrived; the
            -- column is typed and NULL so the schema does not shift under
            -- anything already reading the panel.
            CAST(NULL AS BOOLEAN) AS enabled,
            -- Declared here rather than added by facilities.attach for the
            -- same reason: the panel must have one shape whether or not the
            -- target file has landed. TRUE where the quarter this ZCTA was
            -- switched on came from open_quarter.fillna(1) rather than from
            -- a source. 44.2% of the delivered facility rows are undated.
            CAST(NULL AS BOOLEAN) AS open_quarter_imputed
        FROM base b
        {joins}
        ORDER BY b.zcta, b.year, b.quarter
    """
