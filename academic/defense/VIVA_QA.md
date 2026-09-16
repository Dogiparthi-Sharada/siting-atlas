# Viva Q&A

**The questions you will actually be asked, with answers you can say out loud.**

How to use this: read the answer, then close the file and say it in your own
words. If you cannot, you do not know it yet. The exact wording matters less
than the structure — **name it, size it, answer it, state what remains.**

**Before you read anything else.** **Three** siting models in this project
were built, fitted on real data, and failed. The first was a discrete-time
hazard on ZCTA-quarters; it lost to a constant, and when it was revived on
6.7x the events with real opening dates it lost again. The second was the
conditional ZCTA-choice model built to replace it; it was matched by a single
raw Census count with nothing fitted from it. The third was a *pre-registered*
metro-level entry model, tested on 2026-09-15 against a document written
before the fit; it lost to "rank metros by households" in 0 of 7 held-out
years. Part 0 is the questions that follow from the first two; **Part 0B is
the questions that follow from everything that happened on 14-15 September**,
and between them they decide the viva. Every number quoted here was re-derived
from an artefact; where this file and an artefact disagree, regenerate the
artefact and believe the artefact.

> **Updated 2026-09-15. What changed since this file was last revised, in the
> order an examiner will meet it.** Nothing below retracts a Part 0 number —
> the pilot-frame figures are all still correct for the pilot frame — but
> several of them are no longer the *current* frame, and three answers in this
> file were factually wrong as written. Each correction is marked where it
> occurs.
>
> ```
>   1  THE PANEL GREW.  An industry PDF was OCR'd into 1,904 facilities,
>      1,420 with dates.  Filtered to US delivery stations and screened
>      against the hand-verified panel, it took the facility file from
>      104 rows to 693 (687 buildings, 230 CBSAs).
>      -> outputs/metrics/mwpvl_{extraction,merge,validation}.json
>      -> outputs/metrics/national_panel_expanded.json
>
>   2  A THIRD MODEL WAS PRE-REGISTERED AND LOST.  Metro-level entry.
>      0 of 7 years on AUC, 3 of 7 on calibration, H0.   Sec. 0.5
>      -> docs/PREREG_METRO_MODEL.md, outputs/metrics/metro_entry.json
>
>   3  THE HAZARD MODEL WAS REVIVED AND LOST AGAIN.  5,441 events
>      against 812, real dates, AUC 0.6894 -> 0.6832, calibration
>      beaten by a constant in 0 of 17 comparisons.   Sec. 0.9
>      -> outputs/metrics/hazard_revival.json
>
>   4  THE GBM BENCHMARK EXISTS NOW.  Sec. 0.3 and D1 both say it was
>      "never built".  THAT IS NOW FALSE -- see the correction at 0.3.
>      -> outputs/metrics/gbm_benchmark.json
>
>   5  THE LEAKAGE GUARD WAS AUDITED, NOT JUST DISCLOSED.  Sec. F6 and
>      C3a say the margin is zero and nothing fixes it.  A decisive
>      test was then run on 29 decisions with stated opening dates:
>      the covariate retains 79% of its value and beats the floor
>      50 of 50.  Still not clean.  See the correction at F6.
>      -> outputs/metrics/leakage_decisive.json
>
>   6  TWO FIGURES WERE FOUND FABRICATED, AND FIXED.   Sec. 0.8
>      -> docs/data/FIGURES.md, tools/figures/fig_methods.py
>
>   7  TWO REAL BUGS WERE FOUND IN choice.py AND GUARDED.   Sec. E6
>      -> src/siting_atlas/models/choice.py lines 271-334
> ```
>
> **The single most important framing change.** The old story was "the sample
> is too small". That story is now measured and false: the sample was
> quintupled, the hazard model's events went up 6.7x, and nothing moved. The
> current story is **"the ceiling is the data, and the failure has a
> diagnosis"**. If you deliver the old story an examiner who has read the
> artefacts will correct you with your own files.
>
> ⚠️ **AND ONE OPERATIONAL WARNING, WHICH IS THE MOST LIKELY WAY YOU GET
> CAUGHT.** Two artefacts — `gravity_network.json` and `white_space.json` —
> were **re-run late on 2026-09-15**, after the research notes that cite them
> were written. `gravity_network.json` now carries run
> `20260915-210603-b780`; `white_space.json` moved because 46 delivery
> stations were re-geocoded (455 real coordinates to 501). A pre-promotion
> copy of the old values is on disk under
> `data/interim/prepromotion_backup/20260915T125221/metrics/`.
>
> Every number in `NOTES_GRAVITY_NETWORK.md` and `NOTES_WHITE_SPACE.md`
> matches the **backup**, not the file at the path those notes cite. The
> differences are small and none of them reverses a conclusion — several make
> the negative findings *stronger* — but they are differences, and an
> examiner who opens the JSON will see a different number from the one on
> your page. The affected quotables:
>
> ```
>   quantity                          the notes say   the artefact now says
>   -------------------------------------------------------------------
>   densification band                67-77%          68.7-75.9%
>   gravity large-metro lift          6.2824          6.2187
>   published proximity lift          6.3263          6.2903
>   ... and no-network at all          --             6.2585  (gravity is
>                                                      now WORSE than using
>                                                      no network term)
>   merged ZCTA pairs                 43,239          43,224
>   fulfilment_proximity at boundary  1 of 50         0 of 50
>   white-space openings scored       73 / 130        79 / 131
> ```
>
> **The right response in the room is the boring one:** "that note was
> written against an earlier run of the artefact, the file was re-run on the
> fifteenth, and the current value is X — here is the backup if you want to
> see the difference." Do not bluff a number you have not re-read.

**The five sentences you must be able to say without notes.** They are
unpleasant and volunteering them is the whole strategy.

```
  1  The hazard model lost to a constant.  Brier 0.019522 against 0.019614,
     and its calibration error was 170 times the constant's.

  2  The choice model that replaced it only matched one raw covariate.
     Held out, ranking ZIPs by their existing warehousing count -- zero
     parameters -- gets the right answer in the top ten 20 times in 38.
     The fitted three-parameter model gets 19.  Fitting bought nothing.

  3  The intervals now exist, and they cover the null.  On the one parameter
     that does any work the 95% sandwich interval is [0.734, 2.835] against
     a null of 1.0, at p = 0.287.  Every bootstrap variant agrees.

  4  The covariate that does all the work may contain its own outcome.
     AMENDED 2026-09-15: the guard's margin is no longer "zero and
     untested".  Audited on 29 decisions with stated opening dates, the
     covariate retains 79% of its value and beats the no-covariate floor
     50 of 50, and the per-establishment price is unchanged to within
     1.2%.  It is not clean: the test cost 65 of 94 decisions, those 29
     are measurably easier, and leak and staleness are not separable.

  5  ADDED 2026-09-15.  A third model was PRE-REGISTERED and it lost.
     Metro-level entry, criterion written to disk before the fit, md5
     recorded.  It loses to "rank metros by household count" in 7 of 7
     held-out years, pooled AUC 0.7323 against 0.8949, and 50 of 50
     paired re-splits.  A zero-parameter count of facilities already
     open scores 0.7325 -- two ten-thousandths ABOVE the fitted model.
```

> **Corrected 2026-09-14 — memorise the new wording, not the old.** Sentence 2
> used to read *"lost to one raw covariate"*, and several answers below said
> the raw count **beats** the fitted model. That was wrong, not stale. The
> "loss" existed only in one seeded 56/38 split. Score the same 94 decisions
> over fifty paired re-splits and the raw count's lead is **0.36 hits out of
> 38 (paired sd 1.14)**, and it loses 11 of the 50 outright
> (`outputs/metrics/gbm_benchmark.json`, key
> `across_repeats.conditional_logit`). A third of a decision is a tie, and
> announcing a defeat off one split is reading noise as a result — the same
> error as claiming a win off one split, just pointed at yourself. If an
> examiner offers you "so a raw count beat your model", correct them: it
> **matched** it. The verdict is unchanged and still against the model —
> estimating three parameters buys **no** ranking improvement over counting
> warehouses — and every single-split number quoted in this file is correct
> for its seed.

Marked ⚠ where the honest answer is "we can't, and here is what we do
instead." Those are the ones people get wrong by bluffing.

---

## Part 0 — The two that decide the viva

**Read this part twice. Everything else is detail.**

The siting model in this project was specified, built, fitted on real data,
and it failed. That is the central fact about the work, and an examiner will
find it whether or not you volunteer it. There are exactly two ways this
viva goes badly: you are asked why the method keeps changing and you sound
indecisive, or you are asked about the negative result and you sound
evasive. Both questions have good answers. Learn these two before anything
else in this file.

### 0.1. "Why did the method change again?"

*The one-line version, and say it first:* **"I specified a model, built it,
tested it, and it failed. Then I went to the literature to find out why."**

> "The method changed once, and it changed because of evidence rather than
> because of taste. Here is the sequence.
>
> The proposal specified a discrete-time hazard model over ZIP-code
> quarters: for every ZIP in every quarter, what is the probability Amazon
> switches on delivery here. I built it. I fitted it on the 43-building
> panel I collected. Then I evaluated it honestly, against a null model that
> predicts the same constant everywhere, and it lost.
>
> It ranks slightly better than a coin flip — AUC 0.6894 against 0.5 — and
> that is the only good thing I can say about it. Its Brier skill over the
> null is +0.0047, which is nothing. Its calibration error is 0.00863
> against the null's 0.00005, so the constant is about 170 times better
> calibrated than my model. Split the data by time instead of by unit and
> the skill goes to -0.021; hold out two metros and it goes to -0.062.
> Negative skill means you would have been better off with the constant.
> One of my three covariates is distinguishable from zero, and it is
> households, which tells me Amazon builds where the people are.
>
> At that point I had two choices. Tune it until it looked better, or find
> out what was actually wrong. I went to the literature, and the literature
> gave me a clean answer within one section of one textbook.
>
> Train's *Discrete Choice Methods with Simulation*, Section 3.7.1, page 61,
> states the assumption the likelihood is built on: 'assuming that each
> decision maker's choice is independent of that of other decision makers'.
> Mine were not independent. A delivery station switches on every ZIP within
> a fifteen-mile catchment simultaneously — on my panel the median station
> covers 58 ZIPs, the mean 88, and the largest 307. So 'Amazon chose ZIP
> 60608 in 2021Q2' is not a choice. It is one of 88 simultaneous
> consequences of one choice. My 812 ZIP-quarter events were 43 real
> decisions wearing geometry as a disguise. The standard name for the
> failure is clustering, or pseudo-replication.
>
> I should say that I first cited the wrong section for this — Section 2.2,
> on mutual exclusivity — and I corrected it after reading 2.2 in full. It
> governs a choice set facing a decision maker, and a hazard on ZCTA-quarters
> has no decision maker choosing among those rows, so exclusivity is not a
> property they can have. Train also calls that criterion 'not restrictive'.
> Getting the citation right makes the charge harder, not softer.
>
> That is why 7.6 events per parameter was the honest power figure for that
> model rather than 97, and why the conventional floor of 10 was not met."

**And this is where the answer used to stop, which is no longer honest.**

> "The successor was then built, on a national frame rather than the ten-metro
> pilot, and it does clear the power floor: 94 decisions against three
> parameters. It still does not work. Held out, it ranks the chosen ZIP in
> its top ten 19 times in 38, and ranking those same ZIPs by their existing
> warehousing count with nothing fitted gets 20. So the reframe fixed the
> question and left the answer where it was — which is what the ADR
> recording the change predicted it would do, in the sentence 'the reframe
> could be mistaken for a rescue; it is not'."
>
> So the change is: same question, correct unit. Train points at the
> reframe in the same chapter — *which ZIP does the station go in,
> conditional on a station opening in metro m in period t*. That is a real,
> exclusive, enumerable choice.
>
> And I want to be precise about the provenance of the mistake. The
> ZIP-quarter unit was introduced in version 4 of the proposal. It is not in
> the version 3 I started from, and it was never tested against Train's rule
> before it was adopted. It should have been."

**If they press: "so your specification was wrong from the start?"**

> "The specification was untested from the start, which is worse in one
> sense and better in another. Worse, because an untested specification
> should never have gone into a proposal. Better, because a specification
> that was tested, failed, and was replaced for an articulable reason is
> worth strictly more than one that was never stress-tested at all. The
> second kind is what you get when a project reports only the model that
> survived."

**What NOT to say.** Do not say "we refined the approach." Do not say "the
data suggested a different direction." Both are true and both sound like
you are hiding a failure. Say it failed.

### 0.2. "Your model doesn't work. Why should I pass this?" ⚠

*This is the hardest question in the viva. Do not flinch and do not
oversell. The structure is: agree, size it, show what does work, show the
diagnosis, show the fix.*

> "You are right, and I would rather say it in those words than in softer
> ones. The siting model does not work. Let me give you four reasons the
> project is still worth passing, and you can decide whether they are
> enough.
>
> **First, the negative result is measured, not vague — and there are now
> two of them.** I can tell you exactly how badly each fails and against
> what. The hazard model: Brier 0.019522 against a constant's 0.019614 on
> the same 8,044 rows, calibration error 0.00863 against the constant's
> 0.00005, AUC 0.6894 against 0.5000, negative skill out of time. The
> successor I built to replace it: 94 decisions, three parameters,
> converged, McFadden rho-squared 0.1969 — and held out it puts the chosen
> ZIP in its top ten 19 times in 38, while ranking those same ZIPs by their
> existing warehousing count, with nothing fitted at all, gets 20. A single
> raw Census number matches my model. Those are in
> `outputs/metrics/hazard_report.json` and `outputs/metrics/choice_report.json`
> and you can regenerate both. A project that can say precisely how it
> failed has done more measurement than one that says it succeeded and
> cannot show you the hold-out.
>
> **Second, the negative results come with a diagnosis and a fix, and I got
> the citation for the first one wrong before I got it right.** I am not
> saying 'it didn't work, who knows why'. The hazard model violated
> independence across observations — Train Section 3.7.1, page 61, where the
> likelihood is built: 'assuming that each decision maker's choice is
> independent of that of other decision makers'. A fifteen-mile catchment
> covering a median of 58 ZIPs destroys exactly that. I originally cited
> Section 2.2, mutual exclusivity, and that was wrong: Section 2.2 is about
> a choice set facing a decision maker, and a hazard on ZCTA-quarters has no
> decision maker choosing among those rows. Train also calls that criterion
> 'not restrictive'. So my original citation named a rule that was not
> binding in support of a diagnosis that was correct. The standard name for
> what actually went wrong is clustering, or pseudo-replication.
>
> **Third, the finding itself is publishable in the honest sense.** '43
> delivery stations, dated by federal inspection records, cannot identify a
> siting policy' is a statement about what public data can and cannot do.
> Nobody has measured that for this facility class, because nobody has built
> a public delivery-station panel before. If a city council wants to verify
> an operator's siting claim from public records, this project tells them
> what they will and will not be able to establish. That is a result about
> opacity, and it is the result I actually have.
>
> **Fourth, and most concretely: four of the project's five components work,
> and they never needed the facility panel.** The cost model prices 2,333
> ZIP codes at a median of $1.0830 a parcel. The portfolio optimiser reports
> a break-even margin of $1.3431 over an unobservable one, selects 282
> activations, and declines about 44% of a $2bn budget because no further
> ZIP pays for itself. A 500-draw Monte Carlo over twenty-one constants puts
> that 282 at the 67th percentile of its own distribution, which tells me the
> answer is an ordinary draw rather than a fluke. The warehouse is a DuckDB
> star schema over all 33,791 national ZCTAs. Six validation gates run
> against that real warehouse and write an audit record per invocation. 648
> tests pass with 2 expected failures, on a clean tree at commit b29071e — and
> I would give you the commit rather than the bare number, because that count
> moved five times in two hours on the day I wrote this up and every one of
> those readings was correct at the time. One component needed a large sample,
> and that is the one that did not get one.
>
> What I am not going to tell you is that the failure was a plan. It was
> not. I would rather have a working siting model. I have a measured
> negative one, a reason for it, and the rest of the system standing."

**If they press: "isn't that just a rationalisation after the fact?"**

> "It would be if the diagnosis had arrived with the excuse. It didn't. The
> power check that reports 7.6 events per parameter is in the model code and
> it runs every time the model runs — it was written before the result, not
> after it, and it reports three different event counts precisely so that
> the flattering one cannot be the one quoted. The date-looseness
> measurement, the 4-to-345-month lags, was made against MWPVL's 2012
> snapshot before the model was fitted. The machinery that says this model
> is weak was built into the model."

**If they press: "why didn't you just get more data?"**

> "I tried, and I am still trying. Seven routes now, and the provenance
> record in `docs/data/FACILITY_PANEL_PROVENANCE.md` documents each failure
> with the artefact that proves it. Amazon's hiring site, Google Maps review
> dating, LLM web search, the MWPVL industry census, per-facility news
> search, Sentinel-2 changepoint dating (Sec. C3c) and SEC filings all
> failed -- Amazon discloses no facility locations or dates at all, and
> 'delivery station' appears four times in every filing it has ever made.
> The one that worked, OSHA, gave 43 pilot buildings and 104 national ones.
> A hand-labelling programme on top of that added 13 more, at a cost Sec.
> C3b is honest about. There is
> a paid source — MWPVL sells the panel Houde and co-authors used — and
> buying it would dissolve the problem and also dissolve the point of the
> project, which is that a city should be able to do this from free federal
> records. That decision is written down in
> `docs/METHODS_RESEARCH.md` Section 9 so it can be overturned by someone who
> disagrees with the reasoning rather than by someone who has forgotten it."

### 0.3. "Your best predictor is a single raw variable. What did the model add?" ⚠

*The honest answer is "nothing measurable", and you must reach that phrase
inside the first three sentences. Every second you spend before it is a
second the examiner spends deciding you were going to hide it. Concede,
size, then explain what the finding IS — because there is one, and it is not
the model.*

> "Nothing measurable. That is the answer and I would rather give it
> plainly.
>
> Here is the table. Held out, 38 decisions, each one a real building.
>
> ```
>                              top-1    top-5    top-10    Brier
>   the fitted model            7/38    16/38     19/38    0.008724
>   warehousing count alone     8/38    16/38     20/38    0.008951
>   households alone            1/38     5/38     10/38    0.009271
>   uniform within the metro    1/38     3/38      7/38    0.009316
> ```
>
> Ranking each metro's ZIPs by the number of warehousing establishments
> already in them — NAICS 493, a number Census publishes, free, with nothing
> estimated from it — matches my three-parameter fitted model: one hit ahead
> at top-1, one ahead at top-10, level at top-5 on this split, and level over
> fifty re-splits (see the correction block in Part 0). So the estimation
> bought nothing I can measure.
>
> There is one place the fitted model is ahead and I will not hide behind
> it: its raw Brier score is 0.008724 against the benchmark's 0.008951. That
> is a real difference in the right direction and it is far too small to
> survive 38 decisions. If I made that the headline, I would be choosing the
> metric after seeing the answer, and I have already had to correct one
> document in this project for doing something like that.
>
> **What the result actually is, and it is not nothing.** The finding is
> *'the operator builds where warehouses already are'*. It is true, it is
> twice as good as a population map — 20 out of 38 against 10 out of 38 at
> top-10 — and it costs nothing to compute. For a city council that wants to
> know whether a facility would have come anyway, 'look at your existing
> industrial land' is a more useful sentence than any coefficient I could
> hand them. The negative half is that the structure I wrapped around that
> covariate earns nothing, and the public record does not support the
> parameters.
>
> **The mechanism is visible in the fit itself.** The model parameterises
> the attraction index as `beta = exp(theta)` to keep it positive. Two of my
> three free parameters — land area and total establishments — were driven
> to `theta` around minus thirty-six, so `beta` of about 3 times ten to the
> minus sixteen. They are at the boundary. Once warehousing is in the index,
> everything else collapses to zero. Effectively I fitted a one-covariate
> model and called it three."

**If they press: "so why not just publish the covariate and drop the
model?"**

> "That is a fair reading and I would not fight it hard. Two things argue
> for keeping the specification. The choice framework is what makes the
> comparison legitimate in the first place — the benchmark is scored inside
> the same conditional choice sets, against the same 38 held-out decisions,
> so the dead heat is a measurement rather than an impression. And the
> specification is where the aggregation-invariance restriction lives, which
> is what stops the answer being an artefact of how Census drew the ZIP
> boundaries. Without it I would have a ranking I could not defend against
> the modifiable areal unit problem. But if you asked me what a city should
> actually run tomorrow, it is the covariate, not the model."

**If they press: "you pre-registered a gradient-boosted ranker as the
benchmark. Where is it?"**

> **CORRECTED 2026-09-15. The old answer to this question was "not built",
> and that is now false — it was built on 2026-09-13 and its artefact is
> `outputs/metrics/gbm_benchmark.json`. Learn the new answer; the old one
> concedes something that is no longer true and an examiner with the
> artefact will notice.**

> "It is built, and it says the ceiling is the data rather than my functional
> form. Over 50 re-splits on the same 94 decisions:
>
> ```
>   conditional choice model    20.60 of 38     best Brier of all three
>   warehouse count, unfitted   20.96 of 38
>   gradient-boosted trees      22.26 of 38
> ```
>
> The flexible learner wins by about one decision in 38 — and loses on
> probability quality, which is the axis that matters for anyone who has to
> act on the number. The spread between *all* methods is smaller than any one
> method's variation across re-samples.
>
> Then the sample was quintupled, from 94 decisions to 485, and the GBM's
> edge **disappeared entirely**: 0.5198 against 0.5196. Its one-decision
> advantage had been the small-sample model being slightly underfitted, not a
> real gain from flexibility.
>
> So the pre-registered adversary was the stronger one, it was run, and it
> was reported. What it bought me is the answer to 'is the model held back by
> the data or by its own simple form', and the answer is the data."

**If they press further: "which GBM number should I read?"** *There is a
trap here and you should walk them past it rather than be caught in it.*

> "`across_repeats`, not `headline_split`, and the artefact says so in a
> field called `headline_split_warning` that starts 'DO NOT QUOTE THE GBM
> ROWS OF headline_split'.
>
> The reason is a real instability I measured rather than assumed.
> Multiplying the attraction matrix by one-plus-1e-12-times-a-standard-normal
> — a perturbation far below the precision of any input, about what a parquet
> float round-trip costs — moves the GBM's top-10 on that single split by up
> to 2 of 38 decisions over three draws. The conditional logit at 19 and the
> raw count at 20 do not move at all, in any draw. So the single-split GBM
> figures are a draw from LightGBM's histogram bin boundaries, not a
> measurement.
>
> Two honest riders. It is **not fixed by a determinism flag** — I tested
> `deterministic=True, force_row_wise=True` against every arm and got
> bit-identical counts in all eight comparisons, because the call was already
> reproducible on identical input; the instability is sensitivity to the
> *data*, which no flag removes. And `across_repeats` is stable to about half
> a decision rather than exactly, because `raw_count`'s own mean moved 0.5 in
> one draw. I left the flags off deliberately: setting them would cost a
> re-emit of published numbers and buy a false sense of a fix."

### 0.4. "You have no standard errors." ⚠

*You do now, and they say the coefficient is not distinguishable from the
null. That is a better answer than the one this question expects, but only if
you give the negative result first and the "we computed it" second. Reversing
that order turns a concession into a boast about plumbing. And do NOT reach
for the conformal sets as a substitute — different object, and at the 90%
level they are nearly vacuous.*

> "For most of the day that was true, and it was the largest gap in the
> project. It is no longer true, and what the intervals say is not good news
> for the model.
>
> **First, the thing that makes the table readable.** Households is fixed at
> 1 as the numeraire, because the model is scale-invariant and only ratios of
> coefficients are identified. So every interval is an interval on 'how many
> households one unit of this covariate is worth', and **the null that matters
> is one, not zero.** A reader who applies the usual 'does it cover zero'
> habit reads this backwards.
>
> ```
>   56 training decisions across 38 metros, alpha 0.05
>   1,000 bootstrap replicates over decisions, 1,500 over metros
>
>   warehousing_establishments, beta 1.4428 -- the only interior parameter
>     sandwich, 95%              [0.734,  2.835]
>       z against the ratio 1             1.064    p = 0.287
>     bootstrap over decisions   [0.760,  4.762]   11.8% below 1
>     bootstrap over metros      [0.702, 10.013]   13.4% below 1
>     BCa                        [0.714,  3.522]
>     ALL FOUR COVER 1.0.
>
>   land_area_sqmi     beta 3.0e-16   AT THE BOUNDARY
>   establishments     beta 4.7e-16   AT THE BOUNDARY
>     sandwich refused for both; one-sided bootstrap instead,
>     with about 80% of replicates sitting at the boundary
> ```
>
> So: the one covariate that does any work in my model is **not
> distinguishable from one more household**, at p = 0.287. That is the
> outcome I pre-registered. ADR-0004's residual-risk section said, before any
> of this was run, that the most likely result was wide intervals covering
> the null, and named the bootstrap as the diagnostic that would show it. The
> diagnostic was run and the prediction held.
>
> It is also exactly consistent with the ranking result in Sec. 0.3. A
> coefficient you cannot tell apart from the numeraire is precisely the
> coefficient you would expect to add nothing over a raw count.
>
> **The part that is genuinely hard, and my specification did not notice
> it.** Two of the three free parameters are on the boundary. Because
> `beta = exp(theta)`, `beta = 0` means `theta` goes to minus infinity. A
> sandwich estimator is derived from the asymptotic normality of the score
> at an *interior* maximum where the gradient vanishes in every direction —
> Train Section 8.6, page 201. At a boundary the gradient does not vanish,
> the Hessian block is not the information matrix the asymptotics assume,
> and a standard error computed there would not be a wide number. It would
> be a meaningless one. So the code refuses to print one and prints the
> reason instead. The bootstrap survives, because it does not need an
> interior optimum, but its interval is one-sided with an atom at zero. The
> two halves of my own prescription are not equally available, and Section
> 6.3 asks for both as though they were.
>
> **There is a third level I also missed, and the numbers show it.** The
> specification says resample buildings rather than rows, which is the lesson
> the hazard model taught. But the 100 loaded national facilities sit in only
> 62 metros and Los Angeles alone contributes seven, all facing the same
> choice set with the same attraction values. Resampling decisions treats
> those seven as seven draws; resampling metros treats them as one. The upper
> endpoint moves from 4.76 to 10.01 — a factor of two — so it is not an
> academic distinction. The metro-clustered figure is the conservative one
> and it is the one I quote. That is the same clustering error that killed
> the first model, showing up a third time, one level further up.
>
> **And Train's own precondition fails.** Section 8.6, page 202: the
> bootstrap works 'if this sample is large enough, then it is probably
> similar to the population'. At 56 decisions that is exactly the clause in
> doubt. These intervals measure how much the estimate moves with *which of
> my 56* are included. That is a real quantity. It is not sampling
> variability over the population of siting decisions, and the artefact
> carries that quotation so a reader cannot miss it."

**If they press: "then how do you know anything you have said is real?"**

> "At the level of a coefficient I do not, and the interval is how I know I
> do not — which is the point of computing it. What I can defend is the
> held-out ranking comparison, because it does not depend on an interval: two
> procedures scored on the same 38 decisions, and the one with no parameters
> does just as well. If you ask whether *that* difference is significant, the
> honest
> answer is that 19 against 20 out of 38 is noise, and I am not claiming the
> benchmark is reliably better. I am claiming the estimation has not been
> shown to help, which is weaker and defensible."

**If they press: "when exactly did this land?"** — *answer plainly; the
alternative is looking as though you back-dated it.*

> "On the last day, and it was uncommitted when I wrote the document up. I
> would rather say that than imply it had been there all along. What it does
> not do is change any conclusion: the ranking result was already in, the
> intervals agree with it, and the pre-registration that predicted them
> predates both."

---

## Part 0B — The eight questions the 2026-09-15 results create

**Added 2026-09-15. Read this part after Part 0 and before anything else.**

Between 14 and 15 September the project did five things, and each of them
creates a question an examiner will now ask that is not answered anywhere
above:

```
  1  OCR'd an industry PDF into 1,904 facilities and expanded the
     facility panel from 104 rows to 693
  2  wrote a pre-registration, fitted a metro-level entry model
     against it, and lost
  3  revived the retired hazard model on the expanded panel and
     lost again
  4  found a rule that predicts covariate failure BEFORE fitting
  5  audited its own figures and found two of them fabricated
```

Sections 0.5 to 0.12 are the eight questions that follow. Every one of them
concedes first. **The concession is not a rhetorical move — it is the only
thing in this project that an examiner cannot take off you.**

```
  0.5   the pre-registration failed -- why credit it?
  0.6   1,904 facilities and the model got worse
  0.7   your model is one variable
  0.8   you wrote figures with hand-typed confidence intervals   <- hardest
  0.9   isn't a null result just a failed project?
  0.10  why use your cost model when your prediction model fails?
  0.11  fifteen covariates, none worked -- a fishing expedition?
  0.12  one of your notes says an interval excludes 1.0         <- a trap
```

### 0.5. "You pre-registered a hypothesis and it failed. Why should I credit the pre-registration rather than see it as a failed project?" ⚠

*Concede the loss in the first sentence. Then the argument, which is that a
pre-registration is only worth anything on the day it costs you something,
and this is that day. Do not claim you planned to lose.*

> "It failed, and I would rather say that than 'the results were mixed'. H1
> lost both of its clauses in every arm. Zero of seven held-out years on AUC,
> three of seven on calibration where a majority was required. The verdict is
> H0.
>
> Here is why I think the pre-registration is worth something anyway, and you
> can decide whether it is enough.
>
> **First, it is checkable, not claimed.** `docs/PREREG_METRO_MODEL.md` was
> written on 2026-09-15 before anything was fitted.
> `outputs/metrics/metro_entry.json` records the file path *and its md5* —
> `946f7ef75db69e5278eea409a04c3823` — so you can verify that the document I
> registered is the document on disk. If I had edited it afterwards, the hash
> would not match.
>
> **Second, it wrote both outcomes' language in advance.** Section 7 contains
> two paragraphs, one for H1 and one for H0, written before the fit. The
> finding I am reporting is the H0 paragraph, quoted without softening:
> *'Free public data cannot predict siting at any grain tested. The ZIP-level
> failure is not a resolution problem but a general one: the variables that
> drive the decision are not public at any resolution.'* I did not get to
> choose the sentence after seeing the number.
>
> **Third, it named five ways the test could be invalidated, before the
> test.** Section 8. One of them was 'selection on the outcome' — restricting
> the universe to the 195 metros that actually received a facility. That
> restriction would have produced a much better-looking result, and the
> prereg forbade it in writing, so the universe is all 935 CBSAs. Another was
> 'beating only the uniform baseline', which the prereg calls trivial at 935
> metros. The model *does* beat the uniform baseline in all seven years, and
> that is exactly the number the prereg told me in advance not to quote.
>
> **Fourth — and this is the one that convinced me — the prereg cost me the
> thing I most wanted to say.** Section 4 registered twelve covariates. The
> vintage rule in the same section then killed eight of them, and a coverage
> floor killed two more, so the verdict arm has two covariates. That is a
> weak model and I would rather it were not. But the rule that made it weak
> was written before I knew it would bite.
>
> **And the reason this project needed one at all is a measurement.** An
> honest nested forward selection — choosing covariates inside each training
> fold — came out **worse than adding nothing** on the project's headline
> metric: large-metro top-10 lift **6.2413 against the baseline's 6.3889**,
> a delta of **-0.1476**, and -0.1640 at top-1
> (`outputs/metrics/covariate_search.json`, `core.arms`). Selection is itself
> a parameter, and at this sample size fitting it overfits. Choosing a
> *framing* after seeing a result is the same error one level up, and I had
> already made the smaller version of it.
>
> *(Be precise if pressed: the search is not worse on every metric — it is
> **+0.2378** at top-5 in large metros and +0.0042 on pooled top-10. The
> honest sentence is 'it does not help on the metric I registered, and it is
> noise on the others', not 'it is uniformly worse'. And note the prereg
> itself says '0.72 points WORSE'; I cannot reproduce 0.72 from
> `covariate_search.json` under any stratum or k, so quote -0.1476 and not
> 0.72.)*"

**If they press: "you would be saying the same thing if it had won."**

> "No, and the artefact shows it. Section 7 of the prereg says of the H1
> outcome that the boundary would sit 'between the county and the ZIP code'
> and a community 'can learn that its region is on the list'. That is a
> different and more marketable finding than the one I have. If H1 had won I
> would be telling you a better story, and the prereg is the reason you could
> check that I had not written that story first and fitted towards it."

**If they press: "so what is the residual — where is the prereg wrong?"**
*This is the strongest single move in this answer. Volunteer it.*

> "Three places, and they are listed in `NOTES_METRO_ENTRY.md` §12, written
> by the same run that reported the verdict.
>
> One: section 4 registered Tier 1 and Tier 2 covariates the panel cannot
> supply in a time-respecting form. A two-line check of distinct values per
> unit would have caught that before the list was fixed. The covariate list
> should have been three or four columns long, and the prereg should have
> said so.
>
> Two: section 5's households baseline and section 4's vintage rule are in
> direct conflict given a single ACS vintage on disk, and the prereg does not
> say which wins. The run resolved it against the hypothesis — the baseline
> is scored on a column the model is not allowed to see, which biases the
> comparison *against* H1. That is the conservative direction for the finding
> I reached, and it is the reason a narrow H1 win under that arrangement
> would not have been safe to report.
>
> Three: section 9 does not say which model form carries the verdict, having
> required two in section 5. It made no difference — logistic, Poisson and
> negative binomial agree to within 0.0001 of AUC in every year — but it
> could have.
>
> None of those change the outcome. All three are the kind of thing that is
> only visible once a prereg meets the data, which is an argument for writing
> one rather than against it."

### 0.6. "You found 1,904 facilities and the model got *worse*. Explain that." ⚠

*The examiner has spotted a real thing and the first word must be "yes". The
answer has two halves and you need both: the pooled number fell for an
arithmetic reason that is not about the model, and the sample genuinely did
get harder. Do not lead with the Simpson's paradox — it sounds like an
excuse until you have conceded the number.*

> "Pooled top-10 lift fell from 2.95x to 2.76x on five times the sample, and
> that is the right number to put on the table first. Two things are going
> on, and only the second is about the model.
>
> **The pooled figure is a Simpson's paradox and it was misleading the day it
> was written.** A top-10 lift depends on how many alternatives are in the
> choice set. In a metro with 25 candidate ZIPs, a uniform guess already
> lands in the top ten about two thirds of the time, so lift there is capped
> near 1.5x however good the model is. The MWPVL rows are weighted towards
> small markets: decisions with 25 or fewer alternatives went from 7 of 94 to
> 66 of 485 — 7.4% of the question mix to 13.6%. So the pooled figure moved
> because the *mix of questions* moved.
>
> ```
>   choice-set size    original (n, top-10 lift)   expanded (n, lift)
>   -----------------------------------------------------------------
>   small  <= 25            7      1.66x              66     1.44x
>   mid    26-100          41      2.67x             162     3.09x
>   large   > 100          46      6.14x             257     6.42x
>   -----------------------------------------------------------------
>   POOLED                 94      2.95x             485     2.76x
> ```
>
> The pooled number falls while no stratum falls except the one where lift is
> capped by construction. Standardised to a common market mix — which is the
> like-for-like comparison — it is 2.858 to 2.706
> (`outputs/metrics/lift_by_market_size.json`, `finding_correction`, and the
> artefact is retired in favour of `panel_experiments.json` for exactly this
> reason).
>
> **Now the half that is about the model, and it is the honest half.** Read
> held out, over 50 re-splits, against an analytic chance rate rather than a
> tie-broken empirical one, large-metro top-10 lift goes **6.1804 on the
> 94-decision panel to 6.2585 on the 483-decision one** — 6.2903 if you also
> add the network proximities (`outputs/metrics/panel_experiments.json`,
> `arms.<arm>.methods.conditional_logit.strata.top10.large_gt100.lift`). That
> is flat. Five times the sample bought nothing measurable in the stratum
> where siting is actually contested.
>
> So the correct sentence is not 'it got worse'. It is **'it did not get
> better, and the pooled figure that made it look worse is a mix effect'**.
> Both halves are unflattering and I would give you both."

**If they press: "then what did the extra 589 facilities buy?"**

> "Precision, which is what the module docstring said to look for *before*
> the run — `refit_expanded.py` lines 27-39 states the reading rule in
> advance: 'the thing to read is not which top-10 is higher. It is whether
> the coefficient intervals finally exclude the numeraire — that is what the
> extra sample was for.'
>
> ```
>   warehousing_establishments   n_decisions   interval
>   ----------------------------------------------------------------
>   original pilot panel             94        1.528  [0.985, 2.550]
>   expanded panel                  483        1.191  [0.956, 1.490]
> ```
>
> The interval is 64% narrower and it still contains 1.0, with the point
> estimate moved *towards* the numeraire it was supposed to escape. So the
> binding constraint was never sample size. That is a real finding and it is
> the one the extra data bought.
>
> `outputs/metrics/refit_expanded.json`. And note that same file's own
> caveat, which I did not write afterwards: the added rows are OCR'd, at
> least one duplicate survived the screen, 72 entered unscreened, and about
> 3% of OCR rows merge with a neighbour."

**If they press: "did harder decisions enter the set?"** *Answer precisely.
The measured statement is about market-size mix, not about difficulty in some
other sense — do not claim more than the artefact supports.*

> "Measurably, yes, in one specific sense: the mix shifted towards small
> markets where the metric is capped. I would not claim more than that,
> because nothing in the artefacts measures 'difficulty' directly.
>
> There is one place the project *did* measure that its easy cases are
> unrepresentative, and it cuts the same way. The leakage audit could only
> reach 29 of 94 decisions — the ones MWPVL happens to list and the address
> matcher happens to reach — and on those 29 the model scores 9.24 of 12,
> which is 77%, against 54% on the full 94
> (`outputs/metrics/leakage_decisive.json`,
> `../research/NOTES_LEAKAGE_DECISIVE.md` §6). The subset the project can
> audit is measurably easier than the sample it reports on. I say that
> because it limits my own leakage result, not because it helps me."

### 0.7. "Your model is one variable." ⚠

*Concede in three words. Then the point: the *reason* it is one variable is
now measured, and the measurement is a rule other people can use. That is the
contribution — not the model.*

> "It is. Remove `warehousing_establishments` and large-metro lift collapses
> from 6.3889 to 2.7352 — the covariate is worth 3.65 of 6.39, measured on a
> fixed frame in `outputs/metrics/covariate_search.json`. Three of the four
> inputs contribute nothing; the optimiser drives them to the boundary. The
> model is one variable and I lead with that rather than being walked to it.
>
> Fifteen more were tried. **Seven of the fifteen were exact no-ops** —
> identical to the baseline to fifteen decimal places, meaning the model was
> bit-identical with and without them. The best of the fifteen moved lift by
> +0.0082 and the worst by -0.1927.
>
> Two of those fifteen were never independent tests, and I found that
> myself rather than being caught at it.
> `vehicle_availability_total` is not correlated with `households` — it is
> **equal to it**, to floating-point precision, on all 21,768 ZCTAs, because
> ACS table B25044's universe is occupied housing units. And
> `owner_occupied + renter_occupied = households` exactly, so those are one
> test reported twice. **The honest count is thirteen independent candidates,
> not fifteen** (`../research/COVARIATES_TRIED.md` §2.2).
>
> **Here is what the project has instead of a better model.** The failure has
> a diagnosis, the diagnosis has two named mechanisms, and one of them turned
> into a rule you can run before fitting anything. Section 0.11 is that rule.
> If you want the one-sentence contribution: *a conditional choice model over
> ZIP codes can only use covariates that vary within a metropolitan area and
> are not proxies for population, and most free public data is published at
> county grain or is a population count wearing a different name.* That is a
> statement about US public-data infrastructure, and it is testable.
>
> What I will not do is dress the one-variable model up. It is one variable."

**If they press: "then publish the covariate and drop the model."**

> "I would not fight that hard, and Sec. 0.3 gives the two reasons for
> keeping the specification — the choice framework is what makes the
> benchmark comparison legitimate, and it is where the zone-merger invariance
> restriction lives. But if you asked what a city should run tomorrow, it is
> the covariate, not the model."

### 0.8. "You wrote figures with hand-typed confidence intervals. How do I trust anything else in here?" ⚠⚠

*This is the hardest question in the pack and it is harder than 0.2, because
0.2 is about competence and this is about integrity. Do not minimise, do not
say "only two", and do not reach for the mitigations before you have said
what was wrong. Say the whole thing, then make the only argument available:
the project found it, in writing, and the finding is in the repository.*

> "That is the right question and I am going to give you the whole of it
> before I say anything in my defence.
>
> **Figure 5.** It plotted a cannibalisation decay curve. Nine effect values
> were typed by hand into the plotting code. Around them was a shaded band
> labelled '95% CI'. One point was annotated 'n.s.' — a significance test.
> The y-axis was 2-day order volume, **which does not exist in this
> project's data**, and its absence is the documented reason the
> cannibalisation analysis was abandoned in the first place. So the figure
> asserted a causal effect, a confidence interval and a significance test, on
> a variable the project does not observe. The caption said 'values are
> illustrative pending estimation'. That is six words under a chart carrying
> error bars, and figures get lifted into slides without captions.
>
> **Figure 7.** A tornado chart. Eight bucket swings typed in, per-bar dollar
> labels to the cent, and **no disclosure anywhere** — not in the figure, not
> in the caption. Its caption asserted 'four primary buckets account for
> roughly three-quarters of the swing in net present value' as measured fact.
> No artefact supports it: `montecarlo_report.json` carries aggregate bands
> over 500 draws and no per-bucket decomposition, so it cannot be rebuilt
> from data.
>
> That is the charge and I am not going to reduce it. A hand-typed confidence
> interval in a submitted document is the single most damaging thing a
> reviewer can find, and it was in mine.
>
> **Now the only thing I can say for the project, and you should weigh it for
> exactly what it is worth.** Nobody caught this. The project caught it, in
> its own audit, and wrote it down before anyone asked. The finding is in
> `docs/data/FIGURES.md` under a heading that reads 'What is committed: an
> *invented* interval', and it quotes the offending lines of my own code back
> at me. The remediation is in `tools/figures/fig_methods.py`, in the
> docstrings of the two functions, and it says what was wrong and on what
> date:
>
> - the interval and the significance annotation are gone
> - the curve is dashed, and the y-axis carries no numbers at all
> - the tornado's per-bar dollar labels are gone, because they were false
>   precision on invented numbers
> - an **ILLUSTRATIVE ONLY** banner sits *inside the axes* on both, so it
>   travels with the image when the chart is cropped into a slide
>
> **And the same document clears an adjacent suspicion rather than taking the
> chance to look better.** There was a worry that a re-split spread had been
> drawn as a confidence interval somewhere. It had not: the one figure with a
> band carries a footer saying 'the band in panel A is that two-sigma spread,
> not a confidence interval'. I mention it because a document that only ever
> confesses is as unreliable as one that never does.
>
> **What you should take from the whole episode.** Not that the project is
> clean — it was not. That the project has a mechanism that finds this class
> of error, that the mechanism ran, and that its output is in the repository
> where you can read it and where it embarrasses me. If you want to test
> whether I am telling the truth about anything else in this viva, that
> document is the place to start, and I would rather you started there than
> anywhere else."

**If they press: "why should I believe the fix is complete?"**
*Do not claim it is. Give the standing exposure.*

> "I should not claim it is complete, so I will give you the two things that
> are still open.
>
> The fix removed the *false precision*, not the *invented magnitudes*.
> Figure 7 still draws eight typed-in swings; what changed is that they carry
> no axis numbers and no labels, and the claim has been reduced to the
> ordering — which is defensible from the cost model's own structure, because
> driver time at the door is 66.5% of the per-stop bill in
> `cost_report.json`. To make it real you would decompose the 500 Monte Carlo
> draws by bucket. That is about a day's work and it is listed as open, not
> as done.
>
> And the precedent is worse than two figures. The same defect class had
> already been purged from two *other* figures earlier —
> `tools/figures/fig_backtest.py`'s own docstring records that figure 8 had
> printed a target AUC of 0.84 under an ROC curve synthesised to have that
> area, and figure 9 had invented eight ZIP codes and their rank-stability
> shares. So this is the second time, not the first. The honest reading is
> that the project has a recurring habit of drawing the result it expects and
> a review process that keeps catching it late."

**If they press: "is the audit that found this actually in the repository?"**
*Answer precisely. This is a trap you must not walk into.*

> "On disk, yes. Under version control, no — and that matters, so I will be
> exact about it. `docs/AUDIT_2026_09_14.md` is untracked, and so are
> `docs/data/FIGURES.md`, `docs/data/ARTEFACTS.md` and several of the
> research notes. The two code fixes — the figure remediation in
> `fig_methods.py` and the two guards in `choice.py` — *are* in tracked
> files.
>
> The consequence is the awkward one and you may as well have it from me: a
> clean clone of the repository today contains some of the retracted material
> and not all of the retractions. Committing them is a five-minute job that
> has not been done, and 'it is on my disk' is not an acceptable answer for a
> document whose whole purpose is to be checkable."

### 0.9. "Isn't a null result just a failed project?"

*Do not reach for "negative results are valuable" — it is true and it sounds
like a slogan. Make the argument specific to this project: a null is worth
something when it is (a) pre-registered, (b) measured against a named
alternative, and (c) diagnosed. This one is all three. Then concede the
version of the charge that lands.*

> "Sometimes it is. A null result is a failed project when you cannot say
> what would have counted as success, or when the null is just an
> under-powered study wearing a conclusion. Let me show you which of those
> apply.
>
> **It is not under-power.** That was the original story and it is now
> measured to be false. The hazard model was retired on 39 events; it was
> revived on the expanded panel with 5,441 events and real opening dates and
> the AUC moved from 0.6894 to 0.6832 — it went *down*. Effective events per
> parameter went from 5.6, below the floor of 10, to 87.2. The obvious
> objection — 'you never gave it enough data, or real dates' — has now been
> answered with a measurement rather than an argument
> (`outputs/metrics/hazard_revival.json`).
>
> **It is not undefined.** The metro test had a numeric success criterion
> written down before the fit, and the artefact records the arm that carries
> the verdict as declared at stage 1, before a single model was estimated.
>
> **It is not a single failure.** At ZIP grain the fitted model lost to a
> warehouse count. At metro grain the fitted model loses to a household
> count — in every year, under every model form, with and without the
> pandemic years, in every size tier, and whether or not it is allowed to
> cheat on vintage. In both cases a single free public column already
> contains everything the model recovered.
>
> **And it is diagnosed.** I can tell you the mechanism: a conditional choice
> model uses only within-choice-set variation, most free public data is
> published at county grain or is population under another name, and there is
> a number — the within-metro coefficient of variation — that predicts which
> side of the line a covariate will land on before you fit it. Section 0.11.
>
> **Now the part of your question that lands.** A null result is worth less
> than a positive one, and I would not argue otherwise. What I would argue is
> that the specific null here is a statement about public data infrastructure
> rather than about my model, that it is the harder of the two outcomes my
> own pre-registration described, and that the prereg calls it 'arguably more
> valuable, because it says the transparency gap is structural rather than an
> artefact of one model's grain'. I did not write that sentence after seeing
> the answer."

**If they press: "one qualification you should be giving me?"**
*Give it before they find it. It is the largest hole in the H0 claim.*

> "Yes, and it belongs in the same sentence as the claim. The metro run
> tested whether free public data adds anything to *knowing how big a place
> is*. It did **not** test the construction and freight covariates that
> motivated the hypothesis in the first place, because the vintage gate
> removed them — no time-respecting vintage of them exists in this panel. So
> the Tier 1 mechanism that generated H1 was never testable here.
>
> That is a finding about data availability rather than about the
> hypothesis, and it points at the same conclusion from a different
> direction: the covariates that might have distinguished one metro from
> another are published once, late, and without a usable history, which is
> itself a form of the transparency gap. But it is a qualification and it
> should not be buried in a footnote. `NOTES_METRO_ENTRY.md` §8 puts it in
> the body for that reason."

### 0.10. "Why should a county use your cost model when your prediction model does not work?"

*The answer is that they are independent objects with independent evidence,
and the cost model never touched the facility panel. Say that, then be
specific about what the cost model can and cannot do — including the thing it
cannot do, which is rank sites.*

> "Because they are different objects and the second one's failure is not
> evidence about the first. The cost model does not read the facility panel
> at all — not one column — so none of the upheaval in the siting work
> touches it. That is not a convenient claim; it is a structural fact about
> which module imports which.
>
> **What it is.** Given a ZIP code, what does it cost to deliver one parcel
> there? Nobody publishes that. It is computed from geography and physics,
> using Daganzo's continuous approximation (1984): a van drives out, makes
> many stops, drives back, and cost per parcel falls as one over the square
> root of drop density. Published method, sourced parameters.
>
> **What it produces.** Median $1.083 a parcel, p10 $0.99, p90 $1.36;
> cheapest metro Miami at $0.95, dearest Boise at $1.31; 2,333 ZIPs costed
> and 334 depots solved. Decomposed per stop: 66.5% driver time at the door,
> 22.8% vehicle lease, 7.4% driving, 3.3% fuel. Stress-tested across five
> scenarios spanning -17% to +4.4%.
>
> **What a county actually gets from it.** A defensible answer to 'is this
> site cheap to serve, and by how much, and what drives that'. That is a
> question about *their own geography*, and their geography is fully
> observed. It is not a question about Amazon's intentions, which is the
> question the public record cannot answer.
>
> **And here is the thing I would say unprompted, because it is the most
> useful sentence in the project and it comes out of the cost model
> failing at something.** Of 40 facilities ranked by cost-to-serve within
> their own metro, **none** sits in its metro's cheapest 10% — chance would
> give 10%. So the cost model cannot rank where Amazon will build, and that
> is the model working rather than breaking: the cheapest places to serve are
> the densest, and the densest are exactly where a warehouse cannot be built.
> **Feasibility binds before economics.** A county that internalises that one
> sentence will make better decisions about which parcels to zone than one
> that has my prediction model."

**If they press: "so what should a county NOT use it for?"**

> "Three things, and they are the ones it would be tempting to use it for.
> Not to predict whether a facility is coming — that is the model that
> failed. Not to price a specific building, because the parameters are
> national averages and `parcels_per_depot_per_day` is unsampled, which makes
> every uncertainty band in the report a floor rather than an interval. And
> not to argue about dollar NPVs, because the cannibalisation penalty feeding
> the NPV is assumed — 20 km, linear decay, 0.18 peak — not estimated, and
> the study that would estimate it was never built. That is why the outputs
> we lead with are rank stability and a break-even frontier rather than point
> NPVs."

### 0.11. "You tested 15 covariates and none worked. Is that not just a fishing expedition?" ⚠

*The charge is fair on its face and the answer is not "but I corrected for
multiple comparisons". It is that the failures resolved into a rule that is
**prior** — it scores a covariate before any model is fitted — and that the
rule was then tested causally with a knob. Lead with the rule, not with the
defence.*

> "It would be a fishing expedition if the fifteen were a search for
> something that worked. Two things make it not one, and the second is the
> real answer.
>
> **First, none of them worked, and I reported all fifteen.** A fishing
> expedition is defined by what you don't report. The table is in
> `../research/COVARIATES_TRIED.md` §2, all fifteen rows, with the lift, the
> delta and the reason for each. Seven were exact no-ops. And when a search
> *was* run properly — nested forward selection choosing covariates inside
> each training fold — it came out **worse than adding nothing on the metric
> I registered**: 6.2413 against the baseline's 6.3889, a delta of -0.1476
> (`outputs/metrics/covariate_search.json`, `core.arms`). That is the
> measurement that says selection at this sample size is itself an overfitted
> parameter. I reported it too, and I would add the qualification unprompted:
> the search is *not* worse on every metric — it is +0.2378 at top-5 in large
> metros — so the claim is "it does not help", not "it is uniformly worse".
>
> **Second, and this is the point: the failures resolve into a rule that runs
> *before* you fit anything.** A conditional choice model compares
> alternatives inside a choice set and differences away everything between
> choice sets. So a covariate's only currency is how much it varies among the
> ~200 candidate ZIPs of one metro. Measure that — the within-metro
> coefficient of variation — over 21 network terms, 41 large metros, 8,271
> candidate ZCTAs (`outputs/metrics/gravity_network.json`,
> `terms.dispersion`, run `20260915-210603-b780`):
>
> ```
>   within-metro cv         n     outcome
>   --------------------------------------------------------------
>   below 0.6               7     7 of 7 land on the boundary
>   0.6 to 1.3              0     the region is EMPTY
>   above 1.3              14     8 interior, 6 not
>   --------------------------------------------------------------
>                          21
> ```
>
> **I am going to state this carefully, because it is the project's one
> transferable result and it is easy to overstate — and this repository has
> overstated it.** What the measurement supports is: *low within-metro
> dispersion is **sufficient for failure**, seven times out of seven, and
> nothing at all falls between 0.60 and 1.40. High dispersion is **necessary
> but not sufficient** — six of the fourteen terms above the line still
> fail.* So it is a screening rule for **rejection**. You can score any
> column in seconds before a model exists, and below about 0.6 you should not
> bother. That alone would have saved most of the fifteen.
>
> **And it is not a correlation I noticed afterwards — it was tested with a
> knob.** Eighteen of the 21 terms are the same gravity measure at three
> settings of an exponent. Turning that exponent from 1 to 3 changes nothing
> about what is being measured — still proximity to the same facilities — and
> changes only how sharply the measure discriminates within a metro.
> Following one column: fulfilment gravity walks 0.2975 → 4.3630 → 6.8194,
> and the coefficient walks from the boundary to the interior with it. That
> isolates the grain mechanism from every other property a column could have.
>
> **It also explains a failure that previously had no explanation**, which is
> the thing that made me believe it. A *count* of facilities within a radius
> failed at 25, 50 and 100 miles, while a *distance* to the same facilities
> worked, and nobody could say why. The count sits at cv 0.5918, just under
> the line. The radius was never the issue."

**If they press: "you said 21 of 21 in your glossary. Which is it?"** ⚠
*This will be asked if they have read both documents, and there is only one
acceptable answer.*

> "The 21-of-21 wording is wrong and I would rather correct it than defend
> it. It appears in my own prereg §2, in two research notes and in an earlier
> draft of the glossary, and it is wrong in two ways. There are 21 terms in
> total, not 21 on each side — written as two lines it implies 42
> observations that do not exist. And the upper half has counter-examples:
> `sortation_gravity_count_sqft_subset_a2` sits at cv 5.2999, four times the
> threshold, and its interval still contains the boundary. On the current
> artefact five more join it.
>
> Worse for me, the note that states the rule contradicts itself about this.
> §3.1 says 'all but one of the twelve alpha >= 2 columns are strictly
> interior' and §5 then says the outcome tracks dispersion 'without an
> exception'. §3.1's 'one' *is* §5's exception, and §5's table prints 13 of
> the 21 columns with the counter-example among the eight it omits. I do not
> think that was deliberate and I am not going to argue that it reads well.
>
> The correct claim is the one I gave you: 7 of 7 below the line fail, the
> region between 0.60 and 1.40 is empty, and 8 of 14 above it work. The empty
> region is the strong part and it is the part I would build on."

**If they press: "why did the county-grain variables fail, concretely?"**

> "Because there is nothing in them to rank with. Six of the eighteen columns
> audited are county figures broadcast to every ZCTA in the county — about
> **nine distinct values across two hundred candidate ZIPs**. You cannot rank
> two hundred things with nine numbers, however important the thing being
> measured. And this is not a data-quality problem: `traffic_proximity` is
> populated on 99.9% of rows. It is a grain problem, and collecting more
> county data does not fix it.
>
> The other mechanism is collinearity with the numeraire. Five ACS candidates
> correlate 0.84 to 1.000 with households within metro. The model cannot tell
> 'attractive because people live here' from 'attractive because people live
> here and therefore own cars'. Those two are not symmetric in their
> consequences, incidentally: a boundary coefficient is inert and harmless,
> while a collinear one is destabilising — `in_labor_force` takes a median
> coefficient of 7.0e12 with an interval spanning fourteen orders of
> magnitude, and it drags the one covariate that works along with it."

**If they press: "does the rule hold outside this project?"**
*Do not overclaim. This is the one place in the answer where you must not.*

> "Untested outside this project, and I would say so before claiming
> anything. What I can say is what makes it plausible: it falls out of the
> mathematics of the conditional logit rather than out of this dataset, it
> was confirmed on a knob that varies nothing else, and it retrodicted a
> failure it was not built from. The two thresholds — 0.6 and 1.3 — are the
> edges of an empty region in twenty-one observations, not estimated
> parameters, and I would not defend those specific numbers anywhere else.
> The shape of the rule is the claim; the constants are this panel's."

### 0.12. "One of your notes says an interval excludes 1.0. So something IS significant?" ⚠

*This is a trap and you must not step into it. The claim was withdrawn. The
withdrawal is in the repository, but so is the original — several research
notes still print the number with a withdrawal banner above it, so an
examiner reading quickly can find the claim without the retraction. **Nothing
in this project is statistically distinguishable from its null.** Say that
first.*

> "No. That claim was withdrawn on 2026-09-14 and I would rather correct it
> than let it stand.
>
> The original sentence said `combined_plus_network` was the first
> specification in the project's history whose warehousing interval excludes
> 1.0 — **1.401 [1.037, 1.869]**. The problem is that that bracket is a
> percentile spread over 50 re-splits, and **a re-split spread is not
> inference**. It describes how the estimate moves across partitions of one
> fixed sample. It says nothing about drawing a different sample.
>
> Asked properly, on the same arm:
>
> ```
>   re-split percentiles        1.4009  [1.0368, 1.8683]   EXCLUDES 1.0
>     -- not a standard error
>   MLE on all 485 decisions    1.3120       --
>   bootstrap over 194 metros   1.3120  [0.9769, 1.9195]   contains 1.0
>   sandwich, metro-clustered   1.3120  [0.9606, 1.7922]   contains, p=0.088
>   sandwich, independent       1.3120  [0.8637, 1.9932]   contains, p=0.203
> ```
>
> **All three estimators that are inference contain 1.0. The one that
> excluded it is the one that is not inference.**
>
> Two details I would add rather than be asked for. **The point estimate was
> never 1.40 on all the data** — 1.4009 is the mean of exp(theta) over 50
> fits on 291 training decisions each; the maximum-likelihood estimate on all
> 485 is 1.3120. And the margin was never comfortable even on the wrong
> bracket: the lower end cleared 1.0 by 3.7%.
>
> **The strongest form of the withdrawal is a Monte Carlo argument, and it
> says the retraction will not be reversed by more computation.** 17 of 500
> clustered replicates fall below 1.0, against the 2.5% that an exclusion
> needs — and the 2.5th percentile sits 0.94 of its own Monte Carlo error
> from 1.0. So more replicates would *sharpen* that sentence, not move it.
> The correct statement is that **the lower endpoint is indistinguishable
> from exactly 1.0**, which is weaker than 'contains' and much weaker than
> 'excludes'.
>
> What does survive, weakly, is the two network proximities: sortation 0.110
> [0.007, 0.255] and fulfilment 0.164 [0.007, 0.419], both strictly above
> zero. But 'interior in every one of 50 re-splits' does not survive either —
> 2.2% and 2.4% of clustered replicates land exactly at zero."

**If they press: "why is the withdrawn claim still in your repository?"**

> "Because deleting it would be worse. The note carries the original
> paragraph with a withdrawal banner above it and a section — §12, 'The
> headline, tested properly. It does not survive.' — that shows the work. A
> reader can see what was claimed, what was run, and why the claim went away.
> What I will concede is a presentation failure: the banner is above the
> paragraph and the paragraph is quotable on its own, and the note is one of
> the files that is not under version control. If you found the claim without
> the retraction, that is my fault and not yours."

**And one adjacent thing to get right.** *There is a second, unrelated
withdrawal in ADR-0004 — the "beats vs matches" correction about the raw
count, and a density-preference claim withdrawn from the proposal. Do not
merge the three into one story. They are separate errors with separate
fixes, and conflating them makes it sound like one large retraction rather
than three small ones.*

---

## Part A — Novelty and positioning

### A1. "Amazon already does this. Did you just copy a paper? What is new?"

*This is the strongest card in the pack, because the answer is evidence
rather than assertion. The full derivation is in
`docs/METHODS_RESEARCH.md` Section 4; what follows is what you say out
loud.*

> "There are two definitive papers and I did not copy either, because
> neither one studies the facility I study, and neither one could have been
> reproduced by someone without a purchase order.
>
> **Holmes, *Econometrica* 2011**, on Wal-Mart's rollout. His Section 3 says
> the store-level data 'was obtained from Trade Dimensions, a unit of
> ACNielsen'. Purchased.
>
> **Houde, Newberry and Seim, *Econometrica* 2023, 91(1) 147-190**, on
> Amazon's network. Their Section 2.2 says they obtain the network 'from the
> supply-chain consulting company MWPVL, International'. Also purchased.
>
> Now the part that settles it. Their Section 1 says 'We focus on two types
> of facilities: fulfillment centers and sortation centers', and they
> explicitly drop specialised centres including PrimeNow Hubs. I searched
> their published text for 'delivery station'. **Zero hits.** 'Last-mile'
> returns three, two of them in footnotes, and one of those says Amazon
> began investing in last-mile delivery *after* their sample ends.
>
> So the difference is on three axes and I can name each one.
>
> | Axis | Holmes 2011 | Houde et al. 2023 | This project |
> |---|---|---|---|
> | Facility | Wal-Mart stores and DCs | Fulfilment and sortation; PrimeNow dropped | **Delivery stations** |
> | Data | Trade Dimensions, purchased | MWPVL, purchased | **Federal OSHA records, free** |
> | Question | Economies of density in rollout | Did nexus tax law distort the network | **Who gets served, and can a city check it** |
>
> Facility type: delivery stations, unstudied in either paper. Data
> provenance: 5.2 million federal OSHA inspection records, free and
> reproducible by anyone with a laptop. Question: who gets served and can a
> city verify it, rather than nexus tax policy.
>
> What I do **not** claim is a new estimator. Both of those papers use the
> same revealed-preference machinery and if I go that route I will be using
> theirs. The claim is grain, data regime, and question."

**If they press: "is a new dataset really a contribution?"**

> "On its own, no. What makes it one here is that it is the *only* free
> route to this facility class, and the route itself is a finding: six
> collection methods failed before one worked, and the one that worked
> measures something other than an opening date. Both halves of that are
> written down. A reader who wants to redo this on their own metro now knows
> which four days not to spend."

**One correction to make if it comes up.** An earlier draft of the
`EXPLAINER` said Houde et al. worked "at state grain". That is wrong. Their
demand side is at county grain and their supply side is a 20-mile cluster;
state is the unit of the *tax* variation, not of the analysis. If you have
said "state grain" in a practice run, unsay it.

### A2. "How is this different from what companies already sell?"

> "Esri ships a tool literally called Measure Cannibalization. Coupa, AIMMS and
> Optilogic have sold multi-facility network optimisation for twenty years.
> Buxton and Placer.ai sell site scoring. None of that makes our work wrong
> — it makes the word 'first' naive, so we never use it.
>
> The distinction that survives is methodological, and I have to state it
> carefully because the obvious version of it is a trap I could walk into.
> Commercial cannibalization tooling measures *trade-area overlap*, which is
> descriptive geometry. It answers 'how much do these two areas share?'. It
> does not answer 'what would volume in B have been if A had never opened?'
> — there is no counterfactual and no donor pool in it. What I must not add
> is 'and no standard error', because **I do not have one either**: my
> cannibalisation parameter is a number I typed, 0.18, and nothing in this
> project has a standard error on anything. The difference I can defend is
> that our estimand is a counterfactual and theirs is an overlap statistic.
> Ours is a causal *design*, not yet a causal *estimate* — the estimate has
> not been built.
>
> And structurally: every one of those tools models *your own* network from
> *licensed* data, for a client who paid. None forecasts a competitor's network
> from public data, and none can be inspected by a city council."

### A3. "Isn't the LLM part just a chatbot?"

> "If we led with the chatbot, that would be a fair criticism — every
> applicant has a RAG project in 2026. The interesting part is not that it
> answers questions. It is that it *writes* to a causal model, and that we found
> the existing safety literature does not cover that case."

### A4. "Why should I believe your novelty claims when you got them wrong before?"

> "Because we checked and reported the result. Three claims we would have liked
> to make did not survive: that nobody gates AI writes, that spatial
> econometrics fixes the weight matrix, and that we react faster than the
> operator. Each was falsified by published work or was a category error. We
> withdrew all three and narrowed the rest until a product datasheet cannot
> disprove them. The audit is the reason to trust what is left."

---

## Part B — Method and identification

```
  +------------------------------------------------------------------+
  |  STATUS BANNER -- READ BEFORE USING ANY ANSWER IN THIS PART       |
  |                                                                   |
  |  B1 and B2 concern the SITING model. It was built, fitted, and    |
  |  it failed. See Part 0 and Part D.                                |
  |                                                                   |
  |  B3 to B7 concern the CANNIBALISATION study -- the project's      |
  |  SECOND estimand, from the original v3 proposal. It has NEVER     |
  |  BEEN BUILT. No synthetic control has been run, no placebo        |
  |  distribution exists, no decay curve has been estimated, and no   |
  |  spatial weight matrix has been revised.                          |
  |                                                                   |
  |  Answer B3-B7 in the CONDITIONAL, and say so unprompted. "That    |
  |  is the design, and I have not run it" is a complete answer.      |
  |  Claiming a placebo p-value you do not have is the one mistake    |
  |  in this viva you cannot recover from.                            |
  |                                                                   |
  |  The only cannibalisation in the codebase today is a              |
  |  DETERMINISTIC penalty inside the portfolio optimiser: a 20 km    |
  |  radius, a LINEAR taper in distance, and a 0.18 peak loss that    |
  |  SATURATES in neighbour exposure -- the code applies              |
  |  0.18 * (1 - exp(-exposure)), not a straight line.                |
  |  Every one of those is an assumed parameter, not an estimate.     |
  |  It has no standard error and no donor pool.                      |
  +------------------------------------------------------------------+
```

### B0. "What is the method now, then?" ⚠

*The honest answer is that it is open. Say so, and show that "open" means
"narrowed to a shortlist with stated trade-offs", not "undecided".*

> "It is an open decision, and I would rather present it as one than
> pretend it is settled. Three routes are on the table and the research log
> at `docs/METHODS_RESEARCH.md` Section 8 lays out the trade-offs. No winner
> has been declared.
>
> **Route A, moment inequalities.** This is what both Holmes and Houde et al.
> use. You take the facilities the firm actually built, construct
> counterfactual deviations by swapping opening dates between pairs of them,
> and impose that the observed configuration was at least as profitable as
> each deviation. That yields a *set* of parameter values consistent with the
> data rather than a point.
>
> There is a specific reason I am cautious about it here, and it is not
> squeamishness about the machinery. The identifying variation in the swap
> design is opening *dates*. Holmes Section 7 states plainly that store
> locations and opening dates 'are all assumed to be measured without error',
> and Section 8.3 says his procedure yields **inconsistent** estimates of the
> identified set when there is measurement error in the `x` variables. His
> Section 6.1 protection covers error in profits — the left-hand side —
> which is exactly the place my error is *not*. My dates are OSHA inspection
> dates with externally verified lags of 4, 13, 57, 69 and 345 months. The
> method's identifying variation is the one quantity I cannot observe.
>
> That does not kill Route A. It moves the burden: anyone proposing it has
> to argue either that the date error is confined to the outcome, or that a
> guard-band construction buys back enough robustness. Neither argument has
> been made yet, including by me.
>
> **Route B, a closed-form dynamic logit** — Train Section 7.7.3, the
> conditional-choice reframe. It identifies a point rather than a set, it
> runs in anything that fits a nested logit, and it gives interpretable
> coefficients. Its cost is an assumption: that the firm's ex-ante unknowns
> are our unobservables and are iid extreme value. Train's own caveat is
> that 'it is doubtful that the researcher, in reality, observes everything
> that the decision maker knows beforehand'.
>
> **Route C, interval-outcome partial identification** — Molinari Section
> 2.3. Neither of us named this at the outset and on the reading it is the
> closest fit to the data I actually have, because it treats the outcome as
> an interval by construction, which is literally what an 'operating by'
> date is.
>
> What I will not do is pick one in this room to sound decisive. The
> decision is recorded as open in the roadmap along with six others, and it
> is open because the trade-offs are real."

**The trap in this question.** If an examiner says "surely you must have a
preference" — you may have one, but say it as a preference with a reason,
not as a decision. "If I had to choose today I would take Route C, because
it is the only one of the three whose central object is an interval and my
dates are intervals. I have not verified that it scales to a choice problem
this size." That is honest and it is also a stronger answer than a
confident wrong one.

### B1. "How do you know it's causal and not just selection?"

> "We don't, and at present we do not even attempt to. Operators build where
> they judge it viable, so the areas they skipped are not a randomised control.
>
> The design calls for a Heckman two-step on the pilot metro: a selection
> equation predicting whether a facility opened, then the outcome equation
> augmented with the inverse Mills ratio, with corrected *and* naive
> coefficients reported side by side so the size of the correction is
> visible. **That has not been built.** It sits behind a siting model that
> does not work, and correcting the selection in a specification whose unit
> of analysis is wrong would be polishing the wrong object.
>
> The order of operations matters here and I want to be explicit about it.
> Fix the unit first, because a likelihood that assumes independent
> observations (Train Section 3.7.1, p. 61) and is fed 88 echoes of one
> decision is broken before any selection question arises, and no amount of
> selection correction repairs it. Then ask about selection. Doing it the
> other way round produces a corrected estimate of a quantity that was never
> a choice probability. The unit has since been fixed and the successor
> fitted; the selection correction is still not built."

### B2. "Your instrument is weak." ⚠

**Do not defend it as airtight. This is the single most useful defensive move
in the project.**

> "It is contestable, and I'd rather say so — and it is also not yet
> instrumenting anything, so let me separate those. The proposed instrument
> is distance to the nearest commercially zoned centroid. It plausibly drives
> siting, because operators prefer commercial land. But commercial zoning also
> correlates with employment density and traffic, which could drive
> residential demand directly, so the exclusion restriction is not obviously
> satisfied.
>
> The design reports the first-stage F-statistic for relevance, which is
> testable, and for the exclusion restriction, which is not, a sensitivity
> analysis showing how far the corrected coefficients move if the instrument
> has a small direct effect. **Neither has been run.** No first-stage F exists
> in any artefact in this repository, and if I quote you one I am inventing
> it.
>
> If the conclusion survives a plausible violation, that is worth more than
> claiming there isn't one. But I have not yet earned the right to make that
> argument, because the model it would defend is the one that failed."

### B3. "Why synthetic control rather than a simple before-and-after?"

> "Before-and-after attributes to the launch anything else that changed —
> e-commerce grew everywhere over this period. Difference-in-differences fixes
> that but needs a comparison group, and no single untreated ZIP resembles
> Berkeley.
>
> Synthetic control *builds* the comparison as a weighted blend of untreated
> areas chosen to track the treated one before launch. If the blend tracks well
> beforehand, the gap afterwards is the estimate."

### B4. "Pre-treatment fit isn't evidence."

> "Correct, and that is why we don't stop there. With enough donors some blend
> will fit almost any pre-period.
>
> So the design runs placebo inference: pretend each untreated area was
> treated on the same date, run the whole machinery, and collect the effects
> you get when nothing happened. That gives a null distribution built from
> our own data. Then you ask whether the real unit's post-to-pre RMSPE ratio
> is unusual against that distribution. If it ranked first out of forty,
> that would be a rank-based p-value near 0.025.
>
> I want to be clear that the 'first out of forty' is arithmetic about how
> rank-based inference works, not a result I have. **No placebo distribution
> has been computed in this project.** If I had one I would give you the
> actual rank."

### B5. "SUTVA is violated. Doesn't that invalidate everything?"

> "It is violated, plainly. Same-day launches in Berkeley and Emeryville's
> numbers move even though Emeryville was never treated.
>
> Rather than assume a spillover structure, the design measures it —
> estimating the effect in concentric rings using Pollmann's distance-band
> approach — and then uses that measurement to define the weight matrix and
> to decide which donors are contaminated. The violation becomes a parameter
> instead of a threat.
>
> **The decay curve has not been estimated.** Where you see '8 km, fading to
> 20' in our documents, that is the shape we expect and the band structure we
> would fit, not a measurement. The only distance parameter that exists in
> running code is the portfolio optimiser's cannibalisation penalty — 20 km,
> a linear distance taper, 0.18 peak saturating in neighbour exposure —
> and every part of that is an assumption we impose, not
> something we estimated. It has no standard error, and I will not quote one."

### B6. "Why not just use contiguity for W, like everyone else?"

> "Because 'why contiguity?' has no answer, and it is the first thing a spatial
> reviewer asks. Since we've already estimated how far the effect reaches, we
> define neighbours by measured reach. W stops being an assumption and becomes an
> estimate with a standard error."

### B7. "What if revising W doesn't change anything?"

> "Then we report that, and it is still a result. LeSage and Pace argue
> prominently that spatial estimates are less sensitive to W than practitioners
> assume. Our setup is a natural test of that claim, so we pre-register the
> prediction before running it.
>
> If the coefficient moves, we push back on a well-known robustness claim using a
> novel perturbation. If it doesn't, we confirm it under that perturbation and
> report an honest engineering finding: the mutable-W machinery is elegant but
> not decision-relevant. Both are publishable, which is why we wrote the
> prediction down first.
>
> Same caveat as the rest of Part B: **the test has not been run.** The
> prediction is written down, which is the part that had to happen first, and
> the machinery it would perturb belongs to the second estimand, which is
> untouched."

---

## Part C — Data and measurement

### C1. "Your data is two years old."

> "The lag is real, and it is shared with the decision-maker. Operators plan
> siting from the same public census releases; there is no private real-time
> census. Our disadvantage relative to them is order history, not demographics
> — which is precisely why we model the decision rather than demand.
>
> Second, siting has an 18–36 month lead time, so a facility opening in 2025 was
> decided in 2023 on 2021–22 data. Aligning covariate vintage to *decision*
> vintage is correct specification; using today's data to explain a decision
> taken two years ago would give the model information the decision-maker did
> not have.
>
> Third, what moves fast is sourced fast: monthly rents, monthly building
> permits — which are a forward signal, since construction precedes
> population — and ACS one-year estimates for metro context. Slow sources
> give levels, fast sources give rates of change.
>
> What remains: an area that changed sharply in the last eighteen months with no
> permit or rent signal will be misclassified. We flag those as low-confidence
> rather than ranking them silently."

### C2. "You can't observe revenue. So what is the model worth?" ⚠

> "Six of our eight outputs don't need it. Ranking is invariant to a common
> scale factor — if every area's revenue is multiplied by the same unknown,
> the ordering doesn't change. So the ranked list, the bundle choice, the rank
> stability, the break-even thresholds, the timing window and the
> 'would-they-have-built-here-anyway' propensity are all unaffected.
>
> For the two that do need it, we don't invent a margin. We factor it out:
> results are reported as a multiple of margin with the break-even value
> — 41,000 times *m* minus $3.8M, break-even at *m* = $0.93. A reader with a
> view on margin substitutes theirs; a reader without one still gets the
> threshold. That is strictly more informative than a fabricated point estimate.
>
> And we validate the half we *can* observe: metro-level capital against
> disclosed capital expenditure, targeting within 25%. That is the only
> externally falsifiable number in the system, and it can fail."

### C3. "What if your facility dates are wrong?"

> "Worse than wrong — most of them are not opening dates at all, and we say
> so up front. The pilot panel is 43 Amazon delivery stations and the national
> one is 104 rows, of which 100 load; every row is
> dated by the day OSHA opened an inspection case at the address. That proves
> the building was operating by then; it says nothing about when it opened.
> We consume it as an interval, `(panel start, X]`, not as an event time.
>
> We planned to hand-verify a random hundred and publish the error rate. On
> 43 rows that is not a sample, so we did two things instead. First a census:
> every row carries its source, so there is nothing left to sample. Second,
> we measured how loose the bound actually is. Five addresses appear both in
> MWPVL's 2012 network census, which states real opening months, and in the
> OSHA extract. The bound held five times out of five — no inspection
> predates an opening — and the lag was 4, 13, 57, 69 and 345 months. One
> site opened in 1997 and was first inspected in 2026.
>
> That is the honest headline: the bound is *correct* and frequently
> *uninformative*. So the panel supports claims about **which** ZIPs were
> served much better than claims about **when**, and we do not make the
> second kind.
>
> Two consequences we act on. We model at quarterly grain, which is more
> robust to date noise than monthly. And we quote the decision count next to
> every metric, because the raw event count is a lie: the risk set contains
> 812 ZIP-quarter events, but those come from at most 38 usable buildings and
> possibly as few as 28 independent metro-quarter episodes. Both bounds are
> reported and the verdict is taken on the *optimistic* one, so nobody can
> blame the failure on a conservative proxy. 38 usable buildings over 5
> parameters is 7.6 events per parameter against a conventional floor of 10.
>
> The specification this data actually calls for is **interval censoring** —
> the opening happened somewhere in `(panel start, X]`. That is not
> implemented. `docs/STATUS.md` marks it NOT STARTED, and it is the single
> most defensible piece of remaining work in the project."

**If they press: "you keep calling it a bound. How often is it just the
opening date?"** — *volunteer this one; it is the setup for C3a.*

> "Never, as far as I can tell, and that is worse than it sounds. On all 100
> loaded rows of the national panel, `open_year` and `open_quarter` are
> exactly the year and quarter of the earliest OSHA inspection. The field is
> not an opening date that sometimes coincides with the bound. It **is** the
> bound, written into a column called `open_year`. Anything downstream that
> treats that column as an opening date is silently using an upper bound
> instead, and C3a is what that cost me."

### C3a. "Your warehousing covariate may contain its own outcome." ⚠

*This is the question that lands hardest, because the answer is yes, and
because the covariate in question is the only one in the model that does
any work. The examiner does not need to be told the counter-argument first.
Concede in the first sentence.*

> "It may, and I could not currently rule it out. This is the top open
> defect in the project.
>
> The problem is structural: **an Amazon delivery station is itself a
> warehousing establishment.** NAICS 493 is warehousing and storage, and a
> delivery station falls in it. So if I score a ZIP on its warehousing count
> in the same year the facility opened, that count includes the facility. I
> would be predicting the outcome with the outcome, and the model would look
> excellent for the worst possible reason.
>
> I saw that and built a guard. `ingest/cbp_detail.py` scores every facility
> on the latest County Business Patterns vintage **strictly earlier than its
> recorded `open_year`**. Six facilities that opened in 2017 or earlier have
> no clean vintage at all and are dropped rather than scored, which is what
> takes the sample from 100 decisions to 94.
>
> **The guard is correct in design and nominal in practice, and here is
> why.** `open_year` is not an opening date. On all 100 loaded national rows
> it equals the quarter of the earliest OSHA inspection — the 'operating by'
> upper bound, restated. So a building OSHA first inspected in 2022 might
> have opened in 2017, and my 'strictly earlier' 2021 vintage already counts
> it. The lag I am trying to clear is not one year; it is however long the
> building operated before an inspector arrived, and I have measured that on
> the five addresses where an independent opening month exists: 4, 13, 57,
> 69 and 345 months. **Three of those five exceed twelve months.** On the
> only evidence I have, the guard is defeated more often than it holds. Its
> true margin is zero or negative.
>
> **What that does to the result.** It does not explain the headline away,
> because the headline is a null result: the fitted model only matches the
> raw covariate either way. But it means the one thing that *does* predict well
> may be predicting well partly because it contains the answer. Until the
> lag is measured against real opening dates rather than against bounds, I
> cannot separate 'Amazon builds where warehouses are' from 'Amazon's
> warehouse is in the warehouse count'.
>
> **What would settle it.** A genuine lower bound on opening dates — county
> building permits, or industrial REIT property schedules, both of which are
> public and neither of which I have worked through. With a real opening
> date the vintage lag becomes real and the covariate is either clean or
> measurably dirty. Without one, the guard is a comment."

**If they press: "didn't you already learn this lesson once?"**

> "Yes, and that is the uncomfortable part. The project's first estimand was
> a constructed order-volume target built from income and retail density,
> predicted using income and retail density — the answer made from the same
> ingredients as the question. I caught that, changed to an observable
> estimand, and wrote it up as a lesson learned. This is the same disease in
> a subtler form, and it took a third pass to notice. It is also the third
> place in this project where the unit or the timing of a variable turned out
> to be something other than what its column name said."

### C3b. "You spent four evenings labelling data you already had." ⚠

> "Four evenings, 362 sites, and 80% of them were already classified in a
> file I wrote myself. It is a self-inflicted wound and the cause is a bug
> in my own code.
>
> ```
>   sites hand-labelled across 6 batches              362
>   delivery stations among them                      135
>   genuinely NEW to the delivered frames              13
>   worklist rows already in NATIONAL_CLASSIFIED.csv  289   (80%)
> ```
>
> `scripts/make_unlabelled_batches.py` selected the OSHA rows my name-based
> regex could not classify, and never checked them against
> `NATIONAL_CLASSIFIED.csv` — which is the file the national facility frame
> was built from. So the worklist was called 'unlabelled' and was mostly
> labelled. The failure is comparing against the wrong reference, and I then
> made the *same* error a second time in the same programme: I predicted
> batch 6 would yield zero new sites by checking it against
> `NATIONAL_CLASSIFIED.csv` alone, when the delivered frames are a smaller
> and different set. It yielded three.
>
> **The recoverable half, and I want to put it second rather than first.**
> The 122 rows that were neither new nor unclassifiable are independent
> confirmations of classifications the pipeline had already made — each from
> a different public source, each with a quote and a URL. That is a
> validation set for the name-based classifier in `ingest/osha.py`. It is the
> kind of evidence reviewers ask for and projects rarely hold, and I now have
> one. It was produced by accident. The bug is still in the script, so a
> seventh batch generated today would repeat it."

**If they press: "so was the whole exercise worthless?"**

> "No, but it cost about seven times what it should have. Thirteen new
> delivery stations for 362 labels is a yield of under 4%, when a correctly
> generated worklist would have been most of the way to 100%. The right
> summary is that the programme delivered two things — 13 new facilities and
> an unplanned validation set — at roughly seven times the necessary cost,
> because of a three-line check that was not there."

### C3c. "Your satellite method failed." ⚠

> "It did, and the way it failed is more interesting than the fact that it
> did, so let me give you both.
>
> **Why it should have worked.** Every date I have is an upper bound. If I
> could get a *lower* bound, the pair is an interval, and an interval is
> something the statistics can actually use — it would unblock interval
> censoring, the timing factor of the decomposition, and the vintage lag in
> C3a all at once. When a delivery station is built, bare ground becomes a
> large bright roof and a car park. Sentinel-2 photographs every point on
> Earth every five days, free, back to 2015. Run a changepoint detector on
> the reflectance series and you get the month the ground changed.
>
> **What happened.**
>
> ```
>   sites attempted                     107
>   sites that returned an estimate     107    (100%)
>   median cloud-free scenes            106
>
>   validation on the 83 with a known opening year
>     within 1 year                      41%
>     error standard deviation          3.42 years
>
>   the logical test, on all 107
>     dated AFTER the day an inspector
>       found the building operating     39 of 107  (36%)
>     median lateness of those 39         33 months
> ```
>
> **The logical test is the one that kills it.** An estimate that dates
> construction after the building was observed operating is not imprecise,
> it is impossible, and 36% of them are. The validation figure alone — 41%
> within a year — I might have argued was usable for coarse work. The
> impossibility rate is not arguable.
>
> **And there is no filter that rescues it.** The method emits a confidence
> score, so the obvious move is to keep the high-confidence estimates. It
> does not discriminate: 35% are impossible at confidence above 2 against
> 30% at confidence 1 to 2. Filtering changes nothing. That means the 68
> estimates that happen to pass the logical test are not a trustworthy
> subset — they are the ones that landed on the right side of a test a third
> of their siblings fail — and I do not present them as dates anywhere.
>
> **The diagnosis is localised, which is why I would try again.** The
> imagery is fine; a median of 106 cloud-free scenes per site is plenty. It
> is the changepoint detector picking the wrong break — most likely a
> seasonal or resurfacing transition rather than construction. So the route
> is unsuccessful rather than closed, and I would attack the detector rather
> than the data source."

**If they press: "why report it at all, if it produced nothing?"**

> "Because it is the sixth date-collection method I have tried and the fifth
> that failed, and the catalogue of failures is the most transferable thing
> in this project. Somebody trying to build a facility panel from public data
> now knows that the operator's hiring site, Google review dating, LLM web
> search without page access, a free industry census, SEC filings and
> Sentinel-2 changepoint dating all do not work, and *why* each one does not.
> That is four days somebody else does not have to spend. Also, an
> unreported failed method is an invitation to the question 'did you try
> satellite imagery?', to which 'yes, and here is the impossibility rate' is
> a much better answer than 'no'."

### C4. "Aren't ZIP codes the wrong unit?"

> "They're the unit of the decision — service is switched on per ZIP —
> so they are the right unit to model. But they are postal constructs, not
> statistical ones, and they change between vintages, so the modifiable areal
> unit problem is live.
>
> We pin the 2020 vintage, enforce the ZCTA count as a data contract so vintage
> mixing fails the build rather than silently corrupting a time series, and
> re-run the conclusions at H3 hexagonal grain. If the top-100 list survives a
> completely different spatial partition, the result isn't an artefact of the
> boundaries."

### C5. "Everything is a proxy. Why should I believe any of it?"

> "Precedent is the weak answer — GDP proxies activity, housing starts proxy
> sentiment. The strong answer is the external check. We aggregate our
> ZIP-level capital estimates to metro level and compare against disclosed
> capital expenditure, targeting within 25%. That check can fail, which is what
> makes it a check.
>
> And the sensitivity analysis tells us which proxies matter. If the ranking is
> insensitive to the retail-density proxy, its imperfection is irrelevant to the
> decision."

---

## Part D — Evaluation

### D1. "What's your accuracy?" ⚠

*Answer with the measured numbers, in this order, without being coaxed.*

> "Poor, and I can give you it exactly. Here is the held-out test split,
> model against a null that predicts the same constant for every ZIP in
> every quarter."

```
                                   model      null      verdict
  ------------------------------------------------------------------
  AUC (ranking)                    0.6894    0.5000    model better
  Brier (accuracy)                 0.01952   0.01961   +0.5% skill
  ECE  (calibration)               0.00863   0.00005   NULL ~170x better
  ------------------------------------------------------------------
  Brier skill, temporal hold-out            -0.02091   NULL better
  Brier skill, geographic hold-out          -0.06184   NULL better
  ------------------------------------------------------------------
  covariates distinguishable from zero       1 of 3    households only
  events per parameter                       7.6       floor is 10
```

> "The ranking ability is real but small. The calibration is the damning
> line: a constant predictor is almost perfectly calibrated, trivially,
> because it never sticks its neck out, and my model is about 170 times
> worse than that. So the probabilities must not be quoted to anyone.
>
> On the two hold-outs the skill goes negative, which means the constant
> would have served you better. I will flag one caveat in my own favour and
> one against. In my favour: the geographic hold-out is Phoenix and Boise,
> which hold two dated stations between them, so it is a smoke test for
> gross failure rather than a test of transfer. Against: the temporal
> hold-out is the one I would most like to lean on and it is also the one
> most contaminated by the date problem, because my dates are 'operating by'
> upper bounds and any result that depends on *when* an event happened
> inherits that.
>
> For the unobservable outcome — dollar NPV — I make no accuracy claim,
> because there is no public ground truth. I report conformal intervals with
> empirically verified coverage instead, and the coverage is a weaker result
> than it sounds — see D6."

**Those are the retired model's numbers. The model that replaced it has a
different scoreboard and it is also negative.** Have both ready; an examiner
who has read the artefacts will ask for the second.

```
  held out, 38 decisions       top-1    top-5    top-10    Brier
  ------------------------------------------------------------------
  the fitted choice model       7/38    16/38     19/38    0.008724
  warehousing count alone       8/38    16/38     20/38    0.008951
  households alone              1/38     5/38     10/38    0.009271
  uniform within the metro      1/38     3/38      7/38    0.009316

  McFadden rho-squared, in sample on the 56 training decisions   0.1969
  free parameters                                                3
  of which at the boundary at zero                               2
  95% sandwich interval on the one interior parameter
    (null is 1.0, not 0 -- households is the numeraire)  [0.734, 2.835]
    p against the ratio being 1                                  0.287
    bootstrap over metros, the conservative one          [0.702, 10.013]
  so: not distinguishable from one more household
```

> "There is no AUC for the choice model and quoting one would be a category
> error — it ranks alternatives inside a choice set rather than classifying
> rows. The metric is top-k plus the raw Brier pair. And the row to read is
> the second: a raw covariate with nothing fitted matches it. Sec. 0.3 is the
> long answer."

**And there are now two more scoreboards, both negative. Added 2026-09-15.**
*An examiner who has read `outputs/metrics/` will have seen these. Offer them
rather than waiting.*

```
  THE HAZARD MODEL, REVIVED    outputs/metrics/hazard_revival.json
  ------------------------------------------------------------------
                          retired pilot     expanded + real dates
  events (ZCTA-quarters)          812               5,441
  independent episodes             28                 436
  events per parameter            5.6  (FAILED)     87.2  (cleared)
  AUC                          0.6894              0.6832
  ECE vs the constant null    170x worse       8.7x worse
  calibration wins vs the constant       0 of 17 comparisons
  ZCTAs one opening switches on   median 58      median 39
  the independence violation      violated        STILL violated

  THE METRO-LEVEL ENTRY MODEL   outputs/metrics/metro_entry.json
  pre-registered in docs/PREREG_METRO_MODEL.md, md5 946f7ef7...
  ------------------------------------------------------------------
  criterion clause 1  AUC > households baseline        0 of 7 years
  criterion clause 2  ECE <= constant null             3 of 7 years
  pooled AUC, 6,545 held-out rows, 306 events
      model 0.7323   households 0.8949   facilities-already-open 0.7325
  metro-clustered bootstrap, 2,000 draws, 935 clusters
      model minus households  -0.1628  [-0.2011, -0.1313]
  50 paired re-splits           mean -0.175, losing 50 of 50
  verdict                                                     H0
```

> "Three readings from those two blocks that I would give unprompted.
>
> **The hazard revival is a stronger negative than the retirement was.** The
> obvious objection to retiring a model on 39 events was 'you never gave it
> enough data, or real dates'. Both have now been given. The AUC went *down*
> and the calibration lost 17 of 17. What did not change is the reason: one
> siting decision still enters the likelihood as a median of 39 independent
> observations, and there is no radius at which one opening is one
> observation — I swept 8.3 to 45 miles and the per-opening count never falls
> below 14.
>
> **The metro model is indistinguishable from a column of integers.** Pooled,
> the two-covariate fitted logistic scores AUC 0.7323 and the zero-parameter
> count of facilities already present scores 0.7325, on 6,545 identical rows.
> Top-50 totals are 129 against 127. A model fitted seven times reproduced a
> count.
>
> **And there is a Simpson's paradox in my own headline that I will point at
> before you do.** The pooled 0.7323 is *higher than the model's AUC in every
> single size tier* — 0.4125, 0.5666, 0.6961. Size predicts the outcome and
> size defines the strata, so pooling rewards a ranking the model did not
> have to earn. Quoted alone, 0.73 would read as a working model. In the only
> tier with enough events to measure, it is 0.70 against a baseline's 0.80."

**What we pre-registered, and what we got.** Say this unprompted; it is
better volunteered than extracted.

```
   RETIRED HAZARD MODEL
   pre-registered        measured        verdict
   -----------------------------------------------------------------
   AUC  >= 0.80          0.6894          MISSED, badly
   ECE  <  0.05          0.00863         "passed" -- and meaningless,
                                         because the null scores 0.00005
   precision@100 >= 0.60 not computed    the artefact reports AUC, Brier,
                                         ECE, a 10-bin calibration table
                                         and conformal coverage. No
                                         precision@k. Do not quote one.

   FITTED CHOICE MODEL -- six criteria, two not met
   pre-registered                        verdict
   -----------------------------------------------------------------
   choice set demonstrated, not          MET
     asserted
   attraction variables extensive        MET, all four
   raw Brier pair + calibration as       MET
     the headline, never a skill score
   a benchmark, reported even if it      MET, AND IT DREW LEVEL.  Corrected
     wins                                2026-09-15: this row used to say
                                         the registered gradient-boosted
                                         ranker "was never built".  It WAS
                                         built (2026-09-13,
                                         gbm_benchmark.json) and it is
                                         reported.  Over 50 re-splits it
                                         beats the model by 1.7 of 38 and
                                         LOSES on Brier; on the 485-decision
                                         panel its edge is 0.5198 vs 0.5196,
                                         i.e. gone.  A raw count also
                                         matched the model
   standard errors on DECISIONS,         MET, LATE.  Both landed
     sandwich AND bootstrap                2026-09-14.  Sandwich is
                                           undefined at the two boundary
                                           parameters and is correctly
                                           refused there
   intervals reported, no bare point     MET, AND THEY COVER THE NULL.
     estimate                              Sandwich [0.734, 2.835] against
                                           a null of 1.0, p = 0.287, with
                                           both bootstraps and the BCa
                                           agreeing.  Exactly the outcome
                                           pre-registered in ADR-0004
```

```
   THE METRO-LEVEL ENTRY MODEL -- the only FULL pre-registration
   docs/PREREG_METRO_MODEL.md, written 2026-09-15 BEFORE any fit
   pre-registered                        verdict
   -----------------------------------------------------------------
   universe = all 935 CBSAs, not the     HONOURED.  Restricting to the
     195 with a known opening              195 would have been selection
                                           on the outcome (prereg 8.2)
   AUC > households baseline in a        FAILED, 0 of 7
     majority of held-out years
   ECE <= the constant null in a         FAILED, 3 of 7
     majority of held-out years
   strict vintage gate, drops counted    HONOURED, AND IT COST THE TEST.
                                           8 of 12 covariates dropped on
                                           vintage, 2 more on coverage.
                                           The verdict arm has TWO
   report with and without 2020-21       DONE.  0 of 5 and 1 of 5
                                           without them -- slightly worse
   raw Brier and top-k against a         DONE.  No skill score is quoted
     uniform null, never a skill score
   stratify by metro size                DONE, AND IT MATTERED.  Pooled
                                           AUC 0.7323 exceeds the model's
                                           AUC in all three tiers
   both outcomes' language written       HONOURED.  The finding is the
     in advance                            prereg's own H0 paragraph
   -----------------------------------------------------------------
   VERDICT                               H0
```

The ECE row in the hazard block is the interesting one and worth saying out
loud: **a threshold can be passed by a model that is useless.** 0.00863
clears a 0.05 bar comfortably and is still 170 times worse than doing
nothing. A pre-registered threshold is only as good as the baseline you
register alongside it, and registering the baseline is the thing we got
right — which is exactly why the metro prereg registered three baselines and
named the second as the one that counts.

### D2. "Why did you drop MAPE?"

> "Two independent reasons. It divides by the actual value, and it's undefined
> wherever that's zero — and our whole premise is that many areas are
> structural zeros. Hyndman and Koehler is the standard reference.
>
> Separately, it would have been computed against a target we constructed from
> its own predictors, which would have made a *good* score evidence of a bug."

### D3. "Explain that circularity problem." ⚠ *your best answer*

> "Our first instinct was to predict order volume per ZIP. Nobody outside the
> company can observe that, so we would have had to invent it — splitting
> total orders across ZIPs by income and retail density. Then we'd fit a model
> using income and retail density to predict it.
>
> The answer is made from the same ingredients as the question. It's like
> defining a talent score as 0.6 times height plus 0.4 times shoe size, then
> building a model that predicts talent score from height and shoe size. It
> scores 97% and has learned nothing.
>
> The dangerous part is that the better it looked, the more completely it proved
> the bug. We caught it, changed the estimand to something observable, and that
> turned a meaningless fit statistic into a forecast we can actually score."

**And then it came back, which is the part you must add rather than stopping
on the victory.** *If you tell this story as a clean save, the examiner has
only to open `cbp_detail.py` to make you look as though you were hiding the
sequel. Volunteer it.*

> "That version I caught early. A second version of the same disease got much
> further, and it is in the model I ship. The covariate that carries the whole
> result is the count of warehousing establishments in a ZIP — and an Amazon
> delivery station **is** a warehousing establishment. A contemporaneous count
> would contain its own outcome. I built the obvious guard: score every
> facility on the latest Census vintage strictly earlier than its opening
> year. But the field I called `open_year` is not an opening year. On all 100
> loaded rows it is the quarter of the earliest OSHA inspection — an upper
> bound. So the guard lags off a bound rather than off an opening, and its
> margin is zero rather than a year. Sec. C3a is the full version.
>
> The lesson I would actually draw is not 'watch out for circularity'. It is
> that in both cases the problem was a **column whose name did not describe
> its contents**, and a check that looked correct because it was written
> against the name."

### D4. "AUC 0.6894 — is that good?"

> "No. It is better than a coin flip and that is all it is.
>
> The scale first, so the number means something. 0.5 is a coin flip. Our
> measurement is 0.6894. Above about 0.95 I would suspect leakage — a
> variable that secretly encodes the outcome — so the ceiling on an honest
> public-data model is well under 1.0, and I pre-registered 0.80 as an
> achievable target for that reason. I missed it."

```
   0.50  coin flip                        <- the null model
   0.69  measured                         <- us
   0.80  pre-registered target            <- missed
   0.95  suspect leakage above here
```

> **Added 2026-09-15 — the 0.6894 has now been re-measured twice and it is
> not a small-sample number.** On the expanded panel with real MWPVL opening
> dates, 5,441 events instead of 812, the comparable arm scores **0.6832**
> (`outputs/metrics/hazard_revival.json`). Across all seven arms and three
> hold-outs the range is 0.4527 to 0.7515 with a median of 0.6459; the 0.4527
> is an out-of-time score, worse than a coin flip at the task the model
> exists to do. And at the completely different grain of the metro-level
> entry model, pooled AUC is **0.7323** against a households baseline's
> **0.8949** (`outputs/metrics/metro_entry.json`).
>
> So the useful sentence is no longer "0.69 on a small sample". It is
> **"between 0.64 and 0.73 across three models, two grains, two dating
> regimes and a 6.7x increase in events — and in every case a
> zero-parameter public column does at least as well"**. The number is
> stable, and its stability is the finding.

*If they offer you "your metro model scores 0.73, that is better" — do not
take it.* The households baseline on the same rows scores 0.8949, the
zero-parameter facility count scores 0.7325, and the 0.7323 is higher than
the model's AUC in every individual size tier. A pooled AUC on strata of
very different event rates is not a performance number; it is a statement
about the strata. Sec. D1 has the table.

> "The second thing to say is that AUC is the *flattering* metric here, which
> is why I do not lead with it. AUC only asks whether the ordering is right.
> It is invariant to any monotone squashing of the probabilities, so a model
> can rank tolerably and still emit numbers you must not use. That is exactly
> our case: AUC 0.69, and calibration error 170 times the null's. If I quoted
> you the AUC and stopped, I would be quoting the one metric that hides the
> failure.
>
> And the discipline held: the validation set was never used for retraining,
> which is why the miss is a miss rather than a number I tuned my way to."

*The follow-up to expect here is "so you changed the metric after it failed" —
that is **D5**, and the answer concedes the sequencing before defending the
choice. Do not pre-empt it; but do not be caught by it either.*

### D5. "You changed your metric after it failed. Moving the goalposts?" ⚠

*Asked in full: "You changed your headline metric after your model failed.
Isn't that moving the goalposts?" Concede the sequence in the first sentence.
Everything after that is about whether the destination was right, and it is —
on grounds published in 2007. Do not argue that AUC was unfair to us. It was
not; it was the flattering metric.*

> "Partly, yes, and I will give you the part that lands before I defend the
> rest.
>
> The sequence was: I pre-registered AUC ≥ 0.80, I fitted the model, I measured
> 0.6894, and *then* I read the scoring-rules literature and changed the
> headline. That is the wrong order. If I had read Gneiting and Raftery at
> design time I would have registered a proper score, and I did not. That is a
> planning failure and I am not going to dress it up.
>
> What I will defend is the destination. The rule I moved to was published in
> JASA in 2007, nineteen years before my result existed."

**Then the three grounds, in this order.**

> "First — and this is the point — AUC is not a scoring rule. Gneiting and
> Raftery define a scoring rule as a function of one forecast and one
> observation, `S(P, x)`, averaged over cases. Propriety means: your expected
> score is maximised, uniquely, by quoting what you actually believe. AUC is a
> rank statistic over *pairs* of cases, so it cannot be written in that form at
> all. Propriety isn't violated for AUC; it's undefined. I want the guarantee
> in their equation (1), and AUC is not the kind of object that can carry it.
>
> I want to be careful here, because it would be convenient for me to say the
> paper attacks AUC. It does not. The words AUC and ROC appear zero times in
> those twenty pages. The argument is mine; the framework is theirs.
>
> Second, that paper contains a worked demonstration that this exact mistake
> changes your conclusion — and it is about the weather, not about me. Section
> 8: sixteen thousand sea-level-pressure forecasts, an ensemble known to be
> under-dispersed by a factor of about 1.55. Four proper scores put the optimum
> between 1.62 and 2.41. Two improper ones — including a probability score that
> was in published operational use — put it at 0.05 and 0.02, concluding the
> forecast was essentially certain. Their sentence is 'their use may result in
> misguided scientific inferences, as in this experiment.'
>
> Third, my own numbers are simply the same demonstration again. AUC 0.6894
> reads as a result. The calibration error is a hundred and seventy times the
> null's. AUC is invariant to any monotone squashing of the probabilities, so
> it cannot tell my model from one whose numbers are all ten times too big. The
> metric I dropped was the *flattering* one. I did not swap to a metric that
> made me look better — I swapped to one that made the failure visible, and
> then I reported the failure."

**If they press on the skill score specifically.** *This is the concession that
buys the rest. Volunteer it if the questioner knows the literature.*

> "There is a second thing wrong and you may as well have it from me. The same
> paper, page 362, says skill scores of that form are *generally improper*,
> even when the underlying score is proper — Murphy showed only asymptotic
> propriety, and it names and rejects a 2004 paper claiming otherwise.
>
> So the strictly proper object is the Brier score, not the Brier *skill*
> score. What I report is the raw pair — 0.019522 for the model against
> 0.019614 for the null, on the identical 8,044 rows, which is the comparison
> the paper licenses — and the skill number is how I display that pair, because
> a Brier of 0.0195 at a 2% base rate is unreadable. It is a normalisation, not
> a scoring rule. The impropriety is a hedging effect that vanishes as *n*
> grows and my *n* is eight thousand, so it doesn't bite here — but I'm not
> going to claim Brier skill is proper, because it isn't."

**If they say "your null is better calibrated, so your new metric also says you
failed".** *Agree, and make the failure bigger. This is the strongest move in
the answer.*

> "It does, and more cleanly than AUC did. But let me correct the framing,
> because the null's calibration isn't the surprise people take it for.
>
> My null predicts the base rate everywhere. Gneiting and Raftery call that a
> climatological forecast and say of it, in section 2.3: *calibrated by
> construction, but often lack sharpness.* Of course it scores 0.00005. It
> never sticks its neck out. That is what climatological references are for.
>
> The real indictment is the one their framework gives. The goal of
> probabilistic forecasting, in their words, is to maximise sharpness *subject
> to* calibration. Calibration is a constraint, not a trade. My model's whole
> job was to buy sharpness while holding the constraint. It bought half a
> percent of Brier skill and it *broke* the constraint. It failed the
> constraint and barely moved the objective. That is worse than what AUC would
> have let me say, and it is why I changed the metric."

**Hard boundary — do not say any of these.**

```
  X  "AUC was unfair to my model."          It was generous. Say so.
  X  "Gneiting and Raftery show AUC is
      improper."                            They never mention AUC. This is
                                            a fabricated citation and it is
                                            checkable in thirty seconds.
  X  "Brier skill is the proper scoring
      rule."                                The BRIER SCORE is. The skill
                                            score is generally improper --
                                            same paper, page 362.
  X  "The new metric is the standard one
      in this field."                       Not claimed by anything we read.
                                            Say "it is the one with the
                                            guarantee I need" instead.
```

*Source for every claim above:* Gneiting & Raftery (2007), *JASA* 102(477)
359-378 — propriety at Sec. 2.1 p.360 eq. (1); Brier strictly proper at Sec.
3.1 Example 1 p.363; sharpness-subject-to-calibration at Sec. 1 p.359;
climatological reference at Sec. 2.3 p.362; skill scores improper at Sec. 2.3
p.362; the weather case study at Sec. 8.2 p.374 and Table 3 p.373. Full reading
in [`../research/NOTES_gneiting_raftery_2007.md`](../research/NOTES_gneiting_raftery_2007.md);
the argument, with what it concedes, in
[`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) Sec. 12.

### D6. "What is conformal prediction and why bother?"

> "Most models give you an interval derived from their own assumptions —
> Gaussian errors, correct specification. If those are wrong, the interval is
> wrong and you can't tell.
>
> Split conformal is nearly assumption-free: hold out a calibration set, record
> the errors, take the 90th percentile, and use that as the interval width. Then
> we *check* it on held-out data and report the measured coverage.
>
> Ours: **88.19% empirical against 90% nominal**, which is inside a two-sigma
> tolerance of 0.032 computed on 351 *effective* units rather than on 8,044
> rows. That distinction is the whole point — the rows are not independent,
> because a delivery station flips a whole catchment at once, so a tolerance
> computed on the row count would be far too tight and would have declared a
> miss. It converts an assumed guarantee into a measured one, and it's about
> thirty lines of code.
>
> Note what conformal does *not* rescue. It gives honest coverage for a model
> whose point predictions are badly calibrated; a wide-enough interval covers
> the truth whatever the centre is doing. Valid coverage is not evidence that
> the siting model works."

**Volunteer this before they find it.** The same artefact records
`share_empty: 0.1009` — about **10% of the prediction sets are empty**, and
the mean set size is 0.8991. An empty conformal set is the procedure saying
"at this confidence level I decline to name an outcome." So the honest
reading of our 88.19% is not "we nearly hit 90%"; it is closer to "the
procedure names an outcome 90% of the time and is essentially always right
when it does, and abstains the rest of the time." That is a defensible thing
for a conformal procedure to do on a weak model — abstention is the correct
response to insufficient signal — but it is not a sign of a good underlying
model, and an examiner who opens `hazard_report.json` will see the number.
Say it first.

**The choice model also has conformal sets, and they are a worse story than
the hazard model's. Do not reach for them as a substitute for the standard
errors you do not have.**

```
  alpha   nominal   empirical   median set   median share of the
                    coverage    size         choice set
  -------------------------------------------------------------------
  0.10     0.90       1.000        38.5            71.4%
  0.20     0.80       0.958        34.0            61.7%
  0.30     0.70       0.833        18.5            34.0%

  24 test decisions; median choice set 59.5 alternatives
```

> "At the 90% level the coverage is perfect, and that is the problem rather
> than the achievement. It covers because the set names 38 of a median 59.5
> alternatives — 71% of the metro. A procedure that answers 'it is one of
> these 38 ZIPs, out of 60' has told you almost nothing, and it did not have
> to be right about anything to achieve that. The alpha 0.30 row is the only
> one I would call informative, at a median of 18 alternatives, and its
> coverage is 0.833 against a nominal 0.70, so it is still conservative.
>
> These are also **not** intervals on the coefficients, which is the thing I
> am actually missing. Conformal gives me a set of plausible ZIPs. It says
> nothing about whether the warehousing coefficient is distinguishable from
> anything. Offering it as though it did would be answering a different
> question than the one asked."

### D7. "Your agent benchmark is 100 questions you wrote yourself."

> "Yes, and that's why we don't claim a headline number without context. On the
> BIRD benchmark the best public systems reach about 80% execution accuracy
> against roughly 93% for humans. Claiming 85% on a self-authored set would be
> claiming above state of the art on an unfalsifiable test.
>
> So: n of at least 100, execution accuracy as the primary metric — does the
> generated SQL return the same rows as a gold query, which is objective —
> Wilson intervals reported, results stratified into four difficulty tiers
> because spatial joins are where these systems break, and an audit of our own
> gold queries."

---

## Part E — Scope, feasibility, engineering

### E1. "Isn't a fourteen-megabyte panel too small to be interesting?"

> "File size is the only axis where this is small, and it's small on purpose.
> The panel is 1,081,312 rows over 44 columns — it is fourteen megabytes
> because columnar compression over slowly-moving quarterly demographics is
> very efficient, not because there is little in it.
>
> What it ranks is $7.2–12.1 billion of capital allocation across the 2,413
> ZCTAs in the ten pilot metros. The uncertainty layer was specified at 24
> billion draws and what actually ran is 500 -- I will quote the 500, because
> the 24 billion is a compute estimate in `scope.json` that was never
> executed. The portfolio search space is 2 to the 2,413. We
> integrate fourteen registered sources, thirteen of them analytical, at eight
> different grains across eight years.
>
> I'd rather spend the compute on uncertainty than on scanning rows I don't
> need -- and the 500 draws I did spend it on are what told me the headline's
> earlier 330-activation answer sat at the 97th percentile of its own
> parameter distribution while the current 282 sits at the 67th. The hard
> problem here is identification, not throughput."

**If they press on the capital figure:** say plainly that an earlier draft
claimed $15.6–26B across 5,200 ZCTAs, that the ZCTA count had been estimated
rather than measured, and that counting it under the OMB 2023 delineation gave
2,413. `report/scope.py` now derives every headline figure from the artefacts
so the mistake cannot recur. Seven billion dollars is still seven billion
dollars, and "we found our own number was wrong and wired the fix into the
build" is a better answer than the bigger number ever was.

### E2. "Could you handle data 100 times bigger?"

> "The architecture is scale-agnostic below the feature layer — columnar
> parquet, DuckDB, source-agnostic ELT with contracts in CI. The panel already
> runs nationally: all 33,791 ZCTAs, 1,081,312 rows, 14 MB. Restricting the
> modelling to ten metros is an identification decision, not a capacity one.
> At 100× the same pipeline moves to object storage and a distributed engine
> without touching the model layer.
>
> The part worth discussing is what actually broke at *this* scale: the
> portfolio objective was recomputing all 2,333 priced ZCTAs for every
> candidate when only the selected rows and the candidate matter — 653 seconds
> down to 30 — and road-network preprocessing needs a redesign to fit at all."

### E3. "Can three people build this in nine weeks?"

> "We sized it before committing. The analytical panel fits in memory, compute
> cost is zero, and no GPU is needed. The one component that would have broken
> it was road-network preprocessing — ten cities at once needs about 30 GB of
> working files and more RAM than a student laptop has.
>
> We removed it from the critical path: process one city, extract the drive-time
> table, delete everything, move on. Peak disk drops from 60 GB to 8, and the
> deployed app carries a 10 MB lookup instead of a routing engine."

### E4. "What have you cut, and why?"

> "A fine-tuned narration model and a three-way language-model comparison. About
> eleven days and ninety dollars between them, and neither contributes to
> novelty, model confidence or the use case. The comparison is also underpowered
> at the sample size we could afford — differences under about eight
> percentage points wouldn't be distinguishable.
>
> Both are recorded in the roadmap with reasons, so the cut is a decision rather
> than a gap."

### E5. "What would you do differently?"

*Never answer "nothing."*

> "Two things. Assign pipeline stages, not just modules — we initially
> assigned who owns the model and who owns the app, but not who owns the
> ingest-to-warehouse path, which is how a shared pipeline becomes nobody's job.
>
> And decide the routing strategy in week zero. We nearly put a 30 GB dependency
> on the critical path before realising we only ever needed a lookup table."

### E6. "You found bugs in your own estimator. What were they and how do I know there are no others?" ⚠

*Added 2026-09-15. Two real bugs were found in `src/siting_atlas/models/
choice.py` and guarded; a third instability was found in the GBM benchmark
and deliberately NOT patched. Volunteer all three. The interesting thing
about the first two is that both were silent, and one of them flattered the
fit — which is the dangerous kind.*

> "Two in the estimator, and a third thing that is an instability rather than
> a bug. All three were found by experiments that were not looking for them,
> which is the only honest thing I can say about how they were found.
>
> **One: a NaN that could never be displaced.** `choice.fit` does a
> five-start multi-start and keeps the best by `r.fun < best.fun`. Every
> comparison against NaN is False, so a NaN from the *first* start is never
> displaced by any later start, however good. The function returned a NaN
> model with no error, no warning, and an all-NaN `beta` that propagated into
> every downstream metric. Its only symptom was a `nan` in a printed mean.
> The guard is two lines — skip a non-finite start — plus a `RuntimeError` if
> every start fails, because a caller that gets an exception stops and a
> caller that gets NaN carries it into a published number.
>
> **Two: an infeasible optimum, and this one flattered the fit.** The choice
> probability `P = beta'a / sum(beta'a)` is only a probability while
> `beta'a > 0` for **every** alternative, chosen or not. The exp
> parameterisation enforces that only while every attraction column is
> non-negative — which stops being true the moment you add a centred or
> log-relative column, because a positive coefficient on a negative column
> *subtracts* attraction. Measured on the log-relative arms, the optimiser
> drove coefficients **20x to 77x past the feasibility ceiling**, pushing
> **765 to 4,816 non-chosen alternatives below zero**. That shrinks the
> denominator, inflates P(chosen) from 0.078685 to 0.079346, and raises the
> log-likelihood by up to 1.20 — while nothing ever becomes undefined, so
> nothing complains.
>
> The tell is the part I would want you to notice: **in all five columns, the
> direction with the *lower* feasibility ceiling was the one that 'found' a
> coefficient.** Success was predicted by how cheap it was to violate
> positivity. The guard now checks `beta'a > 0` at the optimum and raises
> with the fix in the message — enter such a covariate through a separate
> unconstrained linear index, not inside the attraction sum.
>
> Note that the first guard does **not** catch the second. An infeasible
> optimum has a perfectly finite log-likelihood; that is the whole problem.
>
> **Three: the GBM's single-split numbers are not a measurement**, and that
> one I disclosed rather than patched — the reasoning is under Sec. 0.3."

**If they press: "how do I know there are no others?"** *Do not say
"extensive testing". Give the exposure.*

> "You do not, and neither do I. Here is the honest coverage picture rather
> than a reassurance. The suite passes — 796 tests, 2 xfailed on the last run
> that reported it — but the project's own audit found **39 of 133 source
> modules are never imported by any test, and 20 of those are the two-day
> sprint**. `models/choice_runner.py`, the module that writes the headline
> `choice_report.json`, is among the untested ones. That is in
> `docs/AUDIT_2026_09_14.md` §2.2, which I commissioned and which I did not
> write afterwards.
>
> What I would offer instead of a guarantee is the pattern. Both bugs were
> found the same way — by a result that was *slightly too good* and did not
> have an explanation. The infeasible optimum was caught because the
> coefficients that 'worked' correlated with which direction was cheapest to
> break. That is a habit rather than a test suite, and it is the thing I
> would actually claim: the project has a habit of chasing results it cannot
> explain, and both of these were caught by it."

---

## Part F — Use, ethics, and the awkward ones

### F1. "Who actually uses this?"

> "Air-quality districts operating warehouse indirect-source rules — South
> Coast's Rule 2305 is EPA-approved and others are considering equivalents
> — need to forecast where warehouses appear to plan mitigation capacity.
>
> City councils facing tax-abatement requests need to know whether the operator
> would have built there anyway. Our selection propensity *is* that
> counterfactual, and it's public money on the other side of it.
>
> Community and environmental-justice organisations need to know where burden
> lands before the permit is filed, which is why we overlay predicted expansion
> on EPA EJScreen by demographic stratum — a map that doesn't currently exist
> publicly.
>
> And researchers get an open panel and harness to test better methods against."

### F2. "Isn't this just helping Amazon's competitors?"

> "That framing was in an earlier draft and we moved away from it, because it's
> both weak and slightly distasteful. Competitive use is legitimate —
> market-structure transparency — but it's the least interesting user. The
> ones who cannot buy an alternative are councils, air districts and community
> groups."

### F3. "Could this be used to help site warehouses in vulnerable communities?"

*A serious question. Answer it seriously.*

> "Yes, in principle — any siting forecast can be read in either direction.
> Three things reduce that risk. The equity overlay makes demographic burden a
> first-class output rather than a footnote, so the disparity is visible in the
> same view as the ranking. The model is framed as operator-consistent
> desirability, not objective viability, so it does not launder historical
> patterns as recommendations. And it's public, which means a community group
> sees the same forecast at the same time as anyone else — which is the
> opposite of the current situation, where only the operator has it."

### F4. "Your model could encode historical bias."

> "It can, and we test for it. We stratify results by ZCTA majority-demographic
> group and report per-stratum accuracy. Where a stratum's error exceeds the
> population error by more than 50%, the application shows a reliability warning
> for that context rather than presenting a confident number. It's aggregate-only
> reporting — no demographic classification enters any model input."

### F5. "Did you use AI to build this?"

> "Yes — for code, for literature triage, and as a component: an agent writes
> to the analytical model behind validation gates. The interesting part was
> discovering where it breaks. Standard gates protect data integrity; none of
> them check whether a valid write invalidates a causal assumption. That's the
> failure class we found and the two gates we added."

### F6. "What's the weakest part of this project?" ⚠

*Have a real answer ready. Deflecting here costs more than the weakness does.*

> "The siting model, and it is not close. I have now fitted two of them and
> neither works. The hazard model lost to a constant — Brier 0.019522 against
> 0.019614, calibration 170 times worse, negative skill on both hold-outs.
> The conditional choice model built to replace it is only matched by a
> single raw Census warehousing count with nothing fitted from it: 19 of 38
> in the top ten against the raw count's 20, and level once you re-split.
> Three estimated parameters bought nothing. That is the weakest part of the
> project and
> I lead with it rather than being walked to it.
>
> If you want the single most damaging fact rather than the headline, it is
> not either of those. **It is that the covariate doing all the work in the
> second model may contain its own outcome, and the guard I built against
> that has a margin of zero.** An Amazon delivery station is itself a
> warehousing establishment; the vintage lag that is supposed to exclude it
> lags off `open_year`, and `open_year` is the OSHA inspection bound rather
> than an opening date on all 100 loaded rows. So the one thing that predicts
> may be predicting partly because it contains the answer. I cannot currently
> rule that out, and nothing in the project fixes it.
>
> Beside that sits the coefficient itself. The intervals landed on the last
> day and they say the warehousing ratio is **not distinguishable from one
> more household**: 95% sandwich [0.734, 2.835] against a null of 1.0, at
> p = 0.287, with every bootstrap variant agreeing. I pre-registered that
> outcome before running it, which helps; it is still a null result on the
> only parameter that does anything.
>
> The root cause underneath all of it is a target variable that cannot carry
> a siting model. The dates are OSHA 'operating by' upper bounds with measured
> lags of 4 to 345 months rather than openings, and both the timing problem
> and the endogeneity problem descend from that one fact.
>
> Third, and worth naming because it will otherwise look like I
> only admit the obvious ones: **the cannibalisation parameter in the
> portfolio optimiser is assumed, not estimated.** 20 km radius, linear
> decay, 0.18 peak. It has no standard error and no donor pool, because the
> design that would have estimated it — the second estimand, spatial
> difference-in-differences with synthetic control — has never been built.
> It feeds directly into the NPV, so if it is wrong the dollar figures move.
> That is why we report rank stability and a break-even frontier rather than
> point NPVs, and why the outputs we lead with are the ones that do not
> depend on it."

> **CORRECTED 2026-09-15 — two of the three paragraphs above have moved, and
> one of them has moved in the project's favour. Learn the amendment; giving
> the old version concedes something that is no longer true, and giving only
> the new version misses the weakness that replaced it.**
>
> **The leakage guard is no longer "unmitigated".** The answer above says the
> margin is zero and nothing in the project fixes it. A decisive test was
> then run (`outputs/metrics/leakage_decisive.json`,
> `../research/NOTES_LEAKAGE_DECISIVE.md`). On the 29 decisions where a
> **stated** MWPVL opening date exists and a Census vintage strictly precedes
> it, the covariate keeps **3.74 of the 4.76 hits it is worth — 79%** — and
> beats the no-covariate floor on **50 of 50** paired re-splits. The
> per-establishment coefficient is the same to within **1.2%** across the two
> datings, which is what agglomeration looks like and is not what a
> contaminated regressor looks like.
>
> It is **not** a clean bill of health, and the caveats are the answer now:
> the test cost two thirds of the sample (94 decisions to 29); it cannot
> separate the leak from the *staleness* that removing the leak introduces,
> so the +1.02-hit gap is an upper bound on the leak rather than a
> measurement of it; a model-free self-count check finds the chosen ZCTA
> really does gain about **one** establishment its neighbours do not (+1.17
> against +0.13), which is exactly the size of the object being predicted,
> concentrated in about a third of the sample; and the 29 are measurably
> easier than the 94 (9.24 of 12 = 77%, against 54% on the full frame). So
> the honest sentence is **"audited, survives with a ~20% haircut of unknown
> split between self-counting and staleness, on a subsample that cannot be
> assumed representative"**.
>
> **And the weakest part of the project has changed.** With the leakage
> defect downgraded from HIGH-and-unmitigated to audited-and-qualified, the
> thing I would now name first is different:
>
> > *"The weakest part is that **three** models have now failed and the third
> > one failed against a pre-registration I wrote myself. Hazard, choice,
> > metro-level entry. At ZIP grain the fitted model lost to a warehouse
> > count; at metro grain it loses to a household count in every year, every
> > model form, every size tier, with and without the pandemic, and whether
> > or not it is allowed to cheat on vintage. There is no version of this
> > project in which the siting model works, and I have now looked for it at
> > two grains with five panel compositions, three algorithms and fifteen
> > covariates."*
>
> **A third item, which is the integrity one and belongs here rather than
> buried at 0.8.** Two figures in the proposal carried fabricated numbers —
> a decay curve with nine hand-typed effects, a band labelled '95% CI', a
> significance annotation and a y-axis variable that does not exist in the
> data; and a tornado chart with per-bar dollar labels and no disclosure at
> all. The project found them in its own audit and fixed them on 2026-09-15.
> That is the weakest part of the project's *process*, distinct from the
> weakest part of its *result*, and Sec. 0.8 is the full answer.

### F7. "What happens if the results are negative?"

*Note the tense. This question was written before the answer arrived. Do not
answer it in the conditional — it already happened.*

> "They are negative, and we reported them. That is not a hypothetical in
> this project; it is the result.
>
> RQ4 asked how much of siting behaviour is explainable from public data.
> The measured answer on this frame is: almost none of it, from 43 buildings
> dated by inspection records. One covariate of three separates from zero and
> it is households, which says Amazon builds where the people are — true, and
> not worth a thesis on its own.
>
> That is a finding about opacity, and it is the finding I have. It tells a
> regulator something concrete: if you want to verify an operator's siting
> behaviour from public records today, the federal inspection trail will tell
> you *where* buildings are and will not reliably tell you *when* they
> opened, and without the when you cannot identify the policy. It also puts a
> price on disclosure — an opening-date registry would be a small
> administrative object and it would close most of this gap.
>
> I said before running it that the version of this project where the
> headline is 'public data isn't good enough for this decision' would be
> worth publishing because nobody had measured it. I now have to live up to
> that, which is harder than writing it was."

> **UPDATED 2026-09-15 — the answer above is anchored on "43 buildings" and
> that is no longer the frame. Two sentences of it are now wrong and the
> replacement is stronger, not weaker.**
>
> The phrase *"from 43 buildings dated by inspection records"* was the
> qualification that made the old answer survivable — it conceded that the
> null might be a small-sample artefact. It can no longer be offered, because
> the sample grew and nothing changed:
>
> ```
>                       then              now
>   facility file       104 rows          693 rows, 687 buildings, 230 CBSAs
>   choice decisions    94                483
>   hazard events       812               5,441 across 275 metros
>   dates               OSHA upper bounds MWPVL stated openings on 545
>   grains tested       ZIP only          ZIP and metro
>   verdict             negative          negative at both grains
> ```
>
> So the current version of this answer is:
>
> > *"They are negative, and the negative is now established rather than
> > suspected. Five panel compositions, three algorithms, fifteen covariates,
> > two geographic grains and a complete reframing all land in the same
> > narrow band. RQ4 asked how much of siting behaviour is explainable from
> > public data, and the measured answer is: at ZIP grain, what a raw
> > warehouse count already tells you; at metro grain, what a household count
> > already tells you; and nothing beyond either.*
> >
> > *That is a finding about opacity and I would now state it with a
> > mechanism rather than a shrug. The variables that would discriminate
> > within a metropolitan area are either published at county grain — about
> > nine distinct values across two hundred candidate ZIPs — or they are
> > population under another name. And at metro grain, the variables that
> > might have discriminated between metros are published **once**, late, and
> > with no usable history: eight of my twelve pre-registered covariates had
> > to be dropped because ACS 2023, BLS OES May 2025 and EJScreen 2024 are
> > single-vintage broadcasts with 1.00 distinct values across all 32
> > quarters of the panel. A covariate you cannot lag is a covariate you
> > cannot use to predict.*
> >
> > *That is a concrete ask a regulator can act on, and it is a different ask
> > from the one I had before. It is not only an opening-date registry. It is
> > that the economic series which already exist should be published with a
> > usable vintage history at a grain below the county."*

---

## Part G — Rapid fire

> **Updated 2026-09-15.** Six rows below carry a `[2026-09-15]` marker: they
> were factually wrong or out of frame as written, and the amendment is
> inline. The rest are unchanged and still correct.

| Question | Answer in one breath |
|---|---|
| **[2026-09-15] How many facilities now?** | **693 rows, 687 buildings, 230 CBSAs, 50 states** in `national_facilities_expanded.csv` (`national_panel_expanded.json`), up from 104. The growth came from OCR'ing an industry PDF into **1,904** facilities, **1,420** of them dated, then filtering to the US small-package delivery-station class (1,269 rows of other classes dropped on purpose) and screening the remaining 635 against the hand-verified panel: 1 internal duplicate, 40 already present, 5 held for clerical review, **589 added** (`mwpvl_extraction.json`, `mwpvl_merge.json`). **0 of 693 carry a coordinate** — every distance covariate is known only to ZCTA-centroid precision |
| **[2026-09-15] How was the OCR validated?** | Three independent ways, all in artefacts. **OSHA cross-check:** of the 1,420 dated rows, 208 link to an OSHA building; 11 claim an opening *after* the date an inspection proves the site was already operating, so the declared edit `E_operating_by` passes on **94.7%** (`mwpvl_validation.json`). **Plausibility:** of the 1,420, 2 delivery-station rows predate the network and **5 are beyond plausible** — the worst claims 2090Q2 against an OSHA record proving operation by 2020. **State cross-check:** the OCR'd state name against the state implied by the ZIP→county→state FIPS crosswalk — **604 of 606 comparable rows agree, 99.67%** (`mwpvl_merge.json`, `ocr_state_grade`). None of the three is a clean bill: 426 of the dated rows could not be checked against OSHA at all, 54 rows had no street to screen on, and the source PDF is not in the repository |
| **[2026-09-15] Was anything pre-registered properly?** | Yes, once, and it lost. `docs/PREREG_METRO_MODEL.md`, written 2026-09-15 before any fit, md5 recorded in `metro_entry.json` as `946f7ef75db69e5278eea409a04c3823`. Both outcomes' language written in advance; five invalidating conditions named in advance; universe fixed at all 935 CBSAs to prevent selection on the outcome. Verdict **H0** — 0 of 7 years on AUC, 3 of 7 on calibration. Sec. 0.5 |
| **[2026-09-15] Is there a rule that comes out of all this?** | Yes, and it is the most transferable thing here — **state it as a rejection rule, not a prediction rule.** Within-metro coefficient of variation, 21 network terms (`gravity_network.json`, `terms.dispersion`): **7 of 7 below cv 0.6 land on the boundary; the region between 0.60 and 1.40 is empty; of the 14 above 1.3, 8 are interior and 6 are not.** So low dispersion is sufficient for failure and high dispersion is necessary but not sufficient. It is a *prior* filter — score any column in seconds before fitting. Shown causal with an exponent knob that varies only within-metro discrimination. **Do NOT say "21 of 21"** — that wording is in the prereg and two notes and it is wrong; Sec. 0.11 has the correction |
| **[2026-09-15] Did you switch to gravity models?** | No, and the case against is stronger now than when it was written. Gravity is a better *measurement* — the only specification whose coefficients never hit the boundary, **0 of 50** re-samples, where `network_within_50mi` is 42 of 50 — and offered both at once the optimiser keeps gravity and pushes the proximities to the boundary in 22 and 28 of 50. But it does not predict better. Current artefact, large-metro top-10 lift over an analytic chance rate, 258 held-out decisions: **gravity 6.2187, published proximity 6.2903, and no network terms at all 6.2585** — gravity is now below even the no-network arm. And it costs zone-merger invariance, which is the specification's only justification: merger error is floating-point zero for the extensive-only control against 0.0436 median / 0.4549 max for the arm carrying network terms, over 43,224 merged ZCTA pairs. **A better measurement that does not predict better, bought with the theoretical foundation. Not adopted.** Note the merger figure is measured on the *proximity* arm; the equivalent gravity number was never computed, and gravity's 3.1-3.9x level drift across vintages suggests it would be worse |
| **[2026-09-15] What single mechanism explains the most?** | **Densification.** At a 45-mile catchment, **75.9%** of 2024-25 openings (79 scored, real-coordinate arm) and **68.7%** (131 scored, fallback arm) land inside territory the pre-2024 network already served — so **roughly seven in ten** (`white_space.json`). Median 7.5 and 10.1 miles to the nearest facility that already existed. That one fact ties together three findings: a raw warehouse count matching the fitted model, network proximity being the only new covariate class ever found interior, and the white-space reframe winning 14 of 108 cells with **zero** significant wins against households' 32. Two caveats to volunteer: the band was "67-77%" before a 2026-09-15 re-geocode of 46 stations and several documents still say so; and at metro grain, once size is controlled, `facilities_open_prior` goes **negative** in all seven years, so densification is a statement about where the big metros are rather than an independent mechanism at that grain |
| What's the unit of analysis? | It **was** the ZCTA-quarter, and that was the mistake — a station flips a whole 15-mile catchment at once, so ZCTA-quarters are not independent observations (Train §3.7.1, p. 61). It is **now** the siting decision: which ZIP, given a station opens. 94 of them, on the national frame |
| How many? | 2,413 ZCTAs modelled in depth across ten metros; 33,791 in the national warehouse |
| What's the target? | Did the operator enable same-day service here, and in which quarter |
| Main method? | **Settled and fitted.** The hazard specification was built, fitted and failed; the conditional ZCTA-choice successor was then built and fitted (`choice_report.json`). ADR-0004 records the change and is deliberately still `proposed`, because ratifying it is the user's decision. Moment inequalities and Molinari interval-outcome partial identification remain open as complements, and three project documents disagree about whether that question is closed — see ADR-0004 |
| Does the model work? | **[2026-09-15] No, three times.** Hazard: Brier 0.019522 vs a constant's 0.019614, ECE 0.00863 vs 0.00005, AUC 0.6894 vs 0.5000, negative skill on both hold-outs — **and revived on 5,441 events with real dates it scores 0.6832 and loses calibration 0 of 17**. Choice: held-out top-10 19/38 against 20/38 for one raw warehousing count with nothing fitted, and the 95% interval on its only working coefficient covers the null (sandwich [0.734, 2.835] against a null of 1.0, p = 0.287) — **on the 483-decision expanded panel the interval is 64% narrower at [0.956, 1.490] and still covers it**. Metro entry: **pre-registered and lost, 0 of 7 years against "rank by households", pooled AUC 0.7323 vs 0.8949, metro-clustered bootstrap -0.163 [-0.201, -0.131], 50 of 50 paired re-splits lost** |
| Why did it fail? | The hazard model: the wrong unit, giving pseudo-replication — **still unfixed at any radius; one opening switches on a median 39 ZCTAs and the sweep from 8.3 to 45 miles never gets it below 14**. The choice model: the right unit and nothing left to learn — the public record supports the ranking and not the parameters. The metro model: **the ceiling is the baseline**, and separately the vintage gate removed 8 of 12 covariates because the panel's economic columns are single-vintage broadcasts with 1.00 distinct values across all 32 quarters. All three share a target variable that is too loosely dated |
| **[2026-09-15] Was it under-powered?** | **No, and that is now measured rather than argued.** That was the original story. The hazard model went from 5.6 events per parameter (below the floor of 10) to **87.2** and the AUC went *down*. The choice model went from 94 decisions to 483 and the coefficient moved *towards* the numeraire. The GBM's one-decision edge disappeared entirely at the larger sample (0.5198 vs 0.5196). Power is not the binding constraint; the data is |
| What *does* work? | Cost model ($1.0830/parcel median, 2,333 ZIPs), portfolio optimiser (282 activations, $1.128bn, declines ~44% of a $2bn budget), a 500-draw Monte Carlo that shows 282 is an ordinary draw and the superseded 330 was not, the warehouse, six agent gates, 648 tests passing with 2 xfail at commit b29071e — four of five components, none of which needed the facility panel |
| How was it validated? | Hazard: a unit-clustered test split (primary), a temporal split and a two-metro geographic hold-out (both secondary, both negative), plus conformal coverage at 88.19% against 90% nominal with 10.09% empty sets. Choice: a 56/38 split over decisions, top-k and the raw Brier pair against four single-covariate benchmarks and a uniform null. Conformal at 90% covers perfectly by naming 71% of the metro, which is near-vacuous |
| Biggest risk? | **[2026-09-15] It has moved.** It used to be the vintage-lag guard's margin of zero on the headline covariate. That has now been **audited**: with MWPVL stated dates the covariate retains **79%** of its value and beats the no-covariate floor 50 of 50 (`leakage_decisive.json`, n = 29), and the per-establishment price is unchanged to within 1.2%. The biggest risk now is that **three models have failed at two grains and there is no fourth design in reserve** — and, behind that, that the source PDF supplying 589 of 693 panel rows is not in the repository and cannot be reproduced from what is (`AUDIT_2026_09_14.md` §1.1). See F6 |
| Second estimand? | Spatial DiD with synthetic control for cannibalisation. **Never touched.** The optimiser's 20 km / 0.18 penalty is assumed, not estimated |
| Total cost? | $80, inside a $100 cap. Compute is $0 |
| Data size? | 1,081,312 rows, 14 MB — deliberately |
| Why public data? | Because checkability is the product |
| What's genuinely new? | Delivery stations as a facility class (zero hits in Houde et al.); a free OSHA-derived panel where the literature buys Trade Dimensions and MWPVL; and a measured negative result about what public data can identify |
| What's not new? | Every estimator. All have paywalled equivalents |
| Timeline? | Nine weeks, with week 0 for decisions — and those seven Phase-0 decisions (D1-D7 in `../ROADMAP.md`) are still open |

---

## Part H — Six rules for the room

**1. Name the weakness before they do.** Every time you volunteer a limitation
with its mitigation and its residual, you buy credibility for the claims you
keep. Every time you defend something indefensible, you spend it.

**2. Never say "first" or "novel."** Say "not published in the open literature"
or "not available as something anyone can check." Those stay true regardless of
what any vendor ships.

**3. If you don't know, say so and say what you'd do.** "We can't measure that
— here's what we report instead" is a complete, strong answer. Bluffing is
the only failure mode that isn't recoverable.

**4. Never quote a number this project has not computed.** The pack contains
illustrative arithmetic — an 8 km decay band, a rank of 1 in 40, a
first-stage F — and none of it is a measurement. If an examiner asks for one
of those, the answer is "that is the design, I have not run it." An invented
figure is the one error that turns a negative result into an integrity
problem, and a negative result you can defend is survivable in a way that an
integrity problem is not.

> **Reinforced 2026-09-15, because this rule was broken.** Two committed
> figures asserted a 95% confidence interval, a significance test and
> per-bar dollar labels on numbers that were typed into the plotting code —
> and one of them did it on a y-axis variable the project does not observe.
> They were found by the project's own audit and fixed. Sec. 0.8 is the
> answer if it comes up, and it is the answer you should rehearse hardest,
> because it is the only question in the pack that is about integrity rather
> than about competence.
>
> The operational version of rule 4 is therefore stronger than "do not quote
> what you have not computed". It is: **before you show a figure, be able to
> name the artefact it was built from, or say in the same breath that it is
> a schematic.** If you cannot do either, do not show it.

**6. Re-read the artefact before you quote it, and say the run id if you
can.** *Added 2026-09-15.* Two artefacts were re-run after the notes that
cite them were written — `gravity_network.json` and `white_space.json` — so
several figures in the research notes no longer match the file at the path
they cite. The differences are small and none reverses a conclusion, but an
examiner with the JSON open will see a different number from the one on your
page. The right response is flat and unembarrassed: *"that note was written
against an earlier run; the current value is X."* The pre-promotion copies
are on disk under `data/interim/prepromotion_backup/` if anyone wants the
diff.

**5. Say "it failed" in those words.** The siting model failed. Every softer
phrasing — refined, evolved, under-powered, directionally right — costs you
credibility you then have to spend defending the four components that
actually work. Lead with the failure and the rest of the viva is about the
project, not about whether you can be trusted to describe it.
