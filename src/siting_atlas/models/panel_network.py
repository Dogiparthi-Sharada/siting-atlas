"""Time-respecting covariates built from the non-delivery-station network.

What this is
------------
The OCR in `data/interim/mwpvl_facilities.csv` recovered 1,904 Amazon
facilities. Only the small-package delivery stations reached the choice
panel. The rest -- fulfilment centres, sortation centres, inbound cross
docks, heavy/bulky stations, air gateways, fresh DCs -- are a covariate
source no model here has used.

The theory is the parcel flow, not a correlation: a parcel moves
FC -> sortation centre -> delivery station. A delivery station is fed by
the sortation network, so where that network already sits is a
theoretically motivated predictor of where the next station goes.

THE TIME CONSTRAINT, WHICH IS THE WHOLE DESIGN
----------------------------------------------
`docs/research/NOTES_COVARIATE_LEAKAGE.md` records what happens when a
covariate is measured after the decision it is meant to predict: the
warehousing count is lagged off an OSHA bound that is a median 34 months
late, so the facility is plausibly inside its own predictor. Using the
2025 network to score a 2019 siting would be the same failure, larger and
more obvious.

So the network is materialised as VINTAGES, one per year, and a decision
is scored on the latest vintage STRICTLY EARLIER than its own opening
year -- the identical rule `choice.build` already applies to CBP. A
facility with no numeric opening year cannot be placed in time and is
excluded entirely rather than assigned to the earliest or the latest
vintage. The count is reported, not absorbed.

THE THREE COVARIATES, AND WHY THEY TAKE THIS FORM
--------------------------------------------------
`choice.py` enforces ``beta_k = exp(theta_k) > 0``, so every column must
be one where MORE IS MORE ATTRACTIVE, and ``beta'a`` must be positive.
A distance is the wrong sign and unbounded, so distances enter as a
proximity kernel ``1 / (1 + miles)``: strictly decreasing in distance,
strictly positive, and zero in the limit where no such facility exists
yet. It is a strictly monotone transform of the distance, so a tree
benchmark loses nothing by being handed it instead of the raw mileage.

    sortation_proximity    1/(1 + road miles to the nearest sortation
                           centre already open)
    fulfilment_proximity   same, nearest fulfilment centre
    network_within_50mi    count of already-open non-DS US facilities
                           within 50 road miles

THE HONEST COST: AGGREGATION INVARIANCE
---------------------------------------
`MODEL_SPEC.md` §1 buys the ``ln(beta'a)`` form from Train §3.4 Example 2
by requiring every attraction to be EXTENSIVE. A proximity is not; nor is
a radius count, because merging two zones does not sum either. This is
the same cost `models/accessibility.py` declared and switched itself off
over. It is paid here deliberately, and it is the first thing to hold
against any result this module produces.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from ..cost.daganzo import haversine_miles
from .accessibility import CIRCUITY

_log = get_logger("models.panel_network")

#: US tables in the OCR output that are NOT small-package delivery
#: stations. Table 08 is the delivery-station table already in the panel;
#: tables 10 and 11 are rest-of-world and cannot feed a US station.
NON_DS_TABLES = ("01_us_fulfillment_center", "02_us_fresh_dc",
                 "03_us_whole_foods_dc", "04_us_fresh_hub",
                 "05_us_inbound_cross_dock", "06_us_sortation_center",
                 "07_us_air_gateway_hub", "09_us_delivery_heavy_bulky")

SORTATION_TABLE = "06_us_sortation_center"
FULFILMENT_TABLE = "01_us_fulfillment_center"

#: A CHOICE, not a sourced constant, and it is reported as one. The cost
#: model's `default_linehaul_miles` is 25 and describes the LAST-mile leg
#: out of a depot; the sortation-to-station leg is a middle-mile leg and
#: is longer, so 25 is a floor rather than the right number. 50 is twice
#: it. `panel_experiments` runs 25 and 100 as a sensitivity.
COUNT_RADIUS_MILES = 50.0

NETWORK_COLUMNS = ("sortation_proximity", "fulfilment_proximity",
                   "network_within_50mi")

#: Vintages are cut at the CBP floor so the arm with network covariates
#: keeps EXACTLY the decision set of the arm without them -- `build`
#: drops a facility with no vintage strictly earlier than its opening
#: year, and moving the floor would silently change the sample. The
#: ceiling is `mwpvl_shape.YEAR_CEILING`; an opening later than that
#: (the OCR-damaged 2075 and 2094) sees the whole network, which is
#: correct, because the whole network does precede it.
VINTAGE_FIRST = 2017
VINTAGE_LAST = 2030

__all__ = ["COUNT_RADIUS_MILES", "NETWORK_COLUMNS", "NON_DS_TABLES",
           "load_network_facilities", "vintage_table", "augment_cbp"]


def load_network_facilities(mwpvl_path, centroids: pd.DataFrame) -> tuple:
    """Non-DS US facilities that can be placed in SPACE and in TIME.

    ``centroids`` is indexed by ZCTA with latitude/longitude columns. A
    facility needs both a resolvable ZCTA centroid and a numeric opening
    year; anything else is excluded and counted, because a facility that
    cannot be placed in time cannot be held to the time constraint.
    """
    raw = pd.read_csv(mwpvl_path, dtype=str, low_memory=False)
    us = raw[raw["table"].isin(NON_DS_TABLES)].copy()
    us["open_year"] = pd.to_numeric(us["open_year"], errors="coerce")
    us["zcta"] = us["postcode"].astype(str).str.strip().str.zfill(5)
    us = us.join(centroids, on="zcta")

    has_year = us["open_year"].notna()
    has_place = us["latitude"].notna()
    diagnostics = {
        "non_ds_us_rows": int(len(us)),
        "excluded_no_numeric_open_year": int((~has_year).sum()),
        "excluded_postcode_not_a_panel_zcta": int((~has_place).sum()),
        "excluded_either": int((~(has_year & has_place)).sum()),
        "kept": int((has_year & has_place).sum()),
        "by_table": {t: int(((us["table"] == t) & has_year & has_place).sum())
                     for t in NON_DS_TABLES},
        "open_year_after_ceiling": int(
            (us.loc[has_year & has_place, "open_year"] > VINTAGE_LAST).sum()),
    }
    _log.info("network covariates: %d of %d non-DS US facilities placed in "
              "space and time (%d dropped for no numeric open_year, %d for a "
              "postcode that is not a panel ZCTA)",
              diagnostics["kept"], diagnostics["non_ds_us_rows"],
              diagnostics["excluded_no_numeric_open_year"],
              diagnostics["excluded_postcode_not_a_panel_zcta"])
    return us[has_year & has_place].reset_index(drop=True), diagnostics


def _distance_matrix(candidates: pd.DataFrame,
                     facilities: pd.DataFrame) -> np.ndarray:
    """Road-equivalent miles, candidate ZCTA centroid to facility ZCTA."""
    return (haversine_miles(
        candidates["latitude"].to_numpy(float)[:, None],
        candidates["longitude"].to_numpy(float)[:, None],
        facilities["latitude"].to_numpy(float)[None, :],
        facilities["longitude"].to_numpy(float)[None, :]) * CIRCUITY
    ).astype(np.float32)


def vintage_table(candidates: pd.DataFrame, facilities: pd.DataFrame,
                  radius_miles: float = COUNT_RADIUS_MILES) -> pd.DataFrame:
    """One row per (ZCTA, vintage year), network as it stood that year.

    Vintage ``Y`` holds only facilities with ``open_year <= Y``. A
    decision in year ``Y+1`` is scored on it, so every contributing
    facility opened strictly before the decision.
    """
    d = _distance_matrix(candidates, facilities)
    years = facilities["open_year"].to_numpy(float)
    table = facilities["table"].to_numpy()
    zcta = candidates["zcta"].to_numpy()

    frames = []
    for vintage in range(VINTAGE_FIRST, VINTAGE_LAST + 1):
        prior = years <= vintage
        sortation = prior & (table == SORTATION_TABLE)
        fulfilment = prior & (table == FULFILMENT_TABLE)
        frames.append(pd.DataFrame({
            "zcta": zcta,
            "cbp_year": vintage,
            "sortation_proximity": _proximity(d, sortation),
            "fulfilment_proximity": _proximity(d, fulfilment),
            "network_within_50mi": (
                (d[:, prior] <= radius_miles).sum(axis=1).astype(float)
                if prior.any() else np.zeros(len(zcta))),
        }))
    return pd.concat(frames, ignore_index=True)


def _proximity(d: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """1/(1 + miles) to the nearest masked facility; 0 if there is none.

    Zero is the right value for "no such facility exists yet": it is the
    limit of the kernel as distance goes to infinity, so a greenfield
    year and an unreachably distant network are scored consistently
    rather than by a sentinel that the optimiser would read as a level.
    """
    if not mask.any():
        return np.zeros(d.shape[0])
    return 1.0 / (1.0 + d[:, mask].min(axis=1).astype(float))


def augment_cbp(cbp: pd.DataFrame, network: pd.DataFrame,
                extra: tuple[str, ...]) -> pd.DataFrame:
    """CBP vintages extended to `VINTAGE_LAST` and joined to the network.

    CBP publishes 2017-2022. A 2025 decision already takes the 2022
    vintage under `choice.build`'s "latest strictly earlier" rule, so
    carrying 2022 forward into 2023-2030 leaves every warehousing value a
    decision sees UNCHANGED while giving the network covariates the later
    vintages they need. That equality is asserted by the caller rather
    than assumed here.
    """
    last = int(cbp["cbp_year"].max())
    parts = []
    for vintage in range(VINTAGE_FIRST, VINTAGE_LAST + 1):
        source = min(vintage, last)
        slab = cbp.loc[cbp["cbp_year"] == source, ["zcta", *extra]].copy()
        net = network.loc[network["cbp_year"] == vintage,
                          ["zcta", *NETWORK_COLUMNS]]
        merged = slab.merge(net, on="zcta", how="outer")
        merged["cbp_year"] = vintage
        parts.append(merged)
    return pd.concat(parts, ignore_index=True)
