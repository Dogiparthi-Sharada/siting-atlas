"""Tests for the mutation runner: gate 6's estimator and the audit record.

Two claims are executed here rather than asserted in prose.

``test_unavailable_estimator_escalates_rather_than_passing`` — with no target
variable, gate 6 cannot run, and a gate that cannot run must not report a
pass. A constant-returning estimator would have made the delta zero and the
tick green, turning "we did not check" into "we checked and it was fine".

``test_gate6_switches_to_a_real_refit_the_day_the_target_lands`` — the same
runner with the same flags against the same warehouse, differing only in
that ``panel.parquet`` now has a populated outcome. That is the "one command
to real results" claim, run.
"""

from __future__ import annotations

import json

import duckdb
import numpy as np
import pytest

from siting_atlas.agent.estimators import (
    AvailabilityAwareStabilityGate,
    HazardThetaEstimator,
    TargetUnavailableError,
    UnavailableThetaEstimator,
    apply_mutation,
)
from siting_atlas.agent.runner import (
    build_pipeline,
    load_mutation,
    run,
    write_audit_record,
)
from siting_atlas.agent.types import Mutation, Severity
from siting_atlas.agent.warehouse_view import DuckDBWarehouseView
from siting_atlas.common import paths
from siting_atlas.models.fixtures import SyntheticSpec, synthetic_panel
from siting_atlas.models.hazard import HazardSpec

# Plano and its neighbours, with real centroids. The distances between them
# are small and known, which is what makes the radius assertions meaningful.
ZCTAS = [
    ("75024", 33.0755, -96.8100),    # Plano  - the mutation target
    ("75025", 33.0830, -96.7500),    # Plano  - ~5.6 km east
    ("75080", 32.9750, -96.7500),    # Richardson - ~12.9 km south-east
    ("94608", 37.8380, -122.2870),   # Emeryville CA - ~2,300 km away
]


@pytest.fixture
def warehouse(tmp_path):
    """A minimal warehouse carrying only what the view actually reads."""
    path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE dim_zcta (zcta VARCHAR, latitude DOUBLE, "
                "longitude DOUBLE)")
    con.executemany("INSERT INTO dim_zcta VALUES (?, ?, ?)", ZCTAS)
    con.close()
    return path


@pytest.fixture
def view(warehouse, tmp_path):
    return DuckDBWarehouseView(warehouse, donor_pool={"75025", "75080"},
                               audit_dir=tmp_path / "audit")


@pytest.fixture(autouse=True)
def no_real_panel(tmp_path, monkeypatch):
    """Point every test at an absent panel unless it says otherwise.

    Without this these tests would assert against whatever
    ``data/processed/panel.parquet`` happens to contain, so they would pass
    today and start failing on the day the facility data lands — for the
    wrong reason. Pinning the input makes each test say which world it is
    describing.
    """
    monkeypatch.setattr(paths, "PANEL", tmp_path / "absent-panel.parquet")


def make_mutation(**overrides) -> Mutation:
    base = dict(  # noqa: C408 - matches the helper in test_gates.py
        mutation_id="test-0001", operator="Walmart", facility_type="SC",
        zcta="75024", latitude=33.0198, longitude=-96.6989,
        open_year=2025, open_quarter=1, confidence=0.94,
        source_text="Walmart opens a new sortation centre in Plano, Texas.",
        source_url="https://example.com/newsroom/plano")
    base.update(overrides)
    return Mutation(**base)


def populated_panel(path) -> None:
    """A small panel that looks like the real one AFTER the target lands.

    Used to prove the claim that nothing but the data has to change: the
    same runner, unmodified, must switch to refitting on real rows.
    """
    frame = synthetic_panel(SyntheticSpec(n_units=120, n_quarters=12))
    frame = frame.rename(columns={
        "x_demand": "households", "x_cost": "median_household_income",
        "x_competition": "rent_index_yoy_pct"})
    # Real covariates, given real variation. Constant columns would be
    # collinear with the intercept and the fit would refuse them.
    rng = np.random.default_rng(4)
    frame["establishments"] = rng.normal(size=len(frame))
    frame["permits_yoy_pct"] = rng.normal(size=len(frame))
    frame.to_parquet(path, index=False)


# ---------------------------------------------------------------------------
# gate 6 when there is no target
# ---------------------------------------------------------------------------
def test_unavailable_estimator_escalates_rather_than_passing():
    """The failure mode this subclass exists to prevent.

    An estimator that returned a constant would make both fits agree, the
    delta zero and the gate green. "We did not check" must never render as
    "we checked and it was fine".
    """
    gate = AvailabilityAwareStabilityGate(
        UnavailableThetaEstimator("no target yet"), threshold=0.02)
    result = gate.check(make_mutation(), view=None)
    assert result.severity is Severity.ESCALATE
    assert result.evidence["evaluated"] is False
    assert "did not run" in result.reason


def test_unavailable_estimator_raises_when_called_directly():
    with pytest.raises(TargetUnavailableError):
        UnavailableThetaEstimator("nothing to fit")(None)


def test_hazard_theta_estimator_recovers_and_reacts(view):
    """Gate 6's real estimator, exercised on the synthetic panel.

    Two things are asserted: the baseline theta is the coefficient the
    fixture was built with, and adding one enablement to one unit moves it
    by a small amount rather than not at all. The second is what makes the
    gate capable of ever firing.
    """
    panel = synthetic_panel(SyntheticSpec(n_units=400))
    spec = HazardSpec(covariates=("x_demand", "x_cost", "x_competition"))
    estimator = HazardThetaEstimator(panel, spec, theta_term="x_demand")

    before = estimator(None)
    assert abs(before - 0.80) < 0.35, "the fixture's truth, roughly"
    assert estimator(None) is before, "the baseline fit must be cached"

    target = panel["zcta"].iloc[0]
    after = estimator(make_mutation(zcta=target, open_year=2020,
                                    open_quarter=2))
    assert after != before, "a real enablement must move the estimate"


def test_apply_mutation_never_touches_the_input(view):
    panel = synthetic_panel(SyntheticSpec(n_units=50))
    original = panel["enabled"].copy()
    target = panel["zcta"].iloc[0]

    out = apply_mutation(panel, make_mutation(zcta=target, open_year=2020,
                                              open_quarter=3))
    assert panel["enabled"].equals(original), "the panel was mutated in place"
    changed = out.loc[(out["zcta"] == target) & (out["year"] >= 2021),
                      "enabled"]
    assert changed.all()


def test_apply_mutation_without_a_date_is_a_no_op(view):
    panel = synthetic_panel(SyntheticSpec(n_units=50))
    out = apply_mutation(panel, make_mutation(open_year=None))
    assert out["enabled"].equals(panel["enabled"])


# ---------------------------------------------------------------------------
# the runner, end to end
# ---------------------------------------------------------------------------
def test_run_writes_an_audit_record_for_an_escalation(warehouse, tmp_path):
    audit = tmp_path / "audit"
    decision, path = run(make_mutation(),
                         donor_pool={"75025", "75080"},
                         db_path=warehouse, audit_dir=audit)

    assert decision.escalated and not decision.rejected
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["outcome"] == "escalated to human"
    assert record["mutation"]["zcta"] == "75024"
    assert record["warehouse_state"]["donor_pool_basis"] == "explicit"
    assert record["gate6_basis"] == "unavailable-target-unpopulated"
    assert record["run_id"], "every record carries the run that produced it"

    journal = (audit / "mutations.jsonl").read_text(encoding="utf-8")
    assert json.loads(journal.strip())["mutation_id"] == "test-0001"


def test_rejected_mutations_are_audited_too(warehouse, tmp_path):
    """A rejected write is the most interesting thing the system does.

    Logging only successes would make the safety claim unfalsifiable.
    """
    decision, path = run(make_mutation(mutation_id="bad-0001", zcta="1890"),
                         donor_pool=set(), db_path=warehouse,
                         audit_dir=tmp_path / "audit")
    assert decision.rejected
    assert path.exists()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["outcome"] == "rejected"
    assert len(record["results"]) == 1, "the pipeline stops at gate 1"


def test_journal_appends_rather_than_overwrites(warehouse, tmp_path):
    audit = tmp_path / "audit"
    for i in range(3):
        run(make_mutation(mutation_id=f"m-{i}"), donor_pool=set(),
            db_path=warehouse, audit_dir=audit)
    lines = (audit / "mutations.jsonl").read_text(
        encoding="utf-8").strip().splitlines()
    assert len(lines) == 3


def test_clean_mutation_still_waits_for_a_human(warehouse, tmp_path):
    """HITL holds a write that clears every gate it could run.

    Gate 6 cannot run today, so this also confirms the hold is not being
    produced by the unavailable estimator alone.
    """
    decision, _ = run(make_mutation(mutation_id="clean-0001"),
                      donor_pool=set(), db_path=warehouse,
                      audit_dir=tmp_path / "audit")
    assert not decision.rejected
    assert not decision.applied
    assert decision.escalated, "gate 6 could not be evaluated"

    data_gates = [r for r in decision.results if r.gate_number <= 5]
    assert all(r.passed for r in data_gates)


def test_gate6_switches_to_a_real_refit_the_day_the_target_lands(
        warehouse, tmp_path, monkeypatch):
    """The claim that only the data changes, executed rather than asserted.

    Same runner, same flags, same warehouse. The only difference is that
    ``panel.parquet`` now has a populated outcome — and gate 6 stops
    escalating for want of an estimator and starts reporting a real
    before/after theta.
    """
    panel = tmp_path / "panel.parquet"
    populated_panel(panel)
    monkeypatch.setattr(paths, "PANEL", panel)

    decision, path = run(make_mutation(mutation_id="post-target-0001"),
                         donor_pool=set(), db_path=warehouse,
                         audit_dir=tmp_path / "audit")

    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["gate6_basis"] == "refit-on-real-panel"

    gate6 = [r for r in decision.results if r["gate"] == 6] \
        if isinstance(decision.results[0], dict) else \
        [r for r in decision.results if r.gate_number == 6]
    assert len(gate6) == 1
    evidence = gate6[0].evidence
    assert "theta_before" in evidence and "theta_after" in evidence
    # 75024 is not in the synthetic panel, so the mutation cannot move the
    # estimate. The gate must then PASS on a measured zero, not escalate for
    # want of an estimator — a different outcome with a different meaning.
    assert evidence["delta"] == 0.0
    assert gate6[0].severity is Severity.PASS


def test_pipeline_has_all_six_gates_in_order():
    pipeline = build_pipeline(UnavailableThetaEstimator("x"))
    assert [g.number for g in pipeline.gates] == [1, 2, 3, 4, 5, 6]
    assert isinstance(pipeline.gates[5], AvailabilityAwareStabilityGate)


def test_unknown_fields_in_a_mutation_file_are_rejected(tmp_path):
    """A producer sending open_date instead of open_year would otherwise
    have its date silently dropped and sail through gate 1 undated."""
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"mutation_id": "m", "operator": "Amazon",
                                "facility_type": "DS", "zcta": "75024",
                                "open_date": "2025-01-01"}),
                    encoding="utf-8")
    with pytest.raises(ValueError, match="unrecognised field"):
        load_mutation(path)


def test_write_audit_record_captures_warehouse_state(view, tmp_path):
    from siting_atlas.agent.types import Decision
    decision = Decision(mutation=make_mutation(), hitl_required=True)
    path = write_audit_record(decision, view, "test-basis",
                              audit_dir=tmp_path / "audit")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["warehouse_state"]["zctas"] == len(ZCTAS)
    assert record["gate6_basis"] == "test-basis"


