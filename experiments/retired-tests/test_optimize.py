"""Tests for the portfolio objective and the budgeted selector.

The objective's failure modes are all silent: a wrong interaction form still
returns a plausible dollar figure, and a broken greedy still returns a
portfolio. So these tests pin the SHAPE of the economics, not just the types.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from siting_atlas.optimize.objective import (
    PortfolioObjective,
    PortfolioParameters,
)
from siting_atlas.optimize.select import BudgetedSelector


def make_frame(n: int = 6, spread: float = 0.02) -> tuple:
    """n ZCTAs in a line, close enough to interact."""
    frame = pd.DataFrame({
        "zcta": [f"{10000 + i:05d}" for i in range(n)],
        "daily_parcels": np.full(n, 1000.0),
        "daily_cost_usd": np.full(n, 1500.0),
        "cost_per_parcel": np.full(n, 1.5),
        "linehaul_miles_per_stop": np.full(n, 0.2),
        "miles_per_stop": np.full(n, 0.5),
        "metro_label": ["Test"] * n,
    })
    panel = pd.DataFrame({
        "zcta": frame["zcta"],
        "latitude": 40.0 + spread * np.arange(n),
        "longitude": np.full(n, -74.0),
    })
    return frame, panel


def mask(n: int, *idx) -> np.ndarray:
    m = np.zeros(n, dtype=bool)
    for i in idx:
        m[i] = True
    return m


# ---------------------------------------------------------------------------
# the interaction form
# ---------------------------------------------------------------------------
def test_cannibalisation_never_exceeds_its_ceiling():
    """The bug this replaced: additive loss reached 90% of demand.

    Exposure in a densely selected metro reaches ~90. A linear rule then
    claimed neighbours destroy nearly all demand, which is arithmetic rather
    than economics. The saturating form must be bounded by `peak` no matter
    how many neighbours are active.
    """
    frame, panel = make_frame(n=40, spread=0.001)   # all effectively on top
    obj = PortfolioObjective(frame, panel)
    everything = np.ones(obj.n, dtype=bool)

    alone = obj.evaluate(mask(obj.n, 0))
    crowded = obj.evaluate(everything)

    per_zcta_alone = alone["parcels"]
    per_zcta_crowded = crowded["parcels"] / crowded["n"]
    retained = per_zcta_crowded / per_zcta_alone

    peak = obj.params.cannibalisation_peak
    assert retained >= 1 - peak - 1e-9, (
        f"lost {1 - retained:.1%} of volume, above the {peak:.0%} ceiling")
    assert retained < 1.0, "fully overlapping ZCTAs must lose something"


def test_isolated_zctas_do_not_interact():
    """Beyond the radius the interaction must be exactly zero, not merely
    small — otherwise a national run accumulates spurious coupling."""
    frame, panel = make_frame(n=2, spread=5.0)      # ~345 miles apart
    obj = PortfolioObjective(frame, panel)

    both = obj.evaluate(mask(2, 0, 1))
    one = obj.evaluate(mask(2, 0))
    assert both["parcels"] == pytest.approx(2 * one["parcels"])
    assert both["cost"] == pytest.approx(2 * one["cost"])


def test_adjacent_selection_loses_volume_but_saves_linehaul():
    """Both directions of the interaction must actually fire."""
    frame, panel = make_frame(n=2, spread=0.01)
    obj = PortfolioObjective(frame, panel)

    one = obj.evaluate(mask(2, 0))
    both = obj.evaluate(mask(2, 0, 1))
    assert both["parcels"] < 2 * one["parcels"], "no cannibalisation applied"
    assert both["cost"] < 2 * one["cost"], "no line-haul sharing applied"


# ---------------------------------------------------------------------------
# break-even identity
# ---------------------------------------------------------------------------
def test_standalone_breakeven_equals_cost_per_parcel():
    """m* = b/a is the claim the whole reporting story rests on."""
    frame, panel = make_frame(n=3, spread=5.0)
    obj = PortfolioObjective(frame, panel)
    np.testing.assert_allclose(obj.standalone_breakeven(),
                               frame["cost_per_parcel"].to_numpy())


def test_capital_raises_the_breakeven_above_operating_cost():
    """Capital has to be earned back, so the portfolio break-even must exceed
    the pure operating cost per parcel."""
    frame, panel = make_frame(n=4, spread=5.0)
    obj = PortfolioObjective(frame, panel)
    got = obj.evaluate(np.ones(4, dtype=bool))["breakeven_margin"]
    assert got > frame["cost_per_parcel"].iloc[0]


def test_empty_selection_is_infinite_not_a_crash():
    frame, panel = make_frame(n=3)
    obj = PortfolioObjective(frame, panel)
    out = obj.evaluate(np.zeros(3, dtype=bool))
    assert out["n"] == 0 and np.isinf(out["breakeven_margin"])


# ---------------------------------------------------------------------------
# batched path must agree with the scalar path
# ---------------------------------------------------------------------------
def test_batch_matches_scalar_exactly():
    """The batched sweep is an optimisation, so it must not change the answer.

    A silent divergence here would make greedy optimise a different objective
    from the one reported, which no output would reveal.
    """
    frame, panel = make_frame(n=12, spread=0.01)
    obj = PortfolioObjective(frame, panel)
    sel = mask(12, 0, 3, 7)
    exposure = obj.exposure(sel)
    cand = np.array([i for i in range(12) if not sel[i]])

    batched = obj.batch_breakeven(sel, exposure, cand, block=3)
    for j, c in enumerate(cand):
        trial = sel.copy()
        trial[c] = True
        assert batched[j] == pytest.approx(obj.marginal_breakeven(trial))


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------
def test_selector_never_exceeds_the_budget():
    """The budget is a ceiling, not a quota.

    An earlier version forced the full budget to be spent, which is what hid
    the objective's degeneracy: it could not express "this last activation
    destroys value", so it always looked like it had chosen to spend.
    """
    frame, panel = make_frame(n=10, spread=0.5)
    obj = PortfolioObjective(frame, panel)
    cap = obj.params.capital_per_activation_usd
    sel = BudgetedSelector(obj, 3 * cap).solve()
    assert 1 <= sel["detail"]["n"] <= 3
    assert sel["detail"]["capital"] <= 3 * cap


def test_selector_stops_when_the_next_activation_destroys_value():
    """At a margin far below every break-even, nothing is worth building."""
    frame, panel = make_frame(n=10, spread=0.5)
    obj = PortfolioObjective(frame, panel)
    cap = obj.params.capital_per_activation_usd
    poor = BudgetedSelector(obj, 8 * cap).solve(margin=0.01)
    rich = BudgetedSelector(obj, 8 * cap).solve(margin=50.0)
    assert poor["detail"]["n"] < rich["detail"]["n"], (
        "the selection did not respond to the margin, so the stopping rule "
        "is not doing anything")
    assert rich["detail"]["n"] == 8, "a high margin should spend the budget"


def test_npv_is_linear_in_the_margin():
    """NPV = m*A - B. Two points determine it, so a third must lie on the
    line; a non-linear result means capital is being double counted."""
    frame, panel = make_frame(n=5, spread=5.0)
    obj = PortfolioObjective(frame, panel)
    sel = np.ones(5, dtype=bool)
    a, b, c = (obj.npv(sel, m) for m in (1.0, 2.0, 3.0))
    assert (b - a) == pytest.approx(c - b)


def test_frontier_activates_more_as_the_margin_rises():
    frame, panel = make_frame(n=12, spread=0.5)
    obj = PortfolioObjective(frame, panel)
    rows = BudgetedSelector(
        obj, 10 * obj.params.capital_per_activation_usd).frontier(
            [0.5, 2.0, 8.0])
    counts = [r["n"] for r in rows]
    assert counts == sorted(counts), f"not monotone in margin: {counts}"


def test_budget_below_one_activation_raises():
    frame, panel = make_frame(n=4)
    obj = PortfolioObjective(frame, panel)
    with pytest.raises(ValueError, match="cannot fund even one"):
        BudgetedSelector(obj, 1000.0)


def test_greedy_prefers_spread_over_clustered_when_cannibalisation_bites():
    """Two tight clusters far apart: greedy should not take one whole cluster.

    This is the behaviour that justifies the optimiser existing at all. If it
    picked purely by standalone cost it would fill one cluster first, and the
    test would fail.
    """
    n = 8
    lat = np.array([40.0, 40.001, 40.002, 40.003,   # cluster A
                    45.0, 45.001, 45.002, 45.003])  # cluster B, far away
    frame = pd.DataFrame({
        "zcta": [f"{10000 + i:05d}" for i in range(n)],
        "daily_parcels": np.full(n, 1000.0),
        "daily_cost_usd": np.full(n, 1500.0),
        # Cluster A marginally cheaper, so a naive rule takes all of it.
        "cost_per_parcel": np.array([1.40, 1.41, 1.42, 1.43,
                                     1.50, 1.51, 1.52, 1.53]),
        "linehaul_miles_per_stop": np.full(n, 0.2),
        "miles_per_stop": np.full(n, 0.5),
        "metro_label": ["A"] * 4 + ["B"] * 4,
    })
    panel = pd.DataFrame({"zcta": frame["zcta"], "latitude": lat,
                          "longitude": np.full(n, -74.0)})
    obj = PortfolioObjective(frame, panel)
    picked = BudgetedSelector(
        obj, 4 * obj.params.capital_per_activation_usd).solve()["selected"]

    from_a = picked[:4].sum()
    assert 0 < from_a < 4, (
        f"greedy took {from_a}/4 from the cheap cluster; it is ignoring "
        f"cannibalisation and behaving like a naive top-K")


def test_upper_bound_is_actually_a_bound():
    frame, panel = make_frame(n=10, spread=0.01)
    obj = PortfolioObjective(frame, panel)
    res = BudgetedSelector(obj,
                           5 * obj.params.capital_per_activation_usd).solve()
    assert res["upper_bound"] <= res["breakeven_margin"] + 1e-9
    assert res["optimality_gap"] >= -1e-9


def test_local_search_never_worsens_the_portfolio():
    frame, panel = make_frame(n=14, spread=0.01)
    obj = PortfolioObjective(frame, panel)
    sel = BudgetedSelector(obj, 6 * obj.params.capital_per_activation_usd)
    res = sel.solve()
    assert res["breakeven_margin"] <= res["greedy_breakeven"] + 1e-9


# ---------------------------------------------------------------------------
# parameters
# ---------------------------------------------------------------------------
def test_parameters_are_frozen():
    """A scenario sweep must not be able to mutate the baseline underneath a
    result that has already been recorded against it."""
    p = PortfolioParameters()
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.discount_rate = 0.2


def test_annuity_factor_matches_the_closed_form():
    p = PortfolioParameters(horizon_years=7, discount_rate=0.10)
    assert p.annuity_factor == pytest.approx(4.8684, abs=1e-3)
