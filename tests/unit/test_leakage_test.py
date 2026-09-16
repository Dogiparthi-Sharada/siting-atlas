"""The warehousing-covariate ablation.

The measurement is a PAIRED difference: the same 50 re-splits, the same
seeds, one arm with the covariate and one without. Everything that makes it
paired is a place where a silent change would move the headline — a seed that
does not reach the split, an arm built from the wrong covariate set, or a
top-k rate reported where the rest of the project quotes counts.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from siting_atlas.common import log_json, paths
from siting_atlas.models import leakage_test
from siting_atlas.models.choice import ChoiceData


def _simulated(n_decisions: int = 20, n_cols: int = 3,
               seed: int = 5) -> ChoiceData:
    rng = np.random.default_rng(seed)
    true = np.linspace(1.0, 2.5, n_cols)
    blocks, groups, chosen, offset = [], [], [], 0
    for g in range(n_decisions):
        n = int(rng.integers(12, 30))
        a = rng.lognormal(0.0, 1.1, size=(n, n_cols))
        p = (a @ true) / (a @ true).sum()
        chosen.append(offset + int(rng.choice(n, p=p)))
        blocks.append(a)
        groups.append(np.full(n, g))
        offset += n
    names = ("households", "land_area_sqmi", "establishments",
             "warehousing_establishments")[:n_cols]
    return ChoiceData(np.vstack(blocks), np.concatenate(groups),
                      np.array(chosen), [str(i) for i in range(n_decisions)],
                      names=names)


# ---------------------------------------------------------------------------
# _one_split
# ---------------------------------------------------------------------------
def test_one_split_converts_the_rate_back_into_hits():
    """`evaluate` returns top-k as a RATE. The rest of the project quotes
    "n of 38", so a rate written into that slot reads as 0.5 hits."""
    data = _simulated()
    out = leakage_test._one_split(data, np.random.default_rng(1))
    n_test = out["n_decisions"]
    assert out["_hits"] == pytest.approx(out["top10"] * n_test)
    assert 0 <= out["_hits"] <= n_test
    assert out["_hits"] >= out["top10"]     # a count, not a rate


def test_the_split_is_sixty_forty_and_holds_out_whole_decisions():
    data = _simulated(n_decisions=20)
    out = leakage_test._one_split(data, np.random.default_rng(1))
    assert out["n_decisions"] == round(20 * leakage_test.TEST_FRACTION)


def test_the_same_seed_gives_the_same_split_so_the_arms_are_paired():
    """If the two arms saw different folds the paired difference would be
    comparing two different questions and the sd would be meaningless."""
    data = _simulated()
    a = leakage_test._one_split(data, np.random.default_rng(7))
    b = leakage_test._one_split(data, np.random.default_rng(7))
    assert a["_hits"] == b["_hits"]
    assert a["brier"] == b["brier"]


def test_a_different_seed_gives_a_different_fold():
    data = _simulated()
    seeds = {leakage_test._one_split(data, np.random.default_rng(s))["brier"]
             for s in range(6)}
    assert len(seeds) > 1


# ---------------------------------------------------------------------------
# _arm
# ---------------------------------------------------------------------------
def test_the_two_arms_differ_by_exactly_the_covariate_under_test(monkeypatch):
    """The ablation is only an ablation if one arm has the column and the
    other does not. Anything else is two unrelated models."""
    seen = {}

    def fake_build(facilities, panel, cbp, extra):
        seen[bool(cbp is not None)] = (cbp, tuple(extra))
        return _simulated()

    monkeypatch.setattr(leakage_test, "build", fake_build)
    leakage_test._arm("f", "p", "cbp", use_cbp=True)
    leakage_test._arm("f", "p", "cbp", use_cbp=False)

    assert seen[True] == ("cbp", ("warehousing_establishments",))
    assert seen[False] == (None, ())


def test_the_covariate_named_in_the_report_is_the_one_ablated():
    from siting_atlas.models.choice import CBP_ATTRACTIONS
    assert CBP_ATTRACTIONS == ("warehousing_establishments",)


def test_the_repeat_count_matches_the_other_two_experiments():
    """50 in the GBM benchmark, 50 here, 50 in the refit. A single 38-event
    test set cannot separate a two-decision difference from noise."""
    assert leakage_test.REPEATS == 50
    assert leakage_test.SEED == 20260914


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def test_a_missing_cbp_extract_says_there_is_nothing_to_ablate(data_root,
                                                               monkeypatch):
    """Without the CBP extract there is no covariate to remove, so there is
    no ablation — and saying so beats reporting a one-armed comparison.

    NOTE for whoever runs this stage: `_load` reads the facility frame and
    the 1M-row panel BEFORE it checks that `cbp_detail.parquet` exists, so on
    a fresh clone the message arrives after the expensive part rather than
    before it.
    """
    import pandas as pd

    monkeypatch.setattr(leakage_test, "load_national", lambda: "facilities")
    pd.DataFrame({"zcta": ["92081"], "cbsa_code": ["41740"],
                  "households": [1.0], "land_area_sqmi": [1.0],
                  "establishments": [1.0]}).to_parquet(paths.PANEL,
                                                       index=False)
    with pytest.raises(SystemExit, match="cbp_detail"):
        leakage_test.main()


@pytest.fixture
def stubbed(data_root, monkeypatch):
    """Everything upstream of the measurement replaced by a toy."""
    monkeypatch.setattr(leakage_test, "_load", lambda: ("f", "p", "cbp"))
    monkeypatch.setattr(leakage_test, "REPEATS", 4)
    monkeypatch.setattr(
        leakage_test, "_arm",
        lambda f, p, c, use_cbp: _simulated(n_cols=3 if use_cbp else 2))
    return data_root


def test_main_writes_a_stamped_artefact_with_both_arms(stubbed, capsys):
    """Audit sec.6.5: `leakage_test.json` carried no run_id."""
    assert leakage_test.main() == 0
    got = log_json.read_json(paths.METRICS / "leakage_test.json")

    assert got["run_id"] and got["written_at"]
    assert set(got["arms"]) == {"with_warehousing", "without_warehousing"}
    assert got["repeats"] == 4
    assert "agglomeration" in got["what_this_cannot_show"]
    assert "ablation" in capsys.readouterr().out


def test_the_paired_difference_is_the_difference_of_the_two_arms(stubbed):
    leakage_test.main()
    got = log_json.read_json(paths.METRICS / "leakage_test.json")

    a = np.array(got["arms"]["with_warehousing"]["hits"])
    b = np.array(got["arms"]["without_warehousing"]["hits"])
    delta = got["paired_difference"]
    assert delta["mean_difference"] == pytest.approx(float((a - b).mean()))
    # Wins, ties and losses must account for every repeat. A missing case is
    # a repeat that voted and was not counted.
    assert delta["with_wins"] + delta["ties"] + delta["without_wins"] == len(a)


def test_every_arm_reports_the_covariates_it_was_actually_given(stubbed):
    leakage_test.main()
    got = log_json.read_json(paths.METRICS / "leakage_test.json")
    with_cov = got["arms"]["with_warehousing"]["covariates"]
    without = got["arms"]["without_warehousing"]["covariates"]
    assert len(with_cov) == len(without) + 1
    assert set(without) < set(with_cov)


def test_the_per_repeat_hits_are_kept_so_the_pairing_can_be_re_derived(
        stubbed):
    leakage_test.main()
    got = log_json.read_json(paths.METRICS / "leakage_test.json")
    for arm in got["arms"].values():
        assert len(arm["hits"]) == 4
        json.dumps(arm)         # plain floats, not numpy scalars
