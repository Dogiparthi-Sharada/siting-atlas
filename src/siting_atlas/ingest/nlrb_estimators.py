"""Capture-recapture estimators, and what each one is allowed to claim.

Split out of `ingest.nlrb_capture` so that the arithmetic can be tested
against the textbook formulae without loading any data. Nothing here knows
what an Amazon facility is.

Three estimators, reported together on purpose, because they disagree and
the disagreement is the finding:

    Lincoln-Petersen / Chapman   assumes the lists are INDEPENDENT
    Chao's lower bound           allows HETEROGENEOUS catchability
    log-linear over three lists  ESTIMATES the pairwise dependence

Our two lists are not independent - OSHA inspects where workers are hurt,
NLRB dockets where workers organise, and both are driven by grievance.
Positive dependence inflates the overlap, which deflates n1*n2/M. So the
first family gives a LOWER BOUND ON THE POPULATION and therefore an UPPER
BOUND ON COVERAGE, and it must be reported in that direction and never as a
point estimate.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np
import statsmodels.api as sm

__all__ = ["Fit", "chao_lower_bound", "chapman", "lincoln_petersen",
           "loglinear_three_list", "lognormal_ci", "odds_ratio"]

Z = 1.959963984540054   # two-sided 95%


def lincoln_petersen(n1: int, n2: int, m: int) -> float:
    """n1*n2/m. The textbook ratio, kept only as the reference point."""
    if m <= 0:
        raise ValueError("no overlap: Lincoln-Petersen is undefined")
    return n1 * n2 / m


def chapman(n1: int, n2: int, m: int) -> tuple[float, float]:
    """Chapman's (1951) bias correction, with its variance.

    The ratio estimator has no finite expectation when the overlap can be
    zero and is biased upward at small m. Chapman's version is close to
    unbiased when n1*n2/N exceeds about 10, which holds comfortably here.
    """
    if m < 0:
        raise ValueError("negative overlap")
    est = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    var = ((n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m)
           / ((m + 1) ** 2 * (m + 2)))
    return est, var


def chao_lower_bound(s_obs: int, f1: int, f2: int) -> tuple[float, float]:
    """Chao's (1987) lower bound, valid under heterogeneous catchability.

    `f1` is the count seen on exactly one list, `f2` on exactly two. With
    two lists f2 IS the overlap. The bias-corrected form is used because f2
    is small enough here for the uncorrected one to run hot.

    It is a LOWER bound by construction, and the direction survives our
    violation: positive dependence between the lists moves units out of f1
    and into f2, which shrinks f1^2/2f2. So dependence makes Chao understate
    as well, and it stays a bound rather than becoming a point estimate.
    """
    if f2 > 0:
        extra = f1 * (f1 - 1) / (2 * (f2 + 1))
        ratio = f1 / f2
        var = f2 * (0.5 * ratio ** 2 + ratio ** 3 + 0.25 * ratio ** 4)
    else:
        extra = f1 * (f1 - 1) / 2
        var = float(extra)
    return s_obs + extra, var


def lognormal_ci(est: float, s_obs: int, var: float) -> tuple[float, float]:
    """Chao's log-normal interval, built on the UNSEEN count.

    A symmetric normal interval on N can dip below the number of places
    already in hand, which is impossible. Transforming the unseen count
    instead makes the lower limit respect what has been observed.
    """
    unseen = est - s_obs
    if unseen <= 0:
        raise ValueError("nothing unseen: the interval is undefined")
    c = math.exp(Z * math.sqrt(math.log(1 + var / unseen ** 2)))
    return s_obs + unseen / c, s_obs + unseen * c


def odds_ratio(a: float, b: float, c: float, d: float) -> float:
    """ad/bc for a 2x2 slice of the capture table. 1.0 means independent.

    Reported rather than assumed. The whole complaint against the naive
    estimate is that the lists are positively dependent; with three lists
    that stops being an argument and becomes a number.
    """
    if b <= 0 or c <= 0:
        return float("inf") if a * d > 0 else float("nan")
    return (a * d) / (b * c)


# --- three-list log-linear model ---------------------------------------

@dataclass(frozen=True)
class Fit:
    """One log-linear model over three lists, and what it implies."""

    name: str
    df: int
    deviance: float
    aic: float
    unseen: float
    unseen_lo: float
    unseen_hi: float


#: Fienberg (1972). Every hierarchical model on three lists that contains
#: the three main effects. The last has zero residual degrees of freedom: it
#: is the "no three-way interaction" model, exactly identified, and the most
#: general thing three lists can support. There is nothing left over to test
#: it with, which is why its interval is so wide and why that width is
#: honest rather than a defect.
_MODELS = {
    "[1][2][3]": (),
    "[12][3]": ((0, 1),),
    "[13][2]": ((0, 2),),
    "[23][1]": ((1, 2),),
    "[12][13]": ((0, 1), (0, 2)),
    "[12][23]": ((0, 1), (1, 2)),
    "[13][23]": ((0, 2), (1, 2)),
    "[12][13][23]": ((0, 1), (0, 2), (1, 2)),
}


def loglinear_three_list(cells: dict[tuple[int, int, int], float],
                         ) -> dict[str, Fit]:
    """Fit every hierarchical model and read off the withheld 000 cell.

    The observable table has seven cells. A Poisson log-linear fit on those
    seven extrapolates the eighth, the count seen by no list. With two lists
    that extrapolation REQUIRES independence; with three it can carry
    pairwise dependence terms, which is the entire reason for wanting a
    third list rather than a longer second one.
    """
    keys = [k for k in sorted(cells, reverse=True) if k != (0, 0, 0)]
    y = np.array([float(cells[k]) for k in keys])
    mains = np.array([[float(v) for v in k] for k in keys])

    fits: dict[str, Fit] = {}
    for name, pairs in _MODELS.items():
        cols = [np.ones(len(keys)), *mains.T]
        cols += [mains[:, i] * mains[:, j] for i, j in pairs]
        design = np.column_stack(cols)
        with warnings.catch_warnings():
            # The zero-df model reproduces the table exactly, which
            # statsmodels reports as perfect separation. That is not a
            # pathology here; it is what "exactly identified" looks like.
            warnings.simplefilter("ignore")
            res = sm.GLM(y, design, family=sm.families.Poisson()).fit()
        log_mu = res.params[0]          # every covariate is 0 in cell 000
        se = math.sqrt(max(res.cov_params()[0][0], 0.0))
        fits[name] = Fit(
            name=name, df=len(keys) - design.shape[1],
            deviance=float(res.deviance), aic=float(res.aic),
            unseen=float(math.exp(log_mu)),
            unseen_lo=float(math.exp(log_mu - Z * se)),
            unseen_hi=float(math.exp(log_mu + Z * se)))
    return fits
