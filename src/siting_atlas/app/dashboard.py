"""L5 — the interactive cost-to-serve dashboard.

    bash scripts/run_dashboard.sh

Same chart functions as siting_atlas.viz.build, so the app and the printed
figures cannot disagree. The app adds only filtering; it computes nothing the
batch build does not.

Two failure modes shaped this file:

* The cost parquet may not exist — the figures are downstream of a model run,
  and a fresh clone has no outputs/. The app must then print the exact
  command that produces it and stop, rather than showing a traceback in the
  browser.
* Streamlit re-runs the whole script on every widget change, so anything
  expensive has to be cached and every matplotlib figure has to be closed
  once it is drawn. ``st.pyplot(clear_figure=True)`` does NOT do that: it
  calls ``fig.clf()``, which empties the figure but leaves it registered with
  pyplot. Streamlit's script runner happens to call ``plt.close("all")``
  between runs, so this never grew without bound in practice — but that is an
  undocumented internal of somebody else's package, and within a single run
  it still meant four dead figures held open while the fourth was drawn.
  ``_show`` closes each figure itself, so the guarantee belongs to this file.

This module deliberately holds no analysis. Numbers come from app.kpis,
pictures come from siting_atlas.viz, so both stay testable without a browser.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Absolute imports, unlike every other module in this package. Streamlit
# execs this file as a top-level script rather than importing it, so it has
# no parent package and `from ..common import ...` raises ImportError before
# the first line of the app runs. scripts/run_dashboard.sh puts src/ on
# PYTHONPATH, which is what makes the absolute form resolve.
from siting_atlas.app import kpis
from siting_atlas.common.context import init_run
from siting_atlas.common.logging_setup import configure
from siting_atlas.viz import charts_density as cd
from siting_atlas.viz import charts_economics as ce
from siting_atlas.viz import data as cost_data
from siting_atlas.viz.style import audit_overflow

st.set_page_config(page_title="Siting Atlas — cost to serve",
                   page_icon="📦", layout="wide")

_SETUP_COMMAND = ("PYTHONPATH=src .venv/bin/python -m "
                  "siting_atlas.cost.runner --all-scenarios")


@st.cache_resource
def _bootstrap() -> None:
    """Configure logging exactly once per server process."""
    init_run()
    configure(quiet=True)


@st.cache_data(show_spinner=False)
def _load(year: int, quarter: int, scenario: str) -> pd.DataFrame:
    return cost_data.load(year, quarter, scenario)


@st.cache_data(show_spinner=False)
def _catalogue() -> list[tuple[int, int, str]]:
    return cost_data.available()


def _stop_with_instructions(detail: str) -> None:
    """The graceful-degradation path: say what is missing and how to fix it."""
    st.title("Siting Atlas — cost to serve")
    st.error("The cost model output this dashboard reads has not been "
             "produced yet.")
    st.markdown(f"**What is missing**\n\n```\n{detail}\n```")
    st.markdown("**Generate it, then reload this page:**")
    st.code(_SETUP_COMMAND, language="bash")
    st.caption("The cost model needs data/processed/panel.parquet (L3). If "
               "that is missing too, build the pipeline first — see "
               "docs/engineering/PIPELINE.md.")
    st.stop()


def _sidebar(catalogue: list[tuple[int, int, str]]):
    """The two widgets that decide WHICH parquet is read.

    Metro and ceiling live in main() instead, because both need the
    loaded frame to bound themselves and the frame cannot be loaded
    until these two have been chosen.
    """
    st.sidebar.title("Filters")

    periods = sorted({(y, q) for y, q, _ in catalogue}, reverse=True)
    year, quarter = st.sidebar.selectbox(
        "Period", periods, key="period",
        format_func=lambda p: f"{p[0]}Q{p[1]}")

    # Only scenarios that have actually been run for this period: offering a
    # scenario with no parquet behind it is offering a dead end.
    scenarios = sorted(s for y, q, s in catalogue if (y, q) == (year, quarter))
    default = scenarios.index("baseline") if "baseline" in scenarios else 0
    scenario = st.sidebar.radio("Scenario", scenarios, index=default,
                                key="scenario", help="Parameter sets from "
                                     "siting_atlas.cost.params.SCENARIOS.")
    return year, quarter, scenario


def _kpi_row(summary: dict, threshold: float) -> None:
    """Five tiles. Each one is a number a reader could be asked to defend.

    Nothing on this row uses ``st.metric``'s delta slot, and that is
    deliberate. A delta means "this much MORE than before": Streamlit renders
    it with a direction arrow, green for positive. "58% of ZCTAs" and
    "$14,089,759/day" are a share and a level, neither of which changed from
    anything, so both rendered as increases over an earlier figure that does
    not exist. ``delta_color="off"`` only greys the arrow; it does not remove
    it. A second number that belongs to a tile goes in a caption underneath
    it instead, where it is just as visible and claims nothing.
    """
    cols = st.columns(5)
    cols[0].metric("ZCTAs in view", f"{summary['zctas']:,}")
    cols[1].metric("Median cost", f"${summary['median_cost']:.2f}",
                   help="Dollars per parcel per day.")
    cols[2].metric(f"Servable under ${threshold:.2f}",
                   f"{summary['under']:,}")
    cols[2].caption(f"{summary['under_share']:.0f}% of the ZCTAs in view")
    cols[3].metric("Parcels those carry",
                   f"{summary['parcel_share']:.0f}%",
                   help="Share of modelled daily parcel volume inside the "
                        "ZCTAs that clear the ceiling. Higher than the ZCTA "
                        "share because cheap ZCTAs are dense ones.")
    cols[4].metric("Fleet / cost per day", f"{summary['vans']:,} vans")
    cols[4].caption(f"${summary['daily_cost']:,.0f}/day")


def _show(fig, name: str) -> None:
    """Audit the labels, draw, then close.

    The audit has to run here as well as in the batch build: the app renders
    filtered data the build never saw, and a five-metro selection changes
    every label width on the chart.

    ``clear_figure`` is off and ``plt.close`` is explicit. ``clear_figure``
    calls ``fig.clf()``, which strips the axes off the figure but leaves the
    figure itself registered with pyplot — a figure that is empty and still
    open, which is the worst of both: nothing to render and still holding
    memory. Closing is what actually releases it, and doing it here means
    this module keeps its own promise instead of relying on Streamlit's
    between-run ``plt.close("all")``, which is an internal nobody has
    promised us.
    """
    bad = audit_overflow(fig, name)
    st.pyplot(fig, clear_figure=False)
    plt.close(fig)
    if bad:
        st.caption(f"⚠ {len(bad)} label(s) could not be fitted on this "
                   "chart at the current filter.")


def _charts(view: pd.DataFrame, threshold: float) -> None:
    """The four figures, in tabs so the page does not become a scroll."""
    tabs = st.tabs(["Density law", "By metro", "Where the money goes",
                    "Coverage curve"])
    with tabs[0]:
        _show(cd.cost_vs_density(view), "app:cost_vs_density")
    with tabs[1]:
        _show(cd.cost_by_metro(view), "app:cost_by_metro")
    with tabs[2]:
        _show(ce.cost_decomposition(view), "app:cost_decomposition")
    with tabs[3]:
        _show(ce.cumulative_coverage(view, threshold=threshold),
              "app:cumulative_coverage")


def _table(view: pd.DataFrame, year: int, quarter: int,
           scenario: str) -> None:
    """The ranked table and its download. Sort by clicking a column header."""
    st.subheader("Ranked ZCTAs")
    table = kpis.ranked_table(view)
    st.dataframe(
        table, width="stretch", hide_index=True, height=420,
        column_config={
            "rank": st.column_config.NumberColumn("rank (all metros)"),
            "cost_per_parcel": st.column_config.NumberColumn(
                "$/parcel", format="%.2f"),
            "cost_per_stop": st.column_config.NumberColumn(
                "$/stop", format="%.2f"),
            "stop_density_per_sqmi": st.column_config.NumberColumn(
                "stops/sq mi", format="%.1f"),
            "daily_parcels": st.column_config.NumberColumn(
                "parcels/day", format="%.0f"),
            "daily_stops": st.column_config.NumberColumn(
                "stops/day", format="%.0f"),
            "van_days": st.column_config.NumberColumn(
                "van-days/day", format="%.2f",
                help="Fractional van capacity this ZCTA consumes. A sparse "
                     "ZCTA uses a slice of somebody else's round, not a van "
                     "of its own, so this column adds up and a per-ZCTA "
                     "whole-van count does not."),
            "daily_cost_usd": st.column_config.NumberColumn(
                "$/day", format="%.0f"),
            "linehaul_miles": st.column_config.NumberColumn(
                "depot miles", format="%.1f"),
            "income_imputed": st.column_config.CheckboxColumn(
                "income imputed",
                help="Median household income was missing for this ZCTA and "
                     "the reference income was substituted."),
        })
    st.download_button(
        "Download this selection as CSV",
        data=table.to_csv(index=False).encode("utf-8"),
        file_name=f"cost_to_serve_{year}q{quarter}_{scenario}_filtered.csv",
        mime="text/csv")


def main() -> None:
    _bootstrap()

    catalogue = _catalogue()
    if not catalogue:
        _stop_with_instructions(
            "no cost_to_serve_*.parquet in outputs/tables/")

    year, quarter, scenario = _sidebar(catalogue)
    try:
        frame = _load(year, quarter, scenario)
    except cost_data.CostTableMissingError as exc:
        _stop_with_instructions(str(exc))
        return

    metros = st.sidebar.multiselect(
        "Metros", cost_data.metro_order(frame), default=[], key="metros",
        help="Empty means every pilot metro.")

    lo = float(frame["cost_per_parcel"].min())
    hi = float(frame["cost_per_parcel"].quantile(0.95))
    threshold = st.sidebar.slider(
        "Cost ceiling ($ per parcel)", min_value=round(lo, 2),
        max_value=round(hi, 2), value=round(float(
            frame["cost_per_parcel"].median()), 2), step=0.01, key="ceiling",
        help="Capped at the 95th percentile: the long sparse-ZCTA tail runs "
             "to several dollars and would make every useful position on "
             "this slider indistinguishable.")

    view = kpis.filter_frame(frame, metros)
    st.title("Cost to serve — last-mile delivery")
    st.caption(f"{year}Q{quarter} · scenario **{scenario}** · "
               f"{len(view):,} of {len(frame):,} pilot ZCTAs · "
               "Daganzo continuous approximation over the public panel. "
               "No facility data is used and none is implied.")

    _kpi_row(kpis.summarise(view, threshold), threshold)
    if view.empty:
        st.warning("That filter selects no ZCTAs. Clear a metro to continue.")
        return
    _charts(view, threshold)
    _table(view, year, quarter, scenario)


main()
