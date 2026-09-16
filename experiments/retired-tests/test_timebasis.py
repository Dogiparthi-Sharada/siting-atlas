"""Tests for the flexible time baseline the hazard is fitted with.

Split out of ``test_risk_set.py``, which had grown to cover three different
modules. The baseline is its own claim: the fixture's true hazard is a hump,
so a straight-line time term is genuinely misspecified against it, and
``test_spline_beats_a_linear_time_term_on_a_curved_baseline`` is therefore a
test with something at stake rather than a tautology.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.models import fixtures as fx
from siting_atlas.models.hazard import DiscreteTimeHazard, HazardSpec
from siting_atlas.models.risk_set import build_risk_set
from siting_atlas.models.timebasis import (
    baseline_design,
    choose_knots,
    restricted_cubic_spline,
)

COVARIATES = tuple(fx.TRUE_COEFFICIENTS)


@pytest.fixture(scope="module")
def risk() -> pd.DataFrame:
    return build_risk_set(fx.synthetic_panel(fx.SyntheticSpec(n_units=1200)))


def test_restricted_cubic_spline_is_linear_beyond_the_outer_knots():
    """That restriction is the entire point of 'restricted'.

    Outside the outer knots the basis must be a straight line, so second
    differences of the fitted values there are zero. Without it the cubic
    does whatever it likes in the tails, where there is least data.
    """
    knots = np.array([5.0, 12.0, 20.0, 28.0])
    t = np.arange(29, 40, dtype=float)          # beyond the last knot
    basis = restricted_cubic_spline(t, knots)
    fitted = basis @ np.array([0.3, -1.2, 0.7])
    assert np.allclose(np.diff(fitted, n=2), 0.0, atol=1e-9)


def test_spline_basis_width_and_knot_choice():
    t = np.arange(32)
    assert len(choose_knots(t, 4)) == 4
    matrix, names, knots = baseline_design(t, spec="spline", n_knots=4)
    assert matrix.shape == (32, 3) and names[0] == "t"
    # Reusing training knots must reproduce the identical basis, otherwise
    # the fitted coefficients do not apply to held-out rows.
    again, _, _ = baseline_design(t[:10], spec="spline", knots=knots)
    assert np.allclose(again, matrix[:10])


def test_dummy_baseline_uses_training_levels():
    train_levels = baseline_design(np.arange(8), spec="dummies")[2]
    matrix, names, _ = baseline_design(np.array([2, 3]), spec="dummies",
                                       knots=train_levels)
    assert matrix.shape == (2, 7), "columns follow training, not test"
    assert names[0] == "t_is_1"


def test_spline_beats_a_linear_time_term_on_a_curved_baseline(risk):
    """The flexible baseline has to earn its parameters.

    The fixture's true baseline is a hump, so a linear term is misspecified
    against it. If the spline did not fit better the default would be
    indefensible.
    """
    spline = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES,
                                           baseline="spline")).fit(risk)
    linear = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES,
                                           baseline="linear")).fit(risk)
    assert spline.result.llf > linear.result.llf
    assert spline.result.aic < linear.result.aic, (
        "the spline must win on AIC too, not just on raw fit — otherwise it "
        "is buying likelihood with parameters")
