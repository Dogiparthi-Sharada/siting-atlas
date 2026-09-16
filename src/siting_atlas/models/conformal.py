"""Split conformal prediction: the one guarantee that does not need the
model to be right.

What is actually guaranteed
---------------------------
Every other number this project reports is conditional on the model being a
reasonable description of the world. An AUC of 0.78 is 0.78 *if* the cloglog
link is right, *if* the covariates are the relevant ones, *if* the baseline
is flexible enough. Conformal prediction drops all of that. Given only that
the calibration rows and the test rows are exchangeable — drawn from the same
pool, order irrelevant — the prediction set contains the truth at least
(1 - alpha) of the time:

    P( Y in C(X) )  >=  1 - alpha

for ANY model. A deliberately terrible model does not break the coverage; it
just produces wider sets to pay for it. That trade is the mechanism: bad
model, uninformative sets, honest coverage. There is no configuration in
which the model quietly overstates its certainty.

How, in three lines
-------------------
1. Score each CALIBRATION row by how badly the model fit its true label.
   For a binary outcome the natural score is ``1 - p_hat(true label)``: near
   0 when the model put its mass on what happened, near 1 when it did not.
2. Take q_hat, the (1-alpha) quantile of those scores, with a small
   finite-sample correction.
3. For a new row, include every label whose score is no worse than q_hat.

The everyday version: you want to promise a delivery window you keep 90% of
the time. You do not model traffic. You look at your last 500 deliveries, find
the lateness that 90% of them beat, and quote that. It works whatever the
traffic does, as long as tomorrow looks like the last 500 days.

Where the guarantee stops, stated plainly
-----------------------------------------
It is MARGINAL coverage, averaged over the population. It does not promise
90% coverage within dense ZCTAs specifically — conditional coverage is not
attainable distribution-free. And exchangeability is a real assumption: a
temporal split where the future differs from the past breaks it, which is
why the runner calibrates on a random unit split and says so.

Clustering, measured rather than assumed
----------------------------------------
The panel gives up to 32 rows per ZCTA and those rows are not independent
draws. Splitting whole units into calibration and test — which the leakage
argument in ``splits.py`` forces — means the calibration rows are a CLUSTER
sample, and strict exchangeability with a single test row does not hold.
Forty replications of the fixture, at nominal 90%:

    calibration split by ROW   (exchangeable)   mean 89.9%,  sd 0.45pp
    calibration split by UNIT  (clustered)      mean 89.8%,  sd 1.66pp

The centre is intact; the SPREAD is 3.7x wider. So clustering does not bias
coverage, it makes any single split a noisy estimate of it, and a run that
reports 87.8% is one standard deviation low rather than broken. That is why
:func:`coverage_tolerance` exists and why the runner prints a band instead
of a bare number — a coverage figure quoted without its tolerance invites
exactly the wrong conclusion.
"""

from __future__ import annotations

import math

import numpy as np

from ..common.logging_setup import get_logger
from .conformal_report import ConformalReport, coverage_tolerance

_log = get_logger("models.conformal")

LABELS = (0, 1)

#: Re-exported so that callers keep importing the report and its tolerance
#: from the module that produces them; the definitions live next door only
#: because this file had grown past the size anyone reads in one sitting.
__all__ = ["ConformalReport", "SplitConformalBinary", "conformal_quantile",
           "coverage_tolerance"]


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """The k-th smallest calibration score, k = ceil((n+1)*(1-alpha)).

    Note the n+1 and note that this is an ORDER STATISTIC, not a quantile
    function evaluated at (1-alpha). Both details are load-bearing and each
    breaks the method in a different direction.

    The n+1: the proof treats the test point as one more exchangeable draw,
    so the relevant rank is out of n+1. Using n undercovers by roughly 1/n —
    invisible at n=10,000 and fatal at n=50, which is exactly the regime the
    first real facility panel will land in.

    The order statistic: ``np.quantile(..., method="higher")`` interpolates
    on an (n-1) grid, so at n=19 and alpha=0.10 it returns the 19th smallest
    score where the proof asks for the 18th. That direction is conservative
    — wider sets, over-coverage — so it never shows up as a failed coverage
    check, only as sets that are quietly less useful than they should be.
    Indexing the sorted array says exactly what is meant.

    When k exceeds n there are too few calibration points to promise that
    coverage at all, and the honest answer is an infinite threshold: every
    label is admitted, coverage is trivially 100%, and the set width says
    so. Returning a finite quantile there would fake a guarantee.
    """
    scores = np.asarray(scores, dtype=float)
    n = len(scores)
    if n == 0:
        raise ValueError("cannot calibrate on an empty sample")

    k = math.ceil((n + 1) * (1.0 - alpha))
    if k > n:
        _log.warning(
            "%d calibration points cannot support %.0f%% coverage "
            "(needs at least %d); every prediction set will contain every "
            "label", n, 100 * (1 - alpha), math.ceil(1 / alpha) - 1)
        return float("inf")
    return float(np.partition(scores, k - 1)[k - 1])


class SplitConformalBinary:
    """Distribution-free prediction sets for a binary outcome.

    Deliberately knows nothing about the hazard model. It takes predicted
    probabilities and realised labels, which means it also wraps a logistic
    regression, a gradient-boosted tree or a coin flip, and the tests
    exercise exactly that: the coverage property is asserted against a
    deliberately miscalibrated predictor, because a guarantee that only
    holds for good models is not a guarantee.
    """

    def __init__(self, alpha: float = 0.10):
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")
        self.alpha = alpha
        self.q_hat: float | None = None
        self.n_calibration = 0

    # -- calibrate ---------------------------------------------------------
    def calibrate(self, p_hat, y) -> SplitConformalBinary:
        """Learn the threshold from held-out rows the model never saw."""
        p_hat = np.clip(np.asarray(p_hat, dtype=float), 0.0, 1.0)
        y = np.asarray(y, dtype=int)
        if len(p_hat) != len(y):
            raise ValueError(
                f"{len(p_hat)} predictions against {len(y)} labels")

        scores = self._score(p_hat, y)
        self.q_hat = conformal_quantile(scores, self.alpha)
        self.n_calibration = len(scores)
        _log.info("calibrated on %d rows: q_hat=%.6f at alpha=%.2f",
                  self.n_calibration, self.q_hat, self.alpha)
        return self

    @staticmethod
    def _score(p_hat: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Nonconformity: one minus the probability given to the truth."""
        return np.where(y == 1, 1.0 - p_hat, p_hat)

    # -- predict -----------------------------------------------------------
    def predict_set(self, p_hat) -> np.ndarray:
        """Boolean (n, 2) array: column j says whether label j is included."""
        if self.q_hat is None:
            raise RuntimeError("call calibrate() before predict_set()")
        p_hat = np.clip(np.asarray(p_hat, dtype=float), 0.0, 1.0)
        # Non-strict comparison, matching the >= in the coverage proof. With
        # ties on the threshold a strict '<' drops exactly the boundary mass
        # the correction above was added to retain.
        return np.column_stack([p_hat <= self.q_hat,
                                (1.0 - p_hat) <= self.q_hat])

    def covers(self, p_hat, y) -> np.ndarray:
        """Per-row: did the set contain the realised label?"""
        sets = self.predict_set(p_hat)
        return sets[np.arange(len(sets)), np.asarray(y, dtype=int)]

    def evaluate(self, p_hat, y, *, groups=None) -> ConformalReport:
        """Coverage and efficiency on a test sample.

        Pass ``groups`` (the unit id of each row) whenever the test rows are
        clustered. It does not change the coverage figure, only the
        tolerance attached to it — and a coverage figure without its
        tolerance is the thing that gets misread.
        """
        sets = self.predict_set(p_hat)
        y = np.asarray(y, dtype=int)
        hit = sets[np.arange(len(sets)), y]
        size = sets.sum(axis=1)

        report = ConformalReport(
            alpha=self.alpha, nominal_coverage=1.0 - self.alpha,
            empirical_coverage=float(hit.mean()),
            n_calibration=self.n_calibration, n_test=len(y),
            q_hat=float(self.q_hat), mean_set_size=float(size.mean()),
            share_singleton=float((size == 1).mean()),
            share_full=float((size == 2).mean()),
            share_empty=float((size == 0).mean()),
            n_effective=len(np.unique(groups)) if groups is not None
            else len(y))
        _log.info("%s", report.summary())

        if not report.within_tolerance:
            # Not an assertion, because a single small test sample can land
            # low by chance. It is a loud warning because the usual cause is
            # not chance: calibration rows that leaked into training, or a
            # temporal split that broke exchangeability.
            _log.warning(
                "empirical coverage %.1f%% is outside the nominal %.1f%% "
                "+/- %.1fpp tolerance (%d effective units) — check that the "
                "calibration split is genuinely held out and that "
                "calibration and test are exchangeable",
                100 * report.empirical_coverage,
                100 * report.nominal_coverage, 100 * report.tolerance,
                report.n_effective or report.n_test)
        return report
