"""The two things about the dashboard that only exist inside the app.

Every number the dashboard shows is checked in test_viz.py against app.kpis,
without a browser. What cannot be checked there is what the app DOES with
them: how long a matplotlib figure lives, and what a tile claims a number
means. Both fail silently — a leaked figure shows up as memory, and a share
rendered as a delta shows up as a green arrow that a reader believes.

``streamlit.testing.v1.AppTest`` runs the real script headlessly, in-process,
so these exercise dashboard.py itself rather than a re-implementation of it.
The cost table is synthetic and written to a tmp_path: a test that reads
outputs/tables passes or fails depending on whether somebody ran the model
today, which makes it useless as a regression test.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pytest

import siting_atlas
from siting_atlas.common import paths
from siting_atlas.viz import charts_density as cd
from siting_atlas.viz import charts_economics as ce
from tests.unit.test_viz import frame

st = pytest.importorskip("streamlit", reason="dashboard needs the viz extra")
AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

# Absolute: AppTest resolves a relative path against the file that calls it,
# which would be this one, not the repo root.
APP = str(Path(siting_atlas.__file__).parent / "app" / "dashboard.py")

# The order dashboard._charts draws them in. Recorded here because the
# assertion below is about what is open at the START of each call.
CHARTS = [(cd, "cost_vs_density"), (cd, "cost_by_metro"),
          (ce, "cost_decomposition"), (ce, "cumulative_coverage")]


@pytest.fixture
def app(data_root, monkeypatch):
    """A dashboard pointed at one synthetic cost table.

    Streamlit memoises ``_load`` and ``_catalogue`` per process, so the cache
    is cleared here as well: without it the second test in this file reads
    the first test's tmp_path, which no longer exists.
    """
    paths.TABLES.mkdir(parents=True, exist_ok=True)
    frame().to_parquet(
        paths.TABLES / "cost_to_serve_2023q4_baseline.parquet", index=False)
    st.cache_data.clear()
    st.cache_resource.clear()
    yield AppTest.from_file(APP, default_timeout=120)
    plt.close("all")


def test_no_figure_is_left_open_while_the_next_one_is_drawn(app, monkeypatch):
    """Each chart is closed before the next is built, by this module.

    ``st.pyplot(clear_figure=True)`` calls ``fig.clf()``. That empties the
    figure and leaves it registered with pyplot — an open figure with
    nothing in it, which is the worst of both. Streamlit's script runner
    happens to call ``plt.close("all")`` between runs, so this never grew
    without bound, but that is an undocumented internal of somebody else's
    package and the module docstring claimed the fix was here.

    Measured at the moment each chart function is entered, which is the only
    place the difference is visible: before the fix the fourth chart was
    drawn with three dead figures still open.
    """
    seen: dict[str, list[int]] = {}
    for module, name in CHARTS:
        original = getattr(module, name)

        def record(*args, _name=name, _fn=original, **kwargs):
            seen[_name] = plt.get_fignums()
            return _fn(*args, **kwargs)

        monkeypatch.setattr(module, name, record)

    app.run()
    assert not app.exception
    assert len(seen) == len(CHARTS), "not every chart was drawn"
    assert all(open_figs == [] for open_figs in seen.values()), seen


def test_no_tile_dresses_a_level_up_as_a_change(app):
    """``st.metric``'s delta slot means "this much MORE than before".

    "58% of ZCTAs" is a share of the current selection and "$14,089,759/day"
    is a level; neither changed from anything, and both were rendered with a
    direction arrow — green, upward, against a baseline that does not exist.
    ``delta_color="off"`` only greys the arrow, it does not remove it, so the
    second number lives in a caption under the tile instead: just as visible
    and claiming nothing.
    """
    app.run()
    assert not app.exception

    labelled = {m.label: m.delta for m in app.metric}
    assert labelled, "no KPI tiles were rendered at all"
    assert not any(labelled.values()), (
        f"a non-delta is still in the delta slot: {labelled}")

    captions = [c.value for c in app.caption]
    assert any("% of the ZCTAs in view" in c for c in captions), (
        "the share must still be shown, just not as an increase")
