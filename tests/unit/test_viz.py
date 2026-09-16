"""Tests for the figure layer.

A chart cannot be asserted to be *good*, so these assert the three things
that actually break a figure pipeline and break it silently:

1. It produces a Figure at all, with the marks and the text it claims to.
2. It survives the degenerate frames a dashboard filter produces — empty,
   one row, all-NaN, zero-density — instead of taking the app down.
3. The text-overflow audit is doing real work. A fitter that always returns
   "fits" is worse than none, because it is trusted, so there is a test that
   forces a label not to fit and checks the audit says so.

Streamlit is deliberately untested here; app.kpis holds every number the
dashboard displays precisely so the arithmetic can be checked without one.
The two things that only exist inside the app — figure lifetime and the
semantics of a metric tile — are in test_dashboard.py, which drives it
headlessly with streamlit.testing.
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from siting_atlas.app import kpis
from siting_atlas.viz import charts_density as cd
from siting_atlas.viz import charts_economics as ce
from siting_atlas.viz import data as cost_data
from siting_atlas.viz import style

CHARTS = [cd.cost_vs_density, cd.cost_by_metro, ce.cost_decomposition,
          ce.cumulative_coverage]


def frame(n: int = 60) -> pd.DataFrame:
    """A synthetic cost table with the schema the real runner writes.

    Synthetic on purpose: a test that reads outputs/tables passes or fails
    depending on whether somebody has run the model today, which makes it
    useless as a regression test.
    """
    rng = np.linspace(0.5, 4000.0, n)
    metros = ["Austin", "Boise", "Chicago", "Miami"] * (n // 4 + 1)
    service, vehicle = 0.85, 0.34
    distance = 0.57 / np.sqrt(rng) * 0.08
    drive = 0.57 / np.sqrt(rng) * 0.20
    per_stop = service + vehicle + distance + drive
    out = pd.DataFrame({
        "zcta": [f"{10000 + i}" for i in range(n)],
        "metro_label": metros[:n],
        "state": ["TX"] * n,
        "stop_density_per_sqmi": rng,
        "cost_service_time": service,
        "cost_vehicle": vehicle,
        "cost_distance": distance,
        "cost_drive_time": drive,
        "cost_per_stop": per_stop,
        "cost_per_parcel": per_stop / 1.4,
        "daily_parcels": np.linspace(50, 9000, n),
        "daily_stops": np.linspace(35, 6400, n),
        "daily_cost_usd": per_stop * np.linspace(35, 6400, n),
        # Both, as the real table carries both: van_days is the fractional
        # capacity a ZCTA consumes and is the one that may be added up.
        "van_days": np.linspace(35, 6400, n) / 120,
        "vans_required": np.ceil(np.linspace(35, 6400, n) / 120),
        "linehaul_miles": np.linspace(1, 40, n),
        "income_imputed": False,
    })
    return out.sort_values("cost_per_parcel").assign(
        rank=range(1, n + 1)).reset_index(drop=True)


@pytest.fixture(autouse=True)
def _close_figures():
    """Close everything a test drew; matplotlib warns after twenty leak."""
    yield
    plt.close("all")


@pytest.mark.parametrize("chart", CHARTS)
def test_every_chart_returns_a_figure_with_content(chart):
    fig = chart(frame())
    assert isinstance(fig, Figure)
    ax = fig.axes[0]
    assert ax.get_title() or ax.texts, "a chart with no title and no text"


@pytest.mark.parametrize("chart", CHARTS)
def test_empty_frame_does_not_raise(chart):
    """A metro filter can select nothing. That is not an error."""
    fig = chart(frame().iloc[0:0])
    assert isinstance(fig, Figure)
    said_something = any(t.get_text() for ax in fig.axes for t in ax.texts)
    assert said_something, "an empty chart must explain itself, not go blank"


@pytest.mark.parametrize("chart", CHARTS)
def test_all_nan_costs_do_not_raise(chart):
    bad = frame()
    bad["cost_per_parcel"] = np.nan
    bad["cost_per_stop"] = np.nan
    assert isinstance(chart(bad), Figure)


@pytest.mark.parametrize("chart", CHARTS)
def test_scattered_nan_and_inf_do_not_raise(chart):
    """Real output can carry an inf: a ZCTA with zero land area."""
    bad = frame()
    bad.loc[0:4, "stop_density_per_sqmi"] = np.inf
    bad.loc[5:9, "stop_density_per_sqmi"] = 0.0
    bad.loc[10:14, "daily_parcels"] = np.nan
    bad.loc[15:19, "cost_per_parcel"] = np.nan
    assert isinstance(chart(bad), Figure)


@pytest.mark.parametrize("chart", CHARTS)
def test_single_row_does_not_raise(chart):
    assert isinstance(chart(frame().head(1)), Figure)


def test_scatter_never_colours_more_than_three_metros():
    """The all-pairs colour-vision cap is a rule, not a default (viz.style)."""
    fig = cd.cost_vs_density(frame(), highlight=["Austin", "Boise", "Chicago",
                                                 "Miami"])
    labelled = [c.get_label() for c in fig.axes[0].collections]
    named = [lbl for lbl in labelled if not lbl.startswith("Other")]
    assert len(named) <= len(style.HUE_SLOTS)


def test_scatter_drops_nonpositive_density_rather_than_plotting_it():
    bad = frame()
    bad.loc[0:9, "stop_density_per_sqmi"] = 0.0
    assert len(cd._plottable(bad)) == len(bad) - 10


def test_decomposition_segments_sum_to_the_total_cost_per_stop():
    """A stack whose parts do not add up to its whole is a lie, not a chart."""
    got = ce._weighted_components(frame())
    pooled = frame()
    expected = float((pooled["cost_per_stop"] * pooled["daily_stops"]).sum()
                     / pooled["daily_stops"].sum())
    assert got.loc["ALL PILOT METROS"].sum() == pytest.approx(expected)


def test_metro_order_is_cheapest_median_first():
    order = cost_data.metro_order(frame())
    medians = [frame().loc[frame().metro_label == m,
                           "cost_per_parcel"].median() for m in order]
    assert medians == sorted(medians)


def test_parcels_per_stop_is_recovered_from_the_output():
    assert cost_data.parcels_per_stop(frame()) == pytest.approx(1.4)


def test_missing_table_names_the_command_that_creates_it(data_root):
    with pytest.raises(cost_data.CostTableMissingError) as exc:
        cost_data.load(2023, 4, "baseline")
    assert "siting_atlas.cost.runner" in str(exc.value)
    assert "--scenario baseline" in str(exc.value)


def test_loader_rejects_a_table_missing_a_column(data_root, tmp_path):
    """An old parquet must fail loudly, not draw a plausible wrong picture."""
    from siting_atlas.common import paths
    paths.TABLES.mkdir(parents=True, exist_ok=True)
    frame().drop(columns=["cost_vehicle"]).to_parquet(
        paths.TABLES / "cost_to_serve_2023q4_baseline.parquet", index=False)
    with pytest.raises(KeyError, match="cost_vehicle"):
        cost_data.load(2023, 4, "baseline")


def test_overflow_audit_actually_catches_an_unfittable_label():
    """Guard against a fitter that always says yes."""
    style.apply_style()
    fig, ax = plt.subplots(figsize=(3, 3))
    style.fitted_text(ax, 0.0, 0.0, 0.02, 0.02, "a label far too long to fit")
    assert style.audit_overflow(fig, "deliberate") != []


def test_overflow_audit_passes_a_label_that_fits():
    style.apply_style()
    fig, ax = plt.subplots(figsize=(8, 4))
    style.fitted_text(ax, 0.05, 0.05, 0.9, 0.3, "short")
    assert style.audit_overflow(fig, "fine") == []


def test_save_figure_reports_its_own_overflow(data_root):
    """save_figure used to return only a path, so the defect list was lost."""
    style.apply_style()
    fig, ax = plt.subplots(figsize=(3, 3))
    style.fitted_text(ax, 0.0, 0.0, 0.02, 0.02, "another far too long label")
    saved = style.save_figure(fig, "unit_test_figure")
    assert saved.path.exists()
    assert saved.overflow


# --- the numbers behind the dashboard tiles --------------------------------

def test_summarise_counts_at_or_below_the_ceiling():
    got = kpis.summarise(frame(), threshold=1.0)
    assert got["under"] == int((frame()["cost_per_parcel"] <= 1.0).sum())
    assert got["under_share"] == pytest.approx(got["under"] / 60 * 100)


def test_summarise_on_an_empty_frame_is_zeroes_not_a_crash():
    got = kpis.summarise(frame().iloc[0:0], threshold=1.0)
    assert got["zctas"] == 0 and got["under"] == 0


def test_parcel_share_survives_zero_demand():
    """A filter can select rows with no modelled parcels; 0/0 is not 'nan%'."""
    zero = frame()
    zero["daily_parcels"] = 0.0
    assert kpis.summarise(zero, threshold=2.0)["parcel_share"] == 0.0


def test_the_fleet_is_summed_before_it_is_rounded():
    """A per-ZCTA whole-van count may not be added up.

    ``vans_required`` is ``ceil(van_days)`` per ZCTA and cost.daganzo
    documents it as the "if this ZCTA had a dedicated van" reading. Summing
    it charged a sparse ZCTA with two stops a day a whole van of its own; on
    the pilot that overstated the fleet by about 1,200 vans, in a headline
    tile, with nothing to suggest the number was not the model's own.
    """
    data = frame()
    got = kpis.summarise(data, threshold=1.0)["vans"]

    assert got == math.ceil(data["van_days"].sum())
    assert got < int(data["vans_required"].sum()), (
        "fixture does not discriminate: every van_days is already whole")


def test_empty_metro_selection_means_all_metros():
    assert len(kpis.filter_frame(frame(), [])) == 60
    assert set(kpis.filter_frame(frame(), ["Boise"])["metro_label"]) == {
        "Boise"}
