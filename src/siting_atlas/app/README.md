# app — the cost-to-serve dashboard

L5. A Streamlit app over the cost model's output. It adds filtering and
nothing else: every chart comes from `siting_atlas.viz` and every number
comes from `app.kpis`, so the app cannot disagree with the printed figures
and neither can be checked only by opening a browser.

**Start here:** `kpis.py`. It is 76 lines of plain functions of a DataFrame
and it carries the two counting rules the tiles depend on.

---

## Files

```
  file           purpose                                         state
  -------------  ----------------------------------------------  ------
  __init__.py    placeholder docstring only ("see                 stale
                 docs/ROADMAP.md for build order"). It tells a
                 reader nothing; this README is the overview
  kpis.py        the summary numbers above the charts. Plain      works
                 functions of a DataFrame, separate from the
                 app because arithmetic that only exists
                 inside a Streamlit callback cannot be tested
  dashboard.py   the app itself. Holds no analysis                works
```

## Running it

```
  bash scripts/run_dashboard.sh                 # localhost:8501
  PORT=8600 bash scripts/run_dashboard.sh       # somewhere else
```

or `make app`. The launcher exists because Streamlit execs the app file as
a top-level script with no parent package, so `src/` has to be on
`PYTHONPATH` or the absolute `siting_atlas.*` imports fail. Needs
`make cost` to have run first; the launcher checks for
`outputs/tables/cost_to_serve_*.parquet` and prints the command to generate
them rather than failing in a browser.

The app writes nothing. It is a reader of `outputs/tables/`.

## Two counting rules worth knowing

**"Servable under $X"** counts ZCTAs at or below the ceiling, and reports
the share of daily PARCELS those ZCTAs carry alongside the share of ZCTAs.
Reporting only the ZCTA count understates the case badly: the cheap ZCTAs
are the dense ones, so half the areas carry roughly two thirds of the
volume.

**`van_days` is aggregated and rounded ONCE.** `vans_required` is per-ZCTA
and already rounded up, and `cost.daganzo` documents it as the "if this ZCTA
had a dedicated van" reading precisely because it may not be summed. Summing
it made every sparse ZCTA contribute a whole van for two stops a day and
overstated the pilot fleet by roughly 1,200 vans — in a headline tile, with
no sign that anything was wrong.

## Worth knowing

`dashboard.py` closes each matplotlib figure itself rather than relying on
`st.pyplot(clear_figure=True)`, which calls `fig.clf()` and leaves the
figure registered with pyplot. Streamlit happens to call `plt.close("all")`
between script runs, but that is an undocumented internal of somebody else's
package, and within a single run it still meant four dead figures held open.

`tests/unit/test_dashboard.py` runs the real script headlessly through
`streamlit.testing.v1.AppTest`, so it exercises `dashboard.py` rather than a
re-implementation of it.
