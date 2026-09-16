"""The six gates a proposed warehouse mutation must clear.

Gates 1-4 protect DATA integrity and have extensive prior art. Gates 5-6
protect INFERENTIAL integrity, and that is the contribution. The two families
live in separate modules because the distinction between them IS the claim;
this module re-exports everything so no caller has to care.

    base.py              Gate (ABC), WarehouseView (Protocol)
    gates_data.py        gates 1-4, data integrity
    gates_inference.py   gates 5-6, inferential integrity
    pipeline.py          GatePipeline
"""

from __future__ import annotations

from .base import US_BOUNDS, VALID_OPERATORS, VALID_TYPES, Gate, WarehouseView
from .gates_data import AuditLogGate, ConfidenceGate, GeocodingGate, SchemaGate
from .gates_inference import DonorPoolIntegrityGate, EstimateStabilityGate
from .pipeline import GatePipeline

__all__ = [
    "Gate", "WarehouseView", "US_BOUNDS", "VALID_TYPES", "VALID_OPERATORS",
    "SchemaGate", "GeocodingGate", "ConfidenceGate", "AuditLogGate",
    "DonorPoolIntegrityGate", "EstimateStabilityGate", "GatePipeline",
]
