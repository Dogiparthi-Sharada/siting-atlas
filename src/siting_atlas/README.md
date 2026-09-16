# src/siting_atlas — the package

Ten sub-packages, one per pipeline layer. Nothing above L3 knows where the
bytes came from, which is the property that makes a second volume a data
swap rather than a rewrite.

**Start here:** [`docs/STATUS.md`](../../docs/STATUS.md) for the state of
every component, then `common/paths.py` for the layer names every other module
uses, then the sub-package you actually need from the table below. Before
quoting any number the code produces, read
[`docs/NUMBERS.md`](../../docs/NUMBERS.md).

---

## The packages

```
  package       n  layer     what it is                        state
  ----------  ---  --------  --------------------------------  --------
  common       16  all       paths, run context, logging,      works
                             DuckDB, HTTP, seeds, address
                             standardisation, record linkage
  ingest       17  L0/L1     source registry, reachability     works
                             probe, download cache, one
                             typed parquet per source
  warehouse     7  L2/L3     DuckDB star schema, the ZCTA-     works
                             quarter panel, the facility
                             target variable
  cost          5  L4        Daganzo continuous-approximation  works
                             cost to serve, plus p-median
                             depot placement
  models          L4        four siting specifications.       FAILED
                             All built, all fitted, all
                             scored, none earns its
                             parameters. Read its README
                             before quoting any of them
  analysis      8  L4        questions the target variable     negative
                             cannot answer -- the white-space
                             coverage backtest
  optimize      5  L4        portfolio selection under a       works
                             capital budget
  agent        10  L4        the six-gate mutation path and    works
                             its audit record
  report        2  L5        measures study scope into
                             outputs/metrics/scope.json        works
  viz           6  L5        the four result figures           works
  app           3  L5        the Streamlit cost dashboard      works
```

`__init__.py` at this level holds only the package docstring and
`__version__`.

## Which of these you can trust

The engineering works and the science does not, and that split is clean. The
cost model (2,333 ZIP codes, median $1.0830 per parcel, 334 solved depots),
the portfolio optimiser, the six agent gates and the whole data pipeline all
run on real data.

`models/` and `analysis/` are the exception. Four siting specifications have
been built, fitted and scored — a discrete-time hazard, a conditional
ZCTA-choice model, a metro-entry model and a coverage back-test — and none
earns its parameters. The metro model's failure is **pre-registered**
([`docs/PREREG_METRO_MODEL.md`](../../docs/PREREG_METRO_MODEL.md)). Read
`models/README.md` and `analysis/README.md` before quoting anything from
either package, and [`docs/STATUS.md`](../../docs/STATUS.md) §2 before quoting
anything from them in a document.

## Indexes

Every sub-package now has one: `agent/`, `analysis/`, `app/`, `common/`,
`cost/`, `ingest/`, `models/`, `optimize/`, `report/`, `viz/`, `warehouse/`.

Note that the `__init__.py` docstring for `cost`, `optimize` and `warehouse`
is still the placeholder "see docs/ROADMAP.md for build order" and tells you
nothing. Read the README, not the docstring.

## Running a stage

Every stage is a module with a `main()`, and the Makefile names them all:

```
  make probe        L0  check every source is still reachable
  make acquire      L0  fetch into the content-addressed cache (needs keys)
  make normalise    L1  one typed parquet per keyless source
  make warehouse    L2  parquet -> the DuckDB star schema
  make panel        L3  the ZCTA-quarter panel every model reads
  make cost         L4  cost to serve, per pilot ZCTA
  make model        L4  fit the hazard and score it
  make agent        L4  the gated mutation demo
  make optimize     L4  portfolio under a budget (minutes, not seconds)
  make scope        L5  study scope into outputs/metrics/scope.json
  make figures      L5  result figures into outputs/figures
  make app          L5  serve the dashboard
```

CI asserts that every module the Makefile names is importable and has a
`main()`, because the Makefile used to name three that did not exist.

## House rules visible in the source

Hand-wrapped to 79 columns so comments sit beside the code they explain;
black is deliberately not configured. Nothing hardcodes a random seed —
they all come from `reproducibility/seeds.toml`. No module opens its own
DuckDB connection or issues its own HTTP request; both go through `common`
so every statement and every fetch lands in `logs/run-*/`.
