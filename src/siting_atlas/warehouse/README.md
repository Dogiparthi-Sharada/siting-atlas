# warehouse/ — L2 star schema and L3 the panel

Typed parquet in, one panel out. Everything above this layer reads
`data/processed/panel.parquet` and nothing else, which is the property that
makes a second volume a data swap rather than a rewrite.

```bash
make warehouse     # L2  python -m siting_atlas.warehouse.schema
make panel         # L3  python -m siting_atlas.warehouse.panel
```

Grain: **one row per ZCTA per quarter**, 2018Q1–2025Q4. 1,081,312 rows × 50
columns (`outputs/metrics/panel_report.json`, run `20260914-220244-d57b`).

## Modules

### The schema and the panel

```
  schema.py      L2. Typed parquet becomes a Kimball star in DuckDB. L1 gives
                 one parquet per publisher, each on its own grain; this
                 conforms them
  geo_keys.py    L2 key bridges -- the lookups that make two vintages of a
                 code system join. Reference tables, not logic
  panel.py       L3. The warehouse becomes the one panel every model reads
  panel_sql.py   the text of the panel query, split from the code that runs it
  optional.py    attaching sources whose schema this code has not seen.
                 Skip loudly, never guess
  flag_gate.py   the L3 gate: a quality flag that is computed MUST reach the
                 panel. It failed on the code as it stood, naming three flags
```

### The target variable

```
  facilities.py      turn a facility list into the `enabled` column. The one
                     piece of code between a delivered facility file and a
                     fitted model. Only DS and SDC set the target; catchment
                     is a radius (15 mi DS / 10 mi SDC) standing in for a
                     drive-time isochrone; pre-2018 facilities are kept as
                     LEFT-CENSORED rather than dropped
  facility_load.py   reading the panel: typing, the quarter index, provenance
  facility_dedup.py  adjudicating rows that describe one building and
                     disagree about it. Rahm & Do separate DUPLICATED from
                     CONTRADICTING records, and the distinction is
                     load-bearing here -- a duplicate is a nuisance, a
                     contradiction in the outcome is a defect
  catchment_band.py  the radius sensitivity band facilities.py asks for
  edits.py           the declared edit set (Fellegi-Holt), dispositions
                     EXCLUDE / REPORT. CORRECT is deliberately absent
  national.py        promote the national facility frame, and measure what it
                     buys
```

### The MWPVL merge

```
  mwpvl_shape.py   OCR'd rows into the panel schema. Nothing here corrects a
                   value -- three things happen and all three are relabelling
  mwpvl_geo.py     postal code -> ZCTA -> county -> CBSA, from crosswalks
                   already on disk
  mwpvl_merge.py   the merge itself, and the facility-class filter that keeps
                   1,269 rows of the wrong class out of a US delivery-station
                   panel. Writes outputs/metrics/mwpvl_merge.json
  mwpvl_report.py  counting for the merge
  mwpvl_print.py   printing for the merge. Computes nothing
  batch_candidates.py  the hand-labelled batches, deduplicated
```

## What to know before trusting the output

- **The `enabled` column is 100% non-null and 2.58% TRUE.** Any document
  claiming it is `0.00%` populated is reading a stale coverage table.
- **`enabled_flags` takes `min(open)` / `max(close)` per ZCTA**, so a gap
  between one station closing and another opening is silently filled.
  Harmless for first-enablement, wrong for the cost and visualisation layers.
- **The expanded facility file fails `ingest/facility_check`** — 142 rows have
  a non-numeric `open_year`. Carried deliberately; the two ways to clear it
  are to drop the rows or invent a year.
- The counts behind all of this are in
  [`docs/NUMBERS.md`](../../../docs/NUMBERS.md) §1 and §7.
