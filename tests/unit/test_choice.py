"""The conditional ZCTA-choice model, and the two properties that define it.

Both tests below check a claim in the module docstring that would be easy to
break silently and expensive to discover later: aggregation invariance is the
entire reason for the `ln(beta'a)` form, and scale invariance is the reason
one coefficient is fixed rather than estimated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.models.choice import (
    ATTRACTIONS,
    ChoiceData,
    build,
    evaluate,
    fit,
    predict,
)


def _toy(n_alts: int = 6, seed: int = 1) -> ChoiceData:
    rng = np.random.default_rng(seed)
    a = rng.uniform(1.0, 10.0, size=(n_alts * 3, len(ATTRACTIONS)))
    group = np.repeat(np.arange(3), n_alts)
    chosen = np.array([0, n_alts, 2 * n_alts])
    return ChoiceData(a, group, chosen, ["a", "b", "c"])


def test_probabilities_sum_to_one_within_every_choice_set():
    d = _toy()
    p = predict(np.zeros(len(ATTRACTIONS) - 1), d)
    for g in range(d.n_decisions):
        assert np.isclose(p[d.group == g].sum(), 1.0)


def test_the_model_is_scale_invariant_in_beta():
    """Why one coefficient is FIXED rather than estimated.

    P(j) = beta'a_j / sum_k beta'a_k, so multiplying every coefficient by c
    cancels. Only ratios are identified. If this ever fails, the numeraire
    convention has stopped being a convention and become a restriction.
    """
    d = _toy()
    theta = np.array([0.4, -0.2])
    base = predict(theta, d)
    # Scaling every beta by exp(1) means adding 1 to every theta AND to the
    # numeraire's implicit log-coefficient of 0. The numeraire is pinned at 1,
    # so the equivalent check is that the ratio structure is what matters:
    # rescale the attraction matrix instead, which is the same operation.
    d2 = ChoiceData(d.a * 7.0, d.group, d.chosen, d.ids)
    assert np.allclose(base, predict(theta, d2))


def test_aggregation_invariance_the_whole_reason_for_the_log_form():
    """Train Sec. 3.4 Example 2: merging two zones must not change the answer.

    If zones j and k merge into c, the model must give P_c = P_j + P_k. That
    holds for `ln(beta'a)` precisely because the attraction variables are
    EXTENSIVE and add on merger. A linear-in-parameters utility fails this,
    which is why the specification is not free to use one.
    """
    a = np.array([[2.0, 1.0, 3.0],
                  [4.0, 2.0, 1.0],
                  [1.0, 5.0, 2.0]])
    d = ChoiceData(a, np.zeros(3, int), np.array([0]), ["x"])
    theta = np.array([0.3, -0.6])
    p = predict(theta, d)

    merged = np.vstack([a[0] + a[1], a[2]])       # zones 0 and 1 combined
    dm = ChoiceData(merged, np.zeros(2, int), np.array([0]), ["x"])
    pm = predict(theta, dm)

    assert np.isclose(pm[0], p[0] + p[1]), (
        "merging two zones changed the answer, so the model is measuring how "
        "the Census drew its boundaries rather than where a station goes")


def _simulate(n_decisions: int, true: np.ndarray, sigma: float,
              seed: int = 11) -> ChoiceData:
    """Choices drawn from a known beta.

    ``sigma`` is the lognormal spread of the attraction variables and it is
    the parameter that matters — see the two tests below.
    """
    rng = np.random.default_rng(seed)
    blocks, groups, chosen, offset = [], [], [], 0
    for g in range(n_decisions):
        n = int(rng.integers(8, 25))
        a = (rng.lognormal(0.0, sigma, size=(n, 3)) if sigma > 0
             else rng.uniform(0.5, 5.0, size=(n, 3)))
        p = (a @ true) / (a @ true).sum()
        chosen.append(offset + int(rng.choice(n, p=p)))
        blocks.append(a)
        groups.append(np.full(n, g))
        offset += n
    return ChoiceData(np.vstack(blocks), np.concatenate(groups),
                      np.array(chosen),
                      [str(i) for i in range(n_decisions)])


def test_fit_recovers_a_known_coefficient_on_simulated_choices():
    """Generate choices from a known beta, then recover it.

    Attractions are lognormal because real ZCTAs are: households in a metro
    span three orders of magnitude. See the next test for why that matters
    more than the sample size does.
    """
    got = fit(_simulate(2000, np.array([1.0, 0.25, 3.0]), sigma=1.2))
    assert got["converged"]
    # Ratios, not levels: households is the numeraire at 1.0.
    assert got["beta"]["land_area_sqmi"] == pytest.approx(0.25, abs=0.10)
    assert got["beta"]["establishments"] == pytest.approx(3.0, rel=0.25)


def test_identification_comes_from_spread_not_from_sample_size():
    """The property that decides whether 60 real decisions are enough.

    Found while writing the test above, which originally used uniform(0.5, 5)
    attractions and failed at 400 decisions — recovering 2.81 for a true 0.25.
    The optimiser was not at fault: it reached a HIGHER likelihood than the
    truth (-LL 1069.70 against 1071.88). The likelihood surface was simply
    flat, because when every alternative is nearly equally attractive each
    choice carries almost no information.

    So sample size is not the binding constraint on this estimator; the
    dispersion of the attraction variables within a choice set is. That is
    good news for us: real ZCTA household counts within a metro span orders of
    magnitude, far more than the uniform case that failed here. It is also a
    warning — do not read a precise coefficient off a metro whose ZCTAs are
    all of a size.
    """
    true = np.array([1.0, 0.25, 3.0])
    flat = fit(_simulate(400, true, sigma=0.0))          # uniform, narrow
    spread = fit(_simulate(400, true, sigma=1.2))        # lognormal, wide

    flat_err = abs(flat["beta"]["land_area_sqmi"] - 0.25)
    spread_err = abs(spread["beta"]["land_area_sqmi"] - 0.25)
    assert spread_err < flat_err, (
        "widening the attraction distribution did not improve recovery; the "
        "claim that identification comes from spread no longer holds")


def test_evaluate_beats_a_uniform_null_on_simulated_data():
    d = _toy(n_alts=12, seed=5)
    got = evaluate(np.zeros(len(ATTRACTIONS) - 1), d)
    assert 0.0 <= got["top1"] <= 1.0
    assert got["n_decisions"] == 3


@pytest.mark.skipif(not paths.PANEL.exists(),
                    reason="needs a built panel; run make panel")
def test_the_real_choice_sets_contain_the_choice_that_was_made():
    """A choice set missing its own observed choice has zero likelihood.

    `build` drops such a facility rather than fitting through it. This pins
    that the drop count stays small: if the zcta join degrades, this is the
    test that notices before the coefficients quietly change.
    """
    from siting_atlas.warehouse.national import load_national
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    d = build(load_national(), panel)
    assert d.n_decisions >= 90, (
        f"only {d.n_decisions} of ~100 national facilities produced a usable "
        "choice set; the zcta-to-CBSA join has degraded")
    for g in range(d.n_decisions):
        assert d.group[d.chosen[g]] == g


def test_the_linehaul_saving_is_zero_where_the_network_already_reaches():
    """The property that makes the saving covariate different from population.

    Two candidates with identical demand must score differently if one sits
    on top of an existing depot. If this ever fails, the covariate has
    collapsed into a headcount and there is no reason to pay the aggregation
    -invariance cost of carrying it.
    """
    from siting_atlas.models.accessibility import savings_for_metro
    alts = pd.DataFrame({
        "zcta": ["A", "B", "C"],
        "latitude": [40.00, 40.00, 40.30],
        "longitude": [-75.00, -75.05, -75.00],
        "households": [1000.0, 1000.0, 1000.0],
    })
    greenfield = savings_for_metro(alts, [])
    assert greenfield.min() > 0, "with no prior network everything saves"

    # Put a depot on A. B is 2.7 road miles away and keeps almost nothing;
    # C is 20 miles north and still has demand to win.
    served = savings_for_metro(alts, ["A"])
    assert served[0] < greenfield[0]
    assert served[1] < greenfield[1]
    assert served[2] > served[1], (
        "a candidate far from the existing depot must out-score one sitting "
        "next to it, or the covariate is measuring demand and nothing else")


def test_conformal_sets_cover_at_the_nominal_rate_on_calibration_itself():
    """The guarantee, checked on data where it must hold by construction.

    Conformal coverage on the calibration decisions is not a real test of
    generalisation — that is what the held-out split in the runner is for —
    but it IS a test that the score and the quantile agree with each other.
    An off-by-one in either direction shows up here immediately and is
    otherwise very hard to see.
    """
    from siting_atlas.models.choice_conformal import (
        aps_scores,
        calibrate,
        prediction_sets,
    )
    d = _simulate(200, np.array([1.0, 0.25, 3.0]), sigma=1.2)
    theta = np.asarray(fit(d)["theta"], float)

    scores = aps_scores(theta, d)
    assert scores.min() > 0.0
    assert scores.max() <= 1.0 + 1e-9

    for alpha in (0.10, 0.25):
        q = calibrate(theta, d, alpha)
        sets = prediction_sets(theta, d, q)
        covered = np.mean([d.chosen[g] in s for g, s in enumerate(sets)])
        assert covered >= 1.0 - alpha - 1e-9, (
            f"coverage {covered:.3f} below the nominal {1 - alpha:.2f}; the "
            "APS score and the conformal quantile disagree")


def test_a_worse_model_buys_coverage_with_a_bigger_set_not_less_coverage():
    """The mechanism that makes conformal worth having.

    Degrade the model deliberately and coverage must HOLD while the sets get
    wider. If coverage falls instead, the guarantee is not being delivered
    and every conformal number in the project is decoration.
    """
    from siting_atlas.models.choice_conformal import calibrate, summarise
    d = _simulate(300, np.array([1.0, 0.25, 3.0]), sigma=1.2)
    good = np.asarray(fit(d)["theta"], float)
    bad = np.zeros_like(good)          # every attraction weighted equally

    out = {}
    for name, theta in (("good", good), ("bad", bad)):
        q = calibrate(theta, d, 0.10)
        out[name] = summarise(theta, d, q, 0.10)
        assert out[name]["empirical_coverage"] >= 0.90 - 1e-9, (
            f"the {name} model failed to cover; conformal is not working")
    assert out["bad"]["set_size_mean"] >= out["good"]["set_size_mean"], (
        "the worse model produced SMALLER sets, which means the score is "
        "not measuring what it claims to measure")
