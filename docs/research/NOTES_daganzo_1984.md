# Notes — Daganzo (1984), the continuous approximation behind `cost/daganzo.py`

> **READ THIS FIRST. THE PAPER WAS NOT READ. IT IS NOT ON DISK.**
>
> Every other file in this directory was written with the PDF open. This one
> was not. No Daganzo paper is in `../Research/`, none could be obtained from
> this host, and **nothing below is a report of what Daganzo (1984) says.**
> There is not one page number, section number or quotation from it anywhere
> in this file, and there must never be one until somebody opens it.
>
> What this file *is*: (a) an exact account of what the repository actually
> does, quoted from the code; (b) everything about the paper that **was**
> retrieved and read — its abstract, verbatim, from OpenAlex; Larson &
> Odoni's *Urban Operations Research* §6.4.8 in full; and a 1991 doctoral
> thesis that describes Daganzo's formula; (c) four numerical experiments
> run on 2026-09-14 to test claims the repository makes about the constant;
> and (d) a precise, itemised list of what must be checked against the
> original.
>
> **Three findings, in order of how badly they need acting on.**
>
> **1. One of the two papers the repository cites for the constant is by
> somebody else.** `docs/REFERENCES.md` §2 and `cost/params.py:47-49` cite
> *"Daganzo, C. F. (1984). Approximate formulas for average distances
> associated with zones. Transportation Science 18(3), 231-253"* and call it
> "the companion paper, and the source of the zone-geometry constants of
> which `bhh_constant = 0.57` is one". That DOI belongs to **R. J. Vaughan**,
> the pages are **231-244**, and the paper is about average distances between
> random points in zones — not tour lengths, not constants, not Daganzo.
> Verified against OpenAlex twice, independently. See §1.1 and §6.3.
>
> **2. The paper that probably IS the source is not cited at all.** Daganzo,
> C. F. (1984), *The length of tours in zones of different shapes*,
> Transportation Research Part B 18(2), 135-145 — confirmed to exist, 274
> citations. §1.4.
>
> **3. `bhh_constant = 0.57` did not survive scrutiny in the form the
> repository defends it.** The value may well be right; the *derivation
> printed in `cost/daganzo.py:16-19` is not consistent with it*, the
> surviving corroborating source says **0.765**, and no retrievable source
> anywhere states 0.57. See §6.2 and §6.3.
>
> Written 2026-09-14. `choice_sandwich.py:21` flags Andrews (1999) as
> named-but-unread rather than pretending; this file does the same thing at
> greater length.

---

## 1. Citation and local file

### 1.1 What the repository cites

Two entries, both in `docs/REFERENCES.md` §2, both marked **[T]** there
(title and venue verified against a publisher URL; contents not read):

```
  Daganzo, C. F. (1984). "The distance traveled to visit N points with a
  maximum of C stops per vehicle: An analytic model and an application."
  Transportation Science 18(4), 331-350.  DOI 10.1287/trsc.18.4.331
      -> REFERENCES.md calls this "the direct source of the model's
         structure": the split between line haul shared across a tour of C
         stops, and local travel scaling as k / sqrt(density).

  Daganzo, C. F. (1984). "Approximate formulas for average distances
  associated with zones."
  Transportation Science 18(3), 231-253.  DOI 10.1287/trsc.18.3.231
      -> REFERENCES.md calls this "the companion paper, and the source of
         the zone-geometry constants of which bhh_constant = 0.57 is one."
      -> IT IS NOT DAGANZO'S PAPER. See 1.1.1 immediately below.
```

### 1.1.1 The second citation is wrong, on three counts

DOI `10.1287/trsc.18.3.231` was resolved against the OpenAlex API
(`https://api.openalex.org/works/doi:10.1287/trsc.18.3.231`, retrieved
2026-09-14). It returns:

```
  title   Approximate Formulas for Average Distances Associated with Zones
  author  R J Vaughan                      <- NOT Daganzo
  venue   Transportation Science, vol 18, issue 3, pp 231-244
                                           <- NOT 231-253
  date    1984-08-01      cited_by 41      <- vs 306 for the real Daganzo
  doi     https://doi.org/10.1287/trsc.18.3.231
```

and its abstract, verbatim from the same response, shows it is about a
different subject entirely:

> "This paper develops formulas for estimating average distances associated
> with zones. The average distance between two points, one located at random
> in a zone and another located at random in another, is first investigated.
> The average distance from a fixed point to a point located at random in a
> zone, and the average distance between two points located at random in the
> same zone, are also examined. The accuracy of the approximations for these
> average distances are found by examining some simple cases."
> — abstract of Vaughan (1984), via OpenAlex

So it is an **average-distance-between-random-points** paper. It contains no
tour, no vehicle, no capacity C and no tour-length constant. It cannot be
"the source of the zone-geometry constants of which `bhh_constant = 0.57` is
one", because `bhh_constant` is a tour-length coefficient and this paper does
not compute tour lengths.

The title and page range in `REFERENCES.md` were presumably copied from a
citation list rather than from the record. `REFERENCES.md`'s annotation says
*"Confirmed against the INFORMS URL"* — whatever was confirmed, it was not
the author, and the page range disagrees too.

**Action, and it is not this file's to take** (`REFERENCES.md` and
`params.py` belong to other workstreams): either delete the citation, or
re-attribute it to Vaughan and stop describing it as a companion paper. It
is not evidence for anything in `cost/`.

*(Method note, because this claim matters: OpenAlex is a bibliographic
aggregator, not the publisher. The record is consistent — right venue, right
volume, right issue, plausible page range, and the 41-vs-306 citation counts
match the two papers' very different reputations — and it was fetched twice,
independently. It should still be confirmed against INFORMS itself by
somebody whose network can reach it.)*

`cost/params.py:47-49` cites both together for `bhh_constant`, plus:

```
  Beardwood, J., Halton, J. H., & Hammersley, J. M. (1959). "The shortest
  path through many points." Mathematical Proceedings of the Cambridge
  Philosophical Society 55(4), 299-327.        [K in REFERENCES.md]

  Larson, R. C., & Odoni, A. R. (1981). Urban Operations Research.
  Prentice-Hall.  §6.4.8.                      [T in REFERENCES.md]
```

### 1.2 Local file: THERE IS NONE

```
  $ ls ../Research/ | grep -i -E 'dagan|beard|halton|hammers|larson|odoni'
  (nothing)

  $ find . .. -iname '*dagan*' -o -iname '*beardwood*'
  ./src/siting_atlas/cost/daganzo.py
  ./tests/unit/test_cost_daganzo_math.py
  (i.e. our own code, and nothing else)
```

Every one of the 33 PDFs in `../Research/` was scanned for the strings
`daganzo` and `beardwood`. Exactly two files matched, and **both matches are
a trap** (see §1.4).

### 1.3 What was retrieved from this host, and how

This host's proxy allows `https://` to a small allowlist and blocks
everything else. Measured on 2026-09-14:

```
  REACHABLE    api.openalex.org      <- THE USEFUL ONE. No key. Full
                                        bibliographic records and, for many
                                        works, the abstract.
               core.ac.uk / api.core.ac.uk   (CORE v3, no key)
               web.mit.edu (200), www.mit.edu, www.nber.org,
               hdl.handle.net, its.berkeley.edu, ora.ox.ac.uk,
               kilthub.cmu.edu, www0.gsb.columbia.edu,
               doi.org (resolves and redirects correctly)
  BLOCKED      pubsonline.informs.org  -> 403, Cloudflare JS challenge
               (both DOIs resolve to it; the articles are behind it)
  UNREACHABLE  arxiv.org, sciencedirect, link.springer.com, jstor,
               api.semanticscholar.org, api.crossref.org, api.unpaywall.org,
               api.datacite.org, opencitations.net, base-search.net,
               doaj.org, web.archive.org, scholar.archive.org,
               scholar.google, researchgate, escholarship, citeseerx,
               mdpi.com, hal.science, dspace.mit.edu, lirias.kuleuven.be,
               users.iems.northwestern.edu   (000 or 503 from the proxy)
  USELESS      www.bing.com returns 200 but the proxy mangles the query
               string; a search for a quoted numeric constant came back
               with results about the number zero. Do not trust it.
```

**Two retrieval recipes worth keeping, because they are not obvious.**

```
  1  BIBLIOGRAPHY AND ABSTRACTS -- api.openalex.org
       curl -sSL https://api.openalex.org/works/doi:10.1287/trsc.18.4.331
     Returns authors, venue, volume, issue, first_page, last_page, date,
     citation count, OA status, and abstract_inverted_index. The abstract
     has to be rebuilt: it is a {token: [positions]} map, so invert it and
     read the tokens back in position order. This is how §2.1 and §1.1.1
     were obtained.

  2  FULL TEXT OF OPEN DEPOSITS -- core.ac.uk/reader/<OUTPUT_ID>
     The HTML of the READER page embeds the whole extracted text as a
     "fullText":"..." JSON string. Parse it out with a regex and
     json.loads.  Three traps:
       - core.ac.uk/download/<id>.pdf 301s to fileserver-az.core.ac.uk,
         which the proxy kills with 503. Use /reader/, not /download/.
       - the CORE v3 API's own fullText field returns "Not available for
         public API users."
       - the work id in results[].id is NOT the reader id. Parse the
         reader id out of sourceFulltextUrls.
     CORE v3 search is also heavily rate-limited without a key (429 after
     roughly one request; space them ~40-70s) and returns HTTP 500 on any
     boolean or quoted query. Bare keyword queries only.
```

**These two recipes are the most durable thing in this file.** The
repository's own `REFERENCES.md` opens by saying it was "built on a host with
no external page access". That is too pessimistic: bibliographic facts and
many abstracts and open deposits *are* reachable, and several [K] and [T]
marks in `REFERENCES.md` could be upgraded or corrected in an afternoon with
recipe 1. The Vaughan mis-citation in §1.1.1 was found in one request.

So the two Daganzo DOIs resolve to a page this host cannot render. **The
INFORMS "confirmation" recorded in `REFERENCES.md` and `PARAMETERS.md` §6.1
could not be reproduced here**; a 403 challenge page is what the DOI returns.
That does not mean the citations are wrong — it means the [T] mark on them is
currently unverifiable from this machine, and the person who wrote it should
say which host and which date they verified it on.

One genuine retrieval succeeded, and it is the only primary text quoted in
this file:

```
  Larson & Odoni, Urban Operations Research, §6.4.8,
  "Probabilistic View of the Traveling Salesman Problem"
  https://web.mit.edu/urban_or_book/www/book/chapter6/6.4.8.html
  Retrieved 2026-09-14, HTTP 200, 9,888 bytes. Read in full.
  NOTE: the page's equations are IMAGES. The text layer renders them as
  blank gaps. Every displayed formula in that section is therefore
  UNREADABLE from the HTML, and only the inline numbers survive. §4 below
  marks each gap.
```

### 1.4 Papers this is easily confused with — and two live traps

**Trap 1, and it is in `../Research/` right now.** The only Daganzo text on
this disk is a *different literature by the same author*:

```
  Daganzo, C. (1979). Multinomial Probit: The Theory and Its Application
  to Demand Forecasting. Academic Press, New York.
      cited in ../Research/Refs_p371-384.pdf (Train's bibliography)
      discussed in ../Research/Ch05_p97-133.pdf (Train ch.5, Probit)

  Daganzo, C., F. Bouthelier & Y. Sheffi (1977). "Multinomial probit and
  qualitative choice: A computationally efficient algorithm."
  Transportation Science 11, 338-358.
      cited in ../Research/Refs_p371-384.pdf
```

Carlos F. Daganzo is cited in this project **twice, for two unrelated
things**: discrete choice (via Train, which we *have* read) and continuous
approximation (which we have not). A `grep` for "Daganzo" across
`../Research/` finds only the first. Anybody who greps and concludes "we have
it" is wrong. Do not let this into the viva.

**Trap 2 — a third Daganzo 1984 paper exists, is heavily cited, and the
repository does not mention it.** Confirmed against OpenAlex 2026-09-14
(`https://api.openalex.org/works/doi:10.1016/0191-2615(84)90027-4`):

```
  title   The length of tours in zones of different shapes
  author  Carlos F. Daganzo
  venue   Transportation Research Part B: Methodological
          vol 18, issue 2, pp 135-145, published 1984-04-01
  doi     10.1016/0191-2615(84)90027-4       cited_by 274
  OA      no. No abstract in OpenAlex either.
```

So there are **three** Daganzo 1984 papers in this area — TR-B 18(2) in
April, Transportation Science 18(4) in November, and (not ours) a third
strand — and the repository cites one of them plus somebody else's.

This is the first place to look for 0.57. Its title is a far closer
description of "where a tour-length constant for a zone comes from" than
either Transportation Science title, and a coefficient for local travel in a
*shaped zone* is exactly the object `bhh_constant` is supposed to be. A 1991
doctoral thesis retrieved in full (§4.3) describes exactly these two papers
as a pair and separates their contributions, which is corroborating.

Note also that the TR-B paper is the only one of the three whose publication
DATE (April 1984) precedes the Transportation Science paper (November 1984),
so if the TS paper uses a constant, the TR-B paper is where it would have
been derived.

### 1.5 The naming of this file

`NOTES_daganzo_1984.md` follows the convention in `docs/research/README.md`
(`NOTES_<first-author-surname>_<year>.md`). It is **imprecise on purpose**:
there are at least two and possibly three Daganzo 1984 papers, this file does
not know which one supplies the constant, and pretending otherwise by naming
the file after one of them would smuggle in an answer. Rename it with a slug
(`NOTES_daganzo_1984_ts_18_4.md`) once somebody has actually read one.

---

## 2. What the paper is for

### 2.1 What the paper itself says it is for — its abstract, verbatim

This is the only text **by Daganzo** anywhere in this file. Retrieved
2026-09-14 from `https://api.openalex.org/works/doi:10.1287/trsc.18.4.331`
and reassembled from the inverted index (recipe 1, §1.3). It is the abstract
of **Transportation Science 18(4), 331-350** — the paper `REFERENCES.md`
calls "the direct source of the model's structure".

> "The purpose of this paper is to develop a simple formula to predict the
> distance traveled by fleets of vehicles in physical distribution problems
> involving a depot and its area of influence. Since the transportation cost
> of operating a break-bulk terminal (or a warehouse) is intimately related
> to the distance traveled, the availability of such a simple formula should
> facilitate the study of more complex logistics problems. A simple manual
> dispatching strategy intended to mimic what dispatchers do, but simple
> enough to admit analytical modeling is presented. Since the formulas agree
> rather well with the length of (nearly optimal) computer built tours, the
> predictions should approximate distances achievable in practice; the
> formulas seem realistic. The technique is a variant of the classical
> 'cluster-first, route-second' approach to vehicle routing problems. In
> these approaches, the depot influence area is first partitioned into
> districts containing clusters of stops; one vehicle route is then
> constructed to serve each cluster. **Our procedure is characterized by the
> way district shapes are chosen; ignoring shape during the clustering step
> can increase significantly travel distances.** The technique is simple. To
> exercise it, one needs only a pencil, eraser, and a scale map showing the
> destinations. Once mastered, the technique takes only a few minutes. This
> time should increase only linearly with the number of destinations. For
> repetitive problems, the technique can be enhanced with the help of
> interactive computer graphics. A newspaper delivery problem for the city of
> San Francisco is used as an illustration."
> — abstract, Daganzo (1984), *Transportation Science* 18(4), 331-350.
> Emphasis mine.

Five things follow from 250 words, and four of them are new information for
this repository.

```
  (i)   THE OBJECT IS RIGHT. "the distance traveled by fleets of vehicles
        in physical distribution problems involving a depot and its area
        of influence" is exactly our object. The citation is apt. We are
        using the right paper for the structure.

  (ii)  IT IS A STRATEGY, NOT A BOUND. "A simple manual dispatching
        strategy intended to mimic what dispatchers do." So the paper's
        constant -- whatever it is -- belongs to object (ii) or (iii) of
        §5.2, a HEURISTIC's coefficient, not the BHH optimum. This is the
        first retrieved evidence bearing on the 0.57 question and it
        points AWAY from bhh_constant being a good name for it.

  (iii) IT IS VALIDATED AGAINST NEAR-OPTIMAL TOURS. "the formulas agree
        rather well with the length of (nearly optimal) computer built
        tours". So the TOTAL the paper predicts is calibrated against
        something close to the optimum. That does not settle what the
        LOCAL coefficient is, because the total is a sum of two terms --
        but it does mean the paper's own accuracy claim is empirical, and
        somebody should read how much error "rather well" covers. It is
        the natural comparator for our unvalidatable cost model
        (ALTERNATIVES.md:152: "We cannot validate the cost model against
        Amazon's real costs, because nobody publishes them").

  (iv)  DISTRICTING IS THE METHOD. "the depot influence area is first
        partitioned into districts containing clusters of stops; one
        vehicle route is then constructed to serve each cluster." The
        unit of the formula is a DISTRICT chosen by the analyst, not an
        administrative area handed to them. We apply it per ZCTA. A ZCTA
        is a postal-delivery artefact, not a district anybody designed to
        be routed. See §6.6 Break 3 and A6.

  (v)   SHAPE IS THE PAPER'S CONTRIBUTION, AND WE IGNORE IT ENTIRELY.
        "Our procedure is characterized by the way district shapes are
        chosen; ignoring shape during the clustering step can increase
        significantly travel distances." The sentence the author chose to
        distinguish their paper from its predecessors is about zone
        shape. The repository holds NO shape or compactness measure for
        any ZCTA. This is the sharpest thing in this file and §6.6
        Break 3 is about it.
```

### 2.2 What we want from it, and what the code actually has

*The rest of this section describes the METHOD as the repository uses it,
reconstructed from the code, from Larson & Odoni and from the 1991 thesis at
§4.3. It is not a description of the paper's contents.*

The problem is this. `docs/data/COST_MODEL.md` §1 states it well: you want
the cost of serving 2,333 ZIP-code areas, you would need it ten thousand
times over inside a Monte Carlo loop, and solving a vehicle-routing problem
that many times is not merely expensive but out of the question. You also do
not *need* the answer a VRP solver gives, because you are not dispatching
vans tomorrow — you want the cost of a *good* route for a place you have
never seen, to within a few percent.

Continuous approximation is the method for that. Rather than treat the stops
as a list of addresses, treat them as a **density smeared over an area**, and
ask what a good tour through such a field costs as a function of that
density. The answer is a formula rather than an algorithm, so it evaluates in
microseconds and differentiates cleanly for sensitivity analysis.

What we want from Daganzo (1984) specifically is three things, and it is
worth being explicit because only the first is currently in the repository:

```
  1  THE STRUCTURE.  The decomposition of distance per stop into a
     line-haul term shared across a tour of C stops, plus a local term
     that scales as 1 / sqrt(stop density).
         -> in the code, and load-bearing.

  2  THE CONSTANT.  The numeric coefficient on the local term, which the
     repository calls bhh_constant and sets to 0.57.
         -> in the code, and UNDEFENDED. This is what §6 is about.

  3  THE CONDITIONS OF VALIDITY.  The paper must state when the formula
     holds: how slowly density may vary, how many points a tour needs
     before the asymptotics bite, what zone shapes are admissible.
         -> NOT ANYWHERE IN THE REPOSITORY. Not in daganzo.py, not in
            params.py, not in COST_MODEL.md, not in PARAMETERS.md. The
            model is applied to 2,333 ZCTAs with no stated condition for
            when it may be applied at all. §6.6 measures what the
            conditions would have caught if they had been written down.
```

Item 3 is the real gap. A reviewer who asks "when does this approximation
stop being valid?" is asking the question the repository has never once
written an answer to, and no amount of sensitivity analysis substitutes for
it, because sensitivity analysis varies the parameter *inside* the formula
and says nothing about whether the formula applies.

---

## 3. Section-by-section walkthrough

**THIS SECTION CANNOT BE WRITTEN AND MUST NOT BE FAKED.**

The house rule in `docs/research/README.md` is that part 3 is a
section-by-section walkthrough of the whole paper, so that nobody has to
reopen the PDF. There is no PDF. Writing a plausible-looking walkthrough from
background knowledge would be the single most damaging thing that could be
put in this directory, because the next reader would trust it.

What follows instead is the **checklist** to fill this section in with, in
the order the answers are needed. Each item names the exact repository claim
it would confirm or destroy.

```
  Q1  Which of the two (or three) 1984 papers states the VRP distance
      formula with a numeric coefficient on the local term?
      -> confirms or corrects REFERENCES.md §2 and params.py:47-49.

  Q2  Write the paper's formula down verbatim, with its own notation, and
      say exactly what each symbol denotes: is the area A the whole
      service region or one vehicle's zone? Is N the total points or the
      points on one tour? Is the "distance" a round trip from the depot
      or an open path?
      -> this is the decisive question for §6.2. The project's derivation
         and the project's constant can only both be right if the paper's
         decomposition differs from the project's.

  Q3  What is the numeric value of the coefficient, printed in the paper,
      and to how many digits?
      -> confirms or destroys 0.57.

  Q4  Under what routing STRATEGY is that coefficient derived? Strip /
      swath? Ring-radial? Optimal tour? A strategy's constant and an
      optimum's constant are different numbers and the difference is the
      whole of §6.2.
      -> params.py:41 asserts "strip/ring-radial routing in a served
         zone" without a page. Verify or delete that sentence.

  Q5  Does the paper relate its coefficient to the Beardwood-Halton-
      Hammersley constant explicitly, and if so, how? Are they the same
      object, or does the paper's decomposition book part of the tour to
      the line-haul term so that its local coefficient is legitimately
      SMALLER than BHH's?
      -> this is the only account under which 0.57 is defensible at all.
         Find it, or accept that the constant has to change.

  Q6  What conditions of validity does the paper state? Specifically:
        (a) how slowly must density vary across the zone;
        (b) how large must C (points per tour) be;
        (c) what zone shapes are admissible, and is there an aspect-ratio
            or elongation condition;
        (d) is there a stated accuracy, e.g. "within x% for C > y"?
      -> item 3 of §2. Nothing in the repository answers any of these.

  Q7  Does the paper handle the case where the zone is SMALLER than one
      vehicle's tour, i.e. where the tour must leave the zone?
      -> 126 of our 2,333 ZCTAs (5.4%) are in exactly that case. §6.6.

  Q8  Does the paper say anything about circuity / non-Euclidean metrics?
      -> daganzo.py:158 multiplies the local term by circuity = 1.30. If
         the paper's constant is already calibrated on road distance, that
         multiplication double-counts. Nobody has checked.
```

Q8 deserves a line of its own. `cost/params.py:65-75` defends `circuity` as
the L1/L2 ratio 4/pi for a grid, which is a statement about *street geometry*
— and a tour-length constant fitted to *observed delivery tours* would
already contain it. The repository applies both and has never asked whether
that is one correction or two.

---

## 4. Verbatim quotes

Three sources were opened and are quoted here: Larson & Odoni §6.4.8 (§4.1),
the two OpenAlex abstracts (§4.2, of which the Daganzo one is reproduced at
§2.1 and not repeated), and a 1991 doctoral thesis retrieved in full (§4.3).
**None of them is Daganzo (1984) itself.** §4.4 quotes the repository, which
is not a source at all.

### 4.1 Larson & Odoni, *Urban Operations Research* §6.4.8

Retrieved 2026-09-14 from
`https://web.mit.edu/urban_or_book/www/book/chapter6/6.4.8.html`. **This is
the source `cost/params.py:49-50` says "restates" our constant.**

The setup, quoted in full:

> "Assume that n points are randomly and independently dispersed over an
> area A with the location of each point determined by a uniform
> distribution over A (i.e., each point is equally likely to be anywhere in
> A). Assume further that an optimum traveling salesman tour has been drawn
> to cover the n points in question, and let L(n, A) be the length of this
> optimum tour through the n points in A. The following has then been shown
> to be true whenever the assumptions above hold [BEAR 59]:"
> — §6.4.8

The theorem itself then follows under the heading "Theorem" — and **it is an
image. The HTML text layer renders it as blank whitespace.** I did not see
the displayed equation. What I did see is the constant, in running text
immediately after it:

> "Recently, K has been estimated as being approximately equal to 0.765
> [STEI 78]. (An earlier set of simulation experiments had led to the
> estimate K [gap] 0.75 [EILO 71].)"
> — §6.4.8

*(The `[gap]` is mine. The retrieved text layer has a blank there; the
missing glyph is presumably an approximately-equal sign, and I have not
inserted one because this is a verbatim quote.)*

**That is 0.765, not 0.57.** See §6.3.

On the conditions of validity — this is the closest thing to an answer to Q6
that exists anywhere in reach:

> "Like all limit theorems, the one above must be used carefully. For
> instance, the value of n which is 'large enough' (for the quantity 0.765
> [gap: displayed formula is an image] to provide good approximations to the
> expected length of the optimal traveling salesman tour) depends on the
> shape of the area in which the n points are distributed uniformly. For
> 'fairly compact and fairly convex' areas (see also Section 3.7.1) it seems
> that surprisingly small values of n may be adequate. For example, n = 15
> or larger is quite adequate for equilateral triangles, circles, or squares
> (see [EILO 71])."
> — §6.4.8

And on robustness to the uniformity assumption being violated:

> "In closing this section, we note that, as long as points are reasonably
> well 'spread around' over a region, the expression 0.765 [gap] often
> provides good approximations to the length of optimum TSP tours, even in
> cases when the n points are not quite independently located or when the
> probability distribution for the location of individual points is not
> exactly uniform over the region. For instance, it has been estimated that
> the optimum tour through 48 major cities, one in each of the 48
> continental states in the United States, and Washington, D.C., is 10,070
> miles long, assuming Euclidean metric [BEAR 59]. Using instead the formula
> 0.765 [gap] with A the area of the continental United States (=
> 3,022,400 square miles), one obtains 9,310 miles, for an error of only
> about -7.5 percent, despite the fact that the 49 cities are far from
> randomly distributed..."
> — §6.4.8

That last passage is worth keeping for the defence: it is a published,
checkable instance of the approximation working to **-7.5%** on a
spectacularly non-uniform point set. It is the best available evidence that
the *structure* of the method tolerates our violations of its assumptions.

Finally, the section's own statement of what the formula is for, which
describes our use of it almost exactly:

> "The approximation formula 0.765 [gap] is a very useful one for:
> 1. Preliminary planning of urban collection and delivery systems (i.e.,
> for 'sizing up' the requirements for vehicle fleets, estimating the number
> of points that can be served with given resources, etc.)"
> — §6.4.8

Note the words **preliminary planning** and **sizing up**. Larson and Odoni
are describing a fleet-sizing instrument, not a ranking instrument. §6.6.

### 4.2 The two OpenAlex abstracts

Daganzo (1984), *Transportation Science* 18(4), 331-350 — reproduced in full
at **§2.1**, not repeated here.

Vaughan (1984), *Transportation Science* 18(3), 231-244 — reproduced in full
at **§1.1.1**, where it establishes that the repository's second citation is
somebody else's paper about a different subject.

### 4.3 A 1991 doctoral thesis, retrieved in full

`https://core.ac.uk/reader/139155` — *"The effect of time-window constraints
and fleet size on the cost of a distribution operation"*, 1991, 526,069
characters of extracted text, retrieved and searched 2026-09-14. The text
layer is OCR and carries visible artefacts; those are reproduced below rather
than silently cleaned, with my reading in square brackets.

This is a **secondary** source: it summarises Daganzo's papers, it does not
reprint them. It is quoted because it is the only retrievable document that
describes the structure of Daganzo's formula, and because it independently
corroborates Larson & Odoni on the BHH constant.

**On Daganzo's formula, and on there being two papers:**

> "Similar work using Continuous Space Modelling has been carried out by
> Daganzo, who calculates total distance travelled per drop from
> vehicle-capacity, the number of customers to be visited and a parameter
> representing the average of the distances from the depot to any random
> point in the delivery-area, (15). The same author also explores the impact
> of zone-shape on the expected length of travelling-salesman tours, thus
> illustrating the usefulness of deriving such analytical expressions for
> estimating the consequences of changing a given variable on the cost
> components of a distribution operation, (16)."
> — core.ac.uk/reader/139155, literature review

Read that carefully. It describes **distance travelled PER DROP** — per
stop, our quantity — as a function of exactly three things: *vehicle
capacity* (our `stops_per_tour`), *the number of customers* (our density,
via area), and *a parameter representing the average depot-to-point distance*
(our `linehaul_miles`). That is our formula, from an independent source, and
it is the best confirmation available that `daganzo.py`'s **structure** is
faithful. Their references (15) and (16) are two different Daganzo papers and
(16) is described as the zone-shape one — consistent with §1.4 Trap 2.

**On the BHH constant, independently of Larson & Odoni:**

> "Since heuristic algorithms, by definition, are liable to produce
> less-than optimum solutions to routing problems, it is useful to be able to
> estimate the difference between the algorithm's solution and the optimum.
> One way in which the cost of an optimum solution may be estimated is using
> a formula devised by Beardwood, Halton and Hammersley, (34). They suggest
> that the shortest distance that is required to pass through a set of points
> within an area of known size is, K. aO. 5. CO-5. [OCR of K · a^0.5 · C^0.5]
> (E. 2.3.) Where, K=a constant that has a value of approximately 0.75, a=
> the size of the area, and, C= is the number of points through which the
> route must pass."
> — core.ac.uk/reader/139155, section on bounding heuristic solutions

Two things this pins down, and both matter for §6.2:

```
  K ~= 0.75. A second, independent secondary source, agreeing with Larson
  & Odoni's 0.75 / 0.765 and disagreeing with our 0.57.

  BHH IS USED AS A LOWER BOUND ON HEURISTICS. The passage's whole purpose
  is to "estimate the difference between the algorithm's solution and the
  optimum" -- i.e. BHH gives the optimum, and a heuristic is measured by
  how far ABOVE it the heuristic lands. That is property P1 of §5.1,
  stated by somebody other than me, and it is why 0.57 cannot be the
  constant in the derivation printed at daganzo.py:16-19.
```

### 4.4 Quotes from the repository — NOT sources

These are quoted so that §6 can be checked line by line. They are our own
assertions and carry no evidential weight whatever.

> "0.57 is Daganzo's value for strip/ring-radial routing in a served zone.
> The asymptotic uniform-random TSP value is ~0.71; real routing beats
> random because drivers follow streets in sweeps. Using 0.57 is therefore
> the *optimistic* end, which biases cost DOWN"
> — `src/siting_atlas/cost/params.py:41-45`

> "SOURCE: Daganzo (1984), Transportation Science 18(3) 231-253 and 18(4)
> 331-350, on Beardwood, Halton and Hammersley (1959); Larson and Odoni,
> Urban Operations Research (1981) sec. 6.4.8 restates it."
> — `src/siting_atlas/cost/params.py:47-50`

> "It follows from the Beardwood-Halton-Hammersley theorem: a tour through n
> random points in area A has length ~ k*sqrt(n*A). One van covering C stops
> works an area C/delta, so its local distance is k*sqrt(C * C/delta) =
> k*C/sqrt(delta), and per stop that is k/sqrt(delta)."
> — `src/siting_atlas/cost/daganzo.py:16-19`

---

## 5. Definitions, stated formally

### 5.1 The Beardwood–Halton–Hammersley theorem

As set up by Larson & Odoni §6.4.8 (§4.1 above), in words, because the
displayed equation is an image I could not read:

```
  Let n points be independently and uniformly distributed over an area A.
  Let L(n, A) be the length of the OPTIMUM travelling-salesman tour
  through them, under a Euclidean metric. Then as n grows large,

        L(n, A)  ->  K * sqrt(n * A)

  for a constant K that does not depend on n or A.
```

Two properties of `K` that matter here and that the repository never states:

```
  P1  K is a property of the OPTIMUM tour, not of any tour. It is a LOWER
      limit on what any routing strategy can achieve on uniform random
      points. No heuristic, no street sweep, no clever driver gets below
      it, because there is nothing below the optimum.

  P2  K has no known closed form. Every value in circulation is a
      numerical estimate, and the estimates have moved over time.
      Larson & Odoni (1981) quote 0.765 (Stein 1978) and 0.75 (Eilon
      1971); the 1991 thesis at §4.3 independently says "approximately
      0.75". Those are the only two values RETRIEVED. A later and lower
      figure near 0.7124 is widely quoted in the modern literature -- NO
      source for that digit string could be retrieved from this host and
      it MUST NOT be quoted until somebody can. PARAMETERS.md §6.1
      already marks it [K] for exactly this reason and that marking is
      correct; do not upgrade it.
```

P1 is not my own reasoning. The 1991 thesis (§4.3) uses BHH for precisely
this purpose — *"Since heuristic algorithms, by definition, are liable to
produce less-than optimum solutions to routing problems, it is useful to be
able to estimate the difference between the algorithm's solution and the
optimum"* — and then gives K ≈ 0.75 as the optimum's coefficient. A routing
heuristic's constant sits **above** 0.75, not below it.

### 5.2 The three constants, which are three different objects

The single most important thing in this file. The repository's prose runs
them together and the code's variable name (`bhh_constant`) asserts they are
one thing.

```
  (i)   THE BHH CONSTANT.  Coefficient of sqrt(nA) in the length of the
        OPTIMUM closed tour through n uniform random points in area A.
        A limit theorem. Value: numerical estimate only; L&O say 0.765.

  (ii)  A STRATEGY'S CONSTANT.  Coefficient of sqrt(nA) for the tour a
        particular HEURISTIC produces -- strip sweep, ring-radial,
        nearest-neighbour. Necessarily >= (i), because (i) is optimal.
        Measured below: strip ~0.93, 2-opt ~0.78, nearest-neighbour ~0.93.

  (iii) DAGANZO'S LOCAL-TERM CONSTANT.  Coefficient of the LOCAL part of
        a decomposed VRP distance, where the rest of the distance has
        already been charged to a separate line-haul term. This need NOT
        be >= (i) and need not even be comparable to it, because it
        multiplies a different quantity -- part of the journey has been
        accounted for elsewhere.
        THIS is the only object 0.57 can plausibly be.
```

`cost/params.py:38` calls the variable `bhh_constant`, i.e. names it (i), and
sets it to a value that can only be (iii). That is not a naming quibble: it
is why the docstring derivation at `daganzo.py:16-19` is wrong (§6.2), why
the Larson & Odoni citation does not support the value (§6.3), and why the
Monte Carlo range is mis-centred (§6.5).

---

## 6. What this means for siting-atlas

### 6.1 Where the constant is set and used — every site

```
  src/siting_atlas/cost/params.py:38
      bhh_constant: float = 0.57
      (frozen dataclass field, docstring lines 39-52 quoted at §4.4)

  src/siting_atlas/cost/params.py:297
      "pessimistic_tour": CostParameters(bhh_constant=0.71),
      (the fifth sensitivity scenario)

  src/siting_atlas/cost/daganzo.py:158            <- THE ONLY USE SITE
      local = p.bhh_constant / np.sqrt(density) * p.circuity

  src/siting_atlas/optimize/montecarlo.py:96
      "bhh_constant": (0.45, 0.71),
      (the joint-sampling range. Sampled TRIANGULAR with the mode at the
       baseline -- montecarlo.py:143-161 -- so the mass concentrates ON
       0.57, not merely inside the interval.)

  tests/unit/test_cost_daganzo_math.py
      test_local_distance_equals_k_over_sqrt_density_times_circuity
      test_local_distance_is_proportional_to_the_bhh_constant
      (both pin the ARITHMETIC. Neither pins the VALUE, correctly --
       a test cannot know whether 0.57 is right.)
```

The full local-travel expression, quoted exactly from `daganzo.py:154-162`:

```python
    def distance_per_stop(self, density: pd.Series,
                          linehaul: pd.Series) -> pd.DataFrame:
        """The core equation, split so each term can be inspected."""
        p = self.params
        local = p.bhh_constant / np.sqrt(density) * p.circuity
        line = 2.0 * linehaul / p.stops_per_tour
        return pd.DataFrame({"local_miles_per_stop": local,
                             "linehaul_miles_per_stop": line,
                             "miles_per_stop": local + line})
```

`density` reaches it from `stop_density` (`daganzo.py:105-113`) as **stops
per square mile of LAND area** — daily parcels / 1.4 parcels per stop,
divided by `land_area_sqmi`. `linehaul` reaches it from `linehaul_miles`
(`daganzo.py:116-152`) as great-circle miles to the nearest solved depot,
already multiplied by circuity. Note that **circuity is applied twice, on two
different lines, to two different terms** — once inside `linehaul_miles` at
line 152 and once again to `local` at line 158.

Everything downstream is arithmetic on `miles_per_stop`
(`daganzo.py:182-202`): a per-mile cost, a per-hour driver cost at 22 mph, a
flat service time and a flat lease share. So `bhh_constant` enters the whole
project through exactly one multiplication.

### 6.2 The docstring derivation demands the BHH constant, and 0.57 is not it

This is the finding. `daganzo.py:16-19` derives the local term like this:

> "a tour through n random points in area A has length ~ k*sqrt(n*A). One
> van covering C stops works an area C/delta, so its local distance is
> k*sqrt(C * C/delta) = k*C/sqrt(delta), and per stop that is k/sqrt(delta)."

Read what that says. It models the van's local travel as **a complete closed
tour through C points uniformly scattered in an area of C/delta square
miles** — which is, word for word, the BHH setting of §5.1. Under that
derivation `k` *is* the BHH constant, and by property P1 the BHH constant is
a **lower** limit: no tour of any kind through uniform random points is
shorter than `K * sqrt(nA)`.

So the derivation as printed forbids `k < K`. Setting `k = 0.57` asserts a
tour roughly 20-25% shorter than the optimum. That is not conservative or
optimistic; within that derivation it is impossible.

**Measured, 2026-09-14** (`/tmp/tspsim.py`, numpy, seed 20260914; points
uniform in the unit square, so `sqrt(nA) = sqrt(n)`; `k = L / sqrt(n)`):

```
     n   reps   nearest-neighbour   NN + full 2-opt      sd(2-opt)
   100     12         0.9822              0.8270           0.0357
   300      8         0.9351              0.7977           0.0106
   600      5         0.9138              0.7816           0.0112
  1000      3         0.9315              0.7778           0.0089
```

and a boustrophedon strip sweep with the strip width optimised by line search
(`/tmp/strip.py`, seed 7):

```
     n     strip-strategy k
   500           0.9649
  2000           0.9365
  8000           0.9309
```

Nothing gets near 0.57. 2-opt converges from above towards the high 0.70s,
consistent with an optimum in the low 0.70s; the strip sweep — which is the
strategy `params.py:41` names — sits at **0.93**, well above both. The
constant for the strategy the docstring appeals to ("drivers follow streets
in sweeps") is *larger* than the random-TSP constant, not smaller, because a
sweep is a heuristic and heuristics lose to the optimum.

**So `params.py:41-45`'s justification is backwards on its own terms.** It
says 0.57 is defensible because "real routing beats random". Real routing
does not beat the *optimal* tour through random points; that is what optimal
means. A street sweep is a constrained heuristic and measures 0.93.

**What this does NOT prove.** It does not prove 0.57 is wrong. It proves
that *if* 0.57 is right, it is right as object (iii) of §5.2 — a decomposed
VRP local-term constant, where some of the travel the simulation above counts
has been booked to the `2L/C` line-haul term instead — and the docstring's
BHH derivation is simply not the derivation that produces it. **That is the
thing to check in the paper (§3, Q2 and Q5).** Until somebody does, the
correct statement in a viva is: *"0.57 is Daganzo's; the derivation printed
in our docstring is the BHH one and the two are not the same argument; I have
not reconciled them."*

### 6.3 The corroborating citations: one is somebody else's paper, another says 0.765

`cost/params.py:47-50` offers four supports for 0.57. Taken one at a time:

```
  Daganzo (1984), Transportation Science 18(4) 331-350
      REAL, and the right paper for the STRUCTURE (§2.1 abstract). Not
      read. Does not state 0.57 anywhere anyone can currently check.

  Daganzo (1984), Transportation Science 18(3) 231-253
      NOT A DAGANZO PAPER. It is Vaughan (1984), pp. 231-244, and it is
      about average distances between random points in zones -- no
      tours, no vehicles, no constant (§1.1.1). It supports nothing.
      One of the two named sources for the most load-bearing number in
      the project is a mis-citation.

  Beardwood, Halton & Hammersley (1959)
      REAL, not read, details in REFERENCES.md marked [K] from memory.
      What IS retrievable about it (§4.1, §4.3) says its constant is
      0.75 to 0.765 and is a LOWER limit. So it does not support 0.57
      either -- it contradicts it under our own derivation (§6.2).

  Larson & Odoni (1981) §6.4.8 "restates it"
      READ IN FULL. It does not restate 0.57. See below.
```

So of four supports, one is real-but-unread, one is a different author's
paper, and two state a value 31-34% higher. **`bhh_constant = 0.57` currently
has no source that survives being looked up.**

On the fourth. `cost/params.py:49-50` says Larson & Odoni §6.4.8 "restates
it". I read
§6.4.8 in full (§4.1). It states **K ≈ 0.765**, citing Stein (1978), and
notes an earlier estimate of 0.75 from Eilon (1971). It does not mention
Daganzo. It does not mention 0.57. It does not mention a decomposed VRP at
all — its worked Example 10 sizes a parcel fleet by computing one grand TSP
tour and then dividing it into four.

0.765 is **34% above** our 0.57.

`params.py:47-50` must be corrected, and it is a five-minute job. A draft
replacement, which somebody who owns `src/` should sanity-check and apply:

```
  SOURCE, INCOMPLETE -- see docs/research/NOTES_daganzo_1984.md.
  The STRUCTURE (line haul over a tour of C stops, plus local travel in
  1/sqrt(density)) is Daganzo (1984), Transportation Science 18(4)
  331-350, unread. The VALUE 0.57 has no source anyone has checked:
  it is NOT the Beardwood-Halton-Hammersley constant, which Larson &
  Odoni, Urban Operations Research (1981) sec. 6.4.8 give as ~0.765 for
  the OPTIMUM tour through uniform random points -- a lower limit that
  0.57 sits 25% below. If 0.57 is right it is Daganzo's coefficient for
  a decomposed VRP local term, a different object; the derivation in
  daganzo.py's docstring is the BHH one and does not produce it. Worth
  1.2% on the median, so the priority is honesty, not accuracy.
```

Two other repairs in the same pass. `pessimistic_tour` at
`params.py:297` sets 0.71 and is described as pessimistic; on the evidence
here 0.71 is roughly the *optimum* and the pessimistic value is nearer 0.93
(§6.2). And the field name `bhh_constant` itself asserts the identification
that §5.2 says is wrong; `local_tour_constant` would be honest. Neither is
urgent.

### 6.4 What the constant is actually worth, re-measured

Recomputed on 2026-09-14 directly from the stored baseline table
(`outputs/tables/cost_to_serve_2023q4_baseline.parquet`, 2,333 ZCTAs) by
rescaling `local_miles_per_stop` and re-deriving cost — no re-run, no other
parameter touched:

```
        k    median $/parcel    vs 0.57       p10       p90    Spearman
                                                              (rank vs base)
   0.4500             1.0747     -0.76%    0.9734    1.3765      0.998795
   0.5700             1.0830      0.00%    0.9778    1.4180      1.000000
   0.7124             1.0926     +0.88%    0.9839    1.4699      0.998712
   0.7500             1.0950     +1.11%    0.9850    1.4835      0.998033
   0.7650             1.0960     +1.20%    0.9856    1.4897      0.997745
   0.9000             1.1054     +2.07%    0.9904    1.5336      0.994385
   1.1547             1.1242     +3.81%    0.9996    1.6270      0.986230
```

And the strongest version of the same test — **delete Daganzo's local term
entirely**, k = 0:

```
   k = 0:  median $1.0406  (-3.91%)   Spearman vs baseline 0.952
           88 of the cheapest 100 ZCTAs are still in the cheapest 100
```

So: correcting 0.57 to Larson & Odoni's 0.765 moves the headline **+1.20%**.
Deleting the term the module is named after moves it **-3.91%** and keeps 88%
of the top ranking. `PARAMETERS.md` §3.1's verdict — *"the routing
mathematics is decoration"* — is confirmed and is if anything understated.

Three consequences, and they pull in different directions:

```
  1  The error identified in §6.2 does not threaten any headline number.
     Even the most extreme defensible constant costs under 4%.

  2  It therefore also cannot be waved away as "we would have noticed".
     Nothing downstream could detect it. That is precisely the class of
     error that survives to a viva.

  3  It is CHEAP to fix -- one constant and two docstrings -- and the fix
     turns "we used an undefended number" into "we used the published
     number and measured the difference at 1.2%". Do it.
```

A caution on how to quote the sensitivity: **the median is the least
sensitive statistic in the table.** The p90 moves from $1.4180 to $1.4897 at
k = 0.765, a **+5.1%** shift, because the sparse tail is where local travel
is the bill. Quoting "+1.2%" without saying it is a median effect overstates
how robust the sparse end is.

### 6.5 The Monte Carlo range is mis-centred

`optimize/montecarlo.py:96` samples `bhh_constant` on **(0.45, 0.71)**,
triangular with the mode at the baseline 0.57 (`montecarlo.py:143-161`; the
module docstring at lines 47-51 explains the choice, and it is a good one).
`PARAMETERS.md` §6.1 justifies the interval: *"The upper end is the asymptotic
uniform-random-TSP constant; the lower end is aggressive strip routing."*

Both halves of that sentence are wrong in the same direction.

```
  The upper end is not an upper end. If 0.71 is the asymptotic
  uniform-random-TSP constant, then by property P1 it is the SMALLEST
  value any tour through uniform random points can take. The range
  should start there, not end there.

  The lower end is not strip routing. Strip routing measures 0.93
  (§6.2), the LARGEST of the three strategies tested, not the smallest.
```

So the sampled interval lies entirely at or below the optimum, and because
the draw is triangular with its mode at 0.57, the distribution is not merely
bounded below the optimum — its mass is piled on a point 20% below it. If the object being sampled is the
BHH constant, the interval should be something like **(0.71, 0.95)** — from
the optimum to a strip sweep. If the object is Daganzo's decomposed local
constant, the interval must be justified from the paper, and cannot be
justified from BHH at all.

This is the one place where the error has a second-order consequence worth
naming: `UNCERTAINTY.md` §8 item 5 currently advises *"Do not commission a
better estimate of ... bhh_constant"*, on the strength of joint sampling that
never sampled a value above 0.71. The advice happens to survive — §6.4 shows
even k = 1.1547 moves the median only 3.81% — but it was not entitled to,
and the reasoning should be repaired even though the conclusion holds.

### 6.6 WHERE THE APPROXIMATION BREAKS

More important than where it works. Four tests, all run 2026-09-14 on the
stored baseline table.

**Break 1 — the asymptotic condition, and it mostly holds.** The derivation
assumes a van fills a tour of C = 120 stops inside the zone whose density is
being used. Where a ZCTA generates fewer than 120 stops a day, the van's
working area is *larger than the ZCTA*, the tour necessarily leaves it into
land of a different density, and the model is charging the ZCTA's own —
extremely low — density for travel that does not happen there.

```
   126 of 2,333 (5.4%)  generate < 120 stops/day: one tour does not fit
    29 of 2,333 (1.2%)  generate < 15 stops/day, below the n >= 15 that
                        Larson & Odoni call "quite adequate" for compact
                        convex areas -- so these are below even the most
                        generous stated threshold in reach
     0 of 2,333         generate < 1 stop/day

   the 126: median density 13.4 stops/sq mi, median land area 2.7 sq mi,
            median IMPLIED TOUR AREA C/delta = 9 sq mi -- i.e. the van's
            zone is more than three times the ZCTA
            they carry 0.070% of pilot parcels but 0.94% of local miles
            median cost $1.4595 vs pilot $1.0830; cost ranks 389-2333,
            median rank 2118 -- they are the expensive tail
```

The honest reading: **the approximation is in its valid regime for ~95% of
the pilot**, the failures are concentrated in the sparse tail, they carry
0.07% of volume, and they are already reported as expensive. This is a real
limitation and a small one — but it is a limitation nobody had written down,
and it is the one a routing examiner will go for.

**Break 2 — the uniformity condition, untested.** BHH requires the points
uniform within the area. Our `delta` is a single number per ZCTA, and a ZCTA
with a dense village and empty farmland has the same `delta` as one with its
households evenly spread. The approximation *understates* cost in the first
case. This is not measurable from the panel, which carries no sub-ZCTA
geography. Larson & Odoni's 48-cities example (§4.1) is the only evidence in
reach that the method tolerates gross non-uniformity, and it is one data
point at -7.5%.

**Break 3 — the shape condition. This is the one, and it is now backed by
Daganzo's own words.** Q6(c) of §3.

Two retrieved statements, one from each side:

> "Our procedure is characterized by the way district shapes are chosen;
> **ignoring shape during the clustering step can increase significantly
> travel distances.**"
> — Daganzo (1984), TS 18(4), abstract (§2.1). Emphasis mine.

> "the value of n which is 'large enough' ... depends on the shape of the
> area in which the n points are distributed uniformly. For 'fairly compact
> and fairly convex' areas ... it seems that surprisingly small values of n
> may be adequate."
> — Larson & Odoni §6.4.8 (§4.1)

And there is a third Daganzo 1984 paper whose entire title is *The length of
tours in zones of different shapes* (§1.4), with 274 citations.

**Zone shape is the thing this literature is about, and the repository does
not represent it at all.**

```
  What we have:   land_area_sqmi. One number. A scalar area.
  What we need:   a compactness measure -- Polsby-Popper, Schwartzberg,
                  or simply the ratio of the zone's diameter to sqrt(area).
  What we do:     apply a single constant to all 2,333 ZCTAs as though
                  every one of them were a compact convex district.
```

ZCTAs are the worst possible case for this. They are not districts anybody
designed to be routed — they are approximations to USPS postal-delivery
routes, and a delivery route is *by construction* a long thin thing that
follows roads. Some pilot ZCTAs are ribbons along a highway. Daganzo's
procedure **chooses** district shapes; we inherit shapes chosen by the Postal
Service for a different purpose, and then apply the constant that the paper
says depends on the choice.

It is also the cheapest gap on this list to close. The TIGER/ZCTA shapefiles
are already ingested (`data/tiger_zcta.md`); a Polsby-Popper score is one
GeoPandas expression, `4*pi*area / perimeter**2`. Computing it would let us
say either "our ZCTAs are compact enough" or "here are the n ZCTAs where the
approximation should not be trusted" — and either sentence is worth more in a
viva than the sensitivity table, because it answers a question about
*validity* rather than about *robustness*. **Recommended as the single
highest-value follow-on from this file.**

Note what it would NOT do: since the local term is only 3.7% of the median
bill (§6.4), a shape correction cannot move the headline. It would move the
*defensibility*, which is the thing currently missing.

**Break 4 — and this is the one that matters — the approximation is valid
and NOT DECISIVE.** The repository's narrative gives Daganzo's 1/sqrt(density)
credit for the shape of the answer. It does not deserve most of it.

```
  At the DENSE end the formula is right and irrelevant. Cost per parcel
  has a floor -- service time plus van lease -- which is completely
  independent of density:

       service + lease, per parcel:  median $0.9489
                                   = 87.6% of the median ZCTA's cost
       in the CHEAPEST decile:       $0.8518 = 89.2% of their cost
       Daganzo's local term there:   $0.02552 = 2.67% of their cost

  So among the cheapest ZCTAs the routing geometry is 2.7% of the bill.
  And it does not even drive the variation WITHIN that group:

       within the cheapest decile,  sd of cost            $0.0304
                                    sd of the floor       $0.0452
                                    sd of Daganzo's term  $0.0114

  The floor's spread is four times the Daganzo term's. What separates
  one cheap ZCTA from another is the DRIVER'S WAGE, not the geometry.
```

That shows up directly in the density deciles. The law is doing real work at
the sparse end and almost none at the dense end:

```
  density decile   median stops/sq mi   median $/parcel
        0                      5.2            1.7065
        1                     39.9            1.2627
        2                    120.3            1.1575
        3                    246.1            1.1096
        4                    397.1            1.0842
        5                    561.1            1.0627
        6                    740.9            1.0594
        7                   1008.9            1.0369
        8                   1692.3            1.0248
        9                   5793.3            0.9951
```

Decile 0 to decile 3 is a 47-cent fall. Decile 8 to decile 9 is **3 cents**,
for 3.4 times the density. Spearman(cost, density) is -0.76 over the whole
pilot but only **-0.34 within the densest quartile**.

And across metros the ranking is a **wage** ranking, not a density ranking:

```
                       n   median $/pcl   median density   implied $/hour
  Miami              181        0.9437            696.8            21.27
  New York           848        1.0445            597.3            24.67
  Phoenix            161        1.0847            375.6            24.51
  Austin              88        1.1044            119.2            23.75
  Denver             131        1.1105            426.1            25.69
  Chicago            378        1.1111            397.8            25.75
  Seattle            161        1.1283            490.4            26.15
  San Francisco BA   237        1.1449            709.5            27.63
  Nashville          108        1.3084             21.9            23.22
  Boise               40        1.4349             29.7            25.71

  The San Francisco Bay Area is the DENSEST metro in the pilot and the
  second most expensive. Miami is cheapest at a LOWER density.
  Miami vs New York: total cost gap $0.1009/parcel, of which the
  service-time (wage) gap alone is $0.0971 -- 96% of it.
```

### 6.7 The "0 of 40" finding: is that the approximation's failure or ours?

`docs/ALTERNATIVES.md:180-187` reports that of 40 pilot facilities ranked by
cost-to-serve *within their own metro*, zero fall in their metro's cheapest
decile, and explains it:

> "That is not a broken cost model. Under Daganzo, cost falls as one over the
> square root of density, so the cheapest ZIPs to serve are the densest ones
> — central Manhattan — and those are precisely where you cannot build a
> warehouse. **Feasibility binds before economics.**"
> — `docs/ALTERNATIVES.md:182-186`

**The conclusion is right. The mechanism is only about 40% right, and the
part that is wrong is the part that names Daganzo.**

What is right: within a metro, the cheapest ZCTAs really are the densest.
Checked — the cheapest ZCTA in the New York metro is **10021, Upper East
Side, rank 1 of 848**, at 27,984 stops/sq mi, and the cheapest NY decile has
median density 6,150 against a metro median of 597. The sentence's claim
about within-metro ranks stands.

What is wrong is the attribution. Look at what those cheap ZCTAs have in
common:

```
  Cheapest 12 in the New York metro
    zcta    $/parcel   stops/sq mi   linehaul mi
   10021      0.9540       27,984          0.00
   10003      0.9547       21,474          0.00
   10023      0.9551       18,814          0.00
   10026      0.9558       15,392          0.00
   11372      0.9563       13,214          0.00
   11201      0.9566       12,398          0.00
   11226      0.9568       11,809          0.00
   07302      0.9575        9,872          0.00
   10468      0.9580        8,814          0.00
   10452      0.9581        8,672          0.00
   11233      0.9581        8,663          0.00
   11211      0.9584        8,104          0.00

  EVERY ONE has line haul exactly 0.00 -- a depot placed inside it.
```

Depots are placed by solving a p-median over parcel volume (`cost/depots.py`,
`NOTES_klose_drexl_2005.md` §6), so **depots land on the density peaks by
construction**. The density-cheapness link therefore runs through *two*
channels, and the model built the second one itself:

```
  within-metro spread of cost per parcel, p90 - p10, decomposed:

    metro               total    Daganzo local term    line-haul term
    New York           0.2153               0.0920            0.1367
    Chicago            0.4286               0.1862            0.2327
    San Francisco BA   0.3218               0.1529            0.2001
    Miami              0.1372               0.0364            0.1121
    Boise              2.4548               1.1549            1.1286

  and the rank correlations, within metro:
    rho(cost, density)  -0.60 to -0.96
    rho(cost, linehaul) +0.89 to +0.98    <- consistently the stronger
```

Line haul carries roughly 60% of the within-metro spread and Daganzo's local
term roughly 40%, and line haul is the endogenous one. Freezing the local
term at its metro median still leaves rho(cost, density) between -0.44 and
-0.92 — the depot network alone reproduces most of the gradient.

**So the answer to "is this a failure of the approximation or of how the
project uses it?" is: neither, and a third thing.**

```
  NOT the approximation. Daganzo's formula is in its valid regime for
  95% of the pilot (§6.6 Break 1), it produces the right qualitative
  shape, and correcting its constant to the published value moves the
  headline 1.2%. It is not broken and it is not being abused.

  NOT really the application either. The model answers "what would it
  cost to serve here" correctly and COST_MODEL.md §6.2 already says in
  bold that a cheap ZCTA is not a prediction that anyone will build
  there. The model is correctly scoped and honestly captioned.

  IT IS AN ATTRIBUTION ERROR IN THE NARRATIVE, and a category error in
  what is being asked of the tool.

    (a) ATTRIBUTION. ALTERNATIVES.md:183 credits "under Daganzo, cost
        falls as one over the square root of density" for a gradient
        that is ~60% produced by a depot network we placed ourselves at
        the density peaks, and, across metros, is dominated by wages.
        Saying "under Daganzo" makes an endogenous modelling choice
        sound like a law of routing geometry. Fix the sentence.

    (b) CATEGORY. Larson & Odoni describe this family of formula as an
        instrument for "preliminary planning" and "sizing up" fleets
        (§4.1). It is an ENGINEERING-ECONOMICS instrument. The 0-of-40
        test asks it to RANK CANDIDATE SITES, and a site ranking needs a
        feasibility constraint the formula has no way to express: there
        is no term in 2L/C + k/sqrt(delta) for "can you get planning
        permission on this block". Feasibility binding before economics
        is not a defect of the approximation; it is a question the
        approximation was never built to answer.
```

The defence to give, therefore, is **not** "Daganzo explains why Amazon
avoids the cheapest ZIPs". It is: *"Cost-to-serve and buildability are
different variables. Our cost model measures the first correctly and says
nothing about the second, and the 0-of-40 result is the measurement of how
far apart they are. That is why ALTERNATIVES.md Option C prices a specific
parcel somebody is already considering rather than ranking all ZIPs."*
`ALTERNATIVES.md:189-190` already says exactly that — *"So the tool prices a
SPECIFIC parcel somebody is already considering. It does not rank all ZIPs
and it must not be sold as though it does."* It is the paragraph immediately
before it, lines 182-187, that needs repairing.

### 6.8 Every assumption the project inherits without testing

Consolidated. The first six are inherited from the approximation; the rest
are the project's own additions to it that nobody has separated out.

```
  A1  THE CONSTANT ITSELF. 0.57, with no page behind it, defended by a
      derivation that implies a different value (§6.2) and a citation
      that states a different value (§6.3).   UNTESTED. The subject of
      this file.

  A2  UNIFORMITY. Points uniform within the zone. The panel has no
      sub-ZCTA geography, so this is untestable as the data stand.
      UNTESTED and currently UNTESTABLE.

  A3  ZONE SHAPE / COMPACTNESS. Larson & Odoni make the adequate n
      depend on it. No compactness measure exists anywhere in the repo.
      Computable from the TIGER/ZCTA shapefiles already ingested.
      UNTESTED, and cheap to test.  <- the best-value item on this list

  A4  ASYMPTOTICS. That C = 120 is "large". Tested here for the first
      time (§6.6 Break 1): holds for 94.6% of ZCTAs, fails for 126.

  A5  EUCLIDEAN METRIC, corrected by a circuity multiplier. Whether
      Daganzo's constant is already a road-distance constant -- in which
      case daganzo.py:158 double-counts -- has never been asked (§3 Q8).
      UNTESTED.

  A6  THAT THE ZONE IS THE UNIT OF ROUTING. The formula describes one
      van's tour. The code applies it per ZCTA, and a real van crosses
      ZCTA boundaries. daganzo.py:204-211 already admits this for
      van-days ("a real route crosses ZCTA boundaries, so a ZCTA with
      two stops a day is two stops on somebody else's round") -- and
      then charges that ZCTA its own isolated density anyway. The
      admission and the arithmetic contradict each other.  UNTESTED.

  A7  C = 120 STOPS PER TOUR is an unsourced estimate (params.py:54-63,
      marked ESTIMATE) and it enters the SAME formula. The constant has
      a citation and the capacity it is paired with does not.

  A8  CIRCUITY APPLIED TWICE. daganzo.py:152 applies it to line haul and
      daganzo.py:158 applies it again to the local term. Defensible --
      both are road distances -- but it means circuity scales the whole
      distance vector, which is not how the sensitivity tables describe
      it.  Noted, not a bug.

  A9  DENSITY IS MODELLED, NOT OBSERVED. delta is derived from ACS
      households x 3.2 parcels x an income scaling / 1.4 / land area.
      Three unsourced parameters sit between the census and the quantity
      the approximation consumes. COST_MODEL.md §7.2 rule 3 already says
      "look at stop_density_per_sqmi before you believe a rank"; that
      rule is the right one and it is about A9.

  A10 THE FORMULA IS USED FOR RANKING, NOT SIZING. §6.7(b).
```

---

## 7. What I did NOT read, and what must be checked

### 7.1 The paper. Any of them.

**Not read. Not on disk. Not obtainable from this host.** The abstract of
Transportation Science 18(4) was retrieved (§2.1); the body of it, and of
every other paper below, was not. Everything in §2.2 and §5 is reconstructed
from Larson & Odoni, from the 1991 thesis at §4.3, and from our own code.

Specifically not established, and each of these is currently asserted
somewhere in the repository without support:

```
  1  That "0.57" appears in Daganzo (1984) at all. NOT ESTABLISHED. No
     retrieved source states it. params.py:41 and REFERENCES.md §2 both
     assert it; neither cites a page.

  2  SETTLED, AND THE ANSWER IS "NEITHER". REFERENCES.md assigns the
     constant to Transportation Science 18(3) 231-253. That DOI is
     Vaughan (1984), pp. 231-244, a different author writing about a
     different thing (§1.1.1). So the constant does NOT come from there.
     Whether it comes from 18(4) 331-350 is still open -- its abstract
     (§2.1) is consistent with it but does not state a number.

  3  SETTLED AND CONFIRMED: "The length of tours in zones of different
     shapes", Transportation Research Part B 18(2) 135-145, DOI
     10.1016/0191-2615(84)90027-4, Daganzo, April 1984, 274 citations
     (§1.4, Trap 2). It EXISTS, it predates the Transportation Science
     paper, and the repository does not cite it. **READ THIS ONE FIRST.**
     Its title is the closest match to what bhh_constant is supposed to
     be, the 1991 thesis (§4.3) describes it as the zone-shape paper,
     and Daganzo's own TS abstract says shape is what their procedure
     turns on.

  4  What routing strategy 0.57 is the constant FOR. params.py:41 says
     "strip/ring-radial routing in a served zone". NOT ESTABLISHED, and
     the simulation in §6.2 measures a strip sweep at 0.93, so the
     "strip" half of that claim is in active tension with measurement.

  5  Whether Daganzo's decomposition books part of the tour to line haul
     in a way that legitimately makes their local constant smaller than
     BHH's. This is THE question. If yes, 0.57 is fine and only our
     docstring is wrong. If no, the constant is wrong.

  6  Every stated condition of validity. §3 Q6.

  7  The Beardwood-Halton-Hammersley paper itself (1959). Not read, not
     on disk, and the volume/issue/pages in REFERENCES.md are marked [K]
     -- from memory. Unverified.

  8  Stein (1978) and Eilon (1971), which are where Larson & Odoni's
     0.765 and 0.75 come from. Not read. I have them only as the
     bracketed tags [STEI 78] and [EILO 71] in the HTML; §6.4.8's own
     reference list was not retrieved, so I do not have full citations
     for either.

  9  The value ~0.7124 for the BHH constant. Widely quoted in the modern
     literature; NO source for it could be retrieved from this host, and
     a dedicated search found none. It appears in the §6.4 table above
     ONLY as a scenario label, not as a claim. PARAMETERS.md §6.1 marks
     it [K] and says "should not be quoted without checking" -- that
     marking is correct and must stay. The two values that WERE
     retrieved are 0.765 (Larson & Odoni, citing Stein 1978) and ~0.75
     (Larson & Odoni citing Eilon 1971, and independently the 1991
     thesis at §4.3). Quote those, not 0.7124.

  9b Merchan & Winkenbach, "An empirical validation and data-driven
     extension of continuum approximation vehicle routing models" (MIT,
     2019), hdl.handle.net/1721.1/140763. LOCATED, NOT OBTAINED -- the
     handle redirects to dspace.mit.edu, which this host cannot reach.
     On its title it is the most likely open source for both the 0.57
     attribution and the BHH-versus-Daganzo relationship, and it is an
     EMPIRICAL VALIDATION of exactly the approximation we are using,
     which is the thing ALTERNATIVES.md:152 says we cannot do. Get it
     from a machine with normal network access; it is the highest-value
     single download available to this project.

 10  Daganzo & Smilowitz (2004), listed in REFERENCES.md §2 with its
     title UNCONFIRMED. The URL is on users.iems.northwestern.edu, which
     this host cannot reach (503 from the proxy).

 11  Daganzo, Logistics Systems Analysis (Springer, any edition), which
     READING_LIST.md item 7 downgraded on 2026-09-13 on the grounds that
     bhh_constant is insensitive. That reasoning was about the VALUE.
     This file's problem is the DERIVATION and the CONDITIONS, which the
     book's textbook treatment would settle and sensitivity analysis
     cannot. RECOMMEND RE-UPGRADING IT -- it is the single most
     obtainable item on this list and it answers Q2, Q4, Q5 and Q6 at
     once.
```

### 7.2 What I did do, and its limits

```
  * Retrieved the Daganzo TS 18(4) and Vaughan TS 18(3) records and
    abstracts from api.openalex.org, and the Daganzo TR-B 18(2) record.
    OpenAlex is an AGGREGATOR, not the publisher. Each record was
    fetched twice, independently, and they are internally consistent
    (venue, volume, issue, plausible pages, citation counts that match
    the papers' reputations). They should still be confirmed against
    INFORMS and Elsevier by somebody whose network can reach them
    before anything here goes into a submitted bibliography.

  * Retrieved and searched the full text of core.ac.uk/reader/139155, a
    1991 doctoral thesis. Read only the ~1,000 characters around each
    occurrence of "Daganzo", "Beardwood" and "Halton", NOT the whole
    526,000-character document. Its reference numbers (15), (16) and
    (34) were NOT resolved -- its bibliography was not retrieved -- so
    "the same author also explores the impact of zone-shape" is that
    thesis's characterisation and not a confirmed identification of the
    TR-B paper. The OCR is poor and is reproduced with its artefacts.

  * Searched deliberately for a source stating 0.57 attributed to
    Daganzo, across OpenAlex, CORE full text and every reachable
    repository. FOUND NOTHING. That is a null result from a restricted
    network, not evidence the attribution is wrong -- but it does mean
    nobody on this project has ever seen the number in a source.

  * Read Larson & Odoni §6.4.8 in full from the MIT web edition. The
    displayed equations are IMAGES and are absent from the text layer, so
    I have the theorem's setup and its constant in prose but have NOT
    seen the formula as typeset. Every gap is marked in §4.1.

  * Did NOT read the rest of the Urban Operations Research chapter 6, or
    §3.7.1 which §6.4.8 cross-references for the compactness discussion.
    §3.7.1 is the obvious next click and would speak to A3.

  * Ran four numerical experiments (§6.2, §6.4, §6.6, §6.7). Scripts are
    in /tmp and are NOT part of the repository; they are throwaway and
    will not survive a reboot. If any number from them is quoted in the
    dissertation, move the script into tools/ first.
      - The TSP simulation uses nearest-neighbour + 2-opt, which is NOT
        optimal. Its 0.778 at n = 1000 is an UPPER bound on the BHH
        constant, not an estimate of it. The argument in §6.2 only needs
        an upper bound, so this is sufficient -- but do not quote 0.778
        as "the BHH constant".
      - n = 1000 with 3 replicates has visible sampling noise (sd 0.009)
        and boundary effects are still shrinking at that n.
      - The strip simulation optimises strip width by a 40-point line
        search, not analytically. My own closed-form attempt gave
        2/sqrt(3) = 1.1547 by summing the longitudinal and lateral
        components in L1; the simulation says 0.93, and the simulation is
        right -- the components combine in L2. The 1.1547 row in the
        §6.4 table is therefore a loose upper bound and is labelled as a
        value, not as a derivation.

  * Re-derived §6.4's sensitivity ARITHMETICALLY from the stored parquet
    rather than by re-running cost.runner, to avoid writing outputs while
    other work was live. The rescaling is exact (the local term is
    linear in k and every other component is untouched), but it does NOT
    re-solve the depot network -- which is correct here, since k does not
    enter depot placement.

  * CHECKED and CONFIRMED PARAMETERS.md §3.1's claim that bhh_constant
    moves the median "1.9% when wrong by half". Recomputed: k = 0.285
    gives -1.85% and k = 0.855 gives +1.78%, so 1.9% is the right order
    on both sides and the claim stands. Note it is a +/-50% figure, NOT
    the effect over the sampled (0.45, 0.71) range, which is only
    -0.76% / +0.87%. Quote it with the "wrong by half" qualifier
    attached or it reads as three times more alarming than it is.
```

### 7.3 Follow-on work — the other citations with no notes file

Listed from `docs/AUDIT_2026_09_14.md` §5.2 for completeness. **None of these
is addressed by this file and none should be written by whoever writes the
next one without reading the source first.**

```
  Beardwood, Halton & Hammersley (1959)
      cited at cost/params.py:38-52 and REFERENCES.md §2 [K].
      Carries a numeric constant. Same problem as this file, one level
      down. Would be folded into a revision of THIS file rather than
      given its own, since it is the same constant.

  Andrews-Guggenberger and Andrews-Soares
      METHODS_RESEARCH.md:209, 290, 859. Three citations supporting a
      methodological position about uniformity, used to argue AGAINST
      reporting a Holmes-style CI as a parameter CI. The audit calls
      this "a strong methodological claim resting on three unread
      citations" and suggests downgrading them to leads, the way
      choice_sandwich.py:21 already does for Andrews (1999). That is the
      honest 20-minute option.

  Fienberg (1972), Belin & Rubin (1995)
      cited in the linkage code. No notes file.

  Jaro (1989)
      covered indirectly by NOTES_winkler_rr99_01.md. Lowest priority.

  cost/depots.py:35 cites "Klose and Drexl (2004)"; the notes file is
  NOTES_klose_drexl_2005.md. The audit calls this a 2-minute fix. It is
  NOT a simple typo -- NOTES_klose_drexl_2005.md §1 explains that the
  copy on disk is the 2004 "article in press" proof and the version of
  record is 2005, so BOTH years are defensible and the repository should
  simply pick one and say why. Not touched here; not this file's.
```

---

## 8. The one-paragraph answer, for the viva

*"Daganzo's continuous approximation replaces a vehicle-routing problem with
a formula: distance per stop is line haul shared across a tour, `2L/C`, plus
local travel that falls as one over the square root of stop density,
`k/sqrt(delta)`. We implement it at `cost/daganzo.py:158`. I have not read the
1984 paper — it is paywalled and unobtainable from the machine this was built
on — and I want to be straight about what that cost us, because when I went
looking I found three things.*

*First, one of the two papers we cited for the constant turned out to be by
somebody else: the DOI we gave is R. J. Vaughan's, not Daganzo's, it is about
average distances between random points rather than tour lengths, and our
page range was wrong too. That is a mis-citation and I have documented it
rather than quietly deleted it. Second, the paper that probably IS the source
— Daganzo's 'The length of tours in zones of different shapes' — we never
cited at all. Third, the constant. We use k = 0.57, and the derivation
printed in our own docstring is the Beardwood–Halton–Hammersley one, which
gives a constant of roughly 0.75 and is a lower limit — no tour beats the
optimum. Larson and Odoni, whom we cite as corroboration, say 0.765. So
either 0.57 is Daganzo's coefficient for a different decomposition, which is
what I believe and could not verify, or it is simply too low.*

*Then I measured what it is worth. Moving it to 0.765 moves our headline
1.2%; deleting the local term altogether moves it 3.9% and still keeps 88 of
the cheapest 100 ZIPs. The routing mathematics is the most robust thing in
the cost model and the least consequential — three quarters of the bill is
labour, and the parameters carrying it have no citation at all. The gap I
actually mind is different: Daganzo's abstract says the whole contribution is
that district shape matters, and we hold no shape measure for any ZCTA. That
is the question I could not answer, and it is the one I would ask."*
