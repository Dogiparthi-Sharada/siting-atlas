"""Gates 1-4 — data integrity. Prior art exists; included for completeness.

These check that the row is well-formed and truthful: the schema holds, the
coordinates resolve, the extraction was confident, the write is attributable.
Every published agent-gating framework we surveyed checks these. We claim no
novelty here, and that is the point of keeping them in their own module —
`gates_inference.py` is where the contribution lives.
"""

from __future__ import annotations

from .base import US_BOUNDS, VALID_OPERATORS, VALID_TYPES, Gate, WarehouseView
from .types import GateResult, Mutation, Protects


class SchemaGate(Gate):
    """Gate 1: is the extracted row even well-formed?

    Cheapest check, so it runs first — a malformed mutation should never
    cost a geocode lookup, let alone a model re-fit.
    """
    number, name, protects = 1, "schema conformance", Protects.DATA

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        """Collect every structural problem, then reject once with all of
        them, so a reviewer sees the whole diagnosis in one message."""
        problems = []
        if m.operator not in VALID_OPERATORS:
            problems.append(f"unknown operator {m.operator!r}")
        if m.facility_type not in VALID_TYPES:
            problems.append(f"unknown facility_type {m.facility_type!r}")
        if not (m.zcta.isdigit() and len(m.zcta) == 5):
            # Five digits with leading zeros preserved. '1890' instead of
            # '01890' is the single most common extraction defect.
            problems.append(f"zcta {m.zcta!r} is not five digits")
        if m.open_year is not None and not (1990 <= m.open_year <= 2035):
            problems.append(f"implausible open_year {m.open_year}")
        if m.open_quarter is not None and m.open_quarter not in (1, 2, 3, 4):
            problems.append(f"invalid quarter {m.open_quarter}")

        if problems:
            return self.reject("; ".join(problems), problems=problems)
        return self.ok("fields present and well-formed")


class GeocodingGate(Gate):
    """Gate 2: does this ZCTA exist, and do its coordinates land in the US?

    Missing coordinates are a WARN, not a rejection: most press releases
    give a city, and the ZCTA centroid is a usable stand-in. Coordinates
    OUTSIDE the US are a rejection, because that is a sign error in
    extraction rather than a real facility.
    """
    number, name, protects = 2, "geocoding reachability", Protects.DATA

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        """Reject an unknown ZCTA or a coordinate outside the US.
        Absent coordinates are only a warning."""
        if not view.zcta_exists(m.zcta):
            return self.reject(f"zcta {m.zcta} is not in the ZCTA universe",
                               zcta=m.zcta)
        if m.latitude is None or m.longitude is None:
            # Not fatal: the ZCTA centroid is a usable fallback, and most
            # press releases give a city rather than coordinates.
            return self.warn("no coordinates; will use the ZCTA centroid")

        w, s, e, n = US_BOUNDS
        if not (s <= m.latitude <= n and w <= m.longitude <= e):
            return self.reject(
                f"coordinates ({m.latitude}, {m.longitude}) fall outside the "
                f"United States — usually a sign error in extraction",
                latitude=m.latitude, longitude=m.longitude)
        return self.ok("coordinates resolve inside the US",
                       latitude=m.latitude, longitude=m.longitude)


class ConfidenceGate(Gate):
    """Gate 3: was the extraction confident enough to act on?

    The threshold is constructor state rather than a constant so a
    deployment can tighten it without editing this file.
    """
    number, name, protects = 3, "confidence threshold", Protects.DATA

    def __init__(self, threshold: float = 0.80):
        """Set the minimum extraction confidence this gate will accept."""
        self.threshold = threshold

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        """Reject anything the extractor was not confident enough about."""
        if m.confidence < self.threshold:
            return self.reject(
                f"extraction confidence {m.confidence:.2f} below threshold "
                f"{self.threshold:.2f}", confidence=m.confidence,
                threshold=self.threshold)
        return self.ok(f"confidence {m.confidence:.2f}",
                       confidence=m.confidence)


class AuditLogGate(Gate):
    """Gate 4: will this write be attributable and reversible?

    Refuses both an unsourced mutation and a writable-nowhere audit log.
    A write that cannot be traced cannot be undone either.
    """
    number, name, protects = 4, "audit-log immutability", Protects.DATA

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        """Reject a write that could not afterwards be traced or undone."""
        if not m.source_url:
            return self.reject("no source_url — the write would be "
                               "unattributable")
        if not view.audit_log_writable():
            return self.reject("audit log is not writable; refusing a write "
                               "that could not be traced or undone")
        return self.ok("write is attributable and will be logged",
                       source_url=m.source_url)


