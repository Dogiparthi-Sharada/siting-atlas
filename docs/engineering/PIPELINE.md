# The Pipeline As Built

**Every stage that exists, the exact command that runs it, what it reads,
what it writes, and the row counts it actually produced.**

> **State on 2026-09-13, with every count re-measured against the artefacts
> on 2026-09-14.** L0 through L5 run end to end and were executed in order
> while writing this document. The 2026-09-14 pass corrected roughly two
> dozen numbers, all of them in §1.1, §2.3, §3.1, §3.3, §5, §6.1, §6.2, §6.3,
> §8.1 and §9; each correction says so where it sits rather than being
> silently applied. The largest were the disk footprints (out by two orders
> of magnitude), the depot algorithm (p-median, not k-means) and the
> portfolio counts (282, not 330).
>
> Until 2026-09-13 this note said the
> project was blocked, because
> `data/external/facility_panel/facilities.csv` was header-only and the panel
> had no outcome column to predict. **That is resolved.** The file now holds
> **43 Amazon delivery stations**, `ingest.external --check` reports
> `facility_panel ok  43 facilities, 2015-2025, 1 operator(s)`, and `enabled`
> is populated — 27,914 TRUE cells of 1,081,312 (2.58%).
>
> **The hazard model has since been fitted on that panel, and it does not
> work.** Worse calibrated than a constant, negative skill out of time and
> out of area. Read [`../STATUS.md`](../STATUS.md) before quoting anything
> from the model layer.
>
> Two things stay true and must travel with that. First, no `SYNTHETIC_*`
> artefact exists any more — the fallback fixture is still in the code but
> nothing has taken that branch since the target landed. Second, the panel is
> small and its dates are mostly "operating by" **upper bounds** from OSHA
> inspection records: 43 buildings give **39 usable events** across 8 fitting
> metros, a ninth (Nashville) having none. Cost, portfolio
> selection and the L5 figures need no target variable and run on real data
> regardless. See
> [`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md).

Every number below came from running the command shown. Where a count is
likely to move — because a source is still being extended — that is said in
place rather than left for the reader to discover.

---

## 1. Before anything runs

### 1.1 The environment

```bash
python3.13 -m venv .venv
.venv/bin/pip install duckdb pandas pyarrow statsmodels scikit-learn \
    lightgbm matplotlib requests openpyxl
```

`.venv` holds Python 3.13.14 with duckdb 1.5.5, pandas 3.0.5, pyarrow 25.0.1,
statsmodels 0.15.0, scikit-learn 1.9.1, lightgbm 4.7.0, matplotlib 3.11.2,
requests 2.34.2 and openpyxl 3.1.5.

`pyproject.toml` now lists only what `src/siting_atlas` actually imports.

**Both statements that used to follow here were wrong and are corrected
2026-09-14.**

*"Geometry sits in a `geo` extra: none is installed and no stage imports
them."* Two thirds false. `geopandas 1.1.4` and `shapely 2.1.2` **are**
installed, and `ingest/osm_landuse.py` imports both (`:56` and `:188`). Only
`h3` is genuinely absent. The claim was true when the only geometry work was
the Gazetteer's centroid and area columns; `normalise_geo.py` and
`osm_landuse.py` changed that. The comment at `pyproject.toml:35-38` — *"not
used yet … until something imports it"* — is stale for the same reason.

*"`openpyxl` is required in practice and is not declared."* False.
`pyproject.toml:20` declares `"openpyxl>=3.1"` in `dependencies`, with the
comment *"pandas.read_excel: the OMB and BLS workbooks"*. It was presumably
added after this line was written and the line was not removed.

### 1.2 `PYTHONPATH=src` is no longer required

The package is now editable-installed: `site-packages` carries
`__editable__.siting_atlas-0.1.0.pth`, so `python -m siting_atlas...`
resolves from any directory. The `PYTHONPATH=src` prefix on every command
below is harmless and still works, and it is what you need if you skipped the
editable install:

```bash
export PYTHONPATH=src        # only if `pip install -e .` was not run
```

### 1.3 Credentials

Two free keys, in `.env` at the repo root, gitignored:

```
CENSUS_API_KEY=...
EIA_API_KEY=...
```

`common.config.load_dotenv()` reads them into the environment on first use,
and `ingest.acquire` now calls it before anything reads the environment — see
2.5. The keyed sources are still acquired by their own modules rather than by
the generic acquire loop, but for a real reason (an API needs a variable list
and paging) rather than because the key was invisible.

---

## 2. L0 — acquire

**Contract:** the network becomes an immutable, content-addressed cache.
Nothing is downloaded twice; every fetch is recorded with its SHA-256 so a
reviewer can re-download and verify.

Four modules sit at L0. Three fetch; one validates what a human placed.

### 2.1 `ingest.sources` — the registry

Not a stage. A frozen dataclass per dataset recording provider, grain, role,
licence, endpoint, credential variable, publication cadence, reporting lag
and — importantly — measured `Availability`.

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.acquire --list
```

Fourteen sources are registered: seven `open`, three `needs_key`, two
`blocked`, two `manual`. Thirteen are analytical; OpenStreetMap is excluded
because it is consumed offline and never reaches the feature table.

### 2.2 `ingest.probe` — is this reachable from here, today?

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.probe
```

A range-limited GET per source, so probing costs kilobytes. Writes
`outputs/metrics/source_probe.json`. Last run: **7 of 14 acquirable without
credentials or manual placement**, and three sources disagreed with the
registry — `zillow_zori` probes `unreachable` (the egress proxy refuses
`files.zillowstatic.com` outright) where the registry says `blocked`;
`eia_prices` probes `blocked` because the probe URL carries no key; and
`acs5` probed `unreachable` on a 25-second read timeout, which is transient
and dominates this stage's wall clock. All three disagreements are recorded
rather than reconciled away; the probe logs a warning when the registry
drifts.

Run this before a long build. A four-hour run that fails at minute 200 on a
blocked host is the failure this stage exists to prevent.

### 2.3 `ingest.acquire` — the cache

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.acquire
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.acquire --only cbp_zip
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.acquire --force
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.acquire --include-large
```

Reads the registry, writes `data/raw/<source>/<hash>.<ext>` and appends to
`data/raw/manifest.jsonl`. Writes `outputs/metrics/acquire_report.json`.

Last run: `fetched 0 | cached 5 | skipped 8 | failed 0`, 11.2 MB on disk. The
five are the open bulk files; the eight skips each carry a reason and a
remediation rather than being silent.

Two design points worth knowing:

- **Vintages are pinned per source, not globally.** `VINTAGE_BY_SOURCE` in
  `acquire.py` exists because publishers disagree: CBP files its 2022
  reference year under `/2022/zbp22totals.zip`, the Gazetteer publishes a
  2023 edition. A single global year is wrong for at least one of them, and
  getting it wrong produces a 404 rather than bad data — see
  `LOGGING.md` §6 for that exact failure, preserved in the logs.
- **Some sources are one file per year.** `bps_county` declares
  `vintages=("17".."25")` and the acquire loop fetches each. That is what
  makes a year-on-year permit feature possible at all; a single vintage
  yields an all-null column, which is what happened before the change.

`data/raw/` after a full run. **Re-measured 2026-09-14 with `du -sh`: the
total is 2.1 GB across eighteen directories, not the 16 MB across eight this
table used to report.** The eight below are what `ingest.acquire` fetches; the
other ten arrived by hand or from a separate module, and three of them are
larger than everything `acquire` downloads put together.

| Directory | Size | Files | How it got there |
|---|---|---|---|
| `osha_bulk` | **1.4 GB** | 3 | `scripts/osha_amazon.py`, manual |
| `tiger_zcta` | **504 MB** | 1 | manual |
| `cbp_zip_detail` | **119 MB** | 7 | manual, see `../data/CBP_DETAIL.md` |
| `geofabrik` | **50 MB** | 1 | manual, Rhode Island only |
| `zcta_county_xwalk` | 6.6 MB | 1 | `acquire` |
| `acs5_2023` | 3.5 MB | 1 | `acquire` |
| `bps_county` | 2.3 MB | 9 (one per year, 2017–2025) | `acquire` |
| `osm_landuse` | 1.2 MB | 1 | `ingest.osm_landuse` cache, see `../data/OSM_LANDUSE.md` |
| `gaz_zcta` | 992 KB | 1 | `acquire` |
| `eia_electricity` | 972 KB | 2 (API pages) | `acquire` |
| `mwpvl` | 852 KB | 1 | manual |
| `cbp_zip` | 808 KB | 1 | `acquire` |
| `eia_diesel` | 316 KB | 1 (API page) | `acquire` |
| `cbsa_county` | 144 KB | 1 | `acquire` |
| `osm_amazon` | 48 KB | 3 | manual |
| `acs1_2023` | 32 KB | 1 | `acquire` |
| `acs5`, `eia_prices` | 0 | 0 | empty, created by `paths.ensure_dirs()` |

Two of the eight `acquire` rows had drifted as well: `eia_electricity` was
recorded as 1.8 MB / 3 files and is 972 KB / 2; `eia_diesel` was 636 KB / 2
and is 316 KB / 1.

### 2.4 `ingest.external` — validating what arrived by hand

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.external --check
```

Five sources cannot be fetched from this environment and are placed manually
into `data/external/`: four public downloads totalling 214 MB, plus the
facility panel, which no publisher issues and which was compiled here from
the public OSHA inspection extract. This stage answers one question before
anything depends on them: is what landed actually usable? It writes
`experiments/superseded-artefacts/external_check.json` and **exits non-zero if the facility
panel is not ready**.

Last run:

```
  facility_panel    ok        43 facilities, 2015-2025, 1 operator(s)
  zillow_zori       ok        9.5MB
  zillow_zhvi       ok        117.4MB
  ejscreen          ok        48.3MB
  bls_oes           ok        38.1MB
  eia_prices        missing   not placed yet
```

Exit code 0. Before 2026-09-13 the first line read
`!facility_panel  suspect  146B` and the stage exited 1; if you see that,
the panel file is missing or truncated.

`eia_prices` shows `missing` and that is correct but misleading: the EIA data
is acquired through the v2 API (2.6), not by hand, so no file is expected in
`data/external/eia_prices/`. The registry entry and the manual-source
expectation describe the same source twice.

The facility panel gets column-level validation because it is the target
variable: required columns, a check that ZIP codes still carry their leading
zeros, numeric `open_year`, recognised `facility_type`, and a count of rows
with no `source_url`. There is a size floor in front of all of that, because
a header-and-nothing-else file used to be the common failure and it is
cheaper to reject on bytes than to parse it.

### 2.5 The two keyed API stages

These are separate modules because an API behaves unlike a bulk file.

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.census_api --acs1
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.eia_api
```

**Census (`ingest.census_api`).** Pulls ten ACS variables plus two margins of
error. Last run: **ACS5 33,772 ZCTAs × 16 columns; ACS1 530 metros × 5
columns**, 2023 vintage. Three publisher quirks are absorbed here:

- the endpoint answers a missing key with an HTML page and HTTP 200, so the
  fetch asserts on `Content-Type`;
- unavailable cells are large negative sentinels (`-666666666` and five
  others), not nulls, and are mapped to missing;
- median home value is censored at $2,000,001 / $9,999 and median income at
  $250,001 / $2,499. Those are censoring codes, not measurements, and each
  gets a `_topcoded` or `_bottomcoded` boolean — declared in
  `common/sentinels.py`, never editing the value — so downstream code *can*
  treat them as bounds. Nothing downstream does. See §3.4.

**EIA (`ingest.eia_api`).** Industrial retail electricity by state and No.2
diesel by PADD region, monthly, joined to one row per state-month. Last run:
**4,992 state-months across 52 states**, diesel coverage 98.1%, latest month
2025-12. The API pages at 5,000 rows *silently* — a request for more returns
5,000 rows and a 200 — so the extractor follows offsets rather than trusting
one response.

Both write directly into `data/interim/`, which means they are labelled L0
but produce an L1 artefact. That is a real inconsistency in the layer
tagging, not a subtlety: a `traced_layer("L0", ...)` block writing a typed
parquet will read oddly in the logs.

**The `.env` gap, now closed.** `acquire.py` used to import `http.api_key`,
which reads `os.environ` directly, without ever calling
`config.load_dotenv()` — so a default `make acquire` reported
`acs5 SKIP needs $CENSUS_API_KEY` even with the key sitting in `.env`. Its
`main()` now calls `config.load_dotenv()` before anything reads the
environment, and the skip reasons for `acs5` and `acs1` are the honest ones
(`acquired by python -m siting_atlas.ingest.census_api, not by a plain GET`).

---

## 3. L1 — normalise

**Contract:** one typed parquet per source. CSV, TSV, fixed-width and zipped
text never appear downstream of this line.

The single most important rule in the layer: **ZIP and ZCTA codes stay
zero-padded strings.** As an integer `01890` becomes `1890` and every join
silently loses those rows.

Two modules, split by file size rather than by source type.

### 3.1 `ingest.normalise` — the fetched sources

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.normalise
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.normalise --only cbp
```

Reads `data/raw/` and the ZORI file in `data/external/`; writes
`data/interim/*.parquet` and `outputs/metrics/normalise_report.json`.

```
  6/6 normalised -> data/interim
    gazetteer               33,791 rows
    cbp                     35,002 rows
    building_permits        15,812 rows
    zcta_county             33,791 rows
    cbsa_county              1,915 rows
    zillow_zori            456,917 rows
```

*`cbsa_county` was added to `NORMALISERS` after this block was written and
the count was not updated; `outputs/metrics/normalise_report.json` has six
results. Corrected 2026-09-14.*

What each one absorbs:

| Source | Quirk handled here |
|---|---|
| `gazetteer` | tab-separated inside a zip, latin-1, whitespace in the header row |
| `cbp` | 35,002 ZIP codes — more than there are ZCTAs, because point ZIPs and retired vintages are included. Filtering happens at L2, not here |
| `building_permits` | two merged header rows then a blank line, so names are assigned positionally; nine annual files concatenated and de-duplicated to one row per county-year. 3,043 counties, 2017–2025 |
| `zcta_county` | pipe-delimited with a BOM; a ZCTA can span counties, so the dominant county by shared land area is kept |
| `zillow_zori` | wide month-per-column becomes long `(zcta, month, rent_index)` |

Note the shape of the ZORI figure: 456,917 rows over **8,547 unique ZCTAs**.
Zillow covers about a quarter of the country's ZCTAs and that coverage is
urban, which is the reason the panel carries an explicit `rent_observed`
column rather than letting absence be inferred.

### 3.2 `ingest.normalise_external` — the three large manual files

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.normalise_external
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.normalise_external \
    --only ejscreen_tract
```

Separated because these are the biggest inputs in the project — a 117 MB CSV,
a 38 MB zipped workbook, a 48 MB zipped CSV — and each is trimmed *before* it
is reshaped rather than after.

```
  3/3 normalised -> data/interim
    zillow_zhvi          3,435,525 rows
    bls_wages                1,571 rows
    ejscreen_tract          86,082 rows
```

- **ZHVI** is cut to 2015-01 onward while still wide. Melting all 318 months
  would build roughly 8 million rows to then discard most of; ZORI starts at
  2015-01, so anything earlier cannot be joined to anything.
- **OES** keeps four occupation codes out of roughly 830, plus the
  all-occupations row as a denominator. It is the slowest step in L1 at about
  26 seconds, because it reads an xlsx.
- **EJScreen** reads 10 of 230 columns via `usecols`.

### 3.3 `data/interim/` after both modules

**Fifteen parquets, 590.6 MB, 4,375,527 rows**, re-measured 2026-09-14. This
table used to say "twelve parquets, 61 MB, 4,139,700 rows" and then list
eleven. Four were missing, and one of the four is 89% of the total size.

| Parquet | Rows | Cols | MB | Grain |
|---|---|---|---|---|
| `zcta_geom` | 25,022 | 3 | **525.82** | ZCTA polygon |
| `zillow_zhvi` | 3,435,525 | 7 | 47.05 | ZCTA-month |
| `ejscreen_tract` | 86,082 | 11 | 6.64 | tract |
| `zillow_zori` | 456,917 | 7 | 5.86 | ZCTA-month |
| `acs5_zcta_2023` | 33,772 | **18** | 1.42 | ZCTA |
| `gazetteer` | 33,791 | 5 | 1.17 | ZCTA |
| `cbp_detail` | 210,745 | 6 | 1.10 | ZIP-year-industry |
| `cbp` | 35,002 | 6 | 0.62 | ZIP |
| `zcta_county` | 33,791 | 3 | 0.55 | ZCTA |
| `building_permits` | 15,812 | 6 | 0.16 | county-year |
| `cbsa_county` | 1,915 | 8 | 0.06 | county |
| `bls_wages` | 1,571 | 9 | 0.04 | metro-occupation |
| `eia_energy` | 4,992 | 7 | 0.03 | state-month |
| `acs1_metro_2023` | 530 | 5 | 0.02 | CBSA |
| `osm_landuse` | 60 | 3 | 0.00 | ZCTA (smoke test only) |

Three things the old table hid:

- **`zcta_geom` is 526 MB**, five times everything else in the directory
  combined, and it is what made the "61 MB" figure and
  `DATA_ENGINEERING.md` §1's disk projections wrong.
- **`acs5_zcta_2023` has 18 columns, not 16** — the four ACS censoring flags
  were added by `common/sentinels.py`. See §3.4.
- **`cbp_detail` and `osm_landuse` are not registered sources.** Neither is in
  `ingest/sources.py` or `data/raw/manifest.jsonl`; both are run by hand. See
  [`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md) §6 and
  [`../data/OSM_LANDUSE.md`](../data/OSM_LANDUSE.md).

**And one contract violation this section states and does not check.** §3
opens with "CSV, TSV, fixed-width and zipped text never appear downstream of
this line". `data/interim/` holds `nlrb_amazon.csv` and `osha_amazon.csv`.
The rule is right; it is not enforced and it is being broken.

### 3.4 The quality flags, which no other section mentions

`common/sentinels.py` declares the substitute codes each source uses and
`warehouse/flag_gate.py` fails the build if one is computed and does not reach
the panel. Seven flags survive to `panel.parquet`:

```
  median_home_value_topcoded           83 ZCTAs
  median_home_value_bottomcoded        20
  median_household_income_topcoded     86
  median_household_income_bottomcoded  23
  rent_observed                     1,928
  wage_suppressed                       0   (nothing was withheld in this extract)
  open_quarter_imputed                433
```

Six of those seven are the new columns behind the panel's move from 44 to 50;
`rent_observed` predates the gate. `panel_report.json` `quality_flags` records
six `computed` and zero `dropped`, because `rent_observed` is derived inside
`panel_sql.py` rather than in an L1 parquet, so there is no upstream artefact
for the gate to compare it against. Panel columns ending in a flag suffix:
seven. Flags the gate is watching: six.

**No model or cost function conditions on any of them.** See
[`../data/DATA_QUALITY.md`](../data/DATA_QUALITY.md) F2 for why that makes
this provenance rather than repair.

---

## 4. L2 — warehouse

**Contract:** one parquet per publisher, each on its own grain, becomes a
Kimball star schema with the grains pinned down once.

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.schema
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.schema --show
```

Reads `data/interim/`; writes `data/processed/siting_atlas.duckdb` (27 MB)
and `outputs/metrics/warehouse_report.json`. Idempotent — `CREATE OR REPLACE`
throughout. Runs in about 6 seconds.

```
  5 tables -> data/processed/siting_atlas.duckdb
    dim_zcta              33,791 rows
    dim_county             3,211 rows
    dim_date                  32 rows
    dim_scenario               1 rows
    fact_zcta_year       270,328 rows
```

| Table | What it is |
|---|---|
| `dim_zcta` | the spine. One row per ZCTA in the 2020 Gazetteer, with county, state and a nullable metro label |
| `dim_county` | 3,211 counties, names unioned from BPS and CBP because neither alone covers the crosswalk |
| `dim_date` | quarterly calendar, 2018Q1–2025Q4 |
| `dim_scenario` | the replay key: weight version, mutation id, seed. Seeded with one `default` row |
| `fact_zcta_year` | 33,791 × 8 years = 270,328 rows |

Three decisions embedded in the SQL, each defensible and each worth knowing
before reading a number off the warehouse:

1. **The Gazetteer is authoritative for which ZCTAs exist.** CBP knows about
   35,002 ZIP codes, which is more than there are ZCTAs. Joining outward from
   the Gazetteer is what keeps point ZIPs out of the spine.
2. **State comes from the county FIPS prefix, not from CBP.** CBP supplies a
   state abbreviation, but only for the 30,928 ZCTAs with a business
   establishment; the remaining 2,863 are rural and would otherwise lose
   their EIA energy price.
3. **`dim_scenario` carries no data yet.** It exists so that a published
   number can later be traced to the weights, mutation and seed behind it.
   Adding the column after the facts are written would mean rewriting every
   row.

The stage warns, but does not fail, when a ZCTA has no county in the
crosswalk. That is one of the places a real data contract belongs.

**`dbt/` has been deleted** — updated 2026-09-14; this paragraph used to say
it was "an empty skeleton" with `models/staging`, `models/marts`, `macros`
and `seeds` as empty directories. There is now no `dbt` directory at all. The
L2 design in `DATA_ENGINEERING.md` §4 specified dbt; what was built is SQL
inside a Python module, logged statement by statement through `common.db`.
`make warehouse` used to run `cd dbt && dbt build` and fail; it now runs
`python -m siting_atlas.warehouse.schema` and works. Nothing in the repository
shells out to dbt and nothing is going to.

---

## 5. L3 — the feature panel

**Contract:** one parquet, one grain, and every model reads it and nothing
else.

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.panel
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.panel --coverage
```

Reads the warehouse and the optional L1 parquets; writes
`data/processed/panel.parquet` (14 MB) and
`experiments/superseded-artefacts/panel_report.json`. Takes about 6 seconds.

`panel.run()` also calls `facilities.attach(db)` unconditionally, which is
the seam the whole project used to wait on. `warehouse/facilities.py` (250
lines, 19 tests) converts a delivered `facilities.csv` into the `enabled`
target, so **the switchover needed no code changes**: absent file → WARNING
and `enabled` stays NULL, malformed file → error logged and the user pointed
at `ingest.external --check`, valid file → target populated. On 2026-09-13
the third branch became the live one and not a line was edited. Only `DS`
and `SDC` enable a ZIP (an `FC` is a regional node), catchment is a 15/10-mile
radius standing in for a drive-time isochrone, and pre-2018 facilities are
kept as left-censored rather than dropped.

What that yields on the 43-row panel:

```
  43 delivery stations -> 1,257 ZCTAs ever enabled
                          27,914 of 1,081,312 cells TRUE   2.58%
  of the 43:  2 in the held-out metros (Phoenix, Boise)
              2 opened before 2018Q1     -> left-censored
             39 usable events across 8 fitting metros
             (a 9th, Nashville, is in scope and has none)
```

`hazard_report.json` reports 38 rather than 39, because
`diagnostics.usable_facilities()` filters on `open_year > 2018` and so drops
DS-022 (Lisle IL) which opened in 2018**Q3** — inside a panel that starts
2018Q1. The 38 is a conservative off-by-one, not a different definition.

The radius is the assumption with the most leverage, so it was measured.
Over the 2,413 ZCTAs in the ten pilot metros, the share ever enabled is
36.2% at 10 miles, **51.0% at the configured 15 miles**, and 63.4% at 20.
Any finding that flips between 10 and 20 miles is a finding about the
radius.

```
  panel -> data/processed/panel.parquet
    1,081,312 rows x 50 columns
```

*44 until 2026-09-14, when the six quality flags of §3.4 were carried through.
`experiments/superseded-artefacts/panel_report.json` reports `"cols": 50`.*

Grain is **one row per ZCTA per quarter**: 33,791 × 32 quarters. The proposal
estimated 811,000 rows for a ZCTA-week panel over ten metros; what was built
is national and quarterly instead. Quarter rather than month because the
slowest input that actually moves (rent) is noisy monthly; quarter rather
than year because a decision made in Q1 should not see Q4 information.

**Dense, not sparse.** Every ZCTA gets every quarter whether or not any
source observed it. Filtering to observed rows would hand the model a
sample-selection bug, because the best-covered sources — Zillow, BPS — are
the urban ones.

### 5.1 Three kinds of column

- **levels** — ACS 2023 and CBP 2022, repeated down the quarters. Pinned
  vintages, not a time series.
- **rates of change** — `rent_index_yoy_pct`, `permits_yoy_pct`. These are
  what distinguish a growing ZCTA from a large one.
- **availability** — `rent_observed`, 100% populated by construction, so a
  model can condition on coverage instead of confusing it with a low rent.

`siting_atlas.warehouse.optional` attaches the three sources that arrive on a
separate ingest track. A source whose schema does not resolve confidently is
skipped with a warning rather than guessed at: a missing column is obvious in
the coverage report, a wrong join is a plausible number nobody questions. All
three joined on the last run, contributing **12 of the 50 columns**
(`panel_report.json` `optional`: `home_value`; `metro_employment` and the four
wage columns plus `wage_suppressed`; `pm25`, `diesel_pm`,
`traffic_proximity`, `low_income_pct`, `people_of_colour_pct`).

### 5.2 Coverage, which is the honest part

`--coverage` prints percent non-null for all 50 columns. Re-read from
`experiments/superseded-artefacts/panel_report.json` on 2026-09-14; four rows below had drifted
and are corrected.

| Column | Non-null | Why |
|---|---|---|
| `zcta`, `year`, `quarter`, `state`, `county_geoid` | 100% | the spine |
| `population`, `households`, `owner_occupied`, `renter_occupied`, `bachelors_degree`, `in_labor_force`, `vehicle_availability_total` | 99.94% | ACS suppresses a handful of ZCTAs |
| `median_age` | 97.09% | ACS, suppressed more often than the counts |
| `median_household_income` | 90.61% | as above; **the census-code flags of §3.4 apply to the 86 ZCTAs at $250,001** |
| `median_home_value` | 89.70% | as above |
| `establishments`, `employment`, `annual_payroll` | 91.53% | CBP only knows ZCTAs with a business |
| `electricity_cents_kwh`, `diesel_usd_gal` | 99.56% | state-level, so near-complete |
| `traffic_proximity`, `low_income_pct`, `people_of_colour_pct` | 99.95% | EJScreen, tract mapped to ZCTA |
| `diesel_pm` | 99.22% | EJScreen |
| `pm25` | 98.55% | EJScreen. **Coverage only — `pm25` is CONSTANT across the 32 quarters in all 33,791 ZCTAs (0 carry more than one distinct value). So are `diesel_pm`, `traffic_proximity`, `low_income_pct`, `people_of_colour_pct` and `median_home_value`. Do not read any coverage figure in this table as evidence that a longitudinal design on that column is feasible; the only outcome column that varies through time is `home_value`, in 26,262 ZCTAs. Measured 2026-09-14 on `data/processed/panel.parquet`; see [`../ALTERNATIVES.md`](../ALTERNATIVES.md) §D.1** |
| `permit_units_total` | 65.44% | nine BPS vintages; the reporting universe widens from ~745 counties to ~3,021 in 2022 |
| `permits_yoy_pct` | 55.44% | LEFT JOIN on year−1, so a county with no prior-year row yields NULL rather than a fabricated spike |
| `home_value` (ZHVI) | 74.90% | broader than ZORI |
| `cbsa_code`, `cbsa_title` | 74.05% | the metro key most code actually joins on |
| `metro_employment` and the four wage columns | 55.32–55.35% | OES is metro-grain, mapped through `cbsa_code` |
| `metro` | 25.09% | a *different, sparser* metro label from `dim_zcta`; do not confuse it with `cbsa_code` |
| `rent_index` | 11.23% | ZORI covers 8,547 ZCTAs |

*The old table compressed the last three rows into one — "`metro` and the
five wage columns | 16.7–25.1%" — which understated wage coverage by more than
a factor of two and hid that there are two different metro columns with very
different coverage. It also gave EJScreen as 97.7–99.1% against a measured
98.55–99.95%, and folded seven ACS columns at 99.94% together with three at
89.70–97.09%.*
| **`enabled`** | **100.0%** | **the target variable. Non-null everywhere because it is a populated boolean, not a sparse column — of which 2.58% are TRUE. Low because the grid is national and the 43 facilities are in nine metros; 51.0% of pilot-metro ZCTAs are ever enabled. See §7.** |

A reader should take the bottom rows seriously. A model fitted on
`rent_index` today would be fitted on an eighth of the country, and that
eighth is not a random eighth.

Two discontinuities in the permits series look like bugs and are not — the
county universe widening in 2022, and Connecticut swapping counties for
planning regions in 2023 while the crosswalk keeps the old codes. Both are
written up in [`../data/bps_county.md`](../data/bps_county.md) under Notes.

---

## 6. L4 and L5 — built

Both layers now exist and both are entered. Every Makefile target names a
module that is really there; the ones that pointed at `warehouse.features`,
`cost.od_matrix`, `models.run`, `app/main.py` and a dbt project have been
removed rather than left to mislead.

| Makefile target | Runs |
|---|---|
| `make cost` | `cost.runner` — cost to serve per pilot ZCTA |
| `make optimize` | `optimize.runner --budget 2e9` |
| `make scope` | `report.scope` → `outputs/metrics/scope.json` |
| `make figures` | `viz.build` → `outputs/figures/*.png` |
| `make app` | `scripts/run_dashboard.sh` (Streamlit; blocks) |
| `make all` | the offline pipeline, L1 through L5 |

### 6.1 L4 — cost

`cost/params.py` (frozen assumptions), `cost/daganzo.py` (the continuous
approximation), **`cost/depots.py`** (the depot network — see §6.2) and
`cost/runner.py` (the stage). Output
`outputs/tables/cost_to_serve_<yr>q<q>_<scenario>.parquet`, one row per pilot
ZCTA, plus `outputs/metrics/cost_report.json`.

Last run, `outputs/metrics/cost_report.json` run **`20260916-024154-0aa8`**:
**2,333 pilot ZCTAs** (2,413 minus 80 with no households), median
**$1.08/parcel**, p10 $0.98, p90 **$1.42**, **78,292 vans/day**,
**$14.00 m/day**. Read `total_vans`, `total_daily_cost_usd` and
`median_cost_per_parcel` from the artefact rather than from this line — the
p-median rewrite of §6.2 moved four of the five.

*Corrected 2026-09-14. This line read "median $1.09, p10 $0.99, p90 $1.36,
$14.09 m/day" against the pre-p-median run. The p90 is the one that matters:
it moved 4.0%, from $1.36 to $1.42, so the old figure overstated how tight
the distribution is.*

*The five-scenario spread is reproducible again as of 2026-09-16. This note
used to say it was not: `cost_report.json` held only the `baseline` key and
the four other scenario parquets predated the p-median rewrite. All five were
re-run on the current depot network (parquets 2026-09-15 19:42, report
`20260916-024154-0aa8`), and on median cost per parcel the spread recomputes
to **−17.1% (`dense_routing`) to +4.4% (`congested`)** — the same figures this
section carried before, now re-derived rather than remembered.*

*(This line said 79,484 vans/day until 2026-09-13. That is the pre-fix
figure: `vans_required` was rounded up per ZCTA and then summed, which
invents 1,192 vans. `cost/runner.py` reports `ceil(sum(van_days))`. See
`../DECISION_LOG.md` §2.6.)*

### 6.2 `cost/depots.py` — the correction worth reading

The first cost model put **one** depot per metro at the population-weighted
centroid, and its docstring asserted the choice barely mattered. That
assertion was measured and was wrong by roughly twentyfold: implied line
hauls ran 0.4 to 145.7 miles, and at **$0.018** per parcel per line-haul mile
(`cost/depots.py:7`) the depot assumption alone injected up to **$2.62/parcel**
into a ranking whose median was $1.51. The model was substantially ranking
distance-from-metro-centre, an artefact, rather than cost.

It now solves a depot *network*: K depots per metro, with
`K = ceil(metro daily parcels / 40,000)`. The throughput figure makes K an
external check rather than a free parameter — it implies **334 depots across
11 CBSAs** for 13,152,992 daily parcels (39,380 per depot), and Amazon alone
runs roughly 700–900 US delivery stations against a pilot holding 17.6% of US
population, so ~250–320 for all operators is the right order of magnitude.

**Placement is p-median, not k-means, and there is no seed. Corrected
2026-09-14.** This paragraph used to read "parcel-weighted k-means …
Placement is seeded (`RANDOM_STATE = 20260912`)". Both halves are now false:
`cost/depots.py` has a section headed *"Why it is no longer k-means"* and
`solve_pmedian()` does greedy-add plus interchange, and `grep -n RANDOM_STATE
src/siting_atlas/cost/depots.py` finds nothing because the algorithm is
deterministic and has no seed to pin. The argument for the change is that
`daganzo.py` bills line haul linearly in distance, so the minimiser is the
weighted median, not the weighted mean — k-means optimised one objective
while the model charged for another. Across the pilot the switch removes 9.3%
of billed parcel-miles and moves the ZCTA ranking by Spearman rho 0.888. It is
also the cause of the portfolio moving from 330 activations to 282; see
[`../data/PARAMETERS.md`](../data/PARAMETERS.md) §9.1.

Line-haul p90 fell from 60.2 to **12.44 miles**; the median is 4.02 and the
maximum 82.92, in Boise, which is a genuinely remote ZCTA rather than an
artefact. *(10.05 / 3.96 / 86.03 until 2026-09-14 — the pre-p-median figures.)*
The pilot spans 11 CBSA codes and not 10, because the
"San Francisco Bay Area" label covers both the San Francisco–Oakland–Fremont
and San Jose–Sunnyvale–Santa Clara CBSAs.

### 6.3 L4 — optimize, models, agent

- `optimize/` — `params.py`, `objective.py`, `select.py`, `runner.py`,
  `montecarlo.py`. Maximises NPV at an assumed contribution margin. Because that margin is
  unobservable, `--frontier` solves across a range of it and `--margin`
  defaults to the break-even of a full-budget portfolio, a self-referential
  anchor rather than a guess. At a $2bn budget it funds **fewer than the 500**
  possible activations, leaving part of the budget unspent because the rest
  lose money — a result the earlier break-even-minimising objective could not
  express, since that one was minimised at a portfolio of **one**. Reports an
  achieved value against a computed upper bound rather than claiming a
  `(1 − 1/e)` guarantee, which does not hold for an objective with both
  positive and negative interactions.

  **Read the counts from the artefact, not from this bullet.**
  `experiments/portfolio-optimiser/artefacts/portfolio_report.json` carries `run_id`, `detail.n`,
  `detail.capital` and `optimality_gap`. The headline has now moved three
  times: 317 / $1.268bn / gap 13.03%, then 330 / $1.320bn / $680m unspent /
  gap 13.39%, and as of run **`20260914-002431-7419`** **282 / $1.128bn /
  $872m unspent / gap 10.73%**. **The cause of the last move is now known**
  and it is not in `optimize/`: it is the k-means-to-p-median rewrite of
  `cost/depots.py` (§6.2), documented in
  [`../data/PARAMETERS.md`](../data/PARAMETERS.md) §9.1. Parameter
  uncertainty does not explain it —
  [`../data/UNCERTAINTY.md`](../data/UNCERTAINTY.md) §3 puts 282 at the 68th
  percentile of 500 joint draws on the current solver and 330 at the 97th.

  `montecarlo.py` is the module that established that: 500 joint draws over
  twenty-one of the twenty-four parameters, writing
  `experiments/portfolio-optimiser/artefacts/montecarlo_report.json` and
  `outputs/tables/montecarlo_draws.parquet`. It takes about 76 minutes.
- `models/` — twenty-three modules as of 2026-09-14, of which the hazard
  apparatus (`risk_set.py`, `timebasis.py`, `hazard.py`) is **retired** and
  the conditional choice model is the successor: `choice.py`,
  `choice_runner.py`, `choice_conformal.py`, `choice_inference.py`,
  `choice_sandwich.py`, `choice_bootstrap.py`, `accessibility.py`,
  `coeftable.py`. Also `panel_source.py`, `fixtures.py`, `splits.py`,
  `base.py`, `metrics.py`, `conformal.py`, `conformal_report.py`,
  `console.py`, `diagnostics.py`, `sensitivities.py`, `truthy.py`,
  `runner.py`. *(This list named ten modules until 2026-09-14 and did not
  mark the hazard ones as retired. Run `ls src/siting_atlas/models/` rather
  than trusting it — the choice modules are being added to actively.)*
  One code path, two inputs: `load_panel()`
  returns the real panel only if `enabled` has at least one `True`, and
  otherwise a labelled synthetic fixture with `SYN-` unit ids, a console
  banner and `SYNTHETIC_`-prefixed artefacts. **The fixture branch is no
  longer taken.** `enabled` has 27,914 `True` cells, the runner reads the
  real panel, and there are no `SYNTHETIC_*` files left anywhere in
  `outputs/`. `hazard_report.json` carries `"synthetic": false`.

  **And the model fitted on that real panel does not work.** Brier 0.019522
  against the null's 0.019614 over the same 8,044 rows; ECE 0.00863 against
  the null's 0.00005, so it is *worse calibrated than a constant*; AUC 0.6894
  against 0.5000; out of time the null wins outright, 0.020635 against
  0.020213 over 11,871 rows. This paragraph used to quote Brier **skill**
  (+0.0047 / -0.0209 / -0.0618); report the raw pair instead, per Gneiting &
  Raftery (2007) §2.3 p.362 — skill scores are generally improper even when
  the underlying rule is proper. The -0.0618 geographic figure is dropped
  entirely: `hazard_report.json:819` calls it a smoke test, Phoenix and Boise
  holding two dated stations between them, and it is not a transfer result.

  **The cause is the unit of analysis, not the sample size.** A ZCTA-quarter
  is not a decision — one station switches on a median of 58 ZCTAs at once —
  so the 812 events in the risk set are 28 to 38 decisions plus geometry, and
  Train (2009) §3.7.1 p. 61 requires observations to be independent of one
  another.
  [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §14.2 is canonical, carries
  that corrected citation, and rejects the sample-size
  reading; [`../adr/0004-model-change-conditional-choice.md`](../adr/0004-model-change-conditional-choice.md)
  records the change of specification. The successor is still under-powered
  (7.6 decisions per parameter against a floor of 10), so it is valid rather
  than precise.

  This block used to read "every model number in the repository is about the
  estimator code, not the world". That is no longer true, and the number that
  is now about the world is a negative one. See
  [`../STATUS.md`](../STATUS.md).
- `agent/` — `types.py`, `base.py`, `gates.py`, `gates_data.py`,
  `gates_inference.py`, `estimators.py`, `pipeline.py`, `warehouse_view.py`,
  `runner.py`. *(Four modules until 2026-09-14; the gates were split.)* The
  six gates are still six, but they now live in `gates_data.py` (SchemaGate,
  GeocodingGate, ConfidenceGate, AuditLogGate) and `gates_inference.py`
  (DonorPoolIntegrityGate, EstimateStabilityGate), assembled by
  `pipeline.GatePipeline`. They run against real warehouse state and write an
  audit record
  for every invocation, rejections included. Gates 5 and 6 now have a donor
  pool to work with, but it is a thin one, so gate 5 escalates often in the
  metros with few rows — the demo mutation is escalated to a human, which is
  correct behaviour rather than a defect. No ingest stage imports this; it is
  a parallel write path.

### 6.4 L5 — report and surfaces

`report/scope.py` writes `outputs/metrics/scope.json`, which every document
reads its headline figures from instead of retyping them. `viz/build.py`
renders four PNGs per scenario (20 across the five) and exits non-zero if a
label had to shrink past its floor. `app/dashboard.py` is a Streamlit front
end over the same chart functions, so the app and the printed figures cannot
disagree.

`tools/` builds the proposal, deck, figures and the plain-text twins of these
documents. It is the documentation toolchain, not the pipeline.

---

## 7. The target variable — formerly the blocker

```
data/external/facility_panel/facilities.csv            4.7 KB,  43 rows
data/external/facility_panel/national_facilities.csv  17.1 KB, 104 rows
```

**The second line was missing from this document entirely until 2026-09-14,
and it is the one the current model is fitted on.** `facilities.csv` is the
ten-metro pilot panel that the retired hazard model used. `national_facilities.csv`
is the national panel behind the conditional choice model — 104 Amazon
delivery stations across 62 CBSAs, 100 of which survive the declared edits at
load, giving 94 fitted decisions. A reader of §7 alone would previously have
concluded that 43 rows is all the target data that exists. Its own defects are
in [`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md);
the sharpest is that `open_year` equals the quarter of the earliest OSHA
inspection for **104 of 104 rows**, so it is an upper bound throughout and not
an opening date. See [`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md) §5.2 for
what that does to the warehousing covariate, and
[`../data/SATELLITE.md`](../data/SATELLITE.md) for the failed attempt to
supply the missing lower bound.

The rest of this section is about `facilities.csv`.

For most of this project that line read `146 bytes` — a header row and no
data — and it was the one thing standing between a working pipeline and a
fitted model. The history is kept here because it explains the shape of the
code: `warehouse/facilities.py` was written, tested and wired in *before*
the data existed, precisely so that the day it arrived cost nothing.

It arrived on 2026-09-13. `ingest.external --check` exits 0 and reports
`facility_panel ok  43 facilities, 2015-2025, 1 operator(s)`.

`data/external/facility_panel/TEMPLATE.csv` still sits beside it showing the
expected shape with three illustrative rows; `ingest.external` deliberately
excludes any file named `TEMPLATE.csv` from discovery, so a run cannot
"succeed" on three fake facilities.

Required columns (`ingest/facility_check.FACILITY_REQUIRED`): `facility_id`,
`operator`, `facility_type`, `city`, `state`, `zip`, `open_year`,
`source_url`, `source_type`. Optional (`FACILITY_OPTIONAL`): `latitude`,
`longitude`, `open_quarter`, `close_year`, `close_quarter`, `square_feet`,
`status`, `confidence`, `site_address`. *(`close_year`, `close_quarter` and
`site_address` were missing from this list until 2026-09-14. All three are
declared in the code and all three are present in the delivered file.)*

**What the file is, stated so nobody over-reads it.**

```
  rows            43, one per building, all Amazon, all facility_type DS
  years           2015-2025
  usable events   39   (43 less 2 held-out metros, less 2 pre-2018Q1
                        openings carried as left-censored)
  closures        1    Chicago 2801 S. Western Ave (DCH1), closed 2021
  metros          Seattle 11 | Chicago 8 | Bay Area 7 | New York 6
                  Denver 6 | Miami 2 | Austin 1 | Nashville 0
                  Phoenix 1 and Boise 1, both held out
  dates           mostly "operating by" UPPER BOUNDS from OSHA
                  inspection records, not opening dates
```

Three consequences a reviewer should hold onto:

- **The coverage is uneven and that unevenness is not a finding.** Seattle
  contributes a quarter of the panel because Washington runs an unusually
  active state-plan OSHA programme, not because Amazon builds more there.
  Nashville is a *fitting* metro with zero events, because all five of its
  OSHA addresses are fulfilment centres. Do not smooth this into an average.
- **The bound is correct and often loose, and that has been measured.** Five
  addresses appear in both MWPVL's 2012 census (which states real opening
  months) and the OSHA extract. The bound held 5 of 5 — no inspection
  predates an opening — but the lag was 4, 13, 57, 69 and 345 months. One
  site opened in 1997 and was first inspected in 2026. So the panel supports
  *which ZIPs* far better than *when*.
- **There are no `SYNTHETIC_*` artefacts left.** The prefix check this
  document used to recommend now has nothing to catch: every file in
  `outputs/` is real. What you must check instead is the *result*, which is
  negative — see [`../STATUS.md`](../STATUS.md).

Provenance, the four collection methods that failed first, the quantified
selection bias and the defects still in the delivered file are in
[`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md),
which also carries a from-scratch rebuild recipe in its §15. The raw inputs
are in the repo under `data/raw/osha_bulk/`, `data/raw/osm_amazon/` and
`data/raw/mwpvl/`, each with a `data/raw/manifest.jsonl` entry and SHA-256;
the collection working files are under `data/collection/`.

---

## 8. Running the whole thing

Cold, in order. On a warm cache this takes about a minute, dominated by the
OES workbook read.

```bash
cd siting-atlas
export PYTHONPATH=src
PY=.venv/bin/python

# L0 - what can this machine reach today?
$PY -m siting_atlas.ingest.probe

# L0 - bulk files into the content-addressed cache
$PY -m siting_atlas.ingest.acquire

# L0 - the two keyed APIs (these load .env; acquire does not)
$PY -m siting_atlas.ingest.census_api --acs1
$PY -m siting_atlas.ingest.eia_api

# L0 - validate the five manually-placed sources
$PY -m siting_atlas.ingest.external --check      # exits 0 since 2026-09-13

# L1 - typed parquet, one per source
$PY -m siting_atlas.ingest.normalise
$PY -m siting_atlas.ingest.normalise_external

# L2 - star schema
$PY -m siting_atlas.warehouse.schema

# L3 - the panel every model will read
$PY -m siting_atlas.warehouse.panel --coverage
```

To make the whole sequence one auditable run rather than eight unrelated
ones, set a run id first and every stage appends to the same log directory:

```bash
export SITING_ATLAS_RUN_ID=$(date -u +%Y%m%d-%H%M%S)-full
```

See `LOGGING.md` §4.

### 8.1 What a re-run costs

Nothing on the network. `common.http.fetch` keys the cache on the request
identity, so a warm re-run of `acquire` reports `fetched 0 | cached 4` and
completes in under a second. The last full pass reported:

| Stage | Wall clock |
|---|---|
| `acquire` (warm) | 0.26 s |
| `census_api --acs1` (warm) | 1.2 s |
| `eia_api` (warm) | 0.3 s |
| `normalise` | 2.7 s |
| `normalise_external` | 31.3 s |
| `warehouse.schema` | 6.7 s |
| `warehouse.panel` | 5.6 s |

Total on-disk footprint, re-measured 2026-09-14: `data/raw` **2.1 GB**,
`data/external` 215 MB, `data/interim` **564 MB**, `data/processed` 41 MB.
About **2.9 GB** in all.

*This paragraph read "17 MB / 214 MB / 61 MB / 39 MB" and was wrong by two
orders of magnitude on `data/raw`. The growth is `osha_bulk` (1.4 GB),
`tiger_zcta` (504 MB) and `cbp_zip_detail` (119 MB) in raw, and
`zcta_geom.parquet` (526 MB) in interim — all four arrived after the figure
was taken and none of them is the routing work the figure was watching for.*

`DATA_ENGINEERING.md` §1 predicted a ~300–500 MB warehouse and ~15 GB of
pass-through. **Neither holds.** The warehouse is **27 MB**, an order of
magnitude under the projection; the pass-through is 2.9 GB rather than 15 GB,
and it is dominated by OSHA inspection records and TIGER shapefiles rather
than by the road graphs the projection assumed, because the routing work was
never started.

---

## 9. Known divergences from the design documents

Recorded here rather than quietly fixed in prose, because the point of this
repository is that its claims survive checking.

| Design says | Built as |
|---|---|
| L2 is dbt Core → DuckDB (`DATA_ENGINEERING.md` §4) | SQL inside `warehouse/schema.py`; **`dbt/` has been deleted** |
| L3 is an 811k-row ZCTA-week panel | 1,081,312-row ZCTA-quarter panel, national rather than ten metros |
| "eleven public sources" (README, pre-update) | fourteen registered, thirteen analytical |
| `make <stage>` rebuilds any stage | **now true.** All **22** `.PHONY` Makefile targets resolve to modules that exist. *(This row said 15; the count was never right, the claim was.)* |
| Data contracts fail the build on drift | reported, not enforced, **with one exception added since**: `warehouse/flag_gate.py` raises if a computed quality flag does not reach the panel. Otherwise only the facility-panel check exits non-zero |
| `reproducibility/seeds.toml` wired into every stochastic step | done: `models/fixtures.py` draws through `seed("models", "hazard")` and two runs forty minutes apart gave identical coefficients. *(This row also claimed `cost/depots.py` pins k-means at `RANDOM_STATE = 20260912`. It does not: depots are placed by a deterministic p-median solver and there is no `RANDOM_STATE` in that file. See §6.2.)* |
| Census ACS is a level feature source | true, and also censored at both ends: `median_home_value` at $2,000,001 / $9,999 and `median_household_income` at $250,001 / $2,499. All four now carry flags that reach the panel, declared in `common/sentinels.py` and enforced by `warehouse/flag_gate.py`. **No model conditions on them** — see §3.4 |
| EIA is a manually-placed source (`ingest.external`) | acquired through the v2 API. The `external` check reports `eia_prices missing`, which is correct and misleading |
| Every source goes through the registry and the manifest | **two do not.** `ingest/cbp_detail.py` reads seven hand-downloaded `zbp??detail.zip` files and `ingest/osm_landuse.py` queries Overpass; neither is in `ingest/sources.py` or `data/raw/manifest.jsonl`, so neither has a recorded hash or URL. See [`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md) §6 |
| `outputs/models/` is the L4 write target (`common/paths.py:38`, `LOGGING.md` §5) | **empty, and nothing writes it.** `grep -rn "paths.MODELS" src/` finds only the declaration |
| L4 is the model layer | `models/choice_runner.py`, the current model, enters **L5**. `ingest/nlrb_capture.py`, an ingest module, enters **L4**. The layer tag is a convention and nothing checks it |

**Artefacts this document does not describe.** Listed so the omission is
visible rather than discovered: `outputs/metrics/` also holds
`choice_report.json`, `montecarlo_report.json`, `national_panel.json`,
`batch_candidates.json`, `nlrb_coverage.json` and `nlrb_only_cities.json`;
`outputs/tables/` also holds `montecarlo_draws.parquet`,
`portfolio_2023q4.parquet` and `hazard_predictions.parquet`; `outputs/audit/`
holds the gate records; `data/external/` also holds `nlrb/` and `subsidies/`.
The NLRB work is documented at [`../data/NLRB.md`](../data/NLRB.md) and the
Monte Carlo at [`../data/UNCERTAINTY.md`](../data/UNCERTAINTY.md).

Two further notes that belong with the engineering, not the design. **Both
were fixed and the notes were left standing, which is its own lesson** — a
divergence list that records repairs as if they were open defects sends the
next reader to fix something twice:

- ~~**`logs/` is not gitignored.**~~ **Fixed.** `.gitignore` line 32 is
  `logs/`. The directory records every URL and SQL statement — see
  `LOGGING.md` §8.1 — so it is never committed.
- ~~**`ingest.acquire` does not load `.env`.**~~ **Fixed.** `acquire.py:180`
  calls `config.load_dotenv()` before anything reads the environment, which
  §4.1 of this same document already said. The two statements contradicted
  each other for as long as both were in the file.
