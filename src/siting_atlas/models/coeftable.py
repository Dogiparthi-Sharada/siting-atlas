"""Reporting fitted coefficients in the units a reader thinks in.

The transform
-------------
The model is fitted on standardised covariates, because a spline basis in
quarters and a covariate in dollars differ by four orders of magnitude and
the optimiser should not have to care. But a coefficient "per standard
deviation of median household income" is not a quantity anyone can check
against the world, so the table is reported in raw units. Since
standardisation is linear the translation is exact:

    eta = b0 + (time terms) + sum_j b_j * (x_j - m_j) / s_j
        = [ b0 - sum_j b_j m_j / s_j ] + (time terms) + sum_j (b_j/s_j) x_j

so b_raw = A @ b_std for a matrix A that is the identity except for the
intercept row and the covariate diagonal.

Why the covariance has to go through the SAME matrix
-----------------------------------------------------
It is tempting to rescale the standard errors the way the coefficients were
rescaled — divide each covariate's SE by its own sd and leave the intercept
alone. That is right for the covariates and wrong for the intercept, and the
error is not small. The raw intercept is no longer one estimated quantity; it
is a LINEAR COMBINATION of the intercept and every covariate coefficient, and
its variance therefore picks up all of their variances and every covariance
between them:

    Var(b0_raw) = Var(b0) - 2 sum_j (m_j/s_j) Cov(b0, b_j)
                          + sum_j sum_k (m_j m_k / s_j s_k) Cov(b_j, b_k)

Leaving the intercept's SE untouched dropped those terms entirely. On a
covariate scaled like real income it reported 0.176 where the truth is 0.252
— 1.4x too narrow — and the printed table contradicted itself, with
coefficient/std_error of -42.6 against a z column reading -30.5. Both
numbers went into ``hazard_report.json``, where the narrow one is the
dangerous one: it is the one that makes a baseline level look better
determined than it is.

The delta method for a linear map needs no approximation at all. A single
``A @ C @ A.T`` gets every term above for free, and it stays correct if the
set of covariates or the standardisation ever changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class Scaler:
    """Centre and scale, with the TRAINING moments retained.

    Retained, not recomputed, because standardising the test split by its own
    mean and standard deviation is leakage: the held-out rows would be
    described using information from the held-out rows.

    It lives beside :func:`raw_scale_map` because the two are the forward and
    the inverse of the same change of units, and a fix applied to one that is
    not applied to the other is a silent inconsistency in the reported table.
    """

    mean: np.ndarray = field(default_factory=lambda: np.zeros(0))
    sd: np.ndarray = field(default_factory=lambda: np.ones(0))

    def learn(self, x: np.ndarray) -> Scaler:
        self.mean = x.mean(axis=0)
        sd = x.std(axis=0, ddof=0)
        # A constant column has sd 0. Dividing by it gives inf; leaving the
        # scale at 1 leaves a constant column, which the intercept absorbs
        # and statsmodels reports as a redundant coefficient rather than a
        # crash.
        self.sd = np.where(sd > 0, sd, 1.0)
        return self

    def apply(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean) / self.sd


def raw_scale_map(n_params: int, n_covariates: int, sd: np.ndarray,
                  mean: np.ndarray) -> np.ndarray:
    """The matrix A with ``b_raw = A @ b_standardised``.

    The covariates are assumed to occupy the LAST ``n_covariates`` columns of
    the design and the intercept the first, which is how
    :meth:`DiscreteTimeHazard.design` assembles it. Returning the map rather
    than applying it keeps the coefficient transform and the covariance
    transform provably consistent — there is only one description of the
    change of units and both callers read it.
    """
    a = np.eye(n_params)
    for j in range(n_covariates):
        col = n_params - n_covariates + j
        a[col, col] = 1.0 / sd[j]
        a[0, col] = -mean[j] / sd[j]
    return a


def coefficient_table(names, params, cov, *, transform=None) -> pd.DataFrame:
    """Coefficients, standard errors and tests, all on one scale.

    ``z`` and ``p_value`` are recomputed from the reported coefficient and
    the reported standard error rather than copied from the fit. That is the
    only way the table can be internally consistent after a change of units:
    a reader who divides the coefficient column by the std_error column must
    land on the z column, and if those two disagree there is no way to tell
    from the outside which one to believe.

    For the covariates the recomputation is a no-op — (b/s)/(se/s) is b/se —
    so this changes nothing anyone was relying on. It changes the intercept,
    which is exactly the term whose scale moved.
    """
    params = np.asarray(params, dtype=float)
    cov = np.asarray(cov, dtype=float)
    if transform is not None:
        params = transform @ params
        cov = transform @ cov @ transform.T

    se = np.sqrt(np.clip(np.diag(cov), 0.0, np.inf))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(se > 0, params / se, np.nan)
    p = 2.0 * stats.norm.sf(np.abs(z))

    return pd.DataFrame({
        "term": list(names),
        "coefficient": params,
        "std_error": se,
        "z": z,
        "p_value": p,
        "hazard_ratio": np.exp(params),
    })


def entry_row_means(frame: pd.DataFrame, covariates, id_col: str,
                    time_col: str) -> np.ndarray:
    """Covariate means with each UNIT counted once, at the row it enters on.

    The trap this exists to avoid
    -----------------------------
    Averaging the covariates over the risk-set ROWS is survivor-weighted. A
    unit that enables in the second quarter contributes two rows; one that
    never enables contributes thirty-two. So the row mean is sixteen times
    more a description of the units that did NOT get chosen, and on any
    covariate that predicts the event it is pulled away from the population
    mean in the direction of the non-events.

    On the fixture, ``x_demand`` has a population mean of 0.00 and a
    risk-set row mean of -0.15 — a seventh of a standard deviation, all of
    it selection. Evaluating "the baseline hazard at the covariate means"
    there reported a curve 13% below the one the data was generated with,
    uniformly, at every quarter. The fit was fine; only the published curve
    was wrong, which is the worst place for it to be, because a curve is
    what gets put on a slide.

    Taking one row per unit — the first, i.e. the quarter it enters the risk
    set — weights every unit equally and describes the cohort as it stood
    when the clock started. For time-invariant covariates that is exactly the
    population mean; for time-varying ones it is the entry value, which is
    the honest reference point for a baseline curve over elapsed time.
    """
    names = list(covariates)
    if not names:
        return np.zeros(0)
    if id_col not in frame.columns:
        # No unit column means the caller is not handing us a panel; the row
        # mean is then the only mean available and is not survivor-weighted.
        return frame.loc[:, names].to_numpy(dtype=float).mean(axis=0)

    # Sorting rather than trusting the incoming order: ``first()`` on an
    # unsorted group returns whichever row happened to come first, and a
    # frame that has been through a split or a concat carries no promise
    # about that.
    ordered = frame.sort_values(time_col, kind="mergesort")
    first = ordered.groupby(id_col, sort=False)[names].first()
    return first.to_numpy(dtype=float).mean(axis=0)
