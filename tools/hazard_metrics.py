"""Measured hazard-model results, for figures and documents to quote.

Reads ``experiments/hazard-model/artefacts/hazard_report.json``, written by
``PYTHONPATH=src python -m siting_atlas.models.runner``. Stdlib only, on the
same reasoning as ``scope.py``: the figure, docx and pptx builders may run
under a different interpreter from the pipeline, so this must not import the
package.

Why it exists. ``fig08_backtest`` previously printed AUC 0.84, ECE 0.03 and
precision@100 0.61 -- targets, typed by hand, drawn as though measured, with
an ROC curve synthesised from ``tpr = fpr ** (1/0.84 - 1)`` so that its area
would match the label. The backtest has since run and the model failed.
Deriving every number on the figure from this file removes the possibility of
a figure disagreeing with the artefact it claims to show.

    from hazard_metrics import HAZARD
    HAZARD.auc            # 0.6894
    HAZARD.brier          # 0.019522
    HAZARD.null_brier     # 0.019614
    HAZARD.stamp          # 'hazard_report.json - run 20260913-133904-a60e'

Nothing here computes anything. If a number is not in the JSON it is not
available to a figure, which is the point.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
# The hazard model was retired to experiments/ on 2026-09-15 and its artefact
# moved with it. This module builds `HAZARD` at import time, so a stale path
# here does not fail lazily -- it raises on `import hazard_metrics`, which
# took tools/figures/build_all.py, tools/deck/build_deck.py and the CI
# `documents` job down with it until 2026-09-16.
_HAZARD_JSON = (_REPO / "experiments" / "hazard-model" / "artefacts"
                / "hazard_report.json")


class Hazard:
    """Read-only view of the measured discrete-time hazard results."""

    def __init__(self, path: Path = _HAZARD_JSON):
        """Load the measured results, or fail naming the command.

        Failing at construction is deliberate: HAZARD is built at import, so a
        figure build stops before it can draw a placeholder where a measured
        result should be.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing. Every number on fig08 and fig09 is read "
                f"from it rather than typed, so fit the model first:\n\n"
                f"    PYTHONPATH=src python -m siting_atlas.models.runner\n")
        self._d = json.loads(path.read_text(encoding="utf-8"))
        self._eval = self._d["evaluation"]
        self._null = self._d["null_model"]
        self._temporal = self._d["temporal_secondary"]
        self._conformal = self._d["conformal"]

    # -- provenance --------------------------------------------------------
    @property
    def run_id(self) -> str:
        """The pipeline run that produced these numbers."""
        return self._d["run_id"]

    @property
    def written_at(self) -> str:
        """ISO timestamp the artefact was written."""
        return self._d["written_at"]

    @property
    def stamp(self) -> str:
        """One-line source and run stamp to print on a figure."""
        return (f"Source: experiments/hazard-model/artefacts/"
                f"hazard_report.json  -  run "
                f"{self.run_id}, written {self.written_at[:10]}")

    # -- primary hold-out, units clustered ---------------------------------
    @property
    def n_rows(self) -> int:
        """Test rows in the primary (unit-clustered) hold-out."""
        return self._eval["n_rows"]

    @property
    def n_events(self) -> int:
        """Events in the primary hold-out."""
        return self._eval["n_events"]

    @property
    def base_rate(self) -> float:
        """Event rate in the primary hold-out."""
        return self._eval["event_rate"]

    @property
    def auc(self) -> float:
        """Measured AUC on the primary hold-out."""
        return self._eval["auc"]

    @property
    def brier(self) -> float:
        """Measured Brier score -- the proper score, and the one to report."""
        return self._eval["brier"]

    @property
    def ece(self) -> float:
        """Measured expected calibration error on the primary hold-out."""
        return self._eval["ece"]

    @property
    def calibration(self) -> list:
        """Ten equal-count calibration bins: predicted vs observed."""
        return list(self._eval["calibration"])

    # -- the null model: a constant equal to the base rate -----------------
    @property
    def null_auc(self) -> float:
        """AUC of a constant prediction. Exactly 0.5, by construction."""
        return self._null["auc"]

    @property
    def null_brier(self) -> float:
        """Brier score of the constant, over the same rows."""
        return self._null["brier"]

    @property
    def null_ece(self) -> float:
        """Calibration error of the constant."""
        return self._null["ece"]

    @property
    def null_point(self) -> tuple:
        """The constant's single calibration point, (predicted, observed)."""
        b = self._null["calibration"][0]
        return b["mean_predicted"], b["mean_observed"]

    # -- secondary hold-out, split on time ---------------------------------
    @property
    def t_n_rows(self) -> int:
        """Test rows in the secondary (temporal) hold-out."""
        return self._temporal["evaluation"]["n_rows"]

    @property
    def t_n_events(self) -> int:
        """Events in the temporal hold-out."""
        return self._temporal["evaluation"]["n_events"]

    @property
    def t_auc(self) -> float:
        """AUC on the temporal hold-out."""
        return self._temporal["evaluation"]["auc"]

    @property
    def t_brier(self) -> float:
        """Brier score on the temporal hold-out."""
        return self._temporal["evaluation"]["brier"]

    @property
    def t_ece(self) -> float:
        """Calibration error on the temporal hold-out."""
        return self._temporal["evaluation"]["ece"]

    @property
    def t_null_brier(self) -> float:
        """Brier score of the constant on the temporal hold-out rows."""
        return self._temporal["null_model"]["brier"]

    @property
    def t_null_ece(self) -> float:
        """Calibration error of the constant on the temporal hold-out."""
        return self._temporal["null_model"]["ece"]

    # -- split conformal ---------------------------------------------------
    @property
    def nominal_coverage(self) -> float:
        """Coverage the conformal procedure was asked for, i.e. 1 - alpha."""
        return self._conformal["nominal_coverage"]

    @property
    def empirical_coverage(self) -> float:
        """Coverage actually observed on the test split."""
        return self._conformal["empirical_coverage"]

    @property
    def coverage_tolerance(self) -> float:
        """Two-sigma band the unit-clustered calibration split implies."""
        return self._conformal["tolerance_2sigma"]

    @property
    def within_tolerance(self) -> bool:
        """Whether observed coverage sits inside that band."""
        return self._conformal["within_tolerance"]

    @property
    def share_empty(self) -> float:
        """Share of prediction sets containing neither label."""
        return self._conformal["share_empty"]

    @property
    def share_singleton(self) -> float:
        """Share of prediction sets containing exactly one label."""
        return self._conformal["share_singleton"]

    @property
    def share_full(self) -> float:
        """Share of prediction sets containing both labels."""
        return self._conformal["share_full"]

    @property
    def n_effective(self) -> int:
        """Independent units behind the coverage figure, not rows."""
        return self._conformal["n_effective"]

    @property
    def n_conformal_test(self) -> int:
        """Rows scored by the conformal procedure."""
        return self._conformal["n_test"]

    # -- power -------------------------------------------------------------
    @property
    def events_per_parameter(self) -> float:
        """Optimistic events per parameter; the verdict is taken on this."""
        return self._d["power"]["events_per_parameter_optimistic"]

    @property
    def power_floor(self) -> float:
        """Conventional floor the ratio is judged against."""
        return self._d["power"]["floor"]


#: Import this. Constructed at import so a missing artefact fails the build
#: loudly rather than drawing a figure with an invented number in it.
HAZARD = Hazard()
