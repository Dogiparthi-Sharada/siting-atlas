# Reproduce This From Scratch

**Clone to cost table, with every command run and verified on 2026-09-12 in
the environment described in §1.**

The rule for this document: if a command is printed here, it was executed
here and the output below it is the output it produced. Where a command
*fails* in this environment, it is printed anyway, with the failure and the
workaround, because an aspirational command is worse than no command.

Two things you should know before you start:

1. **Nine of the fourteen sources download themselves. Five do not.** Four
   are refused by this network or have no stable endpoint, and you place
   them by hand. The fifth — the facility panel — is the target variable,
   and no publisher issues it: it was compiled here from the public OSHA
   inspection extract. It arrived on 2026-09-13 and ships with the repo at
   43 rows, so you inherit it rather than rebuild it. §4.3 says how to
   rebuild it anyway.
2. **You can reproduce L0 through L4-cost completely**, and you can fit the
   model too. Temper what that means: **it fails** — the fitted hazard is
   worse calibrated than a constant, and out of time the constant scores
   better (Brier 0.020635 against 0.020213). If you run `make model` and the
   numbers look disappointing, you have reproduced the result correctly.
   [`STATUS.md`](STATUS.md) states it plainly, and
   [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14 explains why — the cause is the unit of analysis,
   not the 39 events.

---

## 1. What "the same answer" was measured on

| | |
|---|---|
| OS | Linux 5.14, x86-64 |
| Python | 3.13.14 |
| duckdb | 1.5.5 |
| pandas | 3.0.5 |
| pyarrow | 25.0.1 |
| numpy | 2.5.3 |
| Egress | corporate HTTPS proxy; PyPI reachable, github.com release assets are not |

`requires-python` in `pyproject.toml` is `>=3.11`, so 3.11 and 3.12 should
also work. They were not tested here.

---

## 2. Clone and create the environment

```bash
git clone <repo-url> siting-atlas
cd siting-atlas
python3 -m venv .venv
```

### 2.1 Install

```bash
.venv/bin/pip install -e ".[dev,viz,docs]"
```

Verified by resolution (`pip install --dry-run`) on 2026-09-12: resolves
cleanly behind this proxy. `dependencies` in `pyproject.toml` lists only what
`src/siting_atlas` actually imports; geometry (geopandas, shapely, h3) sits
in a separate `geo` extra because nothing imports it yet and GDAL/PROJ is the
single most likely thing to fail on a clean runner.

**A failure worth recording, because it was real earlier the same day.** The
`dev` extra used to include `dbt-duckdb`. Its build backend downloads a wheel
from a GitHub *release* during metadata generation, and this proxy blocks
those:

```
RuntimeError: failed to download https://github.com/dbt-labs/dbt-core/
  releases/download/v2.0.0-rc.2/dbt_core_experimental_parser-...whl:
  <urlopen error Tunnel connection failed: 503 Service Unavailable>
error: metadata-generation-failed
```

`dbt-duckdb` has since been dropped from `dev`, which is correct: nothing in
the pipeline uses dbt. `dbt/` is an empty directory and L2 is plain SQL
inside `warehouse/schema.py`. If you hit the error above, you are on an older
`pyproject.toml`; install `.[viz,docs]` and the test tools separately.

### 2.2 The minimum that actually runs the pipeline

The environment these numbers were produced in has geopandas, shapely, h3
and shap **absent** and every stage below still runs, because no stage
imports them. If you want the smallest working install:

```bash
.venv/bin/pip install --no-deps -e .
.venv/bin/pip install duckdb pandas pyarrow numpy scipy statsmodels \
    scikit-learn lightgbm matplotlib requests openpyxl
```

`openpyxl` is not in `pyproject.toml` but **is required**: the OMB
delineation is an `.xlsx` and the BLS OES tables are an `.xlsx` inside a zip,
and pandas needs openpyxl to read either. Without it L1 fails.

### 2.4 Check the package imports

```bash
.venv/bin/python -c "import siting_atlas; print(siting_atlas.__file__)"
```

An editable install puts a `.pth` file in `site-packages`, so this works from
any directory. If you skipped the editable install, prefix every command
below with `PYTHONPATH=src` — that also works and is harmless either way.

---

## 3. Credentials

Two keys. Both are free, both issue instantly, neither requires a payment
method. Put them in `.env` at the repo root — it is gitignored, and
`common/config.load_dotenv()` reads it on first use.

```bash
cat > .env <<'EOF'
CENSUS_API_KEY=your_key_here
EIA_API_KEY=your_key_here
EOF
```

| Variable | Get it from | Used by |
|---|---|---|
| `CENSUS_API_KEY` | api.census.gov/data/key_signup.html | ACS 5-year (ZCTA), ACS 1-year (metro) |
| `EIA_API_KEY` | eia.gov/opendata/register.php | electricity and diesel prices |

**One trap worth naming.** The Census API answers a request with no key by
returning an HTML "Missing Key" page with HTTP **200**, not an error. The
fetch layer therefore asserts on `Content-Type`. If you see a JSON decode
error, your key is missing or wrong, not the API.

---

## 4. Which sources arrive by themselves, and which you carry

Run this first; it tells you what this machine can reach *today* rather than
what the registry claims:

```bash
.venv/bin/python -m siting_atlas.ingest.probe
```

Verified output. It is one small range-limited GET per source, so it costs
kilobytes; the 29 s wall clock is almost entirely one 25 s read timeout:

```
  7/14 sources acquirable without credentials or manual placement
  3 source(s) disagree with the registry
```

Disagreements are recorded, not smoothed over. In this run there were three:
`zillow_zori` probed `unreachable` where the registry says `blocked` (the
proxy refuses `files.zillowstatic.com` outright); `eia_prices` probed
`blocked` because the probe URL deliberately carries no key; and `acs5`
probed `unreachable` on a 25-second read timeout, which is also what makes
this the slowest of the L0 stages. The `acs5` verdict is transient — the
same endpoint answers fine in `census_api` two commands later.

### 4.1 Downloads itself

| Source | How |
|---|---|
| `gaz_zcta` | plain GET, `ingest.acquire` |
| `cbsa_county` | plain GET, `ingest.acquire` |
| `zcta_county_xwalk` | plain GET, `ingest.acquire` |
| `cbp_zip` | plain GET, `ingest.acquire` |
| `bps_county` | plain GET, nine vintages 2017-2025 |
| `acs5`, `acs1` | Census API, `ingest.census_api` |
| `eia_prices` | EIA v2 API, `ingest.eia_api` |
| `tiger_zcta` | plain GET, but ~520 MB: `--include-large` only |
| `osm` | Geofabrik, but large and not used yet: `--include-large` only |

### 4.2 You place these by hand

Four files, 214 MB, into `data/external/`. The filenames are **exact** —
`normalise_external.py` requires them literally, not by glob:

```
data/external/
  zillow_zori/Zip_zori_uc_sfrcondomfr_sm_sa_month.csv          9.5 MB
  zillow_zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
                                                             117.4 MB
  ejscreen/EJScreen_2024_Tract_with_AS_CNMI_GU_VI.csv.zip     48.3 MB
  bls_oes/oesm25ma.zip                                        38.1 MB
  facility_panel/facilities.csv                    4.6 KB, 43 rows
                                                   <- THE TARGET VARIABLE
```

Per-source download instructions, including which button to press on each
publisher's page, are in
[`data/ACQUISITION_GUIDE.md`](data/ACQUISITION_GUIDE.md) sections 3, 4 and 5.

**The one mistake that costs an afternoon.** Open any of these in Excel and
save, and `01890` becomes `1890`. Every ZIP join then silently loses those
rows — no error, no warning, just fewer rows. Do not round-trip them through
a spreadsheet. `ingest.external --check` catches this for the facility panel
specifically, because that is the target variable.

### 4.3 The one file nobody publishes

`data/external/facility_panel/facilities.csv` is the target variable — the
thing the model is supposed to predict — and no publisher issues it. For
most of this project it was a header row and no data, and that was the one
thing standing between a working pipeline and a fitted model.

**It is now delivered.** As of 2026-09-13 the file is 4.6 KB and holds 43
Amazon delivery stations, and the validator agrees:

```
  facility_panel    ok        43 facilities, 2015-2025, 1 operator(s)
```

Read that as 43 *buildings*, not 43 openings. Two of them opened before the
2018Q1 panel window (Chicago 60608 in 2015, Elizabeth NJ 07201 in 2017) and
are carried as left-censored rather than as events; two more sit in the
held-out metros. **39 usable events.** One closure is recorded: Chicago
2801 S. Western Ave (DCH1), closed 2021.

Most of those dates are **"operating by" upper bounds** taken from OSHA
inspection records, not opening dates. That is measured, not guessed: five
addresses appear in both MWPVL's 2012 census and the OSHA extract, the bound
held 5 of 5, and the lag from opening to first inspection was 4, 13, 57, 69
and 345 months. One site opened in 1997 and was first inspected in 2026.

How it was built, which four collection methods failed first, how the
selection bias was quantified, and the defects still in the file are all in
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) —
including a step-by-step rebuild from the public DOL extract in its §15. The
inputs to that rebuild are in the repo:

```
  data/raw/osha_bulk/            the 1.4 GB DOL extract + metadata
  data/raw/osm_amazon/           the OpenStreetMap export
  data/raw/mwpvl/                the MWPVL PDF (the 2012 yardstick)
  data/collection/prompts/       the collection prompts and worklists
  data/collection/keys/          number -> address maps for decoding replies
  data/collection/results/       DATES_FOUND / OSHA_CLASSIFIED / DS_PANEL
  scripts/osha_amazon.py         standalone stdlib-only OSHA extractor
```

All three raw drops carry a `data/raw/manifest.jsonl` entry with a SHA-256,
so you can check you have the same bytes we did.

`TEMPLATE.csv` sits beside it with three illustrative rows showing the shape.
`ingest.external` deliberately excludes any file named `TEMPLATE.csv` from
discovery, so a run cannot "succeed" on three fake facilities.

Required columns: `facility_id`, `operator`, `facility_type`, `city`,
`state`, `zip`, `open_year`, `source_url`, `source_type`. Optional:
`latitude`, `longitude`, `open_quarter`, `square_feet`, `status`,
`confidence`. See
[`data/FACILITY_PANEL_HOWTO.md`](data/FACILITY_PANEL_HOWTO.md).

Four controlled vocabularies are now **enforced** by
`ingest.external --check`, because an unenforced one drifts — two collectors
wrote `company_page` and `company_site` for the same thing and nothing caught
it:

| Field | Allowed values |
|---|---|
| `facility_type` | `DS` `SDC` `FC` `SC` `AMXL` |
| `source_type` | `press_release` `permit` `news` `company_site` `job_posting` `osm` `other` |
| `status` | `open` `closed` `announced` |
| `open_quarter` | `1`–`4`, or blank if genuinely unknown |

Leave `open_quarter` blank rather than guessing; a blank is honest and a
guess is not recoverable. A batch containing **zero `DS` rows** now raises a
warning, for the reason in §4.4.

### 4.4 What happened the day the file landed: nothing

That was the design goal, and it held. The switchover needed **zero code
changes**. `warehouse/facilities.py` was already written, already tested (15
tests), and already wired into `warehouse.panel.run()` via
`facilities.attach(db)`, which the panel builder calls unconditionally.
Absent file → `enabled` stays NULL, a WARNING is logged, and L0–L3 still
build. Malformed file → an error is logged, the same fallback applies, and
you are pointed at `ingest.external --check`. Present and valid → `enabled`
is populated and `models.runner` stops using the synthetic fixture, because
`panel_source.load_panel()` tests for at least one `True` rather than for the
file existing. On 2026-09-13 the third branch became the live one, and
nothing in the repository had to be edited for it.

What that produced, on the current panel: 27,914 of 1,081,312 cells TRUE
(2.58%), across 1,257 ZCTAs. The 2.58% is a property of the grid, not of the
target — the panel covers all 33,791 US ZCTAs while the facilities sit in
nine metros. Inside the ten pilot metros, which is the only scope anything
is fitted on, 1,230 of 2,413 ZCTAs (51.0%) are ever enabled.

Three modelling judgements are baked into that module. They are judgements,
not facts, and they are the right things to argue with:

- **Only `DS` and `SDC` set the target.** A fulfilment centre is a regional
  node; it does not put a van on a residential street. `FC`, `SC` and `AMXL`
  are carried for context and enable nothing. There is a test asserting
  precisely the failure the first data batch hit: **7 FCs enable zero
  ZCTAs.** Get this wrong and the model answers "where does Amazon warehouse
  things", which is a different question with a different answer.
- **Catchment is a radius — 15 miles for `DS`, 10 for `SDC`.** A real
  catchment is a drive-time isochrone shaped by roads. The radius is the
  honest approximation until the routing matrix exists.
- **Pre-2018 facilities are kept, left-censored.** They are not *events*, but
  they do mean the ZIP was already served on day one. Dropping them would
  tell the model those ZIPs were waiting to be switched on when they never
  were, which biases every coefficient; `models/risk_set.py` removes
  already-enabled units from the risk set instead.

---

## 5. The ordered run

Copy-pasteable. Setting `SITING_ATLAS_RUN_ID` first makes all ten commands
append to a single log directory, so the whole reproduction is one auditable
artefact rather than ten unrelated ones.

```bash
cd siting-atlas
PY=.venv/bin/python
export SITING_ATLAS_RUN_ID=$(date -u +%Y%m%d-%H%M%S)-repro

# ---- L0  acquire ---------------------------------------------------
$PY -m siting_atlas.ingest.probe            # what can this box reach?
$PY -m siting_atlas.ingest.acquire          # bulk files -> data/raw/
$PY -m siting_atlas.ingest.census_api --acs1
$PY -m siting_atlas.ingest.eia_api
$PY -m siting_atlas.ingest.external --check || true   # exits 1: see below

# ---- L1  normalise -------------------------------------------------
$PY -m siting_atlas.ingest.normalise
$PY -m siting_atlas.ingest.normalise_external

# ---- L2  warehouse -------------------------------------------------
$PY -m siting_atlas.warehouse.schema

# ---- L3  feature panel ---------------------------------------------
$PY -m siting_atlas.warehouse.panel --coverage

# ---- L4  decision layer (no target variable needed) ----------------
$PY -m siting_atlas.cost.runner --all-scenarios
$PY -m siting_atlas.optimize.runner --budget 2e9 --frontier

# ---- L4  model layer: real panel; the result is NEGATIVE, see STATUS -
$PY -m siting_atlas.models.runner

# ---- L4  the six write gates, against real warehouse state ---------
$PY -m siting_atlas.agent.runner --demo-plano

# ---- L5  scope and figures -----------------------------------------
$PY -m siting_atlas.report.scope
$PY -m siting_atlas.viz.build --all-scenarios
```

To see the dashboard over the same numbers:

```bash
bash scripts/run_dashboard.sh          # localhost:8501
PORT=8600 bash scripts/run_dashboard.sh
```

The launcher itself was **not executed here** — it blocks on a web server. What
was verified is that `siting_atlas.app.dashboard` imports and renders in
Streamlit's bare mode against the cost tables produced above. The launcher
exists because Streamlit execs the app file as a top-level script with no
parent package, so `src/` has to be on `PYTHONPATH` or the absolute
`siting_atlas.*` imports fail.

`|| true` on the external check is deliberate. That stage **exits 1 on
purpose** when the facility panel is unusable, and under `set -e` it would
stop the script. Since 2026-09-13 the panel is usable and the stage exits 0,
so the guard is dormant — it is kept because the exit code is the signal,
and a dropped guard is the kind of thing nobody notices until the day the
file breaks again.

---

## 6. What each stage should print

Every figure below is from the verified run. A number marked *moves* will
change as a publisher extends a series.

### L0 — probe

```
  7/14 sources acquirable without credentials or manual placement
```
Wall clock **29.4 s**, of which 25 s is the one timeout. Writes
`outputs/metrics/source_probe.json`.

### L0 — acquire

```
  fetched 0 | cached 5 | skipped 8 | failed 0
```
Wall clock **0.9 s warm**. Cold, expect ~11 MB over the network. Skipped
sources each print a reason and a remedy; none is silent.

Writes `data/raw/<source>/<sha-prefix>.<ext>` and appends one line per fetch
to `data/raw/manifest.jsonl` with the SHA-256, so a reviewer can
re-download and verify. `data/raw/` totals **16 MB**.

### L0 — census_api

```
  ACS 2023: 33,772 ZCTAs, 16 columns -> data/interim/acs5_zcta_2023.parquet
```
Plus ACS1 **530 metros x 5 columns**. Wall clock **3.3 s warm**.

### L0 — eia_api

```
  EIA: 4,992 state-months, 52 states -> data/interim/eia_energy.parquet
```
Wall clock **3.0 s warm**. Diesel coverage 98.1%, latest month 2025-12.
*moves*

### L0 — external --check

```
  source            status    detail
  ------------------------------------------------------------------
  facility_panel    ok        43 facilities, 2015-2025, 1 operator(s)
  zillow_zori       ok        9.5MB
  zillow_zhvi       ok        117.4MB
  ejscreen          ok        48.3MB
  bls_oes           ok        38.1MB
  eia_prices        missing   not placed yet

  5 ready | 0 need attention | 1 not placed
```
Wall clock **0.4 s**. **Exit code 0.**

Until 2026-09-13 the first line read `!facility_panel  suspect  146B`, the
tally read `4 ready | 1 need attention`, the stage printed
`BLOCKING: the facility panel is the target variable`, and it exited 1. If
you see that, your `facilities.csv` has not been checked out — see §4.3.

`eia_prices missing` is correct and misleading: EIA comes through the v2 API,
not by hand, so no file is expected there. The registry describes that source
twice.

### L1 — normalise

```
  6/6 normalised -> data/interim
    gazetteer               33,791 rows
    cbp                     35,002 rows
    building_permits        15,812 rows
    zcta_county             33,791 rows
    cbsa_county              1,915 rows
    zillow_zori            456,917 rows
```
Wall clock **5.7 s**. CBP's 35,002 exceeding the 33,791 ZCTAs is correct —
it includes point ZIPs and retired vintages, filtered out at L2.

### L1 — normalise_external

```
  3/3 normalised -> data/interim
    zillow_zhvi          3,435,525 rows
    bls_wages                1,571 rows
    ejscreen_tract          86,082 rows
```
Wall clock **29.9 s** — the slowest stage, dominated by reading a 30 MB xlsx
out of a zip.

### L2 — warehouse.schema

```
  5 tables -> data/processed/siting_atlas.duckdb
    dim_zcta              33,791 rows
    dim_county             3,211 rows
    dim_date                  32 rows
    dim_scenario               1 rows
    fact_zcta_year       270,328 rows
```
Wall clock **7.0 s**. Output 25 MB. Idempotent (`CREATE OR REPLACE`).

### L3 — warehouse.panel

```
  panel -> data/processed/panel.parquet
    1,081,312 rows x 44 columns
```
Wall clock **6.2 s**. Output 14 MB. 33,791 ZCTAs x 32 quarters
(2018Q1-2025Q4).

`--coverage` prints percent non-null for every column, and writes the full
list to `experiments/superseded-artefacts/panel_report.json` (`coverage`, with a `run_id`).
Read it there; the column count has moved once already. The ones to check:

| Column | Expect |
|---|---|
| `zcta` `year` `quarter` `state` `county_geoid` | 100% |
| `population` and the other ACS levels | 99.94% |
| `establishments` `employment` `annual_payroll` | 91.53% |
| `electricity_cents_kwh` `diesel_usd_gal` | 99.56% |
| `home_value` (ZHVI) | 74.90% |
| `permit_units_total` | 65.44% |
| `permits_yoy_pct` | 55.44% |
| the five wage columns | ~54.67% |
| `rent_index` | 11.23% |
| `enabled` | **100%** non-null, of which **2.58% are TRUE** |

**Correction, 2026-09-13.** This table said `enabled` was **0.00%**
populated. It is not, and has not been since the facility panel landed:
`panel_report.json` reports 1,081,312 of 1,081,312 non-null, and §4.4 of this
same document says so two hundred lines earlier — 27,914 TRUE cells (2.58%)
across 1,257 ZCTAs. The §8.3 snippet at the end of this file already asserts
`p['enabled'].notna().mean()` should be `1.0`. A document contradicting
itself about its own target variable is worse than a document that is silent,
so the old figure is recorded here rather than quietly overwritten. The
confusion is a real one worth naming: `enabled` is a **boolean, not
nullable** — every cell is populated, and 2.58% of them are `True`. "0.00%"
was probably the pre-delivery state, when the column existed and was NULL
throughout.

If `permits_yoy_pct` comes out at 0.00%, you fetched one BPS vintage instead
of nine. If a wage column is near 16% rather than 55%, BLS was joined on
metro title instead of CBSA code. If `enabled` comes out at 0.00% non-null,
`facilities.csv` is missing or malformed — run `ingest.external --check`.

### L4 — cost.runner

```
  placed 334 depots across 11 metros (40000 parcels/depot)
  2,333 pilot ZCTAs   median $1.09/parcel   p10 $0.99  p90 $1.36
  78,292 vans/day   $14,087,960/day total
```

**The van count was wrong here until 2026-09-13.** This block said **79,484
vans/day**, which is the pre-fix figure: `vans_required` was rounded up per
ZCTA and then summed, inventing 1,192 vans out of arithmetic
(`DECISION_LOG.md` §2.6). `cost/runner.py` now reports
`ceil(sum(van_days))`. Take the live values from
`outputs/metrics/cost_report.json` — `total_vans`, `total_daily_cost_usd`,
`median_cost_per_parcel` — rather than from this page.
Wall clock **11.6 s** for one scenario, **25.1 s** for all five -- the depot
k-means is solved once per scenario and dominates.

2,413 pilot ZCTAs minus **80 dropped for zero households** = 2,333. That drop
is logged, not silent: a ZCTA with no households would divide by zero and put
an infinite cost at the top of the ranking.

Sensitivity, all five scenarios:

| Scenario | Median $/parcel | vs baseline |
|---|---|---|
| `dense_routing` | 0.90 | -17.0% |
| `baseline` | 1.09 | +0.0% |
| `high_fuel` | 1.09 | +0.6% |
| `pessimistic_tour` | 1.10 | +1.0% |
| `congested` | 1.14 | +4.4% |

This table was itself stale until 2026-09-12: it carried the pre-depot-network
figures (baseline 1.51, `congested` +14.5%) alongside a run block that already
reported the corrected median of $1.09. The spread narrowed because the old
sensitivity was partly measuring the single-centroid proxy — with realistic
line hauls there is far less driving for a lower average speed to punish.

### L4 — optimize.runner

```
  budget funds 500 activations; <detail.n> selected
  capital committed      <detail.capital>
  annual parcels served  <detail.parcels>
  annual cost to serve   <detail.cost>

  BREAK-EVEN MARGIN      <breakeven_margin> per parcel
  greedy alone           <greedy_breakeven>
  after local search     <breakeven_margin>
  upper bound            <upper_bound>   (no cannibalisation)
  optimality gap         <optimality_gap>   instance-specific, NOT worst-case

  vs naive top-K         <naive_breakeven>                   [--compare-naive]
```
Wall clock **29.8 s** plain, **38.6 s** with `--compare-naive`, **162.9 s**
with `--frontier` (six solves, so a little over 5x a single run).

**This block deliberately shows the artefact's key names, not numbers.** Every
value above is a field of `experiments/portfolio-optimiser/artefacts/portfolio_report.json`, which
stamps a `run_id` and a `written_at`. Print it with
`cat experiments/portfolio-optimiser/artefacts/portfolio_report.json`. The reason for the change is on
the record and it is not tidiness:

```
                  as this page read   2026-09-13 14:43   CURRENT, run
                                                         20260914-002431-7419
   ------------------------------------------------------------------------
   activations       317 of 500        330 of 500        282 of 500
   capital           $1,268,000,000    $1,320,000,000    $1,128,000,000
   optimality gap    13.03%            13.39%            10.73%
   unspent           $732m             $680m             $872m
   naive break-even  $1.5516           $1.5567           not emitted
                                                         (frontier: null)
```

**Three runs, three headlines, and the third supersedes both the others.**
Print the artefact; do not read the table.

`DECISION_LOG.md` §4.2 found that divergence and **left the documents stale on
purpose**: "$732m unspent" is a headline finding, and before any document is
edited somebody should establish *why* it moved, because an unintended input
drift is a worse problem than a stale number. The baseline cost median moved
at the same time (1.08744349 -> 1.08749057), which points at an input rather
than a parameter. **The investigation has since happened, 2026-09-14, and the
answer is in `DECISION_LOG.md` §4.2.** The mover is depot placement, which
changed from k-means to p-median with nothing in `optimize/` touched, and a
500-draw Monte Carlo shows the drift is wider than parameter uncertainty —
282 sits at the 67th percentile of the draws and 330 at the 97th. No set is
endorsed and none is typed: the durable fix, and the one this project keeps
relearning, is to cite the run-stamped artefact.

**Read the first line before anything else.** The budget funds 500
activations and the optimiser takes fewer, leaving part of a $2 bn budget
unspent. That is the headline, not an error: at the assumed margin the
remaining fundable ZCTAs destroy value, and the model can now say so. The
previous objective structurally could not.

#### Why the objective was replaced

The old objective *minimised the portfolio's break-even margin*. That is
degenerate, and you can see it in three lines. Ranking ZCTAs by standalone
break-even and taking the cheapest n:

```
   n =   1     marginal break-even  $1.1910   <- the minimum
   n =  10                          $1.4903
   n = 100                          $1.5278
   n = 317                          $1.5193
   n = 500                          $1.5516
```

The objective is minimised at **n = 1**. It literally said "build one
facility". Greedy only ever produced a sensible-looking answer because it was
forced to spend the entire budget — it had no stopping rule and no way to
express "this activation destroys value".

The objective is now **maximise NPV at an assumed contribution margin**:

```
     NPV(S)  =  m * A(S)  -  B(S)  -  K(S)

       m  contribution margin per parcel   (unobservable)
       A  annual parcels served by the set
       B  annual cost to serve it
       K  capital, $4 m per activation
```

Non-degenerate, and it yields a real stopping rule: stop when the marginal
NPV of the next activation is <= 0.

#### The margin is unobservable, so the deliverable is a frontier

Nobody outside the operator knows `m`, and NPV is linear in it, so picking
one number would decide the answer. Two devices keep that honest.

**A self-referential default.** `--margin` defaults to
`_neutral_margin()`: the break-even of a *full-budget* portfolio, emitted as
`naive_breakeven`. At exactly that margin the whole budget is worth spending
and no more — so whatever the optimiser then chooses to leave unspent is a
real finding rather than an artefact of a guessed constant. (It is the same
number the naive top-K reports, because naive top-K *is* the full-budget
portfolio.)

**A frontier instead of a point.** `--frontier` solves across a range. The
table below was produced on 2026-09-12 and **is not in the current
artefact** — `portfolio_report.json` carries `"frontier": null`, because the
14:43 run on 2026-09-13 was a single solve. Re-run
`optimize.runner --frontier` to regenerate it; the shape, not the digits, is
what the section is arguing.

| margin $/parcel | activations | capital $ | NPV $ |
|---|---|---|---|
| 0.931 | 0 | 0 | 0 |
| 1.241 | 37 | 148,000,000 | 60,106,514 |
| 1.552 | 317 | 1,268,000,000 | 907,108,565 |
| 1.862 | 500 | 2,000,000,000 | 3,175,218,042 |
| 2.327 | 500 | 2,000,000,000 | 6,823,208,712 |
| 3.103 | 500 | 2,000,000,000 | 12,965,845,751 |

Read it as: *below about $0.93 a parcel nothing is worth building; around
$1.55 roughly two thirds of the fundable set is; above about $1.86 the budget
binds rather than the economics.* That is a defensible statement about a
quantity we cannot observe. A single NPV would not be.

#### The honest caveats, unchanged

**No (1 - 1/e) guarantee is claimed.** That bound applies to greedy
maximisation of a *monotone submodular* function. This objective has positive
interactions (two adjacent ZCTAs share one trip out of the depot) and
negative ones (overlapping catchments cannibalise), so it is neither
submodular nor supermodular, and citing the bound would be borrowed rigour.
What is reported instead is an achieved value against a computed upper bound
that ignores every negative interaction — genuinely an upper bound — and the
gap. **`optimality_gap` is a statement about this instance, not a worst
case.** (This line used to name 13.03%; read the field.)

**`--compare-naive` earns its keep.** Accounting for interaction beats
naively taking the K cheapest by **10.79%**, up from 7.09% before the
objective was fixed and 2.64% before the depot network landed.

**Two arithmetic bugs were fixed alongside**, both of which had been
inflating the apparent value of clustering:

- annual flows were computed at **365** days; the network delivers **312**
  (6 days x 52). `delivery_days_per_year` is now derived from
  `cost/params.py` rather than typed, so the two cannot drift. It matters
  here more than in `cost/` because capital per activation does *not* scale
  with the flow, so inflating parcels and operating cost together shrank
  capital's share and understated the break-even margin by ~3.5%.
- the line-haul cost pool applied a *mileage* share to *total* cost. Service
  time at the door and the van lease are paid whatever route the van drove,
  so the shareable pool was **2.9x** too large and the optimiser
  over-credited clustering.

**This module is still moving.** The figures above were measured at 11:11 on
2026-09-12. Earlier the same day the same command returned $1.242 (gap
18.20%), then $1.638 (gap 21.66%), then $1.442 (gap 17.71%) — the first two
on the old single-centroid depot proxy, the third on the old objective.
Re-measure rather than quoting these.

### L4 — models.runner  (REAL DATA, and the result is NEGATIVE)

Wall clock **13.4 s**. **Read this section before you quote any number from
it.**

The runner has one code path and two possible inputs.
`models/panel_source.load_panel()` returns the real panel only if `enabled`
contains at least one `True`. **It does** — 27,914 True cells — so the
runner reads the real panel, no banner is printed, and
`experiments/hazard-model/artefacts/hazard_report.json` carries `"synthetic": false`. The
synthetic-fixture branch still exists in the code and nothing has taken it
since 2026-09-13; there are no `SYNTHETIC_*` files left in `outputs/`.

```
  HELD-OUT TEST, 8,044 rows / 161 events    Brier       ECE      AUC
  cloglog hazard                          0.019522   0.00863   0.6894
  base rate only                          0.019614   0.00005   0.5000
                                                     ^ NULL 170x better

  TEMPORAL HOLD-OUT, 11,871 rows / 245 events
  cloglog hazard                          0.020635   0.01196   0.5551
  base rate only                          0.020213   0.00073   0.5000
                                          ^ NULL BETTER OUTRIGHT

  CONFORMAL COVERAGE
  nominal 90.0%   empirical 88.2%   (within tolerance, 351 eff. units)

  POWER (hazard_report.json, "power")
  812 ZCTA events, but 28-38 real decisions, against 5 parameters.
  7.6 events per parameter on the optimistic count; floor is 10. NOT MET.
```

**Report the raw Brier PAIR, not the Brier skill.** This block used to print
`Brier skill +0.0047 / -0.0209 / -0.0618`. A skill score is
`1 - S_model/S_null`, and Gneiting & Raftery (2007) §2.3 p.362 states that
skill scores "are generally improper, even if the underlying scoring rule S
is proper" — which the Brier score is (§3.1 p.363). `hazard_report.json`
still emits `brier_skill`; treat it as a readability normalisation, not as
the estimand. Notes:
[`research/NOTES_gneiting_raftery_2007.md`](research/NOTES_gneiting_raftery_2007.md).

**The geographic hold-out (-0.06184) has been removed from this block** and
must not be quoted as a transfer result. `experiments/hazard-model/artefacts/hazard_report.json:819`
says Phoenix and Boise hold **two dated delivery stations between them**, "so
this is a smoke test for gross failure and not a test of geographic
transfer". It is under `transfer_smoke_test` in the artefact for that reason.

**Read the ECE column, not the AUC column.** The model ranks slightly better
than chance (AUC 0.69) and its probabilities are 170 times less trustworthy
than a constant's. Out of time it is beaten outright. This is a negative
result and should be quoted as one.

**Why it is a *useful* negative result — and this sentence was wrong until
2026-09-13.** It used to read: *"39 events across 43 buildings, dated by OSHA
upper bounds, is exactly the sample you would predict could not identify a
siting model."* That is the sample-size diagnosis, and
[`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14 rejects it. The defect is the **unit of analysis**:
one station switches on every ZCTA within fifteen miles at once, a median of
58, so the 812 ZCTA-quarter events are 28 to 38 decisions plus geometry, and
**Train (2009) §3.7.1, printed p. 61** — the assumption that decision makers
choose independently of one another — is therefore violated. *(CITATION
CORRECTED 2026-09-14: this cited §2.2, mutual exclusivity, which Train calls
"not restrictive".)* A panel ten
times larger at the same grain would fail the same way. Sample size still
matters for the successor — 7.6 per parameter against a floor of 10 — but it
bounds the new model's *precision*, it does not explain the old one's
failure. See [`STATUS.md`](STATUS.md) and
[`adr/0004-model-change-conditional-choice.md`](adr/0004-model-change-conditional-choice.md).

**The older synthetic figures, for context.** On the labelled fixture the
estimator scored AUC 0.729 and recovered `x_demand` 0.728 / `x_cost` -0.346 /
`x_competition` 0.284 against a known 0.800 / -0.450 / 0.300. **That was
never a result about siting.** It was a statement that the link function, the
risk-set construction, the standardisation, the spline basis and the
conformal calibration compose correctly, demonstrated by handing the
estimator a process whose coefficients we chose and checking it hands them
back. With real data the truth is the thing you are trying to find out, so
real data cannot make that check — which is why the fixture branch is kept.

**It is deterministic.** `models/fixtures.py` draws from
`np.random.default_rng(seed("models", "hazard"))`, which reads
`reproducibility/seeds.toml` — nothing hardcodes a seed. Two runs forty
minutes apart produced byte-identical coefficients, so if your numbers differ
from the ones above, something other than the RNG differs.

Note the conformal tolerance is computed on 351 *effective units*, not 7,817
rows — quarters of the same ZCTA are not independent draws.

### L4 — agent.runner

Wall clock **7.8 s**. Runs a demo mutation (a Walmart sortation centre in
75024) through the six gates against real warehouse state.

```
  [PASS] gate 1 schema conformance
  [PASS] gate 2 geocoding reachability
  [PASS] gate 3 confidence threshold (0.94)
  [PASS] gate 4 audit-log immutability
  [HOLD] gate 5 donor-pool integrity
  [HOLD] gate 6 estimate stability: could not be evaluated
  OUTCOME   ESCALATED TO HUMAN
```

Expected, and the point of the exercise: the data is fine and the *inference*
cannot be checked. This paragraph used to explain that as "with `enabled`
empty there is no donor pool to contaminate" — `enabled` is not empty
(see §4.4 and the L3 coverage table), so that reason is retired. The live
reason is that the donor pool built from 43 buildings is **thin**: in metros
holding one or two rows, gate 5 cannot separate donors from treated units and
gate 6 has nothing stable to re-estimate. Every invocation writes
`outputs/audit/<mutation_id>.json` and appends to `mutations.jsonl` —
rejections included, because "it never let a bad write through" is only a
claim if the attempts were logged.

### L5 — viz.build

Wall clock **11.0 s** for one scenario, **14.6 s** for `--all-scenarios`.
Four PNGs per scenario into `outputs/figures/` — `cost_vs_density`,
`cost_by_metro`, `cost_decomposition`, `cumulative_coverage`, each suffixed
with the period and scenario — so **20 PNGs** across the five scenarios. It
exits non-zero if any label had to be shrunk past its floor.

### L5 — report.scope

```
  10 pilot metros (8 fit / 2 held out)
  84 counties, 2,413 ZCTAs [OMB 2023 CBSA delineation]
  capital at risk : $7.2B-$12.1B  ($3-5M per activation)
```
Wall clock **2.4 s**. Writes `outputs/metrics/scope.json`, which is the file
every document reads its headline numbers from. **Never retype a scope
figure** — that is how the proposal ended up claiming 5,200 ZCTAs when the
measured number is 2,413.

---

## 7. Total time and disk

| Stage | Warm wall clock |
|---|---|
| probe | 29.4 s |
| acquire | 0.9 s |
| census_api --acs1 | 3.3 s |
| eia_api | 3.0 s |
| external --check | 0.4 s |
| normalise | 5.7 s |
| normalise_external | 29.9 s |
| warehouse.schema | 7.0 s |
| warehouse.panel | 6.2 s |
| cost.runner --all-scenarios | 25.1 s |
| optimize.runner --compare-naive | 38.6 s |
| models.runner (synthetic) | 13.4 s |
| agent.runner --demo-plano | 7.8 s |
| report.scope | 2.4 s |
| viz.build --all-scenarios | 14.6 s |
| **total** | **~2 min 40 s** (add 163 s if you run `--frontier`) |

Cold, add the download: about 11 MB of bulk files plus the API pulls. The
214 MB of manual files are a one-off human step, not part of the timing.

| Directory | Size |
|---|---|
| `data/raw` | 16 MB |
| `data/external` | 214 MB |
| `data/interim` | 61 MB |
| `data/processed` | 40 MB |
| `outputs` | 2.5 MB |

No distributed compute anywhere. The hard problem in this project is
identification, not throughput.

---

## 8. Verify you got the same answer

Four checks, in increasing strength.

### 8.1 Shape

```bash
.venv/bin/python - <<'EOF'
import pandas as pd
p = pd.read_parquet('data/processed/panel.parquet')
print(p.shape)                     # expect (1081312, 44)
print(p['enabled'].notna().mean()) # expect 1.0  (populated boolean)
print(p['enabled'].mean())         # expect 0.0258 (share TRUE)
EOF
```

### 8.2 Scope, read rather than typed

```bash
.venv/bin/python - <<'EOF'
import json
print(json.load(open('outputs/metrics/scope.json'))['pilot'])
EOF
```

Expect 10 metros, 84 counties, 2,413 ZCTAs, and the per-metro split
New York 893, Chicago 380, SF Bay Area 241, Miami 185, Seattle 170,
Phoenix 164, Denver 137, Nashville 111, Austin 89, Boise 43.

### 8.3 The cost table

```bash
.venv/bin/python - <<'EOF'
import pandas as pd
r = pd.read_parquet('outputs/tables/cost_to_serve_2023q4_baseline.parquet')
print(len(r), round(r.cost_per_parcel.median(), 4),
      round(r.cost_per_parcel.quantile(.10), 4),
      round(r.cost_per_parcel.quantile(.90), 4))
EOF
```

Expect `2333 1.0874 0.9853 1.3643`.

*(This used to read `2333 1.5094 1.123 2.3299`, which were the numbers from
before `cost/depots.py` replaced the single-centroid depot proxy with a
solved 334-depot network. They contradicted §5.1 of this same document for a
day. If you are ever unsure which figure in this file is current, the
parquet is — that is the point of these snippets.)*

### 8.4 One row, end to end

The strongest check, because it exercises the whole chain rather than an
aggregate. ZCTA 11222 (Greenpoint, Brooklyn) in 2023Q4:

```bash
.venv/bin/python - <<'EOF'
import pandas as pd
r = pd.read_parquet('outputs/tables/cost_to_serve_2023q4_baseline.parquet')
print(r[r.zcta == '11222'].T.to_string())
EOF
```

Expect `stop_density_per_sqmi` 6047.213128, `miles_per_stop` 0.041984,
`cost_per_parcel` 0.997283, `vans_required` 77. (`miles_per_stop` and
`cost_per_parcel` also moved with the depot-network fix; density and van
count did not, because neither depends on line haul.) The arithmetic behind those
numbers is walked through by hand in
[`data/COST_MODEL.md`](data/COST_MODEL.md) §4.

### 8.5 Tests

```bash
.venv/bin/python -m pytest
```

`658 passed, 2 xfailed, 0 failed` on 2026-09-15 — **660 collected** across 60
test files — and `ruff check src tests` is clean. It was `483 passed,
2 xfailed` on 2026-09-13 and `647 passed, 1 failed, 2 xfailed` on 2026-09-14 —
the suite is being extended actively, so the count will have moved again.

**The suite is GREEN again, which reverses what this section used to say.**
The single failure recorded here on 2026-09-14 —
`tests/unit/test_choice_inference.py::test_the_sandwich_matches_a_numerical_hessian_at_an_interior_optimum`,
an `ImportError` on `_score_and_hessian`, a private helper renamed while
`models/choice_inference.py` was still landing — is fixed. It was a
test/module mismatch in unfinished work, not a modelling defect.

A green suite is not the same as a covered one. **78 of the 181 source modules
under `src/siting_atlas/` are not imported by any test**, directly or
transitively — an AST import-graph walk seeded from every file under `tests/`,
following relative and absolute `siting_atlas.*` imports and package `__init__`
ancestors. Every headline artefact in `outputs/metrics/` is written by a module
in that unreachable set, so "796 tests pass" and "the headline artefacts have
no test importing their emitter" are both true and should be quoted together.

---

## 9. If it does not reproduce

| Symptom | Cause | Fix |
|---|---|---|
| JSON decode error from the Census stage | no key, or a bad key | the API returns HTML with HTTP 200; check `.env` |
| `permits_yoy_pct` is 0.00% | one BPS vintage fetched, not nine | `acquire --only bps_county --force` |
| Wage columns near 16% | BLS joined on metro title, not CBSA code | rebuild the panel; the override lives in `warehouse/optional.py` |
| `FileNotFoundError` naming a section number | a manual file is missing or misnamed | the filenames in §4.2 are literal |
| Fewer rows than expected after a ZIP join | leading zeros stripped by a spreadsheet | re-export with the column typed as Text |
| `ModuleNotFoundError: siting_atlas` | no editable install | prefix with `PYTHONPATH=src` |
| L1 fails reading an `.xlsx` | `openpyxl` is not declared in `pyproject.toml` | `pip install openpyxl`; see §2.2 |
| `dbt-core` build error during install | an older `pyproject.toml` where `dev` still pulls `dbt-duckdb` | install `.[viz,docs]` plus the test tools; see §2.1 |
| `external --check` exits 1 on `facility_panel` | the panel is empty or malformed | it should exit 0 with `43 facilities, 2015-2025`; check the file was not truncated or Excel-mangled, see §4.3 |

---

## 10. What you cannot reproduce, and why

State plainly, because this is the honest part.

- **No *working* model result.** This bullet used to say the only thing you
  could not reproduce was a *well-powered* fit. That was a hedge, and it is
  now out of date in the worst direction: the fit exists, it is on real data,
  and **it does not work**. Brier 0.019522 against the null's 0.019614 over
  the same 8,044 rows; ECE 0.00863 against the null's 0.00005, so it is worse
  calibrated than a constant; out of time the null wins outright, 0.020635
  against 0.020213 over 11,871 rows. You can reproduce all of that exactly.

  **What you cannot reproduce is a good number — and the reason is not the
  one this bullet used to give.** It said the data "does not contain one" and
  then listed 39 events, 8 fitting metros and a 2-facility backtest window.
  All of those are true and none of them is the cause. The cause is the unit
  of analysis: a ZCTA-quarter is not a decision, one station switches on a
  median of 58 ZCTAs at once, and **Train (2009) §3.7.1, printed p. 61**
  assumes each decision maker chooses independently of every other, which 58
  ZCTAs switched on together do not. *(CITATION CORRECTED 2026-09-14 from
  §2.2.)* [`METHODS_RESEARCH.md`](METHODS_RESEARCH.md) §14 is the canonical statement
  and rejects the sample-size reading; the specification change is recorded
  in [`adr/0004-model-change-conditional-choice.md`](adr/0004-model-change-conditional-choice.md).
  The successor model is under-powered in its own right — ~43 decisions, 38
  usable, 5 parameters, 7.6 per parameter against a floor of 10 — so it will
  be *valid* and *imprecise*, which is a different and better problem.

  Two reporting rules survive from the old bullet and one is added. Quote the
  **decision** count, not the ZCTA-event count, next to every metric. Report
  the raw Brier **pair** rather than the skill (Gneiting & Raftery §2.3
  p.362). And do not quote the geographic hold-out (-0.06184) as evidence
  about transfer: `experiments/hazard-model/artefacts/hazard_report.json:819` calls it a smoke
  test, Phoenix and Boise holding two dated stations between them. There are
  no `SYNTHETIC_`-prefixed artefacts left to check a filename against.
- **No usable verdict from gates 5 and 6.** They run and they refuse to
  report a pass, which is the honest behaviour. The donor pool they need can
  now be built, but from 39 events it will be thin, so expect "not enough
  units" rather than a green light.
- **No drive-time matrix.** Routing (`osm`, OSRM, the OD matrix) is designed
  and not built. The cost model uses great-circle distance times a circuity
  multiplier of 1.30 instead. The depot is no longer a population-weighted
  metro centroid — `cost/depots.py` solves a 334-depot network by
  parcel-weighted k-means — but those are still *modelled* positions, not
  observed buildings.
- **No causal estimate.** Cannibalisation, the decay radius and the spatial
  synthetic control all need many more openings than 39. The panel makes
  them attemptable and does not make them credible.
- **No claim about *when*.** The dates are upper bounds (§4.3), so "this
  ZIP was served by 2022" is supportable and "Amazon opened N stations in
  2023" is not. The modal year in the panel is an inspection fact.
- **A cold clone cannot get to a full rebuild unaided**, because five
  sources are placed by hand. Four of them are downloads a stranger can do;
  the fifth, the facility panel, ships with the repo, and rebuilding it from
  scratch is the multi-day exercise in
  [`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md)
  §15.

See [`STATUS.md`](STATUS.md) §5 and [`ROADMAP.md`](ROADMAP.md) for what unblocks each of these.
