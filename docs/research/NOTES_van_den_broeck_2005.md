# Notes — Van den Broeck et al. (2005), Detecting, Diagnosing, Editing

*Read in full 2026-09-13. These notes exist so nobody has to open the PDF
again.*

---

## 1. Citation and local file

```
  Jan Van den Broeck, Solveig Argeseanu Cunningham, Roger Eeckels,
  Kobus Herbst.
  "Data Cleaning: Detecting, Diagnosing, and Editing Data Abnormalities."
  PLoS Medicine 2(10):e267, October 2005, pp. 966-970.
  DOI: 10.1371/journal.pmed.0020267.  PMC1198040.
  Article type: Policy Forum.  Open access (CC-BY).

  Local file:  ../Research/pmed.0020267.pdf   (5 PDF pages)
  PDF page 1 = printed p. 0966.  Printed pages run 0966-0970.
```

Author affiliations at the time: Van den Broeck (epidemiologist) and Herbst
(public-health physician) at the Africa Centre for Health and Population
Studies, Mtubatuba, South Africa; Cunningham (demographer) at the
University of Pennsylvania; Eeckels, Professor Emeritus of Pediatrics,
Catholic University of Leuven. Funded by the Wellcome Trust.

Note the author-order convention: the paper is universally cited as "Van
den Broeck et al. (2005)" and the second author is Argeseanu Cunningham,
not "Cucu". Our `CLEANING_LITERATURE.md` had the author list as "Van den
Broeck, Cucu, Mehta & Cunningham" — that is wrong and is corrected there.

---

## 2. What the paper is for

Five pages of clinical-epidemiology policy writing that give the single
most usable **procedure** in the cleaning literature: a three-stage,
*repeating* loop of screening, diagnosis and treatment, with an explicit
taxonomy of what you are screening for, an explicit taxonomy of the verdicts
you may reach, and explicit rules for when deletion is and is not
acceptable. It has no mathematics, no data and no theorems. Its value is
that it separates *noticing* from *deciding* from *acting*, and insists
that each be recorded.

It is also, unusually, a paper about the *ethics and reporting* of cleaning.
The recommendation in the abstract is a reporting standard:

> "We recommend that scientific reports describe data-cleaning methods,
> error types and rates, error deletion and correction rates, and
> differences in outcome with and without remaining outliers."

---

## 3. Section-by-section walkthrough

The paper is not numbered. Its headed sections, in order, are: (untitled
opening), "The History of Data Cleaning", "Data Cleaning as a Process",
"Screening Phase", "Diagnostic Phase", "Treatment Phase", "Data Cleaning as
a Study-Specific Process", "Documentation and Reporting", Acknowledgments,
References. Plus Box 1, Box 2, Table 1, Figure 1, Figure 2.

### Opening (printed p. 0966)

Frames the gap: error-prevention strategies exist but "errors occur in
spite of careful study design, conduct, and implementation of
error-prevention strategies. Data cleaning intends to identify and correct
these errors or at least to minimize their impact on study results. Little
guidance is currently available in the peer-reviewed literature on how to
set up and carry out cleaning efforts in an efficient and ethical way."

Quotes the Society for Clinical Data Management (2003) to establish that
this is a real hole:

> "Regulations and guidelines do not address minimum acceptable data
> quality levels for clinical trial data. In fact, there is limited
> published research investigating the distribution or characteristics of
> clinical trial data errors. Even less published information exists on
> methods of quantifying data quality."

### BOX 1 — Terms Related to Data Cleaning (printed p. 0966)

Quoted complete, because these are the paper's formal definitions:

> **Data cleaning:** Process of detecting, diagnosing, and editing faulty
> data.
>
> **Data editing:** Changing the value of data shown to be incorrect.
>
> **Data flow:** Passage of recorded information through successive
> information carriers.
>
> **Inlier:** Data value falling within the expected range.
>
> **Outlier:** Data value falling outside the expected range.
>
> **Robust estimation:** Estimation of statistical parameters, using
> methods that are less sensitive to the effect of outliers than more
> conventional methods.

Note how thin "outlier" is: **falling outside the expected range**. Not
"more than 3 MADs from the median". The range is something you *expect*,
i.e. declare, in advance. That matters — see §5.

### The History of Data Cleaning (printed p. 0966)

Argues that cleaning is under-reported because it is under-respected:

> "Data cleaning is emblematic of the historical lower status of data
> quality issues and has long been viewed as a suspect activity, bordering
> on data manipulation. Armitage and Berry almost apologized for inserting
> a short chapter on data editing in their standard textbook on statistics
> in medical research."

> "Concerns about where to draw the line between data manipulation and
> responsible data editing are legitimate. Yet all studies, no matter how
> well designed and implemented, have to deal with errors from various
> sources and their effects on study results."

And on the state of practice: "In practice, it is rare to find any
statements about data-cleaning methods or error rates in medical
publications."

The paper positions itself against a literature that has treated the
pieces separately: "Although certain aspects of data cleaning such as
statistical outlier detection and handling of missing data have received
separate attention, the data-cleaning process, as a whole, with all its
conceptual, organizational, logistical, managerial, and
statistical-epidemiological aspects, has not been described or studied
comprehensively."

Also notes that quality assurance is broader than cleaning: "The complete
process of quality assurance in research studies includes error prevention,
data monitoring, data cleaning, and documentation."

### Data Cleaning as a Process (printed pp. 0966-0967)

**The core statement of the framework.** This is the sentence to quote:

> "We present data cleaning as a three-stage process, involving repeated
> cycles of screening, diagnosing, and editing of suspected data
> abnormalities. Figure 1 shows these three steps, which can be initiated
> at three different stages of a study."

Two things our summary had wrong. It is a **repeated cycle**, not a
pipeline. And it **can be entered at three different points in a study**,
not only after collection.

**Figure 1** ("A Data-Cleaning Framework", illustration by Giovanni Maki,
printed p. 0967) is the loop diagram. The three stages — screening,
diagnosis, editing — form a cycle, with entry points at the questionnaire,
database and analysis-dataset stages of the data flow.

Why to do it deliberately rather than by accident:

> "Many data errors are detected incidentally during study activities other
> than data cleaning. However, it is more efficient to detect errors by
> actively searching for them in a planned way."

Why screening alone is not enough — the argument for a separate diagnostic
stage:

> "It is not always immediately clear whether a data point is erroneous.
> Many times, what is detected is a suspected data point or pattern that
> needs careful examination. Similarly, missing values require further
> examination. Missing values may be due to interruptions of the data flow
> or the unavailability of the target information. Hence, predefined rules
> for dealing with errors and true missing and extreme values are part of
> good practice."

**Data flow** is the organising concept for diagnosis:

> "After measurement, research data undergo repeated steps of being entered
> into information carriers, extracted, transferred to other carriers,
> edited, selected, transformed, summarized, and presented. It is important
> to realize that errors can occur at any stage of the data flow, including
> during data cleaning itself."

That last clause — errors occur *during cleaning* — is why Table 1 has a
row for "Value incorrectly changed during previous data cleaning".

**The scale-of-error argument:**

> "Inaccuracy of a single measurement and data point may be acceptable, and
> related to the inherent technical error of the measurement instrument.
> Hence, data cleaning should focus on those errors that are beyond small
> technical variations and that constitute a major shift within or beyond
> the population distribution. In turn, data cleaning must be based on
> knowledge of technical errors and expected ranges of normal values."

**Prioritisation.** "Some errors deserve priority, but which ones are most
important is highly study-specific." The named priority list for clinical
epidemiology: "missing sex, sex misspecification, birth date or examination
date errors, duplications or merging of records, and biologically
impossible results." And the reason:

> "Errors of sex and date are particularly important because they
> contaminate derived variables."

The worked example: date errors -> age errors -> weight-for-age errors ->
misclassification as under- or overweight.

### TABLE 1 (printed p. 0967)

"Issues to Be Considered during Data Collection, Management, and Analysis
of a Questionnaire Study". Three data stages x two problem families:

```
 Data stage    Lack or excess of data           Outliers and inconsistencies
 ---------------------------------------------------------------------------
 Questionnaire Form missing                     Correct value filled out in
               Form double, collected             wrong box
                 repeatedly                     Not readable
               Answering box or options list    Writing error
                 left blank                     Answer given is out of
               More than one option selected      expected (conditional)
                 when not allowed                 range

 Database      Lack or excess of data carried   Outliers and inconsistencies
                 over from questionnaire          carried over from the
               Form or field not entered          questionnaire
               Data erroneously entered twice   Value incorrectly entered
               Value entered in wrong field     Value incorrectly changed
               Inadvertent deletions and          during previous cleaning
                 duplications during database   Transformation
                 handling                         (programming) error

 Analysis      Lack or excess of data carried   Outliers and inconsistencies
 dataset         over from database               carried over from database
               Data extraction or transfer      Data extraction or transfer
                 error                            error
               Deletions or duplications by     Sorting errors (spreadsheets)
                 analyst                        Data-cleaning errors
```

The structure of the table is the point: errors *propagate down the data
flow*, and each stage adds its own. "Transformation (programming) error"
and "Data-cleaning errors" are named error classes.

### Screening Phase (printed p. 0967)

**THE FOUR TYPES OF ODDITY.** Quoted exactly:

> "When screening data, it is convenient to distinguish four basic types of
> oddities: lack or excess of data; outliers, including inconsistencies;
> strange patterns in (joint) distributions; and unexpected analysis
> results and other types of inferences and abstractions (Table 1)."

Note that "inconsistencies" are folded *into* outliers, and that the fourth
type — a surprising regression coefficient — counts as a screening signal.

Screening need not be statistical:

> "Screening methods need not only be statistical. Many outliers are
> detected by perceived nonconformity with prior expectations, based on the
> investigator's experience, pilot studies, evidence in the literature, or
> common sense. Detection may even happen during article review or after
> publication."

**How to make screening objective and systematic** — three numbered moves,
paraphrased closely from the text:

1. Examine the data with simple descriptive tools. "For identifying suspect
   data, one can first predefine expectations about normal ranges,
   distribution shapes, and strength of relationships."
2. "the application of these criteria can be planned beforehand, to be
   carried out during or shortly after data collection, during data entry,
   and regularly thereafter."
3. "comparison of the data with the screening criteria can be partly
   automated and lead to flagging of dubious data, patterns, or results."

The word *predefine* is doing heavy lifting and recurs throughout.

**THE ERRONEOUS INLIER PROBLEM.** This is the most valuable paragraph in
the paper for us and is quoted in full:

> "A special problem is that of erroneous inliers, i.e., data points
> generated by error but falling within the expected range. Erroneous
> inliers will often escape detection. Sometimes, inliers are discovered to
> be suspect if viewed in relation to other variables, using scatter plots,
> regression analysis, or consistency checks. One can also identify some by
> examining the history of each data point or by remeasurement, but such
> examination is rarely feasible. Instead, one can examine and/or remeasure
> a sample of inliers to estimate an error rate."

The estimate-an-error-rate-from-a-sample move is the practical fallback
when you cannot check every value. Reference [23] for inliers is Winkler
(1998), "Problems with inliers", Census Bureau RR98/05 — **not in
`../Research/`**.

### BOX 2 — Screening Methods (printed p. 0969)

Quoted complete. This is the checklist:

> - Checking of questionnaires using fixed algorithms.
> - Validated data entry and double data entry.
> - Browsing of data tables after sorting.
> - Printouts of variables not passing range checks and of records not
>   passing consistency checks.
> - Graphical exploration of distributions: box plots, histograms, and
>   scatter plots.
> - Plots of repeated measurements on the same individual, e.g., growth
>   curves.
> - Frequency distributions and cross-tabulations.
> - Summary statistics.
> - Statistical outlier detection.

Statistical outlier detection is **last of nine**, and is the only item the
paper later qualifies as sometimes invalid (see the small-studies
discussion below).

### Diagnostic Phase (printed p. 0968)

**THE FOUR DIAGNOSES.** Quoted exactly:

> "In this phase, the purpose is to clarify the true nature of the
> worrisome data points, patterns, and statistics. Possible diagnoses for
> each data point are as follows: erroneous, true extreme, true normal
> (i.e, the prior expectation was incorrect), or idiopathic (i.e., no
> explanation found, but still suspect)."

Four verdicts. *Idiopathic* — no explanation found but still suspect — is a
legitimate terminal state, which is important: the framework does not force
a decision it cannot support.

**HARD AND SOFT CUTOFFS:**

> "Some data points are clearly logically or biologically impossible.
> Hence, one may predefine not only screening cutoffs as described above
> (soft cutoffs), but also cutoffs for immediate diagnosis of error (hard
> cutoffs). Figure 2 illustrates this method. Sometimes, suspected errors
> will fall in between the soft and hard cutoffs, and diagnosis will be
> less straightforward. In these cases, it is necessary to apply a
> combination of diagnostic procedures."

**Figure 2** (printed p. 0969, illustration by Giovanni Maki): "Areas
within the Range of a Continuous Variable Defined by Hard and Soft Cutoffs
for Error Screening and Diagnosis, with Recommended Diagnostic Steps for
Data Points Falling in Each Area". It is a banded number line: an inlier
region inside the soft cutoffs; a suspect band between soft and hard
cutoffs requiring diagnosis; and beyond the hard cutoffs a region diagnosed
as error immediately. Two thresholds, three regions, per variable.

**Three diagnostic procedures**, in the order given:

1. **Go back up the data flow.** "One procedure is to go to previous stages
   of the data flow to see whether a value is consistently the same. This
   requires access to well-archived and documented data with justifications
   for any changes made at any stage."
2. **Look for corroborating evidence of a true extreme.** "A second
   procedure is to look for information that could confirm the true extreme
   status of an outlying data point. For example, a very low score for
   weight-for-age (e.g., -6 Z-scores) might be due to errors in the
   measurement of age or weight, or the subject may be extremely
   malnourished, in which case other nutritional variables should also have
   extremely low values." This "requires insight into the coherence of
   variables in a biological or statistical sense."
3. **Collect more information.** "A third procedure is to collect
   additional information, e.g., question the interviewer/measurer about
   what may have happened and, if possible, repeat the measurement." Only
   available if cleaning starts soon after collection.

Two more things from this section:

> "Finding an acceptable value does not always depend on measuring or
> remeasuring. For some input errors, the correct value is immediately
> obvious, e.g., if values of infant length are noted under head
> circumference and vice versa."

And a one-line rule that hits two of our defects directly:

> "Substitute code values for missing data should be corrected before
> analysis."

Finally, an honest note on cost: "The diagnostic phase is labor intensive
and the budgetary, logistical, and personnel requirements are typically
underestimated or even neglected at the study design stage. How much effort
must be spent? Cost-effectiveness studies are needed to answer this
question. Costs may be lower if the data-cleaning process is planned and
starts early in data collection. Automated query generation and automated
comparison of successive datasets can be used to lower costs."

### Treatment Phase (printed pp. 0968-0969)

**THE THREE OPTIONS, AND THEY ARE THE ONLY THREE:**

> "After identification of errors, missing values, and true (extreme or
> normal) values, the researcher must decide what to do with problematic
> observations. The options are limited to correcting, deleting, or leaving
> unchanged."

**WHEN DELETION IS ACCEPTABLE.** Three distinct rules, and they are more
permissive than "never delete":

*Rule 1 — impossible values:*

> "Impossible values are never left unchanged, but should be corrected if a
> correct value can be found, otherwise they should be deleted."

So deletion **is** the prescribed treatment for an impossible value whose
correct value cannot be recovered. The prohibition is on *leaving it*, not
on deleting it.

*Rule 2 — true extremes, default is keep:*

> "What should be done with true extreme values and with values that are
> still suspect after the diagnostic phase? The investigator may wish to
> further examine the influence of such data points, individually and as a
> group, on analysis results before deciding whether or not to leave the
> data unchanged. Statistical methods exist to help evaluate the influence
> of such data points on regression parameters. Some authors have
> recommended that true extreme values should always stay in the analysis
> [25]. In practice, many exceptions are made to that rule."

*Rule 3 — the one legitimate exception, and it comes with an obligation:*

> "The investigator may not want to consider the effect of true extreme
> values if they result from an unanticipated extraneous process. This
> becomes an a posteriori exclusion criterion and the data points should be
> reported as 'excluded from analysis'. Alternatively, it may be that the
> protocol-prescribed exclusion criteria were inadvertently not applied in
> some cases."

Note the mechanism: an excluded true extreme is reclassified as an *a
posteriori exclusion criterion* — a declared scope restriction — and must
be reported as such. It does not silently vanish.

Reference [25] for "true extremes should always stay" is Gardner & Altman,
*Statistics with Confidence* (BMJ, 1994). Reference [26], on
post-randomisation exclusions, is Fergusson et al., BMJ 2002.

*The averaging rule for rapid remeasurement:*

> "For biological continuous variables, some within-subject variation and
> small measurement variation is present in every measurement. If a
> remeasurement is done very rapidly after the initial one and the two
> values are close enough to be explained by these small variations alone,
> accuracy may be enhanced by taking the average of both as the final
> value."

**Feedback loop.** "Data cleaning often leads to insight into the nature
and severity of error-generating processes. The researcher can then give
methodological feedback to operational staff to improve study validity and
precision of outcomes. It may be necessary to amend the study protocol
... In extreme cases, it may be necessary to restart the study." And the
analytical consequence: "the analysis strategy should be adapted to include
robust estimation or to do separate analyses with and without remaining
outliers and/or with and without imputation."

That last clause is the paper's alternative to deciding: **report both
ways.**

### Data Cleaning as a Study-Specific Process (printed p. 0969)

The amount of cleaning effort is not a constant; it follows from the
analysis method and the study objectives:

> "The sensitivity of the chosen statistical analysis method to outlying
> and missing values can have consequences in terms of the amount of effort
> the investigator wants to invest to detect and remeasure. It also
> influences decisions about what to do with remaining outliers (leave
> unchanged, eliminate, or weight during analysis) and with missing data
> (impute or not). Study objectives codetermine the required precision of
> the outcome measures, the error rate that is acceptable, and, therefore,
> the necessary investment in data cleaning."

Longitudinal studies get a specific instruction:

> "Longitudinal studies necessitate checking the temporal consistency of
> data. Plots of serial individual data such as growth data or repeated
> measurements of categorical variables often show a recognizable pattern
> from which a discordant data point clearly stands out."

Clinical trials get a warning about the cleaner: "there may be concerns
about investigator bias resulting from the close data inspections that
occur during cleaning, so that examination by an independent expert may be
needed."

**Small studies.** Directly relevant to a 43-row facility file:

> "In small studies, a single outlier will have a greater distorting effect
> on the results. Some screening methods such as examination of data tables
> will be more effective, whereas others, such as statistical outlier
> detection, may become less valid with smaller samples. The volume of data
> will be smaller; hence, the diagnostic phase can be cheaper and the whole
> procedure more complete. Smaller studies usually involve fewer people,
> and the steps in the data flow may be fewer and more straightforward,
> allowing fewer opportunities for errors."

### Documentation and Reporting (printed pp. 0969-0970)

**The data-cleaning plan** — what belongs in the protocol, before any data
arrives:

> "We suggest including a data-cleaning plan in study protocols. This plan
> should include budget and personnel requirements, prior expectations used
> to screen suspect data, screening tools, diagnostic procedures used to
> discern errors from true values, and the decision rules that will be
> applied in the editing phase."

**Per-data-point documentation:**

> "Proper documentation should exist for each data point, including
> differential flagging of types of suspected features, diagnostic
> information, and information on type of editing, dates, and personnel
> involved."

Note "differential flagging of **types** of suspected features" — one
boolean is not enough; the flag should carry which screen fired.

**The reporting standard**, the paper's central recommendation:

> "We recommend that medical scientific reports include data-cleaning
> methods. These methods should include error types and rates, at least for
> the primary outcome variables, with the associated deletion and
> correction rates, justification for imputations, and differences in
> outcome with and without remaining outliers."

Governance: data-monitoring and safety committees should receive detailed
cleaning reports in large studies, and "procedural feedbacks on study
design and conduct should be submitted to a study's steering and ethics
committees."

### References

31 entries, mostly clinical. Worth knowing about: [9] Hadi (1992) on
multiple outliers in multivariate data; [10] Altman (1991) *Practical
Statistics in Medical Research* — the source for hard/soft cutoffs; [12]
Iglewicz & Hoaglin (1993) *How to Detect and Handle Outliers*; [14] Welsch
(1982) on influence functions and regression diagnostics; [19] Wang (1998)
"A product perspective on total data quality management"; [22] Bauer &
Johnson (2000) "Editing data: What difference do consistency checks make?",
Am J Epidemiol 151:921-926; **[23] Winkler (1998) "Problems with inliers",
Census Bureau RR98/05**; [24] West & Winkler (1991) "Database error trapping
and prediction", JASA 86:987-996; [25] Gardner & Altman (1994); [27]
Allison (2001) *Missing Data*; [29] Schafer (1997) *Analysis of Incomplete
Multivariate Data*; [31] Gonzalez, Ogus, Shapiro & Tepping (1975)
"Standards for discussion and presentation of errors in survey and census
data", JASA 70:6-23.

---

## 4. Definitions, stated as the paper states them

All from Box 1 unless noted.

**Data cleaning:** "Process of detecting, diagnosing, and editing faulty
data."

**Data editing:** "Changing the value of data shown to be incorrect."

**Data flow:** "Passage of recorded information through successive
information carriers."

**Inlier:** "Data value falling within the expected range."

**Outlier:** "Data value falling outside the expected range."

**Robust estimation:** "Estimation of statistical parameters, using methods
that are less sensitive to the effect of outliers than more conventional
methods."

**Erroneous inlier** (body, Screening Phase): "data points generated by
error but falling within the expected range."

**The three stages** (body, Data Cleaning as a Process): "a three-stage
process, involving repeated cycles of screening, diagnosing, and editing of
suspected data abnormalities." The section headings name them Screening
Phase, Diagnostic Phase, Treatment Phase; the title names them detecting,
diagnosing, editing. All three namings are the paper's own.

**The four screening oddities** (Screening Phase): "lack or excess of data;
outliers, including inconsistencies; strange patterns in (joint)
distributions; and unexpected analysis results and other types of
inferences and abstractions."

**The four diagnoses** (Diagnostic Phase): "erroneous, true extreme, true
normal (i.e, the prior expectation was incorrect), or idiopathic (i.e., no
explanation found, but still suspect)."

**The three treatments** (Treatment Phase): "The options are limited to
correcting, deleting, or leaving unchanged."

**Soft and hard cutoffs** (Diagnostic Phase): soft cutoffs are "screening
cutoffs"; hard cutoffs are "cutoffs for immediate diagnosis of error".

---

## 5. What this means for siting-atlas

### 5.1 "Erroneous inlier" is the name for two of our three worst defects

This is the concept we were missing, and it unifies findings we had filed
separately.

- `ingest/census_api.py:110`: 86 ZCTAs carry `median_household_income =
  $250,001`. That is a perfectly plausible income. It is inside every
  expected range.
- `warehouse/facilities.py:118`: `open_quarter.fillna(1)` on 19 of 43
  facilities. Q1 is a perfectly plausible quarter. It is inside the
  expected range — in fact it is *in* the range by construction.

Both are "data points generated by error but falling within the expected
range", and the paper's own prediction holds exactly: "Erroneous inliers
will often escape detection." No range check will ever find either. That is
*why* `experiments/superseded-artefacts/panel_report.json` reports them as clean.

And the paper gives the detection method: "Sometimes, inliers are
discovered to be suspect if viewed in relation to other variables, using
scatter plots, regression analysis, or consistency checks." Which is
precisely how the Q1 artefact *was* found — 35.47% of events in Q1 against
25% expected is a strange pattern in a joint distribution, screening oddity
type three. The project measured it in `hazard_report.json` and did not act,
because it had no framework that said a distributional oddity is a
screening signal requiring a diagnosis.

The one-line prescription is in the Diagnostic Phase: **"Substitute code
values for missing data should be corrected before analysis."**

### 5.2 The four diagnoses resolve our outlier stand-off

`DATA_QUALITY.md` F6 finds 28.36% of ZCTAs are robust-z outliers on
household density and concludes, correctly, that filtering would "delete
Manhattan". It then stops, because it has no vocabulary for "extreme and
correct".

The paper supplies it. Every extreme gets one of four verdicts, and F6's own
prose already assigns them without naming them:

```
  our finding (F6)                       Van den Broeck diagnosis
  ---------------------------------------------------------------------
  ZCTA 10069, 162,659 people/sq mi       TRUE EXTREME
  three ZCTAs above 10,000 sq mi (AK/NV) TRUE EXTREME
  cost_per_parcel $6.41 at ZCTA 83650    TRUE EXTREME
  rent_index $68,623/mo at Water Mill    ERRONEOUS  (seasonal lettings
                                           contaminate ZORI)
  permits_yoy_pct = -100% on 6,232 rows  TRUE NORMAL, prior expectation
                                           was wrong (tiny denominators)
  traffic_proximity = 14,529,474         IDIOPATHIC until the units
                                           question is answered
```

And the treatment follows from the diagnosis, not from the magnitude. True
extremes stay — "Some authors have recommended that true extreme values
should always stay in the analysis". The Water Mill contamination is
erroneous and, having no recoverable correct value, is a candidate for
deletion *reported as such*. `permits_yoy_pct` is not a data problem at all
but a derived-variable design problem, and diagnosing it as true-normal is
what points at the real fix (a denominator floor) rather than a filter.

This is a much better structure for R9 than "screen and report counts".
R9 should emit a **diagnosis column**, not a flag.

### 5.3 Hard and soft cutoffs are the practical form of our edit set

`DATA_QUALITY.md` F3 lists 22 edits as pass/fail. Figure 2 says use two
thresholds per variable, not one:

```
  soft cutoff  ->  flag for diagnosis   (screening)
  hard cutoff  ->  diagnose as error immediately
```

Applied to our own list, the difference is real. `population / households
in [1, 10]` currently flags 137 ZCTAs as violations. Under the two-cutoff
scheme, the soft bound is 10 (implausible, look at it) and the hard bound
is something like 200 (a 3,000-inmate prison recorded as one household is
not a plausible reading of the ACS, it is a group-quarters artefact). That
separates "worth a look" from "certainly wrong", and it stops the edit
report being 137 rows of noise that nobody reads twice.

### 5.4 When deletion is acceptable — the answer, and where we fail it

The paper permits deletion in exactly two situations and forbids it
silently in all of them.

1. **Impossible value, correct value not recoverable.** "Impossible values
   are never left unchanged, but should be corrected if a correct value can
   be found, otherwise they should be deleted." Our `cost/runner.py:57`
   drop of 55 zero-population ZCTAs arguably qualifies — a cost per parcel
   with a zero denominator is impossible — and it is *logged*, so it is
   nearly compliant. What is missing is the diagnosis: the other 23 dropped
   ZCTAs have people and no households, which is not impossible, it is
   group quarters. Deleting those is not covered by rule 1.
2. **True extreme arising from an unanticipated extraneous process.** Then
   "This becomes an a posteriori exclusion criterion and the data points
   should be reported as 'excluded from analysis'."

Everything else falls under the standing instruction to report: "differences
in outcome with and without remaining outliers", and "separate analyses
with and without remaining outliers and/or with and without imputation."

Measured against that, `cost/runner.py:166` fails on the *reporting* side
rather than the *deleting* side. It is complete-case deletion with no
diagnosis of the dropped stratum and no with/without comparison. The fix
the paper asks for is not "stop deleting" — it is "run it both ways and
publish the difference". That is cheaper than we assumed and more
convincing than an imputation nobody trusts.

`models/panel_source.py:144` is the better-behaved case and the audit
already credits it: the counts are recorded in `detail`. What it still
lacks is the with/without outcome comparison.

### 5.5 The reporting standard is a checklist we can be graded against

> "error types and rates, at least for the primary outcome variables, with
> the associated deletion and correction rates, justification for
> imputations, and differences in outcome with and without remaining
> outliers."

Scored honestly against `outputs/metrics/`:

```
  error types and rates                 NO   nothing classifies errors
  deletion rates                        PART logged at 4 of 10 sites (F9)
  correction rates                      NO   no edit is recorded as an edit
  justification for imputations         PART daganzo.py income only
  outcome with and without outliers     NO   never run
```

That is a five-line scorecard we could put in the defence pack, sourced.

### 5.6 The small-study caveat lands on the facility panel

> "In small studies, a single outlier will have a greater distorting effect
> on the results. Some screening methods such as examination of data tables
> will be more effective, whereas others, such as statistical outlier
> detection, may become less valid with smaller samples."

The facility panel is 43 rows and 104 national rows. Statistical outlier
detection on it is not worth writing. **Browsing the sorted table is**, and
that is Box 2 item 3. The three contradicting date pairs would fall out of
a sorted table in about a minute. The paper's consolation is real here too:
"the diagnostic phase can be cheaper and the whole procedure more
complete" — 104 rows can be fully adjudicated, which 33,791 ZCTAs cannot.

### 5.7 Two structural points we should adopt

**Errors occur during cleaning.** Table 1 has explicit rows for "Value
incorrectly changed during previous data cleaning", "Transformation
(programming) error" and "Data-cleaning errors". Our own `enabled.fillna
(False)` at `facilities.py:215` is exactly that: a cleaning step that
introduced an error by collapsing "not covered by any known catchment" into
"known not to be served".

**Diagnosis requires the earlier stages of the data flow to still exist.**
"One procedure is to go to previous stages of the data flow to see whether
a value is consistently the same. This requires access to well-archived and
documented data with justifications for any changes made at any stage." We
cannot do this for `open_quarter`, because the original NULL is discarded
at `facilities.py:118` and never reaches the panel. That is the concrete
cost of the reversibility failure, stated in the paper's own terms.

---

## 6. What I did NOT read or did not understand

- **Nothing was skipped.** All 5 PDF pages: the full body, Boxes 1 and 2,
  Table 1, both figure captions, the acknowledgments and all 31 references.
- **Figures 1 and 2 are illustrations and do not appear in the PDF text
  layer.** I have only their captions and the body text that describes
  them. My descriptions in §3 above are **reconstructions from the
  captions and prose, not readings of the images.** Specifically: I am
  confident Figure 1 is a three-stage cycle with three study-stage entry
  points, and that Figure 2 is a banded continuous range with soft and hard
  cutoffs and per-band recommended diagnostic steps, because the text says
  so. I have **not** rendered the pages as images to check the internal
  labels. If either figure is going to be reproduced or paraphrased in
  detail, render PDF pages 2 and 4 first.
- **The paper gives no statistical machinery.** There is no formula, no
  threshold, no test. Every concrete method it names (Hadi's multivariate
  outlier method, the dip test of unimodality, influence functions, robust
  estimation, multiple imputation) is a citation, not an exposition. None
  of those cited works is in `../Research/` and I have read none of them.
- **Reference [23], Winkler (1998) "Problems with inliers"** is the obvious
  next paper if erroneous inliers become a workstream, and it is not in
  `../Research/`. Note it is *not* the same as `rr99-01.pdf`, which has no
  inlier content.
- **The paper is written for clinical epidemiology and I have transposed it
  to an observational ZCTA panel.** Two transpositions are shakier than the
  rest and I flag them rather than hide them. First, "remeasurement" has no
  analogue for us — we cannot re-run the ACS — so diagnostic procedure 3
  collapses into "go and look at a permit record", which is really
  procedure 1. Second, the paper's unit is a patient with repeated
  measurements; our unit is a ZCTA with a pinned vintage broadcast across
  32 quarters, so "temporal consistency of data" means something different
  for us than it does for a growth curve.
- **I did not check the PMC version against the PLoS PDF.** Printed page
  numbers 0966-0970 are taken from the running footers in the PDF and are
  reliable.
