"""Refitting the choice model on two panels and reporting both.

The module's own warning is that the bigger number is not automatically the
better one, and the thing to read is whether a coefficient interval finally
excludes the numeraire. That only works if the artefact reports RATES rather
than counts (the two panels hold different numbers of held-out decisions) and
labels every interval with the covariate it belongs to. Both are asserted
here, on a simulated panel small enough to run in a second.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from siting_atlas.common import log_json, paths
from siting_atlas.models import refit_expanded
from siting_atlas.models.choice import ChoiceData


def _simulated(n_decisions: int = 24, seed: int = 3) -> ChoiceData:
    """Choices drawn from a known beta over lognormal attractions."""
    rng = np.random.default_rng(seed)
    true = np.array([1.0, 0.3, 2.5])
    blocks, groups, chosen, offset = [], [], [], 0
    for g in range(n_decisions):
        n = int(rng.integers(12, 30))
        a = rng.lognormal(0.0, 1.1, size=(n, 3))
        p = (a @ true) / (a @ true).sum()
        chosen.append(offset + int(rng.choice(n, p=p)))
        blocks.append(a)
        groups.append(np.full(n, g))
        offset += n
    return ChoiceData(np.vstack(blocks), np.concatenate(groups),
                      np.array(chosen), [str(i) for i in range(n_decisions)],
                      names=("households", "land_area_sqmi",
                             "establishments"))


def test_measure_reports_every_field_the_artefact_promises():
    got = refit_expanded._measure(_simulated(), repeats=3)
    for key in ("n_decisions", "n_test", "covariates", "top10_rate",
                "top10_rate_sd", "top10_uniform_rate", "brier",
                "beta_mean", "beta_p025", "beta_p975"):
        assert key in got, key
    assert got["n_decisions"] == 24
    assert got["n_test"] == round(24 * 0.40)


def test_accuracy_is_a_rate_so_two_panels_of_different_size_compare():
    """Counting hits instead would make "19 of 38" and "19 of 194" look
    like the same result."""
    got = refit_expanded._measure(_simulated(), repeats=3)
    assert 0.0 <= got["top10_rate"] <= 1.0
    assert 0.0 <= got["top10_uniform_rate"] <= 1.0
    assert 0.0 <= got["brier"] <= 1.0


def test_every_interval_is_labelled_with_the_covariate_it_belongs_to():
    """Households is the numeraire and has no interval. If the labels ever
    slip by one, every coefficient in the artefact is attributed to the
    wrong variable and nothing says so."""
    data = _simulated()
    got = refit_expanded._measure(data, repeats=3)
    expected = set(data.names[1:])
    assert set(got["beta_mean"]) == expected
    assert set(got["beta_p025"]) == expected
    assert set(got["beta_p975"]) == expected
    assert "households" not in got["beta_mean"]


def test_the_percentile_interval_brackets_its_own_mean():
    got = refit_expanded._measure(_simulated(), repeats=8)
    for name in got["beta_mean"]:
        assert got["beta_p025"][name] <= got["beta_mean"][name] \
            <= got["beta_p975"][name], name


def test_the_same_seed_gives_the_same_answer_twice():
    """Repeat r uses SEED + r. A drifting result would move the headline
    without any input changing."""
    data = _simulated()
    a = refit_expanded._measure(data, repeats=3)
    b = refit_expanded._measure(data, repeats=3)
    assert a["top10_rate"] == b["top10_rate"]
    assert a["beta_mean"] == b["beta_mean"]


def test_the_seed_actually_reaches_the_split():
    assert refit_expanded.SEED == 20260914
    assert refit_expanded.REPEATS == 50


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def test_main_refuses_to_run_without_the_expanded_panel(data_root,
                                                        monkeypatch):
    monkeypatch.setattr(refit_expanded, "EXPANDED",
                        data_root / "nowhere.csv")
    with pytest.raises(SystemExit, match="mwpvl_merge"):
        refit_expanded.main()


def test_main_stamps_the_artefact_it_writes(data_root, monkeypatch,
                                            capsys):
    """Audit sec.6.5: `refit_expanded.json` carried no run_id.

    Everything upstream of the write is stubbed; what is exercised is the
    artefact contract, which is where the stamp lives.
    """
    measure = refit_expanded._measure      # bound before it is replaced
    expanded = data_root / "expanded.csv"
    original = data_root / "original.csv"
    expanded.write_text("facility_id\n" + "x\n" * 693, encoding="utf-8")
    original.write_text("facility_id\n" + "x\n" * 104, encoding="utf-8")
    monkeypatch.setattr(refit_expanded, "EXPANDED", expanded)
    monkeypatch.setattr(refit_expanded, "NATIONAL_PATH", original)
    monkeypatch.setattr(refit_expanded, "_panel_and_cbp",
                        lambda: (None, None))
    monkeypatch.setattr(
        refit_expanded, "load_national",
        lambda path=None: [0] * (104 if path == original else 687))
    monkeypatch.setattr(refit_expanded, "build", lambda *a, **k: _simulated())
    monkeypatch.setattr(refit_expanded, "_measure",
                        lambda data, repeats=3: measure(data, 3))

    assert refit_expanded.main() == 0
    got = log_json.read_json(paths.METRICS / "refit_expanded.json")
    assert got["run_id"] and got["written_at"]
    assert set(got["arms"]) == {"original", "expanded"}
    assert got["repeats"] == refit_expanded.REPEATS
    assert "OCR'd" in got["caveat"]
    assert "original" in capsys.readouterr().out


def test_arm_keys_carry_no_row_count(data_root, monkeypatch, capsys):
    """The arm keys were `original_104` and `expanded_658`, and by
    2026-09-15 the expanded file held 693 rows and 687 facilities while the
    key still said 658. A key is the one field a re-run cannot refresh, so
    no count may live in one; the count belongs in `rows_in_file` and
    `facilities`, which this asserts are present and current.
    """
    measure = refit_expanded._measure
    expanded = data_root / "expanded.csv"
    original = data_root / "original.csv"
    expanded.write_text("facility_id\n" + "x\n" * 693, encoding="utf-8")
    original.write_text("facility_id\n" + "x\n" * 104, encoding="utf-8")
    monkeypatch.setattr(refit_expanded, "EXPANDED", expanded)
    monkeypatch.setattr(refit_expanded, "NATIONAL_PATH", original)
    monkeypatch.setattr(refit_expanded, "_panel_and_cbp",
                        lambda: (None, None))
    monkeypatch.setattr(
        refit_expanded, "load_national",
        lambda path=None: [0] * (104 if path == original else 687))
    monkeypatch.setattr(refit_expanded, "build", lambda *a, **k: _simulated())
    monkeypatch.setattr(refit_expanded, "_measure",
                        lambda data, repeats=3: measure(data, 3))

    assert refit_expanded.main() == 0
    arms = log_json.read_json(paths.METRICS / "refit_expanded.json")["arms"]
    for key in arms:
        assert not any(ch.isdigit() for ch in key), key
    assert arms["expanded"]["rows_in_file"] == 693
    assert arms["expanded"]["facilities"] == 687
    assert arms["original"]["rows_in_file"] == 104
    assert arms["original"]["facilities"] == 104


def test_the_artefact_is_json_serialisable_end_to_end():
    """A numpy float32 in the payload raises inside json.dump, AFTER the run
    has spent its time. Everything `_measure` returns must be plain."""
    json.dumps(refit_expanded._measure(_simulated(), repeats=2))
