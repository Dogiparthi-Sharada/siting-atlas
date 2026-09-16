"""Value types for the agent's mutation path.

Kept separate from the gate implementations so a gate can be written and
tested without importing the warehouse, and so these types can be reused by
the application layer when it renders a diff card.

The distinction that runs through this module is between two kinds of
correctness:

    DATA INTEGRITY          the row is well-formed and truthful
    INFERENTIAL INTEGRITY   the estimator's assumptions still hold after it

Every published gating framework we found checks the first. The second is
what this project contributes, and the enum below makes the boundary
explicit rather than implied by a comment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class Protects(StrEnum):
    """What a gate is defending. See the module docstring."""

    DATA = "data integrity"
    INFERENCE = "inferential integrity"


class Severity(StrEnum):
    """What a failure should cause.

    ESCALATE exists because some failures are not errors — a mutation that
    materially moves the estimate may be perfectly correct and still needs a
    human to look at it before it lands.
    """

    PASS = "pass"
    WARN = "warn"            # record it, allow the write
    ESCALATE = "escalate"    # correct, but a human must confirm
    REJECT = "reject"        # do not write


@dataclass(frozen=True)
class Mutation:
    """A write proposed by the agent after parsing unstructured text.

    Frozen because a gate must not be able to repair the thing it is
    judging. If a value needs correcting, that is a new Mutation with a
    recorded provenance chain, not a silent edit.
    """

    mutation_id: str
    operator: str
    facility_type: str
    zcta: str
    latitude: float | None = None
    longitude: float | None = None
    open_year: int | None = None
    open_quarter: int | None = None
    confidence: float = 0.0
    source_text: str = ""
    source_url: str = ""
    proposed_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(
            timespec="seconds"))

    def summary(self) -> str:
        """One line for a log or a diff card."""
        when = f"{self.open_year}" if self.open_year else "undated"
        return (f"{self.operator} {self.facility_type} in {self.zcta} "
                f"({when}, confidence {self.confidence:.2f})")


@dataclass(frozen=True)
class GateResult:
    """The verdict of one gate on one mutation."""

    gate_number: int
    gate_name: str
    protects: Protects
    severity: Severity
    reason: str
    evidence: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Did this gate allow the write through? WARN counts as passing."""
        return self.severity in (Severity.PASS, Severity.WARN)

    def __str__(self) -> str:
        """One bracketed line for a log: PASS/WARN/HOLD/FAIL and the reason."""
        mark = {"pass": "PASS", "warn": "WARN",
                "escalate": "HOLD", "reject": "FAIL"}[self.severity.value]
        return (f"[{mark}] gate {self.gate_number} {self.gate_name}: "
                f"{self.reason}")


@dataclass
class Decision:
    """The outcome of running a mutation through the whole gate pipeline."""

    mutation: Mutation
    results: list[GateResult] = field(default_factory=list)
    hitl_required: bool = True

    @property
    def rejected(self) -> bool:
        """True if any gate said REJECT — the write must not land."""
        return any(r.severity is Severity.REJECT for r in self.results)

    @property
    def escalated(self) -> bool:
        """True if any gate said ESCALATE — correct, but needs a human."""
        return any(r.severity is Severity.ESCALATE for r in self.results)

    @property
    def applied(self) -> bool:
        """Whether the write should land without further human action.

        Note the HITL default: for any public demonstration a mutation that
        clears every gate STILL waits for an explicit human apply. The gates
        are the safety argument in production; in a demo the marginal cost of
        a click is zero and the cost of a live failure is not.
        """
        return (not self.rejected and not self.escalated
                and not self.hitl_required)

    @property
    def outcome(self) -> str:
        """The single word describing what happens to this mutation."""
        if self.rejected:
            return "rejected"
        if self.escalated:
            return "escalated to human"
        if self.hitl_required:
            return "awaiting human apply"
        return "applied"

    def failures(self) -> list[GateResult]:
        """Every non-passing result, for rendering the reason to a reviewer."""
        return [r for r in self.results if not r.passed]

    def by_protection(self, kind: Protects) -> list[GateResult]:
        """Results from gates defending one kind of integrity.

        Lets the diff card separate "the row is wrong" from "the estimate
        moves", which are different questions for the person deciding.
        """
        return [r for r in self.results if r.protects is kind]

    def to_dict(self) -> dict:
        """Serialisable record for the audit log and the diff card."""
        return {
            "mutation_id": self.mutation.mutation_id,
            "summary": self.mutation.summary(),
            "outcome": self.outcome,
            "hitl_required": self.hitl_required,
            "results": [
                {"gate": r.gate_number, "name": r.gate_name,
                 "protects": r.protects.value, "severity": r.severity.value,
                 "reason": r.reason, "evidence": r.evidence}
                for r in self.results
            ],
        }
