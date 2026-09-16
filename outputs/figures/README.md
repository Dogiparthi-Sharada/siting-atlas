# outputs/figures — result charts, 20 PNGs, all of them build output

**These are generated. Nothing here is hand-edited, cropped or retouched.** A
PNG in this directory is a rendering of
[`../tables/*.parquet`](../tables/) and nothing else. If a chart is wrong, the
fix is in `src/siting_atlas/viz/`, not in an image editor.

## Regenerating

```bash
make figures                                              # baseline only, 4 PNGs
python -m siting_atlas.viz.build --all-scenarios          # all five scenarios, 20 PNGs
```

`make figures` deliberately renders only the baseline scenario; the
`--all-scenarios` form is what produced the twenty files here, and it is what
CI and `scripts/build_all.sh` run. The builder **exits non-zero if any label
had to be shrunk past its floor**, so an overflowing label fails the build
instead of reaching a printed PDF. `../metrics/viz_report.json` records what
the last run wrote.

## The filename pattern

```
<chart>_<year>q<quarter>_<scenario>.png
```

Four charts × five scenarios = 20.

| chart | what it shows |
|---|---|
| `cost_vs_density_*` | cost per parcel against stop density, log-x, with the cost floor line that is the point of the chart |
| `cost_by_metro_*` | box plot ordered by median — distributions, not a bar of means |
| `cost_decomposition_*` | cost per **stop** split four ways (distance, drive time, service time, vehicle), stops-weighted |
| `cumulative_coverage_*` | share of ZCTAs and share of parcels covered, on one axis |

The five scenarios are the cost model's parameter sets, defined in
`src/siting_atlas/cost/params.py`:

```
baseline           the sourced central case
dense_routing      150 stops per tour, 2.0 service minutes per stop
congested          16 mph average speed, 1.45 circuity
high_fuel          11 mpg van
pessimistic_tour   a worse Beardwood-Halton-Hammersley constant (0.71)
```

Each scenario moves one or two levers a plausible amount, not an extreme, so
the spread is a credible range rather than a worst case nobody believes.

Every file is `2023q4` because that is the period the cost model is run for;
`--year` and `--quarter` change it.

## Not to be confused with `docs/figures/`

Two trees, two builders, no overlap.

| | this directory | [`../../docs/figures/`](../../docs/figures/) |
|---|---|---|
| what | result charts from the cost tables | the curated figures used in the README, the proposal, the decks and the paper |
| built by | `siting_atlas.viz.build` (a pipeline stage) | `tools/figures/*` (a document builder) |
| contents | 20 PNGs, 4 charts × 5 scenarios | numbered schematics `fig01`–`fig14`, the hero chart, and the paper's result figures |

`docs/figures/README.md` indexes that tree and says which of its figures carry
measured numbers and which are schematics. Read it before putting one in front
of an examiner.
