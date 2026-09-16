"""Choose which ZCTAs to activate under a capital budget.

No performance guarantee is claimed, and that is deliberate
-----------------------------------------------------------
Greedy maximisation of a monotone submodular function is within (1 - 1/e) of
optimal. That theorem is quoted constantly and it does not apply here: the
objective has positive interactions (shared line haul) and negative ones
(cannibalisation), so it is neither submodular nor supermodular. Citing the
bound anyway would be the kind of borrowed rigour this project exists to
avoid.

What is honest is to report an achieved value together with a computed upper
bound, and let the gap speak:

    greedy    -> a feasible portfolio
    local swap-> improves it where a 1-for-1 exchange helps
    bound     -> the best conceivable value ignoring every negative
                 interaction, which is genuinely an upper bound

A small gap means the heuristic is close to optimal FOR THIS INSTANCE. That is
a weaker claim than a worst-case guarantee, and it is the true one.
"""

from __future__ import annotations

import numpy as np

from ..common.logging_setup import get_logger
from .objective import PortfolioObjective

_log = get_logger("optimize.select")


class BudgetedSelector:
    """Greedy construction plus local search under a capital budget."""

    def __init__(self, objective: PortfolioObjective, budget_usd: float):
        """Fix the number of activations the budget funds.

        Capacity is floor(budget / capital per activation), then capped at
        the number of candidates — a budget larger than the pilot cannot
        buy ZCTAs that do not exist.
        """
        self.obj = objective
        self.budget = budget_usd
        self.capacity = int(budget_usd
                            // objective.params.capital_per_activation_usd)
        if self.capacity < 1:
            raise ValueError(
                f"budget ${budget_usd:,.0f} cannot fund even one "
                f"activation at "
                f"${objective.params.capital_per_activation_usd:,.0f}")
        _class = min(self.capacity, objective.n)
        self.capacity = _class
        self.margin = 0.0

    # -- construction ----------------------------------------------------
    def greedy(self, margin: float | None = None) -> np.ndarray:
        """Add the ZCTA with the highest marginal NPV, until it stops paying.

        `margin` is the assumed contribution margin per parcel. If omitted,
        the selection maximises NPV at the margin where the FULL-budget
        portfolio would break even — a neutral choice that neither assumes
        the operator is profitable nor that it is not.

        Two things make this different from ranking by standalone cost. The
        marginal NPV of a candidate depends on what is already selected, so
        twenty adjacent ZCTAs that cannibalise each other are priced as such.
        And the loop stops when the best remaining candidate has NEGATIVE
        marginal NPV, so it can recommend spending less than the budget —
        which the previous objective structurally could not.
        """
        if margin is None:
            margin = self._neutral_margin()
        self.margin = margin

        sel = np.zeros(self.obj.n, dtype=bool)
        exposure = np.zeros(self.obj.n, dtype=float)
        current = 0.0

        for _ in range(self.capacity):
            remaining = np.flatnonzero(~sel)
            if remaining.size == 0:
                break
            # One vectorised sweep over every remaining candidate; exposure is
            # carried forward rather than recomputed.
            vals = self.obj.batch_npv(sel, exposure, remaining, margin)
            best = int(np.argmax(vals))
            if vals[best] <= current:
                _log.info("stopped at %d of %d fundable activations: the next "
                          "one would reduce NPV by $%.0f", int(sel.sum()),
                          self.capacity, current - vals[best])
                break
            pick = remaining[best]
            current = vals[best]
            sel[pick] = True
            exposure = exposure + self.obj._interaction[:, pick]

        _log.info("greedy selected %d of %d ZCTAs at margin $%.3f: "
                  "NPV $%.0f, break-even $%.4f/parcel",
                  sel.sum(), self.obj.n, margin, current,
                  self.obj.marginal_breakeven(sel))
        return sel

    def _neutral_margin(self) -> float:
        """The margin at which a full-budget portfolio would break even.

        Picking a margin out of the air would decide the answer, since NPV is
        linear in it. Anchoring on the full-budget break-even makes the
        default self-referential rather than arbitrary: at exactly this
        margin the budget is worth spending and no more, so whatever the
        optimiser then chooses to leave unspent is a real finding.
        """
        idx = np.argsort(self.obj.standalone_breakeven())[:self.capacity]
        full = np.zeros(self.obj.n, dtype=bool)
        full[idx] = True
        return float(self.obj.marginal_breakeven(full))

    # -- improvement -----------------------------------------------------
    def local_search(self, sel: np.ndarray, max_rounds: int = 8) -> np.ndarray:
        """1-for-1 swaps while they help.

        Greedy commits early to choices that later picks make look bad. A swap
        pass is what lets it back out of one.
        """
        sel = sel.copy()
        best = self.obj.marginal_breakeven(sel)

        for rnd in range(1, max_rounds + 1):
            improved = False
            inside = np.flatnonzero(sel)
            outside = np.flatnonzero(~sel)
            # Only the weakest members are worth trying to replace.
            weak = inside[np.argsort(-self.obj.standalone_breakeven()[inside])]
            strong = outside[np.argsort(
                self.obj.standalone_breakeven()[outside])]

            for out in weak[:40]:
                for inn in strong[:40]:
                    sel[out], sel[inn] = False, True
                    val = self.obj.marginal_breakeven(sel)
                    if val < best - 1e-9:
                        best, improved = val, True
                        break
                    sel[out], sel[inn] = True, False
                if improved:
                    break
            if not improved:
                _log.info("local search converged after %d round(s)", rnd)
                break
            _log.debug("round %d improved break-even to $%.5f", rnd, best)
        return sel

    # -- bound -----------------------------------------------------------
    def upper_bound(self) -> float:
        """Best conceivable break-even margin, ignoring cannibalisation.

        Every negative interaction is switched off and every line-haul saving
        is granted in full, so no real portfolio can beat the best set under
        this relaxation. The bound is a true one and a loose one, which is
        stated rather than disguised.

        Ranking by standalone cost per parcel and taking the K cheapest does
        NOT find that set, and assuming it did was a bug: break-even is a
        RATIO, and the $4M of capital each activation costs does not shrink
        with volume, so a cheap ZCTA that delivers very little can raise the
        ratio it was picked for lowering. On the pilot the top-K set came out
        2.8% above the relaxation's actual optimum, and the reported
        optimality gap was that much too flattering.

        Dinkelbach solves the ratio exactly. For a trial margin ``lam`` the
        best set of a given size is the one with the smallest
        ``b_i - lam * a_i``; re-deriving ``lam`` from that set and repeating
        converges monotonically onto the minimum ratio.

        The cardinality is held at exactly ``capacity`` on purpose. Allowed to
        shrink, this objective is degenerate — a ratio is minimised by the
        single best unit, so the "optimum" would be a one-ZCTA portfolio and
        the gap would only be measuring that the budget was spent. Comparing
        like with like keeps the gap a statement about WHICH K were chosen.
        """
        p = self.obj.params
        a = self.obj.annual_parcels * p.annuity_factor
        b = ((self.obj.annual_cost
              - self.obj.linehaul_cost * p.linehaul_sharing)
             * p.annuity_factor + p.capital_per_activation_usd)

        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(a > 0, b / a, np.inf)
        keep = np.argsort(ratio)[:self.capacity]
        if a[keep].sum() <= 0:
            return float("inf")
        lam = b[keep].sum() / a[keep].sum()

        for _ in range(50):
            keep = np.argsort(b - lam * a)[:self.capacity]
            if a[keep].sum() <= 0:
                break
            new = b[keep].sum() / a[keep].sum()
            if not np.isfinite(new) or abs(new - lam) < 1e-12:
                break
            lam = new
        return float(lam)

    def solve(self, margin: float | None = None) -> dict:
        """Build a portfolio, refine it, and report it against a bound."""
        greedy = self.greedy(margin)
        refined = self.local_search(greedy)

        achieved = self.obj.marginal_breakeven(refined)
        bound = self.upper_bound()
        gap = (achieved - bound) / bound if bound > 0 else float("nan")

        return {"selected": refined,
                "capacity": self.capacity,
                "margin": self.margin,
                "npv": self.obj.npv(refined, self.margin),
                "greedy_breakeven": self.obj.marginal_breakeven(greedy),
                "breakeven_margin": achieved,
                "upper_bound": bound,
                "optimality_gap": gap,
                "detail": self.obj.evaluate(refined)}

    def frontier(self, margins) -> list[dict]:
        """Solve at a range of margins.

        The operator's margin is unobservable, so a single portfolio is a
        single guess. The frontier is the honest deliverable: it says how many
        ZIPs are worth activating AT EACH margin, and the reader supplies the
        one number only they possess.
        """
        out = []
        for m in margins:
            r = self.solve(float(m))
            out.append({"margin": float(m), "n": r["detail"]["n"],
                        "npv": r["npv"],
                        "capital": r["detail"]["capital"],
                        "breakeven_margin": r["breakeven_margin"]})
            _log.info("margin $%.2f -> %d activations, NPV $%.0f",
                      m, r["detail"]["n"], r["npv"])
        return out
