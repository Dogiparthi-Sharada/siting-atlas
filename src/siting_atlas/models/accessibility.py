"""The line-haul saving from siting a depot in each candidate ZCTA.

What this covariate is for
--------------------------
Adding warehousing establishments took the choice model from 30% to 50% at
top-10, but a single raw covariate matched the fitted model exactly, so the
finding reduced to "Amazon builds where warehouses already are". Warehousing
says where industrial land IS. It says nothing about whether a site is well
placed to serve the demand that is left unserved.

This module computes the second thing, from the cost model the project
already has. For a candidate ZCTA ``c`` in metro ``m``:

    saving(c) = sum_j  parcels_j * max(0, min(d_j_now, CAP) - d(j, c))

where ``d_j_now`` is the distance from ZCTA ``j`` to the nearest depot that
ALREADY EXISTED when the decision was made. It is the demand-weighted
reduction in line haul that opening at ``c`` would buy — exactly the greedy
step of the p-median heuristic in `cost/depots.py`, evaluated one candidate
at a time.

Why this is not another population variable
-------------------------------------------
Two ZCTAs with identical households score very differently if one already
sits next to a station: the first has nothing left to save. The covariate
measures position relative to unserved demand, which is what a location
model is actually about and what a headcount cannot express.

The "already existed" part is doing real work
---------------------------------------------
The prior network is built from the OTHER Amazon facilities in the same metro
with an earlier opening year. That is real data, not a solved optimum, so the
covariate cannot be accused of being our own cost model predicting itself.
It also makes the covariate decision-specific: the same ZCTA is scored
differently for a 2019 decision and a 2024 one, because the network in
between changed.

A facility that is the FIRST in its metro has no prior network, so every
``d_j_now`` is the cap and the formula degenerates gracefully to a
demand-weighted centrality measure — how much of the metro's demand sits
close to this candidate. That is the right answer for a greenfield entry.

The honest cost: aggregation invariance
---------------------------------------
Unlike households or warehousing counts, this is NOT extensive. Merging two
candidate zones does not sum their savings, because a depot at the merged
location serves both differently from a depot at either. So adding it to
``V = ln(beta'a)`` breaks the exact zone-merger invariance that Train
Sec. 3.4 Example 2 buys us. That is a real cost, and it is why this covariate
is OFF by default.

RESULT, 2026-09-14: it adds nothing measurable, and the reason is coverage
-------------------------------------------------------------------------
Fitted alongside households, land area, establishments and warehousing on the
94-decision national frame:

    coefficient            0.0000  (at the positivity boundary)
    McFadden rho-squared   0.1969  -> 0.1969, unchanged to four places
    held out, top 1/5/10   7/16/19 -> 7/16/19, identical
    as a SOLE predictor    top-1 0, top-5 4, top-10 9, against a random
                           1/3/7 -- barely above chance

**But the test was underpowered, and that is the finding.** Of the 100
national facilities, **65 are the first Amazon facility in their metro**, and
only 19 of 62 CBSAs hold more than one. For those 65 decisions the prior
network is empty and the formula degenerates to demand-weighted centrality —
which is a population measure, exactly what this covariate exists to escape.
Its distinctive content was available for 35 decisions, and after a 60/40
split for roughly 14 of them.

So the defensible statement is *"we could not test this properly with this
panel"*, not *"position relative to the existing network does not matter"*.
Distinguishing those two needs more facilities PER METRO, not more metros —
which is precisely what labelling the 362 unclassified OSHA buildings would
buy (see `data/collection/prompts/UNLABELLED_BATCH_*.txt`), and what the NLRB
coverage estimate says we are missing: OSHA sees at most 54% of the cities
with an Amazon facility, and within a city it sees fewer still.

The code is kept, tested and switched off. When the panel densifies, turning
it on is a one-word change and the question becomes answerable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from ..cost.daganzo import haversine_miles

_log = get_logger("models.accessibility")

#: Distance beyond which a ZCTA is treated as unserved by the existing
#: network. Set to the cost model's own `default_linehaul_miles` so the two
#: layers agree on what "far" means; a ZCTA further than this from every
#: depot contributes its full demand to any candidate within the cap.
CAP_MILES = 25.0

#: Straight-line to road. The same factor `cost/params.py` applies, derived
#: rather than cited: L1 over L2 on a grid, averaged over direction, is
#: exactly 4/pi = 1.2732.
CIRCUITY = 1.30

COLUMN = "linehaul_saving"

__all__ = ["CAP_MILES", "COLUMN", "savings_for_metro"]


def savings_for_metro(alts: pd.DataFrame, prior_zctas: list[str],
                      weight: str = "households") -> np.ndarray:
    """Demand-weighted line-haul saving for every candidate in one metro.

    ``alts`` needs ``zcta``, ``latitude``, ``longitude`` and ``weight``.
    ``prior_zctas`` are the ZCTAs of facilities already open in this metro;
    an empty list is the greenfield case.

    Returns one value per row of ``alts``, in parcel-miles saved per day.
    """
    lat = alts["latitude"].to_numpy(float)
    lon = alts["longitude"].to_numpy(float)
    w = alts[weight].to_numpy(float)

    # (n_demand, n_candidate) road distance. The metro is a few hundred rows,
    # so the dense matrix is cheaper than any index.
    d = haversine_miles(lat[:, None], lon[:, None],
                        lat[None, :], lon[None, :]) * CIRCUITY

    if prior_zctas:
        have = alts["zcta"].isin(prior_zctas).to_numpy()
        if have.any():
            current = d[:, have].min(axis=1)
        else:
            # The prior facilities sit in ZCTAs that are not candidates here
            # (dropped for a missing covariate). Treat as greenfield rather
            # than silently pretending the network is empty when it is not.
            _log.debug("prior facilities present but none is a candidate; "
                       "scoring this decision as greenfield")
            current = np.full(len(alts), CAP_MILES)
    else:
        current = np.full(len(alts), CAP_MILES)

    current = np.minimum(current, CAP_MILES)
    # max(0, ...): a candidate further from j than j's existing depot saves
    # nothing for j. Summing a negative would let a badly placed candidate
    # borrow credit from demand it does not serve.
    gain = np.maximum(0.0, current[:, None] - d)
    return (w[:, None] * gain).sum(axis=0)


def attach(alts: pd.DataFrame, prior_zctas: list[str],
           weight: str = "households") -> pd.DataFrame:
    """`alts` with the saving column added. Never mutates its input."""
    out = alts.copy()
    out[COLUMN] = savings_for_metro(alts, prior_zctas, weight)
    return out
