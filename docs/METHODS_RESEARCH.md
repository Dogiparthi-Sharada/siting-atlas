# Methods research log

**What we read, what it changed, and what we rejected.** A reader who
finishes this file should be able to reconstruct *why* the method is what it
is, and defend each choice against someone who has read the same papers.

This document is about **method**. How the data was collected, and every way
it is weak, is a different document:
[`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md).
This file does not restate it; it assumes you have read the one-paragraph
version — *the panel began as 43 buildings whose "opening dates" were upper
bounds taken from the date OSHA opened an inspection case at the address, and
is now 693 rows / 687 buildings after an OCR pass over a published industry
census supplied stated openings for part of it.*

**Sec. 14 is the unit-of-analysis diagnosis** — why the first model failed,
with the citation corrected. **Sec. 15 is the ledger** of which paper changed
which line of code. Both were relocated here from the retired `PLAN.md` on
2026-09-15.

> **Why this file exists.** The project spent a day reading seriously and
> recorded none of it. Before this file was written, the repository had
> **zero** occurrences of "Trade Dimensions", "Fellegi", "partial
> identification", "PPHI" and "Politis". Houde et al. appeared in the
> defence notes, but as prior art noted weeks earlier, not as something read.
> A method nobody can trace the reasoning of is a method nobody can defend.

---

## How to read the claims in this file

Every claim carries a tag, because the difference matters more than anything
else here.

```
  SAYS   The source states this. A section number is given. If the
         section number is wrong, the claim is wrong -- check it.

  WE     Our reading, applied to this project. Arguable. A reviewer
         may agree with the SAYS line and reject the WE line.

  OPEN   Not decided. Deliberately unresolved; do not quote it as a
         position.
```

Section 10 is the corrections log: every claim that went into the first
draft of this file and **did not survive contact with the source**. It is
there because the rate at which our beliefs about these papers were wrong
(roughly one claim in three) is itself a finding.

---

## 1. The reading list

| Source | What it is |
|---|---|
| `ecta7699.pdf` | Holmes (2011), "The Diffusion of Wal-Mart and Economies of Density", *Econometrica* 79(1) 253-302 |
| `ECTA15265.pdf` | Houde, Newberry & Seim (2023), "Nexus Tax Laws and Economies of Density in E-Commerce: A Study of Amazon's Fulfillment Center Network", *Econometrica* 91(1) 147-190 |
| `2017-houde.pdf`, `w23361.rev1.pdf` | NBER working-paper ancestors of the above. **Not** drafts of it — see Sec. 3.4 |
| `Ch01`..`Ch14` | Train (2009), *Discrete Choice Methods with Simulation*, 2nd ed. |
| `CWP2519.pdf` | Molinari (2019), "Econometrics with Partial Identification", cemmap CWP25/19, dated 30 May 2019 |
| `ECTA14075.pdf` | Kaido, Molinari & Stoye (2019), "Confidence Intervals for Projections of Partially Identified Parameters", *Econometrica* 87(4) 1397-1432 |
| `rr99-04.pdf` | Winkler, "The State of Record Linkage and Current Research Problems", US Census Bureau. **The year is printed nowhere in the paper**; internal evidence (a shorter version in the 1999 SSC Proceedings, latest references 1999) dates it to 1999 |
| `Gneiting2007jasa.pdf` | Gneiting & Raftery (2007), "Strictly Proper Scoring Rules, Prediction, and Estimation", *JASA* 102(477) 359-378. Read in full; notes in [`research/NOTES_gneiting_raftery_2007.md`](research/NOTES_gneiting_raftery_2007.md). **Use this copy, not `27639845.pdf`** — the latter is the same paper as a JSTOR scan with a cover page, so every PDF page number in it is one too high |

All PDFs live in `MSBA_Project/Research/`.

---

## 2. Holmes (2011) — the moment-inequality machine

### 2.1 What the machine is

SAYS (Sec. 6.1). Holmes follows "the partial identification literature
initiated by Manski (2003)", and within it "Pakes, Porter, Ho, and Ishii
(2006) (hereafter PPHI)". The object is a set of `M` linear inequalities

```
      y_a  >=  x_a * theta ,      a in {1, 2, ..., M}
```

where `a` indexes a **deviation** from the policy the firm actually chose,
`y_a` is "the incremental operating profit from doing a-observed rather than
a", and `x_a * theta` is "the incremental cost". Non-negative instruments
`z_ak >= 0` multiply through and are averaged, collapsing `M` inequalities
into `K` moments `m_k(theta) >= 0`. The criterion is

```
      Q(theta) = sum_k  min{0, m_k(theta)}^2
```

and the estimator `Theta-hat_I = argmin Q` (Sec. 6.1 eq. 12). Identification
is **partial**: "there is a set of points satisfying the moment
inequalities, rather than just a single point" (Introduction).

**A concrete example, in our units.** Amazon opened a delivery station in
Joliet in 2019 and one in Aurora in 2022. Deviation `a` says: *swap them* —
Aurora in 2019, Joliet in 2022. If Amazon was optimising, the profit it
actually earned is at least the profit under the swap, so the profit
difference must cover the cost difference. That is one inequality. On our
43-building panel there are `43*42/2 = 903` such pairwise swaps, of which
**527** are more than a year apart; on the unused 104-station national panel
it is 5,356 and **3,533**.

### 2.2 The measurement-error result

This is the result the project adopted the aggregation for, and it is real.

SAYS (Sec. 6.1). Verbatim:

> "If there is measurement error with full support, then asymptotically the
> estimated set goes to minus infinity. In large samples, significantly
> negative outlier draws of eta_a pin down the estimate. In contrast, by
> aggregating to moment inequalities, the measurement error averages out in
> large samples."

The setup: with the disaggregated inequalities you require *every* one to
hold, so the solution set is `{theta | theta <= min_a (y_a + eta_a)}`. One
sufficiently unlucky negative draw drags the bound down, and with full
support you always eventually get one. Bajari, Benkard and Levin (2007) is
named as the disaggregated approach that this breaks.

**The example.** Suppose the truth is `theta = 5` and we have 500 noisy
readings of a quantity that must be at least `theta`. Take the minimum of
500 draws and you are reading the worst error in the sample, not the truth,
and the more data you collect the worse it gets. Take the *mean* of 500
draws and the errors cancel. Aggregation is the whole trick.

### 2.3 The assumption we probably violate

SAYS (Sec. 6.1). The error condition is stated as `E[eta_a | x_a, z_ak] = 0`
— conditional-mean-zero given both the regressors and each instrument. In
the application (Sec. 6.2) Holmes reaches a weaker-looking `E[eta_a | x_a] =
0` from a *stronger* primitive: the underlying store-level errors are "mean
zero and independent of the other variables in the analysis". He is explicit
that consistency needs the error to average out across stores, and that
cross-store independence is "sufficient but not necessary".

WE. We probably violate this. OSHA opens inspection cases at large, busy,
complained-about facilities sooner than at quiet ones. Busy correlates with
throughput, throughput correlates with local demand density, and demand
density is our main covariate. That makes the date error a function of `x`,
not independent of it.

**The example.** Two stations open the same month. The one in a dense metro
runs 400 routes a day, has more injuries, and is inspected within a year.
The one in an exurb runs 90 routes and is inspected eight years later. Our
measured "opening date" is later for the *less* dense site, so the error is
correlated with density by construction — exactly what `E[eta|x] = 0`
forbids.

OPEN. This is recorded as a **live threat, not a solved problem**. No
correction is implemented and none is proposed here.

### 2.4 The finding that most threatens this route

This is the most important thing in Holmes for us, and it is not the
measurement-error result of Sec. 2.2. It cuts the other way.

SAYS (Sec. 6.1). "Assume `x_a` and `z_ak` are **directly observed**, but
there is measurement error on `y_a`." The framework tolerates error on the
left-hand side only.

SAYS (Sec. 8.3). "This is a concern because my procedure yields
**inconsistent** estimates of the identified set `Theta_I` when there is
measurement error in the `x` variables."

SAYS (Sec. 7). "The group definitions depend only on store locations and
**opening dates, and these are all assumed to be measured without error**,
that is, there is no measurement error in chi_ka. ... Hence, chi_ka is a
valid instrument."

WE. Read those three together. Holmes's protection is for error in profits.
His instruments are built from **opening dates**, which he assumes exact.
Our opening dates are the single most mismeasured object we have, and under
the swap design they simultaneously (i) define which deviations exist,
(ii) define the instrument groups, and (iii) enter the cost side `x` through
the discounting window. The result Sec. 2.2 gives us protects the one place
our error is *not*.

WE. This does not kill route (A), but it moves the burden. Anyone proposing
it has to argue either that date error is confined to `y`, or that the
guard-band trick (Sec. 3.2) buys enough robustness. Neither argument has
been made yet.

### 2.5 Inference: subsample the unit, not the deviation

SAYS (Sec. 8.1). "There are `M = 523,000` deviations used in the analysis,
but these are derived from only `N = 3,176` different store locations. If
Sigma-hat/M is used to estimate the variance ... the amount of averaging
that is taking place is exaggerated, since the measurement error is at the
store level." The fix cites Politis, Romano and Wolf (1999): draw a
**store-level** subsample of size `b = N/3`, keep the deviations whose both
endpoints are in it, and rescale

```
      varcov(w_N)  =  (b / N) * varcov(w_b)
```

Two details worth carrying: `b = N/3` specifically, and Holmes says
"subsampling **with replacement**", which is not textbook Politis-Romano-Wolf
subsampling. The exact deviation count is 522,967; 523,000 is his own
rounding.

WE. The same arithmetic destroys any naive standard error we would compute.
Our 527 usable swaps come from 43 buildings. Treating 527 as the sample size
overstates the averaging by roughly `527/43 ~ 12x` in the variance.

### 2.6 Other caveats Holmes himself flags

| Holmes says | Section | Why it matters here |
|---|---|---|
| No optimisation error is modelled: any deviation that looks more profitable is attributed to measurement error | 7 | Amazon behaving suboptimally would be misread as noise |
| No structural error / unobserved location heterogeneity; he states this "potentially underestimate[s] density economies" | Conclusion | Our unobservables (land, labour, politics) are large |
| The CIs are "for extreme points of the identified set", not for the true parameter, and PPHI did not address uniformity (Andrews-Guggenberger, Andrews-Soares) | 8, 8.1 | Do not report a Holmes-style CI as a CI for a parameter |
| A calibrated first-stage margin moved the lower bound from $3.50 to $2.62 when changed from .17 to .15 — a swing larger than the reported CI, and *outside* it | 8.3 | Our Daganzo cost inputs are calibrated the same way |
| The set narrows only because 336 constraints are piled on; with 12 it is [3.33, 4.92], with 336 it is [3.50, 3.67] | 7, Table XI | Sharpness is bought with instruments, and we have few |

### 2.7 The 336 restrictions

SAYS (Sec. 7). Twelve basic instruments (group indicators, Table IX),
weighted by `1/sum (rho*beta)^(t-1)` to the present value at the point the
deviation begins. Then two tiers of interactions: "72 = 6 x 12 level 1
interaction moments" and "252 = 21 x 12" level 2, so "there are **336 = 12 +
72 + 252** restrictions". Verified exactly, including the "two tiers"
characterisation.

---

## 3. Houde, Newberry & Seim (2023) — the same machine, on Amazon

### 3.1 What they did

SAYS. *Econometrica* 91(1) 147-190, 2023, confirmed from the paper's own
masthead. They study **fulfilment centres and sortation centres** and ask
how nexus (physical-presence) sales-tax laws distorted *where and when*
Amazon opened facilities between 1999 and 2018. Opening a facility in a
state triggers sales-tax collection on every consumer in that state, so the
cost-minimising network (dense, near people) fights the revenue-maximising
one (sparse, away from people).

SAYS (Sec. 2.6). Facilities are clustered: "Roughly, this amounts to
grouping facilities that are within 20 miles of each other", and "cluster"
and "location" are used interchangeably. The network "expanded from five
individual facilities in 1999 to **128** by 2018"; active clusters grew
"from five in 1999 to **70** in 2018".

SAYS (Sec. 4.3 — **not** Sec. 3.5; see Sec. 10). The estimator: "three
criteria to select potential entry date swaps: (i) facility j opened more
than one year before facility j-prime, (ii) facilities j and j-prime are of
the same type (FC or SC), and (iii) the difference between the sizes of j
and j-prime is less than 550,000 sq ft, the inter-quartile range of capacity
differences." This gives "`M = 5577` potential permutations".

The estimand is three cost parameters: shipping cost per order per 100 miles
(`$0.34`), the per-order saving from routing through an in-house sortation
centre (`-$0.52`), and a congestion exponent on fixed cost (`0.98`).

### 3.2 What they do that we should copy

- **Only the opening date is perturbed.** Location, square footage, type and
  the end-of-sample facility count are all held fixed. Sec. 4.3: "By
  focusing only on deviations involving observed facility locations, our
  estimation results are robust to the presence of these dynamic
  considerations." The profit difference telescopes to the window between
  the two swapped dates, so no infinite-horizon dynamic programme is needed.
- **The one-year separation rule is a guard band.** WE: criterion (i) is not
  presented as a robustness device, but it functions as one — a swap of two
  facilities opened three months apart carries almost no signal and is
  maximally vulnerable to date error. With upper-bound dates we would need a
  much wider band than one year.
- **Instruments are built from *pre-determined* quantities.** Population-
  weighted proxies define the instruments; order-weighted aggregates enter
  the moments. Seven trade-offs, each giving an upper and a lower moment =
  **14 moments** in the preferred specification. Table V is a published
  diagnostic that the instruments induce the expected sign pattern.
- **They adjust for swap correlation, as Holmes does.** Footnote 22: the
  empirical correlation between moments sharing a facility is estimated at
  0.3 and used when sampling bootstrap shocks. 5,577 swaps come from ~163
  facilities.
- **Inference is Bugni, Canay and Shi (2017) profiling**, not subsampling,
  with Kaido-Molinari-Stoye cited as the alternative.

### 3.3 What they acknowledge they cannot do

SAYS. "our moment inequalities estimator is only able to capture costs that
vary across the locations in the network" — no intercept, no system-wide
investment. WE: this method identifies *differential* siting cost and never
the base cost of a building. A city asking "what would it cost to serve us"
gets no answer from it.

### 3.4 The working papers are a different paper

SAYS. The 2017 NBER version (w23361) **includes** Prime Now Hubs rather than
dropping them, defines a cluster as same-state *and* within 20 miles, has
`J = 60` clusters and **1,575** perturbations, and uses an Andrews-Soares
bootstrap. The strings `5577`, `550,000` and `128` return zero hits in it.

WE. Do not cite the working paper as a cross-check on the published numbers.
Cite one or the other and say which.

---

## 4. The provenance finding, and the novelty defence

This is the finding that most changes how the project should be positioned,
and it took four greps to establish.

SAYS (Holmes Sec. 3). "The first data element comprising store-level
variables was obtained from **Trade Dimensions, a unit of ACNielsen**."

SAYS (Houde et al. Sec. 2.2). "We obtain information on Amazon's
distribution network from the supply-chain consulting company **MWPVL,
International** (http://www.mwpvl.com/)." MWPVL supplies "location, size in
square feet of floor space, employment, facility type, opening date, and
closing date".

SAYS (Houde et al. Sec. 1, Sec. 2.2). "We focus on two types of facilities:
(i) fulfillment centers and (ii) sortation centers", and "We drop
specialized distribution centers, including 'PrimeNow Hubs', Amazon Fresh
grocery delivery centers, return centers, and distribution centers for
select high-value items such as jewelry."

**Grep results on the published Houde et al. text, case-insensitive:**

```
  "delivery station"   0 hits
  "delivery-station"   0 hits
  "same-day" / "same day"   0 hits
  "last mile"          1 hit   (Sec. 1, in passing)
  "last-mile"          3 hits  (two of them in footnotes, one of which
                                says Amazon began investing in last-mile
                                delivery AFTER their sample ends)
```

WE. The project therefore differs from the two definitive papers on three
axes, and it is worth being precise about which:

| Axis | Holmes 2011 | Houde et al. 2023 | This project |
|---|---|---|---|
| Facility type | Wal-Mart stores + DCs | Fulfilment + sortation centres; PrimeNow Hubs dropped | **Delivery stations** — unstudied in either |
| Data provenance | Trade Dimensions (ACNielsen), purchased | MWPVL International, purchased | **Federal OSHA bulk records, free and reproducible** |
| Question | Economies of density in store rollout | Did nexus tax law distort the network, and what was the welfare cost | **Which ZIPs get served, and can a city verify it** |
| Spatial unit | Store, county | County (demand), 20-mile cluster (supply) | **ZCTA** |

WE. Note what this table does *not* claim. It does not claim a new
estimator. Both of those papers use the same estimator, and we would be
using theirs. The claim is grain, data regime, and question. That is exactly
the claim the project's novelty answer already makes — this file supplies the
evidence for it, which that answer previously asserted without.

WE. One correction that keeps resurfacing. Houde et al. are repeatedly
described as studying "the 2-day network at state grain". Their
demand side is at **county** grain and their supply side is a 20-mile
cluster; state is the unit of the *tax* variation, not of the analysis.

---

## 5. Train (2009) — what the textbook changed

Twelve items. Each is "what we believed", "what Train says", "what changed".
Section numbers here have been checked one at a time and several of the ones
we started with were wrong; the corrections are in Sec. 10.

### 5.1 Our choice set was not a choice set

SAYS (Sec. 2.2). "the alternatives must be mutually exclusive from the
decision maker's perspective", "the choice set must be exhaustive", and "the
number of alternatives must be finite". Train adds that the first two "are
not restrictive" because you can nearly always define your way out of them,
while finiteness "is actually restrictive ... the defining characteristic of
discrete choice models". He also notes the specification "is governed
largely by the goals of the research and the data that are available to the
researcher".

WE. Our ZCTA-quarter alternatives fail mutual exclusivity, and not
marginally. A delivery station switches on **every ZCTA within 15 miles at
once** (`warehouse/facilities.py`, `CATCHMENT_MILES`). Measured on the
delivered panel: the median station covers **58** ZCTAs, the mean **88**, and
the largest **307**. "Amazon chose ZIP 60608 in 2021Q2" is not a choice; it
is one of 88 simultaneous consequences of one choice.

> **CORRECTION 2026-09-14, and it narrows this section's claim.** The
> paragraph above is the right observation attached to the wrong rule.
> Sec. 2.2 governs a choice set facing a decision maker, and a cloglog hazard
> on ZCTA-quarters has no decision maker choosing among ZCTA-quarters, so
> exclusivity is not a property it can violate. Train also calls the
> criterion "not restrictive" (p. 12, quoted in the SAYS block above) and
> gives a two-line repair recipe, which is not the shape of a fatal test.
> The assumption actually violated is **Sec. 3.7.1, printed p. 61**:
> *"assuming that each decision maker's choice is independent of that of
> other decision makers"*. Fifty-eight ZCTAs switched on together are one
> draw entered 58 times, the likelihood multiplies them as independent, and
> the standard errors are correspondingly too small. Smaller claim, true
> claim. **Sec. 2.2 is the authority for BUILDING the successor choice set,
> not the charge against the old model.** Sec. 14 below and
> `MODEL_SPEC.md` Sec. 3.5 carry the argument; recorded in Sec. 10 below.

WE. The reframe: **which ZIP does the station go in, conditional on a
station opening in metro `m` in period `t`.** That is a real, exclusive,
enumerable choice. It gives 43 decisions on the pilot frame and **104** rows
on the national frame (`national_facilities.csv`, 62 CBSAs).

> **BUILT, 2026-09-14.** `models/choice.py`. The fit uses **94** decisions,
> not 104. Four rows are excluded upstream by the `E_operating_by` edit,
> leaving 100 loaded; `choice.build()` then drops a facility whose own ZCTA
> is absent from the panel (a choice set that does not contain the observed
> choice has zero likelihood and would silently poison the fit) and one with
> no CBP vintage strictly earlier than its opening year (scoring it on a
> contemporaneous vintage would let the covariate contain the outcome).
> 56 train, 38 held out. `outputs/metrics/choice_report.json`. Quote **94**
> for the fit, **100** for the loaded frame and **104** for the file, and say
> which.

### 5.2 Sampling of alternatives does not rescue us

SAYS (Sec. 3.7.1, under the unnumbered heading "Estimation on a Subset of
Alternatives"). "**With a logit model**, estimation can be performed on a
subset of alternatives without inducing inconsistency." The reason, given in
Sec. 3.3.2, is IIA. The problem it solves is stated in Sec. 3.7.1: "the
number of alternatives facing the decision maker is so large that estimating
model parameters is very expensive or even impossible."

WE. Two consequences. First, it is a **logit-only** result, so it does not
survive to a probit or a mixed logit. Second, and decisively: the machinery
is built on `q(K|i)`, the probability the researcher's sampling scheme draws
subset `K` — which presupposes the researcher can enumerate the full set
`F`. It solves "too many alternatives", not "we do not know what the
alternatives were". Our problem is the second. Sec. 5.1's reframe is the
fix; this is not.

Worth carrying: without McFadden's uniform conditioning property you must
add a correction term `ln q(K_n|j)` **with its coefficient constrained to
1**, and the estimator is consistent but not efficient.

### 5.3 Zonal alternatives force V = ln(beta'a)

SAYS (Sec. 3.4, Example 2 "Geographic Aggregation"). "The difficulty in
specifying representative utility comes in recognizing that the researcher's
decision of how large an area to include in each zone is fairly arbitrary."
If two zones merge, the model should give the combined zone the sum of the
two probabilities. Because the attraction variables are additive across
zones (`a_j + a_k = a_c`), that holds only if `exp(V_j) + exp(V_k) =
exp(V_c)`, which requires

```
      V_n  =  ln( beta' a_l )      for every zone l
```

"to specify a destination choice model that is not sensitive to the level of
zonal aggregation, representative utility needs to be specified with
parameters inside a log operation."

WE. ZCTAs are exactly Train's arbitrary traffic zones — worse, they are
drawn to make postal routes tidy, and the Census redraws them. If our
utility is linear in households and jobs rather than `ln(beta' a)`, then
merging two adjacent ZCTAs changes the answer, and "the answer changes when
the Post Office reorganises" is not a defensible property.

**The example.** Two ZIPs of 10,000 households each. A log-form model says
the merged ZIP of 20,000 gets the sum of their probabilities. A linear-in-`V`
model says it gets `exp(b*20000)` where it should get `2*exp(b*10000)` —
which are equal only if `b = 0`.

### 5.4 AUC was the wrong scoreboard (with a correction)

SAYS (Sec. 3.8.1). "Another goodness-of-fit statistic that is sometimes
used, but should actually be avoided, is the 'percent correctly
predicted'." The reason: "The statistic is based on the idea that the
decision maker is predicted by the researcher to choose the alternative for
which the model gives the highest probability. However ... the researcher
does not have enough information to predict the decision maker's choice."

WE — **weaker than the version we started with, and the correction matters.**
Our first draft said AUC "is a rank statistic over the same probabilities
and inherits the defect". It does not inherit *that* defect: Train's
objection is to hard assignment, and AUC never thresholds. The defensible
version is a different one. AUC is invariant to any monotone transform of
the predicted probabilities, so it is structurally incapable of detecting
miscalibration, and Train's deeper complaint in Sec. 3.8.1 — that the
statistic "misses the point of probabilities" — lands on that.

WE. Our own numbers make the case better than the citation does.
`STATUS.md`: AUC 0.6894, which reads as a result; ECE 0.00863 against the
null model's 0.00005, i.e. **170x worse calibrated than predicting one
constant everywhere**; Brier skill -0.0209 out of time and -0.0618 out of
geography. The headline should have been Brier skill and ECE from the start.

**Correction to the correction, 2026-09-13, after reading Gneiting & Raftery
(2007).** Two things above are looser than they should be.

*First*, "AUC never thresholds" is wrong as written. AUC is the integral of
the ROC curve *over* all thresholds; what it never does is commit to **one**
threshold. Say that instead.

*Second*, Train's objection has two limbs and we only quoted one. The full
sentence is: "The procedure misses the point of probabilities, **gives
obviously inaccurate market shares**, and seems to imply that the researcher
has perfect information" (Sec. 3.8.1). The hard-assignment limb AUC escapes.
The market-shares limb it does **not** — AUC is invariant to every strictly
increasing transform of the predictions, so it is indifferent to whether the
predicted rates reproduce the observed rates, which is the same indifference
Train is complaining about. So the honest form is *"AUC escapes the
hard-assignment limb but not the market-shares limb"*, not *"AUC does not
inherit that defect"*.

SAYS (Gneiting & Raftery 2007, Sec. 3.1 Example 4, p.363; Theorem 3 and
Table 1, pp.364-365). Train's "percent correctly predicted" has a formal name
and a theorem. It is the **zero-one score**, "also known as the
misclassification loss", and "the meteorological literature uses the term
*success rate* to denote case-averaged zero-one scores". Its status is stated
flatly: "The score in Example 4 is proper but not strictly proper" (p.362).
Two equivalent reasons are given. Its entropy function `G(p) = max_j p_j` "is
neither differentiable nor strictly convex". And in Schervish's
representation, where every binary scoring rule is a mixture of
threshold-at-`c` decision rules weighted by a measure `nu(dc)` over cost-loss
ratios, the zero-one score's `nu` is a **point measure at a single `c`**,
whereas "the scoring rule is strictly proper if and only if `nu` assigns
positive measure to every open interval". The Brier score's `nu` is uniform
over `(0,1)`.

WE. That is Train's prose objection made exact, and it is a better citation
than the prose. A merely-proper rule does not *uniquely* identify the true
probability: a range of different forecasts all maximise it, so the statistic
cannot choose among them. Percent-correctly-predicted checks one cost-loss
ratio; the Brier score checks every one.

WE — **and the limit of the upgrade, which matters more than the upgrade.**
This does *not* transfer to AUC. Gneiting & Raftery never mention AUC, ROC,
discrimination or the area under any curve; the words appear zero times in the
paper, and the only gesture at that literature is a single citation of Pepe
(2003) in the future-work section (Sec. 10, p.376). Nor can their theorems be
applied to AUC second-hand: a scoring rule in their sense is `S(P, x)`,
evaluated on one forecast-observation pair and then averaged over cases
(Sec. 2.1 p.360, Sec. 2.3 p.362). AUC is a rank statistic over *pairs of
cases* and cannot be written in that form, so propriety is **undefined** for
it rather than violated by it. Do not write "Gneiting and Raftery show AUC is
improper". The defensible sentence is: *the guarantee we want from a headline
metric is the one in their equation (1), and AUC is not the kind of object
that can carry it.*

Full treatment, with the propriety hit against the Brier **skill** score that
this argument has to concede, is in Sec. 12 below.

### 5.5 The OSHA date is a censoring structure, not a data defect

SAYS (Sec. 7.5, Contingent Valuation). The estimation "is closely related to
that just described for ordered logits and probits, except that **the cutoff
points are given by the questionnaire design rather than estimated as
parameters**". Person `n` is offered a prompt `k_n`, "answers the question
with a 'yes' if `W_n > k_n`", and "The figure that is used as the prompt ...
is varied over respondents". This is "single-bounded, since the person's
answer gives one bound on his true willingness to pay". Double-bounded adds
a follow-up and brackets the latent variable on both sides.

WE. Replace *willingness to pay* with *true opening date* and *the offered
price* with *the OSHA inspection date*, and it is the same likelihood. The
threshold is known, observation-specific, and varies across observations for
reasons unrelated to the parameter of interest (in Train's case the survey
design; in ours, see Sec. 2.3, **not** unrelated, which is the difference).
An upper-bounded date is a standard single-bounded likelihood, not a broken
variable.

WE. This is the single most actionable item in this file. It is the same
conclusion `STATUS.md` defect A reaches from the survival-analysis side, and
the two arriving independently is a reason to believe it.

### 5.6 We defined far too many time periods

SAYS (Sec. 7.7.3 — **not** 7.7.2; see Sec. 10). "The first suggestion is for
the researcher to consider ways to capture the nature of the choice
situation with as few time periods as possible. Sometimes, in fact usually,
time periods will need to be defined not by the standard markers, such as
the year or month, but rather in a way that is more structural with respect
to the decision process." His example: a two-period college model may be
*more* accurate than an annual one, because students think in terms of "the
college years and their post-college options".

WE. Our panel is **32 quarters** (2018Q1 to 2025Q4; `dim_date` = 32, and
1,081,312 rows = 33,791 ZCTAs x 32). Amazon's delivery-station build-out has
roughly three eras, visible in the national panel's opening years:

```
  pre-2020        11 stations   the early, sparse build
  2020-2021       15            the pandemic surge
  2022-2026       78            the mature rollout
```

WE. Thirty-two quarterly baseline-hazard terms to describe three regimes is
where a large share of our 7.6-events-per-parameter problem comes from.

### 5.7 The closed-form dynamic model, and its price

SAYS (Sec. 7.7.3, "Uncertainty about Future Effects"). "A second powerful
simplification was first noted by Rust (1987). Suppose that the factors that
the decision maker does not observe beforehand are also the factors that the
researcher does not observe (either before or after), and that these factors
are thought by the decision maker to be iid extreme value. Under this
admittedly restrictive assumption, the choice probabilities take a closed
form that is easy to calculate." And: "The model takes the same form as the
upper part of a nested logit model: the first-period choice probability is
the logit formula with a **log-sum term included as an extra explanatory
variable**."

SAYS (Sec. 7.7.3, final paragraph — quoted in full, because the second
sentence is the half people drop):

> "It is doubtful that the researcher, in reality, observes everything that
> the decision maker knows beforehand. However, the simplification that
> arises from this assumption is so great, and the curse of dimensionality
> that would arise otherwise is so severe, that proceeding as if it were
> true is perhaps worthwhile in many situations."

SAYS (Sec. 7.7, unnumbered introduction). "Myopic behavior nearly always
appears as a testable restriction on a fully rational model, namely, a zero
coefficient for the variable that captures future effects." In Sec. 7.7.1
this is `lambda = 0`.

WE. A forward-looking siting model is therefore available to us at the price
of one assumption and one extra regressor, and whether Amazon sites myopically
becomes a **testable hypothesis** rather than a modelling stance.

WE. Be honest about what the assumption asserts in our case: that Amazon's
site-selection team knew nothing in 2019 about 2022 demand that is not in our
ACS, CBP and Zillow columns. Stated plainly, that is not credible. Train's
defence is pragmatic, not epistemic, and it should be quoted as such.

### 5.8 Do not let coefficients vary by metro

SAYS (Sec. 12.7.3, "Fixed Coefficients for Some Variables"). "Ruud (1996)
argues that a mixed logit with all random coefficients is nearly unidentified
empirically, since only ratios of coefficients are economically meaningful.
He recommends holding at least one coefficient fixed, **particularly when the
data contain only one choice situation for each decision maker**."

SAYS (Sec. 11.4, a Monte Carlo on 300 simulated customers). "with one choice
situation the absolute deviation moves 10 percent of the way from no
conditioning to perfect knowledge (from .80 with T = 0 to .72 with T = 1)".
But the same experiment on the other metric "moves about 40 percent of the
way", and Train's own headline reading of Table 11.1 is the optimistic one:
"conditioning on one choice situation captures over 40 percent of the
variation".

SAYS (Sec. 11.7, "Discussion"). "these observable demographics of the
customers could be entered directly into the model itself, so that the
population parameters vary with the observed characteristics of the customers
in the population. In fact, entering demographics into the model is more
direct and more accessible to hypothesis testing".

WE. With 104 stations across 62 CBSAs we average **1.68 stations per metro**
— the `T=1` regime Ruud warns about almost exactly. Metro-varying
coefficients are not identified here. Put observed metro characteristics in
as regressors instead.

WE — and note the honest version. The "10 percent" is the pessimistic
reading of a Monte Carlo about *conditional distributions*, and the same
table supports "40 percent" on a different metric. Do not quote the 10%
figure as a general law; the load-bearing citation for this decision is
Ruud via Sec. 12.7.3, not the Monte Carlo.

### 5.9 Control function, not BLP

SAYS (Sec. 13.4, opening paragraph). "The BLP approach is not always
applicable. If observed shares for some products in some markets are zero,
then the BLP approach cannot be implemented, since the constants for these
product markets are not identified. (Any finite constant gives a strictly
positive predicted share, which exceeds the actual share of zero.)"

SAYS (Sec. 13.4, "Control Functions"). Two steps: regress the endogenous
variable on instruments, keep the residual, and enter a function of it as an
extra regressor — "the part of epsilon that is correlated with `y_nj` is
entered explicitly as an extra explanatory variable, such that the remaining
part is not correlated."

SAYS (Sec. 13.4.1). "the primary limitation of the control function approach
is the need to specify the control function and the conditional distribution
of the new unobserved term".

WE. Zero shares are not an edge case for us, they are the modal cell:
`enabled` is true on 2.58% of 1,081,312 ZCTA-quarters. BLP is unavailable.
The control function is the available route, and its limitation is real —
Train describes it as one of three procedures, not as a recommendation.

### 5.10 Bootstrap the standard errors

SAYS (Sec. 8.6, "Variance of the Estimates"). "The advantage of the bootstrap
is that it is conceptually straightforward and does not rely on formulas that
hold asymptotically but **might not be particularly accurate for a given
sample size**. Its disadvantage is that it is computer-intensive since it
entails estimating the model numerous times."

WE. At 39 events, asymptotic formulas are the thing we can least afford to
trust, and the computational objection costs us seconds. Note the honest
framing: Train presents a balanced pair, not a recommendation.

> **BUILT 2026-09-14, and both halves of the pair are reported.**
> `models/choice_inference.py` and `models/choice_sandwich.py`. Sandwich
> (Sec. 8.6 p. 201), bootstrap over 56 decisions at 1,000 replicates,
> clustered bootstrap over 38 metros at 1,500, BCa where estimable, and a
> convergence trace. The resampling unit is the DECISION, never an
> alternative — resampling alternatives would split a metro's ZCTAs across
> replicates and destroy the choice sets the likelihood is conditioned on,
> which is Sec. 5.1's error in a different costume.
>
> Two refusals, and both are the right call. The sandwich is **not** reported
> for `land_area_sqmi` or `establishments`: `beta = exp(theta)`, so
> `beta = 0` is `theta -> -inf`, the optimum is not interior, and the Hessian
> block is not the information matrix the Sec. 8.6 asymptotics assume. And
> those two get **one-sided** intervals, because 79-81% of replicates sit on
> the boundary and a two-sided interval would be a fiction.
>
> Train's p. 202 precondition — the bootstrap works *"if this sample is large
> enough"* — travels inside the artefact, in `inference.train_precondition`,
> rather than in a caption. At 56 decisions that clause is exactly what is in
> doubt, and saying so in the emitted JSON is the strongest form of the
> disclosure this section asks for.
>
> The result: the null is `beta = 1`, not zero, because households is the
> numeraire and only ratios are identified. Under the clustered bootstrap
> **no coefficient is distinguishable from the numeraire** in the direction
> that would matter — `warehousing_establishments` is [0.702, 10.013].

### 5.11 Bayes is the channel for the Daganzo prior

SAYS (Sec. 12.5.1, "Result A: Unknown Mean, Known Variance"). The posterior
mean is

```
      b1 = [ (1/s0) b0  +  (N/sigma) b-bar ] / [ (1/s0) + (N/sigma) ]
```

— "a weighted average of the sample mean and the prior mean", with "The
weight on the sample mean rises as sample size rises, so that for large
enough N, the prior mean becomes irrelevant."

SAYS (Sec. 12.7.1). "The researcher might want to apply a Bayesian
perspective in this case ... The posterior distribution contains the relevant
information for Bayesian analysis with any sample size, whereas the classical
perspective requires the researcher to rely on asymptotic formulas for the
sampling distribution that need not be meaningful with small samples."

WE. The weights `1/s0` and `N/sigma` *are* prior precision and sample
precision, so "precision-weighted" is mathematically right — but Train never
writes the word, so do not quote it as his.

WE. This is the mechanism by which the Daganzo cost model (`cost/daganzo.py`,
2,333 ZCTAs, median $1.09/parcel) could stop sitting *beside* the siting
model and start informing it. A cost-to-serve estimate derived from routing
geometry is exactly the kind of thing a prior is for, and the posterior
arithmetic above says a 39-event likelihood will not overwhelm it — which is
both the attraction and the danger.

OPEN. Not proposed, not implemented. The obvious objection is that a prior
strong enough to matter at N=39 is a prior strong enough to produce the
answer on its own.

### 5.12 What Train does not cover

Verified by grep across all fourteen chapters, the index and the references:

```
  "moment inequalit"      0 hits
  "partial identif"       0 hits
  "set identif"           0 hits
  "coarsen"               0 hits
  "hazard"                0 hits
  "censor"                1 hit -- and it is exploded logit dropping
                          higher-ranked alternatives, not censoring
  Manski                  cited only on choice-based sampling and
                          simulated frequencies, never on bounds
  Pakes                   cited on BLP and on non-smooth objectives,
                          never on moment inequalities
```

Chapter 14 is **"EM Algorithms"** (14.1 Introduction, 14.2 General Procedure,
14.3 Examples, 14.4 Case Study: Demand for Hydrogen Cars). It is about
flexible mixing distributions. Its only missing-data content is the
historical note that Dempster, Laird and Rubin introduced EM that way.

WE. So Train governs the choice-model half of this project and is silent on
the half that our data actually forces. For interval outcomes and set
identification we are out of the textbook and into Sec. 6.

---

## 6. Partial identification beyond Holmes

### 6.1 Molinari (2019), and the section we should have gone to first

We went to Molinari for Sec. 3.5, the Holmes/Pakes family. The result that
matters for us is in Sec. 2.3.

SAYS (Sec. 3.5). On the revealed-preference family: Pakes and PPHI "propose
to use a **subset** of the model's implications to obtain easy-to-compute
moment inequalities", and "A shortcoming of the method is that the set of
parameter vectors satisfying the moment inequalities may be **wider than the
sharp identification region**". On selection: entrants are a selected group,
so "The authors require the availability of valid (monotone) instrumental
variables to solve this problem."

SAYS (Sec. 2.3, Interval Data). Identification Problem 2.2 is: observe
`(y_L, y_U, x)` with `P(y_L <= y <= y_U) = 1` and `y` unobserved. Theorem
SIR-2.3 gives the **sharp** identified set for the whole conditional
distribution. Theorem SIR-2.5 gives the sharp set for the best linear
predictor under an interval outcome — and that set is **convex**,
representable by its support function, which "allows for a simple sample
analog estimator" and "immediately yields sharp bounds on linear combinations
of theta". Theorem SIR-2.4 (Manski-Tamer 2002) handles interval *covariates*
under a monotonicity assumption, with the author's own caveat that it "may
fail if censoring is endogenous".

SAYS (Sec. 2.3, repeatedly). The naive pointwise CDF band is **only an outer
region**, not the sharp set. Sharpness requires the condition to hold for
every interval, not every point.

SAYS (Sec. 2.1). "identification problems are fundamentally distinct from
finite sample inference problems. The latter are typically reduced as sample
size increase ... The former do not improve, unless a different and better
type of data is collected."

SAYS (Sec. 5, on misspecification). Ponomareva and Tamer: "misspecification
can cause the identified set to be spuriously tight ... **caution should be
taken when interpreting very tight partial identification results as
indicative of a highly informative model**." Bugni, Canay and Guggenberger:
under local misspecification confidence sets "fail" to hold their coverage
and "might be spuriously small". Her closing: robustness to misspecification
"remains an open and important question".

SAYS (Sec. 7). "Sharpness often requires many moment inequalities, the number
of which can exceed the available sample size."

SAYS (Sec. 6). Software for the Sec. 2 bounds exists (including a
Beresteanu-Molinari-Morris implementation for the interval-outcome best
linear predictor); for structural partially identified models there is "a
**paucity** of portable software", the only general-purpose one being the
Kaido-Molinari-Stoye MATLAB package.

SAYS (Sec. 2.4). Measurement error gets one page and defers to Schennach.
**Record linkage error is not covered at all** — zero hits for "record link",
"linkage", "matching error". The nearest hook is Molinari (2008) on
misclassified outcomes.

### 6.2 Kaido, Molinari & Stoye (2019)

SAYS (abstract). "We propose a bootstrap-based calibrated projection
procedure to build confidence intervals for **single components** and for
smooth functions of a partially identified parameter vector in moment
(in)equality models."

The problem it solves: a confidence set for the whole vector, projected onto
one coordinate, is valid but badly conservative, and the conservatism grows
with dimension. Their arithmetic: in a point-identified linear regression the
usual 95% interval is `+/- 1.96`; projecting a 95% ellipsoid with `d = 10`
gives `+/- 4.28` and "a true coverage of essentially 1". Software is a MATLAB
package at `github.com/MatthewThirkettle/calibrated-projection-MATLAB`.

SAYS. Two points that bear directly on route (A). First, on PPHI — the
estimator Holmes uses — they write that PPHI "directly bootstrapped the
sample projection. **This is valid only under stringent conditions**", and
the Supplement gives a counterexample that "satisfies all assumptions
explicitly stated in Pakes, Porter, Ho, and Ishii (2011), illustrating an
**oversight in their Theorem 2**". Second, their own method has a documented
failure case (near-perfectly-correlated binding constraints) where calibrated
projection, BCS profiling and PPHI all bound true coverage at about 63%, and
subsampling fails the same way — while the *conservative* Andrews-Soares
projection survives.

Assumptions worth knowing before adopting it: `{X_i}` are **i.i.d.** (E.1);
analytic gradients of every studentised moment are required, Lipschitz and
uniformly bounded (E.4 — a condition they violated in their own application
and patched by truncating a correlation parameter at 0.85); and the
confidence set must have non-empty interior (A.3).

Scale: their two empirical exercises are `n = 4000, d = 5, J = 16` and
`n = 7882, d = 9, J = 48`. There is no small-`n` simulation anywhere in the
paper and no discussion of `J` relative to `n`.

WE. At `n = 43` this is not a computational problem — the inner linear
programmes are `J + 2d - 2` rows in `d - 1` variables, independent of `n`, so
it would run in seconds. It is a statistical one. The linearisation is
trusted inside a box of radius `rho/sqrt(n)`; with `rho` around 5 to 7 and
`sqrt(43) = 6.6` that radius is about 1.0 in parameter units, where at
`n = 4000` it is about 0.08. A "local" expansion of width 1.0 is not local.
And a panel of buildings is not i.i.d. draws; no theorem in the paper covers
a cluster bootstrap.

---

## 7. Winkler — record linkage, and the error rate we cannot compute

This section is here because the identity of a facility in our panel is the
output of a fuzzy match, and an error there is upstream of every number in
the repository. The implementation lives in
`src/siting_atlas/common/linkage.py` and `common/address.py` and is being
worked on separately; this section is the reading behind it, not a
description of it.

SAYS (Sec. 2). Fellegi-Sunter classifies pairs in `A x B` into `M` (true
matches) and `U` (true non-matches) by the ratio `R = P(gamma|M) /
P(gamma|U)`, where `gamma` is an agreement pattern — his own worked example
is "simple agreement or not on the largest name component, street name, and
street number", which is precisely our setting. `P(gamma|M)` and `P(gamma|U)`
are the **m- and u-probabilities**. The decision rule has two thresholds:

> "If R > UPPER, then designate pair as a match.
>  If LOWER <= R <= UPPER, then designate pair as a **possible match and
>  hold for clerical review**.
>  If R < LOWER, then designate pair as a nonmatch."

and "The cutoff thresholds UPPER and LOWER are determined by a priori error
bounds on false matches and false nonmatches."

SAYS (Sec. 2). Under conditional independence the parameters follow "from a
straightforward application of the EM algorithm (Winkler 1988)", and the
attraction is that "the known truth of matches on subsets is not needed".
The caveat is stated in the same paragraph: "**Caution in the automatic use
of the EM-probabilities is needed because the EM may not exactly divide the
set of pairs into two classes that correspond exactly to matches and
nonmatches.**"

SAYS (Sec. 2.1). Jaro's comparator "accounts for insertions, deletions, and
transpositions"; Budzinsky's review of twenty comparators "concluded that the
methods of Jaro and Winkler worked second best and best, respectively". The
motivating number, from a census undercount application: "**more than 25% of
matches would not have been found via exact character-by-character
matching**", and in St Louis "25% of first names and 15% of last names did
not agree character-by-character among pairs that are matches". Table 1 shows
that accepting a comparator value of 0.6 or better recovers roughly 18 points
of first-name and 10 points of last-name agreement over exact equality.

SAYS (Sec. 2.3, and Sec. 3.1). The paper singles out our case as the hard
one, twice. "Inconsistencies of name and address information are typically
even greater with agriculture and business lists ... If standardization fails
for a record, then automatic matching in software may be impossible." And,
against a technique we might have reached for: "**with many business lists,
agriculture lists, and general administrative lists ... frequency-based
matching may not yield improvements because of the large amounts of
typographical variation**."

SAYS (Sec. 3.4). The paper's central open problem, and the one that decides
what we can claim: "**The method of Belin and Rubin (1995) is currently the
only method for automatically estimating record linkage error rates.**" It
works "in a narrow range of situations ... where there was good separation
between the matching weights associated with nonmatches and matches" — and
Sec. 2 has already said that separation is exactly what business and
administrative lists lack. His fourth research question is, verbatim, "How
does one automatically estimate error rates?"

**Two things Winkler is often credited with and this paper does not contain.**
First, **blocking**: the word does not appear once in the paper. For Winkler
on blocking you need Winkler (1995) in *Business Survey Methods*. Second, the
familiar Fellegi-Sunter optimality theorem ("minimises the clerical-review
region for fixed error rates") is **not stated**; the symbols `mu` and
`lambda` never appear. What the paper asserts is the bounded-error half only.

WE. So we cannot publish a linkage error rate for the panel from theory. What
we *can* do is exploit the one advantage of a tiny panel: at 43 buildings the
clerical-review band is small enough to resolve by hand, which both fixes the
matches and manufactures the labelled subset that Belin-Rubin needs. That is
an inference, not Winkler's recommendation.

---

## 8. The open methodological question

Two routes are on the table. **No winner is declared here.** That decision is
the user's and has not been made.

| | (A) Moment inequalities | (B) Closed-form dynamic logit |
|---|---|---|
| Source | Holmes Sec. 6-8; Houde et al. Sec. 4.3 | Train Sec. 7.7.3 |
| What is identified | A **set** | A **point** |
| Assumption on the firm's information | None distributional | The firm's ex-ante unknowns are our unobservables and are iid extreme value |
| Software | None portable for structural models (Molinari Sec. 6); KMS MATLAB is the exception | Anything that fits a nested logit |
| Cost | High; unfamiliar; analytic gradients required for KMS inference | Low; one extra regressor |
| Interpretability | Bounds on cost parameters | Coefficients, marginal effects |
| Handles our upper-bound dates | Can carry the bound honestly | Must assume the OSHA date is the opening date, or bolt on a censoring model |
| Its worst problem here | Holmes assumes the **dates** are measured without error and says `x`-error makes him inconsistent (Sec. 2.4 above); the sharp set may need more inequalities than we have observations (Molinari Sec. 7) | Train's own caveat: "It is doubtful that the researcher, in reality, observes everything that the decision maker knows beforehand" |
| Failure mode you would not notice | A **tight** set from a misspecified model (Molinari Sec. 5) | A precise coefficient from a false information assumption |

OPEN. There is a third route neither of us named at the outset, and on the
reading it is the closest fit to the data we actually have: **Molinari Sec.
2.3, interval-outcome partial identification.** See Sec. 11.

---

## 9. The MWPVL decision

The decision: **do not buy MWPVL.** The reasoning, recorded so it can be
overturned by someone who disagrees with the reasoning rather than by someone
who has forgotten it.

**For buying it.** It would supply real opening dates and dissolve the worst
problem in the project. Houde et al. Sec. 2.2 confirms MWPVL carries
"location, size in square feet of floor space, employment, facility type,
opening date, and closing date" — which is, item for item, the panel we spent
a day failing to build for free.

**Against.** Two reasons, and the second is the one that settles it.

1. The project's central claim is that a city, an air district or a community
   group can do this with free public data. A licensed input does not just
   weaken that claim; it inverts it. Checkability is the product.
2. **Houde et al. already published the paid-data version.** Buying MWPVL
   moves us from "the free-data version of a question nobody has asked about
   delivery stations" to "a smaller, later, worse-resourced version of an
   Econometrica paper". The purchase would buy better data and destroy the
   contribution.

**The proposed alternative, not yet actioned.** Request a small academic
slice for **validation only** — enough facilities to measure how often the
OSHA bound is right and how loose it is — and publish the measured error rate
for the free pipeline. That converts a competitor's proprietary asset into a
yardstick for ours, and it is the one use of paid data that strengthens
rather than undermines the claim. Today the entire calibration rests on
**five** addresses from MWPVL's 2012 public table, all of them fulfilment
centres from 2008-2011, with lags of 4, 13, 57, 69 and 345 months. Five is
not a measurement.

---

## 10. Corrections log

Every claim that went into the first draft of this file and did not survive
the source. Roughly one in three. The list is here because a research log
that only records the claims that worked is a marketing document.

| Claim as first written | What the source actually says |
|---|---|
| Houde et al. **Sec. 3.5** applies the Holmes estimator | Sec. 3.5 is "Optimization Problem" and states the firm's problem. The estimator is **Sec. 4.3, "Shipping and Fixed Costs"** |
| Train **Sec. 2.2/2.3**: the choice set is defined relative to the researcher's representation | All three choice-set properties are in **Sec. 2.2 alone**. The "relative to a researcher's representation" sentence is in **Sec. 2.3** and is about the **error term**, not the choice set. Train also anchors the choice set in the decision maker: mutual exclusivity is required "from the decision maker's perspective" |
| Train **Sec. 7.7.2**: define as few time periods as possible | Content exact, **section wrong**. It is in **Sec. 7.7.3**, "Uncertainty about Future Effects". Sec. 7.7.2 is "Multiple Periods" and contains no such advice |
| Train **Sec. 11.3/11.4**: one observation per agent buys ~10% of the way to knowing that agent's coefficients | The 10% is in **Sec. 11.4** (a Monte Carlo), not 11.3, and it is the pessimistic of two metrics — the same table gives **40%** on the other, which is Train's own headline reading. Sec. 11.3 is "Implications of Estimation of theta" and is not a warning section. The real T=1 warning is **Sec. 12.7.3**, and it is Ruud's, and the remedy is "hold at least one coefficient fixed", not "do not let coefficients vary" |
| Train **Sec. 3.7.1** requires sampling from a **known universe** | Never stated. The machinery presupposes an enumerable full set `F`, but Train never says "known universe" and **never contrasts it with an unknown choice set**. Do not attribute that contrast to him. Also, 3.7.1 is titled "Exogenous Sample"; the material sits under an unnumbered sub-heading |
| Train **Sec. 13.4** *recommends* a control function; Train **Sec. 8.6** *recommends* the bootstrap | Both are presented with balanced pros and cons, not recommended. The 8.6 quote is verbatim; the section is titled "Variance of the Estimates" and is mostly about analytic formulas |
| BLP fails when **many** alternatives have zero share | Train's condition is "if observed shares for **some** products in **some** markets are zero". No threshold, no count, and nothing about the number of alternatives. The passage is in **Sec. 13.4**, as motivation for control functions, not in Sec. 13.2 where BLP is set out |
| Train **Sec. 2.2**, mutual exclusivity, is the assumption the hazard model broke (Sec. 5.1 above, and five other documents) | It is not, and this is the largest citation error in the project. Sec. 2.2 governs a choice set facing a **decision maker**; a cloglog hazard on ZCTA-quarters has none, so exclusivity is not a property it can violate. Train also calls the criterion "not restrictive" (p. 12) and supplies a two-line repair recipe — not the shape of a fatal test. The assumption actually violated is **Sec. 3.7.1, printed p. 61**, independence across observations, which is what the likelihood is built on. Corrected 2026-09-14 across every status and reference document then in the repository, and Sec. 5.1 above. **Sec. 2.2 is the authority for BUILDING the successor choice set** |
| The posterior mean is a **precision-weighted** average | The mathematics is right and Sec. 12.5.1 gives the formula, but Train writes only "weighted average". The word "precision" appears **nowhere** in chapters 1-14 or the index |
| AUC "inherits the defect" of percent-correctly-predicted | It does not inherit *that* defect — Train's Sec. 3.8.1 objection is to hard assignment, and AUC never thresholds. The defensible objection is different: AUC is invariant to monotone transforms and therefore cannot see miscalibration. Same conclusion, different argument |
| Train Sec. 7.5 is the "referendum" format | Train's word is **single-bounded**. "Referendum" appears nowhere in Sec. 7.5 |
| Holmes: the identified set **is** the argmin of Q | The population identified set is the constraint set; the argmin is the equivalent characterisation and the **sample** analogue. Holmes also offers an absolute-value version solvable by linear programming |
| Our panel has **~80 quarters** | **32.** 2018Q1 to 2025Q4. `dim_date` = 32, and 1,081,312 panel rows = 33,791 ZCTAs x 32 |
| One station switches **~90 ZIPs** at once | ~90 is the **mean** (87.6). The median is **58**, the range 4 to 307. The argument survives; the number should be stated as a distribution |
| Holmes subsamples per textbook Politis-Romano-Wolf | He says "subsampling **with replacement**", and uses `b = N/3`. Worth flagging if anyone reimplements it |
| Winkler covers blocking | The word "block" appears **zero** times in the paper. Nor does the familiar Fellegi-Sunter optimality theorem: `mu` and `lambda` never appear |
| Winkler reports Census error rates | The paper contains three numbers in total (the 25%/15% non-agreement figures, Table 1, and a 0.1-0.2% error from forced 1-1 matching). No PES or Decennial false-match rate appears |
| "MWPVL, International" appears in no repo doc | True for that exact string; **MWPVL** appears in eleven documents. The bibliographic form was missing, not the source |
| The **Brier skill score** is the proper scoring rule we switched to | It is not. Gneiting & Raftery **Sec. 2.3, p.362**: "skill scores of the form (8) are generally improper, even if the underlying scoring rule `S` is proper", with Murphy (1973) giving only *asymptotic* propriety and Mason (2004)'s propriety claim named as "generally incorrect". The **Brier score** is strictly proper (Example 1, p.363); the skill score is a normalisation of it. Report the raw pair. See Sec. 12.4 |
| Gneiting & Raftery is the citation against AUC | **They never mention AUC or ROC.** Zero occurrences in twenty pages; the only gesture is one citation of Pepe (2003) in the future-work section (Sec. 10, p.376). The defensible argument is that AUC is a rank statistic over *pairs* and so is not a scoring rule in their sense at all, which makes propriety undefined for it rather than violated. See Sec. 12.6 |
| Gneiting & Raftery give the reliability-resolution-uncertainty decomposition of the Brier score | They do not. They give the Savage/Bregman decomposition, eq. (7), p.361. Murphy's vector-partition paper is not even in their reference list — their Murphy (1973) is "Hedging and Skill Scores for Probability Forecasts". See Sec. 12.2 |
| AUC "never thresholds" (Sec. 5.4, first correction) | AUC is the integral of the ROC curve **over** all thresholds. It never commits to *one* threshold, which is a different and weaker statement. Also, Train's objection has a second limb we omitted — "gives obviously inaccurate market shares" — and AUC *does* inherit that one |

---

## 11. The thing we should have noticed first

We read Molinari's survey to find out whether the Holmes/Houde estimator was
respectable (Sec. 3.5: it is, with caveats). The section that describes **our
data** is Sec. 2.3, and we walked past it.

Our outcome is not a mismeasured date. It is a date **known to lie in an
interval** — `(panel start, OSHA inspection date]` — which is Molinari's
Identification Problem 2.2 exactly: observe `(y_L, y_U, x)`, know
`P(y_L <= y <= y_U) = 1`, and never observe `y`. That literature gives, for
that structure and no other assumption:

- a **sharp** identified set for the outcome distribution (Theorem SIR-2.3),
  together with the warning that the obvious pointwise CDF band is only an
  outer region;
- a sharp identified set for the **best linear predictor** under an interval
  outcome that is **convex**, has a support function, admits "a simple sample
  analog estimator", and "immediately yields sharp bounds on linear
  combinations" (Theorem SIR-2.5);
- shipping software for that case (Beresteanu-Molinari-Morris), in a survey
  that otherwise complains of "a paucity of portable software".

WE. This is a third route, and it is strictly better matched to the data than
either (A) or (B). It requires **no** model of Amazon's optimisation, no
assumption about what Amazon knew in 2019, and no swap construction — which
means it does not need the one thing Holmes assumes and we cannot supply,
namely dates measured without error (Sec. 2.4). It turns the panel's worst
defect into the estimator's input. It also answers a narrower question than
(A) or (B) do, and it will produce a set rather than a forecast.

WE. And it comes with its own warning from the same survey, which should be
attached to it permanently: Ponomareva and Tamer, that misspecification makes
these sets **spuriously tight**, so "caution should be taken when
interpreting very tight partial identification results as indicative of a
highly informative model". A narrow interval from 43 buildings would be a
reason for suspicion, not celebration.

OPEN. Route (C) is offered, not chosen. It has not been costed and no one has
checked whether the Beresteanu-Molinari-Morris code runs on a panel this
shape.

---

## 12. Gneiting & Raftery (2007) — the defence of the metric

Source: `Research/Gneiting2007jasa.pdf`, *JASA* 102(477) 359-378. Read cover to
cover; the section-by-section notes, the verbatim definitions and the list of
what I did not verify are in
[`research/NOTES_gneiting_raftery_2007.md`](research/NOTES_gneiting_raftery_2007.md).
Page numbers here are journal pages from that copy (journal page = PDF page +
358). **Not** from `Research/27639845.pdf`, the JSTOR scan, whose cover page
shifts everything by one.

This section exists to answer one accusation: *you changed your headline metric
after your model failed.* The sequence is not in dispute — see Sec. 12.5. What
is in dispute is whether the new metric is the principled one. The grounds
below are all from a 2007 review article, and none of them depend on our result.

### 12.1 What a scoring rule is, and what propriety buys

SAYS (Sec. 2.1, p.360). A scoring rule is a function `S: P x Omega -> R̄`: the
forecaster quotes a distribution `P`, the event `omega` happens, the reward is
`S(P, omega)`. Write `S(P, Q)` for the expectation of `S(P, .)` under `Q`. Then

```
    S is PROPER            if  S(Q, Q) >= S(P, Q)  for all P, Q in P.     (1)
    S is STRICTLY PROPER   if  (1) holds with equality iff P = Q.
```

SAYS (Sec. 1, pp.359-360). What that buys, in the authors' words: "The
forecaster has no incentive to predict any `P != Q` and is encouraged to quote
his or her true belief." A strictly proper rule is maximised, *uniquely*, by
quoting what you actually believe.

SAYS (Sec. 2.1, p.361, Theorem 1). Propriety is not a matter of taste. A
regular scoring rule is proper **if and only if** its expected-score function
`G(P) = S(P, P)` is convex and `S(P, omega)` is a subtangent of `G` at `P`.
Proper scoring rules are in bijection with convex functions. Strict propriety
corresponds exactly to strict convexity.

WE. This is the property a headline metric has to have, and the reason is
nothing to do with model quality. A metric that is not proper can be improved
by misreporting. If the number you publish can be raised by quoting something
other than your best estimate, the number is not measuring your model.

### 12.2 Where the Brier score sits

SAYS (Sec. 3.1, Example 1, p.363). The Brier score is the quadratic score
generated by the convex function `G(p) = sum_j p_j^2 - 1`. For a binary event,
in the paper's positive orientation, `S(p, 1) = -(1-p)^2` and `S(p, 0) = -p^2`
(Table 1, p.365) — our mean squared error with the sign flipped. It is
**strictly proper**. Its associated Bregman divergence is the squared Euclidean
distance.

SAYS (Sec. 3.2, Theorem 3 and Table 1, pp.364-365). Every binary scoring rule
is a mixture of threshold-at-`c` decision rules, weighted by a measure `nu(dc)`
over cost-loss ratios `c` — "the relative costs of the two possible types of
inferior decision". The Brier score's `nu` is **uniform on (0,1)**: it weights
every cost-loss ratio equally. And "the scoring rule is strictly proper if and
only if `nu` assigns positive measure to every open interval".

SAYS — **no calibration/refinement decomposition appears in this paper.** If
you want Murphy's reliability-resolution-uncertainty partition of the Brier
score, this is not the citation, and the paper it comes from is not even in the
reference list (their Murphy 1973 is "Hedging and Skill Scores", not "A New
Vector Partition of the Probability Score"). What this paper gives instead is
the Savage/Bregman decomposition: divergence `d(P,Q) = S(Q,Q) - S(P,Q)`, eq.
(7), p.361, which for the Brier score is `sum_j (p_j - q_j)^2`. Do not cite
Gneiting & Raftery for the reliability-resolution split.

### 12.3 Calibration and sharpness: they endorse the paradigm

SAYS (Sec. 1, p.359), verbatim:

> "In earlier work ... we contended that the goal of probabilistic forecasting
> is to maximize the sharpness of the predictive distributions subject to
> calibration. Calibration refers to the statistical consistency between the
> distributional forecasts and the observations, and is a joint property of the
> forecasts and the events or values that materialize. Sharpness refers to the
> concentration of the predictive distributions and is a property of the
> forecasts only."

Two qualifications, in fairness. They present this as their own prior
contention carried forward from Gneiting, Raftery, Balabdaoui & Westveld (2003)
and Gneiting, Balabdaoui & Raftery (2006), not as something established here.
And the paradigm is about the *goal of forecasting*; the paper's own
recommendation for *evaluation* is a single strictly proper score, on the
grounds that a proper score already "assesses both calibration and sharpness"
— said of the interval score at Sec. 8.3, p.374.

WE. Reporting a proper score **and** a calibration diagnostic is therefore
belt-and-braces rather than doctrine. It is defensible: the score gives the
propriety guarantee, the diagnostic locates the failure. But the honest framing
is that the paper's headline recommendation is the score, and the calibration
table is ours.

SAYS (Sec. 2.3, p.362) — and this one lands on us. The reference in a skill
score "is typically a climatological forecast, that is, an estimate of the
marginal distribution of the predictand", and "Climatological forecasts are
independent of the forecast horizon; **they are calibrated by construction, but
often lack sharpness**."

WE. Our null is a constant 0.02006 — precisely a climatological forecast. Its
ECE of 0.00005 is therefore *predicted by the paper*, not a surprise, and we
should stop presenting it as one. The real indictment is sharper than the one
we have been making: the covariate model's entire job was to buy sharpness
**subject to** calibration. It bought 0.5% of Brier skill and lost the
calibration constraint. It failed the constraint and barely moved the
objective.

### 12.4 The concession: the Brier SKILL score is not proper

This has to be volunteered, because it is on page 362 of the paper we are
citing in our own defence.

SAYS (Sec. 2.3, p.362), verbatim:

> "Unfortunately, skill scores of the form (8) are generally improper, even if
> the underlying scoring rule `S` is proper. Murphy (1973) studied hedging
> strategies in the case of the Brier skill score for probability forecasts of
> a dichotomous event. He showed that the Brier skill score is asymptotically
> proper, in the sense that the benefits of hedging become negligible as the
> number of independent forecasts grows. ... Mason's (2004) claim of the
> propriety of the Brier skill score rests on unjustified approximations and
> generally is incorrect."

SAYS (Sec. 10, p.376). They soften it in future work — "Briggs and Ruppert
(2005) have argued that skill score departures from propriety do little harm.
Although we tend to agree, there is a need for follow-up studies" — but a hedge
in a future-work section is not an endorsement.

WE. So "we switched to Brier skill because it is the proper scoring rule" is
**false as stated**. The correct statement has three parts.

1. The **Brier score** is the strictly proper object, and it is what we report:
   `0.019522` for the model against `0.019614` for the null, on the same 8,044
   rows. Sec. 2.3, p.362 requires exactly that — "Scores for competing forecast
   procedures are directly comparable if they refer to exactly the same set of
   forecast situations" — and we satisfy it.
2. The **skill score** `+0.00471` is a presentational normalisation of that
   pair, reported because a raw Brier of 0.0195 at a 2% base rate is unreadable.
   It is not itself a proper scoring rule and should not be described as one.
3. Murphy's hedging benefit vanishes as `n` grows and `n = 8,044`, so the
   impropriety is not operative here. That is a mitigation, not a defence.

Consequence for the repo: wherever "Brier skill" is the headline, the raw
Brier pair should sit beside it wherever the hazard result is quoted.

### 12.5 The accusation, and how much of it lands

The sequence really was: fit the model, see AUC 0.6894, then change the
headline. Nothing below denies that.

What the paper establishes is that the destination was already the right one in
2007. Four grounds, none of which mentions our result:

**(a) Propriety is a property of the metric, checkable before you see data.**
Eq. (1), Sec. 2.1, p.360. Whether a rule is proper is a fact about the rule.

**(b) The paper contains a worked demonstration that an improper metric picks
the wrong model.** Sec. 8, pp.373-374. 16,015 real sea-level-pressure forecasts
from a five-member ensemble known to be underdispersive by a factor of about
1.55. Six scores were asked which inflation factor `r` was best:

```
  Score                     argmax r      proper?
  ------------------------------------------------
  Quadratic (Brier)           2.18          yes
  Spherical                   1.84          yes
  Logarithmic                 2.41          yes
  CRPS                        1.62          yes
  ------------------------------------------------
  Linear score                 .05          NO
  Probability score            .02          NO
                                     (Table 3, p.373)
```

Verbatim, Sec. 8.2, p.374: "The latter two scores have intuitive appeal, and
the probability score has been used to assess forecast ensembles (Wilson et al.
1999). However, they are improper, and their use may result in misguided
scientific inferences, as in this experiment." The improper scores concluded
the forecast was essentially deterministic. The authors state the case study's
purpose as "to demonstrate the importance of propriety" (Sec. 8, p.373).

**(c) A second worked example: a metric can be gamed into pretending to be
certain.** Sec. 4.4, p.368, on the predictive model choice criterion of Laud &
Ibrahim (1995): it "is improper; if the forecaster's true belief is `P` and if
he or she wishes to maximize the expected score, then he or she will quote the
point measure at `mu_P` — that is, a deterministic forecast — rather than the
predictive distribution `P`."

**(d) A third: coverage and width, checked separately, can both be satisfied by
a bad forecast.** Sec. 6.3, Table 2, p.371. Three 95% interval forecasts of a
bilinear process, 100,000 sequential forecasts. All three hit nominal coverage
(95.01%, 95.08%, 94.98%). The *narrowest* of the three, `K` at width 3.79,
loses on the score to the true conditional interval `I` at width 4.00, because
`K` "collapses to a point forecast when the conditional predictive variance is
highest". Diagnostics examined one at a time can be passed by a model the
proper score rejects.

WE. So the general rule — *report a strictly proper score, because an improper
or partial metric can prefer the wrong model* — was published in JASA in March
2007, demonstrated three times on data that has nothing to do with warehouses.
Choosing it in 2026 is applying a known rule late, which is a criticism of the
project's sequencing and not of the metric.

WE — **what the accusation gets right, and should be conceded.** Three things.

1. We should have registered a proper score at design time and did not. That is
   a real failure of planning. The relevant literature is nineteen years old and
   the project did not consult it until after the model had been fitted.
2. The specific new headline, Brier *skill*, is not the proper object — see
   Sec. 12.4. The proper object is the Brier score, and we now report both.
3. The claim "AUC could not see the calibration failure" is true and is
   demonstrated by our own numbers, but it is **our** argument, not one we can
   attribute to this paper. See Sec. 12.6.

### 12.6 AUC: what the paper does and does not say

SAYS — **nothing.** The strings `AUC`, `ROC`, `receiver`, `area under`,
`discrimination`, `reliability` and `resolution` occur **zero** times in the
body of the twenty-page paper. The only hits anywhere in the file are two
reference titles in the bibliography (Friedman 1989, "Regularized Discriminant
Analysis"; a dissertation on a "High-Resolution Model"). Nor do `rare` or
`base rate` occur at all.

SAYS (Sec. 10, p.376). The single gesture at that literature is one clause:
formal tests of forecast performance "[are] a promising avenue for future work,
particularly in concert with biomedical applications (Pepe 2003; Schumacher,
Graf, and Gerds 2003)". Pepe (2003) is the standard ROC monograph. It is cited
once, as future work, and never engaged with.

WE. Therefore: **do not cite Gneiting & Raftery against AUC.** The defensible
argument is structural, and it is stronger for being modest.

```
  A scoring rule is  S(P, x)  -- one forecast, one observation.   Sec. 2.1 p.360
  Scores aggregate as  S_n = (1/n) sum_i S(P_i, x_i).             Sec. 2.3 p.362
  Propriety, eq. (1), is a property of S at that per-case level.  Sec. 2.1 p.360

  AUC is a rank statistic over PAIRS of cases: the probability that a
  randomly drawn event outranks a randomly drawn non-event. It cannot be
  written as an average of per-case scores.

  => Equation (1) cannot be evaluated for AUC. Propriety is UNDEFINED for
     it, not violated by it.
```

That is the honest position, and it is sufficient. What we want from a headline
metric is the guarantee in eq. (1). AUC is not the kind of object that can
carry that guarantee. Separately, and on our own authority, AUC is invariant to
every strictly increasing transform of the predictions and therefore cannot
distinguish our model from one whose probabilities are ten times too large —
which is what our own numbers show, AUC 0.6894 alongside an ECE 170 times the
null's. That second sentence is ours. Tag it WE and never SAYS.

### 12.7 Rare events, at a 2% base rate

SAYS — the paper has no section on rare events and the phrase does not occur.
Four passages bear on it, and one of them is genuinely useful.

SAYS (Sec. 3.2, Example 6, eq. 17, p.365). **Winkler's standardised score.** The
Brier score recentred on a baseline probability, "with the value of `c` in
`(0,1)` adapted to reflect a baseline probability", and offered explicitly "as
an alternative to using skill scores". It is proper. Tetlock (2005) used it to
adjust for forecast difficulty when scoring expert political predictions.

OPEN. At `c = 0.02` this is directly applicable to us, it is proper where the
skill score is not, and it is computable from `hazard_predictions.parquet`
without refitting anything. Nobody has implemented it. It is the cheapest
methodological improvement identified in this file.

SAYS (Sec. 8.2, p.374). "The logarithmic score is strictly proper but involves a
harsh penalty for low probability events and thus is highly sensitive to extreme
cases." Their preferred alternative in that setting is the CRPS, which does not
apply to a binary outcome; for us the relevant reading is that the bounded Brier
score is safer than log loss at a 2% base rate.

SAYS (Sec. 9.1, p.375). "Buja et al. (2005) argued that strictly proper scoring
rules are the natural loss functions or fitting criteria in binary class
probability estimation, and proposed tailoring scoring rules in situations in
which false positives and false negatives have different cost implications."
Binary class probability estimation is exactly our problem. G&R cite this and do
not develop it; Buja, Stuetzle & Shen (2005) is the paper to read next.

WE — **a weakness of our own choice, volunteered.** Table 1, p.365 says the
Brier score's mixing measure over cost-loss ratios is *uniform*. At a 2% base
rate the operationally relevant cost-loss ratios are nowhere near 0.5, and the
Brier score gives the band around 0.5 the same weight as the band around 0.02.
That is a real argument against the Brier score in our application, and the
paper supplies the fix (Example 5's beta family, or Example 6's Winkler score).
Better to say this than to have it said to us.

### 12.8 What changed in this project as a result

```
  CHANGED   Sec. 5.4 above now argues the percent-correctly-predicted point
            from Example 4 and Theorem 3 rather than from Train's prose
            alone, and states plainly that the upgrade does not reach AUC.

  CHANGED   The metric claim is now "the Brier score is the headline, the
            skill score is how we display it". The previous phrasing
            implied Brier skill was the proper object. It is not -- Sec.
            2.3, p.362.

  CHANGED   The defence pack gains a moving-the-goalposts answer, which
            concedes the sequencing failure and defends the destination.

  OPEN      Winkler's score (17) at c = 0.02. Proper, baseline-adjusted,
            cheap, not implemented.

  OPEN      Whether to report the calibration table at all, or only the
            proper score. The paper's own recommendation is the score
            (Sec. 8.3, p.374: a proper score "assesses both calibration and
            sharpness"). We report both because the diagnostic locates the
            failure that the score only registers. That is our choice, not
            theirs.

  UNCHANGED ECE is not a scoring rule and does not appear in this paper. It
            is a diagnostic for the calibration constraint of Sec. 1, and a
            good ECE defends nothing on its own -- the constant null scores
            0.00005 and is useless.
```

---

## 13. Where to go next

| Document | What it has that this one does not |
|---|---|
| [`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md) | how the panel was collected, the five methods that failed, and every known defect in the delivered file |
| [`STATUS.md`](STATUS.md) | the measured state of the project, including defect A (interval censoring not implemented), which Sec. 5.5 and Sec. 11 above both argue for |
| [`adr/0001-observable-estimand.md`](adr/0001-observable-estimand.md) | why the estimand is service enablement rather than order volume, and the 2026-09-13 update recording that "error rate" was the wrong frame |
| [`research/NOTES_gneiting_raftery_2007.md`](research/NOTES_gneiting_raftery_2007.md) | the full section-by-section reading of the scoring-rules paper behind Sec. 12, with every definition verbatim and an explicit list of what was not verified |
| `src/siting_atlas/common/linkage.py` | the Fellegi-Sunter implementation that Sec. 7 is the reading behind |

---

## 14. The unit-of-analysis diagnosis, in full

*Relocated here from `PLAN.md` when that file was retired, 2026-09-15. This
is the canonical statement of why the first model failed. It is a method
argument, not a status report, which is why it lives in this file and not in
[`STATUS.md`](STATUS.md).*

### 14.1 What failed, with numbers

The discrete-time hazard model, fitted on 43 delivery stations
(`hazard_report.json`, run `20260914-002509-2374`):

```
                         model      null (a constant)
Brier score            0.019522     0.019614   <-- the proper score, and
                                                   the thing to report
calibration error (ECE) 0.00863      0.00005   <-- WORSE than a constant
AUC                      0.6894       0.5000
temporal hold-out       -0.02091
```

Both Brier scores are over the same 8,044 rows. **Report the raw pair, not
the skill number** — Sec. 12 above, and Gneiting & Raftery Sec. 2.3 p.362:
skill scores "are generally improper, even if the underlying scoring rule S
is proper". The +0.00471 quoted elsewhere is `1 - 0.019522/0.019614` and is a
normalisation for readability, not the estimand.

The geographic hold-out (−0.06184) is deliberately not in that table.
`hazard_report.json:819` states that Phoenix and Boise hold two dated
stations between them, making it "a smoke test for gross failure and not a
test of geographic transfer", with an explicit instruction not to quote it as
one. Quoting it bare overstates the evidence against our own model.

Read the third row twice. A model that ignores every covariate and predicts
the same number for every ZIP code is **better calibrated** than ours. One of
three covariates was distinguishable from zero: `households`, hazard ratio
1.00005. Translated: *"Amazon builds where the people are."* True, and not
worth a model.

### 14.2 Why it failed

Not sample size. **Unit of analysis.**

One delivery station switches on a median of 39 ZCTAs at once at the 15-mile
catchment (`hazard_revival.json:provenance.catchment_load`; the figure was
reported as 58 on the pilot frame before the panel expanded). So the 812
ZCTA-level "events" in the pilot risk set came from **between 28 and 38 real
decisions plus a circle** — the bounds are in `hazard_report.json`'s own
`power` block. The model spent its capacity learning to draw circles.

**CITATION, and it has been wrong twice.** This diagnosis was originally
filed against Train Sec. 2.2, mutual exclusivity of the choice set. That
citation would not survive an examiner opening the book. Sec. 2.2 governs a
*choice set*, and a cloglog hazard on ZCTA-quarters has no decision maker
choosing among ZCTA-quarters, so exclusivity is not a property it can
violate. Train also calls the criterion weak (p. 12, verbatim):

> "The first and second criteria are not restrictive. Appropriate definition
> of alternatives can nearly always assure that the alternatives are mutually
> exclusive and the choice set is exhaustive."

He then gives a two-line repair recipe. A rule the author calls not
restrictive, and shows how to satisfy, cannot be the indictment. **Sec. 2.2
is the authority for building the SUCCESSOR choice set, not the charge
against the old model.**

The assumption actually violated is **Sec. 3.7.1, printed p. 61** — the one
the likelihood itself is built on (verbatim):

> "Assuming that each decision maker's choice is independent of that of other
> decision makers, the probability of each person in the sample choosing the
> alternative that he was observed actually to choose is L(beta) = ..."

Its common name is **pseudo-replication**. When one station switches on 39
ZCTAs at once, those 39 rows are one draw entered 39 times. The likelihood
multiplies them as if independent, so the model believes it has far more
information than it does and the standard errors are correspondingly too
small.

The diagnosis is unchanged and the fix is unchanged. Only the citation moves,
from a weak criterion the author dismisses to the assumption the estimator
actually rests on. **It is a smaller claim and a true one.**

**The check costs nothing and requires no data.** It should have been applied
before a line of code was written. It was not, and that is the largest single
error in the project.

A useful way to see it: if you want to know which houses flood, you model
where the river breaches and then compute which houses sit below the water
line. You do not model five hundred houses as five hundred independent
events. That would mostly teach you that neighbouring houses flood together.

**And the diagnosis has now been tested rather than asserted.** The hazard
model was revived on the expanded panel — 5,441 events against 812, 11,230
risk-set units against 1,756 — and the constant null is still better
calibrated in **17 of 17** comparisons (`hazard_revival.json`,
`20260915-224104-21a7`). 6.7× the events does not touch a defect that is
geometry.

### 14.3 What changed, and what did not

```
                     was                          becomes
unit           ZCTA-quarter                 station siting decision
observations   812 ZCTA "events"            28-38 real choices (pilot);
                                            483 decisions as actually
                                            fitted on the expanded frame
question       when does a ZIP switch on    which ZIP, given one opens
model          cloglog discrete-time        conditional choice, V=ln(beta'a)
time           32 quarters                  2-3 structural periods
headline       AUC                          Brier pair + calibration
the date       the event time               a conditioning variable
```

**The ZIP-level answer is not abandoned — it is derived:**

```
P(your ZIP gets same-day service)
  =  P(a station opens in your metro)         from base rates
  x  P(the chosen site is within 15 miles)    from the choice model
```

The first factor is the metro-entry model, and it returns a pre-registered H0
([`STATUS.md`](STATUS.md) §2). The reframe made the specification **valid**,
not **powerful**, and then the valid specification also failed. That is worth
saying plainly: the fault was not only the unit of analysis. Either the
covariates available from free public data do not contain the signal, or the
dates are too corrupted to learn from, and this project cannot yet tell
which.

### 14.4 The thing to say if asked why the method changed

> *"I specified a model, built it, tested it, and it failed. Then I went to
> the literature to find out why."*

A specification that was never stress-tested is worth less than one that was
tested, failed, and replaced for a reason that can be stated. Most projects
never learn whether their model works, because they never build a benchmark
to lose to.

---

## 15. Implemented versus documented — the whole reading list

*Relocated from `PLAN.md`, 2026-09-15. Sections 2-12 above are the arguments;
this is the ledger of what each paper actually changed in the code.*

```
  PAPER                     STATUS      WHAT IT CHANGED IN CODE
  Fellegi & Holt 1976       BUILT       warehouse/edits.py - a declared
                                        EDITS registry, dispositions
                                        EXCLUDE/REPORT. CORRECT deliberately
                                        absent (it is the imputation rule
                                        Criterion 2 abolishes). Resolved all
                                        3 date contradictions.
  Rahm & Do 2000            BUILT       common/sentinels.py - one declared
                                        registry for substitute codes, after
                                        the taxonomy showed our two
                                        "separate" defects were one class
  Van den Broeck 2005       BUILT       warehouse/flag_gate.py + the
                                        uncorrected/corrected cross-tab in
                                        data/CLEANING_CHANGELOG.md
  Klose & Drexl 2005        BUILT       cost/depots.py - p-median replacing
                                        k-means, quality bounded at 0.89%
                                        above a Lagrangean lower bound
  Hakimi 1964               DOC ONLY    read, and it does NOT license what we
                                        claimed. Node restriction defended by
                                        a measured 0.45% instead
  Gneiting & Raftery 2007   PARTIAL     reporting changed to the raw Brier
                                        PAIR. Winkler's standardised score
                                        (proper, built for rare events)
                                        identified and NOT implemented
  Train 2009 ch 2,3,4,8,13  BUILT, IN   MODEL_SPEC.md written, then fitted as
                            PART        models/choice.py. Three of the
                                        specification's clauses were not
                                        implemented: two periods, the
                                        sandwich, the bootstrap. MODEL_SPEC
                                        Sec. 0.3
  Little & Rubin            DOC ONLY    diagnosis only; no treatment built
  Winkler RR99-01           PARTIAL     edit registry yes; consistency check
                                        on the edit set NOT built
  Chao / capture-recapture  BUILT       ingest/nlrb_estimators.py
  Holmes 2011 / HNS 2023    DOC ONLY    parameter comparison; the estimator
                                        itself rejected, Sec. 2 and Sec. 3
  Daganzo 1984              PARTIAL     cost/daganzo.py implements the
                                        continuous approximation; the paper
                                        itself is NOT on disk, and
                                        research/NOTES_daganzo_1984.md says
                                        so in its first line
```

**Four literature findings are documented and NOT implemented**, and each is
a real gap rather than a formality:

```
  1  Winkler's standardised score - proper, rare-event, computable from
     outputs/tables/hazard_predictions.parquet WITHOUT refitting. Cheapest
     win outstanding.
  2  The consistency check on the edit set (Winkler feature 2; FH sec 5.2).
  3  Any missingness treatment at all. We measured not-MCAR and did nothing.
     cost/runner.py:166 still does listwise deletion.
  4  Macro / selective editing - rank records by influence on key totals.
     No outlier detection of any kind exists.
```

### 15.1 Why the Econometrica estimator was rejected

**Its identifying variation is exactly the quantity we cannot observe, and
Holmes says so himself.** His Sec. 6.1 measurement-error result, which first
attracted us, assumes `x` and the instruments are "directly observed" and
puts the error on profits. Sec. 8.3 is explicit that the procedure "yields
inconsistent estimates of the identified set when there is measurement error
in the `x` variables", and Sec. 7 states that opening dates "are all assumed
to be measured without error".

Under the swap design our dates define the deviations, the instrument groups
**and** the discounting window. Holmes protects the side we have clean and
assumes clean the side we do not. Our dates are OSHA inspection dates with
externally verified lags of 4, 13, 57, 69 and 345 months. For many pairs we
do not know the sign of `t_j - t_k`, so we cannot say which roll-out was
chosen and which is the counterfactual. Full reasoning in Sec. 2 and Sec. 3
above.
