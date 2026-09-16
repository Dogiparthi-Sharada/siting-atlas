# Glossary

**Every technical term in the project, defined in plain English, with an example.**

Ordered by theme rather than alphabetically, because the terms make more sense
in groups. Use Ctrl-F for a specific one.

---

## 1. Logistics and the domain

**Last mile**
The final leg of a delivery — from the local depot to your door. Named
because it is short in distance but roughly half the total shipping cost, since
one van visits one address at a time.

**Fulfilment centre (FC)**
The giant warehouse, often 800,000+ sq ft, holding millions of items. Feeds
everything downstream.

**Sortation centre (SC)**
A mid-size hub that sorts packed orders by destination.

**Delivery station (DS)**
The last building before your door, typically 100–200k sq ft. Vans load here.
**This is the last-mile node** and mostly what we are predicting.

**Same-day centre (SDC)**
Small and close to customers, holding the most popular ~100k items so they can
reach a door within hours.

> **Example — one order.** A phone case ordered at 9am ships 2-day from an FC
> 300 miles away via an SC and a DS. Ordered same-day, it comes from an SDC 12
> miles away, straight to a van.

**Node**
Any of the above. We use it when the building type doesn't matter.

**Drop density**
Deliveries per unit area. The single most important driver of last-mile cost.

**Stem distance / stem cost**
The drive from the depot out to the neighbourhood, before any package is
delivered. Pure overhead.

**Circuity factor**
How much longer the road route is than a straight line — used as a cheap
substitute for exact routing. Commonly quoted as about 1.35 in US metros; **this
project runs at 1.30**, which is the value recorded in `cost_report.json`. Quote
1.30 if you are asked what the model uses.

---

## 2. Geography

**ZIP code**
A postal *route*, not a shape. Some ZIPs are a single building or a PO Box
cluster with no area at all.

**ZCTA (ZIP Code Tabulation Area)**
The Census Bureau's polygon approximating each ZIP, so demographic data can be
attached. About **33,000** in the US. This is our unit of analysis.

**Census block group / tract**
Smaller official statistical areas. Block groups nest inside tracts; both nest
inside counties. Used where a source is finer-grained than ZCTA.

**Centroid**
The geometric centre of an area — used as its representative point for
distance calculations.

**Shapefile / TIGER/Line**
The Census Bureau's official boundary files.

**Spatial join**
Combining two datasets by geography rather than by an ID — "which ZCTA
contains this facility?"

**Crosswalk**
A lookup translating between two geographic systems or two vintages of the same
one.

**Vintage**
Which year's boundary definitions you are using. Mixing vintages silently
corrupts a time series, which is why we pin one.

**H3**
A hexagonal grid system covering the globe. We re-run conclusions on it to check
they are not an artefact of ZIP boundaries.

**MAUP (Modifiable Areal Unit Problem)**
Statistical results change when you redraw the boundaries, even though the
underlying reality hasn't.

> **Example.** Six households earning `40k, 40k, 40k, 120k, 120k, 120k`. Group
> them `[40,40,40]` and `[120,120,120]` and you see two very different areas.
> Group them `[40,40] [40,120] [120,120]` and you see three similar ones.
> Nothing changed but the lines on the map.

---

## 3. Causal inference

**Counterfactual**
What would have happened if the thing hadn't happened. Never observable —
manufacturing a credible one is the whole discipline.

**Fundamental problem of causal inference**
For any unit you see either the treated outcome or the untreated one. Never
both.

**Treated / control (donor)**
Units that got the intervention, and comparison units that didn't.

**Selection bias**
When who gets treated is related to the outcome, so a naive comparison measures
the selection rather than the treatment.

> **Example.** Patients in intensive care die more often than patients who
> aren't. Intensive care doesn't kill people — **sicker patients get sent
> there.**

**Heckman two-step / correction**
A method for selection bias: model *who gets selected* first, then include a
correction term in the outcome model.

**Inverse Mills ratio**
The correction term from that first step. Loosely: "how surprising is it that
this unit was, or wasn't, selected?"

**Instrument / instrumental variable**
Something that affects *whether you're treated* but doesn't affect the outcome
except through treatment.

**Exclusion restriction**
The assumption that the instrument has no direct effect on the outcome.
**Not testable — it is an argument, and ours is contestable.**

**First-stage F-statistic**
Tests whether the instrument actually predicts selection. Convention: above 10.

**DiD (difference-in-differences)**
Compare the *change* in the treated group to the *change* in the control group.
The control's change is the trend both would have had anyway.

**Parallel trends**
DiD's key assumption: absent treatment, both groups would have moved together.
Untestable after treatment; you check it beforehand and show the plot.

**Synthetic control**
Build the comparison unit as a weighted blend of untreated units, chosen so the
blend tracks the treated unit *before* treatment.

> **Example.** No single city compares to San Francisco. But
> `0.4 × Seattle + 0.3 × Boston + 0.2 × Austin + 0.1 × Denver` might reproduce
> its pre-launch trajectory. That blend is "Synthetic San Francisco"; the gap
> afterwards is the estimate.

**Donor pool**
The untreated units eligible to enter the blend.

**Placebo test (in-space / in-time)**
Pretend an untreated unit was treated, or that treatment happened earlier than
it did, and run everything again. You should find nothing. Doing this for every
unit builds a null distribution from your own data.

**RMSPE ratio**
Post-treatment error divided by pre-treatment error. Stops units that simply fit
badly from looking like large effects.

**SUTVA (Stable Unit Treatment Value Assumption)**
Treating one unit doesn't affect another. **Plainly false in delivery networks.**

**Interference / spillover**
The violation of SUTVA — the effect leaking into neighbours.

**Staggered adoption**
Units treated at different times, which lets later-treated units act as controls
for earlier ones.

**Spatial weight matrix (W)**
A table saying which areas count as neighbours of which. Usually assumed from
shared borders.

> **A claim withdrawn.** This entry used to end "we estimate it from the
> measured decay instead", in the present tense. **That is false.** There is no
> weights matrix `W` anywhere in `src/`, and no decay curve was ever estimated.
> Estimating `W` from a measured decay is the *design* (see the Explainer §3);
> nothing has been built. What the codebase actually contains is a fixed 20 km
> radius with a 0.18 peak in the portfolio optimiser — a hand-picked assumption
> of exactly the kind this entry was complaining about. Every other file in this
> pack flags that; this one did not, and now does.

**Distance-band / ring estimation**
Estimating the effect separately at 0–8 km, 8–20 km, 20+ km, giving a decay
curve rather than one number.

> **The band edges are ILLUSTRATIVE.** 0–8 km, 8–20 km and 20+ km are a worked
> example of the *shape* of the design, not measured breakpoints. No ring
> regression has been run in this project, so there is no measured decay and no
> estimated 8 km band. This pack's own rules require illustrative figures to be
> labelled wherever they appear; this entry previously was not.

**Cannibalization (θ)**
The fraction of apparent new business that was actually taken from your existing
business.

> **Example.** A household goes from 8 orders/month on 2-day to 9 on same-day.
> That is **1 new order and 8 switched**, not 9 new ones.

**Generated regressor**
A variable that was *estimated* (e.g. extracted from text by a model) but is then
used as if measured exactly. Understates standard errors.

---

## 4. Models and statistics

**Discrete-time hazard model**
Asks, for each period: given this hasn't happened yet, what's the chance it
happens now? Chain them for a probability over time.

> **Example.** Quarterly hazards of 0.04, 0.06, 0.09, 0.11 give
> `1 − (0.96 × 0.94 × 0.91 × 0.89) ≈ 27%` within a year.

> **Status in this project: RETIRED / SUPERSEDED.** This was the specification
> for siting. It was built, fitted on the real 43-building panel, and **it
> failed** — AUC 0.6894, Brier skill +0.0047, calibration 170 times worse than
> a constant, negative skill on both hold-outs. Artefact
> `outputs/metrics/hazard_report.json`, current run `20260914-002509-2374`. The
> diagnosis is **clustering**: one station switches on a median of 58
> ZCTA-quarters at once, so the rows are not independent observations and the
> likelihood Train writes at §3.7.1 p. 61 does not apply. It has been superseded
> by the conditional ZCTA choice model — see **McFadden rho-squared** and
> **top-k accuracy** below. See `HANDBOOK_04_MODELS.md`.

**Censoring**
When you stop observing before the event happens. A ZIP not yet enabled isn't a
"no" — it's a "not yet", and hazard models handle that correctly.

**Time-varying covariate**
An input that changes over the panel, used at its value *as at that period*.

**Poisson / negative binomial regression**
Models for counts. Negative binomial allows variance to exceed the mean, which
real count data almost always does.

**Over-dispersion**
More variability than a simple model expects.

**ZINB (zero-inflated negative binomial)**
A mixture of "will this ever be non-zero?" and "if so, how much?"

**Structural vs sampling zero**
A structural zero can *never* be positive; a sampling zero happened to be zero
this time.

> **Example.** Counting fish caught: a visitor who didn't fish is a structural
> zero; one who fished and caught nothing is a sampling zero.

**LightGBM**
A gradient-boosted tree model. Used as a non-parametric benchmark — if it
ranks the same areas highly as our parametric model, the ranking isn't an
artefact of functional form.

**SHAP**
Breaks a single prediction into per-feature contributions.

> **Example.** "Probability 0.72. Baseline 0.31. Income +0.14, distance to
> nearest facility +0.19, density +0.11, competitor −0.03."

**Huff gravity model**
Attraction rises with facility size and falls with distance, relative to
competitors. We fix the distance exponent at 2.0 rather than fitting it, so
nobody can say we tuned it.

**Changepoint detection**
Scanning an ordered series for the point where its statistical behaviour shifts
— a jump in the mean, say — and calling that the moment something happened. It
is the standard way to turn a time series of satellite images into a
construction date: bare land and a finished roof have different reflectance, so
the changepoint in a vegetation or brightness index should be the build.

> **Example — ours, and it is a NEGATIVE RESULT.** The reasoning was sound. OSHA
> gives an *upper* bound on an opening date; Sentinel-2 imagery should give a
> *lower* bound; upper plus lower is an interval the statistics could use (see
> **interval censoring**). The script is
> `data/collection/satellite/colab_date_from_satellite.py`, run in Google Colab.
> The source artefact is `satellite_dates.csv`, which sits **outside this
> repository**.
>
> ```
>    107 of 107   sites got an estimate; median 106 cloud-free scenes
>    41%          of the 83 sites with a known year came within 1 year
>    3.42 years   standard deviation of the error
>    36%          39 of the 107 estimates are LOGICALLY IMPOSSIBLE:
>                 they date construction AFTER the day an OSHA
>                 inspector found the building operating, by a
>                 median of 33 months
> ```
>
> The confidence score does not discriminate — 35% impossible above confidence
> 2, against 30% at confidence 1-2 — so filtering on it changes nothing. The
> cause is the **changepoint detector**, not the imagery. **Do not present the
> 68 surviving estimates as dates.** They are the residue of a procedure that is
> demonstrably wrong a third of the time and nothing distinguishes them from the
> 39 that are provably wrong.

**Margin of error (MOE)**
The uncertainty the Census publishes with every estimate. Routinely ignored; we
carry it through.

---

## 4a. Discrete choice and partial identification

**The vocabulary of where the project went next.** These terms exist because
the hazard model failed and the diagnosis came out of the discrete-choice
literature. An examiner who asks "what went wrong and what replaces it" is
asking for these words, so learn them in this order — they build on each
other. The replacement is no longer hypothetical: the conditional choice model
is fitted, and its result is in **top-k accuracy** below.

**Choice set**
The list of alternatives a decision maker actually chose *between*. Train
(2009) §2.2 puts three requirements on one: the alternatives must be
**mutually exclusive** from the decision maker's perspective, the set must be
**exhaustive**, and the number must be **finite**. Train notes the first two
are "not restrictive" because you can usually define your way out of them,
while finiteness is genuinely restrictive and is "the defining
characteristic of discrete choice models".

> **Example — ours, and what §2.2 is and is not for.** We treated every
> ZCTA-quarter as an alternative. But a delivery station switches on *every*
> ZIP within a fifteen-mile catchment at once: on our panel the median station
> covers 58 ZIPs, the mean 88, the largest 307. So "Amazon chose ZIP 60608 in
> 2021Q2" is not a choice — it is one of 88 simultaneous consequences of one
> choice. Our 812 ZIP-quarter events were 43 real decisions wearing geometry as
> a disguise.

> **A citation withdrawn, and the argument improves.** This entry, and several
> siblings, used to say that the hazard model failed because **mutual
> exclusivity** failed, per Train §2.2. **That is the wrong section.** §2.2
> governs a choice set facing a *decision maker*, and a hazard on
> ZCTA-quarters has no decision maker choosing among those rows, so exclusivity
> is not a property they can have or lack. Worse for the old rhetoric, Train
> calls the criterion "not restrictive" and says "Appropriate definition of
> alternatives can nearly always assure that the alternatives are mutually
> exclusive" (p. 12), then supplies a two-line repair — so citing §2.2 handed a
> reader of Train an easy rebuttal. The assumption actually violated is
> **independence across observations**, Train §3.7.1 p. 61, and the standard
> name for the failure is **clustering** or **pseudo-replication**. It has no
> two-line repair; the only fix is to change the unit of analysis. See
> `../research/NOTES_train_ch03_logit.md` §6.2. **§2.2 stays in this glossary
> because it is the right authority for building the *successor* choice set**,
> which is what the next entry describes.

**Conditional choice set**
A choice set defined *given* something else has already happened, so that the
remaining alternatives really are exclusive.

> **Example — the reframe.** Instead of "did ZIP *z* get enabled in quarter
> *t*", ask "**which** ZIP does the station go in, **conditional on** a
> station opening in metro *m* in period *t*". Exactly one ZIP wins each
> time, so the alternatives are exclusive by construction, the set is
> enumerable, and the count of decisions drops from 812 to 43 on the pilot
> frame. Smaller and honest beats larger and fictional.

> **Status: BUILT AND FITTED.** This is no longer a proposal. The delivered
> model is a conditional ZCTA choice model on the **national** frame — the
> artefact's first key is `"frame": "national"` — with **94** decisions, 56 for
> training and 38 held out, seed `20260914`, three free parameters, converged.
> Artefact `outputs/metrics/choice_report.json`. Its held-out result is in
> **top-k accuracy** below, and it is not a flattering one.

**IIA (independence of irrelevant alternatives)**
A property of the plain logit model: the ratio of the probabilities of any
two alternatives does not depend on what *other* alternatives are available.

> **Example — the classic one.** If you choose a blue bus over a car 50:50,
> IIA says adding an identical red bus leaves the blue-bus-to-car ratio at
> 1:1, giving 33% each. That is wrong — the two buses should split the bus
> share, leaving 50% car and 25% each bus. Whenever two alternatives are close
> substitutes, IIA misbehaves.

Why it matters to us twice over. IIA is what licenses Train §3.7.1's result
that **a logit can be estimated on a random subset of alternatives without
inconsistency** — useful if we end up with a choice set of hundreds of ZIPs
per metro. But it is a *logit-only* result: it does not survive to a probit
or a mixed logit. And it does not rescue our original problem, because that
machinery presupposes you can enumerate the full set. Our problem was not
"too many alternatives"; it was "these were never alternatives."

**Revealed preference**
Inferring what a decision maker values from what they actually did, rather
than from what they say or from a survey. The core idea: if the firm chose
configuration A when B was available, A must have looked at least as good.

> **Example.** Amazon put a station in Sumner rather than in a ZIP fifteen
> miles east. You do not need Amazon's spreadsheet to learn something from
> that — you only need to believe the firm was not choosing at random.

**Moment inequality**
A statistical condition of the form "this expectation is **greater than or
equal to** zero", rather than the usual "equals zero". Revealed preference
naturally produces inequalities, because "A was at least as good as B" is an
inequality, not an equation.

> **Example — how Holmes and Houde et al. build them.** Take the facilities
> the firm actually opened and construct counterfactual deviations by
> **swapping opening dates** between pairs of them. If the real schedule was
> profit-maximising, its profit must be at least that of each swap. Each swap
> contributes one inequality. Holmes uses 522,967 deviations from 3,176 store
> locations.

**Partial identification**
Accepting that the data pin the parameter down to a *range* rather than a
single value, and reporting the range honestly instead of adding assumptions
until a point pops out.

> **Example.** "Fixed cost per station is somewhere between $2.1m and $4.8m"
> is a partially identified answer. "$3.4m" is a point estimate, and if it
> only exists because you assumed a distribution you cannot defend, the range
> was the better answer.

**Identified set**
The actual range that partial identification delivers: the set of all
parameter values consistent with the data and the maintained assumptions.

> **Careful.** A confidence interval built around an identified set is an
> interval for the *extreme points of the set*, not for the true parameter,
> and Holmes flags in his §8.1 that uniformity was not addressed. And a
> **tight** identified set is not automatically good news — Molinari's §5
> warns that a misspecified model can produce a narrow set, which is the
> failure mode you would not notice.

**Numeraire**
The one quantity you *fix* so that everything else can be read as a ratio
against it. Borrowed from economics, where prices are only meaningful relative
to something.

> **Why a choice model forces you to have one.** A conditional choice model is
> **scale invariant**: multiply every alternative's attraction index by the same
> positive constant and every choice probability is unchanged, because the
> constant cancels top and bottom in the share. So the data can never pin down
> the absolute level of the coefficients — only their *ratios* are identified.
> If you try to estimate all of them freely, the likelihood has a ridge rather
> than a peak and the optimiser wanders along it.
>
> **Ours.** `households` is fixed at **1.0** and is not estimated;
> `choice_report.json` records `"numeraire": "households"`. Everything else is
> read against it. `warehousing_establishments` comes out at **1.4428**, i.e.
> one warehousing establishment pulls about 1.44 times as hard as one
> household — a *ratio*, and the only kind of statement the model can support.
> The implementation parametrises `beta = exp(theta)` so the attraction index
> stays positive.
>
> **The catch, and volunteer it.** The other two coefficients came back at
> `3.04e-16` and `4.72e-16`, which is a numerical zero — they are **at the
> boundary** of the parameter space. One free parameter of three is doing any
> work at all, and boundary solutions are also what makes the standard-error
> story below unfixable.

**Boundary solution**
A parameter estimate that comes to rest at the edge of its allowed range rather
than at an interior peak. Exponentiating, as we do, puts the edge at zero.

> **Why it matters more than it looks.** Almost every textbook standard error
> assumes an *interior* maximum where the gradient vanishes. At a boundary the
> gradient need not vanish, so those asymptotics simply do not apply. See
> **sandwich versus bootstrap standard errors**.

**Interval censoring**
When you do not observe *when* an event happened, only that it happened
somewhere inside a window. Distinct from ordinary right-censoring, where you
know the event has not happened *yet*.

> **Example — ours, and why this is the specification the data calls for.**
> Most of our facility dates are the day OSHA opened an inspection case at the
> address. That proves the building was operating *by* then. So the opening
> happened somewhere in the interval `(panel start, X]`. Treating `X` as the
> opening date fabricates an event time. We measured how loose that interval
> is against five addresses whose true opening month is independently known:
> the bound held 5 times out of 5, and the lags were **4, 13, 57, 69 and 345
> months**. One site opened in 1997 and was first inspected in 2026.
>
> The bound is *correct* and frequently *uninformative*. Interval censoring is
> the honest way to consume it, and **it is not implemented**: no artefact in
> `outputs/metrics/` reports an interval-censored fit. (This entry used to cite
> `../STATUS.md` as the authority for that. Cite the absence of the artefact
> instead — a prose status page can go stale, a missing artefact cannot.)
>
> **And the attempt to supply the missing lower bound failed.** The plan was to
> date construction from Sentinel-2 imagery, giving an interval instead of a
> bound. It ran on 107 sites and **36% of the estimates are logically
> impossible** — they date construction *after* the day an OSHA inspector found
> the building operating, by a median of 33 months. See **changepoint
> detection**.

---

## 4b. Research design — the vocabulary added on 2026-09-15

**These six terms did not exist in this glossary before 2026-09-15.** They
were added because the project ran a pre-registered test, lost it, and the
losing is now a large part of what there is to defend. An examiner who asks
"how do I know you did not choose the framing after seeing the answer" is
asking for this section.

**Pre-registration**
Writing the hypothesis, the sample, the covariates, the baselines, the metric
and the success criterion to disk **before** fitting anything, with a
timestamp, so that no later choice can be mistaken for a prediction. The
point is not honesty as a virtue; it is that *choosing* is itself a
parameter, and a parameter fitted after seeing the answer has no error bar.

> **Example — ours, and it is the real thing rather than a gesture.**
> `docs/PREREG_METRO_MODEL.md`, written 2026-09-15 before the metro-level
> entry model was fitted. `outputs/metrics/metro_entry.json` records the file
> path and its md5, `946f7ef75db69e5278eea409a04c3823`, so the document that
> was registered can be checked against the document on disk. The prereg
> wrote **both** outcomes' language in advance (§7), fixed the universe at
> all 935 CBSAs rather than the 195 with a known opening (§8.2, "selection on
> the outcome"), named five invalidating conditions, and gave a numeric
> success criterion (§9). The outcome was **H0** — the hypothesis lost — and
> the paragraph reporting it is the paragraph the prereg had already written.
>
> The evidence that this was not theatre: the prereg also predicted that
> county-grain covariates would work at metro grain, and the run's own
> vintage check killed eight of the twelve covariates before they could be
> tested. `NOTES_METRO_ENTRY.md` §12 lists three places the prereg is
> **wrong** and says the run was executed as written anyway.

**Vintage check (vintage gate)**
Refusing any covariate whose published *vintage* is at or after the period
being predicted, whatever its column name says. Distinct from an ordinary
leakage guard, which usually just lags a value by a fixed number of periods:
a vintage check asks what data actually went into the number.

> **Example — ours, and it was the largest single thing in the metro run.**
> `NOTES_METRO_ENTRY.md` §8. Enforcing the prereg's own §4 rule removed **8
> of the 12** registered covariates, and two more failed a 90% coverage
> floor. The reason is structural: most panel columns are not time series at
> all. Mean distinct values per unit across all 32 quarters of
> `panel.parquet` is **1.00** for population, households, income, traffic
> proximity, diesel PM, both wage columns and metro employment — one value,
> broadcast to every quarter. ACS 5-year 2023 is built from responses
> collected 2019-2023, so using it to predict 2020 puts three of its five
> collection years *after* the outcome. Only `permit_units_total` moves at
> all, at 4.97 distinct values.
>
> What survived into the verdict arm was two covariates. That is a weakness
> and `NOTES_METRO_ENTRY.md` §11 says so in those words.

**Within-metro coefficient of variation — "the dispersion rule"**
A candidate covariate's standard deviation divided by its mean, computed
*inside* one metro's choice set and then averaged over metros. A conditional
choice model compares alternatives within a choice set and differences away
everything between choice sets, so this number — not the covariate's real-world
importance — is the whole of its usable currency.

> **Example — ours. This is the most transferable thing the project produced
> and it is ALSO the claim most often overstated in this repository. Learn
> the honest version; the overstated one is checkable in one command.**
>
> Measured over **21** network terms across 41 large metros (8,271 candidate
> ZCTAs), `outputs/metrics/gravity_network.json`, `terms.dispersion`,
> run `20260915-210603-b780`. Re-read directly off that artefact on
> 2026-09-15:
>
> ```
>   within-metro cv                  n    outcome
>   ------------------------------------------------------------------
>   below 0.6                        7    7 of 7 land on the boundary
>   between 0.6 and 1.3              0    the region is EMPTY
>   above 1.3                       14    8 interior, 6 NOT
>   ------------------------------------------------------------------
>                                   21
> ```
>
> **What survives, and say only this.** *Low within-metro dispersion is
> sufficient for failure — 7 of 7 — and nothing at all lands between 0.60 and
> 1.40. High dispersion is necessary but not sufficient: 6 of the 14 terms
> above the line still fail.* It is a **screening rule for rejection**, not a
> predictor of success, and it costs seconds to run before any model exists.
> Below about 0.6, do not bother.
>
> > **CORRECTED 2026-09-15 — this entry, several research notes and
> > `docs/PREREG_METRO_MODEL.md` §2 all render the rule as "21 of 21 fail
> > below 0.6, 21 of 21 work above 1.3, nothing in between". That wording is
> > wrong twice.** First, there are 21 terms in total, not 21 on each side, so
> > the two lines together imply 42 observations that do not exist. Second and
> > more seriously, **the upper half has counter-examples**:
> > `sortation_gravity_count_sqft_subset_a2` sits at cv **5.2999**, four times
> > the threshold, and its coefficient's interval still contains the boundary.
> > On the current artefact five more join it —
> > `sortation_gravity_sqft_a2` (5.3063), `sortation_gravity_count_sqft_
> > subset_a3` (8.2282), `sortation_gravity_sqft_a3` (8.2920),
> > `sortation_proximity` (1.3993), and `fulfilment_proximity` (1.4418) which
> > is interior in one arm and not in another.
> >
> > The note that states the rule contradicts itself on this point:
> > `NOTES_GRAVITY_NETWORK.md` §3.1 says *"all but one of the twelve alpha >= 2
> > columns are strictly interior"* and its §5 then says the outcome tracks
> > dispersion *"without an exception"*. §3.1's "one" **is** §5's exception,
> > and §5's summary table prints 13 of the 21 columns with the
> > counter-example among those omitted. An examiner reading both sections
> > will find this. Do not say "without exception".
> >
> > The empty region is real and is the strong part of the result. Lead with
> > it.
>
> **Why it is more than a correlation.** Eighteen of the 21 terms are gravity
> measures at three settings of an exponent `alpha`, a knob that changes
> nothing about what is being measured — still proximity to the same
> facilities — and changes only how sharply the measure discriminates
> *within* a metro. Following **one** column across the knob:
>
> ```
>   fulfilment_gravity_count   a1 0.2975  ->  a2 4.3630  ->  a3 6.8194
>   sortation_gravity_count    a1 0.4427  ->  a2 5.4917  ->  a3 8.5046
> ```
>
> Both walk the coefficient from the boundary to the interior, and that
> isolates the grain mechanism from every other property a column could have.
> *(Do not quote "0.30 to 8.50" as one column's walk — 0.2975 is a fulfilment
> term and 8.5046 is a sortation term, so that pair crosses facility types.
> The two rows above are the like-for-like walks.)*
>
> `alpha = 0` was deliberately not run, and the reason is worth knowing:
> `(1+d)**0 == 1`, so the term becomes the total number of open facilities —
> identical for every ZCTA in the country at a given vintage, carrying
> exactly zero within-choice-set variation. It is not a weaker test; it is
> not a test.
>
> It also explains, retrospectively, the one failure that had no
> explanation: `network_within_50mi` sits at cv **0.5918**, just under the
> line, which is why a *count* inside a radius failed at 25, 50 and 100 miles
> while a *distance* to the same facilities worked. The radius was never the
> issue. See `../research/COVARIATES_TRIED.md` §1.2b.

**Densification**
Building inside territory you already serve, rather than into unserved
territory. The opposite of "white space" expansion, and the mechanism that
turned out to tie three of this project's failures together.

> **Example — ours.** `outputs/metrics/white_space.json`, read directly on
> 2026-09-15: at a 45-mile catchment, **75.9%** of 2024-25 delivery-station
> openings in the `real`-coordinate arm land inside coverage the pre-2024
> network already had (79 openings scored), and **68.7%** in the
> `real_plus_fallback` arm (131 openings). So the defensible band is
> **69-76%**. At the project's working 15 miles it is 67.1% and 57.3%.
> Median distance from a 2024-25 opening to the nearest facility that already
> existed in 2023: **7.5 and 10.1 miles**.
>
> > **CORRECTED 2026-09-15.** Several documents in this repository — the
> > prereg §4, `NOTES_METRO_ENTRY.md` §9, `NOTES_WHITE_SPACE.md` and the
> > earlier draft of this entry — quote the band as **"67-77%"**. That was
> > correct for the artefact as it stood earlier on 2026-09-15 and is not
> > correct for the file at that path now: 46 delivery stations were
> > re-geocoded (455 real coordinates to 501), which moved the `real` arm to
> > 75.9% on 79 openings and the fallback arm to 68.7% on 131. The
> > substantive claim is unchanged and the band moved by about one point in
> > each direction. Say "roughly seven in ten" if you are quoting from
> > memory.
>
> "Already-served" has a precise and restrictive definition that must travel
> with the number: a ZCTA is covered when its **centroid** is within the
> radius in **straight-line** miles of at least one facility — not drive
> time, not a road buffer, not a polygon intersection — and the pre-2024
> network excludes every facility opened after 2023 **and every undated
> facility**, which drops 504 of them in the `real` arm.
>
> **Three findings the mechanism unifies**, and be careful how you phrase
> this: only the third is a *failure*. (1) A raw warehouse count matches the
> fitted choice model. (2) Proximity to the existing network is the only new
> covariate class ever found interior. (3) The white-space reframe — rank
> places by *unserved* demand — won 14 of 108 scored cells with **zero**
> significant wins, against 32 significant wins for ranking on households
> alone.
>
> **One caveat that must travel with it**, because it is a genuine internal
> tension and an examiner may find it. At metro grain, once size is
> controlled, `facilities_open_prior` takes a **negative** coefficient in all
> seven held-out years (-0.09 to -0.45) — `NOTES_METRO_ENTRY.md` §9. The raw
> correlation still agrees (baseline 3 alone scores AUC 0.7325), but
> conditional on how big a metro is, having facilities predicts *fewer* new
> ones. So densification is a statement about where the big metros are, not
> an independent mechanism, at least at that grain.

**Zone-merger invariance (aggregation invariance)**
The property that if you merge two adjacent zones, their attractions add up,
so the model's answer does not depend on how the statistical agency happened
to draw the boundaries. It is the reason this project's specification is
restricted to **extensive** (count-like) attraction variables, and it is the
only defence it has against the modifiable areal unit problem.

> **Example — ours, measured rather than asserted.** Over **43,224** merged
> ZCTA pairs the relative error in the merger identity is **0.00** for the
> extensive-only control (max 4.4e-16, i.e. floating-point noise), and
> **0.0436 median / 0.4549 maximum** for the arm that adds the network
> proximities (`outputs/metrics/network_inference.json`,
> `merger_invariance`). Distances do not add when zones merge; counts do.
>
> > **Be precise about which arm this measures.** It is
> > `combined_plus_network` — the **published proximity** specification — not
> > a gravity arm. `NOTES_GRAVITY_NETWORK.md` §10 item 2 states plainly that
> > the equivalent number for a gravity arm **was never computed**, and that
> > gravity's level drift over vintages (3.1x to 3.9x between 2017 and 2030)
> > makes it plausible that gravity is *worse* rather than equal. Earlier
> > drafts of this entry attributed the 0.046/0.470 figures to "the gravity
> > arm". They are the proximity arm's, and the figures themselves moved to
> > 0.0436/0.4549 on 43,224 pairs when the artefact was re-run on 2026-09-15.
> > If asked what gravity's merger error is, the answer is "not measured, one
> > module call away, and the drift says it is probably worse".
>
> The point to make out loud: the gravity model still *runs*. What it loses
> is the argument for why it has that shape, and that argument is the only
> justification the specification offers. A write-up cannot print "invariant
> to ZCTA boundaries, per Train §3.4 Example 2" and a gravity coefficient on
> the same page.

**Clustered bootstrap**
Resampling whole *clusters* — metros, buildings — with replacement, rather
than rows or decisions, so that the interval accounts for the fact that
observations inside a cluster are not independent draws.

> **Example — ours, and it exists because a re-split spread was being quoted
> as though it were a standard error.** A percentile spread across re-splits
> describes how an estimate moves across partitions of one fixed sample. It
> is **not** a standard error and does not describe drawing a different
> sample. In `outputs/metrics/network_inference.json` the metro-clustered
> bootstrap interval on `warehousing_establishments` came out **13% wider**
> than the re-split spread despite being fitted on more decisions.
>
> > **Two cautions on that 13%, both of which an examiner can reach.**
> >
> > **It is not the same object as the "24-28% wider" figure** quoted in
> > `docs/data/FIGURES.md` and in `docs/PREREG_METRO_MODEL.md` §6. That one
> > is the Liang-Zeger CR0 metro-clustered **sandwich**, averaged over four
> > columns; this one is the metro-clustered **bootstrap** on a single
> > column. Both are real. They are different estimators and neither is a
> > correction of the other, but FIGURES.md instructs that a 13% figure
> > "should be traced or dropped" while two other documents still print it.
> > If asked, say which estimator you mean before you say the number.
> >
> > **Both figures are stale as of the 2026-09-15 re-run.** Recomputed off
> > the current `network_inference.json`, the bootstrap ratio on
> > `warehousing_establishments` is about **1.05**, and the four-column
> > sandwich-vs-re-split mean is about **1.27** — with
> > `warehousing_establishments` itself now **narrower** (0.95), which
> > breaks the tie the FIGURES.md paragraph rests on. The qualitative point
> > survives in every version: a re-split spread is not a standard error.
> > The percentage is not safe to quote from memory.
>
> **Do not carry the direction forward as a rule.** On the metro-entry
> problem it reverses: the re-split spread is [-0.235, -0.133], width 0.102,
> and the 2,000-draw metro-clustered bootstrap is [-0.201, -0.131], width
> 0.070 — **31% narrower** (`NOTES_METRO_ENTRY.md` §7). The two objects
> differ: re-splits refit the model 50 times and so include estimation
> variability, while the bootstrap conditions on the fitted models and
> measures only the sampling variability of the metric. The rule that
> survives is the negative one — never quote a re-split spread as a standard
> error.

---

## 5. Evaluation

**Out-of-sample vs out-of-time**
Held-out *rows* vs held-out *future*. The second is much harder and is what we
do.

**Backtest**
Train on the past, predict the following period, score against what happened.

**AUC-ROC**
Pick one positive and one negative case at random — how often does the model
score the positive higher? 0.5 is a coin flip. On the **retired hazard model**
we pre-registered 0.80 and **measured 0.6894**. Note that AUC only judges the
*ordering*, so it survives any monotone squashing of the probabilities — which
is why a model can post a respectable AUC and still emit numbers nobody should
quote. That model does exactly that; see **Expected Calibration Error** below.
AUC is not reported for the successor choice model, and should not be: with one
chosen alternative per decision and thousands of alternatives, **top-k
accuracy** is the meaningful ranking measure.

**McFadden rho-squared (pseudo-R-squared)**
For a choice model, `1 - (LL_model / LL_null)`: how much of the log-likelihood
gap between a useless model and a perfect one you closed. It is **not** the
R-squared of a regression and it does not mean "19% of the variation
explained". McFadden's own guidance is that values which look small by OLS
habits correspond to good fits, so the only safe use is *comparative*.

> **Example — ours, and read the caveat aloud.** Log-likelihood **-203.4497**
> against a uniform model's **-253.3351** gives **0.19691**. That figure is
> **in sample**, on the 56 training decisions. Quote it as in-sample or do not
> quote it. The honest headline is not the rho-squared at all — it is the
> held-out comparison in **top-k accuracy**, where a raw covariate matches the
> fitted model (see **Top-k accuracy** below).

**Top-k accuracy**
For each decision, rank every alternative in the choice set and ask whether the
one actually chosen landed in your top *k*. Report it as a count of decisions,
not a percentage, when the denominator is small — "7 of 38" is honest in a way
that "18.4%" is not.

> **Example — ours, on 38 held-out decisions over 3,998 alternatives. This is
> the project's headline result and it goes the wrong way.**
>
> ```
>                             top-1    top-5    top-10    Brier
>    -------------------------------------------------------------
>    fitted model              7/38    16/38     19/38    0.008724
>    warehousing count alone   8/38    16/38     20/38    0.008951
>    households alone          1/38     5/38     10/38    0.009271
>    establishments alone      0/38     8/38      9/38    0.009307
>    land area alone           0/38     3/38      6/38    0.009816
>    uniform within metro      1/38     3/38      7/38    0.009316
> ```
>
> A single raw Census County Business Patterns count — NAICS 493, warehousing
> and storage, with **nothing fitted from it** — **matches** the three-parameter
> fitted model. On this seed it is one hit up at top-1, one up at top-10 and
> level at top-5. Say "matches", never "beats". The fitted model is marginally
> ahead on raw Brier and that gap is far too small to survive 38 decisions
> either. **The estimation buys nothing measurable.** The useful reading is the
> substantive one: the operator builds where warehouses already are — twice as
> good as a population map at top-10, 20 against 10, and obtainable without a
> model.
>
> > **Corrected 2026-09-14.** This entry used to say the raw count **beats**
> > the fitted model and instructed you to say "beats", never "matches". That
> > instruction is now reversed, because it was wrong rather than out of date.
> > It rested entirely on the single seeded split in the table above. Re-split
> > the same 94 decisions fifty times and the raw count is ahead by **0.36 hits
> > out of 38, paired sd 1.14**, losing 11 of the 50 outright
> > (`outputs/metrics/gbm_benchmark.json`). A third of a decision is a tie, and
> > calling it a win read noise as signal. The table's numbers are right for
> > their seed, and the conclusion does not move: three fitted parameters buy no
> > ranking improvement over counting warehouses.

**Sandwich versus bootstrap standard errors**
Two ways to put uncertainty on an estimate when you do not trust the textbook
formula. The **sandwich** (Huber–White, robust) estimator rebuilds the
covariance as `A^-1 B A^-1` from the observed curvature and the observed score,
so it survives some kinds of misspecification. The **bootstrap** instead
resamples the units — here, whole decisions — refits, and reads the spread of
the refits directly.

> **This project has BOTH, as of 2026-09-14, and every interval covers the
> null.** An earlier version of this entry said the project had neither and
> called it a delivery gap. That was true for most of the day; the `inference`
> block then landed in `choice_report.json`. The withdrawal is recorded here
> because the entry was quoted elsewhere.
>
> **The null in this model is `beta = 1`, not `beta = 0`.** Households is the
> numeraire, the model is scale-invariant, and only ratios are identified — so
> each interval says "how many households one unit of this covariate is worth",
> and 1 means the model cannot tell them apart.
>
> ```
>   56 training decisions across 38 metros, alpha 0.05
>   1,000 bootstrap replicates over decisions, 1,500 over metros, converged
>
>   warehousing_establishments, beta = 1.4428 -- the only interior parameter
>     sandwich, 95%                  [0.734,  2.835]
>       z against the ratio 1                1.064    p = 0.287
>     bootstrap over decisions       [0.760,  4.762]  11.8% below 1
>     bootstrap over metros          [0.702, 10.013]  13.4% below 1
>     BCa                            [0.714,  3.522]
>     ALL FOUR INTERVALS COVER 1.0.
>
>   land_area_sqmi      beta = 3.0e-16   AT THE BOUNDARY
>   establishments      beta = 4.7e-16   AT THE BOUNDARY
>     sandwich REFUSED for both, correctly; one-sided bootstrap instead,
>     with about 80% of replicates sitting at the boundary
> ```
>
> **The sandwich is refused at the two boundary parameters, and that is correct
> rather than a shortfall.** Its asymptotics assume an interior maximum with a
> vanishing gradient; `beta = exp(theta)` puts those two at `theta` near minus
> thirty-six, where a standard error would be meaningless rather than merely
> wide. The bootstrap needs no interiority assumption and survives, with a
> one-sided interval because the sampling distribution has an atom at zero.
>
> Two caveats. Train's precondition for the bootstrap fails at 56 decisions
> (§8.6, p. 202), so these measure sensitivity to *which of our 56*, not
> sampling variability over the population. And the decision and metro
> bootstraps differ by a factor of two on the upper endpoint; quote the
> metro-clustered one. The modules behind this — `choice_inference.py`,
> `choice_sandwich.py`, `choice_bootstrap.py` — were uncommitted when this was
> written.

**Capture-recapture**
A way to estimate how big a population is when you can only ever see part of it,
by using **two or more independent attempts to observe it** and looking at how
much they overlap. If two lists overlap heavily, they are probably between them
seeing most of the population; if they barely overlap, there is a lot you are
both missing. The Lincoln–Petersen estimate is `n1 * n2 / overlap`, with the
Chapman correction applied for small samples.

> **Example — ours, `outputs/metrics/nlrb_coverage.json`.** How much of Amazon's
> footprint can OSHA actually see? Treat OSHA records and NLRB records as two
> attempts to observe the population of US cities containing an Amazon facility.
> The answer: **OSHA sees at most 54%** of them. A three-list log-linear model
> over ten states, adding OpenStreetMap, puts the population at **314 to 417**
> cities, the range depending on which pairwise dependence terms the
> specification allows.
>
> **The dependence between the lists is measured, not assumed** — that is the
> methodological point worth making. Both OSHA and NLRB records are generated by
> worker grievance, so appearing on one raises your chance of appearing on the
> other. Positive dependence inflates the overlap and therefore deflates the
> population estimate, which is why every population figure here is a **lower**
> bound and every coverage figure an **upper** bound.

**Chao estimator**
A capture-recapture estimator that is deliberately conservative: it returns a
**lower bound** on population size that stays valid when the lists are
positively dependent, which is exactly the case where Lincoln–Petersen breaks.
Being a lower bound on the population, it gives an *upper* bound on coverage.

> **Example — ours.** Chao puts OSHA's coverage of Amazon-facility cities at
> **37.8%**, against the Chapman figure's 54%. Quote 54% when you want the most
> generous defensible claim about OSHA and 37.8% when you want the estimator
> that is robust to the dependence we actually measured. Never quote one without
> saying which it is.

**PR-AUC**
Like AUC but ignores true negatives. Matters when positives are rare — ours
are about 2% of ZCTA-quarters in the test split. Not computed in this project;
`outputs/metrics/hazard_report.json` reports AUC, Brier, ECE, a ten-bin
calibration table and conformal coverage, and nothing else. Do not quote a
PR-AUC.

**Base rate**
How often the thing happens at all. Always report it next to PR-AUC. Ours is
0.020015 on the test split — about one ZCTA-quarter in fifty.

**Brier skill score**
How much better your Brier score is than a chosen baseline's, as a fraction:
`1 - (brier_model / brier_null)`. Positive means you beat the baseline;
**negative means the baseline beat you**, and you should have used it.

> **Example — ours, all three splits.** Unit-clustered test split: +0.00471,
> so we beat a constant by half a percent. Temporal hold-out: -0.02091.
> Geographic hold-out: -0.06184. The last two are negative. A constant would
> have served the reader better.

**precision@k**
Of your top *k* predictions, how many were right? Matches how the output is
actually used.

**Calibration**
Do the stated probabilities match reality? A perfectly calibrated "60%" happens
60% of the time.

**ECE (expected calibration error)**
The average gap between stated and actual probability, taken over bins of
predicted probability and weighted by how many cases fall in each bin.

> **Example — the most important number in this project.** Our model's ECE is
> **0.00863**. The null model, which predicts the same constant for every ZIP
> in every quarter, scores **0.00005** — about 170 times better. That is not a
> paradox. A constant is almost perfectly calibrated *trivially*, because it
> never sticks its neck out: it says "1.91% everywhere" and the truth is 1.92%.
> Our model spreads its predictions from roughly 1% to 9%, and those
> spread-out numbers are wrong by enough to cost it the comparison. It buys a
> little ranking ability and pays for it with probabilities you must not quote.
>
> The lesson generalises: **ECE must always be read against a baseline.** Our
> 0.00863 clears the pre-registered threshold of 0.05 comfortably and is still
> evidence of failure.

> **Updated 2026-09-15 — the calibration verdict now carries two more runs,
> and both agree.** The 0.00863 figure above is the retired 39-event pilot and
> is still correct for it. Since then:
>
> - **The hazard model was revived** on the expanded panel — 5,441
>   ZCTA-quarter events against the pilot's 812, with stated MWPVL opening
>   dates instead of OSHA upper bounds. Its calibration beat the constant null
>   in **0 of 17** comparisons (`outputs/metrics/hazard_revival.json`,
>   `calibration_against_constant`, whose verdict field reads *"the constant
>   null is better calibrated everywhere"*). On the comparable arm the model's
>   ECE is 8.7x the null's; on the matched arm, 47.3x.
> - **The metro-level entry model** beat the constant null on ECE in **3 of
>   7** held-out years, which fails its pre-registered majority clause
>   (`outputs/metrics/metro_entry.json`, `verdict.clause2`). The pattern there
>   is worth stating because it is *not* the hazard model's: the model wins in
>   2020, 2021 and 2025 — the three years the base rate jumped — and loses the
>   four quiet years by 5x to 60x. So it is not uniformly worse calibrated
>   than a constant; it is worse calibrated whenever the world is steady,
>   which is most of the time.
>
> One honesty note to volunteer: ECE with 10 quantile bins on a 3-5% event
> rate is a noisy statistic, and `NOTES_METRO_ENTRY.md` §11 says the 3-of-7
> count should be re-read at a different bin count before anyone builds on the
> exact number. It would not survive re-reading into a 4-of-7, because the
> four losing years lose by margins of 5x to 60x rather than narrowly.

**Brier score**
Mean squared error of a probability forecast. Combines calibration and
sharpness. Ours is 0.019522 against the null's 0.019614 — see **Brier skill
score** above for why that difference is nothing.

**Conformal prediction**
A distribution-free way to produce intervals whose coverage you can *verify*
rather than assume.

> **Example — ours.** Hold out a calibration set, take the 90th percentile of
> the errors, use that as the interval width, then check on fresh data. We
> measured **88.19% empirical coverage against 90% nominal**, inside a
> two-sigma tolerance of 0.032. The tolerance is computed on 351 **effective**
> units rather than on 8,044 rows, because a delivery station flips a whole
> catchment at once and the rows are therefore not independent.
>
> Note what conformal does *not* buy you. Valid coverage is compatible with a
> badly calibrated centre — a wide enough interval covers the truth whatever
> the point prediction is doing. Our intervals cover honestly and our point
> predictions are still worse than a constant.

> **On the fitted choice model it looks WORSE, and that has to be volunteered.**
> On a 24-decision test split with a median choice set of 59.5 alternatives:
>
> ```
>    alpha   nominal   empirical   median set   share of choice set
>    ----------------------------------------------------------------
>    0.10     0.90       1.000        38.5             0.714
>    0.20     0.80       0.958        34.0              --
>    0.30     0.70       0.833        18.5              --
> ```
>
> At the 90% level the procedure names **71% of the metro**. It achieves perfect
> coverage by being very nearly vacuous. "Somewhere in these 38 of your 59 ZIPs"
> is not a forecast. The hazard model's 88.19% is the *better*-looking of the
> two, which is a strange sentence and an honest one.

**Monte Carlo simulation**
Re-run the calculation many times with inputs drawn from their uncertainty,
producing a distribution instead of a number.

> **Status: IT RAN.** 500 of 500 draws, seed `20260914`, artefacts
> `outputs/metrics/montecarlo_report.json` and
> `outputs/tables/montecarlo_draws.parquet`. Any text in an older draft saying
> it is specified, blocked, on the backlog, illustrative or not yet run is
> **false**. There was never a 10,000-draw NPV Monte Carlo and never a
> 24-billion-draw one.
>
> ```
>                        p10       p50       p90      min     max
>    ---------------------------------------------------------------
>    activations n       152       264.5     306       82      385
>    capital, $bn        0.608     1.058     1.224     0.328   1.540
>    breakeven margin    1.0892    1.3682    1.7259
>    median $ / parcel   0.8368    1.1224    1.4836
> ```
>
> **It is not a confidence interval, and the artefact says so itself.** Every
> range comes from this project's own `PARAMETERS.md` and **eight** of the
> constants have no external source, so it propagates our priors rather than the
> world's. **`parcels_per_depot_per_day` was not sampled, by oversight, so every
> band above is a floor.** The top variance driver in `n` is
> `cannibalisation_peak` — rank correlation -0.622, **44.3%** of the variance —
> which is the assumed 0.18 nobody estimated.
>
> One thing it settles: the delivered 282 activations sit at the **67th
> percentile**, inside the band, while the previously published 330 sits at the
> **97th** and 317 at the **95th**. The drift in the older headline was real and
> the parameters did not cause it.

**Bootstrap**
Resample the data to put a confidence interval on a statistic — including on
a median.

**P10 / P50 / P90**
The 10th, 50th and 90th percentiles of a simulated distribution.

**Rank stability**
Across all simulation runs, how often does this area stay in the top *k*?

> **Example — ILLUSTRATIVE, NOT MEASURED.** 94608 stays top-ten in 87% of runs
> — act on it. 94612 in 34% — don't commit $4M.
>
> **The 87% and 34% are made up**, to show the shape of the output. There is no
> per-ZCTA rank-stability artefact in this project: the 500-draw Monte Carlo
> reports bands on activation count, capital, break-even margin, median cost per
> parcel and the optimality gap, and nothing per-ZCTA. Do not quote these two
> numbers. This pack's rules require illustrative figures to be labelled
> wherever they appear, and this entry previously was not.

**MAPE**
Mean absolute percentage error. **Undefined when the actual value is zero**,
which is why we don't use it.

**Wilson interval**
A confidence interval for a proportion that behaves properly with small samples.

**MDE (minimum detectable effect)**
The smallest difference your sample size could actually detect. Worth stating
*before* running a comparison.

**Cohen's κ**
Agreement between two raters, corrected for agreement by chance.

---

## 6. AI and agents

**LLM (large language model)**
A model that predicts the next piece of text. Here it does one useful job:
turning prose into structured records.

> **Example.** *"Walmart announced a 350,000 sq ft sortation centre in Plano,
> Texas, opening Q3"* → `{operator, type, city, state, sqft, quarter}`.

**RAG (retrieval-augmented generation)**
Retrieve real documents first, then answer from them, instead of relying on what
the model memorised.

**ReAct**
A loop of Thought → Action → Observation, repeated until the model can answer.
Each step is grounded in a real result.

**Agent**
An LLM that can call tools rather than only produce text.

**Tool**
A function the agent may call — run a query, draw a map, write a record.

**MCP (Model Context Protocol)**
A standard way to expose tools so any compliant client can use them.

**Text-to-SQL**
Turning a natural-language question into a database query.

**Execution accuracy**
Does the generated query return the same rows as a known-correct query? The
objective metric, as opposed to human judgement.

**Hallucination**
Confident output that isn't true.

**HITL (human in the loop)**
A human must approve before an action takes effect. Default ON for any public
demo.

**Data integrity vs inferential integrity**
Data integrity: the rows are correct. Inferential integrity: the *conclusions
drawn from them* are still valid. **A write can preserve the first and destroy
the second — that gap is our main contribution.**

**The six gates**
1 schema · 2 geocoding · 3 confidence · 4 audit log — these protect data.
**5 donor-pool integrity · 6 estimate stability** — these protect the
inference.

**Pre-registered threshold**
A limit fixed *before* seeing results, so it can't be moved to suit them.

---

## 7. Data engineering

**ELT / ETL**
Extract, load, transform (or transform then load) — moving data from sources
into a warehouse.

**Parquet**
A columnar file format. Smaller, typed, and lets you read three columns instead
of forty.

**DuckDB**
An analytical database that runs inside your process from a single file. No
server.

**dbt**
A tool for defining warehouse transformations as version-controlled SQL.

**Star schema**
One central fact table surrounded by dimension tables. Standard analytical
layout.

**Fact table / dimension table**
Facts are the measurements; dimensions are the descriptive context (geography,
date, operator).

**Grain**
What one row represents. Ours is one ZCTA in one quarter.

**Data contract**
An assertion that **fails the build** — row counts, null rates, referential
integrity.

**Content-addressed cache**
Files stored under the hash of the request that produced them, so a repeat
request is a local read.

**Manifest**
The record of every fetch: source, URL, hash, timestamp, size.

**Idempotent**
Running it twice gives the same result as running it once.

**CI (continuous integration)**
Automated build-and-test on every change. A red build blocks merge.

**Seed**
The number that makes a random process repeatable.

**OSRM / OpenStreetMap / PBF**
Open routing engine, the open map it runs on, and the compressed file format.
We use them **once, offline**, then delete the artifacts.

**OD matrix (origin–destination)**
A table of travel times between point pairs. Ours is ~800,000 pairs in 10 MB
— and it replaces the entire routing engine.

---

## 8. Business and finance

**NPV (net present value)**
Future cash flows discounted to today's money, minus what you spend up front.

**Discount rate**
The rate at which future money is worth less than money now. We use 10%.

**Contribution margin (m)**
Profit per additional order after variable costs. **Not observable in public
data** — so we report results as a multiple of it.

**Break-even**
The value an unknown input would need for the answer to be zero.

> **Example.** "Break-even at m = **1.343067**" — the measured break-even
> margin per parcel of the selected **282**-activation portfolio, from
> `outputs/metrics/portfolio_report.json`, run `20260914-002431-7419`. Above
> that it's profitable, below it isn't.
>
> **Numbers withdrawn.** This entry used to read "$1.3842" and "317-ZCTA".
> Both are stale: the current artefact says 1.343067 and n = 282. "$1.39" is
> also stale. The portfolio deploys **$1.128bn** of a **$2bn** budget — 56.4%,
> so it **declines about 44%** of the budget, not "a third" and not "roughly two
> thirds spent". The capacity limit of 500 is **not** binding. The optimality
> gap is 0.107284 against an upper bound of 1.212938.

**Margin frontier**
Because `m` is unobservable and NPV is linear in it, choosing one value for `m`
would choose the answer. Solving the optimiser across a range of margins and
reporting the whole curve is therefore the right design.

> **A claim withdrawn. THE FRONTIER DOES NOT EXIST.** This entry used to call it
> "the project's actual deliverable" and described a six-margin ladder — "empty
> below ~$1.17, 317 activations at $1.55, budget-saturated by $1.86". **None of
> that is in the artefact.** `portfolio_report.json` contains `"frontier":
> null`. What the artefact does deliver is a single solved portfolio (282
> activations, break-even margin 1.343067) plus a 500-draw Monte Carlo band on
> the break-even margin: p10 **1.0892**, p50 **1.3682**, p90 **1.7259**. Quote
> that band if you want a range; do not describe a ladder that was never
> written.

**CapEx (capital expenditure)**
Up-front spend on buildings and equipment. Partly disclosed publicly, which is
why it's our external check.

**Tax abatement**
A tax break offered to attract a facility. The counterfactual — *would they have
built here anyway?* — is exactly what a selection propensity would answer.

> **Not ours, though.** This entry used to say "is exactly what our selection
> propensity answers", present tense. It does not. The hazard model's
> probabilities are worse calibrated than a constant, and the choice model's
> conformal sets name 71% of the metro at the 90% level. The *use case* is real;
> the instrument is not yet good enough to serve it. Say "this is what a working
> model would be for".

**Sensitivity / tornado analysis**
Which input, moved across its plausible range, moves the answer most.

**Submodular / supermodular**
Diminishing returns vs increasing returns as you add items to a set. Ours is
**neither**, which is why the standard greedy guarantee doesn't apply.

**Greedy algorithm**
Take the best item, then the next best, and so on. Fast, and provably decent for
submodular problems — but not for ours.

**Portfolio / bundle selection**
Choosing a *set* rather than ranking items individually, because the items
interact.

---

## 9. Regulatory and public-interest

**Environmental justice (EJ)**
Whether environmental burdens fall disproportionately on particular communities.

**EJScreen**
The EPA's free tool combining pollution burden with demographics.

**Indirect source rule**
A regulation covering facilities that *attract* polluting traffic rather than
emitting directly.

**Rule 2305 / WAIRE**
South Coast AQMD's warehouse indirect source rule (2021, EPA-approved). Large
warehouses must earn emission-reduction points or pay. Creates real institutional
demand for a siting forecast.

**Nominative fair use**
Using a trademark to *refer* to the thing it names. Fine in descriptive prose;
not fine in a product name or domain.

---

## 10. Project shorthand

| Term | Meaning |
|---|---|
| **The estimand** | What we are trying to estimate — here, service enablement and timing |
| **The panel** | The 1,081,312-row x 44-column ZCTA-quarter table every model reads |
| **The national frame** | **Two of them now — say which you mean.** The *pilot* frame is the hand-verified 104-row / 100-loaded, 62-metro OSHA set, and it is what `choice_report.json`, `gbm_benchmark.json` and `leakage_test.json` still read (94 decisions, 38 held out). The *expanded* frame is `national_facilities_expanded.csv` — **693 rows, 687 buildings, 230 CBSAs**, built by merging the MWPVL OCR extraction (`outputs/metrics/mwpvl_merge.json`, `outputs/metrics/national_panel_expanded.json`) — and it is what `refit_expanded.json` (483 decisions), `panel_experiments.json` and `hazard_revival.json` read. Quoting a 94-decision number beside a 483-decision one without saying so is the easiest mistake to make in this pack |
| **The backtest** | Train ≤2023, predict 2024–25, score against reality |
| **The decay curve** | Cannibalization by distance band. **NEVER BUILT** — no decay curve has been estimated in this project. And note what the project's own audit found on 2026-09-15: `fig05_decay` *plotted* one, with nine hand-typed effect values, a band labelled "95% CI", a significance annotation and a y-axis (2-day order volume) that does not exist in the data. It was restyled as a schematic with an in-axes "ILLUSTRATIVE ONLY — NO REGRESSION HAS BEEN RUN" banner (`tools/figures/fig_methods.py`). If an examiner asks for the decay curve, the answer is "there isn't one, and here is the figure that used to imply there was" |
| **The gates** | The six checks on an agent write |
| **The overlay** | Predicted expansion crossed with EJScreen by demographic group |
| **Operator-consistent desirability** | What the operator's revealed preference implies — *not* objective viability |
| **The ceiling** | How much siting behaviour is explainable from public data alone (RQ4) |
| **Volume I** | This capstone. Volume II is data centres |
