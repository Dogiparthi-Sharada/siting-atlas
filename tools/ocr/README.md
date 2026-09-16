# OCR — recovering the facility table from an image-only PDF

This is how the 1,904 facilities in
[`data/interim/mwpvl_facilities.csv`](../../data/interim/mwpvl_facilities.csv)
were produced. **You do not need to run it.** The extracted table ships with
the repository and the results reproduce from it without touching any of this.

Read this if you want to check the extraction, adapt it to a different
document, or understand the provenance of the target variable.

---

## The problem

MWPVL International publishes a network inventory of Amazon facilities. Its
tables are **images** — thirteen of them, one long strip per table, up to
828 × 26,480 pixels. There is no text layer, no table structure, and no
machine-readable release. Copy-paste gets you nothing.

## The approach

Three modules, each doing one thing:

| Module | Job |
|---|---|
| [`mwpvl_layout.py`](mwpvl_layout.py) | Map each extracted page image to the table it belongs to, using `pdfimages -list` for the page index and `pdftotext` for the headings |
| [`mwpvl_strip.py`](mwpvl_strip.py) | Cut a tall strip into overlapping tiles small enough for the OCR engine, and rebase every word's coordinates back onto the original image |
| [`grid_ocr.py`](grid_ocr.py) | Orchestrate: preflight, tile, OCR each tile to word-level TSV, stamp the settings used, reuse images already extracted |

The geometry — turning a bag of positioned words back into rows and columns —
lives in the package proper, at
[`src/siting_atlas/ingest/mwpvl_grid.py`](../../src/siting_atlas/ingest/mwpvl_grid.py),
because it is tested. Two ideas carry it:

- **Columns are recovered from vertical valleys in word density.** A table has
  gutters; gutters have no ink. Scanning the x-axis for sustained low-density
  bands finds the column boundaries without knowing anything about the table.
  A fixed grid was tried first and leaked words between adjacent columns.
- **Rows are anchored on postal codes.** Every record has one, it matches a
  tight regular expression, and it sits on the *last* line of its row — so a
  word is assigned to the first anchor at or below it, not the nearest one.

## What you need to run it

```
  tesseract  >= 4      the OCR engine. A C program; pip cannot install it
  poppler-utils        supplies pdfimages and pdftotext, also C programs
  Pillow               pip install pillow
  the source PDF       not in this repository -- see below
```

```bash
# Debian / Ubuntu
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

Then:

```bash
python tools/ocr/grid_ocr.py --pdf /path/to/the.pdf --out data/raw/mwpvl
```

## Machine requirements — measured, not guessed

The OCR itself is **not** demanding: thirteen images totalling about 12 MB,
tiled before they reach tesseract. Any laptop will do it.

The rest of the project is heavier, and this is the honest picture:

```
  reproducing the published results   ~1 GB peak      (make reproduce)
      cost.runner                       976 MB
      models.choice_runner              366 MB
      report.scope                      156 MB
      viz.build                         205 MB

  rebuilding from raw sources        8 GB recommended (Path B in the README)
      the TIGER ZCTA geometry alone is a 526 MB parquet, and the
      ZCTA-quarter panel is 1,081,312 rows before any join
```

So: **8 GB of RAM if you are rebuilding the data layers from scratch, 2 GB if
you are only reproducing the results.** Disk is the bigger constraint for
Path B — about 4 GB of downloads.

## The source document

The PDF is **not** in this repository. It is third-party copyright, and the
publisher states in the article itself that it is being withdrawn from free
circulation. The *facts* extracted from it ship, attributed;
the document does not. [`docs/DATA_SOURCES.md`](../../docs/DATA_SOURCES.md)
says where to obtain it and credits MWPVL.

This is also a real limitation rather than a formality: if the article goes
away, the extraction is not re-runnable by anyone who did not already have a
copy. That is recorded as a threat to validity in the paper.

## A note on what used to be here

Until 2026-09-16 this directory was `scripts/grid/` and carried three shell
scripts that relocated tesseract, glibc and the dynamic loader onto a
locked-down compute grid running Python 3.6. They worked, and they are
useless to anyone else — they solved one institution's environment, not an
OCR problem. They were removed rather than published, because a script that
appears necessary and is not costs a reader more than it saves.

## Related

- [`docs/data/MWPVL_OCR_PIPELINE.md`](../../docs/data/MWPVL_OCR_PIPELINE.md) —
  the full write-up, including the reading-order bug that cost 22 points of
  geocoding match rate
- [`docs/ALGORITHMS.md`](../../docs/ALGORITHMS.md) — the geometry, stated precisely
- [`data/collection/satellite/colab_date_from_satellite.py`](../../data/collection/satellite/colab_date_from_satellite.py) —
  a standalone Colab notebook that attempts the same problem (dating
  facilities) from Sentinel-2 imagery. It runs anywhere, needs no key, and
  **failed**: 36% of its estimates date construction after an inspector had
  already found the building operating. Kept as a documented negative result
