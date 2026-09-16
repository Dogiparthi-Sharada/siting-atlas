"""The contract every model specification implements.

Why an abstract base class and not three loose functions
--------------------------------------------------------
The research question is not "what does one model say" but "does the answer
survive a change of specification". A cloglog hazard, a logit hazard, a
gradient-boosted classifier and a pure baseline-only null model all answer
the same question from the same panel, and the only honest way to compare
them is to run the identical evaluation over each. If every specification
brings its own bespoke ``score()`` the comparison quietly becomes a
comparison of scoring code.

So ``evaluate`` is implemented ONCE, here, in terms of ``predict``. A
subclass that wants a different metric has to override a named method and
that override is visible in review. Adding a specification means writing a
subclass, not editing a dispatch table.

The everyday version: three people weigh a parcel on three different scales
and report three weights. The disagreement you care about is between the
parcels, not between the scales, so you fix the scale first.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .metrics import CalibrationBin, brier_score, calibration_curve, roc_auc

_log = get_logger("models.base")

EVENT_COL = "event"


@dataclass
class EvaluationReport:
    """Everything one evaluation of one model on one sample produced.

    A dataclass rather than a bare dict because these numbers end up in the
    written report, and a typo in a dict key that silently returns ``None``
    is exactly the sort of thing that reaches a printed table.
    """

    n_rows: int
    n_events: int
    event_rate: float
    auc: float
    brier: float
    ece: float
    bins: list[CalibrationBin] = field(default_factory=list)
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "n_rows": self.n_rows,
            "n_events": self.n_events,
            "event_rate": round(self.event_rate, 6),
            "auc": round(self.auc, 4),
            "brier": round(self.brier, 6),
            "ece": round(self.ece, 5),
            "calibration": [b.to_dict() for b in self.bins],
        }

    def summary(self) -> str:
        """One line for a log or a console report."""
        return (f"{self.label or 'evaluation'}: n={self.n_rows:,} "
                f"events={self.n_events:,} ({self.event_rate:.3%})  "
                f"AUC={self.auc:.3f}  Brier={self.brier:.5f}  "
                f"ECE={self.ece:.4f}")


class Model(ABC):
    """A fitted-or-fittable specification over the ZCTA-quarter risk set.

    Subclasses must implement ``fit`` and ``predict``. They inherit
    ``evaluate``, which is deliberately not abstract: an identical
    evaluation across specifications is the entire reason this class
    exists.
    """

    name: str = "model"

    def __init__(self) -> None:
        self._fitted = False

    # -- the contract ----------------------------------------------------
    @abstractmethod
    def fit(self, frame: pd.DataFrame) -> Model:
        """Estimate parameters from a prepared risk set. Returns self."""

    @abstractmethod
    def predict(self, frame: pd.DataFrame) -> pd.Series:
        """Per-row hazard, P(event at t | still at risk at t), in [0, 1]."""

    # -- shared behaviour ------------------------------------------------
    @property
    def fitted(self) -> bool:
        return self._fitted

    def _require_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError(
                f"{type(self).__name__} has not been fitted; call fit() "
                f"before predict() or evaluate()")

    def evaluate(self, frame: pd.DataFrame, *, n_bins: int = 10,
                 label: str = "") -> EvaluationReport:
        """Score predictions against realised events on ``frame``.

        Three numbers, because each catches a failure the others miss:

            AUC    can the model RANK - is a ZCTA that enabled scored above
                   one that did not? Insensitive to the level, so a model
                   that is uniformly ten times too confident still scores 1.
            Brier  squared error on the probability itself, so it punishes
                   exactly the overconfidence AUC ignores.
            ECE    the gap between "the model said 4%" and "4% of those
                   actually happened", averaged over the range. A siting
                   decision is taken on the probability, not on the rank,
                   so calibration is the one that pays the bills.
        """
        self._require_fitted()
        if EVENT_COL not in frame.columns:
            raise KeyError(
                f"frame has no {EVENT_COL!r} column; evaluate() needs the "
                f"realised outcome, not just covariates")

        y = frame[EVENT_COL].to_numpy(dtype=float)
        p = np.asarray(self.predict(frame), dtype=float)

        bins = calibration_curve(y, p, n_bins=n_bins)
        report = EvaluationReport(
            n_rows=len(y),
            n_events=int(y.sum()),
            event_rate=float(y.mean()) if len(y) else float("nan"),
            auc=roc_auc(y, p),
            brier=brier_score(y, p),
            ece=sum(b.weight * abs(b.mean_predicted - b.mean_observed)
                    for b in bins),
            bins=bins,
            label=label or self.name,
        )
        _log.info("%s", report.summary())
        return report


class BaselineOnly(Model):
    """The null model: the unconditional event rate, for every row.

    It exists so that a reported AUC has something to be better than. A
    discrete-time hazard with five covariates and an AUC of 0.55 is not a
    finding, and the fastest way to notice that is to have the null sitting
    in the same table.
    """

    name = "baseline-only"

    def __init__(self) -> None:
        super().__init__()
        self.rate = float("nan")

    def fit(self, frame: pd.DataFrame) -> BaselineOnly:
        self.rate = float(frame[EVENT_COL].mean())
        self._fitted = True
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        self._require_fitted()
        return pd.Series(self.rate, index=frame.index, name="hazard")
