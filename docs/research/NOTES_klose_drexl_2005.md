# Notes — Klose & Drexl, Facility location models for distribution system design

*Read in full 2026-09-13, all 26 pages of the copy on disk (20 pages of body
plus 6 of references). These notes exist so nobody has to open the PDF
again.*

---

## 1. Citation and local file

```
  Andreas Klose (a,b) and Andreas Drexl (c)
    (a) Universitaet St. Gallen, 9000 St. Gallen, Switzerland
    (b) Institut fuer Operations Research, Universitaet Zuerich, 8015
        Zuerich, Switzerland
    (c) Christian-Albrechts-Universitaet zu Kiel, Olshausenstr. 40,
        24118 Kiel, Germany
  "Facility location models for distribution system design."
  European Journal of Operational Research.
  Received 1 October 2001; accepted 14 October 2003.
  doi:10.1016/j.ejor.2003.10.031

  Local file:  ../Research/klos04facility.pdf   (26 PDF pages)
```

**A citation caveat, and it is why this file's name and its contents
disagree.** The copy on disk is the ARTICLE IN PRESS proof. Every page
carries that banner and the running head reads "European Journal of
Operational Research xxx (2003) xxx-xxx"; the first page says "(2004)".
There is no volume, issue or page range on the document, and the copyright
line is "2003 Elsevier B.V.". The version of record is

```
  European Journal of Operational Research 162(1):4-29, 2005.
```

Page numbers quoted in these notes are the PROOF's own 1-26, which will not
match the published 4-29. Anything cited in the dissertation should be cited
against the published version and the page re-checked there. The filename
`NOTES_klose_drexl_2005.md` follows the published year; the file on disk is
named `klos04facility.pdf` after the proof year. Both refer to the same
paper.

---

## 2. What the paper is for

A review, not a contribution. It surveys facility location models for
distribution system design and lays them out as a family tree of
mixed-integer programs, so that a modeller can find the formulation that
matches the assumptions they actually have. It is almost entirely
formulations plus pointers to solution methods; there is no data, no
experiment, and no worked example anywhere in it.

For this project that is exactly the right shape of source. We had already
decided (correctly) that k-means was the wrong objective; what we needed was
a principled answer to "then WHICH model", given that our depots have a
throughput cap, no fixed cost, and a downstream cost function that only ever
asks for nearest-depot distance. This paper makes that a decision with a
citation rather than a preference. Sections 4, 5.1 and 5.2 are the ones that
matter; the rest is context and is summarised here so that nobody has to
re-derive which section was relevant.

Its weakness, worth knowing before relying on it: it is a taxonomy of
models, so it tells you what to write down and who has solved it, but it
gives almost no guidance on how well the heuristics work or on which model
is empirically adequate. For that you have to follow the references.

---

## 3. Section-by-section walkthrough

### Section 1 — Introduction (p. 1)

Location is strategic and pervasive: plants, warehouses, stores, offices,
schools, hospitals, fire stations. The literature has produced "an ever
expanding family of models" ranging "in complexity from simple linear,
single-stage, single-product, uncapacitated, deterministic models to
non-linear probabilistic models". Simulation-based work is deliberately
excluded for brevity. The road map: section 2 classifies, section 3 does
continuous models, section 4 network models, section 5 mixed-integer models,
section 6 applications.

### Section 2 — Types of models (p. 2)

Nine classification dimensions, given as a numbered list. This is the most
useful page in the paper for deciding where you are, so it is reproduced in
substance:

```
  1  TOPOGRAPHY of the candidate set:  models in the plane (continuous)
     / network location models / discrete, i.e. mixed-integer.  Each
     subclass has its own distance metric.
  2  OBJECTIVE:  MINSUM ("minisum") minimises average distance; MINMAX
     ("minimax") minimises the maximum.  Minsum dominates private-sector
     problems, minmax public-sector ones.
  3  CAPACITY:  uncapacitated models put no restriction on demand
     allocation.  With capacities, allocation must be done carefully, and
     one must decide SINGLE- vs MULTIPLE-SOURCING.
  4  STAGES:  single-stage covers one echelon explicitly; multi-stage
     models the flow through a hierarchy.
  5  PRODUCTS:  single-product if demand, cost and capacity can be
     aggregated into one homogeneous good.
  6  DEMAND ELASTICITY:  usually demand is assumed inelastic, i.e.
     independent of the location decision.  If elastic, cost minimisation
     must be replaced by e.g. revenue maximisation.
  7  TIME:  static (one representative period) vs dynamic.
  8  UNCERTAINTY:  deterministic vs probabilistic input.
  9  ROUTING:  classical models cost each supply-demand pair in isolation.
     If demand is served by delivery TOURS, cost cannot be decomposed that
     way, and combined location/routing models are needed.
```

Point 9 is worth flagging for us on sight — see section 6.5 below.

### Section 3 — Continuous location models (p. 3)

Two defining attributes: the solution space is the whole plane, and distance
is Manhattan, Euclidean, or `l_p`.

The **single-facility Weber problem (SWP)**: choose `(x,y)` to minimise the
weighted sum of Euclidean distances to `m` demand points at `(a_k, b_k)`:

```
   v(SWP) = min    SUM   w_k d_k(x,y),
            (x,y)  k in K

   where  d_k(x,y) = sqrt( (x - a_k)^2 + (y - b_k)^2 )
```

Solved by Weiszfeld's (1937) iterative gradient-like scheme, improved by
Miehle (1958). Hundred-year pedigree; named for Weber (1909); history in
Wesolowsky (1993).

The **multi-source Weber problem (MWP)**, `1 < p < |K|` facilities plus
allocation, is NP-hard, and is a nonlinear mixed-integer program:

```
   v(MWP) = min  SUM     SUM_{j=1..p}  ( w_k d_k(x_j,y_j) ) z_kj
                 k in K

   s.t.  SUM_{j=1..p} z_kj = 1      for all k in K
         z_kj in {0,1},             for all k in K, j = 1..p
         x, y in R^p
```

Exact methods reformulate it as a set partitioning problem and solve the LP
relaxation by column generation (Rosing 1992b; du Merle et al. 1999). Fast
heuristics: Taillard (1996), Hansen et al. (1998), Brimberg et al. (2000).
The `p = 2` case has its own literature (Ostresh 1973, Drezner 1984, Rosing
1992b, Chen et al. 1998).

Also mentioned in passing: barriers (Hamacher & Nickel 1994; Klamroth 2001),
undesirable/obnoxious facilities where minimum distance is MAXIMISED
(Melachrinoudis 1988; Erkut & Neuman 1989; Brimberg & Mehrez 1994), and
minmax location models (Krarup & Pruzan 1979; Love et al. 1988 p. 113 ff.;
Francis et al. 1992 p. 217 ff.).

### Section 4 — Network location models (pp. 3-5)

Distances are shortest paths in a graph. "Nodes represent demand points and
potential facility sites correspond to a subset of the nodes and to points
on arcs."

The **p-median problem (PMP)** is the network analogue of the MWP, and this
is the formulation we adopted. `K` is the node set, `J` a subset of `K` of
potential facilities, `w_k d_kj` the weighted distance, `y_j = 1` if node
`j` is chosen, `z_kj = 1` if demand node `k` is assigned to site `j`:

```
   v(PMP) = min  SUM      SUM     ( w_k d_kj ) z_kj                       (1a)
                 k in K   j in J

   s.t.  SUM_{j in J} z_kj = 1          for all k in K                    (1b)
         z_kj - y_j <= 0                for all k in K, j in J            (1c)
         SUM_{j in J} y_j = p                                             (1d)
         z_kj, y_j in {0,1}             for all k in K, all j in J        (1e)
```

Their reading of the constraints, which is what one wants when writing this
up: "Constraints (1b) guarantee that demand is satisfied, inequalities (1c)
couple the location and the assignment decision, and constraint (1d) fixes
the number of selected facilities to p." Solution methods pointed at:
Christofides & Beasley (1982), Hanjoul & Peeters (1985), Beasley (1993),
Klose (1993).

Immediately before the model, the sentence that carries the whole
node-restriction argument:

> "In the p-median problem p facilities have to be located on a graph such
> that the sum of distances between the nodes of the graph and the facility
> located nearest is minimized. Hakimi (1964, 1965) has shown that it is
> sufficient to restrict the set of potential sites to the set of nodes in
> the case of concave distance functions."
> — section 4, p. 4

Note "(1964, 1965)", and note the condition "concave distance functions".
See `NOTES_hakimi_1964.md` section 6.2.

The **p-centre problem (PCP)** minimises the maximum weighted distance
instead, and it is where node restriction FAILS:

```
   v(PCP) = min r                                                         (2a)
   s.t.  r - SUM_{j in J} w_k d_kj z_kj >= 0     for all k in K           (2b)
         SUM_{j in J} z_kj = 1                   for all k in K           (2c)
         z_kj - y_j <= 0                         for all k in K, j in J   (2d)
         SUM_{j in J} y_j = p                                             (2e)
         z_kj, y_j in {0,1}                                               (2f)
```

> "Unfortunately, for the p-center problem we cannot restrict the set of
> potential facility sites to the set of nodes because the maximum of
> concave distance functions is no concave function any more. Fortunately,
> it suffices to consider a finite set of points on the arcs."
> — section 4, p. 4

Those extra points are the intersection points `q` where
`w_i d_iq = w_k d_kq` for two nodes `i`, `k`.

The PCP transforms into a sequence of covering problems (Handler 1979;
Domschke & Drexl 1996). The **set covering problem (SCP)**, with
`a_kj = 1` iff `w_k d_kj < r`:

```
   v(SCP) = min  SUM_{j in J} y_j                                         (3a)
   s.t.  SUM_{j in J} a_kj y_j >= 1        for all k in K                 (3b)
         y_j in {0,1}                      for all j in J                 (3c)
```

The rest of section 4 is **competitive location**: Hotelling (1929); surveys
in Eiselt et al. (1993), Dobson & Karmarkar, Bauer et al. (1993). Two firms
`A` and `B` locate `r` and `p` facilities; customers always pick the nearest
and ties split demand. Given `A_r`, `B` solves a `(p|A_r)`-MEDIANOID
problem, called the maximum capture problem when restricted to nodes
(ReVelle 1986). Anticipating `B`, firm `A` solves an `(r|p)`-CENTROID
problem, which is a minmax problem. Both are NP-hard if `r` and `p` are not
fixed in advance; given `p`, the medianoid is polynomial on the node set
(Benati & Laporte 1994).

### Section 5 — Mixed-integer programming models (pp. 5-19)

Preamble (p. 5): discrete models "just use input parameters without asking
where they come from", whereas network models take the candidate structure
and metric seriously. Their own rough classification (p. 6): single- vs
multi-stage; uncapacitated vs capacitated; multiple- vs single-sourcing;
single- vs multi-product; static vs dynamic; and with or without routing.

#### 5.1 Uncapacitated, single-stage models (pp. 6-8)

The **uncapacitated facility location problem (UFLP)**, a.k.a. the simple
plant location problem, trades fixed operating cost `f_j` against variable
delivery cost `c_kj`:

```
   v(UFLP) = min  SUM     SUM    c_kj z_kj  +  SUM    f_j y_j             (4a)
                  k in K  j in J                j in J

   s.t.  SUM_{j in J} z_kj = 1            for all k in K                  (4b)
         z_kj - y_j <= 0                  for all k in K, j in J          (4c)
         0 <= z_kj <= 1, 0 <= y_j <= 1                                    (4d)
         y_j in {0,1}                     for all j in J                  (4e)
```

Aggregating (4c) to `SUM_k z_kj <= |K| y_j` gives a compact but much weaker
LP relaxation. Cornuejols and Thizy (1982) showed (4b)/(4c) cover all clique
cuts, which is why the disaggregated form gives a tight bound.
Branch-and-bound via dual ascent: Erlenkotter (1978), Koerkel (1989),
Goldengorin et al. (2003). Benders' inequalities in a Lagrangean ascent:
Guignard (1988). Approximation: rounding and filtering give 3.16 (Lin &
Vitter 1992; Shmoys et al. 1997), improved to 2.4 and 1.74 (Guha & Khuller
1998; Chudak 1999), with a PTAS for Euclidean UFLP (Arora et al. 1998).

Then the two relationships this project needed. First, the exact
relationship between the PMP and the UFLP:

> "Obviously, the p-median problem (1) and the UFLP are close to each other.
> While the number of facilities is fixed in the p-median problem, the
> number of open depots is part of the UFLP solution. Both models can be
> combined if cardinality constraints,
>
>     p_L <= SUM_{j in J} y_j <= p_U                                   (5)
>
> are added to (4). Usually the outcome is called account location problem
> or generalized p-median problem."
> — section 5.1, p. 6

Second, the **aggregate capacity constraint** — the pivot of our
formulation choice. With `s_j > 0` the maximum capacity of depot `j` and
`d(K) = SUM_{k in K} d_k` total demand:

```
   SUM_{j in J} s_j y_j  >=  d(K)                                          (6)
```

> "ensures that facilities open in a feasible solution have enough capacity
> in order to satisfy total demand. Adding constraint (6) to the UFLP,
>
>     v(APLP) = min { SUM SUM c_kj z_kj + SUM f_j y_j : (4b)-(4e) and (6) }  (7)
>
> yields the aggregate capacity plant location problem (APLP)."
> — section 5.1, pp. 6-7

And the sentence that says how seriously to take it:

> "The APLP is not important as a stand-alone model but it has a dominant
> role as a relaxation when solving models presented in Section 5.2."
> — section 5.1, p. 7

Exact algorithms for the APLP: Ryu & Guignard (1992b), Thizy (1994), Klose
(1998).

The remainder of 5.1 is combinatorial relatives: the set partitioning
problem SPaP (8a-8c), the set packing problem SPP (9a-9c), and the **maximal
covering location problem (MCLP)**:

```
   v(MCLP) = max  SUM_{k in K} w_k z_k                                    (10a)
   s.t.  SUM_{j in J} a_kj y_j - z_k >= 0       for all k in K            (10b)
         SUM_{j in J} y_j = p                                             (10c)
         z_k, y_j in {0,1}                                                (10d)
```

with the neat observation (p. 8) that the MCLP "is equivalent to the
p-median problem with the special 'distance' measure `d_kj = (1 - a_kj) w_k`".
Pages 7-8 then work through the chain of transformations UFLP -> SPaP ->
SPP and back to SCP, citing Guignard (1980), Cho et al. (1983), Cornuejols &
Thizy (1982), Krarup & Pruzan (1983) for the polyhedral motivation.

#### 5.2 Capacitated, single-stage models (pp. 8-11)

The section that decides what we are giving up. Adding

```
   SUM_{k in K} d_k z_kj  <=  s_j y_j        for all j in J                (11)
```

to the UFLP — "limiting transshipments SUM_k d_k z_kj for the depots
selected (y_j = 1) to their capacity s_j" — turns it into the **capacitated
facility location problem (CFLP)**. The extended formulation with its
constraints labelled by letter, which is how the rest of the section refers
to them:

```
   v(CFLP) = min  SUM SUM c_kj z_kj  +  SUM f_j y_j

   s.t.  SUM_{j in J} z_kj = 1                     for all k in K       (D)
         SUM_{k in K} d_k z_kj - s_j y_j <= 0      for all j in J       (C)
         z_kj - y_j <= 0                           for all k, j         (B)
         SUM_{j in J} s_j y_j >= d(K)                                   (T)
         SUM_{j in J_q} z_kj <= 1                  for all k, q in Q    (U)
         0 <= z_kj <= 1,  0 <= y_j <= 1                                 (N)
         y_j in {0,1}                                                   (I)
```

(T) is the aggregate capacity constraint (6) again, now redundant but
useful for tightening relaxations. (U) are "clique constraints" over a
partition `{J_q : q in Q}` of the sites, implied by (D) but useful when (D)
is relaxed.

Pages 9-10 are a dense review of Lagrangean bounds following Cornuejols et
al. (1991): notation `Z_R^S` for the bound when constraint set `S` is
ignored and `R` is dualised, and `Z_{R1/R2}` for Lagrangean decomposition.
Their Theorem 1 gives

```
   Z^BIU <= Z^IU <= Z^TU_C <= Z^U_C <= Z,   Z^IU <= Z^U_D <= Z^U_C,
   and   Z^BIU <= Z^U_C <= Z^U_D
```

and their Theorem 2 a chain of equalities for the decomposition bounds. The
practical conclusions: `Z^U_{D/TC}` can be had by Lagrangean substitution
(Chen & Guignard 1998), cutting the dual variables from `|K||J| + |J|` to
`2|J|`; the interesting bounds are `Z^U_D`, `Z_C`, `Z^U_{D/TC}` and `Z^T_D`;
`Z^U_{D/TC}` can be discarded as no stronger than `Z_C` and harder.
Column-generation computation in Klose & Drexl (2001).

Then the assumption that matters most to us:

> "In the CFLP demand d_k can be supplied from more than one depot. Given a
> certain set of depots the CFLP reduces to a simple transportation problem.
> Apparently, this implies transportation cost being proportional to
> shipment size. In many practical settings this assumption does not hold
> and, moreover, it is required that each customer is satisfied from exactly
> one depot. In this case additional constraints
>
>     z_kj in {0,1}        for all k in K, j in J                      (12)
>
> yield a pure integer program, well-known as capacitated facility location
> problem with single sourcing (CFLPSS)."
> — section 5.2, p. 10

And the cost of that:

> "Unfortunately, single sourcing constraints make the problem much harder
> to solve. For a given set O of open depots an optimal solution of the
> NP-hard generalized assignment problem (GAP)
>
>     v(GAP) = min  SUM_{k in K} SUM_{j in O} c_kj z_kj                 (13a)
>     s.t.  SUM_{j in O} z_kj = 1              for all k in K           (13b)
>           SUM_{k in K} d_k z_kj <= s_j       for all j in O           (13c)
>           z_kj in {0,1}                      for all k in K, j in O   (13d)
>
> provides a minimum cost assignment of customers to depots."
> — section 5.2, p. 10

Closing verdict of the section, and it is blunt:

> "Without surprise it is very difficult to calculate an exact solution for
> instances of realistic size."
> — section 5.2, p. 10

Heuristic literature listed: Lagrangean/dual decomposition (a dozen
citations from Geoffrion & McBride 1978 to Diaz & Fernandez 2001), primal-
dual (Van Roy 1986; Wentges 1994, 1996), tabu search (Gruenert 2002),
approximation algorithms (Shmoys et al. 1997; Guha & Khuller 1998; Korupolu
et al. 1998; Chudak & Williamson 1999; Chudak & Shmoys 1999), GRASP and tabu
for CFLPSS (Delmaire et al. 1999), cyclic-transfer local search (Scaparra
2002), and metaheuristics surveyed in Diaz (2001).

#### 5.3 Multi-stage models (pp. 11-13)

When can you ignore the upper echelon? Only if "higher level nodes have a
sufficiently high capacity and handling costs as well as transshipment costs
associated with these nodes are proportional to the amount of items reloaded
and shipped". Otherwise the layers must be located simultaneously.

The **two-stage capacitated facility location problem (TSCFLP)** adds
suppliers `i in I` with capacity `p_i` and transshipment cost `t_ij`:

```
   v(TSCFLP) = min SUM SUM t_ij x_ij + SUM SUM c_kj z_kj + SUM f_j y_j   (14a)
   s.t.  (4b)-(4e), (6) and (11),
         SUM_{j in J} x_ij <= p_i                for all i in I          (14b)
         SUM_{i in I} x_ij = SUM_{k in K} d_k z_kj   for all j in J      (14c)
         x_ij - p_i y_j <= 0                     for all i, j            (14d)
         x_ij >= 0                                                       (14e)
```

(14c) are flow conservation; (14d) redundant but tightening. If every `p_i`
covers total demand, the TSCFLP collapses to the CFLP or CFLPSS.

An alternative PATH-VARIABLE formulation uses `w_ijk`, the fraction of
demand `d_k` routed `i -> j -> k`, with `q_ijk = t_ij d_k + c_kj`. Worth
knowing because their comment generalises: the path form can express costs
that depend on both ends of the route, but the arc form "is advantageous if
the cost q_ijk can be split into two parts ... because it has far fewer
decision variables while the values of the LP-relaxations of both models are
identical."

Generalised to the **two-level capacitated facility location problem
(TLCFLP)** with fixed costs `g_i` on the upper level, then restated in path
variables as (15a)-(15j). Their note on (15f) versus (4c) is the one subtle
point: the path form's left-hand side "covers the fraction of demand d_k
being shipped to k in K indirectly from i in I", a term the arc form cannot
express because the two stages' flows are modelled independently.

#### 5.4 Multi-product models (pp. 14-15)

Needed when products make different claims on the same capacity. Two
further cases: "multi-type" models, where different facility types can be
distinguished at a location, and "multi-activity" models, where fixed cost
depends on which product a location provides. The **multi-commodity /
multi-activity uncapacitated facility location problem (MUFLP)** is given as
(16a)-(16f) with `z_ij = 1` if product `i` is provided at depot `j`, `g_ij`
the fixed product cost, and coupling constraints (16c)/(16d) that "forbid to
assign products to closed depots and to deliver product i to node k from
depot j if product i is unavailable at the depot". Multi-type adds
`SUM_{i in I} z_ij <= 1`. Gao and Robinson Jr. (1992, 1994) show the MUFLP
is a special two-stage hierarchical model.

#### 5.5 Dynamic models (pp. 15-16)

Opening and closing costs `g^o_ij`, `g^c_ij` over periods `t = 1..T` give a
quadratic integer program DUFLP, linearised with `u_{t-1,t,j} = y_{t-1,j}
y_{tj}` and the three standard constraints. Supplementary constraints force
a depot to stay open (closed) for at least `tau_1` (`tau_0`) periods. A
simplified version (17a)-(17e) allows each depot to be opened or closed at
most once, using discounted cash flows `F_tj`.

Their own verdict, which is unusually frank for a survey and is the reason
we are not going anywhere near this:

> "Dynamic models seem to be adequate in light of factors changing over time.
> However, their practical relevance seems to be limited. First, a 'right'
> planning horizon does not exist. Second, the amount of data required is
> enormous. Third, 'disaggregated' models are more sensitive to
> parameter/data adjustments than aggregated ones. Fourth, the complexity of
> dynamic models increases—dramatically—compared with static models and,
> hence, the chances to solve such models decrease."
> — section 5.5, p. 16

#### 5.6 Probabilistic models (pp. 16-17)

Queueing location models (Berman & Larson 1985). A stochastic p-median
(Mirchandani et al. 1985) over states `i in I` with probabilities `pi_i`:

```
   min  SUM SUM SUM pi_i c_ikj z_ikj                                     (18a)
   s.t. SUM_{j in J} z_ikj = 1                                           (18b)
        z_ikj - y_j <= 0                                                 (18c)
        SUM_{j in J} y_j = p                                             (18d)
        z_ikj, y_j in {0,1}                                              (18e)
```

which reduces to the deterministic PMP (1) by relabelling `z_lj` with
`l = i + |I|(i-1)` — but note their warning that for the CFLP the capacity
constraints PREVENT that reduction. Same frankness as 5.5:

> "Unfortunately, stochastic models require a large amount of data in order
> to adapt empirically observed distributions to theoretical ones. Usually
> for strategic facility location problems such information is not
> available."
> — section 5.6, p. 17

Their recommendation is scenario analysis with a regret measure (Owen &
Daskin 1998; Barros et al. 1998) — which is what the project already does
with `SCENARIOS` in `cost/params.py`.

#### 5.7 Hub location models (pp. 17-18)

Hub-and-spoke networks; flow between every pair of nodes; `alpha` in
`(0,1]` discounts the inter-hub leg. The uncapacitated hub location problem
UHLP is (19a)-(19e). "Apparently, if the set of hubs is known then a
shortest path problem remains to be solved. Otherwise, the problem is
NP-hard." Applications: airlines, the Civil Aeronautics Board, emergency
services, postal delivery (Ernst & Krishnamoorthy 1996).

#### 5.8 Routing location models (p. 18)

The section that names our biggest modelling approximation.

> "The application of the location models discussed so far requires that the
> cost c_kj for allocating the demand d_k of a customer k in K to a depot
> can be allocated independently of the allocation of the other demand
> points. A very complex form of service cost depending on each others [sic]
> costs arises if customers are satisfied within routes covering several
> customers simultaneously. In this case location and routing decisions are
> strongly interrelated."
> — section 5.8, p. 18

Three reasons the combination is hard: the optimisation problems become very
complicated; the planning horizons of the two subproblems differ; "facility
location requires to aggregate customers while routing does not".
References: Laporte et al. (1983), Simchi-Levi & Berman (1988), Branco &
Coelho (1990), Gourdin et al. (2000), Jacobsen & Madsen (1980), Perl &
Daskin (1985), Nagy & Salhi (1996), Bruns & Klose (1996), Klose (2001),
Aykin (1995a). Bruns, Klose & Staehly (2000) on "Restructuring of Swiss
parcel delivery services" is the closest thing in the reference list to our
application.

#### 5.9 Multi-objective location models (pp. 18-19)

Periodic cost, investment level, service level, balanced capacity use, and
minimal disruption to the current network all compete. The usual dodge is
to treat cost as primary and the rest as soft constraints, "Such an approach
does, however, not guarantee that pareto-optimal solutions are found."
Discrete multi-objective location is "a topic of current research". Current
et al. (1990); ReVelle (1993); Heller et al. (1989); ReVelle & Laporte
(1996); Fernandez & Puerto (2003).

### Section 6 — Applications (pp. 19-20)

A list of problems that are location problems in disguise. Abbreviated:

```
  cluster analysis       Mulvey & Crowder (1979) model clustering AS a
                         p-median problem.  (Note the direction: the
                         location model is the general one and clustering
                         is the special case, not the reverse.)
  bank accounts          which accounts to use to pay suppliers; the
                         "account location problem", a UFLP with the
                         cardinality constraint (5) -- Cornuejols et al.
                         (1977).  The reverse is the lock box problem.
  vendor selection       Current & Weber (1994), via UFLP and CFLP.
  offshore platforms     Hansen et al. (1992, 1994), capacitated multi-type.
  database location      Fisher & Hochbaum (1980), extended UFLP.
  concentrator location  telecom access networks; Mirzaian (1985),
                         Pirkul (1987), Chardaire (1999).
  index selection        choosing database indexes; formulated as a UFLP
                         (4) -- Caprara & Salazar (1995, 1999).
```

### References (pp. 20-26)

Roughly 200 entries. Three worth knowing the exact form of:

```
  Hakimi, S.L., 1964. Optimum locations of switching centers and the
    absolute centers and medians of a graph. Operations Research 12,
    450-459.
  Hakimi, S.L., 1965. Optimum distribution of switching centers in a
    communication network and some related graph theoretic problems.
    Operations Research 13, 462-475.
  Teitz & Bart does NOT appear in this reference list.
```

That last point matters: the vertex-substitution heuristic we implemented is
standard in the p-median literature but is not one this survey cites. The
p-median solution methods it does cite are Christofides & Beasley (1982),
Hanjoul & Peeters (1985), Beasley (1993) and Klose (1993), all of which are
Lagrangean or tree-search. If the heuristic needs a citation in the
dissertation, Teitz & Bart (1968) has to come from somewhere else.

---

## 4. Load-bearing quotations

Collected for convenience; each also appears in context above.

> "Hakimi (1964, 1965) has shown that it is sufficient to restrict the set
> of potential sites to the set of nodes in the case of concave distance
> functions."
> — section 4, p. 4

> "Constraints (1b) guarantee that demand is satisfied, inequalities (1c)
> couple the location and the assignment decision, and constraint (1d) fixes
> the number of selected facilities to p."
> — section 4, p. 4

> "While the number of facilities is fixed in the p-median problem, the
> number of open depots is part of the UFLP solution."
> — section 5.1, p. 6

> "The aggregate capacity constraint
>     SUM_{j in J} s_j y_j >= d(K)                                      (6)
> where s_j > 0 denotes the maximum capacity of depot j and
> d(K) = SUM_{k in K} d_k total demand, ensures that facilities open in a
> feasible solution have enough capacity in order to satisfy total demand."
> — section 5.1, p. 6

> "The APLP is not important as a stand-alone model but it has a dominant
> role as a relaxation when solving models presented in Section 5.2."
> — section 5.1, p. 7

> "If depots have scarce capacity, constraints
>     SUM_{k in K} d_k z_kj <= s_j y_j      for all j in J             (11)
> limiting transshipments ... have to be added. Hence, in the case of scarce
> capacity the UFLP mutates to the capacitated facility location problem
> (CFLP)."
> — section 5.2, p. 8

> "In the CFLP demand d_k can be supplied from more than one depot. ... In
> many practical settings this assumption does not hold and, moreover, it is
> required that each customer is satisfied from exactly one depot."
> — section 5.2, p. 10

> "Unfortunately, single sourcing constraints make the problem much harder
> to solve."
> — section 5.2, p. 10

> "Without surprise it is very difficult to calculate an exact solution for
> instances of realistic size."
> — section 5.2, p. 10

> "Objectives may be either of the minsum or the minmax type. Minsum models
> are designed to minimize average distances while minmax models have to
> minimize maximum distances."
> — section 2, p. 2, point 2

> "In classical models the quality of demand allocation is measured on
> isolation for each pair of supply and demand points. Unfortunately, if
> demand is satisfied through delivery tours then, for instance, delivery
> cost cannot be calculated for each pair of supply and demand points
> separately."
> — section 2, p. 2, point 9

---

## 5. The formulations we actually depend on, restated exactly

```
  p-MEDIAN (PMP), section 4, equations (1a)-(1e)
  --------------------------------------------------------------------
    min   SUM_{k in K} SUM_{j in J} (w_k d_kj) z_kj                   (1a)
    s.t.  SUM_{j in J} z_kj = 1                    for all k in K     (1b)
          z_kj - y_j <= 0                          for all k, j       (1c)
          SUM_{j in J} y_j = p                                        (1d)
          z_kj, y_j in {0,1}                       for all k, j       (1e)

  AGGREGATE CAPACITY, section 5.1, equation (6)
  --------------------------------------------------------------------
          SUM_{j in J} s_j y_j >= d(K)                                 (6)

  PER-DEPOT CAPACITY, section 5.2, equation (11)  -- NOT IMPOSED BY US
  --------------------------------------------------------------------
          SUM_{k in K} d_k z_kj <= s_j y_j         for all j in J     (11)

  SINGLE SOURCING, section 5.2, equation (12)     -- implied by (1e)
  --------------------------------------------------------------------
          z_kj in {0,1}                            for all k, j       (12)
```

---

## 6. What this means for siting-atlas

### 6.1 The model we chose, and why

**p-median, equations (1a)-(1e), with `p` fixed by the aggregate capacity
constraint (6) rather than by the per-depot constraint (11).**

Instantiated on our problem:

```
  K   the ZCTAs of one CBSA (up to 848 in the pilot's largest metro)
  J   = K.  Candidates are the ZCTA internal points themselves.
  w_k daily parcels in ZCTA k, from DaganzoCostModel.daily_parcels
  d_kj great-circle miles, cost/daganzo.py haversine_miles
  p   = ceil( SUM_k w_k / parcels_per_depot_per_day ),
      i.e. constraint (6) with identical s_j = 40,000
```

Three reasons this is the right pick rather than the CFLP, in the order they
should be given in a defence.

**First, the objective is the one we bill.** `cost/daganzo.py:159` computes
the line-haul term as `2 * L / stops_per_tour`, linear in `L`. Equation (1a)
is linear in `d_kj`. They are the same objective. k-means minimises squared
distance and was not.

**Second, the downstream code cannot consume a capacitated solution.**
`DepotNetwork.distance_miles` returns the distance to the NEAREST depot, and
`daganzo.linehaul_miles` asks for nothing else. Nearest-depot assignment is
precisely what constraints (1b) and (1c) produce at a p-median optimum. A
CFLP solution's assignment is in general NOT nearest-depot — that is the
whole point of (11) — so solving a CFLP and then throwing its assignment
away would give us a placement optimised for one allocation and a cost
computed under another. That is the same category of error as the k-means
bug this work exists to fix, and it would have required changing
`daganzo.py`, which is out of scope.

**Third, there is no fixed cost to trade against distance.**
`cost/params.py` has no `f_j`. Without it the UFLP (4a)-(4e) is degenerate —
it would open every depot — so the depot count must be fixed exogenously,
which is (1d), which is the p-median. Klose and Drexl's own framing at p. 6
is exactly this: fixed `p` is the p-median, endogenous count is the UFLP.
Adding the cardinality constraint (5) to the UFLP gives the "generalized
p-median problem", which is where we would go if a fixed cost were ever
added.

### 6.2 What we are giving up, stated plainly

Our depots DO have a throughput, so the textbook-correct model is the CFLP
of section 5.2, or strictly the CFLPSS once single sourcing (12) is added —
and single sourcing IS forced on us, because `distance_miles` takes a
minimum. Four consequences:

```
  1  Constraint (11) is not enforced.  A depot may be assigned more than
     40,000 parcels/day while a neighbour sits idle.  Only the aggregate
     (6) holds.  MEASURED below, and the violation is large.
  2  Because a capacity-feasible network must push overflow demand to a
     more distant depot, our line haul is a LOWER BOUND on the line haul
     of a feasible network.  The model UNDERSTATES cost wherever demand
     is bunched, and understates it most in the densest ZCTAs -- which
     are the ones at the top of the published ranking.
  3  Even with the depots fixed, restoring feasibility means solving the
     GAP (13a)-(13d), which is NP-hard (section 5.2, p. 10).
  4  We inherit section 5.8 wholesale: our c_kj is computed per ZCTA in
     isolation, while real delivery is by tour.  Daganzo's continuous
     approximation is our answer to that and it is an approximation, not
     a solution.  Klose and Drexl name this gap explicitly at p. 18.
```

Point 2 is the one to put in front of a reader. It is a directional bias in
the headline figure, not a symmetric error.

**How big is the violation? Bigger than "a caveat".** Assigning every pilot
ZCTA to its nearest depot and totalling the load:

```
                            k-means      p-median
  ------------------------------------------------
  depots                        334           334
  depots over 40,000/day    128 (38%)     139 (42%)
  heaviest depot               190,898       142,386
     as a multiple of s_j        4.77x         3.56x
  demand above capacity      3,781,696     2,703,572
     as a share of demand        28.8%         20.6%
```

A fifth of all demand sits above the throughput of the depot nearest to it.
The aggregate constraint (6) is satisfied by construction and is nowhere
near sufficient: (6) says the network has enough capacity IN TOTAL, and says
nothing about whether it is in the right places. Two honest readings, and
both should be stated:

* the p-median is a **substantial** relaxation here, not a technicality, and
  the line-haul figures in 6.3 are correspondingly optimistic;
* the switch to p-median nevertheless **reduces** the infeasibility on every
  measure — worst overload 4.77x to 3.56x, excess demand 28.8% to 20.6% —
  so it moves towards a capacity-feasible network even though it does not
  target one.

The alternative reading, which should also be on the table, is that
`parcels_per_depot_per_day = 40,000` is simply too low for the densest
metros and the real constraint is softer than a hard cap. Distinguishing
those two possibilities requires the CFLP, not more analysis of this model.

A note on the framing that makes this defensible rather than sloppy: what we
solve is the p-median relaxation of the CFLP in which (11) is replaced by
(6). That is not an ad-hoc simplification; (6) is the constraint Klose and
Drexl single out as the basis of the APLP (7), and the APLP is described at
p. 7 as having "a dominant role as a relaxation when solving" the
capacitated models. We are using a relaxation the survey itself identifies
as the standard one, and we should say that rather than "we ignored
capacity".

### 6.3 Measured effect of the change

Pilot, 2024Q1, 2,333 ZCTAs, 11 CBSAs, baseline parameters.

```
                          k-means      p-median      change
  ----------------------------------------------------------
  depots                      334           334         0
  billed parcel-miles  36,552,461    33,156,338     -9.29%
  median $/parcel          1.0860        1.0811     -0.45%
  mean   $/parcel          1.1638        1.1736     +0.85%
  p90    $/parcel          1.3571        1.4099     +3.89%
  median line-haul mi      3.9645        4.0200     +1.40%
  mean   line-haul mi      5.4252        5.9373     +9.44%
  p90    line-haul mi     10.1426       12.4387    +22.64%

  Spearman rho between the two ZCTA rankings        0.8881
  Kendall tau                                       0.7330
  cheapest-50 overlap                              22 / 50
```

The two rows to read together are "billed parcel-miles -9.29%" and "p90
line-haul +22.64%". They are not in conflict: the p-median objective is
DEMAND-WEIGHTED, so depots move towards volume, high-volume ZCTAs get closer
and low-volume ones get further. The unweighted distribution of line haul
gets worse while the quantity the network actually pays for gets better by
9%. That is correct behaviour and it is also more realistic — a real
operator sites for volume, so a thinly populated ZCTA genuinely is a long
way from the nearest delivery station.

Spearman rho of 0.888 is the number to put in front of the user. For
comparison, `cost/params.py` records `parcels_per_depot_per_day` as "the
LARGEST rank mover in the model (Spearman 0.90)". Correcting the objective
moves the ranking about as much as the single most rank-sensitive parameter
in the entire model does across its whole plausible range.

Solver quality, against a Lagrangean lower bound obtained by relaxing (1b)
(the classical p-median relaxation, cf. Beasley 1993):

```
   cbsa     n     p        heuristic   lower bound   gap
   ---------------------------------------------------------
   12420    88    15        1,940,488     1,905,506   1.84%
   14260    40     4          871,790       860,447   1.32%
   16980   378    52        5,544,036     5,402,624   2.62%
   19740   131    18        2,171,023     2,146,893   1.12%
   33100   181    31        3,053,265     3,033,326   0.66%
   34980   108    12        2,451,438     2,451,438   0.00%  <- proved optimal
   35620   848   109        7,690,437     7,641,070   0.65%
   38060   161    27        3,423,390     3,423,390   0.00%  <- proved optimal
   41860   175    29        2,300,480     2,297,149   0.15%
   41940    62    12          978,859       971,587   0.75%
   42660   161    25        2,731,132     2,729,893   0.05%
   ---------------------------------------------------------
   TOTAL                   33,156,338    32,847,904   0.89%
```

### 6.4 Where this is implemented

```
  src/siting_atlas/cost/depots.py:91    solve_pmedian -- greedy add plus
                                        vertex substitution
  src/siting_atlas/cost/depots.py:203   DepotNetwork.fit -- one p-median
                                        per CBSA, p from constraint (6)
  src/siting_atlas/cost/depots.py:263   distance_miles -- the (1b)/(1c)
                                        nearest-depot assignment
  src/siting_atlas/cost/daganzo.py:159  the linear objective it matches
  src/siting_atlas/cost/params.py:215   parcels_per_depot_per_day, the s_j
  tests/unit/test_depots_pmedian.py     objective and solver
  tests/unit/test_depots_network.py     capacity caveat and interface
```

### 6.5 What to read next, if the model has to improve

In priority order, with the section that motivates each:

1. **Section 5.8, routing location.** The largest unmodelled interaction and
   the one Klose and Drexl flag hardest. Bruns, Klose & Staehly (2000),
   "Restructuring of Swiss parcel delivery services", OR-Spektrum 22:285-302,
   is the nearest application in the reference list.
2. **Section 5.2, the CFLP.** If the capacity violation in 6.2 turns out to
   be large, the route in is Lagrangean relaxation of (C) with the aggregate
   constraint (T) retained — the `Z^T_D` bound, which they say "may be
   advantageous, if the set of potential plant locations is large and if the
   capacity constraints are not very tight" (p. 10). That describes us.
3. **Section 5.1, equation (5).** If a fixed cost per delivery station ever
   enters `params.py`, switch to the generalised p-median and let the depot
   count be decided rather than asserted.
4. **Section 5.6.** Their endorsement of scenario analysis over stochastic
   programming supports what `cost/params.py::SCENARIOS` already does; it is
   a citation for a choice already made, not a change.

---

## 7. What I did NOT read, or did not verify

* **Every reference.** About 200 of them, none consulted. In particular
  Hakimi (1965), on which the p > 1 node restriction rests; Cornuejols et
  al. (1991), whose Theorems 1 and 2 I have transcribed but not checked;
  Beasley (1993), the Lagrangean p-median method my bound calculation is
  modelled on from general knowledge rather than from that paper.
* **Nothing was skipped in the body.** All 20 body pages were read. But the
  following I read and did not verify or fully absorb:
  * the Lagrangean bound orderings on pp. 9-10 (`Z^BIU <= Z^IU <= ...`). I
    transcribed the chains; I did not check a single inequality, and I do
    not have independent intuition for why `Z^U_{D/TC}` is no stronger than
    `Z_C`.
  * the UFLP -> SPaP -> SPP transformations on p. 8. I followed the shape of
    the substitution `y^c_j = 1 - y_j` and the slack/penalty construction,
    but I did not check that the resulting SPP is equivalent.
  * the TLCFLP path formulation (15a)-(15j), p. 13. Transcribed; I did not
    work through why (15f) is "equivalent to (4c)" while its left-hand side
    "cannot be incorporated in the former model".
* **No proofs appear in this paper**, so none were skipped. It is a survey;
  every result is cited, not derived. That is a limitation of the source: it
  cannot be used to justify a claim about how WELL any of these models or
  algorithms perform, only about what they are.
* **Section 3's Weiszfeld reference.** I used Weiszfeld's algorithm to
  measure the cost of the node restriction (see `NOTES_hakimi_1964.md`
  section 6.3), on the strength of this paper's one-sentence description
  plus prior knowledge. I did not read Weiszfeld (1937) or Miehle (1958),
  and I did not verify the convergence conditions — in particular the known
  failure case where an iterate lands exactly on a demand point, which my
  implementation guards against only with an epsilon.
* **The published version.** I read the ARTICLE IN PRESS proof. I have not
  compared it against EJOR 162(1):4-29 (2005) and cannot rule out changes
  between proof and final text, including to equation numbers.
