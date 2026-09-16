"""L5 — the summary numbers the dashboard puts above the charts.

Separate from dashboard.py for one reason: a KPI is an arithmetic claim, and
arithmetic that only exists inside a Streamlit callback cannot be tested.
Everything here is a plain function of a DataFrame.

The counting rule worth stating: "servable under $X" counts ZCTAs whose cost
per parcel is at or below the ceiling, and reports the share of daily PARCELS
those ZCTAs carry alongside the share of ZCTAs. Reporting only the ZCTA count
understates the case badly — the cheap ZCTAs are the dense ones, so half the
areas carry roughly two thirds of the volume.

The second rule: aggregate ``van_days`` and round ONCE. ``vans_required`` is
per-ZCTA and already rounded up, and it is documented in cost.daganzo as the
"if this ZCTA had a dedicated van" reading precisely because it may not be
summed. Summing it made every sparse ZCTA contribute a whole van for two
stops a day and overstated the pilot fleet by roughly 1,200 vans — a number
that appeared in a headline tile with no sign that anything was wrong.
"""

from __future__ import annotations

import math

import pandas as pd

RANKED_COLUMNS = ("rank", "zcta", "metro_label", "state", "cost_per_parcel",
                  "cost_per_stop", "stop_density_per_sqmi", "daily_parcels",
                  "daily_stops", "van_days", "daily_cost_usd",
                  "linehaul_miles", "income_imputed")


def summarise(frame: pd.DataFrame, threshold: float) -> dict:
    """Headline numbers for the current filter, in display order."""
    if frame.empty:
        return {"zctas": 0, "median_cost": float("nan"), "under": 0,
                "under_share": 0.0, "parcel_share": 0.0,
                "daily_cost": 0.0, "vans": 0, "parcels": 0.0}

    cost = frame["cost_per_parcel"]
    under = frame[cost <= threshold]
    parcels = frame["daily_parcels"].fillna(0).sum()
    return {
        "zctas": len(frame),
        "median_cost": float(cost.median()),
        "under": len(under),
        "under_share": len(under) / len(frame) * 100.0,
        # Guarded: a filter can select rows whose modelled demand is zero,
        # and a zero denominator here would put "nan%" in a headline tile.
        "parcel_share": (float(under["daily_parcels"].fillna(0).sum())
                         / parcels * 100.0) if parcels > 0 else 0.0,
        "daily_cost": float(frame["daily_cost_usd"].fillna(0).sum()),
        # Sum the fraction, then ceil the total — the same aggregation
        # cost.runner uses for total_vans, so the tile and the printed
        # summary cannot disagree about the size of the fleet.
        "vans": math.ceil(float(frame["van_days"].fillna(0).sum())),
        "parcels": float(parcels),
    }


def filter_frame(frame: pd.DataFrame, metros: list[str]) -> pd.DataFrame:
    """Restrict to the chosen metros, keeping the original cost ranking.

    An empty selection means "all", not "none": a multiselect that has just
    been cleared should show the whole pilot rather than an empty dashboard
    the user has to undo.
    """
    if not metros:
        return frame
    return frame[frame["metro_label"].isin(metros)]


def ranked_table(frame: pd.DataFrame) -> pd.DataFrame:
    """The sortable table view: the columns a reader can act on, in order."""
    cols = [c for c in RANKED_COLUMNS if c in frame.columns]
    return frame[cols].sort_values("cost_per_parcel").reset_index(drop=True)
