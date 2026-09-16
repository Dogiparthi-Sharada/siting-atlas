"""The parameter set is the audit trail; if it can drift, nothing is traceable.

Every number the cost model reports is only reproducible if (a) the parameter
object cannot be mutated after a run has started and (b) the summary written
into the run record lists *every* field. Both are silent failures: a mutated
parameter produces a plausible number attributed to the wrong scenario, and a
summary missing a field produces a run record nobody can replay.
"""

from __future__ import annotations

import dataclasses

import pytest

from siting_atlas.cost.params import BASELINE, SCENARIOS, CostParameters


def test_parameters_are_frozen():
    # A sensitivity sweep holds several parameter sets at once. If one can be
    # mutated in place, every result already computed from it is silently
    # re-attributed to the new value and the sweep is meaningless.
    with pytest.raises(dataclasses.FrozenInstanceError):
        BASELINE.stops_per_tour = 150


def test_replace_produces_an_independent_instance():
    variant = dataclasses.replace(BASELINE, stops_per_tour=150)
    assert variant.stops_per_tour == 150
    assert BASELINE.stops_per_tour == 120, "replace() leaked into the baseline"
    # Untouched fields must carry over, or a scenario silently resets to
    # defaults on every field the caller did not name.
    assert variant.bhh_constant == BASELINE.bhh_constant


def test_summary_lists_every_field():
    # The summary is what lands in outputs/metrics. A field missing here is a
    # parameter that moved the answer and left no trace.
    fields = {f.name for f in dataclasses.fields(CostParameters)}
    assert set(BASELINE.summary()) == fields
    assert BASELINE.summary()["parcels_per_stop"] == 1.4


def test_summary_is_a_snapshot_not_a_view():
    snap = BASELINE.summary()
    snap["stops_per_tour"] = 999
    assert BASELINE.summary()["stops_per_tour"] == 120


# ---------------------------------------------------------------------------
# the unit-economics helpers, hand-checked
# ---------------------------------------------------------------------------
def test_labour_rate_is_annual_wage_over_scheduled_hours():
    # 9h x 6 days x 52 weeks = 2,808 paid hours. $45,000 loaded at 1.32 is
    # $59,400, so $21.15/hour. Getting the denominator wrong (e.g. using a
    # 40-hour week, 2,080 hours) inflates labour by 35% and nothing raises.
    assert BASELINE.labour_usd_per_hour(45_000.0) == pytest.approx(
        59_400.0 / 2_808.0)
    assert BASELINE.labour_usd_per_hour(45_000.0) == pytest.approx(21.154,
                                                                   abs=1e-3)


def test_labour_rate_is_linear_in_the_wage():
    assert (BASELINE.labour_usd_per_hour(90_000.0)
            == pytest.approx(2 * BASELINE.labour_usd_per_hour(45_000.0)))


def test_distance_cost_is_fuel_plus_maintenance():
    # $4.00/gal at 14 mpg = $0.2857/mi of fuel, plus $0.19 of wear.
    assert BASELINE.fuel_usd_per_mile(4.0) == pytest.approx(4.0 / 14.0)
    assert BASELINE.distance_usd_per_mile(4.0) == pytest.approx(
        4.0 / 14.0 + 0.19)
    # Maintenance must not be forgotten: it is 40% of the marginal mile.
    assert (BASELINE.distance_usd_per_mile(4.0)
            > BASELINE.fuel_usd_per_mile(4.0))


def test_worse_fuel_economy_costs_more_per_mile():
    thirsty = dataclasses.replace(BASELINE, van_mpg=11.0)
    assert thirsty.distance_usd_per_mile(4.0) > BASELINE.distance_usd_per_mile(
        4.0)


# ---------------------------------------------------------------------------
# the scenario table
# ---------------------------------------------------------------------------
def test_baseline_is_the_registered_baseline():
    assert SCENARIOS["baseline"] is BASELINE


@pytest.mark.parametrize("name", sorted(set(SCENARIOS) - {"baseline"}))
def test_every_scenario_actually_differs_from_baseline(name):
    """A copy-pasted scenario reports 0.0% in the sensitivity table.

    That looks like a robust model rather than a broken fixture, which is
    exactly why it goes unnoticed.
    """
    assert SCENARIOS[name] != BASELINE
    moved = [f.name for f in dataclasses.fields(CostParameters)
             if getattr(SCENARIOS[name], f.name)
             != getattr(BASELINE, f.name)]
    assert moved, f"scenario {name!r} moves nothing"


@pytest.mark.parametrize("name,params", sorted(SCENARIOS.items()))
def test_no_scenario_has_a_zero_or_negative_divisor(name, params):
    # stops_per_tour, van_mpg, avg_speed_mph and delivery_days_per_week all
    # sit in a denominator. A zero would give inf cost, and inf sorts to the
    # bottom of the ranking rather than raising.
    for field in ("stops_per_tour", "van_mpg", "avg_speed_mph",
                  "delivery_days_per_week", "parcels_per_stop",
                  "reference_income_usd", "shift_hours"):
        assert getattr(params, field) > 0, f"{name}.{field}"
