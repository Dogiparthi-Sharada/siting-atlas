# Data sources — how to fetch everything this project reads

The repository ships **derived data only**. The raw tree is 4.5 GB, four files
exceed GitHub's 100 MB limit, and two sources are not ours to redistribute.
This document is the recipe for the ingredients.

**Read [§18 Reproduction path](#18-reproduction-path) first** if you only want
the results. Most of the headline figures rebuild from what is already in the
clone, with no downloads at all.

### Conventions

- **Module** commands assume `pip install -e .` (a `src/` layout, so the
  importable name is `siting_atlas`, not `src.siting_atlas`; without an install
  prefix with `PYTHONPATH=src`).
- Automatic downloads land in `data/raw/<source>/` and append a line to
  `data/raw/manifest.jsonl` with URL, SHA-256, bytes and content type. **That
  manifest ships**, so every URL below can be checked against what was fetched.
- Hand-placed files go in `data/external/<registry key>/`, publisher's original
  filename, **do not unzip**. Validate with
  `python -m siting_atlas.ingest.external --check`.
- `UNVERIFIED` marks anything I could not confirm from the code, the manifest,
  or a file on disk. The build host has no outbound internet, so **no URL here
  was re-probed live**; "verified" means verified against the repository.

### Keys

Three environment variables, in `.env` at the repo root (gitignored, loaded by
`common/config.py`). **Never commit a key** — `scripts/check_no_secrets.py` is
a pre-commit gate for exactly that.

| Variable | Used by | Free key from |
|---|---|---|
| `CENSUS_API_KEY` | `ingest.census_api` | https://api.census.gov/data/key_signup.html |
| `EIA_API_KEY` | `ingest.eia_api` | https://www.eia.gov/opendata/register.php |
| `DOL_GOV_API_KEY` | *nothing in `src/` reads it* — see §9 | https://dataportal.dol.gov/registration |

## 1. American Community Survey — 5-year and 1-year

**What it is.** Census demographics. ACS5 at ZCTA grain gives population,
median income, median home value, vehicle availability, median age and
educational attainment; ACS1 at metro grain gives shorter-lag context. These
are the level covariates in the panel.

**Where.** `https://api.census.gov/data/2023/acs/acs5` and
`https://api.census.gov/data/2023/acs/acs1` — both in the manifest.

**How.** `python -m siting_atlas.ingest.census_api` (ACS5) and
`python -m siting_atlas.ingest.census_api --acs1` (ACS1).
- **Key** — `CENSUS_API_KEY`, required. The endpoint answers a missing key with
  an HTML page carrying **HTTP 200**, so a naive client caches an error page as
  data; `census_api.py` asserts on Content-Type for that reason.
- **Size / time** — 3.5 MB → 1.4 MB parquet (ACS5), 32 KB → 22 KB (ACS1);
  minutes. **Licence** — US federal work, public domain, redistributable.
- **Vintage** — **2023 only** (`config.ACS_YEAR`). A single snapshot: there is
  no ACS time series here, so no demographic trend covariate is possible and
  none is claimed.

## 2. Census reference geography — Gazetteer, crosswalk, delineation

**What it is.** Three small files that decide the *shape* of the panel.
**Gazetteer** gives centroid and land area per ZCTA — the geometry the cost
model actually uses (§3 is 500× larger and only needed for choropleths).
**ZCTA-to-county** joins county-grain sources down to ZCTA, area-weighted by
each intersection. **OMB delineation** says which counties constitute each
CBSA; membership comes from here rather than from a commercial rent index's
coverage, which would drop 35% of pilot-metro ZCTAs and select on density.

**Where.**
```
https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip
https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt
https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx
```

**How.**
`python -m siting_atlas.ingest.acquire --only gaz_zcta zcta_county_xwalk cbsa_county`
- **Key** — none. **Size / time** — 1.0 MB + 6.8 MB + 144 KB, seconds.
- **Licence** — public domain, redistributable.
- **Vintage** — Gazetteer 2023, delineation 2023, **crosswalk 2020 decennial.**
  That mismatch is the Connecticut gap: the crosswalk uses the eight old
  counties, the delineation nine planning regions, so Connecticut does not
  join. No pilot metro is affected; a known gap, not repaired.

## 3. TIGER/Line ZCTA boundaries

**What it is.** ZCTA polygons for spatial joins, polygon-distance measures and
maps. Produces `data/interim/zcta_geom.parquet`.

**Where.** `https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/tl_2020_us_zcta520.zip`

**How.** `python -m siting_atlas.ingest.acquire --only tiger_zcta --include-large`
— gated so a default run stays small.
- **Key** — none.
- **Size / time** — **528 MB** zipped, derived parquet 526 MB; tens of minutes.
  Neither ships.
- **Licence** — public domain; redistributable but too large for GitHub.
- **Vintage** — **2020, pinned.** Mixing 2010 and 2020 ZCTA boundaries silently
  corrupts a time series.

## 4. TIGER/Line roads — primary and per-county

**What it is.** The highway-access covariate. Two layers are needed because
`PRIMARYROADS` (the freeway centreline network, 17,458 features, all
`MTFCC=S1100`) has **no ramps** — those are `MTFCC=S1630`, shipped only in the
per-county `ROADS` files — and the siting constraint is proximity to an *exit*.

**Where.** (The second is one file per county, fetched only for the counties
the choice model builds choice sets in.)
```
https://www2.census.gov/geo/tiger/TIGER2023/PRIMARYROADS/tl_2023_us_primaryroads.zip
https://www2.census.gov/geo/tiger/TIGER2023/ROADS/tl_2023_<county_geoid>_roads.zip
```

**How.** `python -m siting_atlas.ingest.tiger_roads` — it calls
`tiger_fetch.primary_roads()` and `.county_roads()` itself, so there is no
separate download step (`tiger_fetch` has no CLI entry point). County hashes go
to a sidecar, not the main manifest.
- **Key** — none.
- **Size / time** — 38 MB national + **1.6 GB** county; hours. Neither ships;
  the derived `highway_access.parquet` (663 KB) and
  `tiger_interchanges.parquet` (467 KB) do.
- **Licence** — public domain, redistributable. **Vintage** — TIGER 2023.

## 5. County Business Patterns — ZIP totals and ZIP×industry detail

**What it is.** Two files. `zbp22totals` gives establishment counts per ZIP
(retail density / competitive pull). `zbp??detail` gives counts by ZIP × NAICS,
from which NAICS `493///` (warehousing and storage) is the covariate that took
the choice model from 30% to 50% top-10 — it proxies the binding physical
constraint that you cannot site a delivery station on residential land.

**Where.**
```
https://www2.census.gov/programs-surveys/cbp/datasets/2022/zbp22totals.zip
https://www2.census.gov/programs-surveys/cbp/datasets/{year}/zbp{yy}detail.zip   # 2016-2022
```

**How.** Totals: `python -m siting_atlas.ingest.acquire --only cbp_zip`.
Detail: **no module fetches it** — download by hand into
`data/raw/cbp_zip_detail/`, then `python -m siting_atlas.ingest.cbp_detail`. It
is not in the registry and not in the manifest, so it has **no recorded
SHA-256**; documented by hand in [`data/CBP_DETAIL.md`](data/CBP_DETAIL.md).
- **Key** — none. **Size / time** — 824 KB totals, **119 MB** detail across
  seven vintages; under ten minutes. **Licence** — public domain,
  redistributable.
- **Vintage** — totals 2022 (`config.CBP_YEAR`); detail 2017–2022 used
  (`cbp_detail.USABLE_VINTAGES`), the 2016 file on disk skipped. The file is
  **hierarchical** — the same establishment is counted at all five levels of
  its NAICS code, so summing levels double-counts.

## 6. Building Permits Survey — county annual

**What it is.** The forward signal that offsets the ACS reporting lag:
construction precedes population.

**Where.** `https://www2.census.gov/econ/bps/County/co{yy}12y.txt`, one file per
year; all nine of 2017–2025 are in the manifest.

**How.** `python -m siting_atlas.ingest.acquire --only bps_county`
- **Key** — none. **Size / time** — 2.3 MB total, seconds.
- **Licence** — public domain, redistributable.
- **Vintage** — 2017–2025, all fetched; a year-over-year feature is impossible
  from one file. Two coverage breaks are handled rather than smoothed: the
  county universe widens from ~745 to ~3,021 in 2022, and Connecticut's
  geography changes in 2023.

## 7. BLS Occupational Employment and Wage Statistics — metro

**What it is.** Driver and warehouse wages by metro: the largest cross-metro
varying cost bucket. Four of ~830 occupation codes are kept, including
`53-3033` light truck drivers and `53-7062` labourers and material movers.

**Where.** `https://www.bls.gov/oes/special-requests/oesm25ma.zip` — the
pattern `oesm{yy}ma.zip` is in `registry.py` and the file on disk is
`oesm25ma.zip`, but the URL is **UNVERIFIED**: bls.gov returns HTTP 403 to this
environment even with a descriptive User-Agent, so it has never been fetched
programmatically here. A browser works; if it 404s, navigate from
https://www.bls.gov/oes/tables.htm.

**How.** Download by hand to `data/external/bls_oes/`, then
`python -m siting_atlas.ingest.normalise_external --only bls_wages`.
- **Key** — none. **Size / time** — 40 MB zipped, ~2 min; parquet is 40 KB.
- **Licence** — public domain; redistributable but not shipped (40 MB for a
  40 KB derivative).
- **Vintage** — **May 2025 only.** A single snapshot, so wages are constant
  across the panel's 2018–2025 span — a real limitation on any cost trend.

## 8. EIA — regional energy prices

**What it is.** Industrial retail electricity price by state (monthly,
cents/kWh) and No. 2 diesel retail price by PADD region (monthly, $/gal) — the
fuel-and-energy cost bucket.

**Where.** `https://api.eia.gov/v2/electricity/retail-sales/data/` and
`https://api.eia.gov/v2/petroleum/pri/gnd/data/`, both in the manifest.

**How.** `python -m siting_atlas.ingest.eia_api`
- **Key** — `EIA_API_KEY`, required. An unauthenticated request returns **HTTP
  403**, which reads like a network block but is the missing-key response.
  Pages cap silently at 5,000 rows, so the extractor follows offsets.
- **Size / time** — 1.2 MB across both series, ~1 minute.
- **Licence** — public domain, redistributable.
- **Vintage** — 2018-01 to 2025-12 (`eia_api` defaults). Diesel is published
  only at PADD grain, coarser than the rest of the model.

## 9. OSHA inspections — US DOL bulk extract

**What it is.** Every OSHA inspection ever recorded — the only *uniform*
national list of Amazon buildings, and the project's most important external
source. One run scans 5,200,011 inspections, keeps 951 Amazon rows, and
collapses them to 474 distinct buildings. An inspection date is **not** an
opening date: it proves the building was operating then, an interval-censored
upper bound, and will never say "opened in 2019".

**Where.** Two routes to the same data. Browser:
https://enforcedata.dol.gov/views/data_summary.php → OSHA → Inspection → full
CSV archive, no key. API, which is what the manifest records:
`https://apiprod.dol.gov/v4/get/OSHA/inspection/csv`, needing a DOL key sent as
an `X-API-KEY` header.

**How.** There is **no fetch module**. Download by hand, then
`python -m siting_atlas.ingest.osha /path/to/inspection.zip`, which writes
`data/interim/osha_amazon.csv`.
- **Key** — `DOL_GOV_API_KEY` is declared in `.env` but **no code in `src/`
  reads it**; the download happened outside the pipeline. Treat it as optional
  and use the browser route.
- **Size / time** — **1.4 GB** zipped, ~105 chunked CSVs **each repeating the
  header** (a reader that opens only the largest member gets ~1% of the data
  and looks successful). Download 20–60 min; the scan streams without unpacking.
- **Licence** — public domain; redistributable but 1.4 GB. The derived
  `osha_amazon.csv` (59 KB) ships. **Vintage** — downloaded 2026-09-13; counts
  will differ against a newer DOL extract, the shape should not.
- **Known bias** — OSHA inspects where people get hurt. Of 474 buildings it
  finds 81 fulfilment centres and only 19 delivery stations, so the target
  class is the one this source sees worst.

## 10. NLRB case search

**What it is.** A *second* incomplete list of Amazon worksites. Its value is
not the rows but the denominator: two incomplete lists of the same population
measure each other, which is what produces the capture-recapture coverage
estimate.

**Where.** Route A — https://www.nlrb.gov/search/case : search the employer
field for `Amazon`, once per name variant (`Amazon.com Services LLC`,
`Amazon Logistics, Inc.`, `Amazon.Com.Dedc, LLC`, …), and export each result
set. Route B — https://www.nlrb.gov/reports/graphs-data/recent-election-results :
monthly spreadsheets carrying **street address and bargaining-unit size**,
which Route A usually does not.

**How.** Interactive export only; no API, no stable endpoint. Drop the raw
exports in `data/external/nlrb/`, then `python -m siting_atlas.ingest.nlrb` and
`python -m siting_atlas.ingest.nlrb_capture`. Full instructions, including the
Delivery Service Partner problem, are in `data/external/nlrb/HOWTO.md`.
- **Key** — none. **Size / time** — ~900 KB, 30–60 min of manual searching.
- **Licence** — public domain (US federal agency). The filtered export
  `nlrb_cases_amazon.csv` **does ship**. **Vintage** — exported 2026-09-13.
- **Binding limitation** — the case-search export carries no street address, so
  the finest grain is **city + state**. OSHA averages 1.39 buildings per city,
  so a city-coverage figure is not a building-coverage figure.

## 11. OpenStreetMap

**What it is.** Two uses, one live and one dead.

*Live — Overpass, industrial land.* `landuse=industrial` polygons and
`building=warehouse` footprints per ZCTA. Measures directly what the CBP
warehousing count (§5) only proxies: a ZIP can hold a lot of industrial land
with few establishments on it, which is the profile of a ZIP with room for a
new station.

*Dead — Geofabrik PBF.* `data/raw/geofabrik/rhode-island.osm.pbf` (50 MB) was
downloaded for the OSRM drive-time matrix in ADR-0002. **That work was never
implemented and the file is never read**; the cost model uses great-circle
distance × a circuity factor of 1.30. Do not download it.

**Where.** `https://overpass-api.de/api/interpreter`, queried per-CBSA bounding
box (Overpass will not serve a national query, and 25,022 per-ZCTA queries
would be abusive). Geofabrik, for completeness only:
`https://download.geofabrik.de/north-america/us/{state}-latest.osm.pbf`.

**How.** `python -m siting_atlas.ingest.osm_landuse`. Responses cache per tile
in `data/raw/osm_landuse/`; caching is a requirement, not an optimisation,
because Overpass rate-limits and the build is re-run often.
- **Key** — none, but be polite: Overpass is donated infrastructure.
- **Size / time** — ~3.6 MB cached JSON so far, derived parquet 38 KB; hours
  wall-clock because of rate limiting.
- **Licence** — **Open Database License (ODbL)**: attribution required, and
  share-alike applies to derived databases. The only non-public-domain open
  source in the set; keep the attribution.
- **Vintage** — queried 2026-09-14. The covariate is **verified on three metros
  only** and is blocked on completing the sweep — see
  [`data/OSM_LANDUSE.md`](data/OSM_LANDUSE.md).

## 12. Zillow ZORI and ZHVI

**What it is.** Rent index (ZORI) and home-value index (ZHVI) at ZIP grain,
monthly. Disposable-income proxy and commercial land-cost proxy.

**Where.** ZORI:
`https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv`
is the URL in `registry.py`, but the file actually used is the **seasonally
adjusted** variant `Zip_zori_uc_sfrcondomfr_sm_sa_month.csv`, so the registry
URL does not point at the file on disk and the `_sa_` URL is **UNVERIFIED**.
ZHVI: the file on disk is `Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
and **no URL for it exists anywhere in the repository — UNVERIFIED**; navigate
from https://www.zillow.com/research/data/ → Home Values → ZHVI All Homes
(SFR, Condo/Co-op), Geography = ZIP Code.

**How.** Download by hand into `data/external/zillow_zori/` and
`data/external/zillow_zhvi/`, then `python -m siting_atlas.ingest.normalise`
(ZORI) and `python -m siting_atlas.ingest.normalise_external` (ZHVI). ZHVI is
cut to 2015-01 onward *while still wide* — melting all 318 months would make
~8M rows to then discard.
- **Key** — none, but `files.zillowstatic.com` returns HTTP 503 to this host's
  egress proxy, so fetch from a browser.
- **Size / time** — ZORI 9.9 MB, ZHVI **118 MB**; under five minutes each.
  **Vintage** — downloaded 2026-09; series run to the download month.
- **Licence** — **Zillow Research terms: free for non-commercial research with
  attribution. Redistribution is not granted, so neither CSV ships.** Keep the
  attribution line if you use them.
- **Selection warning** — Zillow publishes an index only where there are enough
  listings, so coverage is selective on density. Rent stays a feature with
  honest missingness and is never used as a filter (see §2).

## 13. EPA EJScreen

**What it is.** Environmental-justice indicators at census-tract grain: PM2.5,
diesel PM, traffic proximity, low-income share, people-of-colour share. Ten of
230 columns are read. Powers the equity overlay.

**Where. UNVERIFIED.** The historical `gaftp.epa.gov` paths now return 404 and
the current distribution location is recorded nowhere in the repository.
Navigate from https://www.epa.gov/ejscreen and take the **census tract,
national** CSV. The file the project used is
`EJScreen_2024_Tract_with_AS_CNMI_GU_VI.csv.zip`.

**How.** Place in `data/external/ejscreen/` (do not unzip), then
`python -m siting_atlas.ingest.normalise_external --only ejscreen_tract`.
- **Key** — none. **Size / time** — 51 MB zipped, ~5 minutes.
- **Licence** — public domain; redistributable but not shipped (51 MB for a
  6.6 MB parquet).
- **Vintage** — **2024 only.** A single snapshot, so the equity overlay is a
  cross-section with no trend. All 288 Connecticut ZCTAs are missing every
  EJScreen column, for the county-geography reason in §2.

## 14. MWPVL International — Amazon distribution network

MWPVL International is a supply-chain consultancy that publishes a detailed
account of Amazon's distribution network. Two of its documents are in play: the
2025 Q1 network article and an earlier April 2012 table.

The 2025 article's facility tables are **images, not text**. They were OCR'd,
yielding **1,904 Amazon facilities worldwide — 1,767 (92.8%) with a postal
code, 1,420 (74.6%) with an opening year, 873 (45.9%) with an opening month**,
of which 635 are US small-package delivery stations. These are the project's
only opening dates that are *lower* bounds; every other date on record is an
OSHA-derived upper bound.

**What ships** is the extracted table, `data/interim/mwpvl_facilities.csv`
(556 KB), and `outputs/metrics/mwpvl_extraction.json`. **What does not ship**
is the PDFs: third-party copyright, and the publisher states in the article
that the information will no longer be updated online. `.gitignore` excludes
`data/raw/mwpvl/*.pdf`. Facts are not copyrightable; the document is.

**Source, with attribution.** MWPVL International, *Amazon.com Distribution
Network Strategy* — https://mwpvl.com/html/amazon_com.html. Retrieved
2026-09-14. To obtain it yourself, visit that page; if it is no longer
available, contact MWPVL International directly.

**To rebuild the extraction** you need the PDF plus `tesseract`. The OCR stage
expects page images already extracted from the PDF into
`data/raw/mwpvl/images/` (override with `MWPVL_IMAGES`):
```bash
bash tools/ocr/grid_ocr.py                    # -> data/raw/mwpvl/tsv/
python -m siting_atlas.ingest.mwpvl_tables      # -> mwpvl_facilities.csv
python -m siting_atlas.ingest.mwpvl_panel       # validate against OSHA
```

Method and measured defects: [`data/MWPVL_OCR_PIPELINE.md`](data/MWPVL_OCR_PIPELINE.md).
The extraction is not treated as ground truth — MWPVL says as much of its own
table — and its dates are tested against the independent OSHA "operating by"
bound rather than against plausibility.

## 15. Good Jobs First Subsidy Tracker

**What it is.** State and local subsidy awards that governments are legally
required to disclose, consolidated by the nonprofit Good Jobs First. Used here
for the Amazon parent-company record: a fourth independent list of facility
locations, with a capture mechanism unrelated to worker grievance.

**Where to buy it.** https://subsidytracker.goodjobsfirst.org/ — search the
**parent company** field for `Amazon` and use the Export control. The project's
copy cost **USD 25** under a subscription licence, downloaded 2026-09-14.

**Redistribution: not permitted.** The raw CSV was purchased under a
subscription licence and is not ours to republish. It is excluded by
`.gitignore` (`data/external/subsidies/`). **What ships instead** is the derived
aggregates in `outputs/metrics/subsidies.json`, written by
`python -m siting_atlas.ingest.subsidies`. If you buy your own copy, note that
`subsidies.SOURCE` hardcodes the filename
`data/external/subsidies/subsidy_tracker_amazon_2026-09-14.csv` — rename your
export to match, or edit that constant.
- **Key** — none, but the endpoint returns HTTP 403 to non-browser clients:
  bot protection, not a missing header. It needs a browser session.
- **Size / time** — 349 KB; minutes once you have an account.
- **Finding** — the obvious use, "tell a county what comparable counties paid",
  is **not supported**: even in the best case for disclosure the records are
  too coarse to attribute an award to a facility.

## 16. Facility panel and geocoding (derived — only the two small panels ship)

Not an external download, but listed so the dependency graph is complete.
`data/external/facility_panel/` holds the target variable, compiled from public
inventories, corporate announcements, permit records and the sources above:
`facilities.csv` (43 pilot delivery stations) and `national_facilities.csv`
(104 rows / 101 buildings). **Only those two ship.** The expanded panel
(`national_facilities_expanded.csv`, 693 rows / 687 buildings) and
`geocoded_expanded.csv` are on disk but **untracked** — `git ls-files
data/external/facility_panel/` returns the two files above and nothing else,
so a fresh clone does not contain the 693-row panel at all. Coordinates
come from the free Census batch geocoder at
`https://geocoding.geo.census.gov/geocoder/geographies/addressbatch` (no key)
via `python -m siting_atlas.ingest.geocode_facilities`, which matches
**501 of 693 = 72.3%**. Read
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) before
trusting it: the dates are upper bounds, the sample is selected on injury
rather than existence, the time trend is partly an inspection trend, and 43
rows in 10 metros is a small slice of roughly 700–900 US delivery stations.

## 17. Facility-class labelling — where the target variable's labels came from

**What it is.** §9 gives a uniform national list of Amazon buildings and **no
facility class**. OSHA records an establishment name, a street address and an
inspection date; it never says whether the building is a delivery station, a
fulfilment centre, a sortation centre, an air hub, a grocery or a pharmacy.
The project models delivery stations, and a panel that mixes the classes
answers no question — a fulfilment centre and a delivery station are different
decisions by different teams against different constraints. §9's own bias line
is the size of the gap: of 474 buildings the establishment name identifies 81
fulfilment centres and 19 delivery stations, and is **silent on 362**. The
class had to be collected. This section documents that collection as a source
in its own right, because the target variable is its output.

**Where.** `data/collection/` — **47 files, all tracked, and they ship**:

```
  prompts/    20   what was asked, verbatim: five prompt texts, thirteen
                   address lists and batches, two worklists
  results/    17   what came back: six unparsed replies, eleven parsed CSVs
  keys/        4   the ANSWER KEYS the replies were checked against
  dates/       3   a separate date-lookup pass, its prompt, its instructions
  satellite/   3   the sixth method, kept as a negative result
```

The account of record is
[`data/collection/README.md`](../data/collection/README.md); the long,
deliberately unflattering version is
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md).

**How — six methods, five of which failed.** Recorded because each one rules
out a route a reader would otherwise ask "why didn't you just…?" about. The
first four are §3 of the provenance document; the fifth has its own write-up.

| Method | Outcome |
|---|---|
| Scrape `hiring.amazon.com` for building type from job titles | **FAILED** — delivery stations are staffed by Delivery Service Partner contractors, not Amazon employees. A 50-mile Chicago search returned 7 jobs, none at a delivery station |
| Date a site from its oldest Google Maps review | **FAILED** — does not scale, and Google merges listings for successive tenants at one address, so the error mode is silent |
| Ask a language model to web-search opening dates from a city name | **FAILED** — ~60 queries produced 4 dates, one a genuine opening. An earlier pass **fabricated 33 of 35**, every row citing one URL that supported none of them |
| MWPVL's public network table as a frame | **FAILED as a frame** — it is an April 2012 snapshot; 4 of 202 OSM candidates appear in it and all four are fulfilment centres. It survives as the *yardstick* of §14 and §6.2 of the provenance document |
| Date construction from free Sentinel-2 imagery | **FAILED** — an estimate for 107 of 107 sites, of which 39 (36%) date construction *after* an inspector found the building operating. [`data/SATELLITE.md`](data/SATELLITE.md) |
| **Batch the unlabelled addresses, have a model classify and date each with a source URL, then verify against evidence it never saw** | **WORKED** — and is what `data/collection/` holds |

The difference is the key the model is given. *"When did the Amazon facility in
Kent WA open?"* has no key and produces fabrication. *"What kind of facility is
20202 84th Ave S, Kent WA 98032?"* hands it a federal street address, which
leasing listings, DSP directories, planning agendas and square-footage figures
are all indexed on.

**The prompt design is the method.** From
`prompts/GEMINI_PROMPT.txt`: *"If you cannot find a real dated source, write
UNKNOWN. Do not estimate"* and *"Give a working source URL for every date."*
A model asked to classify will always return a class, so **refusing has to be
an allowed answer** and the answer has to carry evidence somebody else can
check. `UNKNOWN` was returned often and kept as `UNKNOWN`: 6 of the 82 OSHA
addresses were unresolved after two rounds and left blank; 8 of the 362
addresses in the six unlabelled batches came back `UNKNOWN`; and the honest
redo of the date pass returned **15 of 35 rows with no date at all**, which is
what a truthful pass looks like.

**`keys/` holds answer keys, not credentials.** Nothing in `data/collection/`
is a secret; the directory name is unfortunate and is kept only because the
filenames appear in the audit trail. Each key pairs an address with something
the model was not told — usually `operating_by`, the date of an OSHA
inspection proving the building was already running.

```
  keys/OSHA_CLASSIFY_KEY.csv     82 rows   n,address,city,state,zip,operating_by
  keys/NATIONAL_KEY.csv         319 rows
  keys/GEMINI_KEY.csv            35 rows
  keys/OSHA_ROUND2_KEY.csv       29 rows
```

That check is the declared edit `E_operating_by`
(`src/siting_atlas/warehouse/edits.py`): a claimed opening later than a proven
operating date is **falsified**, not merely doubtful. It is the same edit that
later graded the OCR extraction of §14 at a 94.71% pass rate.

- **Key** — none, and no spend. The prompt files were submitted to a
  web-search-enabled language model (the filenames record Gemini) and the
  replies pasted back; the unparsed replies are kept in
  `results/UNLABELLED_BATCH_*_RAW.txt`. There is no API key, no endpoint and
  no metered cost to reproduce.
- **Size / time** — 47 files, under a megabyte. The cost is human: eleven
  address batches, one OSHA classification pass run in two rounds, and a
  hand-checked date pass.
- **Licence** — the prompts, worklists, keys and parsed results are this
  project's own work and ship under the repository's MIT licence. The
  addresses they are built on are US federal public-domain records (§9).
- **Vintage** — classified 2026-09-13 and 2026-09-14. A re-run against a newer
  OSHA extract changes the worklist, not the method.
- **The binding limitation, and it is not hidden — the check runs one way
  only.** `E_operating_by` can prove a building was operating *earlier* than
  claimed. It can never prove an opening date is right. A label that survives
  is *not falsified*, which is weaker than *correct*, and **an unchecked row is
  not a passing row**: of the 1,420 dated rows in the §14 extraction only 208
  link to an OSHA building at all, and of the 551 dated rows in the expanded
  panel only 136 link, leaving 415 never tested. That asymmetry is why every
  date in the panel is an upper bound with no lower bound, and it is why the
  satellite programme in the table above was attempted at all.

## 18. Reproduction path

### What ships in the clone (~150 MB)

- All code, tests, `docs/`, `Makefile`.
- **`data/processed/`** (73 MB) — `panel.parquet`, `panel_expanded.parquet`,
  `panel_national.parquet`, `siting_atlas.duckdb`. The frame every model reads.
- **`data/interim/`** (~15 MB) — every typed parquet except `zcta_geom.parquet`
  (526 MB) and `zillow_zhvi.parquet` (47 MB), plus `osha_amazon.csv`,
  `mwpvl_facilities.csv` and `nlrb_amazon.csv`.
- **`data/external/`** (~1.5 MB) — the facility panel, the NLRB export, the
  satellite negative-result CSVs and the `TEMPLATE.csv` stubs. **Note (§16):**
  "the facility panel" here means `facilities.csv` and
  `national_facilities.csv` only. `national_facilities_expanded.csv` (693 rows)
  and `geocoded_expanded.csv` are untracked and do **not** ship.
- **`data/collection/`** (~0.4 MB) — the 47 labelling artefacts of §17:
  prompts, raw replies, parsed results, answer keys and the satellite script.
- **`data/raw/manifest.jsonl`** — URL + SHA-256 for every automatic download.
- **`outputs/`** (~18 MB) — all metrics JSON, figures and tables.

Excluded: `data/raw/` (3.7 GB), the two large interim parquets, the licensed
sources (§14, §15), and `data/interim/prepromotion_backup/`.

### Results that need no download at all

**This is the honest answer, and it is the good one.** Because
`data/processed/panel.parquet` ships, everything from L4 onward rebuilds from
the clone:

```bash
pip install -e ".[dev,viz,docs]"
make cost model scope figures      # no network, no keys
```

That regenerates the cost model, the hazard and choice-model results, the
covariate search, the leakage tests, the scope measurement and every figure in
`outputs/figures/` — which is where the headline numbers live. **A reader
checking the paper's claims never needs to download anything.** The models
reading `data/interim/cbp_detail.parquet` (choice model, covariate search, GBM
benchmark, leakage tests) work too, because that parquet ships. Anything that
rebuilds ZCTA geometry or reads `zillow_zhvi.parquet` does **not**.

### Full path, in dependency order

| # | Stage | Fetch | Size | Rough time |
|---|---|---|---|---|
| 1 | Keys | Census, EIA | — | 10 min |
| 2 | `make acquire` | §1, §2, §5 totals, §6, §8 | ~15 MB | 5 min |
| 3 | `--include-large` | §3 TIGER ZCTA | 528 MB | 20–40 min |
| 4 | Hand-place | §7 BLS, §12 Zillow ×2, §13 EJScreen | 219 MB | 20 min |
| 5 | Hand-place | §5 CBP detail, 7 files | 119 MB | 10 min |
| 6 | Hand-place | §9 OSHA bulk | 1.4 GB | 20–60 min |
| 7 | Interactive | §10 NLRB export | 1 MB | 30–60 min |
| 8 | `tiger_roads` | §4 roads + per-county | 1.7 GB | 1–3 h |
| 9 | Overpass | §11 industrial land | 4 MB | hours, rate-limited |
| 10 | Restricted | §14 MWPVL, §15 Subsidy Tracker | 12 MB | USD 25 + manual |

Then:

```bash
make normalise normalise-external warehouse panel cost model scope figures
```

**Total: ~4.0 GB and roughly 6–10 hours wall-clock**, most of it waiting on the
OSHA archive, the TIGER county sweep and the Overpass rate limit. Steps 1–2
alone (15 MB, 15 minutes) rebuild the demographic and cost covariates; steps 8
and 9 are the expensive ones, and each supports one covariate whose measured
lift is reported in `outputs/metrics/`.

*Per-source cards with the full provenance notes are in [`docs/data/`](data/);
orientation for an empty `data/` directory is in
[`data/README.md`](../data/README.md).*
