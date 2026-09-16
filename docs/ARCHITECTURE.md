# Architecture

**The L0-L5 layer model as it actually exists on disk, derived by reading
the tree on 2026-09-12 — not from an earlier design document.**

Where this document and an older design doc disagree, this one is describing
what is there and the older one is describing what was intended. Both
disagreements are listed in §8 rather than quietly reconciled.

---

## 1. The idea in one paragraph

The pipeline is a conveyor belt with six numbered stations. Bytes enter at
L0 from the public internet and leave at L5 as a figure or a table. Each
station may only read what the station before it wrote. Nothing at L3 or
above knows the name of a publisher, which is the property that makes
"Volume II: data centres" a data swap rather than a rewrite.

The station codes are not documentation — they are enumerated in code, in
`src/siting_atlas/common/context.py`:

```
L0  acquire     network            -> immutable content-addressed cache
L1  normalise   cache              -> one typed parquet per source
L2  warehouse   parquet            -> DuckDB star schema
L3  feature     warehouse          -> the single ZCTA-quarter panel
L4  model       panel              -> estimates, costs, portfolios
L5  report      estimates          -> figures, tables, metrics
--  setup       bootstrap, config, anything before the pipeline
```

Every log line carries its layer code, so "which station produced this
number" is answerable from the artefacts alone.

**Newcomer's example.** You want to know the diesel price in Boise in
2023Q4. L0 downloaded an EIA API page and hashed it. L1 turned it into
`eia_energy.parquet` with a typed `diesel_usd_gal` column. L2 averaged it to
state-year inside `fact_zcta_year`. L3 re-averaged it to state-quarter and
stamped it onto all 32 quarters of every Idaho ZCTA. L4 read `4.3497` off
the panel row for ZCTA 83650 and multiplied it by miles. Five stations, and
you can open the artefact at each one.

---

## 2. The whole flow, as a diagram

```
 PUBLIC SOURCES                    14 registered, 13 analytical
 ---------------------------------------------------------------------
  OPEN       (7)  gaz_zcta  cbsa_county  zcta_county_xwalk  cbp_zip
                  bps_county   tiger_zcta*   osm*      * large, opt-in
  NEEDS_KEY  (3)  acs5  acs1   [CENSUS_API_KEY]   eia_prices [EIA_API_KEY]
  BLOCKED    (2)  zillow_zori   bls_oes
  MANUAL     (2)  ejscreen      facility_panel   <-- THE TARGET VARIABLE
        |                                  |
        | HTTPS, hashed                    | a human copies the file in
        v                                  v
 +==============================+   +============================+
 | L0  data/raw/     16 MB      |   | data/external/    214 MB   |
 |  acquire.py    bulk GETs     |   |  zillow_zori  zillow_zhvi  |
 |  census_api.py ACS 5yr/1yr   |   |  bls_oes      ejscreen     |
 |  eia_api.py    paged v2 API  |   |  facility_panel  43 rows   |
 |  probe.py      reachability  |   +=============+==============+
 |  external.py   validates --->|                 |
 |  manifest.jsonl  sha256 log  |                 |
 +===============+==============+                 |
                 |                                |
                 v                                v
 +=====================================================================+
 | L1  data/interim/    12 parquets, 61 MB, ~4.1 M rows                |
 |   normalise.py ............ gazetteer cbp building_permits          |
 |                             zcta_county cbsa_county zillow_zori     |
 |   normalise_external.py ... zillow_zhvi bls_wages ejscreen_tract    |
 |   census_api.py ........... acs5_zcta_2023 acs1_metro_2023          |
 |   eia_api.py .............. eia_energy                              |
 |   RULE: ZIP/ZCTA stay zero-padded strings, forever                  |
 +===============================+=====================================+
                                 |
                                 v
 +=====================================================================+
 | L2  data/processed/siting_atlas.duckdb    25 MB, 5 tables           |
 |   warehouse/schema.py                                               |
 |     dim_zcta 33,791 | dim_county 3,211 | dim_date 32                |
 |     dim_scenario 1  | fact_zcta_year 270,328                        |
 +===============================+=====================================+
                                 |
                                 v
 +=====================================================================+
 | L3  data/processed/panel.parquet   1,081,312 rows x 44 cols, 14 MB  |
 |   warehouse/panel.py       the grid: 33,791 ZCTAs x 32 quarters     |
 |   warehouse/optional.py    late-arriving sources spliced in         |
 |   warehouse/facilities.py  target seam; attach() is already wired   |
 |   `enabled` BOOLEAN, 27,914 TRUE cells (2.58%), 1,257 ZCTAs         |
 +=======+==========================+==========================+=======+
         |                          |                          |
         v                          v                          v
 +================+  +==========================+  +====================+
 | L4  cost       |  | L4  optimize             |  | L4  models         |
 | cost/daganzo   |  | optimize/objective       |  | risk_set  splits   |
 | cost/params    |  | optimize/select          |  | hazard    conformal|
 | cost/runner    |  | optimize/runner          |  | base      metrics  |
 |                |  |                          |  | timebasis fixtures |
 | -> tables/     |  | -> tables/               |  | panel_source       |
 |   cost_to_     |  |   portfolio_*.parquet    |  | -> hazard_report   |
 |   serve_*      |  |                          |  |    .json  REAL DATA|
 |   .parquet     |  |                          |  |    RESULT NEGATIVE |
 +================+  +==========================+  +====================+
         |                          |                       |
         |                          |             +====================+
         |                          |             | L4  agent          |
         |                          |             | types gates        |
         |                          |             | warehouse_view     |
         |                          |             | runner             |
         |                          |             | -> outputs/audit/  |
         |                          |             +====================+
         v                          v
 +=====================================================================+
 | L5  report/scope.py  -> outputs/metrics/scope.json                  |
 |     viz/build.py     -> outputs/figures/*.png   (fails on overflow) |
 |       charts_density  charts_economics  data  style                 |
 |     app/dashboard.py + app/kpis.py   (Streamlit; same chart code)   |
 |     tools/figures  tools/proposal  tools/deck  tools/docs           |
 +=====================================================================+

 ALONGSIDE EVERY LAYER
 +=====================================================================+
 | common/  context (run id, layer, stage)   trace (enter/leave/timing)|
 |          logging_setup (6 streams)  db  http  shell  paths  config  |
 |          metros  seeds  log_json      ->  logs/run-<id>/            |
 | agent/   types.py  gates.py   six gates; not wired into any stage   |
 +=====================================================================+
```

---

## 3. Module by module: what it reads, what it writes

Row counts and sizes are from a full ordered run on 2026-09-12.

### L0 — acquire

| Module | Reads | Writes |
|---|---|---|
| `ingest/sources.py` | nothing (a registry) | nothing |
| `ingest/probe.py` | the registry, network | `metrics/source_probe.json` |
| `ingest/acquire.py` | registry, network | `data/raw/<key>/<hash>.<ext>`, `manifest.jsonl`, `metrics/acquire_report.json` |
| `ingest/census_api.py` | Census API | `raw/acs5_2023/`, `interim/acs5_zcta_2023.parquet`, `interim/acs1_metro_2023.parquet` |
| `ingest/eia_api.py` | EIA v2 API | `raw/eia_*/`, `interim/eia_energy.parquet` |
| `ingest/external.py` | `data/external/` | `metrics/external_check.json`; exit 1 if the facility panel is unusable |

`sources.py` is a frozen dataclass per dataset recording provider, grain,
role, licence, endpoint, credential variable, cadence, reporting lag and a
measured `Availability`. Everything else at L0 is driven from it.

The two API modules are tagged `L0` but write an L1 artefact. That is a real
inconsistency in the layer labelling, noted in §8.

### L1 — normalise

| Module | Reads | Writes |
|---|---|---|
| `ingest/normalise.py` | `data/raw/`, ZORI in `data/external/` | six parquets in `data/interim/` |
| `ingest/normalise_external.py` | three big files in `data/external/` | `zillow_zhvi`, `bls_wages`, `ejscreen_tract` parquets |

The split is by file size, not by source type. The external module trims
before it reshapes: ZHVI is cut to 2015-01 onward while still wide, OES
keeps 4 occupation codes out of ~830, EJScreen reads 10 columns of 230.

The twelve L1 parquets:

| Parquet | Rows | Grain |
|---|---|---|
| `acs5_zcta_2023` | 33,772 | ZCTA |
| `acs1_metro_2023` | 530 | CBSA |
| `gazetteer` | 33,791 | ZCTA |
| `zcta_county` | 33,791 | ZCTA |
| `cbsa_county` | 1,915 | county |
| `cbp` | 35,002 | ZIP |
| `building_permits` | 15,812 | county-year |
| `eia_energy` | 4,992 | state-month |
| `zillow_zori` | 456,917 | ZCTA-month |
| `zillow_zhvi` | 3,435,525 | ZCTA-month |
| `bls_wages` | 1,571 | metro-occupation |
| `ejscreen_tract` | 86,082 | tract |

### L2 — warehouse

`warehouse/schema.py` reads `data/interim/` and writes
`data/processed/siting_atlas.duckdb`. Idempotent: `CREATE OR REPLACE`
throughout, so re-running is always safe.

### L3 — feature panel

`warehouse/panel.py` reads the warehouse plus three optional L1 parquets and
writes `data/processed/panel.parquet` and `metrics/panel_report.json`.
`warehouse/optional.py` resolves each late-arriving source to a CTE, a join
and the columns it contributes; a source whose grain cannot be resolved
confidently is skipped with a warning, never guessed at.

**`warehouse/facilities.py` is the seam the whole project used to wait on,
and the wait is over.** It converts a delivered `facilities.csv` into the
`enabled` target column, and `panel.run()` calls `facilities.attach(db)`
unconditionally inside its `target` step. The file landed on 2026-09-13 with
43 delivery stations, and the switchover cost **zero code changes** —
`attach()` simply found a file where it had previously found none. The three
branches below are still live, because the seam has to keep working if the
file is later replaced with a broken one:

```
   facilities.csv absent     -> WARNING, enabled stays NULL, L0-L3 build
   facilities.csv malformed  -> ERROR logged, same fallback, user sent to
                                `ingest.external --check`
   facilities.csv valid      -> enabled populated; models/panel_source.py
                                stops returning the synthetic fixture,
                                because it tests for >= 1 True rather than
                                for the file existing     <-- the live branch
```

What the delivered file does through that seam, measured on the current
panel:

```
   43 delivery stations  ->  1,257 ZCTAs ever enabled
                             27,914 of 1,081,312 cells TRUE (2.58%)
```

2.58% looks like a rare event and is an artefact of the grid: the panel
covers all 33,791 US ZCTAs and the facilities sit in nine metros. Inside the
ten pilot metros the target is near-balanced — 1,230 of 2,413 pilot ZCTAs
(51.0%) are ever enabled — which is why `models/panel_source.py` restricts
to the pilot CBSAs before fitting anything.

Three judgements are encoded in it, and each is meant to be argued with:
only `DS` and `SDC` set the target (an FC is a regional node and puts no van
on a residential street — a test asserts that 7 FCs enable zero ZCTAs);
catchment is a radius, 15 miles for `DS` and 10 for `SDC`, which is the
honest stand-in for a drive-time isochrone until the routing matrix exists;
and pre-2018 facilities are kept as left-censored, because they are not
events but they do mean the ZIP was already served, and dropping them would
tell the model those ZIPs were waiting to be switched on. Two of the 43 rows
are left-censored that way (Chicago 60608 in 2015, Elizabeth NJ 07201 in
2017); with two more in the held-out metros, that leaves **39 usable
events**.

The radius is the judgement with the most leverage, so it has been measured
rather than asserted. Re-running `enabled_flags()` at three radii, over the
2,413 ZCTAs in the ten pilot metros:

```
   radius     pilot ZCTAs ever enabled, 2018Q1-2025Q4
   ------------------------------------------------------
   10 mi        873 / 2,413   36.2%
   15 mi      1,230 / 2,413   51.0%   <- the configured value
   20 mi      1,529 / 2,413   63.4%
```

15 miles is not chosen because it is the true catchment — nobody knows the
true catchment without a drive-time matrix. It is chosen because it is the
conservative reading of the 20-30 minute service window Amazon quotes, and
it happens to leave the target close to a 50/50 split, which is the regime a
binary hazard model is best behaved in. Moving to 10 or 20 miles moves
coverage by roughly 15 points in either direction, so any conclusion that
flips between those two is a conclusion about the radius, not about siting.

One more thing travels with every use of this column. The opening dates
behind it are mostly **"operating by" upper bounds** read off OSHA
inspection records, not opening dates. The looseness has been measured: five
addresses appear in both MWPVL's 2012 census (with real opening months) and
the OSHA extract, the bound held in 5 cases out of 5, and the lag between
opening and first inspection was 4, 13, 57, 69 and 345 months — one site
opened in 1997 and was first inspected in 2026. So `enabled` supports
statements about *which* ZIPs were served far better than statements about
*when* they were switched on. See
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md).

### L4 — decision layer

| Module | Reads | Writes |
|---|---|---|
| `cost/params.py` | nothing | nothing (frozen assumptions) |
| `cost/daganzo.py` | a dataframe | a dataframe |
| `cost/runner.py` | panel + 2 interim parquets | `tables/cost_to_serve_<yr>q<q>_<scenario>.parquet`, `metrics/cost_report.json` |
| `optimize/params.py` | nothing | interaction and capital assumptions |
| `optimize/objective.py` | a cost table | NPV at a margin; break-even margin |
| `optimize/select.py` | an objective | a chosen set, plus an upper bound |
| `optimize/runner.py` | the cost table | `tables/portfolio_<yr>q<q>.parquet`, `metrics/portfolio_report.json` |
| `warehouse/facilities.py` | `facilities.csv` + `dim_zcta` | the `enabled` target column, attached to the panel |
| `models/panel_source.py` | `panel.parquet` | the real panel, or the synthetic fixture, labelled |
| `models/fixtures.py` | nothing | a synthetic panel with known true coefficients |
| `models/risk_set.py` | a panel | a discrete-time risk set |
| `models/timebasis.py` | the risk set | the baseline-hazard time basis |
| `models/splits.py` | the risk set | train/test split by unit, not by row |
| `models/hazard.py` | a risk set | a fitted cloglog discrete-time hazard |
| `models/base.py` | a risk set | the specification contract and one shared `evaluate` |
| `models/metrics.py` | scores and labels | AUC, Brier, ECE, calibration |
| `models/conformal.py` | held-out scores | distribution-free prediction sets |
| `models/runner.py` | the above | `metrics/hazard_report.json`, or `SYNTHETIC_`-prefixed twins |
| `models/choice.py` | `national_facilities.csv` + the panel + CBP detail | choice sets, a fitted conditional logit, and the Brier/top-k evaluation. **ADDED 2026-09-14** — this inventory was derived on 2026-09-12 and predated it |
| `models/choice_conformal.py` | held-out choice scores | split-conformal prediction sets over ZCTAs |
| `models/choice_runner.py` | the above | `metrics/choice_report.json`, including one unfitted single-covariate benchmark per attraction column |
| `models/accessibility.py` | the depot network | the per-decision line-haul saving covariate |
| `optimize/montecarlo.py` | the cost and portfolio parameter ranges | `tables/montecarlo_draws.parquet`, `metrics/montecarlo_report.json`. **ADDED 2026-09-14** |
| `agent/gates.py` | a proposed mutation + warehouse state | six gate results |
| `agent/warehouse_view.py` | the warehouse | the slice a gate may see |
| `agent/runner.py` | a mutation JSON | `outputs/audit/<id>.json` and `mutations.jsonl` |

Cost and optimisation run **today** because neither needs a target variable.
They answer "what would it cost to serve this ZIP" and "which set should be
funded", which are engineering-economics questions.

**How the optimiser reports value, and why.** `optimize/objective.py`
maximises NPV at an assumed contribution margin:

```
   NPV(S) = m * A(S) - B(S) - K(S)     A annual parcels served
                                       B annual cost to serve
                                       K capital, $4m per activation
                                       m margin, UNOBSERVABLE
```

It did not always. The first objective *minimised the portfolio's break-even
margin*, which is degenerate: measured over the pilot it takes its minimum at
**n = 1** ($1.1910, against $1.5278 at n=100 and $1.5516 at n=500). It
literally said "build one facility", and produced sensible-looking answers
only because greedy was forced to spend the whole budget. It had no stopping
rule and structurally could not express "this activation destroys value".
Maximising NPV does both — stop when marginal NPV <= 0.

Because `m` cannot be observed and NPV is linear in it, the deliverable is a
**frontier**, not a portfolio. `--margin` defaults to the break-even of a
full-budget portfolio, which is self-referential rather than arbitrary;
`--frontier` solves across a range. The headline this produces is that at a
$2bn budget the optimiser deploys **less than the full budget on fewer than
the 500 fundable activations**, because the rest lose money at the neutral
margin.

The counts are deliberately not written out here. Read `detail.n`,
`detail.capital`, `naive_breakeven` and `optimality_gap` from
`experiments/portfolio-optimiser/artefacts/portfolio_report.json`, which stamps a `run_id`. This
paragraph used to assert "$1.268bn on 317 of 500" and a $1.5516 default
margin; the artefact was regenerated twice since and reports 282 / $1.128bn
under run `20260914-002431-7419`. **Why it moved IS now established
(2026-09-14):** depot placement changed from k-means to p-median with nothing
in `optimize/` touched, and a 500-draw Monte Carlo shows the drift is wider
than parameter uncertainty. See [`DECISION_LOG.md`](DECISION_LOG.md) §4.2.
The counts still are not typed here, for the same reason as before.

No `(1 - 1/e)` greedy guarantee is claimed: the objective has positive
interactions (two adjacent ZCTAs share one trip out of the depot) and
negative ones (overlapping catchments cannibalise), so it is neither
submodular nor supermodular. `optimize/select.py` reports an achieved value
against a computed upper bound that ignores every negative interaction, and
lets the gap speak — `optimality_gap` in `portfolio_report.json`,
instance-specific, not worst-case. (This sentence used to name 13.03%; the
current artefact does not agree, see above.)

`optimize/params.py` holds the interaction assumptions, and two arithmetic
corrections live there and in the objective. Annual flows are computed at
`delivery_days_per_year = 6 x 52 = 312`, derived from `cost/params.py` rather
than typed, because 365 invents 53 delivery days that never happen — and
capital does not scale with the flow, so the error understated the break-even
margin by ~3.5%. And the line-haul cost pool applies a mileage share to the
*mileage-driven* cost, not to total cost: door time and the van lease are
paid whatever route the van drove, so the old form made the shareable pool
**2.9x** too large and over-credited clustering. Both bugs flattered the same
conclusion.

`models/runner.py` also runs today, and how it does so is the most important
design decision in this layer. It has **one code path and two possible
inputs**: `panel_source.load_panel()` returns the real panel if `enabled`
contains at least one `True`, and otherwise returns a labelled synthetic
fixture whose true coefficients are known. When the fixture is used, a
warning banner goes to the console and the log, unit ids are `SYN-00001`
(which can never collide with a ZIP code in a join or a plot), and every
artefact is written under a `SYNTHETIC_` filename with `"synthetic": true`
inside it.

That is a claim about the **code**, not about the world. It demonstrates that
the link function, risk-set construction, standardisation, spline basis and
conformal calibration compose correctly — on a verified run it recovered
`x_demand` 0.728 against a true 0.800, `x_cost` -0.346 against -0.450,
`x_competition` 0.284 against 0.300. It says nothing whatever about any real
ZCTA. There is no separate demo mode to fall out of date; on the day
`facilities.csv` lands, the only thing that changes is which branch
`load_panel` takes.

`agent/runner.py` runs too, and degrades honestly: with `enabled` empty,
gate 6 (estimate stability) *cannot* evaluate, so it refuses to report a pass
and the mutation is escalated to a human. That is conservative by design, and
the audit record says exactly why.

### L5 — report

`report/scope.py` measures the study's scope from the same artefacts the
model uses and writes `outputs/metrics/scope.json`. Every headline figure in
the proposal, the deck and this documentation set is read from that file
rather than typed — because the proposal once claimed "approximately 5,200
ZCTAs" and the measured number is 2,413.

`viz/build.py` renders the result figures for one scenario into
`outputs/figures/` and **exits non-zero if any label had to be shrunk past
its floor** — an overflowing label in a PDF at 60% zoom is a defect nobody
notices, so it fails the build instead of the reader. `viz/data.py` locates
and validates the cost parquet; `viz/style.py` holds the palette and the
text-fitting machinery.

`app/dashboard.py` is a Streamlit front end over the *same* chart functions,
launched by `scripts/run_dashboard.sh`. It adds filtering and computes
nothing the batch build does not, so the app and the printed figures cannot
disagree. Numbers come from `app/kpis.py`, pictures from `viz/`, so both stay
testable without a browser.

---

## 4. The star schema

```
                    +-------------------------+
                    |        dim_date         |
                    |-------------------------|
                    | date_id  PK  '2023Q4'   |
                    | year      2018..2025    |
                    | quarter   1..4          |
                    |            32 rows      |
                    +-----------+-------------+
                                | year
                                |
 +----------------------+       v        +----------------------+
 |      dim_zcta        |  +----------+  |     dim_county       |
 |----------------------|  |          |  |----------------------|
 | zcta         PK      |--+  fact_   +--| county_geoid   PK    |
 | land_area_sqmi       |  |  zcta_   |  | county_name          |
 | water_area_sqmi      |  |  year    |  |                      |
 | latitude, longitude  |  |          |  |          3,211 rows  |
 | county_geoid    FK ------> 270,328 |  +----------------------+
 | state                |  |  rows    |
 | metro  (nullable)    |  +----+-----+  +----------------------+
 |          33,791 rows |       |        |    dim_scenario      |
 +----------------------+       |        |----------------------|
                                |        | scenario_id    PK    |
   fact_zcta_year measures:     |        | w_version            |
     population, income,        |        | mutation_id          |
     home value, age,           |        | seed                 |
     households, tenure,        |        |              1 row   |
     education, labour force,   |        +----------+-----------+
     vehicles, establishments,  |                   :
     employment, payroll,       |                   : declared now so a
     permit_units_total,        |                   : published number can
     rent_index,                |                   : later be replayed;
     electricity_cents_kwh,     |                   : carries no fact yet
     diesel_usd_gal             |
                                v
                    33,791 ZCTAs x 8 years = 270,328 rows
```

Three decisions are baked into that SQL and are worth knowing before you
read a number off it:

1. **The Gazetteer decides which ZCTAs exist.** CBP knows 35,002 ZIP codes,
   which is more than there are ZCTAs, because it includes point ZIPs and
   retired vintages. Joining outward from the Gazetteer keeps them out.
2. **State comes from the county FIPS prefix, not from CBP.** CBP supplies a
   state abbreviation only for the 30,928 ZCTAs that have a business; the
   other 2,863 are rural and would otherwise lose their EIA energy price.
3. **The fact grid is dense.** A ZCTA with no Zillow index and no permits
   still gets a row with NULLs. A model that only ever sees rows where rent
   exists learns "covered by Zillow" as a feature, and Zillow coverage is
   urban.

### 4.1 From the star to the panel

L3 re-grains the fact from **ZCTA x year** to **ZCTA x quarter** and adds the
rate-of-change and availability columns:

```
   dim_zcta  33,791          x    dim_date  32 quarters
        \                              /
         +------------ CROSS JOIN ----+
                      |
                      v
            1,081,312 panel rows
                      |
      +---------------+----------------+------------------+
      |               |                |                  |
   LEVELS        RATES OF CHANGE   AVAILABILITY         TARGET
   ACS 2023      rent_index_       rent_observed     enabled
   CBP 2022      yoy_pct           (100% by          BOOLEAN
   repeated      permits_yoy_pct   construction)     2.58% TRUE
   down quarters                                     (51.0% of pilot
                                                      ZCTAs ever on)
```

---

## 5. The observability layer

Every entry point calls `init_run()` then `configure()`. That creates one
directory per run, `logs/run-<run_id>/`, containing up to six streams
segregated by concern, so debugging a bad query does not mean scrolling past
HTTP noise.

| File | One record per | Written by |
|---|---|---|
| `console.log` | log line, plain text | every logger |
| `events.jsonl` | log record, as JSON | every logger |
| `sql.jsonl` | SQL statement | `common/db.py` |
| `commands.jsonl` | shell command | `common/shell.py` |
| `http.jsonl` | HTTP request | `common/http.py` |
| `errors.log` | WARNING and above | every logger |

A run directory only contains the streams it actually used: a pure-SQL stage
writes no `http.jsonl`, a stage that shells out to nothing writes no
`commands.jsonl`. The console shows INFO and above; the files always capture
DEBUG, so a failure can be diagnosed from the artefacts without re-running.

### 5.1 How a line gets its context

```
  context.py                       logging_setup.py
  ----------                       ----------------
  run_id    20260912-140233-a91c
  layer     L3                 ->  ContextFilter stamps every record
  stage     build_panel            with run_id / layer / stage
       ^
       |  set by
       |
  trace.py
     traced_layer("L3", "panel -> ...")   logs ENTER, LEAVE, elapsed
     step("build_panel")                  times it, records failure
     artefact(path, rows=...)             records what was written
     metric("panel_rows", 1081312)        records a measured quantity
```

`contextvars`, not globals, so the stamping stays correct if a stage is ever
run concurrently.

### 5.2 Correlating several commands into one run

Each `python -m ...` invocation is a separate run by default. Export a run
id first and every stage appends to the same directory:

```bash
export SITING_ATLAS_RUN_ID=$(date -u +%Y%m%d-%H%M%S)-full
```

`init_run()` honours that variable. This is how a nine-command reproduction
becomes one auditable artefact instead of nine unrelated ones.

---

## 6. Cross-cutting modules

| Module | Responsibility |
|---|---|
| `common/paths.py` | the only place a path is composed; `SITING_ATLAS_ROOT` relocates the whole tree |
| `common/config.py` | pinned vintages, panel years, pilot metros, ACS variables, `.env` loading |
| `common/metros.py` | the ten-metro registry and its CBSA membership |
| `common/db.py` | DuckDB connection that logs every statement to `sql.jsonl` |
| `common/http.py` | content-addressed fetch, manifest append, credential redaction |
| `common/shell.py` | subprocess wrapper that logs to `commands.jsonl` |
| `common/seeds.py` | `reproducibility/seeds.toml`; unit-tested, and consumed by `models/fixtures.py` and `cost/depots.py` |
| `common/log_json.py` | writes a metrics JSON with run id and timestamp |

---

## 7. The agent layer

`agent/gates.py` implements six gates a proposed warehouse mutation must
clear. Gates 1-4 protect **data** integrity and have extensive prior art.
Gates 5-6 protect **inferential** integrity, which is the contribution.

```
  proposed mutation
        |
        v
  1 SchemaGate ............ types, enums, required fields
  2 GeocodingGate ......... coordinates resolve, inside US bounds
  3 ConfidenceGate ........ extraction confidence above threshold
  4 AuditLogGate .......... the write is recorded before it happens
        |   all four can PASS on a write that is factually correct
        v
  5 DonorPoolIntegrityGate  does this write contaminate the donor pool?
  6 EstimateStabilityGate   does theta move more than the tolerance?
        |
        v
  Decision: ALLOW / REVIEW / BLOCK
```

`agent/runner.py` executes that pipeline against real warehouse state
(`agent/warehouse_view.py`) and writes an audit record for **every**
invocation, including rejections — "it never let a bad write through" is only
a claim if the attempts were logged. Records land in
`outputs/audit/<mutation_id>.json` and are appended to
`outputs/audit/mutations.jsonl`.

Two honest caveats. With `enabled` empty, the donor pool cannot be
identified, so every ZCTA is treated as a nominal donor and gate 5 escalates
any mutation; and gate 6 cannot re-estimate anything, so it reports
*unavailable* rather than *pass*. The demo mutation therefore ends in
ESCALATED TO HUMAN, which is the correct behaviour and not a defect. **No
ingest stage imports this module** — it is a parallel write path, not part of
L0-L3.

---

## 8. Where this architecture diverges from the design documents

Stated plainly, because the point of this repository is that its claims
survive checking.

| Design says | Built as |
|---|---|
| L2 is dbt Core over DuckDB | SQL inside `warehouse/schema.py`; `dbt/` is now an empty directory |
| L3 is an 811k-row ZCTA-week panel over 10 metros | 1,081,312-row ZCTA-quarter panel, national |
| "eleven public sources" | 14 registered, 13 analytical |
| `reproducibility/seeds.toml` wired into every stochastic step | done: `models/fixtures.py` draws through `seed("models", "hazard")` and `cost/depots.py` pins k-means at `RANDOM_STATE = 20260912`. Nothing hardcodes a seed inline |
| Data contracts fail the build on drift | reported, not enforced; only `ingest.external --check` exits non-zero |
| ACS is purely a level source | true, and also top-coded: home value at $2,000,001 and income at $250,001 now carry `_topcoded` flags |
| EIA arrives by hand into `data/external/` | acquired through the v2 API, so `external --check` reports `eia_prices missing`, which is correct and misleading |

Two engineering notes that belong here rather than in a design doc:

- **`ingest/census_api.py` and `ingest/eia_api.py` are tagged L0 and write
  L1 artefacts.** A `traced_layer("L0", ...)` block writing a typed parquet
  reads oddly in the logs. It is a labelling bug, not a data bug.
- **`logs/` can contain credentials.** `common/http.py` redacts known key
  parameters, but a new keyed source added without redaction would leak into
  `http.jsonl`. Treat the directory as sensitive.

---

## 9. The limitation that matters

For most of this project's life the limitation was that there was no outcome
at all: `data/external/facility_panel/facilities.csv` was a header row and
nothing else, and everything above L3 that needed a target was stalled
behind it. That is resolved. The file landed on 2026-09-13 with **43 Amazon
delivery stations**, `ingest.external --check` passes, and `enabled` is
populated.

The limitation has changed shape twice, and the second change is the one
this section was slow to record.

**First** it became that the panel is small, unevenly distributed and dated
by upper bounds — the bullets below. **Then the model was fitted anyway, and
the limitation stopped being a warning and became a measurement: it does not
work.** Brier 0.019522 against the null's 0.019614 over the same 8,044 rows;
ECE 0.00863 against the null's 0.00005 — *worse calibrated than predicting
one constant everywhere*; AUC 0.6894 against 0.5000; and out of time the
null wins outright, Brier 0.020635 against 0.020213 over 11,871 rows. One of
three covariates is distinguishable from zero.

Report the **raw Brier pair** rather than the skill number. A skill score is
`1 - S_model/S_null`, and Gneiting & Raftery (2007) §2.3 p.362 establishes
that skill scores are generally improper even when the underlying rule is
proper, which the Brier score is (§3.1 p.363). This passage used to lead with
"Brier skill +0.0047 ... negative Brier skill on both the temporal (-0.0209)
and geographic (-0.0618) hold-outs". The geographic figure in particular must
not be quoted as a transfer result: `experiments/hazard-model/artefacts/hazard_report.json:819`
records that Phoenix and Boise hold **two dated delivery stations between
them**, making it "a smoke test for gross failure and not a test of
geographic transfer". See
[`research/NOTES_gneiting_raftery_2007.md`](research/NOTES_gneiting_raftery_2007.md).

**And the diagnosis is the unit of analysis, not the sample size.** This is
the correction that matters most, because this section previously implied the
opposite — that the fit failed because 39 events are too few, and that
"everything below explains why it was the expected outcome". The bullets below
are all true and none of them is the cause. The cause is that a ZCTA-quarter
is not a decision: one station signs one lease and every ZCTA inside a
fifteen-mile catchment switches on with it, a median of 58 at a time, so the
812 "events" in the risk set are 28 to 38 real decisions plus geometry
(`hazard_report.json`, `power`). The assumption that breaks is **Train (2009)
§3.7.1, printed p. 61** — the likelihood assumes each decision maker's choice
is independent of every other's, and 58 ZCTAs switched on together are one
draw entered 58 times. *(CITATION CORRECTED 2026-09-14: this sentence cited
§2.2, mutual exclusivity. Train calls that criterion "not restrictive" and
shows how to satisfy it, so it is the authority for building the SUCCESSOR
choice set, not the charge against the old model.)* [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14 is the
canonical statement and rejects the sample-size reading explicitly; the
decision to change specification is
[`adr/0004-model-change-conditional-choice.md`](adr/0004-model-change-conditional-choice.md).

Sample size is not thereby irrelevant, and the honest line is narrow: the
reframe makes the specification **valid**, not **powerful**. The successor
choice model has roughly 43 decisions on the pilot frame — 38 the diagnostic
counts as usable — against 5 parameters, i.e. **7.6 per parameter against a
conventional floor of 10**. Honestly imprecise beats dishonestly confident.

That is the limitation that matters. Everything below describes the panel it
was fitted on. See [`STATUS.md`](STATUS.md).

- `panel.parquet` carries `enabled` as a real boolean: 27,914 TRUE cells of
  1,081,312, across 1,257 ZCTAs. Keeping the column typed and present while
  it was empty is what made the switchover free — adding it later would have
  meant rewriting 1.08 million rows.
- **39 usable events.** 43 rows, less 2 in the held-out metros and 2 that
  opened before the 2018Q1 window and are carried as left-censored. That is
  enough to fit a cloglog hazard with a handful of parameters and to run the
  pipeline end to end on real data. It is not enough to make a *precise*
  claim about how Amazon chooses sites — and, per the correction above, it is
  also not the reason the cloglog failed. Under the reframe these 43 rows
  become 43 decisions rather than 812 pseudo-events, which is the point:
  fewer nominal observations, all of them real.
- **The coverage is lumpy and must not be averaged away.** Seattle
  contributes 11 of the 43 — a fact about Washington's unusually active
  state-plan OSHA programme, not about Amazon's footprint. Nashville is a
  *fitting* metro with **zero** events, because all five of its OSHA
  addresses are fulfilment centres. A model that reports a Seattle effect is
  probably reporting an inspection effect.
- **The dates are "operating by" upper bounds** from OSHA inspection
  records. Measured against the five addresses that also appear in MWPVL's
  2012 census, the bound held 5 of 5 but the lag between opening and first
  inspection was 4, 13, 57, 69 and 345 months. Statements about *where* are
  far better supported than statements about *when*.
- **No `SYNTHETIC_*` artefact remains on disk.** This bullet used to say
  "check the prefix before quoting any number", and that check now catches
  nothing: `hazard_report.json` carries `"synthetic": false`. The AUC of
  0.729 once quoted here was the fixture's, and it meant only that the code
  composes. The real-data AUC is 0.6894 and it comes with the calibration
  failure above.
- The six gates run against a real donor pool now. Gate 5 escalates often
  rather than always — 39 events make a thin pool, and in the metros with
  one or two rows it still cannot separate donors from treated units.
- Cost and optimisation run and produce real numbers, and those numbers
  describe *operating economics*, not *operator behaviour*. Do not read a
  cheap ZCTA as a prediction that anyone will build there.

See [`STATUS.md`](STATUS.md) for the current state of each item,
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) for
how the panel was built and where it is weak, and
[`data/COST_MODEL.md`](data/COST_MODEL.md) for what the L4 cost numbers do
and do not mean.
