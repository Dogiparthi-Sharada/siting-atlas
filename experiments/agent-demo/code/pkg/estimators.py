"""What gate 6 re-runs, and what it does when there is nothing to re-run.

Gate 6 asks a simple question — does applying this write move the estimate
past a pre-registered threshold — and answers it by fitting the model twice.
That requires a model that can be fitted, which requires a target variable.
Today there is no target variable.

The wrong answer, and why it is tempting
----------------------------------------
Hand gate 6 an estimator that returns a constant. Both fits agree, the delta
is zero, the gate passes, and the audit record shows six green ticks. It
takes about ten seconds to write and it converts "we did not check" into "we
checked and it was fine", which is the single most damaging thing a safety
control can do. A gate that cannot run must not report a pass.

So :class:`UnavailableThetaEstimator` raises, and
:class:`AvailabilityAwareStabilityGate` turns that into an ESCALATE with the
reason stated. Extending by subclass is the mechanism ``gates.py`` documents
for exactly this.
"""

from __future__ import annotations

import pandas as pd

from ..common.logging_setup import get_logger
from ..models.hazard import DiscreteTimeHazard, HazardSpec
from ..models.risk_set import TargetUnpopulatedError, build_risk_set
from .gates import EstimateStabilityGate, WarehouseView
from .types import GateResult, Mutation

_log = get_logger("agent.estimators")


class TargetUnavailableError(RuntimeError):
    """The estimate cannot be recomputed because there is no outcome data."""


class UnavailableThetaEstimator:
    """Refuses to produce a number. Callable, so it satisfies gate 6's type.

    An object rather than a lambda so that the reason travels with it and
    shows up in a traceback as something a reader understands.
    """

    def __init__(self, reason: str):
        self.reason = reason

    def __call__(self, mutation: Mutation | None) -> float:
        raise TargetUnavailableError(self.reason)


class HazardThetaEstimator:
    """Refit the hazard with and without the mutation; return one coefficient.

    ``theta`` here is the coefficient the siting argument turns on — by
    default the first covariate in the specification. Which one it is
    matters less than that it is FIXED before the gate runs: choosing the
    coefficient after seeing which one moved would make gate 6 a search for
    a reason to approve.

    The baseline fit is cached. Gate 6 calls the estimator twice per
    mutation and the first call is identical every time, so caching turns
    two fits per mutation into one.
    """

    def __init__(self, panel: pd.DataFrame, spec: HazardSpec,
                 *, theta_term: str | None = None):
        self.panel = panel
        self.spec = spec
        self.theta_term = theta_term or spec.covariates[0]
        if self.theta_term not in spec.covariates:
            raise KeyError(
                f"theta_term {self.theta_term!r} is not in the "
                f"specification's covariates {spec.covariates}")
        self._baseline: float | None = None

    def __call__(self, mutation: Mutation | None) -> float:
        if mutation is None:
            if self._baseline is None:
                self._baseline = self._fit(self.panel)
            return self._baseline
        return self._fit(apply_mutation(self.panel, mutation))

    def _fit(self, panel: pd.DataFrame) -> float:
        try:
            risk = build_risk_set(panel)
        except TargetUnpopulatedError as exc:
            raise TargetUnavailableError(str(exc)) from exc
        model = DiscreteTimeHazard(self.spec).fit(risk)
        coef = model.coefficients().set_index("term")
        return float(coef.loc[self.theta_term, "coefficient"])


def apply_mutation(panel: pd.DataFrame, mutation: Mutation,
                   *, id_col: str = "zcta") -> pd.DataFrame:
    """A copy of the panel with the proposed enablement written in.

    A copy, never in place. Gate 6 is a hypothetical — "what would the
    estimate be IF this landed" — and a gate that mutated the warehouse to
    answer a question about mutating the warehouse would be indefensible.

    The enablement is written as a state flag from the opening quarter
    onwards, matching the encoding the panel builder uses. If the mutation
    carries no opening date there is nothing to place on the time axis, and
    the honest result is an unchanged panel plus a warning, not a guessed
    quarter.
    """
    if mutation.open_year is None:
        _log.warning("mutation %s has no open_year; gate 6 cannot place it "
                     "in time and the panel is returned unchanged",
                     mutation.mutation_id)
        return panel

    out = panel.copy()
    quarter = mutation.open_quarter or 1
    target = out[id_col] == mutation.zcta
    if not target.any():
        _log.warning("zcta %s is not in the panel; the mutation cannot move "
                     "the estimate and gate 6 will trivially pass",
                     mutation.zcta)
        return out

    after = (out["year"] > mutation.open_year) | (
        (out["year"] == mutation.open_year) & (out["quarter"] >= quarter))
    out.loc[target & after, "enabled"] = True
    return out


class AvailabilityAwareStabilityGate(EstimateStabilityGate):
    """Gate 6, with "could not be evaluated" as a distinct outcome.

    Subclassing rather than editing ``EstimateStabilityGate`` keeps the
    published six-gate behaviour exactly as specified and tested, and adds
    the operational case the specification did not cover: the estimator is
    not available yet.
    """

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        try:
            return super().check(m, view)
        except TargetUnavailableError as exc:
            return self.escalate(
                f"estimate stability could not be evaluated ({exc}). The "
                f"gate did not run, so it cannot report a pass; a human "
                f"must decide whether to accept an unverified write",
                evaluated=False, reason_detail=str(exc))
