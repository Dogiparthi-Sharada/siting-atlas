# data — mostly empty, and that is deliberate

If you cloned this repository and found this directory nearly bare, nothing is
broken. **The published repo ships derived data only.** The full tree is 4.5 GB
locally; four files exceed GitHub's 100 MB limit and two sources are licensed
in a way that does not let us redistribute them.

**Everything not here is fetchable.** The recipe is
[`docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md) — one section per dataset,
with the URL, the command, the key (if any), the size, the licence and the
vintage. Read its final section first: most of the project's headline results
rebuild from what is already in your clone, with no downloads at all.

---

## What is here

```
  data/
    processed/    panel.parquet, panel_expanded.parquet,          73 MB
                  panel_national.parquet, siting_atlas.duckdb
                  -- the frame every model reads
    interim/      one typed parquet per source, plus            ~15 MB
                  osha_amazon.csv, mwpvl_facilities.csv,
                  nlrb_amazon.csv
    external/     facility_panel/ (the target variable),        ~1.5 MB
                  nlrb/, satellite/, TEMPLATE.csv stubs
    raw/          manifest.jsonl ONLY -- URL, SHA-256, byte        16 KB
                  count and content type for every automatic
                  download the project has ever made
    collection/   the facility-panel working papers: prompts,    176 KB
                  keys and results from the collection effort
```

`data/raw/manifest.jsonl` is the provenance record and the place to start if
you want to know where a byte came from. Every URL in `DATA_SOURCES.md` can be
checked against it.

## What is not here, and why

```
  what                                   size     why not
  -------------------------------------  -------  --------------------------
  raw/osha_bulk/      DOL inspections    1.4 GB   too large; free to fetch
  raw/tiger_roads/    per-county ROADS   1.6 GB   too large; free to fetch
  raw/tiger_zcta/     ZCTA boundaries    528 MB   too large; free to fetch
  raw/cbp_zip_detail/ CBP ZIP x NAICS    119 MB   too large; free to fetch
  raw/geofabrik/      OSM .pbf extract    50 MB   NEVER READ -- ADR-0002 was
                                                  designed and not built
  external/zillow_*/  ZHVI and ZORI      128 MB   Zillow Research terms do
                                                  not grant redistribution
  external/ejscreen/  EJScreen 2024       51 MB   too large; free to fetch
  external/bls_oes/   OES May 2025        40 MB   too large; free to fetch
  external/subsidies/ Good Jobs First    349 KB   PURCHASED under a USD 25
                                                  subscription licence
  raw/mwpvl/*.pdf     MWPVL articles      12 MB   third-party copyright
  interim/zcta_geom.parquet              526 MB   derived; rebuild from
                                                  tiger_zcta
  interim/zillow_zhvi.parquet             47 MB   derived from a source we
                                                  cannot redistribute
```

For the two licensed sources, the **derived facts do ship**: the MWPVL
extraction as `interim/mwpvl_facilities.csv` (1,904 facilities, attributed to
MWPVL International), and the subsidy aggregates as
`outputs/metrics/subsidies.json`. `DATA_SOURCES.md` §14 and §15 say where to
obtain the originals yourself.

## Rebuilding

```
  layer         rebuild command                     needs
  ------------  ----------------------------------  ---------------------
  raw/          make acquire                        network + 2 API keys
  external/     (none -- placed by hand)            see DATA_SOURCES.md
  interim/      make normalise                      raw/
                make normalise-external             external/
  processed/    make warehouse && make panel        interim/
  collection/   (none -- a one-off paper trail)     --
```

A hand edit under `interim/` or `processed/` is lost the next time the stage
runs. A hand edit under `collection/` or `external/` is permanent and
unrecorded — do not make one without also writing it into `docs/data/`.

Validate anything you place in `external/`:

```bash
python -m siting_atlas.ingest.external --check
```

## Two warnings before you trust what is here

**ZIP codes are zero-padded strings, always.** As integers `01890` becomes
`1890` and every join silently loses those rows — no error, no warning, just a
smaller answer. `ingest/shapes.py:_zpad` is the single most load-bearing
function in the normalisation layer. Excel and Google Sheets strip leading
zeros on save; this has already cost the project once.

**The facility panel is a small, biased sample.** 43 rows in 10 metros against
roughly 700–900 US delivery stations; most dates are OSHA-derived *upper
bounds* rather than opening dates; and OSHA inspects where people get hurt, so
the source sees fulfilment centres far better than the delivery stations the
model is about. All of it is measured and written up in
[`../docs/data/FACILITY_PANEL_PROVENANCE.md`](../docs/data/FACILITY_PANEL_PROVENANCE.md)
and [`../docs/data/DATA_QUALITY.md`](../docs/data/DATA_QUALITY.md).

## The rule the tree obeys

> Every source must be free, public, and re-downloadable by a stranger.

That is the contribution, not a budget constraint. Where a better paid source
exists, the public one is taken and the cost of that choice is reported. The
two exceptions above are documented as exceptions, with their derived facts
published in place of the originals. See
[`../docs/adr/0003-public-sources-only.md`](../docs/adr/0003-public-sources-only.md).
