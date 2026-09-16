# MWPVL's 2025 Q1 network article — what the prose gives us

*Saved 2026-09-14 from `https://mwpvl.com/html/amazon_com.html`, 117 pages,
11.3 MB, at `Stuff/MSBA_Project/Amazon Distribution Network Strategy _ MWPVL
International.pdf`. **Not purchased** — the public page, printed to PDF.*

This document covers the **text layer only**, read in full on 2026-09-14. The
facility tables are images and were OCR'd separately; the dates they carry are
the reason the document was fetched. Everything below is available without OCR
and some of it is worth more than the tables.

> **Status corrected 2026-09-14, evening.** This document was written while the
> OCR was still running, and it speaks about the image layer in the future
> tense throughout. **The OCR has finished.** All thirteen table images were
> parsed the same day and `outputs/metrics/mwpvl_extraction.json` reports
> **1,904 facilities, 1,420 with an opening year, 873 with a month**, of which
> **635 are US small-package delivery stations**. An earlier run of the same
> pipeline had read two tables and returned 591 rows; several documents written
> that morning still quote it. See
> [`MWPVL_OCR_PIPELINE.md`](MWPVL_OCR_PIPELINE.md) for the image layer and
> [`PANEL_EXPANSION.md`](PANEL_EXPANSION.md) for what entered the panel.
>
> **No finding in this document changes.** Everything below was read out of the
> prose and none of it depended on the tables. Three items are now *cheaper*
> rather than different, and are marked where they occur: §3.5 (the heavy/bulky
> network now has 121 parsed rows of its own), §4 (widening to fulfilment
> centres now costs nothing — 385 US FC rows are parsed and sitting unused),
> and §5's OCR calibration, which is still not run.

Text extracted with `pdftotext -layout`: 1,074 lines, 63 KB, of which perhaps
120 lines are prose and the rest are page furniture.

---

## 1. The finding that reverses an earlier decision

[`NLRB.md`](NLRB.md) §219-225 excludes MWPVL from the capture-recapture design,
and the reasoning is correct as written:

> *"MWPVL has a capture probability of zero for every facility that did not
> exist in April 2012, and for every delivery station ever, because delivery
> stations did not exist as a facility class in 2012."*

That reasoning applies to `data/raw/mwpvl/Amazon.com Distribution Network
Strategy.pdf`, which is the **April 2012** snapshot. **This is a different
document.** Line 53: *"As of 2025 Q1, to the best of our knowledge, Amazon
operates the following global distribution infrastructure"*, and it carries a
dedicated section — *"The Amazon 'Last Mile' Delivery Station Network for
Small Packages in the United States"* — with its own table spanning
twenty-eight pages.

The structural zero is gone. The exclusion was right about the 2012 file and
must not be carried over to this one, and `NLRB.md` should say so rather than
being silently contradicted.

**What that makes available: a fourth list.** The three-list model measures
dependence between OSHA, NLRB and OSM. MWPVL's capture mechanism — a logistics
consultancy tracking industry announcements, permits and trade press for
sixteen years — is unrelated to workplace injury, to union petitions, and to
whether a volunteer drew a building. A fourth list with a genuinely different
mechanism tightens the coverage interval rather than merely restating it.

---

## 2. The thesis, happening in public, with a date

Lines 47-51, verbatim and unedited:

> *"Please note that in future we will no longer be updating this information
> online due to the high rates of plagiarism of this content. People seem to
> think that stealing digital content is fine but we remain the only accurate
> source of this data and we have invested significantly to support this
> project for over 16 years. If there is an interest in obtaining current
> information available in XLSX format then please contact us and we can
> provide details regarding the commercial terms."*

Read that against what this project claims. The argument has been that the
asymmetry between Amazon and a county planning department **is not scarcity,
it is price** — the data exists, it is sold, and the people who bear the
consequences of a siting decision cannot buy it.

This is that argument as a primary source. The only free public census of
Amazon's US network is being withdrawn, the withdrawal is attributed to the
data being free, and the same paragraph names the commercial alternative. It
is not an illustration of the thesis. It is the thesis, dated, quotable, and
written by the party with the least incentive to help this project make it.

It also answers the purchasing question that has been open since Option E in
[`ALTERNATIVES.md`](../ALTERNATIVES.md): the product is **XLSX**, terms are
quoted on request, and the contact is in the paragraph.

**The uncomfortable half.** If the free page is withdrawn, this saved PDF
becomes irreproducible for anyone who reads the capstone afterwards. A finding
resting on a source that no longer exists is weak. So the copy must be
archived as evidence, the retrieval date recorded, and the 2012 file kept
alongside it — two vintages of the same source, thirteen years apart, is
itself a measurement of how the free channel decayed.

---

## 3. What the prose says that our data assumes otherwise

These are stated facts in the document that contradict or sharpen something
the code currently does. Each one is a cheap fix and a real one.

### 3.1 Amazon closes buildings, and our panel has no exit

Lines 44-45: *"In 2022-2023, the Amazon distribution network was impacted by
the company's need to reduce operating expenses. **Over 123 buildings were
either closed, canceled or delayed, primarily in the USA.**"*

The panel treats a facility as opening and then existing forever. There is no
closure event, no censoring, no exit. 123 is not a rounding error against the
104 national decisions the choice model is fitted on — it is larger.

This matters in a specific way rather than a vague one. A cancelled building
is a site Amazon **chose and then unchose**, which under a discrete-choice
reading is a revealed preference we are recording with the wrong sign. And a
site that was chosen, built, and closed contributes to the OSHA extract
exactly like one still operating, so some share of the 340 cities OSHA has
ever inspected an Amazon facility in are buildings that are gone.

### 3.2 A stated service radius

Line 383: delivery stations are *"designed to service a **45-mile radius**"*.

The cost model uses Daganzo's continuous approximation and has to assume a
catchment. This is an externally stated figure from an industry source, which
is better than an assumption and is at minimum a sensitivity test the Monte
Carlo should carry.

### 3.3 Zero square feet is a sentinel, not a missing value

Lines 228-230 and 388-389 both say it: *"if the square footage of the facility
is set to zero then the operation is **co-located in another building**
therefore we do not double-count the square footage."*

This is exactly Van den Broeck's erroneous-inlier case inverted. A naive clean
does one of two wrong things with a zero: treats it as missing and imputes it,
or treats it as a real zero and lets it drag an average down. It is neither.
It is a coded statement that the facility exists and shares a roof. It belongs
in `warehouse/sentinels.py` before any OCR'd square footage is used.

### 3.4 The source contradicts itself on delivery-station size

```
  line 379   "typically in the 100,000 to 140,000 sq. ft. range"
  line 634   "mid-sized facilities typically between 60 - 100,000 sq. ft."
```

Same document, same facility class, non-overlapping except at one endpoint.
Our own classification prompt in `scripts/make_unlabelled_batches.py` tells the
researcher *"100,000-250,000 sq ft"*, which agrees with neither.

This is a Rahm & Do single-source instance-level inconsistency, and the honest
treatment is not to pick one. It is to record that the best commercial source
disagrees with itself by a factor of two on the defining attribute of this
project's target facility, and to stop using square footage as a
classification rule where a stated type is available.

### 3.5 Two delivery-station networks, not one

Lines 378-381 and 562-565: the small-package network launched **late 2013**;
a separate network for **heavy/bulky merchandise, 60-300 lbs, from 2017**, now
broken out into its own table. *That table is now parsed:
`09_us_delivery_heavy_bulky`, 121 rows
(`outputs/metrics/mwpvl_extraction.json`). The pooling problem below is
therefore no longer hypothetical — the two networks can be separated, and
`PANEL_EXPANSION.md` admits only the small-package 635.*

Our classifier emits one `DELIVERY STATION` label. These serve different
merchandise with different vehicles and different economics, and pooling them
is a specification choice nobody has made deliberately. The 2013 date is also
a **left truncation**: nothing before it can be a small-package delivery
station, which is a free consistency check on every OCR'd date.

---

## 4. The identification strategy the document hands over

Lines 715-740 describe a structural break, and it is the same one the
published literature is built on.

> *"Until 2013, fulfillment center locations in the U.S. were determined based
> on state tax considerations."*

Before 2013, siting was driven by avoiding sales-tax nexus — which pushed
Amazon into rural low-cost states. After the tax advantage collapsed, siting
was driven by proximity to demand. The document names the states that cut
deals: **Arizona, Tennessee, Pennsylvania, Kentucky, Indiana, Delaware, South
Carolina, Virginia**, each in exchange for job-creation targets.

Houde, Newberry & Seim's Econometrica paper runs on precisely this variation.
Having the mechanism described in prose by an industry source is not a
substitute for their data, but it does three things:

```
  1  it dates the break, so a pre/post split is defensible rather than fitted
  2  it names the treated states, so the deal states can be separated
  3  it gives a REASON the covariates should behave differently across 2013,
     which is a testable prediction rather than a robustness check
```

The catch, and it is a real one: delivery stations only began in late 2013, so
the entire delivery-station panel sits **after** the break. The tax variation
identifies fulfilment-centre siting, not ours. It is usable if the project
widens to fulfilment centres, and not otherwise. That should be decided
deliberately rather than discovered halfway through.

*Updated 2026-09-14, evening: the data cost of that widening is now zero.
`01_us_fulfillment_center` is parsed — **385 US fulfilment centres, 267 with a
year, 185 with a month** — and sits unused in `data/interim/mwpvl_facilities
.csv`. The decision is still a decision, but it is no longer blocked on
anything.*

---

## 5. Dates recoverable from the prose alone

The closed-and-converted list at lines 642-711 gives roughly twenty facilities
with opening and closing dates, in text, no OCR needed. A sample:

```
  TUL1  Coffeyville, KS    opened Apr 1999   closed Feb 2015   915,000 sq ft
  RNO1  Fernley, NV        opened Jan 1999   closed early 2015 786,000
  RNO2  Red Rock, NV       opened Jan 1999   closed Mar 2009   322,560
  ATL1  McDonough, GA      opened Oct 1999   closed 2001       800,000
  MDW1  Munster, IN        opened Oct 2007   closed Mar 2009    75,000
  BNA1  Lebanon, TN        opened Sep 2011                     449,000
  AVP6  Pittston, PA                         closed Jul 2016   437,446
  AVP8  Pittston, PA       opened Aug 2016
  DFW1  Irving, TX         opened 2005       closed Apr 2011   493,290
  SEA6/8 Bellevue, WA      opened Aug 2007   closed 2017       313,300
```

**Be clear about what this is worth: almost nothing for our target.** These are
fulfilment centres. Exactly **one** entry touches the delivery-station panel —
*"Nashua, New Hampshire (BOS1): A 63,750 sq. ft. jewelry fulfillment center was
converted into a delivery station for New England in the **summer of 2018**."*

So the prose yields one dated delivery station. The delivery-station dates are
in the image tables, and the OCR run is the only route to them. This section
exists so nobody mistakes twenty dated fulfilment centres for progress on the
thirteen undated delivery stations.

What the twenty *are* good for is **calibrating the OCR**. They are dates in
the text layer, which is exact, describing facilities that also appear in the
image tables. Wherever both exist, the text layer grades the OCR without
costing us anything.

---

## 6. What this document is not

MWPVL says so itself, four separate times, and it should be quoted rather than
glossed:

```
  line 193   "This distribution network is unfolding slowly and the list of
              facilities below is likely incomplete."
  line 232   "The data concerning the Amazon Fresh network is challenging to
              track and this is the best information that is currently
              available."
  line 391   "The data concerning this network is challenging to track so we
              provide the best information available within the table below."
  line 865   "Our list of these facilities is undoubtedly incomplete."
  line 1053  "there is a possibility that information contained within this
              paper may be out of date or inaccurate."
```

Line 391 is the delivery-station table — our table — and the author is telling
us it is incomplete.

**This does not give the project 100% confidence and it cannot.** It is a
fourth incomplete list, from a source that declares its own incompleteness. The
correct use is the one the project is already set up for: another capture
occasion, which *narrows* the interval on how many facilities none of the lists
contain. An estimate that got tighter is a real gain. A census is not on offer
from anybody, at any price, which is itself the point.

---

## 7. Actions this generates

```
  NLRB.md sec.5        record that the 2012 exclusion does not extend to the
                       2025 file, and why
  ALTERNATIVES.md E    correct "frozen at April 2012" -- that is the OTHER
                       copy. Option E is cheaper than written: the vintage is
                       current and the format is XLSX
  sentinels.py         sq ft == 0 means co-located, not missing
  edits.py             no small-package delivery station before late 2013
  montecarlo.py        45-mile service radius as a sampled parameter
  choice model         closures and cancellations exist; the panel has no exit
  batch prompt         drop the 100,000-250,000 sq ft rule, the source
                       disagrees with itself
```

None of these needs the OCR. All of them were invisible until somebody read
the prose, which took ten minutes and had been skipped for a day in favour of
the tables.

## 8. Related

- [`NLRB.md`](NLRB.md) §5 — the exclusion this revises.
- [`../ALTERNATIVES.md`](../ALTERNATIVES.md) Option E — buying the current product.
- [`CLEANING_LITERATURE.md`](CLEANING_LITERATURE.md) — Rahm & Do on §3.4, Van den Broeck on §3.3.
- [`SATELLITE.md`](SATELLITE.md) — the failed route to the dates these tables hold.
- [`MWPVL_OCR_PIPELINE.md`](MWPVL_OCR_PIPELINE.md) — the image layer, all
  thirteen tables, and the 1,904 facilities they hold.
- [`PANEL_EXPANSION.md`](PANEL_EXPANSION.md) — the 635 delivery stations that
  entered the panel, and the 1,269 rows deliberately left out.
