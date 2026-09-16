# NLRB — how to get it, and what it is for

*Created 2026-09-13. Drop the file in this folder. Nothing in `src/` reads
it yet; wiring it up is a separate task.*

---

## 1. What to download — two routes, do both if you can

### Route A: case search (broader, easier)

```
  https://www.nlrb.gov/search/case
```

Search the employer field for `Amazon`. Do it several times, because the
employer name is typed by regional staff and is not standardised — the same
company appears as all of these and more:

```
  Amazon.com Services LLC          Amazon.com Services, Inc.
  Amazon Logistics, Inc.           Amazon.com, Inc.
  Amazon Fulfillment Services      Amazon.Com.Dedc, LLC
```

Search each variant separately. Export the results table. If the site only
lets you export one page at a time, several files are fine — name them
`nlrb_cases_1.csv`, `nlrb_cases_2.csv` and so on and drop them all here.

**Also search for the DSPs.** Delivery-station drivers are employed by
Delivery Service Partners, which are separate legal companies, so a case at
a delivery station may name the DSP and not Amazon. If you see DSP names in
the results, grab those too and note them. This is the single biggest
limitation of the source for our purposes — see section 4.

### Route B: election reports (better fields, narrower)

```
  https://www.nlrb.gov/reports/graphs-data/recent-election-results
```

These are monthly spreadsheets of election results, and they carry the
**full street address and the size of the bargaining unit**, which the case
search often does not. Unit size is a proxy for facility size and we have no
other measure of it. Download whatever range is available and filter for
Amazon afterwards — do not pre-filter, because we want the denominator too.

---

## 2. Fields we need

`TEMPLATE.csv` in this folder shows the target schema. Do not reformat your
download to match it — **give us the raw export**. Reshaping is our job and
a hand-edited file loses provenance. The template exists so you can see
what we will try to extract:

```
  case_number      e.g. 29-RC-261755
  case_type        RC / RD / RM / CA / CB / CD ...
  employer_name    verbatim, do not clean it
  street_address   the prize — most useful field in the file
  city, state, zip
  date_filed       gives the "operating by" bound
  date_closed
  status
  unit_size        number of eligible voters, if present
  region           NLRB region number
```

**Keep the leading zeros on ZIP codes.** If you open the file in Excel it
will silently eat them and turn 07001 into 7001. Either do not open it in
Excel, or import it as text. This has already bitten this project once.

---

## 3. What it buys us — honestly

### The obvious use, which is worth less than it looks

A filing proves the facility existed and was operating on the filing date.
That is the same **interval-censored "operating by" upper bound** the OSHA
data gives us, and it plugs into the same machinery.

But the volume will be small. Amazon NLRB activity is concentrated in a
handful of well-known sites, and we should expect tens of facilities, not
hundreds. On its own this adds rows at the margin.

### The real prize: measuring how incomplete our panel is

We currently cannot answer *"how many Amazon facilities did you miss?"* We
have no denominator. Two independent incomplete lists give you one.

Capture-recapture, the idea in one example. You want to know how many fish
are in a lake. Catch 100, tag them, release. Later catch another 100 and
find 20 tagged. The second catch was 20% tagged, so your 100 tagged fish are
about 20% of the lake, so the lake holds about 500.

Applied here:

```
  OSHA found        474 buildings (951 inspections)
  NLRB finds        N buildings
  In BOTH lists     M buildings
  Implied total     roughly  474 x N / M
```

That would let us publish a **measured coverage rate** rather than an
apology. It turns "our panel is probably incomplete" into "our panel covers
an estimated X% of the network, and here is how we know." For a project
whose entire claim is *what a city can establish from free public data*,
knowing the size of what you cannot see is close to the whole point.

We have more than two lists, which is better still: OSHA, NLRB, the OSM
extract in `data/raw/osm_amazon/`, and MWPVL's frozen 2012 table. Three or
more lists allow a log-linear model that can estimate the dependence between
sources instead of assuming it away.

---

## 4. Why this might not work — read before spending an evening on it

**The independence assumption is violated, and I want to say so before we
collect rather than after.**

Capture-recapture in its simple form requires the two lists to be
independent: being on one must not change your chance of being on the other.
OSHA inspects where workers get hurt and where workers complain. NLRB cases
arise where workers organise. Both are driven by worker grievance, so a
facility that appears in one is *more* likely to appear in the other.

Positive dependence makes the simple estimator **underestimate** the total.
So a naive Lincoln-Petersen number would be a lower bound, not an estimate,
and we must report it as such. There are estimators built for this — Chao's
lower-bound estimator is valid under heterogeneity, and log-linear models
over three or more lists can estimate pairwise dependence directly. A
defensible lower bound is still far better than nothing, and it is honest.

**Three further limitations, all real:**

```
  1  The DSP problem. Delivery-station drivers work for Delivery Service
     Partners, not Amazon. A case at a delivery station may name the DSP.
     Since delivery stations are our TARGET, this bites exactly where it
     hurts most. Mitigate by searching DSP names too, and by matching on
     ADDRESS rather than employer name.

  2  Selection on our own covariates. Union activity correlates with
     facility size, urbanness and state labour law. Density is the
     variable our whole cost argument turns on, so NLRB coverage is
     selective on the confounder — the same trap as the Zillow rent
     data. Do not treat NLRB presence as random.

  3  No opening dates. Same as OSHA. It bounds from above and never says
     "opened in 2019".
```

**My honest expectation:** a handful of extra buildings, and one genuinely
valuable number — a measured, defensible lower bound on how much of the
network our panel sees. The second is worth the effort; the first is not.

---

## 5. After you drop the file

Tell the assistant it has landed. Wiring it in means:

```
  1  an ingest module, mirroring src/siting_atlas/ingest/osha.py
  2  an entry in the EXPECTED tuple in ingest/external.py so the
     --check gate validates it
  3  address matching against the OSHA panel via common/linkage.py,
     which already implements Fellegi-Sunter and is the right tool
  4  the capture-recapture estimate, with its dependence caveat stated
```

Steps 1 and 2 touch files another agent is currently editing, so this is
sequenced after that work lands, not in parallel with it.
