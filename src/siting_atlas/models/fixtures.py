"""SYNTHETIC panel with a data-generating process we chose ourselves.

WHAT THIS IS NOT
----------------
Not data. Nothing produced from this module describes any real ZCTA, any
real operator or any real facility. Unit identifiers are of the form
``SYN-00001`` precisely so that a row from here can never be mistaken for a
ZIP code in a join, a plot or a spreadsheet, and every artefact built on it
is written under a ``SYNTHETIC_`` filename with ``"synthetic": true`` in the
metrics.

WHAT IT IS FOR
--------------
The estimator has to be verifiable BEFORE the target variable exists, and
there is exactly one way to verify an estimator: give it data whose true
coefficients you already know and check that it hands them back. Real data
cannot do this, because with real data the truth is the thing you are trying
to find out. A model that recovers x_demand = 0.80 from a process we built
with x_demand = 0.80 has demonstrated that the link function, the risk-set
construction, the standardisation and the spline basis all compose
correctly. That is a claim about the CODE, and it is the only claim worth
making today.

The covariates are named ``x_demand``, ``x_cost`` and ``x_competition``
rather than ``median_household_income`` and friends. Deliberately: a plot of
"synthetic income effect" gets screenshotted and repeated as a finding about
income, and neutral names make that impossible.

The process
-----------
    hazard(t) = 1 - exp(-exp( alpha(t) + b1*x_demand + b2*x_cost
                                       + b3*x_competition ))
    alpha(t)  = a0 + a1*t + a2*t^2      a deliberate hump, not a line

The baseline is curved on purpose. A straight-line time term is misspecified
against it, which is what makes "the spline fits better than the linear
term" a test with something at stake rather than a tautology.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from ..common.seeds import seed

_log = get_logger("models.fixtures")

SYNTHETIC_PREFIX = "SYN-"

BANNER = (
    "SYNTHETIC DATA IN USE — the facility panel has not arrived, so the "
    "outcome below was generated from a known process. These numbers "
    "validate the CODE. They are not findings about any real place.")

#: The truth the estimator has to find. Read by the recovery tests.
TRUE_COEFFICIENTS = {
    "x_demand": 0.80,
    "x_cost": -0.45,
    "x_competition": 0.30,
}


@dataclass(frozen=True)
class SyntheticSpec:
    """Knobs on the generator. Defaults give a realistic rare-event panel."""

    n_units: int = 1200
    n_quarters: int = 32              # 2018Q1..2025Q4, matching the panel
    start_year: int = 2018
    betas: dict = field(default_factory=lambda: dict(TRUE_COEFFICIENTS))
    # alpha(t) = a0 + a1*t + a2*t^2. a0 sets the level (and so the event
    # rate); a1 and a2 make the hump.
    alpha0: float = -5.0
    alpha1: float = 0.16
    alpha2: float = -0.0042
    #: Share of units already enabled before the window opens. These are the
    #: left-truncated units the risk set has to recognise and drop.
    left_truncated_share: float = 0.03
    #: Encode the outcome as a state flag (True from the opening quarter
    #: onwards) rather than an event flag. The real panel builder will
    #: almost certainly do this, so it is the default here.
    state_encoding: bool = True
    seed_name: str = "hazard"

    def summary(self) -> dict:
        return {"synthetic": True, "n_units": self.n_units,
                "n_quarters": self.n_quarters, "betas": dict(self.betas),
                "alpha": [self.alpha0, self.alpha1, self.alpha2],
                "left_truncated_share": self.left_truncated_share,
                "state_encoding": self.state_encoding}


def baseline_alpha(t: np.ndarray, spec: SyntheticSpec) -> np.ndarray:
    """The true time baseline on the cloglog scale."""
    t = np.asarray(t, dtype=float)
    return spec.alpha0 + spec.alpha1 * t + spec.alpha2 * t ** 2


def synthetic_panel(spec: SyntheticSpec | None = None) -> pd.DataFrame:
    """Generate a dense unit-quarter panel with a known outcome process.

    Dense on purpose: it returns every quarter for every unit, including the
    quarters after a unit enabled, exactly like the real panel will. If the
    fixture handed back a clean risk set it would be testing the estimator
    against the one input shape that cannot trigger the bug the risk-set
    module exists to prevent.
    """
    spec = spec or SyntheticSpec()
    rng = np.random.default_rng(seed("models", spec.seed_name))
    _log.warning("%s", BANNER)

    n, q = spec.n_units, spec.n_quarters
    unit_ids = np.array([f"{SYNTHETIC_PREFIX}{i:05d}" for i in range(n)])

    # Unit-level covariates, fixed over time. Correlated demand and cost,
    # because in the real panel dense expensive places are the same places,
    # and an estimator that only works on orthogonal covariates has not been
    # tested on anything.
    x_demand = rng.normal(0, 1, n)
    x_cost = 0.4 * x_demand + np.sqrt(1 - 0.4 ** 2) * rng.normal(0, 1, n)
    x_competition = rng.normal(0, 1, n)

    t_grid = np.arange(q)
    eta = (baseline_alpha(t_grid, spec)[None, :]
           + (spec.betas["x_demand"] * x_demand
              + spec.betas["x_cost"] * x_cost
              + spec.betas["x_competition"] * x_competition)[:, None])
    hazard = -np.expm1(-np.exp(eta))            # 1 - exp(-exp(eta))

    # Draw the whole grid, then take the FIRST success per unit. Drawing
    # sequentially and breaking would give the same distribution but a
    # different number of random draws per unit, which makes the fixture's
    # output depend on the event pattern and so harder to reason about.
    fired = rng.random((n, q)) < hazard
    has_event = fired.any(axis=1)
    event_t = np.where(has_event, fired.argmax(axis=1), -1)

    # Left truncation: a slice of units were already enabled when the window
    # opened, so they show as enabled in the very first quarter.
    n_trunc = int(round(spec.left_truncated_share * n))
    if n_trunc:
        truncated = rng.choice(n, size=n_trunc, replace=False)
        event_t[truncated] = 0
        has_event[truncated] = True

    frame = pd.DataFrame({
        "zcta": np.repeat(unit_ids, q),
        "t_true": np.tile(t_grid, n),
        "x_demand": np.repeat(x_demand, q),
        "x_cost": np.repeat(x_cost, q),
        "x_competition": np.repeat(x_competition, q),
    })
    frame["year"] = spec.start_year + frame["t_true"] // 4
    frame["quarter"] = frame["t_true"] % 4 + 1

    event_at = np.repeat(event_t, q)
    if spec.state_encoding:
        enabled = (event_at >= 0) & (frame["t_true"].to_numpy() >= event_at)
    else:
        enabled = frame["t_true"].to_numpy() == event_at
    frame["enabled"] = enabled

    # Carried through every downstream frame so that a stray parquet found
    # on disk in six months still announces what it is.
    frame["synthetic"] = True
    frame = frame.drop(columns=["t_true"])

    _log.info("synthetic panel: %d units x %d quarters = %d rows, "
              "%d units ever enabled (%d left-truncated)",
              n, q, len(frame), int(has_event.sum()), n_trunc)
    return frame


def true_coefficients(spec: SyntheticSpec | None = None) -> dict:
    """The betas the estimator is supposed to recover."""
    return dict((spec or SyntheticSpec()).betas)


def covariate_names(spec: SyntheticSpec | None = None) -> tuple[str, ...]:
    return tuple((spec or SyntheticSpec()).betas)
