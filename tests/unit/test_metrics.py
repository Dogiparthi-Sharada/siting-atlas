"""Tests for AUC, Brier and the calibration curve, on cases done by hand.

Split out of ``test_risk_set.py``. Every assertion here is against a value
that can be worked out on paper, because a metric implementation that is
only checked against itself will agree with itself forever. The tie case in
``test_auc_hand_computable_cases`` is the one that matters: a threshold
sweep that breaks ties by input order reports a perfect 1.0 on data that
carries no signal at all.
"""

from __future__ import annotations

import numpy as np
import pytest

from siting_atlas.models.metrics import (
    brier_score,
    calibration_curve,
    expected_calibration_error,
    roc_auc,
)


def test_auc_hand_computable_cases():
    assert roc_auc(np.array([0, 0, 1, 1]),
                   np.array([0.1, 0.2, 0.8, 0.9])) == 1.0
    assert roc_auc(np.array([0, 0, 1, 1]),
                   np.array([0.9, 0.8, 0.2, 0.1])) == 0.0
    # All ties: every comparison is half a win, so exactly 0.5. A threshold
    # sweep that breaks ties by input order would report 1.0 here.
    assert roc_auc(np.array([0, 0, 1, 1]), np.full(4, 0.3)) == 0.5
    assert np.isnan(roc_auc(np.zeros(4), np.array([0.1, 0.2, 0.3, 0.4])))


def test_brier_and_ece_on_a_perfectly_calibrated_predictor():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 20_000)
    y = (rng.uniform(size=20_000) < p).astype(float)
    assert brier_score(y, p) == pytest.approx(np.mean(p * (1 - p)), abs=0.01)
    assert expected_calibration_error(y, p) < 0.02


def test_quantile_binning_actually_bins_rare_events():
    """Equal-width bins would put everything in the first bin and report a
    perfect calibration that was never measured."""
    p = np.concatenate([np.linspace(0.001, 0.05, 990), [0.6] * 10])
    y = (np.arange(1000) % 50 == 0).astype(float)
    quantile = calibration_curve(y, p, n_bins=10, strategy="quantile")
    uniform = calibration_curve(y, p, n_bins=10, strategy="uniform")
    assert len(quantile) >= 8
    assert len(uniform) <= 2
    assert sum(b.n for b in quantile) == 1000
    assert sum(b.weight for b in quantile) == pytest.approx(1.0)
