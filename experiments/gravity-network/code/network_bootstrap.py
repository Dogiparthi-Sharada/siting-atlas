"""`choice_bootstrap.bootstrap`, spread over cores, draw for draw.

Why this exists and what it is NOT
----------------------------------
It is not a different bootstrap. Every replicate is
``choice_bootstrap.refit`` applied to ``choice_bootstrap.resample_decisions``
of the same draw, and the draws come from the same
``np.random.default_rng(seed)`` in the same order as the sequential loop in
`choice_bootstrap.bootstrap`. The only difference is which core runs which
refit. `network_inference` verifies that claim at run time rather than
asserting it: it runs a handful of replicates both ways and stores the
maximum absolute difference in the artefact.

It exists because the published arm has 56 decisions and this one has 485.
Here a replicate costs 4.5 wall-seconds clustered by metro and about 8
unclustered, MEASURED and logged by the run itself -- the log-likelihood is
evaluated over 86,718 alternative rows and the optimiser is chasing two
parameters that are running to minus infinity. At those rates the sequential
loop at the project's ceiling of 4,000 replicates is many hours per
bootstrap, and there are several to run. No claim is made about what a
replicate costs on the 56-decision arm; nobody has timed it.

THE CEILING IS LOWER HERE, AND THAT IS A REAL CONCESSION
--------------------------------------------------------
`choice_bootstrap`'s stopping rule wants the endpoint nearest 1.0 to sit
more than ten Monte Carlo standard errors away from 1.0, so that Monte
Carlo noise cannot flip the verdict. When the endpoint is genuinely near
1.0 -- which is the whole question here -- that condition can never be
met, and the rule runs to the ceiling by construction. So the ceiling is
lowered and the diagnostic is published instead: every interval below
carries the Monte Carlo error of both its endpoints, and the reader can
see for themselves whether R is the binding constraint on the verdict. An
endpoint 0.04 from 1.0 with a Monte Carlo error of 0.01 is a verdict that
R could flip; the same endpoint with an error of 0.002 is not.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..common.logging_setup import get_logger
from .choice import ChoiceData
from .choice_bootstrap import (
    MCSE_WIDTH_TARGET,
    R_BATCH,
    R_MIN,
    VERDICT_MARGIN,
    endpoint_errors,
    refit,
    resample_decisions,
    rows_by_decision,
)
from .choice_sandwich import BOUNDARY_TOL

_log = get_logger("models.network_bootstrap")

#: `choice_bootstrap.R_MIN`, used as a ceiling as well as a floor, and
#: declared as a cost ceiling rather than a convergence claim. At the
#: measured 4.5 wall-seconds a replicate the project's ceiling of 4,000
#: would be five hours per bootstrap. The defence is not that 500 is
#: enough in general; it is that every endpoint carries its own Monte
#: Carlo error, so a reader can see whether 500 is enough for THIS
#: verdict. See the module docstring.
R_CAP = 500

WORKERS = max(1, min(6, (os.cpu_count() or 2) - 1))

#: Replicates between progress lines. A run that takes hours
#: with no output is a run nobody can tell has hung.
PROGRESS_EVERY = 25

__all__ = ["PROGRESS_EVERY", "R_CAP", "WORKERS", "draws_for",
           "parallel_bootstrap"]

_STATE: dict = {}


def _init(d: ChoiceData, theta: np.ndarray) -> None:
    _STATE["d"], _STATE["theta"] = d, theta
    _STATE["rows"] = rows_by_decision(d)


def _one(draw: np.ndarray) -> np.ndarray:
    return refit(resample_decisions(_STATE["d"], draw, _STATE["rows"]),
                 _STATE["theta"])


def draws_for(n_units: int, rng, members: list | None,
              count: int) -> list[np.ndarray]:
    """The next ``count`` resampling draws, in the sequential loop's order.

    ``choice_bootstrap.bootstrap`` calls ``rng.integers`` once per
    replicate inside its batch loop, so consuming the generator the same
    number of times in the same order reproduces its draws exactly.
    """
    out = []
    for _ in range(count):
        pick = rng.integers(0, n_units, n_units)
        out.append(np.concatenate([members[p] for p in pick])
                   if members is not None else pick)
    return out


def parallel_bootstrap(d: ChoiceData, theta_hat: np.ndarray, seed: int,
                       cluster: np.ndarray | None = None,
                       cap: int = R_CAP,
                       workers: int = WORKERS) -> dict:
    """Resample DECISIONS (or whole metros) with replacement and refit.

    Same return shape as `choice_bootstrap.bootstrap`, plus ``capped``,
    which says whether the run stopped because the stopping rule was
    satisfied or because it hit the ceiling. Reporting an interval from a
    capped run as though it had converged is the failure this field
    exists to prevent.
    """
    rng = np.random.default_rng(seed)
    interior = np.flatnonzero(np.exp(theta_hat) > BOUNDARY_TOL)
    units = (np.unique(cluster) if cluster is not None
             else np.arange(d.n_decisions))
    members = ([np.flatnonzero(cluster == u) for u in units]
               if cluster is not None else None)

    label = "metros" if cluster is not None else "decisions"
    reps: list[np.ndarray] = []
    trace, errors, settled = [], {}, False
    started = time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                             initargs=(d, theta_hat)) as pool:
        while len(reps) < cap:
            batch = draws_for(len(units), rng, members,
                              min(R_BATCH, cap - len(reps)))
            # Mapped in slices purely so progress is observable on a run
            # that takes hours. The draws were generated in one ordered
            # list above, so slicing changes nothing about which draw is
            # which replicate.
            for start in range(0, len(batch), PROGRESS_EVERY):
                reps.extend(pool.map(_one, batch[start:start + PROGRESS_EVERY],
                                     chunksize=1))
                _log.info("bootstrap over %s: %d/%d replicates, %.1f s each",
                          label, len(reps), cap,
                          (time.time() - started) / len(reps))
            beta = np.exp(np.array(reps))
            errors = {int(k): endpoint_errors(beta[:, k], seed + 7)
                      for k in range(beta.shape[1])}
            settled = all(
                errors[k]["near_endpoint_mcse_share_of_width"]
                < MCSE_WIDTH_TARGET
                and errors[k]["near_endpoint_distance_from_one_in_mcse"]
                > VERDICT_MARGIN for k in interior)
            trace.append({"replicates": len(reps), "settled": bool(settled)})
            if len(reps) >= R_MIN and settled:
                break
    _log.info("bootstrap over %s finished: %d replicates in %.0f s, "
              "settled=%s", label, len(reps), time.time() - started, settled)
    return {"beta": np.exp(np.array(reps)), "replicates": len(reps),
            "n_units": int(len(units)), "trace": trace,
            "seconds": float(time.time() - started),
            "settled": bool(settled), "capped": bool(not settled),
            "cap": int(cap), "endpoint_errors": errors}


def agreement_check(d: ChoiceData, theta_hat: np.ndarray, seed: int,
                    n: int = 4) -> dict:
    """Do the parallel and the sequential drivers give the same replicates?

    The claim "this is `choice_bootstrap.bootstrap` on more cores" is
    cheap to assert and cheap to check, so it is checked: the same rng,
    the same draws, the same refits, compared on beta.
    """
    rows = rows_by_decision(d)
    rng_a = np.random.default_rng(seed)
    rng_b = np.random.default_rng(seed)
    batch = draws_for(d.n_decisions, rng_a, None, n)
    serial = np.array([np.exp(refit(resample_decisions(d, g, rows),
                                    theta_hat))
                       for g in draws_for(d.n_decisions, rng_b, None, n)])
    with ProcessPoolExecutor(max_workers=min(n, WORKERS), initializer=_init,
                             initargs=(d, theta_hat)) as pool:
        par = np.exp(np.array(list(pool.map(_one, batch, chunksize=1))))
    return {"replicates_compared": int(n),
            "max_abs_difference_in_beta": float(np.abs(par - serial).max())}
