# Notes — Rahm & Do (2000), Data Cleaning: Problems and Current Approaches

*Read in full 2026-09-13 from the PDF. These notes exist so nobody has to
open the PDF again.*

---

## 1. Citation and local file

```
  Erhard Rahm and Hong Hai Do, University of Leipzig.
  "Data Cleaning: Problems and Current Approaches."
  Bulletin of the IEEE Computer Society Technical Committee on Data
  Engineering, 23(4):3-13, December 2000.

  Local file:  ../Research/TBDE2000.pdf   (11 PDF pages; printed pp. 3-13)
  PDF page 1 = printed p. 3.  Add 2 to a printed page to get the PDF page.
```

Note the year. The bulletin issue is dated December 2000; the paper is
universally cited as Rahm & Do (2000). The PDF metadata says the file was
distilled in 2001, which is irrelevant.

Do's footnote on p. 3: "This work was performed while on leave at Microsoft
Research, Redmond, WA."

---

## 2. What the paper is for

It is a nine-page survey, not a method paper. It does two things we care
about. First, it gives the canonical **classification of data quality
problems** (Figure 2, Tables 1-3) that lets you audit a pipeline against a
checklist instead of against whatever you happened to notice. Second, it
sets out the **phases of a data cleaning process** (Section 3) and the
**data profiling metadata** that detects each problem class (Table 3). It
also surveys the commercial tool market of 2000, which is now of historical
interest only. There are no theorems, no proofs, no experiments and no
data. Its value is entirely taxonomic, and that is exactly what we need it
for.

Abstract, in full:

> "We classify data quality problems that are addressed by data cleaning
> and provide an overview of the main solution approaches. Data cleaning is
> especially required when integrating heterogeneous data sources and
> should be addressed together with schema-related data transformations. In
> data warehouses, data cleaning is a major part of the so-called ETL
> process. We also discuss current tool support for data cleaning."

---

## 3. Section-by-section walkthrough

### Section 1 — Introduction (printed pp. 3-4)

Defines the subject:

> "Data cleaning, also called data cleansing or scrubbing, deals with
> detecting and removing errors and inconsistencies from data in order to
> improve the quality of data." (Sec. 1, first line)

Argues that the need rises sharply on integration, because independent
sources hold "redundant data in different representations". Names the
consequence in one phrase that has been quoted ever since: duplicated or
missing information "will produce incorrect or misleading statistics
('garbage in, garbage out')".

**Figure 1** (printed p. 4) is the ETL diagram: three operational source
cylinders on the left, a box labelled "Extraction, Transformation, Loading"
split into three columns — Extraction / Integration / Aggregation — and a
Data warehouse cylinder on the right. The top row of the box is the
metadata flow (Schema extraction and translation -> Schema matching and
integration -> Schema implementation); the bottom row is the data flow
(Instance extraction and transformation -> Instance matching and
integration -> Filtering, aggregation). A **Data staging area** cylinder
sits between Integration and Aggregation. Underneath everything runs a bar
labelled "Scheduling, logging, monitoring, recovery, backup". Five numbered
metadata items: (1)(3) Instance characteristics (real metadata), (2)
Translation rules, (4) Mappings between source and target schema, (5)
Filtering and aggregation rules.

The load-bearing claim from Figure 1, stated in the text: "all data
cleaning is typically performed in a separate data staging area before
loading the transformed data into the warehouse."

Section 1 then lists the **requirements a data cleaning approach should
satisfy**. Paraphrasing tightly, because this is a list we should be
measured against:

1. Detect and remove all major errors and inconsistencies, both within
   individual sources and on integration.
2. Be supported by tools, to limit manual inspection and programming.
3. Be extensible to cover additional sources easily.
4. Not be performed in isolation, but together with schema-related data
   transformations, based on comprehensive metadata.
5. Mapping functions should be **specified in a declarative way** and be
   reusable for other sources and for query processing.
6. For warehouses, a workflow infrastructure should execute all steps
   reliably and efficiently.

Item 5 is the one that indicts a scatter of ad-hoc filters:

> "Mapping functions for data cleaning and other data transformations
> should be specified in a declarative way and be reusable for other data
> sources as well as for query processing." (Sec. 1)

Section 1 closes with a complaint that data cleaning "has received only
little attention in the research community" relative to schema integration.

### Section 2 — Data cleaning problems (printed pp. 4-7)

This is the section everything else cites.

**Figure 2** (printed p. 5), "Classification of data quality problems in
data sources", is a four-leaf tree. Transcribed exactly, including the
parenthetical box labels and the trailing ellipses:

```
                        Data Quality Problems
             /                                        \
   Single-Source Problems                      Multi-Source Problems
      /             \                            /              \
 Schema Level   Instance Level            Schema Level      Instance Level

 (Lack of       (Data entry errors)       (Heterogeneous    (Overlapping,
  integrity                                data models and   contradicting
  constraints,                             schema designs)   and inconsistent
  poor schema                                                data)
  design)

 - Uniqueness   - Misspellings            - Naming          - Inconsistent
 - Referential  - Redundancy/               conflicts         aggregating
   integrity      duplicates              - Structural      - Inconsistent
 ...            - Contradictory             conflicts         timing
                  values                   ...              ...
                ...
```

Three things about Figure 2 that are easy to get wrong from memory:

- The leaf lists are **illustrative and explicitly truncated** — each ends
  in "...". Figure 2 lists only two or three members per quadrant. The
  full enumerations are in Tables 1 and 2, and they are longer.
- The parenthetical under each leaf is a *cause* label, not a member. The
  single-source instance leaf is captioned "(Data entry errors)"; the
  multi-source instance leaf is captioned "(Overlapping, contradicting and
  inconsistent data)".
- Figure 2's single-source schema leaf names only Uniqueness and
  Referential integrity. Illegal values and violated attribute
  dependencies appear in Table 1, not Figure 2.

Text immediately after Figure 2, setting out what the two axes mean:

> "Schema-level problems of course are also reflected in the instances;
> they can be addressed at the schema level by an improved schema design
> (schema evolution), schema translation and schema integration.
> Instance-level problems, on the other hand, refer to errors and
> inconsistencies in the actual data contents which are not visible at the
> schema level. They are the primary focus of data cleaning." (Sec. 2)

And the caveat that the quadrants are not exclusive:

> "While not shown in Fig. 2, the single-source problems occur (with
> increased likelihood) in the multi-source case, too, besides specific
> multi-source problems." (Sec. 2)

#### The third axis — problem scope (Sec. 2.1)

**This is the part most summaries drop.** The taxonomy is not a 2x2. Inside
each of the four quadrants, problems are further differentiated by scope:

> "For both schema- and instance-level problems we can differentiate
> different problem scopes: attribute (field), record, record type and
> source; examples for the various cases are shown in Tables 1 and 2."
> (Sec. 2.1)

So the frame is 2 (source) x 2 (level) x 4 (scope). Tables 1 and 2 are
organised by that scope column, and reading them without it loses
information — "Duplicated records" is a *record type* problem, not an
attribute problem, and that is why an attribute-level profiler will never
find it.

#### Table 1 — single-source problems at SCHEMA level (printed p. 5)

Caption: "Examples for single-source problems at schema level (violated
integrity constraints)".

```
 Scope     Problem            Dirty Data              Reasons/Remarks
 --------------------------------------------------------------------------
 Attribute Illegal values     bdate=30.13.70          values outside of
                                                      domain range
 Record    Violated attribute age=22,                 age = current year -
           dependencies       bdate=12.02.70          birth year should hold
 Record    Uniqueness         emp1=(name="John        uniqueness for SSN
 type      violation          Smith", SSN="123456");  (social security
                              emp2=(name="Peter       number) violated
                              Miller", SSN="123456")
 Source    Referential        emp=(name="John         referenced department
           integrity          Smith", deptno=127)     (127) not defined
           violation
```

Exactly four classes. Note there is **no "missing values" row in Table 1**.

#### Table 2 — single-source problems at INSTANCE level (printed p. 6)

Caption: "Examples for single-source problems at instance level".

```
 Scope     Problem            Dirty Data              Reasons/Remarks
 --------------------------------------------------------------------------
 Attribute Missing values     phone=9999-999999       unavailable values
                                                      during data entry
                                                      (dummy values or null)
           Misspellings       city="Liipzig"          usually typos,
                                                      phonetic errors
           Cryptic values,    experience="B";
           Abbreviations      occupation="DB Prog."
           Embedded values    name="J. Smith          multiple values
                              12.02.70 New York"      entered in one
                                                      attribute (e.g. in a
                                                      free-form field)
           Misfielded values  city="Germany"
 Record    Violated attribute city="Redmond",         city and zip code
           dependencies       zip=77777               should correspond
 Record    Word               name1="J. Smith",       usually in a free-form
 type      transpositions     name2="Miller P."       field
           Duplicated         emp1=(name="John        same employee
           records            Smith",...);            represented twice due
                              emp2=(name="J.          to some data entry
                              Smith",...)             errors
           Contradicting      emp1=(name="John        the same real world
           records            Smith", bdate=          entity is described by
                              12.02.70);              different values
                              emp2=(name="John
                              Smith", bdate=
                              12.12.70)
 Source    Wrong references   emp=(name="John         referenced department
                              Smith", deptno=17)      (17) is defined but
                                                      wrong
```

Nine classes, against Figure 2's three. Points worth carrying:

- **"Missing values" is an INSTANCE-level, attribute-scope problem**, and
  its canonical example is a *dummy value*, `phone=9999-999999`, not a
  null. The Reasons column says "dummy values or null" — the two are the
  same class.
- **"Violated attribute dependencies" appears in BOTH tables** — at schema
  level (age vs. bdate) and at instance level (city vs. zip). It is not a
  schema-only problem.
- **"Embedded values"** means several distinct values crammed into one
  free-form field. It does not mean a sentinel or a code.
- "Duplicated records" and "Contradicting records" are different rows.
  Rahm & Do separate them deliberately: duplicates have the same values,
  contradictions have different values for the same entity.

Closing note of Sec. 2.1, on why a schema constraint is not enough:

> "Note that uniqueness constraints specified at the schema level do not
> prevent duplicated instances, e.g., if information on the same real world
> entity is entered twice with different attribute values."

And the prevention argument:

> "Given that cleaning data sources is an expensive process, preventing
> dirty data to be entered is obviously an important step to reduce the
> cleaning problem."

#### Section 2.2 — Multi-source problems (printed pp. 6-7)

At schema level the named problems are exactly two: **naming conflicts**
(homonyms — same name, different objects; synonyms — different names, same
object) and **structural conflicts** (attribute vs. table representation,
different component structure, different data types, different integrity
constraints).

At instance level the text names more than Figure 2 does. In order:

- all single-source instance problems, recurring with different
  representations in different sources (duplicated records, contradicting
  records, ...);
- **different value representations** for the same attribute, even where
  the names and data types agree — the example is marital status;
- **different interpretation of the values** — "e.g., measurement units
  Dollar vs. Euro";
- **different aggregation levels** — "sales per product vs. sales per
  product group";
- **different points in time** — "current sales as of yesterday for source
  1 vs. as of last week for source 2".

The last two are what Figure 2 abbreviates to "Inconsistent aggregating"
and "Inconsistent timing". The middle two — value representations and unit
interpretation — are named only in the prose, and are genuinely separate
classes.

The section then names the central multi-source task:

> "A main problem for cleaning data from multiple sources is to identify
> overlapping data, in particular matching records referring to the same
> real-world entity (e.g., customer). This problem is also referred to as
> the object identity problem, duplicate elimination or the merge/purge
> problem." (Sec. 2.2)

> "Frequently, the information is only partially redundant and the sources
> may complement each other by providing additional information about an
> entity. Thus duplicate information should be purged out and complementing
> information should be consolidated and merged in order to achieve a
> consistent view of real world entities." (Sec. 2.2)

**Figure 3** (printed p. 7), "Examples of multi-source problems at schema
and instance level", is three tables. Source 1 `Customer(CID, Name, Street,
City, Sex)` with rows 11 = Kristen Smith / 2 Hurley Pl / South Fork, MN
48503 / 0 and 24 = Christian Smith / Hurley St 2 / S Fork MN / 1. Source 2
`Client(Cno, LastName, FirstName, Gender, Address, Phone/Fax)` with rows 24
= Smith / Christoph / M / 23 Harley St, Chicago IL, 60633-2394 and 493 =
Smith / Kris L. / F / 2 Hurley Place, South Fork MN, 48503-5998. The third
table is the cleaned integrated target `Customers`, three rows, carrying
both `CID` and `Cno` so the source records can be traced.

The demonstrated conflicts: name conflicts (synonyms Customer/Client,
Cid/Cno, Sex/Gender), structural conflicts (different name and address
representations), different gender encodings ("0"/"1" vs. "F"/"M"), and a
duplicate (Kristen Smith = Kris L. Smith). Plus one subtlety worth
remembering:

> "while Cid/Cno are both source-specific identifiers, their contents are
> not comparable between the sources; different numbers (11/493) may refer
> to the same person while different persons can have the same number (24)."

And the ordering rule:

> "Note that the schema conflicts should be resolved first to allow data
> cleaning, in particular detection of duplicates based on a uniform
> representation of names and addresses."

### Section 3 — Data cleaning approaches (printed pp. 7-9)

Opens with the **five phases of data cleaning**. These are given as a
bulleted list, not numbered, but they are sequential. Quoting the phase
names and compressing the bodies:

1. **Data analysis.** "In order to detect which kinds of errors and
   inconsistencies are to be removed, a detailed data analysis is
   required. In addition to a manual inspection of the data or data
   samples, analysis programs should be used to gain metadata about the
   data properties and detect data quality problems."
2. **Definition of transformation workflow and mapping rules.** Early
   steps correct single-source instance problems and prepare for
   integration; later steps deal with schema/data integration and
   multi-source instance problems such as duplicates. "The schema-related
   data transformations as well as the cleaning steps should be specified
   by a declarative query and mapping language as far as possible, to
   enable automatic generation of the transformation code."
3. **Verification.** "The correctness and effectiveness of a
   transformation workflow and the transformation definitions should be
   tested and evaluated, e.g., on a sample or copy of the source data, to
   improve the definitions if necessary. Multiple iterations of the
   analysis, design and verification steps may be needed, e.g., since some
   errors only become apparent after applying some transformations."
4. **Transformation.** Execute the steps.
5. **Backflow of cleaned data.** "After (single-source) errors are
   removed, the cleaned data should also replace the dirty data in the
   original sources in order to give legacy applications the improved data
   too and to avoid redoing the cleaning work for future data
   extractions."

Then the metadata and lineage requirement, which is the sourced version of
"log your edits":

> "To support data quality, detailed information about the transformation
> process is to be recorded, both in the repository and in the transformed
> instances, in particular information about the completeness and freshness
> of source data and lineage information about the origin of transformed
> objects and the changes applied to them." (Sec. 3)

Note "and in the transformed instances" — the lineage is supposed to be
carried in the data, not only in a side log. Figure 3's target table
demonstrates it by keeping CID and Cno.

#### Section 3.1 — Data analysis (printed p. 8)

Two approaches: **data profiling** ("focusses on the instance analysis of
individual attributes") and **data mining** ("helps discover specific data
patterns in large data sets, e.g., relationships holding between several
attributes").

Data profiling derives "the data type, length, value range, discrete values
and their frequency, variance, uniqueness, occurrence of null values,
typical string pattern (e.g., for phone numbers), etc."

**Table 3** (printed p. 8), "Examples for the use of reengineered metadata
to address data quality problems". This is the detection cookbook and it is
the closest thing in the paper to an outlier-screening prescription:

```
 Problem          Metadata                  Examples/Heuristics
 ----------------------------------------------------------------------------
 Illegal values   cardinality               e.g., cardinality(gender) > 2
                                            indicates problem
                  max, min                  max, min should not be outside of
                                            permissible range
                  variance, deviation       variance, deviation of statistical
                                            values should not be higher than
                                            threshold
 Misspellings     attribute values          sorting on values often brings
                                            misspelled values next to correct
                                            values
 Missing values   null values               percentage/number of null values
                  attribute values +        presence of default value may
                  default values            indicate real value is missing
 Varying value    attribute values          comparing attribute value set of a
 representations                            column of one table against that of
                                            a column of another table
 Duplicates       cardinality + uniqueness  attribute cardinality = # rows
                                            should hold
                  attribute values          sorting values by number of
                                            occurrences; more than 1 occurrence
                                            indicates duplicates
```

The "Missing values" row deserves flagging twice: **"presence of default
value may indicate real value is missing"** is Rahm & Do telling you to go
looking for sentinels in 2000.

On data mining, the example given is an association rule at 99% confidence,
where "a confidence of 99% for rule 'total = quantity x unit price'
indicates that 1% of the records do not comply and may require closer
examination." (The PDF's text layer garbles the formula; the sense is
clear.)

#### Section 3.2 — Defining data transformations (printed pp. 8-9)

Argues for SQL:99 with user-defined functions over proprietary ETL rule
languages, on portability and reuse grounds. **Figure 4** is a worked
example: a `CREATE VIEW Customer2 (LName, FName, Gender, Street, City,
State, ZIP, CID) AS SELECT LastNameExtract(Name), FirstNameExtract(Name),
Sex, Street, CityExtract(City), StateExtract(City), ZIPExtract(City), CID
FROM Customer` — the UDFs in bold do the splitting and can carry cleaning
logic. Notes the limits: UDFs do not generically support attribute
splitting/merging or folding/unfolding, for which language extensions such
as SchemaSQL would be needed. Mentions a `Match` operator for approximate
joins as a desirable language extension.

#### Section 3.3 — Conflict resolution (printed p. 9)

Three preparatory single-source transformation types, named:

- **Extracting values from free-form attributes (attribute split)** —
  including "reordering of values within a field to deal with word
  transpositions".
- **Validation and correction** — "Spell checking based on dictionary
  lookup"; "dictionaries on geographic names and zip codes help to correct
  address data"; and, importantly, "Attribute dependencies (birthdate -
  age, total price - unit price / quantity, city - phone area code, ...)
  can be utilized to detect problems and substitute missing values or
  correct wrong values."
- **Standardization** — uniform date/time formats, case normalisation,
  stemming, resolving abbreviations and encoding schemes "by consulting
  special synonym dictionaries or applying predefined conversion rules".

Then ordering and matching. Duplicate elimination comes **after** the other
cleaning steps: "The duplicate elimination task is typically performed
after most other transformation and cleaning steps, especially after having
cleaned single-source errors and conflicting representations." Matching
runs on an identifying attribute where one exists (equi-join, or sort and
compare neighbours); otherwise a fuzzy match / approximate join scored 0-1,
with "different attributes in a matching rule may contribute different
weight to the overall degree of similarity". String techniques named:
wildcards, character frequency, edit distance, keyboard distance, phonetic
similarity (soundex); WHIRL using cosine distance in the vector-space
model. Cost: "Calculating the similarity value for any two records implies
evaluation of the matching rule on the cartesian product of the inputs."
The Hernandez-Stolfo multi-pass windowing approach is described as the
standard mitigation, with the total match set obtained as "the union of the
matching pairs of each pass and their transitive closure".

### Section 4 — Tool support (printed pp. 10-12)

A 2000-vintage vendor survey. Categories: data analysis and reengineering
tools (MIGRATIONARCHITECT for profiling; WIZRULE and DATAMININGSUITE for
mining; INTEGRITY for reengineering), specialised cleaning tools (name and
address: IDCENTRIC, PUREINTEGRATE, QUICKADDRESS, REUNION, TRILLIUM;
duplicate elimination: DATACLEANSER, MERGE/PURGE LIBRARY, MATCHIT,
MASTERMERGE), and ETL tools (COPYMANAGER, DATASTAGE, EXTRACT, POWERMART,
DECISIONBASE, DATATRANSFORMATIONSERVICE, METASUITE, SAGENTSOLUTIONPLATFORM,
WAREHOUSEADMINISTRATOR).

Two facts from this section survive its age. First: "TRILLIUM's extraction
(parser) and matcher module contains over 200,000 business rules" — the
scale at which domain rule libraries actually operate. Second, the standing
criticism of ETL tools:

> "ETL tools typically have little built-in data cleaning capabilities but
> allow the user to specify cleaning functionality via a proprietary API.
> There is usually no data analysis support to automatically detect data
> errors and inconsistencies." (Sec. 4.3)

Everything else in Section 4 is obsolete and I am not carrying it forward.

### Section 5 — Conclusions (printed p. 12)

Restates the classification, the need to treat schema- and instance-related
transformations together, and the tool gaps ("they do typically cover only
part of the problem and still require substantial manual effort or
self-programming", plus limited interoperability from proprietary APIs).
Future work: better languages for both schema and data transformation;
operators such as Match, Merge, Mapping Composition; cleaning under query
processing performance constraints; cleaning semi-structured/XML data.

Acknowledgments thank Phil Bernstein, Helena Galhardas and Sunita Sarawagi.
32 references.

---

## 4. Definitions, stated as the paper states them

**Data cleaning.** "Data cleaning, also called data cleansing or scrubbing,
deals with detecting and removing errors and inconsistencies from data in
order to improve the quality of data." (Sec. 1)

**Schema-level vs. instance-level.** "Schema-level problems of course are
also reflected in the instances; they can be addressed at the schema level
by an improved schema design (schema evolution), schema translation and
schema integration. Instance-level problems, on the other hand, refer to
errors and inconsistencies in the actual data contents which are not
visible at the schema level. They are the primary focus of data cleaning."
(Sec. 2)

**Problem scope.** "For both schema- and instance-level problems we can
differentiate different problem scopes: attribute (field), record, record
type and source." (Sec. 2.1)

**Missing values** (Table 2, attribute scope, instance level). Dirty data
example `phone=9999-999999`; reason "unavailable values during data entry
(dummy values or null)".

**Embedded values** (Table 2, attribute scope, instance level). Dirty data
example `name="J. Smith 12.02.70 New York"`; reason "multiple values
entered in one attribute (e.g. in a free-form field)".

**Contradicting records** (Table 2, record-type scope, instance level).
Dirty data example `emp1=(name="John Smith", bdate=12.02.70);
emp2=(name="John Smith", bdate=12.12.70)`; reason "the same real world
entity is described by different values".

**Data profiling.** "Data profiling focusses on the instance analysis of
individual attributes. It derives information such as the data type,
length, value range, discrete values and their frequency, variance,
uniqueness, occurrence of null values, typical string pattern (e.g., for
phone numbers), etc." (Sec. 3.1)

---

## 5. What this means for siting-atlas

**We had the taxonomy partly wrong, and it cost us a misdiagnosis.**
`docs/data/DATA_QUALITY.md` classified the ACS top-code (`income =
$250,001`, 86 ZCTAs) as Rahm & Do's *embedded values*. It is not. Embedded
values means several values in one free-form field. The top-code is Rahm &
Do's **Missing values** class, whose canonical example is literally a dummy
value, `phone=9999-999999`, and whose detection heuristic is spelled out in
Table 3: "presence of default value may indicate real value is missing".
That reclassification matters because it puts the top-code
(`ingest/census_api.py:110`), the bottom-codes, and
`warehouse/facilities.py:118`'s `open_quarter.fillna(1)` into **one class
with one fix**, instead of two unrelated findings.

**Missing values is an instance-level problem, not a schema-level one.**
DATA_QUALITY.md's scorecard listed it under SINGLE-SOURCE, SCHEMA LEVEL.
Table 1 has exactly four schema-level classes and missing values is not
among them. Corrected in that document.

**The scope axis is missing from our audit entirely.** Our scorecard is a
2x2; the paper's frame is 2x2x4. The scope column is what separates
"profile this attribute" from "you will never find this by profiling
attributes" — duplicated and contradicting records are record-type scope,
and no amount of per-column profiling surfaces them. That is precisely why
the three contradicting facility records
(`warehouse/facilities.py:206`) went unnoticed: `outputs/metrics/
panel_report.json` reports attribute-scope statistics only.

**Violated attribute dependencies belong at both levels.** Our 353 ZCTAs
with `population > 0` and `households = 0` are the instance-level form
(Table 2, record scope, `city="Redmond", zip=77777`), not the schema-level
form.

**Table 3 is the outlier answer, and it is not "detect outliers".** Rahm &
Do's prescription for illegal values is min/max against a permissible
range and "variance, deviation ... should not be higher than threshold" —
that is, a *declared* plausibility band per column, not a distributional
screen. Our F6 finding (28.36% of ZCTAs are robust-z outliers on density,
most of them genuinely Manhattan) is the direct consequence of running a
distributional screen where Rahm & Do prescribe a domain range check. A
robust-z on household density has no permissible range in it and so cannot
distinguish 162,659/sq mi in ZCTA 10069 from a data error.

**Phase 5, backflow, is a gap we have never named.** The five-phase process
ends with writing corrections back to the source so the work is not redone
on the next extraction. We re-derive everything from raw on every build and
have nowhere to put an adjudicated facility date except a code change. The
three facility date adjudications (R2) need a durable home outside
`src/`, or the next refresh of `national_facilities.csv` silently undoes
them.

**Requirement 5 of Section 1 is the sourced form of our edit-set
argument.** "Mapping functions for data cleaning ... should be specified in
a declarative way and be reusable". `cost/runner.py:57`,
`cost/runner.py:166` and `cost/daganzo.py:113` are none of those things.

**Lineage belongs in the data, not just the log.** Section 3's requirement
is that lineage be recorded "both in the repository and in the transformed
instances", and Figure 3 demonstrates it by keeping CID and Cno on the
merged row. Our equivalent gaps: `warehouse/optional.py` broadcasts
county-grain EJScreen values under ZCTA column names with no companion
column recording the source geography, and `data/interim/bls_wages.parquet`
has no year column at all.

**Section 2.2's "different interpretation of the values (measurement units
Dollar vs. Euro)" and "different points in time" are separate named
classes.** Our seven-year vintage spread inside a single panel row is the
second of these, and Figure 2's shorthand for it is "Inconsistent timing".
Our scorecard has that row; what it lacks is the unit-interpretation row,
which is where `employment` (ZIP, CBP, median 574) versus
`metro_employment` (CBSA, OES, median 449,410) actually lives.

---

## 6. What I did NOT read or did not understand

- **Nothing was skipped.** All 11 PDF pages were read: Sections 1-5,
  Figures 1-4, Tables 1-3, the acknowledgments and all 32 references.
- **Figures 1 and 2 are raster images** and do not appear in the PDF's text
  layer. I read them by rendering PDF pages 2 and 3 as images. The Figure 2
  transcription in Section 3 above is from that rendering and I am
  confident in it. Figure 1's five numbered legend items are small in the
  scan; I am confident of the five labels but would not swear to which
  arrow each number sits on.
- **Table 3's association-rule formula is garbled in the text layer**
  (`"total quantity = unit price"` with the numbers floated out of place).
  I have reconstructed it as `total = quantity x unit price` at 99%
  confidence from context. If that formula ever matters, re-check the
  rendered page.
- **Section 4 (tool support) I read but deliberately did not summarise in
  detail.** It is a 2000 vendor listing; most of the named products are
  discontinued or absorbed. I carried forward only the two statements that
  are still true of the tool market.
- **The references were read as a list, not followed.** Several are
  directly relevant and are NOT in `../Research/` — in particular [15]
  Hernandez & Stolfo on merge/purge, [11] Galhardas et al. on AJAX, and
  [25] Raman & Hellerstein on Potter's Wheel. If the multi-pass matching
  argument ever needs a primary source, [15] is it.
- **I have not verified the printed page numbers of Tables 2 and 3 against
  a page-numbered rendering.** The PDF text layer gives printed page
  numbers 3-13 in sequence and I have mapped tables to pages from that
  ordering. Section references above are safe; treat the printed page
  numbers as approximate to within one page.
