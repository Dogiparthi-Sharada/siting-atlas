"""The contract every gate implements.

Split out from the gates themselves so the two FAMILIES of gate can live in
separate modules. That split is not cosmetic: this project's whole claim is
that data integrity and inferential integrity are different problems, and a
reader who opens `gates_data.py` and `gates_inference.py` sees that before
reading a line of code.

    base.py              Gate (ABC), WarehouseView (Protocol)
    gates_data.py        gates 1-4, data integrity — prior art exists
    gates_inference.py   gates 5-6, inferential integrity — the contribution
    pipeline.py          runs them in order and assembles a Decision
    gates.py             re-exports all of the above, unchanged for callers
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from ..common.logging_setup import get_logger
from .types import GateResult, Mutation, Protects, Severity

_log = get_logger("gates")

VALID_TYPES = {"FC", "SC", "DS", "SDC", "AMXL"}
VALID_OPERATORS = {"Amazon", "Walmart", "Costco", "Target"}

# Continental US bounding box, generous. A coordinate outside it is almost
# always a sign/order error in extraction rather than a real facility.
US_BOUNDS = (-179.0, 18.0, -66.0, 72.0)      # W, S, E, N


class WarehouseView(Protocol):
    """The slice of warehouse state a gate is allowed to see.

    A Protocol rather than a concrete class so gates can be unit-tested
    against a stub without a DuckDB file, and so the gate layer does not
    depend on the warehouse layer.
    """

    def zcta_exists(self, zcta: str) -> bool:
        """Is this a real ZCTA in the warehouse's universe?"""

    def is_donor(self, zcta: str) -> bool:
        """Is this ZCTA currently a synthetic-control donor?"""

    def donor_pool(self) -> set[str]:
        """Every ZCTA currently serving as a donor."""

    def neighbours_within(self, zcta: str, km: float) -> set[str]:
        """ZCTAs whose centroid lies within ``km`` of this one's."""

    def audit_log_writable(self) -> bool:
        """Can an audit record actually be written right now?"""


class Gate(ABC):
    """One check on a proposed mutation.

    Subclasses declare which kind of integrity they defend and implement
    ``check``. They must never mutate the mutation or the warehouse — a gate
    reports, it does not repair.
    """

    number: int
    name: str
    protects: Protects

    @abstractmethod
    def check(self, mutation: Mutation, view: WarehouseView) -> GateResult:
        """Evaluate the mutation. Must not raise for ordinary failures."""

    # -- helpers for subclasses ------------------------------------------
    def _result(self, severity: Severity, reason: str, **evidence
                ) -> GateResult:
        """Build a GateResult stamped with this gate's identity."""
        return GateResult(self.number, self.name, self.protects, severity,
                          reason, evidence)

    def ok(self, reason: str = "ok", **evidence) -> GateResult:
        """PASS: the mutation cleared this gate."""
        return self._result(Severity.PASS, reason, **evidence)

    def reject(self, reason: str, **evidence) -> GateResult:
        """REJECT: do not write. Stops the pipeline at this gate."""
        return self._result(Severity.REJECT, reason, **evidence)

    def escalate(self, reason: str, **evidence) -> GateResult:
        """ESCALATE: may well be correct, but a human must confirm."""
        return self._result(Severity.ESCALATE, reason, **evidence)

    def warn(self, reason: str, **evidence) -> GateResult:
        """WARN: recorded, does not block the write."""
        return self._result(Severity.WARN, reason, **evidence)


