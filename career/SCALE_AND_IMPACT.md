# Scale & Impact — the manager-facing answer

**"A fourteen-megabyte panel? That's a college project."**

This document exists because that reaction is the single biggest threat to how
this work lands with a hiring manager, and the honest response is not to inflate
the numbers. It is to **measure the right thing.**

---

## 1. The concern, stated fairly

A manager skimming your résumé runs an unconscious filter:

> *Can this person operate at our scale, or will they drown?*

They reach for row count because it is the cheapest available proxy. The panel
is 1,081,312 rows, which just clears the million mark and therefore says
nothing either way; what trips the filter is "14 MB". That is a real risk and
you should plan for it.

But the proxy is wrong, and you can say so credibly — because **most real
industry decision work is small data.** The median enterprise analytics table is
under a gigabyte. Terabyte-scale data lives in telemetry and logs, which is a
different job family. Nobody needs a billion rows to decide where to put two
hundred buildings.

The failure mode is not having small data. **The failure mode is describing your
project in units nobody funds.**

---

## 2. Measure the right thing: decision value, not row count

Managers do not fund rows. They fund decisions. So lead with the decision.

```
   ZCTAs in the pilot ................        2,413
   capital committed per activation ..     $3M - $5M
   -------------------------------------------------------
   CAPITAL ALLOCATION IN SCOPE .......    $7.2B - $12.1B
   national, if scaled ...............    $101B - $169B
```

**That is the headline.** Not 1,081,312 rows — **a model that ranks $7.2 to
$12.1 billion of capital allocation, and answers a question a city council
faces with public money on the other side of it.**

Those figures are measured, not asserted: ten pilot metros under the OMB 2023
CBSA delineation resolve to 2,413 ZCTAs, and `report/scope.py` multiplies that
through to `outputs/metrics/scope.json`. An earlier draft of this document said
5,200 ZCTAs and $15.6–26B, because the ZCTA count had been estimated rather
than counted. Being able to say "we measured it and it was smaller" is worth
more in the room than the extra ten billion was.

Same project. Same data. Completely different first impression.

### The reframe table

| Don't say | Say |
|---|---|
| "a million-row dataset" | "ranks $7.2B–$12.1B of capital allocation across 2,413 pilot markets" |
| "I built a dashboard" | "built a decision tool for a $4M-per-unit siting decision" — not "shipped", and not "deployed": it runs locally and there is no deploy config in the repository |
| "used public data" | "reproduced a proprietary decision framework from public data alone" |
| "10 metro areas" | "a national panel — all 33,791 US ZCTAs — with ten metros modelled in depth" *(see §5)* |
| "ran a Monte Carlo" | "a 500-draw parameter sweep that settled which of two published headlines was right". **Not** "24 billion draws", and **never** call the sweep a confidence interval — its own artefact says in terms that it is not one. A genuine bootstrap landed separately in `choice_report.json` on 2026-09-14; it is a different object, it is not yet committed, and it is a negative result. Do not merge the two into one claim |
| "small dataset" | "deliberately small — the contribution is identification, not throughput" |

---

## 3. The magnitude that *is* there

Row count is the only dimension where this project is small. Every other axis is
industry-grade, and most candidates cannot claim any of them.

### Compute — and what the uncertainty pass actually did

The 24,130,000,000 figure in `scope.json` is a **specification of compute that
was never executed.** It may be quoted as a design figure. It may never be
quoted as work done, and the phrase "with bootstrap CIs" that used to sit
beside it is deleted — it was written at a time when no standard error of any
kind existed anywhere in this project, and it described the 24-billion line,
which is a compute specification and not an uncertainty result. (An inference
layer has since landed in `choice_report.json`, on 2026-09-14. It is real, it
is uncommitted, and it has nothing to do with the 24 billion figure.)

What ran, on 2026-09-14, is smaller and far more interesting:

```
   parameter sweep over the portfolio optimiser ...  500 of 500 draws, seed
                                                     20260914
   activations n ..............  p10 152   p50 264.5   p90 306   (82-385)
   capital committed, $bn .....  p10 0.608 p50 1.058   p90 1.224
   top variance driver in n ...  cannibalisation_peak, 44.3%
```

**The reason to tell this story is not the band, it is the question it
settled.** A published headline had drifted — 330 activations in one draft, 317
in another, 282 in the current run — and the open question was whether the
parameters were doing it. They were not: 282 sits at the 67th percentile of the
sweep, comfortably inside, while 330 sits at the 97th, outside. So the mover
was depot placement, which the sweep does not classify as a parameter at all.
Diagnosing drift by ruling out the obvious cause is a real engineering answer
to "tell me about a debugging problem."

Two caveats that must travel with it, because they are the credibility:

- `parcels_per_depot_per_day` was **not sampled**, by oversight. Every band
  above is therefore a floor, not a range.
- `capital_usd` is exactly $4m x n in all 500 draws. So $1.128bn, $1.268bn and
  $1.320bn are the counts 282, 317 and 330 restated in dollars — one result,
  not three financial findings. Do not quote them as though they were.

### Combinatorics

```
   as a RANKING problem  ->  2,413 independent decisions
   as a PORTFOLIO problem ->  2^2,413 candidate bundles
   even restricted to the top 200  ->  2^200  ~=  1.6 x 10^60
```

The portfolio framing (bundles interact: cannibalisation pulls down, shared
route density pulls up) turns this into a genuinely hard combinatorial
optimisation. **The search space is larger than the number of atoms in the
observable universe.** That is the sentence that ends the "college project"
conversation.

And it is not left as arithmetic. The optimiser runs: greedy plus pairwise swap
against a computed upper bound, **282** activations selected against a capacity
of 500 that does not bind, and a **10.73%** gap to the bound. The headline
result is that at a $2bn budget it commits only **$1.128bn** and declines the
rest — about 44% of the budget left unspent, because the remaining activations
lose money. "Do not spend the whole budget" is the kind of finding a manager
recognises.

*Corrected 2026-09-14. This paragraph previously read "317 of 500", "13.03%",
"$1.27bn" and "leaves a third unspent", all from a superseded run, and it
credited the optimiser with "10.79% better NPV than naively taking the K
cheapest ZCTAs". That last comparison is not computed in the current run —
`naive_breakeven` is null in `portfolio_report.json` — so it is unverifiable
and has been removed. The break-even contribution margin is 1.343067; any
1.389 is stale.*

### Data recovery — the axis added on 2026-09-15, and the strongest one

Row count measures how much data you were handed. This axis measures how much
data you *made*, and it is the one this project is genuinely good at.

```
   source ...............  a 117-page industry PDF, 11.3 MB
   text layer ...........  1,074 lines for the whole document, ~120 of them
                           prose. The 13 tables are IMAGES - 152,915 pixel
                           rows, one strip 26,480 px tall referenced from 23
                           separate pages
   recovered ............  1,904 facility records, 58,088 words, 156 OCR
                           strips, 13 of 13 tables
   coverage .............  92.8% carry a postal code, 74.6% an opening year
   validated ............  three independent ways (below)
   merged ...............  635 admissible rows -> 589 new panel rows; the
                           facility panel goes 104 -> 693 rows, 62 -> 230
                           metro areas, 29 -> 50 states
```

Nothing about that is a volume claim and all of it is hard. The three
validations are the part to lead with, because each one uses information the
parser cannot see:

```
   vs OSHA inspection records ..  a building cannot open after an inspector
                                  recorded it operating. 208 records linkable,
                                  197 pass, 11 falsified - 94.7%
   vs the source's own prose ...  the network launched in late 2013; the
                                  parser knows nothing about that. 1,413 of
                                  1,420 dated rows plausible - 99.5%. The five
                                  impossible years are 2045, 2075, 2090 and
                                  2094 twice
   vs the ZIP-county-state
     FIPS crosswalk ............  the OCR'd state name ("Taxas", "Texas
                                  Texas") against the first two digits of the
                                  county GEOID. 604 of 606 agree - 99.67%
```

For comparison, the abandoned satellite-dating method failed the *first* of
those three on 36% of its output. Having a test that one of your methods
passes and another fails is what makes the test worth quoting.

Two caveats travel with this block. Several documents in the repo still quote
the earlier run of these validations — 157 linked / 10 falsified / 93.6%, and
556 of 557 / 99.8%. Use the artefacts. And the extraction-quality figure some
docs give as "97% clean" is stated in its own source as a working measurement
not reproducible from an artefact; quote the counts instead, 41 merged rows
falling to 18.

### Integration complexity

Fourteen registered public sources — thirteen of them analytical — at eight
different grains: block group, ZCTA, ZIP, county, CBSA, state region, facility
point and road network. Vintages from 2015 to 2025, different update cadences,
spatial joins and crosswalks throughout.

**Integration complexity is an industry-grade problem and it has nothing to do
with volume.** Anyone who has done enterprise data work knows that reconciling
fourteen sources at eight grains is harder than scanning a big table.

### Throughput and the engineering decision

**This block used to bill an OSRM redesign as done. It was never built, and the
claim has been removed.** No OSRM was ever run, no origin-destination parquet
exists, and no disk figure — the ~60 GB, the ~8 GB, the 30 GB saving — was ever
measured. They are the *design* estimates written into ADR-0002, which is an
accepted decision that was never implemented. The cost model in `src/` uses
great-circle distance multiplied by a circuity factor of 1.30.

This was the single highest-risk sentence in the career folder: it was in bold,
it called itself "the strongest engineering signal in the whole project", and
§3 of this same file said sixteen lines later that the OD matrix was unbuilt.
An interviewer who asked "show me the routing code" would have found the
contradiction inside a minute.

What is actually true and is worth saying:

```
   data passing through the pipeline .....  ~15-20 GB
   application dependency ................   one ~10 MB parquet, no routing
                                             service, no container
   distance model ........................   great-circle x 1.30 circuity
```

The defensible version of the story is a decision, not a saving: **you declined
to put a routing engine in the critical path, wrote down what it would have
cost in an ADR, and used an approximation instead.** That is still a
judgement call a manager recognises. What you may not say is that you measured
the saving, because you did not.

### Temporal and geographic depth

```
   panel span ...........  2018 - 2025  (8 years, 32 quarters)
   ZCTAs in the panel ...  33,791  (national, not a sample)
   panel shape ..........  1,081,312 rows x 50 columns, 14 MB
   priced ZCTAs .........  2,333, median $1.0830 per parcel
```

Two of those lines used to read "~4,000 facilities, 3 operators" and
"800,000 OD pairs computed". Neither figure was ever real, and they have
been replaced by things that are on disk. A third read "334 depots across 11
CBSAs"; **only the "11 CBSAs" was wrong.** The priced table covers ten metros,
and 334 is the sum over those ten of `ceil(metro daily parcels / 40,000)` —
recomputed from the baseline parquet — which is what the solver opens. The
"~329" in `cost/params.py:220` is the same quantity taken as one national
division, 13,152,992 / 40,000 = 328.8. Both are right about different things.
Quote either only with the "over ten metros" or "nationally" attached.

The OD matrix is still designed and unbuilt, so it stays off the list. The
facility panel is no longer missing, and as of the OCR extraction it is no
longer small either. If you put it on a résumé, put it on at this size and with
the caveats attached:

```
   facility panel .......  pilot:     43 Amazon delivery stations, 2015-2025
                           national: 104 rows / 100 buildings / 62 CBSAs /
                                     29 states
                           expanded: 693 rows / 687 buildings / 230 CBSAs /
                                     50 states, after the MWPVL extraction
                                     added 589
                           551 of 693 dated; 142 have no numeric open year
                             and the build REPORTS that rather than dropping
                             them
                           dates are OSHA "operating by" UPPER BOUNDS
                           0 of 693 rows arrive with a coordinate. Census
                             batch geocoding recovers 501 of 693 (72.3%),
                             190 No_Match and 2 Tie. The canonical
                             geocoded_expanded.csv and the data/interim/
                             rebuild are BYTE-IDENTICAL and both read 72.3%;
                             NEITHER is committed, so there is nothing an
                             interviewer can open. The earlier 455 of 700
                             (65.0%) was measured on the superseded 700-row
                             panel and no file on disk reproduces it - so
                             quote the 72.3% level, never a 65 -> 72 lift,
                             because the denominators differ
                           the 501 geocoded points live in a SIDE file and
                             are not joined into the panel, which records
                             coordinates_present: 0 - every distance
                             covariate still resolves to a ZCTA centroid
```

*Updated 2026-09-15.* The previous version of this block stopped at the
104-row national frame and said "0 of 104 rows are geocoded", which was true
when it was written and is now two results out of date in both directions —
the panel is 6.7x larger and most of it geocodes. The 693-row file is,
however, **gitignored** and its source PDF is outside the repository
(`../AUDIT_2026_09_14.md` §1.1, §1.2). Until both are fixed, this is a result
you can describe and cannot hand over, which is a weaker thing than it sounds.

Every part of that is checkable and the caveats are already in it. **Do not put
an unbuilt number on a résumé, and do not round 43 up to "thousands of
facilities"; both are the kind of claim an interviewer can check in a minute.**
The defensible claim here is not the size of the panel — it is that **five**
collection methods failed, the sixth worked, and every failure mode was written
down. The sixth is the OCR extraction, and it is the reason the panel is 693
rows rather than 104. The fifth failure, satellite dating, is the best of the
five; see the next section. See also
[`../data/FACILITY_PANEL_PROVENANCE.md`](../data/FACILITY_PANEL_PROVENANCE.md).

### Two failures worth more than the panel

Both ran in the last week, both are negative, and both are quotable **as
failures found and measured** — never as capabilities.

**Satellite dating, attempted 2026-09-14, failed.** All 107 sites got an
estimate from a median of 106 cloud-free Sentinel-2 scenes. On the 83 with a
known year, 41% landed within one year and the error standard deviation was
3.42 years — mediocre but arguable. The test that killed it was not accuracy:
**39 of 107 estimates, 36%, are logically impossible**, dating construction to
*after* the day an OSHA inspector recorded the building operating, a median of
33 months after. The confidence score does not discriminate — 35% impossible
above confidence 2 against 30% at confidence 1-2 — which localises the fault in
the changepoint detector rather than in the imagery. Finding an impossibility
test that your own output fails is a better interview answer than a working
pipeline, because it shows you looked for the way to be wrong.

**The labelling programme, 362 sites over 6 batches, mostly wasted.** It
produced 135 delivery stations of which only **13 were genuinely new**: 289 of
the 362 rows, 80%, were already classified, because
`scripts/make_unlabelled_batches.py` compared against the wrong reference. Lead
with that. The recoverable part is real but secondary — the 122 non-new rows
each carry a quote and a URL, so they are independent confirmations, and taken
together they are an accidental validation set for the name-based classifier in
`ingest/osha.py`. Say the 80% first and the salvage second; the reverse order
is the version that gets caught.

---

## 4. The scale-anxiety question, and how to answer it

**"Our data is 100x bigger. Could you handle that?"**

Do not get defensive and do not overclaim. Answer with architecture:

> "The panel is small on purpose — the hard part here was identification, not
> throughput. But the architecture is scale-agnostic below the feature layer:
> columnar parquet, DuckDB, a source-agnostic ELT with contracts in CI. The
> panel already runs nationally — all 33,791 ZCTAs, 1,081,312 rows — and it
> comes to 14 megabytes, because columnar compression over eight years of
> quarterly demographics is extremely efficient. Scope is a config change; the
> ten pilot metros are a modelling decision, not a capacity one. If your data
> is 100x this, the same pipeline moves to object storage and a distributed
> engine without touching the model layer, because nothing above L3 knows
> where the bytes came from.
>
> The part I'd want to talk about is what actually broke at *this* scale: the
> portfolio objective was evaluating all 2,333 priced ZCTAs on every candidate
> when only the selected rows matter."

That answer does three things: it declines the premise politely, it shows you
know what scaling costs, and it redirects to a real problem you found.

*Two things were cut from that answer on 2026-09-14. The speedup "from 653
seconds to 30" appears in no artefact — if you can find the timing that
produced it, cite it; until then do not say it. And "road-network preprocessing
needed a redesign to fit at all" is the OSRM claim again: no road-network
preprocessing was ever run. See §3.*

---

## 5. Buy magnitude with the smallness — this one is already banked

This was written as a recommendation. It has since been built, which is the
better version of the same argument.

**Because the data is small, national coverage was nearly free:**

```
   built ZCTA-quarter panel  =  33,791 ZCTAs x 32 quarters x 50 cols
                             =  1,081,312 rows  =  14 MB
```

Note how badly the estimate in the earlier draft missed: it predicted 0.46 GB
and the built artefact is 14 MB, a factor of thirty. Columnar compression over
slowly-moving demographics is far better than people expect, and that is worth
knowing before you size a cluster you do not need.

Ten metros is a scoping decision that *sounds* like a limitation. All 33,791 US
ZCTAs across 50 states is a **coverage claim**, it is true, and it cost almost
nothing precisely because the data stayed small.

**What was done:** ten metros modelled in depth for the causal work (where you
need treated/control structure) — 2,413 ZCTAs, eight fitting and two held out —
over a panel that carries the whole country. So:

> *"National coverage — all 33,791 US ZIP-code areas — with causal
> identification on ten pilot metros, two of them held out."*

That is an industry-grade scope statement, and with the OSRM claim removed from
§3, every word of it is now defensible. It was not while that claim stood.

---

## 6. Think like the manager: what they are really screening for

| What they ask | What they're testing | Where this project answers it |
|---|---|---|
| "How big was the data?" | scale anxiety | §4 — decline the premise, show architecture |
| "What broke?" | production instinct | `objective.py` priced activation capital three ways at once — about a 2.74x overcharge; 42% of depots exceed 40,000 parcels/day, so the line-haul term is a lower bound; `rent_index` is missing in at least one quarter for 94.3% of ZCTAs (80.5% have no value at all) and those rows are still listwise-deleted at `cost/runner.py:166`; and the facility panel still carries **no coordinates at all** — `coordinates_present: 0` on all 693 rows, so every distance covariate resolves to a ZCTA centroid. (The 501 geocoded points exist, but in a side file that is not joined in and not committed. The older version of this cell said "0 of 104 facilities are geocoded", which is stale on the row count and on the reason.) |
| "How did you know it worked?" | evaluation rigour | **It did not, and that is the answer.** The hazard model lost to a constant and was retired, and a revival on the expanded panel confirmed the retirement — AUC did not move (0.6894 → 0.6832) and the constant null is better calibrated in **17 of 17 comparisons** — seven arms across three hold-out designs; `model_better_calibrated_at` is an empty list. The conditional-choice successor was then matched out of sample by a single raw covariate, so its three estimated parameters bought no ranking (corrected from "beaten" on 2026-09-14 — see below). A third, metro-grain specification was pre-registered and failed its own declared criterion in 0 of 7 years, and in all 18 combinations tried. What worked was the *evaluation*: a null for every model, whole-unit hold-outs, a hashed pre-registration, and a 500-draw sweep that settled whether a drifting headline was a parameter effect (it was not — 282 sits at the 67th percentile, 330 at the 97th) |
| "What did you cut?" | prioritisation | cut list in ROADMAP.md, with reasons |
| "Who used it?" | outcome orientation | planners, air districts, EJ orgs — an audience named, not one that asked. Say so |
| "What would you do differently?" | self-awareness | unit of analysis checked before writing code; covariate dispersion checked before choosing a specification; experiments that checkpoint per stage rather than at the end; routing decided in week 0 |
| "Did you find anything that generalises?" | ability to abstract | the dispersion rule — measure a covariate's coefficient of variation *within* the conditioning group before fitting. **7 of 7** terms below cv 0.6 landed on the boundary; **9 of 14** above cv 1.3 came back interior; nothing in between. So the rule is asymmetric — low dispersion is *sufficient for failure*, high dispersion is *necessary but not sufficient* — and it is a screen for what to drop, not a promise about what to keep. The five high-cv failures are all on the sortation side, four of them carrying square footage as the mass. There is a knob (the gravity exponent) that moves the cv 28x on identical underlying facilities and moves the coefficient with it. Say "correlation with a mechanism and a manipulation", not "causal" — the source note refuses the stronger word. And say the n: 21 non-independent terms, one run, one vintage |
| "How do I know you're not just telling me the good parts?" | integrity | the pre-registration: a hashed criterion written 24 minutes before the fit, failed 0 of 7 years, reported in the artefact along with four deviations including one stating the design is biased *against* the hypothesis being tested |

> **Corrected 2026-09-14.** The "how did you know it worked?" row said the
> conditional-choice successor was **beaten** out of sample by a single raw
> covariate. It now says **matched**. That is a retraction, not a refresh: the
> word came from one seeded 56/38 split, where the raw warehousing count led
> the fitted model 8-7 at top-1 and 20-19 at top-10. Fifty paired re-splits of
> the same 94 decisions put the count ahead by **0.36 hits of 38, paired sd
> 1.14**, with the count losing 11 of the 50 and tying 16
> (`../../outputs/metrics/gbm_benchmark.json`, `across_repeats`). A third of a
> decision is noise, and this document's own rule — never quote a number you
> have not read off an artefact — is what caught it.
>
> **The answer to the question is unchanged.** It still did not work: fitting
> three parameters bought no ranking improvement over counting warehouses, and
> that is the second of the two measured negative results this file counts as
> an industry-grade signal. Only the verb is smaller.

**Notice that "how big was the data" is one question out of six, and it is the
only one where you are weak.** Do not let it dominate your own framing of the
work.

---

## 7. Seniority is visible in what you chose *not* to do

This is the part most students miss.

A junior candidate brags about volume. A senior candidate explains a tradeoff.
The sentence that reads as senior is:

> *"I deliberately kept the analytical panel small. The contribution is
> identification, not throughput — and I'd rather spend the compute budget on
> uncertainty than on scanning rows I don't need."*

You cannot say that unless it is true, which is the point. Every cut in
`ROADMAP.md` carries a reason for exactly this purpose: the cut list *is* the
seniority evidence.

*This sentence used to end "on 24 billion uncertainty draws". Cut, on
2026-09-14: 24 billion is a specification in `scope.json` that was never
executed, and the sentence put it in the past tense of a compute budget
actually spent. What was spent is 500 draws.*

**And the counter-example, which belongs here because this section is about
compute discipline.** The brief on this project was single-threaded execution
on a shared six-core box, with instructions to cut the repeat count rather than
parallelise. That instruction is written into two module docstrings recording
the machine at load average 24 and 25. A five-process pool was used anyway, the
box reached **load average 44 on six cores**, the run had to be killed, and
forty-five minutes of finished work was lost because the experiment persisted
only at the end. One neighbouring experiment reached 45 of 50 re-splits and has
no artefact at all; another got 1.1% of a core against a sibling's 96.5% and
lost four of its eleven arms. The recovery — `os.nice(19)` everywhere,
per-stage persistence, a ledger recording which stages actually ran, arm-major
execution in a pre-declared order — is a better engineering story than the
restraint would have been, but only if it is told in that order. Do not present
the policy as a design decision. It was a repair.

---

## 8. The trap: do not fake scale

If you describe this as big data and a manager probes for thirty seconds, it
collapses — and the collapse costs you far more than the small number ever
would. You go from "small project, honest engineer" to "inflates claims," and
only one of those is recoverable.

**The whole strategy of this project is that its claims survive checking.** That
applies to the résumé exactly as it applies to the novelty section and the
accuracy metrics. Same discipline, three different audiences.

---

## 9. The three sentences to memorise

*Revised 2026-09-15 from two to three. The scale sentence answers a question
about volume; it does not, on its own, say anything you built. The extraction
sentence goes first now, because it is the one that is unambiguously an
achievement and it makes the other two land as measurement rather than as
apology.*

> *"The dataset this project needed did not exist in machine-readable form, so
> I built it: 1,904 facility records recovered from a 117-page PDF whose tables
> are images, with the table structure rebuilt from OCR word boxes, validated
> three independent ways — the sharpest one against inspection records that
> prove a building was already operating."*

> *"The analytical panel is deliberately small — 1,081,312 rows and fourteen
> megabytes — because the hard problem is identification, not throughput. What
> it ranks is $7.2 to $12.1 billion of capital allocation across 2,413 pilot
> markets, over a panel that already covers all 33,791 US ZIP-code areas."*

> *"I wrote down what would count as the model working, hashed the file, fitted
> the model, and it failed the criterion in 0 of 7 held-out years — so what I
> can offer you is a method that was tested rather than a result that was
> reported."*

Lead with the first, use the second when they ask about volume, and keep the
third for the moment they ask what you found. Nobody who hears all three asks
whether it's a college project.
