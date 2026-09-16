# Data Engineering & Feasibility

**How big is the data really, what will actually break, and how three students on
laptops ship this in eight weeks.**

> **The headline finding, before anything else:**
> **This is not a big-data project.** The data you *model on* is 14 MB and
> 1,081,312 rows — that fits in RAM on a 2015 laptop twice over.
>
> **Corrected 2026-09-14.** This paragraph used to continue: "The data you
> *pass through* is ~15 GB, and almost all of it is one thing: OpenStreetMap
> road graphs for OSRM", and to name OSRM preprocessing as the first
> bottleneck. **Neither happened.** OSRM was never run, no road graph was ever
> downloaded, and the only OSM in the tree is a 50 MB Geofabrik extract that
> `ingest/osm_landuse.py` reads for landuse polygons. Measured pass-through is
> **2.1 GB** in `data/raw/`, dominated by `osha_bulk` (1.4 G) and
> `tiger_zcta` (504 M) — neither of which this document anticipated at all.
>
> The bottlenecks that turned out to be real are (2) and (3) below: API rate
> limits measured in days, and nobody owning the pipeline. (1) was solved by
> deleting the work, which §10 records.

---

## 1. The actual numbers

### 1.1 What you model on — tiny

Measured on 2026-09-12, not estimated; the facility-panel row was remeasured
on 2026-09-13, the day that file was delivered, and the whole table was
re-measured on 2026-09-14. Where a row is still a projection it says so.

| Table | Rows | Size on disk |
|---|---|---|
| **National ZCTA-quarter panel (33,791 × 32 quarters × 50 cols)** | **1,081,312** | **14.5 MB** |
| `fact_zcta_year` in the warehouse | 270,328 | — |
| Cost-to-serve table, one scenario (2,333 priced ZCTAs) | 2,333 | 0.3 MB |
| Facility panel, pilot (Amazon delivery stations, 10 pilot metros) | **43** | 4.7 KB |
| Facility panel, national (`national_facilities.csv`) | **104** | 17 KB |
| OD drive-time matrix (within-metro pairs only) | *never built — see §10* | *n/a* |
| **DuckDB warehouse, everything, compressed** | — | **27 MB** |

Three corrections in that table, all made on 2026-09-14 and all in the same
direction — the projections were pessimistic:

- The panel is **50 columns, not 44**. Six quality flags were added when
  `common/sentinels.py` and `warehouse/flag_gate.py` landed; see
  `../data/DATA_QUALITY.md` F2.
- The warehouse is **27 MB**, not the projected 300-500 MB. `PIPELINE.md`
  §8.1 previously reported that this projection "holds". It does not; it is
  an order of magnitude high, and DuckDB's compression is the reason.
- **The OD matrix row was a projection presented in the same table as
  measurements**, with a row count and a file size. It was never built. §10
  says so; this table did not.

**Read that again.** The entire analytical warehouse is smaller than a phone photo
album, and the panel every model reads is fourteen megabytes. Pandas holds it.
DuckDB holds it with room to spare. There is no distributed compute anywhere in
this project, and if anyone proposes Spark, the answer is no.

**And read the facility-panel row again too.** It is 4.6 KB, and it is the
target variable — the thing all fourteen megabytes above exist to predict.
For most of this project it was a header row with no data; it was delivered
on 2026-09-13 with 43 Amazon delivery stations, 39 of which are usable
events once the two held-out-metro rows and the two pre-2018 (left-censored)
rows come out. The smallest file in the repository is the one the whole
project turns on, and the engineering consequence is that it is the one file
with column-level validation in front of it
(`ingest.external --check`). Its dates are mostly "operating by" upper
bounds from OSHA inspection records rather than opening dates; see
[`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md).

An earlier version of this table estimated an 811,200-row ZCTA-*week* panel
over ten metros at 260 MB. The built panel is quarterly and national: more
coverage, 33% more rows, and eighteen times less disk. Sizing estimates for
columnar data are routinely wrong in this direction, and the honest way to
report one is to measure the artefact and say when you measured it.

### 1.2 What you pass through — measured, and not what was projected

**Projected 2026-09-12, and wrong about which source dominates.** The original
table is kept below the measured one, because the gap between them is the
useful part.

Measured 2026-09-14 with `du -sh`:

| Directory | Size | What is in it |
|---|---|---|
| `data/raw/` | **2.1 GB** | `osha_bulk` 1.4 G, `tiger_zcta` 504 M, `cbp_zip_detail` 119 M, `geofabrik` 50 M, plus fourteen smaller directories |
| `data/external/` | 215 MB | manually placed sources |
| `data/interim/` | 564 MB | fifteen parquets; `zcta_geom` alone is 526 MB |
| `data/processed/` | 41 MB | the panel and the DuckDB warehouse |

Peak disk in practice is **under 3 GB**, against a projected 60 GB careless /
8 GB careful. The projection was wrong because it assumed a routing pipeline
that was never built, and it did not anticipate the 1.4 GB OSHA bulk download
or the 504 MB TIGER shapefile, both of which arrived later and are now the two
largest things in the tree.

The original projection, retained:

| Source | Projected raw size | Notes |
|---|---|---|
| OpenStreetMap PBF (per metro bbox) | 150–500 MB each | never downloaded |
| OpenStreetMap PBF (per state) | ~1.2 GB | only Rhode Island, 50 MB, was |
| OpenStreetMap PBF (full US) | ~12 GB | never downloaded |
| OSRM processed artifacts (per metro) | 2–5 GB | OSRM was never run |
| EPA EJScreen (national, block group) | 1–2 GB | one CSV — happened |
| Census ACS via API (selected tables, ZCTA) | 30–80 MB JSON | happened |
| TIGER/Line ZCTA shapefile (national) | ~600 MB | 504 MB — happened |
| Zillow ZORI + ZHVI | 50–200 MB | happened |
| Yelp / CBP business data | ~1 GB JSON | see §3 — **Yelp was dropped**, ADR-0003 |
| BLS OES, EIA | < 50 MB | happened |

---

## 2. The one thing that will actually break: OSRM

### 2.1 Why it is the risk

OSRM does not just read a map file. It **preprocesses** it — `osrm-extract` then
`osrm-partition` + `osrm-customize` — and preprocessing is memory-hungry and
disk-hungry in a way that scales badly.

```
   metro bbox PBF     200 MB   ->  osrm-extract  ->  ~2-5 GB of .osrm.* files
   California PBF     1.2 GB   ->  osrm-extract  ->  ~15-25 GB, slow
   full US PBF         12 GB   ->  osrm-extract  ->  NOT LAPTOP TERRITORY
                                                     (needs 64-128 GB RAM)
```

v3's §5.5 says *"The OSRM engine runs locally in a Docker container against
pre-downloaded OpenStreetMap extracts for the ten pilot metros."* Ten metros
processed and retained simultaneously is **~30 GB of OSRM artifacts plus the
PBFs**. On a student laptop with a 256 GB SSD that is survivable but unpleasant;
on 8 GB of RAM the extract step for a large metro will thrash or fail outright.

**This is the single biggest infrastructure risk in the project and v3 does not
acknowledge it.**

### 2.2 The fix that makes it a non-issue

> **Status, 2026-09-13: designed, not built.** There is no `od_*.parquet`
> anywhere in the repo, no OSRM artefact has ever been produced, and there is
> no `cost/od_matrix.py`. What the cost model runs on today is the §2.3
> fallback: `cost/daganzo.py` takes the great-circle distance and multiplies
> it by the circuity factor in `cost/params.py`, which is 1.30. Everything
> below this line is a plan. Written in the present tense because it is a
> design, and marked here because the present tense has already been read as
> a completion once.

**Insight: you do not need a routing server. You need a table of drive times.**

The cost model (§5.5) uses `d_stem(i)` — drive time from the nearest logistics
node to ZCTA *i*. That is a **finite, precomputable set of numbers**: roughly
800,000 within-metro origin–destination pairs, which stores as a **10 MB parquet
file** (computed above).

So:

```
   FOR EACH METRO, ONE AT A TIME:
     1. download the metro bbox PBF        (~200 MB)
     2. osrm-extract + partition + customize
     3. run the OD table query
     4. write od_<metro>.parquet           (~1 MB)
     5. DELETE the PBF and every .osrm.* file       <-- the important step
     6. next metro

   PEAK DISK  = one metro (~5 GB), not ten (~30 GB)
   FINAL DISK = 10 x od_<metro>.parquet  =  ~10 MB
```

After this runs once, **OSRM is gone from the project.** No Docker container in
the app, no routing dependency in the dashboard, no cold-start latency, nothing
for a demo to break on. The app reads a 10 MB parquet.

### 2.3 The de-risking option: skip OSRM in v1 entirely

Daganzo's model is *already* a continuous approximation. Adding exact road
routing to an approximate cost law is precision in the wrong place.

**Use a circuity factor instead:** road distance ≈ great-circle distance × *k*,
where *k* ≈ 1.3–1.4 for US metros.

```python
# stem distance, no routing engine required
road_km = haversine_km(node, zcta_centroid) * CIRCUITY  # CIRCUITY = 1.30
```

*The value shipped is **1.30**, not the 1.35 an earlier draft of this snippet
carried. `cost/params.py` sets `circuity: float = 1.30` and
`outputs/metrics/cost_report.json` records 1.3. §2.2 and §10 already said
1.30; only this line did not. The reasoning is in
[`../data/PARAMETERS.md`](../data/PARAMETERS.md) §6.2: 4/pi = 1.2732 is the
exact grid value and 1.30 is that plus 2%.*

Then treat OSRM as a **validation step, not a dependency**:

> *"We estimate the circuity factor on one metro against OSRM ground truth,
> report the residual error, and apply the calibrated factor to the remaining
> nine."*

That is defensible, it is one paragraph in the methods section, and it removes a
30 GB dependency from the critical path. **Recommended for v1.** If the residual
error is large, you have a finding; if it is small, you have saved two weeks.

---

## 3. The second thing that will break: wall-clock, not bytes

> **SETTLED AND SHIPPED. This section is a record of a decision, not an open
> question.** The recommendation below — drop Yelp, use CBP — was taken. It is
> `adr/0003-public-sources-only.md`. Yelp appears nowhere in `src/`, no Yelp
> key exists, and CBP is in the panel as `establishments` (`cbp.parquet`,
> 35,002 rows) with a second industry-detail extract added later
> (`cbp_detail.parquet`, 210,745 rows, see
> [`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md)). The section is left in
> the present tense below because rewriting it would erase the reasoning, but
> nothing in it is outstanding.

Yelp Fusion free tier is **5,000 requests/day**, 50 businesses per request.

```
   250,000 businesses/day
   -> 750,000 businesses takes 3.0 DAYS of continuous polling
```

Three days is not the problem. **Discovering it in week 4 is the problem.**

### Two responses, and I recommend the second

**(a) Start it in week 1** and let it trickle in the background, checkpointed to
disk. Never re-fetch.

**(b) Drop Yelp and use Census County Business Patterns (CBP) instead.**
CBP gives establishment counts by ZIP by NAICS code, as a **bulk download**, free,
no key, no rate limit, and it is the source v3 already proposes to use as the
*bias check* on Yelp (§4.4). If CBP is good enough to audit Yelp, ask the
uncomfortable question: is it good enough to replace it?

| | Yelp Fusion | Census CBP |
|---|---|---|
| Rate limit | 5,000 req/day | none — bulk file |
| Time to acquire | ~3 days | ~10 minutes |
| Coverage bias | under-represents minority-owned, cash, informal businesses (v3 §4.4 admits this) | administrative universe, no self-selection |
| Cost | free tier, key required | free, no key |
| Granularity | individual business, ratings | counts by ZIP × NAICS |

**Recommendation: use CBP as the primary retail-density source and treat Yelp as
an optional enrichment.** This removes a rate limit, removes a bias you currently
have to apologise for, removes an API key from the reproducibility story, and
makes the whole pipeline re-runnable in minutes instead of days.

It also *strengthens* §4.4 — the Yelp representativeness limitation you currently
have to disclose largely disappears.

---

## 4. Reference architecture for the pipeline

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  L0  ACQUIRE          content-addressed cache, write-once        │
  │      data/raw/<source>/<sha256>.<ext> + manifest.jsonl           │
  │      never re-fetch; a re-run costs zero network                 │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L1  NORMALISE        one parquet per source, typed, documented  │
  │      data/interim/<source>.parquet                               │
  │      CSV/JSON never appears downstream of this line              │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L2  CONFORM          DuckDB star schema, in process             │
  │      warehouse/schema.py  +  data contracts (schema, ranges,     │
  │      row counts, referential integrity)                          │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L3  FEATURE          the 1.08M-row ZCTA-quarter panel           │
  │      one parquet. This is what every model reads.                │
  │      warehouse/panel.py + flag_gate.py                           │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L4  MODEL / SERVE    cost, optimiser, Monte Carlo, agent, app   │
  │      reads L3 only. No model ever touches raw data.              │
  └──────────────────────────────────────────────────────────────────┘
```

**Two corrections to that diagram, 2026-09-14.**

*L2 is not dbt.* The `dbt/` tree has been **deleted**, not left as a skeleton.
L2 is `src/siting_atlas/warehouse/schema.py` running DuckDB in process, and
`make warehouse` invokes it directly. Nothing in the repository shells out to
`dbt`. §7's definition of done still says "`dbt build` green"; that criterion
is void and is marked so there.

*L4 does not include SCM, and "hazard" is retired.* There is no
synthetic-control module in `src/` — the only occurrences of the term are
donor-pool docstrings in `agent/`. `models/hazard.py` exists but the hazard
model was withdrawn (see `../METHODS_RESEARCH.md` §14); the current model is
the conditional
ZCTA choice model in `models/choice.py`, and — see `LOGGING.md` §5 — it is
tagged **L5**, not L4.

**Why content-addressed caching matters (worked example).** You fetch ACS data on
Tuesday. On Thursday you change a feature and re-run the pipeline. Without a
cache you re-hit the Census API — 20 minutes, and if they rate-limit you, you are
blocked. With a cache keyed by the SHA-256 of the request, the fetch is a local
file read: **0.2 seconds, and it works offline on a plane.** Same input, same
hash, same file. You will re-run this pipeline hundreds of times; make re-runs
free.

---

## 5. Ten rules that keep this on a laptop

1. **Parquet everywhere after L1.** Never CSV in the pipeline. ~5× smaller,
   typed, column-pruned reads.
2. ~~**Delete OSRM artifacts after extracting the OD matrix** (§2.2).
   Non-negotiable.~~ **Moot.** OSRM was never run, so there are no artifacts
   to delete; see §10.
3. **Develop on one metro, 200 ZCTAs.** Get the pipeline green end-to-end, *then*
   scale. Never debug on full data — a 30-second loop beats a 20-minute loop and
   you will run it 200 times.
4. **Cache every network call, content-addressed** (§4). Re-runs cost zero.
5. **Push aggregation into DuckDB, not pandas.** `SELECT ... GROUP BY` on a
   parquet file beats loading it and grouping in Python, and DuckDB spills to
   disk when it needs to.
6. **Simplify geometries once, at L1.** Full TIGER polygons are ~600 MB and you
   are drawing them at metro zoom. `ST_Simplify` to ~10 m tolerance → ~100 MB and
   nobody can see the difference.
7. **Pin everything.** `uv.lock` / `requirements.txt` with hashes, plus
   `reproducibility/seeds.toml`. "Works on my machine" is a graded failure here.
8. **One `make` target per stage.** Done: `probe acquire normalise
   normalise-external warehouse panel cost model agent optimize scope figures
   app`, plus `all`, `docs`, `lint`, `lint-tools`, `fmt`, `test`, `clean`,
   `install`, `help` — twenty-two in the `.PHONY` list. Anyone can rebuild
   anything without reading code. *(An earlier draft of this rule cited
   `make features`; the target is `make panel`. There is no `features`
   target.)*
9. **Fail loudly on data contracts.** Row-count drop > 5%, unexpected nulls,
   ZCTA count changes → stop the build. Silent data loss is the bug you find in
   week 8.
10. **Never commit data.** `data/` is gitignored; sources are re-derivable from
    the manifest. The repo stays under 50 MB and clones in seconds.

---

## 6. Hardware: what you actually need

| Setup | Verdict |
|---|---|
| **16 GB RAM, 256 GB SSD** | ✅ **Sufficient**, with per-metro OSRM and delete-as-you-go |
| 8 GB RAM | ⚠️ Works **only** with the circuity approximation (§2.3). OSRM extract on a large metro will struggle |
| 32 GB RAM | Comfortable; still no reason to process full-US OSM |
| GPU | ❌ **Not needed anywhere.** Nothing here trains on a GPU |

### Free compute for the heavy bits — all inside the existing budget

| Job | Where | Cost |
|---|---|---|
| OSRM preprocessing (if you keep it) | Google Colab free tier (~12 GB RAM, ~100 GB disk) | $0 |
| Scheduled ingest + data-contract checks | GitHub Actions (2,000 min/month) | $0 |
| App hosting | HuggingFace Spaces free tier | $0 |
| Warehouse | DuckDB, single local file | $0 |
| Public dataset hosting | HuggingFace Datasets | $0 |

**Compute cost of this project: $0.** The entire budget is LLM inference.

---

## 7. Who owns what — the gap nobody has assigned

v3 assigns *modules* but not *pipeline stages*, which is how pipelines rot.

| Stage | Owner | Definition of done |
|---|---|---|
| L0 acquire + cache + manifest | P2 | `make acquire` runs offline on a warm cache |
| L1 normalise to parquet | P2 | every source typed, documented, contract-tested |
| L2 DuckDB star schema | P1 | ~~`dbt build` green~~ **void — `dbt/` was deleted.** Done means `make warehouse` green and contracts enforced by `warehouse/schema.py` |
| L3 feature panel | P1 | one parquet, 1,081,312 rows, versioned |
| L4 models | P1 | reads L3 only |
| OD matrix extraction | P2 | **not started.** Nothing committed; the cost model uses the §2.3 circuity fallback |
| App + viz | P3 | reads L3/L4 outputs, never raw |
| CI, contracts, reproducibility | P2 | red build blocks merge |

---

## 8. Honest risk register

*Four rows are closed as of 2026-09-14 and are marked so rather than deleted,
because a risk register that only ever grows is not being read.*

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OSRM preprocessing defeats a laptop | **CLOSED** | — | Avoided entirely: OSRM was never run and the circuity fallback (§2.3) shipped |
| Yelp rate limit discovered late | **CLOSED** | — | §3 — switched to CBP, ADR-0003 |
| Facility open-dates are incomplete/wrong | **Certain — it has happened** | **High** | This is the *target variable*, the panel is 43 rows, and most of its dates are "operating by" upper bounds, not openings. A 100-facility audit sample is arithmetically impossible on 43 rows, so the mitigation is **census, not sample**: every row is listed with its source in `data/collection/results/DATES_FOUND.csv`, and the looseness of the bound is measured against the 5 addresses with an independent opening date (held 5/5; lags 4–345 months). See `docs/data/FACILITY_PANEL_PROVENANCE.md` |
| ZCTA boundaries change between vintages | Medium | Medium | Pin one vintage (2020); document crosswalk |
| dbt/DuckDB spatial extension friction | **CLOSED** | — | dbt was dropped; geometry is done in Python at L1 (`normalise_geo.py`, `osm_landuse.py`) and the SQL stays non-spatial |
| Team blocked on one person's laptop | Medium | High | Everything in CI; nothing lives only on a local disk |
| Scope creep re-adds full-US OSRM | **CLOSED** | — | ADR-0002 records the decision. Nothing has re-added it |

---

## 9. What this means for the proposal text

Four edits to §5.5 and §4.1. **Edit 1 is withdrawn, 2026-09-14 — it was the
last surviving instance of the defect §10 records.**

1. ~~**State the OD-matrix precompute explicitly.** It is a genuine
   engineering decision and reviewers respect it: *"OSRM is used once,
   offline, to precompute a drive-time matrix; the deployed application
   carries no routing dependency."*~~
   **WITHDRAWN. Do not put that sentence in the proposal.** It is written in
   the completed present tense and none of it happened: OSRM was never run,
   no drive-time matrix exists, and `grep -rli osrm src/` finds one docstring
   in `common/shell.py`. §10 struck the same sentence from this document and
   this recommendation was missed. The honest version, if the proposal wants
   to mention it at all, is §10's: *a drive-time matrix is designed and not
   built; the cost model uses great-circle distance times a circuity factor
   of 1.30.*
2. **Add the circuity fallback** with the one-metro validation. **Note the
   validation has not been run either** — the factor is an analytical
   derivation (4/pi plus 2%), not a calibration against OSRM ground truth.
   See [`../data/PARAMETERS.md`](../data/PARAMETERS.md) §6.2.
3. **Swap Yelp → Census CBP** as primary, Yelp as optional enrichment.
4. **Delete any implication that this is big data.** Say the real number — a
   1,081,312-row, fourteen-megabyte panel — and say that it is deliberately
   small because the contribution is identification, not scale. **Claiming
   bigness you don't have is a credibility loss; claiming smallness you
   designed for is a credibility gain.**

---

## 10. The two-sentence version, for the viva

> *"The analytical panel is 1,081,312 rows and fourteen megabytes —
> deliberately small, because the contribution is identification, not scale.
> It covers all 33,791 US ZCTAs quarterly from 2018 to 2025. The only heavy
> component would have been road-network preprocessing, and we have not built
> it: the cost model currently uses great-circle distance scaled by a circuity
> factor of 1.30, which is the §2.3 fallback. The OSRM precompute is designed —
> per metro, extract the OD table, delete the artefacts, ship a ten-megabyte
> lookup — and it is designed that way so that routing never enters the
> deployed application. But it is a plan, and the residual error of the
> approximation we are actually using has not yet been measured against routed
> ground truth."*

If the examiner presses on that last clause, the honest follow-up is that the
approximation is defensible rather than a corner cut. Daganzo's law is itself a
continuous approximation, so exact routing is precision in the wrong place; the
1.30 factor is derived (4/pi = 1.2732 for a uniformly random direction on a
rectangular grid, plus two per cent for non-grid detours) rather than tuned;
and both published ancestors, Holmes (2011) and Houde, Newberry and Seim
(2023), apply no circuity at all, so 1.30 biases cost upward relative to them.
None of that is a measurement, and the measurement — residual error on one
metro against routed ground truth — is a day's work that has not been done.
