# Notes — Hakimi (1964), Optimum Locations of Switching Centers and the Absolute Centers and Medians of a Graph

*Read in full 2026-09-13, all ten printed pages including the proof of the
absolute-median theorem. These notes exist so nobody has to open the PDF
again.*

---

## 1. Citation and local file

```
  S. L. Hakimi.  Department of Electrical Engineering,
  Northwestern University, Evanston, Illinois.
  "Optimum Locations of Switching Centers and the Absolute Centers and
   Medians of a Graph."
  Operations Research, Vol. 12, No. 3 (May-June 1964), pp. 450-459.
  Published by INFORMS.  Received November 15, 1963.
  JSTOR stable URL: https://www.jstor.org/stable/168125
  Supported by AFOSR Grant AF-AFOSR-98-63 and the U.S. Army Research
  Office (Durham).

  Local file:  ../Research/168125.pdf
               11 PDF pages: page 1 is the JSTOR cover sheet, PDF pages
               2-11 are printed pages 450-459.
```

The companion paper that everybody actually means when they say "Hakimi's
theorem" in a p-median context is a DIFFERENT one and is **not** on disk:

```
  S. L. Hakimi.  "Optimum distribution of switching centers in a
  communication network and some related graph theoretic problems."
  Operations Research 13:462-475, 1965.
```

This distinction is the single most important thing in these notes and
section 6 below is about why.

---

## 2. What the paper is for

A short, self-contained paper that does two things. It defines the
*absolute centre* and the *absolute median* of a weighted graph — points
that may lie anywhere along an edge rather than only at a vertex — and then
it settles where each of them can be. For the absolute centre (minimise the
maximum weighted distance, the "police station" problem) the answer is
genuinely anywhere, and Hakimi gives a graphical procedure, branch by
branch, for finding it. For the absolute median (minimise the total
weighted distance, the "switching centre" problem) the answer is that you
never need to look off a vertex: **an absolute median of a graph is always
at a vertex**, and he proves it.

That second result is why the paper is cited thousands of times. It is the
licence for the entire discrete-location literature: it says that a
continuous siting problem on a network collapses, without loss, to choosing
from a finite list. Everything downstream — the p-median integer program,
every branch-and-bound and Lagrangean scheme built on it — starts from
being allowed to enumerate nodes.

The paper is also a period piece in a useful way. It was written for
telephone switching, the algorithms are pencil-and-paper graphical
constructions, and the vocabulary ("wires", "lines") predates the
distribution-logistics reading that Klose and Drexl give it forty years
later.

---

## 3. Section-by-section walkthrough

The paper has an abstract, an untitled introduction, and four titled
sections. There is no section numbering in the original; the numbers below
are mine, and I give the printed page for each so a citation can be checked.

### 3.0 Abstract (p. 450)

States the whole paper in six sentences. Generalises "centre" and "median
vertex" to "absolute centre" and "absolute median" of a weighted graph
(weights on vertices AND on branches). Applies them to siting a switching
centre in a communication network and a police station on a highway system.
Announces both answers up front:

> "It is shown that the optimum location of a switching center is always at
> a vertex of the communication network while the best location for the
> police station is not necessarily at an intersection."
> — Abstract, p. 450

### 3.1 Introduction, untitled (pp. 450-451)

Sets up the model. A communication network is a finite graph `G`.
Nonnegative weights are attached to both kinds of element:

```
  w_i  on branch b_i   the length, or the cost per unit capacity, of
                       that element
  h_i  on vertex v_i   the number of wires (lines) that must connect v_i
                       to the switching centre S, i.e. the traffic that
                       originates or terminates at v_i
```

The switching-centre problem is to place `S` to minimise the total length
of wire. The police-station problem is the other objective: minimise the
maximum distance from the station to any community.

Hakimi then says plainly that the textbook graph-theoretic centre and
median are not adequate for either:

> "From the above discussion it is clear that the usual graph theoretic
> concepts of the center and the median cannot be used."
> — Introduction, p. 450

Because the optimum may be *along* an edge, he needs points that are not
vertices. He defines a point `x` on `G` as "a point along some branch of G
that may or may not be a vertex of G", and `d(x,y)` as the length of the
shortest path in `G` between points `x` and `y`, where a path's length is
the sum of its branch weights. With that, the two definitions (p. 451):

```
  ABSOLUTE CENTRE.  x_0 on an element of a weighted n-vertex graph G is an
  absolute centre if, for every point x on G,

      max            h_i d(v_i, x_0)  <=  max            h_i d(v_i, x)      (1)
       1 <= i <= n                         1 <= i <= n

  ABSOLUTE MEDIAN.  y_0 on G is an absolute median if, for every point y
  on G,

       i=n                                 i=n
       SUM  h_i d(v_i, y_0)          <=    SUM  h_i d(v_i, y)               (2)
       i=1                                 i=1
```

And the interpretation: the absolute median is the switching centre, the
absolute centre is the police station.

Note carefully what (2) is and is not. It is ONE facility. There is no `p`
anywhere in this paper.

### 3.2 "CENTERS AND MEDIANS" (pp. 451-452)

The classical, vertex-restricted objects, for contrast. A square matrix
`D = [d_ij]` of order `n` is the distance matrix of an `n`-vertex
nonoriented graph `G` if

```
  d_ij = d(v_i, v_j)   for i, j = 1,...,n and i != j
  d_ij = 0             for i = j                                            (3)
```

Two column statistics do all the work:

```
  d_i^m   the MAXIMUM entry in the ith column of D.
          If d_c^m = min(d_1^m, ..., d_n^m) then v_c is a CENTER of G.

  d_i^s   the SUM of the entries in the ith column of D.
          If d_b^s = min(d_1^s, ..., d_n^s) then v_b is the MEDIAN VERTEX
          of G.
```

Worked on the graph of Fig. 1(a), whose distance matrix is given as
equation (4):

```
          v1   v2   v3   v4   v5
   v1 [    0   10   24   20   34 ]
   v2 [   10    0   14   12   24 ]
   v3 [   24   14    0   12   10 ]      (4)
   v4 [   20   12   12    0   20 ]
   v5 [   34   24   10   20    0 ]

   column max   34   24   24   20   34   ->  v4 is the center
   column sum   88   60   60   64   88   ->  v2 and v3 are both medians
```

Hakimi: "It is easily determined that v_4 is the center of the graph of
Fig. 1(a) and that v_2 and v_3 are two possible choices for the median of
that graph." The radius is defined as the distance to the farthest vertex
from the centre:

```
   r_0 = min          max          d(v_i, v_j)                              (5)
          1 <= j <= n  1 <= i <= n
```

Fig. 1(a) is a five-vertex graph: `v5 - v3 - v2 - v1` in a line with branch
lengths 10, 14, 10, and an apex `v4` joined to all four with lengths 20, 12,
12, 20:

```
                       v4
                   /  |   |  \
               20/  12|   |12  \20
               /      |   |      \
             v5 --10-- v3 --14-- v2 --10-- v1
```

Its radius is 20. Fig. 1(b) is the same graph with a point `x_0` marked on
the branch `b(v_3, v_2)`, and the point of the example is that `x_0` beats
every vertex:

```
   max          d(v_i, x_0) = 18 < d(v_4, v_1) = 20                         (6)
    1 <= i <= 5
```

**A discrepancy worth recording.** The body text says "pick a point x_0 on
the branch b(v_3,v_2) such that d(v_3,x_0) = 6", while Fig. 1(b) labels the
two pieces of that branch 8 (from v_3) and 6 (to v_2). Both readings give
max distance 18, so the conclusion is unaffected; with the figure's labels,
`d(v_5,x_0) = 10+8 = 18`, `d(v_1,x_0) = 10+6 = 16`,
`d(v_4,x_0) = min(12+8, 12+6) = 18`. I have not resolved which is the typo.

The paragraph that closes the section is the thesis of the whole first half:

> "From the above discussion it follows that there are points on a graph,
> such as x_0 in the graph of Fig. 1(b), which, roughly speaking, are more
> centrally located than the center of G."
> — p. 452

### 3.3 "THE ABSOLUTE CENTER AND THE RADIUS OF A GRAPH" (pp. 452-456)

The longest section and the one that is least relevant to us, because it is
about the MINMAX objective and we have a MINSUM one. Summarised for
completeness, and because it explains why the two objectives get different
answers.

Restatement of (1) as a minimisation, defining the absolute radius `r(x_0)`:

```
   min       max          h_i d(v_i, x)  =  max  h_i d(v_i, x_0) = r(x_0)   (7)
   x on G    1<=i<=n                        i
```

Because every point of `G` lies on some branch, the search decomposes over
the `m` branches:

```
   min         [ min        max  h_i d(v_i,x) ]  =  r(x_0)                  (8)
   1<=j<=m       x on b_j    i
```

Each inner problem is a min-max over one branch, whose solution `x_j` he
calls a LOCAL CENTER of `G` on `b_j`:

```
   min        max  h_i d(v_i,x)  =  max  h_i d(v_i,x_j)  =  r(x_j)          (9)
   x on b_j    i                     i

   min       [ r(x_j) ]  =  r(x_0)                                         (10)
   1<=j<=n
```

(Equation (10) and the sentence after it index the local centres by `n`
where the count of branches `m` is meant. A typo; `m` is correct.)

So: find the local centre of every branch, then take the best. The rest of
the section is how to find a local centre, and it is a graphical argument.

For an arbitrary point `x` on branch `b_j(v_p, v_q)` and any vertex `v_i`,
the distance to `v_i` must leave the branch through one of its two ends
(Fig. 2):

```
   d(v_i, x) = min[ d(x,v_p) + d(v_p,v_i),  d(x,v_q) + d(v_q,v_i) ]        (11)
```

Parameterise by `x = d(v_p,x)` and write `B_j = d(v_p,v_q)`:

```
   d(v_i, x) = min[ x + d(v_p,v_i),  B_j - x + d(v_q,v_i) ]                (12)
```

This is the minimum of an up-sloping and a down-sloping straight line, so
as a function of position along the branch it is a tent (Fig. 3): it rises
from `d(v_p,v_i)` at one end, peaks, and falls to `d(v_q,v_i)` at the other.
The peak is at

```
   a_i = (1/2) [ B_j + d(v_q,v_i) - d(v_p,v_i) ]
   d_i = (1/2) [ B_j + d(v_q,v_i) + d(v_p,v_i) ]      (its height)
```

Now overlay the `n` tents `h_i d(v_i,x)`, one per vertex, and take the upper
envelope (Fig. 4):

```
   F_j(x) = max          h_i d(v_i, x),   for x on b_j                     (13)
             1 <= i <= n
```

`F_j` is piecewise linear with finitely many local minima, so its minimum is
found by inspection. That minimum is the local centre `x_j`.

```
   F_j(x)
     ^
     |  h_i d(v_p,v_i)              LOCAL CENTRE          h_p d(v_q,v_p)
     |   \                              |                    /
     |    \      /\      /\             v          /\      /
     |     \    /  \    /  \___________________   /  \    /
     |      \  /    \  /                       \ /    \  /
     |       \/      \/     <- upper envelope   X      \/
     +----------------------------------------------------------> x
     0                    a_i              x_j                 B_j
```

The section closes with a fully worked example on the six-vertex,
eight-branch graph of Fig. 5, taking all vertex weights `h_i = 1`:

```
   Fig. 5 branch lengths
     b1: v6-v5 = 2      b5: v1-v2 = 5
     b2: v5-v3 = 2      b6: v4-v2 = 4
     b3: v6-v1 = 4      b7: v4-v3 = 3
     b4: v1-v4 = 3      b8: v3-v2 = 3

   Distance matrix (equation 14)
          v1  v2  v3  v4  v5  v6
     v1 [  0   3   6   3   6   4 ]
     v2 [  3   0   3   4   5   7 ]
     v3 [  6   3   0   3   2   4 ]
     v4 [  3   4   3   0   5   7 ]
     v5 [  6   5   2   5   0   2 ]
     v6 [  4   7   4   7   2   0 ]
```

Branch by branch (Fig. 6, panels (a)-(h)):

```
   branch   result                                          F at the optimum
   ------   --------------------------------------------    ----------------
   b1       local centre x1 at d(v6,x1) = 1.5                     5.5
   b2       F_2(x) >= 6 everywhere; NO local centre                 -
   b3       local centre x3 at d(x3,v1) = 2.5                     5.5
   b4       F_4(x) >= 6 everywhere; no local centre                 -
   b5       F_5(x) >= 6 everywhere; no local centre                 -
   b6       d(v6,v4) = d(v6,v2) = 7, so F_6(x) >= 7; none           -
   b7       local centre x7 at d(x7,v3) = 1                       5
   b8       local centre x8 with F_8(x8) = 5                      5
```

Minimum over the branches is 5, attained twice, so `G` has TWO absolute
centres, `x_7` and `x_8`, and its absolute radius is 5. Note that neither is
a vertex — this is the counterexample that makes the next section's theorem
non-obvious.

### 3.4 "ABSOLUTE MEDIAN" (pp. 456-458)

The section we actually need. It is a theorem and its proof, and nothing
else. Hakimi credits the tree case to a private communication:

> "THE FOLLOWING theorem is a generalization of a result communicated to the
> author by A. J. GOLDSTEIN,[5] who has shown that an absolute median of a
> connected circuit-less graph (a tree) is always at a vertex.*"
>
> "* Dr. Goldstein did not use the term absolute median or for that matter
> the term median."
> — p. 456

The theorem is stated verbatim in section 5 below. The proof runs pp.
457-458 and I read it line by line; it is reproduced in section 5 as well,
because the *conditions* only become visible in the proof.

The section ends with a remark that is easy to skim past and is worth
keeping, because it is Hakimi telling you the result is deflationary:

> "The above theorem proves that although we can certainly define the term
> absolute median, such a point can never be any more of an absolute
> 'median' than a 'vertex median.'"
> — p. 458

### 3.5 "CONCLUSIONS AND FURTHER PROBLEMS" (pp. 458-459)

Four short paragraphs.

1. The practical summary: for a switching centre "one can limit onself
   [sic] to finding the vertex median of the corresponding graph"; for a
   hospital or police station under a minmax objective one must run the
   branch-by-branch absolute-centre procedure of section 3.3.

2. A nice observation that the objective, not the facility, decides which
   tool applies. If `h_i` is the average number of road accidents at
   community `v_i` and the police must visit every scene, then the total
   travel is what matters, so the police station is a MEDIAN after all — and
   sits at a vertex. Same facility, different objective, different theorem.
   "The problem becomes more complicated if one is to find the optimum
   location of the police station with consideration given to a combination
   of both factors."

3. A game-theoretic reading of the absolute centre. `X` picks a point `x` on
   `G`; `Y` then picks `y`; `X` pays `d(x,y)`. `X` wants to pick a point
   whose maximum distance is minimal, so the least `X` can lose is

```
   min       max       d(x,y)  =  r(x_0)                                   (27)
   x on G    y on G
```

4. "This game theoretic approach seems quite interesting, and the author is
   at the present studying the feasability [sic] of such an approach."

### 3.6 References (p. 459)

Five items, and the shortness is itself informative — this is a 1964 paper
with essentially no prior location literature to cite.

```
  1. O. Ore, "Theory of Graphs," 27-30, Am. Math. Soc. Colloquium
     Publication, Providence R.I., 1962.
  2. C. Berge, The Theory of Graphs, pp. 119-122, Methuen, London, 1962.
  3. E. F. Moore, "Shortest Path Through a Maze," 285-292, Proc. Intl.
     Symposium on Switching Circuits, Harvard, April 1957.
  4. S. L. Hakimi and S. S. Yau, "Distance Matrix and the Synthesis of
     N-port Resistive Networks," Tech. Rep. No. 6, Network Theory Group,
     Dept. of Elect. Eng., Northwestern Univ., Evanston, Ill.
  5. A. J. Goldstein, Private Communication, Bell Telephone Laboratories,
     Murray Hill, N.J., Summer 1962.
```

---

## 4. Load-bearing quotations

Each is followed by its section and printed page.

> "The concepts of the 'center' and the 'median vertex' of a graph are
> generalized to the 'absolute center' and the 'absolute median' of a
> weighted graph (a graph with weights attached to its vertices as well as
> to its branches)."
> — Abstract, p. 450

> "It is shown that the optimum location of a switching center is always at
> a vertex of the communication network while the best location for the
> police station is not necessarily at an intersection."
> — Abstract, p. 450

> "The weight w_i attached to the branch b_i of G represents the length (or
> the cost per unit capacity) of that element. The weight h_i attached to a
> vertex v_i of G represents the number of wires (lines) that must be
> connected between vertex v_i and the switching center S to handle the
> information flows that either originate or terminate at v_i."
> — Introduction, p. 450

> "a point x on G is a point along some branch of G that may or may not be
> a vertex of G. The distance between any two points x and y on G,
> represented by d(x,y), is the length of the shortest path in G between
> points x and y, where the length of a path is the sum of the weights of
> the branches of that path."
> — Introduction, p. 451

> "The absolute median of a graph may be identified with the optimum
> location of the switching center in a communication network, and the
> absolute center may be identified with the optimum location of the police
> station in a highway system."
> — Introduction, p. 451

> "Since F_j(x) is a 'piecewise linear function,' F_j(s) has a finite number
> of local minima each of which can be easily computed; therefore, there is
> no difficulty in calculating the position of the point x_j."
> — Absolute center, p. 456

> "The above theorem proves that although we can certainly define the term
> absolute median, such a point can never be any more of an absolute
> 'median' than a 'vertex median.'"
> — Absolute median, p. 458

> "WE HAVE shown that to find the optimum location of a switching center in
> a communication network, one can limit onself to finding the vertex median
> of the corresponding graph."
> — Conclusions, p. 458

---

## 5. The formal statements, exactly as given

### 5.1 The definitions

Printed page 451. `G` is a weighted `n`-vertex graph with nonnegative
weights `w_i` on branches and `h_i` on vertices; `d(.,.)` is shortest-path
distance in `G`; `x`, `y` range over all points of `G`, vertex or not.

> "We define a point x_0 on an element of a weighted n-vertex graph G to be
> an *absolute center* of G, if for every point x on G
>
>     max_{1<=i<=n} h_i d(v_i,x_0) <= max_{1<=i<=n} h_i d(v_i,x)        (1)
>
> Similarly, we define a point y_0 on G to be an *absolute median* of G, if
> for every point y on G
>
>     sum_{i=1}^{i=n} h_i d(v_i,y_0) <= sum^{i=n}_{i=1} h_i d(v_i,y)    (2)"

### 5.2 The theorem

Printed page 456. Quoted exactly, in full; it is one sentence and there is
no hypothesis attached to it in the statement.

> "THEOREM. *An absolute median of a graph is always at a vertex of a
> graph.*"

### 5.3 The proof, and the conditions it actually uses

Printed pages 457-458. The hypotheses do not appear in the statement, so
they have to be read out of the proof. Reproduced faithfully; I have
verified each algebraic step.

> "*Proof.* To prove this theorem, we will show that if x_0 is an arbitrary
> point on G and x_0 != v_i for i = 1, ..., n, then there always exists a
> vertex v_m in G such that
>
>     sum_{i=1}^{i=n} h_i d(v_i,x_0) >= sum_{i=1}^{i=n} h_i d(v_i,v_m)  (15)
>
> which will prove that a vertex of G will be an absolute median."

Let `x_0` lie on a branch `b(v_p, v_q)`. The proof opens with the same
two-ways-out-of-the-branch fact used for the absolute centre:

```
   d(x_0, v_i) = min[ d(x_0,v_p) + d(v_p,v_i),  d(x_0,v_q) + d(v_q,v_i) ]  (16)
```

Relabel the vertices `i_1, ..., i_n` so that the first `r` of them are
reached through `v_p` and the rest through `v_q`:

```
   d(x_0,v_{i_k}) = d(x_0,v_p) + d(v_p,v_{i_k})   for k = 1,...,r  (r <= n) (17)
   d(x_0,v_{i_k}) = d(x_0,v_q) + d(v_q,v_{i_k})   for k = r+1,...,n        (18)
```

Then the objective splits:

```
   SUM_i h_i d(v_i,x_0)
        = SUM_{k=1}^{r}   h_{i_k} [ d(x_0,v_p) + d(v_p,v_{i_k}) ]
        + SUM_{k=r+1}^{n} h_{i_k} [ d(x_0,v_q) + d(v_q,v_{i_k}) ]          (19)
```

and the argument splits on which end of the branch carries the larger share
of the vertex weight:

```
   Case (a):  SUM_{k=1}^{r} h_{i_k}  >=  SUM_{k=r+1}^{n} h_{i_k}
   Case (b):  SUM_{k=1}^{r} h_{i_k}  <   SUM_{k=r+1}^{n} h_{i_k}
```

**Case (a).** Substitute `d(x_0,v_q) = d(v_p,v_q) - d(x_0,v_p)` into (19),
giving (20), then apply the triangle inequality on the graph,

```
   d(v_p,v_q) + d(v_q,v_{i_k})  >=  d(v_p,v_{i_k})                         (21)
```

to obtain (22), which rearranges to

```
   SUM_i h_i d(v_i,x_0) >= SUM_i h_i d(v_p,v_i)
                         + [ SUM_{k=1}^{r} h_{i_k}
                             - SUM_{k=r+1}^{n} h_{i_k} ] d(x_0,v_p)        (23)
```

The bracket is `>= 0` by the Case (a) hypothesis and `d(x_0,v_p) >= 0`, so
the whole correction term is nonnegative and

```
   SUM_i h_i d(v_i,x_0)  >=  SUM_i h_i d(v_p,v_i)
```

i.e. the endpoint `v_p` is at least as good as `x_0`. "This however is the
desired result."

**Case (b).** Symmetric. Substitute `d(x_0,v_p) = d(v_p,v_q) - d(v_q,x_0)`
into (19), giving (24), and "using entirely similar steps as in Case (a)"
reduce to

```
   SUM_i h_i d(v_i,x_0) >= SUM_i h_i (v_i,v_q)
                         + [ SUM_{k=r+1}^{n} h_{i_k}
                             - SUM_{k=1}^{r} h_{i_k} ] d(x_0,v_q)          (25)
```

and hence, the bracket now being strictly positive,

```
   SUM_i h_i d(v_i,x_0)  >   SUM_i h_i d(v_i,v_q)                          (26)
```

> "which is what was desired, and hence the theorem."

**The conditions, extracted.** The theorem statement carries none, so these
are the hypotheses the proof relies on:

```
  C1  G is a GRAPH.  Every candidate point x_0 lies on a branch with two
      endpoints v_p, v_q, and (16) holds -- any path out of x_0 exits
      through one of those two vertices.  This is the load-bearing
      assumption and it is a statement about network topology.
  C2  d is SHORTEST-PATH distance in G, so the triangle inequality (21)
      holds.
  C3  The demand sits at the VERTICES.  The sum in (2) runs over v_1..v_n;
      "candidate sites" and "demand points" are the SAME finite set.
  C4  Weights h_i are nonnegative (stated in the introduction, p. 450).
      Zero is allowed; the proof only ever needs h_i >= 0.
  C5  The objective is the UNWEIGHTED-IN-DISTANCE sum, i.e. linear in
      d.  The proof adds and subtracts distances freely.  Anything convex
      in d -- squared distance, for one -- breaks step (23).
  C6  ONE facility.  p does not appear anywhere in the paper.
```

C6 is not a quibble. Nothing in (15)-(26) generalises for free: with two
facilities the assignment of vertices to facilities changes as a facility
slides along a branch, and (17)-(18) no longer partition the vertex set in
a fixed way. The `p`-facility version is a separate theorem in a separate
paper, Hakimi (1965).

---

## 6. What this means for siting-atlas

### 6.1 The concrete use

`src/siting_atlas/cost/depots.py` places delivery-station depots. Until
2026-09-13 it did so with k-means (`KMeans(...)`, old line 108), which
minimises SQUARED distance. The model bills line haul linearly, at
`src/siting_atlas/cost/daganzo.py:159`:

```python
line = 2.0 * linehaul / p.stops_per_tour
```

Minimising squared distance while charging linear distance is minimising
the wrong thing, and it is the weighted-mean-versus-weighted-median error.
The module now solves a p-median over a candidate set instead — see
`docs/research/NOTES_klose_drexl_2005.md` section 6 for the formulation and
`src/siting_atlas/cost/depots.py:91` (`solve_pmedian`) for the algorithm.

Hakimi's role in that change is to justify **restricting the candidate set
to the ZCTA internal points** rather than optimising over the whole plane.
The next subsection is about whether he actually does.

### 6.2 Does the theorem transfer? Mostly not, and we should say so

Three separate gaps, in descending order of seriousness.

**Gap 1 — p > 1. The 1964 paper does not cover our case at all.**
We place 334 depots, up to 109 in a single metro. This paper proves a result
about ONE absolute median (condition C6). The p-facility node-optimality
result is Hakimi (1965), which is a different paper and is not in
`Research/`. Klose and Drexl are careful about this and cite both:

> "Hakimi (1964, 1965) has shown that it is sufficient to restrict the set
> of potential sites to the set of nodes in the case of concave distance
> functions."
> — Klose & Drexl, section 4, p. 4

So the honest sentence for the write-up is "Hakimi (1964, 1965)", or "the
Hakimi property", never "Hakimi (1964)" alone. If the 1965 paper matters to
the defence it should be obtained and read; I have not read it and am
relying on Klose and Drexl's characterisation of it.

**Gap 2 — we are in the plane, not on a graph.** Condition C1 is the
engine of the proof, and we do not satisfy it. `depots.py` measures
great-circle distance with `haversine_miles`; there is no road network in
the model, no branches, and no `v_p`/`v_q` for an arbitrary candidate point
to exit through. In the plane the corresponding object is the Weber point
(Klose & Drexl section 3, the SWP), and the Weber point is in general NOT at
a demand point. So in our actual metric space, restricting depots to ZCTA
centroids is a genuine RESTRICTION with a genuine cost, not a free lunch,
and any claim otherwise would be wrong.

It is worth being precise about what would fix this. If we modelled each
metro as a road graph with demand at ZCTA internal points, C1-C5 would hold
exactly and (for p = 1) the theorem would apply as written. Our
haversine-in-the-plane model is an approximation to that graph, and the
approximation is where the licence is being stretched. Hakimi is
inspiration for the modelling choice; he is not authority for it.

**Gap 3 — the candidate set is not obviously the vertex set.** Condition C3
says candidates and demand points are the same set. Our candidates ARE our
demand points (ZCTA internal points), so this one we satisfy — but only
because we chose to. It is emphatically NOT satisfied by the alternative
that was proposed for this work, which was to use the buildings in
`data/external/facility_panel/facilities.csv` and
`national_facilities.csv`. Those are neither the demand points nor the
vertices of anything; restricting to them would be an operational
constraint, justified by "these are real buildings", and Hakimi would have
nothing to say about it.

That set is also unusable as a candidate set on three independent counts,
each of which I checked:

```
  1  NO COORDINATES.  Both files have latitude and longitude columns and
     both columns are 100% null -- 0 of 43 and 0 of 104 rows geocoded.
     They cannot supply a point without a geocoding step that does not
     exist in the repository.
  2  WRONG SCALE.  facilities.csv has 43 rows resolving to 40 distinct
     pilot ZIPs.  The pilot needs 334 depots.
  3  WRONG GEOGRAPHY.  national_facilities.csv's 104 rows resolve to 97
     distinct ZIPs, and ZERO of them fall inside the pilot's ZCTA set.
     It is a genuinely national file covering metros the pilot excludes.
```

There is also a circularity objection that would apply even if the data
were clean: those 43 buildings are Amazon's observed delivery stations,
which is the outcome the project exists to predict. Using them as the
candidate set would put the answer into the model.

What they ARE good for is validation, so I used them that way. Geocoding
each facility to the centroid of its ZIP's ZCTA (all 43 resolve), the
distance from a real Amazon delivery station to the nearest modelled depot
is:

```
                   median    mean    p90     max     (miles)
  k-means           2.99     3.03    4.59    7.88
  p-median          2.90     2.97    4.75    8.15
```

Both networks put a modelled depot about three miles from every real one,
which is a genuine external sanity check on the depot-count rule. It does
NOT discriminate between the two placement methods — the difference is
within noise, and honesty requires saying so rather than claiming the fix
validated itself.

### 6.3 What the restriction actually costs, measured

Since the theorem does not transfer, the restriction has to be defended
empirically instead. I measured it on the 2024Q1 pilot: solve the discrete
p-median over ZCTA nodes, then take that solution and let the depots move
freely in the plane, alternating nearest-depot assignment with a Weiszfeld
solve of each cluster's continuous Weber point until nothing moves.

```
  objective = SUM over ZCTAs of (daily parcels) x (miles to nearest depot)

  discrete p-median, candidates = ZCTA internal points   33,156,338
  continuous multi-source Weber refinement               33,006,455
  cost of the node restriction                                0.45%
```

Caveat, honestly: the continuous figure is itself only a local optimum of a
nonconvex problem, reached by descending from the discrete solution, so
0.45% is a LOWER bound on the true gap to the continuous optimum. It is
nevertheless a useful order of magnitude, and 0.45% of a term that is ~8% of
cost is about 0.04% of cost.

The conclusion to state in the write-up: *the node restriction is not
licensed by Hakimi in our metric, but it is nearly free and it buys the
guarantee that every depot stands on an inhabited ZCTA rather than at an
invented coordinate in a reservoir.* That claim is enforced by a test,
`tests/unit/test_depots_pmedian.py::test_depots_land_on_real_candidate_rows_not_invented_coordinates`.

### 6.4 The one thing that DOES transfer cleanly

Condition C5. The proof adds and subtracts distances and never squares one.
It is a formal statement of the intuition that the minsum objective wants
the median and the minmax objective wants the centre — see section 3.5,
paragraph 2, where Hakimi makes exactly that point about the police station.
That is the same distinction as the k-means/p-median defect in `depots.py`,
stated sixty years earlier, and it is a good line to have in the defence.

### 6.5 What we are not using

The entire absolute-centre machinery of section 3.3 is a minmax tool. Our
cost function is minsum throughout. If a future version of the project ever
adds a service-level constraint of the form "no ZCTA may be more than X
miles from a depot", that becomes a p-centre problem — at which point note
that Klose and Drexl (section 4, p. 4) say the node restriction FAILS for
p-centre and one must also consider intersection points on arcs.

---

## 7. What I did NOT read, or did not fully verify

* **Hakimi (1965)**, the p-facility generalisation. Not on disk, not read.
  Everything in section 6.2 about it comes from Klose and Drexl's one-line
  characterisation. This is the most important gap in these notes.
* **The five references.** None consulted. In particular Goldstein's private
  communication (ref. 5), the tree result the theorem generalises, is by
  definition unavailable.
* **Case (b) of the proof** (p. 458). Hakimi writes "The proof of this case
  is very similar to the previous case" and skips from (24) to (25) with
  "using entirely similar steps as in Case (a)". I did not reconstruct the
  omitted algebra. I did check that (25) has the sign structure the argument
  needs and that the strict inequality in (26) follows from the strict
  inequality in the Case (b) hypothesis, which is consistent.
* **The Fig. 6 constructions** (p. 455, eight panels). I read the summary of
  each and checked the arithmetic on branch b6 only, where
  `d(v_6,v_4) = d(v_6,v_2) = 7` from matrix (14) makes `F_6(x) >= 7`
  immediate. I did not re-derive the local centres on b1, b3, b7 and b8 from
  the plots; I took the paper's word for `x_1 = 1.5`, `x_3 = 2.5`,
  `d(x_7,v_3) = 1` and the values 5.5, 5.5, 5, 5.
* **The Fig. 1(b) discrepancy** flagged in section 3.2 (text says
  `d(v_3,x_0) = 6`, figure labels 8 and 6) is unresolved. I verified only
  that both readings give the stated max of 18.
* **Equation (10)'s index** is `n` where `m` (the branch count) is meant. I
  am confident this is a typo rather than something I have misunderstood,
  because equation (8) uses `1 <= j <= m` for the same quantity, but I have
  not found an erratum.
* I did not check whether the theorem needs `G` to be CONNECTED. It is never
  stated. The proof assumes `d(v_i,x_0)` is finite for all `i`, which on a
  disconnected graph it is not, so connectedness is presumably implicit.
  Immaterial for us — each metro's candidate set is a complete graph under
  haversine distance.
