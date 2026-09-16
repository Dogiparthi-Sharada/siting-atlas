# Geocoding the facility panel — 65% on the retired panel, then the OCR was fixed and it is 72%

*Written 2026-09-14. Code `src/siting_atlas/ingest/geocode_facilities.py`.
Artefact `data/external/facility_panel/geocoded_expanded.csv`, 693 rows keyed
on `facility_id`. Input `data/external/facility_panel/
national_facilities_expanded.csv`, **read only, never written**.*

> **UPDATED 2026-09-14, later the same day. The upstream defect this document
> blamed has been fixed, and the match rate moved 65.0% → 72.3%.** Three OCR
> faults in `ingest/mwpvl_grid.py` and one parsing fault in
> `ingest/mwpvl_fields.py` were found and repaired; §10 is the before/after and
> [`MWPVL_OCR_PIPELINE.md`](MWPVL_OCR_PIPELINE.md) §§8.5–8.7 and §9 are the
> diagnoses. **The numbers in §3–§6 below are the BEFORE run and are left
> standing**, because they are what the diagnosis was made from and a
> before/after with the "before" quietly rewritten is not a measurement. Read
> them as measurements of the **superseded 700-row panel**: no file on disk
> reproduces them any more.
>
> **CORRECTED 2026-09-15. The sentence that used to stand here — "the artefact
> on disk is still the before run" — is wrong, and so is its mirror image
> elsewhere in the project, that the improved run "may live only in uncommitted
> `data/interim/*_rebuilt.csv`".** The panel *was* rebuilt. On this disk
> `data/external/facility_panel/geocoded_expanded.csv` and
> `data/interim/geocoded_expanded_rebuilt.csv` are **byte-identical**
> (`diff` reports no difference, same md5), both 693 rows and 501 `Match`, and
> the same is true of `national_facilities_expanded.csv` against
> `national_facilities_expanded_rebuilt.csv`. The canonical-versus-rebuilt
> distinction this document is organised around has collapsed: there is one
> run, not two. Neither file is committed — `git ls-files
> data/external/facility_panel/` returns only `facilities.csv` and
> `national_facilities.csv` — so there is no committed version of either, and
> **no "before" file exists on disk at all**. See §10.3.

**Status: DONE, PARTIAL, AND USABLE.** 501 of 693 facilities carry a real
street-level coordinate where previously zero did
([`AUDIT_2026_09_14.md`](../AUDIT_2026_09_14.md) §1.9, ranked item 6) — 72.3%,
on the current panel. The 455-of-700 figure below it is the same measurement
on the retired panel. Nothing consumes the file yet — wiring it into the
warehouse is a separate job.

Two numbers matter more than the headline. **Zero** coordinates landed outside
the state their address claims. And the 192 that failed did **not** fail
because the geocoder is weak; they failed because the addresses handed to it
are damaged, and that damage is a defect in the panel, not in this run.

---

## 1. Was the endpoint even reachable?

Yes. This was checked first, because this machine has no general internet and
the honest outcome was expected to be a handoff file.

```
$ curl -o /dev/null -w "%{http_code} %{time_total}\n" \
    "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?\
benchmark=Public_AR_Current&format=json&address=5900+OLD+SEWARD+HIGHWAY..."
200 0.678808
```

The batch endpoint — a multipart POST, a different code path from the GET —
was then tested separately with three addresses including a deliberate
nonsense one, and returned `Match/Match/No_Match` correctly in 0.44 s. The
full panel ran in four chunks of 200 in a few seconds. No key, no quota, no
rate limit encountered.

If it ever stops being reachable, `--write-input <path>` writes the
header-less `id,street,city,state,zip` file the service expects, for
submission from a machine that does have access.

## 2. What was run

`https://geocoding.geo.census.gov/geocoder/geographies/addressbatch`,
benchmark `Public_AR_Current`, vintage `Current_Current`, 200 rows per POST.

The **`geographies`** endpoint was used rather than `locations`. It costs the
same one request and additionally returns the state FIPS, county, tract and
block of the census block the *returned point* falls in. That is what makes
§4's wrong-state check free; with `locations` it would have needed one extra
round trip per matched row.

## 3. The match rate

*This section and §§4–6 are the **before** run, on the superseded 700-row
panel. The current numbers are in §10.1.*

```
rows 700 | Match 455 (65.0%) | Exact 315 | Non_Exact 140
         | No_Match 242 | Tie 3
```

The brief anticipated roughly 80%, from the earlier 133-row run that matched
107. That 80% was not reproduced, and the reason is entirely visible in the
split by provenance:

| source | rows | matched | rate |
|---|---|---|---|
| `NAT-*` (hand-collected permits) | 104 | 87 | **83.7%** |
| `MWP-*` (OCR'd from the MWPVL PDF) | 596 | 368 | **61.7%** |

The hand-collected rows matched at 83.7%, slightly *better* than the earlier
run's 80%. The OCR'd rows dragged the total down by 22 points. This is not a
geocoder result. It is an OCR result.

## 4. Did any coordinate land in the wrong state?

**No. Zero of 451 comparable rows.** (455 matched, less 4 whose `state` the
panel leaves blank, which cannot disagree with anything and are recorded `NA`
rather than `False`.)

A check that cannot fail is not a check, so it was made to fail on purpose.
One row's claimed state was overwritten with `TX` and re-run:

```
facility_id claimed_state returned_state state_agrees
   NAT-0001            TX             AK        False   <- fires correctly
   NAT-0002            CA             CA         True
```

A second, independent check backs it up. `zcta_of_point` is computed locally
by point-in-polygon against the TIGER 2020 ZCTA shapefile already on disk
(`data/interim/zcta_geom.parquet`) — the Census agreeing with itself is not
corroboration, a shapefile is. All 455 points also fall inside the US
bounding box (lat 21.31–64.84, lon −158.10 to −70.90).

**Independent cross-check against the earlier run.** 100 `facility_id`s
overlap with `data/external/satellite/geocoded.csv`; 83 have a coordinate in
both. Maximum absolute difference: **1.0e-12 degrees**. Zero rows matched in
one run and not the other. The batch endpoint reproduces the single-address
endpoint exactly.

## 5. Why 245 rows failed — be unkind about this

```
no_match_street_not_in_tiger           218
no_street_address_in_panel              24
ambiguous_tie_no_coordinate_returned     3
```

**24 rows have no street address at all.** Not a geocoding failure; there was
nothing to geocode. All but one are `MWP-*`.

**64 rows have a street with no house number** ("Goodman Way", "Trippel
Road") — 63 of them `MWP-*`. 54 of those 64 failed. A street name without a
number cannot be geocoded by anything, ever.

**The OCR split street from city in the wrong place.** These are verbatim
from the panel:

| `site_address` | `city` | `state` | what it should be |
|---|---|---|---|
| `3115 N. Road` | `Higley Phoenix` | AZ | 3115 N. **Higley** Road, Phoenix |
| `9807 E. Road` | `Prescott Valley Valley` | AZ | a road name is missing |
| `1900 Pine Street North Little` | `Rock` | AR | …, North Little Rock |
| `; Location 6735 Trippel Road` | `Theodore` | AL | leading OCR junk |

A city field of `Rock` and a street ending `North Little` is one token
boundary in the wrong place. `MWP-*` rows have a 3-or-more-word city 32 times
against `NAT-*`'s 5, and 43 have no city at all.

*Every one of those four is now read correctly. The cause was not the OCR
mis-reading a character; it was the pipeline putting the words back in the
wrong order — see §10.*

**This is not recoverable by trying harder.** Two extra passes were run over
all 245 failures to prove it, rather than assumed:

| retry strategy | extra matches |
|---|---|
| street + ZIP only (drop the suspect city/state) | 1 of 245 |
| street + city + state (drop the ZIP) | 4 of 245 |

Four rows. Neither pass is implemented, because a second method flag and the
code to carry it is not worth four rows. The 218 `no_match` streets are
genuinely absent from the TIGER address-range file — a mix of OCR damage and
new-build industrial roads that TIGER has not caught up with. Industrial
addresses geocode badly; that part is expected. The OCR part is not.

**The fix is upstream.** Repairing the street/city split in the MWPVL
extraction would recover a large share of the 218 at a stroke. No amount of
work inside this module will.

## 6. A defect found on the way out: 28 panel ZIPs are disputed

Not what this task was for, but it falls out of the data and should not be
sat on. Comparing the geocoder's own normalised ZIP against the panel's:

- **All 315 `Exact` matches agree with the panel's ZIP. Zero disagree.**
- **28 of the 140 `Non_Exact` matches disagree.** The correlation is perfect,
  and the direction is the interesting part: a wrong ZIP in the input is
  *why* the match got downgraded to `Non_Exact`. The geocoder still found the
  street — in a different postcode.

Who is right? Adjudicated by the independent TIGER polygon (§4), which is
neither party to the dispute:

| verdict | n |
|---|---|
| polygon sides with the geocoder — **panel ZIP is wrong** | 18 |
| polygon sides with the panel — geocoder's ZIP label differs, point is fine | 7 |
| polygon agrees with neither | 3 |

So **18 confirmed wrong ZIPs**, not 28. The seven are ZCTA-polygon-versus-
postal-ZIP disagreement, which is normal at industrial sites and is not an
error in anything.

Worse, and airtight: **9 of the 700 panel ZIPs are not a valid ZCTA at all**
and would join to nothing in the warehouse. Every one of the nine also has a
blank `state`, which is the same OCR damage as §5.

| facility | panel ZIP | geocoder ZIP | reading |
|---|---|---|---|
| MWP-0133 | 49804 | 19804 | Wilmington DE; leading `1`→`4` |
| MWP-0432 | 98759 | 28759 | Mills River NC; leading `2`→`9` |
| MWP-0587 | 94054 | 84054 | N. Salt Lake UT; leading `8`→`9` |
| MWP-0498 | 17411 | 17111 | Harrisburg PA; digits transposed |
| MWP-0244, MWP-0442, MWP-0443 | 50114, 98728, 29084 | — | unmatched, same pattern |
| MWP-0119, MWP-0276 | 12675, 10100 | — | no address at all |

Four of the nine are repairable directly from `returned_zip` in this file.
**This module did not repair them** — it does not own that file. The evidence
is in the `returned_zip` and `zip_agrees` columns for whoever does.

### 6.1 Re-adjudicated after the OCR fix — nine becomes seven, and the blank state was a symptom

Two of the nine were never postal codes. `MWP-0119` and `MWP-0276` are the two
rows §5 lists as having no address at all, and the reason both were true at
once is that the reading-order fault (§10) had moved `USA,` in front of the
city, which stopped the address pattern matching, which left `parse_address`
reaching for the first five-digit number in the cell. That number was the
**house number**:

```
  MWP-0119   was: postcode 12675, no street, no city
             is:  12675 Liberty Boulevard, Englewood, 80112
  MWP-0276   was: postcode 10100, no street, no city
             is:  2203 Lakeside Boulevard, Edgewood, 21040
```

80112 and 21040 are both valid ZCTAs. **Seven remain.**

The claim above that *"every one of the nine also has a blank `state`, which is
the same OCR damage as §5"* is wrong and is worth correcting, because it reads
as a second independent witness and is not one. `state` in the panel is
**derived** from the postal code by `warehouse/mwpvl_geo.resolve`, so a
postcode that is not a ZCTA produces a blank state by construction — measured:
all 7 blank-state rows in the rebuilt panel are exactly the 7
`postcode_not_a_zcta` rows, and no others.

There *is* a second witness, and it is better: the OCR read the **state name**
out of the address text correctly on all seven, in `mwpvl_facilities.addr_region`.

| facility | panel ZIP | OCR'd state name | geocoder `returned_zip` | that ZCTA's county | verdict |
|---|---|---|---|---|---|
| MWP-0133 | 49804 | Delaware | **19804** | New Castle, DE | settled, two witnesses agree |
| MWP-0432 | 98759 | North Carolina | **28759** | Henderson, NC | settled, two witnesses agree |
| MWP-0587 | 94054 | Utah | **84054** | Davis, UT | settled, two witnesses agree |
| MWP-0498 | 17411 | Pennsylvania | **17111** | Dauphin, PA | settled, two witnesses agree |
| MWP-0244 | 50114 | Iowa | — (No_Match) | — | ONE witness only |
| MWP-0442 | 98728 | North Carolina | — (No_Match) | — | not settled |
| MWP-0443 | 29084 | North Carolina | — (No_Match) | — | not settled |

**Four proposed repairs, and nothing applied.** For MWP-0133, MWP-0432,
MWP-0587 and MWP-0498 two sources that cannot have copied each other — the
Census geocoder's normalisation of the street it found, and the state name
printed in a different part of the same table cell — agree on a postcode whose
county is in the right state. Each is a single leading digit.

They are **not applied here**, and not because of caution for its own sake.
Fellegi & Holt §1's second option is to resolve by *collection*, and the
project's dispositions (`warehouse/edits.py`) deliberately omit `CORRECT`; an
edit localises the failing field and records it. What this section is, is the
localisation and the evidence. Whoever applies them must do it as a declared,
logged, reversible edit carrying the two witnesses, not as a `.replace()` in a
parser.

The last three are explicitly **left alone**. MWP-0244 is `1301 E Gateway
Drive, Grimes, Iowa` and Grimes is 50111, one digit from 50114 — but "the city
name suggests it" is not evidence of the same kind, it is a guess with a
plausible shape, and 50111 is exactly the sort of repair that looks right in a
table and is unfalsifiable afterwards. MWP-0442 (Enka Village, NC) and MWP-0443
(Kannapolis, NC) have no candidate ZCTA in `zcta_county.parquet` at all.

## 7. The output file, and the one rule for reading it

`data/external/facility_panel/geocoded_expanded.csv`, 693 rows, 26 columns,
keyed on `facility_id`. One row per input row, including failures.

| column | meaning |
|---|---|
| `latitude`, `longitude` | the geocode. **Populated only on a clean `Match`** |
| `match_status` | `Match` / `No_Match` / `Tie`, the geocoder's own word |
| `match_quality` | `Exact` / `Non_Exact`, the geocoder's own word |
| `matched_address` | the normalised address it actually resolved to |
| `geocode_method` | `census_batch_geographies`, else blank |
| `returned_state_fips`, `returned_state`, `county_fips`, `tract`, `block` | geography of the returned point |
| `claimed_state`, `state_agrees` | §4. `NA` where either side is blank |
| `claimed_zip`, `returned_zip`, `zip_agrees` | §6 |
| `zcta_of_point`, `zcta_agrees` | independent point-in-polygon, TIGER 2020 |
| `fallback_latitude`, `fallback_longitude`, `fallback_method` | see below |
| `failure_reason` | why a row has no coordinate |

**THE RULE. `latitude`/`longitude` are geocodes and nothing else.** The 2
`Tie` rows get no coordinate; a tie is an unresolved ambiguity and keeping one
silently is how a facility ends up at the wrong one of two candidates.

ZCTA centroids *are* provided for 189 of the 192 unmatched rows — but in
`fallback_latitude`/`fallback_longitude`, flagged `zcta_centroid_gazetteer`,
and blank on every matched row. **Do not coalesce them into
`latitude`/`longitude`.** A ZIP centroid is accurate to the width of a
postcode; presented as a geocode it produces a distance covariate that looks
precise and is not. That is exactly the failure the warehouse already has and
this file exists to end.

Verified invariants: 0 null coordinates on a `Match`; 0 non-null coordinates
on a non-`Match`; 0 fallbacks on a `Match`; 0 points outside the US bbox.

## 8. Reproducing it

```
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.geocode_facilities
```

~10 seconds, free, no key. Writes the CSV and prints the §3/§4/§5 summary.
`--panel`, `--out`, `--chunk` override the defaults; `--write-input <path>`
produces the handoff file described in §1 instead of calling the service.

The service is not deterministic across vintages — `Public_AR_Current`
advances. The run above was 2026-09-14. Re-running later may shift a few
rows; the `match_quality` and agreement columns are how you would detect it.

## 9. What is now unblocked, and what is not

**Unblocked, for 501 facilities (72.3%):** distance to nearest sortation
centre, distance to highway interchange, distance to the existing network,
catchment overlap, cannibalisation — the family §1.9 named.

**Not unblocked.** Any of those features computed on this file is computed on
a **72% subsample that is not missing at random**: it over-represents
hand-collected `NAT-*` rows (83.7% matched) against OCR'd `MWP-*` rows
(70.3%). If matching correlates with anything — urban versus greenfield,
older versus newer sites — a distance covariate built naively on the matched
rows carries that selection into the model. Say so, or use the fallback
column with the flag visible and report both.

**The selection is smaller after §10 and it has not gone away.** The gap
between the two sources was 22.0 points on the retired panel and is 13.4
points now. A 72% subsample that still over-represents hand-collected rows is
the same problem with a better constant, and the sentence above survives
unchanged.

The honest next move was to fix the MWPVL street/city split and re-run this
rather than build distance features on the matched subsample. **That has now
been done — §10 — and the denominator it lifted is the one quoted above.**

## 10. The upstream fix, and what it moved

*2026-09-14, later the same day. `ingest/mwpvl_grid.py`,
`ingest/mwpvl_fields.py`. Diagnoses in
[`MWPVL_OCR_PIPELINE.md`](MWPVL_OCR_PIPELINE.md) §§8.5–8.7 and §9.*

§5 read the damage as "the OCR split street from city in the wrong place".
That was the symptom. Reading the **raw cells** rather than the parsed output
found four distinct faults, none of them a mis-read character:

| # | fault | where | size |
|---|---|---|---|
| 1 | reading order inside a cell used a fixed 12-px lattice, so words on one printed line straddled a band edge and reordered | `mwpvl_grid.build_rows` | 402 cells reordered; 165 streets, 148 cities, 106 states changed |
| 2 | the column HEADING (`State / Code / Location / …`) sits above the first row anchor and was given to row 0 | `mwpvl_grid.build_rows` | 11 rows, one per table that has a heading |
| 3 | a wrapped ZIP+4 tail (`85034-` / `6852`) became the next row's house number | `mwpvl_grid.build_rows` | 73 streets |
| 4 | in a merged cell holding two facilities, the street was read from the FIRST address and the postcode from the last | `mwpvl_fields.parse_address` | 91 streets |

Fault 1 is the one §5 was looking at. `3115 N. Road` / `Higley Phoenix` is
`Road,` in band 98 and `Higley` in band 99, two pixels apart on the same
printed line. Fault 4 is the bigger one for geocoding: it produced rows
pairing one building's street with another building's city and postcode.

### 10.1 Before and after, on every metric that could have been damaged

Both columns are full re-runs on this machine, same day, same service. The
"before" column is reproduced from the frozen artefacts, not remembered.

| metric | before | after |
|---|---|---|
| **Census batch, all rows** | 455 / 700 = **65.0%** | 501 / 693 = **72.3%** |
| &nbsp;&nbsp;`NAT-*` hand-collected | 87 / 104 = 83.7% | 87 / 104 = **83.7%** |
| &nbsp;&nbsp;`MWP-*` OCR'd | 368 / 596 = 61.7% | 414 / 589 = **70.3%** |
| &nbsp;&nbsp;source gap | 22.0 pts | **13.4 pts** |
| &nbsp;&nbsp;`Exact` matches | 315 | **383** |
| &nbsp;&nbsp;coordinate outside claimed state | 0 | **0** |
| rows with no street at all | 24 | **9** |
| rows with a street and no house number | 88 | **67** |
| panel postcodes that are not a ZCTA | 9 | **7** |
| **MWPVL extraction** rows | 1,904 | 1,904 |
| &nbsp;&nbsp;delivery-station rows | 635 | 635 |
| &nbsp;&nbsp;rows with a postcode / year / month | 1,767 / 1,420 / 873 | **1,767 / 1,420 / 873** |
| **OSHA `E_operating_by`** rows linked | 157 | **208** |
| &nbsp;&nbsp;pass rate | 93.6% | **94.7%** |
| &nbsp;&nbsp;date plausibility | 1,413/1,420 = 99.5% | **99.5%** |
| `ruff check src tests` | pass | pass |
| `pytest tests` | 658 passed, 2 xfailed | **658 passed, 2 xfailed, 0 failures** (660 collected) |

The `pytest` row is not a before/after of the OCR fix — it is a repo-wide
count that moves whenever a test is written. Both columns read "658 passed"
when this table was first built; the suite was re-collected and re-run on
2026-09-15 and now stands at **660 collected, 658 passed, 2 xfail, 0
failures**, with `ruff check src tests` still clean. 787 is stale wherever it
appears.

Two lines deserve reading twice. **The OSHA linkage rose by 51 rows** — the
edit that grades this whole extraction can now speak about a third more of it,
because the addresses it links on are right. And **the `NAT-*` rate did not
move at all**, which is the control: the hand-collected rows do not go through
this parser, so a change that moved them would have been a change to the
geocoder, not to the OCR.

### 10.2 Why the panel has 693 rows and not 700

Not seven rows lost. The delivery-station extraction is still 635 rows. With
the addresses repaired, `warehouse/mwpvl_merge`'s Fellegi–Sunter screen
recognises **eight more MWPVL rows as buildings already in the hand-collected
panel** (32 → 40) and holds one fewer for clerical review. Those are
duplicates that were previously invisible because the MWPVL side of the
comparison carried a corrupted street.

### 10.3 Reproducing it, and the one thing this session did not do

```
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.mwpvl_tables
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.mwpvl_panel
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.mwpvl_merge
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.geocode_facilities
```

When this section was written, the first two were re-run and the third was
not: `mwpvl_merge` rewrites
`data/external/facility_panel/national_facilities_expanded.csv`, which was
frozen for that session, so the after column above was measured by pointing
`mwpvl_merge.EXPANDED` at
`data/interim/national_facilities_expanded_rebuilt.csv` and running the
geocoder with `--panel` against that. Three side files held the evidence:

```
  data/interim/national_facilities_expanded_rebuilt.csv   693 rows
  data/interim/mwpvl_merge_rebuilt.json                   the merge report
  data/interim/geocoded_expanded_rebuilt.csv              693 rows, 501 Match
```

> **CORRECTED 2026-09-15 — all four lines have since been run, and the
> distinction this subsection is built on no longer exists.** Measured today:
>
> ```
>   diff data/external/facility_panel/geocoded_expanded.csv \
>        data/interim/geocoded_expanded_rebuilt.csv                 -> identical
>   diff data/external/facility_panel/national_facilities_expanded.csv \
>        data/interim/national_facilities_expanded_rebuilt.csv      -> identical
>   geocoded_expanded.csv    693 rows | Match 501 (72.3%) | No_Match 190 | Tie 2
> ```
>
> The canonical file **is** the after run; the side files are exact copies, not
> a better version held back. The old sentence here, "the committed
> `geocoded_expanded.csv` is still the before run", was wrong in both of its
> parts: it is not the before run, and it is not committed. `git ls-files
> data/external/facility_panel/` lists only `facilities.csv` and
> `national_facilities.csv`, and `git ls-files data/interim/` lists only
> `.gitkeep`. **The 693-row panel and its geocodes exist only on this disk, in
> two identical copies, and nothing reproducing the 455/700 before run
> survives anywhere.** Deleting the side files is now a tidy-up with no
> information loss, not a step that must wait for a rebuild.

Whoever owns the panel should commit it. Nothing else needs to change.
