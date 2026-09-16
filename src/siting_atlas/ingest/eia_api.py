"""Acquire regional energy prices from the EIA v2 API.

Feeds the fuel-and-energy capital bucket: warehouse electricity and van fuel.
Both vary by region enough to matter when comparing metros, which is the
whole reason the cost model is metro-specific rather than national.

    python -m siting_atlas.ingest.eia_api

Two series are pulled:
  * industrial retail electricity price, by state, monthly (cents/kWh)
  * No.2 diesel retail price, by PADD region, monthly ($/gal)

State grain maps to ZCTA directly. Diesel is only published at PADD regional
grain, so it is joined through a state-to-PADD table — coarser than the rest
of the model and noted as such.
"""

from __future__ import annotations

import argparse
import json
import os

import pandas as pd

from ..common import config, paths
from ..common.context import init_run
from ..common.http import fetch
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("eia")

BASE = "https://api.eia.gov/v2/{route}/data/"
MAX_ROWS = 5000          # API page limit

# Petroleum Administration for Defense Districts. Diesel is published at this
# grain only, so every state in a district shares one price — a real loss of
# resolution, recorded here rather than hidden in a join.
PADD = {
    "R10": ["CT", "DE", "DC", "FL", "GA", "ME", "MD", "MA", "NH", "NJ", "NY",
            "NC", "PA", "RI", "SC", "VT", "VA", "WV"],
    "R20": ["IL", "IN", "IA", "KS", "KY", "MI", "MN", "MO", "NE", "ND", "OH",
            "OK", "SD", "TN", "WI"],
    "R30": ["AL", "AR", "LA", "MS", "NM", "TX"],
    "R40": ["CO", "ID", "MT", "UT", "WY"],
    "R50": ["AK", "AZ", "CA", "HI", "NV", "OR", "WA"],
}
STATE_TO_PADD = {s: p for p, states in PADD.items() for s in states}


def _key() -> str:
    """EIA API key from the environment, or a RuntimeError saying where to
    get one. Loads .env first so a developer need not export it."""
    config.load_dotenv()
    key = os.environ.get("EIA_API_KEY")
    if not key:
        raise RuntimeError(
            "EIA_API_KEY is not set. Add it to .env at the repo root. "
            "Free key: https://www.eia.gov/opendata/register.php")
    return key


def _pull(route: str, params: dict, label: str) -> pd.DataFrame:
    """Fetch a series in full, following the API's 5,000-row page cap.

    The cap is silent: a request for 5,952 rows returns 5,000 and a 200. Left
    unpaged that quietly truncates the earliest years of the panel, which is
    exactly the kind of defect that never raises and never gets noticed.
    """
    url = BASE.format(route=route)
    rows: list[dict] = []
    offset, total = 0, None

    while True:
        full = {"api_key": _key(), "length": MAX_ROWS, "offset": offset,
                **params}
        got = fetch(url, source=f"eia_{label}", params=full, expect="json")
        body = json.loads(got.path.read_text(encoding="utf-8")).get(
            "response", {})
        page = body.get("data", [])
        total = int(body.get("total", 0) or 0)
        rows.extend(page)
        artefact(got.path, series=label, rows=len(page), offset=offset)

        if not page or len(rows) >= total or len(page) < MAX_ROWS:
            break
        offset += len(page)
        _log.debug("%s paging: %d/%d rows", label, len(rows), total)

    if total and len(rows) != total:
        _log.warning("%s: fetched %d rows, API reported %d", label,
                     len(rows), total)
    else:
        _log.info("%s: %d rows (complete)", label, len(rows))
    return pd.DataFrame(rows)


def electricity(start: str, end: str) -> pd.DataFrame:
    """Industrial retail electricity price by state, monthly."""
    frame = _pull("electricity/retail-sales",
                  {"frequency": "monthly", "data[0]": "price",
                   "facets[sectorid][]": "IND", "start": start, "end": end},
                  "electricity")
    out = pd.DataFrame({
        "state": frame["stateid"],
        "month": pd.to_datetime(frame["period"]),
        "electricity_cents_kwh": pd.to_numeric(frame["price"],
                                               errors="coerce"),
    })
    out["year"] = out["month"].dt.year
    # The API includes US and regional aggregates alongside the states.
    return out[out["state"].str.len() == 2].dropna(
        subset=["electricity_cents_kwh"])


def diesel(start: str, end: str) -> pd.DataFrame:
    """No.2 diesel retail price by PADD region, monthly."""
    frame = _pull("petroleum/pri/gnd",
                  {"frequency": "monthly", "data[0]": "value",
                   "facets[product][]": "EPD2D", "start": start, "end": end},
                  "diesel")
    out = pd.DataFrame({
        "padd": frame["duoarea"],
        "area_name": frame["area-name"],
        "month": pd.to_datetime(frame["period"]),
        "diesel_usd_gal": pd.to_numeric(frame["value"], errors="coerce"),
    })
    out["year"] = out["month"].dt.year
    return out[out["padd"].isin(PADD)].dropna(subset=["diesel_usd_gal"])


def state_energy(start: str, end: str) -> pd.DataFrame:
    """Both series joined to one row per state-month.

    Diesel is regional, so every state in a PADD carries the same value.
    That coarseness is explicit in the ``diesel_grain`` column rather than
    being invisible after the join.
    """
    elec = electricity(start, end)
    fuel = diesel(start, end)
    padd_map = pd.DataFrame({"state": list(STATE_TO_PADD),
                             "padd": list(STATE_TO_PADD.values())})
    merged = (elec.merge(padd_map, on="state", how="left")
                  .merge(fuel[["padd", "month", "diesel_usd_gal"]],
                         on=["padd", "month"], how="left"))
    merged["diesel_grain"] = "padd_region"
    return merged


def main() -> int:
    """CLI entry point: pull both energy series and write one parquet."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2018-01")
    ap.add_argument("--end", default="2025-12")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L0",
                      f"EIA energy prices {args.start}..{args.end}"), \
            step("eia:state_energy"):
            frame = state_energy(args.start, args.end)
            out = paths.INTERIM / "eia_energy.parquet"
            frame.to_parquet(out, index=False)
            artefact(out, rows=len(frame), cols=len(frame.columns))
            metric("eia_state_months", len(frame))
            metric("eia_states", frame["state"].nunique())
            metric("eia_diesel_coverage",
                   f"{frame['diesel_usd_gal'].notna().mean()*100:.1f}%")

            latest = frame[frame["month"] == frame["month"].max()]
            _log.info("latest month %s: electricity %.2f-%.2f cents/kWh "
                      "across %d states",
                      frame["month"].max().date(),
                      latest["electricity_cents_kwh"].min(),
                      latest["electricity_cents_kwh"].max(),
                      len(latest))

    print(f"\n  EIA: {len(frame):,} state-months, "
          f"{frame['state'].nunique()} states -> "
          f"{paths.rel(paths.INTERIM / 'eia_energy.parquet')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
