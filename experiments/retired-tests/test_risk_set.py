"""Tests for risk-set construction and the clock it is indexed on.

These live apart from ``test_hazard.py`` because they test the pieces the
hazard model is assembled FROM, and because the risk-set invariants deserve
a file whose name says what is being protected. The time baseline, the
metrics and the ``enabled``-column parser used to live here too and now have
files of their own: ``test_timebasis.py``, ``test_metrics.py``,
``test_truthy.py``.

The dense-panel error the first group pins down has no runtime symptom. The
code runs, the coefficients print, the standard errors look tight, and every
number is biased toward zero. There is nothing to catch it by except a test.
The left-truncation group beneath it is the same shape of problem one layer
down: a correction that removes the right units and the wrong rows, leaving
a quarter whose event count is zero by construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.models import fixtures as fx
from siting_atlas.models.hazard import DiscreteTimeHazard, HazardSpec
from siting_atlas.models.risk_set import (
    TargetUnpopulatedError,
    build_risk_set,
    quarter_index,
    summarise,
    validate_risk_set,
)

COVARIATES = tuple(fx.TRUE_COEFFICIENTS)


@pytest.fixture(scope="module")
def risk() -> pd.DataFrame:
    return build_risk_set(fx.synthetic_panel(fx.SyntheticSpec(n_units=1200)))


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
# the risk set — the silent error
# ---------------------------------------------------------------------------
def test_unit_leaves_the_risk_set_after_the_event():
    """The headline invariant: enablement is absorbing.

    A unit enabled in quarter 3 of an 8-quarter panel must contribute 4 rows
    (t = 0, 1, 2, 3), not 8. The four rows that would remain are fabricated
    non-events about the most attractive unit in the sample, and they bias
    every coefficient toward zero.
    """
    # A second, never-enabled unit so the panel has at least one event and
    # one censored unit, as any real panel will.
    panel = pd.concat([tiny_panel(3), tiny_panel(None, unit="SYN-00002")])
    rs = build_risk_set(panel)

    treated = rs[rs["zcta"] == "SYN-00001"]
    assert list(treated["t"]) == [0, 1, 2, 3]
    assert list(treated["event"]) == [0, 0, 0, 1]

    censored = rs[rs["zcta"] == "SYN-00002"]
    assert len(censored) == 8, "a never-enabled unit keeps all of its rows"
    assert censored["event"].sum() == 0


def test_state_and_event_encodings_give_the_same_risk_set():
    """The panel builder's choice of encoding must not reach the estimator.

    ``enabled`` may arrive as a state flag (True from the opening onwards)
    or an event flag (True only in the opening quarter). Taking the first
    True row and truncating is what makes both collapse to one answer.
    """
    state = build_risk_set(pd.concat([
        tiny_panel(4, state_encoding=True),
        tiny_panel(None, unit="SYN-00002")]))
    event = build_risk_set(pd.concat([
        tiny_panel(4, state_encoding=False),
        tiny_panel(None, unit="SYN-00002")]))
    pd.testing.assert_frame_equal(state, event)


def test_left_truncated_units_are_dropped():
    """A unit enabled in the first observed quarter is not an event.

    It is a unit whose exposure started before the window. Keeping it treats
    unknown prior exposure as zero, which inflates the hazard at t=0 and
    drags the whole baseline with it.
    """
    panel = pd.concat([tiny_panel(0), tiny_panel(5, unit="SYN-00002"),
                       tiny_panel(None, unit="SYN-00003")])
    rs = build_risk_set(panel)
    assert "SYN-00001" not in set(rs["zcta"])
    assert set(rs["zcta"]) == {"SYN-00002", "SYN-00003"}

    kept = build_risk_set(panel, drop_left_truncated=False)
    assert "SYN-00001" in set(kept["zcta"])
    assert len(kept[kept["zcta"] == "SYN-00001"]) == 1


def test_left_truncation_does_not_leave_an_empty_first_quarter(risk):
    """Dropping the units and keeping their quarter is the worse half-fix.

    Every unit removed as left-truncated is, by definition, a unit with an
    event in the first quarter. Remove those units and leave the quarter in
    place and what survives at t=0 is precisely the units that did NOT have
    the event: a whole quarter of exposure with a structurally impossible
    zero numerator. The estimator cannot tell that apart from a genuine lull,
    so the spline bends down to meet it and the reported baseline comes out
    roughly a third low at the start of the window — on synthetic data whose
    true opening hazard we know to be 0.0067, the fitted curve said 0.0046.

    Nothing warns. The fit converges, the standard errors are ordinary, and
    the only visible trace is a first quarter that looks unusually quiet,
    which is exactly what a reader would expect a build-out to look like.

    The fix is delayed entry: the sample becomes "units not yet enabled at
    the end of the first quarter" and everybody enters at t=1, so no
    remaining quarter has been selected on its own outcome.
    """
    first = risk[risk["t"] == risk["t"].min()]
    assert first["event"].sum() > 0, (
        "the earliest quarter in the risk set has zero events by "
        "construction — it was selected on the outcome and must not be in "
        "the sample at all")
    assert risk["t"].min() == 1, "the truncated quarter goes, not just the "\
                                 "truncated units"


def test_left_truncation_removes_the_quarter_and_nothing_else():
    """The drop must be surgical: those units, that quarter, no more.

    Stated on a panel small enough to count by hand, because "dropped too
    much" and "dropped too little" both produce a risk set that looks
    perfectly reasonable from the outside.
    """
    panel = pd.concat([tiny_panel(0),                       # truncated
                       tiny_panel(5, unit="SYN-00002"),     # real event
                       tiny_panel(None, unit="SYN-00003")])  # censored
    rs = build_risk_set(panel)

    assert set(rs["zcta"]) == {"SYN-00002", "SYN-00003"}
    # SYN-00002 keeps five of its original eight rows: t=0 goes with the
    # truncated quarter, t=6 and t=7 go because the event is absorbing.
    assert list(rs.loc[rs["zcta"] == "SYN-00002", "t"]) == [1, 2, 3, 4, 5]
    assert rs.loc[rs["zcta"] == "SYN-00002", "event"].sum() == 1
    assert list(rs.loc[rs["zcta"] == "SYN-00003", "t"]) == [1, 2, 3, 4, 5,
                                                            6, 7]


def test_no_left_truncation_means_no_quarter_is_spent():
    """The correction costs a quarter of exposure, so it must not fire
    speculatively. With nobody flagged in the opening quarter there is
    nothing ambiguous to correct for and t=0 has to survive intact."""
    panel = pd.concat([tiny_panel(3), tiny_panel(6, unit="SYN-00002"),
                       tiny_panel(None, unit="SYN-00003")])
    rs = build_risk_set(panel)
    assert rs["t"].min() == 0
    assert len(rs[rs["t"] == 0]) == 3


def test_a_wholly_truncated_panel_raises_instead_of_returning_nothing():
    """If every unit was enabled in the first quarter there is no risk set.

    Returning the empty frame would run: the GLM would be handed zero rows,
    or a split would silently produce three empty parts, and the report
    would announce a successful run with no events in it.
    """
    panel = pd.concat([tiny_panel(0), tiny_panel(0, unit="SYN-00002")])
    with pytest.raises(TargetUnpopulatedError, match="entire sample is "
                                                     "left-truncated"):
        build_risk_set(panel)


def test_all_null_target_raises_rather_than_fitting_nothing():
    """The panel ships ``enabled`` typed and all-NULL. fillna(False) there
    would give a sample in which nothing ever happens, and a GLM will fit
    that quite happily."""
    panel = tiny_panel(None)
    panel["enabled"] = pd.NA
    with pytest.raises(TargetUnpopulatedError, match="no True values"):
        build_risk_set(panel)


def test_validate_rejects_a_contaminated_risk_set():
    """The guard that makes the dense-panel mistake impossible to commit."""
    rs = build_risk_set(pd.concat([tiny_panel(3),
                                   tiny_panel(None, unit="SYN-00002")]))
    # Put the post-event rows back, which is exactly what using the panel
    # unchanged would have done.
    contaminated = pd.concat([rs, pd.DataFrame({
        "zcta": "SYN-00001", "t": [4, 5, 6, 7], "event": 0,
        "year": 2019, "quarter": 1, "x_demand": 0.5, "x_cost": -0.2,
        "x_competition": 0.1})], ignore_index=True)

    with pytest.raises(ValueError, match="remain in the sample after"):
        validate_risk_set(contaminated)


def test_fit_refuses_a_contaminated_risk_set(risk):
    """fit() re-checks rather than trusting its caller."""
    bad = pd.concat([risk, risk[risk["event"] == 1].assign(
        t=lambda d: d["t"] + 1, event=0)], ignore_index=True)
    with pytest.raises(ValueError, match="after their event"):
        DiscreteTimeHazard(HazardSpec(covariates=COVARIATES)).fit(bad)


def test_quarter_index_is_a_single_clock():
    idx = quarter_index([2018, 2018, 2019, 2025], [1, 4, 1, 4])
    assert list(idx) == [0, 3, 4, 31]


# ---------------------------------------------------------------------------
# the clock: two ways to get a plausible wrong answer
# ---------------------------------------------------------------------------
def test_quarter_index_keeps_the_callers_index():
    """Assigning the result back onto a frame must not produce NaN.

    ``pd.Series(np.asarray(...))`` builds a fresh 0..n-1 index. Assigning
    that to a column of a frame whose index is anything else — a filtered
    slice, a concat, anything real — aligns on labels that do not match and
    fills the column with NaN. Pandas does this silently, so the failure
    surfaces far downstream as a design matrix full of missing time, or, if
    the caller uses ``.to_numpy()`` on it first, not at all until someone
    does not.
    """
    frame = pd.DataFrame({"year": [2018, 2018, 2019],
                          "quarter": [1, 2, 3]}, index=[10, 11, 12])
    frame["t"] = quarter_index(frame["year"], frame["quarter"])
    assert list(frame["t"]) == [0, 1, 6], (
        "the clock was computed correctly and then thrown away by index "
        "misalignment")
    assert frame["t"].notna().all()


def test_quarter_index_origin_is_a_quarter_not_a_year():
    """A panel that opens mid-year must still start its clock at zero.

    ``base = year.min()`` ignores the quarter, so a window opening in 2018Q3
    is numbered t = 2, 3, 4 ... The model then places its spline knots on a
    grid that begins at 2 and reports a "t=0 hazard" for a quarter that was
    never observed. Every duration in the panel is overstated by two
    quarters and nothing is out of range, so nothing complains.
    """
    assert list(quarter_index([2018, 2018, 2019], [3, 4, 1])) == [0, 1, 2]
    # An explicit base_year still means "that year's Q1", unchanged.
    assert list(quarter_index([2018, 2019], [3, 1], base_year=2017)) == [6, 8]


def test_risk_set_summary_shape(risk):
    shape = summarise(risk)
    # t_min is 1, not 0: the fixture contains left-truncated units, so the
    # opening quarter is removed for everyone rather than left in the sample
    # with its events selected out. See
    # test_left_truncation_does_not_leave_an_empty_first_quarter.
    assert shape["t_min"] == 1 and shape["t_max"] == 31
    assert shape["events"] == int(risk["event"].sum())
    assert 0 < shape["event_rate"] < 0.10, "a rare event, as designed"
