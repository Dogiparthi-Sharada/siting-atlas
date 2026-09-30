# The models, in plain English — what each one is, and how it performs

**Written 2026-09-15 for a reader who has not followed the engineering.**
Every number cites the file it came from. Where a result was withdrawn or
corrected, that is stated rather than tidied away.

---

## 1. There are four models, and they answer different questions

People say "the model" as if there is one. There are four, they were built in
sequence, and each exists because the previous one hit a wall.

| Model | The question it answers | Verdict |
|---|---|---|
| **Cost model** | *What does it cost to deliver a parcel from here?* | **Works.** The most solid thing in the project |
| **Hazard model** | *Will a station open in this ZIP this quarter?* | **Retired.** Negative result, honestly reported |
| **Choice model** | *Given one station opens in this city, which ZIP?* | **Works, but weakly.** Currently the headline |
| **GBM benchmark** | *Could any model do better with this data?* | **Answered: barely.** It exists to test the others |

---

## 2. The cost model — the one that works

### What it is

Given a ZIP code, how much does it cost Amazon to deliver one parcel there?

You cannot answer this by looking it up; nobody publishes it. So it is
**computed from geography and physics**, using a published method (Daganzo's
continuous approximation, 1984). The intuition is simple:

> A van drives out, makes many stops, and drives back. If houses are packed
> close together, the driver spends most of the time at doors and very little
> driving between them. If houses are spread out, the reverse. So cost per
> parcel falls as density rises — specifically, as **one over the square root
> of density**.

### What it produces

```
  median cost per parcel   $1.1389
  p10 $1.0008, p90 $1.3445
  cheapest station  MWP-0156, Miami FL        $0.92   (catchment median)
  dearest  station  MWP-0472, Enid OK         $1.71
  cheapest metro    Virginia Beach, VA-NC     $0.97   (median of its 4 stations)
  dearest  metro    Enid, OK                  $1.71   (a single station)
  8,037 ZIPs costed, 501 real stations (481 with a costed ZIP)
```

*From `outputs/metrics/cost_by_station.json` (`run_id 20260916-131845-34f1`).
**The depot layer changed on 2026-09-16** and this block is not a correction of
the old one — it is a different model. Depots used to be 334 sites a p-median
solver invented across 10 metros; they are now the operator's 501 real,
address-geocoded delivery stations, nationally. The old block read $1.083 over
2,333 ZIPs with "cheapest metro Miami $0.94, dearest Boise $1.43"; that run is
retired and is kept as the comparison in `docs/NUMBERS.md` §10.2. Note the
metro extremes are now thin — Enid OK is one station — so read the station
extremes, not the metro ones.*

Broken down per stop: **59.75% driver time at the door**, 21.63% vehicle
lease, 12.63% driving, 5.98% fuel (stop-weighted shares; `docs/NUMBERS.md`
§10.1).

**What changed when the depots became real, and why it matters more than the
level.** The median rose only 5.2%. But the median **line haul** — how far the
van drives before its first stop — went from 4.02 miles to **9.09**, because a
real national network is not a distance-minimising one. So driving and fuel
went from 10.1% of a stop to **18.6%**. Labour still carries the bill, but it
is no longer true that "the routing mathematics is decoration"; that sentence
was about the old model. A p-median is a lower bound on line haul by
construction, so **the 5.2% is the measured price of siting in the real world
rather than the optimal one** — land, labour, zoning and leases.

*Coverage: 20 of the 501 stations have no ZIP within 15 miles; 316 ZIPs (0.83%
of catchment households) are dropped for having no federal driver wage and
nothing is imputed; 8 of the 501 are announced rather than open.*

### Why it is trustworthy

It is a published method with sourced parameters, and it was stress-tested
across five scenarios spanning **−17.2% to +7.7%** — `dense_routing` −17.20%
and `congested` +7.68%, measured on **median cost per parcel**
(`cost_by_station.json`, `sensitivity.span_pct`). Always name the statistic:
the retired pilot's span was −17.09% to +4.35%, and two documents once carried
"−16.6% to +4.8%", which no parquet reproduces.

One thing that *used* to be true here is no longer: the cost model used to be
independent of the facility data, so none of the upheaval elsewhere touched
it. **It is now built on the facility panel** — the depots are 501 rows of it.
That is a large improvement in realism and a new dependency, and both should
be said.

### The one thing it cannot do

It cannot rank **where Amazon will build** — and the reason is in the cost
function itself, not in a statistic. Cost falls as one over the square root of
density. So the cheapest places to serve are the densest, and the densest are
exactly where a warehouse cannot physically be built: no parcel of land, no
loading dock, no zoning, no lease. The cost surface and the buildable surface
point in opposite directions.

> **Feasibility binds before economics.**

That is also why the only covariate that predicts siting at all is a raw count
of existing warehouses: it measures where building is *possible*.

**A note on a statistic this document used to carry, and no longer does.**
Earlier versions said "of 40 facilities [later 43], none sits in its metro's
cheapest 10%". **That claim is withdrawn.** Once the cost model's depots *are*
the facilities, a ZIP containing a station has a line haul of about zero
because the station is inside it — so the model makes every facility's own ZIP
cheap by construction and the test measures its own circularity. Masking each
station and re-pricing gives 6.9% of the 501 stations in their metro's
cheapest decile but 16.3% of the original 43 — below chance and above chance,
opposite conclusions from the same run. A number that flips sign depending on
which facilities you draw it over is not evidence. The mechanism above stands
on its own; the decile count does not. Details in `docs/NUMBERS.md` §10.4.

---

## 3. The hazard model — retired, and the retirement is the point

### What it was

For every ZIP, every quarter: will a station open here now? A standard
survival model — the same mathematics used for "will this patient relapse".

### Why it failed

It was fitted on real data and did not work:

```
  AUC 0.689 against a 0.500 coin flip
  worse calibrated than a constant   (ECE 0.00863 vs 0.00005)
  negative skill out of time  (-0.021) and out of area (-0.062)
  39 events across 8 metros   [unverified] -- no such pair is in
                              hazard_report.json, which records 812
                              ZCTA-quarter events and 28 independent
                              episodes on 38 usable facilities
```

"Worse calibrated than a constant" means: a model that ignores everything and
predicts the same number every time produces better-behaved probabilities.

### Why it was retired rather than fixed

It broke a statistical assumption in a way no amount of tuning repairs. When
one station opens, it switches on a **median of 39 ZIPs** at once in the data.
The model treats those as 39 independent observations. They are one decision
counted 39 times, and the standard errors are meaningless as a result.

*This figure was 58 until 2026-09-16. 58 came from the retired pilot run; the
current measurement is the median of 39 at the 15-mile catchment in
`experiments/hazard-model/artefacts/hazard_revival.json`
(`provenance.catchment_load`, mean 52.4, p90 105, max 317). The smaller number
does not soften the objection — no radius between 8.3 and 45 miles brings the
median below 14, so the observations are still multiply-counted, and the
retirement was taken on that, not on the size of the multiple.*

**It is kept in the repository as a documented negative result**, not deleted.

---

## 4. The choice model — the current headline

### What it is

A different question, chosen because it is the one the data can answer:

> *Given that Amazon opens one station in Chicago, which of Chicago's ~200
> candidate ZIPs does it pick?*

Each opening is **one** decision with one answer. No double-counting.

### How it works, in one line

Each ZIP gets an "attraction" score built from a few numbers about it, and the
probability it is chosen is simply **its share of the city's total
attraction**. A ZIP with 10% of the attraction has a 10% chance.

### How well it performs

The fair way to score it: *how much better than guessing?* And that must be
reported separately by city size, because in a small town with 12 candidate
ZIPs, **random guessing already lands in the top 10 about two-thirds of the
time** — there is nothing to beat.

```
  combined arm, conditional logit, 483 decisions
  large metros (>100 candidate ZIPs)    6.26x better than chance  (258 decisions)
  mid-size     (26-100)                 3.05x                     (160)
  small towns  (<=25)                   1.46x                     ( 65)
                                                   <- capped by the arithmetic
```

**6.26× in large metros, on 258 decisions of the 483, is a real result** — and
large metros are where siting is actually contested. The arm has to be named:
the same quantity is 6.18× on `original_only` (94 decisions, 46 large), 6.53×
on `mwpvl_only` (389, 212), 6.78× on `mwpvl_clean` (360, 194) and 6.29× on
`combined_plus_network` (483, 258). An unlabelled "lift in large metros" is
meaningless across those five.

*Source: `outputs/metrics/panel_experiments.json`, regenerated 2026-09-15
13:37 after an OCR address fix was promoted. That fix moved the sample from
485 to 483 decisions and the headline coefficient from 1.170 to 1.191 — small
movements, recorded because this document is meant to be checkable.*

### The uncomfortable part

The model has four inputs. Three of them contribute **nothing** — the
mathematics drives their weight to zero. Remove the fourth, a count of
warehouses already in the ZIP, and the large-metro top-10 lift collapses from
6.22× to 2.68× (`baseline` against `no_warehousing` in
`outputs/metrics/covariate_search.json`, whose frame is a different one again:
477 decisions, 191 held out — not the 483 above). *That artefact was
regenerated on 2026-09-15; these are the figures from the completed run, which
moved the pair from 6.39×/2.74× on the superseded copy. The collapse was never
in doubt and is the same size either way.*

> **The model is one variable.**

And no coefficient in it is statistically distinguishable from the baseline.
Asked four ways, every proper test includes the "no effect" value.

---

## 5. The GBM benchmark — the referee

### What it is

A gradient-boosted tree ensemble: a flexible machine-learning model with no
theory in it, allowed to find any pattern it likes. It exists purely to answer
one question:

> Is the choice model held back by **the data**, or by **its own simple form**?

If the flexible model does much better, the form is the problem. If it does
about the same, the data is the ceiling.

### The answer

```
  original_only frame, 94 decisions, 38 held out, mean over 50 re-samples
  conditional choice model    20.60 of 38     best probability score of all
  warehouse count, unfitted   20.96 of 38
  gradient-boosted trees      22.26 of 38     (gbm stump/200 levels, the best)
```

The flexible learner wins by **about one decision in 38** — and loses on
probability quality. The spread between *all* methods is smaller than any one
method's variation across re-samples.

> **The ceiling is the data, not the model.**

Then the sample was quintupled (94 → 483 decisions, the `combined` arm) and
the GBM's edge **disappeared entirely** (top-10 rate 0.5198 for the GBM against
0.5196 for the choice model). Its one-decision advantage had been the
small-sample model being slightly underfitted, not a real gain from
flexibility.

---

## 6. Did we switch to gravity models? No — and here is why

**Gravity model** means: instead of "distance to the nearest sortation
centre", use "the pull of the *whole* network", where every facility
contributes an amount that falls off with distance — like gravity.

### It won on one axis

It is the first specification whose coefficients are **never** driven to zero
— both of `gravity_count_a3`'s columns are interior in 0 of 50 re-samples,
where the previous best, `proximity_published`, has nearest-sortation-distance
at zero in 4 of 50. And offered both at once (`gravity_best_plus_proximity`),
the model **keeps gravity and discards nearest-distance**: the two proximity
weights collapse from 0.104 and 0.187 to 0.017 and 0.030.

So gravity is the better *measurement*.

### It lost on one axis of three

```
  large-metro top-10 lift, gravity_network.json, 483 decisions, 258 large
  proximity_published (baseline)   6.290
  no_network          (floor)      6.259
  gravity_count_a3    (best)       6.219
```

**No gravity specification beats the baseline on large-metro top-10 lift** —
`gravity_count_a3` comes in below even the no-network floor.

But top-10 is not the whole comparison, and reporting it alone is how this was
previously misread. Paired over the same 50 re-splits, `gravity_count_a3`
against `proximity_published` is **+0.0116 on top-1** (42 re-splits improved, 4
worsened) and **+0.0126 on top-5** (44 improved, 2 worsened), against
**−0.0002 on top-10** (18 improved, 22 worsened). Brier also favours gravity,
0.0050165 against 0.0050303.

**So gravity loses at k=10 and wins at k=1 and k=5.** There is no single
scalar for "gravity versus proximity"; the answer depends on how many ZIPs you
are allowed to shortlist.

### And it costs something real

The model's mathematical justification requires that if you merge two ZIPs,
their attractions add up. Counts do that. Distances and gravity pulls do not.
Measured over 43,224 merged pairs (`network_inference.json:merger_invariance`):
**0.00 error** for the extensive-only control, **0.044 median and 0.455
maximum** for the network specification.

The model still runs. What it loses is the *argument for why it has this
shape* — which is the only justification the specification gives.

> **Verdict: a better measurement that predicts better at k=1 and k=5 and
> worse at k=10, bought with the theoretical foundation. Not switched.**

*(This verdict has changed. It previously read "does not predict better",
which was read off the top-10 column alone. On the current re-run gravity wins
top-1, top-5 and Brier and loses only top-10, so the case against switching now
rests on the aggregation cost above and on the top-10 loss, not on a blanket
failure to predict.)*

---

## 7. The one genuinely useful rule this produced

Fifteen new variables were tested. None helped. But the *reason* generalises,
and it can be turned into a test you run **before** fitting anything.

Measure how much a variable varies **among ZIPs inside a single city**:

```
  varies little  (cv below 0.6)  ->  it fails         7 of 7
  varies a lot   (cv above 1.3)  ->  it works         9 of 14
  nothing lands in between (the 0.6-1.3 band is empty, 0 of 21 terms)
```

**The rule only runs one way.** Low dispersion is *sufficient for failure*:
every one of the 7 terms below 0.6 lands on the coefficient boundary. High
dispersion is *necessary but not sufficient for success*: 9 of the 14 terms
above 1.3 are interior, and the 5 that are not are all on the sortation side,
four of them carrying square footage. So a low reading rules a variable out,
but a high reading does not rule it in. An earlier version of this section
claimed the rule held "21 of 21 times" in **both** directions; it does not, and
the two-way version was the part that made it sound like a predictor.

Why it is not a coincidence in the direction it does run: the test was run on
one variable with a **dial** that changes only how sharply it discriminates
within a city — nothing else. As the dial turned, the variable walked from
useless to useful.

**Read this as description, not as an estimated relationship.** It is 21 terms
from a single run at a single vintage, and they are not independent — each is
one of two columns in one of 13 arms fitted over the same 483 decisions. And
because no term lands between 0.6 and 1.3, the rule says nothing at all about
intermediate dispersion.

**Six of your fifteen failures were county-level numbers copied onto every ZIP
in the county** — about nine distinct values across 200 candidate ZIPs. You
cannot rank 200 things using 9 numbers, however important the thing being
measured.

---

## 8. So what does the project actually show?

**The prediction does not work well, and that is now established rather than
suspected.** Five different datasets, three algorithms, fifteen variables, and
a complete reframing all land in the same narrow band.

What the work produced instead:

1. **A measured visibility gap.** Of the **488** cities where MWPVL lists an
   Amazon delivery station, OSHA has an inspection record in only **138** —
   **28.3%**; the other **350** are invisible to OSHA entirely. These are two
   independent city lists, not a numerator and a denominator. The comparison is
   **conservative** (OSHA's side counts *any* Amazon facility class, so
   narrowing it would widen the gap) and it is a **floor, not an estimate** — a
   two-list intersection rather than capture-recapture, and MWPVL is itself
   incomplete. The modelled estimate is a different quantity and lives in
   `nlrb_coverage.json`.
2. **A diagnosis, not just a null.** Free public data is mostly published at
   county level or is population under another name — and a ZIP-level model
   can use neither. That is a finding about public data infrastructure.
3. **An audit of the project's own key variable** for circularity, which very
   few applied papers perform. It survives, retaining 79% of its value when
   forced to use only pre-opening data.
4. **A mechanism that ties three failures together.** Amazon **densifies** —
   at the headline radius of 45 miles, **68.7% to 75.9%** of 2024-25 openings
   land inside territory the pre-2024 network already served. That range is
   across the two coordinate sets at the *one* radius, not across radii: 75.9%
   is 60 of 79 openings with real coordinates, 68.7% is 90 of 131 once
   ZCTA-centroid fallbacks are allowed in. That single fact explains why
   warehouse-count predicts, why network-proximity works, and why looking for
   unserved gaps fails.

---

## 9. What is NOT done, as of 2026-09-15

Stated plainly because a reader should not have to infer it.

| | Status |
|---|---|
| Proposal markdown | Updated — 9 wrong claims fixed, 2 sections added |
| Proposal `.docx` | A v6 **draft** exists, built before the figure problem was found |
| **Figures 9 and 10** | **NOT FIXED — see below. Treat as blocking** |
| Defense documents | Only partly updated; today's findings not yet in them |
| Hazard model | Never re-run on the expanded panel; still reads the old one |

### The blocking item

Figure 9 in the proposal plots a cannibalisation decay curve with a **95%
confidence band** and a **significance annotation**. All nine values are typed
by hand in the plotting code. The outcome on its y-axis — 2-day order volume —
**does not exist in the project's data**, and its absence is precisely why the
cannibalisation analysis was abandoned.

The caption says "values are illustrative pending estimation". That is six
words beneath a chart showing error bars and a significance test, and figures
are routinely lifted into slides without captions.

Figure 10 is the same pattern with **no disclosure at all**.

**Either restyle both as obvious schematics without intervals, or remove
them.** A hand-typed confidence interval in a submitted document is the single
most damaging thing a reviewer can find.
