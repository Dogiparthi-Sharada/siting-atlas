"""L3 helper — attaching sources whose schema this code has not seen.

Split out of panel.py because it answers a different question. panel.py
defines what the panel *is*; this module deals with the fact that some inputs
arrive on a separate track and may be absent, late, or shaped differently
than expected.

The rule throughout: a source that cannot be joined confidently is skipped
with a warning, never guessed at. A missing column is obvious in the coverage
report; a wrong join is a plausible number nobody questions.

Each source resolves to a block — a CTE, a join clause, and the columns it
contributes — which panel.py splices into its query.
"""

from __future__ import annotations

from ..common import paths
from ..common.logging_setup import get_logger

_log = get_logger("panel.optional")

# Produced by a separate ingest track. Absent is normal, not an error: the
# panel ships without their columns and is rebuilt when they land.
OPTIONAL_SOURCES = ("zillow_zhvi", "bls_wages", "ejscreen_tract")

_NUMERIC = ("BIGINT", "INTEGER", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT",
            "SMALLINT", "TINYINT")
# Never treated as a value to average, whatever their type.
_NOT_A_VALUE = {"zcta", "county_geoid", "state", "year", "quarter", "month",
                "tract", "geoid", "cbsa"}

# Sources whose grain needs a judgement the sniffer cannot make. Anything not
# listed here is shaped key x time and is handled generically.
OVERRIDES = {
    # One row per metro per occupation. Averaging across occupations would
    # produce a number that means nothing, and the three 53-* codes are the
    # freight-handling occupations the cost model actually needs, so the
    # occupation dimension is pivoted out rather than collapsed.
    # Joined on CBSA CODE, not on the metro title. BLS `area_code` is the
    # CBSA code, so the delineation carries it straight to a county and then
    # to a ZCTA. The previous join matched BLS area titles against Zillow's
    # metro strings and landed 325 of 708 - titles are revised with every OMB
    # delineation, and a ZCTA with no Zillow rent listing had no title at all,
    # so wages went missing exactly in the low-density areas the cost model
    # most needs them.
    "bls_wages": {
        "keys": ["cbsa_code"],
        "on": "{a}.cbsa_code = b.cbsa_code",
        "body": """SELECT CAST(area_code AS VARCHAR) AS cbsa_code,
            MAX(total_employment) FILTER (WHERE occ_code = '00-0000')
                AS metro_employment,
            MAX(annual_mean_wage) FILTER (WHERE occ_code = '00-0000')
                AS wage_all_occupations,
            MAX(annual_mean_wage) FILTER (WHERE occ_code = '53-3033')
                AS wage_light_truck_driver,
            MAX(annual_mean_wage) FILTER (WHERE occ_code = '53-7062')
                AS wage_freight_handler,
            MAX(annual_mean_wage) FILTER (WHERE occ_code = '53-1047')
                AS wage_transport_supervisor,
            -- BLS withholds an estimate with '*' and top-codes it with '#'
            -- at >= $239,200/yr; both arrive as NULL, and without this flag
            -- a reader cannot tell "BLS suppressed it" from "this CBSA has
            -- no OES row at all" (540 of 928 do not). ingest/normalise_
            -- external.py computed the flag and the panel then dropped it.
            -- All FALSE in the May-2025 release: 0 of 1,571 rows suppressed.
            BOOL_OR(wage_suppressed) AS wage_suppressed
            FROM {src} GROUP BY 1""",
    },
    # Census tract grain, and no tract-to-ZCTA crosswalk exists in L1. The
    # county is the finest geography both sides share. Weighted by tract
    # population because an unweighted mean lets a 200-person tract count as
    # much as a 9,000-person one when they sit in the same county.
    # Joined on county_geoid_2022, not county_geoid. EJScreen's 2024 tract
    # GEOIDs carry Connecticut's 2022 planning-region codes (09110-09190) and
    # the pinned 2020 ZCTA crosswalk carries the retired county codes
    # (09001-09015), so the join matched nothing for all 288 Connecticut
    # ZCTAs - 46,080 silently NULL cells, invisible because a LEFT JOIN onto
    # a dense spine cannot fail. warehouse/geo_keys.py bridges the vintages.
    "ejscreen_tract": {
        "keys": ["county_geoid"],
        "on": "{a}.county_geoid = b.county_geoid_2022",
        "body": """SELECT county_geoid,
            SUM(pm25 * total_pop) / NULLIF(SUM(total_pop), 0) AS pm25,
            SUM(diesel_pm * total_pop) / NULLIF(SUM(total_pop), 0)
                AS diesel_pm,
            SUM(traffic_proximity * total_pop) / NULLIF(SUM(total_pop), 0)
                AS traffic_proximity,
            SUM(low_income_pct * total_pop) / NULLIF(SUM(total_pop), 0)
                AS low_income_pct,
            SUM(people_of_colour_pct * total_pop) / NULLIF(SUM(total_pop), 0)
                AS people_of_colour_pct
            FROM {src} GROUP BY 1""",
    },
}


def _columns(db, path) -> dict[str, str]:
    """Column name -> DuckDB type for a parquet file, via DESCRIBE.

    Asked of the database rather than of pandas so the types are the ones
    the generated SQL will actually see.
    """
    frame = db.df(f"DESCRIBE SELECT * FROM read_parquet('{path.as_posix()}')")
    return dict(zip(frame["column_name"], frame["column_type"],
                    strict=True))


def _sniff(db, name: str, path, src: str) -> tuple[str, str, list[str]] | None:
    """Infer a key x time aggregation for a source with no override.

    Geography is taken from the finest key present, and the period from
    ``month`` if there is one, otherwise ``year``. Everything numeric that is
    not a key becomes a mean over that period.
    """
    cols = _columns(db, path)
    key = next((k for k in ("zcta", "county_geoid", "state") if k in cols),
               None)
    if key is None:
        _log.warning("optional %-16s no zcta/county_geoid/state column "
                     "(%s) - skipped", name, ", ".join(list(cols)[:6]))
        return None
    if "month" in cols:
        period = ["year(month) AS year", "quarter(month) AS quarter"]
    elif "year" in cols:
        period = ["year"]
    else:
        _log.warning("optional %-16s no month/year column and no override "
                     "- skipped", name)
        return None

    values = [c for c, t in cols.items() if c not in _NOT_A_VALUE
              and any(t.upper().startswith(n) for n in _NUMERIC)]
    group = [key, *period]
    body = (f"SELECT {', '.join(group)}, "
            f"{', '.join(f'AVG({v}) AS {v}' for v in values)} FROM {src} "
            f"GROUP BY {', '.join(str(i + 1) for i in range(len(group)))}")
    on = " AND ".join([f"{name}.{key} = b.{key}", f"{name}.year = b.year"]
                      + ([f"{name}.quarter = b.quarter"]
                         if len(period) == 2 else []))
    return body, on, [key, "year", "quarter"]


def block(db, name: str, taken: set[str]) -> dict | None:
    """Resolve one optional source to a CTE, a join and its columns.

    ``taken`` is the set of column names the panel already has; a source
    never silently shadows an earlier column.
    """
    path = paths.INTERIM / f"{name}.parquet"
    if not path.exists():
        _log.warning("optional %-16s absent - panel omits its columns", name)
        return None

    src = f"read_parquet('{path.as_posix()}')"
    spec = OVERRIDES.get(name)
    if spec:
        body = spec["body"].format(src=src)
        on, keys = spec["on"].format(a=name), spec["keys"]
    else:
        sniffed = _sniff(db, name, path, src)
        if sniffed is None:
            return None
        body, on, keys = sniffed

    # Describe the aggregate rather than restate its output columns, so the
    # two can never drift apart.
    produced = db.df(f"DESCRIBE {body}")["column_name"].tolist()
    values = [c for c in produced if c not in keys and c not in taken]
    if not values:
        _log.warning("optional %-16s adds no new column - skipped", name)
        return None

    _log.info("optional %-16s joined, %d column(s): %s",
              name, len(values), ", ".join(values))
    return {"cte": f"{name} AS ({body})",
            "join": f"LEFT JOIN {name} ON {on}",
            "cols": [f"{name}.{v}" for v in values], "names": values}
