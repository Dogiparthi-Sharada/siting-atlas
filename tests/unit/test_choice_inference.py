"""Uncertainty for the choice model: the four claims that could lie quietly.

A bootstrap that resamples the wrong unit, a sandwich computed at a boundary,
an unseeded draw and a mislabelled one-sided interval all produce output that
looks exactly like output. Each test below pins one of them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.models.choice import ATTRACTIONS, ChoiceData, fit
from siting_atlas.models.choice_bootstrap import (
    ALPHA,
    bootstrap,
    metro_clusters,
    resample_decisions,
)
from siting_atlas.models.choice_inference import summarise
from siting_atlas.models.choice_sandwich import BOUNDARY_TOL, sandwich

NAMES = ("households", "a1", "a2")


def _toy(n_alts: int = 5, n_dec: int = 12, seed: int = 3) -> ChoiceData:
    """Choice sets of a fixed size, with the chosen row varying."""
    rng = np.random.default_rng(seed)
    a = rng.uniform(1.0, 9.0, size=(n_alts * n_dec, len(NAMES)))
    group = np.repeat(np.arange(n_dec), n_alts)
    chosen = np.arange(n_dec) * n_alts + rng.integers(0, n_alts, n_dec)
    return ChoiceData(a, group, chosen, [f"f{i}" for i in range(n_dec)], NAMES)


def test_a_repeated_decision_appears_twice_with_its_whole_choice_set():
    """The property ``ChoiceData.subset`` cannot provide, and the reason.

    ``subset`` maps decision indices through a dict, so drawing decision 4
    twice would collapse it to one and the replicate would be a draw WITHOUT
    replacement of an unknown size. That would understate the spread, which
    is the flattering direction, which is how it would survive review.
    """
    d = _toy()
    draw = np.array([4, 4, 0])
    r = resample_decisions(d, draw)

    assert r.n_decisions == 3
    assert np.bincount(r.group).tolist() == [5, 5, 5]
    for g, src in enumerate(draw):
        rows = np.flatnonzero(r.group == g)
        src_rows = np.flatnonzero(d.group == src)
        assert np.allclose(r.a[rows], d.a[src_rows])
        # The chosen alternative must travel with its own copy of the set.
        assert np.allclose(r.a[r.chosen[g]], d.a[d.chosen[src]])


def test_the_bootstrap_never_splits_a_choice_set():
    """Every replicate is a whole number of complete choice sets.

    Resampling alternatives instead of decisions would leave a metro's ZCTAs
    spread across replicates and break the conditioning the likelihood is
    built on. This is the hazard model's error in a different costume; see
    `docs/adr/0004`.
    """
    d = _toy()
    rng = np.random.default_rng(0)
    for _ in range(20):
        draw = rng.integers(0, d.n_decisions, d.n_decisions)
        r = resample_decisions(d, draw)
        assert len(r.a) == 5 * d.n_decisions
        assert set(np.bincount(r.group).tolist()) == {5}


def test_the_bootstrap_is_reproducible_from_its_seed():
    """An unseeded bootstrap makes the PUBLISHED interval irreproducible."""
    d = _toy()
    theta = np.zeros(len(NAMES) - 1)
    one = bootstrap(d, theta, seed=11)
    two = bootstrap(d, theta, seed=11)
    assert np.allclose(one["beta"], two["beta"])
    assert one["replicates"] == two["replicates"]


def test_the_sandwich_refuses_a_boundary_parameter_and_says_why():
    """The test the brief exists for.

    At ``beta = exp(theta) -> 0`` the optimum is not interior, so the
    Hessian block is not the information matrix the sandwich asymptotics
    assume and any standard error printed there is meaningless rather than
    merely large. The refusal must be explicit, not a silent NaN that a
    downstream table renders as a blank.
    """
    d = _toy()
    theta = np.array([-40.0, 0.3])          # first parameter at the boundary
    out = sandwich(theta, d, ("a1", "a2"))

    assert out["a1"]["available"] is False
    assert "boundary" in out["a1"]["reason"]
    assert "se_beta_delta_method" not in out["a1"]
    assert out["a2"]["available"] is True
    assert out["a2"]["se_beta_delta_method"] > 0


def test_the_sandwich_matches_a_numerical_hessian_at_an_interior_optimum():
    """The analytic score and Hessian, checked against finite differences.

    Hand-derived derivatives are exactly the kind of thing that is wrong by
    a factor of beta and still produces plausible standard errors.
    """
    from scipy.optimize import approx_fprime

    from siting_atlas.models.choice import _neg_log_likelihood
    from siting_atlas.models.choice_sandwich import score_and_hessian

    d = _toy()
    theta = np.array([0.2, -0.3])
    scores, hess = score_and_hessian(theta, d)

    grad = approx_fprime(theta, lambda t: -_neg_log_likelihood(t, d), 1e-6)
    assert np.allclose(scores.sum(axis=0), grad, atol=1e-5)

    def total_score(t, k):
        return score_and_hessian(t, d)[0].sum(axis=0)[k]

    numerical = np.stack([approx_fprime(theta, total_score, 1e-6, k)
                          for k in range(2)])
    assert np.allclose(hess, numerical, atol=1e-4)


def test_a_boundary_parameter_gets_a_one_sided_interval_labelled_as_one():
    """Not a two-sided interval with a zero lower bound quietly inserted."""
    d = _toy()
    fitted = {"theta": [-40.0, 0.3], "numeraire": "households"}
    out = summarise(d, fitted, seed=5)

    a1 = out["parameters"]["a1"]
    assert a1["at_boundary"] is True
    assert a1["bootstrap_over_decisions"]["kind"] == "one-sided percentile"
    assert a1["bootstrap_over_decisions"]["lower"] == 0.0
    assert a1["bca"]["available"] is False
    assert out["parameters"]["a2"]["bca"]["kind"] == "BCa"


def test_every_interval_is_labelled_as_a_ratio_to_the_numeraire():
    """An interval on beta_k is one on the RATIO beta_k / beta_households.

    A reader who takes it for an absolute effect has read the headline
    backwards, and the only defence is that the artefact says so on every
    row.
    """
    d = _toy()
    out = summarise(d, {"theta": [0.1, 0.3], "numeraire": "households"}, 5)
    for name, entry in out["parameters"].items():
        assert "ratio" in entry["interpretation"]
        assert name in entry["interpretation"]
    assert "beta = 1" in out["null_that_matters"]
    assert "large enough" in out["train_precondition"]


def test_the_metro_label_read_off_the_choice_sets_matches_the_real_cbsa():
    """`metro_clusters` infers the metro from the choice set. Verify it.

    If two metros ever shared a (size, household total) signature the
    clustered bootstrap would merge them, so this is checked against the
    actual CBSA codes on the real data rather than asserted.
    """
    from siting_atlas.models.choice import CBP_ATTRACTIONS, build
    from siting_atlas.warehouse.national import load_national

    if not paths.PANEL.exists():
        pytest.skip("no panel on this tree")
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    cbp = pd.read_parquet(cbp_path) if cbp_path.exists() else None
    facilities = load_national()
    d = build(facilities, panel, cbp, CBP_ATTRACTIONS if cbp is not None
              else ())

    home = panel.drop_duplicates("zcta").set_index("zcta")["cbsa_code"]
    truth = pd.Series([home.get(str(r.zcta).strip()) for r in
                       facilities.itertuples()],
                      index=facilities["facility_id"].astype(str))
    inferred = metro_clusters(d)
    frame = pd.DataFrame({"truth": [truth[i] for i in d.ids],
                          "inferred": inferred})
    assert frame.groupby("inferred")["truth"].nunique().max() == 1
    assert frame.groupby("truth")["inferred"].nunique().max() == 1


def test_the_published_warehousing_interval_is_what_the_report_says():
    """The headline number, regenerated from the real data, not trusted.

    Guards the one figure a reader will quote: the interval on
    warehousing_establishments and whether it excludes 1.0.
    """
    report = paths.METRICS / "choice_report.json"
    if not report.exists():
        pytest.skip("no choice_report.json on this tree")
    import json
    inference = json.loads(report.read_text()).get("inference")
    if inference is None:
        pytest.fail("choice_report.json carries no inference block")
    w = inference["parameters"]["warehousing_establishments"]
    ci = w["bootstrap_over_decisions"]
    assert ci["lower"] < w["beta_point"] < ci["upper"]
    assert ci["excludes_ratio_one"] == (ci["lower"] > 1.0 or ci["upper"] < 1.0)
    assert inference["alpha"] == ALPHA
    assert inference["resampling_unit"].startswith("decision")


def test_a_genuinely_zero_covariate_is_found_at_the_boundary():
    """End to end: fit data where one attraction carries no information.

    If the boundary machinery only ever fires on hand-set thetas it is not
    tested. Here the third column is pure noise that the chosen alternative
    does not respond to, and beta for it should collapse.
    """
    rng = np.random.default_rng(9)
    n_alts, n_dec = 6, 40
    hh = rng.uniform(1.0, 9.0, n_alts * n_dec)
    noise = rng.uniform(1.0, 9.0, n_alts * n_dec)
    a = np.column_stack([hh, noise])
    group = np.repeat(np.arange(n_dec), n_alts)
    chosen = []
    for g in range(n_dec):
        rows = np.flatnonzero(group == g)
        p = hh[rows] / hh[rows].sum()       # choice depends on hh ALONE
        chosen.append(int(rng.choice(rows, p=p)))
    d = ChoiceData(a, group, np.array(chosen), [f"f{i}" for i in range(n_dec)],
                   ("households", "noise"))
    beta = fit(d)["beta"]["noise"]
    assert beta < BOUNDARY_TOL, (
        f"a covariate the choice does not respond to came back at {beta}, so "
        "the boundary case the inference module is built around is not what "
        "the fitter produces")
