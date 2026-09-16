"""The atheoretical benchmark MODEL_SPEC.md section 9.4 specified.

The verdict this module reaches — data ceiling or model ceiling — rests on
three mechanics that would be wrong silently: the softmax that turns ranker
scores into probabilities must not reorder anything (or the Brier score and
the top-k table stop describing the same model), the share features must be
a deterministic transform of the levels (or the GBM is being handed extra
information), and every method must be re-fitted inside every repeat (or the
comparison is not paired).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from siting_atlas.common import log_json, paths
from siting_atlas.models import gbm_benchmark as gbm
from siting_atlas.models.choice import ChoiceData


def _simulated(n_decisions: int = 16, seed: int = 4) -> ChoiceData:
    """Choices over four attractions, the last one the ablated column."""
    rng = np.random.default_rng(seed)
    true = np.array([1.0, 0.3, 0.6, 2.5])
    blocks, groups, chosen, offset = [], [], [], 0
    for g in range(n_decisions):
        n = int(rng.integers(12, 24))
        a = rng.lognormal(0.0, 1.1, size=(n, 4))
        p = (a @ true) / (a @ true).sum()
        chosen.append(offset + int(rng.choice(n, p=p)))
        blocks.append(a)
        groups.append(np.full(n, g))
        offset += n
    return ChoiceData(np.vstack(blocks), np.concatenate(groups),
                      np.array(chosen), [str(i) for i in range(n_decisions)],
                      names=("households", "land_area_sqmi",
                             "establishments",
                             "warehousing_establishments"))


# ---------------------------------------------------------------------------
# _features
# ---------------------------------------------------------------------------
def test_the_share_features_double_the_width_and_sum_to_one_per_metro():
    """Shares are a deterministic transform of the same columns plus the
    group structure the logit already uses, so supplying them is not extra
    information. If they stopped summing to 1 they would be."""
    d = _simulated()
    levels = gbm._features(d, shares=False)
    with_shares = gbm._features(d, shares=True)

    assert levels.shape == d.a.shape
    assert with_shares.shape == (d.a.shape[0], 2 * d.a.shape[1])
    assert np.allclose(with_shares[:, :d.a.shape[1]], d.a)
    for k in range(d.a.shape[1]):
        column = with_shares[:, d.a.shape[1] + k]
        totals = np.bincount(d.group, weights=column)
        assert np.allclose(totals, 1.0)


def test_a_metro_whose_column_is_all_zero_gets_zero_not_a_nan():
    d = _simulated()
    d.a[:, 1] = 0.0
    with_shares = gbm._features(d, shares=True)
    assert np.isfinite(with_shares).all()
    assert (with_shares[:, 5] == 0.0).all()


# ---------------------------------------------------------------------------
# _softmax / _temperature
# ---------------------------------------------------------------------------
def test_the_softmax_is_within_metro_and_sums_to_one():
    d = _simulated()
    score = np.linspace(-2.0, 2.0, len(d.a))
    p = gbm._softmax(score, d, 1.3)
    assert np.allclose(np.bincount(d.group, weights=p), 1.0)
    assert (p >= 0).all()


def test_the_softmax_cannot_change_a_top_k_count():
    """A ranker's scores are on an arbitrary scale, so a Brier score taken
    from them means nothing and the map is needed. The map is strictly
    increasing, so every top-k count must survive it unchanged. If it ever
    did not, the probability table and the accuracy table would describe two
    different models."""
    d = _simulated()
    rng = np.random.default_rng(0)
    score = rng.normal(size=len(d.a))
    raw = [gbm._top_k_hits(score, d, k) for k in (1, 5, 10)]
    for t in (0.01, 0.5, 3.0, 40.0):
        mapped = gbm._softmax(score, d, t)
        assert [gbm._top_k_hits(mapped, d, k) for k in (1, 5, 10)] == raw


def test_a_huge_score_does_not_overflow_the_exponential():
    d = _simulated()
    p = gbm._softmax(np.full(len(d.a), 1e4), d, 200.0)
    assert np.isfinite(p).all()


def test_the_temperature_is_non_negative_and_fitted_on_what_it_is_given():
    d = _simulated()
    score = np.zeros(len(d.a))
    score[d.chosen] = 5.0            # a perfect ranker
    assert gbm._temperature(score, d) > 0.0
    # A ranker that says nothing gives no reason to sharpen.
    assert gbm._temperature(np.zeros(len(d.a)), d) >= 0.0


# ---------------------------------------------------------------------------
# _metrics / _count_only
# ---------------------------------------------------------------------------
def test_metrics_reports_the_same_fields_choice_evaluate_does():
    d = _simulated()
    got = gbm._metrics(gbm._softmax(np.zeros(len(d.a)), d, 1.0), d)
    assert set(got) == {"top1", "top5", "top10", "brier",
                        "brier_uniform_null", "mean_prob_of_chosen"}
    assert got["top1"] <= got["top5"] <= got["top10"] <= d.n_decisions
    # A constant score IS the uniform null, so the two Briers must agree.
    assert got["brier"] == pytest.approx(got["brier_uniform_null"])


def test_the_raw_count_benchmark_ranks_by_the_named_column_only():
    d = _simulated()
    assert gbm.COUNT_COLUMN in d.names
    got = gbm._count_only(d)
    assert 0 <= got["top10"] <= d.n_decisions


# ---------------------------------------------------------------------------
# _repeat
# ---------------------------------------------------------------------------
@pytest.fixture
def small_grid(monkeypatch):
    """One cheap configuration, so the repeat runs in under a second."""
    monkeypatch.setattr(gbm, "GRID", (
        ("stump/20   shares", True, {"num_leaves": 2, "max_depth": 1,
                                     "n_estimators": 20,
                                     "learning_rate": 0.10}),
        ("stump/20   levels", False, {"num_leaves": 2, "max_depth": 1,
                                      "n_estimators": 20,
                                      "learning_rate": 0.10}),
    ))
    return gbm.GRID


def test_a_repeat_scores_every_method_on_the_same_fold(small_grid):
    d = _simulated()
    out = gbm._repeat(d, gbm.SEED)
    assert set(out) == {"n_test", "conditional_logit", "raw_count",
                        "gbm stump/20   shares", "gbm stump/20   levels"}
    assert out["n_test"] == round(d.n_decisions * gbm.TEST_FRACTION)
    for name, got in out.items():
        if name == "n_test":
            continue
        assert got["top10"] <= out["n_test"], name
        assert np.isfinite(got["brier"]), name


def test_the_same_seed_reproduces_the_repeat(small_grid):
    d = _simulated()
    assert json.dumps(gbm._repeat(d, gbm.SEED), sort_keys=True) \
        == json.dumps(gbm._repeat(d, gbm.SEED), sort_keys=True)


def test_the_gain_shares_are_labelled_and_sum_to_one(small_grid):
    d = _simulated()
    rng = np.random.default_rng(gbm.SEED)
    order = rng.permutation(d.n_decisions)
    cut = int(round(d.n_decisions * (1 - gbm.TEST_FRACTION)))
    _, model = gbm._fit_gbm(d.subset(np.sort(order[:cut])),
                            d.subset(np.sort(order[cut:])),
                            True, dict(small_grid[0][2]), gbm.SEED)
    gains = gbm._gain_share(model, d.names, shares=True)
    if gains:                       # an ensemble that split on nothing is {}
        assert sum(gains.values()) == pytest.approx(1.0)
        assert set(gains) == set(d.names) | {f"{c} (share of metro)"
                                             for c in d.names}


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def test_run_writes_a_stamped_artefact_with_every_method_in_it(
        data_root, small_grid, monkeypatch):
    """Audit sec.6.5: `gbm_benchmark.json` carried no run_id."""
    import pandas as pd

    d = _simulated()
    monkeypatch.setattr(gbm, "N_REPEATS", 2)
    monkeypatch.setattr(gbm, "load_national", lambda: "facilities")
    monkeypatch.setattr(gbm, "build", lambda *a, **k: d)
    pd.DataFrame({"zcta": ["92081"], "cbsa_code": ["41740"],
                  "households": [1.0], "land_area_sqmi": [1.0],
                  "establishments": [1.0]}).to_parquet(paths.PANEL,
                                                       index=False)
    pd.DataFrame({"zcta": ["92081"], "year": [2019],
                  "warehousing_establishments": [3]}).to_parquet(
        paths.INTERIM / "cbp_detail.parquet", index=False)

    report = gbm.run()
    got = log_json.read_json(paths.METRICS / "gbm_benchmark.json")

    assert got["run_id"] and got["written_at"]
    assert got["n_repeats"] == 2
    assert got["seed"] == gbm.SEED
    assert got["spec"] == "docs/MODEL_SPEC.md section 9.4"
    # Every method reported in the headline split is also reported across
    # repeats. One table naming a method the other does not is how a
    # configuration quietly drops out of the comparison.
    assert set(got["headline_split"]) == set(got["across_repeats"])
    assert got["best_gbm_by_cv_top10"].startswith("gbm ")
    assert report["n_decisions_total"] == d.n_decisions


def test_run_refuses_to_benchmark_without_the_cbp_extract(data_root,
                                                          monkeypatch):
    """Without it the logit is fitted on three covariates and the comparison
    is not the one section 9.4 asks for."""
    import pandas as pd

    monkeypatch.setattr(gbm, "load_national", lambda: "facilities")
    pd.DataFrame({"zcta": ["92081"], "cbsa_code": ["41740"],
                  "households": [1.0], "land_area_sqmi": [1.0],
                  "establishments": [1.0]}).to_parquet(paths.PANEL,
                                                       index=False)
    with pytest.raises(FileNotFoundError, match="cbp_detail"):
        gbm.run()
