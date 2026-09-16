# Notes — Mohammed et al. (2024), The Five Facets of Data Quality Assessment

*Read in full 2026-09-13, including the 29-dimension appendix. These notes
exist so nobody has to open the PDF again.*

---

## 1. Citation and local file

```
  Sedir Mohammed (Hasso Plattner Institute, University of Potsdam),
  Lisa Ehrlinger (HPI Potsdam), Hazar Harmouch (University of Amsterdam),
  Felix Naumann (HPI Potsdam), Divesh Srivastava (AT&T Chief Data Office).
  "The Five Facets of Data Quality Assessment."
  arXiv:2403.00526v2 [cs.DB], 6 December 2024.  20 pages.

  Local file:  ../Research/2403.00526.pdf   (20 PDF pages)
```

The paper cites itself at reference [52] as "Data quality assessment:
Challenges and opportunities, CoRR abs/2403.00526" — the same arXiv id.
That is the v1 title. Cite it as *The Five Facets of Data Quality
Assessment* (2024); some bibliographies will have the older title.

This is a **vision paper**, so labelled in Section 4 ("Vision: A DQ
Assessment Framework"). It proposes a research agenda; it does not evaluate
anything.

Partially funded by the KITQAR project (BMAS, Germany).

---

## 2. What the paper is for

Two useful things and a lot of research-agenda scaffolding around them.

The scaffolding: the paper argues that data quality research has produced
many *dimensions* (accuracy, completeness, timeliness...) but almost no
work on how to actually *assess* them, and proposes organising the
assessment problem by five **facets** — data, source, system, task, human —
so that solving a shared challenge once benefits every dimension that
depends on that facet.

The two useful things for us:

1. **A modern name and a tool for the defect class we keep tripping over.**
   Section 3.3 and Appendix A.7 introduce **"hidden missing values"** —
   arbitrary values standing in for missing data, e.g. `-99`, `EMPTY`, or a
   missing date recorded as `1900-01-01` — and cite a detector (FAHES).
   That is our ACS top-code and our `fillna(1)`.
2. **A 29-dimension glossary with assessment challenges** (Appendix A),
   which is the most complete such list I have seen in one place and is
   directly reusable as an audit vocabulary. It also tells us which
   dimensions are *legally* mandated, via the EU AI Act.

It is a position paper, so almost everything in it is a claim about what
research *should* do. Read it for vocabulary and for the AI Act hook, not
for method.

---

## 3. Section-by-section walkthrough

### Abstract and Section 1 — The Many Dimensions of Data Quality

The gap the paper claims:

> "Research has divided the rather vague notion of data quality into
> various dimensions, such as accuracy, consistency, and reputation. To
> achieve the goal of high data quality, many tools and techniques exist to
> clean and otherwise improve data. Yet, systematic research on actually
> assessing data quality in its dimensions is largely absent, and with it,
> the ability to gauge the success of any data cleaning effort."
> (Abstract)

The motivating slogan, quoted from [76]: "quality cannot be improved if it
cannot be measured: we need concrete assessment methods to evaluate DQ in
individual dimensions."

**The definition of assessment**, taken from Batini et al. [13] and then
extended:

> "Batini et al. define DQ assessment as the measurement of DQ and the
> comparison with reference values for diagnosing it. As such, apart from
> the pure measurement of DQ, assessment includes classifying whether the
> measured quality is sufficient (or 'fit') for the underlying task.
> Measuring vs. judging whether the measured DQ suffices for a task at hand
> are challenges of rather different natures." (Sec. 1)

**The regulatory hook**, which is the part of this paper with teeth:

> "Such requirements have also become part of regulation, as in the General
> Data Protection Regulation (GDPR) and the EU AI Act. For instance, the AI
> Act mentions in Article 10 the DQ dimensions **representativity, accuracy
> (free of errors), completeness and relevancy**." (Sec. 1)

Four dimensions named in law. The paper uses exactly those four as its
worked examples in Section 3.

Vision and mission statements, quoted because they define the scope:

> "Vision statement. Given a dataset, a use case (task specification), a
> set of DQ dimensions, and their formal definitions, our goal is to
> develop effective and efficient assessment procedures for each DQ
> dimension. These procedures should compute values that accurately align
> with the formal definitions."

> "Mission statement. To achieve the vision, we want to identify facets
> upon which assessment procedures across DQ dimensions depend."

Scope limit: "While this paper focuses on structured data, we believe it
can also be extended to semi-structured or unstructured data."

### Section 2 — Data Quality Assessment by Facets

**Figure 1** is a five-spoke wheel: a central node "DQ Assessment" with
five labelled spokes — Data, Source, System, Task, Human — and exemplary
dimensions attached around the rim (Accuracy, Completeness, Representativity,
Relevancy), with "Data, Metadata, External data" annotating the Data spoke.

The five facets are defined as:

> "(i) the data itself, including metadata and external data; (ii) the
> source of the data; (iii) the system to store, handle, and access the
> data; (iv) the task to be performed on the data; and (v) the humans who
> interact with the data. These five facets are inspired by the stages of a
> typical data life cycle: all relevant components of each stage can be
> mapped to one or more facets." (Sec. 2)

#### 2.1 The Data Facet

"Raw data values are intended to represent real-world concepts and
entities. The data facet includes the data semantics and their digital
representation. It also includes metadata, such as schema information and
other documentation, and any assessment-relevant external knowledge (as
data), like a knowledge base."

Key challenge, and it is ours:

> "As data occur in different granularity (e.g., values, records, columns),
> DQ assessment must identify the necessary level of detail and devise
> quality-metric aggregation methods to cross levels of granularity."

Example dimensions called out for this facet: Accuracy ("Typical metrics to
assess accuracy require reference data to determine how closely the data
matches the reality") and Completeness ("**Placeholders represent missing
values, using either obvious placeholders like 'NaN' or less obvious
placeholders. The assessment needs metadata that contains information about
the placeholder representation.**").

#### 2.2 The Source Facet

"The source of data represents a logical perspective. This facet
encompasses evaluating the data generation and collection processes, as
well as assessing the source's integrity and organizational compliance. The
main aspect of the source facet is **data provenance**, which includes
information on the origins, providers, and other organizations involved in
creating and transforming the data."

> "One key challenge is ensuring data lineage traceability, including the
> data origin and its transformations. ... It is also important to consider
> the time range for assessing reliability over time; longer histories
> provide a more comprehensive view, while shorter intervals highlight
> recent changes."

Example dimensions: Reputation, Believability.

#### 2.3 The System Facet

"a physical perspective, including the infrastructure and technology for
storing, handling, and accessing the data. It also covers the system's
technical compliance with legal and regulatory requirements." Challenges:
*clarity* (documenting architecture, processing capabilities,
interoperability, security, UI) and *auditability* (verifying compliance
with regulations such as data deletion and security standards). Example
dimensions: Recoverability, Portability.

#### 2.4 The Task Facet

"pertains to the specific use case and the context in which the data is
employed. Thus, it inherently aligns with the 'fitness for use' definition
of DQ. The task influences which parts of the data (e.g., columns, tuples)
are considered and how well they represent the real-world."

The risk-tiering point, from the AI Act: "the risk of the task, according
to the AI Act, which defines minimal-, limited-, high- and
unacceptable-risk AI systems, can determine the way DQ is assessed. Higher
risk categories require more stringent DQ assessment methods, including
strict validation processes and documentation, to ensure compliance."
Example dimensions: Timeliness, Relevancy.

#### 2.5 The Human Facet

"introduces a subjective view, while including the diverse groups that
interact with the data, perform the task, and interpret the results. ...
Some DQ dimensions (e.g., relevancy, believability), require user surveys
to assess experiences and challenges in handling the data. This subjective
perspective makes it challenging to fully automate the assessment."
Example dimensions: Ease of manipulation, Relevancy.

### Section 3 — Facet Application

Introduces a three-level involvement scale: "`++` for strong involvement,
`+` for medium, and `-` for low to no involvement", determined "through
several discussion rounds among all authors until we reached a consensus"
and deliberately biased toward objectivity: "we deliberately voted in favor
of an objective and automatic assessment and thus tried to minimize the
involvement of the human facet."

Then four worked dimensions — the AI Act's four.

**3.1 Accuracy.** Definition: "Accuracy describes the correspondence
between a phenomenon in the world and its description as data."
Involvement: Data `++`, Source `+`, System `+`, Task `-`, Human `-`. "Most
metrics require reference data, which corresponds to the data facet." Open
data platforms (Kaggle) and knowledge bases (Wikidata, DBpedia) are
proposed as reference sources, matched via schema matching. Error-detection
systems named: NADEEF, HoloClean.

**3.2 Representativity.** Definition: "Representativity aims to ensure that
the characteristics of the reference data are present in the considered
data." Involvement: Data `++`, all others `-`. The useful practical note:
"In contrast to accuracy, assessing representativity does not require the
complete reference data — summary statistics, respectively, data
distributions of the attributes, are often sufficient."

**3.3 Completeness.** Definition: "Completeness refers to the extent to
which data, including entities and attributes, are present according to the
data schema." Involvement: Data `++`, Source `+`, System `+`, Task `-`,
Human `-`.

**The hidden-missing-values passage**, quoted in full because it is the
reason this paper is in our reading list:

> "Since completeness represents the presence of the data, its assessment
> requires the measurement of missing values. While null or conventional
> placeholders like 'NaN' for missing values are easily identified, more
> research is required to also identify so-called 'hidden missing values'
> like '-99', 'EMPTY', or default values. Identifying these hidden missing
> values can either be done through prior knowledge (in terms of metadata
> and sophisticated Data Catalogs or, particularly suited for the ML
> context, with Data Cards) or alternatively learned with ML models taking
> into account the context. Placeholders can differ for each data source or
> be domain-specific, which is why strict documentation is important. In
> addition, transformations on missing values, like deleted records or
> applied imputation strategies, must also be part of the metadata."
> (Sec. 3.3)

The last sentence is the one that indicts `cost/runner.py:166`: deletions
are themselves metadata.

**3.4 Relevancy.** Definition: "Relevancy describes the extent to which
data are applicable and helpful for a given task." Involvement: Data `+`,
Source `-`, System `-`, Task `++`, Human `++`. Assessment options: domain
experts rating attributes and tuples on a Likert scale, or statistical
feature-importance methods (Shapley, LIME), supported by data profiling.

### Section 4 — Vision: A DQ Assessment Framework

**Figure 2** maps the facets onto an AI pipeline: data sources -> data
preparation (data engineer) -> training data -> AI model (data scientist)
-> AI system -> AI product -> consumer, with a "DQ Assessment Framework"
box containing DQ Dimensions and the five Facets, and a "Metadata
Management System" alongside.

Three further cross-cutting challenges are named: **Efficiency** ("The
assessment effort and time should be low from a user perspective"),
**Explainability** ("assessment results must be explainable to consumers.
In addition, the results should be traceable to their root cause, enabling
measures to improve quality"), and **Metadata Management** ("an effective
mechanism to store and query vast, diverse metadata").

### Section 5 — Related Work

Brief. Stvilia et al. [76] distinguish intrinsic, relational and
reputational information quality; Batini et al. [13] divide assessment into
phases and discuss metrics; Pipino et al. [61] combine subjective and
objective assessment; Sadiq et al. [69] identify two dimensions to
empirical DQ management, "the metric type (intrinsic vs. extrinsic) and the
method scope (generic vs. tailored)". The claimed contribution over all of
these: "many existing works implicitly mention individual facets ...
However, so far, a unified view on how to address these different aspects
was missing."

### Section 6 — Conclusion

Restates the five facets and the framework vision. Nothing new.

### APPENDIX A — Definitions and Assessment Challenges of Data Quality Dimensions

**This is the most reusable part of the paper.** 29 dimensions, each with a
definition (sourced to the authors' own Data Quality Glossary [51], itself
compiled from a literature study), an assessment-challenges paragraph, and
a facet-involvement table.

Full list with definitions compressed to the essential clause, and the
facet table. `D S Sy T H` = Data, Source, System, Task, Human.

```
  A.1  Accessibility          technical, organizational, financial and legal
                              ability to access the data
                              D -   S +   Sy ++  T -   H ++
  A.2  Accuracy               "the correspondence between a phenomenon in the
                              world and its description as data"
                              D ++  S +   Sy +   T -   H -
  A.3  Added-value            "the ability to beneficially utilize data in a
                              use case"
                              D -   S -   Sy -   T ++  H ++
  A.4  Appropriate amount     "the size of the data that is appropriate to
       of data                fulfill a specific task"; can be too small OR
                              too large
                              D -   S -   Sy -   T ++  H +
  A.5  Balance                "Data are balanced if the data points within the
                              represented range of values are equally
                              distributed in relation to each other"
                              D ++  S -   Sy -   T +   H -
  A.6  Believability          "the degree to which the available information
                              is regarded as correct"
                              D +   S ++  Sy -   T -   H ++
  A.7  Completeness           "the extent to which data, including entities
                              and attributes, are present according to the
                              data schema"
                              D ++  S +   Sy +   T -   H -
  A.8  Concise representation "the form in which data are represented";
                              concise data are "presented suitably and
                              recognizably, depending on the intended use"
                              D +   S -   Sy -   T ++  H ++
  A.9  Consistency            "Data are consistent if all conditions imposed
                              on the state of the data are met"
                              D ++  S -   Sy -   T -   H -
  A.10 Consistent             "no attribute (column) contains two or more
       representation         unique values that are semantically equivalent"
                              D ++  S ++  Sy -   T -   H -
  A.11 Cost                   monetary + personnel cost of generating,
                              acquiring, preparing and storing the data
                              D +   S +   Sy ++  T ++  H ++
  A.12 Diversity              richness: "Data are diverse if each entity type
                              of the total set occurs at least once"
                              D ++  S -   Sy -   T -   H +
  A.13 Documentation degree   "relevant, complete and correct structured
                              metadata and a textual description are
                              available"
                              D ++  S ++  Sy -   T -   H ++
  A.14 Ease of manipulation   changes "can be performed intuitively or
                              without prior knowledge"
                              D +   S -   Sy ++  T -   H ++
  A.15 Efficiency             "the effectiveness with which various processes
                              or algorithms can be executed on the data"
                              D +   S -   Sy ++  T -   H -
  A.16 Portability            "the ability to transfer structured data
                              reliably and securely from one system to
                              another" (GDPR requirement)
                              D ++  S -   Sy ++  T -   H -
  A.17 Precision              three senses: repeatability under unchanged
                              conditions; level of detail (year vs. exact
                              birthdate; 22C vs. 22.34C); granularity of
                              predefined value classes
                              D ++  S -   Sy -   T -   H -
  A.18 Privacy                "individuals described in the data have control
                              over and access to that data"
                              D -   S ++  Sy +   T -   H +
  A.19 Recoverability         data can be re-created after system errors or
                              carrier loss with quality guaranteed
                              D -   S -   Sy ++  T -   H -
  A.20 Relevancy              "the extent to which data are applicable and
                              helpful for a given task"
                              D +   S -   Sy -   T ++  H ++
  A.21 Reliability            "the extent to which the data can be trusted:
                              the information represented is correct"
                              D ++  S ++  Sy -   T -   H ++
  A.22 Representativity       "the (statistical) characteristics of the
                              reference data are present in the considered
                              data"
                              D ++  S -   Sy -   T -   H -
  A.23 Reputation             "the trustworthiness of the data source and the
                              content"; where accuracy cannot be measured,
                              "reputation can also be understood as the
                              expected quality of data"
                              D -   S ++  Sy -   T -   H ++
  A.24 Security               "the extent of protection against unauthorized
                              access to data"
                              D -   S -   Sy ++  T -   H +
  A.25 Timeliness             "the difference in time between an
                              electronically captured event in the real world
                              and its digital representation in the data,
                              considering the task at hand"
                              D +   S ++  Sy -   T ++  H -
  A.26 Traceability           "the ability to trace the provenance of data,
                              including their origin and all transformations
                              performed on them"
                              D +   S ++  Sy +   T -   H -
  A.27 Transparency           "the extent to which stakeholders can access
                              all data-related information, including the
                              origin of the data, data collection strategies,
                              and the transformations applied to them"
                              D +   S ++  Sy -   T -   H ++
  A.28 Understandability      "the extent to which a user can semantically
                              comprehend the information represented by the
                              data"
                              D ++  S -   Sy -   T -   H ++
  A.29 Uniqueness             "whether each entity in the real world is
                              represented at most by one entry in the data,
                              meaning there are no duplicates"
                              D ++  S -   Sy -   T -   H -
```

Several appendix entries carry content beyond the definition and are worth
extracting:

**A.7 Completeness** adds a second perspective beyond counting nulls:
"quantification of absent tuples that would match the data model schema
(open world assumption)", which needs reference data. And, again: "Missing
tuples can also result from previous transformation strategies, such as
deleting them if they contain missing values. Therefore, transformations
must also be part of the metadata and considered during the assessment."
Its canonical hidden-missing example is "representing a missing date with
1900-01-01".

**A.5 Balance vs. A.12 Diversity vs. A.22 Representativity** are carefully
distinguished, which is unusual and useful. Diversity = each entity type
appears *at least once*. Balance = types appear in *equal* numbers.
Representativity = types appear in the *same proportions as the reference
population*. The worked example for representativity: a total set of 70
male / 30 female students with a given major split is representatively
sampled by 9 female art, 9 female history, 24 male art, 18 male history,
"because the relative ratios between students of the same sex and between
students of the same major are identical when compared to the total set."

**A.9 Consistency** gives examples that are ours: "different date formats
in a single column, **different cities for the same zip code**, or purchase
orders with invalid customer numbers." And the honest difficulty: "Even if
constraints are known (through the metadata), it can be challenging to
actually find the corresponding violations in the data."

**A.10 Consistent representation** — "New York vs. NYC or 2024-1-12 vs.
2024-12-1" — with the provenance caveat: "The origin of the data must also
be considered, as the semantics of individual values depend on the source
from which the data is generated. For instance, values within a single
domain may be considered semantically equivalent. However, when values
originate from different domains, they may no longer share the same
semantic equivalence."

**A.13 Documentation degree** enumerates what metadata should contain:
"the volume of the data, its syntactic schema (data types) and its semantic
schema (table and column names), statistics, information about its
provenance and any transformation that has been performed so far", plus
textual data sheets giving "the data's purpose and previous use(s)".

**A.29 Uniqueness** distinguishes exact from fuzzy duplicates and notes the
granularity question ("whether the uniqueness is measured at value, row, or
column level or across entire datasets") and that exhaustive duplicate
discovery is expensive, "so estimations can help".

---

## 4. Definitions worth quoting verbatim

**DQ assessment** (Sec. 1, after Batini et al. [13]): "the measurement of
DQ and the comparison with reference values for diagnosing it. As such,
apart from the pure measurement of DQ, assessment includes classifying
whether the measured quality is sufficient (or 'fit') for the underlying
task."

**The five facets** (Sec. 2): "(i) the data itself, including metadata and
external data; (ii) the source of the data; (iii) the system to store,
handle, and access the data; (iv) the task to be performed on the data; and
(v) the humans who interact with the data."

**Hidden missing values** (Sec. 3.3): "While null or conventional
placeholders like 'NaN' for missing values are easily identified, more
research is required to also identify so-called 'hidden missing values'
like '-99', 'EMPTY', or default values." Appendix A.7 adds: "A common
example is using specific but arbitrary values to fill missing entries,
such as representing a missing date with 1900-01-01."

**Completeness** (Sec. 3.3 / A.7, after Pipino et al. [61]): "the extent to
which data, including entities and attributes, are present according to the
data schema."

**Representativity** (Sec. 3.2 / A.22): "Representativity aims to ensure
that the characteristics of the reference data are present in the
considered data."

**Timeliness** (A.25): "the difference in time between an electronically
captured event in the real world and its digital representation in the
data, considering the task at hand."

**Traceability** (A.26): "the ability to trace the provenance of data,
including their origin and all transformations performed on them."

---

## 5. What this means for siting-atlas

### 5.1 "Hidden missing values" is the modern name for our worst defect class

Rahm & Do (2000) called it *Missing values* with the example
`phone=9999-999999`. This paper gives it the name that current tooling uses
and, critically, gives it a **detector**: FAHES (Qahtan et al., KDD 2018,
reference [63] — "Fahes: A robust disguised missing values detector"). The
literature term of art is "disguised missing values".

Our instances, all one class:

```
  median_household_income = 250001    86 ZCTAs   census_api.py:110
  median_home_value       = 2000001   83 ZCTAs   census_api.py:110
  median_household_income = 2499      23 ZCTAs   (never looked for)
  median_home_value       = 9999      20 ZCTAs   (never looked for)
  open_quarter            = 1         19 of 43   facilities.py:118
  enabled                 = False     unknown    facilities.py:215
```

The paper's prescription is not "detect them" — it is a metadata
discipline: "Placeholders can differ for each data source or be
domain-specific, which is why strict documentation is important." A
declared per-source placeholder registry is a cheaper and more durable fix
than a detector, because we *know* our placeholders; the detector is for
data you inherited blind.

### 5.2 Deletions are metadata

Twice, in Section 3.3 and again in A.7:

> "transformations on missing values, like deleted records or applied
> imputation strategies, must also be part of the metadata."

> "Missing tuples can also result from previous transformation strategies,
> such as deleting them if they contain missing values. Therefore,
> transformations must also be part of the metadata and considered during
> the assessment."

`cost/runner.py:166` drops rows and prints a count. Under this standard the
drop belongs in the artefact, not the log. Same for `runner.py:57` (80
ZCTAs) and `models/panel_source.py:144` (131 units). This is the same
requirement Van den Broeck makes from the reporting side and Fellegi & Holt
make from the audit side; three independent literatures agree, which is
worth saying in the defence.

### 5.3 The AI Act gives us four dimensions with legal standing

Article 10 names **representativity, accuracy, completeness and
relevancy**. Our `rent_index` finding is squarely a *representativity*
failure in the Act's sense, not merely a statistical one: the complete-case
sample's characteristics (median 1,556.8 households/sq mi) do not match the
reference population's (24.5/sq mi in the missing stratum). Framing it that
way is more forceful in a defence than "MAR on density", and it comes with
an external standard rather than our own judgement.

The paper's risk-tiering point also cuts our way: "Higher risk categories
require more stringent DQ assessment methods". A capstone siting model is
not a high-risk AI system and we should not pretend otherwise — but the
argument that assessment effort should scale with task risk is the same
proportionality principle Winkler states, and it is the honest defence of
*not* building a full edit system.

### 5.4 The granularity challenge is our F7 in general form

> "As data occur in different granularity (e.g., values, records, columns),
> DQ assessment must identify the necessary level of detail and devise
> quality-metric aggregation methods to cross levels of granularity."
> (Sec. 2.1)

We broadcast county-grain EJScreen, state-grain EIA and CBSA-grain BLS
values into ZCTA columns (F7: 10.5 to 52.9 ZCTAs per distinct value). A.26
Traceability and A.13 Documentation degree both say the source grain
belongs in the metadata. Neither is satisfied.

### 5.5 Three appendix dimensions we have no equivalent of and should

- **A.17 Precision**, second sense — "the level of detail in information".
  26 of our 35 numeric columns are constant across all 32 quarters. That is
  not missingness and not staleness; it is a *precision* deficiency in the
  temporal dimension, and naming it that way is clearer than "time-
  invariant".
- **A.25 Timeliness** — "the difference in time between an electronically
  captured event in the real world and its digital representation in the
  data, **considering the task at hand**". Our seven-year vintage spread
  inside one panel row is a timeliness defect, and the trailing clause is
  the reason it matters differently for the cost model (barely) than for a
  backtest trained through 2023 on May-2025 wages (leakage).
- **A.10 Consistent representation** — three columns named `metro`,
  `cbsa_title` and `metro_label` holding semantically equivalent values
  that disagree for 28.1% of the ZCTAs where two of them coexist. That is
  R12, and A.10's provenance caveat explains exactly why it happened:
  "when values originate from different domains, they may no longer share
  the same semantic equivalence."

### 5.6 What this paper does NOT give us

No method. No threshold. No algorithm. It is a research agenda and it says
so. Everything actionable above is vocabulary and one tool citation. Do not
cite it as evidence that anything works; cite it for names, for the AI Act
dimensions, and for the metadata-must-record-deletions rule.

---

## 6. What I did NOT read or did not understand

- **Nothing was skipped.** All 20 PDF pages: abstract, Sections 1-6, the
  81-item reference list, and Appendix A in full (all 29 dimensions with
  their assessment-challenge paragraphs and facet tables).
- **Figures 1 and 2 are vector diagrams whose labels partially survive in
  the text layer.** My descriptions are reconstructed from those fragments
  plus the prose. I am confident about the five facet names and the four
  rim dimensions in Figure 1, and about the pipeline stages in Figure 2,
  but not about the exact arrow topology in either.
- **The facet-involvement ratings are the authors' consensus opinion, not a
  measurement.** They say so: "We determined the involvement of the facets
  through several discussion rounds among all authors until we reached a
  consensus." I have reproduced them because they are a useful structuring
  device, not because they are findings.
- **The reference list is 81 items and I followed none of them.** Three are
  worth knowing exist and are NOT in `../Research/`: [63] Qahtan et al.,
  *FAHES: A robust disguised missing values detector*, KDD 2018 — the
  detector for our defect class; [66] Rekatsinas et al., *HoloClean*,
  PVLDB 2017; [23] Dallachiesa et al., *NADEEF*, SIGMOD 2013. [39] is
  Herzog, Scheuren & Winkler, *Data quality and record linkage techniques*
  (2007), which is the book-length successor to the Winkler record-linkage
  report we already use.
- **I have not read the EU AI Act Article 10 itself**, only this paper's
  characterisation of it. If the representativity argument is going into a
  defence document, read the Article.
- **I have not read the authors' Data Quality Glossary [51]** (Zenodo
  10474880), which is the actual source of the 29 definitions. The
  appendix says the definitions "are taken from our Data Quality Glossary,
  which was compiled through a thorough literature study", so the
  definitions above are at one remove from their originals.
- **Section 3's involvement tables for accuracy and relevancy are discussed
  twice** — once in Section 3 and once in Appendix A — and I did not
  cross-check every rating for consistency between the two. The ones I
  spot-checked (accuracy, completeness, relevancy, representativity) agree.
