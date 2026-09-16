# Reading the MWPVL tables — the OCR pipeline that produced 1,420 opening dates

*Built 2026-09-14. Scripts `tools/ocr/{grid_ocr,mwpvl_layout,mwpvl_strip}.py`
and `tools/ocr/{setup_venv,run_ocr,bundle_tesseract}.sh`; parsers
`src/siting_atlas/ingest/{mwpvl_grid,mwpvl_fields,mwpvl_tables}.py`. Output
`data/interim/mwpvl_facilities.csv` (1,904 rows) and
`outputs/metrics/mwpvl_extraction.json`.*

> **Corrected 2026-09-14, evening. The work moved on; nothing here was wrong.**
> This document was written after the **first two** of MWPVL's thirteen table
> images had been run, and every figure in it described that run: 591
> facilities, 446 years, 306 months, 18 `not_confirmed`, and a §13.3 headed
> *"Eleven of the thirteen tables have not been parsed"*. **All thirteen have
> now been parsed.** `outputs/metrics/mwpvl_extraction.json` today reports
> **1,904 facilities, 1,420 with a year, 873 with a month, 44 `not_confirmed`**.
>
> ```
>   figure                       WAS (2 tables)   IS (13 tables)
>   ------------------------------------------------------------
>   facilities                        591            1,904
>   with a postal code                591  100%      1,767  92.8%
>   with an opening YEAR              446   75%      1,420  74.6%
>   with an opening MONTH             306   52%        873  45.9%
>   not_confirmed                      18                44
>   tables parsed                    2 of 13         13 of 13
>   ------------------------------------------------------------
> ```
>
> The **method sections are untouched and still correct** — the strip layout,
> the grid reader, the field parsers, the confidence handling and every
> measured defect in §13 all describe the same code, run over more images. Two
> things did change substantively and are marked where they occur: the postal
> code is no longer present on 100% of rows (the rest-of-world tables have
> non-US postcodes, or none), and the rest-of-world tables were only readable
> once a **facility-code fallback anchor** was added, because they do not carry
> a US ZIP for the row anchor to key on.
>
> Inline figures below are brought to the artefact. This block is the record of
> what they were.

[`MWPVL_2025.md`](MWPVL_2025.md) covers the article's **text layer** — the
prose, the withdrawal notice, the five findings that needed no OCR. This
document covers the **image layer**, which is where the opening dates are. Do
not read one as a summary of the other; they were mined by different means on
the same day and the prose section says outright that the tables are the only
route to a delivery-station date.

**This worked.** [`SATELLITE.md`](SATELLITE.md) is the write-up of the attempt
that did not, and the two should be read together: the same gap, two methods,
one negative and one positive, both measured against the same OSHA bound.

---

## 0. What it produced

`outputs/metrics/mwpvl_extraction.json`, and every figure below is read from
that file rather than remembered:

```
  facilities                     1,904
  with a postal code             1,767   92.8%
  with an opening YEAR           1,420   74.6%
  with an opening MONTH            873   45.9%
  flagged "not confirmed"
    by MWPVL itself                 44

  01_us_fulfillment_center            385 rows    9,877 words
  02_us_fresh_dc                       22 rows      569 words
  03_us_whole_foods_dc                 11 rows      242 words
  04_us_fresh_hub                      65 rows    1,438 words
  05_us_inbound_cross_dock             69 rows    1,400 words
  06_us_sortation_center              114 rows    2,749 words
  07_us_air_gateway_hub                24 rows      637 words
  08_us_delivery_station              535 rows   11,975 words
  08_us_delivery_station_part2        100 rows    2,162 words
  09_us_delivery_heavy_bulky          121 rows    3,177 words
  10_row_fulfillment_center           160 rows    8,025 words
  11_row_sortation_delivery_air       249 rows   13,394 words
  11_row_sortation_delivery_air_part2  49 rows    2,443 words
  ----------------------------------------------------------
                                    1,904 rows   58,088 words
```

1,904 street addresses with square footage and, for three quarters of them, a
year the building opened. **635 of them are US small-package delivery
stations** — the project's target class, and the only class
[`PANEL_EXPANSION.md`](PANEL_EXPANSION.md) lets into the facility panel. That
is the first lower-bound-bearing date the project has ever held for a delivery
station.

**Postal-code coverage is no longer 100%, and the shortfall is entirely
rest-of-world.** All 137 rows without one sit in two tables —
`10_row_fulfillment_center` (68 of 160 have a postcode) and
`11_row_sortation_delivery_air_part2` (4 of 49) — which print non-US postal
formats or none at all. Every US table is still at 100%.

**It is not a census and it is not ground truth.** MWPVL says so about this
exact table — *"The data concerning this network is challenging to track so we
provide the best information available within the table below"* — and the
project holds something better than plausibility to test it against: 409 cities
where OSHA proves a building was operating by a given day. The dates are
delivered raw, uncleaned, for `warehouse/edits.py` to adjudicate against that
bound. See §10.

## 1. Why this was worth building

Every facility in the panel has an **upper** bound on its opening and no lower
bound. Measured 2026-09-14 and recorded in
[`CBP_DETAIL.md`](CBP_DETAIL.md) §5: for **all 100 of 100** matched national
rows, `open_year` and `open_quarter` equal the quarter of the earliest OSHA
inspection exactly. So `open_year` is not an opening date; it is the OSHA
bound wearing a date's name.

That one gap makes the CBP lag guard nominal on the covariate that carries the
entire choice model, blocks any use of time in that model, killed the hazard
model's event timing, and blocks Option D in
[`../ALTERNATIVES.md`](../ALTERNATIVES.md) outright — *"It needs opening DATES
to define before and after ... Do not start this until the dates exist."*

Satellite imagery was the cheap route and it failed: 36% of its estimates date
construction after the day an inspector stood in the building
([`SATELLITE.md`](SATELLITE.md) §4). MWPVL simply states the month and the
year. The only obstacle is that the tables are pictures.

## 2. The shape of the problem

The saved PDF is 117 pages, 11.3 MB. `pdftotext -layout` returns 1,074 lines,
of which perhaps 120 are prose — the tables are not in the text layer at all.
They are **13 distinct table images totalling 152,915 pixel-rows**, embedded
once each and referenced from every page they span (the delivery-station table
is one object referenced from twenty-three pages).

There are no captions inside the images. A table is a bare grid of pixels with
no title, so an image on its own cannot say what it holds.

So the pipeline has four problems, in order: *which images are tables*, *which
table is which*, *where the columns and rows are*, and *what each cell means*.
Each of the next four sections is one of them, and each records the wrong
answer that was tried first, because in every case the wrong answer produced
plausible output and no error.

## 3. Which images are tables — the filter that silently lost five

**The first version filtered on HEIGHT > 5,000 px.** It kept 8 images. There
are 13. The five it dropped:

```
  Amazon Fresh DC          1,576 px
  Whole Foods DC             665
  Fresh Hub                3,744
  Inbound Cross Dock       3,975
  Air Gateway              1,753
  -----------------------------------
                          11,713 pixel-rows, about 8% of the table content
```

Nothing failed. The run completed, wrote output and reported success. You get
fewer facilities and no error — which is the failure mode this whole document
keeps returning to.

**The fix is to filter on WIDTH.** Every table in this document is rendered
803-828 px wide; the page furniture is not (banners at 1137x42, the logo at
2525x254, the per-page decoration at 1464x1103). `TABLE_WIDTH = (780, 900)` in
`mwpvl_layout.py` separates them with room to spare, and height is now used
only to drop slivers (`MIN_HEIGHT = 300`).

`mwpvl_layout.EXPECTED_TABLES = 13` exists so that a run finding a different
number says so in its log rather than quietly producing a short answer.

## 4. Which table is which — page tagging, not guessing

Two facts, each read from the document by a command anyone can re-run:

```
  pdftotext      gives each section HEADING and the page it sits on.
                 "The Amazon 'Last Mile' Delivery Station Network for Small
                 Packages in the United States" is on page 38.
  pdfimages -list gives the first page each IMAGE appears on.
                 The image of object 137 first appears on page 39.
```

A table on page 39 belongs to the heading on page 38. Deterministic, checkable,
and it does not depend on reading the table's contents.

**It was verified anyway.** Each table's first 700 rows were OCR'd and the
facility codes checked against the section: DBM3/DBM4 under delivery stations,
YYC1/YHM2 under rest-of-world, HBM3/HPX1 under heavy/bulky. The assignment and
the check are independent, which is the point of doing both.

Two details that are easy to get wrong:

- **Boundaries are keyed on the page each TABLE begins, not on heading pages.**
  Page 24 carries two headings (Whole Foods, then Fresh Hub) and heading-page
  boundaries cannot separate them. Table-start pages can, and they are known
  exactly from `pdfimages -list`. The eleven page numbers in
  `mwpvl_layout.SECTIONS` are data, not estimates.
- **Deduplication is by PDF object id, not by pixel hash.** Hashing gives the
  same answer and costs a decode of all 112 copies of the fulfilment-centre
  table to learn what the object id already said.

The extraction workdir is also **cleared before every run**. `pdfimages`
numbers its output by object order and does not remove files it did not write,
so re-running over the old dump can leave a stale PNG occupying the exact
filename a real table needs — a success that is partly OCR of last week's
images.

## 5. Plain-text OCR: built, measured, abandoned

This is the decision the rest of the pipeline is built around, so it is stated
with the evidence that forced it.

MWPVL's rows wrap over **two to four printed lines**, so reading order
interleaves neighbouring cells. Verbatim from a text-mode run:

```
    7200 Chavenelle Road,          January
    Iowa  WWI2  Dubuque, Iowa, USA, 52002  120,000  9022
```

"January" and "9022" are **one cell** — a date — split across two lines by the
address wrapping underneath it. Nothing downstream can rejoin them reliably
from text alone, and the date is the only reason the document is being mined.

In tesseract's `tsv` mode the same two tokens come back as
`January left=1923 top=47` and `9022 left=1969 top=119`: 46 px apart in x, both
inside the Year Opened column. Group by column, then by row band, and the cell
reassembles from geometry.

So: **columns from x, rows from y**. Text mode was measured, found unable to
carry a date, and thrown away.

## 6. Strips and the OCR settings, all measured

The tables are tens of thousands of pixels tall — 152,915 pixel-rows across
thirteen of them — and cannot be handed to tesseract whole, so each is cut into
overlapping strips (`mwpvl_strip.py`). The delivery-station table takes 33
strips and its continuation 3, which is what `data/raw/mwpvl/tsv/` holds today.

```
  STRIP     1400 px    a printed row is ~60 px; one whose address wraps runs
  OVERLAP    400 px    to 250. 400 guarantees no row is cut in half by BOTH
                       strips containing it -- without it a facility landing
                       on a boundary is lost twice and leaves no trace.
```

Every box is rebased into **original image coordinates** (divide by the upscale
factor, add the crop offset) before it is written. That is what makes the
overlap stitchable: two strips that both saw a row report its words at the same
place, so duplicates are removed by **position** on an 8-px lattice.
Deduplicating by string instead would delete genuine repeats — two facilities
in one city share most of their address words.

Upscale and page-segmentation mode were chosen by measurement on a 1,400-px
sample, not by reputation:

```
  upscale   1x -> 23 ZIPs    2x -> 26    3x -> 26    4x -> 26
  psm        4 -> 15 dates    6 -> 17    11 ->  5   12 ->  6
```

2x is where the gain saturates. **4x is used anyway** — on a 16-core node the
extra pixels cost wall-clock nobody is waiting on, and a recovered digit is a
facility that does not have to be thrown away. `psm 6` wins outright.

One operational measurement: tesseract links OpenMP and fans out to **~265% CPU
inside a single process**. With 14 workers that oversubscribes a 16-core node
threefold and everything slows down together, which presents as the job being
slow rather than the job fighting itself. `OMP_NUM_THREADS=1` is set per child,
and workers are `nice`d by 5 because the node is shared.

Every strip writes its own TSV and is skipped if that file exists, so the job
survives being killed and a partial run can be parsed while the rest continues.

## 7. Columns — low-density bands, not empty ones

`mwpvl_grid.column_bounds` projects every word box onto the x axis, counts how
many words cover each pixel column, and cuts at the middle of each sustained
low-density run.

**The first version tested for ZERO coverage and found no columns at all.** On
a table with six columns it returned `[0, 819]` — the whole table as one
column. Over 540 rows there is always some row whose description overflows or
whose address wraps into the gutter, so no x is ever completely empty.

The gutters are real but shallow, and the measurement shows how shallow:

```
  centre of the address column      1,385 words        gutter beside it     3
  square-footage column               490 words        gap after it        65
```

`GUTTER_FRACTION = 0.10` separates every one of the five gutters from every
one of the six columns with an order of magnitude to spare.
`MIN_GUTTER = 12 px` because the narrowest real gutter measured on the
delivery-station table — the one before the address column — is 13 px.

This is self-calibrating on purpose. The thirteen tables do not share a layout:
the US tables start with State, the rest-of-world tables start with a flag icon
and a Country column, which shifts everything right. A hardcoded boundary would
mis-assign every rest-of-world row and report nothing wrong.

## 8. Rows — anchored on postal codes, and three bugs that each looked fine

Every facility row ends its address with a postal code, and nothing else in
that column looks like one. Their y-centres are the row anchors. Anchoring on
the tallest column instead fails, because the description cell often wraps to
more lines than the address and drifts out of alignment.

Three bugs were found in this one function, and **all three produced plausible
output with no error**. Each was found by measuring the rows that failed to
anchor, not by anticipation. Their combined effect on the delivery-station
table:

```
                        rows   clean   merged
  before the fixes       510     469      41     92%
  after the fixes        535     517      18     97%
```

### 8.1 Midpoint banding, defeated by variable row heights

The obvious rule — a row is the band between the midpoints of its neighbouring
anchors — was the first thing tried, and it fails. The printed layout is:

```
  y=2617   275 Valencia Avenue, Brea,             address, line 1
  y=2625   DJT4 | 181,500 | 2025 | Delivery...    everything else
  y=2634   California USA. 92823                  address, line 3  <- ANCHOR
```

The postal code sits on the **last** line of its row, so a row occupies the
space **above** its anchor. Row heights vary with how far the address wraps —
gaps of **48 px and 64 px measured in the same table** — so the midpoint
between two anchors falls *above* the next row's first line, which then joins
the previous facility's address. Two corrupted rows, no error.

Fix: a word belongs to the **first anchor at or below it** (`build_rows`,
binary search, tolerance 8 px for the scatter of words on the anchor's own
line). Words below the last anchor join the final row rather than being
dropped.

### 8.2 Five-digit street numbers invented facilities

A US street address contains two five-digit numbers and only one is a postal
code:

```
  20920 Krameria Ave, March Air Reserve Base, California, USA, 92518
  ^^^^^ house number                                          ^^^^^ ZIP
```

Both match `\d{5}`. Treating the house number as an anchor **invents a
facility** — measured here as a row containing the fragment
`20920 Krameria Ave, March Air` and nothing else, while the real facility lost
its first address line. Two damaged rows, no error, and the row count looks
right.

Fix: `_ends_its_line` — a house number is followed by the street name on the
same printed line; a postal code ends the address. Position, not shape,
separates them. Testing for "leftmost" instead would fail, because a postal
code that wraps onto a line of its own is both leftmost *and* rightmost.

### 8.3 A table border rule broke the test that fixed 8.2

The table is drawn with ruled borders, and a vertical rule OCRs as `|` sitting
just to the right of the last real word. So `94561 |` reads as a postal code
with something after it, the anchor is rejected, and **that facility merges
into its neighbour**. Observed on exactly that ZIP before the filter existed.

Fix: `_ends_its_line` ignores tokens with no alphanumeric character.

### 8.4 Two tolerated OCR manglings, also found by measurement

`ZIP_RE` matches a token *ending* in five digits so that `143,200` and `2025`
cannot match, and tolerates the two ways the code comes back damaged:

```
  92081-2607   clean ZIP+4
  85034-       ZIP+4 split across tokens; the "6852" arrives separately and is
               only four digits, so a strict pattern matches NEITHER half and
               the row silently merges into its neighbour
  USA36322     the comma and space between "USA," and the code dropped
```

Two anchors closer together than a printed line (20 px) are collapsed — one row
read twice, or a ZIP+4 split across tokens.

### 8.5 Reading order inside a cell — a 12-pixel lattice, and 22 points of geocoding

*Found 2026-09-14, from [`GEOCODING.md`](GEOCODING.md) §5, which measured
hand-collected panel rows geocoding at 83.7% against these rows' 61.7%.*

Rows 8.1–8.4 got each word into the right **cell**. This is about the order
they come back out in. A cell holds two to four printed lines and they have to
be rejoined top-to-bottom, then left-to-right. The first version sorted on
`(cy // 12, cx)` — put each word in a fixed 12-pixel band, then order within
the band.

**A fixed lattice has edges, and words sharing a printed line straddle them.**

```
  cy=1186  cx=304  'Road,'    -> band 98
  cy=1188  cx=265  'Higley'   -> band 99     the same printed line
```

"Higley" sorts after everything else on its own line and lands beside the first
word of the line below. What comes out of the cell is

```
  3115 N. Road, Mesa, Higley Phoenix, Arizona, USA, 85215
```

for what the page prints as `3115 N. Higley Road, Mesa, Arizona, USA, 85215`.
The street has lost its name and the city has gained a word, and **nothing
downstream can tell**: the row still has a five-digit postal code, a state that
resolves, and a street that reads like a street. It fails silently at the
geocoder, four hundred lines of pipeline later.

Two more, same bug, one band boundary each:

| what the cell returned | what the page prints |
|---|---|
| `9807 E. Road, Prescott Valley Valley` | `9807 E. Valley Road, Prescott Valley` |
| `1900 Pine Street North Little` / city `Rock` | `1900 Pine Street, North Little Rock` |

Fix: `mwpvl_grid._lines` groups words by the **gap** between neighbouring
y-centres rather than by a fixed band. Measured on this document, words sharing
a line scatter 0–5 px and the step to the next line is 14–17 px, so a cut at
8 px separates the two populations with room either side. A gap has no edges to
fall across.

**One complication, and it is the reason `_unbridge` exists.** Clustering on
gaps chains: a mark parked between two lines joins them into one. The marks are
the ruled border read as `|` (measured 41 px tall, spanning the whole row), a
speck read as `,` or `:` (1–2 px), and a smear read as `ae` or `vee` (23–28 px).
With `|` at cy 2807 between lines at 2800 and 2815, both steps are ≤ 8 and
`2700 Regent Blvd, Irving, Texas, / USA. 75063` came back as
`2700 USA. Regent 75063 Blvd, Irving, Texas,` — worse than the bug being fixed.

So a cluster taller than one printed line can be (10 px) is re-split using only
words of typical height, and the marks are attached to the nearest line
afterwards. Splitting on height *unconditionally* was tried first and was also
wrong: a postal code alone on the last line boxes at 19–24 px because OCR takes
in the rule beneath it, so `92240` counted as a mark, its line had no body text
left, and the ZIP was pulled up into the city line. Only a cluster that is
already impossible gets re-split.

### 8.6 The column heading was facility #1

Every table's heading — `State | Code | Location | Square Feet | Year Opened |
Description of Operation` — is a printed row and OCRs like one. It sits above
the first ZIP anchor, so `build_rows` gave it to row 0, and the first facility
of the delivery station table read

```
  ; Location 6735 Trippel Road, Theodore, Alabama, USA, 36582
```

`Location` is the column heading and `;` is the rule beside it. Thirteen rows
across the document, one per table, and each one fails to geocode.

`_header_bottom` finds the band by heading **vocabulary** inside the top two
row-heights and drops everything at or above it. Detected rather than assumed,
because the two `_part2` continuation tables have no heading and open on a data
row — cutting the first band unconditionally would lose a facility from each.
Two heading lines (`Square` / `Feet`) are absorbed by a 15 px join, which
covers the second line even where OCR mangles it to `(Gpened`.

### 8.7 A wrapped ZIP+4 tail became the next row's house number

§8.4 tolerates `85034-` as an anchor. What it did not do is find the `6852`.
A row is the band **above** its anchor, and the +4 wraps onto a line of its own
**below** it — so it was assigned to the row underneath and landed at the front
of that row's address:

```
  row 7   2050 East Riverview Drive, Phoenix, Arizona, USA, 85034-
  row 8   6852                                <- the +4 of 85034
          7300 N Silverbell Rd, Tucson, Arizona, USA, 85743

  parsed street of row 8:  "6852 7300 N Silverbell Rd"
```

**73 rows** across the document carry a wrong house number this way, 26 of them
delivery stations. `_reunite_postcode_tails` moves the word back, on three
conditions together: the row above ends in a cut-off postal code, the number is
alone on its printed line, and the row still has a house number once it is
taken away.

The third condition is not decoration. `3120 / Lakepoint Parkway,
Cartersville, Georgia, USA, 30121` satisfies the first two, and 3120 is ATL6's
house number, which wrapped for exactly the same reason a +4 does. With the
remainder reading "Lakepoint" there is no house number left and the word stays
where it is; with the remainder reading "7300 N Silverbell Rd" there already is
one. Without that test the rule broke as many rows as it fixed.

## 9. Fields — identified by content, not by position

`mwpvl_fields.identify_columns` scores each recovered column for how much it
looks like each field and assigns greedily from the strongest evidence down
(address wins on `USA` counts, description on facility vocabulary; resolving
those first stops them stealing the numeric columns).

Position-based indexing would read square footage out of the date column for
**five of the thirteen tables** — the rest-of-world ones, which carry an extra
leading Country column — and report nothing wrong.

Two parsing rules worth naming:

- **`sqft == 0` returns `None`, and that is not the same as missing.** MWPVL
  states twice in its own prose that a zero means the facility is co-located in
  another building and its floor area is counted under another record. The
  `colocated` flag carries the distinction; conflating them would let a stated
  zero be averaged in as a real area. See [`MWPVL_2025.md`](MWPVL_2025.md) §3.3
  and `common/sentinels.py`.
- **A bare year is not a missing month.** `date_precision` records which of
  `month` / `year` / `quarter` / `none` was found, because "2025" is MWPVL
  recording a year it is confident about and a month it is not.
- **The street is the last house number in the cell, not the first.** §13.1's
  merged rows put two facilities in one address cell, and the postal code that
  anchored the row belongs to the LAST of them. Reading the street as
  "everything before the first comma" therefore pairs the *lost* facility's
  street with the *anchored* facility's city and postal code:

  ```
    2050 E Riverview Dr, Phoenix, 14000 W Grant St, Goodyear, Arizona,
    USA, 85338
  ```

  85338 is Goodyear; 2050 E Riverview Dr is in Phoenix. The row describes a
  building that does not exist, and **42 of the 50 rows shaped like this failed
  to geocode**. `_street_at` takes the last field opening with a house number.

  A first version scored fields on street-type words — Road, Way, Terrace,
  Park — and was wrong in both directions: Federal Way, Temple Terrace,
  Overland Park and Buena Park are US cities, all four are in this document,
  and the list read the city as the street on every one of them. A leading
  house number cannot be a city and needs no list. Where it finds none the row
  keeps the reading it had, which costs nothing: a street with no number
  ("Goodman Way", "Isle of Capri") cannot be geocoded from any field.

The `FLAGS` table captures MWPVL's own caveats — `not_confirmed`, `delayed`,
`cancelled`, `closed`, `sqft_estimated`, `colocated`, `rural_wagon_wheel`.
These are the most valuable thing in the description column: the publisher is
telling us which rows it does not stand behind, which is the per-record
reliability weight Fellegi & Holt §7 asks for and almost no source supplies.
44 rows are flagged `not_confirmed` across the thirteen tables (18 on the two
delivery-station tables, which is the figure this section carried when only
those two had been run).

## 10. What the pipeline deliberately does NOT do

**Nothing is cleaned, repaired, dropped or inferred.** A year that reads `9022`
is written out as `9022`.

This is not laziness, it is where the cleaning belongs. Downstream in
`warehouse/edits.py` the OSHA `operating_by` bound is available, so a date can
be tested against **evidence** rather than against plausibility, and a
rejection is recorded as a declared edit with a disposition instead of
happening silently inside a parser. That is the same argument Fix 5 in
[`CLEANING_CHANGELOG.md`](CLEANING_CHANGELOG.md) makes about `CORRECT` being
deliberately absent from the edit dispositions.

There is also a free consistency check waiting: the small-package
delivery-station network launched in **late 2013**
([`MWPVL_2025.md`](MWPVL_2025.md) §3.5), so any earlier date in this table is
falsified by the source's own prose.

## 11. Getting tesseract onto a grid node with no tesseract and no root

The grid node has `pdfimages` but **no tesseract, no module providing it, and
no root**. Three ways out: ask an administrator (days), build from source (an
afternoon, and leptonica's configure wants libraries that are also absent), or
copy a working binary from a machine that has one.

`bundle_tesseract.sh` does the third. It copies **tesseract 4.1.1, 14
non-system shared libraries and `eng.traineddata` — 16 MB** — onto `/weka`,
which both hosts mount, and writes a wrapper that sets `LD_LIBRARY_PATH` and
`TESSDATA_PREFIX` so no caller has to know any of this.

**This is valid for one specific reason and is not a general technique: both
hosts run AlmaLinux 9.8 on x86_64 from the same cluster image.** Copying ELF
binaries between different distributions or glibc versions fails with a
confusing symbol error rather than a clean message. `--test` checks the
assumption rather than trusting it. glibc itself (libc, libm, ld-linux) is
deliberately **left behind** and taken from the host — a copied loader against
a host glibc is the combination that fails hardest, and on the same image the
host's copy is the same file anyway.

`setup_venv.sh` looks for the vendored bundle only after PATH and the module
system have both been tried, and symlinks it into the venv's `bin` so
`grid_ocr.py` keeps calling plain `tesseract`.

**The grid interpreter is Python 3.6.8**, which is why `tools/ocr/*` is
written the way it is. Four things that are second nature on 3.7+ are errors
here, and every one fails at a point that does not name the interpreter:

```
  from __future__ import annotations     3.7+   SyntaxError on import
  subprocess.run(capture_output=True)    3.7+   TypeError at the first call
  subprocess.run(text=True)              3.7+   TypeError at the first call
  @dataclass                             3.7+   ImportError
```

So: `stdout=PIPE`, `universal_newlines=True`, plain tuples, no postponed
annotations. **Do not "modernise" those files.** Pillow is pinned to 8.4.0, the
last release supporting 3.6; unpinned, pip resolves to a wheel that will not
install and reports a metadata conflict that never mentions the interpreter.

The grid scripts import Pillow and the standard library and nothing else. They
do not import `siting_atlas`, do not read the project config, and can be copied
to any machine on their own. The `src/siting_atlas/ingest/mwpvl_*.py` parsers
run back in the project venv on a modern interpreter and are written normally.

## 12. How to re-run it

On the machine that has tesseract, once, if the bundle is not already built:

```bash
bash tools/ocr/README.md --test
```

On the grid node — one command, no arguments, from any directory:

```bash
bash tools/ocr/grid_ocr.py
```

It finds the PDF, builds a throwaway venv at `/tmp/mwpvl_venv`, checks the two
C binaries, runs the OCR with `nproc - 2` workers, writes a timestamped log to
`logs/mwpvl_ocr_*.log`, and **checks that it produced output** — an OCR run
that writes nothing otherwise exits 0 and looks like success. Exit codes are
documented at the top of the script (2 PDF not found, 3 venv, 4 missing binary,
5 OCR failed, 6 ran but wrote nothing). It is resumable: run it again any time
and it skips strips already done.

Do not `source` it. The guard refuses outright rather than half-working.

Then, back in the project venv:

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.mwpvl_tables
```

which writes `data/interim/mwpvl_facilities.csv` and
`outputs/metrics/mwpvl_extraction.json` and prints a per-table coverage table.

Overrides, all optional: `MWPVL_PDF`, `MWPVL_WORKERS`, `MWPVL_VENV`,
`MWPVL_OUT`. To redo one strip, delete its TSV.

## 13. Known failure modes, stated plainly

### 13.1 A row whose postal code did not OCR merges into its neighbour — 3%

This is the dominant loss mode and it is structural: the anchor *is* the postal
code, so a code that does not come back is a row that does not exist. Its words
do not vanish — they join the row below, which then carries two facilities'
text and, via `parse_code` taking the **first** match, one facility's code.

**Which of the two the surviving row describes was got wrong until
2026-09-14.** The row is anchored on the LAST postal code in the cell, so the
address that postal code belongs to is the last one too — but `parse_address`
read the street as everything before the first comma, which is the *lost*
facility's. The row that came out had one facility's street and another's city
and postcode. §9 has the example and the fix; the count of merged rows is
unchanged, but they no longer describe buildings that do not exist.

Measured on the delivery-station table: **18 of 535 rows merged, 3%.** It was
41 of 510 (8%) before the three fixes in §8.

Two honest caveats on that figure. First, a merge is under-counted by
construction: it removes a row, so the denominator moves too. Second — and this
is the project's own standing rule about citing artefacts rather than figures —
**the merge count is not emitted anywhere.** `mwpvl_extraction.json` carries
row counts and per-field coverage and no merge count, so 517/535 is a working
figure measured during the fix session and is not reproducible from an
artefact. The fix is the one this project keeps relearning: have the ingest
emit it.

### 13.2 A quarter of the rows carry no year, and half carry no month

```
  1,904 facilities
  1,420 with a year   74.6%      484 (25.4%) have none
    873 with a month  45.9%    1,031 (54.1%) have none
```

*Was, over the two delivery-station tables alone: 591 / 446 (75%) / 306 (52%).
The shortfall is the same shortfall at eleven times the scale, which is the
useful thing the wider run established — the date column is not worse on the
tables nobody had read.*

Some of that is MWPVL not knowing, which is the source behaving correctly and
is *information* — `date_precision` distinguishes it. Some of it is OCR loss in
the date column. **The pipeline does not currently tell those two apart**, and
it could: the text layer (§5 of [`MWPVL_2025.md`](MWPVL_2025.md)) dates about
twenty fulfilment centres exactly, which grades the OCR for free wherever both
exist. That calibration has not been run.

### 13.3 All thirteen tables are now parsed — and one thing had to change

> **Corrected 2026-09-14, evening.** This section was headed *"Eleven of the
> thirteen tables have not been parsed"* and said `data/raw/mwpvl/tsv/` held
> two directories. It now holds thirteen. The section is rewritten rather than
> deleted because the *reason* it gave — a scheduling fact, not a limitation of
> the code — turned out to be **half wrong**, and that is worth recording.

`data/raw/mwpvl/tsv/` now holds thirteen directories, 156 strips in all:

```
  01_us_fulfillment_center            27 strips     385 rows
  02_us_fresh_dc                       2              22
  03_us_whole_foods_dc                 1              11
  04_us_fresh_hub                      4              65
  05_us_inbound_cross_dock             4              69
  06_us_sortation_center               7             114
  07_us_air_gateway_hub                2              24
  08_us_delivery_station              33             535
  08_us_delivery_station_part2         6             100
  09_us_delivery_heavy_bulky           8             121
  10_row_fulfillment_center           22             160
  11_row_sortation_delivery_air       33             249
  11_row_sortation_delivery_air_part2  7              49
```

**It was not purely a scheduling fact.** The row anchor keyed on a five-digit
US postal code, which every US table prints and no rest-of-world table does.
Running tables 10 and 11 required a **facility-code fallback anchor** — when no
postcode is found on a strip line, the Amazon building code anchors the row
instead (`ingest/mwpvl_grid.py`, `_code_anchors`, "the fallback for tables with
no US postal code"). That is why `10_row_fulfillment_center` returns 160 rows
with only 68 postcodes and `11_row_sortation_delivery_air_part2` returns 49
with 4. **137 rows are anchored on the fallback key** and should be read as
such — the module's own docstring notes a code is printed once per row rather
than on the last line, which makes it a *cleaner* anchor where it exists, but
it is present less often and a missing anchor loses a whole facility.

The delivery-station tables were still done first, because they are the
project's target facility class. Anybody quoting "1,904 facilities" should know
it is **1,904 Amazon buildings worldwide across eight facility classes** — of
which **635 are US small-package delivery stations**, the only class
[`PANEL_EXPANSION.md`](PANEL_EXPANSION.md) admits to the panel.

### 13.4 Everything MWPVL's own caveats already say

The source declares its own incompleteness five separate times, and line 391 —
*"The data concerning this network is challenging to track"* — is about this
table specifically. 44 rows are flagged `not_confirmed` by the publisher. A
date from this table is a **claim by a consultancy**, not a record from a
registry, and it should enter the panel with a provenance label that says so
rather than as `source_type=permit`, which is already wrong on 104 of 104
national rows (`docs/STATUS.md` §7, decision D3).

### 13.5 Not attempted

- No confidence-weighted reconciliation between overlapping strips beyond
  keeping the higher-confidence duplicate at the same coordinates.
- No check that a recovered row's square footage is consistent with its stated
  facility type. The source disagrees with itself on delivery-station size by a
  factor of two ([`MWPVL_2025.md`](MWPVL_2025.md) §3.4), so there is no band to
  check against.
- ~~No linkage of these rows to `national_facilities.csv` or the OSHA
  extract.~~ **Done 2026-09-14, evening**, for the 635 US delivery-station rows
  only: [`PANEL_EXPANSION.md`](PANEL_EXPANSION.md) screens them against the
  104-row panel and `outputs/metrics/mwpvl_validation.json` tests 1,420 dates
  against the OSHA bound — 208 link to a building, **94.71% survive it**, and
  99.5% are chronologically plausible. The remaining 1,269 rows, all of them
  the wrong facility class for this panel, are still unlinked.

## 14. What this unblocks

Nothing below is done. Each is a thing that was **blocked on the absence of a
date** and is now blocked only on work.

```
  1  THE CBP LAG GUARD.  WHERE_WE_ARE Sec.3 blocker 2: the guard lags off the
     OSHA bound with margin zero, and an Amazon delivery station IS a
     warehousing establishment -- the covariate that carries the choice model.
     A real opening date is the only thing that makes that guard non-circular.
  2  OPTION D in ALTERNATIVES.md, which says in its own text "Do not start
     this until the dates exist". A before/after design on house prices or
     pm25 needs an event date; 1,420 of them now exist. **But not for pm25:**
     `pm25` is a CONSTANT in data/processed/panel.parquet -- 0 of 33,791 ZCTAs
     carry more than one distinct value over the 32 quarters, so no event date
     can rescue a before/after design on it. The coverage (98.55%, 33,300
     ZCTAs) is fine and the variance is zero. `home_value` is the column that
     actually varies -- in 26,262 ZCTAs, 77.7% -- and it is the one Option D
     should use. See ALTERNATIVES.md Sec.D.1.
  3  TIME IN THE CHOICE MODEL.  MODEL_SPEC Sec.5.1 specifies two structural
     periods and models/choice.py has no period logic at all, partly because
     there was no date to split on.
  4  INTERVAL CENSORING, which risk_set.py does not implement. An MWPVL
     opening month plus an OSHA operating-by date is a genuine interval, and
     an interval is the thing that would let NAT-0036 back in (decision D4).
  5  A FOURTH CAPTURE LIST.  MWPVL_2025.md Sec.1 establishes that the 2012
     exclusion does not extend to this document. 1,904 addresses from a source
     whose capture mechanism is unrelated to injury, union petitions or
     volunteer mapping tightens the coverage interval in nlrb_coverage.json.
```

And one thing it does **not** unblock: this is not a census, so it does not
make the panel complete. It makes part of the panel dated.

## 15. Related

- [`MWPVL_2025.md`](MWPVL_2025.md) — the same document's text layer, and the
  five findings that needed no OCR at all.
- [`SATELLITE.md`](SATELLITE.md) — the failed route to the same dates, and the
  stopping rule that condemned it.
- [`CBP_DETAIL.md`](CBP_DETAIL.md) §5 — the lag guard these dates repair.
- [`FACILITY_PANEL_PROVENANCE.md`](FACILITY_PANEL_PROVENANCE.md) — where
  `open_year` comes from and why it is an upper bound.
- [`CLEANING_CHANGELOG.md`](CLEANING_CHANGELOG.md) — the three row-anchoring
  bugs are logged there as silent failures, alongside the edit set that will
  adjudicate these dates.
- [`../ALTERNATIVES.md`](../ALTERNATIVES.md) Option D — blocked on dates;
  Option E — buying the current product as XLSX.
