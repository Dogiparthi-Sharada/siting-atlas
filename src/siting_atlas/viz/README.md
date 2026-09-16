# viz — the result figures

L5. Four charts rendered from the cost model's output parquet, plus the
style tokens and text-fitting they share. This is the batch twin of the
dashboard: the same chart functions, so a printed figure and the app cannot
disagree.

**Start here:** `__init__.py` — one import surface, six lines, and it shows
the two-line usage. Then `data.py`, because everything else assumes the
parquet has already been located and validated.

---

## Files

```
  file                  purpose                                  state
  --------------------  ---------------------------------------  ------
  __init__.py           the single import surface, shared by     works
                        viz.build and app.dashboard so the two
                        cannot drift into drawing different
                        pictures from the same parquet
  data.py               locate and load the cost table. Names    works
                        two failures: a missing parquet must
                        produce an instruction, not a
                        FileNotFoundError three frames deep
                        (CostTableMissingError), and a parquet
                        that predates a schema change must be
                        rejected, not silently plotted with a
                        column missing
  style.py              the palette and the text-fitting         works
                        machinery. Only THREE categorical
                        colour slots are exposed for all-pairs
                        forms, and the docstring explains that
                        this is a finding and not a preference:
                        no eight-hue set clears the
                        colour-vision floor when every series
                        can sit beside every other. Metro
                        identity is carried by position and
                        direct labels instead
  charts_density.py     the two figures about WHERE cost sits.   works
                        cost_vs_density (log-x, with the
                        horizontal floor line that is the point
                        of the chart) and cost_by_metro (a box
                        plot ordered by median, not a bar of
                        means). Neither raises on an empty or
                        all-NaN selection, because a dashboard
                        filter that selects nothing must not
                        crash the app
  charts_economics.py   the two figures about WHAT the money     works
                        buys. cost_decomposition splits cost
                        per STOP, not per parcel, or the shares
                        sum to about 140%; it aggregates with a
                        stops-weighted mean because medians are
                        not additive and a stack built from
                        medians lies about its own sum.
                        cumulative_coverage plots share of
                        ZCTAs and share of parcels on one axis
                        - the gap between the curves is the
                        finding
  build.py              the batch renderer. Exits NON-ZERO if    works
                        any label had to be shrunk past its
                        floor, so an overflowing label fails
                        the build rather than reaching a PDF
```

## Producing the figures

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.viz.build
  PYTHONPATH=src .venv/bin/python -m siting_atlas.viz.build --all-scenarios
```

or `make figures`. Needs `make cost` to have run first.

Writes PNGs to `outputs/figures/` and a report to
`outputs/metrics/viz_report.json`. Both are GENERATED — hand edits are lost
on the next run, and the overflow audit will not have seen your edit.

## Worth knowing

`tests/unit/test_viz_regressions.py` pins four defects an audit found in
this layer. Three of the four produced a chart that looked entirely ordinary
and was about something other than what it said, which is why the reasons
are written into the test docstrings rather than left implicit.

Nothing here is stale as far as this reading found.
