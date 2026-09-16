"""Discrimination, accuracy and calibration, computed from first principles.

Three metrics, and the reason there are three is that each is blind to a
different failure:

    a model that ranks perfectly but is ten times too confident  -> AUC 1.0
    a model that predicts the base rate for everyone             -> Brier ok
    a model that is right on average but wrong in every bin      -> ECE > 0

Implemented here rather than imported from scikit-learn for one reason that
matters and one that does not. The one that matters: the rare-event binning
below is not scikit-learn's default and getting it wrong makes a calibration
plot that looks fine and means nothing. The one that does not: fewer moving
parts in a number that goes into the written report.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import rankdata


@dataclass(frozen=True)
class CalibrationBin:
    """One point on the calibration curve."""

    lower: float
    upper: float
    n: int
    weight: float           # share of all rows, so bins can be averaged
    mean_predicted: float
    mean_observed: float

    def to_dict(self) -> dict:
        return {"lower": round(self.lower, 6), "upper": round(self.upper, 6),
                "n": self.n, "weight": round(self.weight, 5),
                "mean_predicted": round(self.mean_predicted, 6),
                "mean_observed": round(self.mean_observed, 6)}


def roc_auc(y: np.ndarray, p: np.ndarray) -> float:
    """Area under the ROC curve, via the rank identity.

    AUC is the probability that a randomly chosen event scores above a
    randomly chosen non-event, which equals the normalised Mann-Whitney U.
    Computing it from ranks rather than by sweeping thresholds costs one
    sort and handles ties exactly: ``rankdata`` assigns tied predictions
    their average rank, which credits a tie as half a win. A threshold sweep
    that breaks ties by input order silently rewards a constant predictor
    with an AUC of 1.0 if the data happen to be sorted by outcome.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    pos, neg = y == 1, y == 0
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        # Undefined rather than zero: with one class present there is no
        # ranking question to answer, and returning 0.5 would look like a
        # measured result.
        return float("nan")

    ranks = rankdata(p)
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0)
                 / (n_pos * n_neg))


def brier_score(y: np.ndarray, p: np.ndarray) -> float:
    """Mean squared error of the predicted probability.

    Note the scale trap for rare events: with a 2% event rate, predicting
    0.02 for everybody scores 0.0196, and any real model will score just
    below it. Brier differences look tiny in absolute terms and must be read
    against the base-rate Brier, not against zero.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return float(np.mean((p - y) ** 2))


def brier_skill_score(y: np.ndarray, p: np.ndarray) -> float:
    """Brier relative to always predicting the base rate. 0 = no better."""
    y = np.asarray(y, dtype=float)
    reference = brier_score(y, np.full_like(y, y.mean()))
    if reference == 0:
        return float("nan")
    return float(1.0 - brier_score(y, p) / reference)


def calibration_curve(y: np.ndarray, p: np.ndarray, *, n_bins: int = 10,
                      strategy: str = "quantile") -> list[CalibrationBin]:
    """Observed frequency against predicted probability, binned.

    ``strategy="quantile"`` is the default and it is not a detail. Enablement
    is a rare event, so predicted probabilities pile up near zero: cut the
    [0, 1] interval into ten equal-WIDTH bins and 99.9% of rows land in the
    first one. The plot then shows a single point, the ECE is dominated by
    that point, and the model looks perfectly calibrated because nothing was
    actually measured. Equal-COUNT bins put the same number of rows in each
    bin and ask the question at the resolution the data can answer.

    Equal-width is kept available because it is the right choice when
    comparing against a published curve that used it.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    n = len(y)
    if n == 0:
        return []

    if strategy == "quantile":
        edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
        if len(edges) < 2:
            # Every prediction identical (a constant model). One bin is the
            # honest answer; np.unique collapsing to a single edge would
            # otherwise make np.digitize raise.
            edges = np.array([p[0] - 1e-12, p[0] + 1e-12])
    elif strategy == "uniform":
        edges = np.linspace(0.0, 1.0, n_bins + 1)
    else:
        raise ValueError(f"unknown binning strategy {strategy!r}")

    # right=True with the left edge nudged so the minimum lands in bin 0
    # rather than in a phantom bin below the first edge.
    idx = np.clip(np.digitize(p, edges[1:-1], right=False),
                  0, len(edges) - 2)

    out: list[CalibrationBin] = []
    for b in range(len(edges) - 1):
        mask = idx == b
        count = int(mask.sum())
        if count == 0:
            continue
        out.append(CalibrationBin(
            lower=float(edges[b]), upper=float(edges[b + 1]), n=count,
            weight=count / n, mean_predicted=float(p[mask].mean()),
            mean_observed=float(y[mask].mean())))
    return out


def expected_calibration_error(y: np.ndarray, p: np.ndarray, *,
                               n_bins: int = 10) -> float:
    """Weighted mean absolute gap between predicted and observed frequency.

    ECE is a summary of the calibration curve, so it inherits the binning
    choice above: quoted without the bin strategy it is not reproducible.
    """
    bins = calibration_curve(y, p, n_bins=n_bins)
    return float(sum(b.weight * abs(b.mean_predicted - b.mean_observed)
                     for b in bins))
