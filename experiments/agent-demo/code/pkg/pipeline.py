"""Runs the gates in order and assembles a Decision."""

from __future__ import annotations

from collections.abc import Callable

from ..common.logging_setup import get_logger
from .base import Gate, WarehouseView
from .gates_data import AuditLogGate, ConfidenceGate, GeocodingGate, SchemaGate
from .gates_inference import DonorPoolIntegrityGate, EstimateStabilityGate
from .types import Decision, Mutation, Severity

_log = get_logger("gates")


class GatePipeline:
    """Runs gates in order and assembles a Decision.

    Ordering is deliberate: cheap structural checks first, the expensive
    re-estimation last, so a malformed mutation never costs a model fit.
    """

    def __init__(self, gates: list[Gate], hitl_required: bool = True):
        """Sort the gates by number so the cheap checks always run first."""
        self.gates = sorted(gates, key=lambda g: g.number)
        self.hitl_required = hitl_required

    def evaluate(self, mutation: Mutation, view: WarehouseView) -> Decision:
        """Run every gate in order and assemble the Decision.

        Stops at the first REJECT — later gates may assume earlier ones held,
        so the results list is a PREFIX of the pipeline, not the whole of it.
        Read a Decision's outcome, never the count of its results.
        """
        decision = Decision(mutation=mutation,
                            hitl_required=self.hitl_required)
        for gate in self.gates:
            result = gate.check(mutation, view)
            decision.results.append(result)
            _log.debug("%s", result)
            if result.severity is Severity.REJECT:
                # Stop on rejection: later gates may assume earlier ones held,
                # and re-estimating on a malformed mutation is meaningless.
                _log.warning("mutation %s rejected at gate %d (%s)",
                             mutation.mutation_id, gate.number, gate.name)
                break

        _log.info("mutation %s -> %s", mutation.mutation_id, decision.outcome)
        return decision

    @classmethod
    def standard(cls, estimator: Callable[[Mutation | None], float],
                 *, radius_km: float = 20.0, confidence: float = 0.80,
                 theta_threshold: float = 0.02,
                 hitl_required: bool = True) -> GatePipeline:
        """The six-gate configuration described in the proposal."""
        return cls([
            SchemaGate(),
            GeocodingGate(),
            ConfidenceGate(confidence),
            AuditLogGate(),
            DonorPoolIntegrityGate(radius_km),
            EstimateStabilityGate(estimator, theta_threshold),
        ], hitl_required=hitl_required)
