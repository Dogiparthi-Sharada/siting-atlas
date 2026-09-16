"""Gates 5-6 — inferential integrity. This is the contribution.

The failure these catch is invisible to every gate in `gates_data.py`:

    A press release announces a competitor sortation centre in Plano, Texas.
    The agent extracts (33.0198, -96.6989, SORTATION).
      gate 1 schema        PASS
      gate 2 geocoding     PASS   Plano is real, coordinates resolve
      gate 3 confidence    PASS   0.94
      gate 4 audit log     PASS   written
    All four gates pass. The data is correct.
    But the write changes W -> the donor pool -> theta -> NPV by millions.
    The data is fine. The inference is broken, and nothing checked.
"""

from __future__ import annotations

from collections.abc import Callable

from .base import Gate, WarehouseView
from .types import GateResult, Mutation, Protects


class DonorPoolIntegrityGate(Gate):
    """Does this write move a control unit into treatment?

    Synthetic control builds a counterfactual from untreated donor units. If
    a donor silently becomes treated — or falls inside the measured spillover
    radius of a new facility — the comparison is corrupted and nothing in the
    output signals it. The estimate simply becomes wrong while continuing to
    look reasonable.

    The everyday version: you are running a trial, and halfway through
    somebody quietly gives the placebo group the drug. No error is raised.
    The data collection is flawless. The trial is meaningless.
    """

    number, name, protects = 5, "donor-pool integrity", Protects.INFERENCE

    def __init__(self, radius_km: float = 20.0):
        # Default from the estimated cannibalisation decay: material within
        # ~8 km, fading to ~20, indistinguishable from zero beyond. Passing
        # the estimate in rather than hardcoding contiguity is the point.
        """Set the spillover radius, in km, that defines contamination."""
        self.radius_km = radius_km

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        """Escalate if the write treats a donor, or contaminates one nearby.

        Escalate rather than reject: the write is probably correct, and the
        right response is to recompute the donor pool, which is a human
        decision rather than something a gate should do silently.
        """
        affected = view.neighbours_within(m.zcta, self.radius_km)
        donors = view.donor_pool()
        contaminated = sorted(affected & donors)

        if view.is_donor(m.zcta):
            return self.escalate(
                f"zcta {m.zcta} is itself a donor; this write moves a "
                f"control unit into treatment",
                zcta=m.zcta, contaminated=contaminated)
        if contaminated:
            return self.escalate(
                f"{len(contaminated)} donor(s) fall within {self.radius_km:g} "
                f"km and become spillover-contaminated — recompute the pool "
                f"and flag them rather than silently re-weighting",
                contaminated=contaminated, radius_km=self.radius_km)
        return self.ok(f"no donors within {self.radius_km:g} km",
                       radius_km=self.radius_km,
                       donors_checked=len(donors))


class EstimateStabilityGate(Gate):
    """Does this write materially move the cannibalisation coefficient?

    The estimator is re-run with and without the mutation. If the change
    exceeds a threshold fixed IN ADVANCE, the write escalates to a human
    regardless of automation settings.

    The threshold is pre-registered for a reason: chosen after seeing
    results, it would be set wherever is convenient, and the gate would be a
    rationalisation rather than a control.
    """

    number, name, protects = 6, "estimate stability", Protects.INFERENCE

    def __init__(self, estimator: Callable[[Mutation | None], float],
                 threshold: float = 0.02):
        """Take the estimator to re-run and the PRE-REGISTERED threshold.

        Both injected: a threshold chosen after seeing results is a
        rationalisation, and an estimator imported here would make the gate
        untestable without a fitted model.
        """
        self.estimator = estimator
        self.threshold = threshold

    def check(self, m: Mutation, view: WarehouseView) -> GateResult:
        """Re-run the estimator with and without the write, and escalate
        if theta moves past the pre-registered threshold."""
        before = self.estimator(None)
        after = self.estimator(m)
        delta = abs(after - before)

        evidence = {"theta_before": round(before, 5),
                    "theta_after": round(after, 5),
                    "delta": round(delta, 5),
                    "threshold": self.threshold}

        if delta > self.threshold:
            return self.escalate(
                f"theta moves {delta:.4f} (from {before:.4f} to {after:.4f}), "
                f"beyond the pre-registered threshold of {self.threshold:.4f}",
                **evidence)
        return self.ok(f"theta moves {delta:.4f}, within threshold",
                       **evidence)


