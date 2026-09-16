# Notes — Holmes (2011), The Diffusion of Wal-Mart and Economies of Density

*Read selectively on 2026-09-13 for two specific questions: (a) does Holmes
put a dollar figure on opening a facility, and (b) what exactly does his
cannibalisation number measure. Section 7 below says precisely which parts
were opened and which were not. These notes exist so nobody reopens the PDF
for these two questions.*

---

## 1. Citation and local file

```
  Thomas J. Holmes.
  "The Diffusion of Wal-Mart and Economies of Density."
  Econometrica, 79(1):253-302, January 2011.
  University of Minnesota, Federal Reserve Bank of Minneapolis, and NBER.

  Local file:  ../Research/ecta7699.pdf   (51 PDF pages)
  PDF page 1 is the Econometric Society cover sheet.
  PDF page 2 = printed p. 253.
  So: PDF page = printed page - 251.  Printed p. 302 = PDF page 51.
  Verified: PDF page 24 carries the running head "275" and Table VIII.
```

Every page number quoted below is the **printed** page.

---

## 2. What the paper is for

Holmes asks why Wal-Mart expanded outward from Bentonville in a slow,
contiguous wave rather than jumping to the richest markets first. His answer
is *economies of density*: packing stores close together cuts distribution
cost, because each store is nearer a distribution centre, but it also means
the stores steal sales from each other. The paper estimates a lower bound on
how big the distribution saving must be, given that Wal-Mart was observed to
tolerate a measured amount of self-cannibalisation in order to get it. The
estimator is a revealed-preference moment inequality built by perturbing the
observed opening dates — open store *j* a year earlier and store *k* a year
later, and infer that the swap cannot have raised profit. For siting-atlas
the paper matters for three separate reasons: it is the ancestor of our
portfolio objective's positive/negative interaction structure, it is the only
published source that measures something close to `cannibalisation_peak`, and
its treatment of fixed and sunk cost is the benchmark against which
`capital_per_activation_usd` should be judged.

---

## 3. Walkthrough of the sections actually read

### Section 2 — Model (printed pp. 258-262)

The model is a deterministic, perfect-foresight, infinite-horizon expansion
problem. Wal-Mart chooses, each period, how many stores and distribution
centres to open and where to put them. Three cost components matter besides
cost of goods sold: distribution cost, variable store cost, and fixed cost at
the store level.

**Distribution cost** is `tau * d_jt` — a cost per mile per period per
merchandise segment from the store to its closest distribution centre. Holmes
is explicit that this is modelled as a *fixed* cost per store per period, not
a volume-scaled one, on the grounds that Wal-Mart runs a daily delivery run to
every store whatever the load (p. 259). `tau` is the object the whole paper is
trying to bound.

**Variable cost** is proportionate to sales volume — labour, land and other
inputs all scale linearly with `R_j`. Notably Holmes treats *building size and
shelving* as variable rather than fixed, justified on the grounds that
Wal-Mart continually expands and remodels stores, so store size is "not a
permanent decision that is made once and for all" (p. 260). This is worth
noting for us: the thing a naive reader would call "the capital cost of the
building" is, in Holmes, folded into variable cost and scaled by sales.

**Fixed cost** is where the load-bearing material for our capital question
sits. This is the paragraph in full, printed p. 260, under the sub-heading
"Fixed Costs":

> "We expect there to be a fixed cost of operating a store. To the extent the
> fixed cost is the same across locations, it will play no role in the
> analysis of where Wal-Mart places a given number of stores. We are only
> interested in the component of fixed cost that varies across locations."

He then writes the location-varying part as a quadratic in log population
density (equation (1), p. 260):

```
  c(Popden_j)  =  omega_0 + omega_1 * ln(Popden_j) + omega_2 * ln(Popden_j)^2
```

and immediately normalises the constant away:

> "It will be with no loss of generality in our analysis to assume that the
> constant term omega_0 = 0, since the only component of the fixed cost that
> will matter in the analysis is the part that varies across locations."
> — §2, "Fixed Costs", p. 260

**This is the sentence that decides our capital question, and its logic is
narrower than it first looks.** The normalisation is licensed by the phrase
"the analysis of *where* Wal-Mart places a given number of stores". Holmes
conditions on the number of stores and asks only about their placement. A
location-invariant constant cannot shift a placement decision, so he drops it.
He does *not* claim it is zero, unknowable, or unimportant.

**Sunk costs**, §2 "Dynamics", printed p. 262, the whole passage:

> "No explicit mention has been made about the presence of sunk costs.
> Implicitly, sunk costs are large, and that is why no store is ever closed
> once opened. Sunk costs can easily be worked into the model by having some
> portion of the present value of the fixed cost in equation (1) paid at entry
> rather than in perpetuity each period. This leaves the objective in equation
> (2) unchanged."

Read that carefully. Holmes says sunk costs are *large*, says they can be
worked in *easily*, and says doing so changes nothing **for his objective** —
because the present value of a constant paid at entry equals the present value
of the same constant paid as a perpetuity, and either way it is
location-invariant and differences out of his inequalities.

**Discount factor**, §2 "Dynamics", printed p. 261:

> "Now for more notation. To begin with, the discount factor each period is
> beta. The period length is a year, and the discount factor is set to
> beta = .95."

That is the entire treatment. No source, no sensitivity, no justification.
`1/0.95 - 1 = 5.263%` a year.

### Section 4.1 — Demand specification (printed p. 265)

Consumers make a discrete choice between an outside option and any Wal-Mart
within 25 miles:

> "A consumer at a particular location l chooses between shopping at the
> 'outside option' and shopping at any Wal-Mart located within 25 miles."
> — §4.1, p. 265

The choice set is `B_bar = {j : j in B_Wal and Distance_lj <= 25}`. This is a
**consumer choice-set truncation radius**, not a cannibalisation radius, and
it is the object PARAMETERS.md §6.18 correctly declines to treat as support
for `cannibalisation_radius_km`.

The key structural fact for us: cannibalisation in Holmes arises because a
consumer picks **one outlet** out of several. Sales move between stores when
the choice set changes. Total consumer demand at location `l` is not reduced
by a new store; only its allocation across stores changes, plus whatever is
drawn from the outside option.

### Section 4.2 / Table V — the chain-wide cannibalisation rate (printed p. 269)

```
                                 TABLE V
         CANNIBALIZATION RATES, FROM ANNUAL REPORTS AND IN MODEL
         (percent)

          Year    From Annual      Demand Model      Demand Model
                    Reports       (Unconstrained)    (Constrained)
          ----    -----------     ---------------    -------------
          1998        n.a.              0.62              0.48
          1999        n.a.              0.87              0.67
          2000        n.a.              0.55              0.40
          2001         1                0.67              0.53
          2002         1                1.28              1.02
          2003         1                1.38              1.10
          2004         1                1.43              1.14
          2005         1                1.27              1.00 (imposed)

  Source: model estimates and Wal-Mart Stores, Inc. annual reports 2004, 2006.
```

These are **percentages, chain-wide**. The denominator is total sales at *all*
pre-existing stores, including every region where Wal-Mart opened nothing that
year. Holmes says so himself when reconciling this table with Table VIII
(p. 275, quoted in §4 below). The ~1% figure is therefore the *wrong* object to
compare `cannibalisation_peak` against, and PARAMETERS.md §7.4 is right to
treat the store-level number as the relevant one instead.

Holmes uses the **constrained** model (2005 rate forced to exactly 1.00) as his
baseline, explicitly "in the interests of being conservative in my estimate of
a lower bound on density economies" (p. 270), even though a likelihood-ratio
test rejects the constraint.

### Section 5 and Table VIII — the number we actually use (printed pp. 274-276)

This is the section the `cannibalisation_peak` docstring cites, and it is the
only place in either Econometrica paper where a quantity close to ours is
measured.

Holmes defines incremental sales for a store opening in year *t* as what the
store adds to **total Wal-Mart sales** that year, relative to what sales would
otherwise have been across all other stores open that year (p. 274). Stand-alone
sales are what the store would sell "if it were isolated so that none of its
sales is diverted to or from other Wal-Mart stores in the vicinity" (pp. 274-275).
Both are computed from the fitted demand model at 2005 demand equivalents, in
millions of 2005 dollars, with no multiplicative scale adjustment, so the years
are comparable.

```
                                   TABLE VIII
        INCREMENTAL AND STAND-ALONE VALUES OF NEW STORE OPENINGS
        (millions of 2005 dollars, at 2005 demand equivalents)

  PART A: GENERAL MERCHANDISE (new Wal-Marts including supercenters)

  State's Wal-Mart              Incr.   Incr.    Incr. DC    Stand-   Stand-
  age at opening         N      Sales   Op.Profit Dist (mi)  alone    alone
                                                             Sales    Op.Profit
  --------------------  -----   -----   -------- ---------   ------   ---------
  All                   3,176    36.3     3.1      168.9      41.4      3.6
    1-2                   288    38.0     3.5      343.3      38.7      3.6
    3-5                   614    39.5     3.5      202.0      41.5      3.7
    6-10                   939   37.6     3.3      160.7      40.9      3.6
    11-15                  642   36.1     2.9      142.1      42.2      3.4
    16-20                  383   32.9     2.8      113.7      41.2      3.5
    21 and above           310   29.5     2.4       90.2      44.4      3.6

  PART B: FOOD (new supercenters)

  All                   1,980    40.2     3.6      137.0      44.8      4.0
    1-2                    202   42.4     3.9      252.9      43.9      3.9
    3-5                    484   42.7     4.0      171.2      44.7      4.1
    6-10                   775   41.0     3.6      113.5      45.3      4.0
    11-15                  452   36.7     3.2       95.3      45.3      3.9
    16-20                   67   30.1     2.8       94.0      38.6      3.5
```

**Implied cannibalisation rate, `1 - incremental/stand-alone`, computed by me
from the table above** (Holmes does not print this column):

```
  State's Wal-Mart age     General merchandise     Food (supercenters)
  --------------------     -------------------     -------------------
  All                             12.3%                   10.3%
    1-2                            1.8%                    3.4%
    3-5                            4.8%                    4.5%
    6-10                           8.1%                    9.5%
    11-15                         14.5%                   19.0%
    16-20                         20.1%                   22.0%
    21 and above                  33.6%                     n/a
```

Two things fall straight out of that and neither is in our current docs.

**First, the headline "10 percent" is 12.3% on the general-merchandise row.**
Holmes's own prose rounds it down. His sentence (printed p. 275):

> "Table VIII shows for the average new Wal-Mart, there is a big difference
> between stand-alone and incremental values, implying a substantial degree of
> market overlap with existing stores. Average stand-alone sales is $41.4
> million compared to an incremental value of $36.3 million, approximately a
> 10 percent difference."

`(41.4 - 36.3) / 41.4 = 12.32%`. The food row is `(44.8 - 40.2) / 44.8 =
10.27%`, which is where "approximately 10 percent" is exactly right. So the
comparator that PARAMETERS.md §7.4 reports as "~0.10" is 0.123 for general
merchandise and 0.103 for food.

**Second, and far more important, the "All" row is an average over Wal-Mart's
entire fifty-year diffusion history, including greenfield entry where
cannibalisation is near zero by construction.** The by-maturity rows show the
rate climbing monotonically from 1.8% for the first stores in a state to
**33.6%** once Wal-Mart has been in the state for over twenty years. Holmes
reads the same pattern off the operating-profit column (p. 276):

> "Table VIII shows that incremental operating profit in a state falls over
> time as Wal-Mart adds stores to a state and the store market areas
> increasingly begin to overlap. [...] This pattern is a kind of diminishing
> returns. Wal-Mart is getting less incremental operating profit from the
> later stores it opens in a state."

Holmes also pre-empts the obvious objection that Table VIII (12.3%) and Table V
(~1%) disagree (printed p. 275):

> "Two considerations account for why the big cannibalization numbers found
> here are not inconsistent with the 1 percent cannibalization rates reported
> earlier in Table V. First, the denominator of the cannibalization rate from
> Table V includes all preexisting stores, including those areas of the country
> where Wal-Mart is not adding any new stores. Taking an average over the
> country as a whole understates the degree of cannibalization taking place
> where Wal-Mart is adding new stores. Second, stand-alone sales include sales
> that a new store would never get because the sales would remain in some
> existing store (but would be diverted to the new store if existing stores
> shut down)."

Note the second consideration: Holmes is warning that the stand-alone baseline
is itself generous, so 12.3% is if anything an **over**statement of true
diversion even on his own terms.

### Section 7.1 and footnote 20 — the only dollar figure on a facility (printed p. 287)

This is the "$18 million" our docs quote. It is a *distribution centre*, it is
an *annual operating* cost, and it is presented as a back-of-envelope
cross-check on `tau`, not as an estimate. The main text (p. 287):

> "If we knew something about the fixed cost, then the condition
> phi_k ~ tau * D_kt^inc provides an alternative means of inferring tau. A very
> rough calculation suggests a ballpark fixed cost of $18 million per year."

And footnote 20 on the same page, in full — this is the whole derivation:

> "Distribution centers are on the order of 1 million square feet. Annual
> rental rates including maintenance and taxes are on the order of $6 per
> square foot, so $6 million a year is a rough approximation for the rent of
> such a facility. A typical Wal-Mart DC has a payroll of $36 million. If a
> third of labor is fixed cost, then we have a total fixed cost of
> $18 = $6 + $12 million."

Four inputs — 1m sq ft, $6/sq ft, $36m payroll, one-third fixed — and not one
of them carries a citation. "On the order of" appears twice and "rough"
appears twice in three sentences. PARAMETERS.md §6.16 describes this
accurately.

---

## 4. Formal definitions, exactly as stated

**Incremental sales** (§5, p. 274):

> "Define the incremental sales R_jt^inc of store j to be what the store adds
> to total Wal-Mart sales in segment e in its opening year t, relative to what
> sales would otherwise be across all other stores open that year."

**Stand-alone sales** (§5, pp. 274-275):

> "what would sales and operating profits be at a store if it were isolated so
> that none of its sales is diverted to or from other Wal-Mart stores in the
> vicinity?"

**Consumer choice set** (§4.1, p. 265):

> "B_bar_l^Wal = {j : j in B^Wal and Distance_lj <= 25}"

**Fixed cost** (§2, eq. (1), p. 260):

> "c(Popden_j) = omega_0 + omega_1 ln(Popden_j) + omega_2 ln(Popden_j)^2"

with `omega_0 = 0` imposed as a normalisation.

**Discount factor** (§2, p. 261): `beta = .95`, period length one year.

---

## 5. What this means for siting-atlas

### 5.1 The capital question — Holmes does NOT say "have no capital term"

`docs/data/PARAMETERS.md` §6.16 and the docstring at
`src/siting_atlas/optimize/params.py:42` both currently say Holmes "refuses to
put a dollar on opening a facility" and normalises sunk cost away "precisely
because it does not vary by location". The second half is right; the word
"refuses" is not, and the inference people will draw from it is wrong.

What Holmes actually does is set `omega_0 = 0` **because he is answering a
placement question with the number of stores held fixed** (p. 260, quoted
above), and note that sunk costs are *large* but drop out of *his* objective
(p. 262). His §8.3 point about the estimator is the same species of statement:
an inequality built by swapping two opening dates differences out anything that
is common to both stores.

siting-atlas is not answering Holmes's question. `optimize/select.py` sets
`capacity = floor(budget / capital_per_activation_usd)` and the greedy loop
decides **how many** units to fund. A location-invariant per-facility capital
cost is *exactly* the quantity that determines how many, and Holmes's reason
for dropping it therefore does not transfer. **We should keep a capital term.**
The literature is silent on its value, not hostile to its existence, and our
docs should stop implying otherwise.

What Holmes does license is a much sharper warning about the *unit*: his
`omega_0` is per **store**, i.e. per facility. He never charges a fixed cost per
unit of geography.

### 5.2 The cannibalisation question — our docs cite the wrong row

`src/siting_atlas/optimize/params.py:97` defines `cannibalisation_peak` as the
**"Maximum share of volume a ZCTA can lose to active neighbours"** — the
ceiling of the saturating function `peak * (1 - exp(-exposure))` at
`optimize/objective.py:157-158`. It is a *maximum*, reached only when a ZCTA is
surrounded by active neighbours.

PARAMETERS.md §7.4 compares that maximum against Holmes's **"All" row**, an
average over 3,176 stores spanning greenfield entry to saturation. That is a
category error: it compares a ceiling to a mean. The correct Holmes comparator
for a saturation ceiling is the saturated row — **33.6%** for general
merchandise in states where Wal-Mart has operated 21+ years, or 22.0% for food
at 16-20 years.

Against that comparator, 0.18 is not 1.8x too high. It sits roughly midway
between Holmes's average (12.3%) and Holmes's saturated ceiling (33.6%), which
is a defensible place for a *peak* to sit and is arguably conservative.

Measured today at `optimize/params.py` baseline, $2bn budget, 2023Q4 cost
table (see §6 of these notes for the caveat about a concurrently-changing
`cost/depots.py`):

```
  cannibalisation_peak                              n     BE $/parcel   Jaccard
  ----------------------------------------------  ----   -----------   -------
  0.000  HNS-implied net demand effect             313      1.1788      0.574
  0.050  current docs low end                      311      1.2289      0.647
  0.103  Holmes VIII food, ALL stores              302      1.2780      0.764
  0.123  Holmes VIII gen. merch, ALL stores        302      1.2974      0.808
  0.180  CURRENT VALUE                             282      1.3431      1.000
  0.201  Holmes VIII GM, state age 16-20           266      1.3559      0.864
  0.336  Holmes VIII GM, state age 21+             177      1.3369      0.457
  0.350  current docs high end                     177      1.3403      0.434
```

The 0.35 endpoint that PARAMETERS.md §4 presents as an implausible stress test
is almost exactly Holmes's saturated-state figure of 0.336. The "stress test"
is a literature-supported value.

### 5.3 But the transfer itself is questionable, and that cuts deeper

Everything in §5.2 assumes Holmes's quantity is our quantity. It is not, and the
existing caveat in `optimize/params.py:120-124` gets the direction right while
understating the problem.

Holmes measures **diversion between outlets of the same chain**. A consumer at
location `l` picks one Wal-Mart from a 25-mile choice set; a new store changes
which store gets the sale. Total spending by that consumer barely moves.

`optimize/objective.py:158` does something structurally different:

```python
  parcels = self.annual_parcels * (1.0 - p.cannibalisation_peak * decay)
```

`annual_parcels` for a ZCTA is generated by the **households resident in that
ZCTA** — `cost/daganzo.py` builds it from `households` times
`parcels_per_household_per_week` times an income scaling. Activating a
neighbouring ZCTA does not make those households order fewer parcels. Parcel
demand is anchored to the customer's home, not to a chosen outlet, so there is
no outlet for it to be diverted to.

So the honest reading is that **Holmes's 12.3% (or 33.6%) is not transferable
at all**, because the mechanism that generates it — consumers substituting
between outlets — has no counterpart in a specification whose demand unit is a
residential ZCTA. See the HNS notes for an independent measurement that makes
the same point more sharply.

This is not an argument that the parameter should be 0.10 rather than 0.18. It
is an argument that the parameter is currently measuring something the model
does not contain, and that the fix is definitional, not a recalibration. Both
of the candidate repairs are coherent:

- **Keep the ZCTA as the unit of demand** and set the peak near zero, because
  resident parcel demand does not walk. The neighbour interaction then only
  affects *cost*, which `linehaul_sharing` already handles.
- **Reinterpret an activation as a station** whose catchment overlaps its
  neighbours'. Then Holmes transfers cleanly, 0.12-0.34 is the right band, and
  `capital_per_activation_usd` at $4m per unit becomes correct too — but the
  parcels and cost per unit are then wrong by roughly the ZCTAs-per-station
  ratio.

Those are the same choice. See §5.4.

### 5.4 Questions 1 and 2 are one defect

The capital unit problem and the cannibalisation transfer problem are two
symptoms of a single ambiguity about what an "activation" is:

```
  term                          file:line                   treats a unit as
  ---------------------------   -------------------------   ----------------
  annual_parcels, annual_cost   optimize/objective.py:81-83  a ZCTA of resident demand
  capital (n * $4m)             optimize/objective.py:164    a facility
  cannibalisation of volume     optimize/objective.py:158    a facility with a catchment
```

Rows two and three are internally consistent with each other and both are
inconsistent with row one. Deciding what an activation *is* resolves both
questions at once, which is a better outcome than tuning two constants
separately.

### 5.5 The discount rate — the disagreement is real and correctly described

PARAMETERS.md §7.3 says both papers set beta = 0.95 (~5.3%) and neither cites a
source. **Verified for Holmes**, printed p. 261, quoted in §3 above. Our 0.10 is
1.9x his implied rate. The existing recommendation — keep 10%, state the
disagreement — is sound; a private logistics hurdle rate is a different object
from whatever Holmes had in mind, and he offers no argument to defend.

---

## 6. A caveat on every number in §5.2

The sensitivity figures in §5.2 were measured on 2026-09-13 while another agent
was actively rewriting `src/siting_atlas/cost/depots.py` (k-means placement
replaced by a p-median formulation). The selected-set size at baseline moved
from 330 to 282 over the course of this session for that reason alone, and the
published headline of "330 ZIPs, $1.32bn" in `PARAMETERS.md` §4 is stale as a
result; the drift is recorded at
[`../DECISION_LOG.md`](../DECISION_LOG.md) §4.2. The table above was computed in a single
process against `cost/depots.py` md5 prefix `d93ae1ecaf` so that its rows are
mutually consistent; the **ordering and the Jaccard pattern** are the robust
content, not the absolute counts. Re-measure before quoting.

---

## 7. What I did NOT read

Honest inventory. This was a targeted read for two questions, and most of the
paper's actual contribution was skipped.

**Read in full:**
- §2 Model, all of it (pp. 258-262), including Distribution Costs, Variable
  Costs, Fixed Costs, and Dynamics.
- §4.1 Demand Specification, the choice-set definition only (p. 265).
- §5 Preliminary Evidence of a Trade-Off, in full with Table VIII (pp. 273-276).
- Table V and the surrounding reconciliation discussion (pp. 269-270).
- §7.1, the `tau` cross-check passage and footnote 20 (p. 287).

**Not read, at all:**
- §1 Introduction (pp. 253-258).
- §3 The Data, and Tables I, II, III (pp. 262-265). I have not checked what
  Wal-Mart's store-level sales data actually is or where the opening dates
  came from.
- §4.2 Demand Estimation, Tables IV and VI (pp. 265-268). **I did not read how
  the demand model that generates Table VIII is estimated.** This matters: the
  incremental/stand-alone split in Table VIII is a model output, not a
  measurement, and I have not inspected the model that produced it. The
  distance-decay estimates in Table VI, which PARAMETERS.md §6.18 cites, were
  not opened either — that citation is inherited, not verified here.
- §4.3 Variable Costs at the Store Level, Table VII (pp. 271-272).
- §4.4 Extrapolation to Other Years (p. 272).
- §6 Bounding Density Economies: Method, §6.1 and §6.2, Tables IX and X
  (pp. 276-283). This is the paper's methodological core and the subject of
  `docs/METHODS_RESEARCH.md`. Nothing here revisits or challenges that reading.
- §7 Baseline Results and Tables XI, XII (pp. 283-288) except the footnote-20
  passage. In particular **I did not read the estimates of omega_1 and
  omega_2**, the location-varying fixed-cost coefficients. If anyone wants a
  published magnitude for how much facility fixed cost varies with population
  density, that is where to look and I have not looked.
- §8 Confidence Intervals, §8.1, §8.2, §8.3, Table XIII (pp. 288-293).
  §8.3 is quoted at [`../METHODS_RESEARCH.md`](../METHODS_RESEARCH.md) §15.1
  from a prior reading; I did not re-verify it.
- §9 Concluding Remarks (pp. 293-294).
- All appendices, the supplemental material, and the reference list.

**Specifically not verified:**
- That the demand model underlying Table VIII is well identified.
- Wal-Mart's 2004 annual report, cited by Holmes for the 1% figure and quoted
  at second hand in PARAMETERS.md §7.4. I read Holmes's Table V, not the annual
  report.
- Whether Holmes anywhere reports a store construction or land-acquisition
  cost. I searched the extracted text for "sunk", "construction", "capital" and
  "normaliz/normalis" and found only what is quoted above, but I did not read
  every page, so treat this as "not found in a targeted search" rather than
  "definitively absent".
