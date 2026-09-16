"""Tests for the joint parameter Monte Carlo.

Three things can go wrong in this module and not one of them raises.

A draw can leave its documented range, which silently widens the band the
write-up quotes. The mode can drift off the baseline, which makes the sampled
prior a different prior from the one the docstring claims. And a failed draw
can be dropped instead of recorded — the worst of the three, because the
parameter combinations that break the solver are not a random sample of
parameter combinations. Dropping them biases the distribution toward the
numerically comfortable, and the bias is invisible in the output.

So the tests pin the SHAPE of the sampler and the bookkeeping around failure,
not the types. The expensive solve is replaced by a fake wherever the test is
about the loop rather than about the economics.
"""

from __future__ import annotations

import dataclasses
import json
import logging

import numpy as np
import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.cost.params import BASELINE
from siting_atlas.optimize import montecarlo as mc
from siting_atlas.optimize.objective import PortfolioParameters

TRIANGULAR = {**mc.COST_RANGES, **mc.PORTFOLIO_RANGES}


def _modes() -> dict[str, float]:
    """Baseline value for every sampled parameter, from the dataclasses."""
    base = {**dataclasses.asdict(BASELINE),
            **dataclasses.asdict(PortfolioParameters())}
    return {k: float(base[k]) for k in (*TRIANGULAR, *mc.UNIFORM)}


def _sample(n: int, seed: int = 7) -> pd.DataFrame:
    """`n` joint draws, one frame with one column per parameter."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        cost_p, port_p = mc.draw(rng)
        rows.append({**dataclasses.asdict(cost_p),
                     **dataclasses.asdict(port_p)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------- the sampler

def test_baseline_is_inside_every_documented_range():
    """The mode must be a legal value, or the range and the code disagree."""
    modes = _modes()
    for name, (lo, hi) in {**TRIANGULAR, **mc.UNIFORM}.items():
        assert lo <= modes[name] <= hi, (
            f"{name} baseline {modes[name]} outside [{lo}, {hi}]")


def test_every_draw_stays_inside_its_documented_range():
    """No draw may leave the range PARAMETERS.md documents for it."""
    frame = _sample(500)
    for name, (lo, hi) in {**TRIANGULAR, **mc.UNIFORM}.items():
        col = frame[name].to_numpy(float)
        assert col.min() >= lo, f"{name} drew {col.min()} below {lo}"
        assert col.max() <= hi, f"{name} drew {col.max()} above {hi}"


def test_unsampled_parameters_are_held_at_their_baseline():
    """Anything absent from the range tables must not move.

    `capital_per_activation_usd` in particular: STATUS.md sec.6 records that
    its unit is wrong, and sampling a quantity whose definition is broken
    would dress a
    known defect as uncertainty.
    """
    frame = _sample(50)
    modes = {**dataclasses.asdict(BASELINE),
             **dataclasses.asdict(PortfolioParameters())}
    sampled = {*TRIANGULAR, *mc.UNIFORM}
    assert "capital_per_activation_usd" not in sampled
    for name, base in modes.items():
        if name not in sampled:
            assert (frame[name] == base).all(), f"{name} moved, unsampled"


def test_the_mode_of_a_large_sample_sits_near_the_baseline():
    """Triangular mean is (lo + mode + hi) / 3, so it locates the mode.

    A sampler that quietly used the range midpoint as the mode would pass a
    bounds check and fail this one, which is the point.
    """
    frame = _sample(4000)
    modes = _modes()
    for name, (lo, hi) in TRIANGULAR.items():
        expected = (lo + modes[name] + hi) / 3.0
        observed = float(frame[name].mean())
        assert abs(observed - expected) <= 0.04 * (hi - lo), (
            f"{name} mean {observed:.4f} against expected {expected:.4f}")


def test_the_modal_bin_contains_the_baseline():
    """The densest part of the sample is where the baseline is."""
    frame = _sample(4000)
    modes = _modes()
    for name, (lo, hi) in TRIANGULAR.items():
        counts, edges = np.histogram(frame[name].to_numpy(float),
                                     bins=10, range=(lo, hi))
        peak = int(counts.argmax())
        width = (hi - lo) / 10.0
        centre = (edges[peak] + edges[peak + 1]) / 2.0
        assert abs(centre - modes[name]) <= width, (
            f"{name} peaks at {centre:.4f}, baseline is {modes[name]:.4f}")


def test_discount_rate_is_uniform_not_triangular():
    """Its baseline is the range midpoint, so only the spread tells them apart.

    Uniform variance is (hi - lo)^2 / 12; a symmetric triangular is half that.
    """
    lo, hi = mc.UNIFORM["discount_rate"]
    observed = float(_sample(4000)["discount_rate"].var(ddof=0))
    assert observed == pytest.approx((hi - lo) ** 2 / 12.0, rel=0.15)
    assert "discount_rate" not in TRIANGULAR


def test_a_baseline_outside_its_range_is_warned_about_and_clamped(
        monkeypatch, caplog):
    """An inconsistency between range and baseline must be audible."""
    monkeypatch.setitem(mc.COST_RANGES, "circuity", (2.0, 3.0))
    with caplog.at_level(logging.WARNING):
        frame = _sample(20)
    assert "outside its documented range" in caplog.text
    assert frame["circuity"].between(2.0, 3.0).all()


# ------------------------------------------------------- the draw-loop wiring

class _FakeCostModel:
    """Cost per parcel proportional to service time, so draws differ."""

    def __init__(self, params):
        self.params = params

    def evaluate(self, frame):
        out = frame.copy()
        out["cost_per_parcel"] = 1.0 * self.params.service_minutes_per_stop
        return out


class _FakeObjective:
    def __init__(self, costed, panel, params):
        self.costed, self.panel, self.params = costed, panel, params


class _FakeSelector:
    """Returns a plausible solve. `fail_on` marks draws that blow up."""

    fail_on: set[int] = set()
    calls = 0

    def __init__(self, obj, budget):
        self.obj, self.budget = obj, budget

    def solve(self):
        i = type(self).calls
        type(self).calls += 1
        if i in type(self).fail_on:
            raise ValueError(f"synthetic failure on draw {i}")
        n = 280 + i
        return {"detail": {"n": n, "capital": 4_000_000.0 * n},
                "breakeven_margin": 1.3 + 0.01 * i,
                "optimality_gap": 0.1,
                "selected": [f"{10000 + j:05d}" for j in range(3)]}


@pytest.fixture
def wired(data_root, monkeypatch):
    """`run` with the panel, the pilot slice and the solve all replaced."""
    frame = pd.DataFrame({
        "zcta": ["10001", "10002", "10003"],
        "daily_parcels": [1000.0, 900.0, 800.0],
        "cost_per_parcel": [1.0, 1.1, 1.2],
    })
    panel = pd.DataFrame({
        "zcta": ["10001", "10002", "10003"],
        "latitude": [40.0, 40.1, 40.2],
        "longitude": [-74.0, -74.0, -74.0],
    })
    paths.PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(paths.PANEL, index=False)
    monkeypatch.setattr(mc, "pilot_slice", lambda y, q: frame)
    monkeypatch.setattr(mc, "DaganzoCostModel", _FakeCostModel)
    monkeypatch.setattr(mc, "PortfolioObjective", _FakeObjective)
    monkeypatch.setattr(mc, "BudgetedSelector", _FakeSelector)
    _FakeSelector.calls = 0
    _FakeSelector.fail_on = set()
    yield
    _FakeSelector.calls = 0
    _FakeSelector.fail_on = set()


def test_a_failed_draw_is_recorded_rather_than_silently_dropped(wired):
    """The bias test. Failures must survive into the artefact as rows.

    If a draw vanishes, the remaining sample is conditioned on "the solver
    coped", which is correlated with the parameters and therefore not the
    distribution anybody asked for.
    """
    _FakeSelector.fail_on = {1, 4, 5}
    report = mc.run(draws=8, seed=1)

    assert report["draws"] == 8
    assert report["failed"] == 3
    assert report["ok"] == 5

    rows = pd.read_parquet(paths.TABLES / "montecarlo_draws.parquet")
    assert len(rows) == 8, "a failed draw left no row behind"
    assert sorted(rows.loc[~rows["ok"], "draw"]) == [1, 4, 5]
    assert rows["draw"].tolist() == list(range(8))
    assert rows.loc[~rows["ok"], "n"].isna().all()


def test_the_bands_are_computed_over_the_surviving_draws_only(wired):
    """A failed row must not be read as a zero-activation portfolio."""
    _FakeSelector.fail_on = {0}
    report = mc.run(draws=5, seed=1)
    band = report["bands"]["n"]
    assert band["min"] == 281.0 and band["max"] == 284.0
    assert band["p10"] >= 281.0


def test_every_draw_failing_is_an_error_not_an_empty_report(wired):
    _FakeSelector.fail_on = set(range(4))
    with pytest.raises(RuntimeError, match="every draw failed"):
        mc.run(draws=4, seed=1)


def test_the_report_carries_the_not_a_confidence_interval_caveat(wired):
    """The caveat is load-bearing: it must reach the artefact too."""
    report = mc.run(draws=3, seed=1)
    text = report["interpretation"]
    assert "NOT a confidence interval" in text
    assert "no external source" in text
    written = json.loads(
        (paths.METRICS / "montecarlo_report.json").read_text(encoding="utf-8"))
    assert written["interpretation"] == text


def test_the_artefact_records_every_sampled_parameter_per_draw(wired):
    """Without the parameters beside the outcome, no driver analysis."""
    mc.run(draws=3, seed=1)
    rows = pd.read_parquet(paths.TABLES / "montecarlo_draws.parquet")
    for name in mc.COST_RANGES:
        assert f"c_{name}" in rows.columns
    for name in (*mc.PORTFOLIO_RANGES, *mc.UNIFORM):
        assert f"p_{name}" in rows.columns
    assert "p_capital_per_activation_usd" not in rows.columns


def test_the_run_is_reproducible_from_its_seed(wired):
    first = mc.run(draws=4, seed=99)
    _FakeSelector.calls = 0
    second = mc.run(draws=4, seed=99)
    assert first["bands"] == second["bands"]
