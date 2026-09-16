# Data sources

14 registered sources; 13 feed the analytical panel. OpenStreetMap is infrastructure rather than an analytical source. **The drive-time matrix ADR-0002 describes was designed and never built**, so the sentence this line used to carry — "it is consumed once, offline, to produce the drive-time matrix, after which every artefact is deleted" — described work that does not exist. The cost model uses great-circle distance times a circuity factor; see [`COST_MODEL.md`](COST_MODEL.md).

> **This file is generated, and parts of it are not.** Run
> `python tools/docs/gen_data_docs.py` and everything the generator does not
> emit is destroyed. As of 2026-09-15 that is: the corrected first paragraph
> above, the whole of **"Sources outside this registry"** below, and the two
> dated correction blocks inside it. The false drive-time sentence the first
> paragraph corrects is emitted by `tools/docs/gen_data_docs.py` and declared
> in `src/siting_atlas/ingest/registry.py:303`, so **the next run will restore
> it** unless those two lines are fixed first.
>
> **"The hand-written pages" index below is the exception — it lives in the
> generator** (`HAND_WRITTEN` in `tools/docs/gen_data_docs.py`) and survives a
> regeneration. Add a page there, not here. The generator prints a warning
> naming any `.md` in this folder that is in no index.

## Sources outside this registry

Two ingest modules read files that are not registered here, are not in `data/raw/manifest.jsonl`, and are not fetched by `ingest.acquire`. They have no recorded SHA-256, URL or fetch time, which breaks the provenance rule stated below. Both are documented by hand:

| Module | Document | Status |
|---|---|---|
| `ingest/cbp_detail.py` | [CBP_DETAIL.md](CBP_DETAIL.md) | In use by the choice model; its lag guard is nominal |
| `ingest/osm_landuse.py` | [OSM_LANDUSE.md](OSM_LANDUSE.md) | Built, verified on three metros, blocked on Overpass |

A third data-collection attempt produced no usable source at all and is written up as a negative result: [SATELLITE.md](SATELLITE.md).

A fourth source arrived on 2026-09-14 and is not yet wired to anything: MWPVL International's public 2025 Q1 network article, read in [MWPVL_2025.md](MWPVL_2025.md). It is unregistered for the same reason as the two above and for one more — **its publisher has announced they are withdrawing it from free circulation**, so `ingest.acquire` could not re-fetch it in future even if it were registered. The saved copy and its retrieval date are the artefact. Note that this is a *different document* from the April 2012 MWPVL file excluded in [NLRB.md](NLRB.md) §5.2, and it reaches the opposite verdict.

That article's facility tables are **images, not text**, and were mined by a separate OCR pipeline written the same day: [MWPVL_OCR_PIPELINE.md](MWPVL_OCR_PIPELINE.md). It yields `data/interim/mwpvl_facilities.csv` — **1,904 Amazon facilities worldwide, 1,767 (92.8%) with a postal code, 1,420 (74.6%) with an opening year, 873 (45.9%) with an opening month** (`outputs/metrics/mwpvl_extraction.json`). **635 of them are US small-package delivery stations**, which is the only class [PANEL_EXPANSION.md](PANEL_EXPANSION.md) admits to the facility panel; the other 1,269 are fulfilment centres, sortation centres, cross docks, Fresh/Whole Foods DCs, air gateways, heavy/bulky stations and rest-of-world buildings, parsed and unused. Those are the project's first lower-bound-bearing opening dates; every other date on record is an OSHA-derived upper bound. Read it beside [SATELLITE.md](SATELLITE.md), which is the failed attempt at the same quantity. All thirteen of the document's tables are now parsed, and 3% of recovered rows merge into a neighbour — the pipeline doc states both.

> **Corrected 2026-09-14, evening.** The paragraph above read *"591 US delivery stations, 100% with a postal code, 446 (75%) with an opening year, 306 (52%) with an opening month"* and *"Two of the document's thirteen tables have been parsed so far"*. Both were true of the morning run and neither is now: the remaining eleven table images were parsed the same afternoon. The figures did not move because anything was wrong — the same code read eleven more images, plus a facility-code fallback row anchor for the rest-of-world tables, which have no US ZIP to key on. One thing genuinely changed: postal-code coverage is no longer 100%, because 137 rest-of-world rows print a non-US postal format or none.

## Status summary

| Status | Count | Meaning |
|---|---|---|
| OPEN | 7 | Acquired automatically |
| NEEDS KEY | 3 | Free credential required |
| BLOCKED | 2 | Refused by this network; manual download |
| MANUAL | 2 | No stable endpoint |

## Registry

| Key | Source | Grain | Declared | Probed | Lag |
|---|---|---|---|---|---|
| [acs5](acs5.md) | American Community Survey, 5-year estimates | `zcta` | NEEDS KEY | `unreachable` | 21 mo |
| [acs1](acs1.md) | American Community Survey, 1-year estimates | `metro` | NEEDS KEY | `needs_key` | 9 mo |
| [gaz_zcta](gaz_zcta.md) | Census Gazetteer, ZCTA national file | `zcta` | OPEN | `open` | — |
| [cbsa_county](cbsa_county.md) | OMB metropolitan area delineation, 2023 | `county` | OPEN | `open` | — |
| [zcta_county_xwalk](zcta_county_xwalk.md) | ZCTA-to-county relationship file, 2020 | `zcta` | OPEN | `open` | — |
| [tiger_zcta](tiger_zcta.md) | TIGER/Line ZCTA boundaries, 2020 vintage | `zcta` | OPEN | `open` | — |
| [cbp_zip](cbp_zip.md) | County Business Patterns, ZIP-code totals | `zip` | OPEN | `open` | 18 mo |
| [bps_county](bps_county.md) | Building Permits Survey, county annual | `county` | OPEN | `open` | 2 mo |
| [zillow_zori](zillow_zori.md) | Zillow Observed Rent Index, ZIP level | `zip` | BLOCKED | `unreachable` | 1 mo |
| [bls_oes](bls_oes.md) | Occupational Employment and Wage Statistics, metro | `metro` | BLOCKED | `blocked` | 12 mo |
| [eia_prices](eia_prices.md) | Regional fuel and industrial electricity prices | `region` | NEEDS KEY | `blocked` | 2 mo |
| [facility_panel](facility_panel.md) | Logistics facility panel with opening dates | `facility` | MANUAL | `manual` | 1 mo |
| [ejscreen](ejscreen.md) | EJScreen environmental justice indicators | `block_group` | MANUAL | `manual` | 12 mo |
| [osm](osm.md) | OpenStreetMap road network extracts | `network` | OPEN | `open` | 0 mo |

Reachability last measured **2026-09-12**.

## The hand-written pages

Everything above is generated from the registry. The pages below are written by hand, and they are where the reasoning lives.

### The target variable, and how far to trust it

- [`FACILITY_PANEL_PROVENANCE.md`](FACILITY_PANEL_PROVENANCE.md) — **Read this before quoting any date.** How the panel was built from OSHA enforcement records, the four collection methods that failed first, and the central caveat: `open_date` is an upper bound, not an opening. Selection bias quantified, defects listed with their fix status. The longest document in the folder.
- [`PANEL_EXPANSION.md`](PANEL_EXPANSION.md) — Merging the MWPVL 2025 Q1 extraction into the panel: every decision, both duplicate screens, and what the 693-row file admits and rejects.
- [`MWPVL_OCR_PIPELINE.md`](MWPVL_OCR_PIPELINE.md) — The OCR pipeline that turned thirteen table images into `mwpvl_facilities.csv`, with three validations attached before anything consumed it.
- [`MWPVL_2025.md`](MWPVL_2025.md) — The source article itself: what it is, why it is unregistered, and why its publisher withdrawing it does not break provenance.
- [`GEOCODING.md`](GEOCODING.md) — Geocoding the panel: 72.3% Match on 693 rows, and why the points are not yet joined into the panel.
- [`FACILITY_PANEL_HOWTO.md`](FACILITY_PANEL_HOWTO.md) — The brief that started the panel. Superseded as status, still the fastest route for anyone adding a source.
- [`SATELLITE.md`](SATELLITE.md) — The failed attempt at the same quantity: 36% of its own estimates date construction after OSHA proved the building was operating. A negative result, reported as one.
- [`NLRB.md`](NLRB.md) — Case filings as a delivery-station-skewed second source, and the capture-recapture coverage ceiling they support.

### Data quality — the audit, the literature, and the log

- [`DATA_QUALITY.md`](DATA_QUALITY.md) — The audit of this pipeline against the published cleaning literature. Findings F1-F5, each with the measurement behind it. The second-longest document in the folder and the one a reviewer will open.
- [`CLEANING_LITERATURE.md`](CLEANING_LITERATURE.md) — The data-cleaning argument, written after the papers were actually read: Fellegi-Holt, Rahm & Do, Van den Broeck, Winkler. What each licenses and what it does not.
- [`CLEANING_CHANGELOG.md`](CLEANING_CHANGELOG.md) — Every cleaning decision, dated, with the uncorrected-against-corrected cross-tab Van den Broeck asks for.
- [`UNCERTAINTY.md`](UNCERTAINTY.md) — 500 joint draws over every documented parameter. How far the answer moves when all of them move at once — and the three fields that were not sampled, with reasons.

### The cost and portfolio layer

- [`COST_MODEL.md`](COST_MODEL.md) — The cost model explained from zero: why the answer turns on delivery density and depot distance, and how to read its table.
- [`PARAMETERS.md`](PARAMETERS.md) — Every free parameter, its source, and what it is worth. Names the constants that have no published source and measures how far the headline moves when each one is swept.
- [`HIGHWAY_ACCESS.md`](HIGHWAY_ACCESS.md) — Highway access built and measured on 14,767 ZCTAs. It does not move the model, and that is the finding.
- [`CBP_DETAIL.md`](CBP_DETAIL.md) — County Business Patterns detail — in use by the choice model, and its lag guard is nominal. Unregistered.
- [`OSM_LANDUSE.md`](OSM_LANDUSE.md) — OpenStreetMap land use: built, verified on three metros, blocked on Overpass. Unregistered.

### Operating the data layer

- [`ACQUISITION_GUIDE.md`](ACQUISITION_GUIDE.md) — What to download by hand, where to put it, and how to check it landed. Covers the six sources that do not fetch automatically, in priority order.
- [`ARTEFACTS.md`](ARTEFACTS.md) — Every JSON file in `outputs/metrics/`, reconciled against disk: what wrote it, when, and whether anything still reads it.
- [`FIGURES.md`](FIGURES.md) — The figure layer — what draws what, and what each figure depends on, confirmed by following the imports.

## The rule these sources obey

> Every source must be free, public, and re-downloadable by a stranger.

This is the contribution, not a budget constraint. A model built on licensed data produces conclusions nobody can check, which is precisely the situation the project exists to fix. Where a better paid source exists we take the public one and report the cost of that choice.

## Provenance

Every download is written once into `data/raw/<source>/<hash>.<ext>` and appended to `data/raw/manifest.jsonl` with its SHA-256, byte count, Content-Type and the run that fetched it. A reviewer can re-download from the recorded URLs and verify the hashes.

## Commands

```bash
python -m siting_atlas.ingest.acquire --list      # show registry
python -m siting_atlas.ingest.probe               # measure reachability
python -m siting_atlas.ingest.acquire             # fetch what is reachable
python -m siting_atlas.ingest.acquire --include-large
```

---

*Generated from the registry. Run `python tools/docs/gen_data_docs.py` after changing sources.*
