# Notes — Ehrlinger et al. (2019), Survey of Data Quality Tools

*Read in full 2026-09-13. These notes exist so nobody has to open the PDF
again.*

---

## 1. Citation and local file

```
  Lisa Ehrlinger (1,2), Elisa Rusz (1), Wolfram Woess (1).
    (1) Johannes Kepler University Linz, Austria
    (2) Software Competence Center Hagenberg, Austria
  "A Survey of Data Quality Measurement and Monitoring Tools."
  arXiv:1907.08138v1 [cs.DB], 18 July 2019.  A Preprint.  30 pages.

  Local file:  ../Research/1907.08138.pdf   (30 PDF pages)
  Printed page numbers run 1-26 in the body; the PDF adds front matter.
```

Lisa Ehrlinger is also a co-author of *The Five Facets of Data Quality
Assessment* (`NOTES_five_facets_2024.md`). The two papers are consistent
and complementary: this one is the empirical evidence for the later one's
claim that assessment research has not reached practice.

A later peer-reviewed version exists (IEEE Access, 2022). These notes are
from the 2019 arXiv preprint, which is what is on disk.

---

## 2. What the paper is for

A systematic survey. The authors found **667 distinct software tools**
claiming to do "data quality", filtered them by six exclusion criteria down
to 17, and evaluated 13 of them against a **43-item requirements catalog**
in three categories: data profiling, data quality measurement, and
continuous data quality monitoring. They installed and drove each tool
against a common test database and recorded what it actually produced.

Its value to us is not the tool recommendations — the market has moved on
since 2019 and we are not buying a tool. Its value is threefold:

1. **The 43-item requirements catalog (Table 2) is a ready-made audit
   checklist** for what a data-quality capability consists of. We can score
   our own pipeline against it.
2. **It is empirical evidence that the academic DQ-dimension programme
   failed in practice** — and it says so bluntly. That is a defensible
   reason for us *not* to build a dimension-and-metric framework.
3. **Its findings on outlier detection in real tools** (Section 4.2.1) tell
   us what the practical state of the art actually is, which is much less
   than the research literature implies.

The paper is honest about its own limits and its reporting of
implementation discrepancies between tools is unusually detailed.

---

## 3. Section-by-section walkthrough

### Abstract and Section 1 — Introduction

The framing statistic: "84 % of the CEOs in the US are concerned about
their DQ" and "organizations believe poor data quality to be responsible
for an average of $15 million per year in losses". And the state of
practice:

> "according to a German survey, 66 % of companies use Excel or Access
> solutions to validate their DQ and 63 % of the companies determine their
> DQ manually and ad hoc without any long-term DQ management strategy."
> (Sec. 1)

Why they survey *measurement* rather than *cleansing*:

> "While some tools, which we found in our search, solely offer data
> cleansing and improvement functionality, we specifically observe the
> measurement capabilities, that is, the detection of DQ issues. Since an
> automated modification of the data (i.e., data cleansing) is usually not
> possible in productive information systems with critical content, tools
> that detect and report DQ issues are required." (Sec. 1)

**The five headline findings**, quoted from the introduction:

> - "Despite the presumption that the emerging market of DQ tools is still
>   under development, we found a vast number (667) of DQ tools through our
>   systematic search, where most of them have never been included in one
>   of the existing surveys."
> - "Approximately half (50.82 %) of the DQ tools were domain specific,
>   which means they were either dedicated to specific types of data or
>   built to measure the DQ of a proprietary tool."
> - "16.67 % of the DQ tools focused on data cleansing without a proper DQ
>   measurement strategy."
> - "Most surveyed tools supported data profiling to some extent, but
>   considering the research state, there is potential for functional
>   enhancement in data profiling, especially with respect to multi-column
>   profiling and dependency discovery."
> - "We did not find a tool that implements a wider range of DQ metrics for
>   the most important DQ dimensions as proposed in research papers.
>   Identified metric implementations have several drawbacks: some are only
>   applicable on attribute-level (e.g., no aggregation), some require a
>   gold standard that might not exist, and some have implementation
>   errors."

Plus: "In general-purpose DQ tools, DQ monitoring is considered a premium
feature, which is liable to costs and only provided in professional
versions."

### Section 2 — Survey Methodology

Protocol derived from Kitchenham's methodology for systematic reviews in
computer science, with steps 5-7 (quality assessment, data extraction,
synthesis) omitted as inapplicable to software.

**2.1 Related surveys.** Gartner's "Magic Quadrant for Data Quality Tools"
(2016/2017/2019) is vendor-focused and does not compare functionality;
Fraunhofer IAO (2012, German only) is closest in structure; Woodall et al.
classify methods not tools; Barateiro & Galhardas (2005) is unsystematic
and dated; Pushkarev et al. (2010) and Pulla et al. (2016) cover 7 and 10
free tools with Y/N granularity; Gao et al. (2016) covers big-data QA
without a stated methodology. Conclusion: "To the best of our knowledge
there exists no systematic survey that evaluates state-of-the-art tools
with respect to DQ measurement and monitoring in detail."

**2.2 Research questions**, quoted:

> "1. Which data profiling capabilities are supported by current DQ tools?
> 2. Which data quality dimensions and metrics can be measured with current
> DQ tools?
> 3. Do DQ tools allow continuous data quality monitoring over time?"

**2.3 Search strategy.** Search expression `("data quality" OR "information
quality") AND tool` applied to ACM DL, GitHub, Google Scholar, IEEE Xplore,
Science Direct and Springer Link (Table 1 records the per-engine syntax),
plus a random Google search and the tool lists of six previous surveys.

**Figure 1** is the funnel:

```
  source                        #results   #tools
  ACM Digital Library                 84       34
  GitHub                             418      296
  Google Scholar                      44       21
  IEEE Xplore                        297       86
  Science Direct                     118       20
  Springer Link                      337      127
                          systematic subtotal  567
  related surveys (6)                         110
  random Google search                         43
                          ------------------------
                          total with duplicates 720
                          distinct tools        667

  excluded by criterion (multiple selection possible):
    EC1 domain-specific                        339
    EC2 dedicated to a specific data mgmt task 267   (EC2a cleansing 111,
                                                      EC2b integration 46,
                                                      EC2c other 110)
    EC3 not publicly available                  92
    EC4 deprecated                             102
    EC5 GitHub with no information              65
    EC6 requires a fee, no trial                10
                          selected for study     17
                          actually evaluated     13
```

**2.4 The six exclusion criteria**, quoted:

> (EC1) The tool is domain-specific (e.g., for web data or a specific
> implementations only).
> (EC2) The tool is dedicated to specific data management tasks without
> explicitly offering DQ measurement. (a) data cleansing; (b) data
> integration (including on-the-fly DQ checks); (c) other data management
> tasks (e.g., data visualization).
> (EC3) The tool is not publicly available.
> (EC4) The tool is considered deprecated (i.e., the vendor does not exist
> any more or the tool was found on GitHub and the last commit was before
> January 1st, 2016).
> (EC5) The tool was found on GitHub without any further information
> available.
> (EC6) The tool requires a fee and no free trial is offered upon request.

Four of the 17 were not evaluated: three required a SAP installation the
authors did not have, and IBM InfoSphere Information Server for Data
Quality "could not be installed successfully during the time of the
project, despite great effort but with little support from IBM."

### Section 3 — Theory on Data Quality and Evaluation Framework

**The four core activities of a DQ methodology**, from Batini et al. and
others: "(1) state reconstruction, (2) DQ measurement or assessment, (3)
data cleansing or improvement, and (4) the establishment of continuous DQ
monitoring."

**Data profiling** is defined as "the process of analyzing a dataset to
collect data about data (i.e., metadata) using a broad range of
techniques. Thus, it is an essential task prior to any DQ measurement or
monitoring activity to get insight into a given dataset."

**Measurement vs. assessment**, a distinction the paper insists on:

> "Assessment is the 'evaluation or estimation of the nature, ability, or
> quality of something' and extends the concept of measurement by
> evaluating the measurement results and drawing a conclusion about the
> object of assessment." (Sec. 3)

**Data cleansing**, with a warning:

> "While automated data cleansing methods are very valuable for large
> amounts of data, they pose risks to insert new errors that are rarely
> well understood." (Sec. 3)

**DQ monitoring**, and the distinction that most people miss:

> "There is a difference between 'data monitoring', which describes
> continuous checking of rules, and 'DQ monitoring', which is ongoing
> measurement of DQ." (Sec. 3)

**3.1 Dimensions and metrics.** "there is still no consensus on which
dimensions are the essence for DQ measurement". The four most frequently
used are **accuracy, completeness, consistency, timeliness**. Piro's split
between "hard dimensions" (objectively measurable by check routines) and
"soft dimensions" (subjective) is introduced, with the caveat that "also
objective check routines require a preceding subjective and domain-specific
definition of the data objects to be measured".

A metric "is a function that maps a quality dimension to a numerical
value", measurable at value-, column-, tuple-, table- or database-level,
aggregated upward typically by a weighted arithmetic mean.

Heinrich et al.'s five requirements for a DQ metric are quoted: "the
existence of minimum and maximum metric values (R1), the interval scaling
of the metric values (R2), the quality of the configuration parameters and
the determination of the metric values (R3), the sound aggregation of the
metric values (R4), and the economic efficiency of the metric (R5)".

The concrete metrics given, in the paper's own notation:

```
  Free-of-error rating = 1 - (number of data units in error
                              / total number of data units)        (1)

  accuracy = f( NrOfCorrectValues / TotalNrOfValues, ROE, PDOE )   (2)
    where ROE = randomness of the occurrence of an error,
          PDOE = probability distribution of the occurrence of an error

  Q_Gen(w, A) = min( s(w) / s_opt(A) , 1 )                         (3)
    Hinrichs' accuracy at attribute-value level: s(w) = actual number of
    digits and decimals of value w; s_opt(A) = optimal number for
    attribute A.  Tuple-level (4) is the weighted mean over attributes
    with expert weights g_j; table level is the arithmetic mean over
    tuples; DB level the mean over tables.

  completeness = 1 - (number of incomplete elements
                      / total number of elements)                  (5)

  Q_Time(t) = exp( -decline(A) * t )                               (6)
    where decline(A) is the rate at which attributes go out of date.

  Q_Kon(w) = 1 / ( SUM_j r_j(w) * g_j + 1 )                        (7)
    consistency of attribute value w over n rules, where g_j is the
    severity of rule j and r_j(w) = 0 if w satisfies rule j, 1 otherwise (8)
```

One remark on completeness that matters for us:

> "It should be pointed out that the number of missing values can be
> calculated in different ways, either by taking into account only true
> missing values (i.e. null), or also default values or a textual entry
> stating 'NaN'." (Sec. 3.1.2)

And a monitoring idea worth stealing, from Sebastian-Coleman: measure
consistency over time "by comparing the 'record count distribution of
values (column profile) to past instances of data populating the same
field'."

**3.3 TABLE 2 — THE 43-ITEM REQUIREMENTS CATALOG.** Reproduced in full,
because this is the reusable artefact:

```
  DATA PROFILING
  Single column - cardinalities
     1  Number of rows
     2  Number of null values
     3  Percentage of null values
     4  Number of distinct values ("cardinality")
     5  Number of distinct values divided by the number of rows
     6  Frequency histograms (equi-width, equi-depth, etc.)
  Single column - value distributions
     7  Minimum and maximum values in a numeric column
     8  Constancy: frequency of most frequent value / number of rows
     9  Quartiles: 3 points dividing the values into 4 equal groups
    10  Distribution of first digit in numeric values (Benford's law)
  Single column - patterns, data types, domains
    11  Basic type (numeric, alphanumeric, date, time)
    12  DBMS-specific data type (varchar, timestamp)
    13  Measurement of value length (min, max, average, median)
    14  Maximum number of digits in numeric values
    15  Maximum number of decimals in numeric values
    16  Histogram of value patterns (Aa9...)
    17  Generic semantic data type (code, date/time, quantity, identifier)
    18  Semantic domain (credit card, first name, city)
  Dependencies
    19  Unique column combinations (key discovery)
    20  Relaxed unique column combinations
    21  Inclusion dependencies (foreign key discovery)
    22  Relaxed inclusion dependencies
    23  Functional dependencies
    24  Conditional functional dependencies
  Advanced multi-column profiling
    25  Correlation analysis
    26  Association rule mining
    27  Cluster analysis
    28  Outlier detection
    29  Exact duplicate tuple detection
    30  Relaxed duplicate tuple detection

  DATA QUALITY MEASUREMENT
  DQ dimensions
    31  Metric to measure accuracy
    32  Metric to measure completeness
    33  Metric to measure consistency
    34  Metric to measure timeliness
    35  Metrics to measure other DQ dimensions
  Rule-based checks
    36  Creation of business rules
    37  Availability of general-applicable integrity rules
    38  Verification of data against business rules

  CONTINUOUS DATA QUALITY MONITORING
    39  Scheduling a DQ metric or data profiling task in user-defined
        periods
    40  Storage of DQ measurements and data profiling results
    41  Retrieval of DQ measurements or data profiling results
    42  Comparison between several DQ measurements or profiling results
    43  Visualization of DQ measurements / profiling results over time
```

The profiling requirements are based on Abedjan et al.'s data profiling
taxonomy. The test database is "a modernized version of the well-known
Northwind DB by dofactory".

### Section 4 — Data Quality Tool Evaluation

**4.1** describes each of the 13 evaluated tools: Aggregate Profiler,
Apache Griffin, Ataccama ONE, DataCleaner (Human Inference), Datamartist,
Experian Pandora, Informatica Data Quality, InfoZoom & IZDQ, MobyDQ,
OpenRefine & MetricDoc, Oracle Enterprise Data Quality, Talend Open Studio
for Data Quality, SAS Data Quality. Plus textual descriptions of the three
SAP-dependent tools and the failed IBM installation.

Anecdotes worth remembering because they are about installability, not
features: Apache Griffin required JDK, MySQL, npm, Hadoop, Spark, Hive,
Livy and ElasticSearch, and "two experienced computer scientists needed
over a week to complete the full installation." IBM ISDQ could not be
installed at all.

#### 4.2.1 Data profiling capabilities (Table 3)

The summary finding: "basic single-column data profiling like cardinalities
(DP 1-5) are covered by most tools, but more sophisticated functionalities,
like dependency discovery and multi-column profiling, are offered only in
single cases."

**The most instructive part of the whole paper is that identical test
cases produce different answers across tools.** Three examples:

- Percentage of nulls in one column: "55 % with Datamartist, 55.2 % with
  Oracle EDQ and SAS DataFlux, and 55.17 % in all other tools."
- **Quartiles (Table 4).** Asked for Q1/Q2/Q3 of one column, Aggregate
  Profiler, DataCleaner and Talend return 12 / 18.4 / 32 (true quartiles);
  SAS returns 12.9375 / 19.475 / 33.4375 (demi-deciles, 20 blocks, but the
  UI calls them "percentiles"); InfoZoom returns the inverse function
  (cumulative distribution per value, 2,155 blocks); Ataccama returns
  deciles. "the determination of quantiles is interpreted differently in
  the single DQ tools with respect to the notation ('Q1' vs. 'lower
  quartile' vs. 25 %) as well as the type of quantile."
- **Basic types (Table 5).** The same column is reported as String, Text,
  Alphanumeric, String(32) — and one numeric column as String, Number,
  Decimal, Decimal(5,2), `####.##`, String/numeric, Numeric, Long
  depending on the tool.
- **An outright bug.** "our test case for DP-25 (Pearson correlation ...)
  yielded -0.045350608 with Aggregate Profiler, which did not conform to
  our cross-check using SAS Enterprise Guide (0.00737) and the Python
  package numpy (0.00736647)."

**Dependency discovery** (DP 19-24) is "the lowest coverage of the data
profiling category and is best supported by Experian Pandora and
Informatica DQ". Definitions given: a *unique column combination* is "an
attribute set whose projection contains no duplicate entries" — a candidate
key; an *inclusion dependency* over schemata states "that all values in
attribute set alpha also occur in beta" — foreign key discovery; a
*functional dependency* "asserts that all pairs of records with the same
attribute values in alpha must also have the same attribute values in
beta". Worked results are given on the test DB, including relaxed
(thresholded) variants.

**OUTLIER DETECTION (DP-28) — the finding that matters for us:**

> "Our investigation showed that outlier detection is implemented in the
> tools very differently, and compared to the current state of research,
> only simple methods are used. We have not found a tool that supports
> multivariate outlier detection or one of the more sophisticated
> approaches like z-score, linear regression models, or probabilistic
> models as mentioned in [3]." (Sec. 4.2.1)

What the tools actually do:

- Aggregate Profiler, Ataccama ONE, Datamartist and InfoZoom: **visual
  only** — quantile plot, bar chart or box plot. "Aggregate Profiler and
  Ataccama ONE do not allow drill-down to the actual outlying values and in
  InfoZoom the visualization of the single values in the plot are not
  readable. In all three tools, it is not possible to modify the plot
  settings or to get details about the used settings."
- Experian Pandora: two user parameters, "Rarity Threshold" (default 1000)
  and "Standard Deviation Tolerance" (default 3.3). On the test case it
  returned 18 outlying values.
- Informatica DQ: "pattern outliers" and "value frequency outliers" only —
  "it was not possible to perform our test case, because the characteristic
  of being an outlier depends on the frequency instead of the actual
  value."
- SAS: a fixed list of the five smallest and five largest values, no
  configuration.

The same test case therefore yields one outlier (Datamartist), five (SAS)
or eighteen (Pandora), all "correct".

**Duplicate detection** (DP-29/30) is by contrast well and uniformly
supported: "In contrast to clustering and outlier detection, the
understanding and implementation of duplicate detection is very similar
across all tools we investigated." The user selects columns, optionally
transforms them, and picks a distance function. The paper lists the
distance functions each tool offers — edit distance, Jaro, Jaro-Winkler,
Soundex, Metaphone, Double Metaphone, Levenshtein, q-grams, Hamming,
bigram, cosine similarity, fingerprint, n-gram fingerprint, Cologne
phonetics. DataCleaner uses a two-phase ML approach (pre-selection, then
scoring with a random forest) returning a duplicate probability in [0,1].

#### 4.2.2 DQ measurement capabilities (Table 7)

The headline result, and it is stark. Across 13 tools:

```
  31  accuracy metric      implemented by ONE tool (Apache Griffin)
  32  completeness metric  partial in 6, full in 1 (MobyDQ)
  33  consistency metric   implemented by NO tool
  34  timeliness metric    implemented by NO tool
  35  other DQ metrics     partial in 5, full in 2
  36  create business rules      supported by 11 of 13
  37  general-applicable rules   4 of 13
  38  apply business rules       11 of 13
```

Apache Griffin's accuracy metric is `A_tab = |r_a| / |r| * 100%` comparing
a target table against a user-supplied source table — i.e. it requires a
gold standard. MobyDQ's completeness metric likewise compares target
against source. And:

> "in scenarios where the quality of a single data source should be
> assessed, such metrics are not suitable since a reference or gold
> standard is often not available." (Sec. 5.4)

MetricDoc (the OpenRefine extension) is caught mislabelling: it "offers a
metric that is denoted 'completeness' in the GUI ... [but] they calculate
the missingness M_att on attribute-level and thus did not fulfill
requirement DQM-32." Its "uniqueness" metric actually computes redundancy.
MetricDoc does implement two dimensions nobody else does — *validity* (the
fraction of values not complying with the column data type) and
*plausibility* (the fraction of values that are outliers under a robust or
non-robust statistic).

Aggregation is the other systematic gap: "The aggregation of DQ dimensions
from value-level to attribute-, record-, table-, DB- or
cross-data-source-level ... was not provided by any tool prefabricated.
Informatica DQ is the only tool that allows to aggregate column-level
metrics on table-level, but not higher."

#### 4.2.3 DQ monitoring capabilities (Table 8)

Storage of results (CDQM-40) is universal. Scheduling is widely supported.
Retrieval, comparison and visualisation over time are much patchier, and
"In general-purpose DQ tools, DQ monitoring is considered a premium
feature, which is liable to costs and only provided in professional
versions." The most complete general-purpose support is Informatica DQ
(via "scorecards") and DataCleaner; among open-source, only Apache Griffin.

### Section 5 — Survey Discussion and Lessons Learned

**5.1 Market overview.** 667 tools found; ~50.8% domain-specific; 40%
dedicated to a specific data management task. Informatica DQ judged "the
most mature"; Experian Pandora best for profiling, being the only tool that
"allows to profile across an entire DB and even across multiple connected
data sources. All other tools allow data profiling only for selected
columns or within specific tables."

**5.2 Data profiling and its relevance.** The distinction between profiling
and mining is "fuzzy" (Abedjan et al.: columns vs. rows, technical metadata
vs. new insights) and the authors go further: "we go one step further and
claim that there is also no clear distinction between data mining and data
analytics with respect to the used techniques". The practical consequence
is that advanced multi-column profiling is absent from DQ tools because
"customers and vendors simply do not consider it as part of data profiling
and data quality."

A warning about ML in this setting that is worth carrying:

> "the methods should be widely applicable, easy to use, interpret, store
> and deploy, and should have short response times. A counterexample are
> neural networks, which are increasingly applied in recent research
> initiatives, but need to be handled with care for DQ measurement, because
> they are black-box and hard to interpret. For measuring the quality of
> data (to ensure reliable and trustworthy data analysis), easy and clearly
> interpretable statistics and algorithms are required to prevent a user
> from deriving wrong conclusions from the results." (Sec. 5.2)

**5.4 How to measure data quality.** The paper's most important section and
its strongest claim:

> "We did not find a tool that implements a wider range of DQ metrics for
> the most important DQ dimensions as proposed in research papers ...
> Identified DQ metric implementations have several drawbacks: some are
> only applicable on attribute-level (e.g., no aggregation possibility),
> some require a gold standard that might not exist, and some have
> implementation errors." (Sec. 5.4)

> "Apart from completeness and uniqueness on attribute-level, no DQ
> dimension finds wide-spread agreement in the implementation and
> definition in practice. This is especially noteworthy for the frequently
> mentioned accuracy dimension, which however, requires a reference data
> set that is often not available in practice." (Sec. 5.4)

Vendors' own explanation, reported at first hand: "Other vendors justified
the absence of generally applicable DQ metrics with two reasons: because
such metrics are not feasible in practice, and because customers do not
request it." And, damningly: "while some explicitly stated that they do not
offer generally applicable DQ metrics, others could not answer the question
of how specific metrics are implemented."

The conclusion, quoted because it is a licence to skip a whole body of
theory:

> "We conclude that there is a strong need to question the current usage of
> DQ dimensions and metrics. Research efforts to measure DQ dimensions
> directly with a single, generally-applicable DQ metric have little
> practical relevance and can hardly be found in DQ tools. **In practice,
> DQ dimensions are used to group domain-specific DQ rules (sometimes
> referred to as metrics) on a higher level.** Since research and
> practitioners failed to create a common understanding of DQ dimensions
> and their measurement for decades, a complementary and more practice
> oriented approach should be developed. Several DQ tools show that DQ
> measurement is possible without referring to the dimensions at all.
> Since our focus is the automation of DQ measurement, a practical approach
> would be required without the need for DQ dimensions, but a focus on the
> core aspects (like missing data and duplicate detection), which can
> actually be measured automatically." (Sec. 5.4)

It cites Dasu & Johnson (2003) as having said the same thing sixteen years
earlier about the MIT TDQM dimensions: "not practically implementable and
it is often not clear what they mean."

**5.5 The requirement for automation and declaration.** Two asks. More
automated out-of-the-box profiling across tables and sources. And:

> "In several tools (e.g., AggregateProfiler, InfoZoom), plots were
> generated or outliers were detected without a clear declaration of the
> used threshold or distance function. In alignment with the requirement
> for interpretability of data profiling results, we highlight the need for
> clear declaration of the parameters used." (Sec. 5.5)

### Section 6 — Conclusion and Outlook

Restates the method and the counts. Future work: a practical DQ methodology
"that regards at directly measurable aspects of DQ in contrast to abstract
dimensions with no common understanding"; automated out-of-the-box
profiling with parameter declaration; time-series analytics over monitoring
results. Closes with market-size figures: Experian ~7,200, Informatica
~5,000, SAS ~2,700 customers for their DQ product lines.

---

## 4. Definitions, stated as the paper states them

**Data profiling** (Sec. 3): "the process of analyzing a dataset to collect
data about data (i.e., metadata) using a broad range of techniques. Thus,
it is an essential task prior to any DQ measurement or monitoring activity
to get insight into a given dataset."

**Measurement vs. assessment** (Sec. 3): measure = "to ascertain the size,
amount, or degree of something by using an instrument or device marked in
standard units or by comparing it with an object of known size"; assessment
"extends the concept of measurement by evaluating the measurement results
and drawing a conclusion about the object of assessment."

**Data monitoring vs. DQ monitoring** (Sec. 3): "There is a difference
between 'data monitoring', which describes continuous checking of rules,
and 'DQ monitoring', which is ongoing measurement of DQ."

**DQ metric** (Sec. 3.1): "a function that maps a quality dimension to a
numerical value, which allows an interpretation of a dimension's
fulfillment."

**Constancy** (DP-8, after Abedjan et al.): "the ratio of the frequency of
the most frequent value (possibly a pre-defined default value) and the
overall number of values".

**Unique column combination** (Sec. 4.2.1): "an attribute set alpha
contained in R whose projection contains no duplicate entries in r. In
other words, a UCC is a (possibly composite) candidate key that
functionally determines R."

**Inclusion dependency** (Sec. 4.2.1): "over the relational schemata R_i
and R_j states that all values in attribute set alpha also occur in beta".

**Functional dependency** (Sec. 4.2.1): "alpha -> beta asserts that all
pairs of records with the same attribute values in alpha must also have the
same attribute values in beta."

**Duplicate detection** (Sec. 4.2.1, quoting [23]): "aims to identify
records [...] that refer to the same real-world entity".

---

## 5. What this means for siting-atlas

### 5.1 It is the best available argument for NOT building a dimension framework

If someone asks why our data-quality work is a list of concrete checks
rather than a scorecard of accuracy / completeness / consistency /
timeliness, this paper is the answer, and it is empirical rather than
rhetorical. Thirteen production tools, some of them market leaders with
thousands of customers: **zero implement a consistency metric, zero
implement a timeliness metric, one implements accuracy (and only against a
user-supplied gold standard), and the completeness implementations are
attribute-level with no aggregation.** Two vendors could not explain how
their own metrics worked.

The authors' own conclusion is the sentence to cite: "In practice, DQ
dimensions are used to group domain-specific DQ rules (sometimes referred
to as metrics) on a higher level."

That is precisely the structure `DATA_QUALITY.md` already has — a Rahm & Do
taxonomy used to *group* 22 concrete checks — and this paper says that is
what practice actually converges on. It is a defensible position, not a
shortcut.

### 5.2 Table 2 is a scorecard we can be graded against

Scoring `siting-atlas` honestly against the 43 requirements, from what the
audit in `DATA_QUALITY.md` establishes:

```
  DP 1-5   cardinalities, nulls           YES  panel.py coverage +
                                               panel_report.json
  DP 6-10  value distributions            NO   no histograms, no min/max
                                               report, no constancy, no
                                               quartiles anywhere in src/
  DP 11-18 types, patterns, domains       PART dtypes are pinned; no
                                               pattern or semantic-domain
                                               profiling
  DP 19-22 UCCs and INDs                  PART assert_grain (panel.py:168)
                                               is one hand-declared UCC and
                                               it holds; no discovery, and
                                               no IND / referential report
                                               (this is exactly R7)
  DP 23-24 functional dependencies        NO   would have found the
                                               EJScreen county broadcast
                                               (F7) automatically
  DP 25-28 correlation, clustering,
           outliers                       NO   F6: zero outlier screening
  DP 29-30 duplicate detection            PART linkage.py is better than
                                               most surveyed tools, but is
                                               never run over
                                               national_facilities.csv
  DQM 31-35 dimension metrics             NO   and per 5.1 above, that is
                                               defensible
  DQM 36-38 business rules                NO   22 edits exist in a
                                               markdown document, not in
                                               code.  This is R6.
  CDQM 39-43 monitoring over time         NO   nothing compares today's
                                               profile to yesterday's
```

Two observations from that. First, our single biggest gap relative to a
commodity 2019 tool is **DP 6-10 and DP 19-24** — value distributions and
dependency discovery — neither of which is hard. Second, the thing we do
best (`linkage.py`) is genuinely competitive with the surveyed tools, which
is worth saying in a defence.

### 5.3 Our outlier problem is not unusual and nobody has solved it either

`DATA_QUALITY.md` F6 treats the absence of outlier detection as a
self-inflicted gap. This survey shows it is the state of the market:

> "We have not found a tool that supports multivariate outlier detection or
> one of the more sophisticated approaches like z-score, linear regression
> models, or probabilistic models."

Four of thirteen tools offer outlier detection only as an unlabelled plot
you cannot drill into. That does not excuse us, but it reframes R9: we
should not be trying to match an imagined industry standard, because there
isn't one. What we should copy is the one tool that does it defensibly —
Experian Pandora, which exposes **two declared user parameters** (rarity
threshold, standard-deviation tolerance) and lets you drill to the rows.

Which lands on the paper's closing demand, and it is the right design rule
for R9:

> "In several tools ... plots were generated or outliers were detected
> without a clear declaration of the used threshold or distance function
> ... we highlight the need for clear declaration of the parameters used."

Whatever screen R9 implements, the threshold must be in the output next to
the count.

### 5.4 The reproducibility lesson from Table 4

Five tools asked for quartiles of one column returned five different
things, three of them not quartiles, one of them labelled "percentiles" in
the UI while computing demi-deciles. And one tool's Pearson correlation was
simply wrong against numpy and SAS.

The lesson for us is about `outputs/metrics/`: any summary statistic we
publish must say what it is precisely enough to be recomputed. "28.36% of
ZCTAs are outliers" is exactly the kind of number this paper is warning
about. "28.36% of 33,772 ZCTAs have |modified z| > 3.5 on household
density, where modified z uses the median and MAD" is not.

### 5.5 Two small transferable ideas

**Constancy (DP-8)** — "frequency of most frequent value divided by number
of rows", flagged in the catalog as "possibly a pre-defined default value".
That single statistic, run over our columns, surfaces the hidden-missing-
value problem for free: `open_quarter` would show constancy 0.442, and 86
ZCTAs at exactly 250001 would stand out in a value-frequency profile. It is
one line of pandas and it is requirement number eight of forty-three.

**Consistency over time** — Sebastian-Coleman's suggestion of comparing
"record count distribution of values (column profile) to past instances of
data populating the same field". That is the check that would catch a
silent source-vintage change, which is precisely hazard two under F8
(`oesm24ma.zip` swapped for `oesm25ma.zip` with nothing noticing).

---

## 6. What I did NOT read or did not understand

- **I read all 30 PDF pages**, but two parts less carefully than the rest
  and I will say which. Section 4.1 (the thirteen tool descriptions,
  printed pp. 11-15) I read in full but have summarised only in outline —
  it is vendor-by-vendor narrative about installation experience, customer
  support and UI impressions, and almost none of it is transferable. And
  Appendix A (the Northwind test database and test cases) is referenced
  throughout the body but I did not work through it; my reading of Tables
  3-8 relies on the body text's descriptions of each test case rather than
  on the appendix's specification of them.
- **Tables 3, 7 and 8 have rotated column headers that the PDF text layer
  renders as a vertical jumble.** I reconstructed the tool ordering from
  the alphabetical listing in Section 4.1 and from the body text's
  discussion of individual cells. The *aggregate* claims I make above —
  "zero tools implement a consistency metric", "one implements accuracy" —
  are stated in the prose of Sections 4.2.2 and 5.4 as well as in the
  tables, so they are safe. **I would not trust any single cell I attribute
  to a specific tool without re-rendering the page.**
- **The metric formulae in Section 3.1 (equations 1-8) are transcribed from
  a damaged text layer.** Equations 1 and 5 are simple and certainly right.
  Equations 3, 4, 6, 7 and 8 I have reconstructed and believe are right,
  but the subscripts and the exact form of Hinrichs' normalisation are my
  reading. Do not implement from my transcription.
- **This is a 2019 survey of a fast-moving market and it is now stale.**
  Several evaluated tools have been renamed, absorbed or discontinued since
  (the paper itself records Quadient/DataCleaner and Experian
  Pandora/Aperture mid-transition). Treat every tool-specific statement as
  historical. The *findings about the field* — no consensus on metrics, no
  aggregation, outlier detection primitive — are what survives.
- **I have not read Abedjan et al.'s data profiling survey**, on which the
  DP section of the requirements catalog is based, nor Aggarwal's outlier
  analysis book [3], nor Sebastian-Coleman [68], all of which are cited
  heavily here. None is in `../Research/`.
- **The peer-reviewed IEEE Access version (2022) may differ.** I read the
  arXiv v1 preprint of 18 July 2019 only.
