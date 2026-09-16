"""Four defects an audit found in the figure layer, pinned so they stay fixed.

Kept apart from test_viz.py, which asserts the properties a chart must have
in general. Each docstring here records the specific silent failure it is
holding shut, because a regression test whose reason is not written down is
the one the next person deletes as redundant.

What the four have in common is why they survived review: not one of them
raised, and three produced a chart that looked entirely ordinary and was
about something other than what it said.
"""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from siting_atlas.viz import charts_density as cd
from siting_atlas.viz import charts_economics as ce
from siting_atlas.viz import data as cost_data
from siting_atlas.viz import style
from tests.unit.test_viz import frame


@pytest.fixture(autouse=True)
def _close_figures():
    """Close everything a test drew; matplotlib warns after twenty leak."""
    yield
    plt.close("all")


def frame_with_varying_wages(n: int = 60) -> pd.DataFrame:
    """``frame()``, but with a per-ZCTA driver wage, as the real table has.

    The pilot indexes driver time to local income, so cost_service_time is a
    column, not a number. ``frame()`` holds it constant, and a constant
    column is exactly the condition under which a median and a minimum
    coincide — so a floor computed as a median looks perfectly correct
    against ``frame()`` and is wrong on every real table.
    """
    out = frame(n)
    out["cost_service_time"] = out["cost_service_time"] * np.linspace(
        0.8, 1.3, n)
    out["cost_per_stop"] = out[[c for c, _ in cost_data.COMPONENTS]].sum(
        axis=1)
    out["cost_per_parcel"] = out["cost_per_stop"] / 1.4
    out["daily_cost_usd"] = out["cost_per_stop"] * out["daily_stops"]
    return out


def test_one_uncosted_zcta_leaves_the_frame_rather_than_the_numerator(caplog):
    """The NaN trap cost.runner already sprang, now pinned in the figures.

    ``Series.sum()`` skips NaN but the weight stays in the denominator, so a
    single un-costed ZCTA used to contribute its doors and no dollars: that
    one segment shrank by a believable amount, the four segments stopped
    adding up to cost per stop, and no label anywhere said so. The row with
    the MOST stops is holed here because it is the worst case and the one
    most likely to be a real un-costed ZCTA — a huge metro core.
    """
    whole = frame()
    heavy = whole["daily_stops"].idxmax()
    holed = whole.copy()
    holed.loc[heavy, "cost_distance"] = np.nan

    with caplog.at_level(logging.WARNING, logger="siting_atlas.viz.economics"):
        got = ce._weighted_components(holed).loc["ALL PILOT METROS"]
    # The only defensible answer: the same means the chart would show if the
    # un-costed ZCTA had never been in the file at all.
    expected = ce._weighted_components(
        whole.drop(index=heavy)).loc["ALL PILOT METROS"]

    assert got["cost_distance"] == pytest.approx(expected["cost_distance"])
    assert got.sum() == pytest.approx(expected.sum())
    assert "incomplete cost breakdown" in caplog.text, (
        "a dropped ZCTA that is never reported is a silently smaller pilot")


def test_the_cost_floor_is_a_floor_that_no_plotted_point_goes_under():
    """The dashed line is captioned "Nothing can go below" — so nothing may.

    It was the MEDIAN of a per-row lower bound, which by construction has
    half the rows' bounds beneath it. On the pilot table that put 99 real
    ZCTAs underneath a line saying they could not exist (median 0.9489,
    smallest bound 0.8518). An annotation a reader falsifies by looking at
    the chart costs more credibility than it buys.
    """
    pts = frame_with_varying_wages()
    bound = (pts["cost_service_time"] + pts["cost_vehicle"]) / 1.4
    assert bound.median() > pts["cost_per_parcel"].min(), (
        "fixture does not discriminate: a median floor would pass this test")

    fig = cd.cost_vs_density(pts)
    floor = fig.axes[0].lines[0].get_ydata()[0]
    assert floor == pytest.approx(bound.min())
    assert (pts["cost_per_parcel"] >= floor).all()


def test_a_box_is_labelled_with_its_own_metro_when_another_is_empty(
        monkeypatch):
    """Filter the pairs, never the two lists one after the other.

    ``metro_order`` cannot hand back an empty metro today, which is exactly
    why this needs a test rather than a comment. The old code shortened
    ``series`` and then zipped it against the full ``order``, pairing each
    metro with the i-th SURVIVING series: an empty metro anywhere but the
    end dropped the LAST label instead of the empty one, and every box below
    it was captioned with its neighbour's name. Nothing raises. The chart
    just quietly describes different metros than it names.
    """
    data = frame()
    real = cost_data.metro_order(data)
    monkeypatch.setattr(cd.cost_data, "metro_order",
                        lambda f: ["Nowhere", *real])

    fig = cd.cost_by_metro(data)
    labels = [t.get_text() for t in fig.axes[0].get_yticklabels()]
    assert [lbl.split("  (")[0] for lbl in labels] == real


def test_deferred_labels_do_not_outlive_the_figures_they_point_into():
    """_PENDING held a closed Figure alive for every chart never audited.

    ``audit_overflow`` drains the queue for the figure it audits, which is
    every figure that reaches ``save_figure``. Nothing drained it for a
    figure that is only looked at — a notebook, a test, a scenario sweep —
    and each entry holds an Axes, so ten charts left ten dead Figures
    reachable and the eleventh made eleven. It never surfaced as a crash,
    only as memory.
    """
    style._PENDING.clear()
    for _ in range(10):
        plt.close(cd.cost_vs_density(frame()))

    # One entry may legitimately survive: the most recent figure's, which is
    # swept on the next fitted_text() or audit. Ten would mean none are.
    assert len(style._PENDING) <= 1
    style._drop_closed()
    assert style._PENDING == []
