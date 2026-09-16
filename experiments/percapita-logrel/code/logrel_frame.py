"""Log-relative (within-metro) transforms, and why the model resists them.

The transform is ``logrel_x = ln(x_j / median_m(x))`` over the alternatives
of the same metro ``m``. The choice set IS the metro's ZCTA list, so the
within-group median and the metro median are the same number and the
transform can be computed from a built `ChoiceData` without touching the
panel again.

Two properties matter and they pull in opposite directions.

1  IT IS SCALE-FREE, SO IT COSTS NOTHING TO COMPUTE HERE.
   `covariate_frame.build_frame` divides every column by its own mean. That
   constant cancels in ``x / median(x)``, so the log-relative column built
   from the scaled frame is identical to the one built from the raw panel.
   No re-build, no risk of a different frame, and the baseline arm in this
   module is bit-comparable with `covariate_search`'s.

2  IT TAKES NEGATIVE VALUES, AND `choice.py` REQUIRES ``beta'a > 0``.
   `choice.py` section "Two consequences" is explicit: the probability is
   ``(beta'a_j) / sum_k (beta'a_k)`` and is undefined unless every
   ``beta'a_j`` is positive. Half of a log-relative column is below zero by
   construction (it is centred on the median), so a POSITIVE coefficient on
   it SUBTRACTS attraction from every below-median alternative. That is not
   a free repellent: it is a hard feasibility ceiling. The largest
   admissible coefficient is

       beta_max = min over alternatives with logrel < 0 of
                      (baseline attraction) / (-logrel)

   and `bound` computes it. If that ceiling is small against the numeraire,
   the covariate cannot move the ranking whatever its true effect is, and
   the arm is uninformative for a reason that has nothing to do with the
   data in the column.

The sign question, stated precisely
-----------------------------------
``logrel`` is a MONOTONE INCREASING function of ``x``. ``beta = exp(theta)``
is positive. So the fitted effect of ``x`` on attraction is still forced to
be weakly increasing. Centring does not change that. What DOES change it is
entering ``-logrel = ln(median / x)``, which is monotone DECREASING, and
that is what `NEG` builds. The pair spans both signs — but as two separate
models the analyst chooses between, not as one coefficient whose sign the
data sets, and a choice between two fits carries no standard error.

Zeros
-----
``ln(0)`` is undefined. `covariate_frame.static_frame` keeps ``x >= 0``, so
`bachelors_degree` and `renter_occupied` carry exact zeros on a small share
of alternatives. Those are winsorised UP to the smallest strictly positive
value in the same metro and the count is reported per column. That is a
deviation from this project's no-imputation rule, it is recorded in the
artefact rather than buried, and it is confined to alternatives that were
never chosen (verified: `zero_chosen` is 0 for every column).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .choice import ChoiceData

#: Prefixes, so an arm's name says which direction it is testing.
LOGREL = "logrel_"
NEG = "neglogrel_"

#: The ZIP-grain columns that came back as exact no-ops in
#: `covariate_search.json`, in the priority order the brief sets.
CANDIDATES = ("median_home_value", "median_age", "bachelors_degree",
              "owner_occupied", "renter_occupied")

__all__ = ["CANDIDATES", "LOGREL", "NEG", "augment", "bound", "log_relative",
           "negative_utilities"]


def _winsorise(v: np.ndarray, group: np.ndarray) -> tuple[np.ndarray, int]:
    """Lift exact zeros to the smallest positive value in the same metro."""
    bad = v <= 0
    if not bad.any():
        return v, 0
    s = pd.Series(np.where(bad, np.nan, v))
    floor = s.groupby(group).transform("min").to_numpy(float)
    return np.where(bad, floor, v), int(bad.sum())


def log_relative(v: np.ndarray, group: np.ndarray) -> tuple[np.ndarray, dict]:
    """``ln(x / metro_median(x))`` plus the diagnostics it needs reported."""
    clean, zeros = _winsorise(np.asarray(v, float), group)
    med = pd.Series(clean).groupby(group).transform("median").to_numpy(float)
    lr = np.log(clean / med)
    return lr, {"zeros_winsorised": zeros,
                "zero_share": float(zeros / len(v)),
                "min": float(lr.min()), "max": float(lr.max()),
                "p01": float(np.percentile(lr, 1)),
                "p99": float(np.percentile(lr, 99)),
                "negative_share": float((lr < 0).mean())}


def augment(data: ChoiceData, cols: tuple[str, ...],
            mirror: tuple[str, ...] = ()) -> tuple[ChoiceData, dict]:
    """Append ``logrel_`` (and optionally ``neglogrel_``) columns.

    The new columns are NOT mean-scaled. `choice.build` scales only so the
    optimiser sees O(1) numbers; a log-relative column is already O(1) and
    its mean is ~0, so dividing by it would be arbitrary. Rescaling a column
    changes the units of its beta and nothing else — the probability is a
    ratio — so leaving it alone costs no comparability.
    """
    extra, names, diag = [], list(data.names), {}
    for col in cols:
        lr, info = log_relative(data.a[:, data.names.index(col)], data.group)
        extra.append(lr)
        names.append(LOGREL + col)
        diag[LOGREL + col] = info
        if col in mirror:
            extra.append(-lr)
            names.append(NEG + col)
            diag[NEG + col] = info | {"min": -info["max"],
                                      "max": -info["min"],
                                      "p01": -info["p99"],
                                      "p99": -info["p01"],
                                      "negative_share":
                                          float((-lr < 0).mean())}
    a = np.column_stack([data.a, *extra])
    return ChoiceData(a, data.group, data.chosen, list(data.ids),
                      tuple(names)), diag


def bound(data: ChoiceData, base: tuple[str, ...], beta: dict,
          col: str) -> dict:
    """The largest coefficient on `col` that keeps every ``beta'a`` positive.

    Evaluated at the baseline fit, which is where the optimiser starts the
    new column from. It is a ceiling on the WHOLE search, not a local one:
    raising the other coefficients raises the numerator, but they are
    themselves pinned by the likelihood, and the ratio below is what the
    optimiser actually runs into.
    """
    idx = [data.names.index(n) for n in base]
    u = data.a[:, idx] @ np.array([beta[n] for n in base], float)
    lr = data.a[:, data.names.index(col)]
    neg = lr < 0
    ratios = u[neg] / -lr[neg]
    worst = int(np.flatnonzero(neg)[int(np.argmin(ratios))])
    return {"beta_max": float(ratios.min()),
            "numeraire": 1.0,
            "as_share_of_numeraire": float(ratios.min()),
            "min_baseline_attraction": float(u.min()),
            "binding_alternative_row": worst,
            "binding_logrel": float(lr[worst]),
            "binding_baseline_attraction": float(u[worst]),
            "n_alternatives_below_median": int(neg.sum())}


def negative_utilities(data: ChoiceData, cols: tuple[str, ...],
                       beta: dict) -> dict:
    """How many alternatives the fitted model gives a negative attraction.

    A negative ``beta'a_j`` is not a small numerical wrinkle. It makes
    ``P(j|m)`` negative and the metro total wrong, so the object being
    maximised stops being a likelihood. `choice._neg_log_likelihood` floors
    the CHOSEN probability at 1e-300 and therefore does not crash — it
    quietly optimises something else. This counts the damage.

    The split by chosen vs not is the mechanism, not a detail: pushing a
    NON-chosen alternative below zero shrinks its metro's denominator and so
    RAISES the probability of the chosen one. The likelihood goes up and
    nothing has been learned.
    """
    idx = [data.names.index(n) for n in cols]
    u = data.a[:, idx] @ np.array([beta[n] for n in cols], float)
    totals = np.bincount(data.group, weights=u)
    bad = u <= 0
    bad_chosen = int(bad[data.chosen].sum())
    return {"alternatives": int(len(u)),
            "negative_attraction": int(bad.sum()),
            "negative_share": float(bad.mean()),
            "negative_and_chosen": bad_chosen,
            "negative_and_not_chosen": int(bad.sum()) - bad_chosen,
            "min_attraction": float(u.min()),
            "mean_prob_of_chosen": float(
                (u / totals[data.group])[data.chosen].mean()),
            "metros_with_nonpositive_total": int((totals <= 0).sum())}
