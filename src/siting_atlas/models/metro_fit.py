"""The two model forms prereg section 5 fixes, and nothing else.

    logistic   P(at least one opening in metro m, year t)
    count      Poisson and negative binomial on the number of openings,
               because 2020 and 2021 put 100 and 99 openings into 49 and 53
               metros, so several metros take more than one

Both are estimated by maximum likelihood on the training years only. Three
implementation choices are recorded here rather than buried, because each
could move a result and none of them is specified by the prereg.

**Transforms.** Metro scale is log-normal to a good approximation: households
runs from about 4,000 to about 7,000,000 across the 935 CBSAs. A linear term
in households makes New York a 1,700-sigma observation and the fit is then a
description of New York. Count-like columns therefore enter as log1p, rates
enter raw. The map is fixed in `TRANSFORM` and does not depend on any
outcome.

**Standardisation is computed inside the training fold.** Prereg section 6
flags a Simpson's-paradox trap this project has already hit "twice, the
second time inside a standardisation". Centring on statistics that include
the held-out year would leak the held-out year's distribution.

**Unscorable rows.** A metro-year with a missing covariate is dropped from
the FIT and kept in the PREDICTION universe with the constant-null
probability, which is the training base rate. Dropping it from the universe
instead would be selection on data availability, and availability is
correlated with metro size -- prereg section 8.2. Nothing is imputed: the
covariate stays missing and the row is scored by the null, not by a guess at
what the covariate would have been.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ..common.logging_setup import get_logger

_log = get_logger("models.metro_fit")

__all__ = ["TRANSFORM", "Design", "build_design", "fit_arm", "Prediction"]

#: "log1p" for count-like and heavily right-skewed columns, "raw" otherwise.
TRANSFORM = {
    "permit_units_total": "log1p",
    "permits_yoy_pct": "raw",
    "wage_freight_handler": "log1p",
    "wage_all_occupations": "log1p",
    "metro_employment": "log1p",
    "traffic_proximity": "log1p",
    "diesel_pm": "raw",
    "households": "log1p",
    "population": "log1p",
    "median_household_income": "log1p",
    "facilities_open_prior": "log1p",
    "dist_nearest_outside_prior": "log1p",
}


@dataclass
class Design:
    """A transformed, not-yet-standardised covariate matrix and its mask."""

    columns: list[str]
    values: np.ndarray            # (n, k), NaN where the source was missing
    complete: np.ndarray          # (n,) bool, True where every column is set


def build_design(frame: pd.DataFrame, columns: list[str]) -> Design:
    """Apply `TRANSFORM` column by column. No centring, no filling."""
    cols = list(columns)
    out = np.full((len(frame), len(cols)), np.nan, dtype=float)
    for j, c in enumerate(cols):
        v = frame[c].to_numpy(dtype=float)
        if TRANSFORM[c] == "log1p":
            with np.errstate(invalid="ignore"):
                v = np.where(v >= 0, np.log1p(v), np.nan)
        out[:, j] = v
    return Design(cols, out, np.isfinite(out).all(axis=1))


@dataclass
class Prediction:
    """One arm's probability of at least one opening, per row."""

    p: np.ndarray
    scored: np.ndarray            # True where the model, not the null, ran
    null_p: float
    diagnostics: dict = field(default_factory=dict)


def _standardise(x_tr: np.ndarray, x_te: np.ndarray):
    """Centre and scale on the TRAINING rows only."""
    mu = x_tr.mean(axis=0)
    sd = x_tr.std(axis=0, ddof=0)
    # A zero-variance training column carries no information; scaling it by
    # zero would produce inf. Leave it centred and flat, and let the fit
    # give it whatever coefficient it likes on a column of zeros.
    sd = np.where(sd > 0, sd, 1.0)
    return (x_tr - mu) / sd, (x_te - mu) / sd


def _glm(y, x, family):
    """Fit, falling back to a small ridge if the MLE does not resolve.

    Separation is a real possibility at 935 metros with a 2-5% event rate and
    a strongly scale-ordered covariate. An unconverged fit that still returns
    parameters is worse than a penalised one, so the fallback is explicit and
    is reported in the diagnostics.
    """
    xc = sm.add_constant(x, has_constant="add")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = sm.GLM(y, xc, family=family)
        try:
            res = model.fit(maxiter=200)
            if np.all(np.isfinite(res.params)) and res.converged:
                return res, "mle"
        except Exception as exc:                       # noqa: BLE001
            _log.debug("MLE failed (%s); falling back to ridge", exc)
        res = model.fit_regularized(alpha=1e-3, L1_wt=0.0)
        return res, "ridge"


def fit_arm(frame: pd.DataFrame, columns: list[str], *,
            train: np.ndarray, test: np.ndarray, form: str) -> Prediction:
    """Fit one model form on `train` rows and score `test` rows.

    `form` is "logit", "poisson" or "negbin". All three are scored as a
    probability of at least one opening so that AUC, Brier and ECE mean the
    same thing across forms:

        logit     p               directly
        poisson   1 - exp(-lam)
        negbin    1 - (1 + a lam) ** (-1/a)
    """
    des = build_design(frame, columns)
    y_any = frame["any_event"].to_numpy(float)
    y_cnt = frame["events"].to_numpy(float)

    fit_rows = train & des.complete
    null_p = float(y_any[train].mean())
    p = np.full(len(frame), null_p)
    diag = {"n_train_rows": int(train.sum()),
            "n_train_fitted": int(fit_rows.sum()),
            "n_train_dropped_incomplete": int((train & ~des.complete).sum()),
            "n_test_rows": int(test.sum()),
            "n_test_scored": int((test & des.complete).sum()),
            "n_test_on_null": int((test & ~des.complete).sum()),
            "n_test_events_on_null":
                int(y_any[test & ~des.complete].sum()),
            "null_p": round(null_p, 6)}

    if fit_rows.sum() < 30 or y_any[fit_rows].sum() < 5:
        diag["status"] = "not_fitted_insufficient_training_rows"
        return Prediction(p, np.zeros(len(frame), bool), null_p, diag)

    x_tr, x_te = _standardise(des.values[fit_rows], des.values)
    if form == "logit":
        res, how = _glm(y_any[fit_rows], x_tr, sm.families.Binomial())
        eta = sm.add_constant(x_te, has_constant="add") @ res.params
        fitted = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
    elif form == "poisson":
        res, how = _glm(y_cnt[fit_rows], x_tr, sm.families.Poisson())
        eta = sm.add_constant(x_te, has_constant="add") @ res.params
        fitted = 1.0 - np.exp(-np.exp(np.clip(eta, -30, 20)))
    elif form == "negbin":
        alpha = _negbin_alpha(y_cnt[fit_rows], x_tr)
        res, how = _glm(y_cnt[fit_rows], x_tr,
                        sm.families.NegativeBinomial(alpha=alpha))
        eta = sm.add_constant(x_te, has_constant="add") @ res.params
        lam = np.exp(np.clip(eta, -30, 20))
        fitted = 1.0 - (1.0 + alpha * lam) ** (-1.0 / alpha)
        diag["negbin_alpha"] = round(float(alpha), 6)
    else:
        raise ValueError(f"unknown form {form!r}")

    scored = des.complete.copy()
    p = np.where(scored, np.clip(fitted, 1e-9, 1 - 1e-9), null_p)
    diag["estimator"] = how
    diag["status"] = "fitted"
    diag["coefficients"] = {
        name: round(float(v), 5) for name, v in
        zip(["const", *columns], np.asarray(res.params), strict=True)}
    return Prediction(p, scored, null_p, diag)


def _negbin_alpha(y: np.ndarray, x: np.ndarray) -> float:
    """Dispersion from the standard Poisson-residual auxiliary regression.

    Cameron & Trivedi's method-of-moments step: fit Poisson, then regress
    ((y - mu)^2 - y) / mu on mu through the origin. Estimating alpha on the
    training rows keeps it out of the held-out year like every other
    parameter.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pois = sm.GLM(y, sm.add_constant(x, has_constant="add"),
                      family=sm.families.Poisson()).fit(maxiter=200)
    mu = np.clip(pois.mu, 1e-8, None)
    aux = ((y - mu) ** 2 - y) / mu
    alpha = float(np.dot(aux, mu) / np.dot(mu, mu)) if np.any(mu) else 1.0
    return float(np.clip(alpha, 1e-3, 50.0))
