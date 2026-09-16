"""L4 — run a proposed mutation through the six gates against real state.

    python -m siting_atlas.agent.runner --demo-plano
    python -m siting_atlas.agent.runner --mutation proposed.json
    python -m siting_atlas.agent.runner --mutation m.json --donor-pool d.txt

Every invocation writes an audit record, including the invocations that end
in a rejection. A rejected write is the most interesting thing the system
does and losing that record would be the easiest way to make the safety
argument unfalsifiable: "it never let a bad write through" is only a claim
if the attempts were logged.

The record is written to ``outputs/audit/<mutation_id>.json`` and appended
to ``outputs/audit/mutations.jsonl``. Both, because the per-mutation file is
what a human opens and the JSONL is what an analysis reads.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, step, traced_layer
from ..models.hazard import HazardSpec
from ..models.panel_source import load_panel, real_panel_is_usable
from .estimators import (
    AvailabilityAwareStabilityGate,
    HazardThetaEstimator,
    UnavailableThetaEstimator,
)
from .gates import (
    AuditLogGate,
    ConfidenceGate,
    DonorPoolIntegrityGate,
    GatePipeline,
    GeocodingGate,
    SchemaGate,
)
from .types import Decision, Mutation
from .warehouse_view import DuckDBWarehouseView

_log = get_logger("agent.runner")

JOURNAL = "mutations.jsonl"

PLANO = {
    "mutation_id": "demo-plano-0001",
    "operator": "Walmart", "facility_type": "SC", "zcta": "75024",
    "latitude": 33.0198, "longitude": -96.6989,
    "open_year": 2025, "open_quarter": 1, "confidence": 0.94,
    "source_text": "Walmart opens a new sortation centre in Plano, Texas.",
    "source_url": "https://example.com/newsroom/plano",
}


def load_mutation(path: Path) -> Mutation:
    """Read a proposed write from JSON, rejecting unknown fields loudly.

    Unknown fields are an error rather than something to ignore: a producer
    that sends ``open_date`` instead of ``open_year`` would otherwise have
    its date silently dropped and the mutation would sail through gate 1
    with no date at all.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    known = set(Mutation.__dataclass_fields__)
    unknown = sorted(set(payload) - known)
    if unknown:
        raise ValueError(
            f"{path} carries unrecognised field(s) {unknown}; expected any "
            f"of {sorted(known)}")
    return Mutation(**payload)


def build_estimator(theta_term: str | None = None):
    """Gate 6's estimator, and an honest one when the target is missing.

    Returns ``(estimator, basis)``. The basis string lands in the audit
    record so a reader can tell at a glance whether the stability check
    actually ran.
    """
    # Asked directly rather than via load_panel(), because load_panel's
    # fallback is to GENERATE a synthetic panel — correct for the modelling
    # runner, pointless here, where the answer to "is there a target" is the
    # whole question and a fabricated panel is not an answer to it.
    usable, detail = real_panel_is_usable()

    if usable:
        source = load_panel()
        spec = HazardSpec(covariates=source.covariates)
        return (HazardThetaEstimator(source.frame, spec,
                                     theta_term=theta_term),
                "refit-on-real-panel")

    # Note what is NOT done here: fitting the hazard on the synthetic
    # fixture and reporting the resulting delta as if it were about this
    # mutation. The fixture has no ZCTA 75024 in it; any theta computed
    # there would be a number with no relationship to the write being
    # judged, and dressing it up as a stability check would be worse than
    # having no check at all.
    _log.warning("gate 6 cannot run: %s", detail.get("reason", "unknown"))
    return (UnavailableThetaEstimator(
        "the facility panel has not arrived, so there is no outcome to "
        "re-estimate; " + str(detail.get("reason", ""))),
        "unavailable-target-unpopulated")


def build_pipeline(estimator, *, radius_km: float = 20.0,
                   confidence: float = 0.80,
                   theta_threshold: float = 0.02,
                   hitl_required: bool = True) -> GatePipeline:
    """The standard six, with gate 6 aware that it might not be able to run.

    Mirrors :meth:`GatePipeline.standard` and swaps exactly one gate. Kept
    as a separate constructor rather than a flag on the original so that the
    published configuration stays untouched and this variation is visible.
    """
    return GatePipeline([
        SchemaGate(),
        GeocodingGate(),
        ConfidenceGate(confidence),
        AuditLogGate(),
        DonorPoolIntegrityGate(radius_km),
        AvailabilityAwareStabilityGate(estimator, theta_threshold),
    ], hitl_required=hitl_required)


def write_audit_record(decision: Decision, view: DuckDBWarehouseView,
                       basis: str, audit_dir: Path | None = None) -> Path:
    """Persist the decision, the state it was taken against, and the basis."""
    directory = audit_dir or paths.AUDIT
    directory.mkdir(parents=True, exist_ok=True)

    record = {
        **decision.to_dict(),
        "mutation": {
            k: getattr(decision.mutation, k)
            for k in decision.mutation.__dataclass_fields__},
        "warehouse_state": view.describe(),
        "gate6_basis": basis,
    }

    path = directory / f"{decision.mutation.mutation_id}.json"
    write_json(path, record)

    # Appended, never rewritten. An audit journal that a later run can edit
    # is not an audit journal.
    with open(directory / JOURNAL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"mutation_id": decision.mutation.mutation_id,
                             "outcome": decision.outcome,
                             "gate6_basis": basis,
                             "record": str(path)}, default=str) + "\n")
    artefact(path, outcome=decision.outcome)
    return path


def run(mutation: Mutation, *, donor_pool: set[str] | None = None,
        radius_km: float = 20.0, theta_threshold: float = 0.02,
        hitl_required: bool = True, db_path: Path | None = None,
        audit_dir: Path | None = None) -> tuple[Decision, Path]:
    """Gate one mutation against real warehouse state and record the result."""
    view = DuckDBWarehouseView(db_path, donor_pool=donor_pool,
                               audit_dir=audit_dir)

    with step("gate6:estimator"):
        estimator, basis = build_estimator()

    with step("gates"):
        pipeline = build_pipeline(estimator, radius_km=radius_km,
                                  theta_threshold=theta_threshold,
                                  hitl_required=hitl_required)
        decision = pipeline.evaluate(mutation, view)

    with step("audit"):
        path = write_audit_record(decision, view, basis, audit_dir)
    return decision, path


def _print_decision(decision: Decision, path: Path, basis: str) -> None:
    w = 78
    print("\n" + "=" * w)
    print(f"  MUTATION  {decision.mutation.mutation_id}")
    print(f"  {decision.mutation.summary()}")
    print("=" * w)
    for result in decision.results:
        print(f"  {result}")
    if len(decision.results) < 6:
        print(f"  ... {6 - len(decision.results)} later gate(s) not run; "
              f"the pipeline stops at the first rejection")
    print("-" * w)
    print(f"  OUTCOME   {decision.outcome.upper()}")
    print(f"  gate 6 basis  {basis}")
    print(f"  audit record  {paths.rel(path)}")
    print("=" * w)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--mutation", type=Path,
                     help="JSON file holding one proposed write")
    src.add_argument("--demo-plano", action="store_true",
                     help="the worked example from the proposal")
    ap.add_argument("--donor-pool", type=Path, default=None,
                    help="text file, one donor ZCTA per line")
    ap.add_argument("--radius-km", type=float, default=20.0)
    ap.add_argument("--theta-threshold", type=float, default=0.02)
    ap.add_argument("--no-hitl", action="store_true",
                    help="allow a fully clean mutation to apply itself")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    mutation = (Mutation(**PLANO) if args.demo_plano
                else load_mutation(args.mutation))
    donors = None
    if args.donor_pool:
        donors = {line.strip() for line
                  in args.donor_pool.read_text(encoding="utf-8").splitlines()
                  if line.strip()}

    with traced_layer("L4", f"gate mutation {mutation.mutation_id}"):
        decision, path = run(mutation, donor_pool=donors,
                             radius_km=args.radius_km,
                             theta_threshold=args.theta_threshold,
                             hitl_required=not args.no_hitl)

    basis = json.loads(path.read_text(encoding="utf-8"))["gate6_basis"]
    _print_decision(decision, path, basis)
    # A rejected write is a successful run of this tool, so the exit code
    # stays 0; a non-zero code would make a CI job fail on the system
    # working correctly.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
