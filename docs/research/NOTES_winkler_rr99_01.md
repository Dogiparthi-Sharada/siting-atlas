# Notes — Winkler (1999), State of Statistical Data Editing (RR99-01)

*Read in full 2026-09-13. These notes exist so nobody has to open the PDF
again.*

---

## 1. Citation and local file

```
  William E. Winkler, U.S. Bureau of the Census.
  "State of Statistical Data Editing and Current Research Problems."
  Statistical Research Division Research Report RR99-01,
  U.S. Bureau of the Census, August 1999.

  Local file:  ../Research/rr99-01.pdf   (10 PDF pages, unnumbered)
  PDF keywords field: "editing, Fellegi-Holt methods"

  A shorter version was presented at the Work Session on Statistical Data
  Editing, UN Economic Commission for Europe, Rome.
```

The report carries the standard SRD disclaimer: "This paper reports the
results of research and analysis undertaken by Census Bureau staff. It has
undergone a more limited review than official Census Bureau publications."

**Do not confuse this with RR99-04.** `../Research/rr99-04.pdf` is Winkler's
*record linkage* report, already read and cited at length in
`src/siting_atlas/common/linkage.py`. RR99-01 is about *editing and
imputation*. Same author, same year, different problem. This is the
companion to Fellegi & Holt, not to Fellegi & Sunter.

The pages are unnumbered in the PDF. I cite by section number only, which
is what the paper provides (Sections 1-4 plus subsections 3.1, 3.2).

---

## 2. What the paper is for

It is a ten-page state-of-the-art review, written for statistical-agency
practitioners, of how Fellegi-Holt editing is actually implemented in
production and where it breaks. It is the bridge between the 1976 theory
and 1999 practice: which agencies run which systems, what the algorithms
cost, and what remains unsolved. For us it does three jobs. It gives an
authoritative **paraphrase of Fellegi-Holt's goals** and a four-item list
of what a Fellegi-Holt system *is*. It states, with numbers, **how
expensive implied-edit generation gets**. And it is the source for the
claim about **how long it takes to stand up an edit system** — which turns
out to contradict an estimate we had been carrying.

It is a review, not a research paper. No theorems, no data, no experiments
of its own. It poses research questions rather than answering them.

---

## 3. Section-by-section walkthrough

### Section 1 — Introduction

**The definition of the subject:**

> "I define statistical data editing (SDE) as those methods that are used
> to edit (i.e., clean-up) and impute (fill-in) missing or contradictory
> data. The end result of SDE is data that can be used for intended
> analytic purposes." (Sec. 1)

The purposes named are estimation of totals and subtotals "that are free of
self-contradictory information", where self-contradictory means "groups of
items that do not add to desired subtotals or totals for subgroups that
exceed a known proportion of the total for the entire group", and
crucially: "The published totals do not contradict published totals in
other sources."

There is a **cost-proportionality principle** stated early and it is
directly useful:

> "If only a few published totals need to be accurate, then an efficient
> use of resources may be to perform detailed edits on only a few records
> that effect the estimated totals. If many analyses need to be performed
> on a large number of sub-domains or if the full set of accurate
> micro-data are needed, then a very large number of edits, follow-up, and
> corrections may be needed." (Sec. 1)

Scope: SDE applies across "frame development, form design, proposed
analytic purposes for which the data are collected, and quality assurance",
but this paper concentrates on procedures applied "after the initial
receipt of survey or other data".

**The two-way split of the field:**

> "I broadly subdivide statistical data editing into two subcategories: (1)
> Fellegi-Holt (FH) methods and systems and (2) General methods and
> systems. FH systems are based on the Fellegi-Holt model of editing and
> typically add various options for imputation. General methods are all
> other methods." (Sec. 1)

#### Why so few FH systems exist

> "Whereas the paper by Fellegi and Holt (1976) appeared quite awhile ago,
> few systems have been implemented because of the difficulty in developing
> expertise in the operations research (OR) techniques needed under the
> model. Many statistical agencies have chosen to concentrate on
> traditional methods that are a large sub-portion of general methods."
> (Sec. 1)

#### The indictment of if-then-else editing

This is the passage to cite whenever someone defends a scatter of ad-hoc
filters:

> "These traditional methods include if-then-else rules for detecting
> contradictory information and various ways of imputing values of
> variables to replace the contradictory values. The dilemma with
> if-then-else rules is that they may not be straightforward to develop and
> may be difficult to write into computer code. If there are slight changes
> in the survey form and edit rules, then subsets of thousands of lines of
> code may need to be rewritten and debugged. The reason that FH methods
> are so appealing is that most of the if-then-else types of edits can be
> put in tables that are straightforward to modify and update. Because the
> source code does not need any updating, it is possible to create a FH
> system for editing that can be developed and maintained for different
> surveys by non-programmers such as subject matter specialists,
> statisticians, and economists." (Sec. 1)

Note what the objection actually is. It is **not** that if-then-else rules
are wrong. It is that they are (a) hard to get logically complete, (b)
hard to code correctly, and (c) catastrophically expensive to *change*,
because the logic lives in source rather than in data. The FH payoff is
maintainability by non-programmers.

#### General methods — selective / macro editing

Short but the most directly actionable paragraph in the paper for us:

> "General methods include selective (or macro) editing. In some
> situations, the records associated with the largest companies or firms
> can be delineated for follow-up and review. Some of these methods use
> measures such as the Hidiroglu-Berthelot (HB) statistic or graphical
> displays. HB methods involve measures that determine which records cause
> the largest deviations of key totals in the survey population. Follow-up
> is more efficient because the most important records are reviewed
> first." (Sec. 1)

And exploratory data analysis as an editing tool:

> "DesJardins (1997, 1998) has recently developed courses for using
> point-and-click graphical methods (via SAS Insight or JMP) as exploratory
> data analysis (EDA) tools for finding erroneous data. The significant
> advantage of EDA methods is that they allow non-programmers to delineate
> and review data in ways that are different from the fixed ways available
> in a specific edit system for an individual survey." (Sec. 1)

For more on general editing methods the paper points to Pritzker, Ogus &
Hansen (1965).

### Section 2 — Fellegi-Holt methods and systems

Opens by restating the maintenance problem: "Developing software from
scratch each time a survey form and database is redesigned is
time-consuming and error-prone. It is better to have a system that can
describe edit rules in tables that are read and utilized by reusable
software modules."

#### Winkler's paraphrase of the three FH goals

Explicitly labelled as a paraphrase:

> "FH provided the theoretical basis of such a system that had three goals
> that (paraphrased) are:
>
> 1. The data in each record should be made to satisfy all edits by
> changing the fewest possible variables (fields).
>
> 2. Imputation rules should derive automatically from edit rules.
>
> 3. When imputation is necessary, it should maintain the joint
> distribution of variables."

This matches the ordering in Fellegi & Holt Section 1 (not the ordering in
their abstract). See `NOTES_fellegi_holt_1976.md` §3 for the originals in
full.

#### The consistency check

> "The software would automatically check the logical validity of the
> entire system prior to the receipt of data during production processing.
> Checking the logical validity is often referred to as determining the
> consistency or logical consistency of a set of edits. If a set of edits
> is inconsistent, then there exist no records that can satisfy the set of
> edits." (Sec. 2)

Note that Winkler's gloss ("there exist no records that can satisfy the set
of edits") is looser than Fellegi & Holt's formal definition, which is
about an implied edit ruling out permissible values of a *single* field
irrespective of the others. Winkler's version is the practical consequence.

#### Error localisation and implicit edits

> "The key to the FH approach is to understand the underpinnings of goal 1.
> Goal 1 is referred as the error localization problem. To solve the
> error-localization problem, FH showed that both explicit and implicit
> edits are needed. Implicit edits are those that can be derived (or
> generated) from a set of explicit edits. If the implicit edit fails, then
> necessarily at least one of the explicit edits used in generating the
> implicit edit fail." (Sec. 2)

**Terminology warning.** Winkler says *implicit* edits throughout; Fellegi
& Holt say *implied* edits, and further distinguish *essentially new*
implied edits. They are the same objects. Our documents should pick one and
note the other; I have used "implied" when citing FH and "implicit" when
citing Winkler.

Why prior work failed:

> "In work prior to the FH paper, many authors introduced edit methods for
> identifying fields (variables) to change that could not assure that the
> changed record satisfied all edits. As proved by FH, implicit edits can
> provide information about explicit edits that do not fail with the
> original un-edited record but might fail if information in the implicit
> edit is not properly used." (Sec. 2)

On the significance and the limits of the proof:

> "The main theorem in FH is a landmark result because it demonstrated that
> it is always possible to find a set of fields to change in a record that
> yield a changed record that satisfies all edits. FH's proof is by an
> inductive, existence-type method that does not give insight into how to
> deal with practical computational aspects of generating implicit edits."
> (Sec. 2)

#### THE FOUR KEY FEATURES OF A FELLEGI-HOLT SYSTEM

Quoted in full. This is the list our documentation should have been citing
for "what a formal edit system gives you", as distinct from the three
*goals* above:

> "The key features of a Fellegi-Holt system are:
>
> 1. Edit restraints reside in easily modified tables.
> 2. The logical consistency of the entire edit system can be checked prior
> to the receipt of data.
> 3. The main logic resides in reusable mathematical routines.
> 4. In one pass through the system, records satisfy edits."

#### Discrete vs continuous implementations

> "Implementations of FH systems have typically either been for discrete
> data (e.g., categorical) to which arbitrary edits are applied or for
> continuous data to which ratio or linear inequality edits are applied."

**Discrete worked example.** A household record with a 35-year-old married
male head and a 6-year-old married male son. The edit `E1 = {age < 16,
Marital_Status = Married}` fires; imputing Marital_Status Married -> Single
satisfies it. Winkler is careful about what this costs:

> "Whereas it is possible for an individual who is less than 16 to be
> married, in the overwhelming majority of situations, a record that
> satisfied E1 would truly be in error. Application of this edit is
> necessarily a compromise. In a few situations, changing the marital
> status of a person who has age less than 16 to unmarried might induce an
> error. In most situations, the change would be a correction." (Sec. 2)

That candour is worth keeping: **an edit is a bet, not a fact.**

He also gives a realistic target for migrating an existing ad-hoc system:

> "Within the framework of a given general edit system, it is not possible
> (or at least easily possible) to replace all specific edits in a
> non-general system for an individual survey. A goal might be to replace
> 90-95% of all the predecessor system with the same set of edits in the
> form that the new generalized system accepts." (Sec. 2)

**The implicit-edit example**, which is cleaner than FH's own:

```
  E1 = {age < 16, married}
  E2 = {not married, spouse}
  E3 = {age < 16, spouse}          <- implied by E1 and E2
```

> "If a record fails edit E1 and does not fail edit E2, then edit E3 (which
> must also fail) gives information that allows determination of
> value-states of fields so that the resultant changed record satisfies all
> edits. For instance, if record r fails edit E1 and only the explicit edit
> E1 is used, then a solution for the field to change would be
> marital_status. If marital_status is changed from 'married' to 'not
> married', then record r would fail edit E2." (Sec. 2)

The generation procedure is described in words and matches FH's Lemma:
choose a generation field and a generating set; the generating field's
entry is the **union** of value states across the generating edits, the
remaining fields are the **intersection**; drop the candidate if the union
is not all value-states, or if any intersection is null.

**Continuous case.** Two linear edits can be combined to eliminate a
variable, producing an implicit edit that places no restriction on the
eliminated field. Ratio edits `L_ij < V_i / V_j < U_ij` are a special case
of linear inequality edits, since `L_ij < V_i/V_j` is equivalent to the
linear edit `L_ij * V_j < V_i`.

#### THE COST NUMBERS — Section 2

These are the figures to quote when anyone proposes building a solver:

> "In practice, general algorithms for determining all implicit edits have
> only been developed for sets of linear inequality edits and for sets of
> ratio edits. Generating implicit edits for ratio edits is particularly
> easy. If there are n fields involved in ratio edits, then there can exist
> at most n(n-1)/2 ratio edits (explicit and implicit). With linear
> inequality edits, the number of implicit edits can increase dramatically.
> For instance, with 30 explicit edits and 10 fields, it might be possible
> to generate 400 implicit edits. Although the generation algorithm for
> linear inequality edits is straightforward to program, the algorithm is
> not particularly efficient. The generation can take 24 hours on a
> moderately fast computer with a moderate number of linear inequality
> edits." (Sec. 2)

#### Sande's alternative

Gordon Sande (1979) avoids generating all implicit linear-inequality edits:
he uses Chernikova's algorithm (1964, 1965) to generate the **vertexes** of
the bounded region in R^n defined by the explicit linear inequality edits,
because "The maximum and minimum solutions were known to occur on the
vertexes." Chernikova being too slow, Sande used D. S. Rubin's (1975)
cardinality-constrained vertex generation. Later heuristics
(Schiopu-Kratina & Kovar 1989; Filion & Schiopu-Kratina 1993) gave a 60x
speed-up, incorporated in Statistics Canada's **GEIS** (Generalized Edit and
Imputation System), and in **AGGIES** (Todaro 1998, 1999, written in SAS).
Statistics Netherlands built similar Chernikova variants in **CherryPi**
(De Waal 1996, 1997), being incorporated into **Blaise**.

#### THE TIME-TO-BUILD CLAIM

The single most consequential sentence in this paper for our purposes:

> "FH methods show their power with small demographic surveys. If a small
> survey has reasonably well-documented edits (or at least well
> understood), then it is possible for a non-programmer to create the
> tables of edits and effectively create a production edit system in less
> than one day." (Sec. 2)

Read the preconditions carefully. "Less than one day" is the time for a
*non-programmer* to **populate the edit tables** of an *existing* FH engine
for a small survey with *already well-understood* edits. It is not the time
to build DISCRETE or GEIS. Both halves of that matter to us and are worked
through in §5 below.

For larger surveys the picture degrades: "some conversions are often needed
to put data in a form that would allow it to be edited by a FH system.
Sometimes, the data and edits may need to be partitioned into subsets that
are run separately during implicit edit generation and together during
production editing."

**Derived variables.** The Decennial Census prototype could not express
pairwise age comparisons directly, so software creates new yes/no variables
representing the comparison (e.g. `age_child >= age_householder + 15`
becomes a single two-valued variable). The cost of that trick is stated
honestly:

> "Although the main edit program automatically determines the minimum
> number of fields to impute (i.e., error localization), the minimum is in
> terms of the original variables and the induced variables. A final
> software algorithm makes a conversion to the original set of variables
> that may not be minimal in the sense of FH theory but is guaranteed to
> yield a solution." (Sec. 2)

So even a production FH system relaxes strict minimality when reality
intrudes.

### Section 3 — Selected research problems

Two categories: "(1) algorithms that improve the speed of the software and
(2) adjunct software that provides analyses and outputs needed by other
parts of the edit system."

#### 3.1 Speed improvements

Two bottlenecks: implicit-edit generation by set-covering algorithms, and
error localisation in the main edit program. The trade is stated crisply:

> "If implicit-edits are generated prior to editing, then the amount of
> computation needed for error localization can be significantly reduced.
> The reduction is so significant that the speed of the main edit program
> is no longer an issue. If implicit edits are not generated prior to
> editing, then the edit program will need to generate additional
> information that may be thought of as associated with the precise set of
> implicit edits that fail for each given record." (Sec. 3.1)

**The exponential blow-up, with numbers.** SCIA (Barcaroli et al. 1997) is
the most general discrete generator, and:

> "These algorithms have limitations because they appear to need as much as
> 24 hours to generate implicit edits when 250 or more explicit edits are
> used. With a large survey form or with complicated edit situations, as
> many as 750 explicit edits may be needed. Because the amount of
> computation needed for generation grows at a very high exponential rate
> in the number of edits, it is unlikely that current algorithms can
> generate the full set of implicit edits with as many as 300 explicit
> edits. More specifically, the amount of computation for 250 explicit
> edits is of the order exp(exp(250)) and the amount of computation for 300
> is exp(exp(300))." (Sec. 3.1)

The partitioning workaround and its price:

> "If all the implicit edits can not be generated for a given set of
> explicit edits, then one practical approach is to divide the set of
> explicit edits into subsets that are sufficiently small so that
> edit-generation can be accomplished. The disadvantage of this approach is
> that moderately sophisticated ways of dividing the original full set of
> explicit edits into the subsets of explicit edits may be needed. This
> places additional burden on the users of the system in terms of extra
> methods and programming for tracking the subsets. If subsets are used to
> generate implicit edits, then not all implicit edits can be obtained. It
> will not be possible to find error-localization solutions for some
> edit-failing records." (Sec. 3.1)

Statistics Canada (CANEDIT), Spain (DIA) and ISTAT (SCIA) "have all had to
partition the set of explicit edits for some large surveys."

Algorithmic progress reported: Winkler (1998) set-covering algorithms up to
100x faster in limited situations, by tracking computational paths from the
first stage — but they fail on complicated skip patterns (Italian Labour
Force data, "possibly as many as 10%" of implicit edits missed), because
"skip patterns necessitate tracking the details of computation over
multiple levels". Chen (1998) is a further 100x by generating only *prime*
covers rather than all covers, using new metrics to order edits and prune
paths; but "So far, however, expected speed improvements in the overall
algorithms have not been achieved."

**The most important warning in the whole paper**, from the SPEER
discussion, on what happens if you build half a Fellegi-Holt system:

> "In the new SPEER system, Draper and Winkler (1998) generated a small
> subset of the implicit edits induced by combinations of ratio edits and
> balance equations when items are required to add to a total. Their
> solution is only partially acceptable because the set of fields
> designated for change can no longer be guaranteed to be the
> error-localization solution (minimum number of fields to impute) for some
> records. Indeed, it can no longer even assure that the solution of fields
> to change will yield a record that satisfies all edits. The 'on-the-fly'
> method of computing implicit edits does not compute all implicit edits
> and, thus, cannot yield a proper error-localization solution. Theoretical
> work by Winkler (1998) and Chen (1998) — even though for discrete data —
> strongly suggest that all implicit edits are always needed." (Sec. 3.1)

The mitigation is multiple passes: re-run the imputed record through the
edit system. Draper & Winkler report 43 of 9,769 records failing after the
first pass and 1 after the second. Those 43 "typically fail 12 or more
explicit edits and/or have 6 or more of 17 fields blank." Cost: the extra
subroutines "quadrupled the amount of computation ... the system is still
extremely fast. The program processes 1000 records in less than 4 seconds
on a 200 MHz Pentium computer."

One clear benefit of the Draper-Winkler approach is singled out: "the
proper intervals into which imputation must be done are straightforward to
compute and guaranteed theoretically to be valid."

**Operational limits in production systems.** GEIS and AGGIES both have
timing loops that eject a record after a user-specified time, "Because
there is no control over how long the Chernikova algorithm will take with
some records." Current upper bounds: 1 minute per record in GEIS, 5 minutes
in AGGIES; "In GEIS, more than 95 percent of the records are processed in
less than 0.1 second." CherryPi caps the number of failed explicit edits at
eight: "If a record fails nine or more explicit edits, then the record
should be reviewed clerically and manually corrected by an analyst." And
the clerical route is expensive: "The manual corrections to edit-failing
record can require a number of difficult and very time-consuming iterations
until the record passes edits."

The economics of clerical review, which echoes Section 1's proportionality
principle: "If the reviewed records are associated with small enterprises
that have negligible effect on totals, then a large amount of clerical
review may not be an efficient use of resources."

Also reported: Garfinkel, Kunnathur & Liepins (1986) generate failing
implicit edits per record inside the main edit program, but "Because of the
large additional amount of computation, the methods were too slow to adopt
in practice." And Sande "has shown that it is not possible to generate all
the implicit edits from a large set of explicit linear inequality edits."

The research questions posed (not answered): can generation be sped up
enough for moderate-to-large surveys; are completely new methods needed;
can error localisation work without all implicit edits; which edit-failure
patterns make Chernikova slow, and can they be detected and bypassed; can
hybrid loops raise the proportion of records auto-corrected.

#### 3.2 Adjunct methods and software

The problem: "Individuals sometimes have difficulty using a FH system
because the data are not in a form that can be easily used by the system."
The Decennial Census solution is the derived-variable trick from Section 2,
described in more detail: an edit "a parent must be 12 years older than the
householder" becomes `E = {person1 < person2 + 12, person2_relat =
parent}`, with a two-valued variable V_E (1 if the bracketed condition
holds, 2 if not) replacing the explicit enumeration of all age
combinations. Two extra programs are needed — a pre-processor to create the
derived variables and a post-processor to translate the error-localisation
solution back to original variables — and:

> "The solutions of the original fields-to-change problem can no longer
> guaranteed to be the minimal number of fields to impute." (Sec. 3.2)

Four research questions follow: is the procedure theoretically valid ("It
seems straightforward to prove that it is"); can the final solution be
guaranteed minimal, or only close to minimal; can the pre/post-processors
be made user-friendly; can it be extended to continuous variables
categorised into many bins — the last of which "would allow much more
editing of demographic surveys that contain quantitative data such as
income and expenditure information."

Section 3.2 closes on the discrete/continuous split: Sande (1979) showed
how to edit both simultaneously by converting discrete data to continuous
and applying Chernikova; Pergamentsev (1998) and De Waal (1998) give
details. "The details make clear that a research problem is creating
versions of the algorithms that are sufficiently fast." Winkler asks
plainly: "Why are statistical agencies not using FH systems to edit
discrete and continuous data simultaneously?"

### Section 4 — Concluding remarks

Four sentences. Restates that the paper covers FH methods for discrete and
continuous data, describes systems in use worldwide, and — "Because all the
systems have limitations, it delineates a few research problems that, if
solved, would improve the use of the systems."

### References

About 35 entries. The ones worth knowing exist: Fellegi & Holt (1976);
Sande (1979) "Numerical Edit and Imputation"; Chernikova (1964, 1965);
Rubin, D.S. (1975) vertex generation; Garfinkel, Kunnathur & Liepins (1986)
"Optimal Imputation of Erroneous Data: Categorical Data, General Edits",
Operations Research 34:744-751; Kovar, MacMillan & Whitridge (1991) on
GEIS; Barcaroli & Venturi (1997) on DAISY; Winkler (1998) "Set-Covering and
Editing Discrete Data"; Chen (1998) "Set Covering Algorithms in Edit
Generation"; Draper & Winkler (1997) on SPEER; Pritzker, Ogus & Hansen
(1965) for general editing methods; **Little & Rubin (1987), Statistical
Analysis with Missing Data** — listed in the references but not, as far as
I can see, cited in the body text; Nemhauser & Wolsey (1988) Integer and
Combinatorial Optimization; Thompson & Sigman (1996) "Statistical Methods
for Developing Ratio Edit Tolerances for Economic Censuses".

---

## 4. Definitions, stated as the paper states them

**Statistical data editing (SDE).** "those methods that are used to edit
(i.e., clean-up) and impute (fill-in) missing or contradictory data."
(Sec. 1)

**Implicit edit.** "Implicit edits are those that can be derived (or
generated) from a set of explicit edits. If the implicit edit fails, then
necessarily at least one of the explicit edits used in generating the
implicit edit fail." (Sec. 2)

**Consistency / logical consistency of a set of edits.** "Checking the
logical validity is often referred to as determining the consistency or
logical consistency of a set of edits. If a set of edits is inconsistent,
then there exist no records that can satisfy the set of edits." (Sec. 2)

**Error localization.** "Goal 1 is referred as the error localization
problem" — goal 1 being "The data in each record should be made to satisfy
all edits by changing the fewest possible variables (fields)." (Sec. 2)

**Selective / macro editing.** Editing in which "the records associated
with the largest companies or firms can be delineated for follow-up and
review", using measures such as the Hidiroglu-Berthelot statistic, which
"determine which records cause the largest deviations of key totals in the
survey population." (Sec. 1)

**The four key features of a Fellegi-Holt system.** (Sec. 2, quoted in full
in §3 above.) Tables, pre-data consistency check, reusable mathematical
routines, one-pass satisfaction.

---

## 5. What this means for siting-atlas

### 5.1 It contradicts a cost estimate we were carrying

`docs/data/CLEANING_LITERATURE.md` §5 stated: "A formal edit system in the
Fellegi-Holt sense is a week and is almost certainly the wrong trade for a
capstone." Winkler Section 2 says a non-programmer can stand up a
production edit system for a small survey "in less than one day".

Both can be true, and reconciling them is the useful bit. Winkler's day is
the time to **fill in the tables of an engine that already exists** —
DISCRETE, GEIS, SPEER, AGGIES, CherryPi — for a survey whose edits are
already well understood. We have no engine. So the honest decomposition is:

```
  populate an edit table, given an engine        < 1 day   (Winkler, Sec. 2)
  build the engine (implied-edit generation
    + set-cover error localisation)              the week we were quoting
  keep it correct once built                     see below
```

Our old sentence was not wrong about the total; it was wrong about *what
the week buys*, and it implied the literature agreed that formal editing is
expensive per se. Winkler's position is the opposite: formal editing is
*cheaper to own* than if-then-else rules, because "Because the source code
does not need any updating, it is possible to create a FH system for
editing that can be developed and maintained for different surveys by
non-programmers". The expense is one-time and it is in the solver.

### 5.2 And it gives the decisive argument against building the solver

Not cost — correctness. Section 3.1, on SPEER:

> "the set of fields designated for change can no longer be guaranteed to
> be the error-localization solution (minimum number of fields to impute)
> for some records. Indeed, it can no longer even assure that the solution
> of fields to change will yield a record that satisfies all edits."

A partially-implemented Fellegi-Holt system does not degrade gracefully. It
returns an answer that *looks* like a minimum-change solution and is not,
and may not even satisfy the edits. Compared with a plain declared
constraint list — which makes no such claim and therefore cannot break it —
a half-built solver is strictly worse. That asymmetry, not the week of
effort, is why we should not build one. Winkler's own summary of the
theoretical work is blunt: "all implicit edits are always needed."

### 5.3 What we should take instead, with the paper's own numbers

Winkler's feature 2 — "The logical consistency of the entire edit system
can be checked prior to the receipt of data" — is separable from features 1,
3 and 4 and is the cheapest large win available to us. Our 22 edits in
`DATA_QUALITY.md` F3 have never been checked against each other; one of
them is already known to be broken (the household identity that fires on
the 19 all-NULL ZCTAs). A consistency pass runs before any data is touched
and costs hours.

Scale check, using Winkler's own bounds. Our edit set is 22 explicit edits
over roughly 15 numeric fields, mostly ratio-shaped and linear-inequality-
shaped. Winkler: ratio edits over n fields admit at most `n(n-1)/2` edits
total, explicit and implicit — for n = 15 that is 105. Linear inequality is
worse ("with 30 explicit edits and 10 fields, it might be possible to
generate 400 implicit edits"), but nowhere near the exp(exp(250)) regime
that defeats the Census. So generation would be *feasible* for us. It is
still not *worth it*, for the reason in `NOTES_fellegi_holt_1976.md` §5.4:
there is exactly one place in this project where error localisation tells
us something we cannot see by inspection, and it is three facility records.

### 5.4 Selective / macro editing is the answer to our outlier problem

This is the most useful thing in the paper that we did not know we needed.

`DATA_QUALITY.md` F6 reports 28.36% of ZCTAs as robust-z outliers on
household density and correctly observes that a naive filter "deletes
Manhattan, which for a delivery-siting project deletes the answer". The
document then has nowhere to go, because it is treating outlier detection
as a distributional question.

Winkler Section 1 reframes it as a **prioritisation** question. Macro
editing does not ask "is this value extreme?" It asks "**which records
cause the largest deviations of key totals?**" — the Hidiroglu-Berthelot
measure — and reviews those first, because "Follow-up is more efficient
because the most important records are reviewed first." Section 1's
proportionality principle says the same thing from the other end: "If only
a few published totals need to be accurate, then an efficient use of
resources may be to perform detailed edits on only a few records that
effect the estimated totals."

Applied to us: the published artefact is the 2,333-ZCTA cost ranking. The
right screen is not |robust-z| > 3.5 on `hh_density` over 33,791 ZCTAs. It
is "which rows move the ranking most", reviewed top-down until the reviewer
stops finding errors. ZCTA 10069 at 162,659 people/sq mi is a large
influence and a correct value, so it survives review on the first pass and
is never looked at again. Water Mill at $68,623/month rent is a large
influence and a contaminated value, and macro editing puts it in front of a
human. A robust-z screen puts 9,578 ZCTAs in front of a human and is
therefore never run.

This reframes R9 in `DATA_QUALITY.md`: rank by influence on the published
number, not by distance from the median.

And Winkler's other general method applies too: EDA as an editing tool,
because "they allow non-programmers to delineate and review data in ways
that are different from the fixed ways available in a specific edit system".
We have a viz layer already.

### 5.5 The edit-is-a-bet caveat belongs in our documentation

Winkler on the under-16-married edit: "Application of this edit is
necessarily a compromise. In a few situations, changing the marital status
of a person who has age less than 16 to unmarried might induce an error. In
most situations, the change would be a correction."

We should say the same about our own edits before we enforce any of them.
`population > 0 ==> households > 0` fires on 353 ZCTAs, and the honest
position is that most are group quarters (a correct record we would be
damaging) and some are errors. An edit that is enforced without that caveat
recorded is a silent data-manufacturing step.

### 5.6 A smaller warning we should heed

Section 2 and Section 3.2 both report that once you introduce derived
variables to make edits expressible, minimality is lost: the solution "may
not be minimal in the sense of FH theory but is guaranteed to yield a
solution". Any edit we write over a *computed* column (`hh_density`,
`cost_per_parcel`, `permits_yoy_pct`) rather than a *reported* one inherits
this. It is another reason to keep the edit set small and close to the raw
fields.

---

## 6. What I did NOT read or did not understand

- **Nothing was skipped.** All 10 PDF pages: Sections 1, 2, 3 (with 3.1 and
  3.2), 4, the disclaimer, and the full reference list.
- **The PDF has no page numbers**, so every citation above is by section.
  I have not invented page numbers and no one else should.
- **Two OCR artefacts** I read through rather than around. In Section 2 the
  continuous-data example prints as "E2: x2 + x2 < c", which must be
  `x2 + x3 < c` for the elimination to make sense; and the derived edit
  prints as "E3: a1 x1 + a3 x3 < d", consistent with eliminating x2. Also
  in Section 3.2 the age-comparison edit prints once as `age_child $
  age_householder + 15` where the operator has been lost; from context it
  is `>=` or `>`. Neither affects the argument.
- **This is a review of other people's systems and I have read none of
  them.** GEIS, SPEER, DISCRETE, SCIA, DIA, CANEDIT, AGGIES, CherryPi,
  DAISY and Blaise are described here at second hand and that is all I
  know about them. In particular I have *not* read Sande (1979), Chernikova
  (1964/1965), Rubin (1975), Winkler (1998) or Chen (1998), so every claim
  above about Chernikova's algorithm, vertex generation, prime covers and
  set-covering speed is Winkler's characterisation, not verified.
- **The exp(exp(250)) figure I have quoted but not sanity-checked.** It is
  presented without derivation and reads as an order-of-magnitude
  rhetorical device rather than a tight bound. The operational numbers next
  to it — 24 hours at 250+ explicit edits, 400 implicit edits from 30
  explicit over 10 fields, n(n-1)/2 for ratio edits — are the ones I would
  rely on.
- **The paper contains no outlier-detection section.** Section 5.4 above
  builds on Section 1's two paragraphs about macro editing and EDA, which
  is all the paper says on the subject. There is no treatment of statistical
  outlier detection, robust estimation, inliers or influence measures
  beyond the named Hidiroglu-Berthelot statistic, which is cited and not
  defined. **If we want an inlier treatment, Winkler (1998) "Problems with
  inliers", RR98/05 is the paper — it is cited by Van den Broeck as
  reference [23] and is NOT in `../Research/`.**
- **Little & Rubin (1987) appears in the reference list and I could not
  find where the body text cites it.** Either I missed it or it is a
  leftover. Do not cite RR99-01 as a source for anything about MCAR/MAR.
