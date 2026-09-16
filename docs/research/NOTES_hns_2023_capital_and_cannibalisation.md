# Notes — Houde, Newberry & Seim (2023), Nexus Tax Laws and Economies of Density in E-Commerce

*Read selectively on 2026-09-13 for the same two questions as the Holmes
notes: (a) does the paper put a dollar figure on opening a facility, and
(b) does it measure anything comparable to `cannibalisation_peak`. Section 7
says exactly which parts were opened. These notes exist so nobody reopens the
PDF for these two questions.*

Companion file: `NOTES_holmes_2011_capital_and_cannibalisation.md`. The two
should be read together; HNS deliberately mirror Holmes's design and the
interesting content is in where they differ.

---

## 1. Citation and local file

```
  Jean-Francois Houde, Peter Newberry, and Katja Seim.
  "Nexus Tax Laws and Economies of Density in E-Commerce:
   A Study of Amazon's Fulfillment Center Network."
  Econometrica, 91(1):147-190, January 2023.
  Houde: University of Wisconsin-Madison.  Newberry: University of Georgia.
  Seim: Yale School of Management.

  Local file:  ../Research/ECTA15265.pdf   (44 PDF pages)
  No cover sheet.  PDF page 1 = printed p. 147.
  So: PDF page = printed page - 146.  Printed p. 190 = PDF page 44.
  Verified: PDF page 34 carries the running head "180" and section 4.4.
```

Every page number quoted below is the **printed** page.

---

## 2. What the paper is for

Amazon's fulfilment network was shaped by state nexus tax laws: until the
mid-2010s, putting a warehouse in a state triggered an obligation to collect
that state's sales tax, so Amazon avoided populous states even though
proximity would have cut shipping costs. HNS exploit that tension to estimate
the cost side of Amazon's location problem. They build a demand model over
county-level online spending, an order-flow model that routes each order to a
facility, and a cost function with shipping, labour and fixed components, then
estimate the cost parameters by moment inequalities constructed from
perturbing the **timing** of facility openings. The headline is that economies
of density in shipping exceed the tax distortion, and that total average
fulfilment cost fell 55% between 2000 and 2018.

For siting-atlas it is the closest published analogue to what we are doing:
same firm, same industry, same facility-network object, and a structure that
explicitly separates fixed cost from variable cost. It is cited in
`docs/data/PARAMETERS.md` at §6.11, §6.12, §6.16, §6.18, §6.21 and §7.3.

---

## 3. Walkthrough of the sections actually read

### Section 2.2-2.3 — the network and what "fixed cost" is made of (printed pp. 153-154)

§2.2 describes the facility tiers from MWPVL International data. The two
catchment figures our docs cite are here, printed p. 153:

> "According to MWPVL, packages that are routed through Amazon's own sortation
> network satisfy two conditions. First, the final destination must be within
> the sortation facility's coverage region. MWPVL suggests that a sortation
> center's catchment area includes destination zip codes within 150 miles from
> the facility. Second, the sortation center must be near one or more
> fulfillment centers, at a distance of at most 25 miles."

That confirms the 150-mile and 25-mile figures in PARAMETERS.md §6.21, and
confirms they describe **sortation**, not last-mile delivery. They do not bear
on `CATCHMENT_MILES["DS"] = 15`.

§2.3, printed pp. 153-154, defines the fixed cost. This is the passage that
answers the capital question on the data side:

> "We assume that the costs Amazon faces when making network decisions are
> split into fixed costs and variable costs per order. Fixed costs consist of
> the cost of warehouse space. We recognize, per square foot of warehouse
> space, the observed rental rate and a congestion penalty to urban locations.
> We approximate the rental rate with local commercial rents for warehousing
> space."

and, printed p. 154:

> "We estimate the total fixed cost of a facility as the square footage
> reported by MWPVL times the sum of rent and congestion payment."

**So HNS's "fixed cost" is a rental flow, not a construction cost.** It is
square footage times (rent + congestion penalty), per period. No purchase
price, no build cost, no land acquisition anywhere in the cost function.
Rental rates come from Moody's Analytics REIS, which covers most MSAs
2006-2018; density comes from the Census.

### Section 3.4 — the cost function (printed p. 164)

Equation (9), printed p. 164:

```
  F_t(N_t)  =  sum_j sum_l  k_j * (r_lt + kappa * PopDensity_lt) * 1(l_j = l)

            =  C_t^Rent(N_t)  +  sum_j sum_l k_j * (kappa * PopDensity_lt) * 1(l_j = l)
```

where `k_j` is facility `j`'s square footage and `r_lt` the rental rate in
cluster `l`. The paper's gloss, p. 164:

> "C_t^Rent is the fixed cost of space, which scales with a rental rate of
> r_lt. The parameter kappa measures how the fixed cost per square foot
> increases as the population density of location l increases. Such additional
> penalties reflect either congestion or measurement error in rental rates,
> both of which are likely more pronounced for large facilities."

Note what is and is not in here. Fixed cost varies with **location** (through
rent and density) and with **size** (through square footage). There is no
term at all for the act of opening a facility.

### Section 3.5 — the optimisation problem and the discount factor (printed p. 165)

Equation (11):

```
  a_0  =  max_a  sum_{t=0..inf}  beta^t * pi_t(N_t)

  s.t.   N_t = N_t^0(a)
         sum_j 1(a_j = t) = n_t^0 - n_{t-1}^0
```

and immediately beneath it, printed p. 165:

> "where beta = 0.95 is Amazon's discount factor and n_t^0 - n_{t-1}^0 is the
> observed number of facilities opened in period t."

That is the whole treatment of the discount factor — a subordinate clause. No
source, no sensitivity. Identical to Holmes both in value and in the absence
of any justification. `1/0.95 - 1 = 5.263%` a year. **PARAMETERS.md §7.3 is
verified on both papers.**

The constraint is the important structural feature. HNS hold the **number** of
facilities opened in each period fixed at the observed count, and optimise only
over **which** locations and **when**. They say so directly (p. 164, just above
eq. (11)):

> "We are interested in understanding the trade-offs associated with the
> location choice of each new active facility, conditional on the number and
> characteristics of facilities built every year. Like Holmes (2011), we
> characterize the expansion of the network as the outcome of a constrained
> dynamic optimization problem with perfect foresight"

### Section 3.6 — Discussion. Two passages that decide both of our questions.

**First, on sunk cost** (printed p. 166):

> "A second advantage to exploiting the optimality of the timing of facility
> openings, rather than the optimality of the number of facilities, is that we
> can disregard unobserved sunk costs or benefits to opening facilities,
> provided these are the same across facilities. We thus abstract from
> location-specific unobserved sunk costs to opening a facility, such as the
> local government subsidies studied in Slattery (2020)."

Read the clause structure. They can drop sunk costs **because** they exploit
the optimality of timing "rather than the optimality of the number of
facilities", and **provided** those costs are the same across facilities. Both
conditions are stated explicitly as the enabling assumptions, not as findings
about the world.

**Second, on whether proximity to a facility affects demand** (printed p. 165).
This is the passage that bears directly on `cannibalisation_peak` and it is not
cited anywhere in our docs:

> "In Houde, Newberry, and Seim (2021), we exploited this fact to test whether
> Amazon spending responds to various proxies for shipping speed from the
> closest fulfillment, controlling for tax exposure, and cannot reject the
> hypothesis that consumer spending is independent of proximity to an Amazon
> facility, our maintained assumption here. This is consistent with the limited
> variation in shipping times on Amazon in practice: since 2005, Amazon has
> offered the same shipping terms, free two-day shipping on eligible purchases,
> to all Prime members irrespective of location."

So HNS **tested** whether a household's Amazon spending depends on how close
the nearest fulfilment centre is, could not reject independence, and adopted
independence as a maintained assumption. In their model, opening a facility
near a county changes **nothing** about how much that county orders.

### Section 4.3 and Tables VI-VII — estimated cost magnitudes (printed pp. 177-178)

Preferred specification is (3).

```
                               TABLE VI
                       COST FUNCTION ESTIMATES

                          Spec 1            Spec 2             Spec 3
                     Est.     95% CI    Est.    95% CI     Est.    95% CI
  ------------------ -----  ----------  ----  -----------  ----  -----------
  theta_d  dist            0.16  0.15-0.17  0.59  0.41-0.88  0.34  0.26-0.49
    ($ per 100 miles)
  theta_vi VI orders          -          -      -       -    -0.52 -0.91-0.01
  kappa    density
    (x100)                    -          -   2.06  1.48-3.17  0.98  0.69-1.56
  Moments                     4                8                 14

  All specifications use 5,577 total swaps.
```

```
                              TABLE VII
                      AVERAGE COST DECOMPOSITION
        (dollars per order, except FC and SC which are facility counts)

  Year    FC    SC   Shipping   Labor   Rent   Density   Total
  -----  ----  ----  --------   -----   ----   -------   -----
  2000      5     0     1.99     0.55   0.12     0.05     2.71
  2003      7     0     1.61     0.60   0.11     0.08     2.41
  2006     12     0     1.55     0.62   0.11     0.13     2.40
  2009     16     0     1.39     0.53   0.08     0.10     2.11
  2012     31     1     1.03     0.43   0.07     0.07     1.60
  2015     67    21     0.50     0.51   0.09     0.19     1.28
  2018    128    35     0.29     0.51   0.08     0.22     1.11
  2018*   128     0     0.49     0.48   0.07     0.20     1.23

  2018* is a counterfactual with no sortation centres.
  Components = total network cost / total predicted orders.
```

Two magnitudes worth carrying away. In 2018, with 128 fulfilment centres and
35 sortation centres, Amazon's **entire facility fixed cost is $0.30 per order**
(rent $0.08 + density $0.22) against a total fulfilment cost of $1.11. And
`kappa` is large enough that (p. 177):

> "our estimate of kappa implies that rents account for only approximately one
> half or less of the fixed costs to locating in an urban area with a density
> of 1000 people per square mile. We interpret this as evidence that traffic
> congestion in urban areas increases the fixed cost of managing large
> fulfillment centers."

And the honest limitation, printed p. 178, which is the single most useful
sentence in the paper for our capital question:

> "One reason for this is that our moment inequalities estimator is only able
> to capture costs that vary across the locations in the network. We are
> therefore not able to, for example, identify a constant base cost of shipping
> a package (i.e., a cost function intercept) or the cost contribution of
> system-wide investments in robotics."

They also warn (p. 178) that their cost estimates "are likely a lower bound on
the fulfillment cost", noting that Amazon's own FBA fees to third-party sellers
ran $2.50-$3.50 in Q4 2020 against their $1.11 estimate, though the fee
includes picking, packing, customer service, inventory management and a
mark-up.

### Section 4.4 and Table VIII — the California entry experiment (printed pp. 180-181)

**This is the closest thing in either paper to a direct measurement of what our
`cannibalisation_peak` is trying to capture, and it is not cited anywhere in
our docs.**

The experiment: Amazon opened its first Californian facility in the San
Bernardino cluster in 2012 and added two more in later years. HNS move all
three openings up to 2011 and recompute the network. Before entry, most
southern Californian orders were fulfilled from Arizona.

```
                              TABLE VIII
                  EFFECT OF ENTERING CALIFORNIA (2011)
      (proportional change vs the actual opening sequence)

                        ------- Nexus tax -------    ---- Uniform tax ----
  Dist(mi) State   Orders  Profit  Shipping  L+FC    Orders  Shipping  L+FC
  -------- -----   ------  ------  --------  ----    ------  --------  ----
     302    AZ     -0.88   -0.68    -0.20    0.99    -0.83    -0.21    0.95
     399    NV     -0.17   -0.18    -0.03    0.12    -0.13    -0.04    0.10
     965    WA     -0.03   -0.08    -0.24    0.08    -0.03    -0.23    0.07
    1169    TX     -0.01   -0.01    -0.04    0.01    -0.01    -0.04    0.01
  Total            -0.01   -0.00    -0.08    0.05     0.00    -0.08    0.05

  Distance is miles from each facility to the San Bernardino cluster.
  'Total' is the system-wide change.  L+FC = labour plus fixed cost.
```

The prose confirms the reading of the decimals (printed p. 180):

> "The Arizona facility experiences the biggest drop in fulfilled orders of
> 88%, suggesting that, once there is entry in southern California, the
> facility is largely redundant."

and, on the total row (p. 180):

> "Under the counterfactual opening dates, the total number of orders decreases
> by 1% due to the earlier onset of tax liabilities in California."

and on the right-hand panel (p. 181):

> "Here, entering a new state no longer triggers a new tax collection and,
> thus, total demand remains unchanged (see last row) when we move up the San
> Bernardino opening date."

**Look at the last row of the uniform-tax panel: total orders change by exactly
0.00.** Opening three new fulfilment centres changes system-wide order volume
by nothing at all, once the tax channel is switched off. Every one of the
facility-level declines — 88% at Arizona, 17% at Nevada, 3% at Washington — is
**pure reallocation of the same orders between facilities**.

HNS themselves link this to Holmes (p. 181):

> "This is similar to Holmes' (2011) approach which allows for a trade-off
> between cannibalization and density."

They also note the effect is **not monotone in distance** — Washington loses
only 3% of volume but 24% of shipping cost, because the few reallocated
shipments were the long expensive ones. That non-monotonicity is why they
cannot use Jia's (2008) lattice methods in their counterfactuals. It is also a
direct challenge to our functional form: `optimize/objective.py:126` builds a
strictly linearly-decaying `1 - d/radius` interaction weight, which is monotone
in distance by construction.

---

## 4. Formal definitions, exactly as stated

**Fixed cost of operating a network** (§3.4, eq. (9), p. 164):

> "F_t(N_t) = sum_j sum_l  k_j * (r_lt + kappa * PopDensity_lt) * 1(l_j = l)"

**The firm's problem** (§3.5, eq. (11), p. 165):

> "a_0 = max_a sum_t beta^t pi_t(N_t)  s.t.  N_t = N_t^0(a),
>  sum_j 1(a_j = t) = n_t^0 - n_{t-1}^0"

**Flow profit** (§3.5, eq. (10), p. 164):

> "pi_t(N_t) = mu_bar_t R_t(N_t) - C_t^Shipping(N_t) - C_t^Labor(N_t) - F_t(N_t)"

**Sortation catchment** (§2.2, p. 153): destination ZIPs within 150 miles of the
sortation centre; the sortation centre within 25 miles of one or more
fulfilment centres.

**Discount factor** (§3.5, p. 165): `beta = 0.95`, period one year.

---

## 5. What this means for siting-atlas

### 5.1 The capital question — "refuse" is the wrong verb, and the reason matters

`docs/data/PARAMETERS.md` §6.16 and the docstring at
`src/siting_atlas/optimize/params.py:42` say Holmes and HNS "both REFUSE to put
a dollar on opening a facility and normalise sunk cost away, precisely because
it does not vary by location."

The factual content is right and the framing is misleading. HNS do not refuse.
They state two enabling conditions and then proceed (p. 166, quoted in §3):
they exploit timing **rather than** the number of facilities, and they assume
sunk costs are **the same across facilities**. And separately they tell us
their estimator is structurally incapable of seeing a constant: it "is only
able to capture costs that vary across the locations in the network" (p. 178).

That last sentence is the crux. A location-invariant per-facility capital cost
is **invisible to a moment-inequality estimator built on within-network
swaps**, by construction. Its absence from HNS's cost function is a property of
the identification strategy, not evidence about the world. Reading their
silence as "there should be no capital term" inverts what they said.

And the condition they flag is exactly the one siting-atlas violates.
`optimize/select.py:46-47` computes `capacity = floor(budget /
capital_per_activation_usd)` and the greedy loop at `select.py:81-97` decides
**how many** units to fund. That is "the optimality of the number of
facilities" — the margin HNS explicitly say they are *not* working on, and the
margin on which sunk cost cannot be disregarded.

**Conclusion: the literature supports keeping a capital term, and is silent on
its value.** Our docs should say that rather than implying the papers argue
against one.

### 5.2 A magnitude check on $4m, using Table VII

HNS give us a per-order fixed cost, which is comparable in units to our capital
charge once ours is amortised. Measured today:

```
  annuity factor (10%, 7 years)                     4.8684
  delivery days per year                               312
  selected portfolio                        282 ZCTAs, 3,703,766 parcels/day
  discounted parcels over the horizon              5.626 bn

  capital as charged        282 x $4m = $1,128 m  ->  $0.2005 per parcel
  capital per station       103 x $4m = $  412 m  ->  $0.0732 per parcel
```

HNS's 2018 facility fixed cost is **$0.30 per order** (rent $0.08 + density
$0.22, Table VII), against a total fulfilment cost of $1.11. Ours is a
one-off capital sum amortised, theirs is a recurring rent, so the two are not
the same object and this is a sanity check rather than a validation. But it is
informative that our *capital* line alone, charged per ZCTA, comes to two
thirds of Amazon's entire *fixed operating* cost per order, on a cost base
($1.08/parcel median) roughly equal to theirs. Charged per station it comes to
a quarter of it, which is the more plausible of the two.

Note also Table VII's facility counts: Amazon ran 128 fulfilment centres and 35
sortation centres **nationally** in 2018. `cost/depots.py` places 334 depots
across 11 metros. These are different tiers — delivery stations, not fulfilment
centres — so there is no contradiction, but anyone tempted to validate our
depot count against HNS's Table VII should not.

### 5.3 The cannibalisation question — HNS measure it and get zero

This is the strongest piece of evidence either paper offers on
`cannibalisation_peak`, and it is not currently in our documentation.

`optimize/objective.py:158` reduces the parcels attributed to a selected ZCTA
when neighbouring ZCTAs are also selected:

```python
  parcels = self.annual_parcels * (1.0 - p.cannibalisation_peak * decay)
```

That is a reduction in **total system volume**, because `parcels[sel].sum()` at
`objective.py:162` is what the portfolio is credited with. HNS measure exactly
that quantity in Table VIII and find it is **0.00** — opening three fulfilment
centres in a dense region changes system-wide orders by nothing, absent a tax
change. The 88% they do find is Arizona's *share* of the same orders moving to
California.

And they have a separate, independent reason for expecting that: they tested
whether household spending responds to facility proximity, could not reject
independence (p. 165), and note that Amazon has offered identical shipping
terms to all Prime members irrespective of location since 2005.

So both papers, by different routes, say the same thing. The cannibalisation
measured in this literature is **diversion of a fixed quantity of demand
between the firm's own outlets**. siting-atlas's demand unit is a residential
ZCTA whose parcels are generated by the households living in it
(`cost/daganzo.py`, from `households` x `parcels_per_household_per_week` x an
income scaling). There is no second outlet for those parcels to be diverted to,
because the customer's home does not move.

**Verdict on the prior agent's argument.** The claim in
`optimize/params.py:120-124` — that Holmes cannibalises sales at a store which
walk, whereas we cannibalise volume in a ZCTA which does not, so our peak
"arguably ought to be LOWER than his" — is **correct, and understated**. It is
not a reason to prefer 0.10 over 0.18. It is a reason to doubt that any
non-zero value is well founded under the current specification. HNS Table VIII
turns that from an argument into a measurement.

Measured effect of setting it to zero (same caveat as §6 below):

```
  cannibalisation_peak = 0.18 (current)   282 ZIPs   break-even $1.3431
  cannibalisation_peak = 0.00             313 ZIPs   break-even $1.1788
  Jaccard overlap between the two selections: 0.574
```

Zeroing it moves the break-even margin 12.2% and changes 43% of the portfolio.
It is not a cosmetic parameter.

### 5.4 The functional form has a second, separate problem

`optimize/objective.py:123-126` builds the interaction weight as
`clip(1 - d/radius, 0, 1)` — strictly decreasing in distance. HNS Table VIII
shows the profit and shipping-cost impact of a new facility on existing ones is
**non-monotone** in distance (Washington at 965 miles loses more shipping cost
than Nevada at 399 miles), and they say the non-monotonicity is severe enough to
rule out a standard solution method (p. 181). If we ever do estimate this
interaction rather than assume it, a monotone kernel is the wrong starting
point. Logged here, not acted on.

### 5.5 Discount rate — verified

`beta = 0.95`, printed p. 165, asserted in a subordinate clause with no source.
PARAMETERS.md §7.3's characterisation of both papers is accurate.

---

## 6. A caveat on every measured number above

The portfolio figures in §5.2 and §5.3 were measured on 2026-09-13 while
another agent was concurrently rewriting `src/siting_atlas/cost/depots.py`
(k-means placement replaced by a p-median formulation). Baseline selection size
moved from 330 to 282 during this session for that reason alone, so the "330
ZIPs / $1.32bn" headline in `PARAMETERS.md` §4 is stale — the drift is now
recorded at [`../DECISION_LOG.md`](../DECISION_LOG.md) §4.2. All
rows above were computed in a single process against `cost/depots.py` md5
prefix `d93ae1ecaf` so they are mutually consistent. Re-measure before quoting.

---

## 7. What I did NOT read

**Read in full:**
- §2.2 the network description and the MWPVL catchment rules (p. 153).
- §2.3 Cost Components: Data (pp. 153-154).
- §3.4 Cost Function, the fixed-cost part and eq. (9) (p. 164).
- §3.5 Optimization Problem, eqs. (10)-(11) (pp. 164-165).
- §3.6 Discussion, the willingness-to-pay passage and the sunk-cost passage
  (pp. 165-166).
- §4.3 the results discussion around Tables VI and VII, plus the
  "cost function intercept" limitation (pp. 177-178).
- §4.4 Illustration: California Entry, in full with Table VIII (pp. 180-181).

**Not read, at all:**
- §1 Introduction (pp. 147-153).
- §2.1 Retail Spending and Orders: Data (pp. 152-153). **Note:** PARAMETERS.md
  §6.11 and §6.12 cite comScore spending figures, Table III and Figure 2 from
  this paper. Those citations come from a prior reading and were **not**
  re-verified here.
- §2.4 Sales Taxes: Data, §2.5 Trends: Retail Spending, §2.6 Trends:
  Distribution Network (pp. 155-158), and Tables I and II.
- §3.1 Distribution Network, §3.2 Demand and Revenue Function, §3.3 Order Flow
  (pp. 158-163). I did not read the demand model itself, only the §3.6
  discussion of what it assumes.
- §3.4's shipping and labour cost components (pp. 163-164) beyond noting
  eq. (10). The economies-of-scale parameter gamma in labour cost is mentioned
  in these notes but I did not read its estimation.
- §4.1 Demand and Table III (pp. 165-168).
- §4.2 Order Flow and Labor Demand, Tables IV and V (pp. 168-174).
- §4.3's estimation procedure — the moment-inequality construction, the swap
  design, Bugni-Canay-Shi inference (pp. 174-177). **I read the results tables
  without reading how they were produced.** `docs/METHODS_RESEARCH.md` covers
  the swap design from a prior reading and nothing here revisits it.
- §5 Taxes and Investment, Tables IX and X, Figure 4 (pp. 181-188).
- §6 Conclusion (pp. 188-189).
- The whole Supplemental Appendix, including Online Appendix A, which is where
  the rent construction and the cost-of-goods-sold inference actually live.

**Specifically not verified:**
- Houde, Newberry and Seim (2021), the companion paper containing the
  proximity-independence test quoted in §3. I have only HNS's one-sentence
  summary of their own earlier result.
- Whether MWPVL's square footage figures are accurate, or whether "fixed cost =
  square footage x (rent + congestion)" omits anything material.
- Slattery (2020) on local government subsidies, cited by HNS as the kind of
  location-specific sunk cost they abstract from. That reference is the obvious
  next place to look for an actual dollar figure on opening a facility, and it
  was not pursued.
- Any figure in the paper I did not read, including everything PARAMETERS.md
  currently attributes to Table III or Figure 2.
