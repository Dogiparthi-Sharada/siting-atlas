"""What a portfolio of activated ZCTAs is worth, and why it is not separable.

The margin problem, and how it is dodged
----------------------------------------
Nobody outside the operator knows the contribution margin per parcel. Quoting
an NPV in dollars would therefore be quoting an assumption. So value is kept
linear in the unknown margin `m`:

    NPV_i(m)  =  a_i * m  -  b_i

where a_i is annual parcels and b_i is annual cost to serve. Setting it to
zero gives the break-even margin:

    m*_i  =  b_i / a_i  =  cost per parcel

That identity is the useful part. "This ZIP pays for itself at $1.12 a parcel"
is a claim the operator can check against a number they alone possess, and it
is falsifiable without ever guessing their P&L. A dollar NPV would not be.

Why the portfolio is not just the sum of the parts
--------------------------------------------------
Two adjacent ZCTAs activated together do not deliver the sum of their volumes.
They share drivers, share line haul, and cannibalise each other's demand:

  * SHARED LINE HAUL is a positive interaction — one trip out of the depot
    serves both, so the second is cheaper because the first was chosen.
  * CANNIBALISATION is a negative interaction — overlapping catchments split
    the same customers.

A set function with both positive and negative interactions is neither
submodular nor supermodular, so the classic (1 - 1/e) greedy guarantee does
NOT apply. Anyone claiming that bound here is wrong. What can honestly be
reported is an achieved objective plus a computed upper bound, hence the gap
in `select.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from ..cost.daganzo import haversine_miles
from .params import PortfolioParameters

_log = get_logger("optimize.objective")

#: Re-exported: callers have always imported it from here, and
#: moving a name is not worth breaking them over.
__all__ = ["PortfolioObjective", "PortfolioParameters"]


class PortfolioObjective:
    """Evaluates the value of a set of activated ZCTAs.

    Holds the precomputed neighbour structure so repeated evaluation inside a
    search loop is cheap — building it per call would dominate the runtime.
    """

    def __init__(self, frame: pd.DataFrame, panel: pd.DataFrame,
                 params: PortfolioParameters | None = None):
        """Precompute the per-ZCTA annual flows and the neighbour matrix.

        ``frame`` is a cost-to-serve table from :mod:`siting_atlas.cost`, one
        row per candidate ZCTA; ``panel`` supplies latitude and longitude and
        need only be unique on ``zcta``. Constructed rather than defaulted in
        the signature: a dataclass instance written as a default argument is
        built once at import and then shared by every caller for the life of
        the process.
        """
        self.params = params if params is not None else PortfolioParameters()
        self.frame = frame.reset_index(drop=True)
        self.n = len(self.frame)

        coords = panel.set_index("zcta")[["latitude", "longitude"]]
        coords = coords.reindex(self.frame["zcta"])
        self.lat = coords["latitude"].to_numpy(float)
        self.lon = coords["longitude"].to_numpy(float)

        days = self.params.delivery_days_per_year
        self.annual_parcels = (
            self.frame["daily_parcels"].to_numpy(float) * days)
        self.annual_cost = self.frame["daily_cost_usd"].to_numpy(float) * days
        self.breakeven = self.frame["cost_per_parcel"].to_numpy(float)
        # Line-haul share of cost, the part a neighbour can help pay for. It
        # is a share of the MILEAGE-driven cost, not of total cost: service
        # time at the door and the van lease are paid whatever route the van
        # drove, so scaling the whole cost by the line-haul share of miles
        # made the shareable pool 2.9x too large on the pilot and let the
        # optimiser over-credit clustering.
        share = (self.frame["linehaul_miles_per_stop"]
                 / self.frame["miles_per_stop"].replace(0, np.nan))
        self.linehaul_cost = (self.annual_cost
                              * share.fillna(0).to_numpy(float)
                              * self._mileage_cost_share())

        self._interaction = self._build_interaction()

    def _mileage_cost_share(self) -> np.ndarray:
        """Fraction of cost per stop that moves with distance travelled.

        Fuel, wear and paid driving time scale with miles; service time and
        the van lease do not. Returns all-ones when the cost components are
        absent, which is the case for the synthetic frames the tests build —
        there the distinction does not exist and the old behaviour is right.
        """
        need = ("cost_distance", "cost_drive_time", "cost_per_stop")
        if not all(c in self.frame.columns for c in need):
            return np.ones(self.n, dtype=float)
        driven = self.frame["cost_distance"] + self.frame["cost_drive_time"]
        total = self.frame["cost_per_stop"].replace(0, np.nan)
        # A zero or missing total means there is no cost to share anyway, so
        # zero is the conservative fill rather than one.
        return (driven / total).fillna(0.0).to_numpy(float)

    def _build_interaction(self) -> np.ndarray:
        """Pairwise proximity weight, 1 at zero distance and 0 at the radius.

        Dense N x N. At the pilot's ~2,300 ZCTAs that is 42 MB, which is fine;
        a national run would need a sparse neighbour list instead, and this is
        the line that would have to change.
        """
        radius_miles = self.params.cannibalisation_radius_km * 0.621371
        d = haversine_miles(self.lat[:, None], self.lon[:, None],
                            self.lat[None, :], self.lon[None, :])
        w = np.clip(1.0 - d / radius_miles, 0.0, 1.0)
        np.fill_diagonal(w, 0.0)
        _log.debug("interaction matrix %dx%d, mean neighbours within %.0f km: "
                   "%.1f", self.n, self.n,
                   self.params.cannibalisation_radius_km,
                   float((w > 0).sum(axis=1).mean()))
        return w

    # -- valuation -------------------------------------------------------
    def evaluate(self, selected: np.ndarray) -> dict:
        """Value a boolean selection mask.

        Returns the portfolio's annual parcels, cost and break-even margin.
        Because margin is unknown, "value" IS the break-even margin: a lower
        one is a better portfolio, and it can be compared against whatever
        figure the operator actually has.
        """
        p = self.params
        sel = np.asarray(selected, dtype=bool)
        if not sel.any():
            # Every key the populated branch returns, so a caller cannot
            # KeyError its way out of the empty case. An empty portfolio costs
            # nothing and earns nothing, so its NPV is exactly zero at any
            # margin — which is the value the stopping rule compares against.
            return {"n": 0, "parcels": 0.0, "cost": 0.0, "capital": 0.0,
                    "npv_per_dollar_margin": 0.0, "npv_fixed": 0.0,
                    "breakeven_margin": float("inf")}

        # Exposure: how much active neighbour there is around each ZCTA.
        exposure = self._interaction[:, sel].sum(axis=1)

        decay = -np.expm1(-exposure)          # 1 - exp(-e), saturating at 1
        parcels = self.annual_parcels * (1.0 - p.cannibalisation_peak * decay)
        cost = (self.annual_cost
                - self.linehaul_cost * p.linehaul_sharing * decay)

        tot_parcels = float(parcels[sel].sum())
        tot_cost = float(cost[sel].sum())
        capital = float(sel.sum()) * p.capital_per_activation_usd

        # NPV(m) = m * A - B - K, with A and B discounted over the horizon.
        a = tot_parcels * p.annuity_factor
        b = tot_cost * p.annuity_factor + capital
        return {"n": int(sel.sum()),
                "parcels": tot_parcels,
                "cost": tot_cost,
                "capital": capital,
                "npv_per_dollar_margin": a,
                "npv_fixed": -b,
                # The margin per parcel at which this portfolio breaks even.
                "breakeven_margin": b / a if a > 0 else float("inf")}

    def marginal_breakeven(self, selected: np.ndarray) -> float:
        """Break-even margin of one selection. Convenience over evaluate()."""
        return self.evaluate(selected)["breakeven_margin"]

    def exposure(self, selected: np.ndarray) -> np.ndarray:
        """Active-neighbour weight around every ZCTA, given a selection."""
        return self._interaction[:, np.asarray(selected, bool)].sum(axis=1)

    def _batch_totals(self, selected, exposure, candidates, block):
        """Yield (slice, A, B) for `selected + {c}` over candidate blocks.

        Calling ``evaluate`` once per candidate re-derives the whole exposure
        vector each time, which made greedy O(picks x candidates x n) and took
        ten minutes on the pilot. Adding a candidate only shifts exposure by
        one column of the interaction matrix, so the sweep collapses to array
        arithmetic.

        The second optimisation is what makes it fast rather than merely
        vectorised: only the ALREADY-SELECTED rows and the candidate's own row
        contribute to a portfolio total. Building the intermediate over all n
        ZCTAs did far more arithmetic than necessary, because the unselected
        rows were multiplied, summed, and then masked away.

        Both batched scorers share this kernel so they cannot disagree about
        what a portfolio is worth.
        """
        p = self.params
        sel = np.asarray(selected, bool)
        cand = np.asarray(candidates, int)
        rows = np.flatnonzero(sel)

        a_sel = self.annual_parcels[rows, None]
        c_sel = self.annual_cost[rows, None]
        l_sel = self.linehaul_cost[rows, None]
        e_sel = exposure[rows, None]
        capital = (rows.size + 1) * p.capital_per_activation_usd

        # The candidate's own row. Its exposure is unchanged by adding itself,
        # because the interaction matrix has a zero diagonal.
        dec_c = -np.expm1(-exposure[cand])
        p_cand = self.annual_parcels[cand] * (
            1.0 - p.cannibalisation_peak * dec_c)
        c_cand = (self.annual_cost[cand]
                  - self.linehaul_cost[cand] * p.linehaul_sharing * dec_c)

        for begin in range(0, len(cand), block):
            chunk = cand[begin:begin + block]
            if rows.size:
                e = e_sel + self._interaction[np.ix_(rows, chunk)]
                decay = -np.expm1(-e)
                tot_p = (a_sel * (1.0 - p.cannibalisation_peak
                                  * decay)).sum(axis=0)
                tot_c = (c_sel - l_sel * p.linehaul_sharing
                         * decay).sum(axis=0)
            else:
                tot_p = np.zeros(len(chunk))
                tot_c = np.zeros(len(chunk))

            tot_p = tot_p + p_cand[begin:begin + block]
            tot_c = tot_c + c_cand[begin:begin + block]

            yield (slice(begin, begin + block),
                   tot_p * p.annuity_factor,
                   tot_c * p.annuity_factor + capital)

    def batch_breakeven(self, selected: np.ndarray, exposure: np.ndarray,
                        candidates: np.ndarray,
                        block: int = 256) -> np.ndarray:
        """Break-even margin for `selected + {c}`, for every candidate c."""
        out = np.empty(len(candidates), dtype=float)
        for where, a, b in self._batch_totals(selected, exposure,
                                              candidates, block):
            with np.errstate(divide="ignore", invalid="ignore"):
                out[where] = np.where(a > 0, b / a, np.inf)
        return out

    def npv(self, selected: np.ndarray, margin: float) -> float:
        """Portfolio NPV in dollars at an assumed contribution margin.

        NPV = m*A - B - K. This, not the break-even margin, is what a budgeted
        selection must maximise — see the degeneracy note in `select.py`.
        """
        d = self.evaluate(selected)
        return margin * d["npv_per_dollar_margin"] + d["npv_fixed"]

    def batch_npv(self, selected: np.ndarray, exposure: np.ndarray,
                  candidates: np.ndarray, margin: float,
                  block: int = 256) -> np.ndarray:
        """NPV of `selected + {c}` at `margin`, for every candidate c."""
        out = np.empty(len(candidates), dtype=float)
        for where, a, b in self._batch_totals(selected, exposure,
                                              candidates, block):
            out[where] = margin * a - b
        return out

    def standalone_breakeven(self) -> np.ndarray:
        """Break-even margin per ZCTA ignoring every interaction."""
        return self.breakeven
