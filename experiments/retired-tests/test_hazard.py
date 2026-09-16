"""Tests for the discrete-time hazard and the risk set it is fitted on.

Two tests carry the weight here.

``test_unit_leaves_the_risk_set_after_the_event`` and its siblings pin down
the risk-set construction, because a duration model fitted on a dense panel
runs perfectly and returns biased coefficients with no warning of any kind.
There is no runtime symptom to catch it by, so it has to be caught here.

``test_recovers_known_coefficients`` fits the estimator on data whose true
coefficients we chose, and asserts it hands them back. That is the only
claim available before the facility panel arrives, and it is a real one: it
exercises the link function, the risk set, the standardisation round trip
and the spline basis end to end.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.models import fixtures as fx
from siting_atlas.models.base import BaselineOnly
from siting_atlas.models.hazard import DiscreteTimeHazard, HazardSpec
from siting_atlas.models.risk_set import build_risk_set

COVARIATES = tuple(fx.TRUE_COEFFICIENTS)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def synthetic() -> pd.DataFrame:
    """One synthetic panel, generated once — every fit here is sub-second
    but the panel is 38k rows and there is no reason to rebuild it."""
    return fx.synthetic_panel(fx.SyntheticSpec(n_units=1200))


@pytest.fixture(scope="module")
def risk(synthetic: pd.DataFrame) -> pd.DataFrame:
    return build_risk_set(synthetic)


def tiny_panel(enabled_at: int | None, n_quarters: int = 8,
               unit: str = "SYN-00001", state_encoding: bool = True
               ) -> pd.DataFrame:
    """A single unit over ``n_quarters`` quarters, enabled at one of them."""
    t = np.arange(n_quarters)
    if enabled_at is None:
        flag = np.zeros(n_quarters, dtype=bool)
    elif state_encoding:
        flag = t >= enabled_at
    else:
        flag = t == enabled_at
    return pd.DataFrame({"zcta": unit, "year": 2018 + t // 4,
                         "quarter": t % 4 + 1, "enabled": flag,
                         "x_demand": 0.5, "x_cost": -0.2,
                         "x_competition": 0.1})


# ---------------------------------------------------------------------------
# recovery of the known truth
# ---------------------------------------------------------------------------
def test_recovers_known_coefficients(risk):
    """The estimator returns the coefficients the data was built with.

    Tolerances are stated two ways on purpose. The absolute one is a
    sanity bound; the standard-error one is the real test, because it asks
    whether the estimate is where sampling theory says it should be rather
    than merely close.
    """
    model = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(risk)
    coef = model.coefficients().set_index("term")

    for name, truth in fx.TRUE_COEFFICIENTS.items():
        est = float(coef.loc[name, "coefficient"])
        se = float(coef.loc[name, "std_error"])
        assert abs(est - truth) < 0.15, f"{name}: {est:.3f} vs {truth}"
        assert abs(est - truth) < 4 * se, (
            f"{name} is {abs(est - truth) / se:.1f} standard errors from "
            f"the truth, which is not sampling noise")


def test_recovers_the_baseline_shape(risk):
    """The fitted baseline must track the hump the fixture actually used."""
    model = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(risk)
    curve = model.baseline_hazard(np.arange(32))

    spec = fx.SyntheticSpec()
    true_alpha = fx.baseline_alpha(np.arange(32), spec)
    true_hazard = -np.expm1(-np.exp(true_alpha))

    # Shape only. A curve that is uniformly 13% low correlates at 0.9999
    # with the truth, which is how the row-mean reference went unnoticed —
    # the LEVEL is asserted separately, below.
    assert np.corrcoef(curve["hazard"], true_hazard)[0, 1] > 0.95


def test_standardisation_round_trip_is_exact(risk):
    """Coefficients reported in raw units must match an unstandardised fit.

    Standardising and unscaling is an exact linear transform, so the two
    routes have to agree to numerical precision. If they did not, every
    reported hazard ratio would be wrong by a factor nobody could see.
    """
    scaled = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES,
                                           standardise=True)).fit(risk)
    raw = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES,
                                        standardise=False)).fit(risk)
    a = scaled.coefficients().set_index("term")["coefficient"]
    b = raw.coefficients().set_index("term")["coefficient"]
    assert np.allclose(a.to_numpy(), b.to_numpy(), atol=1e-6)


@pytest.fixture(scope="module")
def scaled_risk(risk: pd.DataFrame) -> pd.DataFrame:
    """The risk set with one covariate on a real-world scale.

    The fixture's covariates are standard normal, and dividing by an sd of 1
    hides every scale bug there is. Putting ``x_demand`` on the scale of a
    median household income — mean 60,000, sd 20,000 — makes the unit
    conversion visible.
    """
    frame = risk.copy()
    frame["x_demand"] = frame["x_demand"] * 20_000 + 60_000
    return frame


def test_the_whole_covariance_survives_the_change_of_units(scaled_risk):
    """Unscaling must reproduce an unstandardised fit EXACTLY — SEs too.

    The raw intercept is not the fitted intercept; it is the fitted
    intercept minus a weighted sum of every covariate coefficient. Its
    variance therefore picks up all of their variances and covariances, and
    an unscale that rescales only the diagonal drops all of those terms. It
    reported 0.176 where the truth is 0.252 — a standard error 1.4x too
    narrow on the term that sets the level of the whole baseline, written
    straight into ``hazard_report.json``. Nothing about that output looks
    wrong: it is a plausible number, it is tighter than the truth, and
    tighter is the direction nobody questions.

    Fitting the same model both ways is the strongest available check:
    standardisation is a reparameterisation, not a different model, so every
    column of the two tables must agree to numerical precision.
    """
    scaled = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES,
                                           standardise=True)
                                ).fit(scaled_risk).coefficients()
    raw = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES,
                                        standardise=False)
                             ).fit(scaled_risk).coefficients()

    for column in ("coefficient", "std_error", "z", "p_value"):
        assert np.allclose(scaled[column].to_numpy(), raw[column].to_numpy(),
                           rtol=1e-6, atol=1e-9), f"{column} disagrees"


def test_the_coefficient_table_agrees_with_itself(scaled_risk):
    """coefficient / std_error must equal the z column, every row.

    A table whose own columns contradict each other cannot be read at all:
    the intercept printed coefficient/std_error of -42.6 against a z of
    -30.5, with no way from the outside to tell which to trust. The z column
    came from the fit on standardised covariates while the coefficient
    column had been converted to raw units, so neither described the same
    quantity as its neighbour.
    """
    coef = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)
                              ).fit(scaled_risk).coefficients()
    implied = coef["coefficient"] / coef["std_error"]
    assert np.allclose(implied.to_numpy(), coef["z"].to_numpy(), rtol=1e-9)


def test_baseline_curve_is_the_average_unit_not_the_average_row(risk):
    """A survivor-weighted reference point publishes the wrong curve.

    ``baseline_hazard`` answers "what did the hazard look like for a typical
    place". Averaging the covariates over risk-set ROWS does not describe a
    typical place: a unit that enables in quarter two contributes two rows
    and one that never enables contributes thirty-one, so on any covariate
    that predicts the event the row mean is dragged toward the units that
    were never chosen. Here that moves ``x_demand`` from a population mean
    of 0.00 to a row mean of -0.16, and the published curve came out ~13%
    below the process the data was generated from — at every quarter, so it
    reads as a level rather than as an error. The fit itself was never
    wrong. Only the curve was, which is worse: the curve is the artefact
    that ends up on a slide.
    """
    spec = fx.SyntheticSpec()
    model = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(risk)
    t = np.arange(int(risk["t"].min()), int(risk["t"].max()) + 1)

    row_mean = model._scaler.mean
    unit_mean = risk.groupby("zcta")[list(COVARIATES)].first().mean()
    assert abs(row_mean[0] - unit_mean.iloc[0]) > 0.10, (
        "the two references barely differ on this sample, so the test "
        "below would pass for the wrong reason — check the fixture")

    published = model.baseline_hazard(t)["hazard"].to_numpy()
    at_row_means = model.predict(
        pd.DataFrame({"t": t, **{c: row_mean[i]
                                 for i, c in enumerate(COVARIATES)}})
    ).to_numpy()
    assert np.all(at_row_means < 0.95 * published), (
        "the row-mean curve must sit materially below the unit-mean one, or "
        "this fixture no longer exercises survivor weighting")

    # Level, not just shape: a curve uniformly 13% low correlates at 0.9999
    # with the truth, which is precisely how this got past the shape test.
    true_hazard = -np.expm1(-np.exp(fx.baseline_alpha(t, spec)))
    relative = published / true_hazard - 1.0
    assert abs(float(np.mean(relative))) < 0.05, (
        f"the published baseline is {np.mean(relative):+.1%} off the known "
        f"process on average, which is a level error, not spline wobble")


def test_contaminated_risk_set_would_have_biased_the_estimate(synthetic):
    """Proof that the invariant is load-bearing, not decorative.

    Fit the same specification on the dense panel — the mistake this module
    exists to prevent — and show the coefficients collapse toward zero. If
    this test ever stops showing attenuation, the risk-set logic has stopped
    doing anything.
    """
    rs = build_risk_set(synthetic)
    good = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(rs)

    # The dense version: keep every quarter, flag only the opening one, and
    # skip the validation that would have caught it.
    dense = synthetic.copy()
    dense["t"] = (dense["year"] - 2018) * 4 + dense["quarter"] - 1
    first = (dense[dense["enabled"]].groupby("zcta")["t"].min())
    dense["event"] = (dense["t"] == dense["zcta"].map(first)).astype(int)
    dense = dense[dense["zcta"].isin(rs["zcta"].unique())]

    bad = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES))
    x, _ = bad.design(dense, training=True)
    import statsmodels.api as sm
    fit = sm.GLM(dense["event"].to_numpy(dtype=float), x,
                 family=sm.families.Binomial(
                     link=sm.families.links.CLogLog())).fit()

    good_beta = float(
        good.coefficients().set_index("term").loc["x_demand", "coefficient"])
    bad_beta = float(fit.params[-3]) / bad._scaler.sd[0]
    assert abs(bad_beta) < abs(good_beta), (
        "the dense panel should attenuate the coefficient toward zero")
    assert good_beta - bad_beta > 0.05, (
        f"attenuation of only {good_beta - bad_beta:.3f} — check the test, "
        f"not the model")


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------
def test_evaluate_beats_the_null_model(risk):
    model = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(risk)
    null = BaselineOnly().fit(risk)

    report = model.evaluate(risk)
    null_report = null.evaluate(risk)

    assert report.auc > 0.65, "a model that cannot rank is not a model"
    assert np.isnan(null_report.auc) or abs(null_report.auc - 0.5) < 1e-9
    assert report.brier < null_report.brier
    assert report.ece < 0.01, "predicted probabilities must mean something"
    assert report.n_events == int(risk["event"].sum())


def test_evaluate_requires_the_outcome(risk):
    model = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(risk)
    with pytest.raises(KeyError, match="event"):
        model.evaluate(risk.drop(columns=["event"]))


def test_predict_before_fit_raises():
    model = DiscreteTimeHazard(HazardSpec(covariates=COVARIATES))
    with pytest.raises(RuntimeError, match="has not been fitted"):
        model.predict(tiny_panel(None).assign(t=0))


def test_constant_covariate_is_named_not_left_to_linalg(risk):
    """A zero-variance column is collinear with the intercept.

    statsmodels reports "Singular matrix", which sends the reader hunting
    through the time baseline. Naming the column is the whole fix.
    """
    flat = risk.assign(x_cost=1.0)
    with pytest.raises(ValueError, match=r"x_cost.*constant"):
        DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(flat)


def test_missing_covariates_are_refused_not_imputed(risk):
    """An imputation decision belongs upstream, where the reason is known."""
    broken = risk.copy()
    broken.loc[broken.index[:5], "x_demand"] = np.nan
    with pytest.raises(ValueError, match="missing covariate"):
        DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(broken)
