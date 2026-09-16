# Handbook Part 1 — Foundations

**The problem domain, from zero. What a delivery network is, why siting is hard,
where the money is, and why anyone outside the company should care.**

You do not need any logistics background to read this. Every term is defined the
first time it appears, and every idea gets an example.

---

## 1.0 Read this before the rest of Part 1

```
  +--------------------------------------------------------------------+
  |  THE DOMAIN TEACHING IN THIS CHAPTER STANDS. THE PROJECT'S SITING  |
  |  MODEL IS NOW A CONDITIONAL CHOICE MODEL, AND ITS HEADLINE IS A    |
  |  NEGATIVE ONE.                                                     |
  |                                                                    |
  |  CURRENT MODEL - conditional ZCTA choice, national frame.          |
  |  Fitted, converged, 3 free parameters, 94 decisions, 56 train /    |
  |  38 held out, seed 20260914. McFadden rho-squared 0.19691 in       |
  |  sample. Artefact outputs/metrics/choice_report.json.              |
  |                                                                    |
  |  THE HEADLINE. On the 38 held-out decisions a SINGLE RAW CENSUS    |
  |  COUNT - warehousing establishments, NAICS 493, nothing fitted     |
  |  from it - MATCHES the fitted model:                               |
  |                                                                    |
  |                          top-1   top-5   top-10    Brier           |
  |     fitted model          7/38   16/38    19/38   0.008724         |
  |     warehousing count     8/38   16/38    20/38   0.008951         |
  |     households alone      1/38    5/38    10/38   0.009271         |
  |     uniform within metro  1/38    3/38     7/38   0.009316         |
  |                                                                    |
  |  The estimation buys nothing measurable. One parameter of three    |
  |  does any work; the other two sat on the boundary at ~3e-16.       |
  |                                                                    |
  |  AND THE INTERVALS AGREE. Inference landed 2026-09-14 (sandwich    |
  |  plus bootstrap, as docs/MODEL_SPEC.md Sec. 6.3 prescribes) and    |
  |  says the one working parameter is NOT distinguishable from the    |
  |  null. Note the null is beta = 1, NOT beta = 0: households is      |
  |  fixed at 1 as the numeraire, so beta = 1 means "worth exactly     |
  |  one household, and the model cannot tell them apart".             |
  |                                                                    |
  |    warehousing_establishments, beta = 1.4428                       |
  |      sandwich 95%             [0.734, 2.835]  p = 0.287            |
  |      bootstrap over decisions [0.760, 4.762]                       |
  |      bootstrap over metros    [0.702, 10.013]                      |
  |      BCa                      [0.714, 3.522]                       |
  |    ALL FOUR COVER 1.0.                                             |
  |                                                                    |
  |  RETIRED / SUPERSEDED - the discrete-time hazard model on          |
  |  ZCTA-quarters. Built, fitted on real data, FAILED. AUC 0.6894     |
  |  against a null of 0.5000; calibration 170x WORSE than a           |
  |  constant-rate null; negative Brier skill on both hold-outs; 7.6   |
  |  events per parameter against a conventional floor of 10. It is    |
  |  kept in this pack as a teaching example, not as a result.         |
  |  Artefact outputs/metrics/hazard_report.json.                      |
  |                                                                    |
  |  HANDBOOK_04_MODELS.md carries both results and the diagnoses.     |
  |  docs/STATUS.md carries the one-page version.                      |
  +--------------------------------------------------------------------+
```

> **A claim withdrawn.** This banner used to present the hazard model as *the*
> project's siting model and said nothing about a successor. A successor has
> since been fitted, so the old banner was stale rather than false. It was
> replaced on 2026-09-14 against `outputs/metrics/choice_report.json`.

> **A second correction, 2026-09-14, and this one was an error rather than a
> staleness.** The banner said the raw CBP count **BEATS** the fitted model.
> It does not; it **matches** it. The word came from the single seeded 56/38
> split whose table is printed above. Re-splitting the same 94 decisions fifty
> times puts the raw count ahead by **0.36 hits out of 38, paired sd 1.14**,
> with the raw count losing 11 of the 50
> (`outputs/metrics/gbm_benchmark.json`). A third of a decision is not a
> result in either direction, and "beats" read noise as one. The printed table
> is still correct for its seed, and the finding it supports is untouched: the
> three estimated parameters buy **no** ranking improvement over simply
> counting warehouses.

**Why that belongs at the top of a foundations chapter.** One idea in this
chapter turned out to be load-bearing and wrong: the claim in Sec. 1.2 that
because service is switched on per ZIP, the ZIP is therefore the natural *unit
of decision*. It is the natural unit of **observation**. It is not the unit of
**decision**, and confusing the two is the single reason the hazard model
failed. That sentence has been corrected in place and the correction is
explained where it sits, so that you learn the domain and the mistake together.

**And note what the successor did and did not buy.** Moving to the right unit
of decision was necessary — the hazard model's units were not independent
observations at all. It was not sufficient: the correctly specified model is
still only level with a raw count you can download from the Census in ten
minutes.
Fixing a specification error does not manufacture signal that the sample does
not contain.

Everything else here - the last mile, ZCTA versus ZIP, the MAUP, the density
law, cannibalisation, who the work is for - is unaffected by either model
result and is still the material you need.

---

## 1.1 What is a "last mile" and why does it have a name?

Shipping a package has three legs:

```
  FIRST MILE          MIDDLE MILE            LAST MILE
  seller  ->  hub     hub  ->  hub           hub  ->  your door

  a truck picks up    long-haul between      a van drives to
  from a warehouse    cities, full loads,    hundreds of individual
                      very efficient         addresses
```

The first two legs move **many packages together**, so the cost per package is
tiny. The last leg moves **one package to one door**, which means a van, a
driver, a parking spot, a walk to the porch.

> **The number that explains the whole industry:** the last mile is commonly
> cited as roughly **half of total shipping cost**, despite being the shortest
> distance. Everything in this project exists because that half is the part you
> can actually optimise.

**Why the name matters for us:** we are not modelling shipping in general. We are
modelling the *placement of the buildings that start the last mile.*

---

## 1.2 The building types, decoded

Retail logistics has an alphabet soup. You need four terms.

| Term | What it is | Rough size | What it does |
|---|---|---|---|
| **FC** — Fulfilment Centre | The giant one. Stores millions of items | 800k–1M+ sq ft | Picks and packs orders. Feeds everything downstream |
| **SC** — Sortation Centre | A sorting hub | 200–400k sq ft | Takes packed orders, sorts by destination ZIP |
| **DS** — Delivery Station | The last building before your door | 100–200k sq ft | Vans load here. **This is the last-mile node** |
| **SDC** — Same-Day Centre | Small, fast, close to customers | 50–150k sq ft | Holds ~100k popular items for sub-24h delivery |

> **Example — following one order.** You order a phone case at 9am.
> - If it ships **2-day**: it sits in an **FC** 300 miles away → trucked to a
>   **SC** → sorted → trucked to your local **DS** → van → your door.
>   Total: two days.
> - If it ships **same-day**: it is already in an **SDC** 12 miles from you →
>   straight to a van → your door by 6pm.

**The strategic point:** same-day is not "2-day but faster." It requires
*physically different buildings, closer to customers.* That is why the expansion
is capital-intensive and why it happens ZIP by ZIP.

### Why we model at ZIP-code grain

Same-day service is switched on **per ZIP code**, not per city. The operator's
own website will tell you same-day is available in 94608 but not 94621, two
adjacent ZIPs in the same city. So the ZIP is the natural **unit of
observation**: it is the finest grain at which you can *see* the outcome.

### The correction that cost us the model: observation is not decision

An earlier version of this paragraph finished "...and therefore the natural unit
of analysis." **That inference is false, and the project's central specification
was built on it.**

A delivery station has a catchment of roughly 15 miles. When it opens, it
switches on *every ZCTA inside that circle at the same moment*. Measured on the
delivered panel:

```
   ZCTAs switched on by ONE delivery station
   -----------------------------------------
   median               58
   mean                 88
   largest             307
```

> **Worked example.** The panel contains the row "ZIP 60608, 2021Q2,
> event = 1". Read as a decision, that says Amazon chose 60608. It did not.
> It chose to put a building somewhere in Chicago, and 60608 was one of
> **88 simultaneous consequences**. Feed all 88 rows to a model as independent
> observations and you have told it you saw 88 decisions when you saw one.

The assumption this violates is **independence across observations**, Train
(2009) Sec. 3.7.1, printed page 61:

> *"Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is
> L(beta) = prod_n prod_i (P_ni)^{y_ni}."*

The likelihood multiplies one term per observation *because the observations
are independent*. Eighty-eight rows generated by one building are not
independent, so the product is wrong and every quantity derived from it —
the log-likelihood, the standard errors, the events-per-parameter count —
is inflated by a factor nobody measured. The standard name for this failure is
**clustering**, or **pseudo-replication**.

> **A claim corrected.** This passage used to cite Train (2009) Sec. 2.2 — the
> requirement that alternatives be mutually exclusive. That is the wrong
> section. Sec. 2.2 governs the choice set facing a decision maker; a hazard on
> area-quarters has no decision maker choosing among those rows, so exclusivity
> is not a property they can have or lack. Train himself calls that criterion
> "not restrictive" and writes that "Appropriate definition of alternatives can
> nearly always assure that the alternatives are mutually exclusive" (p. 12) —
> a two-line repair, not a fatal one. The fatal assumption is independence
> across observations. Corrected 2026-09-14.

**The reframe that is correct, and it has now been built:** *which ZIP does the
station go in, given that a station is opening in metro `m` in period `t`?*
That gives one decision per building instead of eighty-eight rows per building,
so the independence assumption above is at least arguable. It is exclusive,
enumerable, and real — and here Train Sec. 2.2 *is* the right authority,
because now there genuinely is a decision maker facing a choice set.

The successor is fitted: a conditional ZCTA choice model on the national frame,
**94 decisions**, 56 train and 38 held out, three free parameters, converged.
Its result is in the banner above, and it is not a happy one. See
`HANDBOOK_04_MODELS.md` and `../METHODS_RESEARCH.md` Sec. 5.1.

> **A claim withdrawn.** This paragraph used to say the successor specification
> was "open, not chosen - nobody has built it", and put it at 43 decisions on
> the pilot frame. Both statements were true when written and are false now:
> the model exists, it was fitted on the national frame, and it yields 94
> decisions. Measured from `outputs/metrics/choice_report.json` on 2026-09-14.

**So: model at ZCTA grain for everything you can observe at ZCTA grain** - cost
to serve, demographics, service availability, equity overlays. All of those are
genuinely per-ZCTA and all of them work. Do **not** model the siting *choice* as
one independent observation per ZCTA-quarter. The successor still *picks* a
ZCTA, but it does so once per building, conditional on a metro and a period,
which is a different object from a panel of 1.08 million rows each pretending
to be a decision.

---

## 1.3 ZCTA — the unit of analysis, and its known flaw

We say "ZIP code" casually, but we actually use **ZCTA** — ZIP Code
Tabulation Area.

**Why the distinction matters:**

- A **ZIP code** is not a shape. It is a *postal route* — a collection of
  mail delivery paths owned by the postal service. Some ZIPs are a single office
  building. Some are a PO Box cluster with no area at all.
- A **ZCTA** is the Census Bureau's attempt to draw an actual *polygon* that
  approximates each ZIP, so you can join demographic data to it.

There are roughly **33,000 ZCTAs** in the United States.

> **Example of the mismatch.** ZIP 10118 is the Empire State Building. It has a
> ZIP code, thousands of daytime workers, and essentially no residents. As a
> ZCTA it is a tiny polygon with near-zero population — so a demand model
> that keys on population will say "no demand here," which is right for
> residential delivery and wrong for commercial.

### The MAUP — a limitation you must state before a reviewer does

**Modifiable Areal Unit Problem** (Openshaw, 1984): *statistical results change
when you change the boundaries you aggregate over.* Same underlying reality,
different answer.

> **Example.** Imagine six households in a row, with incomes:
> `40k, 40k, 40k, 120k, 120k, 120k`.
> - Group them as `[40,40,40]` and `[120,120,120]` → two very different
>   areas, huge between-area variation.
> - Group them as `[40,40]`, `[40,120]`, `[120,120]` → three areas, much
>   less clean.
>
> Nothing about the households changed. Only the lines on the map.

**Why it bites us:** ZCTAs are postal constructs, not statistical ones, and they
are **redrawn between census vintages**. A result at ZCTA grain need not hold at
census-tract grain or hexagonal grain.

**What we do about it:** pin one vintage (2020) and document the crosswalk.
**Both of those are done** - the pinned ZCTA count is an enforced data contract,
so vintage mixing fails the build rather than passing silently.

**What the design also calls for, and what has not been built:** a robustness
check at **H3 hexagonal grain**. If a conclusion survives a completely different
spatial partition, MAUP is not driving it. There is no H3 code in `src/` today,
so say "specified, not run" if asked. Spatial reviewers always ask, and
"specified, not run" is a perfectly respectable answer; claiming it was run is
not.

> **Note the irony, and use it.** The MAUP is the general warning that your
> answer depends on the boundaries you drew. Sec. 1.2 is the specific case where
> that warning came true and cost this project its headline model. MAUP is not
> a box to tick in a limitations section. It was the failure mode.

---

## 1.4 Where the money is

This is the part to lead with in front of anyone senior.

```
   capital to enable ONE ZIP code for same-day .....  $3M - $5M
   ZIP-code areas in our modelling scope ...........  2,413
   ------------------------------------------------------------
   CAPITAL ALLOCATION IN SCOPE .....................  $7.2B - $12.1B

   if extended to all 33,791 US ZCTAs ..............  $101B - $169B
```

The 2,413 is counted, not estimated: it is what the ten pilot metros resolve
to under the OMB 2023 CBSA delineation, and `report/scope.py` writes it and
the dollar range into `outputs/metrics/scope.json` on every run. An earlier
draft put the scope at 5,200 ZCTAs and $15.6–26B on a guess at the ZCTA count.
Quote the measured figure; a defensible seven billion beats an indefensible
fifteen.

### What that $3–5M is actually made of

Eight buckets. Four dominate.

| Bucket | What it pays for | Metro variation | Tier |
|---|---|---|---|
| **Real-estate lease** | Warehouse space, annualised | **Very high** — SF ≈ 3× Austin per sq ft | Primary |
| **Wages** | Drivers, warehouse staff | **High** — unionised NY ≫ non-union TX | Primary |
| **Delivery vehicles** | Vans at $45–65k, 5-yr depreciation | Low | Primary |
| **Fuel and energy** | Van fuel, warehouse power | Medium — regional prices | Primary |
| Building fitout | Racking, IT, security | Low–medium | Secondary |
| Hiring (one-time) | Recruitment, checks, training | Medium | Secondary |
| Permitting | Building and operating permits | **High** — CA/NY ≫ TX/FL | Secondary |
| Marketing activation | Signing up local subscribers | Low | Secondary |

The four primary buckets account for roughly **75%** of the variation in total
capital. That is why Figure 8 in the proposal is a sensitivity plot: **you do not
need all eight to be accurate — you need the two that dominate.**

> **Example of why metro variation matters.** The same delivery station costs
> dramatically more to operate in the Bay Area than in Austin — mostly
> lease and wages. A model using one national average cost will systematically
> recommend expensive metros and reject cheap ones, for entirely artificial
> reasons.

---

## 1.5 Route density — the single most important idea in last-mile economics

If you understand nothing else about the cost side, understand this.

**The claim:** the cost of delivering a package falls as the number of deliveries
*in the same area* rises — and it falls in a specific, predictable way.

### Why, intuitively

> **Example.** A van has 100 packages for a neighbourhood.
> - **Sparse case:** those 100 addresses are spread over 100 km². The driver
>   averages maybe 1.5 km between stops. Most of the day is *driving*.
> - **Dense case:** those 100 addresses are in 10 km². Average 400 m between
>   stops — sometimes the same apartment building. Most of the day is
>   *delivering*.
>
> Same 100 packages. Same van. Wildly different cost per package.

### The maths, gently

Beardwood, Halton and Hammersley (1959) proved something elegant: if you drop
*N* random points in an area *A*, the shortest tour visiting all of them grows
like

```
        tour length  ≈  k · sqrt( N · A )
```

Divide by *N* to get distance **per stop**:

```
        per-stop distance  ≈  k · sqrt( A / N )  =  k / sqrt( δ )
```

where **δ = N/A** is *delivery density* — stops per unit area.

Daganzo (1984) extended this to capacity-constrained delivery with vehicles that
must return to a depot.

> **What `1/sqrt(δ)` means in practice.** Quadruple the density and per-stop
> distance halves. Not "a bit better" — *halves*. This single relationship
> is why operators cluster facilities and why the order in which you activate
> ZIPs matters.

### The consequence that drives our portfolio argument

Because cost depends on the density of *everything the van serves* — not
just one ZIP — **activating two adjacent ZIPs together is cheaper per
package than activating either alone.** Hold that thought; it returns in
Part 5.

---

## 1.6 Cannibalization — why more orders is not more money

**Definition:** when a new offering takes revenue from your existing offering
instead of generating new revenue.

> **Example.** Before same-day launches in a ZIP, a household orders 8 items a
> month on 2-day shipping. After launch they order 9 items a month, all
> same-day.
>
> A naive read: "same-day generated 9 orders!" **Wrong.** Same-day generated
> **1 genuinely new order** and *converted* 8 existing ones to a more expensive
> fulfilment method.
>
> If same-day costs $2 more per order to fulfil, the operator just spent $16 to
> earn one incremental order. That can easily be a loss.

**Why this is the crux of the whole proposal:** the profitability of a ZIP
depends on the *incremental* fraction, and incrementality is invisible in raw
order counts. You need a **counterfactual** — what would have happened
without the launch — and that requires causal inference (Part 3).

### The spillover that breaks standard methods

Cannibalization does not stop at the ZIP boundary.

> **Example.** Same-day launches in Berkeley (94704) but not neighbouring
> Emeryville (94608). An Emeryville resident works in Berkeley and now has a
> same-day-eligible delivery address at the office. Their household ordering
> pattern shifts. **Emeryville's numbers move despite Emeryville never being
> "treated."**

This is called **interference** or a **SUTVA violation**, and it is the reason
Part 3 exists.

> **Status check before you read Part 3.** Part 3 describes the project's
> *second* estimand - the spatial difference-in-differences and synthetic
> control study of cannibalisation. **None of it has been built.** The only
> cannibalisation in the codebase is an assumed penalty in the portfolio
> optimiser: a 20 km radius and a 0.18 peak, saturating with neighbour exposure
> (`src/siting_atlas/optimize/params.py`). That is a number somebody chose. It
> has no standard error. Part 3 opens with the same warning in a box.

---

## 1.7 Why anyone outside the company should care

This is the section that turns a business-school exercise into a public-interest
project, and it is the answer to "so what?"

### The tax-abatement problem

Cities routinely offer tax breaks — often millions — to attract
logistics facilities: jobs, tax base, prestige.

**The question a council cannot answer:** *would the company have built here
anyway?*

> **Example.** A council is asked for a $2M abatement. If the operator's own
> model already ranks that site in the top decile — good highway access,
> cheap industrial land, dense customers nearby — then the facility was
> coming regardless. **The $2M is a pure transfer** from the public to a
> trillion-dollar company, in exchange for nothing.
>
> If the site is marginal, the abatement genuinely changes the decision, and the
> council should negotiate on that basis.

**A working selection model answers this directly.** The selection equation in
§4.5 produces, for every ZIP, a propensity — the probability the operator would
build there. Read forwards it is a prediction. **Read backwards it is the
abatement counterfactual.** Same number, opposite use.

> **Ours cannot be used this way today, and you must say so.** Neither model
> the project has fitted can carry an abatement argument, and they fail for
> different reasons.
>
> The **retired hazard model** could not, because the argument needs a
> *calibrated probability* and its calibration was the thing that broke:
> expected calibration error 0.00863 against the constant null's 0.00005, which
> is 170 times worse than a model with no inputs. Ranking at AUC 0.6894 is not
> nothing, but "this site is in the top decile" is a much weaker claim to take
> to a council than "the probability is 0.71, plus or minus".
>
> The **current choice model** cannot either, and the reason is blunter. It
> *can* now complete the sentence "plus or minus" — inference landed on
> 2026-09-14 — and what it says is that the only parameter doing any work is
> **not distinguishable from the null**. The relevant null here is beta = 1,
> not beta = 0, because households is fixed at 1 as the numeraire and only
> ratios are identified; beta = 1 therefore means "worth exactly one household,
> and the model cannot tell them apart". The sandwich interval is [0.734,
> 2.835] with p = 0.287, and the bootstrap over decisions, the bootstrap over
> metros and the BCa interval all cover 1.0 as well. Worse, on held-out
> decisions the model is merely matched at top-1 and top-10 by a raw Census
> count of warehousing establishments (see the correction block in Sec. 1.0),
> so a council asking "would they have built here anyway?" would get an
> equally good answer by downloading County Business Patterns as by using our
> model — and get it for free, with nothing to estimate and nothing to defend.
>
> The *use case* is what justifies continuing the project. The *instrument* is
> not ready. Keep those two sentences apart and you can make this argument
> honestly; merge them and you are overselling a model to a city council, which
> is the worst version of this work.

### The environmental-justice problem

Warehouses generate diesel truck traffic, which generates particulate matter and
nitrogen oxides, which generate asthma. Research (METRANS; Urban Freight Lab;
GWU Milken School) documents that warehouse siting correlates with lower-income
communities and communities of colour — a "spatial and racial mismatch
between delivery supply and demand."

**The timing problem:** community groups typically learn about a facility when
the **permit is filed**, which is very late. Objections at that stage are
expensive and rarely succeed.

> **What a forecast changes.** If a community organisation knows in advance that
> their area is in the top decile of predicted expansion, they can engage during
> *zoning* rather than *permitting* — months earlier, when outcomes are
> still genuinely open.

### The regulatory problem

**South Coast AQMD Rule 2305**, the Warehouse Indirect Source Rule (adopted 2021,
approved by the US EPA), requires warehouses ≥ 100,000 sq ft to earn
emission-reduction points or pay mitigation fees. Other regions are considering
equivalents.

A district operating such a rule needs to know **how much warehouse development
is coming** in order to plan mitigation capacity. That is a forecasting problem,
and there is no public forecast.

---

## 1.8 Why now — three things that just became true

**1. Unstructured intelligence became cheap to process.** Press releases, permit
filings and local news can now be parsed into structured facility records at
near-zero marginal cost. Five years ago that was a manual research job.

**2. Spatial causal inference became runnable.** Synthetic control and spatial
estimators that once needed specialist software now run on a laptop in standard
packages.

**3. The regulatory environment changed.** Rule 2305 is the first EPA-approved
indirect source rule targeting warehouses. It creates institutional demand for
exactly the forecast this project produces. That demand did not exist in 2019.

---

## 1.9 What "operator-consistent expansion desirability" means

You will see this phrase throughout the proposal. It is a precision device, and
you should be able to explain why it is there.

**The naive claim would be:** *"This model predicts where same-day delivery is
economically viable."*

**Why that is wrong:** we train the model on where the operator *actually built*.
Those choices reflect the operator's own criteria, constraints, mistakes and
internal politics — not some objective viability. If they systematically
avoid a certain kind of neighbourhood for reasons unrelated to profit, the model
learns that avoidance and reproduces it.

**So the honest claim is:** *"This model predicts what the operator's revealed
preference implies for areas they have not yet reached."*

> **Example of why the distinction is not pedantic.** Suppose the operator has
> historically avoided a demographic profile for reasons unrelated to demand.
> The model will rank those areas low. A naive reading says "not viable." The
> correct reading says "**consistent with what the operator has done before**"
> — which is exactly the kind of pattern an equity audit should surface,
> not launder.

This is why §4.5.5 stratifies results by demographic group and flags strata where
the model is less reliable.

---

## 1.10 Part 1 self-check

If you can answer these without looking, move on to Part 2.

1. Why is same-day delivery a *different building problem* from 2-day, not just
   a faster version of it?
2. What is the difference between a ZIP code and a ZCTA, and why does it matter?
3. State the MAUP in one sentence and give an example.
4. Why does per-stop distance scale as `1/sqrt(density)`, and what does that
   imply about activating adjacent ZIPs?
5. A ZIP shows 9 orders/month after launch, up from 8. Why might that be a
   financial loss?
6. What is a SUTVA violation, in delivery terms?
7. How does a selection propensity score answer a tax-abatement question — and
   give the *separate* reason each of our two models fails to supply one (the
   retired hazard model's calibration; the current choice model's missing
   intervals).
8. Why do we say "operator-consistent desirability" instead of "demand"?
9. The ZIP is the natural unit of *observation*. Why is it not the natural unit
   of *decision*; what are the three numbers (median, mean, largest) that prove
   it; and which assumption in Train (2009) does it break — name the section
   and say what the failure is called.
10. State the current headline result from memory: the held-out top-1, top-5
    and top-10 counts for the fitted choice model against the raw
    warehousing-establishment count, and say what those four numbers imply
    about what the estimation bought. Then state, separately, the retired
    hazard model's AUC, its calibration comparison, and its events-per-parameter
    figure against the floor — and say why it is retired.

---

**Next:** `HANDBOOK_02_DATA.md` — every data source, what it contains, how to
get it, and what will go wrong.
