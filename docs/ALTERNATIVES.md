# Where this project could go next, and why

*Written 2026-09-14, after two prediction models were built and neither one
earned its parameters. This is a decision document for the inspirator, not a
plan. Nothing here is started.*

Each option below says what it is in plain terms, why it is on the table,
what evidence we already have for it, what it would cost, and what would
make it fail. They are not mutually exclusive, but they compete for the same
weeks.

---

## The situation, in four lines

We tried to predict which ZIP code Amazon puts a delivery station in. Two
models, neither of them worth its parameters. The first was beaten outright
by a constant. The second is **matched** by **counting the warehouses
already in each ZIP** — 20 correct against 19 out of 38 — and the inference
says we cannot distinguish our fitted covariate from that raw count
(interval 0.73 to 2.83 against a null of 1, p = 0.287).

> **Corrected 2026-09-14.** These four lines said *"Two models, both beaten.
> The second is beaten by counting the warehouses."* The second clause is now
> **matched**. It is a correction, not news: the word "beaten" came from one
> seeded 56/38 split — the 20-against-19 still quoted above — and fifty
> paired re-splits of the same 94 decisions put the count ahead by only
> **0.36 hits of 38, paired sd 1.14**, with the count losing 11 of the 50
> (`outputs/metrics/gbm_benchmark.json`). We read a one-hit difference as a
> result; it was noise. Nothing else here moves. Three fitted parameters
> still buy no ranking improvement over a warehouse count, which is why the
> options below are written the way they are. (The *first* model really was
> beaten, by a constant — that clause stands.)

Meanwhile one thing we built almost as a side-effect turned out to be new:
we measured **how much of Amazon's physical footprint is visible in free
public records at all.** About a third to a half.

The question is which of those to build the capstone on.

> **Amended 2026-09-14, evening; figures refreshed 2026-09-15.** The model has
> since been refitted on a
> panel expanded from 104 to 693 rows / 687 buildings — 94 decisions to 483 —
> and the conclusion above did not move. `warehousing_establishments` went from
> 1.528 [0.985, 2.550] to 1.191 [0.956, 1.490]: a 66% narrower interval that
> still contains 1.0, with the point estimate moving *towards* the numeraire.
> Five times the sample did not rescue the prediction, which strengthens
> rather than weakens the case for choosing A + B.
> See `docs/research/NOTES_EXPANDED_REFIT.md`.

---

## Option A — Observability. Measure what a community can see.

### In plain terms

Stop asking *"where will Amazon build?"* and ask *"how much of what Amazon
has already built can an ordinary person find out about, for free?"*

The method is the same one ecologists use to count fish. Catch some, tag
them, release, catch again, and the overlap tells you how many you never
caught. We use three independent public lists — safety inspections, labour
complaints, volunteer-made maps — and the overlaps between them tell us how
many Amazon buildings none of the lists contain.

### Why go there

```
  it is NEW           nobody has published this, for any firm. The
                      professor's "did you copy a paper" worry disappears
  it is MEASURED      not an opinion. outputs/metrics/nlrb_coverage.json
  it USES the failures  every dead end becomes evidence about the gap
  it is POLICY        the answer is a number a legislature could act on
```

### The evidence we already have

```
  best free source shows Amazon in            340 US cities
  true number, assuming lists are independent 630   (54% visible)
  true number, allowing for heterogeneity     899   (38% visible)
  three-list model with dependence MEASURED   314-417
```

*Two OSHA city counts are in circulation and they are not the same quantity.*
**340** is `nlrb_coverage.json`'s `n_osha` — the deduplicated city list the
capture–recapture runs on, and the numerator behind the 54% and 38% above.
**409** is the count of distinct cities in the raw inspection extract (the
table in §A below). Quote 340 with the coverage figures; quoting 409 against
630 would give 65%, which is not a number this artefact reports.

The dependence is not assumed. OpenStreetMap gives a third list whose
capture mechanism — a volunteer drew the building — has nothing to do with
worker grievance, which is what drives the other two. Measured odds ratios:
NLRB x OSHA given OSM 1.84, NLRB x OSM given OSHA 1.72, OSHA x OSM given
NLRB 3.82. All positive, which is why the coverage figures are CEILINGS.

### Cost

Already built. `ingest/nlrb_capture.py` and `nlrb_estimators.py` run it.

### What would make it fail

If a reviewer rejects capture-recapture on the grounds that the lists are
not a random sample of anything. That objection is real and the honest
answer is that it is why we report a range and a direction of bias rather
than a point.

---

## Option B — Do Option A for several firms, not one.

### In plain terms

Run the same measurement on Walmart, UPS, Target, FedEx and the rest. One
firm is an anecdote. Eight firms with different answers is a method.

### Why go there

It converts a case study into a contribution, and it opens questions that
one firm cannot ask: does visibility depend on the **firm**, the **sector**,
or the **state's disclosure law**? That last one is a policy lever somebody
could actually pull.

### The evidence we already have

Tested 2026-09-14 against the OSHA bulk extract, one pass over 105 archive
members:

```
  firm          inspections   distinct cities
  UPS                 5,359             1,024
  WALMART             4,896             1,900
  TARGET              2,125               918
  HOME DEPOT          2,076               897
  FEDEX               1,546               586
  KROGER              1,395               513
  AMAZON              1,093               409
  COSTCO                809               299
```

**Amazon is the least-inspected of the eight despite being among the
largest.** That is itself a finding and it is exactly the variation the
comparison needs. OSHA and OSM are national and firm-agnostic; only NLRB
needs one export per firm, which is the same download already done once.

### Cost

An evening of compute plus one NLRB export per firm.

### What would make it fail

If every firm comes out near 50%. That is still interesting — the limit
would be structural rather than firm-specific — but it is a weaker paper
than measured variation.

---

## Option C — Price what a site is worth, so a county can negotiate.

### In plain terms

A county negotiating a tax break has no idea what the site is worth to the
company. Our cost model computes it: how much money Amazon saves by putting
a station here rather than anywhere else. That is a number to negotiate
against.

### Why go there

It rests on the components that **work** — the cost model, the depot
network, the optimiser — rather than the one that does not. And valuation
does not need prediction: you do not have to guess the choice in order to
price the parcel they have already chosen.

### The evidence, including the part that complicates it

`models/accessibility.py` already computes the demand-weighted line-haul
saving from siting at each candidate. But a test on 2026-09-14 found
something that must be said out loud before anyone builds on this:

```
  40 pilot facilities, ranked by cost-to-serve within their own metro
      in the cheapest 10% of the metro     0%    (chance: 10%)
      in the cheapest 25%                 12%    (chance: 25%)
      median rank                       0.44     (chance: 0.50)
```

**Amazon does not build where it is cheapest to serve.** Zero of forty.

That is not a broken cost model. Under Daganzo, cost falls as one over the
square root of density, so the cheapest ZIPs to serve are the densest ones —
central Manhattan — and those are precisely where you cannot build a
warehouse. **Feasibility binds before economics.** It is also why counting
warehouses wins: that count is really a measure of where building is
possible.

So the tool prices a SPECIFIC parcel somebody is already considering. It
does not rank all ZIPs and it must not be sold as though it does.

### Cost

The valuation exists. Two things must be fixed first: the capital term in
`optimize/objective.py` prices an activation three inconsistent ways and
overcharges by about 2.7x, and the depot network is infeasible (42% of
depots exceed throughput), so line haul is a lower bound.

### What would make it fail

We cannot validate the cost model against Amazon's real costs, because
nobody publishes them. The defence is that it is Daganzo's published method
with sourced parameters and a measured sensitivity, not that it is right.

---

## Option D — Ask a different question the data can answer.

### In plain terms

Instead of *"does a station change Amazon's economics"*, ask *"does a
station change the neighbourhood"* — house prices, air quality, traffic.

### Why go there

The original proposal had a second estimand aimed at cannibalisation, whose
outcome is order volume, which we cannot see. It was abandoned for that
reason. But the review found that the prerequisite list **never names the
outcome variable** — it silently assumed order volume throughout.

*"Does a delivery station change nearby house prices?"* makes the project's
stated mission — communities bearing the consequences — literally true rather
than aspirational.

### RE-ASSESSED 2026-09-14, and the verdict changed from BLOCKED to PARTLY OPEN

This section used to end *"Do not start this until the dates exist."* **1,420
opening dates now exist** — `outputs/metrics/mwpvl_extraction.json`, OCR'd from
all thirteen MWPVL 2025 Q1 table images, with 873 of them precise to the month.
The blocker that closed this option is gone.

Re-assessing it honestly turned up two things the paragraph above got wrong,
and one of them kills half of the option.

**1. `pm25` IS NOT A TIME SERIES, so the air-quality half is dead on the data
we hold.** Measured 2026-09-14 against `data/processed/panel.parquet`
(1,081,312 rows, 33,791 ZCTAs, 2018Q1-2025Q4):

```
  column               coverage   ZCTAs with >1 distinct value over 32 quarters
  home_value              74.9%        26,262  <- a real panel
  rent_index              11.2%         6,264  <- thin
  pm25                    98.5%             0  <- A CONSTANT
  median_home_value       89.7%             0  <- A CONSTANT (the ACS one)
```

`pm25` is one cross-section repeated across every quarter. A before/after
design needs the outcome to move, and this one cannot. The old text cited
"`pm25` at 98.6%" as evidence of readiness; 98.5% coverage of a constant is
not readiness, it is a column that looks like a panel and is not one. Air
quality is back to being a data-acquisition problem (EPA AQS by year), not an
analysis one. The same is true of `median_home_value`, which is why only
`home_value` is usable.

**2. The house-price half IS feasible, and it is the whole option now.**
`home_value` varies within 26,262 ZCTAs across the window. That is a real
outcome panel and nothing else in this document is blocked on it.

**3. The dates are not in the panel, and putting them there is the work.**
`enabled` — the treatment column — is built by `warehouse/facilities
.enabled_flags` from `facility_load`'s default file, which is
`data/external/facility_panel/facilities.csv`: **43 pilot facilities in 10
states**, dated off the OSHA bound. Measured: 1,257 ZCTAs are ever enabled and
**912 actually switch 0 to 1 inside the window**, which is the treatment-timing
variation a staggered design needs. The 589 new MWPVL facilities live in
`national_facilities_expanded.csv`, which **nothing downstream reads**. So the
cost line below is not "a week of analysis"; it is a pipeline change first.

**4. The 34-month finding is an argument FOR doing this, and it is new.**
`docs/research/NOTES_COVARIATE_LEAKAGE.md` measures that the OSHA-derived
`open_year` the panel uses is a median **34 months later** than the true
opening (n = 42; 88% of gaps exceed a year). Any before/after design built on
the current `enabled` column is therefore timed about three years late, which
for a house-price event study means the "before" window is mostly after. The
MWPVL dates do not merely unblock this option — they correct a defect that
would have silently ruined it.

### What the dates are, stated so nobody treats them as a registry

They are **OCR'd claims by a consultancy**, validated three ways and not
perfect. `outputs/metrics/mwpvl_validation.json`:

```
  94.71% pass E_operating_by -- 208 dates could be linked to an OSHA
         building, 11 are FALSIFIED by it. On the month-precision rows
         specifically: 160 matched, 9 falsified.
  99.5%  plausible (1,413 of 1,420). The five implausible are OCR damage
         -- 2045, 2075, 2090, 2094 twice -- and are flagged, not repaired.
  1,212  of the 1,420 dated rows could NOT be linked to OSHA at all. An
         unchecked row is not a passing row.
```

For an event study the direction of that error matters more than its size. A
mis-dated event is not symmetric noise: it puts treated periods in the control
window and control periods in the treated one, which **attenuates the estimate
towards zero**. So a null result from this design would be weak evidence of no
effect, and that has to be said in advance rather than discovered in the
discussion section. Three specific exposures:

```
  ~5%   of month-precision dates are falsified by an external bound and
        would be mis-timed by a median of several quarters
  142   of the 589 added rows carry NO year at all and cannot supply an
        event date; they are locations only
  ~3%   of OCR'd rows merge with a neighbour and carry another facility's
        date entirely (MWPVL_OCR_PIPELINE.md sec.13.1)
```

The mitigation is available and cheap: MWPVL's month plus the OSHA
`operating_by` day is a genuine **interval**, so the design can be run on rows
where the interval is tight and the sensitivity to interval width reported.
That is also the thing `models/risk_set.py` has never implemented.

### Cost

Revised. The old estimate was "about a week for a first credible cut", and it
assumed the dates would arrive already joined.

```
  1  rebuild the panel off national_facilities_expanded.csv so enabled
     reflects 693 rows / 687 buildings rather than 43. Blocked first on
     the 142
     rows that fail ingest/facility_check on a non-numeric open_year --
     they are locations without events and the design has to say what it
     does with them.                                      days, not hours
  2  the event study itself, on home_value only            about a week
  3  air quality, IF wanted, needs EPA AQS by year         a new source
```

### What would make it fail

No longer the dates. Four things, in descending order of how likely each is to
be the one that bites.

```
  1  SELECTION. Amazon does not site at random and this document already
     measures it: Option C found Amazon builds in ZERO of forty metros'
     cheapest decile, because feasibility binds before economics. A ZCTA
     that can host a warehouse differs from one that cannot in exactly the
     ways house prices differ. Parallel trends is the assumption and it is
     the one a reviewer will attack first.
  2  ATTENUATION FROM DATE ERROR, above. Measurable, and it biases
     towards finding nothing.
  3  GEOCODING. 0 of 104 national, 0 of 589 MWPVL and 0 of 43 pilot
     facilities carry a coordinate, so "nearby" is resolved at ZCTA
     centroid precision. A distance-band design (0-1 km, 1-3 km) is not
     available; a ZCTA-level one is.
  4  enabled_flags takes min(open) and max(close), so a ZCTA served by two
     stations stays enabled through the closure of one. MWPVL's prose says
     over 123 buildings were closed, cancelled or delayed in 2022-2023
     (MWPVL_2025.md sec.3.1), so exits are real and the panel has none.
```

---

## Option E — Buy the data the published literature used.

### In plain terms

Houde, Newberry & Seim's Econometrica paper is built on a commercial network
census from MWPVL. Buy the same thing, use it as ground truth, and measure
how close free data gets.

### Why go there

This is not cheating and it is not abandoning the free-data claim. It is the
opposite: it turns our coverage ceiling from an estimate into an exact
measurement. *"We bought the commercial dataset solely to measure the error
of the free method, and here is the measured error"* is a stronger sentence
than anything we currently have.

It also reframes the thesis usefully. The data **exists** and is **sold**.
Amazon has it by definition, the industrial REITs have it, site-selection
consultants subscribe. A county planning department does not. The asymmetry
is not scarcity — it is price.

### What to establish before paying

```
  1  does it carry OPENING DATES, or only locations?  Locations alone
     leave our binding constraint untouched.
  2  is there academic pricing?  Consultancies routinely discount for a
     citation, and MWPVL already knows the academic channel exists.
  3  what are the redistribution terms?
```

**Question 1 is now answered, and the answer is yes.** Updated 2026-09-14: the
inspirator fetched MWPVL's *public page* — not the paid product — and it is
current to **2025 Q1**, not the April 2012 vintage this section used to cite.
That older file is a different document and its exclusion in
[`data/NLRB.md`](data/NLRB.md) §5.2 does not carry over. The free page's
tables are images, and OCR of them shows the columns run *state, facility
code, street address, square footage, **opening month and year***. The paid
XLSX is the same data in a machine-readable form.

So the purchase is no longer a gamble on what is inside. It buys three things:
the format, the currency, and the redistribution right. See
[`data/MWPVL_2025.md`](data/MWPVL_2025.md) for the full read.

**And the reason to move rather than deliberate.** From the page itself:

> *"in future we will no longer be updating this information online due to the
> high rates of plagiarism of this content ... If there is an interest in
> obtaining current information available in XLSX format then please contact
> us and we can provide details regarding the commercial terms."*

The free channel is being closed by its publisher, and the stated cause is
that it was free. That sentence is worth more to this project as **evidence**
than the table is as data — it is the price-not-scarcity thesis stated by the
party with the least reason to help us make it — but it also means the window
on the free copy is closing. Archive what we have with its retrieval date.

Contact is `info@mwpvl.com`.

### What would make it fail

Not the dates question any more. The remaining risks are price, and
redistribution terms that forbid publishing derived figures — which would not
stop us measuring the free sources' error against it, but would stop us
shipping the comparison.

---

## What these cost each other

```
  A   observability, one firm      built. Weeks: 0
  B   observability, many firms    an evening of compute + NLRB exports
  C   valuation for counties       fix two defects first. Weeks: 1-2
  D   neighbourhood effects        UNBLOCKED on dates 2026-09-14. House
                                   prices only -- pm25 is a constant in
                                   our panel. Rebuild the panel first,
                                   then weeks: 1
  E   buy the ground truth         no longer a gamble on content; the free
                                   page's tables are already OCR'd, so
                                   this now buys format, currency and
                                   redistribution rights only
```

**A and B are the same work and B is nearly free once A exists.** C is
independent of both. **D is no longer blocked** — it is half the size it looked
(air quality is out) and it carries a pipeline rebuild in front of it. E
strengthens A and B; its dates question is answered, and the 1,269 non-delivery
MWPVL facilities the panel merge excludes are already a fourth capture list for
A and B.

---

## The recommendation, and the reasoning behind it

**Lead with A + B. Keep C as the tool. Hold D. Send the email for E.**

> **Amended 2026-09-14. The recommendation stands and the reason for holding D
> has changed, which matters because the old reason was "impossible" and the
> new one is "expensive".** D was held because dates did not exist. They exist.
> It is still held, for two reasons that are weaker than the old one and should
> be re-examined if either moves: air quality is out until an EPA AQS panel is
> acquired, and the house-price half needs the warehouse panel rebuilt off the
> 693-row facility file before a single regression can be run. If somebody
> rebuilds that panel for another reason — and blocker 1 in
> `STATUS.md` §3 may require it — D becomes a week of work and should be
> reconsidered on the spot rather than left on hold by inertia.

The reason is not that prediction failed. It is that we **measured the
ceiling** on prediction from free data, and that measurement is more
interesting than the prediction would have been if it had worked. A model
that got top-10 to 60% would still have been a worse contribution than
knowing that free records show you a third to a half of what exists.

The failures argue for this rather than against it. Under "can you predict?"
they are four embarrassments. Under "how much can you see?" they are four
measurements of the gap:

```
  satellite failed, 36% impossible     imagery does not substitute for records
  362 sites labelled, 13 new           public lists overlap far more than
                                       they appear to
  model only ties one raw count        free covariates saturate quickly
  cost does not predict siting         feasibility binds before economics
```

*(That third line read "model loses to one raw count" until 2026-09-14. It
ties; see the correction at the top of this file. The point it is making —
that fitting on free covariates adds nothing over a raw count — is the same
either way.)*

**What would change this recommendation.** If the multi-firm run in B comes
back with every firm near the same coverage, the comparison loses its
interest and C becomes the stronger spine — a working tool beats a flat
measurement. That is a two-hour test and it should be run before the
framing is rewritten, not after.
