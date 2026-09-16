"""Tests for the six-gate mutation path.

The central test is ``test_plano_case``: a mutation that passes every
data-integrity gate and is still caught by the identification gates. If that
test ever passes for the wrong reason — because a data gate rejected the
mutation first — the project's contribution is not being demonstrated, so it
asserts explicitly that gates 1-4 all passed.
"""

from __future__ import annotations

import pytest

from siting_atlas.agent.gates import (
    AuditLogGate,
    ConfidenceGate,
    DonorPoolIntegrityGate,
    EstimateStabilityGate,
    GatePipeline,
    GeocodingGate,
    SchemaGate,
)
from siting_atlas.agent.types import Mutation, Protects, Severity


class StubWarehouse:
    """Minimal WarehouseView for tests.

    A Protocol rather than a base class means the gate layer never imports
    the warehouse, so this stub needs no database and the tests run in
    milliseconds.
    """

    def __init__(self, zctas=None, donors=None, neighbours=None,
                 audit_writable=True):
        self._zctas = set(zctas or {"75024", "75025", "75080", "94608"})
        self._donors = set(donors or set())
        self._neighbours = neighbours or {}
        self._audit = audit_writable

    def zcta_exists(self, zcta): return zcta in self._zctas
    def is_donor(self, zcta): return zcta in self._donors
    def donor_pool(self): return set(self._donors)
    def neighbours_within(self, zcta, km): return set(
        self._neighbours.get(zcta, set()))
    def audit_log_writable(self): return self._audit


def make_mutation(**overrides) -> Mutation:
    """A well-formed mutation. Tests override one field to break it."""
    base = {
        "mutation_id": "m-0001", "operator": "Walmart",
        "facility_type": "SC",
        "zcta": "75024", "latitude": 33.0198, "longitude": -96.6989,
        "open_year": 2025, "open_quarter": 1, "confidence": 0.94,
        "source_text":
            "Walmart opens a new sortation centre in Plano, Texas.",
        "source_url": "https://example.com/newsroom/plano",
    }
    base.update(overrides)
    return Mutation(**base)


def steady_estimator(_mutation):
    """theta does not move — the mutation is inferentially harmless."""
    return 0.310


def moving_estimator(mutation):
    """theta moves materially once the mutation is applied."""
    return 0.310 if mutation is None else 0.383


# ---------------------------------------------------------------------------
# gates 1-4, data integrity
# ---------------------------------------------------------------------------
def test_schema_rejects_stripped_leading_zero():
    # '1890' instead of '01890' is the most common extraction defect, and it
    # fails silently in a join rather than raising.
    result = SchemaGate().check(make_mutation(zcta="1890"), StubWarehouse())
    assert result.severity is Severity.REJECT
    assert "five digits" in result.reason


def test_schema_rejects_unknown_facility_type():
    result = SchemaGate().check(make_mutation(facility_type="XX"),
                                StubWarehouse())
    assert result.severity is Severity.REJECT


def test_geocoding_rejects_sign_error():
    # A positive longitude puts a Texas facility in Asia. Sign errors are a
    # classic extraction failure and a bounding box catches them cheaply.
    result = GeocodingGate().check(make_mutation(longitude=96.6989),
                                   StubWarehouse())
    assert result.severity is Severity.REJECT
    assert "outside the United States" in result.reason


def test_geocoding_warns_but_allows_missing_coordinates():
    # Most press releases name a city, not coordinates. The centroid is a
    # usable fallback, so this must not be fatal.
    result = GeocodingGate().check(
        make_mutation(latitude=None, longitude=None), StubWarehouse())
    assert result.severity is Severity.WARN
    assert result.passed


def test_confidence_threshold():
    gate = ConfidenceGate(threshold=0.80)
    assert gate.check(make_mutation(confidence=0.79),
                      StubWarehouse()).severity is Severity.REJECT
    assert gate.check(make_mutation(confidence=0.81),
                      StubWarehouse()).severity is Severity.PASS


def test_audit_gate_requires_attribution():
    result = AuditLogGate().check(make_mutation(source_url=""),
                                  StubWarehouse())
    assert result.severity is Severity.REJECT


# ---------------------------------------------------------------------------
# gates 5-6, inferential integrity
# ---------------------------------------------------------------------------
def test_donor_pool_gate_catches_contamination():
    view = StubWarehouse(donors={"75025", "75080"},
                         neighbours={"75024": {"75025"}})
    result = DonorPoolIntegrityGate(radius_km=20).check(make_mutation(), view)
    assert result.severity is Severity.ESCALATE
    assert result.evidence["contaminated"] == ["75025"]


def test_donor_pool_gate_passes_when_pool_is_clean():
    view = StubWarehouse(donors={"94608"}, neighbours={"75024": {"75025"}})
    result = DonorPoolIntegrityGate().check(make_mutation(), view)
    assert result.severity is Severity.PASS


def test_estimate_stability_escalates_on_material_move():
    gate = EstimateStabilityGate(moving_estimator, threshold=0.02)
    result = gate.check(make_mutation(), StubWarehouse())
    assert result.severity is Severity.ESCALATE
    assert result.evidence["delta"] == pytest.approx(0.073, abs=1e-3)


def test_estimate_stability_passes_within_threshold():
    gate = EstimateStabilityGate(steady_estimator, threshold=0.02)
    assert gate.check(make_mutation(),
                      StubWarehouse()).severity is Severity.PASS


# ---------------------------------------------------------------------------
# the case the whole contribution rests on
# ---------------------------------------------------------------------------
def test_plano_case():
    """Every data gate passes. The inference still breaks.

    This is the example in the proposal, executed. If the mutation were
    caught by a data-integrity gate the demonstration would be worthless, so
    that is asserted rather than assumed.
    """
    view = StubWarehouse(donors={"75025", "75080"},
                         neighbours={"75024": {"75025", "75080"}})
    pipeline = GatePipeline.standard(moving_estimator, radius_km=20.0)
    decision = pipeline.evaluate(make_mutation(), view)

    data_gates = decision.by_protection(Protects.DATA)
    assert len(data_gates) == 4
    assert all(r.passed for r in data_gates), (
        "the point of this test is that the DATA is fine — a data gate "
        "firing here means the fixture is wrong, not that the system works")

    inference_gates = decision.by_protection(Protects.INFERENCE)
    assert len(inference_gates) == 2
    assert all(r.severity is Severity.ESCALATE for r in inference_gates)

    assert not decision.rejected
    assert decision.escalated
    assert decision.outcome == "escalated to human"


def test_hitl_holds_a_fully_clean_mutation():
    """With HITL on, even a mutation that clears all six gates waits.

    For a public demonstration the marginal cost of a click is zero and the
    cost of a live failure is not.
    """
    view = StubWarehouse(donors=set(), neighbours={})
    pipeline = GatePipeline.standard(steady_estimator, hitl_required=True)
    decision = pipeline.evaluate(make_mutation(), view)

    assert all(r.passed for r in decision.results)
    assert not decision.applied
    assert decision.outcome == "awaiting human apply"

    auto = GatePipeline.standard(steady_estimator, hitl_required=False)
    assert auto.evaluate(make_mutation(), view).applied


def test_pipeline_stops_at_first_rejection():
    """A malformed mutation must not cost a model fit."""
    calls = []

    def counting_estimator(mutation):
        calls.append(mutation)
        return 0.31

    pipeline = GatePipeline.standard(counting_estimator)
    decision = pipeline.evaluate(make_mutation(zcta="1890"), StubWarehouse())

    assert decision.rejected
    assert calls == [], "the estimator ran despite a schema rejection"
    assert len(decision.results) == 1
