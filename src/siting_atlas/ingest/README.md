# ingest/ — L0 acquire, L1 normalise

The widest package in the project: 38 modules. `sources.py` declares what
exists, `probe.py` measures what is reachable from *this* machine right now,
`acquire.py` downloads into a content-addressed cache, and `normalise*.py`
turns each raw download into exactly one typed parquet. Everything downstream
reads parquet, never a raw file.

```bash
make probe         # what is reachable
make acquire       # fetch (needs CENSUS/EIA keys)
make normalise     # one typed parquet per keyless source
make normalise-external   # the same for hand-placed files
python -m siting_atlas.ingest.external --check   # validate manual sources
```

## The registry and the cache

```
  sources.py       the 14 declarations. Long, because each records the trap
  source_types.py  the vocabulary a source is described in
  registry.py      the registry object. Reference data, not logic
  probe.py         reachability, measured rather than declared
  acquire.py       download into data/raw/<source>/<hash>.<ext> and append a
                   line to data/raw/manifest.jsonl with URL, SHA-256, bytes
                   and content type. That manifest ships, so a reviewer can
                   re-download and verify
  census_api.py    ACS, separate from acquire.py because an API paginates
  eia_api.py       regional energy prices, same reason
  external.py      validate the hand-placed sources in data/external/
```

## Normalisation

```
  normalise.py           the keyless sources
  normalise_external.py  the three large hand-placed ones (ZHVI, OES,
                         EJScreen), each trimmed before reshaping
  normalise_geo.py       the crosswalks that let every other source find a
                         ZCTA. These decide the SHAPE of the panel
  shapes.py              shared readers. `_zpad` is the single most important
                         function in L1: '01890' read as an integer is 1890,
                         and 1890 joins to nothing -- New England and Puerto
                         Rico simply vanish
```

## The facility panel, and how it was actually assembled

```
  osha.py              pull Amazon facilities out of the national OSHA
                       inspection extract. Every other attempt to date
                       last-mile facilities failed; this one worked
  osha_archive.py      stream the 1.4 GB multi-part DOL zip without
                       unpacking it
  address_audit.py     MEASURE the address matcher instead of trusting it.
                       The previous matcher was never measured
  facility_check.py    column-level validation of the target variable
  geocode_facilities.py  coordinates via the free Census batch geocoder.
                       Reaches 72.3% (501 of 693) and the points are NOT yet
                       joined into the panel
```

## The MWPVL OCR pass

The tables are images; `tools/ocr/` does the pixel work and these modules
turn its output into rows.

```
  mwpvl_grid.py      a bag of OCR'd words with pixel boxes back into table
                     cells. Recovers the grid; interprets nothing
  mwpvl_fields.py    decides what each column means and pulls structure out
  mwpvl_tables.py    every TSV into one CSV of facilities
  mwpvl_panel.py     test the OCR'd opening dates against the OSHA record
  mwpvl_coverage.py  how many delivery-station cities the best free source
                     actually sees. Writes the 488 / 340 / 138 visibility gap
```

## Independent lists, and the covariates

```
  nlrb.py              Amazon worksites from the NLRB case-search export.
                       Here for the DENOMINATOR, not the rows
  nlrb_names.py        is this case about Amazon, and is this city that city
  nlrb_estimators.py   capture-recapture, and what each estimator may claim
  cbp_detail.py        County Business Patterns ZIP x industry -- the
                       warehousing covariate the choice model rests on. Its
                       lag guard is the subject of the leakage tests
  osm_landuse.py       industrially-zoned land per ZCTA
  subsidies.py         Good Jobs First subsidy tracker. Read its
                       `what_this_cannot_support` field first
  tiger_*.py           8 modules: fetch the two road layers, cluster ramps
                       into interchanges, compute distance in a projection
                       that works, build the frame, fit six specifications,
                       print, and scope the artefact's edge
```

## Two standing caveats

**Two ingest modules read files that are not in the registry** —
`cbp_detail.py` and `osm_landuse.py`. They have no recorded SHA-256, URL or
fetch time, which breaks the provenance rule the rest of the package obeys.
Both are documented by hand in `docs/data/`.

**`eia_prices` is registered as both an API and a manual source**, so
`external --check` reports it `missing` on every run. Correct and misleading;
one line to fix.

Full per-source detail:
[`docs/DATA_SOURCES.md`](../../../docs/DATA_SOURCES.md) and
[`docs/data/README.md`](../../../docs/data/README.md).
