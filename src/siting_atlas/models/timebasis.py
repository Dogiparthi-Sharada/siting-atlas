"""The baseline hazard: how the risk of enablement moves with time itself.

Why not just put ``t`` in the regression
----------------------------------------
A linear term in quarter says the log-log hazard changes by the same amount
every quarter for eight years — monotone, forever, no exceptions. The real
series is not monotone and the reasons are obvious once stated: a build-out
push in 2020-21, a pause in 2022-23, capacity coming back later. Force a
straight line through a hump and the misfit does not stay in the time term.
It leaks into any covariate that happens to trend, and rent growth and
permit activity both trend. You then read a coefficient on rent growth that
is partly the shape of the calendar.

Two flexible options, both here:

    dummies   one indicator per quarter. Maximally flexible, no shape
              assumed. With 32 quarters and few events some quarters have
              zero events, the indicator separates perfectly, and the fit
              blows up or silently returns a coefficient of -25.
    spline    a restricted cubic spline in t. Smooth, borrows strength
              across neighbouring quarters, costs 3-5 parameters instead of
              31. This is the default and it is the right default for a
              panel with a few hundred events.

"Restricted" means the fit is forced to be linear outside the outer knots.
That restriction exists because an unrestricted cubic does whatever it likes
in the tails, where there is least data, and a hazard that shoots to 1.0 in
the last quarter of the sample is an artefact of the basis, not a finding.
"""

from __future__ import annotations

import numpy as np

# Harrell's recommended knot placement, as percentiles of the observed
# values, indexed by the number of knots. Quantiles rather than an even grid
# so the flexibility sits where the data are.
_KNOT_PERCENTILES = {
    3: (10, 50, 90),
    4: (5, 35, 65, 95),
    5: (5, 27.5, 50, 72.5, 95),
    6: (5, 23, 41, 59, 77, 95),
    7: (2.5, 18.33, 34.17, 50, 65.83, 81.67, 97.5),
}


def choose_knots(t: np.ndarray, n_knots: int = 4) -> np.ndarray:
    """Knot locations at the recommended percentiles of ``t``.

    Duplicate knots are dropped. A short panel can put two percentiles on
    the same quarter, and a repeated knot makes the basis singular — which
    surfaces much later as an unhelpful linear-algebra error rather than
    here, where the cause is visible.
    """
    if n_knots not in _KNOT_PERCENTILES:
        raise ValueError(
            f"n_knots={n_knots} not supported; choose one of "
            f"{sorted(_KNOT_PERCENTILES)}")
    pct = _KNOT_PERCENTILES[n_knots]
    knots = np.unique(np.percentile(np.asarray(t, dtype=float), pct))
    if len(knots) < 3:
        raise ValueError(
            f"only {len(knots)} distinct knot(s) from {len(np.unique(t))} "
            f"distinct time values; the panel is too short for a spline "
            f"baseline — use baseline='dummies'")
    return knots


def restricted_cubic_spline(t: np.ndarray,
                            knots: np.ndarray) -> np.ndarray:
    """Harrell's restricted cubic spline basis: k knots give k-1 columns.

    Column 0 is ``t`` itself; the remaining columns are the cubic pieces,
    each already constrained to go linear beyond the outer knots. The
    division by ``(k_last - k_first) ** 2`` is not cosmetic: without it the
    cubic terms are on the scale of t-cubed, which for t up to 32 is ~3e4,
    and the GLM's iteratively reweighted least squares loses precision
    against covariates of order one.
    """
    t = np.asarray(t, dtype=float)
    k = np.asarray(knots, dtype=float)
    n_k = len(k)
    if n_k < 3:
        raise ValueError("a restricted cubic spline needs at least 3 knots")

    scale = (k[-1] - k[0]) ** 2
    cols = [t]
    for j in range(n_k - 2):
        num = (_cube_plus(t - k[j])
               - _cube_plus(t - k[-2]) * (k[-1] - k[j]) / (k[-1] - k[-2])
               + _cube_plus(t - k[-1]) * (k[-2] - k[j]) / (k[-1] - k[-2]))
        cols.append(num / scale)
    return np.column_stack(cols)


def _cube_plus(x: np.ndarray) -> np.ndarray:
    """(x)_+ cubed — zero where x is negative."""
    return np.where(x > 0, x, 0.0) ** 3


def baseline_design(t: np.ndarray, *, spec: str = "spline",
                    n_knots: int = 4,
                    knots: np.ndarray | None = None
                    ) -> tuple[np.ndarray, list[str], np.ndarray | None]:
    """Build the time-baseline block of the design matrix.

    Returns ``(matrix, column_names, knots)``. The knots come back so the
    caller can reuse the TRAINING knots when building the design for held-out
    data: re-choosing knots from the test set would put the basis on a
    different footing and the fitted coefficients would no longer apply. That
    is a leakage-shaped bug that produces plausible predictions.
    """
    t = np.asarray(t, dtype=float)

    if spec == "spline":
        used = choose_knots(t, n_knots) if knots is None else np.asarray(
            knots, dtype=float)
        matrix = restricted_cubic_spline(t, used)
        names = ["t"] + [f"t_spline{j + 1}" for j in
                         range(matrix.shape[1] - 1)]
        return matrix, names, used

    if spec == "dummies":
        # The reference quarter is the first one, so every coefficient reads
        # as "log-log hazard relative to the opening quarter of the panel".
        # Levels come from TRAINING when supplied: a quarter that appears
        # only in the test split would otherwise add a column the fitted
        # model has no coefficient for.
        levels = np.unique(t)[1:] if knots is None else np.asarray(knots)
        matrix = np.column_stack([(t == lv).astype(float) for lv in levels])
        names = [f"t_is_{int(lv)}" for lv in levels]
        return matrix, names, levels

    if spec == "linear":
        # Kept only so a specification test can demonstrate that it fits
        # worse. It is not a defensible baseline; see the module docstring.
        return t.reshape(-1, 1), ["t"], None

    raise ValueError(
        f"unknown baseline spec {spec!r}; expected 'spline', 'dummies' or "
        f"'linear'")
