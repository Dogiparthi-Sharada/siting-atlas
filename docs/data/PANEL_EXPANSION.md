# Expanding the facility panel with MWPVL 2025 Q1 — every decision, measured

*Built 2026-09-14. Code `src/siting_atlas/warehouse/mwpvl_{merge,geo,shape,
report,print}.py`. Reproduce with*

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.mwpvl_merge
```

*Outputs `data/external/facility_panel/national_facilities_expanded.csv`
(693 rows) and `outputs/metrics/mwpvl_merge.json`. Every figure below is read
from that artefact and none is remembered.*

`data/external/facility_panel/national_facilities.csv` is **not touched**. It
is hand-verified and it stays the reference; the expansion is a new file
beside it.

---

> ## Corrected 2026-09-14, evening — every count in this document moved
>
> **Nothing below was wrong when it was written. The input got bigger.** This
> document was built in the morning against an OCR run that had read **2 of
> MWPVL's 13 table images**, yielding 591 US delivery stations. All thirteen
> were parsed the same afternoon (`MWPVL_OCR_PIPELINE.md`,
> `outputs/metrics/mwpvl_extraction.json`: **1,904 facilities**), the merge was
> re-run, and every count here moved with it. This is the ordinary kind of
> staleness — *the work moved on* — not an error being buried, and the
> document's **arguments are untouched**: the duplicate screen, the unscreened
> blind spot, the six review rows, the Connecticut vintage gap and all nine
> things in §9 survive at their new sizes.
>
> Read from `outputs/metrics/mwpvl_merge.json` on 2026-09-14, evening, and
> **re-read 2026-09-15 from `run_id 20260915-195256-1c53`** after the OCR
> street/city repair (`GEOCODING.md` §10) changed what the duplicate screen can
> see. The third column is the current artefact and is the one to quote:
>
> ```
>   figure                             WAS (morning)   WAS (14th)   IS (15th)
>   ------------------------------------------------------------------------
>   MWPVL rows read into the merge            591          635          635
>   of an OCR file holding                    591        1,904        1,904
>   excluded as the wrong facility class        -        1,269        1,269
>   internal duplicates dropped                 1            1            1
>   already in national_facilities.csv         30           32           40
>   held for clerical review                    6            6            5
>   ADDED                                     554          596          589
>   panel rows after                          658          700          693
>   rows carrying an opening year             524          556          551
>   ... and also a CBSA code                  503          535          531
>   distinct CBSAs                            210          230          230
>   distinct ZCTAs                            587          625          629
>   unscreened (no comparable street)          72           74           54
>   recall-probe pairs                         33           35           43
>     match / review / nonmatch            29/3/1       31/3/1       40/3/0
>   E_operating_by linked rows                126          130          136
>     falsified                                 5            6            6
>     pass rate                              96.0%        95.4%       95.59%
>   facility_check non-numeric open_year      134          144          142
>   OCR state cross-check                  517 / 518   556 / 557    604 / 606
>   per parameter at 5 params (projected)    71.2         76.0         75.6
>   ------------------------------------------------------------------------
> ```
>
> **The 15th's column is not another OCR run — it is the same 635 rows read
> correctly.** Repairing the street/city split let the Fellegi–Sunter screen
> recognise eight more MWPVL rows as buildings already in the hand-collected
> panel (32 → 40) and cleared one review row, so seven fewer rows were added
> and the panel lands at **693**, not 700. The unscreenable blind spot shrank
> hardest, 74 → **54**, for the same reason: those rows now have a comparable
> street. The OCR state cross-check moved 556/557 → **604 / 606** because the
> parser now recovers a state on 613 of 635 rows instead of far fewer; the
> agreement rate is **99.67%**, not 99.8%.
>
> **The single most important change is not a count.** The 591-row file was
> "what the OCR could read". The 635-row file is "what the OCR could read,
> *filtered to the US small-package delivery-station class*" — 1,269 of the
> 1,904 recovered facilities are fulfilment centres, sortation centres, cross
> docks, Fresh/Whole Foods DCs, air gateways and rest-of-world buildings, and
> they are excluded on purpose, because this panel's unit is a delivery
> station. §8's second caution used to read "only 2 of 13 tables have been
> parsed"; that reason has expired and been replaced by a better one.
>
> Two further figures in §7 moved because their *denominator* grew rather than
> because anything got worse — see the marker there.
>
> Inline figures below have been brought to the artefact. The table above is
> the record of what they were.

---

## 0. The one-paragraph answer

635 OCR'd MWPVL delivery-station rows — the US small-package delivery-station
class, filtered out of a 1,904-facility OCR file by dropping 1,269 rows of the
wrong facility class — were screened against the 104-row national panel and
against themselves. **1** was dropped as an internal duplicate, **40** were
already in the panel, **5** were held for clerical review, and **589** were
added. The panel goes 104 → **693** rows, of which **551** carry an opening
year and **531** carry both a year and a CBSA code, which is what
`models/choice.build` can consume. The declared edit `E_operating_by` passes on
**95.59%** of the 136 rows an OSHA building could be matched to — 93.75% on the
MWPVL rows, 96.15% on the pre-existing ones.

**And the headline is not the number.** Four measurements below say the merge
should be read with its blind spots attached: 54 MWPVL rows could not be
screened at all, 415 of the 551 dated rows could not be checked against OSHA,
one known duplicate slipped through on a damaged street string, and the merge
consumes one facility class out of the eight MWPVL publishes.

---

## 1. The duplicate screen, which is the part that had to be right

`FACILITY_PANEL_PROVENANCE` §19.2 records what happens when this is done on a
cheap key: 362 rows went out for hand-labelling and **289 of them were
already classified**. So no new matching rule is defined anywhere in this
work. The screen is `common/linkage.py` — Jaro-Winkler over addresses parsed
into fixed slots, Fellegi-Sunter's three-way rule (Winkler RR99-04 eq. 4) —
constructed exactly the way `warehouse/edits._tightest_bounds` constructs it,
so "the same building" means the same thing here as it does inside the
declared edit.

```
1,904  facilities in the OCR file (all 13 tables)
-1,269  the WRONG FACILITY CLASS for this panel
  ---
  635  MWPVL US delivery-station rows read
   -1  dropped as an INTERNAL duplicate            (§2)
  ---
  634
  -40  already in national_facilities.csv          (§3)
   -5  held for CLERICAL REVIEW, not added         (§3.2)
  ---
  589  added
```

### 1.1 The building code is deliberately not used as a matching input

`linkage.compare` short-circuits on a pair of Amazon building codes: equal
codes are a match, different codes are a non-match, and nothing else is
consulted. MWPVL prints a code on 406 of its 635 rows and it would have been
the cheapest possible screen.

It is not used, for one reason: **those codes are OCR'd from the same picture
as everything else.** Letting a four-character reading override a parsed
street address is trusting the weaker evidence, and the failure would be
silent in both directions — a mis-OCR'd code vetoes a true match, and a
coincidentally-agreeing code forces a false one. `facility_dedup._records`
already declines to pass a code for the same class of reason, so this is the
project's existing practice rather than a new position.

What the codes are used for is a **diagnostic on the matcher's output**,
after the fact:

| Check | Result |
|---|---|
| merged groups whose MWPVL codes disagree | **1** (MWP-0086 / MWP-0087) |
| unmerged rows sharing a non-empty code | **0** |

Whatever `parse_address` finds inside the street box — the `315 SHUKSAN WAY
DWS4` case from §11.4 — still counts, because that is a code the address
parser recovered rather than one this module supplied.

### 1.2 How many rows the screen can speak about at all

This is the measurement that decides how much the 589 is worth.

```
  634  MWPVL rows entering the cross-screen
  580  carry a street the comparator can parse and compare
   54  carry NO comparable street        <- UNSCREENED, not "screened and new"
```

MWPVL frequently prints a cross-street or a development name instead of an
address — `Valencia & Kolb`, `Rio del Oro Development`, `NE corner Hudson
Road / Settlers Ridge Parkway` — and the OCR loses the street outright on 23
rows. `linkage.compare` returns "no comparable street" for those and refuses
to merge on city and ZIP alone, which is correct (32 of 148 (state, ZIP)
cells in the OSM export hold more than one station). The consequence is that
**54 of the 589 added rows entered the panel as new by default rather than by
evidence**, and the first 25 ids are listed in `mwpvl_merge.json` under
`screenability.unscreenable_ids`. The blind spot was 74 rows before the OCR
street/city repair (`GEOCODING.md` §10); it is a fifth smaller now, and the
reason is that those rows acquired a comparable street, not that the screen
got more permissive.

### 1.3 A recall probe against a cheaper key

The comparator is supposed to beat an exact key. Whether it does is
measurable: every MWPVL-panel pair sharing a five-digit postcode **and** a
house number was compared and its verdict tallied.

```
  43 pairs share a postcode and a house number
     40  match
      3  review
      0  NONMATCH
```

> **This is the one finding in the document that the 2026-09-15 re-run
> reverses, so it is not a digit swap.** The probe used to report 35 pairs
> with one rejection, and that rejection was a real miss:
>
> ```
>   MWP-0519  vs  NAT-0088     Providence RI
>   MWPVL street core  "DR"        <- the OCR kept the suffix and lost the name
>   panel street core  "DUPONT"
>   Jaro-Winkler 0.60, below STREET_REVIEW = 0.78
> ```
>
> The OCR repair restored `DUPONT`, and `mwpvl_merge.json` now lists
> `MWP-0519 -> NAT-0088` in `cross_matches` and an **empty** `rejected` list.
> The old conclusion — "at least one of the added rows is a building the panel
> already holds" — is **no longer supported by this probe**: on the current
> run the comparator recovers every pair the cheap postcode+house-number key
> finds. The diagnosis behind it was right, and it was a diagnosis of OCR
> damage rather than of a badly set threshold, which is why fixing the OCR
> fixed it. §9 item 1 is corrected to match.

What has *not* changed is the standing of the probe: it can only speak about
pairs the cheap key can form, so it bounds recall against that key and not
against the truth.

---

## 2. MWPVL against itself

`docs/data/MWPVL_OCR_PIPELINE.md` §13.1 measures a **3% row-merge defect**:
18 of 535 rows on the delivery-station table carry two facilities' text, and
`parse_code` takes the first match, so the same building can surface twice
under different codes. The internal screen is `facility_dedup.adjudicate`,
which is the project's existing implementation of `E_date_contradiction` plus
the Fellegi & Holt §7 reliability weights.

**One group was found: MWP-0086 / MWP-0087.** They agree on the opening date
(`quarters_apart: 0`), so nothing had to be adjudicated; MWP-0087 folds into
MWP-0086 and `duplicate_of` records it in the CSV.

Two honest observations about that number being small:

- The defect §13.1 describes **destroys** a row rather than duplicating it.
  A merged row is invisible to any duplicate screen, because there is only
  one of it. 3% of 535 is ~18 rows this merge cannot see as two buildings,
  and no amount of matching recovers them.
- The 54 unscreenable rows of §1.2 are unscreenable internally too.

`adjudicate` would leave `open_q_index` NaN if two folded rows disagreed
about the date and their provenances tied — which they always would here,
since every MWPVL row is `source_type=other`. That case is empty today, and
`mwpvl_merge.run` raises rather than writing a file if a later vintage
produces one. Picking a date is the one thing this merge must not do.

---

## 3. What the 40 matches and the 5 review rows look like

### 3.1 One MWPVL row matched two panel rows

`MWP-0474` matches **both** `NAT-0078` and `NAT-0079` — 3610 NW Saint Helens
Road / St Helens Rd, Portland. That is §12.6's known duplicate national pair
seen from the outside by an independent source, and it is the same corroborat-
ion §19.2 reported from the batch worklist. `MWP-0056` now does the same
against `NAT-0011` / `NAT-0012`. 40 MWPVL rows matched **42** distinct panel
rows for this reason. No panel row was matched by more than one MWPVL row.

### 3.2 The five held for clerical review

Winkler's eq. (4) has three outcomes and the middle one is "hold for clerical
review". These five are **not in the expanded file** and are listed in the
artefact with the panel row they resemble:

| MWPVL | panel | why | score |
|---|---|---|---|
| MWP-0187 | NAT-0041 | no ZIP or city corroboration | 1.000 |
| MWP-0098 | NAT-0002 | no ZIP or city corroboration | 1.000 |
| MWP-0032 | NAT-0008 | suffix RD/BLVD | 1.000 |
| MWP-0062 | NAT-0005 | street similarity 0.91 | 0.911 |
| MWP-0337 | NAT-0064 | street similarity 0.80 | 0.805 |

The membership changed as well as the count: `MWP-0319` / `NAT-0062` and
`MWP-0169` / `NAT-0030` were resolved outright by the repaired addresses and
are now merges, and `MWP-0098` / `NAT-0002` entered the band.

Three of the five have an **exact** street match and fail only because neither
postcode nor city agrees, which is consistent with an OCR'd postcode. They
look like true matches and they are still held, because "looks like" is the
standard this project spent a document rejecting. Five rows is five lookups.

**The direction of the error is stated so it is not mistaken for symmetry.**
Excluding a review row understates the panel by at most five. Including it
would risk five duplicate buildings, and a duplicate building is the defect
`facility_dedup` exists to clean up after.

---

## 4. Geography: postcode → ZCTA → CBSA, from files already on disk

Both registered crosswalks are present locally, so nothing was skipped and
nothing was geocoded:

```
  data/interim/zcta_county.parquet    33,791 ZCTAs, one county each
  data/interim/cbsa_county.parquet     1,915 counties -> CBSA
```

On the 589 added rows:

```
  582  (98.8%)  got a ZCTA
  561  (95.2%)  got a CBSA code, across 214 distinct CBSAs
  ----
    7            postcode is not a ZCTA in the 2020 relationship file
   11            ZCTA resolves to a county that is in no CBSA (rural)
   10            Connecticut: the vintage gap below
```

Each failure carries its own `geo_status` value in the CSV, so the three add
up to the total and none can be lost between two subtotals.

**The Connecticut gap is inherited, not introduced.** The CBSA delineation is
OMB 2023 and uses the nine planning regions (FIPS 09110-09190); the
ZCTA-to-county file is 2020 and uses the eight legacy counties
(09001-09015). They do not join. `ingest/registry.py` records this under
`cbsa_county` and `bps_county`. It costs **10 rows**, all of which have a
state and a ZCTA and none of which has a metro.

### 4.1 A postal code is read as a ZCTA, and that is an assumption

ZIPs are USPS delivery routes; ZCTAs are Census tabulation areas built from
blocks. They are different objects and a ZIP with no residential delivery has
no ZCTA at all. This merge treats them as the same because
`warehouse/facility_load` already does — `frame["zcta"] = frame["zip"]
.str.zfill(5)` on all 104 national rows — and doing anything else would make
the expanded panel unjoinable with the panel it extends. What is new here is
that the cost is now **counted**: 7 of 635 postcodes, 1.1%.

### 4.2 A free grade on the OCR, run for the first time

`MWPVL_OCR_PIPELINE.md` §13.2 names a calibration that "has not been run".
Half of it can be run at zero cost here. MWPVL's state column is OCR'd free
text and arrives damaged (`Taxas`, `Texas Texas`, `lebanon: Tannesses:`); the
county GEOID's first two digits are a state FIPS code, which is a fact about
the crosswalk. Comparing them:

```
  613  of 635 OCR'd state names parse to a USPS code
  606  of those also resolved through the crosswalk  <- comparable
  604  agree                                            99.67%
    2  disagree
```

This is *not* a grade on the dates, which is what §13.2 actually asks for. It
is a grade on one field of the same OCR pass, and 99.67% on that field is
evidence that the postal codes — the row anchors — are being read well. The
figure used to read 556 / 557 = 99.8%; the rate is fractionally lower and the
**denominator is 49 rows larger**, because the repaired reading order recovers
a parseable state name on rows that previously had none. A rate measured on
more of the data is the better grade even when it is a shade worse, and both
`517 / 518` and `556 / 557` are superseded.

**The state written into the panel is the crosswalk's, not the OCR's.** The
OCR'd string is preserved in `mwpvl_region_ocr` and nothing is overwritten:
22 rows whose state name does not parse still get a state, because the
postcode resolves even when the word does not.

---

## 5. Provenance, and what MWPVL declines to vouch for

Every added row carries `source_dataset = mwpvl_2025q1`. On the 589:

```
  542  MWPVL vouches for
   47  MWPVL does NOT vouch for
        20  not_confirmed      -> status "announced", confidence "low"
        27  delayed            -> status unchanged,   confidence "low"
         0  cancelled
  other flags carried through unchanged:
         2  closed        28  sqft_estimated
        16  colocated     68  rural_wagon_wheel
```

Three decisions, each with its reason:

**`source_type = other`, not `mwpvl`.** `ingest/facility_check
.VALID_SOURCE_TYPES` is a closed vocabulary whose own comment says why: "an
unenforced vocabulary drifts ... a typo silently creates a provenance class
of one". MWPVL is a consultancy census and is none of the seven, so it is
`other` — which is also **last** in `facility_dedup.DATE_RELIABILITY`, and
that is the correct rank for a source that declares its own incompleteness
five times. The precise provenance travels in `source_dataset`, where it
cannot be confused for one of the seven. A future conflict between an MWPVL
date and a permit date therefore resolves to the permit automatically, by a
weight that was already declared.

**`confidence` is MWPVL's own vouching, not a new ranking.** `medium` when
the publisher stands behind the row, `low` when it does not. Nothing in this
merge invented an ordinal.

**`delayed` does not move `status`.** A delayed building can be open,
announced or abandoned, and MWPVL's phrasing does not say which. It stays a
flag.

### 5.1 The `closed` flag is 0 for 2, so it does not set `status`

This is the one place the merge declines to derive a field, and it is worth
the paragraph. The flag fires on two rows and **both are false positives of
the flag parser reading the description text**:

```
  DBM5  "Delivery Station for Eastwood Birmingham Region. Currently the site
         of the Century Plaza closed in 2009."
         -> the shopping MALL closed; the delivery station replaced it

  DLA2  "Delivery Station closed in June, 2017; Reopened in 2017; ..."
         -> closed and reopened, so open
```

MWPVL prints no closing date for either. `ingest/facility_check
._closure_errors` is explicit about what a `closed` status with no
`close_year` does: it "reaches `warehouse.facilities` as a close index of
positive infinity, so the site enables its catchment forever". Promoting a
flag that is 0 for 2 into the operative field would manufacture that failure.

**The flag itself is untouched** — the `closed` column carries both rows, so
nothing is hidden and nothing is corrected. The merge simply declines to
derive from it. That distinction is the whole of Van den Broeck's third
option: leave unchanged, having recorded the finding.

---

## 6. Dates: flagged, never fixed

```
  589 added rows
  447  carry an opening year        303 month / 117 year / 27 quarter
  142  carry none                   -> date_precision "none"
  330  carry a quarter
  427  carry BOTH a year and a CBSA code  <- what models/choice can use
```

Two rows are flagged and **not repaired**:

```
  MWP-0101  1500 Citation Way, Hollister CA
            open_year = 2094,  date_precision = month
            date_flag = "year_outside_2013_2030"
            The CSV still says 2094.

  MWP-0605  6705 East Marginal Way South, Seattle WA
            open_year = 2075,  date_precision = year
            date_flag = "year_outside_2013_2030"
            The CSV still says 2075.
```

The flagging rule is declared in `mwpvl_shape.YEAR_FLOOR/YEAR_CEILING` and
both edges are sourced rather than chosen: the floor is 2013 because MWPVL's
own prose says the small-package delivery-station network launched in late
2013 (`MWPVL_2025.md` §3.5), so an earlier date is falsified by the same
document; the ceiling is the 2025 Q1 vintage plus five years of announced
pipeline, which admits the one genuine 2028 announcement and catches the 2094
and the 2075. **0 rows** fail the 2013 floor.

`open_quarter` is left **empty** on the 259 rows where MWPVL prints neither a
month nor a quarter. `warehouse/facility_load` applies the Q1-by-convention
rule at load and records it in `open_quarter_imputed`; writing Q1 into the
file here would destroy the distinction that module exists to preserve.

---

## 7. Validation: `E_operating_by` on the expanded panel

The declared edit, from `warehouse/edits.py`:

```
  quarter_start(open_q_index)  <=  osha_operating_by
```

Run in `REPORT`, never `EXCLUDE`: excluding failures before counting them
destroys the measurement, which is the same argument `ingest/mwpvl_panel`
makes.

```
  693  rows in the expanded panel
  551  carry a date the edit can evaluate
  136  the address matcher links to an OSHA building
    6  FALSIFIED
  ---
  95.59%  pass rate

  by source:
    mwpvl_2025q1            32 linked,  2 falsified,  93.75%
    national_facilities    104 linked,  4 falsified,  96.15%
```

> **The MWPVL pass rate went DOWN, 95.5% to 93.75%, and that is the one number
> in this document that should be read twice.** The morning run linked 22
> MWPVL rows and falsified 1; the thirteen-table run linked 26 and falsified
> 2; the repaired-address run links **32** and still falsifies **2**. Each
> step could test more rows, and the rate is moving on a denominator in the
> twenties and thirties. At that size a single row is worth three points and
> the whole difference between the first rate and this one is one building. It
> is reported because the direction is unflattering, not because 32 rows can
> settle anything.

The four national failures are the already-known NAT-0011 / NAT-0026 /
NAT-0036 / NAT-0079 of §12.7 — reproduced here, not discovered. The two MWPVL
failures are rows `ingest/mwpvl_panel` also reports:

```
  MWP-0084   5800 Coliseum Way,    Oakland CA
  claims     2024Q4
  OSHA       inspection 346750268, operating on 2023-06-06
  late by    6 quarters

  MWP-0615   6617 Associated Blvd
  claims     2024Q3
  OSHA       inspection 345651657, operating on 2021-11-22
  late by    11 quarters
```

*This block listed one failure in the morning. MWP-0615 is a row the
thirteen-table OCR recovered and the two-table run had never read; it is a new
row that fails, not a row whose verdict changed.*

**Read the denominator before quoting 95.59%.** `415 of the 551 dated rows
could not be checked at all`, because no OSHA building matched them — and an
unchecked row is not a passing row. The edit speaks only about the 136. For
comparison on the same test: `ingest/mwpvl_panel` reports **94.71% over 208
linked rows** (`outputs/metrics/mwpvl_validation.json`, `run_id
20260915-195247-dbb5`), and the satellite method failed the identical test on
**36%** of its output (`SATELLITE.md` §4).

> **Corrected 2026-09-14, evening; re-measured 2026-09-15.** That sentence has
> now read three different things, and all three were right for their run.
> `mwpvl_panel` tests the **extraction**, not the panel, so its denominator is
> every dated OCR row rather than every dated panel row, and that denominator
> has grown twice:
>
> ```
>   run                       linked   falsified   surviving   pass rate
>   2 tables,   591 rows          36           1          35      97.2%
>   13 tables, 1,904 rows        157          10         147      93.6%
>   13 tables, addresses fixed   208          11         197     94.71%
> ```
>
> **A falling rate on a growing denominator is not the same event as a falling
> rate**, and this table is the reason that distinction was worth making: the
> rate fell from 97.2% to 93.6% while the number of rows actually surviving the
> OSHA bound went from 35 to 147, and it has since **risen** to 94.71% while
> the surviving count went to 197. Nearly six times as many rows now survive
> the bound as were tested at all in the morning. The comparison to make is
> 35-of-36 against 197-of-208; **93.6% and 157 are superseded and should not be
> quoted**, and neither should 517/518 or 556/557 for the state check.
>
> By date precision the current run splits: month 160 matched / 9 falsified,
> year 25 / 2, quarter 23 / 0. Date plausibility is **99.5%**, (1,420 − 7) /
> 1,420 — 2 rows before the network start on the delivery-station tables and 5
> beyond plausible. It is not 99.8%.
>
> **The two rates in this section are different measurements and both are
> current.** `mwpvl_validation.json` tests all 1,420 dated *extraction* rows
> → 208 linked, 11 falsified, 94.71%. `mwpvl_merge.json`'s
> `validation_E_operating_by` tests the 693-row *panel* → 551 dated, 136
> linked, 6 falsified, 95.59%. Same edit, different denominators. Neither is
> 93.6%.

### 7.1 The expanded file does NOT pass `ingest/facility_check`

Stated here so nobody discovers it by running `--check`:

```
  ERROR  142 row(s) have a non-numeric open_year
```

`facility_check` treats `open_year` as required. MWPVL prints no year on a
quarter of its rows. The two ways to make the error go away are to drop those
142 rows — throwing away the location, which is the thing a fourth capture
list exists to supply — or to invent a year. Neither is taken. The error is
carried in `mwpvl_merge.json` under `facility_check`.

The two `closed`-with-no-`close_year` errors that appeared in the first run of
this merge are gone, for the reason in §5.1.

---

## 8. What the expansion buys, stated as a projection and not as a result

```
                            national frame     expanded frame
  rows                            104                693
  dated                           104                551
  dated and in a CBSA             100                531
  distinct CBSAs                   62                230
  distinct ZCTAs                    -                629

  restricted to 2018-2025, the feature panel's window:
    decisions                      80                440
    independent (CBSA, quarter)
      episodes                     79                378
    per parameter at 5 params    15.8               75.6   (floor 10)
```

**This is projected, not fitted.** It applies
`models/diagnostics.independent_episodes`' definition to the facility frame
rather than to a risk set, exactly as `warehouse/national.summarise` does and
for the same reason: no national risk set exists. `src/siting_atlas/models/`
was not touched and nothing was refitted.

Three things it does **not** buy, and the first is the binding one:

1. **It does not buy better dates.** `CBP_DETAIL.md` §5 measures that 104 of
   104 national rows carry exactly the quarter of their building's earliest
   OSHA inspection, so the existing frame is upper bounds with a 4-345 month
   lag. MWPVL's dates are a different kind of claim — a consultancy's stated
   month — and 93.75% of the 32 that could be tested survive the OSHA bound.
   That is genuinely new information and it is still 32 tested rows.
2. **It does not buy coverage of MWPVL's network.** All 13 tables are now
   parsed (`MWPVL_OCR_PIPELINE.md`), and this merge deliberately consumes two
   of them. 635 is 635 **US small-package delivery stations**, not 635 Amazon
   buildings and not the 1,904 facilities the OCR recovered: 1,269 rows —
   fulfilment centres, sortation centres, inbound cross docks, Fresh and Whole
   Foods DCs, air gateways, heavy/bulky stations and every rest-of-world
   building — are excluded as the wrong unit for this panel. They are
   available and unused, which is a choice this document is making and not a
   limit of the OCR. *This caution used to read "only 2 of MWPVL's 13 tables
   have been parsed"; that was true in the morning and is no longer the
   reason.*
3. **It does not buy covariates.** `FACILITY_PANEL_PROVENANCE` §16.3's third
   caution is still unpaid and is now larger: national ACS/CBP/BLS coverage at
   ZCTA grain for **230** CBSAs rather than 62.

---

## 9. Things found on the way that a reader should distrust

Listed rather than buried, in descending order of how much they should worry
somebody using the file.

1. **The recall probe no longer finds a duplicate in the added rows, and that
   is a weaker reassurance than it sounds.** §1.3. This item used to read "at
   least one duplicate is in the 596 — MWP-0519 / NAT-0088"; the OCR repair
   merged that pair and the probe's `rejected` list is now empty. But the probe
   only looks at pairs sharing a postcode **and** a house number, so zero is a
   floor on what it can see, not a total. Item 2 is the reason to keep
   distrusting the count.
2. **54 rows were never screened.** §1.2. They have no comparable street, so
   the comparator could not test them in either direction.
3. **The internal duplicate count of 1 is not reassuring.** §2. The OCR
   defect that matters destroys rows rather than duplicating them, and a
   destroyed row is invisible to a duplicate screen by construction.
4. **Three of the five review rows have an exact street match** and fail only
   on geography, which is consistent with an OCR'd postcode. They are the most
   likely true duplicates in the file and they are excluded, so they are the
   cheapest five lookups available.
5. **The row-merge defect is visible in the data.** `MWP-0276` reads
   `postcode 10100` — not a ZCTA — with the description "Station for East DC
   Delivery Washington Station for MD Delivery Edgewood Region", which is two
   facilities' text in one row with a damaged code between them. That is
   §13.1 happening in front of you.
6. **`facility_type = DS` on all 589 is the source's word, not a check.** Both
   parsed tables are the article's US delivery-station section, so the type is
   MWPVL's classification of its own section. `FACILITY_PANEL_PROVENANCE`
   §11.2 is the warning about reading a type off a name; this is not that
   error, but it is not independent evidence either.
7. **`status = announced` on 20 rows is not enforced anywhere.** Nothing
   downstream filters on `status`, so a not-yet-confirmed building enables a
   catchment exactly like a real one. `mwpvl_vouched` is the column a consumer
   has to test, and today no consumer tests it.
8. **The edit's denominator is 136 of 693.** §7. Most of the expanded panel is
   unchecked by any external record.

9. **The facility-class filter is a judgement, not a measurement.** 1,269 of
   the 1,904 OCR'd facilities are dropped on MWPVL's own table heading. The
   heading is a consultancy's classification of its own section, which is the
   same evidentiary status §9.6 warns about for `facility_type`, applied to
   sixty-seven percent of the file rather than to a column.

---

## 10. Related

- [`MWPVL_2025.md`](MWPVL_2025.md) — the article's text layer, the withdrawal
  notice, and the 2013 left truncation §6 above uses.
- [`MWPVL_OCR_PIPELINE.md`](MWPVL_OCR_PIPELINE.md) — where the 635 rows came
  from, and §13.1/§13.2/§13.3, which are three of the ten items in §9.
- [`FACILITY_PANEL_PROVENANCE.md`](FACILITY_PANEL_PROVENANCE.md) — the 104,
  §12.6's duplicate pairs, §12.7's four falsified rows, and §19.2's 289-of-362
  warning that set the standard for §1.
- [`CBP_DETAIL.md`](CBP_DETAIL.md) §5 — why the existing dates are OSHA bounds
  with a margin of zero.
- `src/siting_atlas/common/linkage.py` — the comparator. No rule in this work
  is defined anywhere else.

---

## 11. Wiring the expanded frame into `warehouse/facilities.attach`

*Added 2026-09-14, in response to `docs/AUDIT_2026_09_14.md` §2.1, "Three
different target variables are live at once". Every figure below was read off
disk on 2026-09-14 with `PYTHONPATH=src .venv/bin/python`; none is remembered.*

### 11.1 What was wrong

`warehouse/facilities.attach` hard-coded `facilities.csv`, the **43-row
pilot**. So `data/processed/panel.parquet` — the one panel every model reads —
carried a target built from 43 buildings, while `choice_report.json` ran on
104 and `refit_expanded.json` ran on 693. Three live targets, none labelled,
nothing reconciling them. And `warehouse/panel.py`'s docstring still opened
*"No target variable. The facility panel has not arrived, so `enabled` is
present, all NULL"*, which stopped being true on 2026-09-13.

### 11.2 What was done — an opt-in, not a replacement

`facility_load.FACILITY_FRAMES` now names the three frames once, each with the
`E_operating_by` disposition it needs:

```
  name       file                               disposition
  pilot      facilities.csv                     REPORT     <- DEFAULT_FRAME
  national   national_facilities.csv            EXCLUDE
  expanded   national_facilities_expanded.csv   EXCLUDE
```

The disposition is **part of the frame, not a caller's preference**, and for
the expanded frame it is not a free choice. Loaded in `REPORT`, the expanded
file *raises*: `NAT-0011/NAT-0012`, `NAT-0025/NAT-0026` and
`NAT-0078/NAT-0079` are three contradicting pairs that no reliability weight
separates, and `facility_load._refuse_unresolved` stops the load rather than
manufacture a date. `EXCLUDE` falsifies one side of each pair with the
declared edit, which leaves nothing to adjudicate. This is the same asymmetry
`warehouse/national.load_national` already documented, inherited rather than
invented.

Selection, in precedence order: the `frame=` argument, then
`$SITING_ATLAS_FACILITY_FRAME` (logged at WARNING whenever it fires), then
`DEFAULT_FRAME = "pilot"`. An unknown name raises rather than falling back.

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.panel
  # -> data/processed/panel.parquet            (pilot, unchanged)
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.panel \
    --facility-frame expanded
  # -> data/processed/panel_expanded.parquet
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.national \
    --frame expanded
  # -> outputs/metrics/national_panel_expanded.json
```

**`panel.parquet` cannot be overwritten by a non-default frame.**
`panel.panel_path` derives the output name from the frame, so this is a
structural guard rather than a convention: there is no argument a caller can
pass that lands an expanded target on the reference artefact. Same guard in
`national.artefact_path`.

### 11.3 Before and after, measured

Ever-enabled ZCTAs, out of the panel's 33,791, at the 15-mile DS catchment:

| frame | ZCTAs ever enabled | of 33,791 | switch on in-window | enabled cells | of 1,081,312 |
|---|---|---|---|---|---|
| pilot (default, **before and after**) | **1,257** | 3.72% | 912 | 27,914 | 2.58% |
| national | 2,713 | 8.03% | 2,432 | 42,091 | 3.89% |
| expanded | **8,937** | 26.45% | 5,922 | 203,398 | 18.81% |

`panel.parquet` itself did **not** move: rebuilt after the change, its
`enabled` column is bit-identical to the 2026-09-13 build, and 1,257 is the
same number `facilities.py`'s catchment comment has always quoted.

The catchment expansion behind it: 3,767 facility-ZCTA pairs from 43
facilities, against 28,546 pairs from **540**.

> *The expanded-frame row of the table above, and the 28,546 / 8,937 / 1,783
> counts beside it, were measured on the 2026-09-14 build when 543 facilities
> set a catchment. The attach ledger is now 540 (§11.4). The three derived
> counts have **not** been re-measured and are `[unverified]` at three
> facilities' worth of drift; rebuilding the frame is what settles them. The
> pilot column is unaffected.*

One caution on the last column. 433 of the pilot's 1,257 ever-enabled ZCTAs
were switched on by a Q1-by-convention quarter; on the expanded frame that is
**1,783 of 8,937** `[unverified, see above]` — 259 of the 687 loadable rows
have no `open_quarter` against 19 of 43 in the pilot. The convention is
unchanged and
`open_quarter_imputed` carries it into the panel as before, but it now covers
20% of the treated units rather than 34% of a much smaller set, and the Q1
pile-up `hazard_report.json` measures should be re-measured before anything is
fitted on this frame.

### 11.4 What fails to attach, and why — 693 in, 540 used

Nothing is corrected and no date is invented. Every row that does not reach
the catchment builder is dropped by a rule that already existed:

```
  693  rows in national_facilities_expanded.csv
   -6  FALSIFIED by E_operating_by under EXCLUDE
        MWP-0084, MWP-0615, NAT-0011, NAT-0026, NAT-0036, NAT-0079
  ---
  687  loaded, all facility_type = DS, 0 contradicting pairs left
 -142  no numeric open_year
   -5  postcode is not a ZCTA, so no centroid to fall back to
  ---
  540  set a catchment
```

**The 142 undated rows are loaded and then ignored, not deleted.** They are
exactly the rows `ingest/facility_check` rejects (§7.1, `142 row(s) have a
non-numeric open_year`). `facilities.catchments` already `dropna`s on
`open_year`, so they fall out there, one layer below the load. That is the
decision, and the two alternatives were both refused: dropping them at load
throws away 142 locations, and writing a year would be the Q1-by-convention
defect applied to the *year* rather than the quarter — a substitute standing
in for a value nobody reported, which is the thing §6 and `facility_dedup`
exist to refuse. Keeping them in the frame means any consumer that wants a
location without a date still has one.

**The 5 are a subset of the 7 `geo_status = postcode_not_a_zcta` rows** of §4
— `MWP-0133, -0244, -0432, -0442, -0443, -0498, -0587`, of which 5 carry a
year and 2 do not. `resolve_coordinates` has no centroid for them because
their postcode is absent from the 2020 relationship file, so `catchments`
cannot place them. `MWP-0119` and `MWP-0276`, which used to be on this list,
were the two rows whose "postcode" was really a house number; the OCR repair
resolved both (`GEOCODING.md` §6.1), which is why the list is 7 and not 9.

By comparison the national frame loses 4 of 104 to `E_operating_by` and
nothing else: 100 of 100 remaining rows set a catchment.

### 11.5 Does any existing artefact's inputs change?

No published input moves. Checked, not assumed:

- `data/processed/panel.parquet` — rebuilt on the default frame. `enabled`
  bit-identical; 49 of 50 columns byte-identical. The one difference is
  `home_value`, max absolute difference **9.3e-10**, which is float-summation
  noise in the Zillow aggregation and not attributable to this change (see
  §11.6).
- `experiments/superseded-artefacts/national_panel.json` — regenerated on the default national
  frame and **byte-identical** to its predecessor (`diff` is empty), because
  `summarise` is still called with the file it used to hard-code. Its
  `coordinate_note` is now counted rather than typed — it read "0 of 104"
  literally, which survived the 693-row expansion unchanged — and the counted
  value is also 0 of 104, so the file did not move.
- `experiments/superseded-artefacts/panel_report.json` — gains three keys and loses none:
  `facility_frame`, `path`, `enabled_cells`. A panel report that does not say
  which frame built it is the confusion this section exists to end. No code
  reads this file; five documents cite it.
- `choice_report.json`, `refit_expanded.json`, `mwpvl_merge.json`, the figures
  and the proposal — untouched. `models/` was not modified.

New files, none of which existed before: `panel_national.parquet`,
`panel_expanded.parquet`, `panel_report_national.json`,
`panel_report_expanded.json`, `national_panel_expanded.json`.

### 11.6 Three things found on the way that should be distrusted

1. **`panel.parquet`'s row order is not reproducible.** Two consecutive
   default builds produce content-identical panels whose rows are in different
   order — `pd.read_parquet(a)[['zcta','year','quarter']].equals(...)` is
   `False`, while every column compares equal after sorting on the key. The
   SQL ends `ORDER BY b.zcta, b.year, b.quarter`, so the order is being lost
   between the temp table and the parallel `COPY`. Any consumer comparing two
   panels positionally, or checksumming the file, will see a spurious diff.
   Pre-existing; not introduced here.

2. **§8's expansion projection does not reproduce through
   `warehouse/national`.** §8 says its numbers apply
   "`models/diagnostics.independent_episodes`' definition to the facility
   frame ... exactly as `warehouse/national.summarise` does". Running
   `national.summarise` on the same file gives **453 decisions / 382 episodes
   / 76.4–90.6 per parameter**, against §8's **440 / 378 / 75.6**. Both are
   defensible; they are not the same measurement. Three differences:
   `mwpvl_report.panel` measures all 693 rows where `national.summarise`
   measures the 687 that survive `E_operating_by`; `mwpvl_report` requires a
   non-empty `cbsa_code` **and** `zcta` where `national` requires only a
   resolvable `open_q_index`; and the episode key is
   `(cbsa_code, open_year, open_quarter)` in one and
   `(cbsa_title, open_q_index)` in the other. The sentence claiming they are
   the same move should be read as "the same *kind* of move".

3. **Unvouched and closed rows still enable a catchment.** §9.7 warned that
   nothing filters on `status`; that is now load-bearing rather than
   hypothetical. Of the 540 rows that set a catchment in
   `panel_expanded.parquet`, **9** carry `status = announced` /
   `not_confirmed` — MWPVL explicitly does not vouch for them — **21** carry
   `delayed`, and **2** carry `closed = True` with no `close_year`, which
   `facility_load` turns into `close_q_index = inf`, so they enable their
   catchment through the end of the panel and never switch off. §5.1 argues
   both `closed` rows are parser false positives and should stay open, so the
   outcome is right for the wrong mechanism. `mwpvl_vouched` remains the
   column no consumer tests.

### 11.7 Not done, and named

`src/siting_atlas/models/panel_source.py:10` carries the same false claim the
audit named alongside `warehouse/panel.py:24` — *"The panel ships with
`enabled` present and typed and entirely NULL."* It is untouched here because
`models/panel_*.py` was being written in parallel. Likewise
`warehouse/panel_sql.py:164`'s comment, *"Target placeholder. The facility
panel has not arrived"*, is stale in its second clause; the placeholder itself
is still correct.
