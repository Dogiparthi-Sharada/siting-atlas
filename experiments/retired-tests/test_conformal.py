"""Tests for split conformal prediction.

Conformal prediction makes exactly one promise — marginal coverage at least
(1 - alpha) under exchangeability — and unlike everything else in this
project that promise is checkable without knowing whether the model is any
good. So it is checked properly here: against a controlled DGP, over many
Monte-Carlo replications, with tolerances derived from the binomial standard
error rather than eyeballed.

The test that matters most is
``test_coverage_holds_for_a_deliberately_terrible_model``. A guarantee that
only holds when the model is good is not a guarantee, it is a coincidence.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from siting_atlas.models.conformal import (
    SplitConformalBinary,
    conformal_quantile,
    coverage_tolerance,
)
from siting_atlas.models.fixtures import SyntheticSpec, synthetic_panel
from siting_atlas.models.hazard import DiscreteTimeHazard, HazardSpec
from siting_atlas.models.risk_set import build_risk_set

ALPHA = 0.10
NOMINAL = 1.0 - ALPHA


def controlled_dgp(n: int, rng: np.random.Generator, *, noise: float = 0.0):
    """A binary outcome whose true probability we know exactly.

    ``noise`` corrupts the predictions handed to the conformal wrapper
    WITHOUT touching the labels, which is how a miscalibrated model is
    simulated: the truth is unchanged, only the model's opinion is wrong.
    """
    p_true = rng.beta(1.2, 12.0, size=n)          # rare-event shaped
    y = (rng.uniform(size=n) < p_true).astype(int)
    p_hat = np.clip(p_true + noise * rng.normal(size=n), 1e-6, 1 - 1e-6)
    return p_hat, y


# ---------------------------------------------------------------------------
# the guarantee
# ---------------------------------------------------------------------------
def test_coverage_matches_nominal_under_exchangeability():
    """The central claim, measured over 200 independent replications.

    One split is a noisy estimate of coverage; 200 are not. The tolerance is
    the binomial standard error of the MEAN coverage across replications, so
    this asserts the method is unbiased rather than merely plausible.
    """
    rng = np.random.default_rng(20260914)
    n_cal = n_test = 2_000
    reps = 200

    coverages = []
    for _ in range(reps):
        p_cal, y_cal = controlled_dgp(n_cal, rng)
        p_test, y_test = controlled_dgp(n_test, rng)
        model = SplitConformalBinary(ALPHA).calibrate(p_cal, y_cal)
        coverages.append(model.evaluate(p_test, y_test).empirical_coverage)

    mean = float(np.mean(coverages))
    se = math.sqrt(NOMINAL * (1 - NOMINAL) / (n_test * reps))
    assert mean >= NOMINAL - 3 * se, (
        f"mean coverage {mean:.4f} is below the guaranteed {NOMINAL}")
    # The guarantee is two-sided for continuous scores: coverage cannot
    # exceed 1-alpha + 1/(n_cal+1) by more than noise. Without this half the
    # test would pass for a method that always returned both labels.
    assert mean <= NOMINAL + 1 / (n_cal + 1) + 3 * se, (
        f"mean coverage {mean:.4f} is above the finite-sample upper bound; "
        f"the sets are wider than the guarantee requires")


def test_coverage_holds_for_a_deliberately_terrible_model():
    """Distribution-free means distribution-free.

    The predictor here is pure noise, uncorrelated with the outcome. Coverage
    must still hit nominal; the price is paid in set size, not in broken
    promises. If this test fails, the implementation has smuggled in an
    assumption about the model being calibrated.
    """
    rng = np.random.default_rng(20260914)
    coverages, sizes = [], []
    for _ in range(100):
        _, y_cal = controlled_dgp(2_000, rng)
        _, y_test = controlled_dgp(2_000, rng)
        junk_cal = rng.uniform(size=2_000)
        junk_test = rng.uniform(size=2_000)

        model = SplitConformalBinary(ALPHA).calibrate(junk_cal, y_cal)
        report = model.evaluate(junk_test, y_test)
        coverages.append(report.empirical_coverage)
        sizes.append(report.mean_set_size)

    mean = float(np.mean(coverages))
    se = math.sqrt(NOMINAL * (1 - NOMINAL) / (2_000 * 100))
    assert mean >= NOMINAL - 3 * se, (
        f"a useless model must still be covered: {mean:.4f}")
    assert np.mean(sizes) > 1.5, (
        "a useless model should pay for its coverage with wide sets; narrow "
        "sets here would mean the guarantee is being met by luck")


def test_a_good_model_buys_narrower_sets_than_a_bad_one():
    """Efficiency is the axis where model quality actually shows up."""
    rng = np.random.default_rng(1)
    p_cal, y_cal = controlled_dgp(5_000, rng)
    p_test, y_test = controlled_dgp(5_000, rng)
    junk_cal, junk_test = rng.uniform(size=5_000), rng.uniform(size=5_000)

    good = SplitConformalBinary(ALPHA).calibrate(p_cal, y_cal).evaluate(
        p_test, y_test)
    bad = SplitConformalBinary(ALPHA).calibrate(junk_cal, y_cal).evaluate(
        junk_test, y_test)

    assert good.mean_set_size < bad.mean_set_size
    assert good.share_singleton > bad.share_singleton


@pytest.mark.parametrize("alpha", [0.01, 0.05, 0.10, 0.20])
def test_coverage_tracks_alpha(alpha):
    """Changing the requested level must change the delivered level."""
    rng = np.random.default_rng(int(1000 * alpha) + 7)
    coverages = []
    for _ in range(60):
        p_cal, y_cal = controlled_dgp(4_000, rng)
        p_test, y_test = controlled_dgp(4_000, rng)
        coverages.append(SplitConformalBinary(alpha).calibrate(
            p_cal, y_cal).evaluate(p_test, y_test).empirical_coverage)

    mean = float(np.mean(coverages))
    nominal = 1 - alpha
    se = math.sqrt(nominal * (1 - nominal) / (4_000 * 60))
    assert nominal - 3 * se <= mean <= nominal + 1 / 4_001 + 3 * se


# ---------------------------------------------------------------------------
# the finite-sample correction
# ---------------------------------------------------------------------------
def test_quantile_is_the_n_plus_one_order_statistic():
    """k = ceil((n+1)(1-alpha)), indexed into the sorted scores.

    With n=19 and alpha=0.10, k = ceil(20*0.9) = 18, so q_hat is the 18th
    smallest of the 19 scores. This is pinned exactly because the obvious
    ways to write it are each off by one, in opposite directions:

        np.quantile at the corrected level k/n, method 'higher'
            -> the 19th score. Over-covers, so no coverage test ever
               catches it; the sets are just needlessly wide.
        np.quantile at 1-alpha, method 'lower'
            -> the 17th score. Under-covers, and at small n materially.
    """
    scores = np.arange(1, 20, dtype=float)       # 1..19, sorted
    assert conformal_quantile(scores, 0.10) == 18.0
    assert np.quantile(scores, 18 / 19, method="higher") == 19.0
    assert np.quantile(scores, 0.90, method="lower") == 17.0
    # Unsorted input must give the same answer; it is an order statistic.
    assert conformal_quantile(np.random.default_rng(0).permutation(scores),
                              0.10) == 18.0
    # n=9: k = ceil(10*0.9) = 9, the maximum rather than the 90th centile.
    assert conformal_quantile(np.arange(1, 10, dtype=float), 0.10) == 9.0


def test_too_few_calibration_points_gives_an_infinite_threshold():
    """Below 1/alpha - 1 points the coverage cannot be promised at all.

    Returning a finite quantile there would manufacture a guarantee the
    sample cannot support. Infinity is the honest answer: every set contains
    every label, coverage is trivially 100%, and the width says so.
    """
    model = SplitConformalBinary(0.10).calibrate(np.array([0.2, 0.4, 0.6]),
                                                 np.array([0, 1, 0]))
    assert model.q_hat == float("inf")
    sets = model.predict_set(np.array([0.01, 0.5, 0.99]))
    assert sets.all(), "an unsupportable level must widen, not narrow"

    report = model.evaluate(np.array([0.01, 0.5]), np.array([0, 1]))
    assert report.empirical_coverage == 1.0
    assert report.mean_set_size == 2.0


def test_small_calibration_samples_still_cover():
    """The regime the first real facility panel will actually land in.

    Fifty calibration rows is where the n+1 correction stops being a detail.
    Coverage must still hold on average.
    """
    rng = np.random.default_rng(99)
    coverages = []
    for _ in range(400):
        p_cal, y_cal = controlled_dgp(50, rng)
        p_test, y_test = controlled_dgp(500, rng)
        coverages.append(SplitConformalBinary(ALPHA).calibrate(
            p_cal, y_cal).evaluate(p_test, y_test).empirical_coverage)
    assert float(np.mean(coverages)) >= NOMINAL - 0.01


# ---------------------------------------------------------------------------
# clustering: the panel's real shape
# ---------------------------------------------------------------------------
def test_clustered_calibration_is_unbiased_but_much_noisier():
    """Why a single split's coverage must be read with a tolerance.

    Splitting by unit keeps every quarter of a ZCTA on one side of the wall,
    which the leakage argument requires — but it also means the calibration
    rows are a cluster sample and strict exchangeability with one test row
    does not hold. The measured consequence is not bias, it is variance: the
    centre stays on nominal while the spread widens several-fold. A run
    reporting 88% on one clustered split is therefore ordinary noise, and
    reading it as a failure of the method would be a mistake.
    """
    spec = SyntheticSpec(n_units=1200)
    rs = build_risk_set(synthetic_panel(spec))
    units = np.sort(rs["zcta"].unique())
    rng = np.random.default_rng(20260914)

    by_unit, by_row = [], []
    for _ in range(15):
        rng.shuffle(units)
        train = set(units[:600])
        model = DiscreteTimeHazard(HazardSpec(
            covariates=tuple(spec.betas))).fit(rs[rs["zcta"].isin(train)])
        rest = rs[~rs["zcta"].isin(train)].copy()
        rest["p"] = model.predict(rest).to_numpy()

        cal_units = set(units[600:900])
        a = rest[rest["zcta"].isin(cal_units)]
        b = rest[~rest["zcta"].isin(cal_units)]
        by_unit.append(SplitConformalBinary(ALPHA).calibrate(
            a["p"], a["event"]).evaluate(b["p"], b["event"]
                                         ).empirical_coverage)

        idx = rng.permutation(len(rest))
        half = len(rest) // 2
        c, d = rest.iloc[idx[:half]], rest.iloc[idx[half:]]
        by_row.append(SplitConformalBinary(ALPHA).calibrate(
            c["p"], c["event"]).evaluate(d["p"], d["event"]
                                         ).empirical_coverage)

    assert abs(float(np.mean(by_unit)) - NOMINAL) < 0.02, "unbiased"
    assert abs(float(np.mean(by_row)) - NOMINAL) < 0.01, "unbiased"
    assert np.std(by_unit) > 2 * np.std(by_row), (
        "clustering should inflate the spread of coverage; if it does not, "
        "the tolerance in coverage_tolerance() is overstated")


def test_tolerance_uses_units_not_rows():
    """The band must widen when the caller declares the clustering."""
    rng = np.random.default_rng(3)
    p, y = controlled_dgp(2_000, rng)
    groups = np.repeat(np.arange(100), 20)

    model = SplitConformalBinary(ALPHA).calibrate(*controlled_dgp(2_000, rng))
    flat = model.evaluate(p, y)
    clustered = model.evaluate(p, y, groups=groups)

    assert flat.empirical_coverage == clustered.empirical_coverage
    assert clustered.n_effective == 100
    assert clustered.tolerance > 4 * flat.tolerance
    assert coverage_tolerance(100, ALPHA) == pytest.approx(
        2 * math.sqrt(0.09 / 100))


# ---------------------------------------------------------------------------
# plumbing
# ---------------------------------------------------------------------------
def test_prediction_sets_are_nested_in_alpha():
    """A looser level can only ever add labels, never remove them."""
    rng = np.random.default_rng(11)
    p_cal, y_cal = controlled_dgp(3_000, rng)
    p_test = np.linspace(0.001, 0.999, 200)

    tight = SplitConformalBinary(0.20).calibrate(p_cal, y_cal)
    loose = SplitConformalBinary(0.01).calibrate(p_cal, y_cal)
    assert loose.q_hat >= tight.q_hat
    assert (loose.predict_set(p_test) >= tight.predict_set(p_test)).all()


def test_predict_before_calibrate_raises():
    with pytest.raises(RuntimeError, match="calibrate"):
        SplitConformalBinary().predict_set(np.array([0.5]))


def test_rejects_an_invalid_alpha():
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="alpha"):
            SplitConformalBinary(bad)


def test_mismatched_lengths_are_caught():
    with pytest.raises(ValueError, match="against"):
        SplitConformalBinary().calibrate(np.array([0.1, 0.2]),
                                         np.array([0, 1, 0]))
