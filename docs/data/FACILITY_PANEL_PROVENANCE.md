# How the facility panel was built, and where it is weak

**The target variable now exists.** `data/external/facility_panel/facilities.csv`
holds **43 rows**, `python -m siting_atlas.ingest.external --check` reports
`facility_panel ok  43 facilities, 2015-2025, 1 operator(s)`, and the hazard
model has something real to predict for the first time.

This document is the provenance record for that file. It is deliberately
unflattering. Five collection methods failed before one worked, the source
that worked measures something other than what we want, and the delivered
file contains defects we have found but not yet repaired. All of that is
written down here rather than discovered by a reviewer.

**And the model fitted on it did not work.** That is reported in
[`../STATUS.md`](../STATUS.md) rather than here, because it is a result about
the model, not about the data — but it is the reason this document matters.
43 buildings could not identify a siting model, and a reader who takes this
provenance record as a success story has read it wrong.

---

## Read this part even if you read nothing else

Four things about this dataset would invalidate a naive reading of it.

```
  1  THE DATES ARE UPPER BOUNDS, NOT OPENINGS.
     27 of the 43 dates come from the date OSHA opened an INSPECTION
     CASE at the address. That proves the building was operating by
     then. It does not say when it opened. Measured against the five
     addresses whose true opening date is independently known, the
     bound held 5 of 5 times but the lag between opening and first
     inspection ran 4, 13, 57, 69 and 345 months -- four months to
     twenty-eight years.

  2  THE SAMPLE IS SELECTED ON INJURY, NOT ON EXISTENCE.
     OSHA goes where people get hurt and where people complain.
     Across all 474 Amazon buildings it found nationally, the
     establishment name identifies 81 fulfilment centres and 19
     delivery stations. Delivery stations are the thing we are
     modelling and they are the thing this source sees worst.

  3  THE APPARENT TIME TREND IS PARTLY AN INSPECTION TREND.
     2021 and 2023 tie as the largest cohorts (9 of 43 each). A
     recently-inspected building looks like a recently-opened
     building, because the bound is the inspection.

  4  THE FRAME IS INCOMPLETE AND WE ARE NOT ESTIMATING A POPULATION.
     Amazon runs roughly 700-900 US delivery stations. This panel has
     43 rows in 10 metros. Any model fitted on it is a DEMONSTRATION
     ON A STATED FRAME, not an estimate of Amazon's siting behaviour.
     It was fitted, and it failed -- see ../STATUS.md.
```

Section 12 lists the defects we know about in the delivered file, marking
each one fixed or still open as of the 2026-09-13 rebuild.

---

## 1. What the file actually contains

| | |
|---|---|
| Path | `data/external/facility_panel/facilities.csv` |
| Rows | 43 |
| Distinct buildings | **43** — one row per building, since the 2026-09-13 rebuild |
| Operator | Amazon only |
| `facility_type` | `DS` on every row |
| Year range | 2015-2025 |
| `open_quarter` | populated on **24 of 43** from a real source month; blank on the rest |
| Closures | 1 (`DS-018`, Chicago 60608, opened 2015, closed 2021Q1) |
| Metros | 10 pilot metros; 8 fitting, 2 held out |
| Date semantics | "operating by", an **upper bound** |
| Validator | `ingest.external --check` exits 0 |

> **Rebuilt 2026-09-13.** An earlier cut of this file held 49 rows describing
> only 44 buildings, and carried an inverted `confidence` column. Both are
> fixed; the file is now one row per building and `confidence` runs the right
> way round (see Sec. 12). If you are reading a quote of "49 rows" or "44
> distinct buildings" anywhere in this repository, it is stale — the figure
> is 43 and 43.

Two upstream working files sit outside the repository and are the audit
trail for it:

| File | What it is |
|---|---|
| `MSBA_Project/DS_PANEL.csv` | 64 candidate delivery stations, 49 dated |
| `data/external/facility_panel/national_facilities.csv` | the national panel: 104 rows, 100 buildings after the edit of Sec. 12.7; see Sec. 16.3 |
| `MSBA_Project/DATES_FOUND.csv` | the 35-facility manual dating pass |
| `MSBA_Project/OSHA_CLASSIFIED.csv` | 82 OSHA addresses with a facility type |
| `data/interim/osha_amazon.csv` | all 474 national Amazon buildings |

`DS_PANEL.csv` carries 64 candidates; 15 of them never got a date and were
dropped rather than guessed. That is where 64 becomes 49. Deduplicating the
49 down to one row per building (Sec. 12.1) is where 49 becomes **43**.

---

## 2. Why this was hard, in one picture

The thing we need is a *panel*: for each building, a location and a date.
Plenty of sources give you one or the other. Almost nothing public gives you
both, for delivery stations, uniformly across the country.

```
                     LOCATION?      DATE?     UNIFORM?
  hiring.amazon.com     no           no          -       FAILED
  Google Maps          yes           no*         no      FAILED
  LLM web search        no          yes*         no      FAILED
  MWPVL census         yes          yes          no      FAILED
  ------------------------------------------------------------
  OSHA bulk extract    yes        bound          YES     WORKED
  LLM classification    -            -            -      WORKED
                       (adds facility TYPE to an OSHA address)

  * = unverifiable, which for our purposes is the same as "no"
```

"Uniform" is the column that decides it. A source that covers Chicago well
and Boise not at all does not just have gaps — it makes the gaps look like
an absence of facilities, which is exactly the thing a hazard model would
happily fit a coefficient to.

---

## 3. The five failures

Failures are recorded because each one rules out a method a reviewer would
otherwise ask "why didn't you just...?" about.

### 3.1 FAILED - `hiring.amazon.com`

**The idea.** Amazon's hourly-jobs site lists postings by building, and the
job title names the building type ("Delivery Station Warehouse Associate").
Scrape the site, get the network.

**Why it failed.** Delivery stations are staffed largely by *Delivery Service
Partners* — third-party contractors who employ the drivers. Those drivers are
not Amazon employees and are not hired through Amazon's hourly site. A
50-mile radius search around Chicago returned **7 jobs, all of them at
fulfilment or sortation sites, and none at a delivery station.**

**The lesson.** Amazon's own hiring surface is biased against exactly the
node type we care about, and for a structural reason that will not change.

> *Concretely:* if you want to know where a DSP-staffed delivery station is,
> the people who advertise its address are the DSPs, not Amazon. That
> observation later rescued several dates — see Sec. 5.3.

### 3.2 FAILED - dating by the oldest Google Maps review

**The idea.** A business's oldest review is a lower bound on when it opened.
Sort the reviews by date, read the oldest, take the year.

**Why it failed.** Two reasons, and the second is the fatal one.

- *It does not scale.* A busy delivery station carries 500+ reviews, and
  Google does not expose a "sort by oldest" that survives pagination. At a
  few minutes per site, 200 sites is a week of clicking.
- *It is not verifiable.* Google **merges listings for successive tenants at
  the same address.** A unit that was a freight forwarder until 2019 and an
  Amazon delivery station after it can carry one continuous review history.
  The oldest review is then evidence about the *previous* occupant, and
  nothing on the page tells you so.

**The lesson.** A method whose error mode is silent and undetectable is worse
than a method that fails loudly, even if it is more accurate on average.

### 3.3 FAILED - asking a language model to search the web for dates

**The idea.** Ask a model with web search "when did Amazon delivery station
X open?" for each facility.

**Why it failed.** Roughly **60 queries produced 4 dates, of which one was a
genuine opening date**; the rest were announcements, lease signings or
construction milestones.

Worse, an earlier attempt at the same thing **fabricated 33 of 35 dates.**
Every fabricated row cited the same URL, which did not support any of them.
Two independent checks caught it:

```
  CHECK 1 - a known answer planted in the list
     Chicago 60628 (Pullman) opened Oct 2020. A chicago.gov press
     release says so. The model returned 2024 Q3.

  CHECK 2 - a second source on the same facility
     MWPVL's own record for the Sumner WA site contradicted the
     date the model returned.
```

**The lesson, and it is the most transferable one in this document.**
The failure was not "the model was wrong sometimes". It was that the output
was *uniformly plausible*: 35 rows, every one with a year, a quarter and a
URL, no hedging, no gaps. A dataset with no missing values, produced by a
process that should have produced many, is evidence of fabrication rather
than of diligence.

**Never send an LLM to find a date without giving it page access and
requiring a quotable sentence.** The redo that produced `DATES_FOUND.csv`
did exactly that, and it returned **15 of 35 rows with no date at all** —
which is what an honest pass looks like.

### 3.4 FAILED - MWPVL International

MWPVL is the standard public census of Amazon's network and the obvious
place to start.

**Why it failed.** Its public "Amazon.com Distribution Network Strategy"
page states in its own introduction:

> *"This article documents the global Amazon.com distribution network as at
> April, 2012."*

It is a **snapshot of April 2012**, listing 32 North American fulfilment
centres. Delivery stations barely existed as a node type then — Amazon's
last-mile build-out is essentially a 2018-2023 phenomenon.

Measured against our own candidate list: of **202** candidate facilities
harvested from OpenStreetMap, exactly **4** appear in MWPVL's 2012 table
(PHX3, PHX6, PHX7, BFI1), and **all four are fulfilment centres.** Zero
delivery stations.

**But it was not useless.** Because MWPVL states a real opening month for
each 2012 facility, it is the only independent yardstick we have for the
OSHA bound. That check is in Sec. 6.2, and it is the most important piece
of validation in this document.

---

## 4. WORKED - the US DOL OSHA bulk inspection extract

### 4.1 What it is

The US Department of Labor publishes every OSHA inspection ever recorded, as
a bulk download, at `enforcedata.dol.gov` (also reachable through the DOL v4
API). It is free, requires no key, and is the same file for everybody.

The archive is ~1.4 GB compressed and arrives as roughly 105 CSV chunks,
**each repeating the header**. A reader that opens only the largest member
returns about 1% of the data and looks like a successful run. The code in
`src/siting_atlas/ingest/osha.py` iterates every member for that reason.

### 4.2 What one run produces

Measured on 2026-09-13 (`logs/run-20260913-121639-1ff8/events.jsonl`):

```
  5,200,011  inspections scanned
        951  Amazon inspection rows kept        (0.018%)
        143  namesake rows rejected             (see Sec. 9)
        474  distinct BUILDINGS after linkage   (was 516; see Sec. 12.5)
         43  states represented
         93  buildings inside the ten pilot metros
```

> **Re-measured 2026-09-13 after the matcher rewrite.** The collapse figure
> was 516 under the old exact-string matcher and is **474** under the new
> one, which is the same input judged by a matcher that can see address
> components. The pilot-metro count is re-derived here by joining `site_zip`
> to the pilot CBSA crosswalk; on the same method the old file gives 102,
> not the 88 this table previously showed, so that 88 came from some other
> route and should not be quoted.

### 4.3 Why it succeeded where the other four failed

One word: **uniform**. Federal and state-plan OSHA use one schema in all 50
states. Whether a facility is in Seattle or Nampa does not change whether it
can appear. Every other source we tried was mediated by someone choosing to
write about the facility — a reporter, a planning clerk, a directory editor —
and that choice correlates with metro size, local news health, and how
controversial the building was.

That does *not* make the OSHA sample unbiased. It makes it biased in a way
that is **stable and describable**, which is the difference between a
limitation you can state and a limitation you cannot.

### 4.4 One record per building, not one per inspection

A busy site is inspected repeatedly. We keep the **earliest** inspection per
address, because the earliest is the tightest "operating by" bound; later
ones add nothing.

Collapsing needs care, because OSHA writes the same address several ways.
`normalise_address()` lower-cases, strips punctuation and folds street
suffixes and directionals to one spelling:

```
  "2801 S. Western Avenue"  -\
                              >--  2801 S WESTERN AVE   -> one site
  "2801 S. Western Ave."    -/
```

Without that fold, one Chicago building became two sites and the earlier
date was lost. **This normaliser is also the source of a defect** — it does
not collapse far enough, and five pairs of rows in the delivered file are
the same building twice. See Sec. 11.1.

---

## 5. WORKED - asking a language model what kind of building it is

### 5.1 Why the same tool failed at dating and succeeded at typing

This is worth sitting with, because the difference is not about the model.

```
  ASKED:  "When did the Amazon facility in Kent WA open?"
  GIVEN:  a city name.
  TRUTH:  exists in maybe one local news story, maybe nowhere.
  RESULT: fabrication, because the model has nothing to ground on.

  ASKED:  "What kind of facility is 20202 84th Ave S, Kent WA 98032?"
  GIVEN:  a real street address, from a federal record.
  TRUTH:  leasing listings, DSP directories, planning agendas, job
          adverts and square-footage figures all name the address.
  RESULT: a verifiable answer with a quotable sentence.
```

The address is the difference. A federal citation hands the model a key that
the open web is actually indexed on. "When did it open" has no such key.

### 5.2 The two rounds

| Round | Sent | Resolved | Left |
|---|---|---|---|
| 1 (`GEMINI_PROMPT_4.txt`) | 82 | 53 | 29 |
| 2 (`GEMINI_PROMPT_5.txt`) | 29 | 23 | **6** |

Final types over the 82 addresses:

```
  FC   30   fulfilment centre
  DS   27   delivery station          <- what the panel needs
  SC   12   sortation centre
  OTHER 5   office, data centre, pharmacy
  FRESH 2   Amazon Fresh / grocery
  ----------
  ?     6   unresolved after two rounds, left blank
```

Six unresolved is a feature. The prompt said, in as many words, *"If you
cannot tell what kind it is, write UNKNOWN. Do not guess. Guessing the kind
is worse than not knowing, because it decides whether the site counts at
all in my model."*

### 5.3 What made round two work

Round two was the leftovers, so a normal search had already failed. The
prompt named specific techniques rather than asking the model to try harder:

- search the **address alone in quotes**, with no mention of Amazon — a
  leasing listing or a trucking directory often names it;
- search the address plus **"DSP"** — the contractors publish the address of
  the station they load at (Sec. 3.1, turned into an asset);
- search the address plus **"square feet"** — size settles it: under 250,000
  is a delivery station, over 600,000 is a fulfilment centre;
- search the address on **hiring.amazon.com**, where the *job title* names
  the building type even when no job is posted for the DSP drivers.

Twenty-three of 29 came back. The size heuristic did most of the work.

---

## 6. THE CENTRAL CAVEAT: `open_date` is not an opening date

### 6.1 What the column means

In the OSHA schema, `open_date` is **the date OSHA opened the inspection
case**. It has nothing to do with the building.

```
     BUILDING OPENS                        OSHA OPENS A CASE
           |                                       |
           v                                       v
   -----[ ??? ]---------------------------------[ X ]-------->
                                                  ^
                                   this is the only date we observe

   What it proves:  the building EXISTED AND WAS OPERATING at X.
   What it does not prove:  anything at all about where ??? is.
```

Treating `open_date` as an opening date would **fabricate an event** for
every row. Instead it is used only as an **upper bound**, and the hazard
model consumes it as **interval-censored** data: the opening happened
somewhere in `(panel start, X]`, not at `X`.

This is the single most important caveat in the dataset. It was caught in
review, not in design, and the whole pipeline is built around it now:
`osha.py` names the output column `operating_by`, not `open_date`.

### 6.2 How loose is the bound? Measured, not asserted

MWPVL's 2012 snapshot states a real opening month for each facility it
lists. Five of those addresses also appear in the OSHA extract, which gives
five cases where both the true opening and our bound are known.

| Facility | True opening | First OSHA inspection | Lag |
|---|---|---|---|
| BFI1 Sumner WA | Jun 2011 | Oct 2011 | **4 mo** |
| PHX4 Goodyear AZ | Jun 2008 | Jul 2009 | **13 mo** |
| PHX6 Phoenix AZ | Oct 2010 | Jul 2015 | **57 mo** |
| PHX7 Phoenix AZ | Sep 2011 | Jun 2017 | **69 mo** |
| PHL1 New Castle DE | Nov 1997 | Aug 2026 | **345 mo** |

**The bound held in 5 cases out of 5.** It was never violated — no OSHA
inspection predates the opening, which is what a valid upper bound requires.

**And it is extremely loose.** The median lag is 57 months. PHL1 — Amazon's
second US distribution centre, open since 1997 — was first inspected in
2026, twenty-eight years later.

Say plainly what that means:

> The upper bound is *correct* and frequently *uninformative*. For a hazard
> model that consumes an interval `(start, X]`, a 28-year interval
> contributes almost no information about timing. The panel therefore
> supports statements about *which* ZIPs got a facility far better than
> statements about *when*.

Two mitigating points, neither of which rescues the timing claim:

1. These five are all **fulfilment centres opened 2008-2011**, when OSHA's
   Amazon inspection activity was near zero. The modern delivery-station
   cohort (2019-2024) sits in a period of intense OSHA attention to Amazon,
   so lags there are probably much shorter.
2. Where a genuine opening date was found by hand (Sec. 7), it replaces the
   bound. 16 of the 43 rows are dated that way.

Point 1 is a conjecture. It is exactly the kind of claim this project's own
standard says to measure rather than assert, and it is **not measured** — we
have no modern delivery station whose true opening date and OSHA bound are
both known. Flagged as an open ticket.

---

## 7. Where the other 16 dates came from

27 of the 43 dates are OSHA bounds. The other 16 come from a hand-research
pass over 35 OpenStreetMap-located candidates, recorded in `DATES_FOUND.csv`
with a URL and a quotable sentence for every claim. Those 16 are the rows
whose `site_address` reads literally `(osm)`, because the OSM candidate list
gave a ZIP and a city but never a street address.

That pass is not uniformly strong, and the file says so:

```
  35 facilities researched
  |
  +-- 15  no date found at all          -> dropped, not guessed
  +-- 20  dated
       |
       +--  8  confidence HIGH
       +--  4  confidence MEDIUM
       +--  8  confidence LOW
       |
       +-- 12 of the 20 are themselves "BY <year>" upper bounds,
              not openings -- the same censoring problem again
```

Only about six rows in the whole pass are genuine, well-sourced openings:
the Pullman Chicago station (chicago.gov press release, Oct 2020), the
Skokie station (Village of Skokie newsletter, Oct 2019), Gage Park
(Guardian/Consumer Reports, 2020), West Chicago (CBS Chicago, Sep 2020),
northeast Mesa (AZ Tech Council, 2021) and the DCH1 Chicago site.

The eight LOW-confidence rows lean on evidence such as an Indeed review by a
DSP driver, a carrier registration, or a chamber-of-commerce directory
listing. Those are real documents, but they date *a contractor's activity
near the site*, not the site. They are kept because dropping them would drop
whole metros, and flagged here because they should not be treated as equal
to a press release.

One row was dropped for exactly this reason: `AMZ-DUR3` (Milpitas CA) had a
2020 date from a DSP office address and was excluded, leaving that candidate
undated. The same standard was **not** applied consistently — `AMZ-DXC5`
(Fremont, chamber directory) and `AMZ-DCX5` (San Jose, Cal/OSHA permit, and
flagged in its own evidence as a possible fulfilment centre) both survived.
That inconsistency is a defect; see Sec. 11.3.

---

## 8. Selection bias, quantified rather than hedged

"There may be some selection bias" is not a limitation, it is a shrug. Here
is the size of it.

### 8.1 OSHA inspects the dangerous, not the typical

OSHA opens cases in response to injuries, complaints, referrals and targeted
programmes. That is a sampling frame weighted by hazard:

- **Fulfilment centres** are 600,000-1,200,000 sq ft, heavily automated,
  employ thousands of Amazon employees directly, and have been the subject
  of national OSHA emphasis programmes. They get inspected a lot.
- **Delivery stations** are 100,000-250,000 sq ft, and most of the people on
  site are DSP contractor drivers rather than Amazon employees. Fewer
  inspections, and some of the ones that happen are filed against the DSP.

Across all 474 national buildings, where the establishment name is explicit
about the building type (re-counted after the matcher rewrite, Sec. 12.5):

```
  FC       81   |################################################
  DS       19   |###########
  SC        6   |####
  AIR       4   |##
  GROCERY   2   |#
  (silent) 362
```

**Fulfilment centres outnumber delivery stations 4.4 to 1** in the source,
in a network where delivery stations outnumber fulfilment centres by
something like 5 to 1 in reality. The source is off by roughly an order of
magnitude *in the direction that hurts us most*.

Illinois on its own: **23 Amazon inspections, at 18 distinct addresses, of
which 3 name a delivery-station entity.**

### 8.2 It distorts the metro distribution too

This is the bias that will actually mislead a reader, because it looks like
a finding.

| Metro | OSHA addresses | Dated DS in panel |
|---|---|---|
| Seattle | 35 | 14 |
| New York | 10 | 6 |
| Chicago | 9 | 9 |
| Bay Area | 8 | 8 |
| Denver | 5 | 6 |
| Austin | 5 | 2 |
| Nashville | 5 | **0** |
| Miami | 2 | 2 |
| Phoenix (held out) | 6 | 1 |
| Boise (held out) | 3 | 1 |

Seattle has **17x** the OSHA coverage of Miami. Amazon does not have 17x the
delivery stations in Seattle that it has in Miami. What Seattle has is
Washington State's own state-plan OSHA programme (DOSH), which is unusually
active, and Amazon's home region. **Seattle's 14 stations against Miami's 2
is a fact about inspection activity, not about Amazon's footprint.**

Any model fitted on this panel will see more openings in Seattle and will be
tempted to attribute that to Seattle's covariates. It is an artefact.

Note also **Nashville: a fitting metro with zero delivery stations in the
panel.** Its 5 OSHA addresses are all fulfilment centres. So of the eight
fitting metros, only seven contribute any events.

### 8.3 And it contaminates the time trend

Because the date is the inspection, **a recently-inspected building looks
like a recently-opened building.**

```
  year of "opening" in the panel        OSHA attention to Amazon
  2015  ##                              low
  2017  ##                              low
  2018  #                               rising
  2019  ######                          rising
  2020  ########                        COVID complaints surge
  2021  #########                       national emphasis programme
  2022  ########                        high
  2023  ##########  <- largest          high
  2024  #                               (extract ends mid-2026)
  2025  ##
```

2023 being the modal year is **probably an inspection fact rather than a
siting fact.** Do not report "Amazon's build-out peaked in 2023" from this
panel. The right statement is that our *observation* of the build-out peaks
in 2023.

---

## 9. False positives: 143 rows that were not Amazon

The Amazon is a river, so plenty of unrelated firms are named after it. A
bare substring match on "amazon" swept in:

- a Hawaii construction company,
- a Nevada masonry business,
- tree surgeons,
- a North Carolina textile division.

None of them are warehouses, and all of them would have entered the panel as
Amazon facilities.

`is_amazon_retailer()` applies three tests in order:

```
  1. explicit trade name wins
     "Amazon Logistics", "Amazon.Com Services Llc"  -> KEEP
  2. an obvious other trade excludes
     construction | masonry | tree | textile | ...  -> DROP
  3. anything left is admitted only on a warehousing
     or courier NAICS (493, 492, 454)               -> JUDGEMENT
```

Rule 3 is the judgement call: it keeps a bare "AMAZON" row sitting in NAICS
493110 (general warehousing) and drops the ones that are not.

**Reconciling the two numbers, because they are easy to confuse:**

```
  before the filter    1,094 inspection rows  ->  577 buildings
  after the filter       951 inspection rows  ->  474 buildings
  ------------------------------------------------------------
  removed                143 ROWS             ->  103 BUILDINGS
```

An earlier draft of this work reported 625 addresses, and a later one 516.
**The current figure is 474**, and it changed because the matcher changed,
not because the input did — see Sec. 12.5. The 143 that gets quoted is the
number of rejected *rows*, not buildings; the same namesake firm appears in
several inspections.

> **A stale figure lives in the source.** The docstring in
> `src/siting_atlas/ingest/osha.py` says "about 170 of 625 addresses". Both
> halves are wrong — it is 143 rows, or 109 addresses. The docstring predates
> the run that produced the current numbers.

---

## 10. Classification caught three would-be false delivery stations

A false *positive* delivery station is more damaging than a missing one. If
we mark a ZIP as served when it was not, the hazard model sees a ZIP that
"already has one" and stops treating it as at-risk — a false zero, and false
zeros bias a hazard model in one consistent direction.

The LLM classification caught three that a code-prefix or an
address-only rule would have admitted:

| Address | Would have been | Actually |
|---|---|---|
| 3745 Bayshore Blvd, Brisbane CA | delivery station | Amazon Pharmacy |
| 11710 118th Ave, Kirkland WA | delivery station | corporate office |
| 990 Beecher St, San Leandro CA | delivery station | Amazon Fresh grocery |

In total **7 of the 82 classified addresses are not logistics buildings at
all** — 5 `OTHER` and 2 `FRESH`. The other four are Amazon's Seattle
headquarters at 2201 Westlake Ave, an Eastlake Ave office, a Hayward site
and the Amazon Fresh at 76 S Lander St in Seattle.

*(The specific labels "pharmacy", "corporate office" and "grocery" come from
the classification pass itself; `OSHA_CLASSIFIED.csv` retains only the
category letter, so the finer description is not independently reproducible
from the stored artefacts.)*

---

## 11. Facility codes are unreliable, for location AND for type

### 11.1 The airport-code trap

**Amazon names buildings after the nearest airport, not the city they sit
in.** This is the single most common way to get a facility's geography
wrong.

```
  OAK3  reads as Oakland   ->  is in Patterson, CA
                               Stanislaus County, ~70 mi inland
  OAK4  reads as Oakland   ->  is in Tracy, CA
                               San Joaquin County, not the Bay Area
  SMF5  reads as Sacramento->  is in Vacaville, CA
                               Solano County, its own MSA
```

None of those three is in the San Francisco Bay Area CBSA. Verified against
the OMB 2023 delineation, not by eye. **Always resolve the ZIP through the
crosswalk; never trust the building code.**

### 11.2 The same trap ruins the facility type

Our original `facility_type` came from a rule of the form *"code starts with
D, therefore delivery station"*. Applied to 202 OSM candidates it produced
76 `DS` and 126 `FC`.

That rule is a **tautology, not a check.** It reads the type off the name and
then reports the name as evidence for the type. It cannot fail, which is
precisely why it tells you nothing.

`DEN5` is the clean counter-example: it starts with `D`, so the rule calls it
a delivery station, and it is a **sortation centre** — because `DEN` is
Denver's *airport* code and the `D` is doing no work at all.

Compared against independent evidence, at least five D-prefixed codes are
mistyped this way. Two are firmly established:

| Code | Prefix rule says | Evidence says | Source |
|---|---|---|---|
| DEN5 | DS | sortation centre | OSHA, 19799 E 36th Dr, Aurora CO |
| DWA6 | DS | fulfilment centre | Sierra Industries, contractor page |

The others (DEN3, DWA9, DPX6) are contradicted by OSHA records at the same
ZIP but matched at ZIP rather than at address, so treat them as strong
suspicion rather than proof.

### 11.3 A better classifier: the operating entity

Amazon files OSHA paperwork under different corporate entities depending on
which arm runs the building, and the establishment name carries it:

```
  "Amazon Logistics, Inc."            -> last-mile arm   -> DELIVERY STATION
  "Amazon Fulfillment Services, Inc." -> warehouse arm   -> FULFILMENT CENTRE
  "Amazon Delivery Station - DLN8"    -> says it outright
  "Amazon.Com.Dedc LLC"               -> holding entity  -> tells you nothing
```

This is real evidence rather than a restatement of the name, because the
entity is a legal fact recorded by a third party. It is what
`classify()` in `osha.py` uses, and it is what confirmed the Chicago DCH1
site as a delivery station after the code-prefix rule had called it a
sortation centre.

It is *silent* far more often than it speaks: 362 of the 474 national
buildings carry a name that identifies no type. Silence is returned as `""`,
never as a guess.

### 11.4 Two facility codes hidden inside the street-address field

An inspector typed the building's internal code into OSHA's street-address
box:

```
  site_address = "315 SHUKSAN WAY DWS4"        Everett WA  -> DWS4
  site_address = "1901 140TH AVE E BFI7"       Sumner WA   -> BFI7
```

Small, and genuinely useful: Sumner has four Amazon buildings on two
adjacent streets (1800, 1901, 2201 140th Ave E and 3711 142nd Ave E), and
the stray `BFI7` is what separated 1901 (a fulfilment centre) from 2201 (a
delivery station).

**The same quirk also breaks the deduplication**, which is Sec. 12.1.

---

## 12. Known defects in the delivered file

Listed so that the first person to use the file knows, rather than
rediscovering them. Each carries its status as of the 2026-09-13 rebuild.

```
  12.1  duplicate rows              FIXED     49 rows -> 43, one per building
  12.2  two rows are not a DS       HALF      Kent WA gone; San Jose remains
  12.3  provenance columns wrong    HALF      inversion fixed; labels loose
  12.4  a closed facility as open   FIXED     DS-018 carries close_year 2021
  12.5  normalise_address itself    FIXED     replaced by a measured matcher
  12.6  national_facilities dupes   FIXED     resolved by a declared edit;
                                              104 rows -> 100 buildings
  12.7  dates later than the        FIXED     4 national rows excluded;
        proven operating date                 1 pilot row reported only
```

### 12.5 The matcher was replaced, and measured  `FIXED`

The generator is now fixed, not just the artefact. `normalise_address()` and
the second, divergent copy of it that lived in `scripts/osha_amazon.py` are
both gone. In their place:

| Module | Job |
|---|---|
| `common/address_tables.py` | the standardisation vocabulary, one copy |
| `common/address.py` | parse into fixed slots (Winkler RR99-04 Sec. 2.3) |
| `common/linkage.py` | Jaro-Winkler + the Fellegi-Sunter 3-way rule, eq. (4) |
| `common/linkage_group.py` | grouping, with the transitive closure CHECKED |
| `ingest/address_audit.py` | the measurements below, reproducible |

Re-running `python -m siting_atlas.ingest.osha` on the real 1.4 GB DOL
archive now gives **951 Amazon inspections -> 474 distinct buildings**, where
the old code gave 516 addresses. Measured on that run:

```
  match rate          611 distinct address strings -> 475 buildings (22.3%)
  blocking recall     1664 of 1664 true matches, comparing 7.3% of pairs
  false matches       0 of 101 non-trivial merge groups, all reviewed
  review band         18 distinct pairs, all 18 judged TRUE matches
  ambiguous           5 records (N/S Chrisman, Gateway Commerce Center)
```

The pairs this section used to quote as broken now collapse, and the pair a
naive fix would have broken does not:

```
  "315 SHUKSAN WAY DWS4"    == "315 SHUKSAN WAY"        MERGED
  "4616-6 HOWARD LANE"      == "4616-6 W HOWARD LANE"   MERGED
  "1555 N CHRISMAN RD"      vs "1555 S CHRISMAN RD"     KEPT APART
```

Regression tests for every one of these are in `tests/unit/test_address.py`
and `tests/unit/test_linkage.py`.

### 12.7 Four dates are later than the date OSHA proves the building operated  `FIXED`

> **Added 2026-09-13, evening.** This section and the revision to 12.6 below
> replace the earlier "three duplicate pairs, unresolved" entry. Full
> reasoning, alternatives rejected and reversibility record:
> [`CLEANING_CHANGELOG.md`](CLEANING_CHANGELOG.md) Fix 5.

An OSHA inspection is conducted at an establishment that exists and is
operating, so `operating_by` is an **upper bound** on the opening — the whole
argument of Sec. 6 above. That makes the following a declared edit rather than
a preference, checked mechanically in `src/siting_atlas/warehouse/edits.py`:

```
  E_operating_by :  quarter_start(open_q_index) <= osha_operating_by
```

Four records in `national_facilities.csv` fail it, each claiming an opening
strictly after the date the building was demonstrably already running:

| Record | Claims | OSHA proves operating by | Late by |
|---|---|---|---|
| NAT-0011 Hawthorne CA | 2020Q2 | 2017-12-29 (act. 342854213) | 10 quarters |
| NAT-0026 Tracy CA | 2026Q3 | 2025-03-17 (act. 348129149) | 6 quarters |
| NAT-0036 Temple Terrace FL | 2024Q4 | 2024-04-17 (act. 347417297) | 2 quarters |
| NAT-0079 Portland OR | 2018Q3 | 2017-12-21 (act. 342848355) | 3 quarters |

Three of the four are one half of a duplicate pair (12.6), so excluding them
loses nothing — the twin carries the surviving date. NAT-0036 has no twin, so
excluding it costs a building; Tampa keeps four other stations, so it costs no
metro.

**And one row of the pilot file fails it too.** `DS-032` (Austin TX, 4616-6
Howard Lane) claims 2019Q3 against an inspection on 2019-03-15. It is
**reported and not excluded**, because removing it would take Austin's only
building out of the fitted frame and move the published ZCTA, cell and event
counts. That is a decision for the inspirator; the finding is pinned by
`tests/unit/test_edits.py`.

**Read this before quoting the edit as validation.** It is *not* an independent
source confirming the panel. Every one of the 104 national rows matches an OSHA
building and **100 of them carry exactly the quarter of that building's
earliest inspection** — the file was built from this extract (Sec. 16.3), so
`source_type=permit` on all 104 is the same mislabelling 12.3 admits for the
pilot. The edit is an internal consistency check that finds four derivation
errors. What makes those four errors rather than research is that all four
depart from the OSHA quarter in the one direction the source forbids; genuine
research would scatter, and mostly fall below an upper bound.

The surviving dates are therefore still OSHA upper bounds with the 4-345 month
lag measured in Sec. 6.2. Promoting the national panel buys **more** bounds,
not better ones.

### 12.6 `national_facilities.csv` held three duplicate buildings  `FIXED`

Running the new matcher over the delivered panels found that
`facilities.csv` is clean - 43 rows, 43 buildings, the hand deduplication
holds - but **`national_facilities.csv` has 104 rows describing only 101
buildings**:

| Rows | Building |
|---|---|
| NAT-0011 / NAT-0012 | 2815 W El Segundo Blvd, Hawthorne / "Hollyglen" 90250 |
| NAT-0025 / NAT-0026 | 1500 E Grant Line Rd / "Grantline" Rd, Tracy 95304 |
| NAT-0078 / NAT-0079 | 3610 NW Saint Helens Rd / "St Helens" Rd, Portland 97210 |

All three are one building spelled two ways, and all three are exactly the
class of defect the old matcher could not see. The file has not been edited on
disk, because correcting curated data is a separate decision from fixing the
code that audits it.

> **Resolved 2026-09-13, evening.** The three pairs are *contradicting*
> records, not duplicates — they disagree about the opening date by 10, 6 and
> 3 quarters — and the Fellegi & Holt Sec. 7 reliability weights tie on all
> three, because all six rows are `source_type=permit`. What separates them is
> the edit in 12.7 above, which falsifies NAT-0011, NAT-0026 and NAT-0079
> outright. `warehouse/national.py` therefore loads the file, and **any count
> of 104 national stations is 100**: 101 buildings less NAT-0036, which the
> same edit falsifies and which has no twin to fall back on.

`tests/unit/test_linkage.py::test_delivered_panel_holds_one_row_per_building`
enforces the clean result on `facilities.csv` so it cannot regress.

### 12.1 Five rows were the same building as another row  `FIXED`

`normalise_address()` folds street suffixes, but not stray suffixes, stray
directionals or the inspector's facility code. Run on the actual pairs:

```
  "4616-6 HOWARD LANE"        -> 4616 6 HOWARD LN
  "4616-6 WEST HOWARD LANE"   -> 4616 6 W HOWARD LN      NOT collapsed
  "315 SHUKSAN WAY DWS4"      -> 315 SHUKSAN WAY DWS4
  "315 SHUKSAN WAY"           -> 315 SHUKSAN WAY         NOT collapsed
  "5509 MILITARY RD."         -> 5509 MILITARY RD
  "5509 MILITARY RD E,"       -> 5509 MILITARY RD E      NOT collapsed
```

Plus two cases where an OSHA row and a hand-researched OSM row describe the
same building from two directions.

| Rows | Building | Effect |
|---|---|---|
| DS-001 / DS-002 | 4616-6 (W) Howard Ln, Austin | Austin 2 -> 1 |
| DS-004 / DS-005 | 2801 S Western Ave, Chicago (DCH1) | Chicago 9 -> 8 |
| DS-028 / DS-029 | 44109 Pacific Commons, Fremont | Bay Area 8 -> 7 |
| DS-037 / DS-038 | 315 Shuksan Way, Everett | Seattle 14 -> 13 |
| DS-044 / DS-045 | 5509 Military Rd, Puyallup | Seattle 13 -> 12 |

Those 49 rows described at most 44 distinct buildings. **The file has since
been rebuilt by hand to one row per building: 43 rows, 43 distinct
`(state, zip, site_address)` triples, no duplicate pairs left.** Corrected
coverage is in Sec. 13. What has *not* changed is the function — see 12.5
above.

### 12.2 Two rows are probably not delivery stations  `HALF FIXED`

`DS-041` (Kent WA 98032, 2015, `AMZ-DWA6`) is **gone** from the rebuilt file.
The two Kent rows that remain are `DS-035` (20202 84th Ave S, 2020) and
`DS-036` (22001 84th Ave S, 2023), neither of which is the fulfilment centre.

The San Jose row **remains**. It is now `DS-008` (95122, 2020), and it is
`AMZ-DCX5` from the Cal/OSHA permit database, whose own evidence line ends
*"Type flagged as possible FC."* One suspected mistype still sets the target.

The original wording, kept for the record:

> - **DS-041, Kent WA 98032, 2015.** This is `DWA6`, and its own evidence
>   line in `DATES_FOUND.csv` reads: *"TYPE CORRECTION: contractor says Kent
>   is a FULFILMENT CENTRE completed 2015, not a delivery station. Does not
>   set the target."* It is nonetheless in a `DS`-only panel.
> - **DS-035, San Jose CA 95122, 2020.** Its evidence line ends *"Type
>   flagged as possible FC."*

`warehouse/facilities.py` only lets `DS` and `SDC` set the target, so a
mistyped `FC` sitting in the file as `DS` enables ZIPs it should not.

### 12.3 The provenance columns are mislabelled  `HALF FIXED`

**The inversion is gone.** `confidence` now runs the right way round:

```
              confidence=high   confidence=medium
  permit            27                 0
  news               0                16
```

The 27 permit-and-OSHA-derived rows — the federal and state records, which
are the strongest evidence in the file — are `high`. The 16 hand-researched
OSM rows are `medium`. **You may now filter on `confidence`.** That sentence
is the reverse of what this section said before 2026-09-13.

What is still loose, and why this is only half fixed:

| Column | What it says | What is true |
|---|---|---|
| `source_type` | `permit` on the 27 OSHA/Cal-OSHA rows | OSHA is an *enforcement* record, not a permit. The label understates how the date was obtained |
| `source_type` | `news` on the 16 researched rows | these are OSM-located and dated from directories, reviews and press; `site_address` literally reads `(osm)` |
| `source_url` | `"see data/collection/results/"` | still not a URL. The real URLs are in `DATES_FOUND.csv` |

So the column you would *filter* on is correct, and the two columns you
would *cite* are not. Do not quote `source_type` or `source_url` in a
write-up without going back to `DATES_FOUND.csv`.

### 12.4 One row records a closed facility as open  `FIXED`

The rebuilt file carries the closure. `DS-018` (Chicago 60608, 2801 S.
Western Ave, the DCH1 site) is `status=closed`, `close_year=2021`,
`close_quarter=1`. It is the panel's only closure, and the only row where
the `enabled` column is ever switched back off.

The original wording, kept for the record:

> `AMZ-DCH1` (Chicago 60608) is marked `status=closed`, `close_year=2021` in
> `DATES_FOUND.csv`, sourced to NLRB cases 13-CA-256021 / 13-CA-259095 and
> Labor Notes. In `facilities.csv` it appears as `status=open` (twice — it
> is also one of the duplicate pairs above).

---

## 13. Coverage, per metro, not averaged away

Averaging coverage hides the thing that matters, which is that some metros
carry the model and some contribute nothing.

Re-derived from the 43-row file on 2026-09-13 by joining `zip` to the
panel's `dim_zcta`, so the metro label is the crosswalk's and not a guess.
Rows and distinct buildings are now equal everywhere, which is what
deduplication means.

```
  Metro                      rows  distinct  with_q  fitting?   note
  ------------------------------------------------------------------------
  Seattle-Tacoma-Bellevue      11      11       9    fit        state-plan
  Chicago-Naperville-Elgin      8       8       2    fit        1 closure
  Denver-Aurora-Lakewood        6       6       1    fit
  New York-Newark-Jersey City   6       6       5    fit        4 of 6 NJ
  San Francisco-Oakland         4       4       3    fit        Bay CBSA 1
  San Jose-Sunnyvale            3       3       0    fit        Bay CBSA 2
  Miami-Fort Lauderdale         2       2       2    fit
  Austin-Round Rock             1       1       1    fit
  Nashville                     0       0       0    fit        NO EVENTS
  ------------------------------------------------------------------------
  fitting total                41      41      23
  ------------------------------------------------------------------------
  Phoenix-Mesa-Chandler         1       1       0    HELD OUT
  Boise City                    1       1       1    HELD OUT
  ------------------------------------------------------------------------
  panel total                  43      43      24
```

`with_q` is the count of rows carrying a real `open_quarter`. It is not
uniform — Seattle has 9 of 11, San Jose and Phoenix have none — so the
quarterly grain is better resolved in some metros than in others. A row
with no quarter is dated to Q1 by convention in `warehouse/facilities.py`,
which is why Q1 is still the largest bucket in the risk set (35% of events)
even though events now land in all four quarters.

The Bay Area is two CBSAs, which is why it appears as two lines. Together it
is 7 buildings, not the 8 the pre-deduplication table showed.

### 13.1 How many usable events that is

The feature panel runs **2018Q1-2025Q4**. A facility already open at the
start of the window is not an event — it is evidence the ZIP was *already*
served, and `warehouse/facilities.py` keeps it as **left-censored** rather
than dropping it. Dropping it would tell the model the ZIP was waiting to be
switched on when it was not.

```
  41  dated buildings in fitting metros    (43 less Phoenix 1, Boise 1)
  -2  open before 2018Q1 (left-censored)   -> 39 usable events
      (Chicago 60608 in 2015, Elizabeth NJ 07201 in 2017)
```

**Exactly 39 events** — the figure is no longer approximate, because rows
and buildings are now the same thing — spread over 8 metros of which one has
none, against a panel of 1,081,312 ZCTA-quarter rows. This is a very small
number of events. It was enough to fit a cloglog hazard with a handful of
parameters and to demonstrate the whole pipeline end to end. It was **not**
enough to support a claim about Amazon's siting policy, and the fit confirms
that rather than merely warning about it: see `../STATUS.md`.

*(The arithmetic changed twice. Before deduplication it read "47 dated rows,
less 5 duplicates, less 3 pre-2018, ~39". It now reads "41 buildings, less 2
pre-2018, 39". The answer is the same 39 by coincidence of the counting, not
because nothing moved: the third pre-2018 row was Kent WA 98032, which was
the misclassified fulfilment centre and has been removed entirely.)*

### 13.2 Fifteen candidates with no date, deliberately dropped

`DS_PANEL.csv` carries 64 candidate delivery stations. Fifteen never got a
date and were left out rather than guessed:

```
  Phoenix   7   Chandler x2, Goodyear, Phoenix x3, Tempe
  Seattle   5   Everett, Frederickson, Lakewood, Maple Valley, Sumner
  Bay Area  3   Dublin, Milpitas, San Jose
```

Phoenix is the instructive case. An official Amazon press release dated
August 2020 announces *multiple* new Phoenix-metro delivery stations, and
areadevelopment.com corroborates it. It is almost certainly the announcement
for several of these seven. **It does not name which cities or which codes**,
so no date was assigned to any of them. Assigning August 2020 to all seven
would have been the single largest fabrication available in this project.

A trap avoided in the same pass, recorded so nobody re-adds it: a search hit
titled *"Amazon Warehouse Slated To Be Closed"* (everettindependent.com,
2022-08-24) refers to Everett, **Massachusetts**, not Everett, Washington.

---

## 14. How the model is allowed to use this

```
  facilities.csv
        |
        v
  warehouse/facilities.py
        |  DS and SDC only        (an FC is a regional node; it
        |                          enables nothing for same-day)
        |  15-mile radius         (standing in for a drive-time
        |                          isochrone until the OD matrix exists)
        |  pre-2018 => left-censored, not an event
        v
  panel.enabled  (BOOLEAN, per ZCTA per quarter)
        |
        v
  models/hazard.py   discrete-time cloglog, interval-censored
```

Three things follow from the provenance and must be respected downstream:

1. **No statement of the form "Amazon opened N stations in year Y."** The
   panel cannot support it (Sec. 8.3).
2. **No population estimate.** The frame is 43 buildings out of a national
   network of several hundred, selected on inspection activity.
3. **Held-out metros stay held out.** Phoenix and Boise have one row each.
   They were chosen as a geographic transfer test before the data arrived,
   and one row each is not a transfer test — it is a coin flip. Report the
   transfer result with that caveat or not at all.

---

## 15. Reproducing this from scratch

Everything below is free, public, and needs no credential.

**Step 1 - get the OSHA bulk extract.**

```bash
# https://enforcedata.dol.gov/views/data_summary.php
# Section: OSHA -> Inspection.  Download the full CSV archive
# (~1.4 GB compressed; ~105 chunked CSVs inside).
# The data dictionary ships alongside it and is worth keeping.
```

**Step 2 - extract the Amazon rows.**

```bash
cd siting-atlas
.venv/bin/python -m siting_atlas.ingest.osha /path/to/inspection.zip
# -> data/interim/osha_amazon.csv
# -> logs/run-<id>/events.jsonl carries the scanned / matched /
#    rejected / collapsed counts
```

Expect: 5,200,011 scanned, 951 Amazon rows, 143 namesake rejections, 516
addresses. Your counts will differ from ours if DOL has published a newer
extract; the *shape* should not.

**Step 3 - restrict to the metros you care about.** Join `site_zip` to the
ZCTA-to-CBSA crosswalk. Do not filter by state, and do not filter by the
facility code (Sec. 11.1). This step took 474 buildings down to 93.

**Step 4 - classify the type.** Take the entity name first
(`classify()` in `osha.py`); it is silent on about 76% of rows. Send the
remainder to a model **with the street address and with web access**, in two
rounds, using the prompts in `MSBA_Project/GEMINI_PROMPT_4.txt` and
`GEMINI_PROMPT_5.txt`. Require a quotable sentence naming the address, and
require `UNKNOWN` as an allowed answer.

**Step 5 - hand-research openings where you can.** For each `DS`, try the
municipal permit portal, the planning-commission agenda, the local business
press. Record the URL and the sentence. Leave the date blank if you cannot
find one.

**Step 6 - validate.**

```bash
.venv/bin/python -m siting_atlas.ingest.external --check
```

**Step 7 - plant a known answer.** Before trusting any automated dating
pass, put a facility whose date you already know into the list and check
that the pass returns it. That is what caught the 33-of-35 fabrication
(Sec. 3.3), and it costs one row.

---

## 16. What would improve this, in priority order

### 16.1 Municipal permit portals - the highest-value gap

This is the only method that ever produced **a date and a facility code
together**, and it did so almost by accident: a Skokie Plan Commission
agenda whose *filename* carried both the case number and the code `DIL7`.
Cross-referenced with the Village of Skokie newsletter — *"in October,
opened a 245,000 sq ft Prime delivery distribution center at 3601 Howard
Street"* — it gave a dated, coded, verifiable opening.

Permit portals are strong exactly where OSHA is weak:

```
  OSHA           inspection date    biased toward dangerous sites
  Permit portal  construction date  biased toward nothing much
                                    -- every building needs a permit
```

The cost is that there is no national portal; it is per-municipality, with
per-municipality software (Accela, Tyler EnerGov, OpenGov, and a long tail
of PDF agendas). Ten metros is maybe 200 jurisdictions. It is a real
project, and it is the one that would turn upper bounds into dates.

### 16.2 NLRB case filings - the best delivery-station skew available

The National Labor Relations Board publishes every unfair-labour-practice
and representation case, and the filings name the employer as, for example:

```
  "Amazon.com Services, LLC d/b/a DCH1"
                                  ^^^^
                    the facility code, in the case caption
```

Two properties make this valuable:

1. **It is coded.** The case caption carries the internal building code,
   which is the join key everything else lacks.
2. **It skews toward delivery stations** — the opposite skew to OSHA. DSP
   labour disputes, driver organising and subcontracting complaints happen
   at last-mile sites. NLRB sees the buildings OSHA misses.

It gave us the DCH1 closure date (cases 13-CA-256021 and 13-CA-259095). The
same censoring caveat applies: a case-filing date is an "operating by"
bound, not an opening. But **combining OSHA and NLRB would give two
independent bounds per site and two independent selection biases, which is
strictly better than one of each.**

### 16.3 The national panel - classification finished, nothing consumes it

> **This file is a moving target.** It grew from 70 rows to 104 during the
> afternoon of 2026-09-13 while this section was being written. The counts
> below are as at **06:39**; re-derive before quoting.

`data/external/facility_panel/national_facilities.csv` holds **104 delivery
stations across 62 metro areas in 29 states**, every one carrying a real
`open_quarter`, spanning 2013-2026. It was built by classifying the national
OSHA extract in batches of 70.

All five batches are now classified — `NATIONAL_CLASSIFIED.csv` holds 319
rows (70, 70, 70, 70, 39) — yielding 106 `DS`, 129 `FC`, 55 `SC`, 5 `FRESH`,
4 `OTHER`, 1 `AIR`. Batch 5 is short at 39 because the address list ran out,
not because it was abandoned.

> **Superseded 2026-09-13, evening.** The sentence below saying *"nothing in
> `src/` reads it"* is no longer true. `src/siting_atlas/warehouse/national.py`
> now loads it under the declared edit of 12.7 and writes
> `experiments/superseded-artefacts/national_panel.json`. Nothing is fitted on it and nothing is
> joined to the panel — the covariate cost named in the third caution below is
> still unpaid, and it was always the larger half of the problem. What changed
> is that the *facilities* are now loadable; the *features* are not built.

**Measured on the promotion**, 2026-09-13, by
`.venv/bin/python -m siting_atlas.warehouse.national`:

```
  104 rows in the file
  -4  falsified by E_operating_by (12.7)
  ---
  100 buildings, 62 CBSAs, 29 states, 2013-2026, every one carrying a
      real open_quarter and none carrying a coordinate

  restricted to the pilot feature panel's window, 2018Q1-2025Q4:
       81 buildings in 52 CBSAs
       -1 opening in 2018 itself, left-censored
      ---
       80 events, 79 independent (CBSA, quarter) episodes
```

Against the five parameters of the fitted pilot specification, and against the
same conventional floor of 10:

```
                              pilot frame       national frame
  independent episodes             28                79
  usable buildings                 38                80
  events per parameter
    effective (episodes)          5.6              15.8
    optimistic (buildings)        7.6              16.0
  meets the floor of 10            no               YES
```

**That is the entire argument for the promotion, and it is a power argument
only.** It does not make the dates better. Every caution below still holds,
and the first one is the binding constraint on anything the larger frame could
be asked to say about *when*.

Three cautions if you pick it up:

- It is the same OSHA source, so it inherits the same injury selection. A
  wider frame is not a less biased one. **And more than that** — 100 of the
  104 dates *are* the OSHA inspection quarter (12.7), so the whole frame is
  upper bounds with a measured 4-345 month lag. Tripling the episode count
  triples the number of censored observations, not the number of known
  opening dates.
- 100 buildings across 62 metros is about 1.6 per metro. That is fewer
  buildings *per metro* than the ten-metro panel, not more — so it buys
  breadth at the cost of ever identifying a within-metro effect.
- Using it needs national ACS/CBP/BLS coverage at ZCTA grain for 62 metros,
  not 10. That is the real cost, it is larger than the collection was, and it
  is still unpaid. `warehouse/national.py` loads the facilities and joins
  nothing.
- Every coordinate is empty here, exactly as in the pilot file: 0 of 104 and
  0 of 43. `resolve_coordinates` falls back to the ZCTA centroid, so a
  15-mile catchment is drawn from a point that can be a couple of miles from
  the building and every distance covariate inherits that error. Not
  geocoded, and not guessed.

### 16.4 Smaller fixes, in order

1. ~~**Deduplicate.**~~ **Done for the file, not for the code.** The panel is
   one row per building. `normalise_address()` is unchanged, so the next
   `ingest.osha` run reintroduces the duplicates upstream. Strengthen it to
   strip a trailing 4-character facility code and to fold leading
   directionals. Sec. 12.5.
2. ~~**Un-invert `confidence`.**~~ **Done.** Sec. 12.3.
3. **Repair the two remaining provenance columns.** `source_type` should
   distinguish an enforcement record from a permit, and `source_url` should
   carry a URL rather than a directory path. Sec. 12.3.
4. **Drop or retype the San Jose row.** `DS-008` is still flagged as a
   possible fulfilment centre. Sec. 12.2.
5. **Measure the bound on a modern delivery station.** Find one whose true
   opening date is documented and whose OSHA bound we hold, and report the
   lag. That is the missing measurement behind the conjecture in Sec. 6.2,
   and it is the single cheapest thing that would tell us how wrong the
   dates are.
6. ~~**Finish national batches 4 and 5.**~~ **Done** — all five are
   classified. What is *not* done is building national covariates so that
   anything can read the result. Sec. 16.3.
7. **Cal/OSHA and the other state-plan databases.** `AMZ-DCX5` came from
   California's DOSH permit database, which is not in the federal extract.
   Twenty-two states run their own plans.

---

## 17. Figure ledger

Every number in this document, and where it was checked. "Verified" means
re-derived from the artefact on 2026-09-13.

| Figure | Value | Source | Status |
|---|---|---|---|
| Inspections scanned | 5,200,011 | `logs/run-20260913-121639-1ff8` | verified |
| Amazon inspection rows | 951 | same | verified |
| Namesake rows rejected | 143 | same | verified |
| Distinct addresses | 516 | `data/interim/osha_amazon.csv` | verified |
| Pre-filter rows / addresses | 1,094 / 625 | `logs/run-20260913-121142-59b7` | verified |
| Addresses removed by filter | 109 | 625 - 516 | verified |
| States represented | 43 | `osha_amazon.csv` | verified |
| Addresses in pilot metros | **88** | ZCTA-CBSA crosswalk join | verified |
| Entity-name types (516) | FC 84 / DS 19 / SC 6 | `osha_amazon.csv` | verified |
| Classification round 1 | 53 of 82 | `OSHA_CLASSIFY_KEY.csv` | verified |
| Classification round 2 | 23 of 29 | `OSHA_ROUND2_KEY.csv` | verified |
| Classification unresolved | 6 | `OSHA_CLASSIFIED.csv` | verified |
| Non-logistics found | **7** (5 OTHER, 2 FRESH) | `OSHA_CLASSIFIED.csv` | verified |
| Illinois inspections | **23**, 18 addresses, 3 DS | re-scan of the archive | verified |
| OSM candidates | 202 | `_candidates_all.csv` | verified |
| Candidates in MWPVL 2012 | 4, all FC | MWPVL PDF vs candidates | verified |
| MWPVL snapshot date | April 2012 | MWPVL PDF, para 2 | verified |
| Bound validation | 5 of 5 hold; 4-345 mo | MWPVL vs `osha_amazon.csv` | verified |
| Panel rows | **43** | `facilities.csv` | re-verified 2026-09-13 |
| Distinct buildings | **43** | distinct `(state, zip, site_address)` | re-verified |
| Year range | 2015-2025 | `ingest.external --check` | re-verified |
| `open_quarter` populated | **24 of 43** | `facilities.csv` | re-verified |
| Closures | **1** (`DS-018`, 2021Q1) | `facilities.csv` | re-verified |
| Dated / undated candidates | 49 / 15 of 64 | `DS_PANEL.csv` | verified (pre-dedup) |
| OSHA-dated / researched | **27 / 16** | `source_type` column | re-verified |
| `confidence` distribution | **27 high / 16 medium** | `facilities.csv` | re-verified |
| Per-metro counts | Sec. 13 table | `zip` joined to `dim_zcta` | re-verified |
| Pre-2018 rows | **2** (2015 Chicago, 2017 Elizabeth) | `facilities.csv` | re-verified |
| Usable events | **39** (41 fitting less 2 pre-2018) | Sec. 13.1 | re-verified |
| National panel, rows | **104** | `national_facilities.csv` | re-verified 06:39 |
| National panel, buildings | **100** | after E_operating_by, Sec. 12.7 | verified evening |
| National panel, CBSAs | **62** | `national_panel.json` | verified evening |
| National rows matched to OSHA | **104 of 104** | `warehouse/edits.py` | verified evening |
| ... carrying the OSHA quarter | **100** | same | verified evening |
| ... falsified by the edit | **4** | `national_panel.json` | verified evening |
| National events, 2018-2025 | **80**, 52 CBSAs, 79 episodes | `national_panel.json` | verified evening |
| National events per parameter | **15.8 .. 16.0** | same, floor 10 | verified evening |
| Pilot rows failing the edit | **1** (`DS-032`) | `tests/unit/test_edits.py` | verified evening |
| Coordinates populated | **0 of 104**, 0 of 43 | both CSVs | verified evening |
| National batches done | **5 of 5** (319 classified) | `NATIONAL_CLASSIFIED.csv` | re-verified |
| `DATES_FOUND` confidence | 8 high / 4 med / 8 low | `DATES_FOUND.csv` | verified |
| Facility codes in address | DWS4, BFI7 | `OSHA_CLASSIFIED.csv` | verified |

**Figures reported to us that the artefacts do NOT support:**

| Claim | Reality |
|---|---|
| "102 addresses in the ten pilot metros" | **88** by the project's own crosswalk. 82 were sent to classification. 102 is not reproducible from any stored artefact. |
| "143 establishments named Amazon that are other companies" | 143 is the count of rejected **rows**; it is **109** distinct addresses. |
| "Illinois: 20 inspections, 1 delivery station" | **23** inspections at 18 addresses, **3** naming a delivery-station entity. The 20/1 figure is a stale docstring in `osha.py`. |
| "Five facilities were wrongly typed" | Two firmly (DEN5, DWA6); three more suspected at ZIP-match resolution only. |
| "Three would-be false delivery stations" | Three are the named examples; **seven** of the 82 are non-logistics. |
| "~43 usable events" | 43 before deduplication; **39** after, and the figure is now exact rather than approximate. |
| "49 rows / 44 distinct buildings" | The pre-2026-09-13 cut. It is **43 / 43**. Any document still quoting 49 or 44 is stale. |
| "the `confidence` column is inverted" | It **was**. It is not any more: 27 permit rows are `high`, 16 news rows are `medium`. |

**Figures we could not verify at all** — no artefact exists, so they are
reported here on the collector's testimony only:

- the hiring.amazon.com 50-mile Chicago search returning 7 jobs;
- "500+ reviews per Google Maps site";
- "~60 queries produced 4 dates, of which one was a real opening";
- "an earlier attempt fabricated 33 of 35 dates" — the 35-facility scope is
  corroborated by `DATES_FOUND.csv` having exactly 35 rows, but the
  fabricated output itself was not retained;
- the specific descriptions "Amazon Pharmacy" (Brisbane), "corporate office"
  (Kirkland) and "Amazon Fresh" (San Leandro) — the stored classification
  keeps only `OTHER` / `FRESH`.

---

## 18. The honest summary

We needed a panel of delivery-station openings. No public source publishes
one. Four attempts to build one from press coverage, map data, a language
model and the standard industry census failed, three of them in ways that
would have produced confident wrong answers rather than obvious gaps.

The fifth attempt works by giving up on the question. Instead of asking
"when did this open", which nothing public answers, we ask "when can we
prove this was operating", which a federal enforcement database answers
uniformly in all 50 states. That converts a missing-data problem into a
censoring problem, and a censoring problem is one that survival analysis was
invented to handle.

What we have is 43 buildings in 10 metros, most of them dated by an upper
bound that is correct and often loose, drawn from a sample selected on
workplace injury. It is enough to run the pipeline end to end on real data
and to demonstrate the method. It is not a census, it is not unbiased, and
the model fitted on it is a demonstration on a stated frame.

**And now we know how that demonstration turned out.** The hazard model was
fitted on this panel and it does not work: it is worse calibrated than a
constant, and its skill goes negative out of time and out of area. The full
numbers are in [`../STATUS.md`](../STATUS.md). That result does not make this
document a failure — it makes it the evidence. A panel this size, dated this
way, cannot identify a siting model, and saying so with a measurement behind
it is worth more than saying so as a caveat.

So there are three deliverables here, not two. The dataset is one. Knowing
exactly what is wrong with it is the second. The demonstration that a dataset
with exactly those things wrong with it cannot answer the question is the
third, and it is the one a reader should remember.

---

## 19. The unlabelled batches: 362 rows, 13 new buildings

Added 2026-09-13, evening, over the first three batches. **Extended
2026-09-14 over all six.** Reproduce with
`PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.batch_candidates`,
which writes `outputs/metrics/batch_candidates.json` and
`data/collection/results/BATCH_DS_CANDIDATES.csv`.

> **UPDATE 2026-09-14 — the programme finished and the ratio got worse.**
> All six batches, measured today:
>
> ```
>   362 rows   135 delivery stations   8 UNKNOWN answers
>              -98  already in national_facilities.csv
>              -24  already in facilities.csv (pilot)
>              ---
>               13  new to both, across 8 CBSAs, 2 of them unplaced
> ```
>
> Batches 4 to 6 contributed 152 rows and 50 delivery stations, of which 46
> were already in the national frame and **four were new**. The per-batch
> yield of new buildings did not improve; the duplication got worse.
>
> **Reproducing the 13 needs a one-line override.**
> `warehouse/batch_candidates.py:54` hardcodes `BATCHES = ("1", "2", "3")`,
> so the module as shipped reads 210 of the 362 rows and writes **nine**
> candidates. `BATCH_DS_CANDIDATES.csv` on disk has nine rows. The constant
> should be a glob; it is recorded as a defect in
> [`CLEANING_CHANGELOG.md`](CLEANING_CHANGELOG.md) Fix 6 and has not been
> changed.
>
> **The rest of §19 below describes the first three batches and the nine.**
> Its reasoning — the date refusal, the duplication mechanism, what the new
> rows buy — carries over unchanged to the thirteen; only the counts move.
> With all thirteen: 113 buildings, 70 CBSAs, first-in-metro share 65.0% to
> 69.0%.

### 19.1 What was asked for, and what the files hold

Sec. 16.3 ends by naming the 362 OSHA buildings the national classification
left unlabelled, and `models/accessibility` names the reason to want them:
its line-haul covariate could not be tested because 65 of the 100 national
decisions have an empty prior network, so for two thirds of the panel the
covariate degenerates to a demand-weighted centrality, which is a population
measure. The prize was facilities **per metro**.

Six batches came back, hand-checked against web evidence — five of 70 and a
sixth of 12, which is what was left:

```
  batch 1   DS 33   FC 23   SC  8   GROCERY 4   OTHER 2
  batch 2   DS 28   FC 28   SC 13   GROCERY 1
  batch 3   DS 24   FC 26   SC 10   GROCERY 1   OTHER 5   UNKNOWN 4
  ------------------------------------------------------------------
            DS 85 of 210        <- the state on 2026-09-13
  batch 4   DS 24   FC 25   SC 19             OTHER 2
  batch 5   DS 21   FC 36   SC  7   GROCERY 1 OTHER 2   UNKNOWN 2   AIR 1
  batch 6   DS  5   FC  2                     OTHER 3   UNKNOWN 2
  ------------------------------------------------------------------
            DS 135 of 362       <- the state on 2026-09-14
```

The eight UNKNOWNs — four in batch 3, two in batch 5, two in batch 6 — are
items where the labeller looked and could not tell. They carry a blank `facility_type`, they are excluded, and they are not
a failed join. `scripts/ingest_batch.py` used to tally them under the heading
`(unmatched)`, which is how they came to be described as missing data; it now
prints the answer it was given.

### 19.2 The worklist was not unlabelled, and 122 of the 135 are duplicates

**289 of the worklist's 362 rows carry an address and state that
`NATIONAL_CLASSIFIED.csv` already holds** — the file
`national_facilities.csv` was built from. So
the batches largely re-label buildings labelled earlier the same week. On an
exact address-and-state key, 52 of the 85 delivery stations were *already
classified DS* in that file, 6 were blank there and 27 do not join at all.

The decisive check is not that key. It is `common/linkage.py`'s
Fellegi-Sunter comparator over **parsed addresses**, run against both
facility frames as they sit on disk, because a city string fails here —
`national_facilities.csv` files one building under HOLLYGLEN that OSHA files
under HAWTHORNE, and the two frames spell GRANT LINE and GRANTLINE
differently.

```
  85 delivery stations in batches 1-3          135 in batches 1-6
  -52  already in national_facilities.csv      -98
  -24  already in facilities.csv (pilot)       -24
  ---                                          ---
    9  new to both                              13

  review band (held for clerical review)   0 pairs, on both passes
```

Two collateral facts, both measured rather than assumed. The 52 and the 24 do
not overlap: **no pilot row matches any national row** (0 of 43), so the two
frames are disjoint and the arithmetic is a straight subtraction. And two
batch rows each match *two* national rows, which is Sec. 12.5's duplication
showing up from the outside: `2815 W. EL SEGUNDO BLVD.` is NAT-0011 and
NAT-0012, `1500 EAST GRANT LINE ROAD` is NAT-0025 and NAT-0026. The edit
`E_operating_by` already removes one of each pair at load.

### 19.3 The date decision: no date

The nine survivors carry OSHA's `operating_by` and no opening date.
`models/choice.build` scores each facility on the latest CBP vintage strictly
earlier than its `open_year`, because a delivery station *is* a warehousing
establishment and a contemporaneous count would contain the outcome
(`ingest/cbp_detail.py`). Writing an upper bound into `open_year` defeats
that guard: a vintage earlier than the BOUND can still be later than the
OPENING, and the lag from opening to first inspection is the 4-345 months of
Sec. 6.2.

Four rules were on the table. Judged against these nine rows and not in the
abstract:

| Rule | Verdict |
|---|---|
| Earliest usable vintage (2017) for all | **Unsafe, demonstrably.** It asserts an opening after 2017. `800 S 75TH AVE, PHOENIX` was already operating on 2017-06-02, and CBP 2017 counts the March 2017 pay period, so this is the one option chosen for safety putting the outcome inside the covariate. |
| `operating_by` minus a margin | **Not estimable.** Safety needs a margin at least as large as the lag. The lag is five observations spanning 4 to 345 months, all of them fulfilment centres opened 2008-2011, and Sec. 6.2 already flags the modern delivery-station lag as unmeasured. A margin safe for the worst case is 29 years, which is the row above; anything smaller is a guess. |
| Admit them for everything **except** the CBP-lagged covariate | **Taken.** Needs no new machinery: `choice.build` drops a facility with no usable `open_year` when an industry covariate is requested and never reads the field when one is not. |
| Wait for the satellite lower bound | **Right, and unavailable.** `data/collection/satellite/` holds the script and a worklist and has not been run. The nine are queued for it; this is the option that actually ends the problem, by turning a bound into an interval. |

So `open_year` and `open_quarter` are left **empty**, and the bound travels
in a column named `osha_operating_by`. Nothing is imputed and nothing is
manufactured, which is the Fellegi and Holt position `facility_load` already
takes when two rows contradict.

One thing must not be read into this. `E_operating_by` compares a *claimed*
opening against the bound, so a record that claims nothing passes by
construction. The nine pass. That is a tautology, not corroboration, and the
artefact says so beside the empty failure list.

### 19.4 What the thirteen buy, which is not what they were collected for

All thirteen, listed 2026-09-14. The first nine came out of batches 1-3 and
the last four out of batches 4 and 6:

```
  CAND-B1-002  17341 W MINNEZONA AVE  GOODYEAR       AZ  Phoenix-Mesa-Chandler
  CAND-B1-006  800 S 75TH AVE         PHOENIX        AZ  Phoenix-Mesa-Chandler
  CAND-B1-033  6990 HAIGH DR          ORLAND         CA  (no CBSA)
  CAND-B1-060  4800 MIDWAY RD         VACAVILLE      CA  Vallejo
  CAND-B1-061  920 EUBANKS DR         VACAVILLE      CA  Vallejo
  CAND-B2-054  201 W GRUMMAN RD       BETHPAGE       NY  New York-Newark
  CAND-B3-035  501 N KEYS RD          YAKIMA         WA  Yakima
  CAND-B3-038  48 BOSTON POST RD      ORANGE         CT  New Haven
  CAND-B3-039  137 LATHROP RD         PLAINFIELD     CT  Putnam
  CAND-B4-065  10 STATE ST            NASHUA         NH  (no CBSA)
  CAND-B6-001  2000 ENTERPRISE PKWY   HAMPTON        VA  Virginia Beach-Norfolk
  CAND-B6-007  1833 TWIN MILLS RD     VIRGINIA BEACH VA  Virginia Beach-Norfolk
  CAND-B6-009  W6331 WALLY WAY        GREENVILLE     WI  Appleton
```

Every one of the eight CBSAs is absent from the national frame, and two rows
are in no CBSA at all. The exercise was run for density and delivers breadth:

```
                          national frame     with the nine     with all 13
  buildings                     100                109              113
  CBSAs                          62                 68               70
  first in their metro           65 (65.0%)         74 (67.9%)       (69.0%)
```

The share **rises**. It rises for two compounding reasons: the new rows land
in empty metros, and an undated facility can never have a prior under
`choice.build`'s rule, so it is counted first-in-metro by construction. That
second reason is the one to remember — **these rows must be kept out of a
`with_saving` fit, not merely out of a CBP one**, because there they would
dilute the 35 informative decisions with thirteen degenerate ones and make
the underpowered test look better resolved than it is.

What remains is real but modest: **eleven** usable decisions for a fit
*without* the warehousing covariate. Eleven, not thirteen — Orland CA (ZCTA
95963) and Nashua NH carry no `cbsa_code`, so `choice.build` drops them. All
thirteen ZCTAs are present in `data/processed/panel.parquet`, so nothing else
stands in the way.

Nothing was merged into `data/external/facility_panel/`. `choice_runner`
fits on `load_national()`, so adding rows there moves a published number.

### 19.5 Two defects this turned up

**The CBP lag guard is nominal on the national frame.** Cross-checking
`data/collection/satellite/SITES_TO_DATE.csv`, which carries both fields,
**100 of the 100 loaded national rows have `open_year` and `open_quarter`
exactly equal to the quarter of their earliest OSHA inspection.** Re-checked
2026-09-14 directly against `NATIONAL_CLASSIFIED.csv`'s `operating_by`
column: it is **104 of 104 rows in the file**, and so 100 of 100 in the
loaded frame. Sec. 12.7 says 100 of 104; that understates it. The national
frame therefore *already* does the thing Sec. 19.3 refuses for the
candidates — it uses the bound as the date, with a margin of zero — and
`choice_runner` fits the `warehousing` covariate on it. Wherever the true lag
exceeds the residual within-year gap, the selected vintage post-dates the
opening and the covariate contains the outcome. This is a live finding about
a published number, so it is recorded and not acted on. Sec. 16.4 item 5 is
the measurement that would size it, and the whole defect now has its own
write-up at [`CBP_DETAIL.md`](CBP_DETAIL.md) §5.

**The satellite worklist double-counts.** `SITES_TO_DATE.csv` holds 133 rows,
100 from the national panel and 33 from batch 1. **25 of those 33 duplicate a
national-panel row already in the same file.** A satellite run would spend a
fifth of its budget re-dating buildings it has already queued. Batches 2 to 6
are not in the file at all; the eleven undated candidates they and batch 1
contribute are the rows that most need it.

*The satellite run has since happened and failed — 36% of its estimates date
construction after the OSHA inspection that proves the building was already
operating. The full negative result is in [`SATELLITE.md`](SATELLITE.md), and
the duplication above is no longer the binding problem with that route.*

---

*Maintained by hand. The figures in Sec. 17 were re-derived from the
artefacts on 2026-09-13, after the panel rebuild; re-derive them again before
quoting this document in anything assessed. Sec. 19 was derived on the same
day from `outputs/metrics/batch_candidates.json`.*

---

## 20. APPENDED 2026-09-15 — the first eight rows, and the two lessons they taught

*This section was relocated here when `docs/TODO.md` was retired. Nothing
above it was changed. It is the episode that produced the rule stated in
§11.1; keep both, because §11.1 is the rule and this is the evidence for it.*

A first hand-compiled batch of 8 facilities exists outside the repository
(`MSBA_Project/facilities (1).csv`). It was **not** copied into
`data/external/facility_panel/`, because checked against the pilot registry
**zero of the eight are in a fitting metro**:

| Facility | ZIP | City | Falls in |
|---|---|---|---|
| AMZ-KRB9 | 85212 | Mesa AZ | Phoenix — held out |
| AMZ-PHX3 | 85043 | Phoenix AZ | Phoenix — held out |
| AMZ-PHX6 | 85043 | Phoenix AZ | Phoenix — held out |
| AMZ-PHX7 | 85043 | Phoenix AZ | Phoenix — held out |
| AMZ-OAK3 | 95363 | Patterson CA | outside the pilot |
| AMZ-OAK4 | 95376 | Tracy CA | outside the pilot |
| AMZ-SCK3 | 95336 | Manteca CA | outside the pilot |
| AMZ-SMF5 | 95688 | Vacaville CA | outside the pilot |

Phoenix is one of the two held-out metros by design, and the four California
rows are in no pilot metro at all.

**Lesson 1 — the airport-code trap, discovered here.** `OAK3` and `OAK4` read
as Oakland and are in Patterson and Tracy, 60 to 70 miles inland in the
Central Valley, in Stanislaus and San Joaquin counties, nowhere near the San
Francisco Bay Area CBSA. `SMF5` reads as Sacramento and is in Vacaville,
which is Solano County and its own MSA. Verified against the OMB 2023
delineation, not by eye. **Always resolve the ZIP through the crosswalk;
never trust the building code.** The rule this produced, and the second half
of the trap (the code also lies about facility *type*), are §11.

**Lesson 2 — fulfilment centres are the wrong node.** Seven of the eight are
`FC` and one is `SC`. **None is a `DS`.** A delivery station is the node that
enables same-day service in a ZCTA, which is the outcome being modelled; a
panel of fulfilment centres answers a different question. This lesson was
re-learned at scale during the MWPVL merge, where a facility-class filter at
the panel boundary excludes 1,269 rows of the wrong class — see
[`PANEL_EXPANSION.md`](PANEL_EXPANSION.md).

**Why Chicago was the right first metro to collect by hand.** 380 pilot ZCTAs
against the Bay Area's 241; one CBSA rather than two (the "San Francisco Bay
Area" label spans 41860 and 41940); and no confusable neighbours, which
matters given the trap above. It also turned out to be the best-documented
metro in the hand-dating pass — five of the six genuinely-sourced opening
dates in `DATES_FOUND.csv` are Chicago-area facilities.
